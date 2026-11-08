# Independent composed VBUS cleanup review

## Finding and disposition

The VBUS cleanup composes with the GPIO24 trial on the tested hashes. I independently reran source-bound scope, exact annulus coverage, full graph delta and boundary displacement calculations rather than inheriting acceptance. Limited reversible development/prototype selection is supported for this VBUS increment, provided the separate GPIO24 review and semantic open-pair check are satisfied. This is neither production approval nor a claim that exact copper inclusion passed. Strict exact inclusion remains FAILED with explicit raw differences.

Source: header-routing/frozen24move/pcb, SHA256 2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4.
Candidate: combined-trial/pcb, SHA256 56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9.

## Independently recomputed

- Non-zone scope is exactly removed VBUS via 1e6f9b6e and shortened b83f85ff track; no other non-zone form changes. All 57 companion files and zone settings match.
- Full material graph delta is identical to the original VBUS trial: four removed direct edges incident to the retired/trimmed objects, one reduced overlapping track contact, no zone edge additions/removals, and two tiny changed GND zone contacts. Pad inventory, all named-pad partitions and guard failures are exact between this source and this candidate.
- The GND contact shrink remains 0.147260768066 to 0.147260767739 mm² on both internal planes. Exact rational geometry independently proves identical complete annulus coverage: the whole 0.25 mm outer disk is inside each plane, nearest actual boundary >0.702577 mm. Exactly opposite fracture seams are canceled; there is no geometric tolerance. Only the via's own drill intersects its annulus bounding box. Therefore the reported contact reduction is numerical Boolean handling, not material loss.
- The actual changed plane-boundary segment lists are exactly identical to the original VBUS trial, despite the new source. Outside the local retired-via region, exact rational subsegment calculations again bound the changed boundaries by 0.732040059 nm old-to-new and 0.707097144 nm new-to-old. These are computed bounds, not a relaxed threshold.
- Raw fill-only subtraction independently gives 2.2998e-08 mm² loss per plane. The source-bound physical-plane diagnostic is preserved verbatim: 2.50615e-08 mm² loss, 0.4365569049455 mm² gain, one plane component before/after, and no old signal-reference intersections. Its 1 nm erosion diagnostic returns zero loss, but raw loss is not waived or relabeled as zero.
- Stored DRC violation reports differ only by removal of the specified VBUS dangling-via warning. Candidate reports ten opens and fifty warnings. Exact open-item record equality is FALSE, explicitly recorded in scope.json; representative endpoints changed. Semantic component pairs are separately verified in combined-native/open-component-pairs.json. No assertion of exact record equality is made here.

## Interpretation and limits

The removed via served no interlayer connection; the serial 0.3 mm track already covered the trimmed 0.2 mm overlap. Refill has sub-nanometre quantized boundary shifts and an intentionally larger ground region where the obsolete via clearance was removed. The same narrow physical interpretation holds after composition, based on freshly tested evidence. This review does not establish GPIO24 return quality independently or qualify transient, thermal, current-carrying, SI/EMC, manufacturing or reliability performance. Ten unresolved opens alone preclude calling this production-ready.

Evidence: scope.json, full-edge-delta.json, exact-cover.json, independent-local-contact.json, boundary-delta.json, boundary-bound.json, original-plane-diagnostic.json and their reproducible scripts/logs. All source/candidate files were read only. No DRC CLI rerun, install, publication or fabrication action was performed.
