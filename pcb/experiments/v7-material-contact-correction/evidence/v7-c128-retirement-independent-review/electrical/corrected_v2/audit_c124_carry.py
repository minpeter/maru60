from pathlib import Path
import json,hashlib,re,collections
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2');P=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-short-local-review/construction');A=P/'isolated-v4/filled/pcb/maru60.kicad_pcb';B=P/'isolated-v4-label-carry/pcb/maru60.kicad_pcb';S=Path('/tmp/v7-buck-deadarm-final-recheck/source/pcb/maru60.kicad_pcb');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A)=='8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6';assert sha(B)=='ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7';assert sha(S)=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
def forms(t):
 depth=0;quote=False;escape=False;out=[];start=None
 for i,ch in enumerate(t):
  if quote:
   if escape:escape=False
   elif ch=='\\':escape=True
   elif ch=='"':quote=False
  elif ch=='"':quote=True
  elif ch=='(':depth+=1;start=i if depth==2 else start
  elif ch==')':
   if depth==2:out.append((start,i+1,t[start:i+1]))
   depth-=1
 assert depth==0 and not quote
 return out
head=lambda t:re.match(r'\(\s*([^\s()]+)',t).group(1)
def footprints(t):
 out={}
 for a,z,s in forms(t):
  if head(s)!='footprint':continue
  fields=forms(s);uid=next(q for _,_,q in fields if head(q)=='uuid');u=re.search('"([^"]+)"',uid).group(1);reference=next(q for q in fields if q[2].startswith('(property "Reference"'));ref=re.match(r'\(property "Reference" "([^"]+)"',reference[2]).group(1);out[u]=dict(start=a,end=z,text=s,ref=ref,reference=reference)
 return out
def mask(t,spans):
 for a,z in sorted(spans,reverse=True):t=t[:a]+'(AUDIT_MASK)'+t[z:]
 return t
at,bt,st=[p.read_text()for p in [A,B,S]];a,b,s=[footprints(t)for t in[at,bt,st]];assert a.keys()==b.keys();changed={u for u in a if a[u]['text']!=b[u]['text']};assert {a[u]['ref']for u in changed}=={'R140','R160','C100','R134','LOGO1'};assert mask(at,[(a[u]['start'],a[u]['end'])for u in changed])==mask(bt,[(b[u]['start'],b[u]['end'])for u in changed]);rows=[]
for u in sorted(changed):
 old,new=a[u],b[u];assert new['text']==s[u]['text']
 if old['ref']!='LOGO1':
  assert mask(old['text'],[old['reference'][:2]])==mask(new['text'],[new['reference'][:2]])
  for q in [old,new]:assert re.findall(r'\(layer "([^"]+)"',q['reference'][2])==['B.SilkS']
 else:
  for q in[old,new]:
   for _,_,c in forms(q['text']):
    h=head(c);assert h not in ['pad','zone','segment','via','gr_line','gr_arc','gr_poly']
    if h.startswith('fp_')or h=='property':assert all(l in ['B.SilkS','B.Fab']for l in re.findall(r'\(layer "([^"]+)"',c))
 rows.append(dict(uuid=u,ref=old['ref'],new_block_is_exact_selected_2c7_copy=True,reference_only=old['ref']!='LOGO1',logo_has_no_conductive_children=old['ref']=='LOGO1',old_block_sha256=hashlib.sha256(old['text'].encode()).hexdigest(),new_block_sha256=hashlib.sha256(new['text'].encode()).hexdigest()))
files=lambda root:{str(p.relative_to(root)):sha(p)for p in root.rglob('*')if p.is_file()};af,bf=files(A.parent),files(B.parent);assert af.keys()==bf.keys()and[k for k in af if af[k]!=bf[k]]==['maru60.kicad_pcb'];zones=lambda t:[q for _,_,q in forms(t)if head(q)=='zone'];assert zones(at)==zones(bt)
graph=P/'isolated-v4/qa/actual-native-physical-graph.json';g=json.loads(graph.read_text());assert g['board_sha256']==sha(A);assert sha(Path(g['source_path']))==sha(A)
r=dict(status='PASS: exact electrical carry; final ec487 can be compared with original 8c45 graph only for unchanged electrical content',base_path=str(A),base_sha256=sha(A),final_path=str(B),final_sha256=sha(B),selected_artwork_source_sha256=sha(S),all_files_count=len(af),all_nonboard_files_byte_exact=True,all_bytes_outside_five_footprints_exact=True,zone_count=len(zones(at)),all_zone_forms_byte_exact=True,changed_blocks=rows,original_graph_path=str(graph),original_graph_sha256=sha(graph),original_graph_board_sha256=g['board_sha256'],reviewed_scripts=['/tmp/v7-c124-rebound-short/main/carry_accepted_labels.py','/tmp/v7-c124-rebound-short/r121-expanded-review/carry-addendum/review_carry.py'],scope='Read-only raw board/file and source-review audit. No native refill/export, CAD mutation or selection.');(D/'C124_EXACT_ELECTRICAL_CARRY.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
