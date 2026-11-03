import os
for k in['KICAD_CONFIG_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME']:os.environ[k]='/tmp/maru-b2l-native'
from pathlib import Path
import pcbnew as p,json,math,hashlib,sys
R=Path(__file__).parent;f=R/(sys.argv[1] if len(sys.argv)>1 else 'corridor-pilot.kicad_pcb');b=p.LoadBoard(str(f));l=json.load(open(R/(sys.argv[2] if len(sys.argv)>2 else 'corridor-pilot-ledger.json')));newids={q['uuid']for q in l['added']if q['role']=='new all-F USB trunk'};zoneids=set(l['new_reference_zones']);refs={};ded=p.SHAPE_POLY_SET()
for layer in[p.F_Cu,p.B_Cu]:
 ps=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!='GND'or not z.IsOnLayer(layer):continue
  ps.BooleanAdd(z.GetFilledPolysList(layer))
  if z.m_Uuid.AsString()in zoneids:ded.BooleanAdd(z.GetFilledPolysList(layer))
 refs[layer]=ps
stats={};missing=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA)or not t.GetNetname().startswith('USB_'):continue
 role='new_trunk'if t.m_Uuid.AsString()in newids else 'retained_escape';key=role+':'+t.GetNetname();s=stats.setdefault(key,{'sample_count':0,'missing':0,'missing_from_explicit_strip':0,'length_mm':0});a,e=t.GetStart(),t.GetEnd();ax,ay=a.x/1e6,a.y/1e6;ex,ey=e.x/1e6,e.y/1e6;L=math.hypot(ex-ax,ey-ay);s['length_mm']+=L;n=max(1,math.ceil(L/.05));nx,ny=(-(ey-ay)/L,(ex-ax)/L)if L else(0,0);width=p.ToMM(t.GetWidth());opp=p.B_Cu if t.GetLayer()==p.F_Cu else p.F_Cu
 for i in range(n+1):
  cx,cy=ax+(ex-ax)*i/n,ay+(ey-ay)*i/n
  for off in[-width/2,0,width/2]:
   x,y=cx+off*nx,cy+off*ny;v=p.VECTOR2I(p.FromMM(x),p.FromMM(y));s['sample_count']+=1
   if not refs[opp].Contains(v):s['missing']+=1;missing.append({'role':role,'net':t.GetNetname(),'track_uuid':t.m_Uuid.AsString(),'at_mm':[x,y]})
   if role=='new_trunk'and not ded.Contains(v):s['missing_from_explicit_strip']+=1
for s in stats.values():s['projected_ground_coverage_fraction']=1-s['missing']/s['sample_count']
r={'board_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'scope':'Every USB track center and width edges sampled≤0.05mm; new trunk separately from preserved connector/core escapes. Filled-GND geometric projection only, not proof polygons belong to a continuous return network or90ohm. Any source/target/transition exceptions are retained explicitly.','stats':stats,'missing_samples':missing,'new_reference_strip_filled_polygons':ded.OutlineCount(),'new_reference_strip_area_mm2':ded.Area()/1e12,'new_reference_zones':[{'uuid':z.m_Uuid.AsString(),'fill_polygons':z.GetFilledPolysList(p.B_Cu).OutlineCount(),'area_mm2':z.GetFilledPolysList(p.B_Cu).Area()/1e12}for z in b.Zones()if z.m_Uuid.AsString()in zoneids]};f.with_suffix('.reference.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k!='missing_samples'},indent=2))
