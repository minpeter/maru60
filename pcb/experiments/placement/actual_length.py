import os,json,sys,math,hashlib,collections
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-placement-config';os.environ['XDG_CONFIG_HOME']='/tmp/maru-placement-config'
import pcbnew as p
path=Path(sys.argv[1]);b=p.LoadBoard(str(path));c=b.GetConnectivity();c.Build(b)
by_net=collections.defaultdict(float);by_layer=collections.defaultdict(float);vias=[];types=collections.Counter();track_count=0
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  vias.append(t);types[str(t.GetViaType())]+=1
 else:
  length=t.GetLength()/1e6;by_net[t.GetNetname()]+=length;by_layer[t.GetLayerName()]+=length;track_count+=1
planes=[]
for i,z in enumerate(b.Zones()):
 if z.GetIsRuleArea():continue
 planes.append({'zone_index':i,'net':z.GetNetname(),'layers':str(z.GetLayerSet().FmtBin()),'filled_area_mm2':z.GetFilledArea()/1e12,'filled':z.IsFilled()})
fp={f.GetReference():f for f in b.GetFootprints()}
report={'board':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'units':'mm','actual_all_net_all_layer_track_centerline_mm':sum(by_net.values()),'track_items_excluding_vias':track_count,'length_by_copper_layer_mm':dict(sorted(by_layer.items())),'length_by_net_mm':dict(sorted(by_net.items(),key=lambda q:-q[1])),'includes_power_and_ground_tracks':True,'via_count':len(vias),'via_types':dict(types),'through_via_vertical_estimate_mm':sum(b.GetDesignSettings().GetBoardThickness()/1e6 for t in vias if t.TopLayer()==p.F_Cu and t.BottomLayer()==p.B_Cu),'via_vertical_note':'Separate nominal through-board barrel estimate, thickness per through-via. Not included in XY track total; blind/buried spans need stackup layer elevations.','filled_zone_area_by_zone':planes,'plane_note':'Plane area is reported separately; no arbitrary conversion of a plane into one wire. Different-layer areas may overlap geometrically.','native_unconnected_count':c.GetUnconnectedCount(False),'fully_connected':c.GetUnconnectedCount(False)==0,'efficiency_comparison_eligible':c.GetUnconnectedCount(False)==0,'copper_layer_count':b.GetCopperLayerCount(),'board_thickness_mm':b.GetDesignSettings().GetBoardThickness()/1e6,'warning':'An incomplete board cannot be declared shorter/better than a completed board; compare only equal connectivity and native DRC acceptance.'}
out=Path(sys.argv[2]) if len(sys.argv)>2 else path.with_suffix('.actual-length.json');out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['length_by_net_mm','filled_zone_area_by_zone']},indent=2))
