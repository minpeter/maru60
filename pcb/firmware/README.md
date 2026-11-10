# RP2350A QMK / VIA overlay

This is a keyboard overlay, not a standalone QMK checkout or hardware-qualified firmware. Its 22 files under `qmk/keyboards/maru60/rp2350` match the new [LED startup recovery candidate](../experiments/led-startup-recovery/candidate/README.md). That candidate preserves 19 former working-source files exactly and newly implements three missing files; it is not an exact historical restoration.

The upstream pin is `emolitor/qmk_firmware`, branch `em-rp2350`, commit `431ed9ade0684e98a66eabc949563c3be8f446e8`. See `qmk-upstream.json` and the two hash-guarded patches under `qmk/patches/` for the VIA EEPROM schema and report synchronization dependencies.

## Current source configuration

| Function | Configuration |
| --- | --- |
| MCU / bootloader | RP2350 / `rp2350` |
| Matrix | 5×15, `COL2ROW`; rows GP0, GP1, GP2, **GP29 (ROW3)**, GP4; columns GP5–GP9, **GP28 (COL5)**, GP11–GP19 |
| Flash | `RP_FLASH_SIZE = 4U * 1024U * 1024U` (4 MiB) |
| Layouts | WKL and HHKB 7U split layouts; keymaps `via` and `via_hhkb`; WK is not a v1 option |
| Lighting | Two independent chains: 64 key LEDs on GP20 and 12 underglow LEDs on GP21; custom RGB Matrix driver; RGBLIGHT disabled |
| LED power control | GP22 enable, GP23 active-low fault; `MARU60_LED_POWER_QUALIFIED` defaults to **0** |

The LED driver includes OFF/SETTLING/ACTIVE startup handling, black-first frames and cancellation checks. Qualification zero keeps LED power disabled. There is no default qualified settling interval or report. The enabled host fixtures use a synthetic interval; passing those fixtures does not authorize enabling lighting on a board. Fault polling is not atomic with an asynchronous fault or in-flight DMA and does not guarantee capture of short pulses or a maximum cancellation latency.

WKL/HHKB VIA definitions are present under `via/`; portable checks regenerate and compare them byte for byte. These definitions and ideal matrix checks do not establish official VIA app interoperability or physical remapping/persistence.

## Verification and remaining acceptance

From the repository root, run:

```sh
uv run tools/check_pcb_portable.py --output /tmp/maru60-portable-new
```

Use a new output directory for every run. Python 3.11+ and a C11 compiler (`cc`, or `CC`) are required; the wrapper has no third-party Python dependencies. It verifies active/candidate identity, runs the existing portable C fixtures, checks GPIO/matrix bindings against the selected prototype's stored netlist, and replays recorded power arithmetic in a scratch copy. See [tests](tests/README.md) and [PCB validation](../../docs/pcb-validation.md) for scope and artifacts.

Fresh full builds of this recovery source passed on 2026-11-09 for **both** WKL `via` and HHKB `via_hhkb`, against the pinned QMK checkout, exact recursive submodules and both patches. All six actual LED translation-unit macro dumps confirm qualification **0**. The [build packet](../experiments/resume-20261109-silk-height/qa/qmk-build/RESULT.json) retains complete compiler/link logs, ELF/UF2 files and hashes, source identities and reproduction instructions. This closes the default-OFF full-build gap; it does not qualify enabled lighting or hardware. The archived recovery candidate's earlier unbuilt status describes its original capture, before this fresh replay.

Follow the [build acceptance instructions](../experiments/led-startup-recovery/candidate/BUILDING.md) when repeating; retain qualification OFF. Host fixtures and full ARM builds supply different evidence: host transport lifecycle behavior is mocked, while the full builds compile/link the actual QMK/ChibiOS configuration without exercising physical GPIO, DMA, PIO or power behavior.

Physical USB enumeration/NKRO, matrix/diode behavior, bootloader and flash operation, VIA persistence, DMA/PIO waveforms, rail readiness/current/inrush, fault timing and suspend behavior remain unqualified. Native CAD checks and arithmetic checks cannot close those gaps. Default prototype USB IDs and optional shared private-test IDs are not production allocations.
