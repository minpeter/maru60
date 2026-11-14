import pcbnew as p,sys,json
path=sys.argv[1];b=p.LoadBoard(path)
created=[]
for layer,bounds in [('In1.Cu',(10,30,27,39)),('In2.Cu',(10,30,27,39)),('In2.Cu',(15,3,25,13))]:
 proto=next(z for z in b.Zones() if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(b.GetLayerID(layer)))
 z=proto.Duplicate(); z.SetAssignedPriority(2); z.SetMinThickness(p.FromMM(.2));z.SetZoneName('critical_return_'+layer+'_'+str(bounds[1]));z.UnFill()
 outline=z.Outline();outline.RemoveAllContours();outline.NewOutline();x1,y1,x2,y2=bounds
 for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:outline.Append(p.VECTOR2I(round(x*1e6),round(y*1e6)))
 b.Add(z);created.append(dict(uuid=z.m_Uuid.AsString(),layer=layer,bounds=bounds,min_thickness_mm=.2,priority=2))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(path,b);print(json.dumps(created,indent=2))
