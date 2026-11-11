# Signal integrity

Computed and simulated from the routed copper of the order candidate with the
tools in [`pcb/tools/signal_integrity`](../../../../tools/signal_integrity/README.md): a
2-D field solve of the outer-layer cross-section (checked against
Hammerstad–Jensen within 0.5 %), lossy LC-ladder line models and ngspice.
Driver and pin values the data sheets do not give are assumed and swept; the
tool README lists them. Nothing is measured. Numbers: `results.json` next to
the tools.

**One change came out of this:** `R115`, 100 Ω in series at the source of the
276 mm underglow data hop (below). It was added after these simulations were
run; the simulated cases with a 100 Ω or weaker driver are the ones that then
apply to that hop.

## Verdict

| Signal | Result | Margin | Basis |
| --- | --- | --- | --- |
| LED data, buffered first hop (U5/U6 → 330 Ω → first LED, 137 mm / 116 mm) | clean edges, no overshoot | noise margin 0.88 V high / 1.4 V low; pulse-width error at most 16.47 ns against a 100 ns tolerance | simulated |
| LED data, LED-to-LED hops (76 hops, 19 mm typical, 81 mm longest key hop) | no extra threshold crossing with a 100 Ω / 10 ns or weaker LED output | full 4 V swing at the receiver | simulated; LED output strength assumed |
| LED data, long underglow hops (276 mm `UG_LED_6`, 105 mm `UG_LED_9`) | clean with a 100 Ω / 10 ns output; **re-crosses the 3.12 V threshold if the LED output is 20 Ω with a 2 ns edge** (high level dips to 2.67 V on the 276 mm hop) | — | simulated; led to R115 |
| LED data on the Caps Lock alternative sites (stubs up to 22 mm, one via) | same as an ordinary hop | — | simulated, all four site combinations |
| Matrix lines coupling into LED data | 0.30 V worst routed pair (49 mm beside a column at 0.25 mm); 0.65 V for a hypothetical 80 mm at minimum clearance | noise margin 0.88 V | simulated |
| USB full speed, device transmitting, at the host after 1 m | crossover 1.65–1.652 V, rise/fall matched (100.0 %) | limits 1.3–2.0 V, 90–111 % | simulated |
| USB full speed, host transmitting, at the RP2350 | crossover 1.67–1.691 V | 1.3–2.0 V | simulated |
| USB pair | 0.25 mm tracks 0.2 mm apart for 124 mm: 95 Ω differential; skew 1.6 ps | full speed has no impedance requirement on the board | field solve |
| USB delay connector → MCU | 1.03 ns | 1 ns is the device allocation in the USB 2.0 delay budget; 3 % over | computed |
| Crystal | load 8.47–8.69 pF against 10 pF specified: -4.7 … 36.5 ppm | USB full speed allows ±2500 ppm | computed from pad and track capacitance |
| Key matrix settling | 7 ns typical, 45 ns with the weakest pin (125 Ω, 86 kΩ pull-up), 134 ns with six keys of one row held | QMK waits 247 ns before reading: 35 × / 5.5 × / 1.8 × | simulated, longest row and column |
| Key matrix settling, all 15 keys of one row held, weakest pin | **295 ns, longer than the 247 ns QMK waits** (94 ns with a typical 40 Ω pin) | 0.8 × | simulated; firmware note below |
| Key matrix leakage at 60 °C | 0.648 V droop with all 61 diodes at maximum leakage | 1.3 V allowed: 2.0 × | computed |
| QSPI flash | 23 mm longest, 34.2 ps mismatch | 13.84 ns slack at the 25 MHz the firmware uses | computed |

## The long underglow hop and R115

The underglow chain has six LEDs along the back edge and six along the front.
`UG_LED_6` joins the last of the first group to the first of the second and
runs 276 mm with 8 vias, unterminated, at about 73 Ω. An SK6805 regenerates
the data on its DOUT pin; OPSCO's data sheet gives no output resistance or
edge rate. With a 100 Ω / 10 ns output the received waveform is clean. With a
20 Ω / 2 ns output the reflection brings the high level down to
2.67 V, below the 3.12 V input threshold, and the low level up to
1.333 V, at the 1.4 V low threshold: a strong, fast LED output could corrupt
the underglow data after LED68.

`R115` (100 Ω, 0402, bottom side next to LED68) makes the source impedance at
least 100 Ω whatever the LED does. Its RC with the 22 pF line and 5 pF input is
under 3 ns against a 300 ns shortest pulse. The 105 mm hop `UG_LED_9` fails
only with a 20 Ω output and an edge of 2 ns or faster; it and the 81 mm key hop
were left as they are.

## Matrix read delay with a whole row held

QMK reads the columns 0.25 µs after it drives a row (`GPIO_INPUT_PIN_DELAY`,
37 CPU cycles at 150 MHz). One row driver then has to pull every closed
column low through its diodes. With all 15 keys of a row held, the pin at its
125 Ω limit and the pull-ups at their weakest, the last column is valid after
295 ns, so that scan could miss a key; the next scan, 30 µs later, sees it. It
needs 15 simultaneous keys in one row and a worst-case pin, and costs nothing
to remove: `#define GPIO_INPUT_PIN_DELAY (CPU_CLOCK / 1000000L)` (1 µs) in the
keyboard's `config.h`. **Not applied here**: the firmware overlay is pinned by
hash to its archived build evidence and was left untouched; make the change
when the firmware is next rebuilt.

## USB delay

The earlier estimate of 0.89 ns used a microstrip formula; the field solve of
the coupled pair gives 1.03 ns odd-mode. The 1 ns figure is this device's share
of the 30 ns end-to-end budget for a full-speed link through five hubs with
5 m cables; 30 ps over it has no effect on a keyboard on a normal port. Do not
lengthen the route.

## Plots

`led-first-hop.png`, `led-hops.png`, `led-crosstalk.png`, `usb-fs-eye.png`,
`xtal-negative-resistance.png`, `matrix-settling.png` in this folder.
