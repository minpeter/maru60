// SPDX-License-Identifier: GPL-2.0-or-later
#include <assert.h>
#include <stdio.h>
#include "../qmk/keyboards/maru60/rp2350/maru_led_counts.h"
#define CHANNEL_COUNT (3*(MARU_KEY_LED_COUNT+MARU_UG_LED_COUNT))
#include "../qmk/keyboards/maru60/rp2350/maru_rgb_policy.h"
int main(void) {
    for(unsigned v=0;v<32;v++) {
        bool allowed=maru_led_may_power(v&1,v&2,v&4,v&8,v&16);
        assert(allowed==(v==23));
    }
    uint32_t seed=1;
    for(unsigned test=0;test<100000;test++) {
        uint8_t frame[CHANNEL_COUNT]; uint32_t sum=0, scaled=0;
        for(unsigned i=0;i<CHANNEL_COUNT;i++) {
            seed=1664525U*seed+1013904223U;
            frame[i]=test==0?255:test==1?0:(seed>>24);
            sum+=frame[i];
        }
        for(unsigned i=0;i<CHANNEL_COUNT;i++) {
            unsigned out=maru_scale_channel(frame[i],sum);
            assert(out<=frame[i]); scaled+=out;
        }
        assert(scaled<=MARU60_PWM_SUM_LIMIT);
        if(sum<=MARU60_PWM_SUM_LIMIT)assert(scaled==sum);
    }
    printf("PASS: all 32 gate states; 100000 %u-pixel frames; PWM sum <=1020 (not an electrical-current proof)\n", MARU_KEY_LED_COUNT+MARU_UG_LED_COUNT);
}
