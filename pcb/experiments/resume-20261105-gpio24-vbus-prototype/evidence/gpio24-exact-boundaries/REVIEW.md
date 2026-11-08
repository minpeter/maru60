# GPIO24 independent exact-boundary review

## Decision
Strict exact no-loss: FAIL, not a tolerance pass. Retain the frozen26b baseline as strict accepted baseline. frozen24move is defensible as an explicitly qualified prototype candidate on this geometry issue, but this review does not promote it, waive the strict guard, establish manufacturing readiness, or qualify SI/EMI/current return behavior. Native residual opens/warnings still need their own disposition.

The unrelated +4V_LED reference loss is real in the serialized geometry, not wholly an artifact of subsequent Boolean evaluation. Its size and all remote boundary displacement are consistent with integer fracture/refill rounding. Causation inside KiCad was not traced, so “consistent with” must not be upgraded to a proven internal cause.

## Source binding
- Source frozen26b PCB SHA256: 04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99
- Candidate frozen24move PCB SHA256: 2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4
- delta.py asserts both hashes and reads native serialized filled-zone integer vertices. No PCB was saved or changed. Native wrapper uses installed pcbnew 9.0.2.

## Independent target verification
Track 3e0fec9e-6c78-45a5-a2dc-22ae925ad604 is unchanged +4V_LED B.Cu, x=274.6 mm, y=35.25–38.35 mm, width=0.25 mm. The investigated rectangle is within its straight copper body, x=274.475–274.540691 mm and y=37.899499–37.917104 mm.

Reviewed and reproduced author's exact rational arrangement/winding method with output redirected to this directory. It partitions a convex rectangle by all intersecting raw polygon edge supporting lines, classifies each cell using its interior centroid and exact raw-outline winding, and asserts area conservation. This is valid for the stated local region. No physical drill bbox intersects it. Crucially, an independent analytical calculation (analytic_target.py) integrates the piecewise-linear source boundary minus the candidate boundary, using Fraction arithmetic rather than polygon clipping or Boolean operations. It obtains the same loss:

1189714324905/42986012 nm² = 2.7676778318142192e-08 mm² per plane.

Maximum vertical difference in this strip is 7524735/10746503 nm = 0.700203126542653 nm. This disproves exact no-loss, even though it is a sub-nanometre nominal displacement. Native Boolean output 2.3625e-08 mm² is not the exact raw-boundary area.

## Full affected-boundary scope
Enumerated both complete GND plane raw outline/hole edge sets and cancelled only exactly reversed edge pairs (zero-winding fracture bridges). Both planes have identical changed edge geometry: 114 removed and 210 added edges before local exclusions.

For full-board remote bounding, excluded only entire segments whose two endpoints lie in one of four convex 0.455 mm disks: moved EXT_GPIO3 old center (97.25,37.55), its new center (97.25,37.45), new GPIO24 centers (92.35,37.75) and (105.8,37.5). This is explicitly broader than the earlier three-disk loss test: old-via boundary recovery is also excluded here. These are transition geometry exclusions, not unqualified signal support allowances.

For every remaining changed segment in each direction, split into exact rational subsegments using opposite-edge endpoint projections. For each subsegment, bound both endpoints' exact squared distance to one opposite revision segment. Distance to a convex segment is convex, so this bounds its entire length. Taking the minimum available capsule per subsegment and maximum over all subsegments yields conservative directed bounds:

- Source remote boundary to candidate boundary <= 0.7600509255697051 nm.
- Candidate remote boundary to source boundary <= 0.7678979913540595 nm.

Exact squared maxima are retained in boundary-bound.json. Thus no remote changed raw boundary segment is displaced by >=1 nm. This is a boundary-location proof, not an exact full-plane area calculation or topology/current-flow proof. Unchanged edges have zero displacement. All deltas are retained rather than normalized.

## Physical holes
Both source and candidate have all native effective drilled shapes inspected (1271 and 1273 respectively). A conservative bbox-distance test against every remote changed segment yields a minimum 240509.68819779382 nm = 0.240509688 mm in both revisions. Thus these remote raw boundary changes are not hidden inside drilled-away material, and physical-hole subtraction cannot dismiss the demonstrated target loss. See drills.json. This covers native pad/via drill shapes, not unspecified fabrication defects.

## Artifacts and limits
- delta.py / boundary-delta.json: source-bound complete integer edge enumeration.
- bound.py / boundary-bound.json: exact rational full-remote-boundary capsule proof, adapted with fresh four-disk scope.
- reproduce.py / reproduced-local.json: reviewed author method reproduced locally.
- analytic_target.py / analytic-target.json: independent exact target-area calculation.
- drills.py / drills.json: all drill-shape bbox separation and exact target-track identity.

No tolerance was used to report an exact pass. No electromagnetic solver, fabricated SI result, warning suppression, copper edit, new installation, credentials, or alternate environment was used. A prototype-only decision can cite the small bounded nominal geometry difference, but must preserve this explicit strict failure and the remaining electrical/manufacturing qualification limits.
