#!/usr/bin/env python3
"""Read-only current-source audit. Run using run-kicad.sh /usr/bin/python3 verify.py.
Requires installed KiCad pcbnew 9; never saves CAD. Writes audit JSON here only.
"""
import hashlib,json,pathlib,xml.etree.ElementTree as ET
import pcbnew
HERE=pathlib.Path(__file__).resolve().parent
R=HERE.parents[1]; REPO=R/'selected-repo'
CAD=REPO/'pcb/experiments/resume-20261106-usb-pendant-prototype/pcb'
FW=REPO/'pcb/firmware/qmk/keyboards/maru60/rp2350'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5'
assert sha(CAD/'maru60.kicad_pcb')==expected
root=ET.parse(HERE/'netlist-fresh.xml').getroot()
assert root.findtext('./design/source')==str(CAD/'maru60.kicad_sch')
old=ET.parse(HERE/'netlist.xml').getroot()
def nodes(r):return {n.get('name'):sorted((p.get('ref'),p.get('pin')) for p in n.findall('node')) for n in r.findall('./nets/net')}
nets=nodes(root); assert nodes(old)==nets
refs={'U1','U2','U5','U6','U7','U8','U11','U12','U18','F1','D100','L2','R109','R112','R113','R120','R121','R122','R123','R124','R125','R126','R128','R159','R160','C100','C120','C124','C125','C126','C136','C137','C138','C139','C140','C141'}
board=pcbnew.LoadBoard(str(CAD/'maru60.kicad_pcb'))
fps={f.GetReference():f for f in board.GetFootprints()}
index={(ref,pin):net for net,ns in nets.items() for ref,pin in ns}
components={}
for c in root.findall('./components/comp'):
 ref=c.get('ref')
 if ref not in refs:continue
 f=fps[ref]; assert f.GetValue()==c.findtext('value'),ref
 pins={p.GetNumber():p.GetNetname() for p in f.Pads() if p.GetNumber()}
 for pin,net in pins.items():assert index[(ref,pin)]==net,(ref,pin,net)
 components[ref]={'value':f.GetValue(),'native_pins':pins,'fields':{x.get('name'):x.text for x in c.findall('./fields/field')}}
assert nets['USB_INPUT_FAULT_N']==[('R126','1'),('U8','4')]
assert nets['GPIO_ISOLATE']==[('R128','1'),('U11','19'),('U12','2')]
assert nets['LED_ENABLE']==[('R109','1'),('U1','34'),('U7','3')]
assert nets['LED_FAULT_N']==[('R113','2'),('TP9','1'),('U1','35'),('U7','4')]
assert nets['RUN']==[('SW101','1'),('TP6','1'),('U1','26')]
config=(FW/'config.h').read_text(); rgb=(FW/'maru_rgb.c').read_text()
assert '#    define MARU60_LED_POWER_QUALIFIED 0' in config
assert '#define MARU_LED_FAULT_N GP23' in rgb
hashes={str(p.relative_to(REPO)):sha(p) for p in sorted(CAD.glob('*.kicad_sch'))+sorted(FW.glob('*')) if p.is_file()}
hashes[str((CAD/'maru60.kicad_pcb').relative_to(REPO))]=expected
focus=['VBUS','VBUS_FUSED','VBUS_PROTECTED_RAW','+4V_REG','+3V3','+4V_LED','USB_INPUT_FAULT_N','GPIO_ISOLATE','LED_ENABLE','LED_FAULT_N','RUN']
result={'outcome':'QUALIFICATION_GAPS_NOT_HARDWARE_FAILURE','native_version':pcbnew.Version(),'checks':{'pcb_hash':'PASS','fresh_export_source':'PASS','previous_export_connectivity_parity':'PASS','selected_component_value_and_all_native_pad_parity':'PASS','fault_observability_topology':'PASS','default_LED_qualification_OFF':'PASS'},'components_checked':len(components),'native_pins_checked':sum(len(c['native_pins']) for c in components.values()),'source_hashes':hashes,'fresh_netlist_sha256':sha(HERE/'netlist-fresh.xml'),'components':components,'nets':{n:nets[n] for n in focus if n in nets},'not_run':['active power simulation','hardware brownout/load/startup measurements','compiled firmware test','DRC rerun','loop/thermal qualification'],'limitations':['Logical net membership is not proof of physical continuity; current PCB remains incompletely routed.','Assertions verify topology and textual policy, not timing or compiled binary behavior.','No source CAD or firmware changes.']}
(HERE/'EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('outcome','checks','components_checked','native_pins_checked')}))
