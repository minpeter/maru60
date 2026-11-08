# Independent C128 retirement evidence review

## Disposition

The unselected candidate remains **ineligible under the strict global plane no-loss gate**. This electrical audit does not waive that gate or apply the BUCK-only 1 nm criterion.

The raw/file/DRC evidence passes, but the original helper's advertised drill-aware graph is inaccurate. The separate canonical-object v1 checker fixes one confirmed mechanism and preserves the recorded pad connectivity conclusions. A second, focused test confirms that v1 still does not subtract other objects' drills from tracks. No blanket physical-contact acceptance is justified from v1.

## Exact inputs

- Source board: aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f.
- Unselected filled candidate: cafa92133d336fef0b8236b8eafb2071bd6535cb991e95223a4b3fc233c4c4cb.
- Immutable contract: 4feb4ba2be91888a12f14524b2137537bd5a9e46aadad826e84be6bb26de3f6b.
- Selected BUCK predecessor tested separately: 2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373.

## Established from independent checks

`ELECTRICAL_AUDIT.json`, `file-manifest.json`, `verified-open-endpoints.json`, `verified-witnesses.json`, and `audit.log` contain the original audit details. All 47 listed checks passed; the report explicitly distinguishes original recorded graph support values from actual canonical support values.

- All 54 source/candidate paths are identical. All 53 non-board files are byte-identical. All 54 selected-source files match the isolated source snapshot.
- Prefill bytes equal the original board with exactly the nine named segment forms and one via form deleted, without additions. Retained nonzone forms are token-exact in original order. All zone configuration fields are exact; only the two saved inner-plane fills differ.
- Native retired centerline is 8.503623449077116 mm. The retired via and nine tracks are all +3V3. The sole live boundary remains track 0858c392 to retained attachment f578f80d.
- Native inventory contains 1,437 pads, including 1,082 named-net pads across 245 nets. Source/candidate inventories and independently reconstructed recorded pad partitions match.
- Full multiplicity-preserving DRC-record comparison is exactly 67 to 66 warnings, solely removal of track_dangling on 53e7b99f-308f-57ae-9e47-9e779e6b3272. No other warning changed or appeared. The full twelve open records are identical, not merely their endpoint UUID pairs.
- Every open endpoint's native UUID, object type, net, physical layer membership, position, and pad reference/number or track length agrees. Both endpoints remain in distinct recorded roots.
- DRC contains no additional errors beyond the twelve opens, schematic parity is empty, and all nine ERC sheets have no violations. Actual command/output/log paths and build/refill hashes are bound; the reused source reports are exact copies of the hash-matched prior candidate reports. DRC JSON itself does not embed an input SHA, so this is evidence-chain binding, not cryptographic execution attestation.

## Confirmed original helper defect and bounded v1 result

The helper `cu(q,l)` chooses its via/hole treatment through Python `isinstance`. `GetConnectedTracks` returns a native via as a Python PCB_TRACK wrapper, while `GetClass()` reports PCB_VIA and `HasHole()` is true. Cached neighbor copper can therefore be a full disk rather than the canonical via annulus.

The v1 checker in `corrected/` resolves every neighbor/contact through the canonical UUID inventory before shape construction. It was run serially on aead, 2c7, and cafa in separate processes/private XDG homes. No board or sealed original report was modified.

`corrected/CORRECTED_GRAPH_AUDIT.json` establishes:

- Each board loses the same three false track-via edges, with no newly positive edges.
- Surviving direct support areas change on 1,040 aead contacts, 1,041 2c7 contacts, and 1,039 cafa contacts. Four zone support values change on each board.
- All 245 pad partitions and all native-object root partitions remain unchanged versus each board's original graph under this canonical own-hole model.
- In both corrected transitions, 2c7 to aead and aead to cafa, all retained direct and zone support records are exact, all pad partitions are exact, and all retained-object root partitions are exact.
- All four C128/C129 supply and return witnesses plus the attachment-to-C128 join remain positive under this model. J1.A1's full object and pad root membership is identical across all three boards.
- `corrected/corrected-contract-witness-ledger.json` gives the corrected contacts alongside the immutable original contract values. It does not rewrite the contract.
- `corrected/controls.json` confirms canonical-via and neighbor-wrapper geometry identity on all four copper layers, rejection of all three observed drill-only false contacts, preservation of a positive annular contact, and unchanged native pad handling for all 1,437 pads/1,908 pad-layer checks (16 plated and 335 non-plated drilled pads).

## Further physical-drill limitation confirmed after v1

`corrected/other-drill-probe.json` tests the three affected 0.05 mm tracks. Each lies entirely inside its associated 0.25 mm via drill and therefore has zero physical copper. V1 still assigns each a positive track-track contact because its track shape does not subtract the via's drill. Those three contact areas become zero when all overlapping actual drill shapes are subtracted.

Thus v1 corrects the wrapper/own-hole bug, but cannot be called a globally drill-subtracted graph. A future all-hole model must also address zero-copper objects and possible multi-outline remnants rather than silently unifying disconnected remnants by one UUID. These caveats do not reverse the independently established strict native plane-loss failure.
