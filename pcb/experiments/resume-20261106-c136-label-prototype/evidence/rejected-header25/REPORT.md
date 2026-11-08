# Header continuation: failed finite attempt, paused

**Decision: REJECTED at the first native DRC gate. No new closure or selection. Further header variants are paused for this round.**

## Immutable provenance

- Verified source: `/workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb`
- Source SHA256: `9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed`.
- Saved rejected geometry experiment: `rejected/isolate-refactor/pcb/maru60.kicad_pcb`.
- Rejected SHA256: `a60175d59abb204a050c008d229e0a968f33604383134912f1c812cab7f07a68`.
- Source hash was rechecked unchanged. All57 companion files are exact. No selected repository or frozen source was modified.

## Saved experiment and first-gate result

The experiment replaces49 short B.Cu GPIO_ISOLATE segments between(108.1,35.05) and(109.3,41.5) with4 segments through(109.6,35.05),(109.6,40.0),(109.3,40.3), intending to open an under-package escape for U11.15 GPIO25. This saved board contains only that geometry refactor, not a completed GPIO25 route. All4 replacement tracks remain0.15mm wide; no rule or layer change. Every retained object and every filled zone is exactly unchanged in parsed raw data.

Native KiCad DRC: **9 opens,42 unchanged warnings,5 added hard errors,parity0**. Exact warning records are identical to the source, including inherited dangling-track warnings; there is no new dangling warning. The five new hard errors are:

1. The new horizontal GPIO_ISOLATE segment from(108.1,35.05) to(109.6,35.05) shorts GPIO3_ISO through-via `00b76649-ed82-4e2e-a708-dc3f517fd018` at(109.7,35.25).
2. The same segment has0.0621mm clearance to GPIO3_ISO B.Cu track `7b5e9124-9875-4909-ba8e-4aa4176aca03`, below the required0.1500mm.
3. The same segment crosses COL5 B.Cu track `1a0b9af6-88ec-455f-ba43-9d292abfa567`.
4. The new GPIO_ISOLATE vertical segment at x109.6, y35.05→40.0 also shorts that GPIO3_ISO via.
5. That vertical segment also crosses the same COL5 track.

These failures reject the proposed corridor. They do not prove that all other possible routes are impossible. A revised design would have to remain on the original side of COL5 and avoid the GPIO3_ISO via, or explicitly redesign additional conductors with new complete checks. No such additional variant was started after rejection.

## Finite screens before the saved trial

All searches used native copper shapes on outer signal layers,0.15mm track width,0.50/0.25mm through-via geometry and conservative screening for existing signal-via plane clearances. They are route-planning diagnostics, not DRC or return-path acceptance.

- Untouched source: J3 GPIO25 can escape to(93.925,40.175). U11.15 has no screened through-via site in its reachable B.Cu pocket; its path is bounded by GPIO_ISOLATE on B.Cu and GPIO25_ISO/ROW1 on F.Cu. Expanding the search beneath the U11 body did not produce an unchanged-copper escape.
- U13 GPIO24/25: unchanged-copper fanout screens fail. A separate in-memory GPIO10 barrier shift opens part of the B.Cu pocket, but proposed GPIO24 via(88.8,42.0) intersects existing COL13 F.Cu track `a19f0dbf-babd-46e0-b269-9c02b78fb0f0`. This variant was never saved or accepted.
- The GPIO_ISOLATE detour permits a tentative U11.15 dogbone to(108.3,37.7), but the J3 F.Cu reachable region is separated from it. The upper J3 escape also fails the finite via screen. These planned new GPIO25 tracks/vias were not saved.
- An untouched-source second-transition screen finds a possible bridge-via site near(98.15,40.6), but its B.Cu reachable region ends near x101.425 and does not reach U11.15. No route or via was saved from that screen.

## Validation deliberately not claimed

After the native hard-error rejection, no expensive material graph, complete return-plane comparison, cold-refill certification, ERC rerun or SI/stability validation was performed on this failed layout. Its unchanged filled zones do not by themselves prove reference integrity or safe signal behavior. There is no new validated count reduction. The verified source remains9 opens/42 warnings for this routing round; the separately reviewed C136 text-only cleanup is outside this packet.

## Correction retained from prior round

The old REPORT27 incorrectly summarized all affected return rows as zero, while its JSON contained0.0003496908615mm² on55e5 near its unchanged source via. That defect was independently caught, and held ad2f/b1e3 must not be used as a base. This work starts only from corrected, independently verified9d7874. `CORRECTION.md` records the error and the requirement to assert both area and contour count for every new/affected reference row before any future pass statement.

## Evidence

- `qa/NATIVE_GATE.json`: exact hard-error records, warning-record equality, source preservation and rejection.
- `qa/isolate-refactor-build.json`: all49 removed and4 added UUIDs, coordinates and hashes.
- `qa/isolate-refactor-drc.json` and `.log`: complete native severity/open/parity output.
- `qa/raw-scope.json`: retained raw objects, all zone fills, net and rule identity.
- `qa/fanout-screen.json`, `route25-plan.json`, `route24-refactor-plan.json`, `route25-refactor-plan.json`, `route25-upper-plan.json`, `bridge25-attempts.json`: finite planning attempts.
- `scripts/`: reproducible source-scoped geometry screens and native save/raw-check helpers. One preliminary SWIG lifetime error occurred in memory, before any save; its log is preserved. Keeping removed native objects alive corrected that script issue. The saved board was parsed successfully by native DRC.
- `images/rejected-full-native.svg/png`: native same-snapshot whole-board view of the rejected geometry, not a selected board.
- `FROZEN_EVIDENCE.json`: exact packet hashes.
