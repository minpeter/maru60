# R2 actual-material graph evidence

This is new, bounded evidence for the three exact input boards, not restoration of missing historical acceptance code, not selection of the C128 experiment, and not a waiver of its strict plane-preservation failure.

Checker SHA256: 57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9.

## Physical model and controls

The checker fails closed on optimized Python, another KiCad build, another enabled copper stack, unsupported drill spans, cut/severed plated annuli, or a named pad without a unique material root. All actual holes are asserted through-board. NPTH cuts all copper layers regardless of its pad-layer list and never gets a barrel join. Compound native shapes are unioned before fragment identity. Every positive object/layer/island remains separate; no small-area waiver discards a fragment.

Through-via/PTH barrel connections require centered-circle or exact integer convex hole-enclosure proof, one remaining annulus per layer, and exact orientation-preserving normalized native contours matching the own-hole annulus. Coordinate discrepancies fail even if native subtraction reports zero area. Accepted contacts additionally have positive native overlap after both material components are guarded inward 2 nm; guard failures remain explicit and are not joined.

Controls cover the observed wrapper failure, all three observed false track-via contacts, an actual NPTH drill removing track-track overlap, partial surviving two-island copper, independent primitive union, NPTH fragments with no cross-layer join, forged raw-coordinate mismatch, outside-hole false-barrel rejection, and microscopic versus robust contact guards. See controls.json and test_material_controls.py.

## Results

All three serial exports completed with exit 0 and unchanged input hashes:

- 2c7 predecessor: 21,797 accepted direct object contacts, 731 zone contacts.
- aead selected source: 21,796 direct, 731 zone.
- cafa unselected C128 candidate: 21,783 direct, 731 zone.

Every board preserves all 245 original pad partitions. Compared with each original helper output, R2 removes 105 direct object contacts and adds none. All three have 20 net-bearing tracks with no physical copper, 17 multi-outline object layers, and 51 microscopic direct material-contact edges that fail the inward guard and are excluded. The latter do not remove additional whole object pairs because other substantial fragments preserve those pairs. No zone contact fails the guard.

The physical root model deliberately does not force empty copper or disconnected remnants into one UUID root. Eleven objects have multiple material roots. The isolated NPTH approximation fragments are retained but have no barrel connection.

## Transition checks

After excluding declared source retirements and candidate additions, both 2c7→aead and aead→cafa have exact retained direct/zone contacts and support areas, exact accepted material-edge raw and guarded support values, exact nonzone material metadata, exact retained material-vertex partitions, and exact guard-failure sets. All pad inventories and 245 pad partitions are exact.

The BUCK replacement's three contact identities match the old active track's identities, but the two geometries have different support areas at two contacts. They remain robustly positive and are reported separately. Do not mislabel new replacement contacts as retained-object contacts. EARLY_DRAFT_CORRECTION.md identifies the preserved erroneous quick report and its corrected replacement.

The four C128/C129 supply/return paths and attachment→C128 join have continuous per-material-node witnesses, including proved plated barrel joins. The same source witnesses and exact edge proofs survive in cafa. J1.A1's complete material-root membership is identical in all three boards. All twelve DRC open endpoint pairs have nonempty, disjoint physical root sets in both aead and cafa.

Primary artifacts: MATERIAL_GRAPH_AUDIT.json, material-witness-contract-ledger.json, twelve-open-material-root-check.json, commands.json, and each board's physical-graph.json/export.log. The original raw/DRC/file audit remains one directory above. The strict native global plane no-loss gate remains a separate FAIL for cafa.

## Explicit NPTH participation supplement

NPTH_PARTICIPATION.json inventories every NPTH fragment and root on all three boards. Each has335 NPTH objects:334 are empty, while only SWRS1/c8b60afe retains56 positive approximation fragments (14 per copper layer). None participates in an accepted edge, a guard-failed edge, a barrel join, or any named-pad root. Their layer/island vertices remain separate. No NPTH material creates an electrical or cross-layer bridge.

## Runtime-isolation erratum

The export runners set four private standard XDG profile homes, plus the nonstandard XDG_RUNTIME_HOME. They did not explicitly set or record XDG_RUNTIME_DIR. Its inherited value is unknown, so five-location runtime isolation is not established. Current run scripts and results are preserved. See RUNTIME_ENVIRONMENT_ERRATUM.json. Future runners must bind the standard runtime directory, set mode0700, and disable bytecode writes.
