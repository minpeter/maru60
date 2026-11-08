from pathlib import Path
import hashlib,json,shutil,time
import pcbnew as p
R=Path('/workspace/shared/maru60-resume/header-independent26b');S=Path('/workspace/shared/maru60-resume/header-routing/frozen26b/pcb');D=R/'cold/pcb'
assert not D.exists();shutil.copytree(S,D)
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();fm=lambda d:{str(f.relative_to(d)):H(f) for f in d.rglob('*') if f.is_file()}
original=fm(S);B=D/'maru60.kicad_pcb';before=H(B);assert before=='04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99'
b=p.LoadBoard(str(B));names=lambda b:{x.m_Uuid.AsString():x.GetNetname() for x in list(b.GetTracks())+[pad for fp in b.GetFootprints() for pad in fp.Pads()]};loadnames=names(b)
tracks=list(b.GetTracks());vias=sum(isinstance(x,p.PCB_VIA) for x in tracks);metrics={'track_segments':len(tracks)-vias,'vias':vias,'footprints':len(list(b.GetFootprints())),'summed_track_length_mm':sum(x.GetLength() for x in tracks if not isinstance(x,p.PCB_VIA))/1e6}
t=time.monotonic();b.BuildConnectivity();assert names(b)==loadnames;p.ZONE_FILLER(b).Fill(b.Zones());assert names(b)==loadnames;p.SaveBoard(str(B),b);after=H(B)
result={'native_build':p.GetBuildVersion(),'source_pcb_sha256':before,'after_sha256':after,'all_files_byte_identical':fm(D)==original,'source_unchanged':fm(S)==original,'names_stable_load_build_refill':True,'metrics':metrics,'seconds':time.monotonic()-t};(R/'cold-refill.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert fm(D)==original
