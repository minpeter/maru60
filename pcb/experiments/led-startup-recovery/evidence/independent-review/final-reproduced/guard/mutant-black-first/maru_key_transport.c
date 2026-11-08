// SPDX-License-Identifier: GPL-2.0-or-later
// Independent PIO/DMA state, buffer and semaphore per physical chain.
#define WS2812_DI_PIN GP20
#define WS2812_LED_COUNT MARU_KEY_LED_COUNT
#define ws2812_init maru_key_init
#define ws2812_set_color maru_key_set_color
#define ws2812_set_color_all maru_key_set_color_all
#define ws2812_flush maru_key_flush
#define ws2812_leds maru_key_leds
#define MARU_READY maru_key_ready
#define MARU_STOP maru_key_stop
#define MARU_RESUME maru_key_resume
#undef WS2812_T1H
#undef WS2812_T1L
#undef WS2812_TRST_US
#define WS2812_T1H 900
#define WS2812_T1L 300
#define WS2812_TRST_US 250
#include "maru_ws2812_transport.inc"
