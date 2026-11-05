import os
for k in ['KICAD_CONFIG_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME']:os.environ[k]='/tmp/maru-b2l-native'
from pathlib import Path
import pcbnew as p,json,hashlib,sys,collections
R=Path(__file__).parent;src=R.parent.parent/'pre-usb-040.kicad_pcb';dst=R/(sys.argv[1]if len(sys.argv)>1 else 'corridor-pilot.kicad_pcb');a=p.LoadBoard(str(src));b=p.LoadBoard(str(dst));l=json.load(open(R/(sys.argv[2] if len(sys.argv)>2 else 'corridor-pilot-ledger.json')));xy=lambda q:tuple(q);uid=lambda q:q.m_Uuid.AsString()
def fp(f):return(f.GetReference(),f.GetValue(),xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),(str(f.GetFPID().GetLibNickname()),str(f.GetFPID().GetLibItemName())),f.IsDNP(),sorted((q.GetNumber(),q.GetNetname(),xy(q.GetPosition()),xy(q.GetSize()),xy(q.GetDrillSize()),q.GetOrientationDegrees(),q.GetShape(),q.GetAttribute())for q in f.Pads()))
assert sorted(fp(f)for f in a.GetFootprints())==sorted(fp(f)for f in b.GetFootprints()),'Fixed pose/value/pad-net contract changed'
def tr(t):return(t.GetNetname(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth(p.F_Cu)if isinstance(t,p.PCB_VIA)else t.GetWidth(),t.GetDrillValue()if isinstance(t,p.PCB_VIA)else None)
old={uid(t):tr(t)for t in a.GetTracks()};new={uid(t):tr(t)for t in b.GetTracks()};removed={q['uuid']for q in l['removed']};modified={q['before']['uuid']for q in l['modified']};added={q['uuid']for q in l['added']}
assert all(new.get(u)==v for u,v in old.items()if u not in removed|modified),'Unledgered original track change'
assert not(removed&new.keys()),'Removed tracks still present'
assert set(new)-set(old)==added,'Added track ledger mismatch'
assert set(old)-set(new)==removed,'Deleted track ledger mismatch'
for item in l['modified']:
 q=item['after'];u=q['uuid'];actual=new[u];assert actual[0]==q['net'] and actual[2]==tuple(round(v*1e6)for v in q['start_mm'])and actual[3]==tuple(round(v*1e6)for v in q['end_mm']),'Boundary modification geometry differs from ledger'

assert b.GetCopperLayerCount()==2
assert all(isinstance(t,p.PCB_VIA)or t.GetLayer()in[p.F_Cu,p.B_Cu]for t in b.GetTracks())
def psdata(ps):return[([xy(ps.Outline(i).CPoint(k))for k in range(ps.Outline(i).PointCount())],[[xy(ps.Hole(i,j).CPoint(k))for k in range(ps.Hole(i,j).PointCount())]for j in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())]
az={uid(z):z for z in a.Zones()};bz={uid(z):z for z in b.Zones()};power=[]
for u,z in az.items():
 assert u in bz and psdata(z.Outline())==psdata(bz[u].Outline()),'Existing zone removed or outline changed'
 if z.GetIsRuleArea()or z.GetNetname()=='GND':continue
 aa=z.GetFilledPolysList(z.GetLayer());bb=bz[u].GetFilledPolysList(z.GetLayer());diff1=p.SHAPE_POLY_SET();diff1.BooleanAdd(aa);diff1.BooleanSubtract(bb);diff2=p.SHAPE_POLY_SET();diff2.BooleanAdd(bb);diff2.BooleanSubtract(aa)
 power.append({'uuid':u,'net':z.GetNetname(),'layer':a.GetLayerName(z.GetLayer()),'outline_identical':True,'fill_identical':psdata(aa)==psdata(bb),'removed_area_mm2':diff1.Area()/1e12,'added_area_mm2':diff2.Area()/1e12,'before_polygons':aa.OutlineCount(),'after_polygons':bb.OutlineCount()})
b.BuildConnectivity();report={'file':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'poses_values_pad_nets_unchanged':True,'footprints':len(list(b.GetFootprints())),'layers':2,'all_original_track_changes_ledgered':True,'removed_track_via_objects':len(removed),'modified_boundary_tracks':len(modified),'added_track_via_objects':len(added),'native_reloaded_unconnected':b.GetConnectivity().GetUnconnectedCount(False),'power_zone_deltas':power,'supply_polygons_identical':all(q['fill_identical']for q in power),'scope':'Diagnostic architectural pilot; footprint/function population preserved but disconnected-pad functionality NOT accepted. Unconnected nets, native DRC, ground reference, power redistribution and manufacturing/stack gates must still be checked.'};dst.with_suffix('.audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
