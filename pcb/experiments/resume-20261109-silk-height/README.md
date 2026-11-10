# PCB review follow-up, 2026-11-09

This checkpoint changes reference lettering only. It retains **nine open pairs**
and is **not manufacturing-ready**. The strict baseline is unchanged.

The source is `../resume-20261106-usb-pendant-prototype/pcb/`, board SHA256
`41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5`.
The candidate board SHA256 is
`ddea15f7eb9188617f81af2e998ed49bf385cfcc473d68bd40beb66ec4ff6020`.

## Change and reproduction

Twelve reference text heights increase from 0.75 to 0.8 mm, retaining their
0.75 mm width. R141's reference also moves 0.075 mm left in board coordinates
to avoid a new silk overlap. Its existing solder-mask clipping warning remains.
C125 and R132 retain their original text: increasing them introduced new
overlaps, so those changes were excluded. The resulting warning count is 26,
down from 38, with no new warning identities (type, severity, ordered item UUIDs).

`changes.patch` is the complete PCB byte difference. Every other board byte,
including all copper, pads, holes, zones and fills, is unchanged; all other 57
CAD files are identical. `qa/byte-scope.json` lists the exact reference UUIDs and
changes; `qa/warning-delta.json` records the native warning comparison.

From the repository root, reconstruct into a fresh ignored directory:

```sh
mkdir -p .omo/evidence/silk-rebuild
cp -a pcb/experiments/resume-20261106-usb-pendant-prototype/pcb .omo/evidence/silk-rebuild/pcb
patch -d .omo/evidence/silk-rebuild/pcb -p1 < pcb/experiments/resume-20261109-silk-height/changes.patch
cmp .omo/evidence/silk-rebuild/pcb/maru60.kicad_pcb pcb/experiments/resume-20261109-silk-height/pcb/maru60.kicad_pcb
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint pcb/experiments/resume-20261109-silk-height --expected-opens 9 --output .omo/evidence/silk-native-new --material
```

See `qa/native/` for fresh DRC/ERC, net identity, cold-refill result and logs.
`qa/material-equivalence.json` binds the two fresh material exports and compares
every field except source path, board hash and runtime. The candidate export is
compressed as `qa/material-graph.json.gz`. Native ratsnest representatives may
differ while naming the same physical components; material partitions establish
the retained nine open-component pairs.

`qa/netlist.xml` deliberately preserves the source checkpoint's exact stored
export, pinned by the portable wrapper. All schematic bytes are unchanged.
`qa/native/netlist.xml` is the separate fresh export checked against this board.
Neither file is a substitute for routed continuity.

## Guarded-contact finding

The 51 inherited rejected contacts attach 48 isolated, padless material fragments:
10 GND contacts/fragments, 16 USB_DP_CONN contacts/fragments and 25 +4V_LED
contacts on 22 fragments. None has an admitted bypass between its exact endpoints.
Counterfactually admitting all 51 changes 380 material components to 332 while
leaving all named-pad partitions across 1,084 pads unchanged. They do not explain a named-pad
disconnection in this graph. They remain rejected; this does not establish
physical contact or manufacturing margin.

`guard-classification/` preserves the source-bound graph traversal, cut witnesses,
51 support paths and 51 edge-removal negative controls. Its original README and
SHA256SUMS record the actual local invocation paths. To replay without editing
this archive, copy `classify.py` into a fresh directory four levels below the
repository root, for example `.omo/evidence/contact-new/run/classify.py`, then
run that copied script with `uv run`. It reads the preserved November 6 source
graph. `qa/material-equivalence.json` also binds that geometry to this checkpoint.

## Routing attempts and remaining work

`rejected-header/` preserves a GPIO24 candidate that reached eight opens,
38 warnings, no other DRC errors, ERC/parity zero and 58 identical cold-refilled
CAD files. It is **rejected**: both inner planes lose exact remote copper outside
the new-via envelopes and actual holes. The rational non-boundary witness
`(591575297/4, 165675501/4)` nm, approximately `(147.89382425, 41.41887525)` mm,
is source copper and candidate non-copper. No tolerance or rule waiver was used.
Full candidate material/contact acceptance was not run after this decisive failure.
The rejected board is retained separately; to rerun native checks, copy the source
58-file CAD directory into a fresh checkpoint and replace only its board with
`rejected-header/maru60.kicad_pcb`. Request eight expected opens explicitly.

The no-new-via header follow-up exhausted its bounded reachable region without
a route. `routing-search/` records other bounded outer-face/fanout failures,
including no legal GP26/GP27 escape-via sites within the searched 3 mm radius.
These are finite searches, not a proof that no overall layout can work.
Original local scripts and complete exploratory logs remain under
`.omo/evidence/pcb-routing-20261109/` on the review server; only the stated
summaries, decisive rejected board and witnesses are packaged here.

Three header pairs and six MCU pairs remain open. Further routing needs another
placement or transition topology followed by the complete copper/contact gates.
USB SI/EMI, effective capacitance, active power, current/inrush, thermal, physical
fit and hardware behavior remain unqualified. The portable 519-assertion power
replay checks recorded arithmetic only. Lighting qualification stays OFF.

## Full firmware build replay

`qa/qmk-build/` retains the complete fresh WKL `via` and HHKB `via_hhkb` build
packet: both exits zero, actual compiler/link logs, recursive submodule identities,
both applied hash-guarded patches, the unchanged 22-file overlay, package versions,
ELF/UF2 files and hashes. All six actual LED translation-unit macro dumps define
`MARU60_LED_POWER_QUALIFIED 0`. No compiler `warning:` or `error:` was reported.
This is default-OFF build evidence, without flashing or hardware qualification.

To repeat on a fresh checkout, first build the KiCad base image as described in
`docs/pcb-validation.md`, then prepare the two input recipes and output directory:

```sh
mkdir -p build/pcb-qmk-20261109 .omo/evidence/pcb-routing-20261109/qmk-build
cp pcb/experiments/resume-20261109-silk-height/qa/qmk-build/Dockerfile build/pcb-qmk-20261109/
cp pcb/experiments/resume-20261109-silk-height/qa/qmk-build/build-layouts.sh build/pcb-qmk-20261109/
```

Then follow `qa/qmk-build/REPRODUCE.md` using fresh paths (the initial build
checkout and output directory must not contain a prior run). The initial image
setup hit its 600-second limit during unpack after image export; the exported
image subsequently started and both builds passed. The setup timeout remains
recorded and is not represented as a successful image-build command.
