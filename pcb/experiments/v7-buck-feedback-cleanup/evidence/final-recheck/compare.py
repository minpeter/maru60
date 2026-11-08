from pathlib import Path
import json,hashlib
D=Path(__file__).parent;Q=D/'qa';T=Path('/tmp/v7-buck-deadarm-trial-2c7e');L=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=L(Q/'source-physical-graph.json');b=L(Q/'candidate-physical-graph.json');oa=L(T/'qa/source-physical-graph.json');ob=L(T/'qa/candidate-physical-graph.json');s=L(Q/'source-drc.json');c=L(Q/'candidate-drc.json');e=L(Q/'candidate-erc.json');ledger=L(T/'qa/build.json')
assert a['board_sha256']==sha(D/'source/pcb/maru60.kicad_pcb')==sha(T/'source/pcb/maru60.kicad_pcb')=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
assert b['board_sha256']==sha(D/'candidate/pcb/maru60.kicad_pcb')==sha(T/'filled/pcb/maru60.kicad_pcb')=='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f'
assert sha(Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb'))==a['board_sha256']
assert a['pad_inventory']==b['pad_inventory'] and a['pad_partitions_by_net']==b['pad_partitions_by_net']
for fresh,old in [(a,oa),(b,ob)]:
 for k in ['pad_inventory','pad_partitions_by_net','direct_edges','zone_edges','zones']:assert fresh[k]==old[k],k
canon=lambda v:json.dumps(v,sort_keys=True);delta=lambda old,new:[json.loads(v) for v in sorted(set(map(canon,old))-set(map(canon,new)))]
removed=delta(s['violations'],c['violations']);added=delta(c['violations'],s['violations']);assert not added and len(removed)==1 and removed[0]['type']=='via_dangling' and removed[0]['items'][0]['uuid']=='d382de57-3476-43c4-ac26-0a72b21acf7c'
opens=lambda dr:sorted([sorted(q['uuid'] for q in v['items']) for v in dr['unconnected_items']]);erc=[v for sh in e['sheets'] for v in sh['violations']];assert not erc and not c['schematic_parity'] and not s['schematic_parity']
assert all(v['severity']=='warning' for v in c['violations']) and len(c['violations'])==67 and len(c['unconnected_items'])==12
r=dict(status='UNSELECTED final recheck; original strict no-plane-loss failure unchanged',source_sha256=a['board_sha256'],candidate_sha256=b['board_sha256'],selected_source_still_exact=True,all_named_net_count=len(a['pad_partitions_by_net']),all_pad_inventory_and_partitions_exact=True,fresh_graphs_equal_prior_native_graphs=True,source_open_pairs=opens(s),candidate_open_pairs=opens(c),exact_open_endpoint_pairs_equal=opens(s)==opens(c),source_open_records=s['unconnected_items'],candidate_open_records=c['unconnected_items'],warning_removed=removed,warning_added=added,source_warnings=len(s['violations']),candidate_warnings=len(c['violations']),candidate_opens=len(c['unconnected_items']),other_DRC_errors=0,parity=0,ERC=0,candidate_totals={k:b[k] for k in ['tracks','vias','footprints','track_length_mm']},receipts={p.name:sha(p) for p in Q.glob('*.json') if p.name!='FINAL_RECHECK.json'})
(Q/'FINAL_RECHECK.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['source_open_records','candidate_open_records','source_open_pairs','candidate_open_pairs','receipts']},indent=2))
