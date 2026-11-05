exec(open('/workspace/shared/maru60-resume/continuation-c782/independent27/audit.py').read().split('a,b=maps')[0])
a,b=maps['base'],maps['header'];plan=json.loads((R/'header/qa/BUILD.json').read_text());added=set(b)-set(a);changed={u for u in a.keys()&b.keys() if a[u]!=b[u]};assert not set(a)-set(b);assert added==set(plan['added_uuids']);assert {u for u in changed if a[u][0]!='zone'}==set(plan['modified_source_uuids'])
for u in changed:
 x,y=a[u],b[u];fields={'filled_polygon','fill_segments'} if x[0]=='zone' else {'at'} if x[0]=='via' else {'start','end'};assert strip(x,fields)==strip(y,fields)
restored=[a[uid(x)] if uid(x) in a else x for x in parsed['header'] if uid(x) not in added];assert restored==parsed['base']
result={'source_to_header_added':len(added),'source_to_header_changed_conductors':len(plan['modified_source_uuids']),'exact_restoration_pass':True,'undeclared_fields_exact':True};(O/'header-scope.json').write_text(json.dumps(result,indent=2));print(result)
