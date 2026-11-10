#!/usr/bin/env bash
set -euo pipefail
cd /qmk
arm-none-eabi-gcc --version > /evidence/toolchain.txt
qmk --version >> /evidence/toolchain.txt
python3 --version >> /evidence/toolchain.txt
pip freeze > /evidence/python-dependencies.txt
dpkg-query -W > /evidence/system-packages.txt
for keymap in via via_hhkb; do
  set +e
  make "maru60/rp2350:${keymap}" -j4 VERBOSE=true DUMP_C_MACROS="maru_key_transport.c maru_ug_transport.c maru_rgb.c" > "/evidence/${keymap}.log" 2>&1
  result=$?
  set -e
  printf '%s\n' "$result" > "/evidence/${keymap}.exit"
  if [ "$result" -ne 0 ]; then tail -40 "/evidence/${keymap}.log"; exit "$result"; fi
  cp ".build/maru60_rp2350_${keymap}.elf" "/evidence/maru60_rp2350_${keymap}.elf"
  cp "maru60_rp2350_${keymap}.uf2" "/evidence/maru60_rp2350_${keymap}.uf2"
  sha256sum "/evidence/maru60_rp2350_${keymap}.elf" "/evidence/maru60_rp2350_${keymap}.uf2" >> /evidence/artifacts.sha256
  arm-none-eabi-size "/evidence/maru60_rp2350_${keymap}.elf" >> /evidence/artifact-sizes.txt
done
