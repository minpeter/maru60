# PCB requirements and evidence ledger

| Requirement | Draft implementation / evidence | State |
|---|---|---|
| GH60 size | 285.0 × 94.6 mm reference from `spec/boards.json` (komar007/gh60 rev C) | Reference recorded; own Edge.Cuts not designed |
| RP2350A | QMK `em-rp2350` port is the firmware investigation baseline | Target selected; schematic/pin map pending |
| USB-C | Rule60 v7.10 notch 12.8 mm wide; surveyed 6095 center X ≈18.0 mm in GH60 frame | Need own connector selection and actual CAD fit |
| MX hot-swap | Required | Socket footprints and collision study pending |
| WK / WKL / HHKB | Required as selectable mechanical layouts | Need complete multi-layout switch-site model |
| Spacebar | 6.25U and 7U | Bottom row envelope model included |
| Alternate keys | Split/non-split Backspace, right Shift, stepped Caps | Sites are illustrative; plate geometry pending |
| Stabilizers | PCB-mount and plate-mount | Require compatible alternate plate cutouts |
| VIA | Required; QMK Raw HID/dynamic keymap path identified | No Maru60 build or GUI remap/persistence validation |
| Per-key RGB + underglow | Required, separate chains contemplated | LED count/topology, power, thermal and timing checks pending |
| Wireless | Undecided | No battery/radio committed |
| Hardware license | Open hardware intended | Exact license not selected; source/provenance audit pending |

## Provenance and reuse

- The GH60 dimensions/grid and Rule60 case interface values are referenced from this repository's recorded interface spec. The proposed board is a new design; no third-party PCB CAD is copied in this draft.
- PH60 was identified during research as CC BY-NC-SA; do not copy its CAD into this design.
- Waffling60 was identified as CERN-OHL-S2; no source geometry has been imported. Redrawing does not itself establish a different provenance.
- Manufacturer drawings/datasheets may be used to place chosen components, with sources and revisions logged when selected.
- Repository root licensing currently pertains to existing project content. This draft does not assert that the PCB inherits a final hardware license.

## Mechanical revision provenance

The PCB work starts from `main` `03c92914fb0acad659a554024d689673794ea5a9`, preserving the housing branch separately. Mechanical reference for fit planning is open PR #1, head `1d89453825131438929ad887e2b0264f8f620cd2`: top case v7.10 and bottom case draft v0.11, as described in that PR and its interface spec.
