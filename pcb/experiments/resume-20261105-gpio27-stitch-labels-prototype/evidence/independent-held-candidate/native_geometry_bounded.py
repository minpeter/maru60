import pcbnew as p,json
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27'
paths={'base':R.parent/'combined-trial/pcb/maru60.kicad_pcb','header':R/'header/trial27/pcb/maru60.kicad_pcb','combined':R/'combined27/pcb/maru60.kicad_pcb'}
def polygon(shape,err=p.ERROR_OUTSIDE):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,err);q.Simplify();return q
def minus(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def both(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[pad for f in b.GetFootprints() for pad in f.Pads()];holes=p.SHAPE_POLY_SET()
 for x in items:
  if isinstance(x,(p.PCB_VIA,p.PAD)) and x.HasHole():holes.Append(polygon(x.GetEffectiveHoleShape()))
 holes.Simplify();planes={}
 for l in [p.In1_Cu,p.In2_Cu]:
  q=p.SHAPE_POLY_SET()
  for z in b.Zones():
   if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l):q.BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
  planes[l]=minus(q,holes)
 return b,{x.m_Uuid.AsString():x for x in items},holes,planes
D={k:capture(v) for k,v in paths.items()};stitch='efdf2c37-5653-4018-9cc8-dfb15999bb91';drill=polygon(D['combined'][1][stitch].GetEffectiveHoleShape());planes=[]
for l in [p.In1_Cu,p.In2_Cu]:
 old,header,new=[D[k][3][l] for k in ['base','header','combined']];loss=minus(old,new);gain=minus(new,old);addedloss=minus(header,new);expected=both(drill,header);extra=minus(addedloss,expected);missing=minus(expected,addedloss);assert extra.OutlineCount()==missing.OutlineCount()==0;assert minus(new,header).OutlineCount()==0
 hits=[]
 for u,x in D['header'][1].items():
  if x.GetNetname() in ('','GND') or not x.GetBoundingBox().Intersects(addedloss.BBox()):continue
  for sl in [p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2) if isinstance(x,p.PCB_VIA) else x.GetEffectiveShape(sl)
   q=both(addedloss,minus(polygon(shape),D['header'][2]));
   if q.OutlineCount():hits.append({'uuid':u,'layer':sl,'area':q.Area()/1e12})
 assert not hits
 planes.append({'plane':D['combined'][0].GetLayerName(l),'base_to_combined_loss_mm2':loss.Area()/1e12,'base_to_combined_gain_mm2':gain.Area()/1e12,'header_to_combined_loss_mm2':addedloss.Area()/1e12,'loss_exactly_expected_stitch_drill':True,'old_signal_shadow_losses_from_stitch':hits,'components':[old.OutlineCount(),header.OutlineCount(),new.OutlineCount()]})
# Native contact patches for the deliberately rerouted GPIO10 segment.
oldid='fdd2376a-e263-51cf-8638-7d8989c5ffc8';last='b3bc6543-bd14-4b17-a59c-2b4bbc878cc5';targets=['2e9d2717-15e1-4bce-856d-b881bc5f3e3b','b90cbf74-89de-49fa-ac51-d43df3605713','2bd88f35-bab5-4803-8710-df5ee50545de','cd5fb524-ab04-563a-a15b-b61178f9c51e'];contacts=[]
def copper(k,u):return minus(polygon(D[k][1][u].GetEffectiveShape(p.B_Cu),p.ERROR_INSIDE),D[k][2])
for t in targets:
 replacement=oldid if t==targets[-1] else last;a=both(copper('base',oldid),copper('base',t));b=both(copper('combined',replacement),copper('combined',t));loss=minus(a,b);gain=minus(b,a)
 contacts.append({'target':t,'replacement':replacement,'before_mm2':a.Area()/1e12,'after_mm2':b.Area()/1e12,'lost_mm2':loss.Area()/1e12,'lost_outlines':loss.OutlineCount(),'gain_mm2':gain.Area()/1e12})
 if t!=targets[-1]:assert loss.OutlineCount()==gain.OutlineCount()==0
out={'native_version':p.GetBuildVersion(),'planes':planes,'GPIO10_contact_patches':contacts};(O/'native-geometry.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
