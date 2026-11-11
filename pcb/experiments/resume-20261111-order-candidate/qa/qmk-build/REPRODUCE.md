# Firmware build with the longer matrix read delay

Both layouts built from the active overlay (`pcb/firmware/qmk/keyboards/maru60`)
against the pinned QMK tree, on 2026-11-11. Nothing was flashed; no hardware
exists. The image, checkout and patch steps are those of the
[2026-11-09 packet](../../../resume-20261109-silk-height/qa/qmk-build/REPRODUCE.md);
the QMK commit and all nine submodule commits are identical to it.

```sh
# checkout, submodules and the two patches as in the 2026-11-09 packet, then:
test ! -e build/pcb-qmk-20261109/qmk_firmware/keyboards/maru60
cp -r pcb/firmware/qmk/keyboards/maru60 build/pcb-qmk-20261109/qmk_firmware/keyboards/
docker build -t maru60-qmk-arm:20261111 -f Dockerfile build/pcb-qmk-20261109
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e QMK_HOME=/qmk \
  -v "$PWD/build/pcb-qmk-20261109/qmk_firmware:/qmk" -v "$PWD/build/qmk-evidence:/evidence" \
  -v "$PWD/build-layouts.sh:/build-layouts.sh:ro" maru60-qmk-arm:20261111 bash /build-layouts.sh
```

`build-layouts.sh` is the 2026-11-09 script with `matrix.c` added to the macro
dump and a disassembly of both ELF files at the end. The image was rebuilt from
the same Dockerfile; Debian and PyPI are not frozen mirrors, the versions that
were installed are in `toolchain.txt`, `system-packages.txt` and
`python-dependencies.txt` (same compiler and QMK CLI as on 2026-11-09).

What was checked (`RESULT.json`):

- both `make` runs exit 0; ELF and UF2 hashes verify;
- `GPIO_INPUT_PIN_DELAY 120` in every dumped translation unit, `matrix.c`
  included, and `MARU60_LED_POWER_QUALIFIED 0` in all of them;
- in both linked ELF files `matrix_output_select_delay` holds exactly 120 `nop`
  instructions and is called once, from the matrix scan. At the 150 MHz system
  clock that is 0.8 µs between driving a row and reading the columns.

The full disassembly is not stored; `arm-none-eabi-objdump -d` on the ELF files
reproduces it.
