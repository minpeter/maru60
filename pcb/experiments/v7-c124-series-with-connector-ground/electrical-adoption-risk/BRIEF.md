# C124 adoption decision brief

**D is a reasonable next-prototype candidate, not an electrically qualified replacement.** It addresses a documented TI recommendation; it does not solve the design's brownout, startup or noise uncertainties.

**Why add 100 Ω?** [TI TPS25947 Rev C §7.3.5.1](https://www.ti.com/lit/ds/symlink/tps25947.pdf) recommends it for actual CdVdt **>10 nF**. Nominal 10 nF alone does not mandate it, but ±10% spans 9–11 nF. D therefore covers a plausible tolerance condition. The 0.891–1.111 µs passive RC product is not an output-ramp or rail-ready guarantee.

**What stays electrically unchanged?** Both selected c770 and D f987 retain the 590 kΩ/156 kΩ OVLO divider and its ±0.1% initial tolerances. Nominal current at 5 V remains 6.7024 µA; nominal rising/falling thresholds remain 5.73846/5.21244 V. Nominal differences are zero. UVLO's 620 kΩ/267 kΩ values also remain unchanged, so the existing brownout concern remains.

**Which R121 comparison is valid?** Selected R121 is generic 0603 with no MPN, manufacturer or datasheet. Its TCR, environmental stability and rating are unknown. TNPW0603156KBEEA was an unselected proposal. D's catalog-supported KOA RN73R1ETTP1563B25 cannot honestly be called either stability-equivalent or a known downgrade versus selected hardware.

Against that unselected TNPW proposal only, KOA's published 1000-hour endurance allowance is looser and tested at a different temperature. Their R121-only threshold sensitivities are approximately ±4.54 mV versus ±2.27 mV, holding everything else fixed; these are not predicted actual drift. KOA's humidity allowance has an exact-value caveat, and R120's missing MPN/TCR prevents a complete tracking budget. [KOA RN73R](https://www.koaspeer.com/pdfs/RN73R.pdf), [Vishay TNPW](https://www.vishay.com/docs/28758/tnpw_e3.pdf).

**What blocks a qualification claim?**
- The passive model is not active eFuse startup, reset or fault testing. Its pin-side pickup example increases with series resistance; it does not prove board noise improvement.
- R125 repetitive discharge/pulse stress and effective C124 over bias/temperature/aging remain unverified.
- No accepted input-fault/transient envelope or complete threshold-drift budget exists. The 23 V resistor diagnostic is not an allowed operating point.
- Actual geometry, assembly-process and mechanical acceptance are separate gates.

**Recommendation:** preserve D as the preferred prototype candidate after its separate geometry gates pass. Make any selection explicitly experimental, with the operating envelope, precision budget and unresolved risks recorded. Require powered startup/brownout/reset/pulse and environmental checks before electrical or production acceptance. Keeping the unspecified selected baseline is not proof of lower risk.

Exact source hashes, independent review and reproducible arithmetic are in MEMO.md and the accompanying evidence. No CAD/BOM changes or new active simulations were made.
