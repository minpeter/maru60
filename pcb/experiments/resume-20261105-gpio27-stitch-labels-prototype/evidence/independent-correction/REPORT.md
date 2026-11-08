# Independent review: corrective combined27fix2

Exact candidate: 9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed.
The held b1e3 candidate and its HOLD report remain preserved. This review does not use the rejected first combined27fix scripting attempt.

## Recommendation

The specifically identified GPIO26 departure-reference defect is corrected without enlarging transition windows or applying a numerical tolerance. Completed independent checks support selection as a qualified, reversible development checkpoint. The complete full-board rerun and strict post-run assertions now pass, and the main exact-candidate cold/ERC/net-identity evidence was reviewed. No fabrication, SI/EMI, active-power, or assembled-hardware acceptance is implied.

## Completed independent checks

1. Raw parsed scope is exactly one changed endpoint on track55e5d0cf-c179-4e88-925d-241a5a9d4416 plus one new 0.15 mm F.Cu trackadb09d04-e93c-4f35-bbef-200d2bb1eb64. Retained segment ends at (95.765,40.815), then the new segment runs to (96.65,41.625). It is nonzero length. Restoring the one old object and removing the addition reconstructs the held board exactly. All zone fills and 57 companion project files are byte/parsed identical as applicable.
2. Exact source departure vector is preserved at fraction0.4: (1.725,1.600)×0.4=(0.690,0.640) mm. Native geometry independently confirms original c782 source-via contact patch is restored exactly: 0.019374803264 mm², zero difference area and zero difference outlines.
3. Native current-reference check over both complete affected track shapes finds zero newly unsupported material outside the unchanged moved-via window after removing the original source track's unsupported footprint. The held candidate's 0.0003496908615 mm² source-via exception is eliminated. Both zero areas also have zero outlines; no small-area waiver is used.
4. Independent optimized full-board drill check confirms each inner plane remains one component. Relative to the header intermediate, only the expected stitch drill removes material, exactly0.049087681002 mm² per plane. No old signal shadow loses reference because of that drill. Every old object is conservatively screened for bounding-box intersection, followed by exact Booleans for all potential overlaps; this is not a cropped proof.
5. Native GPIO10 contacts still reproduce the three far-end remapped patches exactly. The deliberately rerouted GPIO10 start still has explicit old-minus-new1.37825e-8 mm² despite increased overlap. That inherited declared-refactor difference is not erased.
6. Fresh independent DRC returns9 opens,42 warnings, parity0, and no other DRC errors. Material-component-normalized open pairs and all warning records exactly match the main run.
7. Fresh full material export's board hash was verified, then independently compared against held b1e3. Pad inventory/partitions, zone-contact measurements, guard diagnostics, empty/multiple object layers, old barrel joins and all unrelated material nodes are exact. Only the declared retained track's material node changes; the new segment is added.
8. Two retired far-end direct edges on55e5 remap toadb09 with positive guarded contacts; the new split junction is also positive. The source-via edge restores its original source measurement. No unrelated direct edge is removed or changed.

## Contact measurement scope

These are explicit refactors, not exact old far-end contact patches:
- Moved-via endpoint:0.0193748671165→0.019374863805 mm².
- Neighboring df690eec track contact:0.0019396436365→0.001970426796 mm².
- New split joint:0.0176711231225 mm².

All are positive guarded contacts with unchanged complete pad partitions. The small measurement changes are recorded, not silently treated as exact or globally tolerance-waived.

## Full-board plane gate

Independent complete source→corrected-candidate rerun completed with exit0. Explicit machine assertions in assert_full_plane.py passed:
- All137 retained affected GPIO10/26 tracks and15 new tracks have exactly zero newly unsupported area and zero contours outside their unchanged applicable transition windows.
- No old signal projection has undeclared loss. Exactly four changed old projections remain, all explicitly declared refactors.
- Both inner planes remain one component. Source→candidate loss is0.880300188708 mm² per plane, gain0.189959295388 mm², including the actual new stitch drill.
- Zero loss lies outside the original three transition windows plus the actual stitch drill. The split segment uses only the already declared moved-GPIO26 window; no new source-via window is introduced.
- The previously held0.0003496908615 mm² source-departure exception is eliminated in the independent complete rerun, not just the targeted test.

Reviewed main evidence for this exact SHA: cold refill leaves all58 files byte-identical; all12,135 raw conductive object net names and1,064 XML electrical nodes pass identity checks; ERC reports zero violations. These are reviewed main results, not independent reruns of those steps.

## Remaining limits

- This remains descended from qualified c782123, whose tiny remote +4V_LED exact no-loss failure remains inherited. It does not become the preserved bbf61e6 strict baseline.
- Nine physical opens and42 warnings remain; the board is not electrically complete.
- 51 inherited guarded-contact proof failures remain; unchanged diagnostics do not prove those contacts safe.
- Signal return transition distances, nominal plane coverage and positive contacts are not SI/EMI or loop-inductance measurements. Component effective values, active regulator behavior, extracted parasitics, manufacturing and assembled-board performance remain unqualified.
- Main cold-refill, ERC, net-identity and reference-label geometry checks are distinct evidence, not independently rerun here.
- No PCB modification, push, fabrication or publication was performed by this reviewer.

## Evidence

raw-audit.json; target-reference.json; source-contact.json; native-geometry.json; drc.json and drc.log; material-comparison.json. Reproducible scripts are adjacent. full-plane-review.json/full-plane.log record the completed full rerun; full-plane-gates.json records explicit successful assertions.
