# Portable firmware checks

From the repository root:

```sh
uv run tools/check_pcb_portable.py --output /tmp/maru60-portable-new
```

The output must be new and outside source archives. In-repository output is limited to `build/` or `.omo/evidence/`. Requires Python 3.11+ and a C11 compiler (`cc`, or `CC`). All generated files, binaries and logs go to that output directory.

The public wrapper first requires the active 22-file keyboard overlay to match `pcb/experiments/led-startup-recovery/candidate/firmware/qmk/keyboards/maru60/rp2350`, except for the files listed with their own hash in `ACTIVE_DELTAS` (`config.h`, which adds `GPIO_INPUT_PIN_DELAY 120`). The candidate packet itself is unchanged. It invokes that candidate's `run_host_checks.py` with fresh external output. The runner verifies its source manifests and compiles the real recovery driver against host mocks, exercises startup and extracted transport boundaries, and runs LED contracts, power policy, WKL/HHKB options, suspend masks, VIA regeneration, historical matrix and patch-hash checks. Reports and compiler logs are under `host/`; the startup fixture is in the recovery candidate's `tests/startup_guard/`, not this directory.

The wrapper also resolves `development_prototype` in `pcb/current.json`, checks the primary CAD file hashes, and checks the existing `qa/netlist.xml` against a fixed reviewed hash before invoking the static checker with the **active** firmware. `static.json` covers 24 MCU GPIO bindings, three rejected netlist mutations and the ideal WKL/HHKB matrix model. It does not freshly export KiCad or inspect routed connectivity. The power replay runs copied `replay_calculations.py` and `calculations.json` under `power/`; its 519 checks establish arithmetic consistency only.

Do not execute `matrix_simultaneous_model.py` directly: its historical main/BS65 paths and source-tree output assumptions are not current acceptance instructions. The existing runners extract its pure definitions and provide explicit fixtures. Do not run the archived power replay in place, because it writes beside itself.

The recovery startup fixture is new; it does not restore missing historical tests or the lost full integration verifier. GPIO, scheduling, clock, DMA, register and transport lifecycle behavior are mocked. Two deliberately expected assertion failures illustrate the fault-after-final-poll limitation; they are not successful asynchronous-fault qualification. `MARU60_LED_POWER_QUALIFIED` remains **0**. Synthetic enabled fixtures do not qualify a settling interval or justify an enabled hardware build.

Full pinned QMK/ARM WKL and HHKB builds, official VIA application checks and physical hardware acceptance remain separate. See [PCB validation](../../../docs/pcb-validation.md) for evidence boundaries and native tooling.
