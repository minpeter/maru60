# C124 short local circuit experiment, 2026-11-04

**UNSELECTED. No procurement, hardware, mechanical, assembly or production qualification.**

The complete small local circuit is now constructed and independently checked. It uses ordinary0402 R125/C124 and proposed0603 R121, short local tracks, no new drills, and an explicitly expanded UVLO/OVLO contact contract. It avoids the rejected20 mm/five-via alternative. Accepted artwork is preserved in a separate successor.

## Review first

- `isolated-v4-label-carry/RESULT.md`: latest unselected successor **ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7**, carrying accepted2c7 labels/LOGO. Fresh DRC0 hard beyond12 existing opens,64 warnings,0 parity issues. Copper/fills are identical to the fully checked8c45 trial.
- `isolated-v4/RESULT.md`: immutable constructed/refilled **8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6**, full contact/reference/all-net/ERC/netlist evidence and precise limits.
- `r121-expanded-review/actual/REVIEW_ACTUAL.md` and `r121-expanded-review/carry-addendum/ADDENDUM.md`: separate independent actual geometry/contact/reference and accepted-artwork carry reviews.
- `isolated-v4/qa/local-top-bottom-unselected.png`: local native geometry of8c45; actual electrical geometry is identical inec4873. Bottom copper is shown in the same X/Y orientation, so back-side ink is mirrored.

## Decision facts

Exactly31 named old tracks are replaced by21 new tracks; no via/drill change. All10,640 retained track/via records and all12 complete filled-zone records are byte-identical to source. Every old reference shadow remains protected. The only changed pad partitions are the intended USB_DVDT→R125→USB_DVDT_CAP split; GND, UVLO, OVLO and all unrelated nets retain their partitions. Native/reference measurements and independent checks use actual pads, paste/mask, annular copper, source planes and full original contact-support regions.

Pin-side track1.660404265 mm, capacitor-side1.103279203 mm, ground return0.699231721 mm. UVLO becomes0.894932120 mm longer and the OVLO arm1.410519448 mm longer. These are explicit high-impedance routing tradeoffs, not silently unchanged nets. Proposed100Ω×10nF adds a nominal1µs RC; analog/reset/noise and actual distributed parasitics are not qualified.

One new native track_dangling warning remains on the deliberately preserved ground-support tail. Actual physical overlap and roots are positive; the warning is not deleted or waived. Existing12 expansion opens remain, and one8c45 ratsnest target choice changes within the same unchanged component; the full disposition is included. Current exact Murata approval-sheet access and actual socket/plate/terminal mechanical registration remain limitations. Proposed BOMs are not procurement selections.

## Sources, lineage and reproducibility

`source-selected-7c23/pcb` contains the exact53-file construction source. `source-accepted-2c7` contains the later accepted board and automatically generated local editor state; the52 companion design files are identical to7c23. `selected-label-source-tree-proof.json` records the complete relationship. Neither selected source was edited.

`EXPANDED_V4_PLAN.md`, `CONTACT_LEDGER.md`, `PLAN_MANIFEST.json` record the reviewed scope and manufacturer/assembly assumptions. Earlier50µm and tiny-margin R121 rejections are preserved, not converted into passes. The invalid first serialization and its corrections are preserved under `ACTUAL_LINEAGE.json`; do not use the original BUILD_CONTRACT prefill hash as the validated board identity.

The archive includes exact input/output files, scripts, native logs and independently generated results. Execution paths in scripts/logs identify the original isolated directories. Some scripts contain these original absolute paths; this is evidence preservation, not a claimed relocated one-command replay. KiCad9.0.2+dfsg-1 and separate private XDG directories were used. The full old historical routing harness is not claimed recovered.

The separately sealed analog review/binding archives are not duplicated here; their verified paths and hashes are recorded in the result and were sent for durable preservation. No selected-repository edit, Git push, fabrication or flashing occurred.
