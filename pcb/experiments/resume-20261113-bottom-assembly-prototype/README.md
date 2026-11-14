# Bottom-assembly prototype — routed engineering candidate

**Not for fabrication.** This is a separate design experiment. The validated MCU-near-USB candidate remains unchanged; none of its QA results qualifies this redesign.

The latest user decision is to retain **all existing Caps Lock, Right Shift and Backspace layout options**. No switch, stabilizer, socket or mounting-hole pattern is removed. Obstructed emitters move to peripheral positions; these positions do not promise direct illumination through the switch LED window.

The selected default assembly is now **[no expansion port](assembly/no-expansion/README.md)**, authorized by the user on 2026-11-14. J3 and 18 dedicated components are omitted from the candidate BOM and both Backspace placement lists; 319 bottom-side components and 50 part numbers remain. The PCB copper/lands are unchanged. A separate firmware overlay parks the six unused GPIOs LOW; WKL and HHKB full ARM builds pass with RGB qualification still zero. This is an engineering assembly variant, not an order release.

## Implemented

- All 64 key-chain LEDs converted to reverse-mounted SK6812MINI-E-012, LCSC C5149201, using the pinned 2025-11-22 sheet: **1 GND, 2 DIN, 3 VDD, 4 DOUT**. Twelve outward underglow LEDs retain SK6805-EC15-001.
- 66 real rounded internal Edge.Cuts windows (4.0 × 3.6 mm, R0.5); LED14/15 each retain two exclusive Backspace population sites. Fit **one LED per reference**, never both sites of a reference.
- All top SMT moved to B.Cu; 86 passives/diodes moved in total, including displaced bottom parts. Test pads and user-installed switches remain on the switch face.
- All 261 electrically and mechanically unchanged footprints were compared with the baseline; LOGO1 and reference labels were intentionally relocated. The 67 footprints carrying switch/stabilizer/mounting/drilled geometry remain identical. USB data, QSPI, crystal and VREG copper are preserved. This excludes moved UVLO/OVLO control-resistor wiring.
- New library symbol, footprints and schematic pin conversion. ERC: 0; schematic-to-PCB parity: 0 on the routed candidate.
- Geometry export now includes footprint Edge.Cuts and native board-material holes. Local routing and material-connectivity analysis preserve internal apertures.

## Checked routing and remaining qualification

All functional routes and obsolete track stubs are resolved. A fresh cold refill passes native DRC with **0 violations, 0 unconnected items, and 0 schematic parity issues**. `evidence/latest-status.json` identifies the checked board, and `evidence/verification-manifest.json` binds reports and analysis tools to their input hashes. Historical placement and rejected pruning reports do not describe the current board.

The independent material graph clips copper against all 66 windows and every through drill, and connects all pads on each of the **274 named nets** using accepted positive contacts. Its 7,776 guard-rejected contact candidates remain excluded; other proved paths provide connectivity. This does not promote the candidate to a strict baseline. Nineteen focused regression tests pass.

The final preservation check compares 261 unchanged footprints and all 67 mechanical/drilled footprints. It also confirms unchanged USB data, QSPI, crystal, VREG and +1V1 physical tracks/vias, 64 reverse LEDs, 66 windows, both exclusive Backspace population sites, and zero top SMT.

Three local GND zones restore the original 0.20 mm fill behavior beneath USB and QSPI, while the rest of the inner planes retain the 0.30 mm minimum used to remove thin bridges. The baseline-supported critical centerlines retain their adjacent ground support at KiCad's 1 nm coordinate resolution. Raw numerical differences and lost corridor area are retained in `evidence/critical-return-planes.json`; this is a geometry screen, not electromagnetic qualification.

Internal VBUS_FUSED tracks are now 0.90 mm and VBUS_PROTECTED_RAW tracks 0.80 mm, with detours around nearby signal vias and switch drills. The corrected supply-path DC model checks all four LED14/15 population combinations. It preserves holes in pours and recognizes pad-edge/track-body contacts. No modeled supply segment exceeds the empirical IPC-2221 10 °C screen at the stated loads, including 500 mA USB paths. This does not qualify actual temperature or ground-return impedance.

The mixed 64-key/12-underglow LED chain and eight alternate-site hop cases are extracted using each part's actual pinout. The old LED analog simulator deliberately rejects this candidate: its legacy LED thresholds and outer-layer line models do not qualify the new parts and inner-layer routes.

The two alternate LED14 lands have been shifted 0.01 mm outward; their revised footprint is saved in the candidate library. Silkscreen labels and LOGO1 were relocated visibly. Thin ground-pour bridges were refilled with a 0.25 mm minimum on the affected F.Cu zone and 0.30 mm on the inner planes; the UG_LED_6 corner was repaired. The final routing passes the same native rules without waived violations.

The custom reverse-LED lands have 0.30 mm nominal copper-to-cutout clearance; other copper retains 0.50 mm. Land toes were shifted outward, giving about 0.64 mm nominal lead overlap. Milling tolerance, minimum lead overlap, paste/feeding orientation, MSL5a handling and reverse placement need assembler qualification. The window is deliberately larger than the user's approximate 4 × 2 mm reference because this selected LED body is 3.2 × 2.8 mm.

Nominal emitter intrusion is approximately 0.94 mm from the land plane versus 1.6 mm PCB thickness. This is a dimensional screen, not a measured guarantee of flushness. Switch housing, solder seating and tolerances remain physical checks.

This part is **12 mA/channel**, not a sourced 5 mA part. Existing conservative brightness/PWM limits and the unqualified-power firmware interlock remain unchanged. Typical-idle arithmetic is not a worst-case current proof. At RGB code 5 on all 64 key LEDs, an aligned-PWM sensitivity case reaches 2.784 A for about 19.6 µs at the specified typical 1 kHz PWM frequency. The ideal capacitor-only screen already needs about 256 µF for 0.2 V droop against a 174 mA source, before ESR, bias and wiring losses. Existing C121 (4.7 µF nominal) plus bypass capacitors do not establish adequate pulse support. Power/transient design and physical qualification remain unresolved; do not enable RGB power or raise its limit on this evidence.

The candidate is not promoted in `pcb/current.json`, exported as an order package, committed, pushed or merged.

## Simulation campaign — 2026-11-14

[Full report](evidence/simulation-suite-20261114/REPORT.md) and [result summary](evidence/simulation-suite-20261114/summary.json) cover 30 power SPICE conditions, 810 mixed-LED conditions, full first hops and crosstalk, 1,620 PWM charge conditions, 360 thermal cases, USB/matrix/crystal, and current-netlist firmware checks. Twenty-one focused simulation regressions pass. The PCB hash is unchanged.

The campaign **does not qualify LED operation**. With synchronized 64-key RGB code 5 at 1 kHz, the existing assumed 8.9 µF falls below the reverse LED's 3.7 V minimum after about 0.92 µs of a 19.61 µs on-time. Initial fast-driver signal checks flag 37 cases; 35 remain at tighter time steps and two are numerically sensitive. Two full first-hop buffer cases also retain threshold recrossings. USB delay is 0.4184 ns after correcting the route extractor and edge measurement. Firmware RGB qualification remains zero.

The prior `evidence/verification-manifest.json` is a historical snapshot. The simulation tools have since changed; the new [simulation manifest](evidence/simulation-suite-20261114/manifest.json) separately pins the code, results and raw artifact inventory. Neither snapshot implies manufacturing release.

## Cost target review — 2026-11-14

The user target is **five fully assembled boards at about KRW 50,000 each**, including Korea shipping and taxes, excluding sockets, switches and enclosure hardware. The [cost policy](design/cost-policy.json) and [cost review](evidence/cost-review-20261114/REPORT.md) preserve layout options, bottom-side assembly, both RGB functions and required protections.

The historical cost review covers the fully populated 56-part-number configuration: five-board parts total $153.1206 including published attrition. The subsequently selected [no-expansion assembly](assembly/no-expansion/summary.json) has 50 part numbers and $132.3270 in parts. Parts plus Standard setup/stencil/feeders decrease from about KRW 419,759 to KRW 373,599 at the stated exchange/tax assumptions, before fabrication, assembly labor or shipping. Both installed LED types remain Standard Only. Further assembly and architecture changes are required to reach the target. The original CAD and root production order package are unchanged; use the explicitly selected assembly policy for this candidate.

## Inputs and reproduction

- `design/source.json`: pinned validated baseline.
- `design/layout-policy.json`: final user choice.
- `design/led-part.json`, `supplier/`: part facts and pinned source material.
- `design/bottom-assembly-plan.json`, `design/passive-ops.json`: mechanical placement and exact native pad checks.
- `design/copper-clearance-ops.json`: every deliberately removed conductor, with reason.
- `evidence/final-erc.json`, `evidence/final-cold-drc.json`, `evidence/latest-status.json`: routed native diagnostics; **not fabrication qualification**.
- `evidence/final-invariants.json`: preservation checks on the final geometry; rerun after further edits.
- `evidence/final-material-graph.json`: cutout- and drill-aware positive-copper connectivity, with every unproved contact explicitly excluded.
- `evidence/pdn/`: four exclusive LED population DC cases.
- `evidence/signal-integrity/`: extracted routes and explicitly scoped USB/crystal computations.
- `REPRODUCE.md`: commands and acceptance conditions for this exact candidate.
- `evidence/window-material-web-screen.json`: minimum nominal window-to-drill web 0.581 mm (Right Shift), window-to-outline 2.273 mm, between windows 4.218 mm. Fabrication tolerances and strength are not qualified.

Tools are in `pcb/tools/`: `plan_bottom_assembly.py`, `apply_reverse_led_candidate.py`, `plan_bottom_passives.py`, `clear_reverse_led_copper.py`, `export_fixed_dsn.py`, `prepare_bottom_assembly_dsn.py`. Shapely planning uses `.venv/bin/python`; native CAD uses `tools/run_kicad9.sh python3`.

## Continuing and verifying the checked board

The saved PCB is the working CAD source. `apply_reverse_led_candidate.py --reset-board` starts again from the baseline and discards later routing; it is not a replay of this snapshot. Operation files record the edits and routing attempts; native-created item UUIDs are tied to their historical snapshots.

Use `tools/run_kicad9.sh` for `kicad-cli pcb drc --format json --schematic-parity`, `dump_board_geometry.py`, `export_connection_components.py` and `export_material_graph.py`. The component exporter guides route search; cutout-aware material connectivity is the independent electrical check. Use `.venv/bin/python` for `route_bottom_open_pairs.py`, `plan_pad_escape_vias.py` and `verify_bottom_assembly_invariants.py`. Every applied route or rip-up requires new DRC and component exports. The checked candidate has no dangling vias or tracks.

Regression checks: `tools/run_kicad9.sh python3 tests/test_board_cutout_material.py` and `.venv/bin/python tests/test_local_router_cutouts.py`.
