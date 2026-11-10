"""Build and verify a housing pair in an isolated variant directory before optional publication."""

import argparse
import fcntl
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import rule60_spec as spec
from maru60.paths import ROOT, variant_dirs
from maru60.provenance import require_verified


@dataclass
class PipelineStepError(RuntimeError):
    script: str
    log: Path
    returncode: int

    def __str__(self) -> str:
        return f"{self.script} failed ({self.returncode}); see {self.log}"


@contextmanager
def build_lock(path: Path) -> Generator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def run_step(
    script: str, args: list[str], directory: Path, environment: dict[str, str]
) -> None:
    log = directory / f"{Path(script).stem}.log"
    print(f"Running {script}; log: {log}", flush=True)
    with log.open("w") as stream:
        result = subprocess.run(
            [sys.executable, str(ROOT / script), *args],
            cwd=ROOT,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        raise PipelineStepError(script, log, result.returncode)


class Options(argparse.Namespace):
    board: str = spec.default_board()
    strike_inserts: bool = False
    catches: str = "stock"
    no_battery_bay: bool = False
    publish: bool = False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--board",
        choices=[
            b
            for b in spec.board_ids()
            if b != spec.UNIVERSAL and spec.usb_centre_plate_x(b) is not None
        ],
        default=spec.default_board(),
    )
    _ = parser.add_argument("--strike-inserts", action="store_true")
    _ = parser.add_argument(
        "--catches",
        choices=["stock", "luban32"],
        default="stock",
        help="ball-catch hardware; luban32 also cuts CANOT insert bores in both cases",
    )
    _ = parser.add_argument("--no-battery-bay", action="store_true")
    _ = parser.add_argument(
        "--publish",
        action="store_true",
        help="refresh models/ and evidence/ after both verifiers pass",
    )
    args = Options()
    _ = parser.parse_args(namespace=args)
    if args.catches == "luban32" and args.strike_inserts:
        parser.error("--catches luban32 already cuts CANOT insert bores; drop --strike-inserts")
    if not args.no_battery_bay:
        print("WARNING: the battery-bay bottom case is on hold and not reviewed for printing; "
              "--no-battery-bay builds the current wired bottom case.", file=sys.stderr)
    top, bottom = variant_dirs(
        args.board,
        strike_inserts=args.strike_inserts,
        battery_bay=not args.no_battery_bay,
        catches=args.catches,
    )
    environment = {
        **os.environ,
        "MARU60_TOPCASE_DIR": str(top),
        "MARU60_BOTTOMCASE_DIR": str(bottom),
    }
    with build_lock(top.parent / ".lock"):
        top.mkdir(parents=True, exist_ok=True)
        bottom.mkdir(parents=True, exist_ok=True)
        catch_options = ["--catches", args.catches]
        top_options = ["--board", args.board, *catch_options] + (
            ["--strike-inserts"] if args.strike_inserts else []
        )
        bottom_options = ["--board", args.board, *catch_options] + (
            ["--no-battery-bay"] if args.no_battery_bay else []
        )
        run_step("build_topcase_draft.py", top_options, top, environment)
        run_step("build_bottomcase_draft.py", bottom_options, bottom, environment)
        run_step("verify_topcase.py", [], top, environment)
        run_step("verify_bottomcase.py", [], bottom, environment)
        require_verified(top)
        require_verified(bottom, (top,))
        if args.publish:
            with build_lock(ROOT / "build" / ".publish.lock"):
                run_step("export_topcase.py", [], top, environment)
                run_step("export_bottomcase.py", [], bottom, environment)
    print(f"Verified housing pair: {top} and {bottom}")


if __name__ == "__main__":
    main()
