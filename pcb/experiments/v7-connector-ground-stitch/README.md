# Connector ground stitch: experimental working selection

Open `candidate/pcb/maru60.kicad_pro`. Exact selected PCB: aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca. Its predecessor c770 remains unchanged in the preceding unit.

One ordinary GND through-via is added at (17.20, 9.90) mm, diameter 0.50 mm and drill 0.25 mm. Every prior object, component, setting and saved zone record is unchanged. The actual physical ground loss is only the declared new drill, 0.049087681002 mm² per inner plane. Existing current and historical signal shadows, old contacts, all 245 pad-net partitions and 247 original ground-pad roots are preserved. The independent cold refill is byte-identical.

Native status: 9,750 tracks, 919 vias, 382 footprints, 13,176.816253756544 mm track length; 66 unchanged warnings, 12 unchanged expansion opens, zero other hard DRC, zero ERC and zero schematic parity findings. All source evidence remains frozen below `frozen-trial`; its original UNSELECTED labels describe the pre-adoption checkpoint and have not been rewritten. The 92-warning ledger is carried without suppressions.

This is a bounded nominal geometry/connectivity selection for ongoing experiments. It does not restore the USB neck or remove the connector stub. Added grounded copper may change local fields and coupling; no post-change extraction, measured inductance, SI/ESD/EMC gain, startup, assembly or hardware qualification is claimed. LED qualification remains OFF. No push or fabrication is authorized by this record.

Full pre-adoption source/prefill/filled evidence was durably saved in Space as libfile_6e57b31450488191baf5790a6a6ef6dd, archive SHA c79d1364355892fb997c73f2f1590b6f2a30b27cd335db5f71f12e04be76960d. The original lost Git history remains missing; this is the separate recovery lineage.
