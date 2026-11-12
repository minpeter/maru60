# PR #20 automated review follow-ups

This merge is a development snapshot, not fabrication approval. The automated
check completed successfully, but the comments below have not all been triaged
or resolved. They are preserved rather than treating the check result as an
endorsement. Some comments may already be superseded by later commits.

Source: https://github.com/minpeter/maru60/pull/20

Before ordering, prioritize the Gerber job layer-index report, fabrication-rule
exemptions, part/library identity, and remaining stabilizer/socket fit checks.
MCU relocation near USB-C is separate future work and is not in this snapshot.

## 2026-11-12T03:32:14Z — COMMENTED

- P2: The inner copper entries use layer indices `L5` and `L7` on a 4-layer board, while B.Cu is `L4`. Inner layers should be `L2` and `L3`, so the fab's CAM may misread the layer order. This value is copied from `pcb/order`, so fix it there too or confirm the fab accepted it before.

- P3: The note says 0.0 mm of copper precedes R174, but the added UG_LED_5_SRC routing runs about 1.8 mm from LED67 pad 3 to R174 pad 1. Either correct the note to the measured length or move R174 next to the LED67 DOUT pad so the claim holds. The same templated note appears in R173.json and other resistor records.

- P3: The `Reference` property on F.SilkS is set to `hide yes`, so these capacitors get no visible reference designator on the silkscreen. The sibling `R_0402_1005Metric` footprint in this library keeps its reference visible. Remove the hide flag so the 194 capacitor designators can be read during bring-up and rework, or document why capacitors should be unlabeled.

- P3: The new `run_dfm_jlcpcb_drc.py` row does not say it needs `tools/run_kicad9.sh` (KiCad CLI), and the section intro does not cover it. `verify_gerbers.py` also needs its own gerbonara environment, which the row omits. Add the runner and environment to these rows so readers do not run them in the default venv.

- P2: This footprint is flagged as unselected and not assembly-qualified, but the new order BOM and CPL still include C124 for JLCPCB assembly. Either exclude C124 (DNP or remove it from the assembly BOM) until it is approved, or update the Status to match the order.

- P2: This footprint's Value and MPN fields describe the 156k KOA part, but the order BOM uses 154k YAGEO RT0402BRD07154KL. Update the Value, MPN, and Manufacturer fields to match the ordered part, or document why the library keeps the 156k KOA values.

- P3: `artifacts.sha256` and `artifact-sizes.txt` are opened in append mode, so rerunning the script into the same evidence directory keeps the stale entries next to the new ones. Truncate both files before the build loop, or write them with `>` once per run.

- P2: The build script generates hash entries with `/evidence/...` paths, but the committed manifest uses bare filenames, so a fresh host-side hash check cannot consume the generated manifest. Emit hashes from inside `/evidence`.

- P3: This evidence line cannot be reproduced from the packet. No script or REPRODUCE.md step writes `overlay-postbuild-diff.txt`, and the file records only an exit code, not the paths compared. Add the diff command to `build-layouts.sh` or REPRODUCE.md, and record the compared paths in the output.

- P3: The hash values match the current overlay files, but the manifest's `./` relative paths only verify from inside `pcb/firmware/qmk/keyboards/maru60/rp2350`. Running `sha256sum -c` from `qa/qmk-build` fails for all 22 entries. Use the repo-relative paths as the 2026-11-09 manifest does, or document the `cd` step in REPRODUCE.md.

- P3: This adds a second verification record beside the 2026-11-09 `verification` and `verification_evidence` keys, which are left unchanged. The top-level `verification` text still calls the 22-file overlay 'current' and unchanged, which the new config.h delta contradicts. Update the existing keys to the 2026-11-11 state, or rename the old ones as historical, so a reader can tell which record is current.

- P3: The documented `docker run` command does not pass `-u` with the host UID/GID, but `spice.py` does. Following the README leaves root-owned files in `build/si/out`. Add `-u "$(id -u):$(id -g)"` to match the runner.

- P3: The image is not pinned, so a rebuild can silently change the ngspice version and the SI results. Pin the base image by digest and pin the ngspice package version, or record the ngspice version in results.json so runs can be compared.

- P2: The note says "0.0 mm of copper before it", but the SRC routing from LED41 DOUT to R180 pad 1 is about 10.5 mm of track (the 8 `add_tracks` segments on KEY_RGB_CHAIN_42_SRC). The resistor is not at the source, so the series damping does not sit at the driver as the note says. Correct the note to the real length, or move R180 next to LED41 pad 3 and re-route the SRC net.

- P3: The library Value is hardcoded to the net name `+1V1 TEST`. This generic footprint is used for GND, VBUS, +4V, and other test points, so a new placement from this library gets the wrong label. Use a neutral value such as `TEST` and keep the net name on the placed instances.

- P3: The library footprint hardcodes `Value "100 1%"`. Each placed resistor already gets its value from the schematic, so this only leaks into new placements from `Maru60.pretty`. Set the footprint Value back to the generic footprint name, e.g. `R_0402_1005Metric`, and keep the 100 Ω value on the symbol.

- P3: This pin-1 dot duplicates the F.SilkS circle already in the `LED_SK6805_EC15_001_WindowPlusAltSite_LED54` footprint, at the same position and radius (-1.025, 1.025, r 0.12). Remove this op, or delete the file if it has no other content, so the silkscreen is not doubled.

- P3: The note says the 1.0 mm / 0.15 mm change covers only the added parts, but `set_ref_text` has no ref filter and applies to every visible silkscreen reference text on the board. Reword the note to match what the op does.

- P2: The `limitations` field does not mention the known 7U mismatch. The selected Design Studio 7U stabilizer does not match this PCB-mount 7U cutout, which is still unrevised. Add that caveat here so the machine-readable record matches the README.

- P2: The note says 0.0 mm of copper sits before R172, but the new UG_LED_10_SRC track from LED72 pad 3 to R172 pad 1 is about 2.3 mm long. Correct the note to the actual length, or move R172 next to LED72 DOUT if the damping intent requires zero stub length.

- P2: This script writes a fabrication-style Gerber zip for the new plate into `models/`, but the PR says that plate must not be fabricated until its 7U opening is revised. Either gate this output behind an explicit flag, or leave the zip out until the 7U relief is verified.

- P2: This DRC export was produced without `--severity-all` or `--all-track-errors`, so an empty `violations` list may not cover warnings or every track clearance error. The zero-warning claim in `native-RESULT.json` and the README rests on this output. Regenerate the report with the stricter flags used in the a21 gate bundle and record the command in the artifact.

- P2: This footprint is pads-only, unlike its `MX_Backspace_MillMax_Left_2U` sibling. Add a courtyard and silkscreen/fab outline, and the switch center NPTH (3.9878 mm) if the split switch needs one. Without a courtyard, placement DRC cannot catch overlap with the switch body or neighboring parts.

- P3: The placement claim omits an exception. The order package says 332 of 333 placements are fitted, and R123 uses the plain KiCad convention. Add the count so the statement matches the evidence.

- P3: This reproduction command is not executable as written because `<36700843 board>` is an unresolved placeholder. Provide the exact archived base-board path or commit the base PCB needed by the operation lists.

- P2: The commands write `main.json`, `end.json` and `ops.json`, but the spec and the table use `usb-pair-route-main.json`, `usb-pair-route-end.json` and `usb-pair-ops.json`. Rename the outputs to match the names the spec references, or the reproduction will not find the inputs `plan_pair_tracks.py` expects.

- P2: This footprint's Status and MPN fields say it is unselected, not procurement approved, and KOA RK73H1ETTP1000F. The candidate BOM and CPL populate R125 with a different part (UNI-ROYAL 0402WGF1000TCE, C25076). Either update the MPN/Manufacturer/Status fields to match the procured part, or mark the study footprint as not for this order.

- P2: On failure this script prints "no site found" but leaves any existing OPS file from a previous run untouched. A caller that ignores the exit code could apply stale ops to the board. Delete the output file or write an explicit empty result before returning 1.

- P3: The `stack` values (`er_mask` 3.8, `mask_mm` 0.02) are assumptions in fieldsolve.py, but this file presents them as stack data. Add a provenance or assumption marker, or record the solver source, so downstream LED pass/fail results are not read as measured.

- P2: This entry records the README and MANIFEST paths without pinning their SHA256. `tools/check_pcb_current.py` only verifies the ROLES files, so these two files can change without any check failing. Add a `files` list with digests, or have the checker cover `experimental_candidates`.

- P2: If a hop's source or destination pad lookup returns no sites, this loop runs zero times and the hop is dropped without an error. If every hop is dropped, `all([])` makes the report pass. Raise when either site list is empty, and require at least one case before passing.

- P2: These stabilizer fastener coordinates are magic numbers not tied to the board. Derive them from the footprint or stabilizer pads in `by_ref`, or add a check that they match the board, so the envelope check follows the board if it moves.

- P3: The note says 0.0 mm of copper sits between LED64 DOUT and R175, but the added `UG_LED_2_SRC` tracks run about 1.65 mm from pad 3 to R175 pad 1. Correct the note to the measured length, or move R175 next to LED64 pad 3 if zero stub length is the intent.

- P2: The `remove_vias` entry points at (270.11, 33.60375) on KEY_RGB_CHAIN_15, but the board has no via there. That location holds only a zero-length F.Cu track segment on net 145. Correct the entry to the via that was actually removed, or remove the op if no via was removed.

- P2: The slot grid extends to 40 positions (y up to 223.5 mm), beyond the documented y 80-145 mm block. `used` ignores non-R/C symbols, so a spec above 20 parts can land on existing Core content such as the switch at (449.58, 209.55). Limit the grid to the documented block; the 20-part spec fits in it.

- P2: Spec strings go into the .kicad_sch unescaped. A `"` or `\` in `note`, `value`, `footprint` or a net name produces an unparseable schematic. Escape each interpolated field, for example with a helper that replaces `\` and `"`.

- P2: This overwrites the project's `maru60.kicad_dru`, which holds the NPTH `hole_clearance` minimums. The JLCPCB deck has no NPTH-to-zone rule, so the 0.25 mm `npth_to_zone_0.25` check is silently dropped, contrary to the docstring's 'minimums stay in force'. Keep the project's rules in each copy, for example by running them as a separate pass, and correct the docstring.

- P2: This J1 exemption is stale. The GND lands were shortened to 0.21 mm from the pegs, and the JLC 0.20 mm NPTH rule passes without an exemption, so the exemption now only hides a future drop below 0.2 mm. Remove the `!(A.memberOfFootprint('J1') && B.memberOfFootprint('J1'))` clause and the comment that cites 0.194 mm.

- P3: The 0.25 mm zone rule wins over the 0.20 mm copper rule only because it appears later in the file. KiCad uses the last matching rule per constraint, so reordering the two rules would silently relax the zone clearance. Add a comment stating that the zone rule must stay after the copper rule.

- P2: The recorded firmware toolchain is not reproducible: the base image, apt packages, and QMK CLI are mutable. Pin the base digest and package versions, or build from a locked image and dependency set.

- P2: The documented reproduction command cannot run from the repository root because both referenced build files use nonexistent root paths. Use the packet paths for the Dockerfile and build script.

- P2: A failed dielectric corner is recorded as `pass: false` but the checker still exits successfully, so automated reruns can treat a failed USB validation as passing. Exit nonzero after writing the report when `result["pass"]` is false.

## 2026-11-12T03:43:51Z — COMMENTED

- P2: "Select the 7U wire" reads as the stabilizer for the 2U center switch. The candidate README says the 7U selection does not cover the 2U Backspace stabilizer, which is still unselected. State that the 7U wire is for the spacebar and that the 2U Backspace stabilizer is not yet selected.

- P2: This test adds an undeclared `ezdxf` dependency, so the documented clean-environment test suite fails before running it. Add `ezdxf` to the project dependencies and lockfile, or test the R12 file without requiring that package.

- P2: Passing a `ZipInfo` to `writestr` bypasses the `ZIP_DEFLATED` set on `ZipFile`, so these Gerber entries are stored uncompressed. Pass `compress_type=zipfile.ZIP_DEFLATED` to `writestr`, as `export_order_package.py` does for its zip.

- P3: `--seven-u-mount pcb` still reports the plate-mounted Designer Studio stabilizer as `selected_product`, misidentifying the generated alternative's hardware. Make this field conditional or omit it for the PCB-mount variant.

## 2026-11-12T03:58:20Z — COMMENTED

- P2: The report claims a nominal match even when `preserved` or a dimension check fails, because it is written before the later exit-1 guard. Derive this status from `preserved` and `checks` so failed custom plates cannot produce a false passing summary.

