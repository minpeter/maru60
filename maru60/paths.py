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
    board: str, *, strike_inserts: bool, battery_bay: bool
) -> tuple[Path, Path]:
    top_variant = "canot-inserts" if strike_inserts else "stock"
    bottom_variant = "battery-bay" if battery_bay else "no-battery-bay"
    return (
        ROOT / "build" / board / top_variant / "topcase",
        ROOT / "build" / board / top_variant / bottom_variant / "bottomcase",
    )
