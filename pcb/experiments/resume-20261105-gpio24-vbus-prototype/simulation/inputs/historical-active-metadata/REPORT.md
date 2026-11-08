# Official ngspice code-model retry: execution improved, active validation rejected

2026-11-04 UTC. This is a runtime capability investigation, not a hardware qualification or a reason to change PCB/BOM values. No vendor equation or CAD file was edited. The prior no-install failure packet remains unchanged.

## Outcome

- **Installation passed.** The official Debian `ngspice 44.2+ds-1` package matches the existing 44.2 shared library. Its six code-model modules were extracted into this task folder, SHA-256 checked and loaded. No global install, system configuration, account or license change was made.
- **U7/TPS2553-1: parsing and transient execution now work, but logic semantics fail.** The unchanged XNOR primitive yields the wrong table in `ps`, `psa` and `ltpsa`. This rejects startup, enable, protection and current-limit conclusions from this runtime.
- **TPS62932: execution is possible, but regulation/nominal validation has not passed.** The old 5 V exploratory harness runs to 30 ms but does not regulate and has convergence-recovery warnings. A separate self-authored 24 V diagnostic aborts at 1.510645238 ms of the requested 6 ms.
- **TPS25947x/eFuse: still encrypted.** Its `**$ENCRYPTED_LIB` source was identified and preserved, not decrypted or executed. C124 active startup/reset behavior remains unverified.

## U7 semantic rejection, not a demonstrated TI model defect

The wrapper uses the original library, with A/B at 0 or 1 V and the original defaults VDD=1 V, VSS=0 V, VTHRESH=0.5 V. Output order is y00, y01, y10, y11. Expected XNOR: **1,0,0,1**. Observed in all three modes: **1,1,1,0**. These are one-row DC operating-point tests, not an inference from a transient plot.

This primitive is used by the actual model: original library lines 79–80 instantiate X_U1_U826 to produce U1_ENOK; lines 100 and 183 fix the polarity input EN_P=1; lines 141–142 provide the EN comparator; lines 148–149 feed ENOK into POWEROK. Internal probes reproduce the consequence: EN=0 gives ENOK≈1, then EN=3.3 V gives ENOK≈0. The diagnostic output starts near 3.997 V while disabled and falls toward 8.506 mV by 10 ms after enable. These voltages show the rejected simulation's behavior, **not a prediction for the physical part**.

The result demonstrates incompatibility of the current execution semantics with this unchanged PSpice model. It does not prove a defect in TI's intended PSpice simulation. Read-only `listing e` inspection shows that all three compatibility modes retain literal `^` in the expanded B-source expression; ngspice documents that operator as exponentiation. This supports an operator-translation incompatibility, while the truth table is the direct semantic evidence. The exact parser precedence mechanism was not separately reverse-engineered. The original expression at lines 361–362 is `{{IF(V(A) > {VTHRESH} ^ V(B) > {VTHRESH},{VSS},{VDD})}}`. No replacement operator, parentheses, equations or patched library were introduced. Independent review and hashes are in `inputs/independent-review/`.

## Buck diagnostics and exact failure

The recovered 5 V harness is self-authored project evidence, not TI's generated nominal bench. It uses the board-parameter 4 V feedback target, 4.7 µH, 44 µF output capacitance, 100 nF soft-start and 40 Ω load. It completes 304,545 rows through 30 ms, with Vout maximum 7.6186 mV and final 19.9841 µV. It reports singular-matrix, dynamic/true gmin and source-stepping failures before subsequent transient execution. Its 5 V input is below the package's reported 6–30 V corner-test range; that range is **not** asserted to be the physical device's operating limit. This run cannot identify a board fault.

The new `buck-diagnostic-24v.cir` is explicitly **self-authored**, not a recovered official bench. Chosen assumptions: 24 V input ramp in 1 µs, 50 mΩ feed, 10 µF input, EN pull-up 10 kΩ, RT 49.9 kΩ, 10 µH/49.9 mΩ output inductor, 44 µF ideal output capacitor, 33 nF SS, 52.5 kΩ/10 kΩ feedback and 2.5 Ω load. It requests 6 ms with a 20 ns maximum step. It aborts after 227,070 partial rows:

`Timestep too small; time = 0.00151065, timestep = 1.57022e-20: trouble with node "e.xu18.x_u10_u859.e_abm7#branch"`

A partial waveform and `COMMAND_RETURN run: 0` both remain despite `run simulation(s) aborted`. Neither was counted as success. The first runner also returned shell code 0 because its initial fatal-log filter missed this message. That reporting defect was corrected in the reusable runner; the original runner, logs and partial data are retained, and `summarize.py` independently asserts the abort and missing requested end time. No simulated overshoot/current from this incomplete case is treated as a hardware limit or finding.

## Controls and unresolved model coverage

- XSPICE VSWITCH synthetic endpoints match the 1 GΩ/1 Ω, 1 kΩ-load expected results: approximately 0.999999 µV off and 0.999001 V on.
- Forty static outputs from the unchanged buck gate/comparator/MUX definitions pass in both `ps` and `psa`. Dynamic latches, hysteresis, timing and startup are not covered by that pass.
- A top-level synthetic LIMIT control clamps both bound orders correctly in `psa`. Its failed `ps` attempt is retained as a wrapper-mode mismatch: `ps` translates included files, whereas `psa` also translates the top-level netlist. It does not establish a LIMIT defect within the translated vendor library.
- The initialization-file warning is retained. Code models were loaded explicitly; module-load success alone is not validation.

The official archives contain binary OrCAD DSN designs and simulation profiles but no generated readable nominal `.net`/`.cir`. DSN notes establish 24 V input, 5 V output, 2 A and a 5.5 ms/20 ns startup profile, not complete component/net/stimulus/IC assignments. Available embedded reference plots are historical vendor references, not local results. An EVM or guessed circuit is not a substitute for that missing identity. No official nominal benchmark has been reproduced.

The bounded route stops here: no further equation alterations or solver tuning to force a plausible curve. A compatible supported simulator with the complete official design/bench is needed before active-model conclusions. Prior source-bound passive C124/C128 sensitivity results remain separate; they do not gain active-model or hardware qualification from this installation. Selected CAD and experimental-candidate acceptance status are unchanged.

## Reproduction and source identity

`RESULTS.json` records raw extrema, end times, warnings and rejection flags. `runtime-diagnostics.png` is visibly labeled as rejected runtime diagnostics. Full numerical files are preserved; plotting uses display decimation, not a peak guarantee.

Run `python summarize.py` to recheck the stored evidence. `reproduce.py --vendor-root <original vendor folder> --code-model-dir <verified .cm folder> --out <new folder>` repeats the fast controls, with `--full` to add the known-unvalidated transients. It performs no download/install and verifies all original model, module and runtime hashes. Only wrapper include paths are rebound; vendor files are never rewritten. The original package/runtime binaries and TI model libraries are deliberately not redistributed in this evidence ZIP.

Official package: [Debian download and SHA-256](https://packages.debian.org/trixie/amd64/ngspice/download), [module file list](https://packages.debian.org/trixie/amd64/ngspice/filelist). Downloaded package SHA-256: `4d76721dd91416055b1088cfc58626d4db47b91afda7c73258c0968ba6e4d24e`, 4,226,888 bytes. Existing libngspice SHA-256: `8b24e526865425243ee57efa9dcbdde99e7220393eb77a1ab863e849a2e0d761`. Exact module/library/archive identities are in `installation.json` and `inputs/source-runtime-identity.json`; all three libraries remain byte-identical to their original ZIP members.

Primary references: [ngspice 44 manual, behavioral expressions and compatibility modes](https://ngspice.sourceforge.io/docs/ngspice-44-manual.pdf); [TI TPS62932 model](https://www.ti.com/lit/zip/SLUM808), [TI TPS2553-1 model](https://www.ti.com/lit/zip/SLVM426), [TI TPS25947x model](https://www.ti.com/lit/zip/SLVMDJ6). No new license agreement was accepted.

## Separate, unimplemented compatibility-port idea

If separately authorized and reviewed, nested conditionals could explicitly encode the strict-threshold XNOR function: IF(A>threshold, IF(B>threshold,VDD,VSS), IF(B>threshold,VSS,VDD)). This is only a mathematical proposal, not an implemented port, not original TI-model evidence, and not hardware qualification. Boundary voltages, altered VDD/VSS/threshold parameters and dynamic behavior would need independent tests. It is not part of the completed original-model verdict.
