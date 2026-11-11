# Reproduce the relocated-expansion zero-open result

This checkpoint is a bounded development prototype, **not manufacturing-ready**.
The tracked board is:

```
cb7b5b2941bc0e1c4d0a1d10c6dd694f8cf35c4f35665c342dfb747492e10a5d  pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb
```

The source checkpoint is the preserved seven-open header25/U13 checkpoint:

```
df21164e0a5a5a711c206739d603bb581cc65adda2d5c9ea6472f69ca00018d4  pcb/experiments/resume-20261109-header25-u13-contact-repair/pcb/maru60.kicad_pcb
```

All commands below run from the repository root. Use fresh output directories
under `.omo/evidence/` or `build/`; the published `qa/` files are archived
observations and must not be overwritten.

## Prerequisites

- Docker image `maru60-kicad:9.0.2` (KiCad `9.0.2+dfsg-1`, container Python
  3.13.5). The launcher is `tools/run_kicad9.sh`; it mounts the repository at
  `/workspace`, runs with the caller's UID/GID and no network.
- Repository virtual environment `.venv` (Python 3.14.7) with `shapely 2.2.0`
  / GEOS 3.14.1. Use `.venv/bin/python`, **not** `uv`: the `uv` cache is
  read-only in this environment and the old `uv run --script` shebang on the
  GEOS script fails. The promoted script now uses a plain `python3` shebang and
  the repository venv.
- A C11 compiler (`cc`, here GCC 15.2.0) for the portable host checks.

## 0. Verify the tracked manifest

`SHA256SUMS` is relative to this directory. The two promoted tools are listed
as `../../../pcb/tools/...` and the modified native checker as
`../../../tools/...`, so the manifest still verifies from here:

```sh
cd pcb/experiments/resume-20261109-relocated-expansion-zero-opens
sha256sum -c SHA256SUMS
cd -
```

## 1. Native CAD replay (0 opens, 0 warnings)

```sh
tools/run_kicad9.sh python3 tools/check_pcb_native.py \
  --checkpoint pcb/experiments/resume-20261109-relocated-expansion-zero-opens \
  --expected-opens 0 \
  --expected-warnings 0 \
  --output .omo/evidence/relocated0-native-new \
  --material
```

`--expected-warnings` defaults to 0 and is asserted, not merely recorded. A
nonzero baseline must pass its recorded count explicitly (for example the
strict baseline uses `--expected-opens 11 --expected-warnings 51`). The checker
also records its `command` and `cwd` in `RESULT.json`.

Expected `RESULT.json`:

| Field | Value |
| --- | --- |
| `pass` | `true` |
| `board_sha256` | `cb7b5b29...` |
| `kicad_version` | `9.0.2+dfsg-1` |
| `open_pairs` | `0` |
| `warnings` | `0` |
| `other_errors` | `0` |
| `ERC` | `0` |
| `schematic_parity` | `0` |
| `cold_refill_files_identical` | `58` |
| `source_unchanged` | `true` |
| `material_recomputed` | `true` |

The archived `qa/native/*.log` files record the original container path
`/workspace/.omo/evidence/pcb-routing-20261109/manual/repair2-native/`; the
fresh run writes the same reports to the new output directory. See
`qa/native/COMMAND.txt` for the exact command, tool versions and input hashes.

## 2. Material graph

The native replay above already recomputes the graph with `--material`. To
produce it explicitly:

```sh
mkdir -p .omo/evidence/relocated0-material-new
tools/run_kicad9.sh python3 pcb/tools/export_material_graph.py \
  pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb \
  .omo/evidence/relocated0-material-new/material-graph.json
```

The archived graph is `qa/material-graph.json.gz` (gzip of the same JSON). Its
`source_path` and `seconds` fields record the original run, so a fresh graph is
not byte-identical; compare the material content instead. The audit in step 4
uses the archived graph by default, which is what reproduces the published
`material-comparison.json` byte-for-byte. Expected material comparison:

- pad inventory identical: `true`
- source pad-component splits: `[]`
- merges: 7 nets (`EXT_GPIO25`, `MCU_GPIO3/10/24/25/26/27`), each 2 -> 1
- multi-group nets remaining: `{}`
- unchanged direct contacts checked: `17701`
- missing/reduced direct contacts: `[]`
- retained barrels: `754`; candidate barrels: `910`; all retained records equal by UUID: `true`
- guard failures: `0`
- new empty / multiple-component object layers: `[]` / `[]`

## 3. Portable checks

```sh
.venv/bin/python tools/check_pcb_portable.py \
  --output .omo/evidence/relocated0-portable-new
```

Expected `results.json`: `pass: true`, `active_candidate_files_exact: 22`,
`inputs_unchanged: true`, `qualification_default: 0`. The host stage runs
`pcb/experiments/led-startup-recovery/candidate/firmware/tests/led_contract_test.py`;
that test now invokes the generator with `sys.executable` instead of a bare
`python` (this environment has no `python` on `PATH`). The candidate
`source-manifest.json` hash for that test was refreshed to match the fix
(`db437a2c...` -> `8b409419...`), and `verify_sources.py` passes. The active
copy `pcb/firmware/tests/led_contract_test.py` carries the same fix.

## 4. Native audit (geometry, material comparison, inner planes)

```sh
tools/run_kicad9.sh python3 pcb/tools/audit_relocated_zero_opens.py \
  --candidate-board pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb \
  --candidate-material pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/material-graph.json.gz \
  --out-dir .omo/evidence/relocated0-audit-new
```

The script resolves the repository root from its own location, so it works from
the repository root regardless of the current directory. It writes
`audit-summary.json`, `material-comparison.json`, `routing-scope.json` and the
~80 MB `exact-native-plane-inputs.json` used by step 5.

Expected `audit-summary.json`:

| Field | Value |
| --- | --- |
| `pass` | `true` |
| footprints | `383` total, `363` unchanged electrical, `19` relocated block, `1` silkscreen-only |
| `In1.Cu` area | `23450.8724` -> `23494.2804` mm2 (`+43.4080`) |
| `In2.Cu` area | `23501.3927` -> `23521.9331` mm2 (`+20.5404`) |
| inner-plane islands | `1` -> `1` on both layers |
| min different-net via neck | `0.1512` mm |
| sub-0.15 mm different-net pairs | `0` |
| uncovered outside zone-antipad envelope | `0` |
| `material_graph_pass` | `true` |

The three JSON reports are byte-identical to the published `qa/` copies when
run with the pinned image and the archived material graph.

## 5. Independent GEOS + exact-rational replay

```sh
.venv/bin/python pcb/tools/geos_witness_zero_opens.py \
  --qa-dir .omo/evidence/relocated0-audit-new
```

This reads `exact-native-plane-inputs.json` from step 4 and writes
`geos-audit.json` and `geos-rational-witnesses.json` into the same directory.
The archived copies were produced with shapely 2.1.2 / GEOS 3.13.1; the venv
has shapely 2.2.0 / GEOS 3.14.1. The geometry numbers are identical; only the
engine/shapely strings differ. The fresh `geos-audit.json` also records a
`producer` block (script, argv, cwd, input SHA256) that the archived copy
predates.

Expected numbers:

| Field | Value |
| --- | --- |
| `In1.Cu` outside-window area | `270373826809.79376` nm2 (`0.27037382680979377` mm2) |
| `In2.Cu` outside-window area | `280586640402.9662` nm2 (`0.2805866404029662` mm2) |
| retained-reference lost-support max | `30996010286.46605` nm2 |
| retained-reference lost-support outside windows max | `97070.52395249158` nm2 |
| invalid input polygons | `0` on all four source/candidate layers |
| GEOS parts | `1837` |
| strict Q^2 interior witnesses | `1837` |
| witness area | `550960467212.7601` nm2 (`0.5509604672127602` mm2) |

See `qa/geos-audit-command.txt` for the exact commands, versions and input
hashes.

## 6. Mechanical clearance (3.3 / 3.5 mm)

`qa/mechanical-clearance.json` records the relocated-part positions, the J3
plug corridor, the bottom-case cavity floor and the computed free height, with
the source of each number. The key values are:

- cavity floor `Z_p = 18.20` mm (`build_bottomcase_draft.py:74`, `FLOOR_ZP`);
- PCB top `Z_p = 12.50` mm, PCB bottom `Z_p = 14.10` mm (1.6 mm PCB);
- full gasket travel `0.8` mm;
- free height at rest `18.20 - 14.10 = 4.10` mm;
- free height at full gasket travel `18.20 - 14.10 - 0.80 = 3.30` mm;
- J3 plug-insertion corridor `3.5` mm, bbox `y = 68.175..71.675` mm
  (`relocate_j3.py` `CORRIDOR = 3.5`; README rounds to `68.2..71.7`).

The 3.3 mm is a vertical PCB-to-case gap, not a measured part height; the
3.5 mm is a horizontal plug corridor. Physical fit, actual part height and
gasket compression remain unqualified.

## Review and fabrication tools

These are analysis/export tools, not qualification. Each writes its own report
with explicit limitations.

```sh
# Strict-promotion decision (witness classification + SVG map)
.venv/bin/python pcb/tools/analyze_strict_promotion.py

# Mechanical fit (bottom-case 3MF ray-cast, USB-C notch, 7U stabilizer)
.venv/bin/python pcb/tools/check_mechanical_fit.py

# Power arithmetic (input C, inrush, UVLO/OVLO, soft-start, LED limiter)
.venv/bin/python pcb/tools/analyze_power.py

# Fabrication draft (BOM/CPL + Gerbers/drill/IPC-D-356/STEP + provenance)
.venv/bin/python pcb/tools/export_fabrication.py

# Power transient simulation (eFuse, buck, UVLO/OVLO, LED rail, sequencing)
.venv/bin/python pcb/tools/simulate_power.py

# Thermal simulation (lumped network + 2D board spreading)
.venv/bin/python pcb/tools/simulate_thermal.py

# USB 2.0 SI (D+/D- impedance, PRBS-7 eye, length/ESD sweeps)
.venv/bin/python pcb/tools/simulate_usb_si.py
```

Outputs: `qa/strict-promotion/`, `qa/mechanical-fit/`, `qa/power-review/`,
`qa/power-sim/`, `qa/thermal-sim/`, `qa/usb-si-sim/` and `pcb/fabrication/`.
The analyses are read-only; `export_fabrication.py` writes the fabrication
package and refuses to write outside `pcb/fabrication/`.

## Archived vs fresh outputs

| Artifact | Archived | Fresh |
| --- | --- | --- |
| `qa/native/RESULT.json` | no `command`/`cwd`/expected fields | records `command`, `cwd`, `expected_open_pairs`, `expected_warnings` |
| `qa/geos-audit.json` | GEOS 3.13.1 / shapely 2.1.2, no producer | GEOS 3.14.1 / shapely 2.2.0, adds `producer` |
| `qa/audit-summary.json`, `material-comparison.json`, `routing-scope.json` | pinned | byte-identical with the pinned image and archived graph |
| `qa/geos-rational-witnesses.json` | pinned | identical witnesses and numbers |

## Remaining gaps

- Physical bottom-case clearance, actual J3/U13 part height, gasket
  compression, active power, USB SI/EMI, thermal and hardware qualification
  remain open. The 3.3/3.5 mm artifact records design geometry only.
- The archived `qa/native/*.log` and `qa/geos-audit.json` still carry the
  original `/workspace/.omo/...` paths and the older tool versions; the
  `COMMAND.txt` files and this document are the tracked provenance for them.
- The archived `qa/` files are not rewritten by this reproduction; fresh runs
  go to new directories.
