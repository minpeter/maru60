// SPDX-License-Identifier: GPL-2.0-or-later
// Opt-in bench experiment only: unchanged clock sources/divisors and WAKE_EN.
#include "quantum.h"
#include "maru_suspend_masks.h"
#if !defined(MCU_RP) || !defined(MARU60_SUSPEND_EXPERIMENT)
#    error This file requires the explicit Maru60 RP2350 suspend experiment
#endif
static bool masked;
static uint32_t saved0, saved1;
void maru_suspend_enter(void) {
    if (masked) return;
    // Task context, after both LED transports have been aborted/stopped.
    // ChibiOS idle WFI wakes on its existing timer/USB interrupts; do not
    // mask IRQs, alter PLLs, stop timebase or turn off XIP/memory power.
    saved0 = CLOCKS->SLEEP_EN0;
    saved1 = CLOCKS->SLEEP_EN1;
    CLOCKS->SLEEP_EN0 = maru_sleep_mask0(saved0);
    CLOCKS->SLEEP_EN1 = maru_sleep_mask1(saved1);
    __DSB();
    masked = true;
}
void maru_suspend_leave(void) {
    if (!masked) return;
    CLOCKS->SLEEP_EN0 = saved0;
    CLOCKS->SLEEP_EN1 = saved1;
    __DSB();
    masked = false;
}
