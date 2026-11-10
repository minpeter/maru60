// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "maru_report_sync.h"
#include "report_sync.h"
#include <stdatomic.h>
#include <stdint.h>
#if QMK_REPORT_SYNC_API_VERSION != 1 || !defined(KEEP_REPORT_STATE_SYNCHRONIZED)
#    error Maru report sync requires the pinned opt-in QMK report synchronization patch
#endif
#if ATOMIC_INT_LOCK_FREE != 2
#    error Report notification counters must be lock-free in USB callback context
#endif
static _Atomic(uint32_t) requested_generation;
static _Atomic(uint32_t) observed_state = UINT32_MAX;
static uint32_t serviced_generation;
void maru_report_sync_notify(struct usb_device_state state) {
    // Callback context: lock-free bookkeeping only, no sends/EEPROM/key clears.
    uint32_t packed = ((uint32_t)state.protocol << 8) | (uint32_t)state.configure_state;
    if (atomic_exchange_explicit(&observed_state, packed, memory_order_relaxed) != packed) {
        atomic_fetch_add_explicit(&requested_generation, 1, memory_order_release);
    }
}
void maru_report_sync_task(void) {
    // Acknowledge the exact observed request only. An interrupt before/during/
    // after the send increments requested_generation and survives for next time.
    uint32_t request = atomic_load_explicit(&requested_generation, memory_order_acquire);
    if (request != serviced_generation && usb_device_state_get_configure_state() == USB_DEVICE_STATE_CONFIGURED) {
        send_keyboard_report_force();
        serviced_generation = request;
    }
}
