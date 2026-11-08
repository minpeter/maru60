# Independent one-via acceptance review

Candidate aaafc033 passes the frozen c770 one-GND-via contract. It is eligible for bounded adoption by the routing coordinator. This reviewer has not selected or edited the source/candidate.

- Actual native via: GND at (17.20, 9.90) mm, diameter 0.50 mm, drill 0.25 mm, intact four-layer barrel. All 1,270 physical holes are included.
- Every original raw object and all saved zone records stay exact. Physical inner-plane copper is not globally unchanged: the actual new drill removes exactly 0.049087681002 mm² from each inner plane, and nothing else. The geometric XOR against source-minus-that-drill is zero. Outer zone material is unchanged.
- Both rooted inner contacts are 0.147260768066 mm², or 0.1472558792225 mm² after independent 2 nm inward guards. All old edge witnesses/barrels and all 382 old material components remain intact. All 247 GND pads plus the new via reach J1.A1.
- All 13,129 current outer conductor/pad shadows have zero new-drill intersection. The frozen original a9 audit binds all 11,905 non-GND outer shadows, including the retired U10 D− shadow. No generic endpoint mask or area allowance is used.
- Independent normal cold refill took 2.47 s and reproduced aaaf byte-for-byte in a private copy. The routing candidate tree stayed unchanged. Native results preserve all full warning/open entries: 66 warnings and 12 raw opens, with zero other hard DRC, ERC or parity findings.

The merged-antipad return neck and the 0.95 mm connector GND stub are unchanged. The new grounded copper can change local USB fields/coupling even though existing signal objects are identical. There is no source-supported parasitic extraction or post-change waveform model for this stitch. Do not claim neck restoration, reduced inductance, improved SI, unchanged physical SI, hardware qualification, or global board completion. Historical coverage is current c770 plus exact original a9, not a restored full historical QA ledger.

Read FINAL_ELIGIBILITY.json together with actual_geometry.json and actual_R2_binding.json. The latter resolves the earlier pending-R2 phase labels in actual_geometry.json. cold_refill_results.json binds the independent refill. All six optimized-Python fail-closed tests passed. The initial cold-refill syntax error occurred before any copy/edit; the slow v0 audit was interrupted and replaced by the equivalent, stricter nominal-contact rejection fast path. Both diagnostics are retained.

Scripts are reproducible with /usr/bin/python3 and the pinned KiCad 9.0.2+dfsg-1 environment. The cold-refill script intentionally requires a fresh output directory. No external data or web claims were needed for this native geometry review.
