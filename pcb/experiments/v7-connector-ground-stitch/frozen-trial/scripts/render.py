from pathlib import Path
import os,json,hashlib
R=Path('/tmp/v7-connector-gnd-stitch-c770');os.environ['MPLCONFIGDIR']=str(R/'mplconfig');os.environ['XDG_CACHE_HOME']=str(R/'xdg/cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch,Patch,Circle
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();view=R/'qa/local-native-view.json';d=json.loads(view.read_text());h=H(R/'filled/pcb/maru60.kicad_pcb');assert d['filled']['board_sha256']==h=='aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca';m=json.loads((R/'qa/comparison.json').read_text())['native_metrics'];assert m['vias']==919
fig,axs=plt.subplots(2,4,figsize=(20,12));fig.patch.set_facecolor('#f5f7fa')
for row,phase in enumerate(['source','filled']):
 for col,layer in enumerate(['F.Cu','B.Cu','In1.Cu','In2.Cu']):
  ax=axs[row,col];ax.set_facecolor('#ffffff');ax.set_title(('Selected source c770' if phase=='source' else 'UNSELECTED aaaf')+' | '+layer,fontsize=12,fontweight='bold')
  for q in d[phase]['layers'][layer]:
   isnew=q['uuid']=='cda2df4b-6411-5409-a933-5106751244d8'; net=q['net']; color='#bde0c7' if q['type']=='ZONE' else '#007b54' if net=='GND' else '#974aaf' if 'USB_DP' in net else '#247fbb' if 'USB_DM' in net else '#aeb7c3';z=0 if q['type']=='ZONE' else 3 if isnew else 2
   for p in q['poly']:
    verts=[];codes=[]
    for ring in [p['o']]+p['h']:
     if len(ring)<3:continue
     verts+=ring+[ring[0]];codes += [MPath.MOVETO]+[MPath.LINETO]*(len(ring)-1)+[MPath.CLOSEPOLY]
    if verts:ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',zorder=z))
  ax.set_xlim(14,21.5);ax.set_ylim(13.5,7);ax.set_aspect('equal');ax.grid(color='#e4e9ef',linewidth=.4);ax.set_xlabel('Board X (mm)');ax.set_ylabel('Board Y (mm)')
  if phase=='filled':
   ax.add_patch(Circle((17.2,9.9),.38,fill=False,edgecolor='#da5b24',lw=1.7,zorder=6));ax.annotate('New GND via\n0.50 / 0.25 mm',(17.2,9.9),xytext=(14.25,12.45),arrowprops={'arrowstyle':'->','color':'#bc4d1c'},fontsize=9,color='#9a3e16',bbox={'fc':'white','ec':'none','alpha':.95},zorder=8)
  if col>=2:ax.annotate('Existing neck gap remains',(18.25,8.4),xytext=(15.2,7.45),arrowprops={'arrowstyle':'->','color':'#555'},fontsize=8.5,bbox={'fc':'white','ec':'none','alpha':.92},zorder=8)
fig.suptitle('UNSELECTED connector ground-stitch trial | exact actual board aaafc033',fontsize=20,fontweight='bold',y=.98)
fig.text(.5,.94,'9,750 tracks | 919 vias | 13,176.816254 mm track length | 382 footprints',ha='center',fontsize=13)
fig.text(.5,.915,'12 inherited opens | 66 unchanged warnings | other DRC / ERC / schematic parity: 0',ha='center',fontsize=12)
fig.legend([Patch(color='#bde0c7'),Patch(color='#007b54'),Patch(color='#974aaf'),Patch(color='#247fbb')],['GND plane','GND copper','USB D+','USB D−'],loc='lower center',bbox_to_anchor=(.5,.10),ncol=4,frameon=False,fontsize=11)
fig.text(.5,.085,'One new through-via. Existing tracks, connector stub and saved zone records are unchanged.',ha='center',fontsize=11)
fig.text(.5,.062,'Physical inner-plane loss is the new drill (~0.049087681 mm² per plane). Independent acceptance review pending.',ha='center',fontsize=11)
fig.text(.5,.039,'Same X/Y on all layers; native polygon display, not a 3D view. No restored neck, quantified SI gain or hardware qualification.',ha='center',fontsize=10)
fig.text(.5,.018,'SHA256 '+h,ha='center',fontsize=9,family='monospace')
fig.subplots_adjust(top=.88,bottom=.15,left=.04,right=.99,hspace=.24,wspace=.20)
out=R/'maru60-v7-connector-gnd-unselected-aaaf.png';fig.savefig(out,dpi=160)
(R/'qa/image-binding.json').write_text(json.dumps({'board_sha256':h,'native_view_sha256':H(view),'metrics_receipt_sha256':H(R/'qa/comparison.json'),'image_sha256':H(out),'selected':False,'render_tolerance_nm':100,'no_3D_or_hardware_qualification':True},indent=2)+'\n');print(out)
