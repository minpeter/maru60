"""Mixed LED revisions must use their actual DIN/DOUT and supply pins."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcb.tools.signal_integrity.extract_geometry import led_chains,led_pins
from pcb.tools.analyze_pdn import led_supply_pad


def led(ref,reverse,din,dout):
    roles={"GND":"1","DIN":"2","VDD":"3","DOUT":"4"} if reverse else {"DIN":"1","VDD":"2","DOUT":"3","GND":"4"}
    nets={"DIN":din,"DOUT":dout,"VDD":"+4V_LED","GND":"GND"}
    return dict(ref=ref,value='SK6812MINI-E-012' if reverse else 'SK6805-EC15-001',x=0,y=0,
                pads=[dict(num=pin,net=nets[fn],pinfn=fn if reverse else '',x=int(pin),y=0) for fn,pin in roles.items()])


class ReverseLedAnalysisTest(unittest.TestCase):
    def test_chain_respects_revised_pinout_across_a_series_resistor(self):
        parts=[led('LED1',True,'KEY_RGB_5V','SRC'),led('LED2',False,'NEXT','END'),led('LED65',False,'UNDERGLOW_5V','UG_END'),
               dict(ref='R170',value='33',pads=[dict(num='1',net='SRC'),dict(num='2',net='NEXT')])]
        chains=led_chains(SimpleNamespace(raw=dict(fps=parts)))
        self.assertEqual(len(chains['key']),2)
        self.assertEqual(chains['key'][0][2],('LED1','2'))
        self.assertEqual(chains['key'][1][2],('LED2','1'))
        self.assertEqual(chains['key'][1][3]['from'],('LED1','4'))
        self.assertEqual(chains['underglow'][0][2],('LED65','1'))

    def test_supply_load_attaches_to_power_net_not_old_pin_two(self):
        self.assertEqual(led_supply_pad(led('LED1',True,'IN','OUT'))['num'],'3')
        self.assertEqual(led_supply_pad(led('LED65',False,'IN','OUT'))['num'],'2')

    def test_inconsistent_or_unknown_pinout_is_rejected(self):
        f=led('LED1',True,'IN','OUT');f['pads'][0]['pinfn']='DIN'
        with self.assertRaisesRegex(ValueError,'mismatch'):led_pins(f)
        f['value']='SK6812MINI-E'
        with self.assertRaisesRegex(ValueError,'Unsupported'):led_pins(f)

if __name__=='__main__':unittest.main()
