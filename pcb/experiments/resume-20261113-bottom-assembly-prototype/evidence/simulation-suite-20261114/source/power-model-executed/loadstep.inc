* (b) load-step stimulus, shared by the switching and the averaged deck.
* Start-up is shortened (soft-start capacitor 10 nF instead of 100 nF and
* a 50 x faster eFuse ramp) so the rails are settled by 4 ms; the steps are
* applied to a settled circuit, so this does not change them.
*   6 ms   3V3 load i33a -> i33b in 1 us        8 ms  back to i33a
*  10 ms   LED_ENABLE high (rail charges, 38 mA static load appears)
*  16 ms   LED drive current 0 -> iled in 1 us  19 ms  back to 0
Vsrc src 0 pwl(0 0 10u 0 11u {vsrc})
Vlen len 0 pwl(0 0 10m 0 10.001m 3.3)
Vi33 i33cmd 0 pwl(0 {i33a} 6m {i33a} 6.001m {i33b} 8m {i33b} 8.001m {i33a})
Vled ledcmd 0 pwl(0 0 16m 0 16.001m {iled} 19m {iled} 19.001m 0)
Vsh33 sh33 0 0
Vshl shled 0 0
