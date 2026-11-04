// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include "usb_device_state.h"
void maru_report_sync_notify(struct usb_device_state state);
void maru_report_sync_task(void);
