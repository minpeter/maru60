# Read-only review of prospective stitch contract

Reviewed `inspect_site.py`, `site_results.json`, `check_legacy_shadow.py`, `legacy_shadow_results.json`, and `original_source_provenance.json`. No CAD mutation, full exporter, or new simulation was run. Selected board remains `c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a`.

## Outcome

No present-site geometry or source-provenance contradiction was found. The rational capsule-axis inequalities are conservative and correctly include the existing drill radius, new drill/copper radius, and stated clearance. Same-root inner-plane annulus containment plus positive guarded overlap supports prospective material contact. It does not prove a new SI/ESD benefit, and the added via would be redundant in the existing named-pad connectivity graph.

## Corrections before treating this as a reusable construction gate

1. **Fail closed with optimized Python.** Both scripts rely on `assert` without the explicit `if not __debug__: raise RuntimeError(...)` used by the active R2 helper. Running either under `python -O` can currently suppress every safety assertion while still writing a pass result. Add the explicit guard to both. Pin and report the native KiCad build in the legacy script as well.
2. **Bind rule inputs.** Record and require the `.kicad_pro` hash and the presence/hash or verified absence of `.kicad_dru`. The current project has no `.kicad_dru`; all current netclasses have 0.15 mm clearance. Global minimum rules alone should not be generalized to resolved DRC rules. Final native DRC remains mandatory.
3. **Make the permitted material loss exact.** The new drill intentionally removes 0.049087681002 mm² from each of the two main inner GND-plane components. Express this as a precise shape/layer/root exception, not a general small-loss allowance. Assert zero drill loss on every other existing object and zone, including inner-layer GND objects and outer-layer GND zones. The current loops do not explicitly cover both latter classes completely.
4. **Assert board containment, not distance alone.** An outside point can be far from every Edge.Cuts drawing. Require successful native outline construction and containment of the proposed copper envelope in the valid board area, in addition to the edge-clearance predicate.
5. **Keep the future inserted-board gate explicit.** Construct only in an isolated candidate; require exactly one new 0.5/0.25 mm through GND via at (17.2,9.9) with the specified fresh UUID, preserve all existing object definitions including the retained stub, then refill and run native DRC plus the active R2 exporter and acceptance checks. Verify all named-pad partitions and preserved contacts, the new intact barrel, and both guarded main-plane contacts. Do not turn this prospective read-only pass into an inserted-candidate or SI/ESD pass.

## Independent lightweight confirmations

- Rehashed the ZIP to the recorded archive hash and compared the exact member bytes with `input-original-a9.kicad_pcb`; both matched. The extracted board is exactly SHA `a9ff40100f8b34cd46b7706eb3264cbbc61508cc4c6895fdcefcb2cce35e7b67`. This does not restore missing original QA/history.
- Native outline reconstruction succeeded, with one outline spanning (0,0) to (285,94.6), and (17.2,9.9) is inside.
- There are no board or footprint graphical objects on the four copper layers, so their omission from the object scan does not hide current copper.
- The proposed drill has zero native intersection with existing inner-layer GND object shapes.
- Proposed drill intersection with every current F.Cu/B.Cu zone is exactly zero, including all three outer GND zones. Only the two inner GND zones have nonzero intersection, each 0.049087681002 mm².
- Current pad-local clearance overrides found are 0.125 mm on C102/C103, so they do not make the checked 0.15 mm foreign-copper margin inadequate.

These confirmations close the present-instance gaps, but the corresponding assertions and input binding should still be incorporated into a repeatable future gate. No existing stub was changed.
