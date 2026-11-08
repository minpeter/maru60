import os,subprocess,json,copy,hashlib,xml.etree.ElementTree as E
from pathlib import Path
W=Path(__file__).resolve().parent;source=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-series-with-connector-ground/candidate/pcb/maru60.kicad_pcb');h=hashlib.sha256(source.read_bytes()).hexdigest();assert h=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401'
e=os.environ.copy()
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'render-runtime'/k.lower();d.mkdir(parents=True,exist_ok=True,mode=0o700);e[k]=str(d)
e['QT_QPA_PLATFORM']='offscreen';svg=W/'source-native.svg'
cmd=['kicad-cli','pcb','export','svg','--layers','B.Mask,B.Silkscreen,B.Fab,B.Courtyard,Edge.Cuts','--page-size-mode','1','--exclude-drawing-sheet','--mode-single','--output',str(svg),str(source)]
with (W/'source-native.log').open('w')as f:r=subprocess.run(cmd,env=e,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
S='http://www.w3.org/2000/svg';E.register_namespace('',S);root=E.parse(svg).getroot();out=E.Element('{'+S+'}svg',{'width':'1200','height':'900','viewBox':'170 77 20 15'});g=E.SubElement(out,'{'+S+'}g',{'transform':'translate(360,0) scale(-1,1)'})
for c in root:
 if c.tag.endswith('}g'):g.append(copy.deepcopy(c))
p=W/'buck-source.svg';E.ElementTree(out).write(p,encoding='unicode',xml_declaration=True)
with (W/'source-raster.log').open('w')as f:r=subprocess.run(['inkscape',str(p),'--export-type=png','--export-filename='+str(W/'buck-source.png'),'--export-width=1200','--export-height=900','--export-background=#122129','--export-background-opacity=1'],env=e,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0 and hashlib.sha256(source.read_bytes()).hexdigest()==h
