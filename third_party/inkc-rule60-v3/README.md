# INKC STUDIO Rule 60 V3 plate drawing

`rule60-v3.dwg` is the Rule 60 V3 plate drawing by **INKC STUDIO (别离)**, the
designer of the Rule 60 V3. It is redistributed here unmodified so the
housing can be rebuilt and checked without third-party downloads.

| | |
| --- | --- |
| File | `rule60-v3.dwg`, AutoCAD R2004 (AC1018), units mm |
| SHA-256 | `48ca24d1f7cf39dba5b0d91581277c6039f2e165a1af83417343bf3f1d53c35c` |
| Obtained from | [minjunkim0205/Hobby-CustomKeyboard @ ecf3575](https://github.com/minjunkim0205/Hobby-CustomKeyboard/blob/ecf3575e9fb844d32f57b42ce6f7f23f30294396/keyboards/housings/Rule60/housing-design-files/rule60-v3.dwg) (that repository has no license) |
| Created / last saved | 2024-05-31 / 2024-06-17, Chinese AutoCAD 2020 (zh-CN) |

## Why it is attributed to INKC STUDIO

- Every label is in simplified Chinese (`6095定位板`, `全兼容定位板（PCB卫星轴）`,
  `rule60v3 内配 厚度4.5MM`, `rule60v3 外配装饰板 厚度3mm`).
- It was created two days before the Rule 60 V3 sale opened (2024-06-02).
- Later community drawings embed the same content under the block name
  `rule 60 v3 定位板（和V2不通用）`.

## Terms

The creator's Rule 60 V3 interest-check post
(<https://www.zfrontier.com/app/flow/GJ7JjlX8qwxY>) states:

> 5. 单外壳加兼容 GH60规格的pcb（wooting等磁轴方案建议使用top结构，定位板图纸开源，自行改装定位板）

"The bare case also fits GH60-spec PCBs (top mount is recommended for
Wooting-style magnetic-switch boards); the plate drawings are open source,
modify the plate yourself."

No formal license accompanies that statement. This file is **not** covered by
this repository's CC BY 4.0 license; it stays the work of INKC STUDIO. It is
redistributed on the strength of the statement above, with attribution. If
INKC STUDIO objects, it will be removed.

Community drawings derived from it (gasket-top, island, socks, HE plates) are
the work of other people, carry no license and are not redistributed here;
see the repository linked above.

## Contents and use

The drawing holds 10 gasket-mount and 9 top-mount plate variants (two
outlines, varying key cutouts), the 8 top-mount holes (Ø2.2), the battery-bay
filler (`内配`, 139.6 × 44.6 × 4.5 mm) and the 3 mm back decoration plate
(`外配装饰板`, 239.6 × 35.6 mm). It has no case, PCB or ball-catch geometry.

[`spec/rule60-v3-outlines.json`](../../spec/rule60-v3-outlines.json) is
extracted from it:

```sh
(cd tools/dwg && bun install)
bun tools/dwg/dwg_to_json.mjs third_party/inkc-rule60-v3/rule60-v3.dwg /tmp/rule60-v3.json
uv run tools/dwg/extract_outlines.py third_party/inkc-rule60-v3/rule60-v3.dwg /tmp/rule60-v3.json spec/rule60-v3-outlines.json
```
