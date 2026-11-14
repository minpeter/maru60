"""Cutout-aware 2-D heat-spreading sensitivity study on the current PCB.

Sheet conductance and heat transfer are swept assumptions, not measured case
properties. Every void in native board material plus drilled holes is removed.
No claim of package junction temperature or thermal shutdown timing is made.
"""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import splu
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.prepared import prep

def heat_pads(footprint, population):
 """Choose one occurrence of each power pad on mutually exclusive LED lands."""
 pads=[p for p in footprint['pads'] if p['net'] in ['GND','+4V_LED','+3V3','+4V_REG','VBUS_PROTECTED_RAW']]
 if footprint['ref'] in population:
  nums=sorted({p['num'] for p in pads})
  pads=[[p for p in pads if p['num']==n][population[footprint['ref']]] for n in nums]
 return pads

def mesh(material,step):
 x0,y0,x1,y1=material.bounds;xs=np.arange(x0,x1,step);ys=np.arange(y0,y1,step);cells=[];idx={};areas=[]
 prepared=prep(material)
 for iy,y in enumerate(ys):
  for ix,x in enumerate(xs):
   cell=box(x,y,x+step,y+step)
   area=step*step if prepared.covers(cell) else (material.intersection(cell).area if prepared.intersects(cell) else 0.)
   if area>1e-8:idx[(ix,iy)]=len(cells);cells.append((x+step/2,y+step/2));areas.append(area*1e-6)
 rows=[];cols=[];weights=[];diagonal=np.zeros(len(cells))
 for (ix,iy),i in idx.items():
  x,y=xs[ix],ys[iy]
  for shift,edge in [((1,0),LineString([(x+step,y),(x+step,y+step)])),((0,1),LineString([(x,y+step),(x+step,y+step)]))]:
   j=idx.get((ix+shift[0],iy+shift[1]))
   if j is None:continue
   fraction=1. if prepared.covers(edge) else material.intersection(edge).length/step
   if fraction<=0:continue
   diagonal[i]+=fraction;diagonal[j]+=fraction;rows.extend([i,j]);cols.extend([j,i]);weights.extend([-fraction,-fraction])
 rows.extend(range(len(cells)));cols.extend(range(len(cells)));weights.extend(diagonal)
 return np.array(cells),np.array(areas),coo_matrix((weights,(rows,cols)),shape=(len(cells),len(cells))).tocsc()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('geometry',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();g=json.loads(a.geometry.read_text());out=a.output;out.mkdir(parents=True,exist_ok=True)
 material=unary_union([Polygon(o[0],o[1:]) for o in g['board_material']]);drills=[]
 for f in g['fps']:
  for p in f['pads']:
   if p['drill'][0]>0:drills.append(Point(p['x'],p['y']).buffer(max(p['drill'])/2,16))
 for v in g['vias']:drills.append(Point(v['x'],v['y']).buffer(v['drill']/2,12))
 material=material.difference(unary_union(drills));fps={f['ref']:f for f in g['fps']}
 cases=[('LED_off',0.,.060,False),('typical_idle_plus_PWM_average',.1024,.060,False),('assumed_idle_stress',.128,.120,False),('limiter_maximum_DC',.234,.120,False),('LED_short_constant_limit_whatif',0.,.120,True)]
 populations=[{'LED14':a,'LED15':b} for a,b in itertools.product(range(2),repeat=2)]
 cases=[(label,iled,i33,short,pop) for pop in populations for label,iled,i33,short in cases]
 rows=[];maps={};transient=[]
 for step in [1.,.5]:
  positions,areas,L=mesh(material,step);powers=np.zeros((len(positions),len(cases)))
  def deposit(col,ref,power):
   f=fps[ref];pads=heat_pads(f,cases[col][4])
   xy=[(p['x'],p['y']) for p in pads] or [(f['x'],f['y'])]
   for point in xy:
    d2=np.sum((positions-point)**2,axis=1);near=np.where(d2<=max(1.,step)**2)[0]
    if not len(near):near=[int(np.argmin(d2))]
    weights=areas[near];powers[near,col]+=power/len(xy)*weights/weights.sum()
  for col,(label,iled,i33,short,pop) in enumerate(cases):
   deposit(col,'U1',3.3*i33);deposit(col,'U2',.7*i33+.0003)
   total4=4*(i33+(.234 if short else iled));deposit(col,'U18',total4*(1/.90-1))
   deposit(col,'U7',4*.234 if short else iled*iled*.135)
   deposit(col,'F1',(.3**2)*.165)
   if iled:
    for f in g['fps']:
     if f['ref'].startswith('LED'):deposit(col,f['ref'],4*iled/76)
  for sheet,h in itertools.product([.004,.010,.020],[2.,5.,10.]):
   K=sheet*L+diags(2*h*areas);lu=splu(K.tocsc());rise=lu.solve(powers)
   assert np.isfinite(rise).all() and rise.min()>-1e-7
   for col,(label,iled,i33,short,pop) in enumerate(cases):
    v=rise[:,col];imax=int(np.argmax(v));rows.append(dict(population=pop,grid_mm=step,sheet_W_per_K=sheet,face_heat_transfer_W_m2K=h,case=label,power_W=float(powers[:,col].sum()),maximum_rise_C=float(v.max()),mean_rise_C=float(np.average(v,weights=areas)),hotspot_xy_mm=list(positions[imax]),board_max_C_by_ambient={str(ta):float(ta+v.max()) for ta in [25,40,60,85]},numerical_energy_balance_error_W=float(abs((2*h*areas*v).sum()-powers[:,col].sum()))))
    if step==.5 and sheet==.010 and h==5.:maps[f'{label}_LED14-{pop["LED14"]}_LED15-{pop["LED15"]}']=v
   if step==.5 and sheet==.010 and h==5.:
    # 30 s backward Euler, 1 h, areal heat capacity ~3.4 kJ/m2/K.
    cap=3400*areas;dt=30.;solve=splu((K+diags(cap/dt)).tocsc());v=np.zeros(len(positions));load=powers[:,2]
    for iteration in range(121):
     transient.append([iteration*dt,float(v.max())])
     v=solve.solve(load+cap/dt*v)
  print('thermal mesh',step,len(positions),'nodes complete',flush=True)
  if step==.5:np.savez_compressed(out/'temperature-maps.npz',xy_mm=positions,area_m2=areas,**maps)
 report={'scope':__doc__,'geometry_sha256':hashlib.sha256(a.geometry.read_bytes()).hexdigest(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_window_count':sum(len(o)-1 for o in g['board_material']),'board_material_after_drills_mm2':material.area,'assumptions':{'uniform_sheet_conductance_W_K':[.004,.010,.020],'effective_heat_transfer_per_face_W_m2K':[2,5,10],'ambient_C':[25,40,60,85],'areal_heat_capacity_J_m2K':3400,'buck_efficiency':.90,'LED_electrical_power_as_heat':1.,'MCU_whole_3V3_load_placed_at_U1':True,'LED_heat_distribution':'uniform over 76 LEDs, one site at each reference; not PWM peak heating','package_junctions_and_case_contacts':'not modeled; supplier thermal parameters and assembled case boundary conditions needed'},'steady_cases':rows,'transient_nominal_model_assumed_idle_stress':transient}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('thermal cases',len(rows))
if __name__=='__main__':main()
