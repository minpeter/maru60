import os,json,hashlib,collections
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p
D=Path(__file__).parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
uid=lambda x:x.m_Uuid.AsString()
def get(path):
 b=p.LoadBoard(str(path));b.BuildConnectivity();cn=b.GetConnectivity();nets=collections.defaultdict(dict);pn={}
 for f in b.GetFootprints():
  for q in f.Pads():
   if not q.GetNetname():continue
   nets[q.GetNetname()][uid(q)]=q;pn[uid(q)]=(f.GetReference(),q.GetNumber())
 for t in b.GetTracks():nets[t.GetNetname()][uid(t)]=t
 out={}
 for net,items in nets.items():
  left=set(items);groups=[]
  while left:
   todo=[next(iter(left))];seen=set()
   while todo:
    u=todo.pop()
    if u in seen or u not in items:continue
    seen.add(u);todo.extend(uid(q)for q in list(cn.GetConnectedTracks(items[u]))+list(cn.GetConnectedPads(items[u]))if q.GetNetname()==net)
   left-=seen
   pads=sorted(u for u in seen if u in pn)
   if pads:groups.append(pads)
  out[net]=sorted(groups)
 return out,pn,{'footprints':len(list(b.GetFootprints())),'vias':sum(isinstance(t,p.PCB_VIA)for t in b.GetTracks()),'segments':sum(not isinstance(t,p.PCB_VIA)for t in b.GetTracks()),'track_centerline_mm':sum(p.ToMM(t.GetLength())for t in b.GetTracks()if not isinstance(t,p.PCB_VIA))}
a,ap,am=get(D/'source.kicad_pcb');b,bp,bm=get(D/'candidate.kicad_pcb');assert ap==bp
changed={k:{'before':a.get(k),'after':b.get(k)}for k in a.keys()|b.keys()if a.get(k)!=b.get(k)}
assert set(changed)<=set(['GND','+3V3','+1V1','+5V','+5V_LED','VREG_LX','VREG_AVDD','LED_ENABLE']),list(changed)
assert len(a['LED_ENABLE'])==2 and len(b['LED_ENABLE'])==1
assert sorted(bp[u]for u in b['LED_ENABLE'][0])==[('R109','1'),('U1','34'),('U7','3')]
j={'source_sha256':sha(D/'source.kicad_pcb'),'candidate_sha256':sha(D/'candidate.kicad_pcb'),'method':'Native track/pad adjacency complete connected-component traversal, compares physical pad UUID partitions for every named net. Copper-only components excluded from this function check but exact copper ledger and native opens reported separately. Saved-zone power/ground reachability independently covered by thirteen source witness gates.','net_count':len(b),'all_other_nonrail_physical_pad_partitions_unchanged':True,'actual_LED_ENABLE_closure':[['R109','1'],['U1','34'],['U7','3']],'rail_track_only_partition_changes_expected_use_saved_zone_witnesses':list(changed),'changed':changed,'source_metrics':am,'candidate_metrics':bm,'pad_identity_by_UUID':bp,'candidate_groups':b}
(D/'canonical-function-groups.json').write_text(json.dumps(j,indent=2));print({k:v for k,v in j.items()if k not in ['candidate_groups','pad_identity_by_UUID']})
