USB PENDANT DEVELOPMENT CHECKPOINT

PCB SHA256: 41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5

Native KiCad 9.0.2: 9 open connection pairs, 38 warnings, no other native errors, ERC 0 and parity 0. Exactly one unused 0.4375 mm F.Cu USB_DM_CONN segment is removed. The active USB path geometry, widths, transitions and pad bindings do not change. This does not claim an SI improvement or active-path shortening.

Independent review confirms the entire PCB serialization is otherwise exact, including all retained primitives, all holes, every zone fill and all remote boundaries. All-hole analysis proves the pendant only attached to its retained via, while both active F/B launch contacts retain positive guarded overlap. Complete physical pads, contact graph and nine open-component pairs are preserved. All 58 CAD files survive cold refill unchanged. No exception window or loss tolerance was used.

All prior checkpoints and the strict geometry baseline remain preserved. Earlier exact-no-loss failure and 51 guarded-contact proof diagnostics remain unresolved. This is immediate-source bounded cleanup, not promotion to strict baseline or a fabrication release. Construction/reviewer reports say unselected because they predate final checkpoint selection; DECISION.json records current status.

Three GPIO25 routing experiments are preserved separately under evidence/rejected-gpio24-via25. Two reached eight native opens but introduced exact remote inner-plane loss; the third failed clearance. None is selected, and no new wiring pair is claimed. Incomplete reference scans are explicitly marked; tiny loss is not waived. Their native-count improvement must not be confused with this checkpoint.

The power supplement checks 13 U18 circuit components and 32 pin assignments against the source PCB and fresh schematic netlist. It documents nominal/component-qualified versus unknown parameters, conditional feedback/soft-start arithmetic and an input-capacitor review flag, with no blind value substitution. A separate stdlib-only replay verifies 519 arithmetic assertions. It does not prove active regulator behavior, stability, effective capacitance or hardware safety. Its PCB provenance intentionally remains the unchanged immediate source hash; the exact copper-removal proof establishes that no power objects or assignments changed in this checkpoint.

Open pcb/maru60.kicad_pro. VERIFY.py uses installed KiCad 9.0.2+dfsg-1 to rerun native DRC, ERC, net identity and cold refill; --material additionally regenerates the graph and checks all contacts and physical open pairs. Original construction/reviewer scripts retain their source-bound paths and inputs. Nested manifests describe their original evidence; the outer delivery manifest is authoritative for delivered bytes.

The preview is native F.Cu/B.Cu geometry at the same viewport and scale, not hardware. No SI/EMI, PDN, active-power, full ARM/QMK, thermal, assembly or production qualification is claimed. LED qualification remains OFF. No external push, order or flashing occurred.
