# RP2350A QMK / VIA scaffold

Upstream baseline: `emolitor/qmk_firmware`, branch `em-rp2350`, commit `431ed9ade0684e98a66eabc949563c3be8f446e8`. `qmk-upstream.json` records the pin and upstream sample paths.

The upstream RP2350 sample metadata explicitly sets `processor: RP2350`, `bootloader: rp2350`, and GPIO matrix pins. The fork author reports Pico 2 (RP2350A) USB enumeration, WS2812, and flash-backed EEPROM checks; this is their report, not Maru60 bench evidence. The branch contains Raw HID/VIA dynamic keymap support and the RP2350 flash driver.

This subtree is an overlay scaffold, not a standalone QMK checkout. `keyboard.json` proposes a 5×15 matrix on GP0–GP19 and `rules.mk` enables VIA/dynamic keymaps. Pin assignments are candidates until schematic and routing review. The keymap matrix is a WK 7U seed only. The 7U WK/WKL/HHKB VIA physical layout definitions and switch-to-matrix mapping remain unfinished; there are no 6.25U variants in the v1 firmware scaffold.

## Not built or verified

- No local QMK checkout/toolchain was available in this execution environment, so `qmk compile` was not run.
- VIA Configurator layout and end-to-end remapping/persistence are not validated.
- RP2350 flash size is not selected; set the fork's `RP_FLASH_SIZE` to match the chosen component.
- Per-key RGB and underglow are both required, but their LED count, chain/zone architecture, GPIOs, power budget, and build configuration await component/PCB decisions.
- No USB, matrix, lighting, or bootloader hardware test has been run.

Use the overlay under the pinned fork's `keyboards/maru60/rp2350` and finish the physical layout/net mapping before treating it as buildable firmware.
