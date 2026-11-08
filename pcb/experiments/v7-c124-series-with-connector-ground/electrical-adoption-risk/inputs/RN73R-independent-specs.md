# KOA RN73R1ETTP1563B25 independent review
Checked 2026-11-04; read-only, no adoption.

## Manufacturer catalog support
[RN73R datasheet](https://www.koaspeer.com/pdfs/RN73R.pdf), page 1 dated 10/24/25; page 2 dated 1/20/25:
- Ordering: RN73R / 1E=0402 / T=Sn / TP / 1563=156×10³Ω / B=±0.1% / 25=±25ppm/K.
- Range explicitly includes E192 and 47Ω–300kΩ for 1E/B/25. This is positive table support, not merely plausible syntax.
- Standard mode: 0.063W at 85°C ambient, 90°C terminal; power mode 0.1W, 105°C terminal. Derate linearly to zero at 155°C; operating range −55…155°C.
- Working/overload ceilings: 50/100V; rated voltage=min(√PR,50V).
- Standard overload: min(2.5×rated-voltage,100V), 5s, drift ±(0.05%+0.05Ω). No separate pulse-energy curve established.
- Endurance: 1000h, 85°C, 1.5h-on/0.5h-off, ±(0.1%+0.05Ω) standard; power-mode 0.2%. Moisture/high-temperature limits 0.25%+0.05Ω carry resistance-dependent caveats.
- Body mm: L=1.0 +0.10/−0.05; W=0.50±0.05; t=0.35±0.05. Top termination c=0.25±0.10; bottom d=0.25 +0.05/−0.10.

## Packaging and exact value corroboration
[Appendix A](https://www.koaspeer.com/pdfs/Appendix_A.pdf), page 1, 10/27/26: RN73R 1E expressly uses TP, 2mm-pitch paper, 10,000/reel, 180mm reel diameter.
[Appendix D](https://www.koaspeer.com/pdfs/Appendix_D.pdf), page 3: 156 appears in the E192 standard-value table. Combined with datasheet range/tolerance/TCR and Appendix A, the requested full code is supported as a standard catalog ordering combination. No independent manufacturer exact-SKU web listing was found; catalog support does not establish stock or delivery.

## Recommended reflow lands
[Appendix B](https://www.koaspeer.com/pdfs/Appendix_B.pdf), page 1, 04/15/26, RN73 family 1E row, visually checked diagram:
- A (inner gap) = 0.50mm.
- B (outside span) = 1.30mm.
- C (pad width) = 0.30mm.
- D (pad length) = 0.40mm.
- Derived pad-center spacing: 0.90mm.
KOA notes soldering conditions may change optimum lands. These are manufacturer recommendations, not a claim of suitability for the actual board or production process. In particular, do not substitute Vishay's wider recommended lands or infer that narrower KOA lands eliminate all courtyard/placement constraints.

## Scope
Datasheets, extracted text, and visual evidence are stored beside this report. No actual PCB land overlap, courtyard, soldermask, paste, placement tolerance, circuit transient, stock, or manufacturing qualification was assessed. Parent handles divider calculations.

## Comparison with proposed Vishay TNPW0603 e3
Compare published test limits, not presumed interchangeable performance:
- KOA standard endurance: ±(0.1%R+0.05Ω), 1000h at 85°C; power-mode limit is 0.2%R+0.05Ω.
- Vishay general endurance: ±(0.05%R+0.01Ω), 1000h at 70°C. Its general load-life table additionally gives 0.10% at 8000h and 0.30% at 225000h; no equivalent longer-duration KOA promise was established.
- KOA moisture: ±(0.25%R+0.05Ω), 85°C/85%RH/1000h, with value-dependent caveat. Standard-mode bias is rated voltage (limited by working voltage), cycling 1.5h on/0.5h off.
- Vishay accelerated humidity: ±(0.1%R+0.01Ω), 85°C/85%RH/1000h, general-mode bias sqrt(0.1×P70×R), capped at 0.3×Umax. Different biases and endurance temperatures prevent treating these as a controlled head-to-head comparison.
- No explicit numerical DC voltage coefficient guarantee was located in either reviewed datasheet. Vishay's non-linearity graph is not a guaranteed DC ppm/V value and must not be imported into KOA.
- KOA is therefore a catalog-supported candidate, not an established stability-equivalent replacement. Do not reuse TNPW drift allowances for RN73R without adjusting the divider budget. R120 MPN/TCR and thermal tracking remain unknown.
- No accepted fault/transient VIN maximum exists in the supplied scope. 5/5.25/5.5V and the 23V resistor-only diagnostic do not establish system safety or transient qualification.

Comparison source: Vishay document 28758 rev 10-Apr-2026, pp2,9,12–13, https://www.vishay.com/docs/28758/tnpw_e3.pdf; KOA RN73R above. Courtyard/process acceptance remains separate from these geometry data.
