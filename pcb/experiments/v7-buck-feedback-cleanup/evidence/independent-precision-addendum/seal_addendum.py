import json,hashlib,shutil,zipfile,math
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parent;P=R/'packet';P.mkdir(exist_ok=False);S=Path('/tmp/v7-buck-deadarm-independent-review/packet');C=Path('/tmp/v7-buck-deadarm-trial-2c7e/filled/pcb/maru60.kicad_pcb');B=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb')
def H(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
read=lambda p:json.loads(p.read_text());strict=read(S/'MANIFEST.json');assert H(S/'MANIFEST.json')=='d44a930febcfe545cedae062c2649b952225778cca0603bfbf0a480b63fbee6f'
for n,d in strict['files'].items():assert H(S/n)==d['sha256']
assert H(B)=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373' and H(C)=='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f'
M=read(R/'material-coverage-proof.json');Q=read(R/'qualified-invariant-review.json');V=read(R/'remote-rule-review.json');assert M['candidate_specific_proposed_1_nm_criterion_pass'] and Q['original_no_old_shadow_loss_and_root_support_conditions_pass'] and V['all_remote_patch_hulls_clear_correctly_typed_copper_and_holes_at_unchanged_normal_rules'];E=read(R/'boundary-envelope-proof.json')
# Explicitly verify both observed normal-refill controls against actual board bytes.
bindings={}
for name,root,expected in [('source-noedit',Path('/tmp/v7-buck-deadarm-noedit-control'),H(B)),('candidate-repeat',Path('/tmp/v7-buck-deadarm-repeat-control'),H(C))]:
 d=read(root/'RESULT.json');assert d['source_sha256']==d['noedit_normal_refill_sha256']==expected==H(root/'pcb/maru60.kicad_pcb');assert all(z['raw_native_vertices_identical'] and z['loss_mm2']==z['gain_mm2']==0 for z in d['zone_controls']);dest=P/'bound-controls'/name;dest.mkdir(parents=True)
 for n in ['RESULT.json','control.py','control.log']:
  shutil.copyfile(root/n,dest/n);bindings[name+'/'+n]={'source_path':str(root/n),'sha256':H(root/n),'packet_path':str((dest/n).relative_to(P))}
 if (root/'NATIVE_GRID.json').exists():shutil.copyfile(root/'NATIVE_GRID.json',dest/'NATIVE_GRID.json')
 bindings[name+'/board']={'source_path':str(root/'pcb/maru60.kicad_pcb'),'sha256':expected}
# Main proof records, plus exploratory probes preserved distinctly.
main=['prove_boundary_envelope.py','boundary-envelope-proof.json','prove_material_coverage.py','material-coverage-proof.json','material-coverage.log','verify_remote_rules.py','remote-rule-review.json','remote-rule.log','verify_remote_invariants.py','remote-invariant-review.json','remote-invariant.log','qualify_invariants.py','qualified-invariant-review.json','qualified-invariant.log','native-grid-independent.json','optimized-python-controls.json','seal_addendum.py']
for n in main:shutil.copyfile(R/n,P/n)
exp=P/'exploratory-probes';exp.mkdir()
for n in ['examine_boundary_cycles.py','raw-change-inventory.json','boundary-cycle-inventory.json','verify_remote_obstacles.py','remote-obstacle-review.json','remote-obstacle.log','verify_remote_distances.py','remote-distance-review.json','remote-distance.log','verify_remote_invariants_preload_failure.py.txt','remote-invariant-preload-failure.log']:
 shutil.copyfile(R/n,exp/n)
prior=P/'prior-strict-pins';prior.mkdir()
for n in ['MANIFEST.json','FINAL_REVIEW.json','SOURCE_BINDINGS.json']:
 shutil.copyfile(S/n,prior/n);bindings['strict/'+n]={'source_path':str(S/n),'sha256':H(S/n),'packet_path':str((prior/n).relative_to(P))}
for n in ['source-strip.json','candidate-strip.json','raw-graph-review.json','open-pair-review.json']:
 bindings['strict/'+n]={'source_path':str(S/n),'sha256':H(S/n),'provided_in_accompanying_prior_strict_packet':True}
bindings['source_board']={'path':str(B),'sha256':H(B)};bindings['candidate_board']={'path':str(C),'sha256':H(C)};bindings['project']={'path':str(C.with_suffix('.kicad_pro')),'sha256':H(C.with_suffix('.kicad_pro'))};(P/'SOURCE_BINDINGS.json').write_text(json.dumps(bindings,indent=2)+'\n')
worst=max((p for l in E['layers'] for p in l['patches']),key=lambda p:F(p['maximum_distance_squared_nm2']));area={l['layer']:{'remote_loss_nm2_exact':l['remote_loss_nm2_exact'],'remote_gain_nm2_exact':l['remote_gain_nm2_exact'],'local_gain_nm2_exact':l['local_gain_nm2_exact'],'remote_loss_mm2_approx':float(F(l['remote_loss_nm2_exact']))/1e12,'remote_gain_mm2_approx':float(F(l['remote_gain_nm2_exact']))/1e12,'local_gain_mm2_exact_decimal':'0.641253345104','raw_total_signed_area_delta_nm2_exact':l['raw_signed_area_delta_nm2_exact']} for l in M['layers']}
gap_rows=[p for l in V['layers'] for q in l['patches'] for p in q['tested_nearby_obstacles']];minholes=min(q['new_boundary_gap_native_bracket']['last_noncollision_nm'] for q in gap_rows if q['kind']=='actual_drill_hole');mincopper=min(q['new_boundary_gap_native_bracket']['last_noncollision_nm'] for q in gap_rows if q['kind']=='foreign_inner_copper');assert minholes>=150000 and mincopper>=200000
receipt={'decision':'pass_authorized_candidate_specific_1nm_precision_criterion_pending_fresh_final_recheck','source_sha256':H(B),'candidate_sha256':H(C),'old_strict_global_no_loss_result':'FAIL; unchanged and still true','prior_strict_manifest_sha256':H(S/'MANIFEST.json'),'criterion_application_authorized_by_parent':'2026-11-04 11:19:55 UTC; exact aead candidate only','candidate_specific_precision_criterion_pass':True,'final_adoption_eligible':False,'pending':'Fresh final physical graph, DRC/parity and ERC recheck, followed by separate parent selection decision. No selection made by reviewer.','criterion':{'scope':'Only exact2c7→aead dead-arm cleanup under unchanged saved native rules and remote obstacle geometry.','bound_nm':1,'remote_region':'All source-only and candidate-only saved material differences except the exact original removed-via hole polygon. No local-region expansion.','required_invariants':['Exact unchanged other conductor/footprint/drill/net/zone/project geometry','Every remote difference point within1nm of opposite true saved-material closure/boundary, both directions','Zero loss at every original non-GND full-width shadow and every retained rooted/physical contact support','Unchanged normal clearance/hole rules, native DRC/parity/ERC and complete physical partitions','Both exact source and candidate observed as byte-identical normal-refill fixed points'],'explicit_engineering_precision_criterion_not_automatic_native_rule':True},'proof':{'remote_patches_per_layer':51,'exact_disjoint_difference_cells_per_layer':181,'actual_material_boundary_segment_tests_per_layer':208,'maximum_constructive_opposite_material_distance_squared_nm2_exact':M['maximum_exact_opposite_material_distance_squared_nm2'],'maximum_constructive_distance_upper_bound_nm':M['maximum_distance_bound_nm'],'worst_source_point_mm':[float(F(v))/1e6 for v in worst['witness_old']],'explicit_opposite_boundary_point_mm':[float(F(v))/1e6 for v in worst['witness_new']],'complete_raw_area_identity_verified':True,'areas':area},'native_grid':{'integer_IU_per_mm':1000000,'IU_nm':1,'integer_vertices_can_encode_real_sub_nm_slivers':True},'clearance_and_support':{'foreign_inner_copper_rule_nm':200000,'hole_rule_nm':150000,'minimum_native_new_copper_last_noncollision_nm':mincopper,'minimum_native_new_hole_last_noncollision_nm':minholes,'no_copper_or_hole_intrusion':True,'all_exact_loss_bands_clear_old_outer_shadows_with_2nm_native_guard':True,'all_exact_loss_and_gain_bands_clear_retained_inner_GND_contact_copper_with_2nm_native_guard':True,'one_gain_only_patch_adds_reference_under_existing_outer_shadows':True,'all731_plane_contact_ids_and_support_areas_exact':True,'all247_rooted_GND_pads_exact':True,'all245_observed_net_pad_partitions_exact':True},'controls':{'material_geometry_checks':11,'wrong_gain_to_loss_classification_rejected':True,'optimized_Python_scripts_rejected_before_work':5,'native_collision_primitive_controls':3,'observed_normal_refill_fixed_points':2},'limitations':['The strict mathematical zero-loss gate still fails. This applied alternate criterion does not erase or relabel the real slivers.','The0.733693794nm number is an exact constructive upper bound to the opposite material, not a claimed exact nearest-point Hausdorff maximum.','Vertex-grid scale motivates a narrowly scoped engineering precision criterion; it is not a manufacturing tolerance or proof of electrical equivalence.','No quantified pickup/noise/loop-stability/SI/hardware/manufacturing improvement.','Proof and controls are candidate-specific, not a general validated production checker.','No six-copy cold replay or new active SPICE result is claimed.'],'evidence':{n:H(P/n) for n in ['material-coverage-proof.json','boundary-envelope-proof.json','remote-rule-review.json','qualified-invariant-review.json','native-grid-independent.json','SOURCE_BINDINGS.json']}}
(P/'FINAL_PRECISION_REVIEW.json').write_text(json.dumps(receipt,indent=2)+'\n')
(P/'REVIEW.md').write_text('''# Candidate-specific coordinate-precision review

**Exact aead candidate passes the separately authorized 1 nm criterion. Final fresh graph/DRC/parity/ERC recheck and parent selection are still pending. The original strict global zero-loss result remains FAIL, unchanged.**

Source: `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`.
Candidate: `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`.

## Applied criterion and rationale

For this exact cleanup only, retain every prior source/contact/root/reference/clearance requirement, but assess the remote serialization differences using a bilateral 1 nm distance-to-opposite-material bound. The only larger local gain permitted is the exact original saved hole polygon belonging to the retired via. It is not enlarged; the .50 mm radius used in consequence checks is merely a containment check, not extra permission.

The installed API uses 1,000,000 integer internal units per mm: one native coordinate unit is 1 nm (`PCB_IU_PER_MM`, `FromMM`, `ToMM`, integer `VECTOR2I`). Wrapper/native-library hashes and exact KiCad9.0.2+dfsg-1 are recorded. **Integer vertices can encode real sub-nm transverse slivers.** The criterion does not claim those slivers are nonexistent, unrepresentable, or mathematically zero. One native grid unit is an explicitly chosen engineering precision bound, not an automatic rule or a manufacturing/electrical tolerance.

The justification also depends on exact unchanged remote obstacle geometry and rules, deterministic source/candidate normal refills, strict zero old-shadow loss and contact/root preservation. It is not justified by thinness alone.

## Exact bilateral material proof

Exact reverse fracture edges cancel algebraically; no rounding or approximate simplification is used. All remaining directed edges partition into closed cycles. Source/candidate cycles differ by exactly one removed local hole plus 51 remote patches per layer. Each patch is split at exact longitudinal breakpoints and crossings into convex rational cells: 181 disjoint cells per layer.

Every opposite chain is proved to be a genuine material boundary, with no nonadjacent crossing/overlap and exact sided membership. All other boundaries are excluded from cell interiors. Each cell has constant source-only or candidate-only classification, cells are pairwise interior-disjoint, and their exact areas plus the local hole reproduce the full raw signed-area difference. Thus no remote loss or gain is omitted.

For every point in every remote difference cell, a finite-segment point on the opposite saved-material boundary is explicitly available at the same longitudinal coordinate. The perpendicular separation is piecewise linear; checking all exact knots proves the whole cell, not a sampled approximation. The squared maximum constructive bound is `20946193984/38911272217 nm²`, giving **0.733693793701 nm**, below1nm. This is an upper bound on nearest opposite-material distance, not a claimed exact Hausdorff maximum. A worst witness lies at source (148.545580000000,85.664891000000) mm, paired to (148.545579280404,85.664890856861) mm.

Exact raw material areas per layer are:
- Remote source-only loss: approximately0.000000336086505284 mm².
- Remote candidate-only gain: approximately0.000000806539005284 mm².
- Local recovered original hole: exactly0.641253345104 mm².

Fractions and every cell/vertex are retained. These exact areas differ from the prior native integer-Boolean report because that operation rounds intersection vertices. Both results are preserved; the earlier nonzero-loss conclusion is not rewritten.

## Strict conditions retained

All exact loss bands are clear of every original non-GND outer reference shadow, with a conservative2nm native guard. All loss and gain bands are clear of retained inner-GND contact copper. One entirely gain-only patch adds plane coverage beneath three existing front power shadows and one back ROW0 shadow; it contains no source-only loss. A control deliberately reclassifying that patch as loss is rejected.

All731 physical plane-contact identities/support areas, all247 J1.A1-rooted GND pads and all245 pad-net partitions remain exact. Native hard errors/ERC/parity remain0, the same12 complete open pairs remain, and precisely the named via warning disappears (68→67). These previously checked observations await the requested fresh final repetition.

Conservative integer convex hulls enclose both loss and gain cells. Fresh native obstacle tests consider all actual holes and foreign inner copper, with NPTH pads treated as holes rather than phantom copper disks. Correct unchanged limits are .20mm for zone-to-foreign-copper and .15mm for holes. Minimum native last-noncollision brackets are at least .200499mm and .150499mm, respectively; no material enters copper or holes. Source-to-candidate brackets move by no more than one native unit. The initial exploratory uniform .20mm test was overbroad for holes; its failed result is preserved, not presented as a rule failure or silently discarded.

The exact selected source and candidate each independently survive one no-electrical-edit normal refill byte-for-byte. These are builder-executed fixed-point controls whose actual board bytes, code, logs and results were independently rechecked, not six-copy replay or reviewer-performed refills. They show this is a geometry-change-induced serialization difference, not generic repeated-fill drift.

## Scope, controls and reproduction

The old strict packet and its hash manifest are unchanged. This is an additive candidate-specific assessment, authorized separately, not a generic validated checker. Larger2nm loss/gain controls, a thin displaced strip with mismatched endpoints, nonmonotone chains, boundary/interior/overlap tests and gain/loss misclassification controls exercise the proof. Optimized Python is refused before work in five scripts. Native collision controls verify the obstacle calls.

No source/candidate CAD was edited. No noise, pickup, active-loop stability, SI, hardware or manufacturing benefit is inferred. A native-grid criterion cannot establish those outcomes.

`FINAL_PRECISION_REVIEW.json` records the decision and pending final recheck. `SOURCE_BINDINGS.json` pins the prior strict packet, boards and fixed-point controls. For pure reproduction, set `BUCK_STRICT_PACKET` to the accompanying unpacked strict-review packet, then run the proof scripts with normal Python (not `-O`). Native obstacle scripts need the matching candidate project and KiCad Python. Their original paths are preserved in code. Private runtime homes are excluded. The pre-load syntax failure and exploratory stronger probes are preserved separately and are not passing evidence.
''')
manifest={'schema':'buck-candidate-specific-precision-addendum-v1','source_sha256':H(B),'candidate_sha256':H(C),'prior_strict_manifest_sha256':H(S/'MANIFEST.json'),'files':{str(p.relative_to(P)):{'sha256':H(p),'bytes':p.stat().st_size} for p in sorted(P.rglob('*')) if p.is_file()}}
(P/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');z=R/'v7-buck-precision-criterion-addendum.zip'
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
 for p in sorted(P.rglob('*')):
  if p.is_file():f.write(p,'v7-buck-precision-criterion-review/'+str(p.relative_to(P)))
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None
 for n,d in manifest['files'].items():assert hashlib.sha256(f.read('v7-buck-precision-criterion-review/'+n)).hexdigest()==d['sha256']
print(json.dumps({'packet':str(P),'files':len(manifest['files']),'manifest_sha256':H(P/'MANIFEST.json'),'receipt_sha256':H(P/'FINAL_PRECISION_REVIEW.json'),'zip':str(z),'zip_sha256':H(z),'bytes':z.stat().st_size},indent=2))
