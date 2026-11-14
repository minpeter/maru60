#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run: uv run tools/check_pcb_portable.py --output /tmp/maru60-portable-new
# ──────────────────
"""Replay bounded portable checks without writing into archived sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_pcb_current import JsonValue, ManifestError, read_pins

ROOT: Final = Path(__file__).resolve().parents[1]
RECOVERY: Final = ROOT / "pcb/experiments/led-startup-recovery"
CANDIDATE: Final = RECOVERY / "candidate"
OVERLAY: Final = Path("firmware/qmk/keyboards/maru60/rp2350")
POWER: Final = ROOT / "pcb/experiments/resume-20261106-usb-pendant-prototype/evidence/power-audit"
NETLIST_SHA256: Final = "2258e9920ce2b6c72daa6c1198c2325a8bb7ab7eea3384ba6b8af1fa57057306"
# Files of the active overlay that deliberately differ from the archived recovery candidate, with
# the hash of the active file. The candidate packet itself stays as it was reviewed.
#   config.h: GPIO_INPUT_PIN_DELAY 120 (matrix read delay; order-candidate signal-integrity report)
ACTIVE_DELTAS: Final = {
    "config.h": "6f6a98aef67d23758078954e9e8a892d2c0454f3f986199c1d8ae47e9b356033",
}
ARCHIVE_PINS: Final = (
    (CANDIDATE / "run_host_checks.py", "83db97c804ba1a83afd5172e5ead9b6684a989527537ac42857b4b97ac5e2377"),
    (RECOVERY / "evidence/static-v7/check.py", "cd213acf8055464b388c133fbfe75163f3fce3c52930e3984beecf831756df66"),
    (POWER / "replay_calculations.py", "63ba8dec25f9feb733db6182847ee30eea4094d0089df3ea8db19ce3acfb4c29"),
    (POWER / "calculations.json", "db58fc528787e2016e5c09eae4f018aac2fd3deb8f7d5b1e2a5477204bbed001"),
)


@dataclass(frozen=True, slots=True)
class CheckFailure(Exception):
    detail: str


class Arguments(argparse.Namespace):
    output: Path = Path()


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_pin(path: Path, expected: str) -> None:
    """Reject missing or changed inputs before executing archived checkers."""
    if digest(path) != expected:
        raise CheckFailure(f"SHA256 mismatch: {path}")


def overlay_identity() -> tuple[tuple[str, str], ...]:
    """Require the 22-file active overlay to equal the recovery candidate except for ACTIVE_DELTAS."""
    manifests: list[tuple[tuple[str, str], ...]] = []
    for base in (ROOT / "pcb" / OVERLAY, CANDIDATE / OVERLAY):
        manifests.append(tuple(
            (str(path.relative_to(base)), digest(path))
            for path in sorted(base.rglob("*")) if path.is_file()
        ))
    active, candidate = manifests
    if len(active) != 22 or [name for name, _ in active] != [name for name, _ in candidate]:
        raise CheckFailure("Active firmware must have the 22 recovery-candidate files")
    for (name, actual), (_, archived) in zip(active, candidate, strict=True):
        expected = ACTIVE_DELTAS.get(name, archived)
        if actual != expected:
            raise CheckFailure(f"Active firmware file differs from its pin: {name}")
    return active


def selected_netlist() -> Path:
    """Validate manifest pins and resolve the selected prototype's stored netlist."""
    manifest = ROOT / "pcb/current.json"
    for pin in read_pins(manifest):
        path = (ROOT / pin.path).resolve()
        if Path(pin.path).is_absolute() or not path.is_relative_to(ROOT):
            raise CheckFailure(f"Manifest path escapes repository: {pin.path}")
        check_pin(path, pin.sha256)
    data: JsonValue = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CheckFailure("Expected current.json object")
    prototype = data.get("development_prototype")
    if not isinstance(prototype, dict):
        raise CheckFailure("Expected development_prototype object")
    records = prototype.get("files")
    if not isinstance(records, list):
        raise CheckFailure("Expected development_prototype files")
    boards: list[Path] = []
    for record in records:
        if not isinstance(record, dict):
            raise CheckFailure("Expected prototype file object")
        name = record.get("path")
        if isinstance(name, str) and name.endswith(".kicad_pcb"):
            boards.append(ROOT / name)
    if len(boards) != 1:
        raise CheckFailure("Expected exactly one development prototype PCB")
    netlist = boards[0].resolve().parent.parent / "qa/netlist.xml"
    check_pin(netlist, NETLIST_SHA256)
    return netlist


def run(command: list[str], log: Path) -> None:
    """Capture the exact child invocation and exit status in the output directory."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONOPTIMIZE="")
    with log.open("w", encoding="utf-8") as stream:
        _ = stream.write("argv: " + json.dumps(command) + "\n")
        stream.flush()
        result = subprocess.run(command, cwd=log.parent, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
        _ = stream.write(f"\nexit_code: {result.returncode}\n")
    if result.returncode:
        raise CheckFailure(f"Child exited {result.returncode}; see {log}")


def main() -> int:
    """Run identity, real host C checks, stored-netlist checks and arithmetic replay."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--output", type=Path, required=True,
                        help="fresh directory outside source (in-repo: build/ or .omo/evidence/)")
    output = parser.parse_args(namespace=Arguments()).output.resolve()
    try:
        if output.is_relative_to(ROOT) and not any(
            output.is_relative_to(ROOT / allowed) for allowed in ("build", ".omo/evidence")
        ):
            raise CheckFailure("In-repository output must be under build/ or .omo/evidence/")
        output.mkdir(parents=True, exist_ok=False)
        before = overlay_identity()
        netlist = selected_netlist()
        manifest_before = digest(ROOT / "pcb/current.json")
        for path, expected in ARCHIVE_PINS:
            check_pin(path, expected)
        _ = (output / "identity.json").write_text(json.dumps({
            "active_equals_candidate": not ACTIVE_DELTAS, "declared_active_deltas": sorted(ACTIVE_DELTAS),
            "file_count": len(before),
            "source_hashes": dict(before), "current_manifest_sha256": manifest_before,
            "netlist": str(netlist.relative_to(ROOT)), "netlist_sha256": NETLIST_SHA256,
            "archive_hashes": {str(p.relative_to(ROOT)): h for p, h in ARCHIVE_PINS},
        }, indent=2) + "\n", encoding="utf-8")
        python = [sys.executable, "-B"]
        run([*python, str(CANDIDATE / "run_host_checks.py"), "--output",
             str(output / "host")], output / "host.log")
        run([*python, str(RECOVERY / "evidence/static-v7/check.py"),
             "--netlist", str(netlist), "--expected-sha256", NETLIST_SHA256,
             "--source", str(ROOT / "pcb" / OVERLAY), "--matrix-script",
             str(CANDIDATE / "firmware/tests/matrix_simultaneous_model.py"),
             "--output", str(output / "static.json")], output / "static.log")
        scratch = output / "power"
        scratch.mkdir()
        for name in ("replay_calculations.py", "calculations.json"):
            _ = shutil.copyfile(POWER / name, scratch / name)
        run([*python, str(scratch / "replay_calculations.py")], output / "power.log")
        if before != overlay_identity():
            raise CheckFailure("Firmware changed during validation")
        check_pin(ROOT / "pcb/current.json", manifest_before)
        _ = selected_netlist()
        for path, expected in ARCHIVE_PINS:
            check_pin(path, expected)
        _ = (output / "results.json").write_text(json.dumps({
            "pass": True, "scope": "Portable checks only; no native CAD or hardware qualification",
            "active_candidate_files_exact": len(before), "inputs_unchanged": True,
            "host_report": "host/results.json", "static_report": "static.json",
            "power_report": "power/calculation-replay-result.json",
            "qualification_default": 0,
            "not_run": ["Fresh KiCad export/ERC/DRC", "Full pinned QMK/ARM builds",
                        "Official VIA application validation", "Physical hardware qualification"],
        }, indent=2) + "\n", encoding="utf-8")
    except (CheckFailure, ManifestError, OSError, ValueError) as error:
        print(f"Portable PCB check failed: {error}", file=sys.stderr)
        return 1
    print(f"PASS portable checks only: {output / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
