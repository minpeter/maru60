"""Run the existing SI modules on explicit, isolated candidate inputs."""
import argparse,functools,hashlib,importlib,json,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('geometry',type=Path);ap.add_argument('board',type=Path);ap.add_argument('work',type=Path);ap.add_argument('step',choices=['extract_geometry','sim_usb','sim_xtal','sim_matrix','check_misc','sim_led']);a=ap.parse_args()
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(Path(__file__).resolve().parent))
import geom,spice
work=a.work.resolve();work.mkdir(parents=True,exist_ok=True)
spice.OUT=work/'out';spice.DECKS=work/'decks';spice.QA=work/'plots'
for p in [spice.OUT,spice.DECKS,spice.QA]:p.mkdir(parents=True,exist_ok=True)
m=importlib.import_module(a.step)
# Modules use Board() without arguments. Bind only their input factory;
# the geometry algorithms, numeric settings and limits remain unchanged.
m.Board=functools.partial(geom.Board,a.geometry.resolve())
if a.step=='extract_geometry':m.OUT=spice.OUT
before=hashlib.sha256(a.board.read_bytes()).hexdigest();gsha=hashlib.sha256(a.geometry.read_bytes()).hexdigest()
m.main()
if a.step=='extract_geometry':
 p=spice.OUT/'geometry.json';d=json.loads(p.read_text());d['source']=str(a.geometry);d['board_sha256']=before;d['geometry_sha256']=gsha;p.write_text(json.dumps(d,indent=1)+'\n')
else:
 d=json.loads((spice.OUT/'geometry.json').read_text());assert d['board_sha256']==before and d['geometry_sha256']==gsha,'stale SI extraction'
assert hashlib.sha256(a.board.read_bytes()).hexdigest()==before,'board changed during simulation'
(work/(a.step+'-provenance.json')).write_text(json.dumps({'board':str(a.board),'board_sha256':before,'geometry':str(a.geometry),'geometry_sha256':gsha,'step':a.step,'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).resolve().parent.glob('*.py')},'scope':'Computed/model evidence; no hardware measurements'},indent=2)+'\n')
