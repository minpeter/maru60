import pathlib,json,hashlib
B=pathlib.Path('/workspace/scratch/edd9a5be63e7/maru60-push-recovery');S=B/'study';R=B/'repo';O=B/'study-validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
x=json.loads((S/'power-conditions/EVIDENCE.json').read_text()); errors=[n for n,h in x['source_hashes'].items() if not (R/n).is_file() or sha(R/n)!=h]
u=json.loads((S/'u18-land-pattern/source-hashes.json').read_text()); mapped={n.split('/selected-repo/')[1]:h for n,h in u.items() if '/selected-repo/' in n};ue=[n for n,h in mapped.items() if sha(R/n)!=h]
r=json.loads((O/'results.json').read_text());r['power_source_binding']={'count':len(x['source_hashes']),'errors':errors};r['u18_source_binding']={'cad_count':len(mapped),'errors':ue,'vendor_and_installed_library':'Not verified: unavailable external inputs'};(O/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(r['power_source_binding'],r['u18_source_binding'])
