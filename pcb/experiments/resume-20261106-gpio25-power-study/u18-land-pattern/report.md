# U18 TPS62932DRLR native land-pattern review

**Finding: copper geometry and pin orientation match TI's DRL0008A example. No CAD edit is warranted from this check. Keep assembly and hardware qualification provisional.**

## Evidence and scope

Read-only check of `maru60.kicad_pcb`, selected USB-pendant prototype, source commit be51692. Board SHA-256 is `41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5`. Native KiCad 9.0.2 extracted U18's actual inline pads rather than accepting its SOT-583-8 name. All eight normalized pads also agree with the installed KiCad library footprint.

Official source: https://www.ti.com/lit/ds/symlink/tps62932.pdf ; supplied local PDF SHA-256 `16ec2eac43c7374eb9e7edd7df7bdb24de6862f695e1582c68716ced4820e5f6`. Physical PDF pages 48, 49 and 50 were rendered and visually inspected. Datasheet header is SLUSEA4D, revised August 2022; the attached package/land/stencil drawings are **DRL0008A, drawing 4224486/G, November 2024**. Do not describe those drawings as August 2022 drawings.

## Dimensional result (mm)

- Eight rounded rectangular copper pads: 0.67 × 0.30; TI example 0.67 × 0.30; deviation 0.
- Adjacent pitch: 0.50; TI 0.50; deviation 0.
- Opposing row centers: 1.48; TI 1.48; deviation 0.
- Corner radius: 0.05 (ratio 0.1666666667, quantized to native units); TI R0.05; deviation 0 at native precision.
- Derived clearances: adjacent copper edge gap 0.20, opposing edge gap 0.81, total transverse copper span 2.15, longitudinal copper span 1.80. No exposed center pad is shown or required by this eight-terminal drawing.
- Effective paste expansion is 0 in both dimensions. Eight B.Paste apertures therefore equal the copper pads, matching the example's aperture dimensions. There is no pad or footprint paste override.
- Effective mask expansion is **0.000 per side**, inherited from board settings; no local override. Nominal mask openings coincide with copper outlines. TI depicts preferred non-solder-mask-defined pads with **0.05 maximum** clearance around them, and a mask-defined alternative with **0.05 minimum** copper overlap. Zero nominal expansion does not exceed the NSMD maximum, but does not establish positive mask clearance or robust NSMD behavior under registration tolerance. This is an unresolved fabrication detail, not a proven violation of a mandatory 0.05 expansion requirement. Do not blindly enlarge masks without fabricator agreement.

## Numbering and backside transform

U18 is on B.Cu at (179.25,84.25), 90 degrees. Canonical component-top-view pad 1 is (-0.74,-0.75), pads 1–4 run down the left row and 5–8 run up the right row, as on TI's drawing. KiCad's stored inline backside coordinates have Y mirrored; they must not be compared directly to an unmirrored front library footprint.

For canonical (x,y), inline coordinates are (x,-y), and board coordinates are (179.25-y,84.25-x). Native API board coordinates agree. Pad 1 is (180.00,84.99), 4 is (178.50,84.99), 5 is (178.50,83.51), and 8 is (180.00,83.51). Net correspondence is RT1, EN2, VIN3, GND4, SW5, BST6, SS7, FB8; RT and EN are explicitly named unconnected/float nets. This check finds no swapped numbering or incorrect backside transformation.

## Body and silkscreen

B.Fab body spans 1.20 × 2.10, centered on the pad pattern, consistent with the drawing's molded-body width 1.1–1.3 and length 2.0–2.2. The separate 1.5–1.7 package dimension includes the leads; it should not replace the 1.20 fabrication-body width. Chamfer and B.SilkS triangle are at pad 1 after the backside transform. Silkscreen end lines are at inline Y=±1.16 with 0.12 stroke; nearest pad edge is |Y|=0.90, yielding 0.20 nominal silk-to-copper gap. Silk centerlines lie 0.11 beyond the nominal body ends. Courtyard is 2.64 × 2.60, giving 0.245 transverse clearance outside copper and 0.25 beyond nominal body ends. These are footprint alignment checks, not a new whole-board DRC or proof of all neighbor clearances.

## Mandatory versus recommended; remaining gates

The vendor explicitly labels land pattern and stencil as **examples**, with parenthesized reference dimensions and alternate IPC/fabricator/assembly recommendations permitted. Electrical terminal identity and physical compatibility must remain correct; there is no demonstrated mandatory geometry violation here. A geometric match does not certify solderability.

TI's aperture example assumes a **0.10 mm stencil**. The PCB file does not establish the manufactured stencil thickness, laser-cut profile, paste material/release performance, reflow process, inspection criteria or assembler acceptance. Confirm the stencil and mask strategy with the fabricator/assembler. This check also does not qualify thermal layout, current handling, transient/loop behavior, EMI, reliability or real hardware. Keep the existing provisional DRL/paste/assembly status; the copper-dimensional subquestion alone is now evidenced as a match.

## Reproduction and redistribution

Run `run-kicad.sh /usr/bin/python3 continuation-be51692/u18-land-pattern/replay.py` from the Maru60 work root. Script reads source CAD and installed footprint, asserts source hashes and geometry, and writes only this review's JSON. `geometry.json` contains native coordinates, nets, effective settings and graphics. `source-hashes.json` records all source hashes.

Only files named in `allowlist.json` are deliverables. Vendor PDF, extracted full text and rendered vendor screenshots are deliberately excluded; temporary review pixels remain outside the output directory. No CAD, schematic qualification status, repository commit, manufacturing order or external state was changed.
