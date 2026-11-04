#include <assert.h>
#include <stdio.h>
#include "mock/quantum.h"
#include "../qmk/keyboards/maru60/rp2350/maru_layout_policy.h"
struct led_config_mock g_led_config;
void via_set_layout_options_kb(uint32_t value);
extern uint32_t maru_layout_options;
int main(void) {
 for(unsigned state=0;state<4;state++) {
  via_set_layout_options_kb(state);
  unsigned active=0;for(unsigned i=0;i<64;i++)active+=maru_pixel_active(i,state);
  assert(active==(MARU60_LAYOUT_HHKB?60:(state&2?59:60)));
  assert(g_led_config.matrix_co[2][0]==((state&1)?30:29));
  assert(g_led_config.matrix_co[3][11]==((state&2)&&!MARU60_LAYOUT_HHKB?44:45));
  assert(g_led_config.matrix_co[3][12]==((state&2)&&!MARU60_LAYOUT_HHKB?NO_LED:43));
  assert(maru_pixel_active(g_led_config.matrix_co[2][0],state));
  assert(maru_pixel_active(g_led_config.matrix_co[3][11],state));
 }
 puts(MARU60_LAYOUT_HHKB?"PASS HHKB: canonical split RShift, Caps alternatives, bottom blockers":"PASS WKL: four Caps/RShift option combinations, inactive pixels black, dynamic reactive mapping, bottom blockers");
}
