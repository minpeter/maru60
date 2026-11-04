import os,pathlib,hashlib,json,time,sys
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
A=pathlib.Path('/tmp/v7-buck-deadarm-trial-2c7e/source/pcb/maru60.kicad_pcb');B=D/'pcb/maru60.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(B);assert before==sha(A)=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373';b=p.LoadBoard(str(B));b.BuildConnectivity();start=time.monotonic();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(B),b);a=p.LoadBoard(str(A));out=[]
def dump(ps):
 def ring(r):return[[r.CPoint(i).x,r.CPoint(i).y]for i in range(r.PointCount())]
 return[dict(outline=ring(ps.COutline(i)),holes=[ring(ps.CHole(i,j))for j in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())]
for z in a.Zones():
 q=next(q for q in b.Zones()if q.m_Uuid.AsString()==z.m_Uuid.AsString())
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not z.IsOnLayer(l):continue
  x=z.GetFilledPolysList(l);y=q.GetFilledPolysList(l);loss=p.SHAPE_POLY_SET(x);loss.BooleanSubtract(y);gain=p.SHAPE_POLY_SET(y);gain.BooleanSubtract(x);out.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),layer=a.GetLayerName(l),raw_native_vertices_identical=dump(x)==dump(y),loss_mm2=loss.Area()/1e12,gain_mm2=gain.Area()/1e12,loss=dump(loss),gain=dump(gain)))
sys.path.insert(0,'/tmp/v7-buck-deadarm-trial-2c7e/tools');from sexpr_spans import children,head
sourcecanon=pathlib.Path('/tmp/v7-buck-deadarm-trial-2c7e/qa/source-canonical.kicad_pcb').read_text();same=[t for _,_,t in children(sourcecanon)if head(t)!='zone']==[t for _,_,t in children(B.read_text())if head(t)!='zone'];assert same;r=dict(source_sha256=before,noedit_normal_refill_sha256=sha(B),canonical_nonzone_nodes_exact=True,native_seconds=time.monotonic()-start,zone_controls=out,interpretation='No-electrical-edit normal-refill control only. It cannot waive any observed strict source-to-candidate plane loss. Source and BUCK candidate snapshots unchanged.');(D/'RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps([{k:v for k,v in x.items()if k not in ['loss','gain']}for x in out],indent=2));assert sha(A)==before
