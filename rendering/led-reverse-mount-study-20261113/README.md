# Reverse-mounted key LEDs: feasibility study, 2026-11-13

**Recommendation:** develop a separate bottom-assembly candidate using reverse-mounted
key LEDs and normally mounted underglow LEDs. This is a manufacturing optimization
with a real commercial precedent. It is not yet a routed or order-qualified design.

## Reference identified

The user's HHKB Oni matches the [YMDK GH60 HHKB-style Tsangan Oni PCB](https://ymdkey.com/products/ymdk-gh60-hhkb-style-tsangan-oni-hot-swappable-both-underglow-switch-rgb-via-programmable-pcb-compatible-with-tokyo-60).
The vendor explicitly describes both switch RGB and underglow. Its photographs show
rectangular windows on the switch side and small reverse-mounted key LEDs plus
larger outward-facing underglow LEDs on the assembly side. This supports the user's
observation of the architecture. It does **not** establish the exact LED model,
cutout dimensions, PCB revision, or the production process used for their purchased unit.

Source photographs, retrieved 2026-11-13, © their respective owner:

- [Switch-side windows, HHKBRGBPCB_5](https://cdn.shopify.com/s/files/1/0006/5227/9869/files/HHKBRGBPCB_5.jpg?v=1716347296)
- [Assembly-side detail, HHKBRGBPCB_3](https://cdn.shopify.com/s/files/1/0006/5227/9869/files/HHKBRGBPCB_3.jpg?v=1716347296)
- [Switch-side lighting, HHKBRGBPCB_1](https://cdn.shopify.com/s/files/1/0006/5227/9869/files/HHKBRGBPCB_1.jpg?v=1716347296)

## Maru60 scope

Source: `pcb/experiments/resume-20261113-mcu-near-usb-zero-opens/`.
Board SHA-256: `2cc544c8e6eb00bd3f53fa480a0167dcb8e14dac687f7eb2af0c85946bda5584`.

The validated candidate was only read. No PCB, schematic, manufacturing exports,
firmware, or candidate manifest was modified. No merge was performed.

Automated placement counts from its BOM/CPL:

| Scenario | Top | Bottom | Status |
| --- | ---: | ---: | --- |
| Current candidate | 136 | 200 | Existing export |
| Move 61 key LEDs and 63 LED capacitors | 12 | 324 | Arithmetic only; feasibility unproven |
| Relocate all automated components to bottom | 0 | 336 | Target; feasibility unproven |

The 63 capacitors are 100 nF, with pads on `+4V_LED` and `GND`. The other top
parts are C144, F1, R100, R101, R118, R120, R177, R179, R180, R181, R183, R187.
LED14 and LED15 remain excluded from automatic assembly in the current export;
their mutually exclusive Backspace sites must also be redesigned deliberately.
The existing total LED count is 76, with 74 automatically assembled.

Moving 124 of 136 top placements addresses about 91% of them, but **leaving even
12 top placements still requires a second assembly side**. This percentage is not
a cost saving. One-sided assembly can avoid the second print/place/reflow pass,
subject to the assembler's process. Savings must be quoted against the added
cutout machining, replacement LED procurement, setup and inspection costs.

## Part selection

Current part: OPSCO SK6805-EC15-001, LCSC C2890035, a 1.5 × 1.5 mm package.
Its primary lands have centers at ±0.475 mm and dimensions 0.55 × 0.55 mm.
A centered 4 × 2 mm opening removes those lands. It cannot simply be flipped.

An independently documented example is [Adafruit's reverse-mount SK6812-E](https://www.adafruit.com/product/4960),
with the linked [OPSCO SK6812MINI-E Rev. 02 datasheet](https://cdn-shop.adafruit.com/product-files/4960/4960_SK6812MINI-E_REV02_EN.pdf).
This is an example package, **not an identification of Oni's part or an approved
Maru60 substitute**. The drawing on page 4 specifies a 3.2 × 2.8 mm body, 5.88 mm
overall lead span, and 1.78 mm height. The window must fit the selected part's
insertion geometry with manufacturing tolerances; a nominal 4 × 2 mm rectangle
is not a generic footprint prescription for this package.

The vendor's listed example drives approximately 12 mA/channel, versus the
current 5 mA/channel LED. The datasheet also mentions a SK6805MINI-E 5 mA variant;
its exact orderable MPN and electrical revision are not qualified here.
Prefer a low-current reverse-mount part with controlled procurement.

Maru60's existing LED rail is 4.00 V. Its limiter is 174 / 202 / 234 mA
(minimum / nominal / maximum), so 234 mA must not be treated as guaranteed usable
current. Existing firmware already limits brightness and LED power.
The example Rev. 02 sheet lists 3.7–5.5 V supply range, but the detailed IC table
is conditioned on 4.5–5.5 V, with thresholds characterized at 5 V. Its typical
idle current is 1 mA versus the current part's 0.5 mA. Therefore neither the
existing 4 V margins nor power limits transfer without qualification.
Check voltage, idle and channel currents, logic thresholds, DIN/DOUT timing,
GRB ordering, pin mapping and reflow/feeding orientation for the purchased part.

## Direct intersection screen

Reproduce from repository root:

```sh
.venv/bin/python rendering/led-reverse-mount-study-20261113/analyze.py
```

The script reads the frozen geometry and CSVs, writes [findings.json](findings.json),
and checks that the source board hash is unchanged. It assumes **hypothetical
4 × 2 mm rectangles**, long axis X, centered at the 61 current automated top
LED footprint anchors. These are not selected or released cutouts.

- 7 windows intersect pads of other components.
- 61 intersect existing track records, including their own LED connections.
- 60 intersect existing via copper.
- 7 intersect bottom component courtyards.

Other-pad intersections: LED1/C200; LED16/C105 and R193; LED17/Y1;
LED30/SWCAP1; LED44/J3; LED48/R119; LED49/R182.
At LED16 the screen also finds QSPI_SD1 and QSPI_SS on In2.Cu, QSPI_SD3
on B.Cu, and the U3 courtyard. Local MCU/flash routing must be redesigned or
the LED window relocated.

This screen adds no edge clearance or machining tolerance, does not qualify
plane continuity, switch/stabilizer volumes or alternate LED sites, and does
not constitute DRC. Courtyard overlap is a placement flag, not proof of body
collision. Source track counts may contain duplicate records.

## Implementation order

1. Qualify the exact low-current reverse-mount LED and assembler support.
2. Establish its non-plated cutout, internal corner radius, pad geometry,
   paste aperture, copper-to-edge clearance on every layer and orientation.
3. Solve the MCU/flash/crystal and special-layout sites first, then relocate
   LEDs, nearby capacitors and the remaining 12 automatic top placements.
4. Retain the four-layer stack; one-sided assembly does not mean a one-layer PCB.
   Recheck switch LED openings, hot-swap sockets, 7U plate-mount stabilizer and
   2U Backspace PCB-mount stabilizer clearance, stiffness and support margins.
5. Refill zones and regenerate schematic/board parity, DRC/ERC, connectivity,
   SI/PDN checks, manufacturing exports and firmware power/timing constraints.
6. Obtain an assembly quote and verify prototype fit, solderability and light
   output before promoting the candidate for ordering.

Other optimization should follow measured bottlenecks. This architecture can
simplify assembly and free the switch face, but it does not increase scan or
USB polling rates. Actual savings and reliability improvements require evidence.
