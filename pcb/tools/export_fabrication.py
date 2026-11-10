#!/usr/bin/env python3
"""Build a draft fabrication package for the frozen Maru60 PCB.

The board is a KiCad 9 s-expression file.  ``pcbnew`` is not available in this
environment, so this script parses the board directly and emits:

* ``BOM.csv``          one row per non-logo footprint (382 rows)
* ``CPL.csv``          SMD placements only (370 rows)
* ``PROVENANCE.json``  hashes, exact commands, timestamps and checks
* ``VERIFICATION.json`` machine-readable check results
* ``export.log``       captured KiCad CLI output

It also runs the KiCad 9 CLI through ``tools/run_kicad9.sh`` to produce
Gerbers, drill, IPC-D-356 and STEP.  The script never writes outside
``pcb/fabrication/`` and never touches the frozen board.

Run with the repository virtualenv, not ``uv``::

    .venv/bin/python pcb/tools/export_fabrication.py

The script is intentionally stdlib-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOARD = (
    REPO_ROOT
    / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb"
)
DEFAULT_OUT = REPO_ROOT / "pcb/fabrication"
EXPECTED_BOARD_SHA256 = (
    "cb7b5b2941bc0e1c4d0a1d10c6dd694f8cf35c4f35665c342dfb747492e10a5d"
)
KICAD_IMAGE = "maru60-kicad:9.0.2"
KICAD_WRAPPER = "tools/run_kicad9.sh"

# Footprints that are not BOM lines.  LOGO1 is a board-only silkscreen logo;
# the task's 382-row count is the 383 footprint blocks minus that logo.
BOM_EXCLUDED_REFS = {"LOGO1"}

# Candidate / open items called out by the fabrication task.
CANDIDATE_NOTES = {
    "J1": "candidate: USB4105-GF-A; not approved",
    "F1": "candidate: SF-1206F100-2; not approved",
    "C137": "candidate 4.7uF 50V; effective C TBD; not approved",
    "C140": "22uF 10V; effective >=12uF TBD",
    "C141": "22uF 10V; effective >=12uF TBD",
    "C125": "1uF 50V; effective TBD",
    "C274": "100nF 10V X7R candidate",
    "C275": "100nF 10V X7R candidate",
    "U1": "candidate; not procurement approved",
}

STATUS_REFS = {"L1", "C102", "C103", "C199"}


# ---------------------------------------------------------------------------
# s-expression parsing
# ---------------------------------------------------------------------------


def parse_sexpr(text: str):
    """Parse a KiCad s-expression into nested lists of strings.

    KiCad uses quoted strings with backslash escapes and bare atoms.  The
    parser is deliberately small and strict enough for a board file.
    """

    i = 0
    n = len(text)

    def skip_ws() -> None:
        nonlocal i
        while i < n and text[i].isspace():
            i += 1

    def parse_value():
        nonlocal i
        skip_ws()
        if i >= n:
            raise ValueError("unexpected end of s-expression")
        ch = text[i]
        if ch == "(":
            i += 1
            out = []
            while True:
                skip_ws()
                if i >= n:
                    raise ValueError("unterminated list")
                if text[i] == ")":
                    i += 1
                    return out
                out.append(parse_value())
        if ch == '"':
            i += 1
            buf = []
            while i < n:
                ch = text[i]
                if ch == "\\":
                    i += 1
                    if i >= n:
                        raise ValueError("unterminated escape")
                    esc = text[i]
                    buf.append(
                        {
                            "n": "\n",
                            "t": "\t",
                            "r": "\r",
                            '"': '"',
                            "\\": "\\",
                        }.get(esc, esc)
                    )
                    i += 1
                elif ch == '"':
                    i += 1
                    return "".join(buf)
                else:
                    buf.append(ch)
                    i += 1
            raise ValueError("unterminated string")
        start = i
        while i < n and not text[i].isspace() and text[i] not in "()":
            i += 1
        return text[start:i]

    return parse_value()


def child(node, name: str):
    if not isinstance(node, list):
        return None
    for item in node:
        if isinstance(item, list) and item and item[0] == name:
            return item
    return None


def children(node, name: str):
    if not isinstance(node, list):
        return []
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def atom(node, index: int, default: str = "") -> str:
    if isinstance(node, list) and len(node) > index:
        return str(node[index])
    return default


def first_prop(props: dict[str, str], *names: str) -> str:
    for name in names:
        value = props.get(name, "").strip()
        if value:
            return value
    return ""


def natural_key(value: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def clean_text(value: str) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


# ---------------------------------------------------------------------------
# board model
# ---------------------------------------------------------------------------


def parse_footprint(node) -> dict:
    footprint_name = atom(node, 1)
    layer_node = child(node, "layer")
    layer = atom(layer_node, 1) if layer_node else ""
    at_node = child(node, "at")
    x = float(atom(at_node, 1, "0"))
    y = float(atom(at_node, 2, "0"))
    rotation = float(atom(at_node, 3, "0")) if at_node and len(at_node) > 3 else 0.0

    props: dict[str, str] = {}
    for prop in children(node, "property"):
        if len(prop) >= 3:
            props[str(prop[1])] = str(prop[2])

    attr_node = child(node, "attr")
    attr_tokens = [str(token) for token in attr_node[1:]] if attr_node else []
    dnp_node = child(node, "dnp")
    dnp = "dnp" in attr_tokens or (dnp_node is not None and atom(dnp_node, 1).lower() == "yes")

    pads = []
    for pad in children(node, "pad"):
        pads.append(
            {
                "number": atom(pad, 1),
                "type": atom(pad, 2),
                "shape": atom(pad, 3),
            }
        )

    return {
        "reference": first_prop(props, "Reference"),
        "value": first_prop(props, "Value"),
        "footprint": footprint_name,
        "layer": layer,
        "x": x,
        "y": y,
        "rotation": rotation,
        "props": props,
        "attr_tokens": attr_tokens,
        "dnp": dnp,
        "board_only": "board_only" in attr_tokens,
        "exclude_from_bom": "exclude_from_bom" in attr_tokens,
        "exclude_from_pos": "exclude_from_pos_files" in attr_tokens,
        "smd": "smd" in attr_tokens,
        "through_hole": "through_hole" in attr_tokens,
        "pads": pads,
    }


def compute_edge_extents(root) -> dict | None:
    xs: list[float] = []
    ys: list[float] = []
    for node in root[1:]:
        if not isinstance(node, list) or not node:
            continue
        if node[0] not in {"gr_line", "gr_arc", "gr_rect", "gr_circle", "gr_poly"}:
            continue
        layer_node = child(node, "layer")
        if not layer_node or atom(layer_node, 1) != "Edge.Cuts":
            continue
        for key in ("start", "mid", "end", "center"):
            point = child(node, key)
            if point and len(point) >= 3:
                xs.append(float(atom(point, 1)))
                ys.append(float(atom(point, 2)))
        pts = child(node, "pts")
        if pts:
            for point in children(pts, "xy"):
                if len(point) >= 3:
                    xs.append(float(atom(point, 1)))
                    ys.append(float(atom(point, 2)))
        if node[0] == "gr_circle":
            center = child(node, "center")
            end = child(node, "end")
            if center and end and len(center) >= 3 and len(end) >= 3:
                cx, cy = float(atom(center, 1)), float(atom(center, 2))
                ex, ey = float(atom(end, 1)), float(atom(end, 2))
                radius = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
                xs.extend([cx - radius, cx + radius])
                ys.extend([cy - radius, cy + radius])
    if not xs or not ys:
        return None
    return {
        "x": round(max(xs) - min(xs), 4),
        "y": round(max(ys) - min(ys), 4),
        "min_x": round(min(xs), 4),
        "min_y": round(min(ys), 4),
        "max_x": round(max(xs), 4),
        "max_y": round(max(ys), 4),
    }


def parse_board(board_path: Path) -> dict:
    text = board_path.read_text(encoding="utf-8")
    root = parse_sexpr(text)
    if not root or root[0] != "kicad_pcb":
        raise ValueError(f"{board_path} is not a kicad_pcb file")

    general = child(root, "general")
    thickness_node = child(general, "thickness") if general else None
    thickness = float(atom(thickness_node, 1)) if thickness_node else None

    layers_node = child(root, "layers")
    copper_layers = []
    if layers_node:
        for item in layers_node[1:]:
            if isinstance(item, list) and len(item) >= 2 and str(item[1]).endswith(".Cu"):
                copper_layers.append(str(item[1]))

    setup = child(root, "setup")
    stackup = child(setup, "stackup") if setup else None
    finish_node = child(stackup, "copper_finish") if stackup else None
    finish = atom(finish_node, 1) if finish_node else ""
    dielectric_node = child(stackup, "dielectric_constraints") if stackup else None
    dielectric_constraints = atom(dielectric_node, 1).lower() == "yes" if dielectric_node else None

    footprints = []
    for node in root[1:]:
        if isinstance(node, list) and node and node[0] == "footprint":
            footprints.append(parse_footprint(node))

    return {
        "format_version": atom(child(root, "version"), 1),
        "generator": atom(child(root, "generator"), 1),
        "generator_version": atom(child(root, "generator_version"), 1),
        "thickness_mm": thickness,
        "copper_layers": copper_layers,
        "finish": finish,
        "dielectric_constraints": dielectric_constraints,
        "edge_extents": compute_edge_extents(root),
        "footprints": footprints,
    }


# ---------------------------------------------------------------------------
# BOM / CPL
# ---------------------------------------------------------------------------


def manufacturer_of(fp: dict) -> str:
    return first_prop(
        fp["props"],
        "Manufacturer",
        "manufacturer",
        "Mfr",
        "MFR",
        "Manufacturer_Name",
    )


def mpn_of(fp: dict) -> str:
    return first_prop(
        fp["props"],
        "MPN",
        "mpn",
        "manufacturer_pn",
        "Manufacturer_PN",
        "Mfr_PN",
        "Mfr Part Number",
        "Manufacturer Part Number",
    )


def supplier_sku_of(fp: dict) -> str:
    return first_prop(
        fp["props"],
        "Supplier SKU",
        "Supplier_SKU",
        "SupplierSKU",
        "LCSC",
        "LCSC Part",
        "LCSC Part #",
        "JLCPCB Part #",
        "Digi-Key Part Number",
        "Mouser Part Number",
    )


def notes_of(fp: dict) -> str:
    notes: list[str] = []
    ref = fp["reference"]

    if fp["board_only"]:
        notes.append("board_only")
    if fp["exclude_from_bom"]:
        notes.append("exclude_from_bom")
    if fp["exclude_from_pos"]:
        notes.append("exclude_from_pos_files")
    if fp["dnp"]:
        notes.append("DNP")

    if ref.startswith("TP"):
        notes.append("test point; excluded from BOM/CPL")
    if ref == "STAB_RS1":
        notes.append("board-only stabilizer; not a BOM line")
    if ref == "J2":
        notes.append("through-hole SWD header")
    if ref in CANDIDATE_NOTES:
        notes.append(CANDIDATE_NOTES[ref])
    if ref in STATUS_REFS:
        status = first_prop(fp["props"], "status", "Status", "Part_Selection_Status")
        if status:
            notes.append(status)
    if ref == "U1":
        silicon = first_prop(fp["props"], "Silicon_Revision_Requirement")
        if silicon:
            notes.append(silicon)
        identity = first_prop(fp["props"], "Incoming_Identity_Check")
        if identity:
            notes.append(identity)

    description = first_prop(fp["props"], "Description")
    if description:
        notes.append(description)

    # Preserve order while removing duplicates.
    return "; ".join(dict.fromkeys(clean_text(note) for note in notes if note))


def build_bom_rows(footprints: list[dict]) -> list[dict]:
    rows = []
    for fp in footprints:
        if fp["reference"] in BOM_EXCLUDED_REFS:
            continue
        mpn = mpn_of(fp)
        rows.append(
            {
                "Reference": fp["reference"],
                "Value": clean_text(fp["value"]),
                "Footprint": fp["footprint"],
                "Layer": fp["layer"],
                "DNP": "yes" if fp["dnp"] else "no",
                "Manufacturer": manufacturer_of(fp),
                "MPN": mpn,
                "Supplier SKU": supplier_sku_of(fp),
                "Notes": notes_of(fp),
                "missing_mpn": "no" if mpn else "yes",
            }
        )
    rows.sort(
        key=lambda row: (
            row["Value"].lower(),
            row["Footprint"].lower(),
            natural_key(row["Reference"]),
        )
    )
    return rows


def package_name(footprint: str) -> str:
    return footprint.rsplit(":", 1)[-1] if footprint else ""


def build_cpl_rows(footprints: list[dict]) -> list[dict]:
    rows = []
    for fp in footprints:
        if not fp["smd"]:
            continue
        if fp["dnp"] or fp["board_only"] or fp["exclude_from_bom"] or fp["exclude_from_pos"]:
            continue
        layer = "Top" if fp["layer"] == "F.Cu" else "Bottom" if fp["layer"] == "B.Cu" else fp["layer"]
        rows.append(
            {
                "Ref": fp["reference"],
                "Value": clean_text(fp["value"]),
                "Package": package_name(fp["footprint"]),
                "Mid X": f"{fp['x']:.4f}",
                "Mid Y": f"{fp['y']:.4f}",
                "Rotation": f"{fp['rotation'] % 360.0:.2f}",
                "Layer": layer,
            }
        )
    rows.sort(key=lambda row: natural_key(row["Ref"]))
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# hashing / export
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run_command(argv: list[str], purpose: str, log_lines: list[str]) -> dict:
    shell = shlex.join(argv)
    log_lines.append(f"$ {shell}")
    started = time.monotonic()
    proc = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    duration = round(time.monotonic() - started, 3)
    if proc.stdout:
        log_lines.append(proc.stdout.rstrip("\n"))
    if proc.stderr:
        log_lines.append(proc.stderr.rstrip("\n"))
    log_lines.append(f"[exit {proc.returncode} in {duration}s]")
    log_lines.append("")
    record = {
        "purpose": purpose,
        "argv": argv,
        "shell": shell,
        "cwd": ".",
        "exit_code": proc.returncode,
        "duration_s": duration,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {shell}")
    return record


def export_files(board_rel: str, out_rel: str, log_lines: list[str]) -> list[dict]:
    gerbers_rel = f"{out_rel}/gerbers"
    commands = [
        (
            "kicad version",
            [KICAD_WRAPPER, "kicad-cli", "version"],
        ),
        (
            "gerbers (stored board plot settings)",
            [
                KICAD_WRAPPER,
                "kicad-cli",
                "pcb",
                "export",
                "gerbers",
                "--output",
                gerbers_rel,
                "--board-plot-params",
                board_rel,
            ],
        ),
        (
            "drill (Excellon mm, absolute origin, GerberX2 map)",
            [
                KICAD_WRAPPER,
                "kicad-cli",
                "pcb",
                "export",
                "drill",
                "--output",
                gerbers_rel,
                "--format",
                "excellon",
                "--drill-origin",
                "absolute",
                "--excellon-zeros-format",
                "decimal",
                "--excellon-oval-format",
                "alternate",
                "--excellon-units",
                "mm",
                "--generate-map",
                "--map-format",
                "gerberx2",
                board_rel,
            ],
        ),
        (
            "IPC-D-356 netlist",
            [
                KICAD_WRAPPER,
                "kicad-cli",
                "pcb",
                "export",
                "ipcd356",
                "--output",
                f"{out_rel}/maru60.d356",
                board_rel,
            ],
        ),
        (
            "STEP board assembly",
            [
                KICAD_WRAPPER,
                "kicad-cli",
                "pcb",
                "export",
                "step",
                "--output",
                f"{out_rel}/maru60.step",
                "--force",
                board_rel,
            ],
        ),
    ]
    records = []
    for purpose, argv in commands:
        records.append(run_command(argv, purpose, log_lines))
    return records


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------


def check(checks: list[dict], name: str, ok: bool, detail) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def verify_package(
    board_path: Path,
    board_sha: str,
    board: dict,
    bom_rows: list[dict],
    cpl_rows: list[dict],
    out_dir: Path,
    job: dict | None,
    job_path: Path | None,
) -> tuple[list[dict], dict]:
    checks: list[dict] = []
    gerbers_dir = out_dir / "gerbers"

    check(checks, "board_sha256_matches_expected", board_sha == EXPECTED_BOARD_SHA256, {
        "actual": board_sha,
        "expected": EXPECTED_BOARD_SHA256,
    })
    check(checks, "board_sha256_unchanged_after_export", sha256_file(board_path) == board_sha, board_sha)

    layer_gerbers = sorted(gerbers_dir.glob("maru60-*.gbr"))
    # The drill map is also a .gbr; exclude it from the layer count.
    layer_gerbers = [path for path in layer_gerbers if path.name != "maru60-drl_map.gbr"]
    copper_gerbers = [
        path
        for path in layer_gerbers
        if path.name
        in {
            "maru60-F_Cu.gbr",
            "maru60-In1_Cu.gbr",
            "maru60-In2_Cu.gbr",
            "maru60-B_Cu.gbr",
        }
    ]
    all_gbr = sorted(gerbers_dir.glob("*.gbr"))
    drill_files = sorted(gerbers_dir.glob("*.drl"))
    job_files = sorted(gerbers_dir.glob("*.gbrjob"))

    check(checks, "gerber_layer_file_count", len(layer_gerbers) == 11, len(layer_gerbers))
    check(checks, "gerber_copper_layer_count", len(copper_gerbers) == 4, [p.name for p in copper_gerbers])
    check(checks, "gerber_gbr_file_count_including_drill_map", len(all_gbr) == 12, len(all_gbr))
    check(checks, "drill_file_count", len(drill_files) == 1, [p.name for p in drill_files])
    check(checks, "gerber_job_file_count", len(job_files) == 1, [p.name for p in job_files])
    check(checks, "ipc_d356_exists", (out_dir / "maru60.d356").is_file(), "maru60.d356")
    check(checks, "step_exists", (out_dir / "maru60.step").is_file(), "maru60.step")

    check(checks, "bom_row_count", len(bom_rows) == 382, len(bom_rows))
    check(checks, "cpl_row_count", len(cpl_rows) == 370, len(cpl_rows))
    check(checks, "bom_missing_mpn_count", sum(1 for row in bom_rows if row["missing_mpn"] == "yes") == 374, sum(1 for row in bom_rows if row["missing_mpn"] == "yes"))
    check(checks, "bom_dnp_count", sum(1 for row in bom_rows if row["DNP"] == "yes") == 1, sum(1 for row in bom_rows if row["DNP"] == "yes"))

    job_summary = None
    if job is None:
        check(checks, "gerber_job_parsed", False, "missing or unreadable")
    else:
        specs = job.get("GeneralSpecs", {})
        size = specs.get("Size", {})
        job_summary = {
            "path": str(job_path.relative_to(REPO_ROOT)) if job_path else None,
            "layer_number": specs.get("LayerNumber"),
            "size_mm": {"x": size.get("X"), "y": size.get("Y")},
            "finish": specs.get("Finish"),
            "impedance_controlled": specs.get("ImpedanceControlled"),
            "board_thickness_mm": specs.get("BoardThickness"),
            "files_attributes": job.get("FilesAttributes", []),
        }
        check(checks, "gerber_job_layer_number_4", specs.get("LayerNumber") == 4, specs.get("LayerNumber"))
        check(
            checks,
            "gerber_job_size_285_05_x_94_65",
            size.get("X") == 285.05 and size.get("Y") == 94.65,
            {"x": size.get("X"), "y": size.get("Y")},
        )
        check(checks, "gerber_job_finish_enig", specs.get("Finish") == "ENIG", specs.get("Finish"))
        check(
            checks,
            "gerber_job_impedance_controlled",
            specs.get("ImpedanceControlled") is True,
            specs.get("ImpedanceControlled"),
        )
        check(
            checks,
            "gerber_job_board_thickness_1_6",
            specs.get("BoardThickness") == 1.6,
            specs.get("BoardThickness"),
        )
        copper_functions = [
            item
            for item in job.get("FilesAttributes", [])
            if str(item.get("FileFunction", "")).startswith("Copper,")
        ]
        check(checks, "gerber_job_copper_file_count_4", len(copper_functions) == 4, len(copper_functions))

    edge = board.get("edge_extents") or {}
    check(
        checks,
        "edge_cuts_nominal_285_0_x_94_6",
        edge.get("x") == 285.0 and edge.get("y") == 94.6,
        {"x": edge.get("x"), "y": edge.get("y")},
    )
    check(checks, "board_thickness_1_6", board.get("thickness_mm") == 1.6, board.get("thickness_mm"))
    check(checks, "board_finish_enig", board.get("finish") == "ENIG", board.get("finish"))
    check(checks, "board_copper_layer_count_4", len(board.get("copper_layers", [])) == 4, board.get("copper_layers"))

    counts = {
        "footprints": len(board["footprints"]),
        "bom_rows": len(bom_rows),
        "cpl_rows": len(cpl_rows),
        "missing_mpn": sum(1 for row in bom_rows if row["missing_mpn"] == "yes"),
        "dnp": sum(1 for row in bom_rows if row["DNP"] == "yes"),
        "smd": sum(1 for fp in board["footprints"] if fp["smd"]),
        "through_hole": sum(1 for fp in board["footprints"] if fp["through_hole"]),
        "board_only": sum(1 for fp in board["footprints"] if fp["board_only"]),
        "exclude_from_bom": sum(1 for fp in board["footprints"] if fp["exclude_from_bom"]),
        "gerber_layer_files": len(layer_gerbers),
        "gerber_copper_layers": len(copper_gerbers),
        "gerber_gbr_files": len(all_gbr),
        "drill_files": len(drill_files),
    }
    return checks, {"counts": counts, "gerber_job": job_summary}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD, help="frozen .kicad_pcb")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--expected-sha256", default=EXPECTED_BOARD_SHA256)
    parser.add_argument("--skip-export", action="store_true", help="only rebuild BOM/CPL/provenance")
    args = parser.parse_args()

    board_path = args.board.resolve()
    out_dir = args.out.resolve()
    allowed_root = (REPO_ROOT / "pcb/fabrication").resolve()
    if not out_dir.is_relative_to(allowed_root):
        raise SystemExit(f"refusing to write outside {allowed_root}: {out_dir}")
    if not board_path.is_file():
        raise SystemExit(f"board not found: {board_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    board_rel = str(board_path.relative_to(REPO_ROOT))
    out_rel = str(out_dir.relative_to(REPO_ROOT))

    board_sha = sha256_file(board_path)
    if board_sha != args.expected_sha256:
        raise SystemExit(
            f"board SHA256 mismatch: got {board_sha}, expected {args.expected_sha256}"
        )

    board = parse_board(board_path)
    bom_rows = build_bom_rows(board["footprints"])
    cpl_rows = build_cpl_rows(board["footprints"])

    write_csv(
        out_dir / "BOM.csv",
        [
            "Reference",
            "Value",
            "Footprint",
            "Layer",
            "DNP",
            "Manufacturer",
            "MPN",
            "Supplier SKU",
            "Notes",
            "missing_mpn",
        ],
        bom_rows,
    )
    write_csv(
        out_dir / "CPL.csv",
        ["Ref", "Value", "Package", "Mid X", "Mid Y", "Rotation", "Layer"],
        cpl_rows,
    )

    log_lines: list[str] = [
        "Maru60 fabrication export log",
        f"generated_at_utc: {utc_now()}",
        f"board: {board_rel}",
        f"board_sha256: {board_sha}",
        f"output: {out_rel}",
        "",
    ]
    commands: list[dict] = []
    if not args.skip_export:
        gerbers_dir = out_dir / "gerbers"
        if gerbers_dir.exists():
            if not gerbers_dir.resolve().is_relative_to(out_dir):
                raise SystemExit(f"refusing to remove unexpected path: {gerbers_dir}")
            shutil.rmtree(gerbers_dir)
        gerbers_dir.mkdir(parents=True, exist_ok=True)
        for stale in ("maru60.d356", "maru60.step"):
            (out_dir / stale).unlink(missing_ok=True)
        commands = export_files(board_rel, out_rel, log_lines)

    (out_dir / "export.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    job_path = out_dir / "gerbers" / "maru60-job.gbrjob"
    job = None
    if job_path.is_file():
        try:
            job = json.loads(job_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            job = None

    checks, verification = verify_package(
        board_path, board_sha, board, bom_rows, cpl_rows, out_dir, job, job_path
    )
    all_checks_pass = all(item["ok"] for item in checks)

    # Per-file hashes for the manufacturing set.  README.md is included when it
    # exists so a second run after writing the README records its hash too.
    output_paths: list[Path] = [
        out_dir / "BOM.csv",
        out_dir / "CPL.csv",
        out_dir / "export.log",
        out_dir / "maru60.d356",
        out_dir / "maru60.step",
    ]
    if (out_dir / "README.md").is_file():
        output_paths.append(out_dir / "README.md")
    if (out_dir / "gerbers").is_dir():
        output_paths.extend(sorted((out_dir / "gerbers").iterdir()))

    outputs = {}
    for path in output_paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(out_dir))
        outputs[rel] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    if "BOM.csv" in outputs:
        outputs["BOM.csv"]["rows"] = len(bom_rows)
    if "CPL.csv" in outputs:
        outputs["CPL.csv"]["rows"] = len(cpl_rows)

    kicad_version = "unknown"
    for record in commands:
        if record["purpose"] == "kicad version":
            kicad_version = record["stdout_tail"].strip().splitlines()[-1] if record["stdout_tail"].strip() else "unknown"

    provenance = {
        "schema_version": 1,
        "package": "maru60-fabrication-draft",
        "status": "draft_not_manufacturing_release",
        "generated_at_utc": utc_now(),
        "generator": {
            "script": "pcb/tools/export_fabrication.py",
            "python": sys.version.split()[0],
            "kicad_cli": kicad_version,
            "kicad_image": KICAD_IMAGE,
            "board_generator": board.get("generator"),
            "board_generator_version": board.get("generator_version"),
            "board_format_version": board.get("format_version"),
        },
        "source": {
            "board_path": board_rel,
            "board_sha256": board_sha,
            "board_sha256_expected": args.expected_sha256,
            "board_sha256_match": board_sha == args.expected_sha256,
            "board_size_nominal_mm": {"x": 285.0, "y": 94.6},
            "board_size_edge_cuts_mm": {
                "x": (board.get("edge_extents") or {}).get("x"),
                "y": (board.get("edge_extents") or {}).get("y"),
            },
            "board_size_gerber_job_mm": (verification.get("gerber_job") or {}).get("size_mm"),
            "board_thickness_mm": board.get("thickness_mm"),
            "copper_layers": board.get("copper_layers"),
            "copper_layer_count": len(board.get("copper_layers", [])),
            "finish": board.get("finish"),
            "impedance_controlled": (verification.get("gerber_job") or {}).get("impedance_controlled"),
            "impedance_source": "gerber job GeneralSpecs.ImpedanceControlled",
            "footprint_count": len(board["footprints"]),
            "bom_rows": len(bom_rows),
            "cpl_rows": len(cpl_rows),
            "dnp_count": verification["counts"]["dnp"],
            "missing_mpn_count": verification["counts"]["missing_mpn"],
            "smd_count": verification["counts"]["smd"],
            "through_hole_count": verification["counts"]["through_hole"],
            "board_only_count": verification["counts"]["board_only"],
            "exclude_from_bom_count": verification["counts"]["exclude_from_bom"],
        },
        "commands": commands,
        "outputs": outputs,
        "gerber_job": verification.get("gerber_job"),
        "verification": {
            "all_checks_pass": all_checks_pass,
            "checks": checks,
        },
    }
    (out_dir / "PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    verification_doc = {
        "generated_at_utc": utc_now(),
        "provenance_sha256": sha256_file(out_dir / "PROVENANCE.json"),
        "all_checks_pass": all_checks_pass,
        "counts": verification["counts"],
        "gerber_job": verification.get("gerber_job"),
        "checks": checks,
    }
    (out_dir / "VERIFICATION.json").write_text(
        json.dumps(verification_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"board: {board_rel}")
    print(f"board sha256: {board_sha}")
    print(f"BOM rows: {len(bom_rows)} (missing MPN: {verification['counts']['missing_mpn']})")
    print(f"CPL rows: {len(cpl_rows)}")
    print(f"gerber layer files: {verification['counts']['gerber_layer_files']} (copper: {verification['counts']['gerber_copper_layers']})")
    print(f"gerber .gbr files: {verification['counts']['gerber_gbr_files']}")
    print(f"drill files: {verification['counts']['drill_files']}")
    if verification.get("gerber_job"):
        job_summary = verification["gerber_job"]
        print(
            "gerber job: "
            f"{job_summary['layer_number']} layers, "
            f"{job_summary['size_mm']['x']} x {job_summary['size_mm']['y']} mm, "
            f"{job_summary['finish']}, "
            f"impedance={job_summary['impedance_controlled']}"
        )
    print(f"all checks pass: {all_checks_pass}")
    if not all_checks_pass:
        for item in checks:
            if not item["ok"]:
                print(f"FAIL: {item['check']}: {item['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
