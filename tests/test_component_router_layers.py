"""Inner routing may cross outer congestion, but must respect inner keepouts."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb/tools'))
import route_component_pair as R
from test_local_router_cutouts import board,part

class LayerRoutingTest(unittest.TestCase):
    def test_plated_terminal_and_unplated_hole_are_distinct(self):
        terminal=part('PTH','SIG',(-1.25,-1.25,1.25,1.25))
        pad=terminal['pads'][0]
        pad.update(attr=0,drill=[1.7,1.7],layers=['F.Cu','B.Cu'])
        g=board([terminal])
        mapped=R.Maps(g,{'SIG'},[-3,-3,3,3])
        cy,cx=mapped.cell(0,0)
        self.assertGreater(mapped.dist_all['B.Cu'][cy,cx],.255)
        # Drilling another via here is still forbidden.
        self.assertEqual(mapped.dist_holes[cy,cx],0)
        pad.update(attr=3,net='')
        unplated=R.Maps(g,{'SIG'},[-3,-3,3,3])
        self.assertEqual(unplated.dist_all['B.Cu'][cy,cx],0)

    def test_inner_route_and_return_corridor(self):
        bottom=part('B','BLOCK',(-.5,-9,.5,9))
        top=part('F','BLOCK',(-.5,-9,.5,9))
        top['layer']='F.Cu';top['pads'][0]['layers']=['F.Cu']
        g=board([bottom,top])
        groups=[[['F.Cu',-3,0]],[['F.Cu',3,0]]]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'components.json';path.write_text(json.dumps(groups))
            with patch.object(R,'LAYERS',('F.Cu','In1.Cu','In2.Cu','B.Cu')),patch.object(R,'arg',lambda name,default=None:str(path)):
                m=R.Maps(g,{'SIG'},[-4,-4,4,4])
                result=R.search(m,groups[0][0],groups[1][0],None,3,.255,.5)
                self.assertIsNotNone(result)
                self.assertTrue(any(p[0] in ('In1.Cu','In2.Cu') for p in result[0]))
                g['zones'].append(dict(net='',keepout=True,layers=['In1.Cu','In2.Cu'],fill={},outline=[[[-.7,-9],[.7,-9],[.7,9],[-.7,9]]]))
                blocked=R.Maps(g,{'SIG'},[-4,-4,4,4])
                self.assertIsNone(R.search(blocked,groups[0][0],groups[1][0],None,3,.255,.5))

if __name__=='__main__':unittest.main()
