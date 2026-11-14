"""A short branch ending mid-segment must survive dangling-tail cleanup."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pcbnew as p
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb/tools'))
import prune_dangling_tracks as prune

class JunctionPruningTest(unittest.TestCase):
    def test_midsegment_branch_remains_electrically_connected(self):
        b=p.BOARD();net=p.NETINFO_ITEM(b,'SIG');b.Add(net)
        point=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
        fp=p.FOOTPRINT(b);fp.SetReference('TEST');b.Add(fp)
        for i,xy in enumerate([(42.375,57.8),(42.4,64.45)]):
            layers=p.LSET();layers.AddLayer(p.F_Cu)
            pad=p.PAD(fp);pad.SetNumber(str(i+1));pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(point(.6,.6));pad.SetLayerSet(layers);pad.SetPosition(point(*xy));pad.SetNet(net);fp.Add(pad)
        specs=[((42.375,57.8),(43.975,58.6)),((43.975,58.6),(44.04,58.67)),((43.5,59.75),(44.4,57.95)),((42.4,64.45),(43.5,59.75))]
        tracks=[]
        for a,z in specs:
            t=p.PCB_TRACK(b);t.SetStart(point(*a));t.SetEnd(point(*z));t.SetWidth(p.FromMM(.15));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t);tracks.append(t)
        report={'violations':[{'type':'track_dangling','items':[{'uuid':tracks[i].m_Uuid.AsString(),'pos':{'x':specs[i][0][0],'y':specs[i][0][1]}}]} for i in (1,2)]}
        with tempfile.TemporaryDirectory() as tmp:
            board=Path(tmp)/'test.kicad_pcb';drc=Path(tmp)/'drc.json';p.SaveBoard(str(board),b);drc.write_text(json.dumps(report))
            with patch.object(sys,'argv',['prune',str(board),str(drc),'--nets','SIG','--max-length','300']):prune.main()
            after=p.LoadBoard(str(board));after.BuildConnectivity();cn=after.GetConnectivity();pads=list(next(iter(after.GetFootprints())).Pads())
            seen=set();todo=[pads[0]]
            while todo:
                q=todo.pop();uid=q.m_Uuid.AsString()
                if uid in seen:continue
                seen.add(uid);todo.extend(list(cn.GetConnectedTracks(q))+list(cn.GetConnectedPads(q)))
            self.assertIn(pads[1].m_Uuid.AsString(),seen)
            self.assertFalse(any(t.GetEnd()==point(44.4,57.95) for t in after.GetTracks()))

if __name__=='__main__':unittest.main()
