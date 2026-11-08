// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
// Requires the hash-guarded patch in pcb/firmware/qmk/patches/.
#include "via_eeprom_schema.h"
#if QMK_VIA_EEPROM_SCHEMA_API_VERSION != 1
#    error Unsupported VIA EEPROM schema API
#endif
#ifndef MARU60_LAYOUT_HHKB
#    define MARU60_LAYOUT_HHKB 0
#endif
// Bump for incompatible EEPROM addresses/meanings/options, NOT build dates,
// GPIO-only routing changes or revised default keycodes. Never reuse old IDs.
#define MARU60_VIA_SCHEMA_VERSION 2UL
#define MARU60_VIA_SCHEMA_FAMILY 0x60UL
#define VIA_EEPROM_SCHEMA_ID ((0x4DUL << 16) | ((MARU60_VIA_SCHEMA_FAMILY + MARU60_LAYOUT_HHKB) << 8) | MARU60_VIA_SCHEMA_VERSION)
