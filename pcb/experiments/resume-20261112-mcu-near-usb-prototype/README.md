# MCU relocation prototype — NOT FOR FABRICATION

**Historical incomplete checkpoint.** Continue from the
[2026-11-13 routed candidate](../resume-20261113-mcu-near-usb-zero-opens/README.md),
which has 0 opens / errors / warnings and a separate fabrication package.
Its physical-fit hold still applies. The observations below describe only this
preserved 22-open board.

Work in progress on `feat/mcu-near-usb`, based on merged main `12bc13e` and the separate 2U Backspace candidate. This experiment does not replace `pcb/order` or either earlier candidate. The board is not electrically complete and is not approved for ordering.

## Placement

- U1 RP2350A: (111, 81.5) → (26, 35) mm, rotated 180° with its crystal, regulator inductor, and core decoupling group.
- U3 flash: (123.725, 88.45) → (10, 35) mm; its supply capacitors and pullup move beside it.
- D16 moves to (20.91, 31.25) mm to clear the regulator capacitor lands. Switch sockets, stabilizer geometry, outline and connector positions remain at their source coordinates.
- R102/R103 exchange their vertical order to terminate the new USB pair; R102 is now at (19.0, 35.1) mm so its USB via is outside the SMD land. The L1 polarity mark moves 0.5 mm left to preserve silk clearance, and the project footprint library is updated to match. MCU-side escape routes are redrawn.
- Local ground/power zone outlines and regulator keepouts move with the core. Existing inner-layer signal traces must be accounted for; this is not an exclusively outer-layer-routed source board.

## Diagnostic evidence, not acceptance

Nominal case-floor sampling with conservative assumed body heights found at least 1.55 mm below the moved bottom-side packages after the assumed 0.8 mm gasket travel. This is a placement calculation, not measured assembly qualification.

The current USB-only model gives connector-to-PHY delay 0.427 ns against its 1 ns criterion, using the actual relocated MCU routes and vias. It does not qualify the unfinished board, and must be rerun on the final geometry. Actual material tolerances and PHY behavior remain model assumptions.

The current checkpoint has 22 open pairs and 57 dangling track/via warnings, with no other native DRC violations. A limited set of 34 In2 segments completes VBUS, QSPI_SS, MCU_GPIO24 and COL9 while both inner GND planes remain single-island. All 32 JLCPCB DFM rules are otherwise clean, including SMD-pad via exclusion and the PTH/silk checks. Native ERC, schematic parity and a 79-file cold refill pass with those expected incomplete diagnostics; the material graph is regenerated, but 1,589 guarded-contact failures remain and are not strict acceptance. Matrix/LED/expansion/power routing, PDN and complete non-USB SI checks remain pending. Both QMK layouts rebuild to the same UF2 bytes as the order-candidate's verified firmware. No previous candidate's passing report applies to this PCB.

## Working evidence

The construction workspace is `build/mcu-near-usb/` (ignored). It holds placement operations, geometry snapshots, native DRC reports, routing attempts and USB diagnostic models. The published evidence in this directory is explicitly a prototype checkpoint; see `qa/status.json` for exact hashes and remaining issues when available. Native, DFM, USB-SI, PDN and mechanical-fit reports are kept under their respective `qa/` subdirectories, and selected operations are preserved in `qa/design-operations/`.

Freerouting is being evaluated on a separate DSN/Ses conversion with critical USB/crystal/regulator traces locked. It runs without network access. Its output is not accepted until imported into KiCad and independently checked; DSN conversion is not authoritative for manufacturing geometry or clearances.
