MARU60 resumed routing checkpoint

Open pcb/maru60.kicad_pro. Exact selected PCB SHA256:
04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99

The EXT_GPIO26 header-side connection is now routed from J3 pin 8 to its already-routed U11/U13 network. The separate MCU_GPIO26 connection is still open. Native open connection pairs fall from 12 to 11. The same 51 warnings remain, with no other DRC errors, ERC violations or schematic parity findings.

Only two 0.15 mm outer-layer segments and one 0.5 mm / 0.25 mm-drill through via were added. No old conductor, component, schematic, rule or firmware was changed. Added length: 3.602290795897 mm. Total: 13,188.057740811157 mm, 9,752 segments and 920 vias.

The first candidate (76653875) was rejected because its via antipad cut the ground reference beneath existing EXT_GPIO10. Moving the via to (95.075, 40.175) eliminated every old signal-reference loss in both inner planes. Native all-hole material checks preserve all old contact witnesses and unrelated pad partitions. Both inner GND planes remain one component. New-track unsupported projection is confined to explicitly declared signal-via transition envelopes. An existing ground through-via is 0.77862 mm away. This is bounded geometry evidence, not an impedance, SI, EMI, dynamic stability or hardware guarantee.

Independent DRC, raw-to-native net identity, all 1,064 electrical schematic pin bindings, full-plane reference checks and byte-identical cold refill passed. All 58 candidate files retain identity under independent refill. Read SELECTION.json and evidence for source-bound results and limitations.

This is a continued prototype-development selection only. Remaining work includes 11 expansion open pairs, 51 warnings, input/current/stackup assumptions, active fault/startup/brownout/pulse models, full QMK/ARM builds, and physical/mechanical/manufacturing gates. LED qualification stays OFF. No public push, ordering or flashing. Original recovery and rejected designs remain preserved.
