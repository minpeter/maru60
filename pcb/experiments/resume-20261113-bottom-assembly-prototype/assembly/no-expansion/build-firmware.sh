#!/usr/bin/env bash
set -euo pipefail
cd /qmk
arm-none-eabi-gcc --version > /evidence/toolchain.txt
qmk --version >> /evidence/toolchain.txt
for keymap in via via_hhkb; do
    if make "maru60/rp2350_noexp:${keymap}" -j4 VERBOSE=true \
        DUMP_C_MACROS="maru60.c maru_key_transport.c maru_ug_transport.c maru_rgb.c matrix.c" \
        > "/evidence/${keymap}.log" 2>&1; then
        printf '0\n' > "/evidence/${keymap}.exit"
    else
        result=$?
        printf '%s\n' "$result" > "/evidence/${keymap}.exit"
        tail -45 "/evidence/${keymap}.log"
        exit "$result"
    fi
    cp ".build/maru60_rp2350_noexp_${keymap}.elf" /evidence/
    cp "maru60_rp2350_noexp_${keymap}.uf2" /evidence/
    arm-none-eabi-objdump -d ".build/maru60_rp2350_noexp_${keymap}.elf" > "/evidence/${keymap}.disasm.txt"
    printf 'Completed %s\n' "$keymap"
done
