from pathlib import Path
import xml.etree.ElementTree as E,copy,json,hashlib
D=Path('/workspace/shared/maru60-resume/continuation-c782/combined27fix2');E.register_namespace('','http://www.w3.org/2000/svg');root=E.parse(D/'images/back-native.svg').getroot();ns='{http://www.w3.org/2000/svg}'
for name,(x,y,w,h)in {'U13':(84,37,13,12),'U11-label':(102,30,12,13),'R135-R145':(111,32,11,12)}.items():
 out=E.Element(ns+'svg',width='1200',height=str(round(1200*h/w)),viewBox=f'{x} {y} {w} {h}');g=E.SubElement(out,ns+'g',transform=f'translate({2*x+w},0) scale(-1,1)')
 for c in root:g.append(copy.deepcopy(c))
 E.ElementTree(out).write(D/f'images/{name}.svg',encoding='utf-8',xml_declaration=True)
(D/'images/PROVENANCE.json').write_text(json.dumps({'board_sha256':hashlib.sha256((D/'pcb/maru60.kicad_pcb').read_bytes()).hexdigest(),'whole_board':'Native KiCad SVG export, F.Cu/B.Cu/Edge.Cuts; not a 3D rendering.','local_views':'Native KiCad SVG export B.SilkS/B.Fab/B.CrtYd/B.Mask/Edge.Cuts, cropped and mirrored to the bottom-side view. Not actual assembled hardware.','raw_geometry_not_altered':True},indent=2)+'\n')
