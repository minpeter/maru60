from screen import *
# Read-only finite inventory under ordinary 150um clearance, including all four layers.
def blockers(a):
 s=p.SHAPE_CIRCLE(V(*a),250000);bb=s.BBox();keys=set()
 for l in L:
  for x in range(bb.GetX()//1000000,bb.GetRight()//1000000+1):
   for y in range(bb.GetY()//1000000,bb.GetBottom()//1000000+1):keys.update(bins[l].get((x,y),()))
 return [{'uuid':k[0],'layer':b.GetLayerName(k[1]),'net':shapes[k][0],'gap_nm':s.GetClearance(shapes[k][1])}for k in keys if shapes[k][0]!='EXT_GPIO25'and s.GetClearance(shapes[k][1])<150000]
out={}
for name,(x0,y0,x1,y1) in {'J3':(93.3,39.8,94.5,40.8),'bridge':(97.5,40.1,98.8,41.2)}.items():
 rows=[]
 for x in range(round(x0*40),round(x1*40)+1):
  for y in range(round(y0*40),round(y1*40)+1):
   a=[x/40,y/40];rows.append({'point':a,'blockers':blockers(a)})
 out[name]=rows;clear=[r['point']for r in rows if not r['blockers']];print(name,len(clear),clear,flush=True)
(ROOT/'qa/SITE_INVENTORY.json').write_text(json.dumps(out,indent=2))
