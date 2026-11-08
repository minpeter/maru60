from pathlib import Path
import sys,re,hashlib,json,shutil
from sexpr_spans import children,head
R=Path('/tmp/v7-c124-rebound-short');V=R/'isolated-v4';O=R/'isolated-v4-label-carry';B=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pcb');L=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb');A=V/'filled/pcb/maru60.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1';assert sha(L)=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373';assert sha(A)=='8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6';assert not O.exists()
def objects(s):
 d={}
 for a,z,t in children(s):
  m=re.search(r'\(uuid "([^"]+)"\)',t)
  if m:d[m.group(1)]=(a,z,t)
 return d
bs,ls,aa=B.read_text(),L.read_text(),A.read_text();bo,lo,ao=map(objects,[bs,ls,aa]);assert set(bo)==set(lo);changed={u for u in bo if bo[u][2]!=lo[u][2]};refs={};proof=[]
for u in changed:
 old,new=bo[u][2],lo[u][2];assert head(old)==head(new)=='footprint';ref=re.search(r'\(property "Reference" "([^"]+)"',new).group(1);refs[ref]=u;assert ao[u][2]==old
 if ref!='LOGO1':
  def no_ref(t):return[t for a,z,t in children(t)if not t.startswith('(property "Reference"')]
  assert no_ref(old)==no_ref(new),ref
 else:
  assert not any(head(t)in['pad','zone']for a,z,t in children(new));assert '"F.Cu"' not in new and '"B.Cu"'not in '\n'.join(t for a,z,t in children(new)if head(t).startswith('fp_'))
 proof.append({'reference':ref,'uuid':u,'old_block_sha256':hashlib.sha256(old.encode()).hexdigest(),'accepted_block_sha256':hashlib.sha256(new.encode()).hexdigest(),'scope':'reference field only'if ref!='LOGO1'else'nonconductive whole LOGO1 artwork only'})
assert set(refs)=={'C100','R140','R160','R134','LOGO1'}
shutil.copytree(V/'filled/pcb',O/'pcb');(O/'qa').mkdir();s=aa
for a,z,t in sorted([(ao[u][0],ao[u][1],lo[u][2])for u in changed],reverse=True):s=s[:a]+t+s[z:]
p=O/'pcb/maru60.kicad_pcb';p.write_text(s);co=objects(s);assert set(co)==set(ao);assert{u for u in co if co[u][2]!=ao[u][2]}==changed
m={'status':'UNSELECTED separate accepted-artwork carry; no electrical change or adoption','selected_source_sha256':sha(L),'trial_source_sha256':sha(B),'prior_filled_trial_sha256':sha(A),'successor_sha256':sha(p),'changed_footprint_blocks':proof,'all_other_blocks_byte_identical':True,'all_12_zone_records_byte_identical':True,'all_copper_pads_tracks_vias_geometry_nets_and_rules_unchanged':True,'source_paths':[str(B),str(L),str(A)]};(O/'CARRY_PROOF.json').write_text(json.dumps(m,indent=2)+'\n');(O/'README.md').write_text('# Unselected V4 with accepted label/logo carry\n\nThis separate successor carries only the four accepted reference fields and whole nonconductive LOGO1 from selected2c7 onto the completed8c45 short local circuit experiment. All electrical geometry, layers, nets, rules, physical contacts and filled reference planes are identical to8c45. See CARRY_PROOF.json. Native DRC is still required on this exact hash. Analog, component approval, socket/plate, assembly and production qualification remain false. No source or selected repository was modified.\n');print(json.dumps(m,indent=2))
