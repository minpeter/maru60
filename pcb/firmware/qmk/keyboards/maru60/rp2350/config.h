// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "report_sync.h"
#if QMK_REPORT_SYNC_API_VERSION != 1
#    error Unsupported report synchronization API
#endif
#define KEEP_REPORT_STATE_SYNCHRONIZED
#include "maru_via_schema.h"
#include "maru_led_counts.h"
#define RP_FLASH_SIZE (4U * 1024U * 1024U)
#define USB_MAX_POWER_CONSUMPTION 500
#define RGB_MATRIX_LED_COUNT (MARU_KEY_LED_COUNT + MARU_UG_LED_COUNT)
#define RGB_MATRIX_MAXIMUM_BRIGHTNESS 64
#define RGB_MATRIX_DEFAULT_VAL 16
#define RGB_MATRIX_DEFAULT_MODE RGB_MATRIX_SOLID_COLOR
#define RGB_MATRIX_SLEEP
#define RGB_MATRIX_LED_FLUSH_LIMIT 16
#define ENABLE_RGB_MATRIX_BREATHING
#define ENABLE_RGB_MATRIX_CYCLE_ALL
#define ENABLE_RGB_MATRIX_SOLID_REACTIVE_SIMPLE
// Both independent chains use exact OPSCO SK6805-EC15-001 Rev A/1 timing.
#define WS2812_T0H 300
#define WS2812_T0L 900
#define WS2812_T1H 900
#define WS2812_T1L 300
#define WS2812_TRST_US 250
// Deliberate bring-up interlock. Set to 1 only in a qualified build after
// measured non-LED rail, hardware limiter, inrush and suspend tests pass.
// An enabled build must also define MARU60_LED_POWER_SETTLE_MS and a nonempty
// MARU60_LED_POWER_SETTLE_REPORT string naming bench evidence for that interval.
// No default interval is provided: /FAULT is not LED-rail power-good, and a
// datasheet turn-on time under another load does not qualify this board.
#ifndef MARU60_LED_POWER_QUALIFIED
#    define MARU60_LED_POWER_QUALIFIED 0
#endif

// pid.codes1209:0001/0002 are SHARED PRIVATE IN-HOUSE TEST IDs only.
// NOT unique; MUST NOT be used on redistributed/sold/manufactured devices.
// https://pid.codes/1209/0001/ and https://pid.codes/1209/0002/
// Default build remains prototypeFEED; neither default nor private-test IDs
// constitute a production allocation. Select an allocated ID before manufacture.
#ifdef MARU60_PRIVATE_TEST_IDS
#    undef VENDOR_ID
#    undef PRODUCT_ID
#    define VENDOR_ID 0x1209
#    if MARU60_LAYOUT_HHKB
#        define PRODUCT_ID 0x0002
#    else
#        define PRODUCT_ID 0x0001
#    endif
#endif

// Fresh/reset EEPROM only. Preserve an existing user-selected 6KRO setting.
#define NKRO_DEFAULT_ON true

// Matrix read delay, in CPU cycles after a row is driven low. QMK's default is
// CPU_CLOCK / 4 MHz = 37 cycles (247 ns at 150 MHz). With all 15 keys of one
// row held and the row pin at its data-sheet limit, the last column of the
// order-candidate board is valid after 228 ns at 27 C and 250 ns at 0 C
// (qa/signal-integrity/REPORT.md of the order candidate). 120 cycles is
// 0.8 us. wait_cpuclock() handles 1..135 only: a larger value waits 6 cycles.
#define GPIO_INPUT_PIN_DELAY 120
#if GPIO_INPUT_PIN_DELAY < 1 || GPIO_INPUT_PIN_DELAY > 135
#    error GPIO_INPUT_PIN_DELAY must be 1..135 for wait_cpuclock()
#endif
