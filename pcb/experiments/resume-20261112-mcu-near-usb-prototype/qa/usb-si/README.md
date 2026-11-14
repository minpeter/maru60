# USB full-speed model evidence

`usb.json` contains nine ngspice cases for the relocated USB geometry, and `usb-fs-eye.png` shows the 8 ns device/host eyes and the 50 pF J1 test-load response. `geometry-summary.json` is the extracted board-model input.

- Connector-to-RP2350 delay: **0.427 ns** against the 1 ns model criterion.
- Simulated DP-minus-DM arrival skew: **-46.75 ps**.
- J1-to-27R delay: **0.337 ns**.
- All four USB connector vias and both actual PHY-side vias are modeled. The simulator no longer uses the old fixed 4.104/3.82 mm PHY stubs.
- At the J1 50 pF test load, the modeled 4/8/16 ns ramps produce 4.72/7.17/13.08 ns rising and 4.73/7.17/13.08 ns falling times, with crossover inside 1.3–2.0 V.

These are computed full-speed models, not USB high-speed analysis, compliance measurements, or hardware qualification. Source resistance, PHY capacitance, dielectric corners, cable and host-load assumptions are listed in `pcb/tools/signal_integrity/sim_usb.py`. The 25-open checkpoint is not an accepted final board; rerun the model after the final route is frozen.
