"""Record source provenance and final deliverable checksums after reproduction/QA."""
from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
urls={
'21-0168.pdf':'https://mds.analog.com/api/public/content/tdfn-cu_21-0168.pdf',
'90-0065.pdf':'https://pdfserv.maximintegrated.com/land_patterns/90-0065.PDF',
'tnpw_e3.pdf':'https://www.vishay.com/docs/28758/tnpw_e3.pdf',
'grm31cr71h475ka12.pdf':'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71H475KA12-01A.pdf',
'grm31c5c1h683ja01.pdf':'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31C5C1H683JA01-01A.pdf',
'grm1885c1h103ja01.pdf':'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM1885C1H103JA01-01A.pdf',
'max38902evkit.pdf':'https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902EVKIT.pdf',
'tps3890.pdf':'https://www.ti.com/lit/ds/symlink/tps3890.pdf',
'tps3808.pdf':'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
'tps3899.pdf':'https://www.ti.com/lit/ds/symlink/tps3899.pdf'}
entries=[]
for name,url in urls.items():
 p=P/'sources'/name;assert p.read_bytes().startswith(b'%PDF')
 entries.append({'path':str(p.relative_to(P)),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'obtained':'official endpoint via HTTPS, 2026-11-02 UTC'})
for p,url in [(P.parent/'correction-study-20261102/sources/max38902.pdf','https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf'),(Path('/workspace/shared/maru-rp2350-support-audit/datasheet.txt'),'https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf'),(P.parent/'sources/usb20-base.pdf','https://www.usb.org/document-library/usb-20-specification')]:
 entries.append({'path':str(p),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'obtained':'existing pinned local official-source archive; not redownloaded'})
(P/'source-register.json').write_text(json.dumps({'date_UTC':'2026-11-02','sources':entries},indent=2)+'\n')
status={'scope':'isolated component implementation study, not production approval','completed':['exact five-part BOM','official U2 land dimensions and pad numbering','native capacitor land candidates','all pin/net endpoints preserved','ERC 0','placement-only pad/net check and DRC with 12 declared unrouted connections','bounded resistor error allocation','supported 10 nF BYP comparison versus68 nF and omission rejection','explicit hardware RUN/reset/USB restart architecture contract','unchanged accepted PCB and prior correction manifest'],
'pending':[{'action':'Obtain approved effective C and ESR limits','target':'C101 GRM31CR71H475KA12L and ADI ESR frequency contract','reason':'public no-bias X7R/DF data does not bound bias, aging or applicable <30mOhm ESR'},{'action':'Qualify local input impedance/capacitance','target':'C100 and upstream buck/source waveform','reason':'ADI recommends4.7uF; no published2uF input minimum'},{'action':'Approve applicable leakage and cleanliness envelope','target':'C142 GRM1885C1H103JA01D plus assembled PCB','reason':'public IR tests are room-temperature/rated-voltage, not guaranteed hot assembled leakage'},{'action':'Approve declared life/environment error allocation','target':'R163 TNPW060331K6BYEA','reason':'sum of individual test limits is not an arbitrary combined-life warranty'},{'action':'Complete routed Kelvin/EP thermal implementation','target':'isolated LDO tile before PCB adoption','reason':'tile intentionally contains no tracks, vias or planes'},{'action':'Implement and qualify external RUN/reset and enable-isolation path','target':'additional isolated reset revision','reason':'current V6 supervisor drives GPIO_ISOLATE only; typical-only propagation cannot guarantee all dips'},{'action':'Close preconfiguration charging and whole-USB state ledger','target':'10nF BYP startup and complete board','reason':'nominal capacitor charge53.5mA consumes most conditional startup headroom; no all-corner waveform available'}],
'uncertain':['supplier approval','assembled effective C/ESR/leakage','actual fault waveforms and thermal behavior','whole-device current and reset feasibility'], 'denied':[], 'not_performed':['accepted CAD/firmware edits','supplier contact','orders','fabrication','flashing','public push','physical measurements']}
(P/'status.json').write_text(json.dumps(status,indent=2)+'\n')
files=[]
for p in sorted(P.rglob('*')):
 if p.is_file() and p.name!='manifest.json':files.append({'path':str(p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size})
(P/'manifest.json').write_text(json.dumps({'date_UTC':'2026-11-02','status':'ISOLATED STUDY ONLY; inspect pending gates','files':files},indent=2)+'\n')
print('Files:',len(files),'manifest SHA256:',sha(P/'manifest.json'))
