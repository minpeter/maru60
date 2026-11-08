// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
// RP2350 datasheet SLEEP_EN0/1 tables621/622. Only unused peripheral endpoints.
// Preserve clocks for USB, timer/ticks, bus, all SRAM/XIP, GPIO/SIO, PLLs, watchdog.
#define MARU_SLEEP_GATE0 ((1UL<<30)|(1UL<<25)|(7UL<<18)|(3UL<<11)|(3UL<<9)|(3UL<<2))
#define MARU_SLEEP_GATE1 ((15UL<<22)|(1UL<<21)|15UL)
static inline uint32_t maru_sleep_mask0(uint32_t prior) { return prior & ~MARU_SLEEP_GATE0; }
static inline uint32_t maru_sleep_mask1(uint32_t prior) { return prior & ~MARU_SLEEP_GATE1; }
