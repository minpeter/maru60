# Independent code and regression review: canonical-wrapper revision1

Reviewed checker SHA35df75c4c564fee2f4b69982282cb15111c6e96bbe8d6fdb54990f05cf1bcf43; test SHAa43649bed74bf79a001b1a405d97058c4926c01080b65dd571f978b5f3633366; controls SHAfabdddb39090cd528319190c3c0921cabed5c8442ed6c0f181f59f4919d660e4. Exact examined copies retained separately. No original or sealed code edited; no full-board run duplicated.

## Intended fix: correct by inspection
- Direct q originates from the canonical board inventory. Every native neighbor z is replaced byidx[uid(z)]before IsOnLayer or material requests.
- Zone contacts are all UUID-resolved before layer access.
- cu()also resolvesidx[uid(q)]before accessing the UUID/layer cache, type, width, shape or hole. The only wrapper access before resolution is its UUID, as required to look it up.
- Unknown UUID raisesKeyError rather than retaining a wrapper/falling back; fail-closed follows directly from dictionary indexing. The supplied controls do not explicitly exercise this exception branch.
- Own-hole treatment, via outer-circle representation, pad effective shape, PTH identity and the all-drill zone subtraction are unchanged by the small patch. No rule/clearance changes are present in the diff.

## Current controls genuinely exercise the reported defect
The actual native neighbor has Python typePCB_TRACK whileGetClass()isPCB_VIA; the canonical object has Python typePCB_VIA. Fresh caches independently compare wrapper versus canonical geometry on all four layers and compare with outer-circle minus outside-hole material. Reverting canonicalization would fail that comparison for the observed wrapper.

The recorded tests reject all three observed drill-only false edges, preserve the known positive annular contact0.0564735324735mm² and test every canonical pad/layer against unchanged native own-hole treatment:1437pads,1908pad-layer checks,16PTH and335NPTH. This is a useful defect-specific regression, not a complete physical-geometry test suite. The pad controls compare canonical pads, not each possible native pad-wrapper class. The current code structure covers those wrappers through UUID resolution, but the wrapper variants are not independently demonstrated by these controls.

The tests extract actual checker functions through AST, avoiding a second full graph export. They do not execute the direct/zone traversal loops, so their canonicalization is additionally verified by static inspection. They clear caches between inputs, proving corrected equality but not explicitly exercising a mixed wrapper-first/cache-hit sequence. Canonicalization preceding cache lookup makes that sequence safe by inspection. The lost-edge list is an external audit input; the reviewed controls contain exactly three cases but do not assert a fixed count/hash internally. This review binds all examined files.

## Remaining optimistic material issue: revision1 is not complete validation
cu(track)does not subtract other physical drills; cu(via/pad)subtracts only its own drill. Thus a track–track, track–pad or other overlap that lies wholly inside a third-party NPTH/drill could still create a positive physical edge. Global hole subtraction is applied to zones, not each conductor material. This issue remains even after wrapper canonicalization and needs separate per-layer material treatment and targeted controls/source comparisons. No assertion of globally complete drill-aware connectivity is justified from revision1 alone.

All holes are currently unioned into all zone layers. This is only appropriate if actual holes traverse those layers; blind/buried drill handling must be explicit or ruled out by source inventory. A single object identity is appropriate for plated via/PTH barrels, but not automatically for NPTH copper on multiple layers. Current NPTH net/copper relevance must be checked rather than inferred from pad-count tests.

Native inside-copper/outside-hole polygon bounds are conservative approximations, but integer Boolean clipping can have grid artifacts at boundaries. Positive-area decisions near that precision are not an exact rational proof by themselves. Bounds and source-specific comparisons remain relevant; a wrapper fix must not silently become a precision waiver.

Conclusion: revision1 correctly addresses the observed wrapper/cache defect. Its reported preserved pad partitions are not, by themselves, complete material validation. Continue separate revision2/all-drill audit; retain original and revision1 evidence without overwriting it.
