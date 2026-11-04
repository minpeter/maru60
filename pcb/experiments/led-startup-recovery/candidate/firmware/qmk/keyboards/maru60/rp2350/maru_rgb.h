// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "quantum.h"
enum maru_keycodes { MARU_UG_TOGGLE = QK_KB_0, MARU_UG_HUE, MARU_KEY_TOGGLE, MARU_CAPS_OPTION, MARU_RSHIFT_OPTION };
void maru_rgb_power_off(void);
void maru_rgb_task(void);
void maru_rgb_usb_configured(bool configured);
void maru_rgb_toggle_underglow(void);
void maru_rgb_next_underglow_hue(void);
void maru_rgb_toggle_keys(void);
// Task-context polling guard; not an atomic hardware fault interlock.
bool maru_rgb_can_flush(void);
