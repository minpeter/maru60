# Candidate-specific coordinate-precision review

**Exact aead candidate passes the separately authorized 1 nm criterion. Final fresh graph/DRC/parity/ERC recheck and parent selection are still pending. The original strict global zero-loss result remains FAIL, unchanged.**

Source: `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`.
Candidate: `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`.

## Applied criterion and rationale

For this exact cleanup only, retain every prior source/contact/root/reference/clearance requirement, but assess the remote serialization differences using a bilateral 1 nm distance-to-opposite-material bound. The only larger local gain permitted is the exact original saved hole polygon belonging to the retired via. It is not enlarged; the .50 mm radius used in consequence checks is merely a containment check, not extra permission.

The installed API uses 1,000,000 integer internal units per mm: one native coordinate unit is 1 nm (`PCB_IU_PER_MM`, `FromMM`, `ToMM`, integer `VECTOR2I`). Wrapper/native-library hashes and exact KiCad9.0.2+dfsg-1 are recorded. **Integer vertices can encode real sub-nm transverse slivers.** The criterion does not claim those slivers are nonexistent, unrepresentable, or mathematically zero. One native grid unit is an explicitly chosen engineering precision bound, not an automatic rule or a manufacturing/electrical tolerance.

The justification also depends on exact unchanged remote obstacle geometry and rules, deterministic source/candidate normal refills, strict zero old-shadow loss and contact/root preservation. It is not justified by thinness alone.

## Exact bilateral material proof

Exact reverse fracture edges cancel algebraically; no rounding or approximate simplification is used. All remaining directed edges partition into closed cycles. Source/candidate cycles differ by exactly one removed local hole plus 51 remote patches per layer. Each patch is split at exact longitudinal breakpoints and crossings into convex rational cells: 181 disjoint cells per layer.

Every opposite chain is proved to be a genuine material boundary, with no nonadjacent crossing/overlap and exact sided membership. All other boundaries are excluded from cell interiors. Each cell has constant source-only or candidate-only classification, cells are pairwise interior-disjoint, and their exact areas plus the local hole reproduce the full raw signed-area difference. Thus no remote loss or gain is omitted.

For every point in every remote difference cell, a finite-segment point on the opposite saved-material boundary is explicitly available at the same longitudinal coordinate. The perpendicular separation is piecewise linear; checking all exact knots proves the whole cell, not a sampled approximation. The squared maximum constructive bound is `20946193984/38911272217 nm²`, giving **0.733693793701 nm**, below1nm. This is an upper bound on nearest opposite-material distance, not a claimed exact Hausdorff maximum. A worst witness lies at source (148.545580000000,85.664891000000) mm, paired to (148.545579280404,85.664890856861) mm.

Exact raw material areas per layer are:
- Remote source-only loss: approximately0.000000336086505284 mm².
- Remote candidate-only gain: approximately0.000000806539005284 mm².
- Local recovered original hole: exactly0.641253345104 mm².

Fractions and every cell/vertex are retained. These exact areas differ from the prior native integer-Boolean report because that operation rounds intersection vertices. Both results are preserved; the earlier nonzero-loss conclusion is not rewritten.

## Strict conditions retained

All exact loss bands are clear of every original non-GND outer reference shadow, with a conservative2nm native guard. All loss and gain bands are clear of retained inner-GND contact copper. One entirely gain-only patch adds plane coverage beneath three existing front power shadows and one back ROW0 shadow; it contains no source-only loss. A control deliberately reclassifying that patch as loss is rejected.

All731 physical plane-contact identities/support areas, all247 J1.A1-rooted GND pads and all245 pad-net partitions remain exact. Native hard errors/ERC/parity remain0, the same12 complete open pairs remain, and precisely the named via warning disappears (68→67). These previously checked observations await the requested fresh final repetition.

Conservative integer convex hulls enclose both loss and gain cells. Fresh native obstacle tests consider all actual holes and foreign inner copper, with NPTH pads treated as holes rather than phantom copper disks. Correct unchanged limits are .20mm for zone-to-foreign-copper and .15mm for holes. Minimum native last-noncollision brackets are at least .200499mm and .150499mm, respectively; no material enters copper or holes. Source-to-candidate brackets move by no more than one native unit. The initial exploratory uniform .20mm test was overbroad for holes; its failed result is preserved, not presented as a rule failure or silently discarded.

The exact selected source and candidate each independently survive one no-electrical-edit normal refill byte-for-byte. These are builder-executed fixed-point controls whose actual board bytes, code, logs and results were independently rechecked, not six-copy replay or reviewer-performed refills. They show this is a geometry-change-induced serialization difference, not generic repeated-fill drift.

## Scope, controls and reproduction

The old strict packet and its hash manifest are unchanged. This is an additive candidate-specific assessment, authorized separately, not a generic validated checker. Larger2nm loss/gain controls, a thin displaced strip with mismatched endpoints, nonmonotone chains, boundary/interior/overlap tests and gain/loss misclassification controls exercise the proof. Optimized Python is refused before work in five scripts. Native collision controls verify the obstacle calls.

No source/candidate CAD was edited. No noise, pickup, active-loop stability, SI, hardware or manufacturing benefit is inferred. A native-grid criterion cannot establish those outcomes.

`FINAL_PRECISION_REVIEW.json` records the decision and pending final recheck. `SOURCE_BINDINGS.json` pins the prior strict packet, boards and fixed-point controls. For pure reproduction, set `BUCK_STRICT_PACKET` to the accompanying unpacked strict-review packet, then run the proof scripts with normal Python (not `-O`). Native obstacle scripts need the matching candidate project and KiCad Python. Their original paths are preserved in code. Private runtime homes are excluded. The pre-load syntax failure and exploratory stronger probes are preserved separately and are not passing evidence.
