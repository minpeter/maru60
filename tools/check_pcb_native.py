#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# Run: tools/run_kicad9.sh python3 tools/check_pcb_native.py --output <new-directory>
"""Replay pinned native CAD checks into a fresh directory without editing a checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]


def hashes(directory: Path) -> Mapping[str, str]:
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--output", type=Path, required=True)
    _ = parser.add_argument("--checkpoint", type=Path)
    _ = parser.add_argument("--expected-opens", type=int)
    _ = parser.add_argument("--material", action="store_true")
    args = parser.parse_args()
    if not __debug__:
        parser.error("geometry assertions require normal Python")
    selected = json.loads((ROOT / "pcb/current.json").read_text())[
        "development_prototype"
    ]
    checkpoint = (
        args.checkpoint or (ROOT / selected["files"][0]["path"]).parent.parent
    ).resolve()
    expected = (
        args.expected_opens
        if args.expected_opens is not None
        else selected["reported_diagnostics"]["open_pairs"]
    )
    source = checkpoint / "pcb"
    board = source / "maru60.kicad_pcb"
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and not any(
        output.is_relative_to(ROOT / allowed)
        for allowed in ("build", ".omo/evidence")
    ):
        parser.error("in-repository output must be under build/ or .omo/evidence/")
    if (
        output.exists()
        or output.is_relative_to(checkpoint)
        or checkpoint.is_relative_to(output)
    ):
        parser.error("output must be new and separate from the checkpoint")
    before = hashes(source)
    if args.checkpoint is None:
        for pin in selected["files"]:
            assert (
                hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest()
                == pin["sha256"]
            ), pin["path"]
    output.mkdir(parents=True)
    environment = dict(
        os.environ, QT_QPA_PLATFORM="offscreen", PYTHONDONTWRITEBYTECODE="1"
    )

    def run(name: str, command: list[str]) -> None:
        with (output / f"{name}.log").open("w") as log:
            _ = subprocess.run(
                command,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )

    import pcbnew

    assert pcbnew.GetBuildVersion() == "9.0.2+dfsg-1", pcbnew.GetBuildVersion()
    run(
        "drc",
        [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--schematic-parity",
            "-o",
            str(output / "drc.json"),
            str(board),
        ],
    )
    run(
        "erc",
        [
            "kicad-cli",
            "sch",
            "erc",
            "--format",
            "json",
            "-o",
            str(output / "erc.json"),
            str(source / "maru60.kicad_sch"),
        ],
    )
    run(
        "netlist",
        [
            "kicad-cli",
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "-o",
            str(output / "netlist.xml"),
            str(source / "maru60.kicad_sch"),
        ],
    )
    drc = json.loads((output / "drc.json").read_text())
    erc = json.loads((output / "erc.json").read_text())
    assert len(drc["unconnected_items"]) == expected, drc["unconnected_items"]
    assert not drc["schematic_parity"], drc["schematic_parity"]
    assert not any(row["severity"] == "error" for row in drc["violations"]), drc[
        "violations"
    ]
    assert not any(sheet.get("violations") for sheet in erc["sheets"]), erc
    portable = (
        ROOT / "pcb/experiments/resume-20261106-usb-pendant-prototype/portable-tools"
    )
    run(
        "net-identity",
        [
            sys.executable,
            str(portable / "verify_net_identity.py"),
            str(board),
            str(output / "netlist.xml"),
            str(output / "net-identity.json"),
        ],
    )
    cold = output / "cold/pcb"
    shutil.copytree(source, cold)
    loaded = pcbnew.LoadBoard(str(cold / "maru60.kicad_pcb"))
    loaded.BuildConnectivity()
    pcbnew.ZONE_FILLER(loaded).Fill(loaded.Zones())
    pcbnew.SaveBoard(str(cold / "maru60.kicad_pcb"), loaded)
    assert hashes(cold) == before, "cold refill changed serialized CAD"
    if args.material:
        run(
            "material",
            [
                sys.executable,
                str(ROOT / "pcb/tools/export_material_graph.py"),
                str(board),
                str(output / "material-graph.json"),
            ],
        )
    assert hashes(source) == before, "source CAD changed"
    result = {
        "pass": True,
        "board_sha256": before["maru60.kicad_pcb"],
        "kicad_version": pcbnew.GetBuildVersion(),
        "open_pairs": len(drc["unconnected_items"]),
        "warnings": sum(row["severity"] == "warning" for row in drc["violations"]),
        "other_errors": 0,
        "ERC": 0,
        "schematic_parity": 0,
        "cold_refill_files_identical": len(before),
        "source_unchanged": True,
        "material_recomputed": args.material,
        "manufacturing_ready": False,
        "scope": "Native CAD replay against the expected open count; physical, SI and active-power qualification remain separate.",
    }
    (output / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
