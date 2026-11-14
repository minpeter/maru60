# Final-board signal models

Electrical results were computed from PCB
`86c4243dc112f308ab22614bf576716b77d9c33a38fea3776249dace63da6a5e`.
Final PCB `2cc544c8e6eb00bd3f53fa480a0167dcb8e14dac687f7eb2af0c85946bda5584` differs only by a
0.2 mm R193 reference-text move. [Geometry equivalence](../geometry-equivalence.json)
proves byte-identical copper/pads/holes and records the exact CAD difference.
There are no hardware measurements and no global SI/compliance approval.
[assessment.json](assessment.json) gives the measured case counts and narrowly
applied criteria. Individual JSON files retain all raw scenario metrics.

## USB full speed

The connector-to-RP2350 propagation model gives **0.4270 ns** against the
1 ns board-delay criterion, with DP-minus-DM skew −46.68 ps. RP2350 supports
full speed; this does not qualify USB high speed or order controlled impedance.

The three device-transmit **50 pF test-load** cases meet the modeled crossover,
4–20 ns rise/fall, matching and jitter limits. Six further scenarios model
transmission through a 1 m cable, including a 150 pF host-load corner.
The transmitter test-load limits do not apply indiscriminately to these
receiver-node measurements. In particular, the raw 4 ns host-transmit scenario
reports a 519.3% rise/fall ratio; it is preserved in `usb.json`, not counted as a
transmitter compliance pass. The receiver eye and timing are separate model
outputs. Actual PHY strength, edge rate, parasitics and cable remain assumptions.

[USB eye plot](plots/usb-fs-eye.png) and [raw results](usb.json).

## LED data

R192/R193 = 100Ω and R115 = 150Ω resolve the [pre-damping failures](pre-damping/README.md).
The actual routes pass [24 targeted strong/weak/load cases](led-damping/results.json),
including both LED30 populations. The all-hop strong-driver screen now records
threshold recrossings and minimum timing budgets as well as noise margins.

The report distinguishes the populated circuit from resistor-removal
counterfactuals. `assessment.json` checks populated-hop pulse-width budgets,
threshold recrossings and high/low margins, the two buffered first hops, the
strong-driver screen and the populated strength sweep. Counterfactual negative
margins are retained; removing the damping resistors is not the selected circuit.
The separate [54-case Backspace sweep](backspace-led.json) covers all changed
source/destination population pairs with six assumed driver corners at 4 V.
LED output strength and input capacitance are not specified by the supplier;
these are explicit model assumptions, not guaranteed production corners.

The crosstalk subsection of the inherited LED script uses **historical sensitivity
envelopes** (49 mm at 0.25 mm, 32 mm at 0.20 mm, and 80 mm at 0.15 mm). The labels explicitly mark these as historical envelopes, not the new
board's actual neighbors. For example, final UG_LED_6's extracted nearby
matrix line is COL11 (16.803 mm within 0.6 mm, minimum gap 0.367 mm), not the
legacy COL10 scenario. Treat these crosstalk runs as hypothetical sensitivity
probes. Final neighbors are in `geometry.json`; complete coupling, return-current
and EMI qualification has not been performed.

[Hop waveforms](plots/led-hops.png), [first hops](plots/led-first-hop.png),
[crosstalk probes](plots/led-crosstalk.png) and [raw results](led.json).

## Matrix, QSPI and crystal

Nine matrix corners give a maximum **208.3 ns** select settling time against
800 ns configured wait, at least 3.8× margin. Release and leakage results are
in [matrix.json](matrix.json). This uses the recorded QMK timing constants and
assumed pin capacitance, not a measured scan timing trace.

QSPI SCLK is 25.937 mm; data routes are 14.463–17.804 mm. Including both via
barrels gives about 0.365 ns clock/data round-trip and 13.63 ns simplified
slack at configured 25 MHz. The 75 MHz comparison is unconfigured, is outside
the flash's 50 MHz limit for the selected 03h command, and is **not** endorsed.
Inner traces use approximate per-mm parameters, not a solved inner-layer field.
[Miscellaneous signal calculations](misc.json) also cover reset, BOOTSEL, SWD
and expansion pins without certifying ESD or external-cable performance.

Crystal startup remains **conditional**. At worst assumed pin/C0 values,
negative resistance exceeds 5× maximum ESR at the sampled gm = 1.5 mS; actual
RP2350 oscillator gm is not guaranteed by this model. The load estimate spans
8.4–10.15 pF depending on pin and output-branch accounting. The drive bound
peaks at 177.4 µW under the assumed model, below the 200 µW maximum but not a
measured limit. See [xtal.json](xtal.json) and the
[negative-resistance plot](plots/xtal-negative-resistance.png).

## Numerical correction and evidence

The old `led_hop19_weakp` deck contained a floating-point split remainder of
roughly 2e-15 mm. That produced a near-singular section (about 9.5e-25 H and
2.7e-28 F), and ngspice aborted even with finer Gear integration. Both failed
decks and logs are retained in [numerical-failure](numerical-failure).
Partial waveforms were rejected and are not used in any accepted result.

The fix treats ≤1e-9 mm as a junction using the existing 1 mΩ convention,
1000× below KiCad's 1 nm grid. All physical route sections remain. The corrected
case completes with the original trapezoidal solver; halving maximum timestep
from 0.2 to 0.1 ns changes reported pulse widths and margins by 0.00 ns / 0.000 V
at the stored precision. [Convergence evidence](convergence/results.json)
records its thresholds, measurements and two complete decks. `experiment.py`
preserves the original diagnostic invocation with historical build paths.
No automatic solver retry or electrical-limit relaxation is used in final runs.

`source/` preserves the exact simulation Python files. The step provenance files
retain the actual simulation-input board and decompressed geometry hashes.
The geometry-equivalence record binds those inputs to final CAD. `ngspice-decks-and-logs.zip` retains generated decks/logs; the full raw waveforms remain under ignored
`build/`. Each sweep and screen corner now has a unique deck name. Independent corners
can run concurrently with `MARU60_SI_WORKERS=4`; the default is one worker.
A timed-out simulation removes only its own Docker container. Stub traversal
now follows source-to-destination order, removing Python hash-seed dependence.
Two fresh final-board extractions are byte-identical; see `extraction-repeat.json`. Stack/dielectric, via and driver assumptions are listed
in [the shared model notes](../../../../tools/signal_integrity/README.md).

`waveform-reuse.json` records each fresh simulation or reused completed waveform.
Reuse requires byte-identical electrical decks after normalizing only the initial
comment/title and output filename. Stimuli, circuit values, solver settings, vectors
and stop time remain exact; finite complete waveforms and their hashes are checked.
Measurements are recalculated, including former failures; no case is selected by
outcome. `waveform-reuse-runner.py` records the construction invocation.
