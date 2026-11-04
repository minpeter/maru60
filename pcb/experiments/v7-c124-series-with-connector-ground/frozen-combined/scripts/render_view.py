import os
os.environ['MPLCONFIGDIR']='/tmp/v7-c124-d-plus-connector-gnd/mplconfig'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch,Patch,Circle
from pathlib import Path as P
import json,hashlib
R=P('/tmp/v7-c124-d-plus-connector-gnd');d=json.loads((R/'qa/local-native-view.json').read_text());assert d['sha256']=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401';pal={'GND':'#6e9b75','USB_DVDT':'#d99100','USB_DVDT_CAP':'#00a6ba','USB_OVLO':'#9b51ab','USB_UVLO':'#3d68c8','USB_ILM':'#d44d3a','VBUS_PROTECTED_RAW':'#db6964','VBUS_FUSED':'#c95c52'}
fig,axs=plt.subplots(1,3,figsize=(18,8));fig.patch.set_facecolor('#f5f7fa')
for ax,(layer,title,xlim,ylim) in zip(axs,[('F.Cu','Connector • F.Cu',(14.5,20.5),(13.0,7.3)),('B.Cu','Connector • B.Cu',(14.5,20.5),(13.0,7.3)),('B.Cu','C124 circuit • B.Cu',(12.0,19.2),(22.1,16.5))]):
 ax.set_facecolor('white');ax.set_title(title,fontsize=14,fontweight='bold')
 for row in d['layers'][layer]:
  typ=row['type'];col=pal.get(row.get('net'),'#8c929b')if typ=='copper'else'#242a33'if typ=='silk'else'#65788b'if typ=='fab'else'#b6bec8'
  for z in row['poly']:
   vs=[];cs=[]
   for ring in [z['o']]+z['h']:
    if len(ring)<3:continue
    vs+=ring+[ring[0]];cs+=[Path.MOVETO]+[Path.LINETO]*(len(ring)-1)+[Path.CLOSEPOLY]
   if vs:ax.add_patch(PathPatch(Path(vs,cs),facecolor=col,edgecolor='none',alpha=.85 if typ=='copper'else .7,zorder=3 if typ=='silk'else 2 if typ=='copper'else 1))
 if title.startswith('Connector'):
  ax.add_patch(Circle((17.2,9.9),.47,fill=False,color='#00824d',linewidth=1.4,linestyle='--',zorder=10));ax.annotate('Only added via\nØ0.50 / drill 0.25',(17.2,9.9),(17.8,8.4),fontsize=9,color='#00683d',arrowprops={'arrowstyle':'->','color':'#00683d'},zorder=11)
 ax.set_xlim(*xlim);ax.set_ylim(*ylim);ax.set_aspect('equal');ax.grid(color='#e8edf3',linewidth=.4);ax.set_xlabel('Board X (mm)');ax.set_ylabel('Board Y (mm)')
fig.suptitle('UNSELECTED combined trial • actual saved board 7882c9d9',fontsize=19,fontweight='bold',y=.94)
fig.text(.5,.89,'All panels use board X/Y orientation. Native copper, drilled holes, reference ink, Fab and courtyard graphics.',ha='center',fontsize=10)
ks=['USB_DVDT','USB_DVDT_CAP','USB_OVLO','USB_UVLO','USB_ILM','GND'];fig.legend([Patch(color=pal[k])for k in ks],ks,loc='lower center',ncol=6,bbox_to_anchor=(.5,.19),frameon=False)
fig.text(.5,.155,'9,750 tracks / 919 vias / 383 footprints / 13,185.28691027245 mm',ha='center',fontsize=11)
fig.text(.5,.12,'DRC: 0 hard / 64 warnings / 12 opens. ERC: 0. Parity: 0. All D warning/open records retained, including three support-end warnings.',ha='center',fontsize=10)
fig.text(.5,.075,'UNSELECTED. No assembly, hardware, SI/ESD/EMC, pulse/reset, or active-startup qualification.',ha='center',fontsize=11,color='#a33330')
fig.subplots_adjust(top=.83,bottom=.31,left=.05,right=.98,wspace=.22);p=R/'qa/combined-unselected.png';fig.savefig(p,dpi=180);print(p,hashlib.sha256(p.read_bytes()).hexdigest())
