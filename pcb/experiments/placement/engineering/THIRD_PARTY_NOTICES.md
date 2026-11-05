MX_V2 footprint files in this directory were copied from https://github.com/ai03-2725/MX_V2 at commit 0b379eebbeb66c7fd6e82e400b47958ad695614e.
They are licensed under MIT; see LICENSE (Copyright (c) 2017 ai03). This license applies to these copied library files only. Maru60 has not selected an overall PCB hardware license.
Upstream's 2024-08-15 breaking-change notice says new designs should flip hotswap footprints so the socket/pad side faces the bottom. The screening script uses source-local coordinates and does not apply that transform.

Additional native-circuit iteration:
- ai03 same pinned commit: 2U, 2.25U and 2.75U footprints added for stabilizer/candidate studies; no other layout requirements added. Actual board footprints are B.Cu-flipped.
- Raspberry Pi RP2350A Minimal R4/S1 official archive: extracted U1/L1 footprint geometry and pin facts under included MIT license. `third_party/RP2350A_Minimal/PROVENANCE.md` records URL/hash and adaptation boundary.
- Installed KiCad 9 standard libraries: https://www.kicad.org/libraries/license/ (CC-BY-SA 4.0 with design-output exception). Embedded symbols and board footprint instances originate in these libraries unless noted. No unilateral overall Maru60 hardware license selected.
- `candidates.pretty` contains explicitly marked adapted ai03 geometry studies. They inherit the upstream MIT notice, with Maru60 modifications described in study reports; not approved manufacturing footprints.
