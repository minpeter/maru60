#!/usr/bin/env python3
"""Prepare a conservative incremental outer-layer routing job.

The enlarged router keepouts deliberately encroach on the reverse LED land
tips: the autorouter may report those fixed-pad conflicts. They protect new
tracks/vias at 0.5 mm from milling; native KiCad DRC remains the final judge.
"""
import argparse
import json
import re
from pathlib import Path
from shapely.geometry import Polygon


def spans(text, tag):
    for m in re.finditer(r'\('+tag+r'\s', text):
        depth, quoted, escaped = 0, False, False
        for j in range(m.start(), len(text)):
            c = text[j]
            if quoted:
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == '"':
                    quoted = False
                continue
            if c == '"':
                quoted = True
            else:
                depth += (c == "(")-(c == ")")
                if depth == 0:
                    yield m.start(), j+1
                    break


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("input", type=Path)
ap.add_argument("output", type=Path)
a = ap.parse_args()
s = a.input.read_text()
window_count = 0
def grow_window(m):
    global window_count
    nums = list(map(float, m[1].split()))
    g = Polygon([(nums[i]/1000, -nums[i+1]/1000) for i in range(0, len(nums), 2)])
    assert g.is_valid and 13.8 < g.area < 14.5, (g.area, g.bounds)
    g = g.buffer(.36, 12).simplify(.002)
    coords = " ".join(f"{x*1000:.3f} {-y*1000:.3f}" for x, y in g.exterior.coords)
    window_count += 1
    return '(keepout "" (polygon signal 0 '+coords+'))'
s = re.sub(r'\(keepout "" \(polygon signal 0\s+([^()]*)\)\)', grow_window, s)
assert window_count == 66, window_count
for x, z in reversed(list(spans(s, "plane"))):
    if re.search(r'\(polygon [FB]\.Cu\b', s[x:z]) and not s[x:z].startswith(("(plane +1V1", "(plane VREG_LX")):
        s = s[:x]+s[z:]
x, z = next(spans(s, "class"))
cl = s[x:z].replace('(width 200)', '(width 150)').replace('(clearance 150)', '(clearance 160)')
cl = cl.replace('(use_via "Via[0-3]_600:300_um")', '(use_via "Via[0-3]_500:250_um")')
power = {"GND": 250, "+1V1": 400, "+3V3": 400, "+4V_LED": 400,
         "+4V_REG": 400, "VBUS": 500, "VBUS_FUSED": 500, "VBUS_PROTECTED_RAW": 600}
for net in power:
    cl = re.sub(r'(?<!\S)'+re.escape(net)+r'(?!\S)', '', cl)
extra = "".join(f'\n(class POWER_{i} {net} (circuit (use_via "Via[0-3]_500:250_um")) (rule (width {width}) (clearance 160)))'
                for i, (net, width) in enumerate(power.items()))
s = s[:x]+cl+extra+s[z:]
s = re.sub(r'\(circuit\s*', '(circuit (use_layer F.Cu B.Cu) ', s)
a.output.write_text(s)
print("Prepared", window_count, "protected windows; fixed copper retained; new routing confined to outer layers")
