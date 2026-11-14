# Selected design-operation evidence

This directory preserves the operations and SES data behind the 25-open checkpoint; it is **not a complete sequential replay recipe** and not a fabrication release.

- `inner-pass1.ses` and `inner-pass1-routing.json`: 267 tracks and 6 vias added by the limited-In2 finishing run. `merge_routes.py` merges only new records and asserts footprint positions.
- `COL10-ripup-ops.json` and `ROW2-ripup-reroute-ops.json`: the controlled ROW2 segment replacement that completes the local COL10 path.
- `r102-move2-ops.json`: R102 at (19.0, 35.1) mm, moving the USB via outside the SMD land. `translate_l1_dot.py` moves the L1 polarity mark 0.5 mm left; `pcbnew.FootprintSave` then updates the project library so native footprint comparison remains clean.
- `pth-*.json`: local ROW2/ROW4 changes that close the recommended PTH-hole-to-copper checks without changing the native clearance result.
- `edge-reroute22f-combined-ops.json`, `set_track_width.py`, and `cut_gnd_necks.py`: board-edge reroutes, ROW0 contact-width reinforcement, and two pour-only GND neck cuts.
- The `power-*` and `v3-*` files retain the accepted LED/3.3 V routes and their rejected-route cleanup records.

The native evidence in `qa/native-incomplete/RESULT.json` binds board SHA256 `bdb8c355b302dd473c73684190f5b9cb064e1017d33581b1db056dfac49d3eed`. Twenty-two open pairs and 57 dangling warnings remain; no order package should be produced from these intermediate operations.

For assembly placement, rerun `pcb/tools/fit_jlcpcb_placement.py` on the current geometry. Reusing the older candidate's fit file would incorrectly place U1 at its former (111, 81.5) mm position. The current dry run places U1 at (26, 35), R102 at (19.0, 35.1), and has no failed checks other than the expected incomplete DRC.
