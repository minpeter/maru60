#!/usr/bin/env python3
"""Simulate every Backspace LED population combination; assumptions, not hardware limits.

Needs the field-solver lines.json and the maru60-ngspice:bookworm image.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import spice
import sim_led
from geom import Board


def passes(m):
    return (all('error' not in m[k] and m[k]['extra_threshold_crossings'] == 0 for k in ('0', '1'))
            and m.get('noise_margin_high_V', -1) >= 0
            and m.get('noise_margin_low_V', -1) >= 0
            and bool(m.get('budget_ns')) and min(m['budget_ns'].values()) >= 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('geometry', type=Path)
    ap.add_argument('board', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--lines', type=Path, default=Path('build/si/out/lines.json'))
    args = ap.parse_args()
    b = Board(args.geometry)
    table = json.loads(args.lines.read_text())
    root = args.output.resolve().parent
    spice.DECKS, spice.OUT = root/'decks', root/'out'
    spice.DECKS.mkdir(parents=True, exist_ok=True)
    cases = []
    drivers = [(f'strong-{r:g}ohm-{c:g}pF', {'r': r, 'edge': 1e-9, 'cin': c*1e-12})
               for r, c in itertools.product((10., 20.), (5., 15.))]
    drivers += [('nominal', sim_led.DRIVERS['nom']), ('weak', sim_led.DRIVERS['weak+'])]
    for net, src, dst in [('KEY_RGB_CHAIN_13','LED13','LED14'), ('KEY_RGB_CHAIN_14','LED14','LED15'),
                          ('KEY_RGB_CHAIN_15','LED15','LED29'), ('UG_LED_5','LED67','LED68')]:
        series = [f for f in b.fps.values() if f['ref'].startswith('R')
                  and any(p['num']=='2' and p['net']==net for p in f['pads'])]
        if len(series) != 1:
            raise ValueError(f'{net}: expected exactly one series resistor')
        ser = series[0]
        snet = next(p['net'] for p in ser['pads'] if p['num']=='1')
        def sites(ref, num):
            return [(p['x'], p['y']) for p in b.fps[ref]['pads'] if p['num']==num]
        for source, dest in itertools.product(sites(src,'3'), sites(dst,'1')):
            def pick(p):
                if p['ref'] == src:
                    return math.dist((p['x'], p['y']), source) < .1
                if p['ref'] == dst:
                    return math.dist((p['x'], p['y']), dest) < .1
                return True
            pre = b.route(snet, (src,'3'), (ser['ref'],'1'), pick)
            route = b.route(net, (ser['ref'],'2'), (dst,'1'), pick)
            if not pre or not route:
                raise ValueError(f'{net}: disconnected population {source}, {dest}')
            resistance = float(ser['value'].split()[0])
            for label, driver in drivers:
                name = f'backspace_{len(cases):02d}'
                measurement, _ = sim_led.sim_hop(name, route, table, driver, (pre, resistance))
                row = {'net': net, 'source_ref': src, 'destination_ref': dst,
                       'source_mm': source, 'destination_mm': dest,
                       'length_mm': route['length_mm'], 'stub_mm': route['stub_total_mm'],
                       'series': ser['ref'], 'series_ohms': resistance,
                       'driver': label, 'assumptions': driver,
                       'measurement': measurement, 'pass': bool(passes(measurement))}
                cases.append(row)
                print(net, label, row['pass'], flush=True)
    report = {'board_sha256': hashlib.sha256(args.board.read_bytes()).hexdigest(),
              'geometry_sha256': hashlib.sha256(args.geometry.read_bytes()).hexdigest(),
              'lines_sha256': hashlib.sha256(args.lines.read_bytes()).hexdigest(),
              'scope': 'Four changed LED hops, all source/destination population combinations, six assumed driver corners at 4 V; not hardware qualification or full-board SI.',
              'cases': cases, 'pass': all(c['pass'] for c in cases)}
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    if not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
