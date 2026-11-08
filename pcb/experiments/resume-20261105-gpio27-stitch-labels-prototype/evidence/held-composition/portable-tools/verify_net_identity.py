from pathlib import Path
import sys,argparse,json,re,hashlib,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
from sexpr_spans import children,head,field
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('board');ap.add_argument('netlist');ap.add_argument('output');a=ap.parse_args()
bp=Path(a.board);out=Path(a.output);assert bp.resolve()!=out.resolve() and not out.exists()
raw=bp.read_text();digest=hashlib.sha256(bp.read_bytes()).hexdigest();top=children(raw);nets={int(re.match(r'\(net\s+(\d+)',s).group(1)):json.loads(re.search(r'("(?:[^"\\]|\\.)*")\s*\)$',s).group(1)) for _,_,s in top if head(s)=='net'}
def raw_net(obj):
 f=field(obj,'net');return nets[int(re.match(r'\(net\s+(\d+)',f).group(1))] if f else ''
def uid(obj):return json.loads(re.search(r'("[^"]+")',field(obj,'uuid')).group(1))
objects={};padnames={}
for _,_,s in top:
 h=head(s)
 if h in ('segment','arc','via'):objects[uid(s)]=raw_net(s)
 elif h=='footprint':
  fields=children(s);ref=next((json.loads(re.match(r'\(property\s+"Reference"\s+("(?:[^"\\]|\\.)*")',x).group(1)) for _,_,x in fields if x.startswith('(property "Reference"')),None)
  for _,_,pa in fields:
   if head(pa)!='pad':continue
   u=uid(pa);objects[u]=raw_net(pa);pn=json.loads(re.match(r'\(pad\s+("(?:[^"\\]|\\.)*")',pa).group(1));padnames.setdefault((ref,pn),[]).append(raw_net(pa))
b=p.LoadBoard(str(bp));native=lambda:{x.m_Uuid.AsString():x.GetNetname() for x in list(b.GetTracks())+[q for fp in b.GetFootprints()for q in fp.Pads()]};loaded=native();b.BuildConnectivity();built=native()
xml=ET.parse(a.netlist).getroot();mismatch=[];checked=0
for n in xml.findall('./nets/net'):
 name=n.get('name')
 for node in n.findall('node'):
  key=(node.get('ref'),node.get('pin'));vals=padnames.get(key);checked+=1
  if not vals or any(v!=name for v in vals):mismatch.append({'ref_pin':key,'schematic_net':name,'raw_board_nets':vals})
result={'board_sha256':digest,'native_build':p.GetBuildVersion(),'raw_object_count':len(objects),'raw_to_loaded_equal':objects==loaded,'loaded_to_built_equal':loaded==built,'electrical_xml_nodes_checked':checked,'source_pin_mismatches':mismatch,'board_unchanged':hashlib.sha256(bp.read_bytes()).hexdigest()==digest}
result['pass']=result['raw_to_loaded_equal'] and result['loaded_to_built_equal'] and not mismatch and result['board_unchanged'];out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['pass']
