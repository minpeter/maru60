#!/usr/bin/env python3
"""Check current physical map regeneration without modifying checked-in files."""
from pathlib import Path
import json,subprocess,sys,tempfile
pcb=Path(__file__).resolve().parents[2];overlay=pcb/'firmware/qmk/keyboards/maru60/rp2350'
j=json.loads((pcb/'engineering/key-rgb-index-map.json').read_text());assert len(j['pixels'])==64
assert len({x['led_ref'] for x in j['pixels']})==64
with tempfile.TemporaryDirectory() as d:
 subprocess.run([sys.executable,str(pcb/'firmware/tools/generate_led_config.py'),'--map',str(pcb/'engineering/key-rgb-index-map.json'),'--components',str(pcb/'engineering/lighting-components.json'),'--output',d],check=True)
 for name in ['led_config.c','maru_led_counts.h','maru_layout.c','maru_layout_policy.h']:
  assert (Path(d)/name).read_bytes()==(overlay/name).read_bytes(),name+' stale'
# Exact intended overrides are compile-checked in the dedicated transports.
s=(overlay/'maru_key_transport.c').read_text();assert '#define WS2812_T1H 900' in s and '#define WS2812_T1L 300' in s and '#define WS2812_TRST_US 250' in s
assert 'define MARU60_LED_POWER_QUALIFIED 0' in (overlay/'config.h').read_text()
assert 'pioSmSetPCX(state_machine, program_offset)' in (overlay/'maru_ws2812_transport.inc').read_text()
cfg=(overlay/'config.h').read_text()
assert '#define WS2812_T1H 900' in cfg and '#define WS2812_T1L 300' in cfg and '#define WS2812_TRST_US 250' in cfg
comps=json.loads((pcb/'engineering/lighting-components.json').read_text())
assert sum(c['ref'].startswith('LED') for c in comps)==76
assert all(c['value']=='SK6805-EC15-001' for c in comps if c['ref'].startswith('LED'))
print('PASS64unique physical pixels, reproducible option/reactive maps and counts, EC15timing overrides, gateOFF, PIOresumePCreset')
