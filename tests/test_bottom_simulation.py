"""Independent invariants for waveform decisions and capacitor stress screens."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb/tools/signal_integrity'))
from sim_mixed_led import measure,PROFILES
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb/tools'))
from simulate_bottom_pwm import simulate
from simulate_bottom_thermal import heat_pads,mesh
from shapely.geometry import box
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
from sim_usb import edge_times
class BottomSimulationTest(unittest.TestCase):
 def test_clean_nominal_bits_satisfy_both_receiver_parts(self):
  t=np.arange(0,5001,.2);v=np.zeros(len(t))
  for start,high in [(100,300),(1300,900),(2500,300),(3700,900)]:
   v+=4*np.minimum(np.clip((t-start),0,1),np.clip(start+high+1-t,0,1))
  for profile in PROFILES.values():self.assertTrue(measure(t,v,profile)['meets_assumed_corner'])
 def test_missing_pulse_is_rejected(self):
  t=np.arange(0,5001,.2)
  self.assertFalse(measure(t,np.zeros(len(t)),PROFILES['SK6812MINI-E-012'])['meets_assumed_corner'])
 def test_aligned_pwm_small_cap_fails_and_large_cap_improves(self):
  small=simulate(64,5,1000,8.9e-6,.005,.174,'aligned')
  large=simulate(64,5,1000,470e-6,.005,.174,'aligned')
  self.assertFalse(small['stays_above_3p7']);self.assertTrue(large['stays_above_3p7'])
 def test_phase_assumption_changes_peak_not_mean_load(self):
  self.assertTrue(simulate(64,5,1000,8.9e-6,.005,.174,'distributed')['stays_above_3p7'])
 def test_exclusive_led_has_only_one_heat_source_site(self):
  f={'ref':'LED14','pads':[{'num':n,'net':net,'x':x} for n,net in [('1','GND'),('3','+4V_LED')] for x in [0,20]]}
  for site in [0,1]:
   pads=heat_pads(f,{'LED14':site})
   self.assertEqual(len(pads),2)
   self.assertEqual({p['x'] for p in pads},{site*20})
 def test_usb_low_level_ringing_does_not_pair_next_data_edge(self):
  t=np.arange(0,201,.01)
  # Two 10 ns rises, one 10 ns fall; low ringing crosses only 10%.
  v=np.interp(t,[0,10,20,60,70,75,80,85,100,110,200],[0,0,3.3,3.3,0,0,.6,0,0,3.3,3.3])
  (rise,fall),diagnostics=edge_times(t,v)
  self.assertAlmostEqual(rise,8.,places=4);self.assertAlmostEqual(fall,8.,places=4)
  self.assertEqual(diagnostics[0]['measured_edges'],2)
 def test_thermal_uniform_heating_has_analytic_rise_and_conserves_energy(self):
  material=box(0,0,5,4).difference(box(2,1,3,3))
  _,areas,L=mesh(material,.5)
  h=5.;power=100*areas
  rise=spsolve(.01*L+diags(2*h*areas),power)
  np.testing.assert_allclose(rise,10.,rtol=1e-9)
  self.assertAlmostEqual(float((2*h*areas*rise).sum()),float(power.sum()),places=12)
if __name__=='__main__':unittest.main()
