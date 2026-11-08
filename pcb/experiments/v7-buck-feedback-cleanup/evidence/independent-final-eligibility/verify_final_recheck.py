if not __debug__:raise RuntimeError('Optimized Python unsupported')
import json,hashlib,collections,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;F=Path('/tmp/v7-buck-deadarm-final-recheck');Q=F/'qa';S=Path('/tmp/v7-buck-deadarm-independent-review/packet');P=Path('/tmp/v7-buck-precision-criterion-review/packet');read=lambda p:json.loads(p.read_text())
def H(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for d,expected in [(S,'d44a930febcfe545cedae062c2649b952225778cca0603bfbf0a480b63fbee6f'),(P,'ba50b29c74fbcef38c15012dbbd020c6e03bcf632b56f5f433bac20a4bccc2c6')]:
 assert H(d/'MANIFEST.json')==expected
 for n,meta in read(d/'MANIFEST.json')['files'].items():assert H(d/n)==meta['sha256']
term=read(Q/'FINAL_RECHECK.json');assert H(Q/'FINAL_RECHECK.json')=='8f0af4db3f30e7f06f58c344b8fab8f3694da1de03f81c262f54d929f4af8640'
for n,h in term['receipts'].items():assert H(Q/n)==h
prior=read(S/'raw-graph-review.json');maps={}
for n,key in [('source','selected'),('candidate','candidate')]:
 d=F/n/'pcb';m={str(p.relative_to(d)):H(p) for p in sorted(d.rglob('*')) if p.is_file()};assert m==prior['complete_filemaps'][key];maps[n]=m
oldsg=read(S/'bound-evidence/source-physical-graph.json');oldcg=read(S/'bound-evidence/candidate-physical-graph.json');sg=read(Q/'source-physical-graph.json');cg=read(Q/'candidate-physical-graph.json')
for name,fresh,old in [('source',sg,oldsg),('candidate',cg,oldcg)]:
 assert fresh['source_path']==str(F/name/'pcb/maru60.kicad_pcb') and fresh['board_sha256']==maps[name]['maru60.kicad_pcb']
 assert {k:v for k,v in fresh.items() if k not in ['source_path','seconds']}=={k:v for k,v in old.items() if k not in ['source_path','seconds']}
cmds=read(Q/'commands.json');assert len(cmds)==5 and all(type(q['exit_code'])is int and q['exit_code']==0 and type(q['seconds'])in(float,int) and q['seconds']>0 for q in cmds)
expected=[['/usr/bin/python3','/tmp/v7-buck-deadarm-trial-2c7e/tools/export_native_physical_graph.py',str(F/'source/pcb/maru60.kicad_pcb'),str(Q/'source-physical-graph.json')],['kicad-cli','pcb','drc','--schematic-parity','--format','json','--output',str(Q/'source-drc.json'),str(F/'source/pcb/maru60.kicad_pcb')],['/usr/bin/python3','/tmp/v7-buck-deadarm-trial-2c7e/tools/export_native_physical_graph.py',str(F/'candidate/pcb/maru60.kicad_pcb'),str(Q/'candidate-physical-graph.json')],['kicad-cli','pcb','drc','--schematic-parity','--format','json','--output',str(Q/'candidate-drc.json'),str(F/'candidate/pcb/maru60.kicad_pcb')],['kicad-cli','sch','erc','--format','json','--output',str(Q/'candidate-erc.json'),str(F/'candidate/pcb/maru60.kicad_sch')]];assert [c['command'] for c in cmds]==expected
# Reuse the sealed independent endpoint/component checker against the NEW observed graphs and diagnostics.
ns={'__file__':str(S/'audit_open_pairs.py')};exec((S/'audit_open_pairs.py').read_text().split("S=read(R/'source-strip.json')")[0],ns)
sd=read(Q/'source-drc.json');cd=read(Q/'candidate-drc.json');sp,srecords=ns['check'](read(S/'source-strip.json'),sg,sd);cp,crecords=ns['check'](read(S/'candidate-strip.json'),cg,cd);assert collections.Counter(sp)==collections.Counter(cp)
canon=lambda x:json.dumps(dict(x,items=sorted(x['items'],key=lambda q:q['uuid'])),sort_keys=True);a=collections.Counter(map(canon,sd['violations']));b=collections.Counter(map(canon,cd['violations']));assert not(b-a) and sum((a-b).values())==1;removed=json.loads(next(iter(a-b)));assert removed==prior['native_DRC']['removed_exact_warning'];assert len(a)==68 and len(b)==67 and all(q['severity']=='warning' for q in cd['violations']);assert not sd['schematic_parity'] and not cd['schematic_parity'];assert not any(v for s in read(Q/'candidate-erc.json')['sheets'] for v in s['violations'])
assert term['source_open_records']==sd['unconnected_items'] and term['candidate_open_records']==cd['unconnected_items'];assert term['warning_removed']==[removed] and term['warning_added']==[]
for k,val in [('source_warnings',68),('candidate_warnings',67),('candidate_opens',12),('other_DRC_errors',0),('parity',0),('ERC',0)]:assert type(term[k])is int and term[k]==val
assert term['source_sha256']==sg['board_sha256'] and term['candidate_sha256']==cg['board_sha256'];assert term['candidate_totals']=={k:cg[k] for k in ['tracks','vias','footprints','track_length_mm']}
selected=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb');actual=Path('/tmp/v7-buck-deadarm-trial-2c7e/filled/pcb/maru60.kicad_pcb');assert H(selected)==sg['board_sha256'] and H(actual)==cg['board_sha256']
# Keep complete new outputs in the builder packet; seal exact per-file bindings and small final records here.
E=R/'bound-records';E.mkdir(exist_ok=False)
for n in ['FINAL_RECHECK.json','commands.json','source-drc.json','candidate-drc.json','candidate-erc.json','source-graph.log','candidate-graph.log','source-drc.log','candidate-drc.log','candidate-erc.log','comparison.log']:
 shutil.copyfile(Q/n,E/n)
bindings={str(p.relative_to(F)):{'sha256':H(p),'bytes':p.stat().st_size} for p in sorted(F.rglob('*')) if p.is_file() and not any(x in ('runtime','fullboard-preview') for x in p.relative_to(F).parts)}
bindings['external_graph_exporter']={'path':'/tmp/v7-buck-deadarm-trial-2c7e/tools/export_native_physical_graph.py','sha256':H(Path('/tmp/v7-buck-deadarm-trial-2c7e/tools/export_native_physical_graph.py'))}
(R/'RECHECK_BINDINGS.json').write_text(json.dumps(bindings,indent=2)+'\n')
result={'decision':'eligible_for_bounded_adoption_under_authorized_exact_candidate_1nm_criterion','source_sha256':sg['board_sha256'],'candidate_sha256':cg['board_sha256'],'old_strict_global_no_plane_loss':'FAIL preserved unchanged','applied_candidate_specific_precision_criterion':'PASS','fresh_final_recheck':'PASS independently reverified','strict_manifest_sha256':H(S/'MANIFEST.json'),'precision_manifest_sha256':H(P/'MANIFEST.json'),'precision_receipt_sha256':H(P/'FINAL_PRECISION_REVIEW.json'),'fresh_builder_terminal_sha256':H(Q/'FINAL_RECHECK.json'),'all_five_actual_commands_successful_and_expected':True,'all_recorded_output_hashes_verified':True,'every_actual_output_log_and_complete54file_source_candidate_copy_bound':True,'fresh_full_graphs_equal_prior_rechecked_graphs_except_path_timing':True,'all245_net_partitions_exact':True,'all12_complete_endpoint_component_pairs_exact':True,'all48_new_DRC_endpoint_UUID_native_position_description_checks_pass':True,'fresh_source_candidate_raw_open_records_exact_after_item_order_normalization':collections.Counter(map(canon,sd['unconnected_items']))==collections.Counter(map(canon,cd['unconnected_items'])),'diagnostics':{'warnings_before':68,'warnings_after':67,'only_removed_warning_uuid':'d382de57-3476-43c4-ac26-0a72b21acf7c','hard_DRC_errors':0,'parity':0,'ERC':0,'remaining_opens':12},'selection_performed':False,'limitations':['Eligibility is only for exact aead2fb0 under the separately authorized1nm coordinate-precision condition, not the original strict gate.','No generic checker, future-candidate exemption, new active simulation, SI/noise/loop-stability/hardware or manufacturing qualification.','Twelve inherited GPIO opens and67remaining warnings are not resolved by this cleanup.'],'bindings_sha256':H(R/'RECHECK_BINDINGS.json')}
(R/'FINAL_ELIGIBILITY.json').write_text(json.dumps(result,indent=2)+'\n')
(R/'REVIEW.md').write_text('''# Final BUCK cleanup eligibility

Exact candidate aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f is eligible for bounded adoption under the separately authorized candidate-specific1nm criterion. The original strict zero-plane-loss FAIL remains true and preserved.

The fresh source/candidate physical graphs equal the previously independently reviewed graphs in every field except execution path and timing. All five commands, every terminal-bound output hash, full54-file source/candidate copies and all output/log bindings were independently checked. Both graphs and new DRC endpoint records were rechecked against complete components and native identities; all12 pairs remain exact. DRC has0othererrors,67warnings (only the specified dangling via removed),12opens, parity0; ERC0.

The sealed strict and precision packets remain unchanged. This receipt closes only their pending final recheck. Parent selection/installation is separate; no CAD or selection was changed by the reviewer. No SI/noise/stability/hardware/manufacturing improvement or general future waiver is implied. This unit still has12inheritedGPIOopens and67warnings.
''')
manifest={'schema':'buck-final-independent-eligibility-v1','candidate_sha256':cg['board_sha256'],'files':{str(p.relative_to(R)):{'sha256':H(p),'bytes':p.stat().st_size} for p in sorted(R.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}};(R/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');z=R.parent/'v7-buck-final-recheck-independent-review.zip'
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
 for p in sorted(R.rglob('*')):
  if p.is_file():f.write(p,'v7-buck-final-recheck-independent-review/'+str(p.relative_to(R)))
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None
 for n,d in manifest['files'].items():assert hashlib.sha256(f.read('v7-buck-final-recheck-independent-review/'+n)).hexdigest()==d['sha256']
print(json.dumps({'directory':str(R),'manifest_sha256':H(R/'MANIFEST.json'),'eligibility_sha256':H(R/'FINAL_ELIGIBILITY.json'),'zip':str(z),'zip_sha256':H(z),'bytes':z.stat().st_size},indent=2))
