from pathlib import Path
import json
out=Path(__file__).resolve().parent
root=Path(__file__).resolve().parents[2]
assert json.loads((root/'engineering/key-rgb-index-map.json').read_text())['led_count']==64,'This definition generator is for the reviewed64keyrevision'
j=json.loads((root/'firmware/qmk/keyboards/maru60/rp2350/keyboard.json').read_text())
custom=[{'name':n,'title':t,'shortName':s} for n,t,s in [('Underglow toggle','Toggle independent underglow zone','UG On'),('Underglow hue','Next underglow hue','UG Hue'),('Key RGB toggle','Toggle key RGB zone','Key RGB'),('Caps physical option','Toggle normal / stepped Caps LED and reactive mapping','Caps Opt'),('Right Shift physical option','WKL only: toggle split / normal Right Shift LED mapping','RS Opt')]]
for variant,key in [('wkl','LAYOUT_wkl_7u_split'),('hhkb','LAYOUT_hhkb_7u')]:
 sites=j['layouts'][key]['layout'];rows=[];caps_group=1 if variant=='wkl' else 0
 for y in range(5):
  row=[];lastx=0
  for s in sorted([s for s in sites if s['y']==y],key=lambda s:s['x']):
   r,c=s['matrix'];prop={'a':0,'t':'#000000','c':'#aaaaaa' if s.get('w',1)!=1 or r==4 else '#cccccc'}
   if s['x']!=lastx:prop['x']=s['x']-lastx
   if s.get('w',1)!=1:prop['w']=s['w']
   legend=f'{r},{c}'
   if [r,c]==[2,0]:legend+=f'\n\n\n{caps_group},0'
   if variant=='wkl' and r==3 and c in [11,12]:legend+='\n\n\n0,0'
   row.extend([prop,legend]);lastx=s['x']+s.get('w',1)
  rows.append(row)
 # Alternatives deliberately below the default boundingbox and alignedX.
 rows.append([{'y':1,'w':1.75,'a':0,'c':'#aaaaaa'},f'2,0\n\n\n{caps_group},1'])
 if variant=='wkl':rows.append([{'x':12.25,'w':2.75,'a':0,'c':'#aaaaaa'},'3,11\n\n\n0,1'])
 labels=[['Caps','Normal','Stepped']]
 if variant=='wkl':labels.insert(0,['Right Shift','Split 1.75U + 1U','Normal 2.75U'])
 d={'name':f'Maru60 {variant.upper()} PRIVATE TEST - shared ID; not for manufacture','vendorId':'0x1209','productId':'0x0001' if variant=='wkl' else '0x0002','matrix':{'rows':5,'cols':15},'menus':['qmk_rgb_matrix'],'customKeycodes':custom,'layouts':{'labels':labels,'keymap':rows}}
 (out/f'maru60-{variant}-64.json').write_text(json.dumps(d,indent=2)+'\n')
