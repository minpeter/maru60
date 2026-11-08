import json,hashlib,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;P=R/'packet';P.mkdir(exist_ok=False)
def H(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
read=lambda n:json.loads((R/n).read_text());D=Path('/tmp/v7-buck-deadarm-trial-2c7e');J=Path('/tmp/v7-j3-unselected-closure-2c7e/qa');W=Path('/workspace/scratch/edd9a5be63e7');B=W/'pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb'
g=read('strip-geometry-review.json');rg=read('raw-graph-review.json');cl=read('contour-loss-audit.json');ls=read('loss-support-review.json');op=read('open-pair-review.json')
for name,path in [('selected',B),('copied_source',D/'source/pcb'),('prefill',D/'prefill/pcb'),('candidate',D/'filled/pcb')]:
 now={str(p.relative_to(path)):H(p) for p in sorted(path.rglob('*')) if p.is_file()};assert now==rg['complete_filemaps'][name]
files=['export_strip_native.py','source-strip.json','source-strip.log','candidate-strip.json','candidate-strip.log','compare_strip_geometry.py','strip-geometry-review.json','strip-geometry.log','audit_contour_loss.py','contour-loss-audit.json','contour-loss.log','audit_loss_supports.py','loss-support-review.json','loss-support.log','audit_raw_graph.py','raw-graph-review.json','raw-graph.log','audit_open_pairs.py','open-pair-review.json','open-pair.log','source-plan-verification.json','seal_review.py']
for name in files:shutil.copyfile(R/name,P/name)
# Preserve failed/aborted review attempts as provenance, not passing evidence.
A=P/'review-attempts';A.mkdir()
for name in ['export_native.py','source.log','candidate.log','compare_geometry_attempt1.py.txt','geometry_attempt1.log','export_full_native.py','source-full.log','candidate-full.log','compare_full_geometry.py','full-geometry.log','audit_contour_loss_attempt1.py.txt','contour-loss_attempt1.log']:
 shutil.copyfile(R/name,A/name)
omitted={name:{'sha256':H(R/name),'bytes':(R/name).stat().st_size,'reason':'Superseded/unused duplicate native exports; current bounded proof uses complete native bbox inventory plus all shapes in the proven full-board-width loss strip.'} for name in ['source.json','candidate.json','source-full.json','candidate-full.json']}
(P/'OMITTED_DUPLICATE_EXPORTS.json').write_text(json.dumps(omitted,indent=2)+'\n')
E=P/'bound-evidence';E.mkdir();bindings={}
inputs={'source-physical-graph.json':J/'source-physical-graph.json','source-drc.json':J/'fresh-source-drc.json','candidate-physical-graph.json':D/'qa/candidate-physical-graph.json','candidate-drc.json':D/'qa/drc.json','candidate-erc.json':D/'qa/erc.json','build.json':D/'qa/build.json','fill.json':D/'qa/fill.json','plan.json':Path('/tmp/v7-buck-deadarm-2c7e-plan/PLAN.json'),'historical-passive-README.md':W/'v7-recovered-library-20261104/extracted/v7-buck-feedback-study-20261104/README.md','historical-passive-ERRATUM.md':W/'v7-recovered-library-20261104/extracted/v7-buck-feedback-study-20261104/ERRATUM.md'}
for name,p in inputs.items():
 shutil.copyfile(p,E/name);assert H(E/name)==H(p);bindings[name]={'source_path':str(p),'packet_copy':str((E/name).relative_to(P)),'sha256':H(p),'bytes':p.stat().st_size}
for name,path in [('selected',B),('copied_source',D/'source/pcb'),('prefill',D/'prefill/pcb'),('candidate',D/'filled/pcb')]:bindings[name+'_board']={'source_path':str(path/'maru60.kicad_pcb'),'sha256':H(path/'maru60.kicad_pcb'),'all54file_map':'raw-graph-review.json:complete_filemaps:'+name}
(P/'SOURCE_BINDINGS.json').write_text(json.dumps(bindings,indent=2)+'\n')
f={'decision':'hold_unselected_strict_global_plane_loss_gate_failed','review_scope_completed':True,'source_sha256':g['source_sha256'],'candidate_sha256':g['candidate_sha256'],'bounded_cleanup_geometry_pass':True,'retired_uuids':g['retired_uuids'],'replacement_uuid':g['replacement_uuid'],'active_length_mm':1.95,'removed_dead_length_mm':2.85,'removed_drill_diameter_mm':.25,'counts_before':g['counts_before'],'counts_after':g['counts_after'],'all54_source_and_candidate_filemaps_rechecked_unchanged':True,'other_nonboard_files_exact':True,'all_other_raw_electrical_geometry_exact':True,'no_new_copper_outside_original_track':True,'all_three_feedback_pads_and_declared_contacts_preserved':True,'all245_net_pad_partitions_and_247_ground_root_pads_exact':True,'all731_plane_contact_identities_and_support_areas_exact':True,'retained_old_shadow_loss_mm2':0,'retained_segment_absolute_inherited_reference_gap_mm2':0.068332661731,'introduced_reference_gap_mm2':0,'strict_global_no_plane_loss':False,'global_loss_is_not_only_Boolean_artifact':True,'global_loss_native_reported_mm2':[x['reported_loss_mm2'] for x in cl['layers']],'exact_rational_real_loss_witnesses_by_layer':[x['polygons_with_exact_real_loss_witness'] for x in cl['layers']],'reported_loss_polygons_by_layer':[x['number_reported_loss_polygons'] for x in cl['layers']],'maximum_reported_sliver_enclosing_width_nm_upper_bound':max(x['max_enclosing_strip_width_nm_upper_bound'] for x in cl['layers']),'zero_operation_controls_per_layer':4,'loss_intersects_retained_physical_contact_support':False,'loss_intersects_removed_via_0_50mm_radius_region':False,'native_diagnostics':{'hard_errors':0,'warnings_before':68,'warnings_after':67,'exact_warning_removed':rg['native_DRC']['removed_exact_warning'],'new_warnings':0,'ERC_violations':0,'parity_violations':0,'unconnected_complete_component_pairs':12,'native_endpoint_representative_changes':4,'all48_native_endpoint_identities_and_geometry_validated':True},'qualification':{'selected_by_reviewer':False,'noise_improvement_proven':False,'loop_stability_proven':False,'SI_qualified':False,'hardware_qualified':False,'new_active_simulation':False,'cold_refill_replay_by_reviewer':False},'blocker':'At least one real positive-area subset of the original serialized inner plane is absent in the candidate outside the intended local restoration. No epsilon or old-shadow-only waiver has been applied.','next_condition':'Preserve this candidate. Either construct a separate result that meets the unchanged strict global no-loss condition and remeasure, or explicitly review/authorize a narrowly justified alternate serialization-geometry criterion before adoption. This review does not supply or authorize such a criterion.','numerical_limit':'Reported total loss areas and enclosing-width bounds describe native integer Boolean polygons. Exact rational interior witnesses establish real raw-contour loss, but do not claim the Boolean total is an exact rational integral of every changed sliver. Unproven slivers are not silently called real or discarded.','evidence':{name:H(P/name) for name in ['strip-geometry-review.json','contour-loss-audit.json','loss-support-review.json','raw-graph-review.json','open-pair-review.json','SOURCE_BINDINGS.json']}}
(P/'FINAL_REVIEW.json').write_text(json.dumps(f,indent=2)+'\n')
(P/'REVIEW.md').write_text('''# BUCK_FB dead-arm cleanup: hold unselected

Candidate `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f` is based on selected `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`, not the J3 experiment.

## Bounded cleanup succeeds

The degree-one via d382de57 and original 4.80 mm track 2c0aa2c5 are retired. Replacement 6ffab701 is exactly .15 mm F.Cu, (181,85.75) to (182.95,85.75): the 1.95 mm active portion, with no copper outside the old track. All three declared active contacts and U18.8/R159.2/R160.1 remain connected. Independent full-track-deletion control isolates U18.8, confirming why retaining the active portion is necessary.

Every other raw conductor, footprint, net and zone setting is exact. All 54-file maps were checked again at sealing; all non-board files are unchanged. Track count stays 9,752, vias fall 919→918, pads stay 1,437 and actual holes fall 1,270→1,269. Centerline length falls exactly 2.85 mm, from 13,181.60473138763 to 13,178.75473138763 mm. This is removed branch length, not a shortened U18-to-divider active path.

All 245 observed physical pad-net partitions, all 247 J1.A1-rooted GND pads and all 731 zone-contact identities/support areas are exact. Independent native FB intersections corroborate the critical branch. The original 68 warnings become 67 by removal of exactly the named dangling-via record, with no added warning. Observed hard errors, ERC and schematic parity remain zero. Twelve open complete endpoint-component pairs remain exact; all 48 reported endpoint UUIDs, native positions and descriptions were validated. Four representatives change (MCU_GPIO10/24/25/26), not their complete component pairs.

## Strict global plane condition fails

Outer fills are unchanged. Native saved-fill subtraction reports remote inner losses of 0.000000142282 mm² on In1 and 0.000000140974 mm² on In2, alongside gains of 0.641253861231 / 0.641253859923 mm². No threshold discards these losses.

The raw serialized contour coordinates exactly match the native exported coordinates. Exact rational point-in-polygon witnesses against those original contours, without Boolean clipping or epsilon, establish real source-inside/candidate-outside regions in 10 of 17 reported In1 slivers and 9 of 16 In2 slivers. Self-subtraction and identical-reparse controls are zero on both layers (eight controls total). Thus the result cannot be dismissed as only a Boolean artifact. Every reported sliver fits an enclosing strip no wider than 0.811799 nm. This is a geometric bound, not an assumed manufacturing tolerance or acceptance waiver. The native Boolean total is not asserted to be an exact rational integral of all slivers.

No retained full-width old shadow is lost. The replacement's absolute inherited reference gap is unchanged at 0.068332661731 mm²; newly introduced gap is zero. Neither result substitutes for the global plane requirement. Loss regions intersect no retained inner-layer physical contact support and do not intersect the .50 mm-radius region around the removed via. All source-root supports remain intact. These are consequence checks, not permission to ignore the contour change.

## Decision and next condition

**Hold unselected.** The strict no-global-plane-loss condition is not met. Preserve this candidate. A separate successor must meet the unchanged condition, or a narrowly justified alternate serialization-geometry criterion must be explicitly reviewed before adoption. This review neither invents an epsilon nor authorizes a new rule. It does not show the board is physically unsafe, but the specified strict gate has failed.

No quantified noise, pickup, stability, thermal, manufacturing, hardware or SI improvement is established. The historical passive FB study is not an active regulator model and warns that reducing shunt capacitance alone can increase edge pickup.

## Evidence and methods

`FINAL_REVIEW.json` provides the machine-readable decision; `SOURCE_BINDINGS.json` pins the actual boards, build/DRC/ERC and inherited graph observations. Native source and candidate geometry was independently exported in separate one-board/private-XDG processes, with no save or fill. The complete native bbox inventory plus a full-board-width strip (x0–300, y85.2–86.4 mm) covers every demonstrated loss and every possible affected shadow. No loss is omitted merely for being remote or small. Full copied geometry/graph/open records and exact contour witnesses are retained.

The first local-window review failed because remote losses fell outside its bounds. A full-board export was then completed, but an initial comparison launched before its candidate export existed and failed. Final bounded proof uses fresh board-wide strip exports and verifies the loss bounds explicitly; unused duplicate 366 MB exports are hash-listed rather than duplicated in this portable packet. An initial exact-contour probe was interrupted for quadratic rotation-comparison cost; the final algorithm preserves exact semantics and completes with all controls passing. Preserved review-attempt files document these events, not CAD failures or acceptance evidence.

The graph/DRC/ERC observations were rechecked and component partitions independently reconstructed; they are not claimed as a new complete native graph/DRC run by this reviewer. No cold refill or active simulation is claimed. Scripts retain original execution paths; board-dependent replay requires the matching boards supplied in the builder's packet. Pure exported-geometry checks can run in this packet with the native KiCad Python module.
''')
manifest={'schema':'independent-buck-deadarm-review-v1','decision':f['decision'],'candidate_sha256':f['candidate_sha256'],'files':{str(p.relative_to(P)):{'sha256':H(p),'bytes':p.stat().st_size} for p in sorted(P.rglob('*')) if p.is_file()}}
(P/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
z=R/'v7-buck-deadarm-independent-review.zip'
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as fz:
 for p in sorted(P.rglob('*')):
  if p.is_file():fz.write(p,'v7-buck-deadarm-independent-review/'+str(p.relative_to(P)))
with zipfile.ZipFile(z) as fz:
 assert fz.testzip() is None
 for name,m in manifest['files'].items():assert hashlib.sha256(fz.read('v7-buck-deadarm-independent-review/'+name)).hexdigest()==m['sha256']
print(json.dumps({'packet':str(P),'files':len(manifest['files']),'manifest_sha256':H(P/'MANIFEST.json'),'final_review_sha256':H(P/'FINAL_REVIEW.json'),'zip':str(z),'zip_sha256':H(z),'zip_bytes':z.stat().st_size},indent=2))
