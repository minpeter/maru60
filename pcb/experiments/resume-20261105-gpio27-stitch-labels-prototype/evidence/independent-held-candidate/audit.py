from pathlib import Path
import sys,json,hashlib,copy
sys.path.insert(0,'/workspace/shared/maru60-resume/continuation-c782/header/scripts')
import sexp as sx
R=Path('/workspace/shared/maru60-resume/continuation-c782'); O=R/'independent27'
paths={'base':R.parent/'combined-trial/pcb','header':R/'header/trial27/pcb','stitch':R/'stitch/pcb','labels':R/'warnings-next/candidate/pcb','combined':R/'combined27/pcb'}
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
parsed={k:sx.parse((v/'maru60.kicad_pcb').read_text()) for k,v in paths.items()}
uid=lambda x:(sx.get(x,'uuid') or [None,None])[1] if isinstance(x,list) else None
maps={k:{uid(x):x for x in a if uid(x)} for k,a in parsed.items()}
strip=lambda x,fields:[v for v in x if not(isinstance(v,list) and v[0] in fields)]
a,b=maps['header'],maps['combined']; added=set(b)-set(a);removed=set(a)-set(b);changed=[u for u in a.keys()&b.keys() if a[u]!=b[u]]
assert added=={'efdf2c37-5653-4018-9cc8-dfb15999bb91'} and not removed
assert b[next(iter(added))]==maps['stitch'][next(iter(added))]
rows=[]
for u in changed:
 x,y=a[u],b[u]
 if x[0]=='zone': assert strip(x,{'filled_polygon','fill_segments'})==strip(y,{'filled_polygon','fill_segments'});kind='fill only'
 elif x[0]=='footprint':
  assert strip(x,{'property'})==strip(y,{'property'})
  xp=[z for z in x if isinstance(z,list) and z[0]=='property'];yp=[z for z in y if isinstance(z,list) and z[0]=='property'];assert len(xp)==len(yp)
  delta=[(v,w) for v,w in zip(xp,yp) if v!=w];assert len(delta)==1 and delta[0][0][1]=='Reference'
  ref=delta[0][0][2];assert ref in ['U13','R135','R145','U11'];assert y==maps['labels'][u];kind='reference only '+ref
 else: raise AssertionError((u,x[0]))
 rows.append({'uuid':u,'type':x[0],'scope':kind})
restored=[copy.deepcopy(a[uid(x)]) if uid(x) in a else x for x in parsed['combined'] if uid(x) not in added];assert restored==parsed['header']
fmap=lambda p:{str(f.relative_to(p)):H(f) for f in p.rglob('*') if f.is_file()}
fm={k:fmap(v) for k,v in paths.items()};assert set(fm['combined'])==set(fm['base']);companions=[n for n in fm['base'] if fm['base'][n]!=fm['combined'][n]];assert companions==['maru60.kicad_pcb']
G={k:json.loads(p.read_text()) for k,p in {'base':R.parent/'combined-trial/qa/material-graph.json','header':R/'header/qa/material-graph.json','stitch':R/'stitch/qa/material-graph.json','combined':R/'combined27/qa/material-graph.json'}.items()}
for k,g in G.items():assert g['board_sha256']==fm[k]['maru60.kicad_pcb']
assert sorted(G['header']['direct_edges'])==sorted(G['combined']['direct_edges'])
for field in ['pad_inventory','pad_partitions_by_net','guard_failing_material_edges','empty_object_layers','multiple_component_object_layers']:
 assert G['header'][field]==G['combined'][field],field
for k,v in G['header']['material_nodes'].items():
 if v['kind']=='object':assert v==G['combined']['material_nodes'][k],k
assert all(x in G['combined']['barrel_joins'] for x in G['header']['barrel_joins'])
znew=[x for x in G['combined']['zone_edges'] if x not in G['header']['zone_edges']];zgone=[x for x in G['header']['zone_edges'] if x not in G['combined']['zone_edges']];assert not zgone and len(znew)==2 and all(x[1] in added for x in znew)
def edges(g,field):return {tuple(sorted(v[:2])):v[2:] for v in g[field]}
x,y=edges(G['base'],'direct_edges'),edges(G['combined'],'direct_edges');delta={'removed':[list(k) for k in x.keys()-y.keys()],'changed':[{'key':k,'before':x[k],'after':y[k]} for k in x.keys()&y.keys() if x[k]!=y[k]]}
result={'hashes':{k:v['maru60.kicad_pcb'] for k,v in fm.items()},'header_to_combined_added':list(added),'header_to_combined_changes':rows,'raw_reconstruction_pass':True,'all_57_companions_exact':True,'header_direct_contacts_exact':True,'header_old_object_material_nodes_exact':True,'header_pad_partitions_exact':True,'header_guard_failures_exact':True,'new_stitch_zone_contacts':znew,'base_direct_delta':delta}
(O/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
