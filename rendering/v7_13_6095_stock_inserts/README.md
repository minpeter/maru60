# Maru60 v7.13 — 6095 / stock catches / inserts

Historical baseline retained for comparison and the v7.15 geometry audit. See [the build record](../../docs/print-history.md).

Upper housing with integrated wrist rest, using the latest v7.13 geometry,
`--board 6095-trimode --catches stock --inserts`.

The underside view exposes all eight insert positions and the original
ball-catch strike pockets. The shell comes directly from the exported 3MF,
without smoothing or shape changes. Brass inserts are nominal OD3.5 × L3
sleeves for visualization; their knurling and threads are omitted. U-BL.2
uses the specified 0.35 mm recess. PCB, lower housing and catch hardware
are not displayed. The blue-grey polymer and lighting are presentation choices.

Geometry verification: `geometry/verification.json`, `ALL_PASSED`.
Rendering: llm-labs, AMD Radeon RX 570, Blender 5.2.2 Cycles HIP.
The final image is 2800 × 2100, up to 256 adaptive samples, with OIDN denoising.
`render-receipt.json` records the selected GPU, input hashes and render time.

Rebuild geometry from the repository root:

```sh
export MARU60_TOPCASE_DIR="$PWD/rendering/v7_13_6095_stock_inserts/geometry"
uv run python build_topcase_draft.py --board 6095-trimode --catches stock --inserts
uv run python verify_topcase.py
uv run python rendering/v7_13_6095_stock_inserts/prepare.py
```

Copy `render.py`, `shell-meshes.json`, and `insert-sites.json` into one
directory on llm-labs. From that directory:

```sh
~/blender-gfx803/scripts/blender-gfx803 -b --factory-startup \
  --python-exit-code 1 --python render.py -- --quality final
```
