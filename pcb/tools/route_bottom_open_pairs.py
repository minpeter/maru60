#!/usr/bin/env python3
"""Plan incremental repairs; exact geometry and native DRC gate acceptance.

Inputs: dump_board_geometry.py and export_connection_components.py outputs.
The planner never edits CAD. Re-export inputs after applying an operation file.
"""
import argparse
import gc
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

import local_router as LR
import route_component_pair as R

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('geometry', type=Path)
ap.add_argument('components', type=Path)
ap.add_argument('output', type=Path)
ap.add_argument('--indices', help='Comma-separated component-pair indices')
ap.add_argument('--retries', type=int, default=12)
ap.add_argument('--margin', type=float, default=7)
ap.add_argument('--power-width', type=float, default=.4)
ap.add_argument('--fine', action='store_true', help='Search at 0.05 mm instead of 0.1 mm')
ap.add_argument('--vbus-width', type=float, default=.5)
ap.add_argument('--inner', action='store_true', help='Allow inner-layer repairs outside protected critical-return corridors')
ap.add_argument('--ripup', action='store_true', help='Allow one selected pair to cut obstructing noncritical tracks; reroute victims afterwards')
ap.add_argument('--clearance', type=float, default=.18, help='Planning clearance; exact/native minimums remain enforced')
a = ap.parse_args()
if a.fine:
    R.STEP = 1
if a.clearance < .16:
    ap.error('planning clearance must be at least 0.16 mm')
if a.ripup and (a.indices is None or len(a.indices.split(',')) != 1):
    ap.error('--ripup requires exactly one --indices value and fresh inputs afterwards')
g = json.loads(a.geometry.read_text())
entries = json.loads(a.components.read_text())
critical_corridors = {}
if a.inner:
    LR.OUTER = R.LAYERS = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
    critical = lambda n: n.startswith(('USB_DP', 'USB_DM', 'QSPI_', 'VREG_')) or n in ('XIN', 'XOUT', 'XTAL_OUT')
    # Preserve the adjacent reference plane of each outer critical conductor.
    # The other inner plane is shielded by that preserved reference plane.
    for signal_layer, reference_layer in [('F.Cu', 'In1.Cu'), ('B.Cu', 'In2.Cu')]:
        guard = lambda net: 1.5
        shapes = [LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w']/2+guard(t['net']), 24)
                  for t in g['tracks'] if critical(t['net']) and t['layer'] == signal_layer]
        shapes += [Polygon(pl).buffer(guard(p['net']), 24) for f in g['fps'] for p in f['pads'] if critical(p['net']) and signal_layer in p['layers'] for pl in p['poly'] if len(pl) >= 3]
        protected = critical_corridors[reference_layer] = unary_union(shapes)
        g['zones'].append({'net': '', 'name': 'planner-only critical return corridor', 'layers': [reference_layer], 'keepout': True,
                           'outline': [list(p.exterior.coords) for p in getattr(protected, 'geoms', [protected]) if not p.is_empty], 'fill': {}})
L = LR.Layout(g)
tracks, vias, report = [], [], []
removed_tracks, retained_tracks = [], []
protected_net = lambda n: n.startswith(('USB_', 'QSPI_', 'VREG_')) or n in ('XIN', 'XOUT', 'XTAL_OUT', '+1V1')
groupfile = a.output.with_suffix('.groups.json')
R.arg = lambda name, default=None: str(groupfile) if name == '--components' else default


def enrich(group, net):
    """Offer centerline and inset-pad anchors, not just crowded pad centers."""
    original = {(p[0], round(p[1], 6), round(p[2], 6)) for p in group}
    result = set(original)
    for t in g['tracks']:
        if t['net'] != net or t['layer'] not in LR.OUTER:
            continue
        ends = [(t['layer'], round(t[x], 6), round(t[y], 6)) for x, y in [('x1', 'y1'), ('x2', 'y2')]]
        if not all(p in original for p in ends):
            continue
        n = max(1, math.ceil(math.dist(ends[0][1:], ends[1][1:])/.5))
        for i in range(1, n):
            result.add((t['layer'], round(t['x1']+(t['x2']-t['x1'])*i/n, 6), round(t['y1']+(t['y2']-t['y1'])*i/n, 6)))
    for f in g['fps']:
        for p in f['pads']:
            if p['net'] != net or p['drill'][0]:
                continue
            for layer in LR.OUTER:
                if (layer, round(p['x'], 6), round(p['y'], 6)) not in original:
                    continue
                shape = unary_union([Polygon(pl) for pl in p['poly'] if len(pl) >= 3]).buffer(-.085)
                if shape.is_empty:
                    continue
                x0, y0, x1, y1 = shape.bounds
                pitch = .05 if min(x1-x0, y1-y0) < .15 else .15
                for x in np.arange(x0+.005, x1, pitch):
                    for y in np.arange(y0+.005, y1, pitch):
                        if shape.contains(Point(x, y)):
                            result.add((layer, round(float(x), 6), round(float(y), 6)))
    return sorted(result)


def nearby_groups(groups, net):
    left, right = [enrich(group, net) for group in groups]
    tree = cKDTree([p[1:] for p in right])
    distances, indices = tree.query([p[1:] for p in left], k=min(3, len(right)))
    distances = np.asarray(distances).reshape(len(left), -1)
    indices = np.asarray(indices).reshape(len(left), -1)
    pairs = sorted((float(distances[i, j]), tuple(left[i]), tuple(right[int(indices[i, j])]))
                   for i in range(len(left)) for j in range(distances.shape[1]))
    center = [(pairs[0][1][k]+pairs[0][2][k])/2 for k in (1, 2)]
    pairs = [pair for pair in pairs if math.dist([(pair[1][k]+pair[2][k])/2 for k in (1, 2)], center) <= 12][:600]
    selected = [sorted({pair[k] for pair in pairs}) for k in (1, 2)]
    # Retain the escape side of a pad even when its near edge ranks first.
    bounds = [min(p[k] for group in selected for p in group) for k in (1, 2)] + [max(p[k] for group in selected for p in group) for k in (1, 2)]
    return [[p for p in group if bounds[0]-3 <= p[1] <= bounds[2]+3 and bounds[1]-3 <= p[2] <= bounds[3]+3] for group in (left, right)]


def save():
    a.output.write_text(json.dumps({'status': 'routing plan; native checks still required',
                                   'inputs': {'geometry': str(a.geometry), 'components': str(a.components)},
                                   'routing_layers': list(R.LAYERS),
                                   'critical_inner_return_corridor_mm': {'signals_and_VREG': 1.5, 'DC_1V1': 'physical copper and native switching keepouts preserved; no synthetic projection exclusion'} if a.inner else None,
                                   'ops': [{'op': 'remove_tracks', 'tracks': removed_tracks}, {'op': 'add_tracks', 'tracks': retained_tracks+tracks}, {'op': 'add_vias', 'vias': vias}] if a.ripup else [{'op': 'add_tracks', 'tracks': tracks}, {'op': 'add_vias', 'vias': vias}],
                                   'report': report}, indent=2)+'\n')


def via_reasons(v, net):
    x, y = v['x'], v['y']
    annulus, drill = Point(x, y).buffer(.25, 32), Point(x, y).buffer(.125, 32)
    bad = []
    if not L.outline.buffer(-.50).contains(annulus):
        bad.append('edge')
    for layer in LR.OUTER:
        for c in L.cu[layer]:
            if c[1] == net or (c[2] == 'zone' and c[1] in ('GND', '+3V3')):
                continue
            if LR.R.near_box(c[0], x, y, 1) and c[0].distance(annulus) < a.clearance:
                bad.append('outer copper')
    if any(nn != net and LR.R.near_box(shape, x, y, 1) and shape.distance(annulus) < a.clearance for shape, nn in L.inner):
        bad.append('inner copper')
    if any(LR.R.near_box(shape, x, y, 1) and shape.distance(drill) < .10 for shape, _ in L.smd):
        bad.append('SMD drill web')
    if any(LR.R.near_box(hole, x, y, 2) and hole.distance(drill) < .35 for hole in L.pad_holes+L.via_holes):
        bad.append('drill spacing')
    if net == 'GND':
        core = Point(x, y).buffer(.35, 32)
        if not all(any(shape.contains(core) for shape in shapes) for shapes in L.gnd_planes.values()):
            bad.append('ground plane contact')
    return sorted(set(bad))


def screen(new_tracks, new_vias, net):
    bad, bad_vias = [], []
    rip = {}
    copper = {layer: [c for c in L.cu[layer] if c[1] != net and not (c[2] == 'zone' and c[1] in ('GND', '+3V3'))] for layer in LR.OUTER}
    trees = {layer: STRtree([c[0] for c in cs]) for layer, cs in copper.items()}
    own_shapes = {layer: [c[0] for c in L.cu[layer] if c[1] == net and c[2] != 'zone'] for layer in LR.OUTER}
    own_trees = {layer: STRtree(shapes) for layer, shapes in own_shapes.items()}
    hole_tree = STRtree(L.pad_holes)
    edge = L.outline.buffer(-.5)
    for t in new_tracks:
        shape = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w']/2, 24)
        layer = t['layer']
        covered = unary_union([own_shapes[layer][i] for i in own_trees[layer].query(shape)])
        added = shape.difference(covered)
        if layer in critical_corridors and added.intersects(critical_corridors[layer]):
            bad.append('critical return corridor')
        if not edge.contains(shape):
            bad.append('routed edge')
        if not added.is_empty:
            for i in trees[layer].query(added.buffer(.16)):
                other = copper[layer][i]
                if added.distance(other[0]) >= .155:
                    continue
                if a.ripup and other[2] == 'track' and not protected_net(other[1]):
                    rip[id(other[3])] = other[3]
                else:
                    bad.append('copper clearance')
        if any(L.pad_hole_nets[i] != net and shape.distance(L.pad_holes[i]) < .205 for i in hole_tree.query(shape.buffer(.21))):
            bad.append('drilled hole clearance')
    for v in new_vias:
        reasons = via_reasons(v, net)
        if reasons:
            bad.append('via clearance')
            bad_vias.append({'x': v['x'], 'y': v['y'], 'reasons': reasons})
    for i, v in enumerate(new_vias):
        for w in new_vias[i+1:]:
            if math.dist((v['x'], v['y']), (w['x'], w['y'])) < .60:
                bad.append('new via drill spacing')
                bad_vias.append({'x': w['x'], 'y': w['y'], 'reasons': ['new drill spacing']})
    return sorted(set(bad)), bad_vias, list(rip.values())


def route(m, groups, net, width):
    clear = a.clearance
    soft_cost = 40 if a.ripup else None
    result = R.search(m, groups[0][0], groups[1][0], soft_cost, 3, width/2+clear, .25+clear+.03)
    if result is None:
        return None
    path, cost = result
    start, end = R.SELECTED
    runs, current = [], [path[0]]
    for point in path[1:]:
        if point[0] != current[-1][0]:
            runs.append(current); current = [point]
        else:
            current.append(point)
    runs.append(current)
    runs = [R.pull(m, run, width/2+clear, soft_cost) for run in runs]
    new_tracks, new_vias = [], []
    def segment(layer, aa, bb):
        if math.dist(aa, bb) > 1e-6:
            new_tracks.append(dict(x1=aa[0], y1=aa[1], x2=bb[0], y2=bb[1], w=width, layer=layer, net=net))
    for run in runs:
        for aa, bb in zip(run, run[1:]):
            segment(run[0][0], aa[1:], bb[1:])
    segment(start[0], start[1:], runs[0][0][1:])
    segment(end[0], runs[-1][-1][1:], end[1:])
    for run_index, run in enumerate(runs[:-1]):
        x, y = run[-1][1:]
        old = min((v for v in g['vias'] if v['net'] == net and math.dist((x, y), (v['x'], v['y'])) < .6),
                  key=lambda v: math.dist((x, y), (v['x'], v['y'])), default=None)
        if old:
            for layer in (run[0][0], runs[run_index+1][0][0]):
                segment(layer, (x, y), (old['x'], old['y']))
        elif not any(math.dist((x, y), (v['x'], v['y'])) < 1e-6 for v in new_vias):
            new_vias.append(dict(x=x, y=y, d=.5, drill=.25, net=net))
    return new_tracks, new_vias


wanted = None if a.indices is None else {int(i) for i in a.indices.split(',')}
for index, entry in enumerate(entries):
    if wanted is not None and index not in wanted:
        continue
    if entry.get('members') and any(not any(item['kind'] in ('pad', 'zone') for item in group) for group in entry['members']):
        report.append({'index': index, 'status': 'orphan-copper; review removal instead of adding a connection'})
        save()
        continue
    match = re.search(r'\[(.*?)\]', entry['items'][0]['description'])
    if not match or not all(entry['groups']):
        continue
    net = match[1]
    if net.startswith('unconnected-'):
        continue
    width = a.vbus_width if net.startswith('VBUS') else a.power_width if net.startswith('+') else .25 if net == 'GND' else .15
    groups = nearby_groups(entry['groups'], net)
    legal_center = L.outline.buffer(-(.505+width/2))
    groups = [[p for p in group if legal_center.contains(Point(p[1], p[2]))] for group in groups]
    if not all(groups):
        report.append({'index': index, 'net': net, 'status': 'no-edge-safe-anchor'})
        save()
        continue
    points = groups[0]+groups[1]
    # One millimetre of extra obstacle context prevents clipped-map boundaries
    # from forgetting nearby copper. The nominal search margin remains larger.
    window = [max(0, min(p[1] for p in points)-a.margin), max(0, min(p[2] for p in points)-a.margin),
              min(285, max(p[1] for p in points)+a.margin), min(94.6, max(p[2] for p in points)+a.margin)]
    groupfile.write_text(json.dumps(groups))
    m = R.Maps(g, {net}, window, protected={t['net'] for t in g['tracks'] if protected_net(t['net'])})
    # Reusing existing copper does not remove additional reference-plane
    # material. A conservative mask may overlap an already validated annulus;
    # allow the route inside that annulus, and check all added metal exactly.
    for layer in R.LAYERS:
        mask = Image.new('1', (m.w, m.h), 0)
        draw = ImageDraw.Draw(mask)
        for shape, nn, kind, _ in L.cu[layer]:
            if nn != net or kind == 'zone':
                continue
            inside = shape.buffer(-(width/2+.006))
            for part in getattr(inside, 'geoms', [inside]):
                if part.is_empty:
                    continue
                draw.polygon([((x-m.x0)/R.G, (y-m.y0)/R.G) for x,y in part.exterior.coords], fill=1)
                for hole in part.interiors:
                    draw.polygon([((x-m.x0)/R.G, (y-m.y0)/R.G) for x,y in hole.coords], fill=0)
        inside = np.asarray(mask, dtype=bool)
        for distance in (m.dist_hard[layer], m.dist_all[layer]):
            distance[inside] = np.maximum(distance[inside], width/2+.181)
    m.blocked_vias = []
    attempts = []
    status = 'no-route'
    for attempt in range(a.retries):
        result = route(m, groups, net, width)
        if result is None:
            break
        new_tracks, new_vias = result
        bad, bad_vias, rip = screen(new_tracks, new_vias, net)
        attempts.append({'reasons': bad, 'bad_vias': bad_vias,
                         **({'rejected_tracks': new_tracks, 'rejected_vias': new_vias} if bad else {})})
        if bad:
            status = 'exact-screen-rejected'
            if bad_vias:
                m.blocked_vias.extend((v['x'], v['y'], .18) for v in bad_vias)
                continue
            break
        status = 'routed'
        if rip:
            route_shapes = {layer: unary_union([LineString([(t['x1'],t['y1']),(t['x2'],t['y2'])]).buffer(t['w']/2,32) for t in new_tracks if t['layer']==layer]) for layer in R.LAYERS}
            for old in rip:
                line = LineString([(old['x1'],old['y1']),(old['x2'],old['y2'])])
                remain = line.difference(route_shapes[old['layer']].buffer(old['w']/2+.20,32))
                for piece in getattr(remain,'geoms',[remain]):
                    if piece.is_empty or piece.length < .05:
                        continue
                    aa,bb = piece.coords[0],piece.coords[-1]
                    retained_tracks.append(dict(old,x1=aa[0],y1=aa[1],x2=bb[0],y2=bb[1]))
            removed_tracks.extend(rip)
            attempts[-1]['ripup_nets'] = sorted({t['net'] for t in rip})
            attempts[-1]['ripup_track_count'] = len(rip)
        tracks.extend(new_tracks); vias.extend(new_vias)
        g['tracks'].extend(new_tracks); g['vias'].extend(new_vias)
        for t in new_tracks:
            L.add_track(t)
        for v in new_vias:
            L.add_via(v['x'], v['y'], net)
        break
    report.append({'index': index, 'net': net, 'status': status, 'width': width, 'attempts': attempts, 'search': R.LAST_DIAGNOSTIC})
    print(index, net, status, len(attempts), attempts[-1]['reasons'] if status != 'routed' and attempts else R.LAST_DIAGNOSTIC, flush=True)
    save(); del m; gc.collect()
save()
