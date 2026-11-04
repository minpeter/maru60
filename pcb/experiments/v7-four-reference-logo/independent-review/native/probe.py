#!/usr/bin/python3
"""Independent fixed-threshold native ink screen. No constructor/fill/save calls."""
import sys,os,hashlib,json,collections,time
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parent.parent/'v7-safe-five-logo-recovered';B=W/'candidate-four/pcb/maru60.kicad_pcb'
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 q=D/'runtime'/k.lower();q.mkdir(parents=True,mode=0o700,exist_ok=False);os.environ[k]=str(q)
import pcbnew as p
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();uid=lambda x:x.m_Uuid.AsString();xy=lambda v:[v.x,v.y]
expected='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
assert H(B)==expected and p.Version()=='9.0.2' and p.GetBuildVersion()=='9.0.2+dfsg-1'
b=p.LoadBoard(str(B));fps={f.GetReference():f for f in b.GetFootprints()};assert len(fps)==382
SL=p.B_SilkS;CU=p.B_Cu;MA=p.B_Mask
FSL=p.F_SilkS
side={p.F_SilkS:(p.F_Cu,p.F_Mask,p.F_CrtYd,p.F_Fab),p.B_SilkS:(p.B_Cu,p.B_Mask,p.B_CrtYd,p.B_Fab)}
mask={sl:[] for sl in side};silk={sl:[] for sl in side};courts={sl:[] for sl in side};fab={sl:[] for sl in side};other={sl:[] for sl in side};edge=[];maskkeys=[];maskcounts=collections.Counter();fabstats=[]
def obj(x,ref=None,kind=None):return {'uuid':uid(x),'reference':ref,'kind':kind,'layer':x.GetLayerName()}
def eff(x):return x.GetEffectiveTextShape() if isinstance(x,(p.PCB_TEXT,p.PCB_FIELD)) else x.GetEffectiveShape()
def outline(shape):
 out=p.SHAPE_POLY_SET();shape.TransformToPolygon(out,1,p.ERROR_OUTSIDE);return out
def closed(points):
 ch=p.SHAPE_LINE_CHAIN()
 for pt in points:ch.Append(p.VECTOR2I(*pt))
 ch.SetClosed(True);out=p.SHAPE_POLY_SET();out.AddOutline(ch);return out
# All explicit board/footprint graphics and all fields, de-duplicated by actual UUID.
graphics={uid(x):(x,None) for x in b.GetDrawings()}
for ref,f in fps.items():
 for x in list(f.GraphicalItems())+list(f.GetFields()):graphics[uid(x)]=(x,ref)
for x,ref in graphics.values():
 if hasattr(x,'IsVisible') and not x.IsVisible():continue
 l=x.GetLayer()
 if l in side:silk[l].append((obj(x,ref,'explicit_silk'),eff(x)))
 if l in (p.F_Mask,p.B_Mask):
  assert isinstance(x,(p.PCB_SHAPE,p.PCB_TEXT,p.PCB_FIELD));sl=p.F_SilkS if l==p.F_Mask else p.B_SilkS
  mask[sl].append((obj(x,ref,'mask_graphic_or_field'),eff(x)));maskkeys.append((b.GetLayerName(l),'mask_graphic_or_field',uid(x)));maskcounts[b.GetLayerName(l)+'/mask_graphic_or_field']+=1
 if l==p.Edge_Cuts:edge.append((obj(x,ref,'edge'),eff(x)))
for z in list(b.Zones())+[z for f in fps.values() for z in f.Zones()]:
 assert not any(z.IsOnLayer(l) for l in (p.F_Mask,p.B_Mask,p.F_SilkS,p.B_SilkS)),'Unreviewed mask/silk zone'
for x in list(b.GetTracks())+[x for f in fps.values() for x in f.Pads()]:
 for sl,(cu,ma,cy,fa) in side.items():
  if isinstance(x,p.PAD):
   if not x.IsOnLayer(ma):continue
   assert x.IsOnLayer(cu),'Mask-only pad requires explicit shape treatment';exp=x.GetSolderMaskExpansion(ma);ref=x.GetParentFootprint().GetReference();kind='pad'
  elif isinstance(x,p.PCB_VIA):
   if not x.IsOnLayer(cu) or x.IsTented(ma):continue
   exp=x.GetSolderMaskExpansion();ref=None;kind='untented_via'
  else:
   if not x.IsOnLayer(cu) or not x.HasSolderMask():continue
   exp=x.GetSolderMaskExpansion();ref=None;kind='exposed_track_or_arc'
  shape=outline(x.GetEffectiveShape(cu))
  if exp:shape.Inflate(exp,1,p.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS)
  mask[sl].append((obj(x,ref,kind),shape));maskkeys.append((b.GetLayerName(ma),kind,uid(x)));maskcounts[b.GetLayerName(ma)+'/'+kind]+=1
assert len(maskkeys)==1759 and len(set(maskkeys))==1759
for ref,f in fps.items():
 f.BuildCourtyardCaches()
 for sl,(cu,ma,cy,fa) in side.items():
  q=f.GetCourtyard(cy)
  if q.OutlineCount():courts[sl].append((obj(f,ref,'courtyard'),p.SHAPE_POLY_SET(q)))
  segs=[];closed_count=0;unsupported=0
  for x in f.GraphicalItems():
   if x.GetLayer()!=fa or not isinstance(x,p.PCB_SHAPE):continue
   if x.GetShape()==p.SHAPE_T_RECT:q=closed([xy(v) for v in x.GetRectCorners()])
   elif x.GetShape()==p.SHAPE_T_POLY:q=p.SHAPE_POLY_SET(x.GetPolyShape())
   elif x.GetShape()==p.SHAPE_T_SEGMENT:segs.append((tuple(xy(x.GetStart())),tuple(xy(x.GetEnd())),x));continue
   else:other[sl].append((obj(x,ref,'unreconstructed_fab'),eff(x)));unsupported+=1;continue
   fab[sl].append((obj(f,ref,'closed_fab'),q));closed_count+=1
  # Independent connected-component degree-2 loop construction for Fab line body proxies.
  adjacency=collections.defaultdict(list)
  for i,(a,z,x) in enumerate(segs):adjacency[a].append((z,i));adjacency[z].append((a,i))
  remain=set(range(len(segs)))
  while remain:
   first=min(remain);todo=[segs[first][0]];points=set();component=set()
   while todo:
    a=todo.pop()
    if a in points:continue
    points.add(a)
    for z,i in adjacency[a]:component.add(i);todo.append(z)
   remain-=component
   if len(points)<3 or any(len(adjacency[a])!=2 for a in points):
    for i in component:other[sl].append((obj(segs[i][2],ref,'open_fab'),eff(segs[i][2])))
    unsupported+=len(component);continue
   firstpoint=min(points);sequence=[firstpoint];previous=None;cur=firstpoint
   while True:
    candidates=[z for z,i in adjacency[cur] if z!=previous];assert candidates
    nxt=candidates[0]
    if nxt==firstpoint:break
    assert nxt not in sequence;sequence.append(nxt);previous,cur=cur,nxt
   assert len(sequence)==len(points)
   fab[sl].append((obj(f,ref,'closed_fab'),closed(sequence)));closed_count+=1
  if closed_count or unsupported:fabstats.append({'reference':ref,'side':b.GetLayerName(sl),'closed_contours':closed_count,'unreconstructed_primitives':unsupported})
boardoutline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(boardoutline)
def hit(shape,inventory,clear,exclude=()):
 bb=shape.BBox();bb.Inflate(clear);ans=[]
 for meta,s in inventory:
  if meta['uuid'] in exclude:continue
  if bb.Intersects(s.BBox()) and shape.Collide(s,clear):ans.append(meta)
 return ans
prior='R120 R144 J3 D100 R124 C142 C141 R163 C137 C126 C129 U2 R126 U10 C101'.split();changed=['C100','R140','R160','R134'];targets=[]
for ref in changed+prior:
 x=fps[ref].Reference();targets.append((ref,uid(x),x.GetLayer(),eff(x),[uid(x)],ref in changed))
logo=fps['LOGO1'];parts=[x for x in logo.GraphicalItems() if x.GetLayer()==SL];assert len(parts)==2 and all(x.GetShape()==p.SHAPE_T_POLY for x in parts)
for x in parts:targets.append(('LOGO1',uid(x),SL,eff(x),[uid(q) for q in parts],True))
rows=[]
for ref,u,sl,shape,exclude,strict in targets:
 categories={'mask':mask[sl],'silk':silk[sl],'edge':edge,'courtyard':courts[sl],'closed_fab':fab[sl],'unreconstructed_fab':other[sl]};r={'reference':ref,'uuid':u,'threshold_hits':{}}
 for name,inv in categories.items():
  clearance=250000 if name=='edge' else 150000 if strict or name in ('mask','silk') else 0
  hits=hit(shape,inv,clearance,exclude if name=='silk' else [])
  r['threshold_hits'][name]={'clearance_nm':clearance,'hits':hits}
 q=outline(shape);q.BooleanSubtract(boardoutline);r['outside_board_area_nm2']=q.Area();r['pass']=r['outside_board_area_nm2']==0 and not any(v['hits'] for v in r['threshold_hits'].values());rows.append(r)
 assert r['pass'],r
producer=json.loads((W/'qa/candidate-four-ink.json').read_text());prodkeys=sorted((q['mask_layer'],q['source'],q['uuid']) for q in producer['complete_mask_aperture_inventory']);assert sorted(maskkeys)==prodkeys
assert H(B)==expected
report={'pass':True,'candidate_sha256':expected,'checker_sha256':H(Path(__file__)),'native_version':p.Version(),'native_build':p.GetBuildVersion(),'native_pid':os.getpid(),'one_native_board_load':True,'no_CAD_save_fill_or_mutation':True,'complete_mask_aperture_count':len(maskkeys),'complete_mask_source_keys_match_producer':True,'mask_source_counts':dict(maskcounts),'targets':rows,'thresholds':{'changed_four_and_logo_mask_silk_courtyard_closedFab_unreconstructedFab_nm':150000,'boardedge_nm':250000,'prior15_mask_silk_nm':150000,'prior15_courtyard_Fab_required_no_intersection_only':True},'all_target_ink_conservatively_outside_polygonized_1nm_and_inside_board':True,'source_file_unchanged':True,'manufacturer_mechanical_3D_hardware_qualified':False,'full_adversarial_acceptance_replay_performed':False,'private_homes':{k:os.environ[k] for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']},'Fab_proxy_inventory':fabstats}
(D/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('pass','candidate_sha256','native_build','complete_mask_aperture_count')},indent=2))
