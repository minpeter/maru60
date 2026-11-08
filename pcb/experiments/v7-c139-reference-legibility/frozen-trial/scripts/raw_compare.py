from pathlib import Path
import sys,re,json,hashlib,collections
sys.path.insert(0,'/tmp/v7-support-endpoint-trial/scripts');from sexpr_spans import children,head
R=Path('/tmp/v7-buck-three-labels-4765');S=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-two-reference-legibility/candidate/pcb');C=Path('/tmp/v7-buck-three-labels-4765/candidate/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):
 d={};other=[]
 for a,z,t in children(p.read_text()):
  u=next((x for _,_,x in children(t)if head(x)=='uuid'),None)
  if u:d[re.search(r'"([^"]+)"',u).group(1)]=t
  else:other.append(t)
 return d,other
def refchild(t):return next(x for _,_,x in children(t)if x.startswith('(property "Reference"'))
a,ao=rec(S/'maru60.kicad_pcb');b,bo=rec(C/'maru60.kicad_pcb');assert a.keys()==b.keys()and ao==bo
changed=[u for u in a if a[u]!=b[u]];rows=[]
for u in changed:
 assert a[u].startswith('(footprint')
 ra=refchild(a[u]);rb=refchild(b[u]);assert a[u].replace(ra,'REFERENCE_FIELD')==b[u].replace(rb,'REFERENCE_FIELD');ref=re.match(r'\(property "Reference" "([^"]+)"',ra).group(1);rows.append({'uuid':u,'reference':ref,'source_reference_raw':ra,'trial_reference_raw':rb})
assert {x['reference']for x in rows}=={'C139'}
sourcefiles={str(p.relative_to(S)):H(p)for p in S.rglob('*')if p.is_file()};candidatefiles={str(p.relative_to(C)):H(p)for p in C.rglob('*')if p.is_file()};assert sourcefiles.keys()==candidatefiles.keys();assert {k for k in sourcefiles if sourcefiles[k]!=candidatefiles[k]}=={'maru60.kicad_pcb'}
sourceDRC=Path('/tmp/v7-serial-legs-plus-two-labels/qa/drc.json');trialDRC=R/'qa/drc.json';sd=json.loads(sourceDRC.read_text());cd=json.loads(trialDRC.read_text());cnt=lambda v:collections.Counter(json.dumps(x,sort_keys=True)for x in v);removed=[json.loads(x)for x in(cnt(sd['violations'])-cnt(cd['violations'])).elements()];added=[json.loads(x)for x in(cnt(cd['violations'])-cnt(sd['violations'])).elements()];assert not added and len(removed)==4;assert cnt(sd['unconnected_items'])==cnt(cd['unconnected_items']);assert not cd['schematic_parity'];assert all(x['severity']=='warning'for x in cd['violations']);zones=[u for u in a if head(a[u])=='zone'];assert len(zones)==12 and all(a[u]==b[u]for u in zones)
refs=['C100','R140','R160','R134','C124','R121','R125','U8'];unchanged={}
for ref in refs:
 x=next(u for u,t in a.items()if head(t)=='footprint'and f'(property "Reference" "{ref}"'in t);assert a[x]==b[x];unchanged[ref]={'footprint_uuid':x,'full_raw_footprint_exact':True}
out={'source_sha256':H(S/'maru60.kicad_pcb'),'trial_sha256':H(C/'maru60.kicad_pcb'),'status':'PASS exact raw one-Reference-only scope; geometry acceptance separate','changed_footprints':rows,'all_other_raw_top_level_objects_exact':True,'all_non_reference_bytes_in_changed_footprints_exact':True,'all12_raw_zones_exact':True,'all_tracks_vias_holes_pads_nets_settings_exact':True,'source_file_count':len(sourcefiles),'all_companions_exact':True,'eight_selected_full_footprints_exact':unchanged,'source_drc_sha256':H(sourceDRC),'trial_drc_sha256':H(trialDRC),'warning_counts':[len(sd['violations']),len(cd['violations'])],'removed_warnings':removed,'added_warnings':added,'raw12opens_exact':True,'hard_DRC':0,'parity':0}
(R/'qa/raw-warning-comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
