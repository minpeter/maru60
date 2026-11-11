# Power distribution: copper resistance, current capacity, heating

Computed by [`pcb/tools/analyze_pdn.py`](../../../../tools/analyze_pdn.py) from the routed
copper of the order candidate. Tracks are cut at every junction and become
resistors (ρ = 1.72 µΩ·cm at 20 °C, +0.393 %/K; 35 µm outer, 15.2 µm inner
copper); vias are 1.62 mΩ barrels (20 µm plating assumed); pads and zone-fill
islands are equipotential. The solver reproduces a hand-calculated 100 mm ×
0.5 mm track (98.286 mΩ). The inner GND planes are not solved: at
1.13 mΩ per square the return path stays under a millivolt.
**No design change is needed.** Nothing here is measured.

## Rail drops at 60 °C copper

| Path | Resistance | Current | Drop | Vias carrying > 30 % |
| --- | --- | --- | --- | --- |
| VBUS J1 -> F1 | 39.48 mΩ | 0.5 A | 19.74 mV | 1 |
| VBUS_FUSED F1 -> U8 | 9.9 mΩ | 0.5 A | 4.95 mV | 1 |
| VBUS_PROTECTED_RAW U8 -> U18 | 270.29 mΩ | 0.5 A | 135.15 mV | 14 |
| +4V_REG L2 -> U2 | 74.49 mΩ | 0.15 A | 11.17 mV | 2 |
| +4V_REG L2 -> U7 | 103.63 mΩ | 0.234 A | 24.25 mV | 6 |
| +3V3 U2 -> U1 pin 49 (VREG_VIN) | 88.26 mΩ | 0.15 A | 13.24 mV | 8 |
| +3V3 U2 -> U3 | 88.26 mΩ | 0.05 A | 4.41 mV | 8 |

Connector to buck input at 0.5 A: 19.74 + 4.95 + 135.15 mV of copper,
plus the fuse (0.132 Ω typical, 66 mV) and the eFuse (28 mΩ typical, 14 mV):
about 240 mV. At the 295 mA worst steady input current from the power
simulation it is about 140 mV.

## LED rail (+4V_LED from U7 to each LED) at 60 °C

| Case | Largest drop | Median |
| --- | --- | --- |
| firmware cap: 38 mA static + 25 mA drive, even | 7.2 mV at LED8 | 6.57 mV |
| limiter maximum 234 mA, even | 26.75 mV at LED8 | 24.42 mV |
| 38 mA static even + 196 mA in the 16 LEDs furthest from U7 | 29.37 mV at LED13 | 26.28 mV |

Worst case at the furthest LED: lowest buck output 3.908 V, minus
24.25 mV to U7, minus the TPS2553 switch (85 mΩ typical, about
135 mΩ hot: 20–32 mV at 234 mA), minus 29.37 mV on the rail = **about 3.82 V**
against the LED's 3.7 V minimum. At the firmware current cap the furthest LED
sees 3.97 V from a nominal rail.

## Current capacity (IPC-2221, external layer, 10 °C rise)

No track is above its limit. The highest loading is at the USB connector:
0.2 mm track carrying the full 0.5 A, 67 % of the 0.745 A limit; the 0.3 mm
sections of the VBUS path are at 50 %. Each of the 14 vias in series on the
long VBUS_PROTECTED_RAW run carries the full current; a 0.25 mm via is good
for well over 1 A.

## Heating (data-sheet thermal resistance × computed dissipation)

| Part | Dissipation | θJA | Rise | Junction at 50 °C inside the case |
| --- | --- | --- | --- | --- |
| U2 AP2112K, 150 mA | 0.105 W | 184 °C/W (DS39724 p.4) | 19 °C | 69 °C |
| U2 AP2112K, 300 mA | 0.21 W | 184 °C/W | 39 °C | 89 °C (limit 150 °C) |
| U18 TPS62932, 0.3 A out | 0.119 W (earlier thermal report, data-sheet efficiency) | 112 °C/W JEDEC | 13 °C | 63 °C |
| U8 TPS259470, 0.5 A | 11 mW at 45 mΩ maximum | — | about 1 °C | — |
| U7 TPS2553, 234 mA | 7 mW | 183 °C/W | 1 °C | — |
| U7 TPS2553, output shorted | up to 0.94 W (4.0 V × 234 mA) | 183 °C/W | exceeds its thermal limit | cycles on its own thermal shutdown until the firmware, which sees FAULT, drops EN |
| L2, 0.3 A | 4 mW | — | negligible | — |
| LEDs at the firmware cap | 0.25 W over 76 parts | — | negligible | — |

The LDO is no longer a thermal concern: the MAX38902A's exposed pad had no
thermal via, the SOT-23-5 dissipates through its leads and runs 39 °C above
ambient at twice the expected load.
