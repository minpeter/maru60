# GND dead-branch trial: eligible for bounded adoption

This frozen packet records independent pre-adoption verification, not hardware qualification. Source: aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f. Actual candidate: c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a. The parent will record selection and the recovery commit separately after this evidence is preserved.

Exactly two unused F.Cu GND segments retire:68f95f8e-16e1-430a-a0b2-1c1d51d16fde (0.10 mm) and577f36c1-4f15-4c40-b632-02db2931cfb0 (1.838477631 mm), both0.25 mm wide. Existing GND via277a8b55 at(132.1,76.05), diameter0.5/drill0.25 mm, stays unchanged. A one-track deletion would merely expose the next dangling track and is not the constructed scope.

## Verified actual result

- All retained raw objects, all12 serialized zone records, all1,269 physical drills, every rule/stackup/net/component and all53 non-PCB project companions are byte-identical to the selected source. Exactly the two named tracks disappear. Source/prefill/filled54-file project trees are separate.
- Strict saved-plane preservation passes outright with zero difference. No epsilon, coordinate-tolerance condition, endpoint mask or BUCK exception is used.
- Fresh corrected R2 exporter preserves14,685 retained material nodes in382 components, all245 pad-net partitions, all247 original J1.A1 ground-return paths,934 barrel proofs, and every retained material/zone contact witness. All51 existing guard failures remain explicit and unchanged.
- The retained via has an intact plated barrel and unchanged positive annular contact to both inner GND planes. Each guarded overlap is0.1472558792225 mm². It has no independent external F.Cu/B.Cu contact; the two inner-plane contacts retain it as connected ground copper.
- Native DRC:66 warnings,12 inherited expansion opens,zero other hard violations andzero schematic-parity findings. ERC:zero violations. Only the68f95f8e dangling-track warning disappears; none is added. All12 full raw open records and semantic component pairs match source.
- Inventory:9,750 tracks,918 vias,382 footprints,13,176.816253756544 mm total track length.
- Normal independent cold refill of a separate copied project reproduces c770 byte-for-byte in2.01 s. Source and candidate remain unchanged after review.

Independent final eligibility is at `independent-review/actual-candidate-review/ELIGIBILITY.json`, SHA262450e261c621c1dfedef8a0f460859ab7db032ecdc043eae2895ee1eb18f43. All original return paths and the exact retirement contract are included. The active checker is exact R2 SHA57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9.

## Scope and limits

This is removal of a proved nominal-connectivity leaf, not an assertion of better high-frequency ground, noise, PDN, SI, EMC, thermal, stability, assembly or hardware behavior. Existing source architecture and power/firmware/expansion limitations remain. The physical F.Cu ground foil is intentionally reduced; no general physical-return invariance is claimed. Inner reference copper, drills, active return connectivity and retained contacts are exact under the declared model. The board still has12 opens and66 warnings and is not ready for fabrication on this evidence alone.

No C124 circuit, component/BOM change, J3 closure, model port, firmware change or clearance/rule reduction is included. LED qualification remainsOFF. Historical lost Git and old full QA are not reconstructed. No push, fabrication or flashing occurred.

The manifest binds every included byte. Original scripts retain their execution paths and private standard XDG homes were used for native work. This is a source-bound frozen experiment, not a universal validation harness or relocated one-command replay guarantee. The independent eligibility requires preservation before adoption; the later repository adoption receipt governs selected status.
