from pathlib import Path
import json,hashlib,collections,csv,re
r=Path(__file__).resolve().parent;source=r.parent/'pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/qa/recovery-native/drc.json';d=json.loads(source.read_text());native=json.loads((r/'native-dangling-contacts.json').read_text());contacts={x['uuid']:x for x in native['rows']}
notes={
'68f95f8e-16e1-430a-a0b2-1c1d51d16fde':('Local GND open-ended stub, 0.1000 mm. Immediate contact to an existing F.Cu GND track is confirmed; this does not qualify the return path.','Retain until a bounded trim or useful return connection proves original rooted GND and reference requirements. Removing a warning is not the same as improving ground.'),
'bc0a06ab-785a-4a27-a164-9c3256c7f3bd':('Connector-region GND open-ended stub, 0.9500 mm, directly contacts the existing GND via at (15.70,9.80).','Review together with connector return geometry. Existing between-signal-via neck discontinuity remains; this stub or a new stitch cannot be described as restoring that neck.'),
'53e7b99f-308f-57ae-9e47-9e779e6b3272':('Retained original C128 supply stub. C128 itself was relocated and connected; the 2.248399 mm warned segment belongs to the longer retained rooted supply branch.','No blind removal or damping change. The recovered C128 PDN study includes conditional antiresonance and unknown component/parasitic ranges; any trim needs before/after topology, reference and model comparison.'),
'1e6f9b6e-9a22-418a-8cde-6feb5aafb26e':('VBUS via has two immediate B.Cu track contacts and no direct pad contact; the native warning concerns lack of a useful second-layer connection, not an isolated VBUS pad.','Keep as open cleanup candidate. Any removal must preserve the overlapping active VBUS tracks and all required pad connectivity; no hardware reliability benefit inferred.'),
'b04e3a6d-1e98-43d1-9b10-58c23321ca28':('USB_DM_CONN open-ended 0.4375 mm F.Cu branch. It contacts the active F.Cu trace and transition via at (18,12.4).','A bounded branch trim could be tested, but do not remove its active junction/via. Require full USB topology, saved-reference preservation and explicit updated reduced-model inputs before a signal-quality claim.'),
'acf57724-d322-4087-84ab-2893c779cea3':('Open-ended +4V_REG F.Cu branch, 1.555635 mm, immediately connected to the active rail segment ending at (23.7,19.65).','No blind deletion. A bounded trim must preserve source-to-load and old-reference requirements. It is not a fix for the unresolved input/buck headroom and brownout contract.'),
'd382de57-3476-43c4-ac26-0a72b21acf7c':('BUCK_FB via has exactly one immediate F.Cu track contact. The recovered dedicated study proves the 4.80 mm track contains a 2.85 mm dead arm and a 1.95 mm active divider-to-U18 section.','Never delete the whole 4.80 mm segment. Via-only removal can exchange this for a dangling-track warning. A bounded dead-arm trim needs native/fill/reference checks; lower shunt capacitance alone is not a guaranteed noise/stability improvement.')}
rows=[]
for i,v in enumerate(d['violations'],1):
 ids=sorted(x['uuid']for x in v['items']);typ=v['type'];canonical=json.dumps({'type':typ,'items':v['items'],'description':v['description']},sort_keys=True);identity=hashlib.sha256(canonical.encode()).hexdigest();
 if typ in ['track_dangling','via_dangling']:
  obs,action=notes[ids[0]];priority='electrical_review';detail=contacts[ids[0]]
 elif typ=='text_height':
  obs='The native reference/text-height rule is violated. This is an unresolved fabrication/readability warning, not an electrical open.';action='Increase or relocate only after exact ink/mask/silk/courtyard checks and unambiguous component association. Preserve accepted labels and circuit placement.';priority='legibility';detail=None
 elif typ=='silk_overlap':
  obs='Native silkscreen objects overlap. Whether a safe drawing/reference/logo move resolves it must be checked on actual ink and component association.';action='Test an isolated label or intact-logo move. Reject ambiguous ownership even when warning totals fall; preserve unrelated objects.';priority='legibility';detail=None
 elif typ=='silk_over_copper':
  obs='Native silkscreen overlaps an exposed-copper/mask area. It is not a copper-clearance error, but the marking can be clipped or obscure assembly identification.';action='Check complete actual mask apertures and ink, not only pad bounding boxes. Move only with readable association and no new overlaps.';priority='assembly_marking';detail=None
 else:raise AssertionError(typ)
 rows.append({'index':i,'warning_identity_sha256':identity,'type':typ,'severity':v['severity'],'status':'open_not_waived','priority':priority,'items':v['items'],'native_description':v['description'],'review_disposition':obs,'next_action':action,'native_immediate_contact_evidence':detail})
assert len(rows)==92 and len({x['warning_identity_sha256']for x in rows})==92
report={'board_sha256':native['board_sha256'],'drc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'total_warnings':len(rows),'categories':dict(collections.Counter(x['type']for x in rows)),'all_warning_records_accounted':True,'all_warnings_open_not_waived':True,'electrical_warnings_with_fresh_native_immediate_contact_evidence':7,'scope':'Every fresh native warning is individually enumerated and given a category-specific or object-specific review disposition. This is not a statement that all underlying physical risks are solved.','rows':rows};(r/'warning-register.json').write_text(json.dumps(report,indent=2)+'\n')
with (r/'warning-register.csv').open('w',newline='')as f:
 w=csv.writer(f);w.writerow(['index','identity','type','status','priority','objects','disposition','next action'])
 for x in rows:w.writerow([x['index'],x['warning_identity_sha256'],x['type'],x['status'],x['priority'],' | '.join(t['description']+' '+t['uuid']for t in x['items']),x['review_disposition'],x['next_action']])
(r/'README.md').write_text('''# Recovered V7 warning review

Source: exact selected board 7c23d6ea, freshly checked with KiCad 9.0.2. All 92 warning records have unique source-bound identities and explicit dispositions in JSON/CSV: 28 text-height, 31 silk overlap, 26 silk-over-mask, 5 dangling tracks and 2 dangling vias. None is waived or marked electrically qualified.

The seven electrical warnings were freshly re-extracted from the actual board using read-only native immediate track/pad connectivity. This is not a complete all-net geometric graph replay or an SI/PDN proof. The native source bytes are unchanged.

Highest-consequence review items remain the USB_DM branch/connector return, retained C128 supply stub with conditional PDN resonance, and BUCK_FB dead arm. Do not delete active junctions or interpret reduced warning count/capacitance as better stability. The two GND stubs, VBUS via and +4V_REG stub have explicit preservation requirements as well.

Typography and intact-logo candidates are handled in separate experiments, including complete ink/mask geometry and visual association. The original 108-warning packet is missing; this is a new 92-warning register for the exactly recovered selected board, not a recreated historical packet.

The reused C128 PDN and BUCK_FB findings come from recovered source-bound archives whose native input board 8a4ff6a6 matches the recovered chain. Their numerical assumptions and qualification limits remain in those packets; no new physical simulation is asserted here.
''')
manifest={str(f.relative_to(r)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in sorted(r.iterdir())if f.is_file()and f.name!='MANIFEST.json'};(r/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'warnings':92,'electrical':7,'categories':report['categories']}))
