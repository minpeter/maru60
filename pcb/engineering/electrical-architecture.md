# RP2350A electrical architecture - draft decisions

This fixes an architecture to investigate, not a circuit ready for layout. Actual schematic, BOM and PCB still require KiCad authoring, review, ERC/DRC and prototype measurement.

## MCU and boot
- Bare RP2350A (QFN-60, flash-less RP2350), not a prebuilt Pico module.
- External QSPI NOR flash is required. Capacity remains open until the selected part agrees with QMK's RP_FLASH_SIZE build setting.
- Follow Raspberry Pi's RP2350A Minimal reference design for the switched 1.1 V core supply, 3.3 V rail, decoupling, QSPI routing, RUN/BOOTSEL and SWD. RP2350's regulator is a 200 mA switching regulator with a layout-critical VREG_LX/inductor/capacitor/PGND loop; do not reuse RP2040 circuitry or improvise this block.
- Keep USB BOOT, RUN/reset access and SWD in the first prototype.
- Source matrix and lighting GPIO choices from the official RP2350A QFN-60 pinout. Current QMK GP0-GP19 matrix seed is not an approved pin map.

## USB-C device port
Proposed block order: USB-C receptacle -> VBUS protection/power entry and USB D+/D- ESD protection -> RP2350 USB PHY; include USB-device CC pulldowns and BOOTSEL/RUN circuitry from the official reference design. Select the receptacle only after matching footprint, shell stakes, insertion depth and the Rule60 case notch. The housing reference's USB center target is about GH60 X=18 mm from photo metrology, not a chosen connector or verified fit.
USB data routing, ESD part, CC resistors, VBUS current protection and connector body/through-hole fit remain open. No connector is selected and no USB-C compliance claim is made.

## Switch matrix and hot-swap
Use one switch contact and diode per key in a row/column matrix. Contact/diode polarity and row/column grouping must agree in schematic, QMK keyboard.json, VIA matrix map and board nets. Matrix source is incomplete.
Licensed ai03 MX_V2 1U and 7U hot-swap footprints are vendored under third_party/MX_V2, from upstream commit 0b379eebbeb66c7fd6e82e400b47958ad695614e under MIT. The geometry checker extracts actual SMD copper pads and 7U NPTH features from those files and screens all seven WKL/HHKB bottom-row union sites. It only checks copper-pad AABB overlap. Upstream warns new designs should flip the hotswap footprint so socket/pads face the bottom. The checker does not apply the transform and cannot replace KiCad DRC or actual switch/plate fit.

## Stabilizers and plates
The current Rule60 plate reference uses plate-mount stabilizer cutouts. The ai03 7U footprint provides four NPTH features around the spacebar; geometry screening found positive distance from candidate switch copper pads. This does not prove fit with any stabilizer maker or the existing plate. PCB-mount stabilizers need a verified plate variant; plate-mount stabilizers need the current plate CAD plus chosen part checked. No generic combined cutout is assumed.

## Lighting and power
Per-key RGB and underglow remain required and should be independently controllable zones. Exact LEDs, counts, chain topology, data pins, decoupling, power injection and current limit are not selected. Choose 5 V/3.3 V signaling after a specific LED datasheet is chosen; size VBUS and power distribution against that datasheet and host current policy. No full-white current estimate can be responsibly stated now. LED power and thermal validation remain open.

## KiCad availability and install gate
No kicad-cli.exe or pcbnew.exe was found under the checked KiCad 8/9 install paths, and no KiCad was installed. The official Windows page currently offers KiCad stable 10.0.8 x64 installer: https://www.kicad.org/download/windows/ . Installation needs an environment that permits software installation; this workspace permits writes only under the task directory and no installation approval was granted. winget was attempted but its Windows alias could not execute. No hand-written unvalidated KiCad file is being presented as a finished schematic or routed board.
QMK's official Windows guide uses QMK MSYS and qmk setup: https://docs.qmk.fm/newbs_getting_started . Windows has no local QMK MSYS. A separate Debian/GCC cloud toolchain compiled the pinned RP2350 sample and Maru60 overlay after adding USB metadata; this is separate from KiCad and all physical hardware tests.

## Primary references
- Raspberry Pi, Hardware design with RP2350: https://pip.raspberrypi.com/documents/RP-008280-DS-hardware-design-with-rp2350.pdf (RP2350A package/external flash, power and QSPI/BOOTSEL).
- ai03 MX_V2: https://github.com/ai03-2725/MX_V2 and orientation notice: https://github.com/ai03-2725/MX_V2#breaking-changes-notice-commit-6e5adad-2024-08-15; MIT license included.
- Mechanical reference: Maru60 PR #1 head 1d89453825131438929ad887e2b0264f8f620cd2. Rule60 frame and USB-notched top-case geometry from its spec files.
