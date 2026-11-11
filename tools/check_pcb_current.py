#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# ─── How to run ───
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run: uv run tools/check_pcb_current.py
# ──────────────────
"""Check primary PCB file identity without modifying CAD or running KiCad."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypeAlias

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
ROOT: Final = Path(__file__).resolve().parents[1]
ROLES: Final = ("strict_baseline", "development_prototype", "order_candidate")


@dataclass
class ManifestError(Exception):
    field: str
    reason: str

    def __str__(self) -> str:
        return f"{self.field}: {self.reason}"


@dataclass(frozen=True, slots=True)
class FilePin:
    path: str
    sha256: str


def read_pins(manifest: Path) -> tuple[FilePin, ...]:
    """Parse the manifest's primary-file records at the JSON boundary."""
    data: JsonValue = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ManifestError("schema_version", "expected manifest version 1")
    pins = []
    for role in ROLES:
        entry = data.get(role)
        if not isinstance(entry, dict):
            raise ManifestError(role, "expected a record")
        if entry.get("manufacturing_ready") is not False:
            raise ManifestError(role, "must remain explicitly not manufacturing-ready")
        records = entry.get("files")
        if not isinstance(records, list) or not records:
            raise ManifestError(role, "expected nonempty files")
        for record in records:
            if not isinstance(record, dict):
                raise ManifestError(role, "expected a file record")
            path, digest = record.get("path"), record.get("sha256")
            if not isinstance(path, str) or not path:
                raise ManifestError(role, "expected a nonempty path")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ManifestError(path, "expected a lowercase SHA256 digest")
            pins.append(FilePin(path, digest))
    return tuple(pins)


def main() -> int:
    """Return failure for malformed manifests, escaping paths or changed files."""
    if len(sys.argv) != 1:
        print("Usage: uv run tools/check_pcb_current.py", file=sys.stderr)
        return 2
    try:
        pins = read_pins(ROOT / "pcb/current.json")
        for pin in pins:
            relative = Path(pin.path)
            path = (ROOT / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(ROOT):
                raise ManifestError(pin.path, "path must stay within the repository")
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != pin.sha256:
                raise ManifestError(pin.path, f"SHA256 mismatch: {actual}")
            print(f"OK {pin.path} {actual}")
    except (ManifestError, OSError, ValueError) as error:
        print(f"PCB manifest check failed: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {len(pins)} primary CAD files match; no selection is manufacturing-ready."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
