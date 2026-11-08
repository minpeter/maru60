from pathlib import Path
import re,json,hashlib
R=Path('/tmp/v7-serial-legs-plus-two-labels');A=Path('/tmp/v7-support-endpoint-trial/filled/pcb');D=R/'filled/pcb';L=Path('/tmp/v7-two-label-corrected-7882/candidate/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert H(A/'maru60.kicad_pcb')=='abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d';assert H(D/'maru60.kicad_pcb')=='4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136'
def parts(s):
 depth=0;q=False;e=False;start=None;out=[]
 for i,c in enumerate(s):
  if q:
   if e:e=False
   elif c=='\\':e=True
   elif c=='"':q=False
   continue
  if c=='"':q=True
  elif c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:out.append((start,i+1,s[start:i+1]))
   depth-=1
 assert depth==0 and not q
 return out
s=(A/'maru60.kicad_pcb').read_text();c=(D/'maru60.kicad_pcb').read_text();l=(L/'maru60.kicad_pcb').read_text();a=parts(s);b=parts(c);assert len(a)==len(b);restored=c;changed=[]
lf={re.search(r'\(property "Reference" "([^"]+)"',f).group(1):f for _,_,f in parts(l)if f.startswith('(footprint')}
for (x,y,old),(u,v,new)in reversed(list(zip(a,b))):
 if old==new:continue
 assert old.startswith('(footprint')and new.startswith('(footprint');ref=re.search(r'\(property "Reference" "([^"]+)"',old).group(1);assert ref in ['U18','L2'];op=parts(old);np=parts(new);assert len(op)==len(np);revert=new;fields=[]
 for (i,j,of),(k,m,nf)in reversed(list(zip(op,np))):
  if of==nf:continue
  assert of.startswith('(property "Reference" "'+ref+'"')and nf.startswith('(property "Reference" "'+ref+'"');source_field=[t for _,_,t in parts(lf[ref])if t.startswith('(property "Reference" "'+ref+'"')];assert source_field==[nf];fields.append(nf);revert=revert[:k]+of+revert[m:]
 assert len(fields)==1 and revert==old;restored=restored[:u]+old+restored[v:];changed.append(ref)
assert set(changed)=={'U18','L2'}and restored==s
fm=lambda p:{str(f.relative_to(p)):H(f)for f in p.rglob('*')if f.is_file()};aa=fm(A);dd=fm(D);assert set(aa)==set(dd)and len(aa)==58 and [k for k in aa if aa[k]!=dd[k]]==['maru60.kicad_pcb']
old=json.load(open('/tmp/v7-support-endpoint-trial/qa/drc.json'));new=json.load(open(R/'qa/drc.json'));key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'));oa={key(w):w for w in old['violations']};nb={key(w):w for w in new['violations']};assert len(oa)==61 and len(nb)==55 and not(nb.keys()-oa.keys());removed=[oa[k]for k in oa.keys()-nb.keys()];expected=json.load(open('/tmp/v7-selected-label-screen-7882/DRC_COMPARISON.json'))['removed'];assert {key(w)for w in removed}=={key(w)for w in expected};assert old['unconnected_items']==new['unconnected_items']and len(new['unconnected_items'])==12;assert old['schematic_parity']==new['schematic_parity']==[];assert all(w['severity']=='warning'for w in new['violations'])
out={'source_sha256':H(A/'maru60.kicad_pcb'),'candidate_sha256':H(D/'maru60.kicad_pcb'),'two_fields_match_actual_reviewed_99c2':True,'reverting_only_reference_fields_recovers_abdb_exact_bytes':True,'all57_companions_exact':True,'all_electrical_drills_zones_rules_exact':True,'all_serial_material_support_reference_results_inherit_as_identical_inputs':True,'exact_six_warnings_removed':removed,'no_added_warning':True,'native_warnings':55,'raw_opens_identical':12,'parity_entries':[],'active_hardware_and_SI_qualification':False}
P=Path('/tmp/v7-two-label-carry-root-review');P.mkdir(exist_ok=True);(P/'CARRY_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS',out['candidate_sha256'])
