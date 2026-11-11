# Strict-baseline promotion decision — relocated-expansion 0/0 prototype

**Board:** `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`  
**SHA256:** `cb7b5b2941bc0e1c4d0a1d10c6dd694f8cf35c4f35665c342dfb747492e10a5d`  
**Witness input:** `qa/geos-rational-witnesses.json` (1,837 witnesses, 0.550960467 mm²)  
**Generated:** 2026-11-11T00:28:00Z  
**Scope:** read-only geometry analysis; no DRC/refill replay, no physical qualification.

## Decision: **PROMOTE_UNDER_AMENDED_POLICY**

The 0/0 prototype is electrically, thermally and manufacturing-wise sound with respect to the 0.551 mm² outside-window area, but it does **not** satisfy the strict baseline's current zero-outside-window policy. The area is dominated by the designed 0.25 mm `zone_min_thickness` fillet cusps between adjacent new vias, not by a defect. Promotion is conditional on a documented window-policy amendment (or an explicit fillet-cusp waiver) and on resolving the residual keyhole-chord artifacts. If the zero-outside-window rule is non-negotiable, the answer is **DO NOT PROMOTE**.

## 1. What the 0.551 mm² actually is

The witness file contains **1,837** exact-rational witnesses totalling **0.550960467 mm²**: **932** on `In1.Cu` (0.270373827 mm²) and **905** on `In2.Cu` (0.280586640 mm²). Every witness is outside the declared circular via-transition windows (minimum window gap 0.002322 mm).

| Class | Witnesses | Area (mm²) | Share | Geometric cause |
| --- | ---: | ---: | ---: | --- |
| `fillet_window` | 26 | 0.507054638 | 92.031% | 0.25 mm `zone_min_thickness` cusp between two adjacent added vias; the cusp lies outside both 0.455 mm windows |
| `via_antipad` | 9 | 0.042630488 | 7.737% | single-antipad crescent just outside one 0.455 mm window |
| `keyhole_chord` | 1,802 | 0.001275341 | 0.231% | Clipper2 integer keyhole fracture-line reshuffling; integer-grid slivers far from the added vias (recorded chord shift: 1 nm) |
| `other` | 0 | 0.000000000 | 0.000% | none in this dataset |

The classification is geometric: a witness within 0.60 mm of an added via is via-associated; if it is within 0.60 mm of two added vias whose distances differ by at most 0.01 mm and whose centers are at most 1.20 mm apart, it is a two-via fillet cusp; otherwise it is a single-antipad crescent. Witnesses farther than 0.60 mm from every added via are keyhole-chord slivers.

### Per-layer breakdown

| Layer | `fillet_window` | `via_antipad` | `keyhole_chord` | `other` | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `In1.Cu` | 13 / 0.249715093 | 4 / 0.020007964 | 915 / 0.000650770 | 0 / 0.000000000 | 932 / 0.270373827 |
| `In2.Cu` | 13 / 0.257339544 | 5 / 0.022622524 | 887 / 0.000624572 | 0 / 0.000000000 | 905 / 0.280586640 |

### Largest witnesses

| Layer | Index | x (mm) | y (mm) | Area (mm²) | Class | Nearest added via | d1 (mm) | d2 (mm) |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `In1.Cu` | 929 | 42.9250 | 78.6000 | 0.024366810 | `fillet_window` | `EXT_GPIO10` | 0.5274 | 0.5274 |
| `In2.Cu` | 902 | 42.9250 | 78.6000 | 0.024366810 | `fillet_window` | `EXT_GPIO10` | 0.5274 | 0.5274 |
| `In1.Cu` | 37 | 106.4000 | 84.0250 | 0.024366761 | `fillet_window` | `COL10` | 0.5274 | 0.5274 |
| `In2.Cu` | 64 | 106.4000 | 84.0250 | 0.024366761 | `fillet_window` | `COL10` | 0.5274 | 0.5274 |
| `In1.Cu` | 930 | 98.3250 | 77.7750 | 0.023947710 | `fillet_window` | `COL11` | 0.5256 | 0.5256 |
| `In1.Cu` | 931 | 103.4250 | 72.6250 | 0.023947710 | `fillet_window` | `SWDIO` | 0.5256 | 0.5256 |
| `In2.Cu` | 903 | 98.3250 | 77.7750 | 0.023947710 | `fillet_window` | `COL11` | 0.5256 | 0.5256 |
| `In2.Cu` | 904 | 103.4250 | 72.6250 | 0.023947710 | `fillet_window` | `SWDIO` | 0.5256 | 0.5256 |
| `In2.Cu` | 67 | 107.5250 | 87.9250 | 0.023112918 | `fillet_window` | `COL3` | 0.5303 | 0.5303 |
| `In1.Cu` | 43 | 108.1250 | 86.3250 | 0.023112899 | `fillet_window` | `MCU_GPIO10` | 0.5303 | 0.5303 |

The 26 fillet cusps are the dominant term: each is a compact 0.15–0.28 mm region at the midpoint of a pair of added vias about 1.05 mm apart. The two 0.45 mm antipads leave a 0.15 mm neck; the 0.25 mm `zone_min_thickness` fillet removes the neck, and the resulting cusp extends to about 0.53 mm from each via center — outside the 0.455 mm declared window. The 9 crescents are the analogous single-via remnant (0.002–0.032 mm outside the window). The 1,802 keyhole-chord witnesses are integer-grid Clipper2 fracture-line reshuffling artifacts (the recorded chord shift is 1 nm); their total area is only 0.001275 mm².

## 2. Risk assessment

| Domain | Finding | Risk |
| --- | --- | --- |
| Electrical | Both inner `GND` planes remain one connected island; net area increased (`In1.Cu` +43.408 mm², `In2.Cu` +20.5404 mm²); minimum different-net inner-plane neck is 0.1512 mm (> 0.15 mm rule); native DRC 0 opens / 0 warnings / 0 other errors. | **None attributable to the 0.551 mm².** |
| Thermal | The 0.507 mm² of fillet cusps is 0.0022% of the ~23,500 mm² plane; the plane area increased overall. | **None attributable to the 0.551 mm².** |
| Manufacturing | The cusps are a designed `zone_min_thickness` fillet, not a defect; the board passes native DRC and cold refill. | **None attributable to the 0.551 mm².** |
| Tolerance policy | The 0.455 mm / 0.755 mm declared windows do not cover the two-via fillet cusp; the strict baseline's zero-outside-window rule is therefore violated by 0.551 mm². | **Policy artifact, not a physical risk.** |

The 0.551 mm² is therefore best described as a **tolerance-policy artifact**: the declared windows were sized for a single via's antipad, not for the cusp created when two new vias are placed about 1.05 mm apart and the 0.25 mm `zone_min_thickness` fillet is applied. The keyhole-chord component (0.001275 mm², 0.231%) is a pure Clipper2 integer-representation artifact.

## 3. What promotion would require

1. **Amend the declared-window policy** to cover the two-via fillet cusp. The simplest defensible change is a capsule/union window around each adjacent via pair (or a 0.55 mm non-GND / 0.85 mm GND radius) with a written rationale that the cusp is a designed `zone_min_thickness` fillet. Alternatively, explicitly waive the outside-window rule for fillet cusps.
2. **Resolve the 9 single-antipad crescents** (0.042630 mm²). Determine whether they are real copper voids or artifacts of the antipad/track interaction; if real, widen the window or adjust the via placement.
3. **Resolve the 1,802 keyhole-chord slivers** (0.001275 mm²). Use a tolerance-aware comparison that ignores 1 nm Clipper2 keyhole fracture-line reshuffling, or regenerate the planes with a deterministic keyhole topology.
4. **Re-run the full audit** (native DRC, cold refill, portable checks, GEOS + exact Q² replay) and confirm 0 opens, 0 warnings, 0 other errors, single inner islands, and zero outside-window area under the amended policy.
5. **Complete the outstanding qualification** that is independent of this geometry: bottom-case clearance for the relocated `B.Cu` parts, active power, USB SI/EMI, thermal, and hardware/fit gates. The prototype README and `pcb/CURRENT.md` already list these as open.

## 3b. Amended policy result

The amended policy keeps the original single-via windows and adds a 0.55 mm capsule around each adjacent pair of non-GND added vias (centers <= 1.20 mm, active only in the inter-via neck >= 0.50 mm from both centers).

| Class | Outside count | Outside area (mm²) |
| --- | ---: | ---: |
| `fillet_window` | 0 | 0.000000 |
| `via_antipad` | 9 | 0.042630 |
| `keyhole_chord` | 1802 | 0.001275 |
| `other` | 0 | 0.000000 |
| **total** | **1811** | **0.043906** |

Under the amended policy, 1811 witnesses / 0.043906 mm² remain outside the window. The designed two-via fillet cusps are covered; the residual is the single-antipad crescents and the Clipper2 keyhole-chord slivers.

## 4. Recommendation

**PROMOTE_UNDER_AMENDED_POLICY.**

The 0/0 prototype is a genuine improvement over the strict baseline on the criteria that matter physically: 0 opens, 0 warnings, 0 other DRC errors, single connected inner planes, and a net increase in `GND` copper. The 0.551 mm² outside-window area is 92.0% designed fillet cusp, 7.7% single-antipad crescent, and 0.23% Clipper2 keyhole-chord artifact; it is not an electrical, thermal or manufacturing defect. Promotion should therefore be **conditional**, not rejected on physical grounds. The condition is a policy decision: either amend the declared windows to include the fillet cusp (preferred, because the cusp is a designed DFM feature) or explicitly waive the cusp area. If the strict baseline's zero-outside-window rule is treated as non-negotiable, the correct decision is **DO NOT PROMOTE** until the via pairs are re-spaced or the windows are amended.

## 5. Reproduction

```sh
.venv/bin/python pcb/tools/analyze_strict_promotion.py
```

The script verifies the board SHA256, reconstructs the 156 declared windows from `qa/routing-scope.json` and the board's GND thermal gap, classifies every witness, and writes `witness-map.json`, `witness-map.svg` and this report.

## 6. Limitations

- The classification is geometric and threshold-based; it does not replay KiCad's zone filler or DRC.
- Nearest-object distances are center/edge distances from the parsed board geometry; pad positions use the standard footprint-local transform and are not a substitute for a full shape-clearance check. The nearest object may be on a different copper layer; the JSON `same_layer` field records this.
- The witness areas are GEOS/Q² areas of the source-minus-candidate plane difference outside the declared windows; they are not a measurement of fabricated copper.
- No electrical, thermal, SI/EMI, mechanical or manufacturing qualification is claimed. The prototype remains not manufacturing-ready.

