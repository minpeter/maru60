"""Freshly rebuilt native actual-ink scene. Not a restored historical checker or acceptance harness."""
import sys,os,json,hashlib,collections
from pathlib import Path
sys.dont_write_bytecode=True
if not __debug__ or sys.flags.optimize:raise RuntimeError('Optimized evidence execution forbidden')
import pcbnew as p
UID=lambda x:x.m_Uuid.AsString()
XY=lambda v:[v.x,v.y]
SHA=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def typo(x):return {'uuid':UID(x),'text':x.GetText(),'position_nm':XY(x.GetPosition()),'size_nm':[x.GetTextWidth(),x.GetTextHeight()],'stroke_nm':x.GetTextThickness(),'angle_deg':x.GetTextAngle().AsDegrees(),'visible':x.IsVisible(),'mirrored':x.IsMirrored(),'layer':x.GetLayerName(),'bold':x.IsBold(),'italic':x.IsItalic()}
def info(x,ref=None):
 r={'uuid':UID(x),'class':x.GetClass(),'layer':x.GetLayerName(),'position_nm':XY(x.GetPosition())}
 if ref:r['reference']=ref
 if isinstance(x,p.PAD):r.update(pad=x.GetNumber(),net=x.GetNetname())
 return r
def effective(x):return x.GetEffectiveTextShape()if isinstance(x,(p.PCB_TEXT,p.PCB_FIELD))else x.GetEffectiveShape()
def poly(shape,outside=False):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE if outside else p.ERROR_INSIDE);return q
def filled(points):
 c=p.SHAPE_LINE_CHAIN()
 for x,y in points:c.Append(x,y)
 c.SetClosed(True);q=p.SHAPE_POLY_SET();q.AddOutline(c);return q
def nearby(shape,objects,clear):
 b=shape.BBox();b.Inflate(clear)
 return [(i,s)for i,s in objects if b.Intersects(s.BBox())]
def hits(shape,objects,clear=0):return [i for i,s in nearby(shape,objects,clear)if shape.Collide(s,clear)]
def gap(shape,objects,cap=10000000):
 best=cap;chosen=None;partner=None
 for i,s in nearby(shape,objects,best):
  if not shape.Collide(s,best):continue
  lo=0;hi=best
  if shape.Collide(s,0):hi=0
  else:
   while hi-lo>1:
    mid=(hi+lo)//2
    if shape.Collide(s,mid):hi=mid
    else:lo=mid
  if chosen is None or hi<best:best=hi;chosen=s;partner=i
 if chosen is not None:require(shape.Collide(chosen,best)and(best==0 or not shape.Collide(chosen,best-1)),'Invalid collision bracket')
 return {'lower_bound_nm':best-1 if chosen is not None and best>0 else cap if chosen is None else None,'upper_bound_nm':best if chosen is not None else None,'lower_noncollision_verified':chosen is None or best>0,'upper_collision_verified':chosen is not None,'capped_lower_bound':chosen is None,'cap_nm':cap,'partner':partner}
class Scene:
 def __init__(self,path):
  self.path=Path(path);self.before=SHA(path);self.homes={k:os.environ[k]for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']};hs=[Path(x)for x in self.homes.values()];require(len(set(hs))==5 and len(set(x.parent for x in hs))==1 and all(x.is_dir()and x.stat().st_mode&0o077==0 for x in hs),'Five private0700 XDG homes required');self.board=p.LoadBoard(str(path));require(p.GetBuildVersion()=='9.0.2+dfsg-1','KiCad9.0.2 required');self.fps={fp.GetReference():fp for fp in self.board.GetFootprints()};self.fields={r:fp.Reference()for r,fp in self.fps.items()};self.build()
 def build(self):
  b=self.board;side={p.F_SilkS:(p.F_Cu,p.F_Mask,p.F_CrtYd,p.F_Fab),p.B_SilkS:(p.B_Cu,p.B_Mask,p.B_CrtYd,p.B_Fab)};self.buckets={sl:{k:[]for k in ['silk','mask','courtyard','fab','unreconstructed_fab']}for sl in side};self.apertures=[];self.fab_inventory=[]
  graphics=[(x,None)for x in b.GetDrawings()]+[(x,r)for r,fp in self.fps.items()for x in list(fp.GraphicalItems())+list(fp.GetFields())];dedup={UID(x):(x,r)for x,r in graphics};self.edges=[]
  for x,r in dedup.values():
   layer=x.GetLayer()
   if layer in side and(not hasattr(x,'IsVisible')or x.IsVisible()):self.buckets[layer]['silk'].append((info(x,r),effective(x)))
   if layer in[p.F_Mask,p.B_Mask]:
    require(isinstance(x,(p.PCB_SHAPE,p.PCB_TEXT,p.PCB_FIELD))and(not hasattr(x,'IsVisible')or x.IsVisible()),'Unsupported/invisible mask primitive')
    sl=p.F_SilkS if layer==p.F_Mask else p.B_SilkS;m=info(x,r);m.update(source='mask_graphic_or_field',mask_layer=b.GetLayerName(layer));self.apertures.append(m);self.buckets[sl]['mask'].append((m,effective(x)))
   if layer==p.Edge_Cuts:self.edges.append((info(x,r),effective(x)))
  zones=[(z,None)for z in b.Zones()]+[(z,r)for r,fp in self.fps.items()for z in fp.Zones()];self.mask_silk_zones=[]
  for z,r in zones:
   for layer in[p.F_Mask,p.B_Mask,p.F_SilkS,p.B_SilkS]:
    if z.IsOnLayer(layer):self.mask_silk_zones.append(dict(info(z,r),tested_layer=b.GetLayerName(layer)))
  require(not self.mask_silk_zones,'Encountered mask/silk zone: fail closed until geometry reviewed')
  for x in list(b.GetTracks())+[pad for fp in self.fps.values()for pad in fp.Pads()]:
   for sl,(cu,ma,cy,fa)in side.items():
    if isinstance(x,p.PAD):
     if not x.IsOnLayer(ma):continue
     require(x.IsOnLayer(cu),'Unsupported mask-only pad without corresponding copper')
     expansion=x.GetSolderMaskExpansion(ma);ref=x.GetParentFootprint().GetReference();kind='pad'
    elif isinstance(x,p.PCB_VIA):
     if not x.IsOnLayer(cu)or x.IsTented(ma):continue
     expansion=x.GetSolderMaskExpansion();ref=None;kind='untented_via'
    else:
     if not x.IsOnLayer(cu)or not x.HasSolderMask():continue
     expansion=x.GetSolderMaskExpansion();ref=None;kind='exposed_track_or_arc'
    m=info(x,ref);m.update(source=kind,mask_layer=b.GetLayerName(ma),copper_layer=b.GetLayerName(cu),expansion_nm=expansion);q=poly(x.GetEffectiveShape(cu),True)
    if expansion:q.Inflate(expansion,1,p.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS)
    self.apertures.append(m);self.buckets[sl]['mask'].append((m,q))
  for r,fp in self.fps.items():
   fp.BuildCourtyardCaches()
   for sl,(cu,ma,cy,fa)in side.items():
    bk=self.buckets[sl];q=fp.GetCourtyard(cy)
    if q.OutlineCount():bk['courtyard'].append((info(fp,r),p.SHAPE_POLY_SET(q)))
    shapes=[x for x in fp.GraphicalItems()if x.GetLayer()==fa and isinstance(x,p.PCB_SHAPE)];edges=[];closed=[];other=[]
    for x in shapes:
     t=x.GetShape()
     if t==p.SHAPE_T_RECT:closed.append(filled([XY(v)for v in x.GetRectCorners()]))
     elif t==p.SHAPE_T_POLY:closed.append(p.SHAPE_POLY_SET(x.GetPolyShape()))
     elif t==p.SHAPE_T_SEGMENT:edges.append((tuple(XY(x.GetStart())),tuple(XY(x.GetEnd())),x))
     else:other.append(x)
    remaining=set(range(len(edges)));open_components=0
    while remaining:
     start=next(iter(remaining));component={start};points=set(edges[start][:2]);changed=True
     while changed:
      changed=False
      for k in remaining-component:
       a,c,x=edges[k]
       if a in points or c in points:component.add(k);points.update([a,c]);changed=True
     remaining-=component;adj=collections.defaultdict(list)
     for k in component:a,c,x=edges[k];adj[a].append(c);adj[c].append(a)
     if len(points)<3 or any(len(v)!=2 for v in adj.values()):open_components+=1;other.extend(edges[k][2]for k in component);continue
     first=min(points);ordered=[first];prev=None;cur=first
     while True:
      ns=adj[cur];nxt=ns[0]if ns[0]!=prev else ns[1]
      if nxt==first:break
      ordered.append(nxt);prev,cur=cur,nxt;require(len(ordered)<=len(points),'Invalid Fab traversal')
     require(len(ordered)==len(points),'Incomplete Fab contour');closed.append(filled(ordered))
    for q in closed:bk['fab'].append(({'uuid':UID(fp),'reference':r,'layer':b.GetLayerName(fa)},q))
    for x in other:bk['unreconstructed_fab'].append((info(x,r),effective(x)))
    if shapes:self.fab_inventory.append({'reference':r,'layer':b.GetLayerName(fa),'closed_contours':len(closed),'open_components':open_components,'other_shape_count':sum(x.GetShape()!=p.SHAPE_T_SEGMENT for x in other)})
  self.outline=p.SHAPE_POLY_SET();require(b.GetBoardPolygonOutlines(self.outline),'Closed board outline')
 def measure_shape(self,shape,sl,exclude=()):
  bk=self.buckets[sl];out={}
  for name,objects in list(bk.items())+[('edge',self.edges)]:
   if name=='silk':objects=[(i,s)for i,s in objects if i['uuid']not in exclude]
   out[name+'_intersections']=hits(shape,objects);out[name+'_gap']=gap(shape,objects);out[name+'_target_pass']=not hits(shape,objects,250000 if name=='edge'else 150000)
  q=poly(shape);q.BooleanSubtract(self.outline);out['whole_ink_inside_board']=q.Area()==0;return out
 def measure_ref(self,ref):
  x=self.fields[ref];return {'reference':ref,'typography':typo(x),'footprint_center_nm':XY(self.fps[ref].GetPosition()),'geometry':self.measure_shape(effective(x),x.GetLayer(),[UID(x)])}
 def measure_logo(self):
  fp=self.fps['LOGO1'];shapes=[x for x in fp.GraphicalItems()if x.GetLayer()==p.B_SilkS];require(len(shapes)==2 and all(isinstance(x,p.PCB_SHAPE)and x.GetShape()==p.SHAPE_T_POLY for x in shapes),'Two intact back polygons');own=[UID(x)for x in shapes];return {'footprint':info(fp,'LOGO1'),'angle_deg':fp.GetOrientationDegrees(),'polygon_uuids':own,'polygons':[dict(info(x,'LOGO1'),geometry=self.measure_shape(effective(x),p.B_SilkS,own))for x in shapes]}
 def report(self,refs):
  require(SHA(self.path)==self.before,'Source file changed during native read');return {'board_sha256':self.before,'native_board_loads':1,'native_build':p.GetBuildVersion(),'native_pid':os.getpid(),'private_xdg':self.homes,'all382_reference_typography':{r:typo(x)for r,x in sorted(self.fields.items())},'rows':[self.measure_ref(r)for r in refs],'whole_LOGO1':self.measure_logo(),'complete_mask_aperture_inventory':sorted(self.apertures,key=lambda x:(x['mask_layer'],x['source'],x['uuid'])),'mask_source_counts':dict(collections.Counter(x['mask_layer']+'/'+x['source']for x in self.apertures)),'mask_silk_zones':self.mask_silk_zones,'board_zone_count':len(list(self.board.Zones())),'footprint_zone_count':sum(len(list(fp.Zones()))for fp in self.fps.values()),'silk_inventory':{self.board.GetLayerName(sl):[i for i,s in bk['silk']]for sl,bk in self.buckets.items()},'edge_inventory':[i for i,s in self.edges],'Fab_proxy_inventory':self.fab_inventory,'board_file_unchanged':True,'outside_mask_polygonization_error_nm':1,'manufacturing_and_actual_3D_visibility_qualified':False}
if __name__=='__main__':
 scene=Scene(sys.argv[1]);refs=sys.argv[3].split(',');result=scene.report(refs);Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'board_sha256':scene.before,'reference_count':len(refs),'mask_apertures':len(scene.apertures)}))
