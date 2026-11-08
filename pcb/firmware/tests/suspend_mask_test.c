// SPDX-License-Identifier: GPL-2.0-or-later
#include <assert.h>
#include <stdio.h>
#include "suspend_mock/quantum.h"
#include "../qmk/keyboards/maru60/rp2350/maru_suspend_masks.h"
mock_clocks_t mock_clocks;
void maru_suspend_enter(void);
void maru_suspend_leave(void);
int main(void) {
    // Explicit essential clocks from RP2350 datasheet tables621/622.
    uint32_t essential0=(1UL<<31)|(1UL<<29)|(3UL<<21)|(1UL<<17)|(1UL<<13)|(1UL<<7)|(3UL<<5)|1UL;
    uint32_t essential1=(3UL<<29)|(1UL<<28)|(3UL<<26)|(15UL<<17)|(1023UL<<4);
    assert(!(MARU_SLEEP_GATE0 & essential0));
    assert(!(MARU_SLEEP_GATE1 & essential1));
    uint32_t seed=1;
    for(unsigned i=0;i<100000;i++) {
        seed=1664525U*seed+1013904223U; uint32_t a=seed;
        seed=1664525U*seed+1013904223U; uint32_t b=seed;
        mock_clocks=(mock_clocks_t){a,b};
        maru_suspend_enter();
        assert(mock_clocks.SLEEP_EN0==(a&~MARU_SLEEP_GATE0));
        assert(mock_clocks.SLEEP_EN1==(b&~MARU_SLEEP_GATE1));
        maru_suspend_enter(); // repeated 17ms suspend loop must not overwrite saved registers
        maru_suspend_leave();
        assert(mock_clocks.SLEEP_EN0==a && mock_clocks.SLEEP_EN1==b);
        maru_suspend_leave();
        assert(mock_clocks.SLEEP_EN0==a && mock_clocks.SLEEP_EN1==b);
    }
    puts("PASS: essential clock masks preserved; 100000 actual enter/reenter/leave/releave register-model cycles. NOT hardware sleep/wake validation.");
}
