# Follow-up verification (2026-11-11)

The datasheet review left four points unconfirmed. Each was checked against a
manufacturer document or manufacturer characteristic data. Nothing here is a
bench measurement.

## 1. Buck output capacitance under DC bias — changed `C100`

Source: Samsung Electro-Mechanics product pages
(`https://product.samsungsem.com/mlcc/<part>.do`), DC-bias curve at 25 °C,
120 Hz, 0.5 Vrms, read from the page's embedded graph data.

| Part | Package | Nominal | ΔC at 4 V | Effective at 4 V |
| --- | --- | ---: | ---: | ---: |
| CL10A226MP8NUN (`C140`, `C141`) | 0603, 10 V | 22 µF | −60.4% | 8.7 µF |
| CL10A226MQ8NRN | 0603, 6.3 V | 22 µF | −63.2% | 8.1 µF |
| CL10A226MO7JZN | 0603, 16 V | 22 µF | −60.4% | 8.7 µF |
| CL10A476MQ8QRN | 0603, 6.3 V | 47 µF | −84.9% | 7.1 µF |
| CL21A226MAQNNN | 0805, 25 V | 22 µF | −41.0% | 13.0 µF |
| **CL31A226KAHNNN (`C100`)** | 1206, 25 V | 22 µF | −28.1% | **15.8 µF** |

TI gives a minimum effective output capacitance of 15 µF for the TPS62932 with
4.7 µH (3.3 V row; 10 µF for 5 V with 6.8 µH) and says designs near the minimum
need loop and load-transient testing.

- `C140` + `C141` alone: 17.4 µF nominal, **13.9 µF at −20% tolerance**. No 0603
  part does better, so the note "effective ≥ 12 µF" per capacitor could not be
  met.
- `C100` is on the same rail, 37 mm of 0.4 mm track from the inductor (about
  45 mΩ, 15–30 nH). At the loop crossover that is a small series resistance, so
  it counts as output capacitance. It was 4.7 µF X7R; it is now
  **22 µF 25 V X5R** on the same 1206 land.
- Rail total: about **33 µF nominal, 28 µF at worst-case tolerance**. Switching
  ripple on the local pair is about 5 mV.

Buck input (`C137`, CL10A106MA8NRN): −52.8% at 5 V, 4.7 µF effective, about half
of TI's 10 µF typical. Input ripple at 0.3 A is about 20 mV. No larger part fits
the 0603 land; not changed.

## 2. LED current version — 5 mA

Source: OPSCO `SK6805-EC15-001`, Rev. A/1 (the datasheet attached to LCSC
C2890035).

- Part number decoding: "6805: 68 series IC, 5 mA current version"; "001:
  internal code".
- Output drive current 4.7 / 5 / 6.3 mA per channel (min / typ / max).
- Static current 0.5 mA typical per LED: **38 mA for 76 LEDs**. This is not in
  the earlier limiter arithmetic (`qa/power-review`), which divides the whole
  173.7 mA by the channel count. It does not change the conclusion: the
  firmware PWM budget (`MARU60_PWM_SUM_LIMIT 1020`) holds the drive current to
  about 20 mA typical, 25 mA at the 6.3 mA maximum, so the rail carries about
  60 mA against the 174 mA minimum limit.
- Full white at the datasheet maximum is 76 × 3 × 6.3 mA + 38 mA = 1.47 A.

## 3. Kailh socket land pattern — matches, hole 0.05 mm under nominal

Source: Kailh product specification `KH-PS1607-10` Rev. A for CPG151101S11,
section 8 "Recommended PCB Layout" (the datasheet attached to LCSC C2803348).

| | Kailh | Board (`MX_V2:MX-Hotswap-1U`) |
| --- | --- | --- |
| Hole spacing | 6.35 mm × 2.54 mm | 6.35 mm × 2.54 mm |
| Pad size | 2.55 × 2.5 mm | 2.55 × 2.5 mm |
| Hole diameter | 3.05 ± 0.05 mm | 3.00 mm |

The drawing does not dimension the pad position; scaled from the drawing, the
pads sit about 0.3 mm further from the holes than on the board, well inside
the pad size. The 3.00 mm hole is the lower limit of Kailh's tolerance and is
the value the widely used ai03 footprint has; not changed.

## 4. LED supply at 4.0 V — inside the specified range

Same OPSCO document: VDD 3.7 – 5.5 V in both the limit table and the IC
electrical table (typical 5.0 V), so 4.0 V is inside the specified operating
range with 0.3 V of headroom. The input high threshold is 0.78 × VDD = 3.12 V
at 4.0 V; the data buffers (`U5`, `U6`) are powered from the same rail and
swing to it. Rail drop along the 0.5 mm trunks is about 15 mV at the
firmware-limited 60 mA and about 60 mV at the 234 mA limiter maximum.

The drive current is specified with 1 V across the driver. At 4.0 V the blue
and green channels have less than that left after the LED forward voltage, so
they may run somewhat below 5 mA. Colour balance at 4.0 V can only be judged on
a built board.
