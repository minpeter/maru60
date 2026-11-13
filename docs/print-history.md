# 실물 제작 기록

제작 회차는 사용자가 지정한 실물 제작 기준이며, CAD의 `v7.x` 버전 번호와는 별개입니다.

## 실물 제작 2차 — v7.15

2026-11-13, 사용자가 이번 출력본을 **실물 제작 2차**로 지정했습니다.
최종 전달한 좌우 파일을 아래 경로에 그대로 보관했습니다. 출력 완료 시점과
조립·사용 결과는 아직 이 기록에 추가되지 않았습니다.

| 항목 | 확정 내용 |
| --- | --- |
| 부품 | Maru60 HHKB 상단 하우징 + 일체형 손목받침 |
| CAD 버전 | `v7.15-centred-joint-axis` |
| 기판 | 6095 tri-mode (`6095-trimode`) |
| 볼캐치 | 정품 Rule 60 V3 (`stock`) |
| 인서트 | CANOT M2, 외경 3.5 × 길이 3.0 mm, 상단 8개 |
| 중앙 리브 | 폭 13.8 mm, 하우징 중심 X=0에 정렬 |
| 짜맞춤·분할선 | 3개 짜맞춤의 축과 주 분할선을 X=-2.9 mm로 이동 |
| 가운데 범폰 | 중심 X=0 유지, 앞쪽의 둥근 16 mm 받침만 국소적으로 넓음 |
| 출력 파일 | 좌우 모두 v7.15 사용; 이전 반쪽과 짜맞춤 위치가 다름 |

### 최종 출력 파일

- [좌우 한 묶음 ZIP](../models/print-02-v7.15-6095-stock-inserts/maru60-v7.15-6095-stock-inserts-print.zip)
- [왼쪽 3MF — 렌더의 파란 부품](../models/print-02-v7.15-6095-stock-inserts/maru60-v7.15-6095-stock-inserts-left.3mf)
- [오른쪽 3MF — 렌더의 주황 부품](../models/print-02-v7.15-6095-stock-inserts/maru60-v7.15-6095-stock-inserts-right.3mf)
- [파일 해시와 제작 회차 manifest](../models/print-02-v7.15-6095-stock-inserts/manifest.json)
- [최종 두 색상 렌더](../rendering/v7_15_6095_stock_inserts/maru60-v7.15-two-tone.png)

각 반쪽은 출력 방향으로 배치되어 있으며 크기는 100%를 유지합니다. 프린터와
필라멘트 프로필은 슬라이서에서 선택합니다. 포함된 Z 5.4–10.0 mm 구간의
0.10 mm 레이어 설정이 반영되는지 확인합니다.

### 이번 설계 변경

v7.13에서는 중앙 리브가 분할선 기준 왼쪽 4.0 mm / 오른쪽 9.8 mm여서
벌집 여백과 가운데 범폰의 정렬이 어긋나 보였습니다. v7.14에서는 리브를
19.6 mm로 넓혔지만, 사용자가 두꺼워진 형태를 지적했습니다.

최종 v7.15는 짜맞춤 형상을 유지한 채 위치를 -X 방향으로 2.9 mm 옮겨,
원래 13.8 mm 리브를 중앙에 정렬했습니다. 벌집 여백은 양쪽 3.903 mm이고,
상판 벌집 패턴과 기판·정품 볼캐치 접합부는 유지했습니다. v7.14는 비교용
기록이며 이번 제작본은 v7.15입니다.

### 검증 기록

- [출력 형상 검증](../rendering/v7_15_6095_stock_inserts/geometry/verification.json):
  `ALL_PASSED`. 메시, 91단계 조립 경로, 유지력 간섭, 접착 간극, 레이어 연결,
  오버행, 정품 부품과 범폰 게이지 및 중앙부 20개 단면 확인.
- [v7.13 대비 형상 비교](../rendering/v7_15_6095_stock_inserts/change-audit.json):
  이동량을 되돌리면 6개 짜맞춤 반쪽의 차이가 각각 0.001 mm³ 미만이며,
  상판과 기판 접합부 형상이 유지됨.
- [회귀 테스트](../rendering/v7_15_6095_stock_inserts/regression.log):
  인서트 옵션, 정품/LUBAN 옵션, 상·하판 조합 관련 8개 테스트 통과.
- [리모트 main 반영 전 검증](../models/print-02-v7.15-6095-stock-inserts/publication-validation.json):
  별도 체크아웃에서 출력 파일 추적 검사를 포함한 11개 테스트와 파일 해시 확인 통과.
- [원본 및 출력 파일 추적](../rendering/v7_15_6095_stock_inserts/source-provenance.json),
  [GPU 렌더 기록](../rendering/v7_15_6095_stock_inserts/two-tone-receipt.json).

위 검증은 CAD 검증 기록입니다. 2차 실물의 출력·조립 관찰은 확인되는 대로
이 항목에 이어 기록합니다.
