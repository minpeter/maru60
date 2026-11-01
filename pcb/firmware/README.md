# RP2350A QMK / VIA integration draft

Firmware starting point: `emolitor/qmk_firmware`, branch `em-rp2350`, pinned at `431ed9ade0684e98a66eabc949563c3be8f446e8` (revision recorded during research for this iteration). The author reports Pico 2 USB enumeration, WS2812 output, and EEPROM-emulation flash persistence on ARM and Hazard3/RISC-V. This is upstream author-reported hardware verification; Maru60 has not been built or tested.

That branch includes an RP2350 handwired one-key target and an inherited `via_ci` target. QMK Raw HID, VIA dynamic keymaps, and the RP2350 flash-backed EEPROM path are present. The cited one-key target is only an MCU/port starting point, not this keyboard's firmware. We have not established a VIA desktop app end-to-end test for the Maru60 board.

## Integration plan

- Create a QMK keyboard target after confirming the branch is still available and pinning its exact tree revision/submodule dependencies.
- Define an electrically reviewed 5×14 (or smaller if layout analysis permits) diode matrix and map it to the selected RP2350A package GPIOs. This is a pin-budget proposal only; no pin assignments are approved yet.
- Use the branch's tested flash persistence driver and set `RP_FLASH_SIZE` to the chosen RP2350A board's actual flash size.
- Add `VIA_ENABLE = yes`, per-key RGB (likely WS2812-compatible chain), and separate underglow output after power budgeting. Confirm the chosen LED protocol and GPIO/timing support on this branch.
- Verify all intended keymap layouts, Raw HID, VIA remapping, flash persistence after power cycle, RGB operation, and bootloader recovery on the assembled PCB.

Do not infer wireless support from the commercial 6095 tri-mode reference PCB. Bluetooth/radio/battery remain open product decisions. Build success, USB enumeration, and the upstream author's Pico 2 report are not a Maru60 prototype validation.
