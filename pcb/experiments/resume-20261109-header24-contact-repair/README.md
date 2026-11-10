# GPIO24 routing and guarded-contact repair

Selected development checkpoint: board SHA256
`637ed688ce3a593be455cca977f634b4fdeef9e721839eb1588541c1f324118d`.
Source: `../resume-20261109-silk-height/`, board SHA256
`ddea15f7eb9188617f81af2e998ed49bf385cfcc473d68bd40beb66ec4ff6020`.
**Eight open pairs remain: two header and six MCU pairs. Not manufacturing-ready.**

GPIO24 at U13.12 joins the existing J3.5/U11.16 component. Surrounding surface
routes are rebuilt; an existing GPIO26 via at (96.65,41.625) mm is reassigned to
GPIO10 while restoring GPIO26 through its other existing vias. All 383 footprint
serializations and every drilled object remain identical. Both inner GND fills
remain identical. `qa/routing-scope.json` lists every removed/added primitive and
all routes. No new or moved holes, netlist changes, rule relaxation or exceptions
to unresolved opens were introduced.

Ten outer-layer 0.25 mm tracks terminating at 0.25 mm via drills are widened to
0.26 mm. This removes isolated numerical fragments and reduces guarded-contact
failures from 51 to zero. The 2 nm guard is unchanged. The separate repair packet
under `qa/contact-repair/` proves the original failures and viable-node mapping.
Its optional native exact polygon-containment check remains explicitly FAIL:
five tracks have 48..465 nm² meshing residuals. Ideal analytic fixed-centerline
capsule widening is a separate inclusion argument. No hardware margin is inferred.

`qa/native/RESULT.json`: fresh KiCad 9.0.2 reports 8 opens, 26 warnings, zero other
DRC errors, ERC/parity zero, raw netlist identity and all 58 CAD files byte-identical
after cold refill. The complete fresh material export is `qa/material-graph.json.gz`.
`qa/refined8-material-comparison.json` proves every old named-pad component
preserved, only GPIO24 merged, all 938 barrel records unchanged, and 21,615
unaffected direct contacts retained without overlap reduction. The source-bound
routing/width changes are explicit exclusions, not undisclosed contact waivers.

`qa/merged8-reference-local-audit.json` checks 124 added/widened signal track
shadows on BOTH inner planes, subtracting actual holes and separately recognizing
fixed own-via transition regions (via radius + 0.2 mm recorded conservative clearance envelope + 0.005 mm
polygon allowance). All shadows outside those transition regions are covered.
No new unsupported region is tolerated. Original same-net unsupported material
is separately available to the audit; the final candidate needs no new exception.

`qa/refined8-zone-scope-fast.json` checks all GND fill loss after actual holes:
outer-layer allowed regions are the explicitly changed track/via geometries plus
their recorded clearance envelope and polygon allowance. Loss outside these regions is zero;
both inner planes have zero loss and gain. Identical hole-owner geometry is
proved before using exact Boolean algebra to subtract holes after set difference.

Reproduce native checks from repository root with a fresh output directory:

```sh
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint pcb/experiments/resume-20261109-header24-contact-repair --expected-opens 8 --output .omo/evidence/header24-native-new --material
uv run tools/check_pcb_portable.py --output .omo/evidence/header24-portable-new
```

`qa/netlist.xml` preserves the source's exact stored export pinned by the portable
wrapper; all schematic dependencies remain identical. `qa/native/netlist.xml` is
the separately fresh native export verified against the board. Earlier full WKL
and HHKB ARM build evidence still applies to the unchanged 22-file overlay.
LED qualification stays OFF. Routing, active power, SI/EMI, thermal, mechanical
fit, physical USB/matrix/VIA and hardware qualification are still incomplete.
The local scripts/full exploratory logs remain under
`.omo/evidence/pcb-routing-20261109/`; current state and acceptance counts are
recorded independently in `pcb/current.json` and this checkpoint's `DECISION.json`.
