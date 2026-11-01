# RP2350A QMK / VIA scaffold

Upstream baseline: `emolitor/qmk_firmware`, branch `em-rp2350`, commit `431ed9ade0684e98a66eabc949563c3be8f446e8`. `qmk-upstream.json` records the pin and upstream sample paths.

The upstream RP2350 sample metadata explicitly sets `processor: RP2350`, `bootloader: rp2350`, and GPIO matrix pins. The fork author reports Pico 2 (RP2350A) USB enumeration, WS2812, and flash-backed EEPROM checks; this is their report, not Maru60 bench evidence. The branch contains Raw HID/VIA dynamic keymap support and the RP2350 flash driver.

This subtree is an overlay scaffold, not a standalone QMK checkout. `keyboard.json` proposes a 5×15 matrix on GP0–GP19 and `rules.mk` enables VIA/dynamic keymaps. Pin assignments are candidates until schematic and routing review. The keymap matrix is a WKL 7U seed only. WK is not a v1 option. The WKL/HHKB VIA physical layout definitions and switch-to-matrix mapping remain unfinished; the PCB model retains the union sites needed by both.

## Not built or verified

- The Windows environment has no QMK MSYS. A separate Debian/GCC cloud build compiled the pinned upstream RP2350 `via_ci` baseline and then the Maru60 `via` overlay after USB metadata was added (UF2 output, exit code 0). This is a source build only; no physical RP2350A board was tested.
- VIA Configurator layout and end-to-end remapping/persistence are not validated.
- RP2350 flash size is not selected; set the fork's `RP_FLASH_SIZE` to match the chosen component.
- Per-key RGB and underglow are both required, but their LED count, chain/zone architecture, GPIOs, power budget, and build configuration await component/PCB decisions. See `pcb/engineering/electrical-architecture.md` for the current design risks and official RP2350A reference.
- No USB, matrix, lighting, or bootloader hardware test has been run.

Use the overlay under the pinned fork's `keyboards/maru60/rp2350` and finish the physical layout/net mapping before treating it as buildable firmware.
