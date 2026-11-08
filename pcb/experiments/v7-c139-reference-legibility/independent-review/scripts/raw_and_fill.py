from pathlib import Path
import re,json,hashlib,shutil,time,sys
import pcbnew as p
sys.dont_write_bytecode=True
from sexpr_spans import children,head
R=Path('/tmp/v7-c139-independent-review');S=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-two-reference-legibility/candidate/pcb');C=Path('/tmp/v7-buck-three-labels-4765/candidate/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=H(S/'maru60.kicad_pcb');dest=H(C/'maru60.kicad_pcb');assert source=='4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136' and dest=='2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69';a=(S/'maru60.kicad_pcb').read_text();b=(C/'maru60.kicad_pcb').read_text();aa=children(a);bb=children(b);assert len(aa)==len(bb);changes=[];back=b
for (_,_,old),(x,y,new)in reversed(list(zip(aa,bb))):
 if old==new:continue
 assert head(old)==head(new)=='footprint';oa=children(old);nb=children(new);assert len(oa)==len(nb);changed=[];revert=new
 for (_,_,of),(i,j,nf)in reversed(list(zip(oa,nb))):
  if of==nf:continue
  assert of.startswith('(property "Reference" "C139"')and nf.startswith('(property "Reference" "C139"');changed.append({'old':of,'new':nf});revert=revert[:i]+of+revert[j:]
 assert len(changed)==1 and revert==old;changes.extend(changed);back=back[:x]+old+back[y:]
assert len(changes)==1 and back==a
fm=lambda d:{str(f.relative_to(d)):H(f)for f in d.rglob('*')if f.is_file()};sm,cm=fm(S),fm(C);assert len(sm)==len(cm)==58 and sm.keys()==cm.keys()and[k for k in sm if sm[k]!=cm[k]]==['maru60.kicad_pcb']
old=json.load(open('/tmp/v7-serial-legs-plus-two-labels/qa/drc.json'));new=json.load(open('/tmp/v7-buck-three-labels-4765/qa/drc.json'));key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'));oa={key(x):x for x in old['violations']};nb={key(x):x for x in new['violations']};removed=[oa[k]for k in oa.keys()-nb.keys()];assert len(oa)==55 and len(nb)==51 and not(nb.keys()-oa.keys())and len(removed)==4;assert all(any(i['description']=='Reference field of C139'for i in r['items'])for r in removed);assert old['unconnected_items']==new['unconnected_items']and len(new['unconnected_items'])==12 and new['schematic_parity']==[];assert all(v['severity']=='warning'for v in new['violations'])
D=R/'cold-copy/pcb';assert not D.exists();shutil.copytree(C,D);B=D/'maru60.kicad_pcb';board=p.LoadBoard(str(B));assert p.GetBuildVersion()=='9.0.2+dfsg-1';ref=next(f for f in board.GetFootprints()if f.GetReference()=='C139').Reference();assert(ref.GetPosition().x,ref.GetPosition().y)==(181400000,81800000)and ref.GetTextWidth()==ref.GetTextHeight()==800000 and ref.GetTextThickness()==100000 and ref.GetTextAngle().AsDegrees()==90 and ref.IsVisible()and ref.IsMirrored()and ref.GetLayer()==p.B_SilkS;t=time.monotonic();board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(B),board);assert fm(D)==cm and fm(C)==cm and fm(S)==sm
result={'status':'PASS exact one-Reference-only raw reversal, native identity and separate cold refill','source_sha256':source,'candidate_sha256':dest,'change':changes[0],'all57_companions_exact':True,'all_electrical_copper_drills_zones_rules_exact':True,'native_typography_verified':True,'cold_refill_seconds':time.monotonic()-t,'cold_refill_all58_files_byte_identical':True,'warnings_before':55,'warnings_after':51,'four_exact_C139_warnings_removed':removed,'no_new_warning':True,'same_raw_opens':12,'other_hard_and_parity':0,'ERC_and_material_results_inherit_as_identical_input_only':True,'hardware_qualification':False}
(R/'qa/raw-and-cold-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
