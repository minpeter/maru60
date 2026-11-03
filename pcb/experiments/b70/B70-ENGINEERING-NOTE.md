# B70: 고정 배치 2층 실험의 짧은 재연결 5건

## 이번 결과

B75에서 **미연결 75 → 70개**로 줄였다. COL5 4개, COL6 1개의 끊어진 구리 연결을 되살렸다. 두 net 전체가 완성된 것은 아니다. COL5는 5개, COL6는 4개의 native open이 남는다.

- 동결 보드: `checkpoint-shorttree-070.kicad_pcb`
- SHA256: `1b585bd5858f7bf40811ba6fbd285809b1c1d927f35a2eb6916f89f86ea6f60b`
- native DRC: 미연결 70, 일반 오류 0, 회로도 parity 0.
- 경고 105개: track dangling 70 + via dangling 35. 완전한 프로젝트 라이브러리를 갖춘 새 ERC는 0개.
- 변경: 0.20mm track 31개, 총 6.3439675mm; 0.50/0.25mm 관통 via 1개. 기존 B75 객체는 삭제·이동·net 변경 없이 모두 유지.
- 340개 footprint pose/value/pad geometry/net 보존. 고유 전기적 ref/pin 924개, 번호 있는 물리 pad 940개, NPTH 등을 포함한 전체 물리 pad 1275개를 구분한다.
- 4층 main, 기존 B40/B43/B44/B75는 편집하지 않았다. B40의 40개와 B70의 70개는 USB 구조가 다른 후보이므로 단순 성적 비교를 하면 안 된다.

**판정은 조건부 배선 진전이다. 제작·전원·USB 검증 합격이 아니다.**

## 전략과 거절한 후보

한 DRC airwire의 끝점만 잇는 대신, 실제 native copper component 전체를 만들고 기존 선분 내부에도 0.1mm 이하 간격의 branch anchor를 둔 다중 terminal tree를 사용했다. 부품과 기존 구리를 그대로 두고, USB reference strip 및 기존 power/core 보호 조건을 유지했다. 각 연결의 비용 한도를 25mm(전이 via 비용 포함)로 두었다. 이는 전기 규칙이나 사용자 제약이 아니라, 불필요한 장거리 우회를 채택하지 않기 위한 이번 탐색 범위다.

- COL5 4건: 5.1634145mm + via 1개.
- 최종 채택한 COL6 1건: 1.1805531mm, via 없음.
- 초기 68-open 조합은 COL11과 UG_LED_6의 기존 반대면 GND 투영을 잘라 거절했다.
- 69-open 축소본에도 UG_LED_6 중심선에 0.151813mm의 새로운 공백이 남아 거절했다.
- 별도 수동 69-open 우회는 DRC가 0이어도 USB DP 기준면에 약 1.07705mm의 새 중심선 공백을 만들어 거절했다.
- KEY_RGB_CHAIN_5/UG_LED_6의 185/223mm 장거리 우회도 이번 짧은 연결 후보에 넣지 않았다. +5V의 이전 실패 모델을 반복하거나 전원 폭·clearance를 줄이지 않았다.

## 저장본에 묶인 검증

`gates-final70-complete/BUNDLE.json`은 정확한 PCB/project/schematic/로컬 라이브러리 및 검사 코드 hash를 묶은, 실제 종료된 새 native DRC/ERC/parity와 13 source witness 실행 묶음이다. 실행 완료가 모든 의미상 gate의 합격을 뜻하지는 않는다.

`final70-cold1-proof.json`은 별도의 새 process가 원래와 동일한 project를 먼저 배치하고 Load → connectivity → refill → 같은 경로 Save를 실행한 증거다. B70은 **PCB bytes/SHA가 그대로**였고, 모든 단계에서 project hash도 동일했다. Cold 저장본의 native DRC도 70/0/0/105다.

B75 no-edit control은 첫 refill에서 바뀐 뒤 두 번째에서 안정됐다. B70의 모든 non-GND power fill은 그 독립 B75 cold control과 점 단위로 동일하다. 따라서 작은 +3V3 변화는 이번 새 배선의 독립 효과로 오인하지 않았다. GND의 clearance 제거는 따로 측정했다. Rule/outline/부품값을 바꿔 이 결과를 만들지 않았다.

## 기준면과 source의 남은 한계

기존 outer track 전체의 중심선과 양쪽 폭 가장자리를 연속적인 native polygon 경계 교차로 비교했다. Boolean 결과에 Unfracture를 호출하지 않았다. 최종 B70의 새 누락은 각 구간 최대 0.73nm 이하의 경계 수치 차이뿐이다. 합계는 중심선 1.3585nm, 양쪽 가장자리 각각 0.5144/0.7123nm다. 이를 수학적으로 정확한 0이라고 표시하지 않는다. 거절 후보의 0.15~1mm 공백과는 구분한다.

USB 객체 162개와 모든 기존 escape는 동일하다. 이전의 새 DP/DM trunk는 20,013개 폭/중심 표본 모두 GND 투영을 유지하고, 전체 USB의 누락 3,735/24,366 표본도 B75와 같다. **커넥터·MCU escape가 검증됐다는 뜻은 아니다.** 전체 USB 투영 표본율 84.67%는 길이 가중치나 90Ω/컴플라이언스 검증이 아니다.

새 matrix 구리 자체의 반대면 GND는 완전하지 않다. 끝점/via 예외를 빼지 않은 연속 검사에서:

- COL5 5.1634145mm 중 중심선 1.8431463mm에 GND 투영이 없다.
- COL6 1.1805531mm는 전체 중심선에 GND 투영이 없다.
- 이것은 새 branch의 명시적인 reference/return 검토 항목이다. DRC 0으로 덮거나 전원 투입 가능 판정으로 바꾸지 않는다.

Native critical open은 여전히 **35개: GND 32, +3V3 1, +5V 1, KEY_RGB_5V_BUF 1**이다. 13개 center/edge source witness에서 B75 대비 새로 미도달한 pad는 없다. 해당 witness가 보고하는 미도달은 GND 199/215 pads, +3V3 2/28, +5V 5/7, KEY-BUF 1/2이며 나머지 9개 source 집합은 도달한다. 이는 물리적 annulus를 전부 입증한 결과와 구분한다.

## 물리 annulus 검사 상태

이번 backup 시점의 정확한 상태는 `PHYSICAL-VERIFIER-STATUS.json`과 `FINAL70-RESULT.json`에 있다. **물리 annular/source graph는 아직 완료로 인정하지 않는다.**

원래 공용 helper의 실제 B75/B70 입력을 재현해 검사하니, Boolean drill subtraction 뒤 Unfracture를 호출하는 과정에서 159개 island 중 153개의 형상이 바뀌고 hole 수가 각각 845→0, 842→0으로 줄었다. 그 helper의 기존 결과를 B2L 합격 증거로 쓰지 않았다. 원본 PCB에는 변화가 없다. Hole-preserving 별도 검사 결과는 완료 후 별도 hash-bound 부록으로 추가하며 이 동결 backup을 덮어쓰지 않는다. 이 발견을 4층의 다른 검증 sequence 전체에 일반화하지 않는다.

## 다음 설계 범위

현재 확정된 B70으로 이어가되, 남은 COL5/COL6 branch는 USB/LED 경로를 함께 검토하는 지역 설계가 필요하다. 32 GND open과 +3V3/+5V/key buffer의 기존 source 단절도 그대로 남는다. 107.798mm의 기존 LED 전원 우회, 실제 부하·전압강하·온도, 제조사 stack에 맞춘 USB impedance/return 검증은 이번 작업으로 해결되지 않았다. bare PCB당 기존 $6.54 절감 비교도 검증 완료 절감액으로 바뀐 것이 아니다.
