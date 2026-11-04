"""Native CAD preview of the actual reduced candidate, with bound measured metrics."""
import sys,os,json,subprocess,hashlib,copy
from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
if not __debug__:raise RuntimeError('No optimized execution')
W=Path(__file__).resolve().parent;Q=W/'qa';P=Q/'preview';P.mkdir();board=W/'candidate-four/pcb/maru60.kicad_pcb';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected=json.loads((W/'PLAN-four.json').read_text())['candidate_board_sha256'];assert sha(board)==expected;S='http://www.w3.org/2000/svg';E.register_namespace('',S)
def env_for(name):
 e=os.environ.copy();homes={}
 for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
  p=Q/'runtime'/name/k.lower();p.mkdir(parents=True,mode=0o700);e[k]=str(p);homes[k]=str(p)
 return e,homes
native=P/'back-native.svg';cmd=['kicad-cli','pcb','export','svg','--layers','B.Mask,B.Silkscreen,B.Fab,B.Courtyard,Edge.Cuts','--page-size-mode','1','--exclude-drawing-sheet','--mode-single','--output',str(native),str(board)];env,homes=env_for('preview-native');log=P/'native-export.log'
with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0 and sha(board)==expected
records=[{'command':cmd,'private_xdg':homes,'exit_code':r.returncode,'svg_sha256':sha(native),'log_sha256':sha(log)}]
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';f=lambda n,b=False:ImageFont.truetype(bold if b else font,n);canvas=Image.new('RGB',(1680,1700),'#0b151d');d=ImageDraw.Draw(canvas);d.text((40,24),'V7 four-label + intact-logo trial',font=f(38,True),fill='#f3f8fb');d.text((40,78),'Actual candidate 2c7e100a  |  Native mask / silk / Fab / courtyard plots',font=f(23),fill='#b8ccd8');d.text((40,112),'92 → 68 warnings   •   same 12 GPIO opens   •   unselected screening trial',font=f(23),fill='#b8ccd8')
specs=[('C100',(133,68,16,12),'C100: outside its own capacitor',40,170),('R140',(108,28,12,11),'R140: opposite side of its own part',860,170),('R160',(178,80,12,12),'R160: clear outward side of its owner',40,680),('R134',(101,39,13,12),'R134: below its own resistor',860,680),('LOGO1',(65,77,26,16),'LOGO1: both complete polygons together',40,1190)]
root0=E.parse(native).getroot()
for name,box,title,x,y in specs:
 x0,y0,bw,bh=box;root=E.Element('{'+S+'}svg',{'width':'780','height':'420','viewBox':f'{x0} {y0} {bw} {bh}','preserveAspectRatio':'xMidYMid meet'});g=E.SubElement(root,'{'+S+'}g',{'transform':f'translate({2*x0+bw},0) scale(-1,1)'})
 for child in root0:
  if child.tag.endswith('}g'):g.append(copy.deepcopy(child))
 svg=P/(name+'.svg');E.ElementTree(root).write(svg,encoding='unicode',xml_declaration=True);png=P/(name+'.png');cmd=['inkscape',str(svg),'--export-type=png','--export-filename='+str(png),'--export-width=780','--export-height=420','--export-background=#122129','--export-background-opacity=1'];env,homes=env_for('preview-raster-'+name);log=P/(name+'-raster.log')
 with log.open('w')as h:r=subprocess.run(cmd,env=env,stdout=h,stderr=subprocess.STDOUT)
 assert r.returncode==0
 d.rounded_rectangle((x-8,y-4,x+788,y+484),radius=14,fill='#152733');d.text((x+12,y+12),title,font=f(22,True),fill='#eef6fa');canvas.paste(Image.open(png).convert('RGB'),(x,y+56));records.append({'panel':name,'crop_board_mm':box,'back_display_mirrored':True,'svg_sha256':sha(svg),'png_sha256':sha(png),'raster_command':cmd,'private_xdg':homes,'log_sha256':sha(log)})
x,y=880,1220
for text,b in [('Fresh scoped checks',True),('4 reference fields; one whole-artwork translation',False),('24 exact warnings removed; none added',False),('Mask lower bound: 0.409895 mm',False),('Silk lower bound: 0.302395 mm',False),('Courtyard lower bound: 0.159895 mm',False),('All 1,759 mask aperture objects checked',False),('R131 and circuit-reserved labels unchanged',False),('Full acceptance replay not run',False),('2D proxies only; no supplier / 3D qualification',False)]:d.text((x,y),text,font=f(26 if b else 20,b),fill='#eef6fa'if b else'#bdd2de');y+=40
out=P/'candidate-four-preview.png';canvas.save(out);assert sha(board)==expected;(P/'PREVIEW_BINDING.json').write_text(json.dumps({'candidate_board_sha256':expected,'native_plot_and_panels':records,'png_sha256':sha(out),'screen_comparison_sha256':sha(Q/'SCREEN_COMPARISON.json'),'native_ink_sha256':sha(Q/'candidate-four-ink.json'),'all_CAD_geometry_unaltered_for_visualization':True,'method':'Native SVG groups with viewBox crops and back-side reflection; native Fab proxy/reference graphics remain visible, not actual silkscreen objects. Other existing board warnings are not hidden.','selected':False,'manufacturing_or_actual_3D_visibility_qualified':False},indent=2)+'\n');print(out)
