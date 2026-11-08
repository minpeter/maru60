from pathlib import Path
import re,json,hashlib
p=Path(__file__).resolve().parent;s=(p/'native-c128-LR/reconstructed.kicad_pcb').read_text();H=lambda s:hashlib.sha256(s.encode()).hexdigest();assert H(s)=='8a4ff6a646396a3faa11dda0f756c89e82c20eec18f37fe531cf730789106eea'
net=97;uid='0fcbbcbc-52de-5e52-b60d-79b83d0b7fa8';add='\n\t(segment\n\t\t(start 140.5 72.7)\n\t\t(end 140.6 72.8)\n\t\t(width 0.15)\n\t\t(layer "B.Cu")\n\t\t(net 97)\n\t\t(uuid "'+uid+'")\n\t)'
pat=r'\n\t\(segment\n.*?\n\t\)';ms=[m for m in re.finditer(pat,s,re.S)if '(net 97)'in m.group() and '(layer "B.Cu")'in m.group()];later=[m for m in ms if re.search(r'\(uuid "([^"]+)"',m.group()).group(1)>uid];pos=later[0].start();s=s[:pos]+add+s[pos:];width=H(s);(p/'width-reconstructed.kicad_pcb').write_text(s)
refs=['R120','R144','J3','D100','R124','C142','C141','R163','C137','C126','C129','U2','R126','U10','C101'];moves={'U2':('(at 0 2 0)','(at 0 -1.8 0)'), 'C101':('(at 0 1.4 90)','(at 0 1.7 90)'), 'J3':('(at 0 3.98 180)','(at -0.1 3.98 180)'), 'C142':('(at 0 1.25 0)','(at 0.05 1.25 0)')}
for ref in refs:
 pat=r'\n\t\t\(property "Reference" "'+re.escape(ref)+r'"\n.*?\n\t\t\)';m=re.search(pat,s,re.S);assert m,ref;old=m.group();assert old.count('(size 0.75 0.75)')==1,(ref,old);new=old.replace('(size 0.75 0.75)','(size 0.8 0.8)')
 if ref in moves:
  a,b=moves[ref];assert new.count(a)==1,(ref,new,a);new=new.replace(a,b)
 s=s[:m.start()]+new+s[m.end():]
typo=H(s);(p/'typography-reconstructed.kicad_pcb').write_text(s);r={'width':{'sha256':width,'expected':'0e5bbc5ae365d9511ce51a81f75d9e9236fbb93af89b17b2e9486ceb038e026c','exact':width=='0e5bbc5ae365d9511ce51a81f75d9e9236fbb93af89b17b2e9486ceb038e026c'},'typography':{'sha256':typo,'expected':'7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1','exact':typo=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'},'delta_source':'Archived study geometry for C128. Width and typography continuity data from independent review checkpoint; full SHA is the exact-restoration criterion, not remembered geometry alone.'};(p/'width-typography-reconstruction.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
