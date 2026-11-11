# Signal integrity

Board `pcb/maru60.kicad_pcb`, SHA-256 `36700843ef6c…` (`results.json` carries the
full hash; `run_all.py --check` compares it with the board file). Everything is
computed or simulated from the routed copper with the tools in
[`pcb/tools/signal_integrity`](../../../../tools/signal_integrity/README.md): a 2-D
field solve of the outer-layer cross-section (−0.5 … +1.2 % against
Hammerstad–Jensen), lossy LC-ladder lines, ngspice 39. **No hardware exists;
nothing here is a measurement.**

Basis words used below: **simulated** (ngspice on the routed geometry),
**computed** (field solve or hand calculation), **datasheet** (a limit read from
the named document), **assumed** (the document does not give the value; the
value used is stated and swept).

## Verdict

| Signal | Result | Margin | Basis |
| --- | --- | --- | --- |
| LED data, first hops: GPIO → U5/U6 → 330 Ω → LED1 (137 mm, 7 vias) / LED63 (116 mm, 8 vias) | pass. Rise/fall 14–28 ns, no overshoot, no ring-back | noise margin 0.88 V high, 1.40 V low; pulse-width error −16.4 / +7.7 ns against ±100 ns | simulated; buffer output 15–100 Ω and its tPLH/tPHL difference assumed |
| LED data, the 69 LED-to-LED hops without a series part (key: median 21 mm, longest 33 mm; underglow: 28–62 mm) | pass with an LED output of 35 Ω or more at any edge, or 20 Ω with a 2 ns or slower edge | at 20 Ω / 2 ns the longest (`UG_LED_11`, 62 mm) keeps 0.40 V; full noise margin with 100 Ω / 10 ns; pulse-width error at most −33 / +15 ns with a 1 kΩ output | simulated; SK6805 output strength assumed; finding 3 |
| LED data, the five hops longer than 62 mm, each with 100 Ω at its source: `UG_LED_6` (274 mm, `R115`), `UG_LED_9` (102 mm, `R116`), `KEY_RGB_CHAIN_60` (79 mm, `R117`), `_61` (72 mm, `R118`), `_52` (63 mm, `R119`) | pass for every output swept (10–1000 Ω, 1–30 ns edges): no overshoot, no ring-back | noise margin 0.87–0.88 V / 1.36–1.40 V; pulse-width error at most −60 / +29 ns (274 mm), −39 / +19 ns (the others) | simulated |
| LED data, Caps Lock alternative sites (`KEY_RGB_CHAIN_29/30/31`, stubs to 22 mm, one via) | pass, same as a plain hop in all four fitted combinations | noise margin ≥ 0.67 V even with 20 Ω / 2 ns | simulated |
| Matrix edges coupling into LED data | ±0.30 V on the worst routed pair (`UG_LED_6` beside `COL10`, 49 mm at 0.25 mm) | 0.88 V available; 0.65 V for a hypothetical 80 mm at 0.15 mm | simulated, 3.3 V / 1 ns aggressor |
| Buck switch node (500 kHz) into LED data and `RUN` | ≤ 1.0 mV into `UG_LED_10` (2.85 mm away), ≤ 1.5 mV into `RUN` (1.72 mm) | > 500 × | computed (field-solve mutual capacitance over the plane) |
| USB FS, device transmitting, 50 pF test load at J1 | VCRS 1.648–1.654 V; TFR = TFF; jitter ±0.05 ns | 1.3–2.0 V; 90–111 %; ±3.5 ns | simulated; PHY edge rate assumed |
| USB FS eye at the host after 1 m of cable | 3.27 V high at the centre, 0.995–0.997 UI wide above ±0.2 V | sensitivity 0.2 V | simulated |
| USB FS eye at the RP2350, host transmitting | 3.15 V, 0.987–0.997 UI, VCRS 1.67–1.69 V, jitter ±0.30 ns | receiver tolerates ±18.5 ns | simulated |
| USB pair geometry | 95 Ω differential / 34 Ω common for 124 mm; length skew 0.34 mm (2 ps); ground plane under the whole pair | full speed sets no board impedance | computed |
| USB delay, J1 to the RP2350 | **1.03 ns to R102/R103, 1.07 ns to the pins; the specification allows 1 ns** | 3–7 % over; finding 2 | simulated |
| Crystal load capacitance | 8.7–9.3 pF for a 10 pF crystal: +10 … +20 ppm (bracket −5 … +37 ppm) | USB full speed ±2500 ppm; crystal class ±30 ppm | computed; pin capacitance and motional capacitance assumed |
| Crystal start-up and drive level | needs gm ≥ 0.5 mS for −50 Ω, ≥ 1.5 mS for −250 Ω; drive level ≤ 178 µW | 200 µW maximum; **RP2350 gm is not published: UNVERIFIED** | simulated (AC); same circuit as the Raspberry Pi reference |
| QSPI flash | longest net 23.5 mm, data against clock 5.7 mm (34 ps), no vias | 13.8 ns slack at the 25 MHz used; 0.5 ns at 75 MHz (not used) | computed |
| SWD | `SWCLK` 35 mm, `SWDIO` 67 mm (0.4 ns) | 2.5 % of a half period at 30 MHz | computed |
| `RUN` | 87 mm, 14 pF, internal pull-up only; all neighbours switching together couple 47 mV | 2.5 V needed for a reset: 53 × | computed |
| BOOTSEL | button net is behind 1 kΩ (R106); pressed level 0.30 V | VIL 0.8 V | computed |
| Key matrix, column valid after row select | 13 ns typical; 45 ns at the pin limits; 120 ns with six keys of the row held | the firmware waits 800 ns: 63 × / 18 × / 6.7 × | simulated |
| Key matrix, all 15 keys of row 0 held, pin at its data-sheet limits | 228 ns at 27 °C, 250 ns at 0 °C | 3.5 × / 3.2 × with the 800 ns wait (1.1 × / 1.0 × with QMK's 247 ns default, which the firmware used before) | simulated; finding 1, closed |
| Key matrix, column back high after row release | 1.5–4.4 µs | QMK waits 30 µs: ≥ 6.9 × | simulated |
| Key matrix leakage at 60 °C | 0.65 V droop with all 61 other diodes at maximum leakage | 1.3 V allowed: 2.0 × | computed from the 1N4148W data sheet |
| Expansion port, switch off or board unpowered | ≤ 10 µA per line into the port, no path into a supply rail | MCU pin offset ≤ 0.39 V, VIL 0.8 V | datasheet (SN74CB3T3245, TPD6E05U06) |
| Expansion port, 3.3 V and 5 V signals from outside | 2.83–3.02 V and 3.02–3.36 V at the MCU pin | ≥ 0.83 V above VIH; below IOVDD + 0.3 V | datasheet curves, scaled to 3.3 V |

## Changes made and what is left

No finding blocks the order. Findings 1 and 3 of the earlier runs are acted
on; finding 2 is recorded.

1. **Matrix read delay: done in the firmware.** QMK's default reads the
   columns 37 CPU cycles (247 ns) after it drives a row. With all 15 keys of
   row 0 held, the row pin at its 125 Ω limit and 86 kΩ pull-ups, the last
   column is below 0.8 V after 228 ns at 27 °C and 250 ns at 0 °C: no margin.
   `keyboards/maru60/rp2350/config.h` now has

   ```c
   #define GPIO_INPUT_PIN_DELAY 120   /* CPU cycles: 0.8 µs at 150 MHz */
   ```

   which gives 3.2 × in that corner and costs 2.8 µs per scan. Both layouts
   were rebuilt; the linked `matrix_output_select_delay` holds 120 `nop`
   instructions ([`qa/qmk-build`](../qmk-build/RESULT.json)). The value must
   stay within 1–135: `wait_cpuclock()` (`platforms/chibios/_wait.c`) runs no
   8-cycle block above that, so 150, for example, waits 6 cycles (40 ns).
   `config.h` rejects a value outside the range at compile time.
2. **USB delay: recorded, not changed.** The pair runs 156 mm (plus 4 mm after
   the 27 Ω parts) with four vias per line. USB 2.0 §7.1.16 allows 1 ns from
   the connector to the transceiver; this route is 1.03–1.07 ns. The allowance
   is one device's share of a 30 ns one-way budget through five hubs and 5 m
   cables, so 70 ps has no effect on a keyboard on an ordinary port, and every
   waveform limit passes with large margin. Meeting the number means removing
   13 mm. The route is a staircase between the switch holes from the connector
   to the MCU, 156 mm against 132 mm for the shortest octilinear path with no
   obstacles, and the last 20 mm thread between vias beside the MCU; the
   excess is spread over the whole run and cannot be taken out locally.
3. **LED data: the five hops longer than 62 mm now have a series resistor.**
   `R115`–`R119` make those hops independent of the LED output. Without the
   parts the same hops ring back under the 3.12 V high threshold with a
   20 Ω / 2 ns output (274 mm and 102 mm) or keep only 0.13–0.34 V
   (63–79 mm). The 69 remaining hops are 62 mm or shorter. The longest,
   `UG_LED_11`, keeps 0.40 V with a 20 Ω / 2 ns output and rings back only
   with 20 Ω and a 1 ns edge, or 10 Ω and 2 ns or faster. The data sheet gives
   no output figure; a 5 V CMOS output that strong and that fast is unlikely
   for an LED driver pin. Look at one LED input after a long hop (`LED59`,
   `LED74`) with a scope at bring-up.

## LED data

Thresholds 3.12 V and 1.40 V (0.78 and 0.35 × VDD at the 4.0 V LED rail,
OPSCO SK6805-EC15-001 Rev A/1). The firmware sends 300 ns / 900 ns high times
exactly (PIO at 20 MHz from 150 MHz); the data sheet accepts T0H 200–400 ns,
T1H ≥ 700 ns, T0L ≥ 700 ns, T1L ≥ 200 ns, so the budget is ±100 ns on a "0" and
−200 ns on a "1". Each LED regenerates the data, so the errors below do not add
along the chain. The sheet gives no DOUT strength and no DIN capacitance:
four cases are assumed (20 Ω / 2 ns, 100 Ω / 10 ns, 500 Ω / 30 ns into 5 pF,
1 kΩ / 30 ns into 15 pF) and the strength is swept from 10 to 100 Ω and 1 to
10 ns on the hops with a series part and on the longest one without.

| Hop | Length, vias, stubs | 100 Ω / 10 ns: rise, width error | 1 kΩ, 15 pF: width error | 20 Ω / 2 ns: overshoot, high level after the peak |
| --- | --- | --- | --- | --- |
| `KEY_RGB_5V` (R110 → LED1), buffered | 137.3 mm, 7 | 15–28 ns, −16.4 / +7.7 ns (slow corner) | — | none |
| `UNDERGLOW_5V` (R111 → LED63), buffered | 116.0 mm, 8 | 14–27 ns, −15.7 / +7.2 ns | — | none |
| `UG_LED_6` with R115 100 Ω | 3.7 + 274.0 mm, 8 | 15.9 ns, −8.8 / +3.8 ns | −60.4 / +29.4 ns | none, 4.00 V |
| `UG_LED_6` with R115 shorted (before the change) | same | 9.1 ns, −6.1 / +3.2 ns | −55.6 / +27.0 ns | 2.31 V, **2.67 V** |
| `UG_LED_9` with R116 100 Ω | 2.3 + 102.0 mm, 4 | 10.3 ns, −6.2 / +3.3 ns | −39.2 / +18.5 ns | none, 4.00 V |
| `UG_LED_9` with R116 shorted (before the change) | same | 8.4 ns, −5.7 / +3.1 ns | −36.5 / +17.1 ns | 1.74 V, **3.08 V** |
| `KEY_RGB_CHAIN_60` with R117 100 Ω | 2.9 + 78.9 mm, 3 | 9.7 ns, −6.1 / +3.2 ns | −36.8 / +17.3 ns | none, 4.00 V |
| `KEY_RGB_CHAIN_60` with R117 shorted (before the change) | same | 8.3 ns, −5.7 / +3.0 ns | −34.5 / +16.1 ns | 1.41 V, 3.25 V |
| `KEY_RGB_CHAIN_61` with R118 100 Ω | 9.5 + 72.1 mm, 0 | 9.5 ns, −6.0 / +3.2 ns | −35.5 / +16.6 ns | none, 4.00 V |
| `KEY_RGB_CHAIN_61` with R118 shorted (before the change) | same | 8.3 ns, −5.7 / +3.0 ns | −33.3 / +15.5 ns | 1.06 V, 3.46 V |
| `KEY_RGB_CHAIN_52` with R119 100 Ω | 1.8 + 63.1 mm, 7 | 9.9 ns, −6.1 / +3.2 ns | −37.5 / +17.7 ns | none, 4.00 V |
| `KEY_RGB_CHAIN_52` with R119 shorted (before the change) | same | 8.4 ns, −5.7 / +3.0 ns | −35.1 / +16.4 ns | 1.37 V, 3.31 V |
| `UG_LED_11`, the longest hop without a series part | 61.7 mm, 2 | 8.2 ns, −5.7 / +3.0 ns | −31.5 / +14.6 ns | 0.93 V, 3.52 V |
| `KEY_RGB_CHAIN_30`, LED30 on its alternative site, LED75 on the bottom | 52.5 mm, 1, stubs 8.8 + 5.5 mm | 8.3 ns, −5.7 / +3.0 ns | −33.0 / +15.4 ns | 0.54 V, 3.80 V |
| `KEY_RGB_CHAIN_30`, default sites | 39.1 mm, 1, stubs 22.3 + 5.5 mm | 8.3 ns, −5.7 / +3.0 ns | −32.7 / +15.2 ns | 0.37 V, 3.86 V |
| `KEY_RGB_CHAIN_30`, LED75 on its top pads | 40.7 mm, 0, stubs 17.1 mm (with a via) + 8.8 mm | 8.3 ns, −5.7 / +3.0 ns | −32.8 / +15.3 ns | 0.37 V, 3.87 V |
| `KEY_RGB_CHAIN_29`, default / alternative site | 22.3 mm + 9.0 mm stub / 15.3 mm + 16.1 mm stub | 8.1 ns, −5.6 / +3.0 ns | −28.5 / +13.2 ns | 0.25 V, 3.91 V |
| `KEY_RGB_CHAIN_31`, LED75 bottom / top | 42.4 mm, 1, 2.6 mm stub / 32.6 mm, 12.4 mm stub with a via | 8.2 ns, −5.7 / +3.0 ns | −30.4 / +14.1 ns | 0.36 V, 3.84 V |
| `KEY_RGB_CHAIN_3` (ordinary hop) | 18.7 mm, 0 | 8.1 ns, −5.6 / +3.0 ns | −27.1 / +12.6 ns | 0.22 V, 3.92 V |

- All 76 links were extracted (length, layers, vias, stubs, capacitance,
  neighbours, plane openings): `led_hop_table` in `results.json`. Key hops
  without a series part: 15.3–33.0 mm, vias only on `_44`, `_46`, `_51`
  (2 each). Underglow hops without one: 27.7–61.7 mm with 2–4 vias. The five
  longer hops each sit behind a 100 Ω part 1.8–3.7 mm from the LED (`R118`:
  9.5 mm, the nearest place outside the spacebar's stabilizer zone).
- Strength sweep (10–100 Ω, 1–10 ns) with the series part in place: all five
  hops keep the full 0.88 V / 1.40 V at every point. With the part as 0 Ω the
  274 mm hop goes under the threshold up to 20 Ω / 4 ns, the 102 mm hop up to
  20 Ω / 2 ns and the three key hops at 20 Ω / 1 ns and 10 Ω / 2 ns; that is
  what the parts remove. `UG_LED_11` without a part: under the threshold at
  10 Ω / 1–2 ns (−1.01 V, −0.06 V) and 20 Ω / 1 ns (−0.09 V), clear elsewhere.
- The stubs and vias added for the Caps Lock sites are electrically short
  (22 mm is 0.13 ns) and change nothing visible.
- The ground plane is continuous under every hop; the only openings are the
  hops' own via antipads and one 0.1 mm neighbouring antipad under
  `UNDERGLOW_5V`.
- First hops: GPIO high is 3.3 V against a buffer threshold of about 1.75 V
  at 4.0 V (interpolated between the 3.6 V and 4.5 V rows of the SN74LV1T125
  data sheet). TI gives no tPLH/tPHL difference; ±3 ns is assumed and is inside
  the stated error.
- Longest runs beside a matrix line: `UG_LED_6`/`COL10` 49 mm at 0.25 mm,
  `UG_LED_3`/`COL13` 32 mm at 0.20 mm, `UG_LED_6`/`COL11` 29 mm at 0.20 mm. The
  matrix lines move at the scan rate, not continuously.
- Buck switch node: 5.2 mm² on the bottom at (173–179, 81–84). No key hop
  within 5 mm; `UG_LED_10` 2.85 mm and `UG_LED_9` 4.1 mm away.

![LED hops](led-hops.png)
![LED first hop](led-first-hop.png)
![LED crosstalk](led-crosstalk.png)

## USB 2.0 full speed

Limits, all read from the USB 2.0 specification (`usb_20.pdf`, 27 April 2000,
in `usb_20_20240604.zip` from usb.org):

| Quantity | Limit | Source | This board |
| --- | --- | --- | --- |
| Crossover voltage VCRS | 1.3–2.0 V | Table 7-7 | 1.648–1.654 V at J1 into 50 pF; 1.67–1.69 V received |
| Rise and fall time TFR, TFF | 4–20 ns, 50 pF load | Table 7-9, Figures 7-8 and 7-9 | 4.5 / 6.9 / 12.9 ns (10–90 %) for an assumed 4 / 8 / 16 ns PHY ramp (0–100 %) |
| Rise/fall matching TFRFM | 90–111.11 % | Table 7-9 | 100.0 % (board contribution under 0.02 ns; the PHY model is symmetric) |
| Driver output resistance ZDRV | 28–44 Ω | Table 7-9 | 27 Ω + PHY; PHY resistance not published, 9 Ω assumed |
| Source jitter TDJ1 / TDJ2 | ±3.5 / ±4 ns | Table 7-9 | ±0.05 ns / 0.00 ns |
| Receiver jitter tolerance TJR1 / TJR2 | ±18.5 / ±9 ns | Table 7-9 | ±0.30 ns / 0.00 ns arriving |
| Differential sensitivity VDI | ≥ 0.2 V | Table 7-7 | eye 3.15–3.27 V |
| Connector to transceiver delay | ≤ 1 ns | §7.1.16 | 1.03 ns to R102/R103, 1.07 ns to the pins |

Models: RP2350 PHY as 3.3 V behind 9 Ω with 4, 8 and 16 ns ramps (assumed; the
RP2350 data sheet gives VOH ≥ 2.8 V, VOL ≤ 0.3 V and the 27 Ω parts only);
cable 1 m, 90 Ω differential, 5.2 ns/m; host 36 Ω per line, 15 kΩ, 20 pF (and
150 pF once).

Geometry:

- `J1.A6 → R102`: 155.83 mm, `J1.A7 → R103`: 155.77 mm; then 4.10 mm and
  3.82 mm to the RP2350. Four vias on each line. 0.25 mm tracks 0.20 mm apart
  for 124 mm (95.1 Ω differential, 34.4 Ω common), 0.16–0.25 mm gap elsewhere
  (90–100 Ω), 0.15 mm break-outs for 16–18 mm (117–137 Ω).
- Skew: 0.34 mm of length (2 ps); 9 ps single-ended arrival difference in the
  simulation, from the unequal break-outs. Full speed has no skew limit; the
  effect is inside the VCRS figure.
- Stubs: 6.0 mm with one via to `J1.B6` and U10 on D+, 2.4 mm to `J1.B7` on D−.
- Places where the two lines separate (distance from J1, position):
  1.0–6.9 mm, up to 3.8 mm apart, connector and U10 fan-out, (17.7, 8.4);
  48.5–49.1 mm, via pair, (53.6, 30.1); 132.8–134.3 mm, via pair, (114.6, 71.9);
  149.7–150.6 mm, (124.2, 81.9); 153.4–155.8 mm, into R102/R103, (121.4, 82.4).
- Reference plane: ground fill is present under every 0.1 mm sample of both
  lines except their own via antipads (0.5 mm each, eight per line) and 0.3 mm
  of a neighbouring via's antipad under D− at (18.25, 8.39). The pair crosses
  no slot, split or gap, and no track on the inner layers.
- Closest other nets: `ROW3` 5.3 mm at 0.175 mm beside D+, `UNDERGLOW_5V`
  3.2 mm at 0.28 mm.

![USB eye](usb-fs-eye.png)

## Crystal (Y1 ABM8-272-T3, C106/C107 15 pF, R108 1 kΩ)

- Copper: `XIN` 10.9 mm, 1.57 pF; `XTAL_OUT` 5.4 mm, 1.16 pF; `XOUT` 3.0 mm,
  0.46 pF (pads included).
- Load: 8.7 pF, or 9.3 pF counting the XOUT pin behind R108, with 2 pF per pin
  assumed; 8.5–10.2 pF for 1–4 pF. The crystal is specified at 10 pF. Raspberry
  Pi's reference arrives at 10.5 pF by assuming 3 pF of parasitics.
- Frequency offset from the load: +10 … +20 ppm nominal, −5 … +37 ppm over a
  motional capacitance of 2–6 fF (not on the Abracon sheet) and 1–4 pF pins.
- Negative resistance at 12 MHz: −50 Ω needs gm ≥ 0.3 mS (0.5 mS worst case),
  −250 Ω needs 1.0 mS (1.5 mS); the most negative value is −3.0 kΩ (−2.1 kΩ)
  near 16 mS. The RP2350 data sheet gives no transconductance, pin capacitance
  or negative resistance: the chip's own margin is UNVERIFIED.
- Drive level, upper bound with XOUT swinging rail to rail: 178 µW at 50 Ω
  ESR, 121 µW at 30 Ω, against 200 µW maximum (10 µW typical).

![Crystal](xtal-negative-resistance.png)

## Flash, SWD, RUN, BOOTSEL

- QSPI: `SCLK` 10.5 mm, `SD0–3` 8.6–16.2 mm, `SS` 23.5 mm with branches of 1.4 mm
  (R106) and 3.6 mm (R105). The boot ROM and this firmware read at clk_sys / 6 =
  25 MHz; W25Q32JV tCLQV is 6 ns, the board round trip 0.16 ns.
- BOOTSEL: the 39 mm `BOOT_BUTTON` net and its test pad sit behind R106, so
  they do not load `/CS`. A discharge to that pad reaches the pin through
  1 kΩ only.
- SWD: plane openings under the two lines total 0.3 mm and 0.8 mm.
- `RUN`: no capacitor, an exposed test pad, 5.8 mm beside `SWCLK` at 0.17 mm.
  The data sheet states no glitch filter; none is assumed.

## Key matrix

QMK timing read from the pinned tree (`quantum/matrix.c`,
`platforms/chibios/_wait.h`) and the keyboard's `config.h`: read 120 cycles
(0.8 µs) after select, 30 µs after release. QMK's default is 37 cycles
(247 ns); the margins against it are in `results.json` as `default_…`.
Pin limits from the RP2350 data sheet: VOL ≤ 0.5 V at 4 mA (125 Ω), pull-up
32–86 kΩ, VIL 0.8 V, VIH 2.0 V; 40 Ω typical and 5 pF per pin are assumed.

- Copper capacitance: rows 33–60 pF (`ROW0` 463 mm, 28 vias), columns 15–44 pF
  (`COL11` 323 mm), 508 pF for the 15 columns of row 0 together.
- The column that is read is `COL11`; the other closed keys use the next
  largest columns with their own capacitance.
- Low level of a pressed key: 0.44–0.56 V (0 °C worst), 0.24 V under VIL.
- Leakage at 60 °C: 43 nA typical, 107 nA maximum per diode (25 nA at 20 V and
  25 °C scaled by the data-sheet curve); budget 15 µA.
- RP2350-E9 concerns pull-downs on stepping A2; the matrix uses pull-ups. The
  BOM requires A4. GPIO28/29 are ADC pads, not 5 V tolerant, at 3.3 V here.

![Matrix settling](matrix-settling.png)

## Expansion port (R130–R135 1 kΩ, U11 SN74CB3T3245, U13, J3)

- MCU side 22–45 mm (8.4–12.3 pF with the pin), connector side 45–60 mm
  (10.9–14.4 pF with switch and U13).
- Switch off or VCC at 0 V: Ioff and IOZ ≤ 10 µA. U13 clamps to ground only,
  so an external signal cannot power a rail.
- Switch on: the switch limits its output to about its own supply. From the
  data-sheet curves (VCC 3.0 V, scaled) a 5 V input gives 3.1–3.45 V.
- U11 is enabled by U12 whenever +3V3 is above 2.93 V. Firmware cannot turn
  it off.
- R140–R145 39 kΩ hold a floating line at 0 V on stepping A4 only; A2 would
  need 8.2 kΩ or less (E9).

## Assumed values

Not in the data sheets, stated where used and swept in `results.json`:
SK6805 DOUT resistance and edge, DIN capacitance; SN74LV1T125 output resistance
and edge; RP2350 pad capacitance (5 pF), output resistance (40 Ω typical), USB
PHY resistance and edge rate, oscillator gm and pin capacitance; crystal
motional capacitance; solder-mask thickness and permittivity (20 µm, 3.8).
