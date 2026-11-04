# Current V7 experimental working selection

Open `experiments/v7-c124-series-with-connector-ground/candidate/pcb/maru60.kicad_pro`.
PCB SHA256: 7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401.

Selected for continued prototype development after separate GND and C124 reviews plus independent combined cross-review. It is not an electrical, manufacturing or hardware release. Previous selected sources and frozen UNSELECTED trial records remain unchanged.

The C124 branch now has a local 100 Ω series resistor; C124 remains nominal 10 nF ±10%, and R121 remains 156 kΩ ±0.1% with an explicitly catalog-supported smaller package. Nominal divider behavior is unchanged. The separate connector GND via is retained. All old contacts, source supports, reference witnesses and pad partitions survive; the independent normal cold refill is byte-identical. Inner ground loses only the declared new via drill, 0.049087681002 mm² per plane, outside current and historical signal shadows.

9,750 tracks; 919 vias; 383 footprints; 13,185.28691027245 mm. DRC: 64 warnings, 12 unchanged expansion opens, zero other hard errors. ERC/parity: zero. Five old label warnings disappeared; three new GND/OVLO/UVLO support-end warnings remain unresolved, not suppressed. The ledger preserves 92 original warnings plus the three new entries.

Read the unit's `electrical-adoption-risk/BRIEF.md`. Input-fault/transient envelope, R120 TCR/tracking, capacitor bias/aging, repetitive resistor pulse stress, active startup/reset/brownout, environmental stability and actual signal integrity remain unqualified. The GND via does not restore the USB neck or demonstrate SI/ESD improvement. Assembly/socket/plate/case and hardware checks remain open. Twelve expansion nets remain incomplete. No endpoint/clearance waiver was used; the historical BUCK-only 1 nm condition is not extended.

Active firmware is unchanged at `firmware/qmk/keyboards/maru60/rp2350`; LED qualification stays 0. No full pinned QMK/ARM build or flashing. Verify its identity from repo root with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb`. Do not fabricate or push from this record. Original lost history/full historical QA are not restored.
