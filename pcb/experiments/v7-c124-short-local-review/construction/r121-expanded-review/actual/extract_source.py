import pcbnew as p,pathlib,hashlib,json,re
D=pathlib.Path('/tmp/v7-c124-rebound-short/r121-expanded-review/actual');S=pathlib.Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb');C=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4/filled/pcb/maru60.kicad_pcb')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert sha(S)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1';assert sha(C)=='8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6'
def blocks(path,kind):
 s=path.read_text();r={};pat=re.compile(r'(?m)^\t\('+re.escape(kind)+r'(?=\s)');pos=0
 while True:
  m=pat.search(s,pos)
  if not m:break
  start=m.start()
  end=s.index('\n\t)\n',start)+4;raw=s[start:end];u=re.search(r'\(uuid "([^"]+)"\)',raw).group(1);r[u]=hashlib.sha256(raw.encode()).hexdigest();pos=end
 return r
raw={'source_sha256':sha(S),'candidate_sha256':sha(C)}
for kind in ['zone','segment','via','footprint']:
 a,c=blocks(S,kind),blocks(C,kind);shared=a.keys()&c.keys();raw[kind]={'source_count':len(a),'candidate_count':len(c),'removed':sorted(a.keys()-c.keys()),'added':sorted(c.keys()-a.keys()),'changed':[u for u in shared if a[u]!=c[u]],'unchanged_count':sum(a[u]==c[u]for u in shared)}
 if kind=='zone':raw[kind]['source_hashes']=a;raw[kind]['candidate_hashes']=c
(D/'raw_source_candidate_delta.json').write_text(json.dumps(raw,indent=2)+'\n')
b=p.LoadBoard(str(S));fs={f.GetReference():f for f in b.GetFootprints()};idx={q.m_Uuid.AsString():q for q in b.GetTracks()};cp=next(q for q in fs['C124'].Pads()if q.GetNumber()=='2')
def poly(s,loc):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,loc);return z
def shape(q,loc):
 z=poly(q.GetEffectiveShape(p.B_Cu),loc)
 if q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_INSIDE if loc==p.ERROR_OUTSIDE else p.ERROR_OUTSIDE))
 return z
def dump(z):
 ring=lambda q:[[q.CPoint(i).x,q.CPoint(i).y]for i in range(q.PointCount())]
 return [{'outer':ring(z.COutline(i)),'holes':[ring(z.CHole(i,j))for j in range(z.HoleCount(i))]}for i in range(z.OutlineCount())]
result={'source_sha256':sha(S),'supports':[]}
for u in ['19181a2b-164e-4055-9004-2860bebe32f4','763086b7-5549-4f5e-bb08-ce25387b3627']:
 row={'uuid':u}
 for name,loc in [('inside',p.ERROR_INSIDE),('outside',p.ERROR_OUTSIDE)]:
  z=shape(cp,loc);z.BooleanIntersection(shape(idx[u],loc));row[name]={'area_mm2':z.Area()/1e12,'polygon_nm':dump(z)}
 result['supports'].append(row)
(D/'source_support_polygons.json').write_text(json.dumps(result)+'\n');print('source support extracted; raw source/candidate deltas',json.dumps({k:v for k,v in raw.items()if k not in['zone']},indent=2));print('zone unchanged',raw['zone']['unchanged_count'])
