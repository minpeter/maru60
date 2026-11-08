# Explicit four-layer NPTH variants

`MX-Hotswap-2.25U-4L-NPTH` and `MX-Hotswap-7U-4L-NPTH` derive from
`../third_party/MX_V2/` equivalents. Retain that directory's MIT LICENSE and
existing ai03 provenance. This derivative does not select a whole-project hardware
license. Source hashes are recorded in `../stabilized-footprint-normalization.json`.

Changes: serialize through KiCad 9; assign every NPTH pad an explicit
F.Cu/In1.Cu/In2.Cu/B.Cu/F.Mask/B.Mask layer set rather than the source's mixture
of legacy `*.Cu`/`F&B.Cu` declarations and inherited inconsistent layer masks.
No pad shape, position, size, drill shape, drill size or contact geometry changes.
Generator asserts these exact properties before and after library save/reload.
The apply script independently asserts installed board geometry is unchanged.

This is a representation/layer-mask repair for this four-copper-layer design,
not evidence of stabilizer or switch housing fit. It is not intended as a generic
2-layer or arbitrary-layer-count variant.
