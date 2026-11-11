#!/usr/bin/env python3
"""Schematic side of the U2 swap: MAX38902AATA+T -> AP2112K-3.3TRG1, C142 and R163 removed.

usage: edit_schematic_ldo_swap.py PCB_DIR

The supply sheet is label based (no wires): every pin end carries a global
label.  The U2 symbol keeps its UUID and position; it gets five pins, and the
labels of the pins that no longer exist are deleted with C142 and R163.
"""
import re
import sys

NEW_LIB = '''(symbol "Study:U2" (pin_names (offset .5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 9.620000000000001 0) (effects (font (size 1.0 1.0)))) (property "Value" "AP2112K-3.3TRG1" (at 0 -9.620000000000001 0) (effects (font (size 1.0 1.0)))) (symbol "U2_0_1" (rectangle (start -10.16 7.62) (end 10.16 -7.62) (stroke (width .254) (type default)) (fill (type background)))) (symbol "U2_1_1" (pin power_in line (at -15.24 5.08 0) (length 5.08) (name "VIN" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0))))) (pin power_in line (at -15.24 2.54 0) (length 5.08) (name "GND" (effects (font (size 1.0 1.0)))) (number "2" (effects (font (size 1.0 1.0))))) (pin input line (at -15.24 0.0 0) (length 5.08) (name "EN" (effects (font (size 1.0 1.0)))) (number "3" (effects (font (size 1.0 1.0))))) (pin no_connect line (at -15.24 -5.08 0) (length 5.08) (name "NC" (effects (font (size 1.0 1.0)))) (number "4" (effects (font (size 1.0 1.0))))) (pin power_out line (at 15.24 5.08 180) (length 5.08) (name "VOUT" (effects (font (size 1.0 1.0)))) (number "5" (effects (font (size 1.0 1.0)))))))'''


def main():
    path = f"{sys.argv[1]}/protection-supply-context.kicad_sch"
    lines = open(path).read().split("\n")
    out = []
    removed = []
    for line in lines:
        # labels of removed pins (SELA, BYP, OUTS, EP) and of C142 / R163
        if line.startswith("(global_label") and any(f"(at {at} " in line for at in (
                "137.16 63.5", "167.64000000000001 58.42", "167.64000000000001 60.96", "167.64000000000001 63.5",
                "238.76 152.4", "269.24 152.4", "137.16 208.28", "167.64000000000001 208.28")):
            removed.append(line[:60])
            continue
        if line.startswith("(no_connect (at 137.16 66.04)"):
            removed.append(line[:40])          # pin 4 is now a no_connect type pin
            continue
        if line.startswith('(symbol (lib_id "Study:C142")') or line.startswith('(symbol (lib_id "Study:R163")'):
            removed.append(line[:40])
            continue
        if line.startswith('(symbol (lib_id "Study:U2")'):
            for a, b in (('(property "Value" "MAX38902AATA+T"', '(property "Value" "AP2112K-3.3TRG1"'),
                         ('"MaruStudy:MAX_T822-3C_90-0065_2x2_P0.5_EP0.8x1.38"', '"Maru60:SOT-23-5_TightCourtyard"'),
                         ('"https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf"', '"https://www.diodes.com/assets/Datasheets/AP2112.pdf"'),
                         ('(property "Status" "ISOLATED BOM STUDY: qualification gates in IMPLEMENTATION.md"', '(property "Status" "Order candidate 2026-11-11: replaces MAX38902AATA+T (no stock)"'),
                         ('(property "Manufacturer" "Analog Devices"', '(property "Manufacturer" "Diodes Incorporated"'),
                         ('(property "MPN" "MAX38902AATA+T"', '(property "MPN" "AP2112K-3.3TRG1"')):
                assert a in line, a
                line = line.replace(a, b, 1)
        if line.startswith("(lib_symbols"):
            i = line.index('(symbol "Study:U2"')
            depth = 0
            for j in range(i, len(line)):
                if line[j] == "(":
                    depth += 1
                elif line[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
            line = line[:i] + NEW_LIB + line[j + 1:]
        if line.startswith('(text "ISOLATED U2 CORRECTION ONLY'):
            line = re.sub(r'\(text "[^"]*"', '(text "U2 AP2112K-3.3TRG1: 3.3 V LDO from the 4.0 V buck rail. EN tied to VIN; pin 4 is NC.\\\\nReplaces MAX38902AATA+T (order candidate 2026-11-11); C142 (BYP) and R163 (minimum load) removed with it."', line, count=1)
        if line.startswith('(text "ISOLATED BOM/FOOTPRINT STUDY'):
            removed.append(line[:40])
            continue
        if line.startswith("(title_block"):
            line = '(title_block (title "3.3 V LDO") (rev "order candidate"))'
        out.append(line)
    assert len(removed) == 12, removed
    open(path, "w").write("\n".join(out))
    print(f"removed {len(removed)} items; U2 is now AP2112K-3.3TRG1")


if __name__ == "__main__":
    main()
