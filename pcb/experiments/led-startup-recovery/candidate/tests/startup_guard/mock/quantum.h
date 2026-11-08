#pragma once
#include <stdbool.h>
#include <stdint.h>
#define QK_KB_0 0x7E00
#define GP22 22
#define GP23 23
#include "config.h"
void gpio_set_pin_output(int pin);
void gpio_set_pin_input_high(int pin);
void gpio_write_pin_low(int pin);
void gpio_write_pin_high(int pin);
bool gpio_read_pin(int pin);
