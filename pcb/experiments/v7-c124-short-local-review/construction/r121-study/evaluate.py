def bbshape(s):
 q=s.BBox();return [mm(q.GetX()),mm(q.GetY()),mm(q.GetRight()),mm(q.GetBottom())]
def rect(x0,y0,x1,y1):
 s=p.SHAPE_POLY_SET();s.NewOutline()
 for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:s.Append(round(x*1e6),round(y*1e6))
 return s
def sep(a,b,hi=2000000):
 if a.Collide(b,0):return [-1,0]
 if not a.Collide(b,hi):return [hi,None]
 lo=0
 while hi-lo>1:
  mid=(lo+hi)//2
  if a.Collide(b,mid):hi=mid
  else:lo=mid
 return [lo,hi]
allobs=[]
for f,x in localp:
 if f.GetReference() not in ['R121','C124']:allobs.append((f.GetReference()+'.'+x.GetNumber(),x,x.GetEffectiveShape(p.B_Cu)))
for t in localt:
 if t.GetNetname()!='USB_OVLO':allobs.append((uid(t),t,t.GetEffectiveShape(p.B_Cu)))
ps=list(r.Pads()); orig=p.VECTOR2I(r.GetPosition())
original_pads=[(q,p.VECTOR2I(q.GetPosition()),q.GetOrientationDegrees()) for q in ps]
original_shapes=[(s,p.VECTOR2I(s.GetStart()),p.VECTOR2I(s.GetEnd())) for s in r.GraphicalItems() if hasattr(s,'GetStart')]
def pos(dx=0,dy=0,a=90):
 # Restore exact original pad and courtyard primitives before each trial.
 # KiCad repeated incremental rotations otherwise accumulate integer-nm rounding.
 r.SetOrientationDegrees(90);r.SetPosition(orig)
 for q,xy,ang in original_pads:q.SetPosition(xy);q.SetOrientationDegrees(ang)
 for s,st,en in original_shapes:s.SetStart(st);s.SetEnd(en)
 r.SetOrientationDegrees(a);r.SetPosition(p.VECTOR2I(round(14e6+dx*1e6),round(18.5e6+dy*1e6)));r.BuildCourtyardCaches()
def check(details=False):
 ans=[]
 for pad in ps:
  sh=pad.GetEffectiveShape(p.B_Cu)
  for lab,o,shape in allobs:
   if pad.GetNetCode()!=o.GetNetCode() and sh.Collide(shape,150000):
    ans.append([pad.GetNumber(),lab,o.GetNetname(),sep(sh,shape)] if details else [pad.GetNumber(),lab])
 return ans
def contacts():
 ans=[]
 for pad in ps:
  sh=pad.GetEffectiveShape(p.B_Cu)
  for t in localt:
   if sh.Collide(t.GetEffectiveShape(p.B_Cu),0):ans.append([pad.GetNumber(),uid(t),t.GetNetname()])
 return ans
pos();baseline_contacts=contacts();nominal=[]
for pad in ps:
 sh=pad.GetEffectiveShape(p.B_Cu)
 for lab,o,s in allobs:
  if pad.GetNetCode()!=o.GetNetCode():
   d=sep(sh,s,400000)
   if d[1] is not None:nominal.append([pad.GetNumber(),lab,o.GetNetname(),d])
nominal.sort(key=lambda x:x[3][0])
print('NOMINAL nearest',nominal[:15], 'contacts',baseline_contacts,flush=True)
lo=0;hi=200000
while hi-lo>1:
 mid=(lo+hi)//2;pos(-mid/1e6)
 if check():hi=mid
 else:lo=mid
print('SHIFT_BOUND',lo,hi,flush=True)
pos(-lo/1e6);good=check(True);goodcontacts=contacts()
pos(-hi/1e6);bad=check(True)
pos();court_info={}
for f in {f.GetReference():f for f,x in localp}.values():
 c=f.GetCourtyard(p.B_CrtYd);court_info[f.GetReference()]={'bbox':bbshape(c),'outlines':[[vxy(c.COutline(i).CPoint(j)) for j in range(c.COutline(i).PointCount())] for i in range(c.OutlineCount())]}
out={'nominal_nearest_nm':nominal,'pure_left_max_pass_nm':lo,'pure_left_next_fail_nm':hi,'pass_contacts':goodcontacts,'fail_obstacles':bad,'baseline_contacts':baseline_contacts,'courtyards':court_info}
json.dump(out,open(ROOT+'/evaluate.json','w'),indent=2)
print(json.dumps(out,indent=2),flush=True)
