"""Build locations; legacy scripts retain their original default folders."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def topcase_dir() -> Path:
    return Path(os.environ.get("MARU60_TOPCASE_DIR", ROOT / "topcase-draft")).resolve()


def bottomcase_dir() -> Path:
    return Path(
        os.environ.get("MARU60_BOTTOMCASE_DIR", ROOT / "bottomcase-draft")
    ).resolve()


def variant_dirs(
    board: str,
    *,
    inserts: bool = False,
    strike_inserts: bool = False,
    battery_bay: bool,
    catches: str = "stock",
) -> tuple[Path, Path]:
    use_inserts = inserts or strike_inserts
    if catches == "luban32":
        top_variant = "luban32-canot-inserts" if use_inserts else "luban32"
    else:
        top_variant = "canot-inserts" if use_inserts else "stock"
    bottom_variant = "battery-bay" if battery_bay else "no-battery-bay"
    return (
        ROOT / "build" / board / top_variant / "topcase",
        ROOT / "build" / board / top_variant / bottom_variant / "bottomcase",
    )
