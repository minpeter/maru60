from pathlib import Path
import datetime,hashlib,json,platform,subprocess,shutil
import numpy,scipy,shapely,matplotlib
root=Path.cwd();cand=root/'pcb/experiments/resume-20261113-bottom-assembly-prototype';out=cand/'evidence/simulation-suite-20261114';raw=root/'build/bottom-sim-20261114'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
s=json.loads((out/'summary.json').read_text())
assert s['LED']['first_hop_refined_flagged_remaining']==2
p=out/'REPORT.md';t=p.read_text().replace('해당 두 조건의 추가 시간 간격 재검사 결과는 `led/first-refinement.json`과 `summary.json`에 기록했다.','0.025 ns 재검사에서도 두 조건 모두 재교차가 남았다. 결과는 `led/first-refinement.json`과 `summary.json`에 기록했다.');p.write_text(t)
rows=[]
for r in s['PWM']['selected']:
 c=r['effective_cap_uF'];passed=r['stays_above_3p7'];time=s['PWM']['aligned_on_time_us'] if passed else r['first_below_spec_us'];width=100*time/s['PWM']['aligned_on_time_us'];label=f'{c:g} µF';desc=f'{r["min_valid_voltage"]:.3f} V 유지' if passed else f'{time:.2f} µs 후 이탈'
 rows.append(f'<div class="barrow"><span class="cap">{label}</span><div class="track"><div class="fill {"held" if passed else "lost"}" style="width:{width:.3f}%"></div></div><span class="value">{desc}</span></div>')
html='''<!doctype html><html lang="ko"><head><meta charset="UTF-8"><style>
:root{color-scheme:light dark}body{margin:0;color:var(--foreground);font-family:var(--font-sans);font-size:14px;line-height:1.6}p{margin:8px 0 14px}strong{font-weight:650}.scope{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.scope span{background:var(--secondary);border-radius:var(--radius);padding:5px 10px;font-size:12px}.note{color:var(--muted-foreground);font-size:12px}.plot{padding:16px;background:var(--card);border-radius:var(--radius)}.chart{height:252px}.barrow{display:grid;grid-template-columns:66px minmax(60px,1fr) 104px;align-items:center;gap:10px;height:42px}.track{height:16px;background:var(--secondary);border-right:1px dashed var(--muted-foreground)}.fill{height:16px}.lost{background:var(--destructive)}.held{background:var(--chart-2)}.value{font-size:12px;text-align:right;font-variant-numeric:tabular-nums}.cap{font-size:13px}.barrow:first-child .cap{font-weight:750}.scale{text-align:right;font-size:12px;color:var(--muted-foreground);margin-right:114px}.key{color:var(--destructive);font-weight:650}.observations{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}.observations div{padding:16px;border-radius:var(--radius);background:var(--secondary)}@media(max-width:440px){.observations{grid-template-columns:1fr}.barrow{gap:6px;grid-template-columns:60px minmax(40px,1fr) 97px}.plot{padding:12px}.scale{margin-right:103px}}
</style></head><body>
<div class="scope"><span>전원 SPICE 30조건</span><span>LED 신호 810조건</span><span>PWM 1,620조건</span><span>열 360조건</span></div>
<p><strong>동시에 켜지는 LED의 순간 전류가 가장 큰 문제입니다.</strong><br>현재 용량 가정은 19.61 µs 점등 구간을 지지하지 못합니다.</p>
<div class="plot"><p><strong>LED 전원이 3.7 V 이상을 유지하는 시간</strong></p><div class="scale">점등 구간 끝 · 19.61 µs ↓</div><div class="chart">'''+''.join(rows)+'''</div><p class="note">8.9 µF는 현재 부품의 유효용량 가정입니다. 12.5 µF는 명목 합계, 47–470 µF는 가상 비교입니다. 막대가 끝까지 이어져도 실제 부품 변경이 검증된 것은 아닙니다.</p></div>
<p class="note">조건: 64키 RGB code 5, PWM 위상 일치, 1 kHz, 4 V 공급, 전류제한 174 mA, ESR 5 mΩ. 키 LED 순간 피크 2.784 A. 3.7 V 미만에서는 모델을 종료했습니다.</p>
<div class="observations"><div><strong>USB · 키 입력</strong><br>USB 지연 0.418 / 1 ns<br>키 선택 안정화 237 / 800 ns<br><span class="note">모델상 시간 여유 확보</span></div><div><strong>LED 신호</strong><br><span class="key">초기 37조건 재교차 경고</span><br>정밀 재검사: 35개 유지, 2개 민감<br><span class="note">실제 출력·입력 특성 확인 필요</span></div></div>
<p class="note">현재 PCB의 계산 결과이며 실측·제조 승인이 아닙니다. 첫 LED 전체 경로에서도 별도 두 조건의 경고가 남았습니다.</p>
</body></html>'''
(out/'dashboard.html').write_text(html)
# Preserve the earlier manifest as historical evidence; do not recalculate it.
status=cand/'evidence/latest-status.json';d=json.loads(status.read_text());d['usb_board_delay_model_ns']=s['USB_delay_ns'];d['simulation_suite']={'report':'evidence/simulation-suite-20261114/REPORT.md','manifest':'evidence/simulation-suite-20261114/manifest.json','summary':'evidence/simulation-suite-20261114/summary.json','board_unchanged':True,'RGB_qualification':0,'model_outcome':'LED synchronized PWM supply fails tested assumptions; fast output and full first-hop recrossing flags remain','regression_tests_passed':21};d['unresolved'][1]='Mixed LED signal recrossings under assumed drivers, physical buffer/LED models and 3D inner returns; USB metric corrected but hardware qualification outstanding';d['historical_manifest_note']='verification-manifest.json retains the prior CAD/analysis snapshot. Simulation geom.py, sim_usb.py and sim_xtal.py were changed; use simulation-suite-20261114/manifest.json for this campaign.';write(status,d)
p=cand/'README.md';t=p.read_text();anchor='## Inputs and reproduction';addition='''## Simulation campaign — 2026-11-14

[Full report](evidence/simulation-suite-20261114/REPORT.md) and [result summary](evidence/simulation-suite-20261114/summary.json) cover 30 power SPICE conditions, 810 mixed-LED conditions, full first hops and crosstalk, 1,620 PWM charge conditions, 360 thermal cases, USB/matrix/crystal, and current-netlist firmware checks. Twenty-one focused simulation regressions pass. The PCB hash is unchanged.

The campaign **does not qualify LED operation**. With synchronized 64-key RGB code 5 at 1 kHz, the existing assumed 8.9 µF falls below the reverse LED's 3.7 V minimum after about 0.92 µs of a 19.61 µs on-time. Initial fast-driver signal checks flag 37 cases; 35 remain at tighter time steps and two are numerically sensitive. Two full first-hop buffer cases also retain threshold recrossings. USB delay is 0.4184 ns after correcting the route extractor and edge measurement. Firmware RGB qualification remains zero.

The prior `evidence/verification-manifest.json` is a historical snapshot. The simulation tools have since changed; the new [simulation manifest](evidence/simulation-suite-20261114/manifest.json) separately pins the code, results and raw artifact inventory. Neither snapshot implies manufacturing release.

''';assert anchor in t
if '## Simulation campaign — 2026-11-14' not in t:t=t.replace(anchor,addition+anchor)
p.write_text(t)
p=cand/'REPRODUCE.md';t=p.read_text();extra='\n## Supplementary simulation campaign (2026-11-14)\n\nSee [simulation commands](evidence/simulation-suite-20261114/COMMANDS.md) and the separate [manifest](evidence/simulation-suite-20261114/manifest.json). This campaign corrects the SI route extractor and USB edge measurement; prior tool hashes remain historical. The saved PCB and baseline are unchanged. RGB remains unqualified.\n'
if '## Supplementary simulation campaign (2026-11-14)' not in t:p.write_text(t+extra)
shutil.copyfile(Path(__file__),out/'finalize_report.py')
for p in [root/'tools/check_pcb_portable.py',root/'pcb/firmware/tests/matrix_simultaneous_model.py',root/'pcb/experiments/led-startup-recovery/evidence/static-v7/check.py']:
 dest=out/'source'/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
write(out/'manifest.json',{'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Computational models only; NOT FOR FABRICATION; PCB unchanged','inputs':{str(p.relative_to(root)):sha(p) for p in [cand/'pcb/maru60.kicad_pcb',cand/'evidence/final-geometry.json',raw/'netlist.xml',cand/'evidence/verification-manifest.json']},'dependency_versions':{'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__,'matplotlib':matplotlib.__version__},'ngspice_image_id':subprocess.check_output(['docker','image','inspect','maru60-ngspice:bookworm','--format','{{.Id}}'],text=True).strip(),'scope_notes':['Prior verification-manifest is historical and not rewritten; geom/USB/xtal tools changed.','Power numerical execution used source-at-power-run wrapper; final wrapper only fixes labels.','Per-step SI provenance hashes unused modules too; each actual simulator and geometry dependencies are snapshotted.','Initial failed power/thermal and superseded extraction runs are excluded from accepted results.','Two refined LED decisions changed; time sensitivity is not spatial convergence.','Large raw files are local build artifacts enumerated by raw-artifacts.json.'],'artifacts_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'},'current_status_sha256':sha(status)})
print(out/'REPORT.md')
