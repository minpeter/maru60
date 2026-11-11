#!/usr/bin/env python3
"""Add two-pin parts to the Core sheet and rename LED data labels on the Lighting sheet.

usage: edit_schematic_added_parts.py PCB_DIR SPEC.json

SPEC.json:
  {"parts": [{"ref": "R170", "kind": "R" | "C", "value": "100 1%", "footprint": "Maru60:R_0402_1005Metric",
              "net1": "UG_LED_11_SRC", "net2": "UG_LED_11", "note": "..."}],
   "relabel": [{"net": "UG_LED_11", "to": "UG_LED_11_SRC"}]}

The layout tools (plan_series_resistor.py and the hand-written operation lists)
place the footprint and give it the symbol UUID uuid5(URL, "maru60/order-candidate/REF");
this tool writes the matching symbol.  Each part is a Device:R or Device:C with a
global label on each pin, set in the empty block of the Core sheet (x 340-545 mm,
y 80-145 mm), next free slot first.  "relabel" renames the label on the DOUT pin of
the driving LED: every chain net has exactly two global labels on the Lighting
sheet, the one at the DOUT pin at angle 0 and the one at the next DIN pin at 180.
Running the tool again changes nothing.
"""
import json
import re
import sys
import uuid
from pathlib import Path

X0, Y0, DX, DY, COLS = 340.36, 81.28, 50.8, 20.32, 5
PATHS = ('(instances (project "maru60-core" (path "/53792dd2-6a48-520e-a7fa-0fba59d43747" (reference "{ref}") (unit 1))) '
         '(project "maru60" (path "/5cea1f07-cba7-55d1-9c88-823833390084/0940d797-79a6-569a-9535-d8f19961ba0b" (reference "{ref}") (unit 1))))')


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "maru60/order-candidate/" + "/".join(parts)))


def main():
    pcb, spec = Path(sys.argv[1]), json.load(open(sys.argv[2]))
    core = pcb / "maru60-core.kicad_sch"
    s = core.read_text()
    used = {(round(float(x), 2), round(float(y), 2)) for x, y in re.findall(r'\(symbol \(lib_id "Device:[RC]"\) \(at ([\d.]+) ([\d.]+) 0\)', s)}
    slots = [(round(X0 + DX * (i % COLS), 2), round(Y0 + DY * (i // COLS), 2)) for i in range(40)]
    add = []
    for p in spec.get("parts", []):
        if f'(property "Reference" "{p["ref"]}"' in s:
            continue
        x, y = next(q for q in slots if q not in used)
        used.add((x, y))
        ref = p["ref"]
        add.append(f'(symbol (lib_id "Device:{p["kind"]}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(ref)}") '
                   f'(property "Reference" "{ref}" (at {round(x + 5, 2)} {round(y - 1.5, 2)} 0) (effects (font (size 1.27 1.27)))) '
                   f'(property "Value" "{p["value"]}" (at {round(x + 5, 2)} {round(y + 1.5, 2)} 0) (effects (font (size 1 1)))) '
                   f'(property "Footprint" "{p["footprint"]}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) ' + PATHS.format(ref=ref) + ')')
        for net, dy, tag in ((p["net1"], -3.81, "pin1"), (p["net2"], 3.81, "pin2")):
            add.append(f'(global_label "{net}" (shape input) (at {x} {round(y + dy, 2)} 0) (effects (font (size 0.9 0.9)) (justify left)) (uuid "{uid(ref, tag)}"))')
        add.append(f'(text "{ref}: {p["note"]}" (at {round(x - 2, 2)} {round(y - 8.3, 2)} 0) (effects (font (size 1 1)) (justify left)) (uuid "{uid(ref, "note")}"))')
    if add:
        marker = "\n(sheet_instances"
        if marker not in s:
            marker = "\n(embedded_fonts"
        if marker in s:
            i = s.rindex(marker)
            s = s[:i] + "\n" + "\n".join(add) + s[i:]
        else:                       # last closing parenthesis of the file
            i = s.rstrip().rindex(")")
            s = s[:i] + "\n" + "\n".join(add) + "\n" + s[i:]
        core.write_text(s)
    light = pcb / "maru60-lighting.kicad_sch"
    t = light.read_text()
    n = 0
    for r in spec.get("relabel", []):
        if f'(global_label "{r["to"]}"' in t:
            continue
        hits = re.findall(r'\(global_label "%s" \(shape bidirectional\) \(at [\d.]+ [\d.]+ (\d+)\)' % re.escape(r["net"]), t)
        if sorted(hits) != ["0", "180"]:
            raise SystemExit(f'{r["net"]}: expected one label at 0 and one at 180 on the Lighting sheet, found {hits}')
        t, k = re.subn(r'\(global_label "%s" (\(shape bidirectional\) \(at [\d.]+ [\d.]+ 0\))' % re.escape(r["net"]), r'(global_label "%s" \1' % r["to"], t)
        assert k == 1
        n += 1
    light.write_text(t)
    print(f"{len(add) // 4} parts added to the Core sheet, {n} labels renamed on the Lighting sheet")


if __name__ == "__main__":
    main()
