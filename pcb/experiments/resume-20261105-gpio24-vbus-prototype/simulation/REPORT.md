# MARU60 bounded power replay, 2026-11-05

## Fresh outcome

All 14 saved passive/explicitly behavioral decks completed using the already installed ngspice 44.2 shared library and the recovered, inspected ctypes runner. No program installation, external fetching, credential change, CAD modification or vendor-equation alteration occurred. Every waveform reached its requested final time, was finite, passed fatal-log checks, and matched the saved waveform numerically exactly (maximum absolute difference 0 at saved decimal precision). RC analytic maximum error was 3.03512 µV. Six capacitor cases passed independent finite-ramp endpoint checks, and all four behavioral hysteresis transitions agreed with their resistor/threshold equations within 2 mV.

This is a fresh solve of frozen saved models, NOT a fresh circuit extraction or full stability/production qualification.

## Source binding

Library identities and version 0 bindings are in library-identities.json. archive-hashes.json binds all three supplied ZIPs. All 109 members in the power archive's manifest were hash-checked without a mismatch. RESULTS.json binds each replayed deck, runner, runtime library and output waveform. The installed shared library SHA-256 matches the historical report: 8b24e526865425243ee57efa9dcbdde99e7220393eb77a1ab863e849a2e0d761.

The frozen decks refer to historical board 3663aac96fb305eb4925fff938dd2db5862b880c6c262b2fa82707567a6e98f7. The selected current PCB was independently hashed as 04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99. These identities are different: equivalence of all relevant source parameters/connectivity cannot be claimed from waveform reproduction alone. Parent task reports unchanged power/lighting/schematic parts with only EXT_GPIO26 routing changed. This replay does not verify that broader equivalence assertion and does not reuse old geometry validation as current-board validation.

## Useful bounded results

- A 200 mA load increment with regulator current artificially fixed for 50 µs gives 4 V output endpoints of 2.7461 V / 3.5794 V / 3.7687 V for 8 / 24 / 44 µF. Opposite steps give 5.2539 V / 4.4206 V / 4.2313 V. ESR is assumed 20 mΩ; the finite 10 ns stimulus ramp is accounted for. These demonstrate charge sensitivity, not actual regulator settling, overshoot, or physical capacitor values.
- The idealized eFuse hysteresis switches at input 3.9866 V up, 5.7390 V up, 5.2120 V down and 3.6208 V down. It explicitly excludes slew, delay, current limit, temperature, tolerance and active reset behavior. This retains a potential brownout/headroom concern; it does not demonstrate a real observed fault.
- Abrupt 5 V / 100 ns protected-feed recovery peaks span 4.9463–6.9480 V across assumed 2/4.7 µF and 0.1/0.5/1 µH cases. Assumed series R is 0.358287 Ω, ESR 20 mΩ and load 33 Ω. This is deliberately NOT normal eFuse slew-limited startup, measured ringing, or ESD validation.

## Active-model blocker, freshly reproduced

Both unmodified saved active startup wrappers were attempted with their original vendor libraries using the existing runtime. Both exited unsuccessfully with no waveform:

- TPS2553-1: MIF-ERROR unable to find definition of model xu7.x_u1_s14:a_u1_s14; circuit not parsed.
- TPS62932: MIF-ERROR unable to find definition of model xu18.x_u10_u9:as1; circuit not parsed.

Logs are in active-probes/. No installed .cm code-model modules were found under /usr/lib. The saved authorized-retry archive explicitly excludes the original modules/binaries. No installation/fetch was attempted under this task's constraints. These are execution/model-availability failures, not access denials and not evidence of hardware faults. ngSpice_Command returns zero even on these errors; the missing waveform and fatal text correctly reject the runs.

Restoring modules alone would not establish validity: the historical retry report records wrong U7 XNOR truth tables in ps/psa/ltpsa, failed buck regulation in the exploratory 5 V harness, and an aborted self-authored 24 V diagnostic. These historical findings were read, not freshly rerun here. The eFuse library remains encrypted; no decryption was attempted. A complete official generated nominal bench is absent. No active loop-stability, startup, fault, brownout, pulsed-load, reset, or off-state injection qualification is available.

## Unresolved coverage

U5/U6 powered-off input injection and grounded-OE behavior are not represented. C128/C129 generic part values have no adopted MPN, DC-bias/aging model. R120 candidate TCR/MPN adoption and input supply/current assumptions remain unresolved. The saved advanced USB packet was inspected for coverage: its field/channel work is based on assumed fab geometry/materials and historical copper hashes, without an actual MCU IBIS model or USB certification. It was not rerun or rebound to the selected copper in this power task.

No component values were changed merely to make these artificial waveforms look better. A compatible supported active-model simulator with a complete official bench, confirmed part models/input assumptions, and physical measurement are still required to make the missing claims.

## Reproduce

Run `/usr/bin/python3 replay.py` from this directory. Each circuit runs in its own process; results go to separate runs/ directories, never over the recovered evidence. The script asserts full endpoint and finite data and checks relevant analytic controls. Input archives remain unchanged.

## Current-source reconciliation supplement

APPLICABILITY.md supersedes the source-equivalence uncertainty for its explicitly checked component values and pin-net assignments only. current-source-crosscheck.json binds the fresh schematic/netlist/native-board checks. capacitor-inventory.json exhaustively lists capacitor references directly attached to five relevant power nets, with both terminal nets and grounded/between-net classification. None of the fourteen complete decks qualifies as a direct current-board model; see the individual classifications and omissions in the supplement.
