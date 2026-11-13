# Maru60 v7.14 — symmetric centre rib

Superseded widening trial. The owner selected v7.15 for physical build 02. See [the build record](../../docs/print-history.md).

The underside centre rib now extends 9.8 mm to each side of the X=0 split
and runs straight from the wrist-rest front wall to the keyboard bezel.
The centre bumpon pocket stays on X=0. Both honeycomb margins are 1.003 mm.
This replaces v7.13's 4.0 mm left web and 9.8 mm right socket support.

Variant: `--board 6095-trimode --catches stock --inserts`.
The source CAD geometry was changed; the renderer adds only nominal brass
OD3.5 × L3 sleeves, with threads and knurling omitted.

Validation:

- `geometry/verification.json`: exported mesh, 91-step dovetail assembly,
  retention, stock mating interfaces, layer connectivity, overhangs and
  bumpon gauges all passed. Centre-rib edges are checked at 16 sections.
- `regression.log`: eight insert-option, stock/LUBAN compatibility and paired
  housing workflow tests passed.
- `change-audit.json`: approximately 5846 mm³ of material added inside the
  central rib. Material removed and changes outside that area are below
  0.002 mm³ (export rounding); the top skin and honeycomb pattern are unchanged.

Rendering uses llm-labs over SSH, AMD Radeon RX 570, Blender 5.2.2 Cycles HIP,
2800 × 2100, up to 256 adaptive samples and OIDN denoising. Camera and lighting
match v7.13. `render-receipt.json` records the input hashes and selected GPU.
`view.html` shows matching crops before and after, and the full revised image.

Rebuild from the repository root:

```sh
export MARU60_TOPCASE_DIR="$PWD/rendering/v7_14_6095_stock_inserts/geometry"
uv run python build_topcase_draft.py --board 6095-trimode --catches stock --inserts
uv run python verify_topcase.py
uv run python rendering/v7_14_6095_stock_inserts/prepare.py
```

Copy `render.py`, `shell-meshes.json` and `insert-sites.json` into one directory
on llm-labs. From there:

```sh
~/blender-gfx803/scripts/blender-gfx803 -b --factory-startup \
  --python-exit-code 1 --python render.py -- --quality final
```

Printable revised halves are in `geometry/maru60-hhkb-left-plate.3mf` and
`geometry/maru60-hhkb-right-plate.3mf`. Published `models/` were not refreshed.
