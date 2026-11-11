# Maru60 PCB — order package (JLCPCB)

**Status: order candidate for a first prototype run.** The CAD checks are
clean, every part has been checked against its data sheet, the power tree and
the critical signals have been simulated, and the exported files have been read
back and compared with the board. No board has been built: electrical
behaviour, fit and firmware are unproven on hardware. Order a small quantity
(5 boards, 2 assembled) first.

Source board: [`resume-20261111-order-candidate`](../experiments/resume-20261111-order-candidate/README.md),
SHA256 in [`PROVENANCE.json`](PROVENANCE.json). Regenerate everything here with
`.venv/bin/python pcb/tools/export_order_package.py`.

| File | Use |
| --- | --- |
| `maru60-gerbers.zip` | Upload as the PCB. 11 Gerber layers, PTH and NPTH drill files. |
| `bom-jlcpcb.csv` | Upload as the assembly BOM (54 part numbers, 333 placements). |
| `cpl-jlcpcb.csv` | Upload as the placement file (138 top, 195 bottom). Rotations and centres are fitted to JLCPCB's own footprints. |
| `bom-full.csv` | Every footprint, including what is *not* assembled and why. |
| `parts.json` | Part selection rules and the stock snapshot date. |
| `jlcpcb-placement.json` | Per part: the rotation and centre fitted to the footprint JLCPCB places from, and how well the two land patterns agree. |

## 1. Before ordering: parts to arrange

| Part | Situation on 2026-11-11 | What to do |
| --- | --- | --- |
| Everything in `bom-jlcpcb.csv` | in stock | Nothing to source separately. |
| Hot-swap sockets, Kailh CPG151101S11 (C2803348) | 0 in stock | Not in the BOM. Hand-solder one per switch (62 for HHKB/WKL), or pre-order and add the `SW*` rows from `bom-full.csv`. |
| `U13` TPD6E05U06RVZR | 51 in stock | Check stock on the day. |
| `U1` RP2350A | in stock | Stepping **A4** is required. Ask in the order remark that the marking is confirmed. |
| `L2` XAL4030-472MEC | in stock, about USD 8 | Optional saving: any 4.7 µH, Isat ≥ 3.4 A, DCR ≤ 45 mΩ part on the same 4 × 4 mm land. |

Stock moves daily (the latch-off `TPS2553DBVR-1` went from 16 to 6 during this
review, which is why the BOM names the constant-current `TPS2553DBVR`).

## 2. PCB options

| Option | Value |
| --- | --- |
| Layers / size / thickness | 4 / 285 × 94.6 mm / 1.6 mm |
| Stackup | JLC04161H-7628 (standard). **No impedance control**: RP2350 USB is full speed only. |
| Copper | 1 oz outer, 0.5 oz inner |
| Minimum track / space | 0.15 / 0.15 mm |
| Vias | 0.25 mm drill, 0.5 mm pad, tented |
| Surface finish | ENIG (0.4 mm pitch QFN, exposed socket pads) |
| Remove order number | Specify a location, or pay for removal |
| Edge rails / fiducials | The board has no fiducials or tooling holes, and 23 parts sit within 2.5 mm of an edge (the USB connector is at the edge). Let JLCPCB add edge rails and fiducials ("added by JLCPCB"). |

## 3. Assembly options

- **Assemble both sides** (Standard PCBA). Top: 63 LEDs, 63 capacitors, F1,
  R100, R101, R118, R120, R177, R179, R180, R181, R183, R187, C144. Bottom:
  everything else.
- Turn on **Confirm Parts Placement** and look through the preview before
  paying. The placement file is not raw KiCad output: for each part the
  footprint JLCPCB uses was fetched and the rotation and centre that put its
  pads on the board's pads were solved (332 of 333 placements; `R123`, a
  resistor, uses the plain convention because JLCPCB publishes no footprint for
  it). The preview should therefore already be right. Still check:
  - `L1`: polarised, and JLCPCB's footprint cannot tell which end has the dot.
    The dot on the part goes to the silkscreen dot (the +1V1 pad).
  - `D100`, `U2`, `U7`, `SW100`, `SW101`: JLCPCB's land pattern differs from the
    board's by 0.15–0.3 mm, so the drawn outline will look slightly off-centre
    on the pads. Orientation is what matters.
  - `U1`: pin 1 at the silkscreen mark; stepping A4.
  - LEDs: every land site has a silkscreen dot at pin 1 (DIN).
  - `J1`: centred on its pads (JLCPCB's origin for this connector is 1.3 mm
    from KiCad's; the file already accounts for it).

## 4. After the boards arrive

1. Inspect, then power from a current-limited 5 V supply (300 mA limit) before
   using a computer port. Expected rails: `TP3` 4.0 V, `TP4` 3.3 V, `TP5` 1.1 V;
   idle current about 20 mA.
2. With a scope on `TP3`, switch a load on the 4 V rail (the LED rail is the
   easy one) and check that it settles without ringing: the simulated buck
   phase margin is 46–51° with the 22 pF feed-forward capacitor `C143`. If it
   rings, `C143` can go up to 47 pF on the same pads.
3. Hold BOOTSEL (`SW100`) while plugging in; the board must enumerate as an
   RP2350 mass-storage device. Flash `maru60_rp2350_via_hhkb.uf2` (HHKB) or
   `maru60_rp2350_via.uf2` (WKL) from the checkpoint's
   [`qa/qmk-build`](../experiments/resume-20261111-order-candidate/qa/qmk-build/RESULT.json).
4. Solder the sockets and test the matrix.
5. Per-key LEDs stay off: the firmware keeps `MARU60_LED_POWER_QUALIFIED` at 0
   until the LED rail has been measured. Full white (1.14 A) is far above the
   174–234 mA limiter; keep the brightness cap.
6. When the LEDs are first enabled, look at the data input of one LED after a
   long hop (`LED59`, `LED69`) with a scope: the high level must stay above
   3.1 V after the edge. 23 hops have a 100 Ω series resistor (`R115`–`R119`,
   `R170`–`R186`, `R188`); the others are 27 mm or shorter.

Use switches with an SMD-LED opening in the bottom housing. The spacebar
stabilizer holes are reversed (wire at the back) so they clear the board edge.

## 5. Layout options and their limits

The default build is HHKB or WKL with a **normal Caps Lock** and a **split right
Shift (1.75U + 1U)**.

| Option | What it needs |
| --- | --- |
| Stepped Caps Lock | Move `LED75` from its bottom relay site to its top pads (in the stepped switch window) and `LED30` from its window to its second top site in the row gap above. Each LED has both sites on the board; fit exactly one. |
| 2.75U right Shift, plate-mount stabilizer | Nothing to change: the stabilizer hangs from the plate about 1.5 mm above the PCB by nominal dimensions and `LED54` is 0.65 mm tall. Not checked against a real part. |
| 2.75U right Shift, PCB-mount stabilizer | Move `LED54` from its window to its second site in the row gap 9 mm to the left (pin-1 dot on the silkscreen); its window site lies under the left stabilizer housing. Fit exactly one site. Planned from nominal dimensions; `LED55` sits about 0.1 mm from the right stabilizer housing, so check the fit on the part. |
| 2U Backspace | Not supported. Backspace is split only: a third switch position between two hot-swap sockets overlaps both, and would need solder-in receptacles instead. |

## 6. What was changed and checked

The [checkpoint README](../experiments/resume-20261111-order-candidate/README.md)
lists every change from the 0/0 prototype, the analyses run on the result
(JLCPCB rule check, power simulation, copper resistance and heating, signal
integrity, Gerber read-back) and what was deliberately left as it is.
