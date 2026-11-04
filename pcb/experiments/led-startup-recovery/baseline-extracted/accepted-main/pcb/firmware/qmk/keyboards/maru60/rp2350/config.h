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
