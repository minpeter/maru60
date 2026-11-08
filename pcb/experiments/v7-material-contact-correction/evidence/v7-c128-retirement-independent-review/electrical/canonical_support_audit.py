from pathlib import Path
import os,json,hashlib,collections
O=Path('/tmp/v7-c128-retirement-independent-review/electrical');os.environ['XDG_CONFIG_HOME']=str(O/'runtime/config')
import pcbnew as p
D=Path('/tmp/v7-c128-stub-retirement-aead');g=json.load(open(D/'qa/candidate-physical-graph.json'));b=p.LoadBoard(str(D/'filled/pcb/maru60.kicad_pcb'));idx={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];cache={}
def poly(sh,out=False):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);return z
def cu(u,l):
 key=u,l
 if key not in cache:
  q=idx[u];z=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),True))
  cache[key]=z
 return cache[key]
def support(a,c):
 out=[]
 for l in layers:
  if idx[a].IsOnLayer(l)and idx[c].IsOnLayer(l):
   t=p.SHAPE_POLY_SET();t.BooleanIntersection(cu(a,l),cu(c,l));ar=t.Area()/1e12
   if ar>0:out.append([b.GetLayerName(l),ar])
 return out
wrong=[];lost=[];corrected=[]
for a,c,saved in g['direct_edges']:
 native=support(a,c);corrected.append([a,c,native])
 if native!=saved:wrong.append(dict(a=a,b=c,saved=saved,actual=native,types=[idx[a].GetClass(),idx[c].GetClass()]))
 if not native:lost.append([a,c,saved])
reject=[]
for a,c in g['native_pairs_without_positive_copper']:
 native=support(a,c)
 if native:reject.append([a,c,native])
# Explicit runtime-type test of cn.GetConnectedTracks neighbor for the independently discovered failing edge.
b.BuildConnectivity();q=idx['cdcdaf62-0d7e-520a-9821-934ef8e04931'];neighbor=next(x for x in b.GetConnectivity().GetConnectedTracks(q)if x.m_Uuid.AsString()=='2a8005ba-8cc3-5ec3-bf91-40e20122da23')
r=dict(input_board_sha256=hashlib.sha256((D/'filled/pcb/maru60.kicad_pcb').read_bytes()).hexdigest(),checked_saved_direct_edges=len(corrected),wrong_support_count=len(wrong),lost_positive_edges=lost,saved_rejects_with_positive_support=reject,wrong_support_edges=wrong,wrapper_type_probe=dict(native_class=neighbor.GetClass(),python_class=type(neighbor).__name__,is_PCB_VIA=isinstance(neighbor,p.PCB_VIA),has_hole=neighbor.HasHole(),canonical_python_class=type(idx[neighbor.m_Uuid.AsString()]).__name__),scope='Recompute support only on existing saved edge lists and rejection list; no new neighbor-pair discovery or full graph export. All native objects resolved by UUID to canonical board inventory before shape tests.')
(O/'canonical-direct-support-audit.json').write_text(json.dumps(r,indent=2));(O/'canonical-direct-edges.json').write_text(json.dumps(corrected,indent=2));print(json.dumps({k:v for k,v in r.items()if k!='wrong_support_edges'},indent=2))
