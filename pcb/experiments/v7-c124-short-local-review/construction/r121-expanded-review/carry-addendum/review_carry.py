import pathlib,hashlib,json,re,collections,difflib
D=pathlib.Path('/tmp/v7-c124-rebound-short/r121-expanded-review/carry-addendum')
BASE=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4/filled/pcb/maru60.kicad_pcb')
NEW=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4-label-carry/pcb/maru60.kicad_pcb')
SEL=pathlib.Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb')
PROOF=NEW.parents[1]/'CARRY_PROOF.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
hashes={str(p):sha(p.read_bytes()) for p in [BASE,NEW,SEL,PROOF]}
assert hashes[str(BASE)]=='8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6'
assert hashes[str(NEW)]=='ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7'
assert hashes[str(SEL)]=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
# String-aware S-expression span parser, retaining all original bytes; no CAD imports.
def children(s):
 depth=0;quoted=False;esc=False;start=None;out=[]
 for i,c in enumerate(s):
  if quoted:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quoted=False
   continue
  if c=='"':quoted=True
  elif c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:
    raw=s[start:i+1];m=re.match(r'\(([^\s()]+)',raw);out.append({'start':start,'end':i+1,'kind':m.group(1),'raw':raw})
   depth-=1
 assert depth==0 and not quoted
 return out

def field(s,kind):return [x for x in children(s) if x['kind']==kind]
def scalar(s,kind):
 x=field(s,kind)
 return x[0]['raw'] if len(x)==1 else None

def footprints(s):
 r={}
 for n in children(s):
  if n['kind']=='footprint':
   uu=scalar(n['raw'],'uuid');u=re.fullmatch(r'\(uuid "([^"]+)"\)',uu).group(1)
   ref=next(x for x in field(n['raw'],'property') if x['raw'].startswith('(property "Reference"'))
   n['ref']=re.match(r'\(property "Reference" "([^"]+)"',ref['raw']).group(1);n['reference_node']=ref;r[u]=n
 return r

def stripped(s,nodes):
 for n in sorted(nodes,key=lambda q:q['start'],reverse=True):s=s[:n['start']]+'(REVIEW_REPLACED_BLOCK)'+s[n['end']:]
 return s

texts=[p.read_text() for p in [BASE,NEW,SEL]]
a,b,c=map(footprints,texts)
assert a.keys()==b.keys()
changed=[u for u in a if a[u]['raw']!=b[u]['raw']]
expected={'C100','R140','R160','R134','LOGO1'}
assert {a[u]['ref'] for u in changed}==expected
assert stripped(texts[0],[a[u]for u in changed])==stripped(texts[1],[b[u]for u in changed])
result={'method':'Pure UTF-8 file parsing and hashing; no pcbnew import, BOARD load, fill, export, or candidate write.','hashes':hashes,'scope':'Separate unselected artwork carry only; no adoption or qualification.','footprint_count':len(b),'unchanged_footprints':len(a)-len(changed),'outside_five_footprints_byte_identical':True,'changed_footprints':[]}
for u in changed:
 x,y,z=a[u],b[u],c[u]
 assert y['raw']==z['raw']
 row={'uuid':u,'reference':x['ref'],'exact_selected_block_copy':True,'old_block_sha256':sha(x['raw'].encode()),'new_block_sha256':sha(y['raw'].encode())}
 if x['ref']!='LOGO1':
  assert stripped(x['raw'],[x['reference_node']])==stripped(y['raw'],[y['reference_node']])
  
  for version in [x,y]:
   layer=re.findall(r'\(layer "([^"]+)"',version['reference_node']['raw']);assert layer==['B.SilkS']
  row.update(reference_field_only=True,reference_layer_before_after='B.SilkS',old_reference=x['reference_node']['raw'],new_reference=y['reference_node']['raw'])
 else:
  
  for version in [x,y]:
   for item in children(version['raw']):
    assert item['kind'] not in ['pad','zone','via','segment']
    if item['kind'].startswith('fp_') or item['kind']=='property':
     layers=re.findall(r'\(layer "([^"]+)"',item['raw']);assert layers and all(layer in ['B.SilkS','B.Fab'] for layer in layers)
  row['old_and_new_logo_have_no_conductive_children']=True
  kids=children(y['raw']);row['child_counts']=dict(collections.Counter(n['kind']for n in kids))
  # No pads, drills, zones, copper primitives, copper/edge/keepout geometry.
  assert not any(n['kind']in['pad','zone','via','segment']for n in kids)
  layers=re.findall(r'\(layer "([^"]+)"',y['raw']);row['all_layer_uses']=dict(collections.Counter(layers))
  # Footprint container B.Cu does not itself draw copper; all drawing child layers individually checked.
  graphic=[]
  for n in kids:
   if n['kind'].startswith('fp_') or n['kind']=='property':
    ls=re.findall(r'\(layer "([^"]+)"',n['raw']);graphic+=ls
    assert ls and all(not l.endswith('.Cu') and l not in ['Edge.Cuts','Margin'] for l in ls)
  row['graphic_layer_uses']=dict(collections.Counter(graphic));row['zero_pad_drill_zone_copper_primitive']=True
 result['changed_footprints'].append(row)

top_a=children(texts[0]);top_b=children(texts[1]);counts=collections.Counter(q['kind']for q in top_b)
result['top_level_counts']=dict(counts)
result['identical_copper_drills_fills_nets_board_settings']=True
result['complete_zone_count']=counts['zone']
# All non-board companion files that exist on both sides, including project settings.
companions={}
for p in sorted(BASE.parent.iterdir()):
 q=NEW.parent/p.name
 if p.is_file() and p.suffix!='.kicad_pcb' and q.is_file():
  companions[p.name]={'base_sha256':sha(p.read_bytes()),'carry_sha256':sha(q.read_bytes()),'byte_identical':p.read_bytes()==q.read_bytes()}
result['companion_files']=companions
assert companions['maru60.kicad_pro']['byte_identical']

OLD_DRC=BASE.parents[2]/'qa/filled-drc.json';DRC=NEW.parents[1]/'qa/drc.json'
old=json.loads(OLD_DRC.read_text());new=json.loads(DRC.read_text())
def canonical(v):
 z=dict(v)
 if 'items'in z:z['items']=sorted(z['items'],key=lambda q:json.dumps(q,sort_keys=True))
 return json.dumps(z,sort_keys=True)
def diffcat(k):
 aa=collections.Counter(map(canonical,old[k]));bb=collections.Counter(map(canonical,new[k]));return {'base_count':len(old[k]),'carry_count':len(new[k]),'added':[json.loads(s)for s,n in(bb-aa).items()for i in range(n)],'removed':[json.loads(s)for s,n in(aa-bb).items()for i in range(n)]}
result['drc']={'path':str(DRC),'sha256':sha(DRC.read_bytes()),'date':new['date'],'source':new['source'],'kicad_version':new['kicad_version'],'base_counts':dict(collections.Counter(v['type']for v in old['violations'])),'carry_counts':dict(collections.Counter(v['type']for v in new['violations'])),'carry_severity':dict(collections.Counter(v['severity']for v in new['violations'])),'categories':{k:diffcat(k)for k in['violations','unconnected_items','schematic_parity']}}
result['drc']['bridge_b_records']=[v for v in new['violations']if any(i['uuid']=='0dd51559-bc06-502f-8bb1-1b186fa751d0'for i in v['items'])]
assert not result['drc']['categories']['violations']['added']
assert not result['drc']['categories']['unconnected_items']['added']
assert not result['drc']['categories']['unconnected_items']['removed']
assert len(new['schematic_parity'])==0
result['final_hashes']={str(p):sha(p.read_bytes())for p in [BASE,NEW,SEL,PROOF]}
assert result['hashes']==result['final_hashes']
(D/'pure_file_review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'changed':[{k:v for k,v in q.items()if k not in ['old_reference','new_reference']}for q in result['changed_footprints']],'top_counts':result['top_level_counts'],'companion_files_identical':all(q['byte_identical']for q in companions.values()),'drc_counts':result['drc']['carry_counts'],'drc_severity':result['drc']['carry_severity'],'drc_removed_count':len(result['drc']['categories']['violations']['removed']),'drc_added_count':len(result['drc']['categories']['violations']['added']),'unconnected':len(new['unconnected_items']),'bridge_b':result['drc']['bridge_b_records'],'hashes_unchanged':True},indent=2))
