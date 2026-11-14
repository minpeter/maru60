from pathlib import Path
import re
root=Path('build/mcu-near-usb');s=(root/'mcu.dsn').read_text()
def spans(text,tag):
 for m in re.finditer(r'\('+tag+r'\s',text):
  depth=0;quoted=False
  for j in range(m.start(),len(text)):
   c=text[j]
   if c=='"':quoted=not quoted
   if not quoted:
    depth+=(c=='(')-(c==')')
    if depth==0:yield m.start(),j+1;break
for a,z in reversed(list(spans(s,'plane'))):
 if re.search(r'\(polygon [FB]\.Cu\b',s[a:z]):s=s[:a]+s[z:]
for layer in ['In1.Cu','In2.Cu']:s=s.replace('(layer '+layer+'\n      (type signal)','(layer '+layer+'\n      (type power)')
a,z=next(spans(s,'class'));cl=s[a:z];cl=cl.replace('(width 200)','(width 150)')
for net in ['+3V3','+4V_LED','VBUS_PROTECTED_RAW']:cl=re.sub(r'(?<!\S)'+re.escape(net)+r'(?!\S)','',cl)
cl=cl.replace('(use_via "Via[0-3]_600:300_um")','(use_via "Via[0-3]_500:250_um")')
extra=''
for name,net,width in [('POWER_3V3','+3V3',400),('POWER_LED','+4V_LED',600),('POWER_VBUS','VBUS_PROTECTED_RAW',600)]:extra+=f'\n    (class {name} {net} (circuit (use_via "Via[0-3]_600:300_um")) (rule (width {width}) (clearance 160)))'
s=s[:a]+cl+extra+s[z:]
s=s.replace('(circuit\n', '(circuit\n        (use_layer F.Cu B.Cu)\n')
(root/'mcu-route.dsn').write_text(s)
