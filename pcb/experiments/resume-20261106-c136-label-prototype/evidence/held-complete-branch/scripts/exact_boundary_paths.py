from pathlib import Path
import json,collections
from fractions import Fraction as F
D=Path('/workspace/shared/maru60-resume/continuation-9d787/branch4v');x=json.loads((D/'qa/boundary-delta.json').read_text());out={}
def paths(edges):
 succ=collections.defaultdict(list);pred=collections.Counter()
 for a,b in edges:a,b=tuple(a),tuple(b);succ[a].append(b);pred[b]+=1
 assert all(len(v)==1 for v in succ.values());result={};seen=set()
 for start in succ:
  if pred[start]:continue
  pts=[start];q=start
  while q in succ:
   seen.add((q,succ[q][0]));q=succ[q][0];pts.append(q)
  result[(start,q)]=pts
 cycles=[e for e in edges if tuple(map(tuple,e))not in seen];return result,cycles
def area2(pts):return sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(pts,pts[1:]+pts[:1]))
for layer,row in x.items():
 a,ac=paths(row['removed']);b,bc=paths(row['added']);rs=[]
 for key,old in a.items():
  if key not in b:rs.append({'unmatched_source_path':old});continue
  new=b[key];signed=F(area2(old+list(reversed(new))),2);rs.append({'source_path_nm':old,'candidate_path_nm':new,'exact_signed_area_between_paths_nm2':str(signed),'area_mm2':float(signed)/1e12,'net_signed_area_zero':signed==0})
 out[layer]={'matched_paths':rs,'source_cycles_or_untraced_edges':ac,'candidate_cycles_or_untraced_edges':bc,'unmatched_candidate_paths':[v for k,v in b.items()if k not in a],'interpretation':'Fracture edges were canceled as opposite-directed pairs first. Nonzero exact signed area between serialized paths proves a true represented boundary displacement, not a Boolean subtraction-only artifact. Zero net signed area alone does not prove identical boundaries.'}
(D/'qa/exact-boundary-paths.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
