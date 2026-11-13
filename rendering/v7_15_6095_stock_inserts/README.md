# Maru60 v7.15 — relocate the joint axis

Selected by the owner for **physical build 02** on 2026-11-13. See the
[build record](../../docs/print-history.md) and the
[frozen print release](../../models/print-02-v7.15-6095-stock-inserts/).

The three wrist/front-bezel dovetails and the main split move 2.9 mm toward
negative X. This centres the original 13.8 mm support envelope at X=0,
without the 19.6 mm rib used in the v7.14 trial. The joint profiles retain
the original 4.0 mm root-side and 9.8 mm socket-side support from the seam.

The middle bumpon remains on X=0, centred on the rib. Its rounded 16 mm pad
widens the rib only at the front. The unchanged honeycomb lattice has equal
3.903 mm margins. PCB/stock catch interfaces and the rear strike seam retain
their original positions. Variant: `6095-trimode`, `stock`, `--inserts`.

Use both v7.15 halves together: the moved joints do not align with older halves.
Print files are `geometry/maru60-hhkb-left-plate.3mf` and
`geometry/maru60-hhkb-right-plate.3mf`. The exact delivered pair and ZIP are
also published under `models/print-02-v7.15-6095-stock-inserts/`; generic
`models/` filenames retain the earlier variants.

Validation:

- `geometry/verification.json`: mesh integrity, 91-step assembly path,
  retention, glue clearances, printing layers, stock mating gauges and
  bumpon clearance all passed. Centre-rib/pad edges checked at 20 sections.
- `regression.log`: all eight insert, catch and paired-housing tests passed.
- `audit.py` / `change-audit.json`: the six exported joint halves match v7.13
  after undoing the 2.9 mm translation (differences below 0.001 mm³). Top skin
  and keyboard interfaces match. Assembled volume is within 24 mm³ of v7.13.

The 2800 × 2100 render uses llm-labs RX 570, Blender 5.2.2 Cycles HIP, up to
256 adaptive samples and OIDN denoising, with the same camera and lighting.
Brass inserts are nominal OD3.5 × L3 sleeves; threads/knurling are omitted.
`render-receipt.json` records the GPU and input hashes.

Rebuild from the repository root:

```sh
export MARU60_TOPCASE_DIR="$PWD/rendering/v7_15_6095_stock_inserts/geometry"
uv run python build_topcase_draft.py --board 6095-trimode --catches stock --inserts
uv run python verify_topcase.py
uv run python rendering/v7_15_6095_stock_inserts/prepare.py
uv run python rendering/v7_15_6095_stock_inserts/audit.py
```

Copy `render.py`, `shell-meshes.json` and `insert-sites.json` to a directory
on llm-labs, then run there:

```sh
~/blender-gfx803/scripts/blender-gfx803 -b --factory-startup \
  --python-exit-code 1 --python render.py -- --quality final
```

The two-tone render is `maru60-v7.15-two-tone.png`: blue `LeftHalf`, orange
`RightHalf`, including their actual interlocking fingers and staggered rear
seam. `render_two_tone.py` opens the original saved scene and changes only
the two shell materials; run it after loading
`maru60-v7.15-6095-stock-inserts.blend`. `two-tone-receipt.json` records the
source scene hash and GPU settings. `two-tone.html` includes a joint close-up.
