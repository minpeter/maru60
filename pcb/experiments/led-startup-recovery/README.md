# LED startup recovery integration packet

Status: independently reviewed, source-bound development candidate with production LED qualification OFF. This is not the lost historical working packet and is not an ARM build or hardware release.

## Documentation-only clarification after review

The primary candidate README now states precisely that observed /FAULT LOW and transport-not-ready while non-OFF latch across USB reconfiguration, while unexpected EN readback LOW cancels without latching and permits a later fresh settling epoch. The original independent fixture explicitly tests EN-loss restart. Only that README sentence and its manifest entry changed after review. evidence/documentation-clarification retains the previous README, reviewed manifest, exact diff and equality receipt. The original independent verdict binds unchanged code/test bytes and its original manifest; it is not relabeled as a new review of the documentation seal.

## Exact recovery versus new code

The immutable baseline contains 22 keyboard-overlay files with complete hashes matching the retained historical baseline. The new candidate matches 19 of the former active overlay's 22 complete hashes: 18 unchanged files plus exactly reconstructed config.h. maru_rgb.c, maru_rgb.h and maru_ws2812_transport.inc are NEW implementations. The old Git objects, original 72-file working packet, old startup/independent fixtures, and full 362-file verifier were not recovered. NEW-startup-guard.patch is this new implementation's delta, not the original lost patch.

candidate/source-manifest.json current SHA-256: 4ecbf22170617f42fccefb1ca5cbda496cb864d829965b0fcc80f241e72cefa0. Original independent-review manifest: ab7f168c0f973c5d9447ec305a3973f1b418467af5fa7018c93a26f58b46d500. The complete 62-file candidate differs only in the single README clarification and manifest entry; all code, tests and wrappers are unchanged. All raw current evidence is outside it. The candidate README's preparation-time static-map gap is superseded only by the later bounded check below, not by a full recovered verifier.

## Integration map

Copy this entire packet under pcb/experiments/led-startup-recovery, preserving paths. For primary host replay, only candidate/ (all 62 files), known-source-hashes.json and baseline-extracted/accepted-main/pcb/firmware/qmk/keyboards/maru60/rp2350/ (all 22 files) are required. No downloads, helper scripts, old Git objects or binaries are needed. Python 3 and a host C compiler are required; independent lifecycle replay also requires compiler UBSan support.

Parent's active adoption plan is byte-identical copies of candidate/firmware to pcb/firmware and candidate/engineering to pcb/engineering. Do not merge stale files into these directories. Hash-check their exact file sets against the sealed candidate. INTEGRATION-MAP.json lists every payload file and every active-copy file with destination and SHA-256. This packet does not edit the selected repository or establish an external build/deployment target itself. The new startup fixture and main replay wrapper remain in the candidate root, not in pcb/firmware/tests.

The immutable baseline is the rollback/reference source, not the current fixed development overlay. For future builds explicitly choose the active copy or the sealed candidate as documented in candidate/BUILDING.md; neither folder creation nor host tests change a deployed device.

## Reproduction

From this packet's directory:

    python3 candidate/verify_sources.py
    python3 candidate/run_host_checks.py --output /tmp/led-host-fresh-output
    python3 replay_all.py --output /tmp/led-complete-fresh-output

Outputs must be fresh, outside this packet. replay_all.py runs the unchanged reviewed main wrapper, copies the unchanged independent fixture and candidate into its expected sibling layout in the output directory, runs 73 lifecycle tests, and runs the later bounded current-V7 static check. It does not use existing binaries or mutate sealed sources. verify_package.py checks the exact packaged file set/hashes and candidate seal; optional --active-root <repo>/pcb compares active firmware and engineering byte-for-byte.

## Fresh results and comparison

90 startup and 288 transport executions passed across O0/O2; seven invalid compile contracts were rejected and seven targeted code mutations killed. Two expected fault-at-submit assertion failures deliberately demonstrate the non-atomic polling gap. Independent actual maru_rgb.c + maru60.c wrapper tests passed 73 executions under UBSan using synthetic 1/7/2147483647 ms intervals.

A new common mock fixture reproduces the exact baseline's hypothetical qualification-1 problem: fault injected during its blocking wait leaves four post-cancellation flush callbacks, while USB loss injected during that wait leaves two callbacks after EN went low. Corresponding new settling-cancellation cases issue zero unauthorized callbacks. The baseline fault case leaves EN high in that fixture; do not conflate it with the USB case. Both baseline and candidate production qualification-0 cases produce zero EN epochs, callbacks and mock DMA. Scheduling and 7 ms are synthetic test inputs, not observed rail timing or physical measurements. These fresh observations are not recovered historical receipts.

The later static check passes 24 ROW/COL/LED GPIO net and MCU-pad bindings against current-V7 XML SHA-256 1b46d899330d9aba0b86380ab08b7a60d309fa7a1c8962b9e6fab3ad556f2d29. GP20=KEY_RGB, GP21=UNDERGLOW, GP22=LED_ENABLE, GP23=LED_FAULT_N. Both 60-key variants pass all one-, two- and three-key subsets (60,1770,34220 each) plus all/none; three pin/net mutations and reversed-diode controls are detected. It is a new schematic/ideal-matrix check, not PCB continuity, all2^60 combinations, physical hardware or the lost362-file verifier. An initial checker-only assumption missed GPIO29_ADC3/28_ADC2 suffixes; its failed log is retained and the corrected parser was rerun.

## Evidence and remaining gates

- evidence/author-final-run: final source-bound author receipts and text logs, no binaries.
- evidence/independent-review: sealed verdict, actual fixture/mocks and current/earlier referenced receipts. The review's initial fixture-only false alarm is disclosed and retained where present.
- evidence/static-v7: later check source, bound XML snapshot, current results and parser-development log.
- evidence/arm-prerequisites.json: fresh runtime inspection, no ARM compile attempted. The historical prerequisite receipt itself is missing; its known hash is not a recovery claim.

Full pinned QMK/ARM builds for WKL via and HHKB via_hhkb remain required. No full transport-TU/PIO integration, real QMK callback/IRQ ordering, waveform, USB host, physical LED rail/current/inrush/settling/suspend qualification, official VIA reader validation or flashing was performed. EN and /FAULT are not rail power-good. Polling cannot guarantee instantaneous fault-to-DMA cancellation. No production settle interval is supplied. Keep MARU60_LED_POWER_QUALIFIED=0.
