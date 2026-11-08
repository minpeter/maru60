// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
#define MARU_LAYOUT_CAPS_STEPPED 1UL
#define MARU_LAYOUT_RSHIFT_NORMAL 2UL
#ifndef MARU60_LAYOUT_HHKB
#define MARU60_LAYOUT_HHKB 0
#endif
static inline uint32_t maru_effective_options(uint32_t value) { return MARU60_LAYOUT_HHKB ? value & ~MARU_LAYOUT_RSHIFT_NORMAL : value; }
static inline bool maru_pixel_active(unsigned i,uint32_t options) {
 options=maru_effective_options(options);
 if(i==29) return !(options & MARU_LAYOUT_CAPS_STEPPED);
 if(i==30) return options & MARU_LAYOUT_CAPS_STEPPED;
 if(i==45) return !(options & MARU_LAYOUT_RSHIFT_NORMAL);
 if(i==43) return !(options & MARU_LAYOUT_RSHIFT_NORMAL);
 if(i==44) return options & MARU_LAYOUT_RSHIFT_NORMAL;
 if(i==57) return !MARU60_LAYOUT_HHKB;
 if(i==63) return !MARU60_LAYOUT_HHKB;
 if(i==58) return MARU60_LAYOUT_HHKB;
 if(i==62) return MARU60_LAYOUT_HHKB;
 return true;
}
