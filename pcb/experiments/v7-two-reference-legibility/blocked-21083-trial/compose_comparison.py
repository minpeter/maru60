from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
w=Path(__file__).resolve().parent;build=json.loads((w/'TWO_LABEL_BUILD.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';f=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
im=Image.new('RGB',(2480,1250),'#0b151d');d=ImageDraw.Draw(im)
d.text((35,20),'UNSELECTED TWO-LABEL TRIAL | U18 and L2',font=f(40,True),fill='#f3f8fb')
d.text((35,76),'Actual native mask / silk / Fab / courtyard. Back side mirrored as viewed from underneath.',font=f(25),fill='#b8ccd8')
for x,title,path in [(25,'Selected source 7882c9d9',w/'buck-source.png'),(1255,'Trial 21083e94',w/'buck-trial.png')]:
 d.text((x+15,130),title,font=f(29,True),fill='#eef6fa');im.paste(Image.open(path).convert('RGB'),(x,180))
lines=['64 → 58 warnings; exactly six removed, none added. Same 12 expansion opens; zero other hard DRC errors.',
'Two reference fields only. 0.8 mm text; all copper, pads, drills, planes, circuitry and other references unchanged.',
'Actual ink: mask gap ≥0.549793 mm; silk gap ≥0.229525 mm; courtyard gap ≥0.154525 mm.',
'Independent review pending. This is not assembly, manufacturing, signal-integrity or hardware qualification.']
for y,t in zip([1095,1130,1165,1200],lines):d.text((35,y),t,font=f(24),fill='#bdcdda'if y<1200 else'#f2baac')
out=w/'two-label-unselected-comparison.png';im.save(out)
(w/'IMAGE_BINDING.json').write_text(json.dumps({'source_board_sha256':build['source_board_sha256'],'candidate_board_sha256':build['candidate_board_sha256'],'source_svg_sha256':sha(w/'source-native.svg'),'trial_svg_sha256':sha(w/'trial-native.svg'),'source_png_sha256':sha(w/'buck-source.png'),'trial_png_sha256':sha(w/'buck-trial.png'),'image_sha256':sha(out),'selected':False,'images_are_actual_native_plots':True},indent=2)+'\n')
