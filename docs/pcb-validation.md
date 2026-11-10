# PCB validation and evidence boundaries

`pcb/CURRENT.md` describes the selected strict baseline and bounded development prototype; `pcb/current.json` pins their primary CAD files. Neither selection is manufacturing-ready. Keep identity, stored reports, fresh native checks, portable checks and physical qualification separate when reporting results.

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| `uv run tools/check_pcb_current.py` | Current primary project, PCB and root schematic bytes match the manifest | Full CAD dependency identity, fresh ERC/DRC, manufacturing readiness |
| Archived `qa/` reports | Recorded observations for their recorded inputs/tools, after independently verifying those bindings | A fresh replay or acceptance of changed source |
| Fresh KiCad 9.0.2 run | Results of the exact saved invocation against its supplied CAD copy | Hardware operation, regulator stability, firmware behavior or complete qualification |
| Portable wrapper | Active/recovery firmware identity, real host fixtures, stored-netlist GPIO/ideal-matrix checks and recorded arithmetic replay | Fresh netlist export, routed continuity, full QMK/ARM builds or hardware qualification |
| Full QMK/ARM build | Current overlay compiles and links for the recorded layout, source pin, patches, toolchain and configuration | Enabled LED qualification, flashing or physical behavior |
| Physical qualification | Only the measured board, setup, loads, timing and scenarios documented by bench evidence | Untested conditions or automatic manufacturing approval |

## Reproduce portable checks

```sh
uv run tools/check_pcb_portable.py --output /tmp/maru60-portable-new
```

Requirements: `uv`, Python 3.11+ and a C11 compiler (`cc`, or set `CC`). No KiCad, ARM toolchain or third-party Python libraries are needed. The output must not exist. Use an external path or an ignored path under `build/` or `.omo/evidence/`; source directories are rejected.

The wrapper fails on missing inputs, changed primary CAD hashes, mismatched active/candidate firmware, changed pinned checker/power inputs, a changed stored netlist hash, or any child check failure. The 22-file overlay identity is checked before and after execution; the host runner independently checks its recovery and baseline manifests and their preservation. The static checker consumes the active overlay and the selected development prototype's `qa/netlist.xml`. Its hash pin is intentionally fail-closed: a newly exported or changed netlist needs review before updating the pin. Hash equality alone does not prove that a stored export reflects every current CAD dependency.

| Artifact under the output directory | Observable |
| --- | --- |
| `identity.json` | 22 matching active/candidate file hashes; selected manifest/netlist hashes; checker/power input hashes |
| `host.log`, `host/results.json`, `host/guard/results.json` | Child invocation/exit code, fresh host test outcomes, qualification default zero; detailed logs/binaries under `host/` |
| `static.log`, `static.json` | 24 GPIO bindings; rejected wrong GPIO, LED net and duplicate GPIO mutations; ideal matrix results |
| `power.log`, `power/calculation-replay-result.json` | `PASS_ARITHMETIC_ONLY`, 519 checks, 48 feedback corners and eight soft-start corners; copied inputs retained under `power/` |
| `results.json` | Written only after all stages and final input checks succeed; explicit unperformed acceptance categories |

A partial output directory or `identity.json` alone is not a passing run. Inspect the exit code, aggregate result and individual reports. Power arithmetic uses recorded assumptions and nominal components; it does not requalify source values, effective capacitance, startup dynamics, active-loop stability or board load capacity. The matrix model uses ideal forward diodes/digital levels and bounded combinations, not all possible key subsets or physical timing.

## Reproduce native checks separately

Build and inspect the repository's pinned KiCad image:

```sh
docker build -f tools/kicad9.Dockerfile -t maru60-kicad:9.0.2 .
tools/run_kicad9.sh kicad-cli version
tools/run_kicad9.sh python3 tools/check_pcb_native.py --output .omo/evidence/pcb-native-new --material
```

The Dockerfile installs Debian trixie's KiCad `9.0.2+dfsg-1` and the standard footprint/symbol libraries. The launcher uses the calling user's UID/GID, isolated temporary configuration/cache and no container network. Its workspace mount is writable: use disposable CAD copies and explicit fresh output paths when running export, ERC, DRC or zone refill. Preserve schematic dependencies and local libraries in those copies. Missing-library diagnostics are environment failures to resolve, not warnings to suppress. The launcher does not itself run any validation or mark a board accepted.

The native checker defaults to the development prototype and expected open-pair count in `pcb/current.json`. It runs fresh DRC/ERC, exports a netlist, checks board/netlist identity and cold-refills a copied board; `--material` also recomputes the material graph. For an explicit checkpoint, supply both `--checkpoint <checkpoint-directory>` and `--expected-opens <count>`. Inspect `RESULT.json`, `drc.json`, `erc.json`, `net-identity.json` and the logs: matching an expected nonzero open count is a baseline replay, not zero-open routing acceptance.

In-repository output is restricted to `build/` or `.omo/evidence/` and must be new and separate from the checkpoint. Paths supplied to the container launcher are container paths: use repository-relative paths for both input and persistent output. Its private `/tmp` is removed with the container.

For every native result retain the exact command, tool version, input hashes, complete machine-readable report and stderr/stdout. Refill-dependent checks must record both source and filled-board identities. Report warnings and unconnected items alongside errors, and distinguish known baselines from acceptance. A container build or version check is not a native CAD PASS.

## Firmware and hardware acceptance still required

The active source configures GP29 for ROW3, GP28 for COL5, 4 MiB flash, WKL/HHKB layouts and independent 64-key/12-underglow LED chains. Lighting qualification remains zero. See the [firmware overview](../pcb/firmware/README.md) and [full-build requirements](../pcb/experiments/led-startup-recovery/candidate/BUILDING.md).

Fresh full WKL and HHKB builds must use the pinned QMK commit, exact submodules and both hash-guarded patches, with qualification OFF, compiler logs and ELF/UF2 hashes. Historical builds and portable mock compilation do not substitute for this. Official VIA behavior and physical USB, matrix, flash/bootloader, DMA/PIO signals, rail settling/current/inrush, fault response and suspend behavior require their own reproducible evidence. No portable or native check in this workflow authorizes LED enablement or manufacturing.

The [2026-11-09 build packet](../pcb/experiments/resume-20261109-silk-height/qa/qmk-build/RESULT.json) records fresh full WKL `via` and HHKB `via_hhkb` builds of the current 22-file overlay: both compile/link and UF2 generation pass, all six LED translation-unit macro dumps show qualification zero, and ELF/UF2 hashes and complete logs are retained. This supplies the default-OFF full-build evidence required above. See the [checkpoint README](../pcb/experiments/resume-20261109-silk-height/README.md) for replay setup; hardware acceptance remains open.
