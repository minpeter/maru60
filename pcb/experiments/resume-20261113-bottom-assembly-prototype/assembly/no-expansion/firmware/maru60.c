// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "maru_rgb.h"
#include "usb_device_state.h"
#include "maru_report_sync.h"
#include "via.h"
#include "maru_layout_policy.h"
#ifdef MARU60_SUSPEND_EXPERIMENT
void maru_suspend_enter(void);
void maru_suspend_leave(void);
#endif
void keyboard_pre_init_kb(void) {
    gpio_set_pin_output(GP22); gpio_write_pin_low(GP22);
    gpio_set_pin_output(GP20); gpio_write_pin_low(GP20);
    gpio_set_pin_output(GP21); gpio_write_pin_low(GP21);
    // No-expansion population only: these nets end at U1 and empty lands.
    // Preload LOW before enabling the output; never drive an attached module.
    gpio_write_pin_low(GP3); gpio_set_pin_output(GP3);
    gpio_write_pin_low(GP10); gpio_set_pin_output(GP10);
    gpio_write_pin_low(GP24); gpio_set_pin_output(GP24);
    gpio_write_pin_low(GP25); gpio_set_pin_output(GP25);
    gpio_write_pin_low(GP26); gpio_set_pin_output(GP26);
    gpio_write_pin_low(GP27); gpio_set_pin_output(GP27);
    keyboard_pre_init_user();
}
void notify_usb_device_state_change_kb(struct usb_device_state state) {
    maru_report_sync_notify(state);
#ifdef MARU60_SUSPEND_EXPERIMENT
    if (state.configure_state != USB_DEVICE_STATE_SUSPEND) maru_suspend_leave();
#endif
    maru_rgb_usb_configured(state.configure_state == USB_DEVICE_STATE_CONFIGURED);
    notify_usb_device_state_change_user(state);
}
void housekeeping_task_kb(void) {
    maru_report_sync_task();
    maru_rgb_task();
    housekeeping_task_user();
}
void suspend_power_down_kb(void) {
    maru_rgb_power_off();
    suspend_power_down_user();
#ifdef MARU60_SUSPEND_EXPERIMENT
    maru_suspend_enter();
#endif
}
bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if (!process_record_user(keycode, record)) return false;
    if (keycode == MARU_CAPS_OPTION || keycode == MARU_RSHIFT_OPTION) {
        if (record->event.pressed) {
            uint32_t bit=keycode==MARU_CAPS_OPTION?MARU_LAYOUT_CAPS_STEPPED:MARU_LAYOUT_RSHIFT_NORMAL;
            via_set_layout_options(maru_effective_options(via_get_layout_options() ^ bit));
        }
        return false;
    }
    if (keycode == MARU_UG_TOGGLE || keycode == MARU_UG_HUE || keycode == MARU_KEY_TOGGLE) {
        if (record->event.pressed) {
            if (keycode == MARU_UG_TOGGLE) maru_rgb_toggle_underglow();
            if (keycode == MARU_UG_HUE) maru_rgb_next_underglow_hue();
            if (keycode == MARU_KEY_TOGGLE) maru_rgb_toggle_keys();
        }
        return false;
    }
    return true;
}

bool shutdown_kb(bool jump_to_bootloader) {
    maru_rgb_power_off();
#ifdef MARU60_SUSPEND_EXPERIMENT
    maru_suspend_leave();
#endif
    return shutdown_user(jump_to_bootloader);
}
