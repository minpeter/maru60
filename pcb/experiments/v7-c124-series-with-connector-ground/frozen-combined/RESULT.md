# Combined C124 D + connector GND: source-bound experimental checkpoint

**Construction-side combined checks PASS.** This tree is an isolated candidate; it does not edit or select the repository entrypoint. Independent cross-review is recorded separately. Any working selection is experimental only, with all hardware/assembly/active-startup/SI qualifications still false.

## Exact source and result

- Source D: `f987edb49e7eb99e6db711ea428a5efb66a36653fe9dce77b02aae12f281441b`.
- Prefill: `a6303c45fc3df52e519753022ff3d8f1e731696d4fb45fee7ff199432da9dd95`.
- Normal-filled combined PCB: **`7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401`**, `filled/pcb/maru60.kicad_pcb`.
- Only added object: ordinary GND via `cda2df4b-6411-5409-a933-5106751244d8`, (17.20,9.90), diameter .50 mm, drill .25 mm, F.Cu through B.Cu. GND net code 83 was verified from actual D and native load, not blindly inherited.
- The via's independently reviewed contract is `c58baac31c087ddd115fb5ccbe7953ced52d8469c0efe675b2184ea00ff7d7a5`; its separate aaaf eligibility is `27c41ca26cfa052bbb2f7c983152d285c584299d8dff5f40d4a3fced05d58d69`.

All 10,668 old D track/via records, all old footprints/nets/settings/edges, all twelve serialized zones and all 57 companion files are byte-exact. The two earlier remote GND deletions and BUCK cleanup remain absent. No D/C124 module, part, pose, route, label, land, mask or paste setting changes. Source/prefill/filled are separate complete 58-file trees.

## Actual verification

- **9,750 tracks / 919 vias / 383 footprints / 13,185.28691027245 mm**; normal refill completed in 2.334831027 seconds.
- **0 hard DRC / 64 warnings / 12 opens / ERC 0 / parity 0**. Every warning and open entry is exactly D's entry. Three native support-end warnings remain on `cc1282fe…`, `f58bc791…` and `d4be2091…`; no new warning is introduced and none is suppressed.
- Fresh XML components, library parts and nets are exactly D. Thus the actual U8.7 → R125 100 Ω → C124 10 nF → rooted GND circuit and divider logical values remain unchanged.
- One corrected R2 export only, checker SHA `57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9`. Actual graph SHA **`304954c5b4195c28bcea68ef950625584efd557fd3475430c1245c0078ff877c`**. All old named-pad partitions, direct contacts, retained material-edge witnesses and barrel proofs remain exact; all 247 GND pads and the new via share the intended J1.A1 root. The 51 pre-existing material guard failures remain unchanged.
- Exactly four new via-layer material nodes, one proved intact through barrel and **two** new inner-GND-zone contacts. Each contact is .147260768066 mm², or .1472558792225 mm² after the inward 2 nm guard. There is no new old-object or outer-zone contact, no foreign merge and no resistor bypass.
- Physical copper, with every actual through drill subtracted, loses exactly the new native drill polygon: **.049087681002 mm² on each inner GND plane**. The expected-versus-actual native Boolean XOR is zero. All outer/non-GND zone material is unchanged. Raw zone equality alone is not used to hide this actual drill loss.
- Every one of **13,131 D outer-shape shadows** is disjoint from that loss. All **37 D added/changed shapes**, including ground bridges and changed pads, remain disjoint even expanded 2 nm. With identical source objects and saved zones, all 14 D full boundary supports and 58 outward-reference witnesses remain intact. Earlier c770 and original a9 shadows, including the retired U10 D-minus segment, are separately rebound to this exact same drill polygon. No missing historical full-QA archive is claimed restored.
- Actual via-to-foreign-copper minimum is .225 mm. The six D component pad-to-new-via outer gaps are all at least 8.523078 mm. All original via and footprint holes remain unchanged; only the declared new through hole is added.

Key receipts: `qa/raw-native-comparison.json`, `qa/comparison.json`, `qa/actual_geometry.json`, and **`qa/FINAL_GEOMETRY_MATERIAL_BINDING.json`**. The last receipt closes earlier pending-R2 phase labels. The D component/BOM/land/envelope review remains valid through exact footprint/companion inheritance, not a new assembly approval.

## Preserved limits and provenance

No unchanged passive equation run was repeated. D's existing nominal/passive analysis does not extract actual combined-board parasitics or qualify startup, brownout, noise, R125 pulse/reset or hardware behavior. R121 RN73R long-term drift equivalence to TNPW is unproved; R120 MPN/TCR/thermal tracking remains unknown. C124's maximum occupied courtyard remains explicit and its .030 mm full-boundary margins remain unchanged. Assembly, stencil/reflow, mask registration, socket/plate/case and procurement qualification remain false.

The added GND via does not restore the connector merged-antipad neck. New grounded copper can change local USB fields/coupling despite unchanged signal objects. No SI/ESD/EMC/PDN improvement or compliance is claimed. Twelve existing opens and all native warnings remain on the board.

The normal-fill log retains a layerless `GetWidth()` diagnostic from the initial inventory assertion; the separate actual audit explicitly verifies .50 mm on all four layers and .25 mm drill. The initial pure constructor stopped before creating a candidate because it counted repeated pad-net declarations instead of distinct GND net codes; its original script is retained. The corrected constructor and native checks verify the actual unique net code. A premature material-comparison invocation before export completion is also retained; the completed comparison is separate. No failed candidate was substituted or silently discarded.

`qa/combined-unselected.png` is a same-snapshot native display of actual 7882 connector copper and C124 region. It is not a geometry proof. The image retains the pre-integration UNSELECTED label; routing owns any subsequent experimental working selection and its history.

## Completed independent cross-review

All **45 independent checks pass** in `/tmp/v7-c124-d-plus-connector-gnd-independent-review`. A separate normal cold refill is byte-identical to 7882, taking 3.405 seconds. Actual combined target B.Mask/B.Paste apertures are exact to D. The independent review retains all three native warnings and all process/electrical/SI/ESD limits.

- RESULT.md SHA: `d30ebf850a8e9a9af4cae1c86820e126128155771dd6df1d60620ec4d228d395`
- ELIGIBILITY.json SHA: `e55c7655cc410d0e8faffcc99f28820386e6a2892a80f984f61ae2cbb0b9ed6b`
- MANIFEST.json SHA: `330e5c4e2c5b1d75cc98c5f149147fa87733908a7d2ca89060a8962c2286fa1e`

This closes the combined cross-check, not the board's remaining opens or hardware qualification. Routing may record the separately authorized experimental working selection; this constructor did not write the repository.
