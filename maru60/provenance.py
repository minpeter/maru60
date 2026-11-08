"""Bind a verification receipt to the exact files checked, including its mating gauge."""

import json
from dataclasses import dataclass
from hashlib import file_digest
from pathlib import Path

from maru60.paths import ROOT


@dataclass
class UnverifiedBuildError(RuntimeError):
    directory: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.directory}: {self.reason}; rebuild and rerun verification before exporting"


def input_fingerprint(
    directory: Path, dependencies: tuple[Path, ...] = ()
) -> dict[str, str]:
    if not __debug__:
        raise UnverifiedBuildError(
            directory, "Python optimization disables geometry assertions"
        )
    files: dict[str, Path] = {}
    for label, folder in [
        ("build", directory),
        *[(f"dependency-{i}", p) for i, p in enumerate(dependencies)],
    ]:
        files[f"{label}/draft-report.json"] = folder / "draft-report.json"
        for path in folder.iterdir():
            if path.suffix in {".stl", ".3mf"}:
                files[f"{label}/{path.name}"] = path
    sources = [
        ROOT / name
        for name in (
            "build_topcase_draft.py",
            "build_bottomcase_draft.py",
            "verify_topcase.py",
            "verify_bottomcase.py",
            "rule60_spec.py",
        )
    ]
    sources += list((ROOT / "maru60").glob("*.py")) + list(
        (ROOT / "spec").glob("*.json")
    )
    files.update({str(p.relative_to(ROOT)): p for p in sources})
    result: dict[str, str] = {}
    for name, path in sorted(files.items()):
        with path.open("rb") as stream:
            result[name] = file_digest(stream, "sha256").hexdigest()
    return result


def ensure_inputs_unchanged(
    directory: Path, expected: dict[str, str], dependencies: tuple[Path, ...] = ()
) -> None:
    if input_fingerprint(directory, dependencies) != expected:
        raise UnverifiedBuildError(directory, "verification inputs have changed")


def require_verified(directory: Path, dependencies: tuple[Path, ...] = ()) -> None:
    receipt = directory / "verification.json"
    if not receipt.is_file():
        raise UnverifiedBuildError(directory, "no verification receipt")
    data: object = json.loads(receipt.read_text())
    if not isinstance(data, dict):
        raise UnverifiedBuildError(directory, "invalid verification receipt")
    if data.get("status") != "ALL_PASSED" or data.get(
        "input_sha256"
    ) != input_fingerprint(directory, dependencies):
        raise UnverifiedBuildError(
            directory, "missing or stale verification fingerprint"
        )
