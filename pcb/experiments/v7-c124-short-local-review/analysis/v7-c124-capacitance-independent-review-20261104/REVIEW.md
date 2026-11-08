# Independent C124 comparison review

**Approval-eligible as a read-only analytical screen. No BOM/CAD selection or hardware qualification.**

The exact7c23 source board and recorded netlist bindings are correct. C124 has no recorded exact MPN or dielectric. USB_DVDT contains only C124.1 and U8.7; the directly connected1uF+0.1uF+4.7uF capacitors sum to5.8uF nominal. U18 VIN is on that rail with EN intentionally floating, so the simple capacitive-current calculation excludes active startup load.

The original1,200 unique factorial rows were independently recomputed in Decimal/SI units. The original calculation was also reproduced in an isolated copy, yielding byte-identical results.json and sensitivity.csv. The separate NP0 calculation likewise reproduces byte-identically and matches independent arithmetic. No original CAD/BOM/study file was edited by this review.

The simplified upper corners are10.373nF for8.2nF±10% with+15%,9.9015nF for8.2nF±5% with+15%, and8.602nF for6.8nF±10% with+15%. They are conditional tolerance/temperature screens, not guaranteed assembled-circuit limits.

Manufacturer facts and the corrected TI citation, TDK NRND status and0603/0402 distinction are verified. TDK C1608NP01H822J080AA is a supported Production0603/NP0 candidate. Its conditional coefficient-extrapolation upper case is8.6422875nF, with1.3577125nF to10nF. Detailed coefficient testing uses25/85C and lower-temperature checks; applying a constant worst coefficient across the full catalog range is explicitly an assumption, not a verified pointwise guarantee.

Existing C124 lands have0.65mm gap,0.90mm axial length and0.95mm width. TDK recommends0.60–0.80mm for each. The gap matches; length and width exceed recommendations by0.10/0.15mm. This requires assembly review and is neither automatic drop-in approval nor proof of unsafe assembly.

Official links and source-specific qualifications are in official-facts/. Full source hashes, numerical checks and limitations are in FINAL_REVIEW.json and the two detailed JSON reviews. No activeSPICE, hardware startup, parasitic extraction or production qualification was performed.
