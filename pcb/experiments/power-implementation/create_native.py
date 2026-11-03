"""Bounded BOM/footprint revision; input correction study and accepted main are read-only."""
from pathlib import Path
import shutil,sys,json
P=Path(__file__).parent
S=P.parent/'correction-study-20261102/native-max38902a'
O=P/'native-max38902a'; O.mkdir(exist_ok=True)
for f in S.iterdir():
 if f.suffix in ['.kicad_sch','.kicad_sym','.kicad_pro'] or f.name=='sym-lib-table':shutil.copy2(f,O/f.name)
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools')
from sexp import parse,get,all,dump
L=O/'MaruStudy.pretty';L.mkdir(exist_ok=True)
name='MAX_T822-3C_90-0065_2x2_P0.5_EP0.8x1.38'
lines=[f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu")',
'(descr "ADI 90-0065 Rev E land pattern, T822-3C; outline21-0168 Rev M. STUDY ONLY, assembly/thermal qualification pending")',
'(property "Reference" "REF**" (at 0 -2) (layer "F.SilkS") (effects(font(size .7 .7)(thickness .1))))',
f'(property "Value" "{name}" (at 0 2) (layer "F.Fab") (effects(font(size .5 .5)(thickness .08))))',
'(attr smd) (solder_mask_margin 0.025)',
'(fp_rect(start -1 -1)(end 1 1)(stroke(width .1)(type solid))(fill none)(layer "F.Fab"))',
'(fp_rect(start -1.59 -1.25)(end 1.59 1.25)(stroke(width .05)(type solid))(fill none)(layer "F.CrtYd"))',
'(fp_circle(center -1.55 -.75)(end -1.45 -.75)(stroke(width .1)(type solid))(fill none)(layer "F.SilkS"))']
for pin in range(1,9):
 x=-.99 if pin<5 else .99
 y=-.75+.5*(pin-1) if pin<5 else .75-.5*(pin-5)
 lines.append(f'(pad "{pin}" smd rect(at {x} {y})(size .70 .30)(layers "F.Cu" "F.Paste" "F.Mask"))')
lines.append('(pad "9" smd rect(at 0 0)(size .80 1.38)(layers "F.Cu" "F.Mask"))')
# Separate stencil apertures: 2 x .6*.55 = 59.78% of EP copper area; no open via-in-pad.
for y in [-.345,.345]:lines.append(f'(pad "" smd rect(at 0 {y})(size .60 .55)(layers "F.Paste"))')
lines.append(')'); (L/f'{name}.kicad_mod').write_text('\n'.join(lines)+'\n')
cap='Murata_GRM31_1206_Reflow_1.0x1.6_Gap1.9'
(L/f'{cap}.kicad_mod').write_text(f'''(footprint "{cap}" (version 20241229)(generator "pcbnew")(layer "F.Cu")
 (descr "Murata reference sheet reflow recommendation: a1.9,b1.0,c1.6 mm. Assembly qualification pending")
 (property "Reference" "REF**" (at 0 -1.4)(layer "F.SilkS")(effects(font(size .7 .7)(thickness .1))))
 (property "Value" "{cap}" (at 0 1.4)(layer "F.Fab")(effects(font(size .5 .5)(thickness .08))))
 (attr smd)(solder_mask_margin .025)
 (fp_rect(start -1.6 -.8)(end 1.6 .8)(stroke(width .1)(type solid))(fill none)(layer "F.Fab"))
 (fp_rect(start -2.2 -1.15)(end 2.2 1.15)(stroke(width .05)(type solid))(fill none)(layer "F.CrtYd"))
 (pad "1" smd rect(at -1.45 0)(size 1 1.6)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect(at 1.45 0)(size 1 1.6)(layers "F.Cu" "F.Paste" "F.Mask")))
''')
small='Murata_GRM18_0603_Reflow_0.65x0.75_Gap0.7'
(L/f'{small}.kicad_mod').write_text(f'''(footprint "{small}" (version 20241229)(generator "pcbnew")(layer "F.Cu")
 (descr "Murata GRM18 reference sheet reflow a0.7,b0.65,c0.75 mm. STUDY ONLY")
 (property "Reference" "REF**" (at 0 -1.25)(layer "F.SilkS")(effects(font(size .8 .8)(thickness .12))))
 (property "Value" "{small}" (at 0 1.25)(layer "F.Fab")(effects(font(size .5 .5)(thickness .08))))
 (attr smd)(solder_mask_margin .025)
 (fp_rect(start -.8 -.4)(end .8 .4)(stroke(width .1)(type solid))(fill none)(layer "F.Fab"))
 (fp_rect(start -1.25 -.75)(end 1.25 .75)(stroke(width .05)(type solid))(fill none)(layer "F.CrtYd"))
 (pad "1" smd rect(at -.675 0)(size .65 .75)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect(at .675 0)(size .65 .75)(layers "F.Cu" "F.Paste" "F.Mask")))
''')
(O/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "MaruStudy")(type "KiCad")(uri "${KIPRJMOD}/MaruStudy.pretty")(options "")(descr "ISOLATED STUDY ONLY")))\n')
spec={
'U2':('MAX38902AATA+T',f'MaruStudy:{name}','Analog Devices','https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf'),
'R163':('31.6k 0.1% 10ppm/K', 'Resistor_SMD:R_0603_1608Metric','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
'C100':('4.7uF 50V X7R 10%',f'MaruStudy:{cap}','Murata','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71H475KA12-01A.pdf'),
'C101':('4.7uF 50V X7R 10%',f'MaruStudy:{cap}','Murata','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71H475KA12-01A.pdf'),
'C142':('10nF 50V C0G 5%',f'MaruStudy:{small}','Murata','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM1885C1H103JA01-01A.pdf')}
mpn={'U2':'MAX38902AATA+T','R163':'TNPW060331K6BYEA','C100':'GRM31CR71H475KA12L','C101':'GRM31CR71H475KA12L','C142':'GRM1885C1H103JA01D'}
t=parse((O/'supply-context.kicad_sch').read_text())
for sym in all(t,'symbol'):
 props={x[1]:x for x in all(sym,'property')};ref=props['Reference'][2]
 if ref not in spec:continue
 v,fp,mfr,url=spec[ref]
 for k,value in [('Value',v),('Footprint',fp),('Datasheet',url),('Status','ISOLATED BOM STUDY: qualification gates in IMPLEMENTATION.md')]:props[k][2]=value
 for k,value in [('Manufacturer',mfr),('MPN',mpn[ref])]:
  p=parse(dump(props['Status']));p[1]=k;p[2]=value;sym.append(p)
for txt in all(t,'text'):
 if 'R163 guarantees' in txt[1]:txt[1]=txt[1].replace('R163 guarantees >=0.1mA load floor.', 'R163 >=0.1mA floor requires total resistance error <=1%.')
 if 'Capacitor MPN' in txt[1]:txt[1]='ISOLATED BOM/FOOTPRINT STUDY. No electrical net changes from reviewed correction.\nExact parts and official land pattern now specified; effective C/ESR/hot leakage/thermal gates OPEN.\n31.6k load floor requires total resistance error <=1%; see bounded drift budget.\nBYP-OUT10nF: ~0.66ms initial ramp, ~330ms short recovery, neither a guaranteed timing bound.\nReset/USB recovery requires hardware rail qualification, not a firmware delay.'
(O/'supply-context.kicad_sch').write_text(dump(t)+'\n')
(O/'README.md').write_text('Isolated BOM/land-pattern study, NOT FOR FAB. See ../IMPLEMENTATION.md and ../RESET-RECOVERY.md. Electrical pin/net endpoints identical to independently reviewed correction; exact MPN/footprint metadata and C14268nF-to10nF value differ. The placement-only PCB is NOT the main board and not routed.\n')
(P/'bom.json').write_text(json.dumps([dict(reference=r,value=spec[r][0],manufacturer=spec[r][2],mpn=mpn[r],footprint=spec[r][1],datasheet=spec[r][3],status='candidate; acceptance contract in IMPLEMENTATION.md') for r in spec],indent=2)+'\n')
print(O)
