#pragma once
#include <stdbool.h>
#include <stdint.h>
typedef struct { volatile uint32_t SLEEP_EN0, SLEEP_EN1; } mock_clocks_t;
extern mock_clocks_t mock_clocks;
#define CLOCKS (&mock_clocks)
#define __DSB() ((void)0)
