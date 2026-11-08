from pathlib import Path
import sys,re,json,hashlib,shutil
sys.path.insert(0,'/tmp/v7-support-endpoint-trial/scripts');from sexpr_spans import children,head
R=Path('/tmp/v7-serial-legs-plus-two-labels');S=Path('/tmp/v7-support-endpoint-trial/filled/pcb');L=Path('/tmp/v7-two-label-corrected-7882/candidate/pcb');H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert H(S/'maru60.kicad_pcb')=='abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d';assert H(L/'maru60.kicad_pcb')=='99c2ef0ef03406fda6bff02d1d9dcf81712698eed2657514826593911b12c552';assert not R.exists();R.mkdir();(R/'scripts').mkdir();(R/'qa').mkdir();(R/'images').mkdir()
for stage in ['source','prefill']:shutil.copytree(S,R/stage/'pcb')
old=(S/'maru60.kicad_pcb').read_text();label=(L/'maru60.kicad_pcb').read_text();new=old;changes=[]
for ref in ['U18','L2']:
 sfp=next((a,z,t)for a,z,t in children(new)if head(t)=='footprint'and f'(property "Reference" "{ref}"'in t);lfp=next(t for a,z,t in children(label)if head(t)=='footprint'and f'(property "Reference" "{ref}"'in t);sa,sz,st=next((a,z,t)for a,z,t in children(sfp[2])if t.startswith('(property "Reference"'));lt=next(t for a,z,t in children(lfp)if t.startswith('(property "Reference"'));replacement=sfp[2][:sa]+lt+sfp[2][sz:];new=new[:sfp[0]]+replacement+new[sfp[1]:];changes.append({'reference':ref,'old_reference_raw':st,'new_reference_raw':lt})
(R/'prefill/pcb/maru60.kicad_pcb').write_text(new);shutil.copytree(R/'prefill/pcb',R/'filled/pcb')
manifest=lambda root:{str(p.relative_to(root)):{'sha256':H(p),'bytes':p.stat().st_size}for p in sorted(root.rglob('*'))if p.is_file()}
(R/'SOURCE_TREE_MANIFEST.json').write_text(json.dumps(manifest(S),indent=2)+'\n');(R/'PREFILL_TREE_MANIFEST.json').write_text(json.dumps(manifest(R/'prefill/pcb'),indent=2)+'\n')
contract={'status':'UNSELECTED exact two-Reference carry onto independently reviewed abdb','electrical_source_sha256':H(S/'maru60.kicad_pcb'),'label_source_sha256':H(L/'maru60.kicad_pcb'),'prefill_sha256':H(R/'prefill/pcb/maru60.kicad_pcb'),'changes':changes,'only_two_reference_fields':True,'selected_source_untouched':True,'full_graph_reexport_not_needed_if_exact_raw_reversion_passes':True,'no_qualification':True};(R/'BUILD_CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n');print(json.dumps(contract,indent=2))
