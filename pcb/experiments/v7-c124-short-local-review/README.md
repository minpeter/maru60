# Reviewed but UNSELECTED C124 local circuit trial

The selected board remains recovery commit e62f9ff / PCB 2c7e100a. This package does not change that selection. The complete independent actual geometry, contact, reference, artwork-carry and passive-model reviews are now preserved, superseding the earlier pending-review backup.

Latest experimental project: construction/isolated-v4-label-carry/pcb/maru60.kicad_pro. PCB SHA256 ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7. This carries selected labels/LOGO onto electrically identical 8c45df36 trial. Native DRC: 0 hard violations, 12 inherited expansion opens, 64 warnings; ERC/parity 0. The full original 7c23 source and accepted 2c7 artwork source are preserved.

Read construction/README.md and its two RESULT files first. Thirty-one bounded tracks are retired and 21 added; no drills changed, all retained copper and filled zones remain exact, and all unrelated physical net partitions are preserved. The pin-side 1.660404265 mm / capacitor-side 1.103279203 mm / local return 0.699231721 mm topology is independently bound. One new rooted support-tail warning remains explicit. This is not a DRC-clean board.

Analysis contains the independently checked passive comparison, actual geometry binding, and read-only smaller-capacitance alternatives. These use hypothetical parasitics, not extracted PCB parameters. Added 100 ohms meets the cited TI recommendation for capacitance above 10 nF; it is not a brownout solution or a blanket noise improvement. No alternate capacitor was selected.

Still unqualified: active eFuse/startup and repeated reset/pulse behavior, actual coupling and capacitor bias/temperature/age, assembly/3D envelope, exact current Murata approval-sheet details, hardware, EMC and production. Proposed BOM entries are not procurement authorization. The independent current carry review is included and finds no new electrical changes. Historical scripts retain their original execution paths; this is a verified archival package, not a claim of a fully relocated one-command replay or restored original Git history.
