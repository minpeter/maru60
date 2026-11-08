# C124 analytical 0603 NP0/C0G-class option

Checked 2026-11-04. Original fact audit remains in verification.md; its 6.8 × 1.10 × 1.15 arithmetic is corrected to **8.602 nF**. No CAD, study, or BOM edits were made.

## Supported candidate and exact identity

**TDK C1608NP01H822J080AA** is officially in **Production**, rather than NRND. Manufacturer facts: 8.2 nF ±5%; 50 VDC; NP0, 0±30 ppm/°C; -55°C to +150°C; commercial grade, not AEC-Q200; EIA 0603 (1608 metric). L/W/T are 1.60/0.80/0.80 mm, each ±0.10 mm. Termination B is at least 0.20 mm, and terminal spacing G at least 0.30 mm. Packaging is punched paper tape, nominal 180 mm reel, 4,000 pieces. The page separately displays an internal item-description pattern, C1608NP01H822JT****; that wildcard is not a fully resolved orderable suffix.

Official source: https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608NP01H822J080AA

TDK's high-temperature catalog identifies the catalog-number suffix as thickness 080 = 0.80 mm, packaging style A = 178 mm reel / 4 mm pitch, and final A = reserved internal code. The catalog warns that catalog numbers differ in the last five positions from label/internal item descriptions. Use the complete verified catalog number above, not an invented concrete expansion of T****. The catalog's 178 mm designation and product page's nominal 180 mm reel designation both refer to the listed standard packaging; retain each source's wording rather than treating them as a separate variant.

Official source: https://product.tdk.com/en/system/files/dam/doc/product/capacitor/ceramic/mlcc/catalog/mlcc_commercial_hightemp_en.pdf

## Temperature coefficient and analytical envelope

The high-temperature catalog lists NP0, 0±30 ppm/°C, and the -55°C to +150°C range together. The exact candidate occurs in its NP0 capacitance table. The linked general specification's section 3, printed p.5, gives NP0 a **25°C reference temperature**. Listing coefficient and range together does not, by itself, resolve the detailed specification's limited coefficient-test points into a guaranteed pointwise linear bound at every temperature.

A **conditional coefficient-extrapolation screening calculation**, assuming a pointwise ±30 ppm/°C envelope relative to 25°C over the whole operating range, is:

- Maximum distance from 25°C over this range is 125°C.
- 8.2 nF × 1.05 × (1 + 30e-6 × 125) = **8.6422875 nF**.

This is not a confirmed guaranteed full-range capacitance maximum. No additional primary-source guarantee was located that independently closes the gap between the catalog range and the detailed coefficient-test points. It is also not a guarantee for all stresses, test methods, or circuit startup. The specification's Class-1 method (p.7) calculates coefficient using 25°C and 85°C and lists lower measurement temperatures of -10°C and -25°C. It separately specifies capacitance drift of ±0.2% or ±0.05 pF, whichever is larger. Do not silently absorb that separate drift allowance into the ppm coefficient or assume a complete operating bound from the simple calculation. Resolve applicable measurement, drift, and application conditions before qualification.

Official specification, linked from the exact product page: https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/specification/mlccspec_commercial_general_midvoltage_en.pdf

## Land-pattern comparison

The specification's printed p.18 land drawing was visually checked. A (product-page PA) is the inner gap between lands; B/PB is each land's length along the component axis; C/PC is land width perpendicular to that axis. The C1608 reflow recommendation is **0.60–0.80 mm for each A, B, and C**.

The parent's supplied current C124 geometry is pads 0.90 × 0.95 mm, centered at local x = ±0.775 mm. Taking 0.90 mm along local x, the inner gap is 1.55 - 0.90 = **0.65 mm**. The gap is within the recommendation, but pad length 0.90 mm exceeds the recommended maximum by 0.10 mm and width 0.95 mm exceeds it by 0.15 mm. Thus this is **not a demonstrated manufacturer-recommended land-pattern match or drop-in replacement**. This comparison uses parent-supplied pad geometry, not an independent CAD read. It does not prove the existing land is unmanufacturable either; assembly/process review is still required.

## Old TDK part must not be conflated

**C1608C0G1H822J080AA** is officially **Obsolete**, not merely NRND. TDK lists discontinuance issue 2023-05-11, last order 2025-01-31, and last shipment 2025-03-31. Its suggested alternate is C1608C0G2A822J080AC, with interchangeability not guaranteed. The obsolete part's temperature range ends at +125°C. The selected +150°C NP0 part above is a separate catalog candidate, not a packaging-suffix-only rename of it.

Official source: https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608C0G1H822J080AA

The NP0 option removes reliance on an assumed X7R ±15% thermal-change model. It does not establish startup qualification, dVdt slew bounds, pin-current corners, pad equivalence, procurement availability, or authorization to modify the BOM.
