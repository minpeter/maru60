from pathlib import Path
import sys,json,re,hashlib,collections
sys.dont_write_bytecode=True
if not __debug__:raise RuntimeError('Optimized Python unsupported')
sys.path.insert(0,'/tmp/v7-gnd-tail-cleanup-aead/scripts');from sexpr_spans import children,head,field
R=Path('/tmp/v7-gnd-tail-cleanup-aead');O=Path(__file__).resolve().parent;S=R/'source/pcb/maru60.kicad_pcb';P=R/'prefill/pcb/maru60.kicad_pcb';C=R/'filled/pcb/maru60.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(S)=='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f';assert sha(C)=='c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a'
plan=json.loads((O.parent/'two-track-contract.json').read_text());remove={x['uuid']for x in plan['retire_exactly']};uid=lambda n:(re.search(r'\(uuid "([^"]+)"',n).group(1)if re.search(r'\(uuid "([^"]+)"',n)else None)
def parse(p):
 t=p.read_text();r=children(t);outside=t
 for a,b,n in reversed(r):outside=outside[:a]+outside[b:]
 assert ''.join(outside.split())=='(kicad_pcb)'
 return [n for _,_,n in r]
a=parse(S);p=parse(P);c=parse(C);dropped=[n for n in a if uid(n)in remove];assert len(dropped)==2 and all(head(n)=='segment'for n in dropped);assert [n for n in a if uid(n)not in remove]==p==c
zones=[n for n in a if head(n)=='zone'];assert len(zones)==12;assert zones==[n for n in c if head(n)=='zone'];keptvias=[n for n in a if head(n)=='via'];assert keptvias==[n for n in c if head(n)=='via']and len(keptvias)==918
companions=[]
for src in S.parent.rglob('*'):
 if src.is_file()and src.name!='maru60.kicad_pcb':
  rel=src.relative_to(S.parent);assert(C.parent/rel).is_file()and sha(src)==sha(C.parent/rel);companions.append(dict(path=str(rel),sha256=sha(src)))
assert {str(x.relative_to(S.parent))for x in S.parent.rglob('*')if x.is_file()}=={str(x.relative_to(C.parent))for x in C.parent.rglob('*')if x.is_file()}
r=dict(source_sha256=sha(S),prefill_sha256=sha(P),candidate_sha256=sha(C),retired_uuids=sorted(remove),retired_raw_records=dropped,only_declared_two_tracks_removed=True,all_remaining_raw_records_byte_identical=True,outside_records_only_whitespace_differences=True,all_12_zone_records_byte_identical=True,all_filled_polygon_coordinates_exact=True,strict_raw_plane_preservation_pass=True,all_918_vias_raw_exact=True,all_retained_footprint_and_pad_records_exact=True,all_1269_drills_retained_exact=True,all_zone_definitions_rules_settings_nets_exact=True,companion_file_count=len(companions),companion_manifest=companions,zone_record_sha256={uid(z):hashlib.sha256(z.encode()).hexdigest()for z in zones},raw_top_level_record_counts=[len(a),len(p),len(c)])
(O/'RAW_OBJECT_AND_ZONE_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['companion_manifest','zone_record_sha256','retired_raw_records']},indent=2))
SD=Path('/tmp/v7-c124-c-actual/qa/source-drc.json');CD=R/'qa/drc.json';s=json.loads(SD.read_text());c=json.loads(CD.read_text());key=lambda r:(r['type'],r['severity'],r['description'],tuple(sorted(i['uuid']for i in r['items'])));sv={key(r):r for r in s['violations']};cv={key(r):r for r in c['violations']};added=[cv[k]for k in cv.keys()-sv.keys()];removed=[sv[k]for k in sv.keys()-cv.keys()];assert not added and len(removed)==1 and removed[0]['type']=='track_dangling'and [x['uuid']for x in removed[0]['items']]==['68f95f8e-16e1-430a-a0b2-1c1d51d16fde'];erc=json.loads((R/'qa/erc.json').read_text());counts=dict(warnings=sum(x['severity']=='warning'for x in c['violations']),hard_errors=sum(x['severity']=='error'for x in c['violations']),opens=len(c['unconnected_items']),schematic_parity=len(c['schematic_parity']),erc=sum(len(x['violations'])for x in erc['sheets']));assert counts==dict(warnings=66,hard_errors=0,opens=12,schematic_parity=0,erc=0)
r=dict(source_sha256=sha(S),candidate_sha256=sha(C),source_drc_sha256=sha(SD),candidate_drc_sha256=sha(CD),native_counts=counts,only_removed_warning=removed[0],added_warnings=added,raw_open_rows_equal=s['unconnected_items']==c['unconnected_items'],semantic_open_pair_review='Pending fresh R2');(O/'NATIVE_PRELIMINARY.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
