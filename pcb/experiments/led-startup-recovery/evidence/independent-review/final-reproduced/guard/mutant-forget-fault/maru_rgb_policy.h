// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdbool.h>
#include <stdint.h>
// A numeric PWM budget, NOT a guaranteed electrical current bound.
#define MARU60_PWM_SUM_LIMIT 1020U
static inline bool maru_led_may_power(bool qualified, bool configured, bool ready, bool latched_fault, bool requested) {
    return qualified && configured && ready && !latched_fault && requested;
}
static inline uint8_t maru_scale_channel(uint8_t value, uint32_t sum) {
    return sum > MARU60_PWM_SUM_LIMIT ? ((uint32_t)value * MARU60_PWM_SUM_LIMIT) / sum : value;
}
