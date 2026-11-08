# Checkpoint01 source-cut erratum

The frozen checkpoint01 files and their measured ERC/DRC/parity results are unchanged. A later audit found that the first insertion script used PAD.GetLayer() on backside pads; in KiCad9 this returns F.Cu despite pad.IsOnLayer(B.Cu) being true. The script consequently removed front-side tracks beneath replaced backside parts and missed some actual backside boundary tracks. Zero geometry DRC did not prove that these removals were necessary.

The initial 56-cut description must not be treated as a qualified source-preservation contract. The next revision restores falsely cut original objects and retires only actual common-copper-layer touching objects. Exact source UUIDs, raw geometry and semantic net names are retained. This is a candidate-only correction; accepted main was never changed. The next revision requires fresh native net assignment, source delta, refill, ERC/parity/DRC/source-root checks.
