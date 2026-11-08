# Short local C124/R125: expanded V4 contract for review

**Analytical, unselected, not constructed.** This is an explicit changed contract, not a continuation of the earlier unchanged-UVLO gate. The old 20 mm/five-via candidate remains rejected. No source CAD, repository, selection, or prior packet has been changed.

## Exact source and scope

PCB SHA-256: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1` (selected unit 34). Read-only recovered source: `/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb`. Canonical recovery repository is `pcb-v7-recovery-20261104`, commit `49ce079404c79d18c85a7f80742f8d1778c47062`, selected subdirectory `pcb/experiments/v7-reference-legibility/candidate/pcb`. Construction, if subsequently approved, must copy that complete selected tree and verify its exact board hash, retaining the accepted reference corrections and corrected TP schematic labels.

Retire exactly 31 old B.Cu tracks: five DVDT feed segments, two OVLO arm segments, and the contiguous 24-segment UVLO chain whose exact UUIDs are recorded in `main/counterfactual-uvlo-r121-ipc-v4.json`. No old via is removed, moved, renetted, or resized. No other old track may change. Change only C124 and R121 footprint geometry/pose, add R125, and add the single net USB_DVDT_CAP. Retain U8, source/decoupling/supply copper, all other pads, board shape, stack, settings, clearance rules, and all source/reference copper.

The earlier pure-left R121 bound is still 37.701665379 µm mathematically, 37,700 nm conservatively proved. A 50 µm shift failed the unchanged UVLO contract. V4 does not waive that bound: it proposes replacing the actual UVLO obstruction by a named, independently reviewed route. The source-centered 88° trial gave only 2–5 µm court gaps and is not the construction basis.

## Proposed real parts and lands

All three parts are on B.Cu. Dimensions in mm, coordinates are in the source board coordinate system. These MPNs are proposed for an isolated experiment, not selected for procurement or production.

- R125: KOA RK73H1ETTP1000F, 100 Ω ±1%, ordinary 0402. Center (15.54,20.27), horizontal. Pad 1 USB_DVDT at (15.99,20.27); pad 2 USB_DVDT_CAP at (15.09,20.27). Each land 0.40 X ×0.30 Y, rectangular, pitch0.90. Courtyard1.80×1.05. KOA Appendix B's ordinary 1E reflow option is G0.50/overall1.30/width0.30/land-length0.40. Do not silently substitute its different AT pattern or a generic KiCad land.
- C124: proposed Murata GRM155R71H103KA88D, nominal10 nF ±10%,50 V,X7R,ordinary0402. Center (15.38,19.17), horizontal. Pad1 USB_DVDT_CAP at (15.005,19.17); pad2 GND at (15.755,19.17). Each land **0.35 X ×0.50 Y**, pitch0.75, innergap0.40. This corrects the earlier swapped land orientation. Court1.60×1.05. Current exact approval-sheet access is unavailable; historical dimensional/land documentation and conservative envelope are analytical assumptions, not a current manufacturer assembly guarantee.
- R121: proposed Vishay TNPW0603156KBEEA, unchanged156 kΩ ±0.1%,25 ppm/K,0603. Center (13.68,18.65), vertical, a deliberate −0.32 X/+0.15 Y displacement. Pad1 OVLO at (13.68,19.45), pad2 GND at (13.68,17.85), each **1.00 X ×0.90 Y**, pitch1.60. Use the full official IPC reflow option (G0.70,Y0.90,X1.00,Z2.50), not the old footprint or a selectively reduced court. Court enlarged to1.50×3.00. PCB/schematic currently have no exact R121 MPN; this is an explicit proposed BOM and land-pattern change.

Prospective custom footprint library entries must record manufacturer, MPN, sources, B.Cu/B.Paste/B.Mask layers, real pads and paste openings, body/Fab and exact court primitives. Do not represent terminals by track copper, reuse a generic footprint name for changed lands, or implicitly change mask/paste conventions. Board mask margin is zero; no new mask/paste exception is proposed. Any later assembly-process change needs separate documentation.

## Complete track geometry

All following routes are B.Cu,0.15 mm width, zero new vias. Consecutive vertices form ordinary track segments:

- UVLO: (14.2,16.35) → (13.1,17.05) → (12.8,17.55) → (12.8,19.9) → (14.2,21.3) → (16.85,21.3) → (17.2,21.15). Six segments,9.247623313 mm, replacing24 old segments totalling8.352691193 mm. Both boundary contact neighborhoods must be recorded and connected exactly; no UVLO divider pad/via changes.
- OVLO: (13.68,19.45) → (14.5,19.45) → (14.5,19.95) → (14.55,20.67) → (14.8,20.97) → (16.8,20.97) → (17.2,20.8) → (18,20.95) → (20.175,21). Eight segments,7.856388450 mm. Retire only `05a0b97d-79af-50e5-b191-fe26b55d2c02` and `eb147f3b-fbe7-5ff5-a09d-d36fa376b92f`. Retain `e218cfe4-e4ba-5b6c-985d-8f1da39a4402`, `6e2e82bf-1a07-562e-b012-9a61a7509e00` and the downstream via (22,19.6) unchanged. Full new arm to that via10.172156727 mm versus old8.761637279 mm (+1.410519448 mm).
- U8-to-R125: retained U8.7 source stub `7c494a73-d1ac-5d4f-ae2d-7b26d0b153f3`, (17.275,19.375)→(17.25,19.4),0.035355339 mm; then new (17.25,19.4) → (16.85,19.4) → (16.5,19.8) → (15.99,20.27),1.625048926 mm. Total pin-side track1.660404265 mm. Retire the five obsolete DVDT segments with prefixes18d72adc,3aa399c7,3dce1fa7,5b54e93a,c69210ed, total1.857514077 mm.
- After R125: (15.09,20.27) → (15.005,19.17),1.103279203 mm, net USB_DVDT_CAP. This net must contain only R125.2,C124.1 and this route. The original DVDT stub/new input route must not bypass R125.
- C124 ground: (15.755,19.17) → existing GND via (16.4,18.9),0.699231721 mm. Existing via UUID `8e0fa85d-f2bc-543d-aae7-d8f6ff75061a` and its U8.8/feed/plane contacts must remain intact.

Add the exact reviewed old C124 ground-contact bridge as **two ordinary tracks**, not a custom copper primitive: width0.28,(15.5,17.725)→(14.9,17.275); width0.20,(15.5,17.85)→(15.5,17.25). This preserves the full two old C124.2 contact support regions, not merely contact at the old pad center. Keep both old ground vias and spurs, with both vias' separate In1/In2 plane roots. The moved R121.2 must have positive native contact to its retained spur, and any change of that pad's support must be explicitly recorded rather than described as byte-identical contact preservation.

Proposed addition totals:19 route tracks plus2 ground-bridge tracks=21 new tracks, zero vias, one new footprint; two old footprints changed. Expected track/via count change is −31+21=−10 (source10,671 →10,661); footprint count382→383. This is a predicted inventory, not an actual CAD measurement.

## Completed bounded geometry screen

Native KiCad9.0.2 source shapes,1 nm polygon approximation, private XDG, one loaded source BOARD/process; source SHA checked before/after. No BOARD mutation/save/refill. All retained B.Cu foreign conductors considered individually, new-new foreign copper checked, real maximum terminal boxes expanded by ±0.05 mm X/Y placement,±2° rotation and an additional0.05 mm lateral solder halo. These process bounds are explicit assumptions, not an assembler-certified capability. Small-angle corner extrema are conservatively enclosed. This is more than nominal pad/courtyard clearance; it is not full assembly qualification.

- Minimum new-new foreign copper gap0.172115 mm (newUVLO/OVLO); minimum new-to-retained copper0.172115 mm at retained UVLO/OVLO interface.
- R121 IPC pad2→newUVLO minimum0.173673 mm.
- C124.1 worst terminal/solder envelope→OVLO0/1 minimum0.170722 mm.
- R121.2 worst terminal/solder envelope→retained ILM via minimum0.167370 mm.
- C124.1 worst envelope→retained ILM via0.179286 mm.
- R125.2 worst envelope→OVLO3 minimum0.182903 mm.
- C124.2 land→existing ground-via annulus outer edge0.220425 mm; land→physical drill0.345425 mm. No via-in-pad. New ground trace intentionally enters the existing via annulus; this is not a pad/via exception.
- Exact critical court gaps: R125–C1240.050 mm, R125–U80.060 mm, C124–R1210.150 mm, R125–R1210.210 mm. Actual source U8 court vertices are used, not the misleading cached5 µm erosion.
- New UVLO to SW16 physical NPTH edge minimum0.293750 mm. Board project has copper clearance0.15 and hole clearance0.15; hole-to-hole0.25. No rule reduction is proposed. No new hole is introduced.

The screen's exact UUID/coordinate/minimum records are in `main/counterfactual-uvlo-r121-ipc-v4.json`. V1/V2/V3 remain preserved and are not passes. V2's insufficient land/via solder separation and V3's actual R121 IPC-land/UVLO conflicts motivated V4.

## Contacts, reference, circuit behavior and pending acceptance

The companion `main/counterfactual-v4-contact-reference.json` records native old contacts touching all removed objects/pads, new-to-retained and new-to-new contacts, exact six-object old ground component, full ground bridge support, existing plane roots, new-track reference coverage, and physical drill clearances. The completed native analysis records 74 affected old positive-contact edges (including exactly nine old pad contacts),16 new-to-retained contacts and19 new-to-new contacts. Both old C124.2 support regions have exactly zero area outside the reviewed bridge. New R121.2 overlaps its retained ground spur by0.055103142777 mm² versus original0.118391566097 mm²; this is an explicit changed pad-contact support, not a claim of complete old R121 support preservation. Each of the three retained ground vias separately overlaps both inner GND fills by0.147260768066 mm² of annular copper. Every screened new signal track/pad has zero area outside each drill-subtracted source GND plane. These are analytical source-plane contacts/projection checks, not an actual-candidate refill or global rooted-connectivity replay. The source hash is unchanged after the run.

There is no new drill or inner-layer conductor in this plan. Local USB region has no B.Cu zone; inner/far fills are therefore expected not to change, but only an actual isolated saved native refill can establish that. Every old reference shadow, including removed DVDT/OVLO/UVLO track shadows, remains an acceptance target. No antipad disk, epsilon, transition deficit, or reference waiver is introduced. Any new-route projection deficit against retained source fill must be individually classified; do not call full reference coverage without that result. Existing via holes/antipads are not filled-in reference.

The schematic changes only by inserting100Ω between U8.DVDT and C124.1 and assigning the new capacitor-side net; R121/UVLO divider values and logical topology remain unchanged. Total U8-to-C track length2.763683468 mm versus original direct1.892869416 mm; signal length grows0.870814052 mm, but the sensitive pin-side run is1.6604 mm instead of the rejected remote20 mm. Nominal added RC is1 µs; at3.82 µA the resistor drop is0.382 mV. These elementary checks do not establish startup, reset pulse, distributed coupling, leakage or noise immunity. UVLO gets0.894932120 mm longer, OVLO arm1.410519448 mm longer, both near high-impedance sense nodes and requiring analog review. Return is directly to U8's existing ground via, but common return impedance has not been extracted; do not call it quiet solely because it is rooted.

R125 ordinary1E rated power0.1 W implies sqrt(P×R)=3.162 V nominal continuous-rated voltage at100Ω; the family75 V cap is not the allowable voltage across this particular resistance. Published short-overload testing and unassured pulse plots are not repetitive-reset qualification. New0402 pulse/thermal assessment must not inherit previous0603 approval.

Assembly qualification remains false: actual switch/socket/plate/keycap envelope and its height/registration are not verified. The old misread1.68 mm socket-strip claim is explicitly withdrawn and must not be reused. Source courtyard clearances do not establish socket/body/terminal clearance. A complete electrically screened isolated candidate may be built for investigation after the expanded contract review, but neither construction nor a clean DRC selects it for production.

## Review/construct/verify sequence

1. Independent read-only review of these exact31 retirements, UVLO/OVLO boundary contacts, R121 ground contact, support bridge, part/land assumptions and complete route; parent approval of expanded contract.
2. Build complete separate unselected schematic/BOM/local footprint/layout candidate from exact selected source. No partial or known-colliding CAD. Preserve all source settings and accepted labels. Use ≥0.8 mm actual reference ink for changed/new references without new avoidable silkscreen defects.
3. Immediately report actual board hash/inventory and first native DRC, rather than spending a long cycle on a replay harness. Save prefill and filled states separately.
4. Verify exact immutable old objects and explicitly changed pad/track contact ledger; unchanged all-net partition outside this bounded contract; pin→R→C→ground order and no bypass; schematic/netlist/ERC/parity; all-layer drill/source/decoupling/ground rooted graph; actual masks/paste/courts/physical gaps.
5. Compare actual In1/In2 and all other fill polygons, every old shadow and complete new reference coverage against exact source, with zero unapproved loss. Preserve failed variants honestly. Independent actual-candidate review and analog binding are required before any adoption decision.

## Primary sources and access limits

- KOA RK73H family: https://www.koaspeer.com/catimages/Products/RK73H/RK73H.pdf (retrieved2026-11-04); KOA lands: https://www.koaspeer.com/pdfs/Appendix_B.pdf.
- Vishay TNPW e3: https://www.vishay.com/docs/28758/tnpw_e3.pdf (revision10-Apr-2026); full IPC lands: https://www.vishay.com/doc?28950 (revision12-Jul-2022). Proposed ordering grammar, dimensions and land option verified; no procurement/availability claim.
- Murata exact-part current SimSurfing index: https://ds.murata.com/simsurfing/mlcc.html?oripartnumbers=%5B%22GRM155R71H103KA88D%22%5D&partnumbers=%5B%22GRM155R71H103KA88%22%5D&rgear=jomoqke&rgearinfo=au . Parent verified its current part listing; this worker's direct rendered page contains controls only. The exact current product/PDF endpoints returned403, and the historical-01 PDF returned404 on this worker's latest fetch. No access restriction was bypassed. Current terminal dimensions/land approval remain conditional. Conservative C terminal envelope uses max body1.05×0.55 and0.40 terminal length; historical secondary copies show0.35 maximum, not used to shrink the screen.
