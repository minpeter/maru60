#!/usr/bin/env python3
"""Read-only recovery audit. Never loads, fills or saves CAD."""
import json,re,hashlib,collections
from pathlib import Path
BASE=Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104')
OUT=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXT=BASE/'extracted'; REC=BASE/'exact-reconstruction'
before={str(p.relative_to(EXT)):H(p) for p in sorted(EXT.rglob('*')) if p.is_file()}
checks=[]; total_checks=0
def require(ok,message):
 global total_checks
 if not ok:raise RuntimeError(message)
 total_checks+=1
 if not message.startswith('no duplicate root UUID '):checks.append(message)
def top(s):
 depth=0;quote=False;escape=False;start=None;out=[]
 for i,c in enumerate(s):
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c=='"':quote=False
  elif c=='"':quote=True
  elif c=='(':
   if depth==1:start=i
   depth+=1
  elif c==')':
   depth-=1
   if depth==1:out.append(s[start:i+1])
 require(depth==0 and not quote,'balanced top-level board expressions')
 return out

def indexed(s):
 out={};opaque=[]
 for block in top(s):
  typ=re.match(r'\(([^\s()]+)',block).group(1)
  uid=re.search(r'\n\t\t\(uuid "([^"]+)"\)',block)
  if uid:
   k=(typ,uid.group(1));require(k not in out,'no duplicate root UUID '+str(k));out[k]=block
  else:opaque.append(block)
 return out,opaque

def delta(a,b):
 aa,ao=indexed(a);bb,bo=indexed(b)
 require(ao==bo,'unchanged all non-UUID board metadata')
 added=sorted(bb.keys()-aa.keys());removed=sorted(aa.keys()-bb.keys());changed=sorted(k for k in aa.keys()&bb.keys() if aa[k]!=bb[k])
 return {'added':[list(k) for k in added],'removed':[list(k) for k in removed],'changed':[list(k) for k in changed],'unchanged_uuid_objects':sum(aa[k]==bb[k] for k in aa.keys()&bb.keys()),'all_zone_raw_blocks_equal':all(aa[k]==bb.get(k) for k in aa if k[0]=='zone') and {k for k in aa if k[0]=='zone'}=={k for k in bb if k[0]=='zone'}},aa,bb

manifest_checks=[]; total_checks=0
for root,mp,sub in [(EXT/'maru60-tscircuit-full/input','manifest.json','v7'),(EXT/'v7-c128-pdn-study-20261104','MANIFEST.json',''),(EXT/'v7-si-advanced-20261104/return_geometry','manifest.json','')]:
 j=json.loads((root/mp).read_text());m=j.get('files',j);fail=[]
 for k,v in m.items():
  p=root/sub/k;sha=v['sha256'] if isinstance(v,dict) else v
  if not p.is_file() or H(p)!=sha:fail.append(k)
 require(not fail,'archive manifest exact '+str(root)+' '+str(fail))
 manifest_checks.append({'manifest':str(root/mp),'sha256':H(root/mp),'verified_file_count':len(m),'failures':fail})
known={
 'baseline3663.kicad_pcb':'3663aac96fb305eb4925fff938dd2db5862b880c6c262b2fa82707567a6e98f7',
 'u10-original2bf.kicad_pcb':'2bfcb5292319626d4f33cad5e827ed0b1eb6c1b2ef852d8cc7fc2a3bf5792a55',
 'u10-label-accepted400fd.kicad_pcb':'400fd2641ebd3208315359acf295ee630dab8d3319a6d990ea7ab8d558961fa2',
 'native-c128-LR/reconstructed.kicad_pcb':'8a4ff6a646396a3faa11dda0f756c89e82c20eec18f37fe531cf730789106eea',
 'width-reconstructed.kicad_pcb':'0e5bbc5ae365d9511ce51a81f75d9e9236fbb93af89b17b2e9486ceb038e026c',
 'typography-reconstructed.kicad_pcb':'7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'}
texts={}
for k,v in known.items():
 require(H(REC/k)==v,'full known board SHA exact '+k);texts[k]=(REC/k).read_text()
raw={}
d,aa,bb=delta(texts['baseline3663.kicad_pcb'],texts['u10-label-accepted400fd.kicad_pcb'])
x=json.loads((EXT/'v7-si-advanced-20261104/return_geometry/baseline_native.json').read_text());y=json.loads((EXT/'v7-si-advanced-20261104/return_geometry/candidate_native.json').read_text());xid={t['id']:t for t in x['tracks']};yid={t['id']:t for t in y['tracks']}
require(d['changed']==[] and d['removed']==[['segment',u] for u in sorted(xid.keys()-yid.keys())] and d['added']==[['segment',u] for u in sorted(yid.keys()-xid.keys())],'U10 raw delta is precisely archived 1 removed/10 added tracks')
require(all(xid[k]==yid[k] for k in xid.keys()&yid.keys()) and all(x[k]==y[k] for k in ('vias','pads','planes','zone_settings')),'archived U10 shared tracks/vias/drilled-pad/plane/settings exact')
raw['u10']=d
u=texts['u10-original2bf.kicad_pcb'].encode();v=texts['u10-label-accepted400fd.kicad_pcb'].encode();positions=[i for i,(a,b) in enumerate(zip(u,v)) if a!=b]
require(len(u)==len(v) and len(positions)==2 and all(u[i]==ord('5') and v[i]==ord('4') for i in positions),'board label correction exactly two ASCII 5-to-4 bytes')
raw['voltage_labels']={'changed_byte_offsets':positions,'old_contexts':[u[i-55:i+15].decode() for i in positions]}
d,aa,bb=delta(texts['u10-label-accepted400fd.kicad_pcb'],texts['native-c128-LR/reconstructed.kicad_pcb'])
require(d['removed']==[] and d['changed']==[['footprint','47590d17-4db9-41bf-a1ff-5a7f2c886bb8']] and d['added']==[['segment','99335a61-c21f-59c4-876b-507f6433e7c6'],['segment','b0cc9de1-aec9-5121-a294-6107a6342d33'],['via','74838ec4-2a2a-5ebb-82d1-e1c3369351cd']],'C128 exactly one changed footprint and three added conductors')
require(d['all_zone_raw_blocks_equal'],'C128 all old zone raw fields and saved fill bytes exact')
raw['c128']=d
# Raw proposal-based additions, no native interpretation or regeneration.
for typ,uid,fragments in [('segment','99335a61-c21f-59c4-876b-507f6433e7c6',['(start 112.225 36.025)','(end 111.646017 36.003416)','(width 0.3)','(layer "F.Cu")','(net 83)']),('segment','b0cc9de1-aec9-5121-a294-6107a6342d33',['(start 113.775 36.025)','(end 110.45 33.4375)','(width 0.3)','(layer "F.Cu")','(net 97)']),('via','74838ec4-2a2a-5ebb-82d1-e1c3369351cd',['(at 111.346017 36.003416)','(size 0.5)','(drill 0.25)','(layers "F.Cu" "B.Cu")','(net 83)'])]:
 require(all(t in bb[typ,uid] for t in fragments),'C128 new exact raw geometry '+uid)
d,aa,bb=delta(texts['native-c128-LR/reconstructed.kicad_pcb'],texts['width-reconstructed.kicad_pcb'])
require(d['removed']==[] and d['changed']==[] and d['added']==[['segment','0fcbbcbc-52de-5e52-b60d-79b83d0b7fa8']],'width sole additional raw conductor, no changed old object')
require(all(t in bb['segment','0fcbbcbc-52de-5e52-b60d-79b83d0b7fa8'] for t in ['(start 140.5 72.7)','(end 140.6 72.8)','(width 0.15)','(layer "B.Cu")','(net 97)']),'width exact raw geometry')
raw['width']=d
d,aa,bb=delta(texts['width-reconstructed.kicad_pcb'],texts['typography-reconstructed.kicad_pcb'])
refs=['R120','R144','J3','D100','R124','C142','C141','R163','C137','C126','C129','U2','R126','U10','C101'];moves={'U2':('(at 0 2 0)','(at 0 -1.8 0)'), 'C101':('(at 0 1.4 90)','(at 0 1.7 90)'), 'J3':('(at 0 3.98 180)','(at -0.1 3.98 180)'), 'C142':('(at 0 1.25 0)','(at 0.05 1.25 0)')};seen=[]
require(not d['added'] and not d['removed'] and len(d['changed'])==15 and all(k[0]=='footprint' for k in d['changed']),'typography changes exactly 15 existing footprints')
for k in map(tuple,d['changed']):
 a,b=aa[k],bb[k];ref=re.search(r'\(property "Reference" "([^"]+)"',a).group(1);require(ref in refs,'typography ref allowed '+ref);seen.append(ref)
 pat=r'(\n\t\t\(property "Reference" "'+re.escape(ref)+r'"\n.*?\n\t\t\))';ma=re.search(pat,a,re.S);mb=re.search(pat,b,re.S);expected=ma.group().replace('(size 0.75 0.75)','(size 0.8 0.8)')
 if ref in moves:expected=expected.replace(*moves[ref])
 require(expected==mb.group() and a[:ma.start()]+a[ma.end():]==b[:mb.start()]+b[mb.end():],'typography exact reference-only field change '+ref)
require(sorted(seen)==sorted(refs),'typography complete 15-reference set')
raw['typography']=dict(d,reference_names=sorted(seen),anchor_moves=moves)
# Static construction code is reviewed and bound, not executed by this audit.
scripts={k:H(REC/k) for k in ('recover_u10.py','recover_c128.py','recover_width_typography.py')}
after={str(p.relative_to(EXT)):H(p) for p in sorted(EXT.rglob('*')) if p.is_file()}
require(before==after,'all recovered source file bytes and file set unchanged throughout independent audit')
require(all(H(REC/k)==v for k,v in known.items()),'all reconstructed boards unchanged during audit')
report={'decision':'exact_board_chain_recovered','scope':'Read-only hash, archive manifest and raw object-delta audit; no CAD load/fill/save, no constructors run, no DRC/ERC/native validation rerun.', 'board_hashes':known,'archive_manifests':manifest_checks,'raw_delta_checks':raw,'reviewed_constructor_hashes':scripts,'recovered_source_files_verified_unchanged':len(before),'checks_passed':total_checks,'historical_qa_fully_recovered':False,'historical_git_objects_recovered':False,'full_selected_54_file_project_equality_established':False,'limitations':['Exact full board SHA establishes the recovered board bytes, not restoration of missing historical validation scripts/results or Git commits.','Earlier 53-file project input manifest is exact. The later complete 54-file selected project map is not present in these artifacts, so that full package equality is not claimed.','Source-bound simulation snapshots remain partial circuit/geometry models, not hardware or manufacturing qualification.','Recovery constructor scripts are ad hoc deterministic recovery tools, not substitutes for historical acceptance gates.'], 'recovery_script_notes':['recover_u10.py reports its initially expected original U10 hash as false because its source already has corrected labels; the resulting 400fd SHA is exact, and separate reversal of two PCB Value bytes yields original 2bf SHA.','recover_c128.py uses explicit layer-specific via.SetWidth, native footprint transformation/save, then canonical conductor sorting after fixed UUID substitution. Actual output SHA, not an assumed serializer equivalence, establishes recovery.','Width adds one fixed-UUID raw segment. Typography changes exactly 15 Reference sizes and four anchor positions.'], 'native_new_tests_claimed':False}
(OUT/'review.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({'decision':report['decision'],'board_count':len(known),'recovered_source_files_unchanged':len(before),'checks_passed':total_checks,'review_sha256':H(OUT/'review.json')},indent=2))
