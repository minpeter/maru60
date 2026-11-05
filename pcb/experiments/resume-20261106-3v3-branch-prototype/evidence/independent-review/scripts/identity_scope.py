from pathlib import Path
import json,hashlib,sys,math,pcbnew as p
R=Path('/workspace/shared/maru60-resume'); S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype'; C=R/'continuation-97d9eb7/stub3v3'; D=R/'continuation-97d9eb7/stub3v3-independent'; H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
ha,hb=[H(q/'pcb/maru60.kicad_pcb')for q in[S,C]];assert ha=='2e532c1a16e64a34eafafdfbd5b85c05d70bb12ad9e52924c5cbe024fdc9aa2c';assert hb=='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e'
man=[{str(f.relative_to(q/'pcb')):H(f)for f in (q/'pcb').rglob('*')if f.is_file()}for q in[S,C]];assert man[0].keys()==man[1].keys();changed=[k for k in man[0]if man[0][k]!=man[1][k]];assert changed==['maru60.kicad_pcb'];assert len(man[0])==58
sys.path.insert(0,str(R/'tools'));from sexpr_spans import children,head,field
raw=[(q/'pcb/maru60.kicad_pcb').read_text()for q in[S,C]]
def prim(t):return {json.loads(field(s,'uuid').split(' ',1)[1][:-1]):s for _,_,s in children(t)if head(s)in('segment','arc','via','footprint')}
a,b=map(prim,raw);removed=set(json.loads((C/'qa/build.json').read_text())['removed']);assert set(a)-set(b)==removed;assert all(u in a and a[u]==v for u,v in b.items())
bs=[p.LoadBoard(str(q/'pcb/maru60.kicad_pcb'))for q in[S,C]]
items=[{x.m_Uuid.AsString():x for x in list(board.GetTracks())+[x for f in board.GetFootprints()for x in f.Pads()]}for board in bs]
tracks=[items[0][u]for u in removed if not isinstance(items[0][u],p.PCB_VIA)];assert len(tracks)==9 and all(q.GetWidth()==300000 and q.GetNetname()=='+3V3'for q in tracks)
length=sum(math.hypot(q.GetStart().x-q.GetEnd().x,q.GetStart().y-q.GetEnd().y)for q in tracks)/1e6;assert abs(length-8.503623449077)<1e-12
hole_ids=[{u for u,q in it.items()if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()}for it in items];assert hole_ids[0]-hole_ids[1]=={'0826a4b6-5567-52ab-a787-b898d20d23ac'}and not hole_ids[1]-hole_ids[0]
drc=[json.loads((D/'qa'/n).read_text())for n in['source-drc.json','drc.json']];v=[{json.dumps(v,sort_keys=True)for v in q['violations']}for q in drc];assert not v[1]-v[0];removed_w=[json.loads(x)for x in v[0]-v[1]];assert len(removed_w)==1 and removed_w[0]['type']=='track_dangling' and removed_w[0]['severity']=='warning';assert any(i['uuid']=='53e7b99f-308f-57ae-9e47-9e779e6b3272'for i in removed_w[0]['items']);assert all(not q['schematic_parity']and len(q['unconnected_items'])==9 for q in drc)
x={'source_sha256':ha,'candidate_sha256':hb,'project_file_count':58,'unchanged_companions':57,'changed_files':changed,'all_retained_serialized_primitives_identical':True,'removed':sorted(removed),'removed_tracks':9,'removed_track_length_mm':length,'removed_vias':1,'retained_holes_identical':True,'fresh_native_counts':[[len(q['violations']),len(q['unconnected_items']),len(q['schematic_parity'])]for q in drc],'removed_warning':removed_w,'manifests':man};(D/'qa/identity-scope.json').write_text(json.dumps(x,indent=2));print({k:v for k,v in x.items()if k!='manifests'})
