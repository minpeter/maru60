# Pre-order review — power / protection parts vs manufacturer datasheets

Board: `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`.
Read-only review; no tracked file changed. Date: 2026-11-11.

## Result in one paragraph

**No blockers found.** All 14 parts: schematic pin numbers match the datasheet pin
tables, and the pin order on the board has the correct handedness for every IC
(all are on B.Cu; checked from absolute pad positions in `board.json`, not from
the un-flipped listing). Eleven footprints match the manufacturer land pattern
exactly or are the stock KiCad pattern for a standard package. Two footprints are
MARGINAL (U13 RVZ-14, F1 fuse). The open items are capacitor values at the buck,
not connectivity.

## How this was checked

- Datasheets were downloaded from the manufacturer sites and read as text; package
  drawings were rendered and read as images. All 14 opened. Nothing below is from
  memory except where marked **(not from a datasheet)**.
- Handedness: for each IC, three pins were taken from `board.json` absolute pad
  positions, mirrored for B.Cu, and compared with the datasheet top view. All 10
  in-scope ICs (plus U1, U3) pass. The custom library footprints for U8, U13 and U2
  were also read directly from the `.kicad_mod` files.
- Not done: no simulation, no bench work, no check of the assembly house's
  rotation/centroid data, and no DC-bias curves (capacitor MPNs are not fixed in
  the design).

## Ranked findings

### BLOCKERS

None.

### SHOULD-FIX

1. **U13 TPD6E05U06 footprint is wider and carries about twice the paste of TI's
   pattern.** Board pads are 0.30 x 0.65 mm with full-size paste; TI's land and
   stencil are 0.20 x 0.50 mm on the same 0.5 mm pitch. Copper gap between
   neighbours is 0.20 mm (TI 0.30 mm), and the pad is 0.05 mm wider than the
   maximum lead (0.25 mm). Paste area per pad is 0.195 mm² vs 0.10 mm². Bridging
   on the pin 8-14 side would short EXT_GPIO lines to each other or to GND.
   Fix: narrow pads to 0.20-0.25 mm, or at least shrink the paste apertures to
   about 0.20 x 0.50 mm. Outer pad edge (0.875 mm from centre) already equals TI's.
2. **Buck input capacitance at U18 is 4.8 µF nominal, not 5.8 µF.** C126 (1 µF) sits
   at the eFuse, about 170 mm from U18; only C137 (4.7 µF) and C136 (100 nF) are
   within 4 mm of U18 VIN. TI's guidance is 10 µF typical plus 0.1 µF. The feed
   between them is one 0.6 mm trace about 234 mm long, roughly 0.22 Ω assuming
   35 µm copper (my estimate from track lengths). A BOM-only fix is to fit C137 as
   10 µF / 25 V in the same 0603 land.
3. **Buck output capacitors: MPN not fixed, and the "effective ≥ 12 µF" note on
   C140/C141 is probably not achievable.** A 22 µF / 10 V 0603 typically keeps
   well under half its value at 4 V bias **(not from a datasheet — verify on the
   chosen part's DC-bias curve)**. TI's table gives minimum effective 15 µF
   (3.3 V, 4.7 µH) and 10 µF (5 V, 6.8 µH), typical 40 / 20 µF, and says designs
   near the minimum need Bode and load-transient testing. Pick the MPN before
   ordering and confirm total effective capacitance at 4.0 V is above 15 µF.
4. **F1 land is the generic KiCad 1206, not Bourns' pattern.** Board: pads
   1.25 x 1.75 mm, inner gap 1.55 mm, outer span 4.05 mm. Bourns: 1.25 x 1.65 mm,
   gap 2.2 ± 0.2 mm, span 4.7 ± 0.3 mm. The terminals (1.05-1.55 mm from centre)
   are fully on the pads, so it will solder; the pads reach 0.33 mm further under
   the body and the toe is 0.33 mm shorter than Bourns shows. Acceptable for a
   5 V prototype; correct it if the footprint is touched anyway.

### NOTES

- **U8, A instead of L:** confirmed drop-in (details in the U8 section). Behaviour
  change: after thermal shutdown the A part retries every 110 ms instead of
  staying off until replug, so a persistent short produces continuous hiccup.
- **U8 OVLO recovery:** the '470 variants bypass dVdt after an overvoltage event
  and restart in current limit, so the 0.2 V/ms ramp applies only to a normal
  plug-in.
- **U8 divider pins at abnormal VBUS:** at 20 V in, EN/UVLO sits at 6.0 V
  (abs max 6.5 V, recommended 5 V); at 23 V it would be 6.9 V. The OVLO pin
  reaches 4.2 V at 20 V and 4.8 V at 23 V. Only matters with a faulty source;
  there is no TVS on VBUS and TI lists one as optional.
- **U8 output capacitor:** TI asks for "larger than 1 µF" close to OUT; C126 is
  exactly 1 µF nominal at 3.2 mm.
- **U8 stencil:** the paste layer copies TI's example, which assumes a 0.100 mm
  stencil.
- **U7 TPS2553-1 vs TPS2553:** pin-compatible. The -1 latches off after the 7.5 ms
  deglitch and also latches on reverse voltage (OUT above IN by 135 mV for 4 ms);
  both need EN toggled or a power cycle. The non -1 part holds constant current
  and thermal-cycles, and recovers by itself. FAULT is asserted in both.
- **U5/U6 at VCC = 4.0 V:** VIH is specified at 3.6 V (1.48 V) and 4.5 V (2.03 V),
  not at 4.0 V. Taking 2.03 V as worst case still leaves margin for 3.3 V logic.
  The inputs have no clamp to VCC, so driving them while +4V_LED is off is safe.
- **U12 below 0.9 V:** output is undefined below VPOR (0.9 V for the active-high
  part). R128 pulls OE_N to the same rail, which is the right direction.
- **U11:** with VCC = 3.3 V the switch does not pass a full 3.3 V high (TI Fig. 7-1
  shows the clamp behaviour; I did not extract a number). Relevant only if
  EXT_GPIO26/27 are used as ADC inputs near the rail.
- **L2 orientation:** Coilcraft marks the start lead and says to connect it to the
  high-dv/dt node (SW, pad 1) for lowest EMI. Not electrically required.
- **VBUS entry copper:** the A4/B9 pin pair reaches the fuse through about 9.5 mm
  of 0.2 mm trace, and all VBUS current passes one 0.25 mm-drill via and a 0.3 mm
  trace. Fine at the 0.5 A eFuse limit; thin if the fuse ever has to clear a
  fault upstream of U8.

## Per-part detail

Legend: (1) pin table vs schematic, (2) footprint vs land pattern, (3) application
circuit, (4) source.

### U8 TPS259470 (RPW, 10-pin)

1. **MATCH.** 1 EN/UVLO, 2 OVLO, 3 AUXOFF, 4 FLT, 5 IN, 6 OUT, 7 DVDT, 8 GND,
   9 ILM, 10 ITIMER.
2. **OK — exact.** Side pads 0.6 x 0.25 at x ±0.9, y ±0.225; corner pads 0.6 x 0.3
   at y ±0.7 plus 0.25 x 0.65 stubs at x ±0.725; IN/OUT bars 0.3 x 2.4 at x ±0.25.
   Pin 1 top-left, pin 5 bar next to pins 1-4, as in TI's top view. No exposed pad.
3. - A vs L: the comparison table lists identical overvoltage response, overcurrent
     response and pin 3 / pin 4 functions; only "Response to Fault" differs. The
     pin table describes both as "TPS259470x".
   - Pin 3 on the '470 is AUXOFF, an open-drain output that goes high when the
     input is valid and inrush is complete. Leaving it open is allowed (TI's own
     test conditions state "AUXOFF = Open"); nothing depends on it.
   - Pin 10 ITIMER open is the documented option: "Leave this pin open for fastest
     response to overcurrent events". Result: no blanking, so any load above ILIM
     is limited immediately.
   - On the '470, persistent overcurrent is current-limited and not latched; only
     overtemperature and an ILM short are latched. That is where A and L differ.
   - R124 6.65 kΩ is the top of the allowed 549 Ω - 6.65 kΩ range: 0.425 / 0.500 /
     0.575 A.
   - C124 10 nF gives 0.2 V/ms; R125 100 Ω is TI's suggestion for CdVdt above 10 nF,
     harmless here.
   - Divider top resistors 590 k and 620 k meet TI's ≥ 350 kΩ advice for pins
     pulled up to IN. OVLO pin sits at 1.05 V at 5 V in (recommended 0.5-1.5 V).
   - EN/UVLO, OVLO and ILM must not float; none do.
4. https://www.ti.com/lit/ds/symlink/tps25947.pdf — SLVSFC9C (May 2026). Section 4
   table p.4; Fig. 5-1 / Table 5-1 p.5-6; 6.1, 6.3, 6.5 p.7-10; 7.3.5.1 p.29-30;
   7.3.5.3 p.31-33; Tables 7-2, 7-3, section 7.3.10 p.37-39; 8.3.1 p.60-61;
   RPW0010A 4225183/A, PDF p.72-74.

### U18 TPS62932DRLR (SOT-583)

1. **MATCH.** 1 RT, 2 EN, 3 VIN, 4 GND, 5 SW, 6 BST, 7 SS, 8 FB.
2. **OK — exact.** TI: 0.67 x 0.30 pads, 0.5 pitch, rows 1.48 apart. Board identical.
3. - RT floating = 500 kHz (table: floating / above 280 kΩ).
   - EN floating = enabled (internal pull-up current source).
   - FB: 0.8 V x (1 + 40.0k / 10.0k) = 4.00 V; 10 kΩ bottom is TI's recommended value.
   - SS 100 nF: above the 6.8 nF minimum; about 14.5 ms.
   - BST 100 nF to SW: as specified.
   - L 4.7 µH: in line with TI's table (4.7 µH at 3.3 V, 6.8 µH at 5 V, 500 kHz).
   - Input and output capacitance: see SHOULD-FIX 2 and 3.
4. https://www.ti.com/lit/ds/symlink/tps62932.pdf — SLUSEA4D (Aug 2022). Table 7-1
   p.3-4; 8.5 p.6-7; 9.3.4-9.3.6 p.19-20; 10.2.2.8-9 and Table 10-2 p.31-32;
   DRL0008A 4224486/G, PDF p.48-49.

### U2 MAX38902AATA+T (TDFN-8 2x2)

1. **MATCH.** 1 IN, 2 GND, 3 EN, 4 SELA, 5 SELB, 6 OUTS, 7 BYP, 8 OUT, EP.
2. **OK — exact.** ADI 90-0065 Rev E: 0.70 x 0.30 pads, 0.50 pitch, 1.98 between pad
   centres, EP 0.80 x 1.38. Board identical; EP is on GND.
3. - SELA = GND, SELB unconnected is the 3.3 V row of Table 1.
   - C142 from BYP to OUT is the datasheet connection ("capacitor between OUT and
     BYP"), not BYP to GND. 10 nF is inside 1 nF - 100 nF; start-up slew 5 V/ms.
   - EN tied to IN is explicitly allowed.
   - Output: 2 µF minimum effective, 4.7 µF recommended; C101 4.7 µF at 2.1 mm
     plus C102. Input: 4.7 µF recommended; C100 4.7 µF at 2.1 mm.
   - An open SEL pin tolerates 10 pF maximum; pad 5 has no trace.
4. https://www.analog.com/media/en/technical-documentation/data-sheets/max38902a-max38902d.pdf
   — 19-100191 Rev 10 (7/22): Package Information and Electrical Characteristics;
   Pin Description p.11; Table 1 p.14. Land pattern
   https://www.analog.com/media/en/package-pcb-resources/land-pattern/tdfn-ep/90-0065.pdf (Rev E).

### U7 TPS2553DBVR-1 (SOT-23-6)

1. **MATCH.** 1 IN, 2 GND, 3 EN (active high), 4 FAULT, 5 ILIM, 6 OUT.
2. **OK.** Stock KiCad SOT-23-6: 1.325 x 0.6 at x ±1.14. TI: 1.1 x 0.6 at ±1.3,
   0.95 pitch. Outer edge within 0.05 mm of TI's.
3. R112 133 kΩ is inside 15-232 kΩ. Input capacitor (≥ 0.1 µF close to IN): C120
   1 µF at 3.3 mm. EN high threshold 1.1 V, driven from 3.3 V.
4. https://www.ti.com/lit/ds/symlink/tps2553.pdf — SLVS841G (Oct 2026). Table 4-1
   p.3; Fig. 5-1 / Table 5-1 p.4; 6.3 p.5; 8.3.1-8.3.3 p.15; 9.1.1 p.18;
   DBV0006A 4214840/G, PDF p.43-44.

### U10 TPD2EUSB30DRTR (DRT-3)

1. **MATCH.** 1 D+, 2 D-, 3 GND.
2. **OK.** The datasheet gives only the DRT outline, no land pattern. Leads at
   x ±0.35 (pins 1, 2) and centre (pin 3), tips 0.5 mm from centre; board pads
   0.3 x 0.3 at y ±0.425 cover them with 0.05-0.1 mm toe.
3. Stand-off 5.5 V; sits on the connector side of R102/R103. Nothing missing.
4. https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf — SLVSAC2G (Jun 2021). Fig. 5-1 /
   Table 5-1 p.3; 6.5 p.5; DRT outline 4206292-2/D, PDF p.26.

### U13 TPD6E05U06RVZR (RVZ-14)

1. **MATCH.** 14 D1+, 13 D1-, 12 D2+, 11 D2-, 9 D3+, 8 D3-, 5 and 10 GND; 1-4, 6, 7 NC.
   Using only the D pins and leaving the NC pins open is valid: TI describes them as
   "Not connected; used for optional straight-through routing. Can be left floating
   or grounded".
2. **MARGINAL.** See SHOULD-FIX 1. Pitch, pin 1 position and pin order are correct;
   no exposed pad. Row spacing 1.10 mm vs TI 1.25 mm, same outer edge.
3. Stand-off 5.5 V. Both grounds connected.
4. https://www.ti.com/lit/ds/symlink/tpd6e05u06.pdf — SLVSBO7O (Aug 2024). Fig. 4-4 /
   Table 4-3 p.5; 5.5 p.7; RVZ outline 4218112/B p.22; land pattern 4221500/A p.23.

### U11 SN74CB3T3245PWR (TSSOP-20)

1. **MATCH.** 1 NC, 2-9 A1-A8, 10 GND, 11-18 B8-B1, 19 OE, 20 VCC.
2. **OK — exact.** TI: 1.5 x 0.45 pads, 0.65 pitch, rows 5.8 apart.
3. OE is active low: low connects A to B, high disconnects. Unused switch channels
   may float; the only control input is driven. C128 100 nF at 1.4 mm.
4. https://www.ti.com/lit/ds/symlink/sn74cb3t3245.pdf — SCDS136E (May 2026). Fig. 4-1 /
   Table 4-1 p.3; Table 7-1 p.9; PW0020A 4220206/A, PDF p.24-25.

### U12 TLV810EA29DBZR (SOT-23)

1. **MATCH.** 1 GND, 2 RESET, 3 VDD. The part number has no R or V pinout
   letter, so the standard DBZ pinout applies.
2. **OK.** Stock KiCad SOT-23: 1.475 x 0.6 at x ±0.94. TI: 1.3 x 0.6 at ±1.05.
3. Output is push-pull, active high: driven high while VDD is below the threshold
   and for the delay after it recovers. So OE_N is held high (isolated) while
   +3V3 is below threshold. Threshold 2.93 V ± 2 % (2.87-2.99 V), release up to
   3.03 V with hysteresis, delay 130 / 200 / 270 ms (suffix A).
4. https://www.ti.com/lit/ds/symlink/tlv810e.pdf — SLVSES2J (May 2021). Fig. 5-1 p.3;
   Fig. 6-1 / Table 6-1 p.4-5; electrical characteristics p.8; timing p.9;
   DBZ0003A 4214838/F, PDF p.39-40.

### U5 / U6 SN74LV1T125DBVR (SOT-23-5)

1. **MATCH.** 1 OE, 2 A, 3 GND, 4 Y, 5 VCC.
2. **OK.** Stock KiCad SOT-23-5; TI 1.1 x 0.6 at ±1.3, 0.95 pitch.
3. OE tied low = enabled. Thresholds: see NOTES. Decoupling C122 / C123 at 2.0 /
   1.5 mm.
4. https://www.ti.com/lit/ds/symlink/sn74lv1t125.pdf — SCLS745D (Mar 2024). Fig. 5-1 /
   Table 5-1 p.4; 6.5 p.6; 8.3.1 p.10; DBV0005A 4214839/K, PDF p.20-21.

### D100 PMEG4030ER (SOD-123W)

1. **MATCH.** Pin 1 cathode, pin 2 anode. Cathode on VBUS_PROTECTED_RAW, anode on
   +4V_REG: reverse-biased by about 1 V in normal operation, conducts only when the
   input falls below the output.
2. **OK — exact.** Nexperia reflow footprint: 1.2 x 1.2 lands, 2.8 between centres.
3. 40 V, 3 A; nothing to add.
4. https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf — 23 Jan 2023.
   Table 2 p.2; Fig. 14 p.8; Fig. 15 p.9.

### L2 XAL4030-472MEC

1. Two-terminal, non-polar: n/a.
2. **OK — exact.** Coilcraft: 0.98 x 3.4 pads, 2.37 between centres.
3. 4.7 µH ± 20 %, DCR 40.1 mΩ typ / 44.1 max, Isat 4.6 A, Irms 3.9 A (20 °C rise).
   Isat is above the TPS62932 high-side limit (2.8 / 3.4 / 4.0 A).
4. https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf
   — Document 806, revised 02/25/26; table p.1, land pattern p.4.

### F1 SF-1206F100-2

1. Two-terminal, non-polar: n/a.
2. **MARGINAL.** See SHOULD-FIX 4.
3. 1 A fast-acting, 63 VDC, 50 A interrupting, 0.132 Ω typ ± 25 % (66-83 mV at
   0.5 A). Holds 100 % for 4 h minimum, clears 200 % within 60 s. Sits above the
   eFuse limit, so it only acts on faults upstream of U8.
4. https://www.bourns.com/docs/product-datasheets/sf-1206f.pdf — REV. J 04/21;
   electrical table p.1, pad layout p.2.
