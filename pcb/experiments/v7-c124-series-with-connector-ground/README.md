# Local C124 series correction with connector GND stitch

This is the selected experimental development snapshot, not a manufacturing or electrically qualified release. Open `candidate/pcb/maru60.kicad_pro`.

PCB SHA256: 7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401. The preceding GND-only selection aaaf and original c770 are retained in their own units. Frozen D and combined reports retain their original UNSELECTED phase labels; this adoption record records the later, limited working-selection decision.

## Changes and verification

C124 retains nominal 10 nF ±10%, 50 V, now explicitly YAGEO CC0402KRX7R9BB103. R125 is a local 100 Ω ±1% KOA RK73H1ETTP1000F in series with its dV/dt branch. R121 retains 156 kΩ ±0.1%, now explicitly KOA RN73R1ETTP1563B25 0402. Its original selected generic 0603 had no MPN or rating. Footprints, schematic fields and the exact series order were independently checked; no copper bypass exists. The small UVLO/OVLO route changes and source-support bridges preserve all original boundary supports under strengthened 2 nm inclusion checks. No clearance or reference rule was lowered.

The connector GND via from the preceding commit is retained. All 12 saved zone records and every old drill remain exact. Its sole declared physical ground loss is 0.049087681002 mm² per inner plane. All 14 C124 support witnesses, 58 new-reference witnesses, existing net partitions, contact records, ground roots and barrels survive the combination. The independent combined review passes 45 checks and normal cold refill is byte-identical.

Actual native inventory: 9,750 tracks, 919 vias, 383 footprints, 13,185.28691027245 mm track length. DRC: zero hard errors other than 12 inherited expansion opens, 64 warnings. ERC and schematic parity: zero. The 12 open entries are unchanged. Five previous silk/text warnings disappeared; THREE new source-support endpoint warnings remain on GND f58bc791, OVLO cc1282fe and UVLO d4be2091. They are explicitly unresolved. The full ledger retains all 92 baseline warning identities plus these three new records: 31 resolved original, 61 remaining original, three new.

## Electrical decision and limitations

Read `electrical-adoption-risk/BRIEF.md` before treating this as more than a prototype choice. TI recommends the 100 Ω resistor for actual CdVdt >10 nF; applying it to the 9–11 nF tolerance interval is our tolerance-aware inference. It does not fix brownout, prove startup or improve noise universally. Selected-versus-D nominal divider current, threshold and initial tolerance are unchanged. RN73R cannot be called a demonstrated downgrade or equivalent to the selected unspecified resistor. Its looser environmental figures are compared only with the earlier UNSELECTED TNPW proposal under different test conditions.

Input-fault/transient envelope, R120 TCR/tracking, effective C under bias/temperature/aging, R125 repetitive pulse/discharge stress, active eFuse startup/reset/brownout and environmental stability remain unqualified. Passive equations were checked under explicit assumed RLC inputs, not extracted board parasitics. The added GND via can alter USB fields; it does not restore the old neck or establish SI/ESD/EMC improvement. Mechanical/socket/plate/case, assembly/process and hardware qualification remain absent. LED qualification is still OFF, and no full QMK/ARM build, flashing, fabrication or push is implied.

## Preserved evidence

`frozen-combined` contains every byte in the completed 229-file execution map, plus its map. `independent-combined-review` contains the separate 45-check review. `evidence/actual-D-frozen.zip` is the exact standalone D packet, independently reviewed with 223 component and 33 actual checks and its passive-binding packet. The original D backup remains Space libfile_35bcead8bcd881919234a3e0df7792fd. The separate GND archive remains libfile_6e57b31450488191baf5790a6a6ef6dd. Frozen absolute run paths are provenance, not a relocated one-command replay promise. All previous CAD/history is preserved; original lost pre-recovery history is still not restored.
