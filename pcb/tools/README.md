# Current physical-material checker

`export_material_graph.py` is the exact reviewed R2 implementation, SHA256 57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9. It accepts an input PCB path and an output JSON path. It requires the checked KiCad 9.0.2+dfsg-1 Python bindings, exactly four copper layers and the asserted through-hole geometry. Unsupported cases fail closed. Do not use optimized Python.

The caller must supply a new output path distinct from the input board; the preserved checker itself does not enforce output-path exclusivity. The following example uses a separate output file. Do not pass an existing CAD or evidence file as the output.

Example from this repository:

`/usr/bin/python3 pcb/tools/export_material_graph.py pcb/experiments/v7-buck-feedback-cleanup/candidate/pcb/maru60.kicad_pcb /tmp/v7-material-graph.json`

For isolated runs, set fresh private XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_DATA_HOME, XDG_STATE_HOME and XDG_RUNTIME_DIR directories; the runtime directory must have mode 0700. This script does not configure isolation itself. The historical runner's XDG_RUNTIME_HOME typo is explicitly recorded in the erratum, not silently fixed in its receipts.

This is a source-specific nominal material-connectivity checker, not a DRC/ERC/parity checker, independent CAD kernel, analog/SI simulator, manufacturing or hardware qualification. Native candidate-pair discovery can omit a geometric contact; accepted contacts require conservative positive material overlap. See `../experiments/v7-material-contact-correction/` for all reviewed controls, exact selected-board contact witnesses, original limitations and superseded evidence. Stored test/report paths preserve execution provenance; no relocated one-command replay of every historical suite is claimed.
