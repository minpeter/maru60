# Original simulation-tool evidence

These are the exact `geom.py`, `spice.py`, `sim_led.py` and `analyze_pdn.py` bytes hashed when this older
Backspace candidate was validated. The shared tools subsequently changed to
count inner-layer via excursions and reject incomplete ngspice analyses, and
to avoid numerical-zero LC sections. The PDN tool now preserves duplicate
load sites and currents, includes overlapping round copper caps and rejects
loaded floating components instead of silently giving them a weak ground tie. The manifest now points to these preserved
original bytes instead of requiring the shared tools to stay frozen.

No historic simulation output was regenerated or relabelled. These source
files are provenance snapshots, not a standalone simulation environment. Use the
new MCU-near-USB candidate for current-tool results on its own board.

The current LED sweep also uses unique per-corner decks and optional concurrent
runs; its historical crosstalk labels are now marked as sensitivity envelopes.

The geometry dump and copper-material exporter are also preserved at their
original hashes; shared versions later gained board-cutout handling.
