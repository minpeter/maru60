# Independent recovered LED startup-guard review

Verdict: source-bound approval eligible for the disabled recovery candidate. No blocking source defect found. This is not hardware, ARM-build, release, or merge approval.

## Source identity

Candidate 62-file manifest SHA-256: `ab7f168c0f973c5d9447ec305a3973f1b418467af5fa7018c93a26f58b46d500`.

Exact historical active overlay files: 19/22. New files: maru_rgb.c, maru_rgb.h, maru_ws2812_transport.inc.

- `maru_rgb.c` SHA-256: `dcb1acc86789b2a8f919769671dea8c5e2042fb20756cc15a6b2e3304e62ca52`
- `maru_rgb.h` SHA-256: `85403c42339f1777106308a2cc4c537f84a5c84021d4f50ebf406c00fb6a618e`
- `maru_ws2812_transport.inc` SHA-256: `802e09fe8e95b9ce7e149b879e808f7c3ee6d772e244cebea61bb44f83ee3716`
- `config.h` SHA-256: `3923a07e7329edf1bc8f78067b56c8a093dd3f223bba0bc89ed652198bf2235d`

## Checks

- Explicit OFF/SETTLING/ACTIVE flow; each enable epoch stops both chains and stages black before asserting EN; resumes occur only after elapsed interval.
- No production settling interval or report is supplied. Qualification defaults OFF. Qualified compilation requires a nonempty string report and interval 1..2147483647.
- USB-configured false, direct power OFF, both zones OFF and observed fault/readiness/EN failures invalidate the current state. Hardware/transport faults remain latched across USB cycles.
- Direct OFF is intentionally not a persistent user disable: with policy allowed, a later task starts a new full settling epoch. Both zones OFF and unconfigured USB remain inhibited.
- Guards run before each chain, after transport synchronization and immediately before DMA enable; a final post-underglow guard observes failure before returning.
- Source-bound tests exercise default OFF with zero transport callbacks, invalid compile contracts, fault latching, boundaries and negative mutation controls.
- Independent fresh fixture compiles actual maru_rgb.c and maru60.c at O0/O2 under UBSan, with 1/7/2147483647 ms synthetic intervals, wraparound, missing resources, cold and active faults, manual OFF, USB suspend/configure wrappers, EN loss, zone cycles, and shutdown.

## Evidence

- Fresh reproduced suite: 90 startup and 288 transport executions across O0/O2; all passed.
- 7 invalid contracts correctly rejected; seven targeted mutations killed.
- Two fault-at-submit controls intentionally fail, explicitly exposing non-atomic polling.
- 73 independent real-wrapper/state-machine executions passed under UBSan.
- Default OFF produces zero EN epochs, transport calls, and mock DMA submissions.

## Resolved documentation finding

The initial firmware/tests/README.md gave obsolete enable-only build instructions and historical ARM verification without qualification. Reported to implementation owner, who corrected it. Reviewer reread the replacement README, BUILDING.md and top-level README; obsolete instructions and missing links were removed, and limitations are explicit.

## Limits

- The 19/22 statement concerns historical active overlay file bytes, not recovery of the original lost working packet, verifier or logs. Three files are new source.
- Reproduced transport tests compile only source-extracted ws2812_flush, not the full PIO/DMA translation units. Independent tests mock transports, GPIO, USB scheduling and time.
- Expected submit-time fault controls fail by design, proving the polling-to-DMA gap is not atomic. No instantaneous fault-stop or physical cancellation-latency guarantee.
- GPIO EN readback and /FAULT are not rail power-good; no measured settling interval, current/inrush/suspend electrical qualification or signal measurement exists.
- Suspend tests prove actual wrapper calls and invalidation with mocked state notifications, not real QMK USB callback order, IRQ scheduling or host behavior.
- No new pinned QMK/ARM build, full integration verifier, physical USB/hardware/VIA validation, flash, CAD changes, network publication or merge approval was performed.
- Source eligibility applies only to the exact hashes in this report with production qualification OFF, and does not approve enabling, manufacturing, release or merging.

## Reproduction

Run `python3 candidate/run_host_checks.py --output <fresh directory outside candidate>` from the recovery root. Run reviewer fixture `python3 independent/run.py` from a clean copy of this report directory with the same recovery sibling layout; its output directory must not exist.

The independent fixture development false alarm is disclosed in review.json; the raw first attempt is retained.

## Artifact hashes

- `reproduced/results.json`: `23a5b47bc2101d1340258fefa0d61a379c5bac08c30e666d8055393449b97bfc`
- `reproduced/guard/results.json`: `07db6d15d8b6ff26e6150bd4f0128425c338e7723845adf48216bf1b4a0af905`
- `independent/results/results.json`: `624f2f35e2fd7b25762ebe56e8b1c74185099af7af5a937e9815020fe59c85ee`
- `independent/lifecycle_test.c`: `4df9464e66f0c837c6d17935dd9573c27a69f2ee60bf24228ff7186a6fc2b4b7`
- `independent/run.py`: `e48ea322f5f1a2f20041c97f9b1fa957295b8a1f3e504bdc06759703462f5d34`
- `sealed-reproduced/results.json`: `23a5b47bc2101d1340258fefa0d61a379c5bac08c30e666d8055393449b97bfc`
- `final-reproduced/results.json`: `75fcda19d6c91fe613bef174e024442ad9bbb39518aeb6d7f90ad90904756ddf`
