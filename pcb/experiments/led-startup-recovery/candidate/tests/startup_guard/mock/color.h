#pragma once
#include <stdint.h>
typedef struct { uint8_t r,g,b; } RGB;
typedef struct { uint8_t h,s,v; } HSV;
RGB hsv_to_rgb(HSV value);
