# Maru60 PCB — order package (JLCPCB)

**Status: order candidate for a first prototype run.** The CAD checks are clean
and every part has been checked against its datasheet, but no board has been
built yet: electrical behaviour, fit and firmware are still unproven on
hardware. Order a small quantity (5 boards, 2 assembled) first.

Source board: [`resume-20261111-order-candidate`](../experiments/resume-20261111-order-candidate/README.md),
SHA256 in [`PROVENANCE.json`](PROVENANCE.json). Regenerate everything here with
`.venv/bin/python pcb/tools/export_order_package.py`.

| File | Use |
| --- | --- |
| `maru60-gerbers.zip` | Upload as the PCB. 11 Gerber layers, PTH and NPTH drill files. |
| `bom-jlcpcb.csv` | Upload as the assembly BOM (51 part numbers, 307 placements). |
| `cpl-jlcpcb.csv` | Upload as the placement file (130 top, 177 bottom). |
| `bom-full.csv` | Every footprint, including what is *not* assembled and why. |
| `parts.json` | Part selection rules and the stock snapshot date. |

## 1. Before ordering: parts to arrange

| Part | Situation on 2026-11-11 | What to do |
| --- | --- | --- |
| `U2` AP2112K-3.3TRG1 (C51118) | in stock | Replaces the out-of-stock MAX38902AATA+T. 3.3 V 600 mA in SOT-23-5; no BYP capacitor, output sense or minimum load. |
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

## 3. Assembly options

- **Assemble both sides** (Standard PCBA). Top: 63 LEDs, 63 capacitors, F1,
  R100, R101, R120. Bottom: everything else.
- Turn on **Confirm Parts Placement** and check the preview yourself. The
  rotations in `cpl-jlcpcb.csv` are KiCad's and carry **no JLCPCB per-package
  correction**, so some parts will look turned in the preview and must be
  corrected there. Check at least:
  - `U1`–`U3`, `U5`–`U8`, `U10`–`U13`, `U18`: pin 1 against the silkscreen.
  - `L1`: polarised. The dot on the part goes to the silkscreen dot (the +1V1
    pad). Do not describe it by +/−.
  - `LED1`–`LED76`: no silkscreen mark. DIN is pad 1; on the top side it is
    the pad at the lower left of each LED (toward the front-left of the board).
  - `D1`–`D62`, `D100`: cathode band to the silkscreen bar.
  - `J1`, `J3`, `Y1`.

## 4. After the boards arrive

1. Inspect, then power from a current-limited 5 V supply before using a
   computer port. Expected rails: `TP3` 4.0 V, `TP4` 3.3 V, `TP5` 1.1 V.
2. Hold BOOTSEL (`SW100`) while plugging in; the board must enumerate as an
   RP2350 mass-storage device. Flash the UF2 from `pcb/firmware`.
3. Solder the sockets and test the matrix.
4. Per-key LEDs stay off: the firmware keeps `MARU60_LED_POWER_QUALIFIED` at 0
   until the LED rail has been measured. Full white (1.14 A) is far above the
   174–234 mA limiter; keep the brightness cap.

Use switches with an SMD-LED opening in the bottom housing. The spacebar
stabilizer holes are reversed (wire at the back) so they clear the board edge.

## 5. Layout options and their limits

The default build is HHKB or WKL with a **normal Caps Lock** and a **split right
Shift (1.75U + 1U)**.

| Option | What it needs |
| --- | --- |
| Stepped Caps Lock | Move `LED75` from its bottom relay site to its top pads (in the stepped switch window) and `LED30` from its window to its second top site in the row gap above. Each LED has both sites on the board; fit exactly one. |
| 2.75U right Shift | `LED54` lies under the left stabilizer housing and cannot simply be left out (the LEDs are in series). Not supported with a stabilizer in this revision. |
| 2U Backspace | Not supported. Backspace is split only. |

## 6. What changed since the 0/0 prototype

See the [checkpoint README](../experiments/resume-20261111-order-candidate/README.md).
In short: 64 top-side parts moved out from under switch housings, `C200` moved
to the bottom beside the LED rail via and is populated again, the Caps Lock LEDs
got a second land site, three footprint/layout corrections from the datasheet
review, the out-of-stock MAX38902A LDO became an AP2112K-3.3 in SOT-23-5 (so
`C142`, `R163` and the In2 sense jumper went away), switch pin holes grew to
Kailh's 3.05 mm, every SK6805 land site got a pin-1 dot, the buck input
capacitor went to 10 µF on both C136 and C137 and `C100` to 22 µF, and five
values now name parts that can be bought.
