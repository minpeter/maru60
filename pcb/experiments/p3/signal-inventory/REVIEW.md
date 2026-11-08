# P3 remaining actual signal components — read-only inventory

Bound to immutable C105-ground-complete source723ce052, not an adopted board. Native track/pad graph deliberately excludes zone-fed power/GND/VREG and NC nets. This is not the native unconnected-item count.

There are **42 split populated non-power nets**:22 matrix nets (ROW0–4,COL0–14,KEY_2,KEY_16),6 QSPI nets,4 USB nets and10 control/RGB/service nets. The JSON records every physical pad and distinct ref/pin endpoint by native component, so remaining work targets actual populated functions rather than obsolete geometric endpoints.

Additionally,11 padless non-power components contain40 copper objects. These are a classification, not automatic permission to erase them: each needs original-boundary/foreign-reference/return and future-interface review before retirement. Do not feed padless stubs solely to lower a metric; do not delete loaded source trunks because one old core endpoint moved. Physical duplicate-number pads are not automatically merged by this report.

Signal inventory can be reused across later positive-rail-only stages only after exact non-power geometry/pad/net retention is verified. It does not prove source rails, powered operation, critical reference/SI, GPIO timing, assembly or firmware. A25's actual KEY16 closure has only a separate static reuse screen so far and is intentionally still listed split here.
