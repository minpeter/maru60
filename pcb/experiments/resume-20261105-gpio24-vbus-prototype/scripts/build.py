from pathlib import Path
import sys,shutil,hashlib,json
sys.path.insert(0,'/workspace/shared/maru60-resume/tools')
from sexpr_spans import children,head,replace_child
import pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'combined-trial';S=R/'header-routing/frozen24move/pcb';C=D/'pcb';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert H(S/'maru60.kicad_pcb')=='2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4'
assert not C.exists();shutil.copytree(S,C)
f=C/'maru60.kicad_pcb';s=f.read_text();uid='1e6f9b6e-9a22-418a-8cde-6feb5aafb26e';rows=[(a,z,t)for a,z,t in children(s)if uid in t];assert len(rows)==1 and head(rows[0][2])=='via'
a,z,t=rows[0];s=s[:a]+s[z:];changed_uid='b83f85ff-dd51-4f3a-987a-b80209573fa1';aa,zz,tt=next((aa,zz,tt)for aa,zz,tt in children(s)if changed_uid in tt);assert head(tt)=='segment';nt=replace_child(tt,'start','(start 20.15 10.95)');s=s[:aa]+nt+s[zz:];f.write_text(s);shutil.copyfile(f,D/'prefill.kicad_pcb');print(t,tt,nt,flush=True)
b=p.LoadBoard(str(f));ns=lambda:{x.m_Uuid.AsString():x.GetNetname()for x in list(b.GetTracks())+[q for fp in b.GetFootprints()for q in fp.Pads()]+list(b.Zones())};before=ns();b.BuildConnectivity();assert ns()==before;p.ZONE_FILLER(b).Fill(b.Zones());assert ns()==before;p.SaveBoard(str(f),b)
result={'source_sha256':H(S/'maru60.kicad_pcb'),'candidate_sha256':H(f),'removed_via':uid,'removed_form':t,'old_net_names_unchanged':True,'added_items':0,'removed_tracks':0,'removed_vias':1,'serialized_track_uuid':changed_uid,'serialized_track_old_form':tt,'serialized_track_new_form':nt,'intent':'Remove single-layer VBUS via and serialize existing overlapping tracks without reducing their planar copper union','status':'UNSELECTED experiment pending complete material/reference validation'}
(D/'qa/BUILD.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
