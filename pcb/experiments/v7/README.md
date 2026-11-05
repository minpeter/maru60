# MARU60 V7 protection integration — checkpoint02

Actual full-board routed-work-in-progress candidate. Source/main/A22 unchanged. All382 footprints are on-board, comprising380 electrical parts plusSTAB_RS1/LOGO1. PCB SHA256 `6164d155b2970c7033c02e52722f47c42aec38df078ca4034c01381d1f103864`.

## Exact verified state
- Native ERC0, hard geometry DRC0, schematic parity0; XML↔PCB1,062-pin parityPASS.
- **53 unrouted connections and123 warnings. Not fabrication-ready and not electrically qualified.**
- Per-UUID raw→Load→connectivity→refill net assignmentPASS for11,934 objects. Project/rules remain byte-identical to accepted main.
- Corrected boundary layer selection:30 falsely cut original objects restored;67 actual common-layer power/ESD boundary objects retired, plus one guardedCOL4 detour. Cross-net actual-source collision count0. The checkpoint01 erratum is preserved.
- 9381 retained original copper objects have exact geometry; unaffected original footprint poses and1,260 retained pad shapes preserved;909 main pin endpoints checked. Every new routing object is explicitly ledgered.
- Grouped MAX38902A and TPS62932 local placements; explicit output/BYP/sense, buck/input/GPIO routes and24 local ground connections added.
- GND audit usesUSB J1.A1 as source and actual filled polygons. 9 ground pads remain unreached: [['U13', '5'], ['U13', '10'], ['J3', '4'], ['J3', '7'], ['C128', '2'], ['U2', '2'], ['U2', '4'], ['U2', '9'], ['U8', '8']]. This is not a ground-complete claim.

## Important unfinished connections
LDO IN/EN, buck SW-to-L2 and soft-start, some fine-pitch GND/EP connections, inter-block rails and GPIO/USB connections still need routing. In particular U2 EP/ground has NOT been declared thermally implemented. A completed per-net continuity/source/return proof and a local-loop/Kelvin geometry review remain required. No current-carrying or stability conclusion follows from DRC.

## Remaining electrical release gates
Reset-to-RUN hardware; LED powered-off/brownout injection; USB startup/configured/suspend current; real effective capacitance/ESR and component qualification; low-input/dropout and fuse coordination; actual thermal/mechanical/ESD/fault/USB tests. Current LV1T125 parts and76 LEDs remain; no150mA brightness cap was adopted. Optional20/21V survival is not an adopted requirement. No main merge, fabrication upload, purchase or whole-safety approval.
