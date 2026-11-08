#!/usr/bin/env python3
"""Regenerate option-aware EC15 firmware maps. Reject unsupported option types."""
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--map',required=True);ap.add_argument('--components',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
out=Path(a.output);pixels=json.loads(Path(a.map).read_text())['pixels'];pixels.sort(key=lambda p:p['index']);assert [p['index'] for p in pixels]==list(range(len(pixels)))
assert len(pixels)==64,'Normal Backspace addition needs explicit option-policy extension'
allowed={'always','caps_normal','caps_stepped','rshift_normal','rshift_split'}
assert all(p['active_when'] in allowed for p in pixels)
idx={p['led_ref']:p['index'] for p in pixels};components=json.loads(Path(a.components).read_text());ug=sorted([p for p in components if p['ref'].startswith('LED') and 63<=int(p['ref'][3:])<=74],key=lambda p:int(p['ref'][3:]));assert len(ug)==12
matrix=[['NO_LED']*15 for _ in range(5)]
for p in pixels:
 if p['active_when'] in {'caps_stepped','rshift_normal'}:continue
 r,c=p['matrix'];assert matrix[r][c]=='NO_LED';matrix[r][c]=str(p['index'])
s='// SPDX-License-Identifier: GPL-2.0-or-later\n// Generated option-aware physical index map; do not hand edit.\n#include "quantum.h"\nled_config_t g_led_config = {\n {\n'+''.join('  {'+', '.join(r)+'},\n' for r in matrix)+' },\n {\n'+''.join('  {%d,%d},\n'%(round(p['x_mm']/285*224),round(p['y_mm']/94.6*64)) for p in pixels+ug)+' },\n {'+', '.join(['4']*len(pixels)+['2']*len(ug))+'}\n};\n';(out/'led_config.c').write_text(s)
(out/'maru_led_counts.h').write_text('// SPDX-License-Identifier: GPL-2.0-or-later\n#pragma once\n#define MARU_KEY_LED_COUNT 64\n#define MARU_UG_LED_COUNT 12\n')
# These refs are the approved composite sites; fail if the topology changes.
assert all(k in idx for k in ['LED30','LED75','LED54','LED55','LED76','LED56','LED57','LED61','LED62'])
s='''// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
#define MARU_LAYOUT_CAPS_STEPPED 1UL
#define MARU_LAYOUT_RSHIFT_NORMAL 2UL
#ifndef MARU60_LAYOUT_HHKB
#define MARU60_LAYOUT_HHKB 0
#endif
static inline uint32_t maru_effective_options(uint32_t value) { return MARU60_LAYOUT_HHKB ? value & ~MARU_LAYOUT_RSHIFT_NORMAL : value; }
static inline bool maru_pixel_active(unsigned i,uint32_t options) {
 options=maru_effective_options(options);
'''
for ref,expr in [('LED30','!(options & MARU_LAYOUT_CAPS_STEPPED)'),('LED75','options & MARU_LAYOUT_CAPS_STEPPED'),('LED54','!(options & MARU_LAYOUT_RSHIFT_NORMAL)'),('LED55','!(options & MARU_LAYOUT_RSHIFT_NORMAL)'),('LED76','options & MARU_LAYOUT_RSHIFT_NORMAL'),('LED56','!MARU60_LAYOUT_HHKB'),('LED62','!MARU60_LAYOUT_HHKB'),('LED57','MARU60_LAYOUT_HHKB'),('LED61','MARU60_LAYOUT_HHKB')]:s+=f' if(i=={idx[ref]}) return {expr};\n'
s+=' return true;\n}\n';(out/'maru_layout_policy.h').write_text(s)
s='''// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "via.h"
#include "maru_layout_policy.h"
uint32_t maru_layout_options;
void via_set_layout_options_kb(uint32_t value) {
 value=maru_effective_options(value);
 maru_layout_options=value;
'''
for r,c,expr in [(4,0,f'MARU60_LAYOUT_HHKB?NO_LED:{idx["LED56"]}'),(4,1,f'MARU60_LAYOUT_HHKB?{idx["LED57"]}:NO_LED'),(4,11,f'MARU60_LAYOUT_HHKB?{idx["LED61"]}:NO_LED'),(4,12,f'MARU60_LAYOUT_HHKB?NO_LED:{idx["LED62"]}'),(2,0,f'(value & MARU_LAYOUT_CAPS_STEPPED)?{idx["LED75"]}:{idx["LED30"]}'),(3,11,f'(value & MARU_LAYOUT_RSHIFT_NORMAL)?{idx["LED76"]}:{idx["LED54"]}'),(3,12,f'(value & MARU_LAYOUT_RSHIFT_NORMAL)?NO_LED:{idx["LED55"]}')]:s+=f' g_led_config.matrix_co[{r}][{c}]={expr};\n'
s+='}\n';(out/'maru_layout.c').write_text(s)
print('Generated64key+12UG maps, explicit Caps/RShift policy and count header')
