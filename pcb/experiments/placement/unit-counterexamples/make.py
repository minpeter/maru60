import os,json,shutil,subprocess
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-placement-config';os.environ['XDG_CONFIG_HOME']='/tmp/maru-placement-config'
import pcbnew as p
root=Path(__file__).parent
V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
keep=[]
for name in ['via_touching','plane_center','plane_pad_offcenter','plane_via_offcenter']:
 d=root/name;d.mkdir(exist_ok=True);b=p.BOARD();keep.append(b);b.SetCopperLayerCount(4)
 net=p.NETINFO_ITEM(b,'GND',1);b.Add(net)
 for a,z in [((0,0),(20,0)),((20,0),(20,20)),((20,20),(0,20)),((0,20),(0,0))]:
  s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
 def pad(ref,x,y):
  f=p.FOOTPRINT(b);f.SetReference(ref);f.SetValue('unit_test');b.Add(f);f.SetPosition(V(x,y));q=p.PAD(f);q.SetNumber('1');q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_RECT);q.SetSize(V(.8,.8));ls=p.LSET();ls.AddLayer(p.F_Cu);q.SetLayerSet(ls);q.SetPosition(V(x,y));q.SetNet(net);f.Add(q);keep.extend([f,q]);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 def via(x,y):
  v=p.PCB_VIA(b);v.SetPosition(V(x,y));v.SetWidth(p.F_Cu,p.FromMM(.6));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);v.SetLocked(True);b.Add(v);keep.append(v)
 def track(a,z):
  t=p.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetNet(net);t.SetLocked(True);b.Add(t);keep.append(t)
 if name=='via_touching':
  pad('J1',5,10);pad('J2',15,10);via(10,10);via(10.6,10);track((5,10),(10,10));track((10,10),(10.6,10));track((10.6,10),(15,10))
 else:
  pad('J1',5,5);pad('J2',15,5);via(6,5);via(14,5)
  dp=.2 if name=='plane_pad_offcenter' else 0;dv=.1 if name=='plane_via_offcenter' else 0
  track((5+dp,5),(6-dv,5));track((14,5),(15,5))
  z=p.ZONE(b);z.SetLayer(p.In1_Cu);z.SetNet(net);z.SetLocalClearance(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.1));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_NEVER);o=z.Outline();o.NewOutline()
  for x,y in [(1,1),(19,1),(19,19),(1,19)]:o.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z);keep.append(z)
 path=d/'input.kicad_pcb';shutil.copyfile('/workspace/shared/maru60-placement-lab/frozen.kicad_pro',path.with_suffix('.kicad_pro'))
 p.SaveBoard(str(path),b);b=p.LoadBoard(str(path));keep.append(b);filler=p.ZONE_FILLER(b);keep.append(filler);filler.Fill(b.Zones());b.GetConnectivity().Build(b);p.SaveBoard(str(path),b)
 print(name,'native opens',b.GetConnectivity().GetUnconnectedCount(False),flush=True)
 # reload project-backed board to export exact original process rules
 bb=p.LoadBoard(str(path));keep.append(bb);assert p.ExportSpecctraDSN(bb,str(d/'input.dsn'))
 shutil.copyfile('/workspace/shared/maru60-placement-lab/frozen.kicad_pro',path.with_suffix('.kicad_pro'))
 raw=(d/'input.dsn').read_text().replace('(clearance 200)','(clearance 150)').replace('(clearance 50 (type smd_smd))','(clearance 37.5 (type smd_smd))');(d/'input.dsn').write_text(raw)
 subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','-o',str(d/'native-drc.json'),str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 j=json.loads((d/'native-drc.json').read_text());(d/'native-summary.json').write_text(json.dumps({'opens':len(j['unconnected_items']),'violations':[{'type':v['type'],'severity':v['severity']}for v in j['violations']]},indent=2))
 if name=='via_touching':
  dd=root/'via_touching_attach_on';dd.mkdir(exist_ok=True);(dd/'input.dsn').write_text((d/'input.dsn').read_text().replace('(attach off)','(attach on)'))
