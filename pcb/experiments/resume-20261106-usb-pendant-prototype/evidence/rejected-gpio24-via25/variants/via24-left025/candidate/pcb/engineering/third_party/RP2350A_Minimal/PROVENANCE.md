# Raspberry Pi RP2350A Minimal R4 / S1

Official source: https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-010328-CA-1-RP2350A%20Minimal%20KiCAD.zip

Downloaded 2026-11-01. Archive SHA256: c0b858d78f56fa271a827064198e8ee81e4ec246234ce6659be8a1fcd877d06b

MIT license included. Extracted official U1 QFN thermal-via footprint, L1 polarized inductor footprint, and symbol pin definitions. Core net topology independently adapted to Maru60. No third-party case/keyboard board copied. This license covers these vendor elements, not a unilateral license choice for the Maru60 hardware. Reference CAD is KiCad 10; new project emits KiCad 9-compatible schema.

2026-11-02 addition: `C_0402_Official_R4_Wide.kicad_mod` is extracted from reference C6 (same wide land pattern used for C7), preserving pad, mask, paste, courtyard and fabrication geometry. This pattern is necessary for the reference's VREG_LX neck; substituting generic0402 pads is not equivalent. Candidate local signal/power routing is adapted from the same MIT R4 board with an explicit reflected transform; the reference's board outline and full-board plane outlines are not reused.

2026-11-02 GPIO fanout addition: `gpio-route-reference.json` records 91 GPIO0..19 signal segments from the same official board, with the exact source PCB SHA256. `route_mcu_reference_escape.py` uses only the connected proximal F.Cu escape path from each QFN pad, reflects it to Maru60 B.Cu (`x=211-y_ref`, `y=181.5-x_ref`), then truncates it before Maru60's edge. Terminal via fanout is newly routed and validated against actual Maru60 geometry. No reference board outline, complete board routing, or reference plane outline is copied by this GPIO workflow.
