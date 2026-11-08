# Independent VBUS cleanup review

## Disposition

The cleanup is defensible as a limited engineering cleanup candidate, not as an exact no-copper-loss pass and not as a qualified board. Keep the strict raw-loss gate visibly failed. If selection requires exact set inclusion, keep it unselected; do not quietly increase tolerance to remove a warning. The contact-area blocker is independently disproved as a physical loss. The remaining plane differences are explicit sub-nanometre refill/Boolean boundary effects, with no demonstrated connectivity or return-path regression. Eleven opens and fifty warnings remain; no fabrication release is supported.

## Identity and scope

Source SHA256: 04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99.
Candidate SHA256: 9bcd6e46965ef471309af503ba49d5438fad5b974984dc2485525f52487359f6.
Independent normalized non-zone form comparison finds only via 1e6f9b6e removed and track b83f85ff start shortened from (20.15,12.45) to (20.15,10.95). Zone settings and all 57 companion files are exact. Stored source-bound DRC reports differ only by the named dangling-via warning; all eleven open records are exact. I compared these reports, not reran DRC.

## Contacts and copper

Full graph comparison, not the early-exit material comparator, finds four removed direct edges (all incident to the removed via or trimmed track), one decreased track-overlap edge, zero removed or added zone edges, and exactly two changed zone edges. Both changed zone edges are GND via 30f42945 to the two internal planes. All named-pad partitions and guard-failure records remain exact. The physical serial 0.3 mm leg already existed; deleting its superposed 0.2 mm segment does not narrow the track union. The provided native geometry result has exact track union, zero physical track-union loss, and drill-removal gain. Removed via pads/barrel are intentionally retired, not a retained via connection.

Both reported GND contacts decrease from 0.147260768066 to 0.147260767739 mm² (3.27e-10 mm² each). This is a Boolean arithmetic artifact, not an actual reduced contact. Native Boolean operation order produces inconsistent results including contact greater than the annulus itself. Independent exact integer/rational analysis avoids those Boolean operations: cancel exactly reversed fracture seam edges, perform exact ray crossing, and calculate exact point-to-segment squared distance. Both fills contain the entire 0.25 mm radius disk around this GND via. Nearest actual boundaries are >0.702577 mm away. Only its own 0.125 mm radius drill intersects this via's bounding box. Thus the full identical annulus is covered on both planes. No epsilon or area waiver is used in this proof. See exact-cover.json, exact_cover.py and independent-local-contact.json.

## Plane differences: preserved, not erased

Original provided physical-plane Boolean differences are 2.50615e-08 mm² loss and 0.4365569049455 mm² gain per plane. All losses disappear with the diagnostic 1 nm inward guard; this is not an acceptance threshold. Provided signal-shadow intersection check reports no old signal reference loss and both planes remain one component.

My separate raw-fill subtraction (before drill subtraction) gives 2.2998e-08 mm² loss and 0.436556895138 mm² gain per plane. The difference between these measures reinforces that integer polygon operations themselves contribute rounding. Nevertheless serialized filled-zone boundaries really do have different quantized vertices, including far from the retired via, so exact geometric equality is not claimed.

After canceling exact reverse fracture edges there are 119 removed and 81 added directed boundary segments per plane, mainly different split points along existing boundaries. Outside the explicitly changed local box x=19.5..20.8 mm, y=10.3..11.6 mm, exact rational segment subdivision bounds every changed old segment within 0.732041 nm of a changed new segment, and every changed new segment within 0.707098 nm of a changed old segment. These are calculated upper bounds, not chosen tolerances. This is consistent with refill fracture/split coordinate rounding, not meaningful rerouting. Raw numbers and segment deltas are retained. The local retired-via clearance genuinely adds copper; the tiny local loss component also appears in the provided explicit diagnostics, and was not globally relabeled as zero.

## Limits and reusable method

This establishes nominal geometry/connectivity interpretation only. It is not transient, thermal, current-capacity, SI/EMC, fabrication or reliability qualification. Removing a dangling via also changes its parasitic pad/barrel capacitance and stub; no numerical performance benefit is asserted.

exact_cover.py accepts --source, --candidate, --via, --output. It is valid for a circular via and filled zones on In1/In2; it proves absence of a physical zone boundary inside the annulus and an exact inside sample after canceling only exactly opposed seam edges. Inspect target dimensions/layers and independently account for foreign drills before reusing its conclusion. False means unproved, not necessarily a real loss. It does not prove arbitrary track-shadow preservation. The GPIO24/+4V_LED shadow-loss case has not been reviewed here and cannot inherit the VBUS classification. boundary_bound.py is specific to this VBUS delta and local box; do not apply its scope mask to a different candidate.

Source and candidate files were read only. All new evidence is confined to this review directory.
