# Maru60 housing

The HHKB top case includes the wrist rest.

The owner designated **v7.15 / 6095-trimode / stock catches / inserts** as
**physical build 02** on 2026-11-13. Its frozen print pair, changes and validation
are in the [physical build record](print-history.md). Use both v7.15 halves:
the main split and its three joints moved 2.9 mm, so older halves do not mate.

The code serves two product lines, both experimental:

| Line | Parts printed | Mates with | Options |
| --- | --- | --- | --- |
| [Stock-compatible](#stock-compatible-top-case) | Top case only | Stock Rule 60 V3 bottom case, ball catches and strikes, gasket plate, caps and PCB | `--board`, `--inserts` |
| [Maru set](#maru-set) | Top and bottom case | Each other, with stock or compatible LUBAN 32 mm catches, self-tapping pilots or CANOT inserts, weight plate, battery or wired | `--board`, `--no-battery-bay`, `--catches {stock,luban32}`, `--inserts` |

Start with the
[top-case printing and downloads](fabrication.md#maru60-hhkb-top-case-with-integrated-wrist-rest-experimental)
and [bottom-case assembly and downloads](fabrication.md#maru60-hhkb-bottom-case-draft),
including the USB bridge support requirement and physical-fit limitations.
What each line still needs measured is listed in
[still to measure](../evidence/topcase/README.md#still-to-measure).

## Stock-compatible top case

The default top case keeps every stock interface: the bottom-case pocket copies
the caliper-measured stock top case, the strike pockets take the stock strikes
on their 13 mm M2 pilots, and the gasket pockets take the stock plate and caps.
Print only the top case and reuse the stock bottom case. `--board` moves the
USB-C notch in the right half; `--inserts` (alias `--strike-inserts`) switches
the 8 M2 self-tapping pilots per case to CANOT M2 OD3.5 x L3 heat-set insert
bores while keeping the stock contour and strike layout. For a 6095 tri-mode PCB, print
`models/maru60-hhkb-topcase-left.3mf` and
`models/maru60-hhkb-topcase-right-usb-6095-trimode.3mf`.

```sh
uv run python -m maru60.pipeline --board 6095-trimode
uv run python -m maru60.pipeline --board 6095-trimode --inserts
```

The pipeline also builds the matching Maru bottom case; the top case it
verifies against the stock bottom-case pocket is the stock-compatible part.

## Maru set

The Maru bottom case pairs with the top case and owns everything below the rim:
battery bay or wired floor, weight-plate recess and the chosen catch hardware.
The wired case (`--no-battery-bay`) is the current one. The battery-bay case is
on hold and not reviewed for printing: building it prints a warning.

```sh
uv run python -m maru60.pipeline --board ph60-rev3 --no-battery-bay
uv run python -m maru60.pipeline --board ph60-rev3 --no-battery-bay --inserts
uv run python -m maru60.pipeline --board ph60-rev3 --no-battery-bay --catches luban32
uv run python -m maru60.pipeline --board ph60-rev3 --no-battery-bay --catches luban32 --inserts
```

Both `--catches stock` and `--catches luban32` default to M2 self-tapping screw
pilots (`Ø1.8 mm` in the top case, `Ø1.7 mm` in the bottom case), and both accept
`--inserts` (`CANOT M2 OD3.5 x L3` heat-set insert bores, `Ø3.2 x 3.55 mm` on
`stock` and `Ø3.2 x 3.20 mm` on `luban32`, in both cases). `--catches luban32`
fits the compatible LUBAN 32 mm double ball catches (25 mm body / 11 mm strike
pitch, 11 mm engaged height): the strike seat sits 0.55 mm deeper (Zp 5.00), the
catch seat sits at Zp 16.00, the original strike pockets widen inward to the skirt
wall and the back-seam key is 0.8 mm shorter. Its top case no longer fits the stock bottom
case or stock catches: print it only as a Maru set. Only faces hidden inside the assembled housing
change: the bottom-case verifier rebuilds the stock-catch pair and proves that no
changed face looks out of the assembly. **The catch and strike widths (7.2 mm) are
assumed, not measured** (`ball_catch.luban32` in
[`spec/rule60-v3.json`](../spec/rule60-v3.json)): the seller's 8.0 mm is a bounding
box and does not fit beside the gasket plate. Caliper the parts (widest point
near the top of the catch, strike width and thickness, engaged height) before
printing.

## Build and verify together

The pipeline builds and verifies both cases for one board and option set.
Each combination has its own directory under `build/`, so switching boards,
upper strike inserts, catches or lower battery options does not reuse another
variant's working meshes. The default uses original screw pilots and includes
the battery bay. `--strike-inserts` and `--no-battery-bay` can be combined.
Board definitions and measured limitations are in
[`spec/boards.json`](../spec/boards.json) and the
[interface specification](fabrication.md#interface-spec-and-pcb-boards).

The paired workflow accepts boards with a known on-board USB position.
`universal` remains a top-case-only option in the legacy scripts; the bottom-case
PCB gauge requires one concrete board.

Publication is explicit:

```sh
uv run python -m maru60.pipeline --board ph60-rev3 --publish
```

`--publish` refreshes the applicable downloads in `models/` and reports in
`evidence/` after verification. Without it, the pipeline leaves these published
directories alone. The insert option is a dimensional trial, not a physical
qualification; read the [insert installation limitations](fabrication.md#optional-upper-strike-inserts-canot-od35--l3-trial)
before printing or installing hardware.

Run the geometry and workflow regression suite with:

```sh
uv run python -m unittest discover -s tests
```

## Legacy scripts and retained studies

Existing `build_topcase_draft.py`, `verify_topcase.py`, `export_topcase.py`,
`build_bottomcase_draft.py`, `verify_bottomcase.py` and `export_bottomcase.py`
remain compatibility entrypoints. Their default working directories are
`topcase-draft/` and `bottomcase-draft/`, each containing the latest selected
variant. Build matching cases and verify again after changing any option;
the lower verifier depends on the matching upper output. Verification receipts
now include SHA256 hashes of the meshes, reports, source and specifications;
changed inputs or old receipts without hashes require verification again.
`MARU60_TOPCASE_DIR` and `MARU60_BOTTOMCASE_DIR` can select explicit working
directories when driving individual scripts. Legacy export scripts
publish directly. Their exact commands remain in the
[fabrication reference](fabrication.md#reproduce).

The [local insert study](fabrication.md#local-m2-insert-mount-study-not-released)
and [purchased-catch trials](fabrication.md#purchased-32-mm-catches--canot-inserts--separate-local-trial)
retain their separate tooling and limitations. They are not enabled by the
pipeline's upper strike-insert option. The
[HHKB gasket plate](fabrication.md#hhkb-gasket-plate-inkc-drawing) remains a
separate fabrication workflow.

Housing code and derived designs use [CC BY-NC 4.0](../LICENSE-topcase).
Return to the [project overview](../README.md).

## Code and output locations

- `maru60/frames.py` owns shared plate-to-print coordinates.
- `maru60/mesh_io.py` owns mesh conversion, sections and 3MF writing.
- `maru60/provenance.py` binds verification to the files checked.
- `maru60/pipeline.py` runs generation, verification and optional publication.
- `build/<board>/<upper-option>/` holds isolated working outputs and logs;
  published files remain under `models/`, `evidence/` and `images/`.

The pipeline uses POSIX file locks (Linux/macOS) to serialize writers to the same
upper variant and publication destination.
