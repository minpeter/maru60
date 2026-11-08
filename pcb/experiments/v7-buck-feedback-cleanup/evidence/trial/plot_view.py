import os
os.environ['MPLCONFIGDIR']='/tmp/v7-buck-deadarm-trial-2c7e/mplconfig'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch,Patch
import pathlib,json,hashlib
D=pathlib.Path(__file__).parent;r=json.load(open(D/'qa/local-native-view.json'));ledger=json.load(open(D/'qa/build.json'));ret={q['uuid']for q in ledger['retired_objects']};new=ledger['new_objects'][0]['uuid'];fig,axs=plt.subplots(2,2,figsize=(15,11));fig.patch.set_facecolor('#f5f7fa')
for i,phase in enumerate(['source','filled']):
 for j,l in enumerate(['F.Cu','B.Cu']):
  ax=axs[i,j];ax.set_title(('Selected source2c7'if phase=='source'else'UNSELECTED aead trial')+' • '+l,fontsize=12,fontweight='bold')
  for q in r[phase]['layers'][l]:
   color='#c52f55'if phase=='source'and q['uuid']in ret else '#007ea8'if q['uuid']==new else '#ba8c28'if q['net']=='BUCK_FB'else '#82a590'if q['net']=='GND'else '#b8bec6';alpha=1 if q['net']=='BUCK_FB'else .55
   for z in q['poly']:
    verts=[];codes=[]
    for ring in[z['o']]+z['h']:
     if len(ring)<3:continue
     verts+=ring+[ring[0]];codes+=[Path.MOVETO]+[Path.LINETO]*(len(ring)-1)+[Path.CLOSEPOLY]
    if verts:ax.add_patch(PathPatch(Path(verts,codes),facecolor=color,edgecolor='none',alpha=alpha,zorder=3 if q['net']=='BUCK_FB'else 1))
  ax.set_xlim(176.8,185.3);ax.set_ylim(88,82);ax.set_aspect('equal');ax.grid(color='#e2e7ed',linewidth=.4);ax.set_xlabel('Board X (mm)');ax.set_ylabel('Board Y (mm)')
  if j==0:
   ax.annotate('Dead-arm via'+(' removed'if phase=='filled'else''),(178.15,85.75),xytext=(177.1,87.45),arrowprops=dict(arrowstyle='->',color='#a72a48'),fontsize=10,color='#a72a48',bbox=dict(fc='white',ec='none',alpha=.9))
   ax.annotate('Active tap retained',(181,85.75),xytext=(180.3,87.5),arrowprops=dict(arrowstyle='->',color='#007ea8'),fontsize=10,color='#007ea8',bbox=dict(fc='white',ec='none',alpha=.9))
   if phase=='filled':ax.text(181.15,85.5,'1.95 mm active',fontsize=9,color='#006884',bbox=dict(fc='white',ec='none',alpha=.85))
fig.suptitle('UNSELECTED BUCK_FB cleanup • strict global plane-preservation FAIL',fontsize=18,fontweight='bold',y=.98)
fig.text(.5,.947,'Candidate: 9,752 tracks | 918 vias | 12 unchanged opens | 67 warnings (one removed) | parity/ERC: 0',ha='center',fontsize=11)
fig.legend([Patch(color='#c52f55'),Patch(color='#007ea8'),Patch(color='#ba8c28'),Patch(color='#82a590')],['Retired objects in source','Replacement active segment','Retained BUCK_FB','GND'],loc='lower center',ncol=4,bbox_to_anchor=(.5,.115),frameon=False)
fig.text(.5,.09,'Native outer-copper geometry, same X/Y on both sides. Subnanometre remote inner-plane losses are not visible at this scale.',ha='center',fontsize=10)
fig.text(.5,.065,'No selection, epsilon waiver, noise or loop-stability improvement claim.',ha='center',fontsize=11,color='#a72a48')
fig.text(.5,.035,'Candidate SHA-256: '+r['filled']['board_sha256'],ha='center',fontsize=9,family='monospace')
fig.subplots_adjust(top=.91,bottom=.18,left=.05,right=.98,hspace=.22,wspace=.15);out=D/'qa/source-vs-unselected-buck-cleanup.png';fig.savefig(out,dpi=165);(D/'qa/LOCAL_VIEW_BINDING.json').write_text(json.dumps(dict(source_sha256=r['source']['board_sha256'],candidate_sha256=r['filled']['board_sha256'],image_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),selected=False,strict_global_plane_preservation='FAIL',SI_qualified=False,native_display_polygon_tolerance_nm=100),indent=2));print(out)
