#!/usr/bin/python3
"""Pinned read-only exact-witness audit of R2 selected-aead accepted edges.

Requires explicit --execute. Default/preflight never imports pcbnew or loads a
board. Reconstructs source components only; no new native neighbor discovery,
new material graph, save, fill, source edit, or production exporter edit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
import traceback

HERE = Path('/tmp/v7-contact-positive-witness-helper')
CHECKER = Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2/export_material_graph.py')
GRAPH = Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2/aead/physical-graph.json')
BOARD = Path('/tmp/v7-c128-stub-retirement-aead/source/pcb/maru60.kicad_pcb')
HELPER = HERE/'positive_witness.py'
PINS = {
    str(CHECKER): '57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9',
    str(GRAPH): '7a6ca935a3699b2d0a2e1e7b21de7c27059aa802e07080f904b8b80314170741',
    str(BOARD): 'aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f',
    str(HELPER): '0ea4d4b9447fcc62780b8f12a9fcd1538c2f8f27d2fe9ab61b18cbf7573d2d7c',
}
MARKER = '# Native candidate discovery is resolved to canonical objects before any shape use.'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def demand(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def check_pins():
    observed = {path: sha(path) for path in PINS}
    demand(observed == PINS, {'error': 'pinned_input_mismatch', 'expected': PINS, 'observed': observed})
    commands = json.loads((CHECKER.parent/'commands.json').read_text())
    matches = [r for r in commands if r.get('label') == 'aead']
    demand(len(matches) == 1, 'Missing/ambiguous selected-aead command provenance')
    c = matches[0]
    demand(c['exit_code'] == 0 and c['checker_sha256'] == PINS[str(CHECKER)]
           and c['output_sha256'] == PINS[str(GRAPH)]
           and c['input_sha256_before'] == c['input_sha256_after'] == PINS[str(BOARD)],
           'Pinned selected graph does not match successful commands.json provenance')
    return observed


def isolate_xdg():
    root = HERE/'selected-aead-xdg'
    mapping = {}
    for variable, leaf in [('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'),
                           ('XDG_DATA_HOME', 'data'), ('XDG_STATE_HOME', 'state'),
                           ('XDG_RUNTIME_DIR', 'runtime')]:
        path = root/leaf
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.chmod(0o700)
        os.environ[variable] = str(path)
        mapping[variable] = str(path)
    # Also isolate the nonstandard spelling used by the original export runner.
    os.environ['XDG_RUNTIME_HOME'] = mapping['XDG_RUNTIME_DIR']
    mapping['XDG_RUNTIME_HOME'] = mapping['XDG_RUNTIME_DIR']
    return mapping


def run(report, prior=None):
    from positive_witness import ExactPoint, prepare_polyset, find_positive_witness, verify_positive_witness, verify_witness_record
    report['xdg'] = isolate_xdg()  # Before the prefix imports pcbnew.
    graph = json.loads(GRAPH.read_text())
    demand(graph['source_path'] == str(BOARD) and graph['board_sha256'] == PINS[str(BOARD)], 'Graph source binding differs')
    demand(graph['native_version'] == '9.0.2+dfsg-1' and graph['unchanged'] is True, 'Unsupported/incomplete graph export')
    demand(graph['contact_guard']['inward_nm'] == 2, 'R2 guard changed')
    text = CHECKER.read_text()
    demand(text.count(MARKER) == 1, 'Cannot identify exactly one pinned setup prefix')
    prefix = text.split(MARKER)[0]
    # This prefix loads this one board, builds source components and proves
    # barrels. It never reaches per-object GetConnectedTracks/GetConnectedPads.
    ns = {'__name__': '__exact_witness_source_reconstruction__', '__file__': str(CHECKER)}
    old_argv = sys.argv
    try:
        sys.argv = [str(CHECKER), str(BOARD), str(HERE/'UNUSED-never-written-graph.json')]
        exec(compile(prefix, str(CHECKER)+'::setup-prefix', 'exec'), ns, ns)
    finally:
        sys.argv = old_argv
    p, board, components, metadata = ns['p'], ns['b'], ns['components'], ns['metadata']
    demand(p.GetBuildVersion() == '9.0.2+dfsg-1', 'Native build changed')
    # Reconstruct the identical physical zone components WITHOUT candidate
    # discovery or edge generation. IDs and native source metadata are checked
    # against the pinned graph before any witness can count.
    for zone in board.Zones():
        if zone.GetIsRuleArea():
            continue
        for layer in ns['layers']:
            if not zone.IsOnLayer(layer):
                continue
            layer_name = board.GetLayerName(layer)
            physical = p.SHAPE_POLY_SET(zone.GetFilledPolysList(layer))
            physical.BooleanSubtract(ns['all_drills'])
            for i, part in enumerate(ns['parts'](physical)):
                name = 'zone:'+ns['uid'](zone)+':'+str(layer)+':'+str(i)
                demand(name not in components, ('Duplicate reconstructed node', name))
                components[name] = part
                metadata[name] = dict(kind='zone', uuid=ns['uid'](zone), layer=layer_name,
                                      index=i, area_mm2=part.Area()/1e12, net=zone.GetNetname())
    demand(metadata == graph['material_nodes'], 'Reconstructed node IDs/metadata/areas differ from R2')
    demand(set(components) == set(graph['material_nodes']), 'Reconstructed physical component IDs differ')
    demand(ns['objects'] == graph['object_nodes_by_layer'], 'Object component assignment differs')
    demand(ns['barrels'] == graph['barrel_joins'], 'Reconstructed barrel proofs differ')
    report.update(reconstructed_node_count=len(metadata),
                  source_metadata_exact_match=True, source_object_mapping_exact_match=True,
                  source_barrel_proofs_exact_match=True,
                  accepted_material_edge_count=len(graph['material_edges']),
                  existing_guard_failed_edges_not_audited=len(graph['guard_failing_material_edges']))
    print('SOURCE_BINDINGS_PASS', len(metadata), 'edges', len(graph['material_edges']), flush=True)
    prepared, certificates, failures = {}, report['witnesses'], report['failures']
    seed_types = {'raw_intersection': 0, 'guarded_intersection_fallback': 0, 'prior_certificate_reverified': 0}
    prior_witnesses = {}
    if prior is not None:
        demand(prior['input_sha256'] == PINS and prior['all_pinned_inputs_unchanged'] is True, 'Prior certificate source bindings differ')
        prior_witnesses = {w[0]: w for w in prior['witnesses']}
        prior_failures = {f['edge_index']: f for f in prior['failures']}
        demand(len(prior_witnesses) == len(prior['witnesses']) and len(prior_failures) == len(prior['failures']), 'Duplicate prior edge records')
        demand(set(prior_witnesses).isdisjoint(prior_failures) and set(prior_witnesses)|set(prior_failures) == set(range(len(graph['material_edges']))), 'Incomplete prior edge coverage')
        demand(all(f['reason'] == 'edge_verification_exception' and f.get('error') == "RuntimeError('Recomputed unguarded edge area differs')" and f['endpoints'][0].startswith('zone:') for f in prior_failures.values()), 'Replay is limited to known zone operand-order failures')
    guard_cache = ns['guard_cache']
    for edge_index, edge in enumerate(graph['material_edges']):
        a, b, raw_area, guarded_area = edge
        try:
            demand(raw_area > 0 and guarded_area > 0, 'Pinned accepted edge has nonpositive area')
            demand(metadata[a]['layer'] == metadata[b]['layer'] and metadata[a]['net'] == metadata[b]['net'], 'Edge layer/net mismatch')
            for name in (a, b):
                if name not in prepared:
                    prepared[name] = prepare_polyset(components[name])
            if edge_index in prior_witnesses:
                old = prior_witnesses[edge_index]
                demand(prior['component_sha256'][a] == prepared[a].digest and prior['component_sha256'][b] == prepared[b].digest, 'Prior coordinate fingerprint differs')
                demand(verify_positive_witness(prepared[a], prepared[b], ExactPoint(old[1], old[2], old[3])), 'Saved exact witness does not reverify')
                certificates.append(old)
                seed_types['prior_certificate_reverified'] += 1
                continue
            overlap = p.SHAPE_POLY_SET()
            # R2's unguarded zone call is area(object, zone), although its
            # material-edge endpoint order is [zone, object]. Preserve this
            # native operand order instead of assuming rounded commutativity.
            raw_a, raw_b = (b, a) if metadata[a]['kind'] == 'zone' else (a, b)
            overlap.BooleanIntersection(components[raw_a], components[raw_b])
            demand(overlap.Area()/1e12 == raw_area, 'Recomputed unguarded edge area differs')
            seed_types['raw_intersection'] += 1
            result = find_positive_witness(prepared[a], prepared[b], seed_polyset=overlap)
            if not result.found:
                # Alternative seeds only. This never changes the physical
                # boundaries or the final exact verifier's 2 nm requirement.
                for name in (a, b):
                    if name not in guard_cache:
                        eroded = p.SHAPE_POLY_SET(components[name])
                        eroded.Deflate(2, p.CORNER_STRATEGY_ROUND_ALL_CORNERS, 1)
                        guard_cache[name] = eroded
                guarded_overlap = p.SHAPE_POLY_SET()
                guarded_overlap.BooleanIntersection(guard_cache[a], guard_cache[b])
                demand(guarded_overlap.Area()/1e12 == guarded_area, 'Recomputed guarded edge area differs')
                seed_types['guarded_intersection_fallback'] += 1
                result = find_positive_witness(prepared[a], prepared[b], seed_polyset=guarded_overlap)
            if not result.found:
                failures.append(dict(edge_index=edge_index, endpoints=[a, b],
                                     reason=result.reason, candidates_checked=result.candidates_checked,
                                     raw_area_mm2=raw_area, guarded_area_mm2=guarded_area))
            else:
                certificate = result.witness.to_dict()
                demand(verify_witness_record(prepared[a], prepared[b], certificate), 'Certificate self-reverification failed')
                point = result.witness.point
                certificates.append([edge_index, point.x_num, point.y_num, point.den])
        except Exception as exc:
            failures.append(dict(edge_index=edge_index, endpoints=[a, b],
                                 reason='edge_verification_exception', error=repr(exc)))
        if (edge_index+1) % 2000 == 0:
            print('EXACT_WITNESSES', edge_index+1, 'passed', len(certificates), 'failed', len(failures), flush=True)
    report.update(component_sha256={name: c.digest for name, c in sorted(prepared.items())},
                  seed_types=seed_types, prepared_component_count=len(prepared),
                  verified_edge_count=len(certificates), failed_edge_count=len(failures))
    demand(len(certificates)+len(failures) == len(graph['material_edges']), 'Audit edge count mismatch')
    report['status'] = 'passed' if not failures else 'failed'
    report['all_accepted_material_edges_have_exact_positive_witness'] = not failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Execute the explicitly authorized one-board audit')
    parser.add_argument('--check-pins-only', action='store_true')
    parser.add_argument('--replay-zone-order', action='store_true', help='Reverify saved certificates; rerun only known zone operand-order failures')
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Optimized Python unsupported')
    check_pins()
    if args.check_pins_only or not args.execute:
        print(json.dumps({'pins_match': True, 'board_loaded': False,
                          'execution_requires': '--execute', 'pins': PINS}, indent=2))
        return 0
    prior_path = HERE/'selected-aead-exact-witnesses.json' if args.replay_zone_order else None
    prior_sha = sha(prior_path) if prior_path else None
    prior = json.loads(prior_path.read_text()) if prior_path else None
    output = HERE/('selected-aead-exact-witnesses-order-replay.json' if prior_path else 'selected-aead-exact-witnesses.json')
    demand(not output.exists(), 'Refusing to overwrite previous audit; coordinate a new output explicitly')
    started = time.monotonic()
    report = dict(status='running', revision='selected-aead-r2-exact-witness-audit-v2-preserve-native-operand-order',
                  input_sha256=PINS.copy(), audit_script_sha256=sha(__file__),
                  native_version='9.0.2+dfsg-1', clearance_nm_at_least=2,
                  witness_schema=['pinned_graph_material_edge_index', 'x_num_nm', 'y_num_nm', 'positive_common_denominator'],
                  component_binding='Each witness edge index resolves endpoints in pinned graph material_edges; both endpoint coordinate hashes are in component_sha256.',
                  method='Exact outer-and-hole PIP and exact segment-distance >=2 nm for both original physical components; native intersections generate seeds only.',
                  scope='Only R2 accepted material edges; existing guard failures excluded, barrel proofs reconstructed/compared but not treated as coplanar witness edges. Source topology is reconstructed by pinned native R2 code, not independently certified.',
                  witnesses=[], failures=[])
    if prior_path:
        report.update(prior_report_path=str(prior_path), prior_report_sha256=prior_sha)
    try:
        run(report, prior)
    except Exception as exc:
        report.update(status='failed', fatal_error=repr(exc), fatal_traceback=traceback.format_exc(),
                      all_accepted_material_edges_have_exact_positive_witness=False)
    finally:
        after = {path: sha(path) for path in PINS}
        report['input_sha256_after'] = after
        report['all_pinned_inputs_unchanged'] = after == PINS and (prior_path is None or sha(prior_path) == prior_sha)
        if not report['all_pinned_inputs_unchanged']:
            report['status'] = 'failed'
            report['all_accepted_material_edges_have_exact_positive_witness'] = False
        report['seconds'] = time.monotonic()-started
        output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
        summary = {k: v for k, v in report.items() if k not in ('witnesses', 'component_sha256', 'fatal_traceback', 'failures')}
        summary.update(output=str(output), output_sha256=sha(output), failure_examples=report['failures'][:10])
        output.with_name(output.stem+'-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(json.dumps(summary, indent=2), flush=True)
    return 0 if report['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
