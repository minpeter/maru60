from pathlib import Path
import xml.etree.ElementTree as E,copy,json,hashlib
D=Path(__file__).resolve().parent;ns='http://www.w3.org/2000/svg';E.register_namespace('',ns);root=E.Element('{'+ns+'}svg',width='1600',height='820',viewBox='0 0 1600 820');E.SubElement(root,'{'+ns+'}rect',width='1600',height='820',fill='white')
for col,(name,title)in enumerate([('source','Before PCB: 88fbac1d'),('candidate','After PCB: 41f82c80')]):
 text=E.SubElement(root,'{'+ns+'}text',x=str(30+col*800),y='38',fill='#172033',style='font-family:DejaVu Sans,sans-serif;font-size:25px');text.text=title
 defs=E.SubElement(root,'{'+ns+'}defs');clip=E.SubElement(defs,'{'+ns+'}clipPath',id='panel'+str(col),clipPathUnits='userSpaceOnUse');E.SubElement(clip,'{'+ns+'}rect',x=str(10+col*800),y='58',width='780',height='700')
 group=E.SubElement(root,'{'+ns+'}g',{'clip-path':'url(#panel'+str(col)+')'});nested=E.SubElement(group,'{'+ns+'}svg',x=str(10+col*800),y='58',width='780',height='700',viewBox='15.9 10.6 4.2 3.8',overflow='hidden')
 for c in E.parse(D/(name+'.svg')).getroot():nested.append(copy.deepcopy(c))
 text=E.SubElement(root,'{'+ns+'}text',x=str(30+col*800),y='795',fill='#45556a',style='font-family:DejaVu Sans,sans-serif;font-size:18px');text.text='Native CAD: F.Cu + B.Cu overlay; same coordinates and scale'
E.SubElement(root,'{'+ns+'}line',x1='800',x2='800',y1='15',y2='805',stroke='#ccd3df');E.ElementTree(root).write(D/'before-after.svg',encoding='utf-8',xml_declaration=True)
(D/'PROVENANCE.json').write_text(json.dumps({'source_sha256':'88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e','candidate_sha256':'41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5','method':'Native KiCad F.Cu/B.Cu/Edge.Cuts SVG, identical coordinate viewport and scale; vector composition and installed Inkscape rendering. No underlying copper geometry edited in image.','viewport_mm':[15.9,10.6,4.2,3.8],'not_assembled_hardware':True},indent=2)+'\n')
