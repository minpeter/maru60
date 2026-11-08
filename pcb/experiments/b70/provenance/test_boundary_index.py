from pathlib import Path
import os,json,random,time
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-b2l-native'
import pcbnew as p
import annular_source_hole_safe as slow
import annular_source_indexed as fast
random.seed(70);D=Path(__file__).parent;rows=[]
def poly(points):
 q=p.SHAPE_POLY_SET();q.NewOutline()
 for x,y in points:q.Append(p.FromMM(x),p.FromMM(y))
 return q
for i in range(30):
 x,y=random.randint(-20,20),random.randint(-20,20);w,h=random.randint(1,20),random.randint(1,20);a=poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)]);b=poly([(x+w,y-1),(x+w+3,y-1),(x+w+3,y+h+1),(x+w,y+h+1)])
 if i%3==1:b=a
 if i%3==2:b=poly([(x+1,y+1),(x+w+1,y+1),(x+w+1,y+h+1),(x+1,y+h+1)])
 aa,bb=slow.finite_shared_boundary_mm(a,b),fast.finite_shared_boundary_mm(a,b);assert abs(aa-bb)<1e-12;(rows.append({'case':i,'slow_mm':aa,'indexed_mm':bb}))
b=p.LoadBoard(str(D/'checkpoint-shorttree-070.kicad_pcb'));v=next(t for t in b.GetTracks()if isinstance(t,p.PCB_VIA)and t.GetNetname()=='GND');low,_,_=slow.conductor_polygons(v,p.F_Cu);aa=slow.finite_shared_boundary_mm(low,low);bb=fast.finite_shared_boundary_mm(low,low);assert abs(aa-bb)<1e-12;rows.append({'case':'actual_annular_via_self_boundary','uuid':v.m_Uuid.AsString(),'slow_mm':aa,'indexed_mm':bb})
(D/'boundary-index-equivalence.json').write_text(json.dumps({'pass':True,'scope':'30 exact integer straight-edge/partial-overlap/disjoint cases plus native actual annular via self-boundary. Same hole-preserving polygons; source graph/native guards still independent.','cases':rows},indent=2));print('PASS',len(rows))
