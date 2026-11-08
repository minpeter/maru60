# New LED startup-guard recovery candidate

This is an **isolated new development candidate**, not an exact restoration of the earlier working firmware, a released binary, or hardware-qualified firmware. The active candidate source is `candidate/firmware/qmk/keyboards/maru60/rp2350` relative to this recovery package. Nothing here changes an external build/deploy target or the selected PCB.

## What was recovered exactly

All 22 baseline keyboard-overlay files from the saved accepted-main archive match the previously recorded baseline SHA-256 values. Eighteen were unchanged by the original fix. `config.h` was reconstructed from retained text and matches the old fixed file's complete SHA-256, giving **19 of 22 exact former working-source files**.

The old complete patch, `maru_rgb.c`, `maru_rgb.h`, `maru_ws2812_transport.inc`, original test fixtures/receipts, 72-file working packet, Git history and 362-file import verifier were not recovered. The three missing source files were **newly implemented and freshly tested** against the exact recovered baseline. Their hashes intentionally differ from the historical target hashes. See `SOURCE-STATUS.json`, `provenance/recovery.json` and the package's `known-source-hashes.json`. Do not reuse old pass counts or old manifests as proof for this candidate.

The recovered baseline is immutable under `baseline-extracted/accepted-main/pcb/firmware/qmk/keyboards/maru60/rp2350`. It preserves the former blocking-startup behavior for comparison, not an enabled-use recommendation.

## Current behavior and limits

`MARU60_LED_POWER_QUALIFIED` defaults to **0**. Neither production settling interval nor qualification-report default is supplied. The new code uses OFF/SETTLING/ACTIVE states, keeps transports stopped and data LOW while settling, sends black first at each enable epoch, rechecks cancellation between resumes and chains, and guards the extracted transport after synchronization and immediately before DMA submission. Observed `/FAULT` LOW and transport-not-ready while non-OFF remain latched across USB reconfiguration. Unexpected EN readback LOW cancels the current epoch without latching; a later allowed task may start a new full settling epoch. Direct OFF is non-latching: an otherwise allowed subsequent task may start a **new** settling interval.

The guard samples state in task context. It is **not atomic** with an asynchronous fault or in-flight DMA, can miss brief pulses, and supplies no maximum cancellation latency. EN readback and `/FAULT` do not measure LED-rail readiness. The tests' **7 ms is synthetic**, not board qualification. Existing synchronization can still wait for its timeout. Timer-wrap tests do not prove behavior after an entire 32-bit-millisecond rollover without service.

## Reproduce from the recovery package root

```sh
python3 candidate/verify_sources.py
python3 candidate/run_host_checks.py --output /tmp/a-fresh-led-recovery-run
```

Requires existing Python and a C11 compiler. Assertions must be enabled. Output must be fresh and outside candidate/baseline source. The runner checks baseline hashes, compiles the actual new `maru_rgb.c` with its actual config, extracts the current `ws2812_flush` body, and compares all source hashes before/after. GPIO, clock, scheduling, conversion, transport lifecycle, register access and DMA are mocked. Both complete transport translation units and QMK/ChibiOS are **not** compiled by these host checks.

Fresh tests cover 45 startup scenarios at two optimization levels (90 executions), 144 transport-boundary cases at two levels (288 executions), default-OFF before/after, seven rejected invalid contracts and seven killed mutations. Two expected assertion failures demonstrate the fault-after-final-poll limitation. These numbers describe the **new fixtures**, even where counts happen to resemble the lost suite. Portable checks cover LED regeneration, power arithmetic, WKL/HHKB options, suspend register model, VIA byte regeneration, historical-main matrix model and patch payload hashes.

Fresh baseline fault/USB-loss injections produce 4/2 attempted flush callbacks after cancellation; corresponding candidate settling cancellation produces zero. These are host API attempts and mocked DMA submissions, not physical wire edges. USB loss during the baseline wait is an injected ordering assumption, not evidence of actual QMK scheduling. Default-OFF remains zero EN transitions/flushes/DMA in both sources.

## Pending acceptance

Full WKL `via` and HHKB `via_hhkb` builds against pinned QMK `431ed9ade0684e98a66eabc949563c3be8f446e8`, exact submodules and both hash-guarded patches remain required, with qualification OFF. Local ARM GCC/QMK CLI and full checkout are absent; no full ARM build was attempted. The QMK metadata labels inherited success statements historical. See BUILDING.md. No download, install, flash, enabled release or production qualification is authorized by these checks.

The selected V7 CAD/repository was not modified. Static mapping to that recovered selected PCB has not been rerun using the lost compatibility verifier. Physical USB, rail/current/inrush/fault/suspend behavior, signals, waveforms and actual board timing remain unqualified.
