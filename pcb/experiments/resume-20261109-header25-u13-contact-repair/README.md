# GPIO24 and GPIO25 U13/header routing, with contact repair

Selected development board SHA256:
`df21164e0a5a5a711c206739d603bb581cc65adda2d5c9ea6472f69ca00018d4`.
**Seven open pairs remain: U11's GPIO25 header connection and six MCU pairs.**
The checkpoint is not manufacturing-ready; routing continues.

Relative to the preserved November 9 nine-open [silk checkpoint](../resume-20261109-silk-height/README.md), GPIO24's U13 component joins its existing J3/U11 component, and GPIO25's U13/J3 components join. Three existing vias are reassigned, with their original signals restored: GPIO26→GPIO10 at (96.65,41.625), GPIO10→GPIO25 at (88.7,43.2), and GPIO27→GPIO25 at (92.9,42.5) mm. All 383 footprint serializations, all drilled geometry and both inner GND fills remain unchanged. The cumulative removed/added objects and via net changes are explicit in `qa/routing-scope.json`.

The ten-track contact repair from the preceding [eight-open checkpoint](../resume-20261109-header24-contact-repair/README.md) is carried forward. Its [source-bound proof and limits](../resume-20261109-header24-contact-repair/qa/contact-repair/README.md) remain preserved, including the explicitly failed optional native exact polygon-containment assertion. No guard or rule was relaxed.

Fresh `qa/native/RESULT.json` records 7 opens, 26 warnings, zero other DRC errors, ERC/parity zero, board/netlist identity and 58 byte-identical cold-refilled CAD files. The complete recomputed material graph is `qa/material-graph.json.gz`. `qa/header7-reference-guard0-comparison.json` proves zero guarded-contact failures, every old named-pad component retained, exactly the two intended merges, all 938 barrel records unchanged and all 21,566 unaffected direct contacts retained without reduced overlap. Barrel records are compared by UUID, independent of iteration order.

`qa/merged7-reference-audit.json` checks 184 added/widened signal-track shadows against BOTH inner GND references. Actual drill material is excluded; fixed own-via transition windows use unchanged via radius + the recorded 0.2 mm conservative clearance envelope + 0.005 mm polygon allowance. All shadows outside those windows are covered; no new unsupported contour is accepted. The audit also retains the original same-net unsupported footprint separately.

`qa/refined7-zone-scope.json` checks all GND fill loss after actual holes. Inner loss and gain are zero. Outer loss is zero outside only the explicitly retired/added/reworked track and via clearance regions. Identical hole-owner geometry is established before applying exact Boolean subtraction algebra. There is no numerical loss tolerance.

Reproduce from repository root, using fresh output directories:

```sh
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint pcb/experiments/resume-20261109-header25-u13-contact-repair --expected-opens 7 --output .omo/evidence/header25-native-new --material
uv run tools/check_pcb_portable.py --output .omo/evidence/header25-portable-new
```

`qa/netlist.xml` is the unchanged source export pinned by the portable wrapper; `qa/native/netlist.xml` is the separately fresh export checked against this board. Every schematic dependency remains unchanged. Full WKL/HHKB ARM build evidence still applies to the unchanged firmware overlay. LED qualification remains OFF. Active power, SI/EMI, thermal, physical fit and hardware qualification remain incomplete. Full local scripts/exploratory logs remain under `.omo/evidence/pcb-routing-20261109/`; this packet retains the passing checkpoint and machine-readable decisions.
