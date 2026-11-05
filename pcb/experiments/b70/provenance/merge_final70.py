from pathlib import Path
import os,json,hashlib,shutil
for k in ['KICAD_CONFIG_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME']:os.environ[k]='/tmp/maru-b2l-native'
import pcbnew as p
D=Path(__file__).parent;src=D/'checkpoint-corridor-075.kicad_pcb';dst=D/'checkpoint-shorttree-070.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();ph=sha(src.with_suffix('.kicad_pro'))
for ext in ['.kicad_pcb','.kicad_pro','.kicad_sch']:shutil.copyfile(src.with_suffix(ext),dst.with_suffix(ext))
b=p.LoadBoard(str(dst));assert sha(dst.with_suffix('.kicad_pro'))==ph
for netname in ['COL5','COL6']:
 j=json.load(open(D/('local-'+netname+'.json')));net=b.FindNet(netname).GetNetCode()
 for q in (j['segments'][6:11] if netname=='COL6' else j['segments']):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(x)for x in q['start']]));t.SetEnd(p.VECTOR2I(*[p.FromMM(x)for x in q['end']]));t.SetWidth(p.FromMM(q['width_mm']));t.SetLayer(b.GetLayerID(q['layer']));t.SetNetCode(net);b.Add(t)
 for q in j['vias']:
  t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*[p.FromMM(x)for x in q['at']]));t.SetWidth(p.F_Cu,p.FromMM(q['diameter_mm']));t.SetWidth(p.B_Cu,p.FromMM(q['diameter_mm']));t.SetDrill(p.FromMM(q['drill_mm']));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNetCode(net);b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dst),b);assert sha(dst.with_suffix('.kicad_pro'))==ph;print(sha(dst))
