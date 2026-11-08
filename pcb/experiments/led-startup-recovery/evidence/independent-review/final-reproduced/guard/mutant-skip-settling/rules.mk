VIA_ENABLE = yes
DYNAMIC_KEYMAP_ENABLE = yes
RGB_MATRIX_ENABLE = yes
RGB_MATRIX_DRIVER = custom
RGBLIGHT_ENABLE = no
COMMON_VPATH += $(DRIVER_PATH)/led
SRC += maru_key_transport.c maru_ug_transport.c maru_rgb.c maru60.c led_config.c
OPT_DEFS += -DRP_DMA_REQUIRED=TRUE -DRP_PIO_REQUIRED=TRUE

# Bench-only clock-gating experiment; NOT USB power qualification.
ifeq ($(strip $(MARU60_SUSPEND_EXPERIMENT)),yes)
    OPT_DEFS += -DMARU60_SUSPEND_EXPERIMENT=1 -DPORT_ENABLE_WFI_IDLE=TRUE
    SRC += maru_suspend.c
endif

SRC += maru_layout.c

# Explicit opt-in ONLY for in-house testing; shared IDs forbid manufacture/distribution.
ifeq ($(strip $(MARU60_PRIVATE_TEST_IDS)),yes)
    OPT_DEFS += -DMARU60_PRIVATE_TEST_IDS=1
endif

# Compiled bitmap report; boot protocol still falls back to 6KRO.
NKRO_ENABLE = yes

SRC += maru_report_sync.c
