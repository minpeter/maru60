# 기본 실장 구성: 확장 포트 제외

**사용자 결정 “확장 포트는 없어도 됨”을 반영한 기본 실장 후보이다.** J3와 확장 전용 부품 18개를 BOM과 두 실장 위치 목록에서 제외했다. USB 키보드, 키 RGB 64개·언더글로우 12개, Caps Lock·오른쪽 Shift·Backspace 선택, 소켓·스테빌라이저·장착 패턴은 유지한다.

기판 배선과 부품 랜드는 기존 그대로이고, 해당 부품을 붙이지 않는 구성이다. 회로도/PCB의 개별 DNP 표시를 바꾼 것은 아니다. [기본 실장 정책](../../design/assembly-policy.json)과 이 디렉터리의 BOM/parts 규칙이 선택된 구성이다. 이전 root `pcb/order` 파일이나 원본 KiCad 위치 목록으로 이 구성을 대신하면 안 된다.

**제조 승인 전의 후보이며 주문 패키지가 아니다.** LED 전원·신호 문제, 공급사의 역실장 승인 및 최종 견적은 아직 남아 있다. 위치 목록은 KiCad 원점·각도 기준이며 공급사 라이브러리에 맞춘 최종 CPL이 아니다.

## 반영한 내용

미실장 19개:

`C128, C129, J3, R128, R130–R135, R140–R145, U11, U12, U13`

- U11 GPIO 버스 스위치, U12 그 제어용 감시 IC, U13 외부 포트용 ESD와 전용 수동 부품을 함께 제외한다.
- **R126은 유지한다.** 입력 eFuse fault 신호의 pull-up이다. C138/C139, USB/LED/전원 보호 부품도 유지한다.
- 남은 MCU GPIO3/10/24/25/26/27은 U1과 빈 랜드로만 이어진다. 해당 후보 펌웨어에서 LOW를 먼저 기록한 뒤 출력으로 전환한다. 외부 기기가 연결된 기존 확장 포트 구성에는 이 펌웨어를 사용하지 않는다.
- 현재 copper·회로도·geometry 해시는 유지된다. 물리 기판 크기나 층수 절감은 계산하지 않는다.
- Backspace는 split과 2U에 대해 각각 319개 위치 목록을 만들었다. 두 목록의 차이는 LED14와 LED15 위치뿐이며, 어느 목록을 쓰든 **각 reference는 한 개만 실장**한다.
- 실제 조립 스텐실은 미실장 19개와 선택하지 않은 LED14/15 위치에 페이스트를 인쇄하지 않도록 확인해야 한다. 원본 B.Paste를 그대로 최종 스텐실로 승인한 것이 아니다.

## 비용 영향

2026-11-14 공개 가격, 5장, USD/KRW 1,400 및 세금 여유 10% 가정이다. 주문·지불한 비용이나 확정 견적이 아니다.

| 항목 | 이전 전체 확장 구성 | 확장 제외 기본 구성 |
|---|---:|---:|
| 실장 부품/장 | 338개 | **319개** |
| 서로 다른 부품번호 | 56종 | **50종** |
| Basic / Extended | 17 / 39종 | **15 / 35종** |
| 5장 부품 가격, 공개 손실 수량 포함 | $153.1206 | **$132.3270** |
| Standard 설정·스텐실·feeder | $119.45 | **$110.27** |
| 부품 + 위 준비비, 환율·세금 가정 반영 | 419,759원 | **373,599원** |

차액을 반올림하면 **5장 약 46,159원, 장당 약 9,232원 절감 예상**이다. 표의 두 합계를 먼저 반올림해서 빼면 1원 차이가 난다. SMT 작업 차이, X-ray/지그/handling 등은 절감액에 넣지 않았다. 제작·배송 및 기타 조립비도 위 합계에는 없다.

현재 재고 부족이 확인됐던 U13은 이 실장 구성에서 빠진다. 남은 부품의 현재 구매 가능 여부는 주문 시 다시 확인해야 한다. LED 두 종류는 여전히 Standard Only이며, **이 변경만으로 총 25만원 목표를 충족하지 못한다.**

## 검증

- [검사 결과](evidence/population-host.json): BOM 50행, 위치 목록 각 319개, 세 목록의 reference 일치, 19개 누락과 공유 부품 보존, PCB/geometry/netlist 해시 동일.
- [회로 경계](net-boundary.json): 제외 부품과 남은 회로가 만나는 선은 +3V3/GND 및 확장용 GPIO 6개뿐이다. 키 매트릭스·USB·RGB 데이터와 enable/fault GPIO가 제외되지 않는다.
- 시작 함수의 실제 소스를 host C로 실행했다. 미사용 6개 GPIO가 LOW를 기록한 뒤 출력으로 바뀌고, 사용자 hook 전에 RGB enable/data가 LOW이며, 다른 GPIO는 건드리지 않는지 확인했다. GPIO26 초기값 누락과 ROW3/GP29 오조작의 두 오류 주입은 모두 검출됐다. GPIO 하드웨어는 mock이다.
- [현재 netlist 검사](evidence/current-netlist.json): 기존 기능 GPIO 24개 일치. WKL/HHKB의 1·2·3키 조합 합계 72,100개 및 전체 누름/뗌의 이상 매트릭스 검사를 통과했다. 실제 스위치·다이오드·USB 시험은 아니다.
- [ARM 빌드 결과](evidence/firmware-build.json): 준비된 pinned QMK 및 동일 9개 submodule로 `via`, `via_hhkb` 모두 전체 빌드 성공. 다섯 translation unit씩 총 10개 macro dump에서 `MARU60_NO_EXPANSION=1`, **`MARU60_LED_POWER_QUALIFIED=0`**, `GPIO_INPUT_PIN_DELAY=120`을 확인했다.
- 링크된 두 ELF의 시작 함수에 RGB 3개 + 미사용 6개의 GPIO mode 호출을 확인했다. GPIO6개 LOW 설정은 출력 mode 전환 전에 있다. 실제 실행·전기 시험은 아니다. 아무 보드에도 flash하지 않았다.

기존 아날로그 시뮬레이션을 재실행했다고 주장하지 않는다. 배선이 같아도 부품 미실장으로 3.3V 부하 등이 달라지므로 기존 결과를 이 구성의 전원 자격으로 승격하지 않는다. 미해결 RGB 문제와 qualification 0은 유지한다.

## 파일과 재현

- `parts.json`: 선택된 실장 규칙. `variant_omission`은 실제 CAD DNP 플래그와 구분한다.
- `population-all.csv`: 전체 footprint의 실장 여부.
- `bom-review.csv`: 공급사 BOM 형식의 검토용 부품 목록.
- `placements-native-split.csv`, `placements-native-2u.csv`: 각 319개, KiCad 좌표·각도. **최종 JLCPCB CPL 아님.**
- `priced-parts.json`, `summary.json`: 이번 실장 구성의 가격 계산.
- `firmware/`: 이 구성 전용 22파일 overlay. 기존 `pcb/firmware`와 다른 파일은 `maru60.c`, `config.h` 두 개다. `firmware-source.json`이 양쪽 해시를 기록한다.
- `evidence/`: 전체 빌드 로그의 무손실 gzip, 두 ELF/UF2, 검사 결과. UF2는 RGB OFF인 개발용 결과다.
- `prior-cost-policy.json`: 사용자 선택 이전 비용 정책의 사본. 이전 비용 검토 manifest에 기록된 정책 해시와 일치한다. 기존 비용·시뮬레이션 증거는 당시 상태 그대로 보존한다.

저장소 루트에서:

```sh
python3 pcb/experiments/resume-20261113-bottom-assembly-prototype/assembly/no-expansion/generate.py
python3 pcb/experiments/resume-20261113-bottom-assembly-prototype/assembly/no-expansion/verify.py --output /tmp/maru60-noexp-check-new
```

전체 ARM 빌드는 `build/pcb-qmk-20261109/qmk_firmware`의 pinned checkout을 사용했다. 기존 `keyboards/maru60/rp2350`을 덮어쓰지 않고 이 overlay를 별도 target `keyboards/maru60/rp2350_noexp`에 복사했다. `build-firmware.sh`는 `/qmk`와 `/evidence`가 마운트된 동일 build image에서 실행하며, 이미지 ID와 upstream commit은 빌드 결과 파일에 있다. 네트워크·추가 설치 없이 실행했다. 다시 빌드할 때 두 target의 오브젝트를 새로 만들거나 `make ...:clean` 후 실행해 macro dump도 다시 얻어야 한다.
