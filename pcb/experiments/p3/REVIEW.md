# P3 merged source stage — 78 intentionally open, not A-series progress

**No main/A-series adoption, prototype/current/PI/SI or assembled-fit approval.** Exact terminal three-via +3V3 source repair is combined with the two frozen unchanged-pose C105 arms. No TP5 move, AVDD patch or A25 KEY16 route is included.

PCB SHA256 `3ff913a8351d6c284bc67a40b39a99391a7c761d239f895827d6874647e60680`.
Native all-severity/all-track **78 unconnected items /0 hard /119 warnings /parity0/ERC0**. Cold refill/save is byte-identical. All10,341 intended pad/track/via/zone semantic net names pass load/build/refill/save/reload. All340 footprint/1,275 physical-pad/924 numbered identities and all27 simultaneous local controls are preserved. Exactly two C105 tracks are added to the terminal bridge, with all9,051 source copper objects,13zone definitions and project bytes exact.

## What actually closed
- All215 GND physical pads are source-reached.
- Nine of ten+1V1 pads are source-reached, including C103/L1 output, U1.50 feedback and DVDD6/23/39 with C108/C109/C110. TP5.1 is the sole populated unreached1V1 endpoint. There is also one separate **padless** old test-branch component, so the witness reports two unreached components; that is not two loaded endpoints.
- The previously rejected four+3V3 losses at C102.1/U1.49/U1.30/U1.38 are restored. All other previously reached source endpoints remain reached. C105 has explicit positive-to-U3.8 and ground-to-existing-via arms, without a new hole or part move.
- U1.48→L1.2 LX and the restored input/output/feedback/ground topology do **not** fully qualify the regulator: R104/C104/U1.46 AVDD filter is still disconnected, selected-capacitance/ESR and current/loop behavior remain open.

## Reference and return evidence
All7,958 retained outer tracks have zero additional left/center/right reference-loss intervals. Comparator was rerun without unsafe Unfracture; the attached scoped addendum independently reproduces all five prior P3 stage comparisons. All saved fill geometry is unchanged by this two-track composition.

Fresh new-route audits against this exact PCB show: C105 positive arm has zero raw full-width gaps; new1V1 feeds have zero gaps outside explicitly categorized own-via neighborhoods; new3V3 feeds retain one **0.509167mm edge-only** VIN-launch interval over the unchanged LX inner keepout. Its centerline/other edge remain referenced. The .20mm track's west edge x23.8 intrudes at most .05mm; pin49's existing copper already extends .065mm into that keepout. This is not a plane-wide centerline split, nor a blanket return waiver.

Nearest real source-GND transfers for the three new3V3 vias are .763409/.670820/1.528275mm, including the actual plated EP pad where applicable. The C1081V1 transition's nearest source-GND transfer is a real U1 EP plated pad at1.300000mm. Source membership is proven on both inner planes; these distances are not complete return loops or impedance/EMI qualification. Source tap→U1.49 and→U1.38 positive feeds are5.951352/11.534172mm with two vias each, not loop lengths. C105's two external arms sum4.675600mm and its via-to-via return chord13.602007mm remains a documented bypass tradeoff.

## Remaining finite gates
Native warnings are107 dangling tracks,10 dangling vias and2silk-over-copper; unfed1V1 island and old thinGND neck warnings are gone. +3V3 still has11unreached source components, +5V has two components/three physical endpoints, AVDD two endpoints; BOOT/QSPI and loaded source interfaces remain explicit. LED5V's160 downstream pads being connected does not power U7 while its upstream+5V is open.

Read-only signal inventory is exactly retained:42 split populated non-power nets —22matrix,6QSPI,4USB,10control/RGB/service. Eleven padless non-power components contain40copper objects; this is NOT permission to delete them or a native open-count equivalence. Source restoration precedes broad external routing. TP5 output-side and AVDD quiet-return proposals remain separate pending native/source/reference/mechanical/tool contracts.

Accepted main80681cd3, original b9, all frozen P3 fallbacks and the current A-series branch remain unchanged. Full PCB completion and actual parts/process/assembly/firmware/current/SI gates remain open.
