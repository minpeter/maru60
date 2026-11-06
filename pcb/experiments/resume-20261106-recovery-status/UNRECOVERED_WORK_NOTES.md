# Historical reconstruction notes, not executable evidence

These details were retained from the prior work report. The corresponding files were not recovered. Hashes below identify reported former artifacts, not bytes verified in this checkout. Do not claim these tests pass from this document. Rebuild and independently rerun before using any result.

## Integrated COL14/GPIO25 experiment

The reported source was selected be51692, with the rejected j2-b2 transition candidate as control. The control PCB is available in the restored GPIO25 supplement and has SHA256 cadbc4b068abd62087c33a712e1bc91c55b7899a3c4dcbeb8a510e49140cf4b5.

- GPIO25 transition positions were (93.925, 40.3) and (98.275, 40.55) mm. The existing GPIO24 via move was (105.8, 37.5) to (105.7, 37.525) mm.
- COL14 original F.Cu segment UUID 9820d4ee-e433-4a88-934a-98eda993e59e was 0.15 mm wide, from (97, 42.5) to (100.2, 39.3) mm. The original start contact was track 18aa8a30-c718-42e9-a8e5-ca9f9459d203; the end contact was via e0a162c7-4808-4fef-941e-0cc34755e5a2.
- Three doglegs used d = 0.20, 0.35, 0.50 mm with points [(97,42.5), (97.2,42.3), (97.2+d,42.3+d), (100+d,39.5+d), (100,39.5), (100.2,39.3)].
- A fourth long-launch path used [(97,42.5), (97.2,42.3), (97.55,42.65), (100.1,40.1), (99.75,39.75), (100.2,39.3)].

Reported former PCB SHA256 values:

- offset-200: fc672d8604e0f28fbb625a5fa01badaa1ea980b911791bba4f8d1ec785bf93fb
- offset-350: 1c067cfc90ebbd94c198fe7e1c22ef578103af73ed32860bab5e8a998909c3a3
- offset-500: 65e10052a3706322219f581b70bee5abb21a1e367c92aa2626f110de09759a78
- offset-350-long-launch: 987c6af7620eaf02c0733cd7c5807546bef8875b8e02a020f961623d78c7a745

The reported native result was 8 opens, unchanged 38 warning records and parity 0 for all four. All four were rejected: In1/In2 filled contour serializations remained identical to the rejected control, so the remote GND-loss counterexamples remained. A local projected-gap diagnostic, including the small long-launch diagnostic, did not constitute a local zero-loss or all-hole contact proof. Full material/contact acceptance, cold-refill, ERC and net-identity acceptance were not completed after decisive rejection. None was selected.

## Low-voltage host test plan previously reported as executed

The former harness reportedly copied eight exact selected firmware files: maru_rgb.c, maru_rgb.h, maru_rgb_policy.h, maru_layout_policy.h, maru_led_counts.h, config.h, maru_ws2812_transport.inc and maru_via_schema.h. It used seven mock headers from the existing led-startup-recovery startup_guard tests: wait.h, color.h, timer.h, rgb_matrix_drivers.h, quantum.h, via_eeprom_schema.h and report_sync.h.

It reportedly compiled the actual maru_rgb.c plus an extracted ws2812_flush body using a C11 host compiler at O0 and O2 with warnings as errors. Temporary test-only definitions enabled MARU60_LED_POWER_QUALIFIED=1, MARU60_LED_POWER_SETTLE_MS=7 and a SYNTHETIC-HOST-ONLY-NOT-QUALIFICATION report string. The real selected firmware default remained qualification=0. Do not enable that flag in production to recreate a host-only test.

The scenario matrix was seven enabled cases (invisible, delayed_fault, fault, usb, transport, enable, off), two phases (settling, active) and two optimization levels: 28 scenarios, plus two default-off cases. Eight instances were explicitly expected observability-limit reproductions, not safety passes. A harness-only external_rail_disturbed label did not enter any firmware input or GPIO mock; unchanged actual inputs therefore could not establish a new power epoch. The delayed-fault case introduced an observable fault only later. Fault/transport loss reportedly latched off; USB/enable/off events reportedly required a new settling interval and a black first frame. Each scenario ran in a fresh process.

Two temporary mutation controls reportedly removed fault latching or ignored USB deconfiguration, and were detected by failing assertions. The reported relocated replay compared all 30 trace objects, with former results SHA256 27f829ce26d30860fba49bf500f1b4739c91c9f512557d6f80bc2528508e5fca.

These were software-observability tests. They did not simulate analog rail voltage, regulator dynamics, current, real fault latency, MCU reset/BOR, real PIO/DMA, a full ARM/QMK build, thermal behavior or physical brownout. Mock time was not physical latency. The proposed bench template had no qualified numerical limits or measured waveforms. No firmware was flashed. The absent harness and results must be reconstructed and replayed before citing them as available evidence.

## Next experiment boundary

Do not repeat small GPIO25 site offsets as if the remote return-plane problem were resolved. A different transition topology must be checked with exact source/candidate boundaries and physical drill exclusions. For low-voltage recovery, investigate observable rail supervision and safe LED power gating, but do not tie push-pull outputs together or assume a combinational gate cannot oscillate when turning a load switch off clears its own fault. No proposed protection circuit was selected or implemented in the recovered source.
