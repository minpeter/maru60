# Maru60 housing

The HHKB top case includes the wrist rest; the matching bottom case retains
the stock gasket/catch interfaces. Both remain experimental. Start with the
[top-case printing and downloads](fabrication.md#maru60-hhkb-top-case-with-integrated-wrist-rest-experimental)
and [bottom-case assembly and downloads](fabrication.md#maru60-hhkb-bottom-case-draft),
including the USB bridge support requirement and physical-fit limitations.

## Build and verify together

Run from the repository root after `uv sync --locked`:

```sh
uv run python -m maru60.pipeline --board ph60-rev3
uv run python -m maru60.pipeline --board ph60-rev3 --strike-inserts
uv run python -m maru60.pipeline --board ph60-rev3 --no-battery-bay
```

The pipeline builds and verifies both cases for one board and option set.
Each combination has its own directory under `build/`, so switching boards,
upper strike inserts or lower battery options does not reuse another variant's
working meshes. The default uses original screw pilots and includes the
battery bay. `--strike-inserts` and `--no-battery-bay` can be combined.
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
