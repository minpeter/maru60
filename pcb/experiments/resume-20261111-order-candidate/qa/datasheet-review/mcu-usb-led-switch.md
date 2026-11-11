# Pre-order datasheet review — MCU / USB / LED / connectors / switches

Board: `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`
Date: 2026-11-11. Read-only; no tracked file was changed.

Method: every datasheet below was downloaded and read (text + rendered drawing pages), then compared
against `pin-nets.txt`, `footprint-pads.txt`, and absolute pad coordinates taken from `board.json` and the
embedded footprints in the `.kicad_pcb`. Handedness was checked in absolute board coordinates
(KiCad X right, Y down, viewed from F.Cu), not from the un-flipped script frame.
Note on the script frame in `footprint-pads.txt`: for B.Cu parts it is the view from the bottom side
(X mirrored). It is self-consistent; nothing below depends on it.

**Result: no BLOCKER found. Three SHOULD-FIX items (two tiny layout edits near the core regulator, one
assembly-data action). Ranked list is at the end.**

---

## U1 RP2350A (QFN-60)

1. **Pins: MATCH (60/60 + EP).** All 60 pin functions and the EP=GND agree with Figure 2.
   Checked individually incl. 44 ADC_AVDD, 46 VREG_AVDD, 47 VREG_PGND, 48 VREG_LX, 49 VREG_VIN, 50 VREG_FB,
   51 USB_DM, 52 USB_DP, 53 USB_OTP_VDD, 54 QSPI_IOVDD, 55 SD3, 56 SCLK, 57 SD0, 58 SD2, 59 SD1, 60 SS.
2. **Footprint: MARGINAL vs the datasheet drawing, IDENTICAL to Raspberry Pi's own reference footprint.**

   | | Datasheet Fig. 148 | Board (`RP2350A_QFN60_Official_R4`) |
   |---|---|---|
   | Pitch | 0.40 | 0.40 |
   | Lead pad | 0.875 x 0.20, spans 3.000–3.875 from centre | 0.70 x 0.23, spans 3.10–3.80 |
   | EP | 3.40 x 3.40 | 3.40 x 3.40, 9 vias 0.6/0.25 |

   Pads are 0.175 mm shorter (0.10 less heel, 0.075 less toe) and 0.03 mm wider (copper gap 0.17 mm).
   Package lead is L 0.35/0.40/0.45, b 0.13/0.18/0.23 (Fig. 147), so heel fillet is ~0 and toe 0.30 mm.
   I downloaded Raspberry Pi's "RP2350A Minimal R4-S1" KiCad project and its `rpi_rp2350a_vias` footprint is
   pad-for-pad the same (0.7 x 0.23 @ ±3.45, EP 3.4, same 9 vias). Accept as-is.
   Paste: the embedded B.Cu copy has all 76 paste apertures on B.Paste (60 leads + 16 EP windows, EP coverage
   ≈38 %); mask is opened over the EP except over the vias. EP will be soldered.
3. **Application circuit vs "Hardware design with RP2350" + datasheet §6.3.8: OK, two layout deviations.**
   I mapped every support part into U1's own frame and compared with the reference board:

   | Function | Ref (RPi Minimal) | Board | Verdict |
   |---|---|---|---|
   | L1 3.3 µH AOTA-B201610S3R3-101-T | (2.0, −7.2), pad1 = +1V1, pad2 = VREG_LX | same position, same nets | OK |
   | COUT 4.7 µF (VREG_FB/DVDD) | C7 (2.0, −5.55) | C103 (2.0, −5.55) | OK |
   | CIN 4.7 µF (VREG_VIN) | C6 (2.0, −4.61) | C102 (2.0, **−4.84**) | 0.23 mm off — see SHOULD-FIX 2 |
   | VREG_AVDD RC | R3 33 Ω (4.2, −6.9), C9 4.7 µF (4.2, −5.05) | R104 / C104 same | OK |
   | 2nd 4.7 µF at DVDD pin 23 | recommended (§6.3.8.1) | C109 at pin 23 | OK |
   | Crystal ABM8-272-T3, 15 pF x2, 1 kΩ in XOUT | X1/C3/C4/R2 | Y1/C106/C107/R108 same positions and topology | OK |
   | USB 27 Ω | R7/R8 at chip | R102/R103 same positions, 3.9–4.1 mm to pins | OK |
   | Flash CS | 10 k pull-up (DNF in ref), 1 k to BOOTSEL switch | R105 10 k fitted, R106 1 k → SW100 → GND | OK |
   | RUN | internal pull-up | SW101 → R107 1 k → GND, TP6 | OK |
   | ADC_AVDD, USB_OTP_VDD, QSPI_IOVDD, 6x IOVDD | 3V3 | +3V3, 100 nF population adequate | OK |
   | DVDD x3 | 1V1 | +1V1 (pins 6, 23, 39) + VREG_FB | OK |

   - GND vias: two adjacent GND vias at the CIN/COUT ground (116.5/115.9, 78.4) and a separate one for CFILT
     (114.85, 77.65) — as the datasheet asks.
   - Plane cut-out under LX: In2.Cu (the layer next to B.Cu) and In1.Cu have no copper under the LX pad / pin 48
     (rule-area cut-out present) — as Fig. 27 asks.
   - **Deviation A:** a +3V3 zone finger (~0.3 mm wide, x≈117.7–119.1, y≈79.35–79.65 on B.Cu) runs *under the
     inductor body between its two pads*. The reference board has no copper there and §6.3.8.1 says "cut away
     any extra copper underneath the inductor". See SHOULD-FIX 1.
   - **Deviation B:** CIN position, above.
4. Sources:
   - RP2350 datasheet, https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf — Fig. 2 (p.15, pinout),
     §6.3.8 Figs. 25–29 (pp.410–414, regulator schematic/layout/inductor), Fig. 147–148 (pp.1324–1325, package
     and recommended footprint), §1.2.2 pin descriptions.
   - Hardware design with RP2350, https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf —
     §2.1 (regulator, L1/C6/C7/C9/R3), §3.1 (flash, R1/R6), §4 (crystal), §5.1 (USB).
   - Reference KiCad project, https://datasheets.raspberrypi.com/rp2350/Minimal-KiCAD.zip
     (`RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb`).

### L1 polarity (the question asked)

- **Confirmed: the dot end goes to +1V1 (VOUT), the un-marked end to VREG_LX.**
  Datasheet Fig. 26 shows the orientation indicator on the VOUT-side pad; Fig. 28 shows current entering at the
  un-marked end and leaving at the dot. The reference board has L1.1 = +1V1, L1.2 = VREG_LX with the silk dot at
  pad 1.
- Board: pad 1 (118.2, 80.2) = +1V1, pad 2 (118.2, 78.8) = VREG_LX, B.SilkS dot at (117.5, 80.9), i.e. next to
  pad 1. **Netlist and footprint are correct.**
- Caveat for assembly: Abracon's own sheet does not number the terminals, and its marking figure labels the dot
  end "+", the opposite sign convention to Raspberry Pi's Fig. 28 (it only illustrates a current direction).
  Do not describe the part to the assembler by +/−; describe it by dot position. See SHOULD-FIX 3.
- Footprint vs Abracon land pattern: Abracon recommends 1.0 x 1.6 pads with a 1.0 gap (span 3.0 mm); the board
  uses 0.7 x 1.7 at ±0.7 (span 2.1 mm), which is exactly Raspberry Pi's footprint. MARGINAL vs Abracon,
  intentional per reference. Body is 2.0 ±0.2, terminals 0.6 ±0.2.
- Source: https://abracon.com/datasheets/AOTA-B201610S3R3-101-T.pdf (Rev A 9/13/2024), p.1 electrical, p.4
  dimensions/land pattern/marking, p.6 tape orientation.

### Y1 ABM8-272-T3

1. Pins: **MATCH.** Abracon top view: 1 and 3 are the crystal (diagonal), 2 and 4 GND. Board: 1 = XIN, 3 =
   XTAL_OUT, 2/4 = GND, and the B.Cu copy is correctly mirrored.
2. Footprint: OK (1.4 x 1.2 at ±1.1/±0.85, same as RPi reference). The Abracon PDF I could open has no land
   pattern page; terminal drawing only.
3. Circuit: 12 MHz, CL 10 pF, ESR 50 Ω max; 15 pF + 15 pF + 1 kΩ as the guide prescribes.
4. https://abracon.com/datasheets/ABM8-272-T3.pdf (drawing 456603 Rev B, sheets 2 and 4).

### U3 W25Q32JVSSIQ

1. Pins: **MATCH** (1 /CS, 2 DO/IO1, 3 /WP/IO2, 4 GND, 5 DI/IO0, 6 CLK, 7 /HOLD/IO3, 8 VCC) and the
   QSPI_SDn mapping is right.
2. Footprint: OK. Package SS: body 5.18–5.38, H 7.70–8.10, L 0.50–0.80. Pads span 2.775–4.40 from centre →
   toe 0.35–0.55, heel ≥0.27.
3. "IQ" = QE bit fixed to 1; fine for RP2350 boot. 10 k pull-up on /CS present.
4. https://www.winbond.com/resource-files/W25Q32JV%20RevI%2005042021%20Plus.pdf — §3.1 Fig. 1a (p.5), §9.2
   (p.66), ordering information section ("IQ" = QE fixed 1).

---

## J1 GCT USB4105-GF-A

1. Pins: **MATCH.** GCT table: A1/A12/B1/B12 GND, A4/A9/B4/B9 VBUS, A5 CC1, B5 CC2, A6/B6 D+, A7/B7 D−,
   A8/B8 SBU. Board: A6 and B6 both on USB_DP_CONN, A7 and B7 both on USB_DM_CONN; CC1 → R100 5.1 k → GND,
   CC2 → R101 5.1 k → GND (separate resistors); SBU open; shell to GND.
2. Footprint: **OK, exact.** Pad order left→right with the board edge at the bottom, seen from the component
   side: A1/B12, A4/B9, B8, A5, B7, A6, A7, B6, A8, B5, B4/A9, B1/A12 — the board reproduces this when viewed from
   B.Cu (so handedness is right; a mirrored footprint would have swapped CC with SBU). Dimensions: ±3.2 / ±2.4
   (0.6 x 1.15), ±1.75/±1.25/±0.75/±0.25 (0.3 x 1.15), shell slots at ±4.32: rear 0.6 x 1.7 in 1.0 x 2.1,
   front 0.6 x 1.4 in 1.0 x 1.8, 4.18 apart; pegs Ø0.65 at ±2.89, 3.68 from the front slots. All equal.
   One offset: GCT puts the front slot centre 2.60 mm from the PCB edge; on the board it is 2.725 mm
   (edge at y = 0, J1 at y = 3.8). The connector sits 0.125 mm further in than nominal. Harmless; check the
   case opening.
3. Bottom-side mounting changes nothing electrically: the receptacle is rotationally symmetric, both
   orientations of the plug are already supported by A6=B6 / A7=B7 and one Rd per CC pin. The only effect is
   that the part is a "top mount" style sitting on B.Cu, so its mouth centreline is about 1.7 mm below the
   bottom surface (GCT side view) — a case matter.
4. https://gct.co/files/drawings/usb4105.pdf (rev B4, sheet 1: pin table and "Recommended PCB Layout").

---

## LED OPSCO SK6805-EC15 (76 pcs: 64 on F.Cu, 12 on B.Cu)

1. Pins: **MATCH.** Datasheet: 1 DIN, 2 VDD, 3 DOUT, 4 GND. Schematic/netlist the same.
2. Footprint: **OK, exact.** Recommended PCB (top view): 4 GND top-left, 3 DOUT top-right, 1 DIN bottom-left,
   2 VDD bottom-right; pads 0.55 x 0.55 with 0.40 gaps (centres ±0.475). Board pads in absolute coordinates on
   F.Cu: 1 (−0.475, +0.475), 2 (+0.475, +0.475), 3 (+0.475, −0.475), 4 (−0.475, −0.475). Same. The B.Cu
   copies are correctly mirrored.
   Marking: the part has no top-side pin-1 dot in the drawing; the bottom has a triangle between the VDD and DOUT
   pads and the top view shows the IC die on the GND/DIN side. The footprint has no silkscreen mark (only a
   F.Fab chamfer at pad 4 and a "1" at pad 1).
3. Application:
   - Supply: table 8 gives VDD +3.7 … +5.5 V; the IC parameter table is specified at 4.5–5.5 V (typ 5.2 V).
     4.0 V is inside the supply range but outside the characterised range, with 0.3 V headroom to 3.7 V before IR
     drop. Logic threshold VIH = 0.7·VDD = 2.8 V at 4.0 V, so the 4.0 V data swing from the LV1T125 is fine.
   - Current: the "05" IC is 5 mA per channel (15 mA per LED full white), the "03" IC is 3 mA; static 1 mA typ per
     LED. The "-001" suffix on the BOM value is not decoded in the datasheet — confirm which current version the
     ordered part number is.
   - Decoupling: the typical circuit shows 100 nF per LED. Board has 78 x 100 nF on +4V_LED for 76 LEDs, nearest
     cap 3.1–4.3 mm from each LED. OK. Series resistor ~500 Ω on the first DIN is suggested; board has 330 Ω.
   - Height 0.65 mm on F.Cu at (0, ±5.08) from the switch centre: only switches with an SMD-LED window in the
     bottom housing will seat.
4. I found no OPSCO-hosted copy; used distributor mirrors of the OPSCO document
   "SPC / SK68XX-EC15 Rev. No. 06": https://www.rose-lighting.com/wp-content/uploads/sites/53/2020/05/SK68XX-EC15-REV.06-EN1515-RGB-6805.pdf
   (p.4 dimensions, pin table, recommended PCB; p.5 electrical; p.6 IC parameters; p.9 application circuit) and
   Rev. 05 https://ecksteinimg.de/Datasheet/LED/LED0016/SK6805-EC15_REV05_EN.pdf.

---

## MX hot-swap (Kailh CPG151101S11) and Cherry MX hole pattern

1. Pin/hole positions: **MATCH with the Cherry MX circuit-board layout.** Cherry: centre Ø0.157 in (3.988),
   fixation pins Ø0.067 in (1.702) at ±0.2 in, contact pins on the 0.05 in grid at (−0.15, −0.10) in and
   (+0.10, −0.20) in = (−3.81, −2.54) and (+2.54, −5.08) mm. Board, viewed from F.Cu:
   - 57 switches: holes at (−3.81, −2.54) and (+2.54, −5.08), LED at (0, +5.08);
   - SW1, SW2 (next to the USB connector) and the pin-south positions of the Caps / RShift option footprints:
     (+3.81, +2.54) and (−2.54, +5.08), LED at (0, −5.08) — the same pattern rotated 180°.
   Both are the correct chirality for a switch inserted from F.Cu. No mirrored instance exists.
2. Socket land pattern: **UNVERIFIED against a Kailh drawing** (kailhswitch.com serves no PDF; mirrors returned
   404). What I can say: the socket barrels must sit on the switch pins, which is verified above; the pads
   (2.55 x 2.5, 3.275 / 3.302 mm outboard of each Ø3.0 hole, on B.Cu) are identical to the ai03 `MX_V2`
   `MX-Hotswap-1U` footprint I fetched from GitHub, which is the de-facto pattern for this socket.
3. Matrix: D pad 1 (cathode) on ROWn, anode on KEY_n, switch to COLn — consistent with
   `pcb/engineering/key-sites.json` "COL2ROW".
4. Cherry MX series datasheet (Cherry catalogue page 10-3, "Circuit Board Layouts"), copy at
   https://cdn.sparkfun.com/datasheets/Components/Switches/MX%20Series.pdf p.2. cherrymx.de returned HTML only.
   ai03 reference: https://raw.githubusercontent.com/ai03-2725/MX_V2/main/MX_Hotswap.pretty/MX-Hotswap-1U.kicad_mod

## Stabilizers

1. Hole sizes and Y offsets: **MATCH Cherry.** "Spacebar without frame": Ø0.12 in (3.048) holes 0.275 in
   (6.985) from the switch centre on the contact-pin side, Ø0.157 in (3.988) holes 0.60 in further (8.255 on
   the other side). Board uses 3.048 / 3.988 and 6.985 / 8.255 everywhere.
2. X spacing ±11.938 (2.25U/2.75U) and ±57.15 (7U): **UNVERIFIED against a manufacturer drawing** (Cherry's
   dimension "A" table is not in the page I have). They are the standard 0.94 in and 4.5 in values.
3. Orientation on the board (Y grows toward the front):

   | Key | Small Ø3.048 | Large Ø3.988 | Switch pins | Comment |
   |---|---|---|---|---|
   | SW43 LShift 2.25U | back (y 59.36) | front (74.60) | back | Cherry-standard, wire at the front |
   | SW42 Enter 2.25U | back (40.31) | front (55.55) | back | Cherry-standard |
   | STAB_RS1 RShift 2.75U | back (59.36) | front (74.60) | front | stabilizer standard, switch rotated — fine |
   | SW59 Space 7U | **front (92.38)** | **back (77.14)** | back | reversed, wire at the back |

   Conventional is large hole toward the front for every key. The reversed spacebar is deliberate and necessary
   here: in the standard orientation the Ø3.988 hole would sit at y 93.65 and break the board edge (94.6).
   Stabilizer and keycap are symmetric, so this works; a plate, if used, needs the spacebar stabilizer cut-out
   rotated too. As placed, the Ø3.048 holes leave 0.69 mm of board to the front edge.

---

## J3 JST SM10B-SRSS-TB

1. Pins: custom pinout, nothing to compare; pin 1 position is right (No. 1 circuit at the left with the pads at
   the top, seen from the mounting side). Pin 10 is unconnected and there is no supply pin on this connector.
2. Footprint: **OK, exact.** JST: signal pads 0.6 x 1.55 at 1.0 pitch, A = 9.0 for 10 circuits, mounting pads
   1.2 x 1.8 with 0.7 from the last pad centre to the mounting-pad edge (centres ±5.8), 3.875 between pad-row
   and mounting-pad centres. Board equal.
4. https://www.jst-mfg.com/product/pdf/eng/eSH.pdf p.1 ("PC board layout", side entry type), p.3 (header table).

## SW100 / SW101 E-Switch TL3342

1. Pins: **MATCH.** Datasheet schematic: 3–4 common, 1–2 common, contact between the two rows. Footprint has
   one pad number per row, so the switch is between pad 1 and pad 2.
2. Footprint: **OK, exact.** P.C. mounting 8.00 / 4.60 by 4.80 / 2.80 → pads 1.7 x 1.0 at (±3.15, ±1.90).
4. https://sten-eswitch-13110800-production.s3.amazonaws.com/system/asset/product_line/data_sheet/165/TL3342.pdf
   (e-switch.com itself returned HTML only).

## D1..D62 1N4148W SOD-123

1. The Diodes Inc. sheet gives "Polarity: Cathode Band" and no pin numbers; KiCad `D_SOD-123` pad 1 = K. Board:
   pad 1 → ROWn. Consistent with COL2ROW. Footprint is stock; not re-measured against the suggested pad layout.
4. https://www.diodes.com/assets/Datasheets/BAV16W_1N4148W.pdf p.1.

---

## USB speed and the existing SI report

- **The RP2350 PHY is full-speed / low-speed only.** Datasheet §1.2.2: "USB controller, supporting Full Speed
  device and Full/Low Speed host"; USB_OTP_VDD is the "supply for internal USB Full Speed PHY". Hardware guide
  §5.1: "RP2350 is limited to full speed data rate (12 Mbps)". The device never performs the high-speed chirp,
  so the link can never run at 480 Mbit/s.
- **So `qa/usb-si-sim/REPORT.md` §4 (HS eye, 0.3 V / 0.4 UI template, 150 ps edges, length sweep to "220 mm")
  does not apply to this board**, and its layout changes 1–4 (widen to 0.40 mm for 90 Ω, shorten the run, fewer
  vias) are not needed for function. Only §5 is relevant, and its 1.4 V source amplitude is wrong for FS (FS
  swings rail-to-rail, ~3.3 V), though that does not change the conclusion.
- What full speed actually asks of this route (USB 2.0 ch. 7 — **values quoted from memory, I could not open the
  spec text; only the 26 ns cable / 30 ns total figures were corroborated by a search**):
  - Driver: 28–44 Ω per line including the series resistor (the 27 Ω parts do this), edges 4–20 ns, rise/fall
    matched within about ±10 %, crossover 1.3–2.0 V.
  - Delay budget: 30 ns one-way total = 26 ns cable + 3 ns host/hub + **1 ns from the device's connector to its
    transceiver**. This route is 167 mm + 4 mm ≈ 171 mm at ~5.2 ps/mm (the report's own er_eff 2.44) ≈
    **0.89 ns**. Inside the allocation, with about 10 % to spare. This is the only FS figure the long route gets
    close to.
  - Skew 5.3 mm ≈ 27.5 ps against a 4 ns minimum edge and an 83.3 ns bit: irrelevant.
  - Impedance: 90 Ω ±15 % is a cable requirement. With 4 ns edges and a 1.8 ns round trip the 113 Ω section is
    electrically short; reflections settle inside the edge. Raspberry Pi's guide says the same ("USB FS can be
    quite forgiving").
- Board state today: connector-side nets are 0.25 mm wide for 137–138 mm with 20–22 mm of 0.15 mm, 5 / 4 vias;
  MCU-side 0.15 mm, 3.9–4.1 mm.

---

## Ranked list

### BLOCKERS
None found in the parts in scope.

### SHOULD-FIX
1. **+3V3 copper under L1.** B.Cu +3V3 zone finger between the inductor pads (x≈117.7–119.1, y≈79.35–79.65).
   Not present in the reference layout and against RP2350 datasheet §6.3.8.1. Add a zone keep-out under the L1
   body and refill. Raspberry Pi states regulator stability is sensitive to exactly this area.
2. **C102 (CIN) is 0.23 mm off the reference position**, at (115.84, 79.5) instead of (115.61, 79.5). Its +3V3
   pad is 0.24 mm from C103's +1V1 pad (reference: 0.47 mm). A solder bridge there puts 3.3 V on DVDD. Move it
   back.
3. **Tell the assembler L1 and the LEDs are polarised and check rotation in the placement preview.** L1 looks
   like a non-polar 2-pin part and Abracon does not number its terminals; the white dot must land on the
   +1V1 pad, i.e. at the silk dot at (117.5, 80.9). The 76 LEDs have no silkscreen orientation mark at all.

### NOTES
- RP2350A lead pads have ~zero heel vs the datasheet land pattern, but equal Raspberry Pi's reference footprint.
- L1 pads are smaller than Abracon's land pattern, equal to Raspberry Pi's.
- SK6805-EC15 at 4.0 V: inside the 3.7–5.5 V range, outside the 4.5–5.5 V characterised range, 0.3 V headroom.
  Confirm the 3 mA vs 5 mA version. (Full-white current vs the limiter is already recorded in `pcb/CURRENT.md`.)
- LEDs on F.Cu need switches with an SMD-LED window.
- USB route delay ≈0.89 ns against a 1 ns device allocation (from memory); do not lengthen it. HS analysis is moot.
- J1 sits 0.125 mm further from the edge than GCT's nominal.
- Spacebar stabilizer reversed (needed for edge clearance); 0.69 mm web to the board edge; rotate any plate cut-out.
- J3 has no supply pin and pin 10 is unused.
- UNVERIFIED against a manufacturer document: Kailh socket land pattern, stabilizer X spacing, USB 2.0 numeric
  limits, SOD-123 pad dimensions. OPSCO data came from distributor mirrors.
