"""Crop native KiCad renders and record which unchanged board was rendered."""
import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
board=Path('pcb/experiments/resume-20261113-mcu-near-usb-zero-opens/pcb/maru60.kicad_pcb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='2cc544c8e6eb00bd3f53fa480a0167dcb8e14dac687f7eb2af0c85946bda5584'
assert sha(board)==expected
boxes={}
for side in ['top','bottom','iso']:
 im=Image.open(root/f'pcb-{side}.png').convert('RGBA');bbox=im.getchannel('A').getbbox();assert bbox
 assert min(bbox[0],bbox[1],im.width-bbox[2],im.height-bbox[3])>10,(side,bbox,im.size,'camera clips board')
 boxes[side]=bbox
 cropped=im.crop((bbox[0]-28,bbox[1]-28,bbox[2]+28,bbox[3]+28));cropped.save(root/f'pcb-{side}-crop.png')
 small=Image.new('RGBA',cropped.size,'#e4e9e6');small.alpha_composite(cropped);small.convert('RGB').thumbnail((1400,700))
 small.thumbnail((1400,700));small.convert('RGB').save(root/f'{side}-preview.jpg',quality=90)
(root/'provenance.json').write_text(json.dumps({'board':str(board),'board_sha256':expected,'renderer':'KiCad 9.0.2 native raytracer, high quality','scope':'Bare PCB appearance. Component body models are unavailable; no populated hardware or stabilizer assembly shown. Soldermask colors and lighting are illustrative.','render_bounds':boxes,'files':{p.name:sha(p) for p in root.glob('pcb-*-crop.png')}},indent=2)+'\n')
print(boxes)
