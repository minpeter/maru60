"""Prevent ordinary vias in SMD/lead-hole exclusions, while using existing barrels."""
import unittest
from types import SimpleNamespace
import numpy as np
from pcb.tools.plan_pair_route import search


class ViaExclusionTest(unittest.TestCase):
    def route(self, smd=10., holes=10., reuse=False, pair=False):
        shape = (21, 21)
        maps = SimpleNamespace(h=21, w=21, x0=0., y0=0.,
            dist_hard={k: np.full(shape, 10.) for k in ('F.Cu','B.Cu')},
            dist_all={k: np.full(shape, 10.) for k in ('F.Cu','B.Cu')},
            dist_smd=np.full(shape, smd), dist_holes=np.full(shape, holes),
            reuse_vias=[(.5,.5)] if reuse else [],
            cell=lambda x,y: (int(round(y/.05)),int(round(x/.05))))
        return search(maps, ('F.Cu',.5,.5), ('B.Cu',.5,.5), None, 4.4,
                      need=.25, via_room=.78 if pair else .43)

    def test_open_space_allows_layer_change(self):
        self.assertIsNotNone(self.route())

    def test_smd_mask_exclusion_blocks_new_vias(self):
        self.assertIsNone(self.route(smd=.20))

    def test_lead_hole_exclusion_blocks_new_vias(self):
        self.assertIsNone(self.route(holes=.55))

    def test_existing_barrel_is_not_a_pair_of_vias(self):
        self.assertIsNotNone(self.route(smd=0., reuse=True))
        self.assertIsNone(self.route(smd=0., reuse=True, pair=True))
