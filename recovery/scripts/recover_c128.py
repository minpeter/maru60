from pathlib import Path
import json,hashlib,os,sys,re
base=Path(__file__).resolve().parent;run=base/('native-c128-'+sys.argv[1]);run.mkdir(exist_ok=True)
for k in ['HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR']:
 p=run/k;p.mkdir(mode=0o700,exist_ok=True);os.environ[k]=str(p)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import pcbnew as p
src=base/'u10-label-accepted400fd.kicad_pcb';assert hashlib.sha256(src.read_bytes()).hexdigest()=='400fd2641ebd3208315359acf295ee630dab8d3319a6d990ea7ab8d558961fa2'
uuid_map={};b=p.LoadBoard(str(src));f=next(f for f in b.GetFootprints()if f.GetReference()=='C128');f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT if sys.argv[1]=='LR'else p.FLIP_DIRECTION_TOP_BOTTOM);f.SetPosition(p.VECTOR2I(p.FromMM(113),p.FromMM(36.025)));f.SetOrientationDegrees(180)
r=f.Reference();r.SetPosition(p.VECTOR2I(p.FromMM(111.2),p.FromMM(37.5)));r.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));r.SetTextThickness(p.FromMM(.1));r.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));r.SetMirrored(False)
for uid,net,a,z in [('b0cc9de1-aec9-5121-a294-6107a6342d33','+3V3',(113.775,36.025),(110.45,33.4375)),('99335a61-c21f-59c4-876b-507f6433e7c6','GND',(112.225,36.025),(111.646017,36.003416))]:
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*(p.FromMM(v)for v in a)));t.SetEnd(p.VECTOR2I(*(p.FromMM(v)for v in z)));t.SetWidth(p.FromMM(.3));t.SetLayer(p.F_Cu);t.SetNetCode(b.FindNet(net).GetNetCode());uuid_map[t.m_Uuid.AsString()]=uid;b.Add(t)
v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(111.346017),p.FromMM(36.003416)));v.SetWidth(p.F_Cu,p.FromMM(.5));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(b.FindNet('GND').GetNetCode());uuid_map[v.m_Uuid.AsString()]='74838ec4-2a2a-5ebb-82d1-e1c3369351cd';b.Add(v)
out=run/'reconstructed.kicad_pcb';p.SaveBoard(str(out),b)
s=out.read_text()
for old,new in uuid_map.items():s=s.replace(old,new)
pat=r'\n\t\((?:segment|via)\n.*?\n\t\)';blocks=list(re.finditer(pat,s,re.S));assert all(blocks[i].end()==blocks[i+1].start()for i in range(len(blocks)-1))
def key(m):
 text=m.group();net=int(re.search(r'\(net (\d+)\)',text).group(1));layer=1 if text.startswith('\n\t(via')else{'F.Cu':0,'B.Cu':2,'In1.Cu':4,'In2.Cu':6}[re.search(r'\(layer "([^"]+)"',text).group(1)];uid=re.search(r'\(uuid "([^"]+)"',text).group(1);return net,layer,uid
s=s[:blocks[0].start()]+''.join(m.group()for m in sorted(blocks,key=key))+s[blocks[-1].end():];out.write_text(s)
h=hashlib.sha256(out.read_bytes()).hexdigest();print(json.dumps({'flip':sys.argv[1],'sha256':h,'exact8a4':h=='8a4ff6a646396a3faa11dda0f756c89e82c20eec18f37fe531cf730789106eea','path':str(out)}))
