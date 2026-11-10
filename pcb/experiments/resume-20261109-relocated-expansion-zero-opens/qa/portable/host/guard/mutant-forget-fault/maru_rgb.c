// SPDX-License-Identifier: GPL-2.0-or-later
#include "maru_rgb.h"
#include "maru_rgb_policy.h"
#include "rgb_matrix_drivers.h"
#include "color.h"
#include "maru_layout_policy.h"
extern uint32_t maru_layout_options;
#include "timer.h"
#define MARU_LED_ENABLE GP22
#define MARU_LED_FAULT_N GP23

#if MARU60_LED_POWER_QUALIFIED
#    if !defined(MARU60_LED_POWER_SETTLE_MS) || !defined(MARU60_LED_POWER_SETTLE_REPORT)
#        error Qualified LED power requires a measured settling interval and qualification report
#    elif MARU60_LED_POWER_SETTLE_MS < 1 || MARU60_LED_POWER_SETTLE_MS > 0x7FFFFFFF
#        error LED power settling interval must be in 1..2147483647 milliseconds
#    endif
_Static_assert(sizeof("" MARU60_LED_POWER_SETTLE_REPORT) > 1, "Missing LED settling qualification report");
#    define MARU_LED_SETTLE_MS MARU60_LED_POWER_SETTLE_MS
#else
// No enabled production timing is supplied while qualification remains OFF.
#    define MARU_LED_SETTLE_MS 0U
#endif

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
static bool initialized, configured, fault_latched;
static enum { MARU_LED_OFF, MARU_LED_SETTLING, MARU_LED_ACTIVE } power_state;
static uint32_t settle_started;
static bool keys_enabled = true, ug_enabled = true;
static uint8_t ug_hue = 160;
void maru_rgb_power_off(void) {
    // Invalidate pending startup before stopping data LOW and lowering EN.
    power_state = MARU_LED_OFF;
    if (initialized) { maru_key_stop(); maru_ug_stop(); }
    gpio_write_pin_low(MARU_LED_ENABLE);
}
void maru_rgb_usb_configured(bool state) {
    configured = state;
    if (!state) maru_rgb_power_off();
    // Do not clear a fault on USB reset/resume: avoid repeated overload retry.
}
static bool transports_ready(void) { return maru_key_ready() && maru_ug_ready(); }
static bool power_allowed(void) {
    if (!initialized) return false;
    fault_latched = !gpio_read_pin(MARU_LED_FAULT_N);
    bool ready = transports_ready();
    if (power_state != MARU_LED_OFF && !ready) fault_latched = true;
    return maru_led_may_power(MARU60_LED_POWER_QUALIFIED, configured, ready,
                              fault_latched, keys_enabled || ug_enabled);
}
static bool recheck_power(void) {
    // EN readback is not rail-ready. A direct OFF cancels even if policy is ON.
    if (!power_allowed() || power_state == MARU_LED_OFF || !gpio_read_pin(MARU_LED_ENABLE)) {
        if (power_state != MARU_LED_OFF) maru_rgb_power_off();
        return false;
    }
    return true;
}
bool maru_rgb_can_flush(void) {
    return recheck_power() && power_state == MARU_LED_ACTIVE;
}
static void flush_transports(void) {
    if (!maru_rgb_can_flush()) return;
    maru_key_flush();
    if (!maru_rgb_can_flush()) return;
    maru_ug_flush();
    (void)maru_rgb_can_flush();
}
static void maru_init(void) {
    gpio_set_pin_output(MARU_LED_ENABLE); gpio_write_pin_low(MARU_LED_ENABLE);
    gpio_set_pin_input_high(MARU_LED_FAULT_N);
    maru_key_init(); maru_ug_init(); initialized = true;
    maru_rgb_power_off();
}
void maru_rgb_task(void) {
    if (!power_allowed()) {
        if (power_state != MARU_LED_OFF) maru_rgb_power_off();
        return;
    }
    if (power_state == MARU_LED_OFF) {
        // Start every enable epoch stopped and black; no blocking rail delay.
        maru_key_stop(); maru_ug_stop();
        maru_key_set_color_all(0,0,0); maru_ug_set_color_all(0,0,0);
        if (!power_allowed()) return;
        gpio_write_pin_high(MARU_LED_ENABLE);
        settle_started = timer_read32();
        power_state = MARU_LED_SETTLING;
        (void)recheck_power();
        return;
    }
    if (!recheck_power() || power_state != MARU_LED_SETTLING) return;
#if MARU60_LED_POWER_QUALIFIED
    if (timer_elapsed32(settle_started) < MARU_LED_SETTLE_MS) return;
#endif
    maru_key_resume();
    if (!recheck_power()) return;
    maru_ug_resume();
    if (!recheck_power()) return;
    power_state = MARU_LED_ACTIVE;
    flush_transports(); // Black is submitted first, separately guarding chains.
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
    if (!maru_rgb_can_flush()) return;
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
    flush_transports();
}
void maru_rgb_toggle_underglow(void) {
    ug_enabled = !ug_enabled;
    if (!keys_enabled && !ug_enabled) maru_rgb_power_off();
}
void maru_rgb_next_underglow_hue(void) { ug_hue += 16; }
void maru_rgb_toggle_keys(void) {
    keys_enabled = !keys_enabled;
    if (!keys_enabled && !ug_enabled) maru_rgb_power_off();
}
const rgb_matrix_driver_t rgb_matrix_driver = {.init=maru_init,.set_color=maru_set_color,.set_color_all=maru_set_color_all,.flush=maru_flush};
