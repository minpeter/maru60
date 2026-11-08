// SPDX-License-Identifier: GPL-2.0-or-later
// Independent PIO/DMA state, buffer and semaphore per physical chain.
#define WS2812_DI_PIN GP21
#define WS2812_LED_COUNT MARU_UG_LED_COUNT
#define ws2812_init maru_ug_init
#define ws2812_set_color maru_ug_set_color
#define ws2812_set_color_all maru_ug_set_color_all
#define ws2812_flush maru_ug_flush
#define ws2812_leds maru_ug_leds
#define MARU_READY maru_ug_ready
#define MARU_STOP maru_ug_stop
#define MARU_RESUME maru_ug_resume
#include "maru_ws2812_transport.inc"
