// SPDX-License-Identifier: GPL-2.0-or-later
#include "maru_rgb.h"
#include "maru_rgb_policy.h"
#include "rgb_matrix_drivers.h"
#include "color.h"
#include "maru_layout_policy.h"
extern uint32_t maru_layout_options;
#include "wait.h"
#define MARU_LED_ENABLE GP22
#define MARU_LED_FAULT_N GP23
#define DECLARE_TRANSPORT(n) \
    void maru_##n##_init(void); \
    bool maru_##n##_ready(void); \
    void maru_##n##_stop(void); \
    void maru_##n##_resume(void); \
    void maru_##n##_set_color(int, uint8_t, uint8_t, uint8_t); \
    void maru_##n##_set_color_all(uint8_t, uint8_t, uint8_t); \
    void maru_##n##_flush(void)
DECLARE_TRANSPORT(key);
DECLARE_TRANSPORT(ug);
static RGB frame[RGB_MATRIX_LED_COUNT];
static bool initialized, configured, powered, fault_latched;
static bool keys_enabled = true, ug_enabled = true;
static uint8_t ug_hue = 160;
void maru_rgb_power_off(void) {
    // Stop data at LOW before removing the shared buffer/LED supply.
    if (initialized) { maru_key_stop(); maru_ug_stop(); }
    gpio_write_pin_low(MARU_LED_ENABLE);
    powered = false;
}
void maru_rgb_usb_configured(bool state) {
    configured = state;
    if (!state) maru_rgb_power_off();
    // Do not clear a fault on USB reset/resume: avoid repeated overload retry.
}
static bool transports_ready(void) { return maru_key_ready() && maru_ug_ready(); }
static void maru_init(void) {
    gpio_set_pin_output(MARU_LED_ENABLE); gpio_write_pin_low(MARU_LED_ENABLE);
    gpio_set_pin_input_high(MARU_LED_FAULT_N);
    maru_key_init(); maru_ug_init(); initialized = true;
    maru_rgb_power_off();
}
void maru_rgb_task(void) {
    if (!initialized) return;
    if (!gpio_read_pin(MARU_LED_FAULT_N)) fault_latched = true;
    bool requested = keys_enabled || ug_enabled;
    if (!maru_led_may_power(MARU60_LED_POWER_QUALIFIED, configured, transports_ready(), fault_latched, requested)) {
        if (powered) maru_rgb_power_off();
        return;
    }
    if (!powered) {
        maru_key_set_color_all(0,0,0); maru_ug_set_color_all(0,0,0);
        maru_key_resume(); maru_ug_resume();
        gpio_write_pin_high(MARU_LED_ENABLE); powered = true;
        wait_ms(2); // candidate settle delay; actual rail rise must be measured
        maru_key_flush(); maru_ug_flush();
        if (!transports_ready()) { fault_latched = true; maru_rgb_power_off(); }
    }
}
static void maru_set_color(int index, uint8_t r, uint8_t g, uint8_t b) {
    if (index < 0 || index >= RGB_MATRIX_LED_COUNT) return;
    frame[index] = (RGB){.r=r,.g=g,.b=b};
}
static void maru_set_color_all(uint8_t r, uint8_t g, uint8_t b) {
    for (int i=0; i<RGB_MATRIX_LED_COUNT; ++i) maru_set_color(i,r,g,b);
}
static void maru_flush(void) {
    maru_rgb_task();
    if (!powered) return;
    RGB output[RGB_MATRIX_LED_COUNT];
    RGB ug = hsv_to_rgb((HSV){.h=ug_hue,.s=255,.v=16});
    uint32_t sum = 0;
    for (int i=0; i<RGB_MATRIX_LED_COUNT; ++i) {
        output[i] = i < MARU_KEY_LED_COUNT ? (keys_enabled && maru_pixel_active(i,maru_layout_options) ? frame[i] : (RGB){0}) : (ug_enabled ? ug : (RGB){0});
        sum += output[i].r + output[i].g + output[i].b;
    }
    for (int i=0; i<RGB_MATRIX_LED_COUNT; ++i) {
        RGB c = output[i];
        c.r=maru_scale_channel(c.r,sum); c.g=maru_scale_channel(c.g,sum); c.b=maru_scale_channel(c.b,sum);
        if (i<MARU_KEY_LED_COUNT) maru_key_set_color(i,c.r,c.g,c.b); else maru_ug_set_color(i-MARU_KEY_LED_COUNT,c.r,c.g,c.b);
    }
    maru_key_flush(); maru_ug_flush();
        if (!transports_ready()) { fault_latched = true; maru_rgb_power_off(); }
}
void maru_rgb_toggle_underglow(void) { ug_enabled = !ug_enabled; }
void maru_rgb_next_underglow_hue(void) { ug_hue += 16; }
void maru_rgb_toggle_keys(void) { keys_enabled = !keys_enabled; }
const rgb_matrix_driver_t rgb_matrix_driver = {.init=maru_init,.set_color=maru_set_color,.set_color_all=maru_set_color_all,.flush=maru_flush};
