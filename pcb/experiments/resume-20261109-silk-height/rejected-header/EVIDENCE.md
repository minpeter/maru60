# Header routing candidate: REJECTED

Source: `pcb/experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pcb`, SHA256 `41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5`.
Candidate: `candidate/pcb/maru60.kicad_pcb`, SHA256 `4a7d0a5159723398de17a1e47696ec2e61afae9e044ba18484a8a0e5226f59b0`.

All commands run from repository root. Prefix below: `H=.omo/evidence/pcb-routing-20261109/header-candidates`.

| Scenario | Invocation | Binary observable | Captured artifact |
|---|---|---|---|
| Bounded local reroute and full GPIO24 route | `tools/run_kicad9.sh python3 $H/plan.py` | `MULTI_FOUND`, detour and fanout paths present | `planning-multilayer.log`, `qa/plan.json` |
| Generate experimental CAD | `tools/run_kicad9.sh python3 $H/build.py` | Board saved, six removed GPIO10 tracks, three new GPIO24 vias, explicit route geometry | `build.log`, `qa/build.json`, `candidate/pcb/maru60.kicad_pcb` |
| Native DRC/ERC/parity/identity/cold refill | `tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint $H/candidate --output $H/native --expected-opens 8` | PASS: 8 opens,38 warnings,0 other DRC errors,ERC0,parity0,58 cold files identical | `native/RESULT.json`, `native/drc.json`, `native/erc.json`, `native/net-identity.json`, `native.log` |
| Exact remote plane-loss screen | `tools/run_kicad9.sh python3 $H/outside_loss_allholes.py` | FAIL: 9 outside-loss contours per inner plane,0.0476034500035mm2 per plane | `qa/outside-loss-allholes.json`, `outside-loss.log` |
| Rational non-boundary witnesses | `tools/run_kicad9.sh python3 $H/rational_loss_strict.py` | FAIL: source copper true/candidate copper false, neither boundary, both planes | `qa/rational-loss-strict.json`, `rational-loss.log` |
| Source local boundary scope and decision | `python3 $H/record.py` | Exactly two external source contacts: U13.13 and original GPIO10 via; candidate accepted=false | `qa/source-chain.json`, `DECISION.json` |

The plane-loss check subtracts 455000nm disks around only the three new vias (250000nm radius +200000nm plane clearance +5000nm polygon error), then subtracts actual source drill holes. The exact rational witness `(591575297/4,165675501/4)`nm, approximately `(147.89382425,41.41887525)`mm, establishes remote copper loss on both In1.Cu and In2.Cu without a numerical tolerance.

No original vias move. The local source contact analysis reads the parent's freshly recomputed source material graph, verifies its board SHA against the actual source file, and enumerates all direct edges of the six removed tracks. It is only source scope evidence. Full candidate material graph, named-pad partitions, retained-contact and new-reference gates were deliberately not run after the decisive exact plane failure; none are claimed passing. No tracked CAD or historical artifacts were edited. Candidate is not selected or manufacturing-ready.
