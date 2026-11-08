# Actual LED_ENABLE closure: isolated A21 checkpoint

## Result

The immutable PCB `candidate.kicad_pcb` is SHA256 **b5dc3fbab560f200a4144b38a11a273d24fd432eee98bc14eb0515703008906f**. It comes from A22 `fdd9ce12580c1dc8a1fe14dfced60f0199b2911b2d7c87a818a2bf7affb5fa33`, with no footprint, pin, component value, DNP attribute, board outline or zone-definition change. Accepted main remains `80681cd392d1ca83bd37e58faef07a0def301f2d93763102982eaf1c0148f831`.

This is an actual U1.34 → R109.1/U7.3 connection, not a tail-only or orphan-removal count reduction. Every other populated nonrail connected-component partition is unchanged, including the complete UNDERGLOW and COL1 functions. The final native result is **21 opens, 0 hard errors, 58 warnings, schematic parity 0 and ERC 0**. The 21 remaining opens are itemized in FINAL-SUMMARY.json. This board is still incomplete and is not accepted main.

## Coherent three-net arrangement

The original MCU exit was bounded by recent FAULT and UG copper. An outboard via alone was insufficient because COL1 segment `87fad0e2-f9b6-4f24-b77a-499bd0b8c3db` was a real separator. The final arrangement reserves the entire ENABLE exit and COL1 lane before routing UG, including continuous reservation checks during path simplification.

- ENABLE uses a standard 0.50/0.25 mm transfer at (36.4,19.2), beyond the crystal no-drill envelope, and reaches the existing remote populated component. Added ENABLE copper is 41 tracks / 120.368871526 mm and five standard vias. This is positive signal centerline length, not a return-loop or vertical-via length.
- The exact recent UG B arm between (34.975,16.475) and (38.35,21.725) changes from 114 tracks / 6.647970773 mm to 7 tracks / 6.545437621 mm. The U1.33 → U6.2 function is retained.
- The single COL1 segment between (34.325,16.55) and (37.7,21.4) changes from 5.908732944 mm to 6 tracks / 6.224685530 mm. No switch, load, pad, or endpoint moves.
- Eleven recent FAULT launch tracks are replaced by four tracks preserving the actual four-pad fault function. The only GND retirement is audited unloaded old C107 tail `7feee974-e301-44e1-95ec-db424b6bbee6`, 1.170288853 mm. GND via `6a3f580c-5712-47ea-8383-e2a4d03abf80` and tail `54f14d63-40e1-426a-a963-26583874af9e` remain byte-for-byte unchanged. No via is retired, and the tail retirement is not credited as a functional closure.
- The newly introduced ENABLE via originally at (40.85,20.2) was moved west to (40.7,20.2), along with only its two new legs, to eliminate a small collateral reference deficit. The north alternative was rejected. No deficit is waived in the final candidate.

## Completed evidence on the exact final bytes

The hash-bound bundle has 17 completed processes, all 13 source witnesses passing, and no unconnected protected power/clock/USB/QSPI net. Seven additional source witnesses cover XIN, XOUT, XTAL_OUT, UG, FAULT, ENABLE and COL1. Identity gates retain 340 footprints, 924 unique numbered pins and all 1,275 physical pad identities/attributes/net assignments.

The canonical retained-node and semantic-net comparison runs before native Load, then after Load, BuildConnectivity, refill and same-path Save. The prior rejected reassignment fixture remains a negative regression. Never relabel already reassigned copper to make a guard pass.

The no-Unfracture native old-minus-new comparator checks all **9,545 retained outer tracks**, including LED chains and supply tracks: **zero new center or parallel-edge reference loss**. All newly added COL1, UG, FAULT and ENABLE traces also have zero continuous center/edge projection loss outside explicitly declared same-net 0.55 mm launch disks. Existing inherited exceptions are not upgraded to qualification.

Four new GND stitches serve the remote ENABLE transitions. Final nearest source-contacting GND center distances are 0.781025 mm at the local transfer, 0.95 mm at (40.7,20.2), and 0.8 mm at each of the other three transitions. The local return is existing GND via (35.9,19.8). Actual annular filled-plane intersection evidence is included. These distances are not total return-loop lengths or waveform/inductance qualification.

Cold refill is byte-identical. Exact canonical-source removal/addition replay using the full native node ledger also regenerates the identical PCB bytes. `replay_exact_delta.py`, `replay-proof.json`, and the serialized S-expression ledger preserve the distinction between native numeric tokens and quoted strings.

## Power-fill tradeoff and limits

B-side +3V3 filled copper loses **0.268960924894 mm²** and gains **0.000000181606 mm²** relative to A22 because of the local FAULT refinement. Therefore this packet does **not** claim identical positive fills. Other positive rail fills retain their coordinates; all 13 source/connectivity gates and native protected-net checks pass. Source connectivity is not current-density, PI, startup, thermal or powered-rail qualification.

The buffer rail-off/reset/trip/collapse logic gate remains blocked, and no firmware, regulator, current-limit or power architecture changes are adopted. Oscillator startup/load/drive, actual switch SKU/full assembly, fabrication capability and physical waveform gates remain open. There are no new parts, orders, public pushes or accepted-main edits.

Partial board totals are 12,111.263716155 mm / 890 vias / 9,817 segments. These cannot be compared as a completed-routing improvement while 21 opens remain. Earlier provisional placement and routing alternatives remain separate and are not substitutes for this final candidate.

## Reproduction and safe continuation

Use matching KiCad 9 project/schematic/libraries and standard 0.50/0.25 mm vias with the unchanged 0.15 mm project clearance. For an independent native check: `kicad-cli pcb drc --format json --all-track-errors --severity-all --schematic-parity -o drc.json candidate.kicad_pcb`; run schematic ERC separately. Exact delta reconstruction can be run with `/usr/bin/python3 replay_exact_delta.py` in a writable copy of this packet with KiCad Python available.

Continue only from an isolated copy, preserve the canonical source and this immutable packet, and rebase exact source UUID deltas rather than overwriting a newer board. The owner coordinates integration with concurrent RUN/SWDIO work. No public push or main adoption is authorized by this packet.
