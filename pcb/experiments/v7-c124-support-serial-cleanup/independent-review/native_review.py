import os,sys,json,hashlib,shutil,time
from pathlib import Path
W=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'native-runtime'/k.lower();d.mkdir(parents=True,mode=0o700);os.environ[k]=str(d)
os.environ['QT_QPA_PLATFORM']='offscreen'
import pcbnew as p
assert p.GetBuildVersion()=='9.0.2+dfsg-1'
R=Path('/tmp/v7-support-endpoint-trial');S=R/'source/pcb/maru60.kicad_pcb';A=R/'filled/pcb/maru60.kicad_pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before={str(f):H(f)for f in[S,A]};plan=[('abcd4fb1-881b-43f9-906e-39d93366692e','f58bc791-8a08-55a5-ada7-19575bcd7e75'),('ae94ea04-2d21-5f84-8952-7f8960275e00','cc1282fe-f0b3-5fea-9d45-66eea8068d66'),('f41eeb49-8180-5bac-bccf-c1a0b3b4c547','d4be2091-cd02-51f1-b2e5-0505e7ec1e8a')];U=lambda x:x.m_Uuid.AsString();xy=lambda q:[q.x,q.y]
def rec(q):return {'uuid':U(q),'net':q.GetNetname(),'layer':q.GetLayerName(),'width_nm':q.GetWidth(),'start_nm':xy(q.GetStart()),'end_nm':xy(q.GetEnd()),'length_nm':q.GetLength(),'is_via':isinstance(q,p.PCB_VIA)}
result={}
for label,path in [('source',S),('candidate',A)]:
 b=p.LoadBoard(str(path));b.BuildConnectivity();cn=b.GetConnectivity();track={U(q):q for q in b.GetTracks()};rows=[]
 for main,support in plan:
  m=track[main];q=track[support];rows.append({'main':rec(m),'support':rec(q),'main_dangling':cn.TestTrackEndpointDangling(m,True),'support_dangling':cn.TestTrackEndpointDangling(q,True)})
 result[label]={'sha256':H(path),'track_via_count':len(track),'footprints':len(list(b.GetFootprints())),'rows':rows}
 if label=='candidate':
  assert all(not r['support_dangling']and not r['main_dangling'] for r in rows)
  for r in rows:
   m=r['main'];q=r['support'];assert m['net']==q['net']and m['layer']==q['layer']=='B.Cu';assert set(map(tuple,[m['start_nm'],m['end_nm']]))&set(map(tuple,[q['start_nm'],q['end_nm']])), 'Serial junction must be exact endpoint to endpoint'
 else:assert all(r['support_dangling']for r in rows)
for a,z in zip(result['source']['rows'],result['candidate']['rows']):assert a['support']==z['support'];assert a['main']['width_nm']==z['main']['width_nm']
D=W/'cold-refill/pcb';assert not D.exists();shutil.copytree(A.parent,D);b=p.LoadBoard(str(D/'maru60.kicad_pcb'));start=time.monotonic();f=p.ZONE_FILLER(b);ok=f.Fill(b.Zones());assert ok;p.SaveBoard(str(D/'maru60.kicad_pcb'),b);elapsed=time.monotonic()-start;assert H(D/'maru60.kicad_pcb')==H(A)
assert {str(f):H(f)for f in[S,A]}==before
result.update({'native_build':p.GetBuildVersion(),'cold_refill_byte_identical':True,'cold_refill_seconds':elapsed,'source_and_actual_unchanged':True,'scope':'Only exact source topology and normal refill. No SI or active analog improvement claim.'});(W/'NATIVE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'serial_junctions_exact':True,'native_dangling_removed':3,'cold_refill_equal':True,'seconds':elapsed}))
