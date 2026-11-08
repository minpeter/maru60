#pragma once
#include <stdint.h>
#define NO_LED 255
struct led_config_mock { uint8_t matrix_co[5][15]; };
extern struct led_config_mock g_led_config;
