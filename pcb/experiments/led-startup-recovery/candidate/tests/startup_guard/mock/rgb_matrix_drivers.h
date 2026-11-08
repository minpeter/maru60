#pragma once
#include <stdint.h>
typedef struct {
    void (*init)(void);
    void (*set_color)(int,uint8_t,uint8_t,uint8_t);
    void (*set_color_all)(uint8_t,uint8_t,uint8_t);
    void (*flush)(void);
} rgb_matrix_driver_t;
extern const rgb_matrix_driver_t rgb_matrix_driver;
