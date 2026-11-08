#pragma once
#include <stdbool.h>
#include <stdint.h>
#define QK_KB_0 0x7E00
#define GP20 20
#define GP21 21
#define GP22 22
#define GP23 23
#include "config.h"
typedef struct { struct { bool pressed; } event; } keyrecord_t;
void gpio_set_pin_output(int);
void gpio_set_pin_input_high(int);
void gpio_write_pin_low(int);
void gpio_write_pin_high(int);
bool gpio_read_pin(int);
void keyboard_pre_init_user(void);
void housekeeping_task_user(void);
void suspend_power_down_user(void);
bool process_record_user(uint16_t,keyrecord_t*);
bool shutdown_user(bool);
