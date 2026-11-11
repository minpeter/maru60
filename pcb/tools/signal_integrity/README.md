# Signal-integrity checks for the order candidate

Everything here is computed or simulated from the routed board. No hardware
exists and nothing was measured. The report is
[`qa/signal-integrity/REPORT.md`](../../experiments/resume-20261111-order-candidate/qa/signal-integrity/REPORT.md).

## Rerun

```sh
# 1. geometry dump of the board (KiCad container), if the board changed
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py \
  pcb/experiments/resume-20261111-order-candidate/pcb/maru60.kicad_pcb build/order-review/final.json

# 2. ngspice image (network is needed for this step only) and a Python with scipy
docker build -t maru60-ngspice:bookworm pcb/tools/signal_integrity
uv venv build/si/venv
uv pip install --python build/si/venv/bin/python numpy scipy matplotlib shapely

# 3. everything (about 10 minutes; the LED driver sweep is most of it)
build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py
# or one step, e.g. only USB (geometry.json must exist):
build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py sim_usb.py
```

Outputs: `results.json` in this folder, the generated ngspice decks in `decks/`,
plots in the report folder, raw waveforms and logs in `build/si/out/` (git-ignored).
Any deck can be rerun alone:

```sh
docker run --rm -v "$PWD/pcb/tools/signal_integrity/decks:/decks:ro" -v "$PWD/build/si/out:/out" \
  -w /out maru60-ngspice:bookworm -b /decks/usb_04_device_tx_8ns.cir
```

## Files

| File | What it does |
| --- | --- |
| `Dockerfile` | Debian bookworm + ngspice 39 |
| `geom.py` | Copper graph of a net from the geometry dump: pad-to-pad path, stubs, vias, neighbours, plane coverage |
| `fieldsolve.py` | 2-D finite-volume Laplace solve of the outer-layer cross-section: C, L, Z0, odd/even mode. `--selftest` compares it with Hammerstad–Jensen (within 0.5 %) |
| `extract_geometry.py` | Writes `build/si/out/geometry.json` and `lines.json` |
| `spice.py` | Deck builder (LC ladders, coupled ladders, vias), ngspice runner, waveform measurements, plot style |
| `sim_led.py` | Every kind of LED data hop, the two buffered first hops, crosstalk from matrix lines, DOUT strength sweep |
| `sim_usb.py` | Full-speed eye at the host and at the RP2350, test-load edges and crossover, pair impedance and delay |
| `sim_xtal.py` | Crystal load capacitance, negative resistance against amplifier gm, drive-level bound |
| `sim_matrix.py` | Row select and release settling against QMK's delays, diode leakage budget |
| `check_misc.py` | QSPI, BOOTSEL, SWD, RUN and the expansion port (hand calculations) |
| `run_all.py` | Runs the steps and merges `results.json` |

## Models and their limits

- Stack: F.Cu 35 µm / 0.2104 mm 7628 prepreg (εr 4.4) / In1 GND, mirrored on the
  bottom. Solder mask 20 µm, εr 3.8 (assumed). Traces next to a top-side pour are
  treated as plain microstrip.
- Lines are lossy LC ladders with sections of 2 mm or less (12 ps); the fastest
  edge simulated is 1 ns.
- Via: 0.49 pF and 1.36 nH from the usual closed-form expressions.
- Values the datasheets do not give are assumed and swept, and the report says so:
  SK6805 DOUT strength and DIN capacitance, RP2350 pad capacitance and output
  resistance, RP2350 USB PHY edge rate, RP2350 oscillator transconductance and pin
  capacitance, crystal motional capacitance.
