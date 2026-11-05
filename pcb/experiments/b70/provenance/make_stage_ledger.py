import os
for k in ['KICAD_CONFIG_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME']:os.environ[k]='/tmp/maru-b2l-native'
from pathlib import Path
import pcbnew as p,json,hashlib,sys
R=Path(__file__).parent;base,candidate,role=sys.argv[1:4];a=p.LoadBoard(str(R/(base+'.kicad_pcb')));b=p.LoadBoard(str(R/(candidate+'.kicad_pcb')));l=json.load(open(R/(base+'-ledger.json')));uid=lambda t:t.m_Uuid.AsString();xy=lambda q:[q.x/1e6,q.y/1e6]
def tr(t):return(t.GetNetname(),t.GetLayer(),tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth(p.F_Cu)if isinstance(t,p.PCB_VIA)else t.GetWidth(),t.GetDrillValue()if isinstance(t,p.PCB_VIA)else None)
old={uid(t):tr(t)for t in a.GetTracks()};new={uid(t):tr(t)for t in b.GetTracks()};assert all(new.get(u)==v for u,v in old.items()),'Unexpected mutation during additive reroute';added=[]
for t in b.GetTracks():
 if uid(t)in old:continue
 d={'uuid':uid(t),'net':t.GetNetname(),'layer':b.GetLayerName(t.GetLayer()),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd()),'width_mm':p.ToMM(t.GetWidth(p.F_Cu)if isinstance(t,p.PCB_VIA)else t.GetWidth()),'via':isinstance(t,p.PCB_VIA),'drill_mm':p.ToMM(t.GetDrillValue())if isinstance(t,p.PCB_VIA)else None,'role':role};added.append(d);l['added'].append(d)
l.setdefault('additive_stages',[]).append({'base':base,'base_sha256':hashlib.sha256((R/(base+'.kicad_pcb')).read_bytes()).hexdigest(),'candidate':candidate,'role':role,'new_objects':added});l['output']=str(R/(candidate+'.kicad_pcb'));l['output_sha256']=hashlib.sha256((R/(candidate+'.kicad_pcb')).read_bytes()).hexdigest();b.BuildConnectivity();l['native_unconnected_presave']=b.GetConnectivity().GetUnconnectedCount(False);(R/(candidate+'-ledger.json')).write_text(json.dumps(l,indent=2));print(l['output_sha256'],'opens',l['native_unconnected_presave'],'added objects',len(added))
