"""Isolated V4 constructor. Requires explicit reviewed-scope execution flag.
Does not write selected source/repository. Native actual fill/DRC remain separate.
"""
from pathlib import Path
import sys,re,json,uuid,hashlib,shutil,math
from sexpr_spans import children,head,field,replace_child
assert sys.argv[1:]==['--execute-reviewed-v4'], 'Requires parent approval of expanded V4 scope before execution'
ROOT=Path('/tmp/v7-c124-rebound-short');OUT=ROOT/'isolated-v4';SRC=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/candidate/pcb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
S='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
assert sha(SRC/'maru60.kicad_pcb')==S
assert not OUT.exists(), 'Preserve existing trials; never overwrite'
g=json.loads((ROOT/'main/counterfactual-uvlo-r121-ipc-v4.json').read_text());c=json.loads((ROOT/'main/counterfactual-v4-contact-reference.json').read_text())
assert g['source_sha']==c['source_sha256']==S
shutil.copytree(SRC,OUT/'pcb');P=OUT/'pcb'
ns=uuid.UUID('4462b343-3b64-41fb-b31e-7d2c81b0bad3');u=lambda n:str(uuid.uuid5(ns,'7c23-v4:'+n)); f=lambda n:format(n,'.9f').rstrip('0').rstrip('.') if isinstance(n,float)else str(n)
orig=(P/'maru60.kicad_pcb').read_text();netcodes={m.group(2):int(m.group(1))for m in re.finditer(r'\(net (\d+) "([^"]+)"\)',orig)}
assert 'USB_DVDT_CAP'not in netcodes;netcodes['USB_DVDT_CAP']=max(netcodes.values())+1
retired={r['uuid']for r in c['retired_tracks']};assert len(retired)==31
oldfps={}
for a,z,t in children(orig):
 if head(t)=='footprint':
  r=re.search(r'\(property "Reference" "([^"]+)"',t)
  if r and r.group(1)in ['C124','R121']:oldfps[r.group(1)]=t
assert len(oldfps)==2
LIB='C124_Short_Study'
parts={
'R125':dict(name='R_KOA_RK73H1E_0402_Reflow_B',value='100 1%',mpn='RK73H1ETTP1000F',maker='KOA',datasheet='https://www.koaspeer.com/catimages/Products/RK73H/RK73H.pdf',at=[15.54,20.27],pads=[['1',.45,0,.4,.3,'USB_DVDT'],['2',-.45,0,.4,.3,'USB_DVDT_CAP']],body=[1,.5],court=[1.8,1.05],refat=[10.6,21.0],sch=u('R125-symbol')),
'C124':dict(name='C_Murata_GRM155_0402_B_Conditional',value='10nF 10% 50V',mpn='GRM155R71H103KA88D',maker='Murata',datasheet='https://pim.murata.com/en-us/pim/details/?partNum=GRM155R71H103KA88%23',at=[15.38,19.17],pads=[['1',-.375,0,.35,.5,'USB_DVDT_CAP'],['2',.375,0,.35,.5,'GND']],body=[1,.5],court=[1.6,1.05],refat=[10.6,19.8],sch='2beed947-16ca-5de9-a318-0eac08db31e1'),
'R121':dict(name='R_Vishay_TNPW0603_IPC_Vertical_B',value='156k 0.1%',mpn='TNPW0603156KBEEA',maker='Vishay',datasheet='https://www.vishay.com/docs/28758/tnpw_e3.pdf',at=[13.68,18.65],pads=[['1',0,.8,1,.9,'USB_OVLO'],['2',0,-.8,1,.9,'GND']],body=[.85,1.55],court=[1.5,3],refat=[10.6,18.6],sch='3c9a1e86-b5b6-52b9-8936-5c621f352915')}
for r,v in parts.items():
 v['uuid']=re.search(r'\(uuid "([^"]+)"\)',oldfps[r]).group(1)if r in oldfps else u(r+'-footprint')
 v['pad_uuids']={}
 if r in oldfps:
  for _,_,t in children(oldfps[r]):
   if head(t)=='pad':v['pad_uuids'][re.match(r'\(pad "([^"]+)"',t).group(1)]=re.search(r'\(uuid "([^"]+)"\)',t).group(1)

def fp(r,v,board=True):
 at=v['at']if board else[0,0];name=LIB+':'+v['name']if board else v['name']; lines=[f'(footprint "{name}"', '(version 20241229) (generator "pcbnew")'if not board else '', '(layer "B.Cu")',f'(uuid "{v["uuid"]}")'if board else '',f'(at {f(at[0])} {f(at[1])})'if board else '', '(descr "UNSELECTED isolated V4 manufacturer-specific analytical land study; assembly qualification false")','(attr smd)']
 fields=[('Reference',r,'B.SilkS',False),('Value',v['value'],'B.Fab',True),('Datasheet',v['datasheet'],'B.Fab',True),('Manufacturer',v['maker'],'B.Fab',True),('MPN',v['mpn'],'B.Fab',True),('Status','UNSELECTED - not assembly or procurement approved','B.Fab',True)]
 for name,val,layer,hide in fields:
  xy=[v['refat'][0]-v['at'][0],v['refat'][1]-v['at'][1]]if name=='Reference'else[0,0]
  sz=.8 if name=='Reference' else 1; thick=.12 if name=='Reference'else.15
  lines.append(f'(property "{name}" "{val}" (at {f(xy[0])} {f(xy[1])} 0) (layer "{layer}") '+('(hide yes) 'if hide else'')+f'(uuid "{u(r+name)}") (effects (font (size {f(sz)} {f(sz)}) (thickness {f(thick)})) (justify mirror)))')
 if board:lines.append(f'(path "/2ed114c6-5cd0-5571-b3b7-30ce41438842/{v["sch"]}")')
 for name,wh,width in [('B.Fab',v['body'],.10),('B.CrtYd',v['court'],.05)]:
  lines.append(f'(fp_rect (start {f(-wh[0]/2)} {f(-wh[1]/2)}) (end {f(wh[0]/2)} {f(wh[1]/2)}) (stroke (width {f(width)}) (type solid)) (fill none) (layer "{name}") (uuid "{u(r+name)}"))')
 for num,x,y,w,h,net in v['pads']:
  pu=v['pad_uuids'].get(num,u(r+'-pad'+num));lines.append(f'(pad "{num}" smd rect (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) (layers "B.Cu" "B.Paste" "B.Mask") '+(f'(net {netcodes[net]} "{net}") 'if board else'')+f'(uuid "{pu}"))')
 return '\n'.join(x for x in lines if x)+'\n)'

# Preserve all source object bytes except the exact allowlisted records.
replacements=[];removed=[]
for a,z,t in children(orig):
 m=re.search(r'\(uuid "([^"]+)"\)',t)
 if head(t)in['segment','arc','via']and m and m.group(1)in retired:
  assert head(t)=='segment';replacements.append((a,z,''));removed.append(m.group(1))
 if head(t)=='footprint':
  r=re.search(r'\(property "Reference" "([^"]+)"',t)
  if r and r.group(1)in oldfps:replacements.append((a,z,fp(r.group(1),parts[r.group(1)])))
assert set(removed)==retired
s=orig
for a,z,t in sorted(replacements,reverse=True):s=s[:a]+t+s[z:]
tracks=[]
for r in g['routes']:tracks.append(dict(name=r['name'],net=r['net'],start=r['start'],end=r['end'],width=.15))
tracks +=[dict(name='GROUND_BRIDGE_A',net='GND',start=[15.5,17.725],end=[14.9,17.275],width=.28),dict(name='GROUND_BRIDGE_B',net='GND',start=[15.5,17.85],end=[15.5,17.25],width=.20)]
assert len(tracks)==21
for r in tracks:r['uuid']=u(r['name']+'-track')
add=[f'(net {netcodes["USB_DVDT_CAP"]} "USB_DVDT_CAP")',fp('R125',parts['R125'])]
for t in tracks:add.append(f'(segment (start {f(t["start"][0])} {f(t["start"][1])}) (end {f(t["end"][0])} {f(t["end"][1])}) (width {f(t["width"])}) (layer "B.Cu") (net {netcodes[t["net"]]}) (uuid "{t["uuid"]}"))')
s=s.rstrip();assert s.endswith(')');s=s[:-1]+'\n'+'\n'.join(add)+'\n)\n';(P/'maru60.kicad_pcb').write_text(s)
(P/(LIB+'.pretty')).mkdir()
for r,v in parts.items():(P/(LIB+'.pretty')/(v['name']+'.kicad_mod')).write_text(fp(r,v,False))
libfile=P/'fp-lib-table';ls=libfile.read_text().rstrip();assert ls.endswith(')');libfile.write_text(ls[:-1]+f'\n(lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.pretty") (options "") (descr "UNSELECTED V4 manufacturer-specific B-side land study"))\n)\n')
# Schematic: preserve source primitives except the three changed fields and C124's source label.
sch=P/'protection-input-protection.kicad_sch';ss=sch.read_text();repl=[];template=None
for a,z,t in children(ss):
 if head(t)=='symbol'and'(lib_id'in t:
  r=re.search(r'\(property "Reference" "([^"]+)"',t).group(1)
  if r=='R124':template=t
  if r in ['C124','R121']:
   v=parts[r];t=re.sub(r'\(property "Footprint" "[^"]+"',f'(property "Footprint" "{LIB}:{v["name"]}"',t);t=re.sub(r'\(property "Datasheet" "[^"]*"',f'(property "Datasheet" "{v["datasheet"]}"',t)
   props=''.join(f'(property "{name}" "{val}" (at 0 0 0) (effects (font (size 1 1)) (hide yes)))'for name,val in [('Manufacturer',v['maker']),('MPN',v['mpn'])]);t=t[:-1]+props+')';repl.append((a,z,t))
 if head(t)=='global_label'and'a78e13f3-5f3b-5410-8583-d6d3dd8a7415'in t:repl.append((a,z,t.replace('"USB_DVDT"','"USB_DVDT_CAP"')))
lib=field(ss,'lib_symbols');rt=next(t for _,_,t in children(lib)if t.startswith('(symbol "Study:R124"'))
rt=rt.replace('Study:R124','Study:R125').replace('R124_','R125_').replace('6.65k 0.1%','100 1%').replace('(property "Reference" "U"','(property "Reference" "R"')
for a,z,t in children(ss):
 if head(t)=='lib_symbols':repl.append((a,z,t[:-1]+'\n'+rt+')'))
for a,z,t in sorted(repl,reverse=True):ss=ss[:a]+t+ss[z:]
assert template
# Clone the already-valid matching passive instance into an empty row.
r=template.replace('Study:R124','Study:R125').replace('"R124"','"R125"').replace('67a38ace-fe14-51c2-8c3a-d9ca63053dcf',parts['R125']['sch']).replace('6.65k 0.1%','100 1%')
r=re.sub(r'\(at ([\d.]+) ([\d.]+) 0\)',lambda m:f'(at {f(float(m.group(1))+60.96)} {f(float(m.group(2))+35.56)} 0)',r)
r=re.sub(r'\(property "Footprint" "[^"]+"',f'(property "Footprint" "{LIB}:{parts["R125"]["name"]}"',r);r=re.sub(r'\(property "Datasheet" "[^"]*"',f'(property "Datasheet" "{parts["R125"]["datasheet"]}"',r)
r=r[:-1]+''.join(f'(property "{name}" "{val}" (at 111.76 230 0) (effects (font (size 1 1)) (hide yes)))'for name,val in [('Manufacturer','KOA'),('MPN',parts['R125']['mpn'])])+')'
labels=[f'(global_label "{net}" (shape bidirectional) (at {x} 210.82 {ang}) (effects (font (size 1 1)) (justify {just})) (uuid {u("R125-label-"+net)}))'for net,x,ang,just in [('USB_DVDT',96.52,180,'right'),('USB_DVDT_CAP',127,0,'left')]]
ss=ss.rstrip();ss=ss[:-1]+'\n'+r+'\n'+'\n'.join(labels)+'\n)\n';sch.write_text(ss)
(OUT/'BOM_PROPOSAL.json').write_text(json.dumps({'status':'UNSELECTED; no procurement or assembly approval','parts':parts},indent=2)+'\n')
(OUT/'BUILD_CONTRACT.json').write_text(json.dumps({'source_sha256':S,'candidate_prefill_sha256':sha(P/'maru60.kicad_pcb'),'retired_track_uuids':sorted(retired),'changed_old_footprint_uuids':[parts[r]['uuid']for r in ['C124','R121']],'added_tracks':tracks,'parts':parts,'new_signal_net':'USB_DVDT_CAP','new_drills':0,'qualification':False},indent=2)+'\n')
(OUT/'README.md').write_text('# Unselected isolated C124 V4 experiment\n\nConstructed only for electrical validation of the reviewed expanded UVLO/OVLO contact contract. No analog, mechanical, assembly, procurement, or production qualification. Selected source/repository untouched. Manufacturer-dimension/assembly limits remain in the source plan. Actual native refill, DRC/ERC/netlist, source contact/reference and independent review are mandatory before any adoption consideration.\n')
assert sha(SRC/'maru60.kicad_pcb')==S
print(json.dumps({'status':'isolated complete prefill candidate written, NOT validated','pcb':str(P/'maru60.kicad_pcb'),'sha256':sha(P/'maru60.kicad_pcb'),'retired_tracks':len(retired),'new_tracks':len(tracks),'new_vias':0},indent=2))
