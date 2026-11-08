// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "via.h"
#include "maru_layout_policy.h"
uint32_t maru_layout_options;
void via_set_layout_options_kb(uint32_t value) {
 value=maru_effective_options(value);
 maru_layout_options=value;
 g_led_config.matrix_co[4][0]=MARU60_LAYOUT_HHKB?NO_LED:57;
 g_led_config.matrix_co[4][1]=MARU60_LAYOUT_HHKB?58:NO_LED;
 g_led_config.matrix_co[4][11]=MARU60_LAYOUT_HHKB?62:NO_LED;
 g_led_config.matrix_co[4][12]=MARU60_LAYOUT_HHKB?NO_LED:63;
 g_led_config.matrix_co[2][0]=(value & MARU_LAYOUT_CAPS_STEPPED)?30:29;
 g_led_config.matrix_co[3][11]=(value & MARU_LAYOUT_RSHIFT_NORMAL)?44:45;
 g_led_config.matrix_co[3][12]=(value & MARU_LAYOUT_RSHIFT_NORMAL)?NO_LED:43;
}
