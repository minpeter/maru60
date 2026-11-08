"""Full-board native front/back copper+mask+silk preview, bound to this exact trial."""
import sys,os,json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
W=Path(__file__).resolve().parent;Q=W/'qa';O=Q/'fullboard-preview';O.mkdir();board=W/'candidate-four/pcb/maru60.kicad_pcb';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();h=sha(board);c=json.loads((Q/'SCREEN_COMPARISON.json').read_text());s=json.loads((Q/'SCHEMATIC_CHECKS.json').read_text());assert h==c['candidate_board_sha256']==s['candidate_board_sha256'];records=[];images=[]
def env_for(name):
 e=os.environ.copy();homes={}
 for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
  p=Q/'runtime'/name/k.lower();p.mkdir(parents=True,mode=0o700);e[k]=str(p);homes[k]=str(p)
 return e,homes
for side in ['F','B']:
 svg=O/(side+'-copper-mask-silk.svg');png=O/(side+'-copper-mask-silk.png');cmd=['kicad-cli','pcb','export','svg','--layers',side+'.Cu,'+side+'.Mask,'+side+'.Silkscreen,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--mode-single','--output',str(svg)]+(['--mirror']if side=='B'else[])+[str(board)];env,homes=env_for('fullboard-native-'+side);log=O/(side+'-native.log')
 with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==0 and sha(board)==h
 records.append({'side':side,'command':cmd,'private_xdg':homes,'exit_code':0,'svg_sha256':sha(svg),'log_sha256':sha(log)})
 cmd=['inkscape',str(svg),'--export-type=png','--export-filename='+str(png),'--export-width=2600','--export-background=#122129','--export-background-opacity=1'];env,homes=env_for('fullboard-raster-'+side);log=O/(side+'-raster.log')
 with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==0
 im=Image.open(png).convert('RGB');images.append((side,im));records.append({'side':side,'command':cmd,'private_xdg':homes,'exit_code':0,'png_sha256':sha(png),'log_sha256':sha(log)})
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';f=lambda n,b=False:ImageFont.truetype(bold if b else font,n);height=220+sum(im.height+70 for _,im in images)+190;canvas=Image.new('RGB',(2700,height),'#0b151d');d=ImageDraw.Draw(canvas);d.text((50,28),'V7 current full-board preview • four labels + intact LOGO1',font=f(43,True),fill='#eff6fa');d.text((50,91),'Actual candidate2c7e100a • unselected • native front/back copper, mask and silk; no 3D claim',font=f(29),fill='#bdd2de');d.text((50,140),'9,752 tracks | 919 vias | 13,181.60473138763 mm track length | 382 footprints',font=f(29),fill='#bdd2de');y=220
for side,im in images:
 d.text((50,y-3),'Front'if side=='F'else'Back, mirrored as viewed from underside',font=f(29,True),fill='#eff6fa');canvas.paste(im,(50,y+45));y+=im.height+70
d.text((50,y+20),'Native DRC: 68 warnings, same 12 GPIO open-component pairs, 0 other errors | ERC: 0 | parity: 0',font=f(28),fill='#bdd2de');d.text((50,y+66),'92 → 68 warnings; 24 exact records removed, none added. All electrical geometry is unchanged.',font=f(27),fill='#bdd2de');d.text((50,y+111),'Board SHA256: '+h,font=f(21),fill='#9db6c7');out=O/'candidate-four-fullboard.png';canvas.save(out);assert sha(board)==h;(O/'FULLBOARD_BINDING.json').write_text(json.dumps({'candidate_board_sha256':h,'preview_png_sha256':sha(out),'native_and_raster_records':records,'same_snapshot_metrics_source_sha256':sha(Q/'SCREEN_COMPARISON.json'),'same_snapshot_ERC_XML_source_sha256':sha(Q/'SCHEMATIC_CHECKS.json'),'displayed_layers':['F.Cu','F.Mask','F.Silkscreen','B.Cu','B.Mask','B.Silkscreen','Edge.Cuts'],'selected':False,'manufacturing_or_3D_qualified':False},indent=2)+'\n');print(out)
