# Current V7 experimental working selection

Open `experiments/v7-c124-support-serial-cleanup/candidate/pcb/maru60.kicad_pro`.
PCB SHA256: abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d.

Selected for continued prototype development after separate GND and C124 reviews plus independent combined cross-review. It is not an electrical, manufacturing or hardware release. Previous selected sources and frozen UNSELECTED trial records remain unchanged.

The C124 branch now has a local 100 Ω series resistor; C124 remains nominal 10 nF ±10%, and R121 remains 156 kΩ ±0.1% with an explicitly catalog-supported smaller package. Nominal divider behavior is unchanged. The separate connector GND via is retained. All original source-support patches, reference witnesses and pad partitions survive; the latest serial-leg change has two retired and eight changed incident contact witnesses, with all unrelated contacts and all material component sets preserved. The independent normal cold refill is byte-identical. Inner ground loses only the declared new via drill, 0.049087681002 mm² per plane, outside current and historical signal shadows.

9,750 tracks; 919 vias; 383 footprints; 13,184.45545001526 mm. DRC: 61 warnings, 12 unchanged expansion opens, zero other hard errors. ERC/parity: zero. The three later GND/OVLO/UVLO support-end warnings are now resolved by genuine serial routing of their retained supports. The ledger preserves all95 historical entries:34 resolved and61 remaining. No warning is suppressed. Three main endpoints changed; all fourteen strengthened old supports and actual reference requirements pass. The summed track-length reduction is not a measured impedance or stability improvement.

Read `experiments/v7-c124-series-with-connector-ground/electrical-adoption-risk/BRIEF.md`. Input-fault/transient envelope, R120 TCR/tracking, capacitor bias/aging, repetitive resistor pulse stress, active startup/reset/brownout, environmental stability and actual signal integrity remain unqualified. The GND via does not restore the USB neck or demonstrate SI/ESD improvement. Assembly/socket/plate/case and hardware checks remain open. Twelve expansion nets remain incomplete. No endpoint/clearance waiver was used; the historical BUCK-only 1 nm condition is not extended.

Active firmware is unchanged at `firmware/qmk/keyboards/maru60/rp2350`; LED qualification stays 0. No full pinned QMK/ARM build or flashing. Verify its identity from repo root with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb`. Do not fabricate or push from this record. Original lost history/full historical QA are not restored.
