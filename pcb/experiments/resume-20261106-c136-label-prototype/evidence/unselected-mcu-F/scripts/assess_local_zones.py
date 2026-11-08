import pcbnew as p,json,hashlib
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-led-repair');S=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu/source/pcb/maru60.kicad_pcb');b=p.LoadBoard(str(S));clip=p.SHAPE_POLY_SET();clip.NewOutline()
for x,y in [(109.7,74.7),(111.9,74.7),(111.9,76.8),(109.7,76.8)]:clip.Append(round(x*1e6),round(y*1e6))
rows=[]
for z in b.Zones():
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not z.IsOnLayer(l):continue
  q=p.SHAPE_POLY_SET();q.BooleanIntersection(z.GetFilledPolysList(l),clip)
  if q.Area()>0:rows.append({'uuid':z.m_Uuid.AsString(),'net':z.GetNetname(),'layer':b.GetLayerName(l),'rule_area':z.GetIsRuleArea(),'local_clearance_mm':z.GetLocalClearance()/1e6,'filled_copper_within_inventory_region_mm2':q.Area()/1e12})
j={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'region_mm':[109.7,74.7,111.9,76.8],'zone_copper':rows,'constraint':'Existing F.Cu GND fill is not immutable: proposed F track move requires native refill at zone clearance and full contact checks. Inner GND fill is the actual adjacent reference. No claim that removing local F fill is harmless before validation.'};(R/'qa/read-only-local-zones.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
