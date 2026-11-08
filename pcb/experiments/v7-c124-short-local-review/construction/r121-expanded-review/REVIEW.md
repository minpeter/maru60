# Independent review of expanded short-C124 V4 plan

## Decision

**No new analytical blocker found. Suitable for parent-approved, isolated, unselected CAD construction only.** This review does not authorize selecting the candidate, procurement, assembly, or production adoption. V4 explicitly changes the old unchanged-UVLO contract and proposes a new R121 MPN and land pattern; it must not be represented as the old 37.7 µm movement allowance passing unchanged.

Reviewed source board SHA-256: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`.
Reviewed geometry JSON SHA-256: `0201051134f0ffe6b1498a83687ba7a3dc909869d6f117fdb8456351d4ad5c51`.
Reviewed contact/reference JSON SHA-256: `c731b943caa355e67060ef0c60adbc6b06a83183c90b9a84b42a537ea2212332`.

The source remained unchanged. All output from this reviewer is in this directory. No candidate board, fill, full-board graph, or production change was created. Native checks used pcbnew 9.0.2, a private XDG directory, one loaded BOARD per bounded process, and 1 nm geometry approximations. Main scripts were read, not imported or replayed.

## Independent native results

1. **Exact retirement identity.** All 31 listed objects exist at the exact recorded source coordinates, widths and nets: 24 UVLO, 2 OVLO, 5 DVDT. Every one is a B.Cu track, not a via. There were zero UUID/coordinate/type mismatches.
2. **No missing contact branch in the bounded ledger.** Recomputed all 74 affected old positive-area copper-contact pairs. The supplied ledger has neither missing nor spurious pairs. The 24-segment UVLO chain has endpoint-connected retained branches only at (14.2,16.35) to `751dcade…` and (17.2,21.15) to `7d18b97e…`. Nearby non-endpoint copper contacts are also accounted for: the new UVLO boundary segments positively contact `78c0ab16…`, `c206500a…` and `d2cb1d31…`. No orphaned external contact was found.
3. **Signal interfaces remain positive.** Independently rechecked all ten supplied UVLO/OVLO/DVDT new-to-retained boundary contact entries. All are positive, including the retained OVLO `e218cfe4…` continuation, DVDT stub `7c494a73…`, and both physical U8.7 pad shapes. New route continuity and R125 input/output separation are consistent with the supplied new-new ledger and foreign-copper screen; constructed-board topology is still required.
4. **Changed R121 support is explicit.** Proposed R121.2 land intersects the retained `abcd4fb1…` GND spur by **0.055103142777 mm²**, reproducing the supplied result. This replaces, rather than fully preserves, the old 0.118391566097 mm² pad contact. No claim of byte-identical support is warranted.
5. **Full old C124 support is covered, with the stronger approximation direction.** Independently formed each old physical support region from outside approximations of the old pad and supporting physical conductor, then subtracted the inside-approximated two-track bridge. Both deficits are **exactly 0 mm²**. This covers the source spur `19181a2b…` contact and the actual drilled annulus of `763086b7…`, not a full via disk or just the pad center. The two ordinary bridge tracks must be built with the exact reviewed widths and endpoints.
6. **Fresh bridge-to-retained-foreign clearance passes.** The minimum using the outside 1 nm bridge envelope is **0.375000 mm** to ILM track `2aa1548e-40ed-5870-8e20-2519c0040e88`. No retained foreign B.Cu conductor is closer than 0.150 mm. The next native gaps and identities are recorded in `additional_native.json`.
7. **Expanded R121 courtyard is clear.** Its exact 1.50×3.00 mm rectangle has zero overlap with every retained source-courtyard enclosing box, including source primitive stroke extents. This is a conservative check using actual source shapes, not cached courtyard erosion. Nearest conservative gaps are SW1 **0.887750 mm**, SW16 **1.035250 mm**, R124 **1.675000 mm**. Exact new rectangular court gaps independently reproduce R121–C124 **0.150 mm**, R121–R125 **0.210 mm**, C124–R125 **0.050 mm**, U8–R125 **0.060 mm**.
8. **All six retained source plane roots are positive.** Each of the three retained ground vias (`efadf2be…`, `763086b7…`, `8e0fa85d…`) intersects both source In1 and In2 ground fills with physical annular contact **0.147260768066 mm²**. Native drill subtraction was used. These are source-root checks; candidate refill preservation remains pending.

## Part and assembly assumptions

The proposed R121 full IPC geometry is supported by [Vishay recommended solder-pad dimensions, document 28950](https://www.vishay.com/doc?28950): 0603 reflow G=0.70, Y=0.90, X=1.00, Z=2.50 mm. For the vertical orientation, that gives 1.00 X×0.90 Y pads at pitch1.60. It is not the smaller IEC option. The [TNPW e3 datasheet, revision10-Apr-2026](https://www.vishay.com/docs/28758/tnpw_e3.pdf) supports the proposed ordering grammar, 156 kΩ ±0.1%/25 ppm/K family range, and conservative maximum L1.60/W0.95/termination0.50 mm. It does not establish what R121 was previously fitted with or certify this assembly.

The [KOA ordinary1E land pattern](https://www.koaspeer.com/pdfs/Appendix_B.pdf) is consistent with R125's 0.40×0.30 mm pads, pitch0.90 and overall1.30. The larger AT pattern is distinct. The [RK73H family drawing](https://www.koaspeer.com/catimages/Products/RK73H/RK73H.pdf) distinguishes ordinary1E dimensions and supports conservative body/terminal bounds; this review does not claim procurement availability or pulse qualification.

C124's current exact-part manufacturer approval remains unverified, as the plan discloses. The stated maximum body/terminal and process envelope is an explicit analytical assumption, not an assembly guarantee. The ±0.05 mm placement, ±2° rotation and 0.05 mm solder spread are also assumptions. The envelope implementation uses endpoint/zero-angle corner samples; for the specified corner offsets no coordinate stationary point falls inside ±2°, so the sampled extrema cover the requested rotation interval before nanometre rounding. Clearance margins are tens of micrometres, not rounding-sized margins.

## Reference review and required next gates

I reviewed the reference-check implementation and all 44 supplied signal/pad projection results: none reports uncovered area after physical source drill subtraction. I did not run an independent full shadow/fill comparison. It remains incorrect to promote those inside-approximation source-fill screens to proof of an actually saved and refilled candidate.

Before any adoption, the isolated build must still demonstrate:

- Exact whitelist inventory and unchanged objects/settings, actual board hash, masks/paste, and unique custom footprints with real MPN/source metadata.
- Native DRC, schematic/ERC/netlist parity, complete bounded contact ledger, no R125 bypass, and unchanged all-net partition outside the authorized changes.
- Both physical inner reference roots, every old shadow and all new reference projections after actual refill, with no unapproved loss.
- Analog acceptance of longer high-impedance UVLO/OVLO routing, the new R125 pulse/reset/thermal behavior, and common-return impedance.
- Current C124 part/land acceptance and actual switch/socket/plate/keycap height and registration checks.

No part of this review waives these gates. The old remote20 mm/five-via candidate remains rejected.

## Evidence

- `review.py`, `review_native.json`, `review_native.log`: independent retirement/contact/support/root checks.
- `additional.py`, `additional_native.json`, `additional_native.log`: fresh bridge foreign-clearance and actual-source-courtyard bounds.
- Exact input hashes above bind this review to the reviewed V4 records. Input changes require reconciliation before applying this finding.
