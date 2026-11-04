from pathlib import Path
import re,json,hashlib,collections,copy
P=Path(__file__).resolve().parent;W=P.parent/'v7-safe-five-logo-recovered';Q=W/'qa';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
source=W/'input/maru60.kicad_pcb';candidate=W/'candidate-four/pcb/maru60.kicad_pcb';assert H(source)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1';assert H(candidate)=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
s=source.read_text();c=candidate.read_text();original=c
refs={'C100':('(at 0 1.4 90)','(at 0 -1.8 90)'), 'R140':('(at 0 1.43 90)','(at -0.2 -2.37 180)'), 'R160':('(at 0 1.43 90)','(at 0 -1.45 90)'), 'R134':('(at 0 1.43 0)','(at 0.6 -1.37 0)')};ids=[]
for ref,(old,new) in refs.items():
 pat=r'\n\t\t\(property "Reference" "'+ref+r'"\n.*?\n\t\t\)';a=re.findall(pat,s,re.S);b=re.findall(pat,c,re.S);assert len(a)==len(b)==1
 assert a[0].count('(size 0.75 0.75)')==1 and old in a[0]
 assert a[0].replace(old,new).replace('(size 0.75 0.75)','(size 0.8 0.8)')==b[0]
 ids.append(re.search(r'\(uuid "([^"]+)"',a[0]).group(1));c=c.replace(b[0],a[0],1)
def logo(txt):return next(b for b in re.findall(r'\n\t\(footprint\s.*?\n\t\)',txt,re.S) if '(property "Reference" "LOGO1"' in b)
a=logo(s);b=logo(c);oa=re.search(r'\n\t\t\(at [^)]*\)',a).group();ob=re.search(r'\n\t\t\(at [^)]*\)',b).group()
assert oa=='\n\t\t(at 193.413393 83.125 180)' and ob=='\n\t\t(at 85.326786 82.1 180)'
assert b.replace(ob,oa,1)==a;c=c.replace(b,a,1)
assert c==s,'Entire raw board byte restoration fails'
plan=read(W/'PLAN-four.json');smap={str(p.relative_to(W/'input')):H(p) for p in (W/'input').rglob('*') if p.is_file()};cmap={str(p.relative_to(W/'candidate-four/pcb')):H(p) for p in (W/'candidate-four/pcb').rglob('*') if p.is_file()}
assert smap==read(W/'SOURCE.json')['files_sha256'] and len(smap)==53
assert cmap==plan['candidate_file_map'] and len(cmap)==54
assert set(cmap)-set(smap)=={'maru60.kicad_prl'} and all(cmap[k]==v for k,v in smap.items() if k!='maru60.kicad_pcb')
pr=read(Q/'preview/PREVIEW_BINDING.json');assert pr['candidate_board_sha256']==H(candidate)
assert H(Q/'preview/candidate-four-preview.png')==pr['png_sha256']
assert H(Q/'SCREEN_COMPARISON.json')==pr['screen_comparison_sha256'] and H(Q/'candidate-four-ink.json')==pr['native_ink_sha256']
for row in pr['native_plot_and_panels']:
 if 'panel' in row:
  for ext in ('png','svg'):assert H(Q/f"preview/{row['panel']}.{ext}")==row[ext+'_sha256']
 else:assert H(Q/'preview/back-native.svg')==row['svg_sha256'] and row['exit_code']==0
si=read(Q/'source-ink.json');ci=read(Q/'candidate-four-ink.json');ni=read(Q/'source-native.json');nc=read(Q/'candidate-four-native.json')
assert si['board_sha256']==ni['board_sha256']==H(source) and ci['board_sha256']==nc['board_sha256']==H(candidate)
assert si['complete_mask_aperture_inventory']==ci['complete_mask_aperture_inventory'] and len(ci['complete_mask_aperture_inventory'])==1759
for k in set(ni)-{'board_sha256','private_xdg','footprint_placement'}:assert ni[k]==nc[k],k
expected=copy.deepcopy(si['all382_reference_typography']);assert len(expected)==382
for row in plan['reference_changes']:assert expected[row['reference']]==row['before'];expected[row['reference']]=row['after']
expected['LOGO1']['position_nm']=[a+b-c for a,b,c in zip(expected['LOGO1']['position_nm'],plan['logo_after']['position_nm'],plan['logo_before']['position_nm'])]
assert expected==ci['all382_reference_typography']
canon=lambda r:json.dumps(dict(r,items=sorted(r['items'],key=lambda x:x['uuid'])),sort_keys=True)
sd=read(Q/'source-drc.json');cd=read(Q/'candidate-four-drc.json');old=collections.Counter(map(canon,sd['violations']));new=collections.Counter(map(canon,cd['violations']))
assert len(sd['violations'])==92 and len(cd['violations'])==68 and not(new-old)
removed=[json.loads(k) for k,n in (old-new).items() for _ in range(n)];assert len(removed)==24
logoids=set(ci['whole_LOGO1']['polygon_uuids']);assert len(logoids)==2;allowed=set(ids)|logoids
assert all(any(i['uuid'] in allowed for i in r['items']) for r in removed)
assert len(sd['unconnected_items'])==len(cd['unconnected_items'])==12 and not sd['schematic_parity'] and not cd['schematic_parity']
assert all(r['severity']=='warning' for r in sd['violations']+cd['violations'])
# Native components/edges are compared exactly as recorded; full source-rooted physical reference proof is not asserted here.
result={'decision':'pass_actual_preview_association_and_raw_delta_screen','source_board_sha256':H(source),'candidate_board_sha256':H(candidate),'whole_source_board_bytes_restored_exactly_after_undoing_four_fields_and_logo_at':True,'all53_source_files_preserved_except_board':True,'candidate54th_metadata_explicitly_bound':True,'warning_counts':[92,68],'removed_records':removed,'removed_types':dict(collections.Counter(r['type'] for r in removed)),'new_warning_records':[],'all_removed_records_involve_a_changed_field_or_logo_polygon':True,'recorded_native_electrical_inventory_equal':True,'recorded_complete_mask_inventory_equal_count':1759,'all382_recorded_native_typography_matches_plan':True,'preview_binding_sha256':H(Q/'preview/PREVIEW_BINDING.json'),'preview_png_sha256':pr['png_sha256'],'visual_association_findings':{'C100':'Placed on the clear outward side of its own capacitor, with no intervening component.','R160':'Placed on the clear outward side of its own resistor instead of the original anchor over neighboring R159.','R134':'Placed immediately below its own resistor, outside its body.','R140':'Placed directly beside its owner. Nearby R144 remains distinguishable by its separate vertically oriented reference below. No crossed-component association like the rejected19-label bundle is visible.','LOGO1':'Both complete polygons remain together in the open region. No shape editing or split relocation.'},'scope_limits':['Visual judgment is based on the source-bound native preview, not confirmed assembled3D visibility.','Raw bytes and observed records were independently checked; no nativeCAD load/fill/save or new native geometry run occurred in this review.','The rebuilt ink checker and aggregate have not received a full adversarial/replay adoption review here. Native measurement claims remain producer observations, not an independent native rerun.','Existing unrelated warning/association issues, including unchanged R131/U12, remain visible and are not waived.','No physical/source-rooted graph regeneration, active simulation, full acceptance replay, hardware qualification or selection is claimed.'],'adoption_eligible':False,'selected':False}
(P/'review.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'sources.json').write_text(json.dumps({str(p.relative_to(W)):H(p) for p in [source,candidate,W/'PLAN-four.json',W/'SOURCE.json',W/'compare_screen.py',W/'native_ink.py',W/'native_electrical.py',Q/'SCREEN_COMPARISON.json',Q/'source-ink.json',Q/'candidate-four-ink.json',Q/'source-native.json',Q/'candidate-four-native.json',Q/'source-drc.json',Q/'candidate-four-drc.json',Q/'preview/PREVIEW_BINDING.json',Q/'preview/candidate-four-preview.png']},indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'candidate_sha256':H(candidate),'adoption_eligible':False},indent=2))
