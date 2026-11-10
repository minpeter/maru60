# Full ARM QMK build evidence

The captured Dockerfile requires the existing `maru60-kicad:9.0.2` Debian trixie base (resolved base digest in docker-build.log: sha256:7a42dc28b517b2049b2c5863bb8ffad0e45a2d01404aa4fc2ff12cb1b82c4dd3). No host packages were installed. Python/system package versions are captured; repositories are not a frozen package mirror. The exact exported build image identity is docker-image-id.txt. Source/patch bytes are also archived in overlay-and-patches.tar.gz.

Commands from repository root, using a new empty build directory if repeating:

```bash
git init build/pcb-qmk-20261109/qmk_firmware
git -C build/pcb-qmk-20261109/qmk_firmware remote add origin https://github.com/emolitor/qmk_firmware.git
git -C build/pcb-qmk-20261109/qmk_firmware fetch --depth 1 origin 431ed9ade0684e98a66eabc949563c3be8f446e8
git -C build/pcb-qmk-20261109/qmk_firmware checkout --detach FETCH_HEAD
git -C build/pcb-qmk-20261109/qmk_firmware submodule update --init --recursive --depth 1 --jobs 8
python3 pcb/firmware/qmk/apply_via_schema_patch.py build/pcb-qmk-20261109/qmk_firmware
python3 pcb/firmware/qmk/apply_report_sync_patch.py build/pcb-qmk-20261109/qmk_firmware
python3 pcb/firmware/qmk/apply_via_schema_patch.py build/pcb-qmk-20261109/qmk_firmware --apply
python3 pcb/firmware/qmk/apply_report_sync_patch.py build/pcb-qmk-20261109/qmk_firmware --apply
test ! -e build/pcb-qmk-20261109/qmk_firmware/keyboards/maru60
cp -r pcb/firmware/qmk/keyboards/maru60 build/pcb-qmk-20261109/qmk_firmware/keyboards/
docker build -t maru60-qmk-arm:20261109 -f build/pcb-qmk-20261109/Dockerfile build/pcb-qmk-20261109
timeout 600 docker run --rm --name maru60-qmk-build-20261109 --user "$(id -u):$(id -g)" -e HOME=/tmp -e QMK_HOME=/qmk -v "$PWD/build/pcb-qmk-20261109/qmk_firmware:/qmk" -v "$PWD/.omo/evidence/pcb-routing-20261109/qmk-build:/evidence" -v "$PWD/build/pcb-qmk-20261109/build-layouts.sh:/build-layouts.sh:ro" maru60-qmk-arm:20261109 bash /build-layouts.sh
```

The recorded initial Docker image build used timeout600 and reached that bound during unpack, after exporting the tagged image. The subsequent docker run succeeded using that image; full firmware run exit0. Allow more than10minutes for initial image preparation on a repeat run.

`build-layouts.sh` invokes the exact two sequential make commands and copies/hashes linked artifacts. `DUMP_C_MACROS` uses the upstream compiler recipe, including actual headers/flags. QMK decorates macro dump output with warning-style formatting because stdout is nonempty; this is not itself a compiler warning. `*-macro-check.txt` extracts the relevant output, and complete dumps remain in full logs. Per-layout `*-flags/` contains QMK's actual C/assembler/link flags and compiler identity.

Acceptance assertions executed: both exit files equal0; each full log contains exactly3 `#define MARU60_LED_POWER_QUALIFIED 0` records; neither log defines qualification1, private-test IDs or suspend experiment; all four ELF/UF2 files are nonempty; sha256sum -c succeeds; recursive postbuild diff shows current overlay unchanged. Captured outputs: acceptance-check.txt, artifact-hash-check.txt, overlay-postbuild-diff.txt. Both layouts retain prototype FEED:6060. No flashing, physical USB/IRQ/task/DMA/PIO/power validation or hardware qualification was performed.
