// SPDX-License-Identifier: GPL-2.0-or-later
// NEW recovery fixture. Real maru_rgb.c and extracted ws2812_flush are compiled;
// GPIO, timer, scheduling, packing, lifecycle and DMA registers are mocks.
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "maru_rgb.h"
#include "color.h"
#include "rgb_matrix_drivers.h"

uint32_t maru_layout_options;
static uint32_t now_ms, enable_time;
static bool en, fault_n=true, usb, healthy[2]={true,true}, running[2];
static bool zone_on[2]={true,true}, armed, injected, observe;
static unsigned epoch, first_epoch[2], resumes[2], flushes[2], dma[2];
static unsigned unsafe_dma, early_dma, nonblack_first, callbacks_after_cancel;
static unsigned packs[2], registers[2], current_chain, target_chain;
static const char *stage, *cause;
static RGB pixels[2][MARU_KEY_LED_COUNT];
static uint32_t WS2812_BUFFER[MARU_KEY_LED_COUNT];
static const void *state_machine=(void *)1, *dma_channel=(void *)1;
static const uint32_t RP_DMA_MODE_WS2812=0;
static bool transfer_failed;
#define WS2812_LED_COUNT (current_chain ? MARU_UG_LED_COUNT : MARU_KEY_LED_COUNT)
#define ws2812_leds pixels[current_chain]

static void cancel(void) {
    if (!strcmp(cause,"fault")) fault_n=false;
    else if (!strcmp(cause,"usb")) { usb=false;maru_rgb_usb_configured(false); }
    else if (!strcmp(cause,"transport")) { healthy[target_chain]=false;transfer_failed=true; }
    else if (!strcmp(cause,"enable")) en=false;
    else if (!strcmp(cause,"off")) maru_rgb_power_off();
    else if (!strcmp(cause,"policy")) {
        if (zone_on[0]) {maru_rgb_toggle_keys();zone_on[0]=false;}
        if (zone_on[1]) {maru_rgb_toggle_underglow();zone_on[1]=false;}
    } else abort();
}
static void event(const char *where,unsigned chain) {
    if (armed && !injected && !strcmp(stage,where) && target_chain==chain) {
        injected=true; cancel();
    }
}
static bool permitted(void) {
    return MARU60_LED_POWER_QUALIFIED && en && fault_n && usb && healthy[0] && healthy[1] && (zone_on[0]||zone_on[1]);
}
void gpio_set_pin_output(int pin) {(void)pin;}
void gpio_set_pin_input_high(int pin) {(void)pin;}
void gpio_write_pin_low(int pin) { assert(pin==GP22);assert(!running[0]&&!running[1]);en=false; }
void gpio_write_pin_high(int pin) { assert(pin==GP22);en=true;enable_time=now_ms;epoch++; }
bool gpio_read_pin(int pin) {return pin==GP22?en:fault_n;}
uint32_t timer_read32(void) {return now_ms;}
uint32_t timer_elapsed32(uint32_t before) {return now_ms-before;}
void wait_ms(uint16_t delay) {now_ms+=delay;event("settle",0);}
RGB hsv_to_rgb(HSV value) {event("render",0);return (RGB){value.v,0,0};}
static void sync_ws2812_transfer(void) {now_ms++;event("sync",current_chain);}
static uint32_t rgbw8888_to_u32(uint8_t r,uint8_t g,uint8_t b,uint8_t w) {
    (void)w;packs[current_chain]++;event("pack",current_chain);
    return ((uint32_t)g<<24)|((uint32_t)r<<16)|((uint32_t)b<<8);
}
static void dmaChannelSetSourceX(const void *c,uint32_t source) {(void)c;(void)source;registers[current_chain]++;event("source",current_chain);}
static void dmaChannelSetCounterX(const void *c,unsigned count) {(void)c;(void)count;registers[current_chain]++;event("counter",current_chain);}
static void dmaChannelSetModeX(const void *c,uint32_t mode) {(void)c;(void)mode;registers[current_chain]++;event("mode",current_chain);}
static void dmaChannelEnableX(const void *c) {
    (void)c;event("submit",current_chain);
    if (!permitted()||!running[current_chain]) unsafe_dma++;
    if ((uint32_t)(now_ms-enable_time)<7U) early_dma++;
    if (first_epoch[current_chain]!=epoch) {
        first_epoch[current_chain]=epoch;
        for(unsigned i=0;i<(unsigned)WS2812_LED_COUNT;i++)
            if (pixels[current_chain][i].r||pixels[current_chain][i].g||pixels[current_chain][i].b) {nonblack_first++;break;}
    }
    dma[current_chain]++;
}
#define ws2812_flush fixture_transport_flush
#include "transport_flush.inc"
#undef ws2812_flush
static void chain_flush(unsigned chain) {
    current_chain=chain;transfer_failed=!healthy[chain];flushes[chain]++;
    if (injected) callbacks_after_cancel++;
    event("entry",chain);fixture_transport_flush();
}
#define TRANSPORT(name,n) \
void maru_##name##_init(void){} \
bool maru_##name##_ready(void){return healthy[n];} \
void maru_##name##_stop(void){running[n]=false;} \
void maru_##name##_resume(void){running[n]=true;resumes[n]++;event("resume",n);} \
void maru_##name##_set_color(int i,uint8_t r,uint8_t g,uint8_t b){pixels[n][i]=(RGB){r,g,b};event("color",n);} \
void maru_##name##_set_color_all(uint8_t r,uint8_t g,uint8_t b){for(unsigned i=0;i<(n?MARU_UG_LED_COUNT:MARU_KEY_LED_COUNT);i++)pixels[n][i]=(RGB){r,g,b};} \
void maru_##name##_flush(void){chain_flush(n);}
TRANSPORT(key,0)
TRANSPORT(ug,1)
static void off(void) {assert(!en&&!running[0]&&!running[1]);}
static void begin(void) {
    rgb_matrix_driver.init();rgb_matrix_driver.set_color_all(40,20,10);
    usb=true;maru_rgb_usb_configured(true);rgb_matrix_driver.flush();
}
static void tick(unsigned ms) {now_ms+=ms;rgb_matrix_driver.flush();}
static void active(void) {tick(7);assert(dma[0]==2&&dma[1]==2);assert(en&&running[0]&&running[1]);}
static void restart(const char *why) {
    unsigned old0=dma[0],old1=dma[1],e=epoch;
    if (!strcmp(why,"usb")) {usb=false;maru_rgb_usb_configured(false);off();usb=true;maru_rgb_usb_configured(true);}
    else if (!strcmp(why,"policy")) {maru_rgb_toggle_keys();maru_rgb_toggle_underglow();off();maru_rgb_toggle_keys();maru_rgb_toggle_underglow();}
    else {maru_rgb_power_off();off();}
    rgb_matrix_driver.flush();assert(epoch==e+1&&en&&!running[0]&&!running[1]);
    tick(6);assert(dma[0]==old0&&dma[1]==old1);
    tick(1);assert(dma[0]==old0+2&&dma[1]==old1+2);
}
int main(int argc,char **argv) {
    assert(argc>=2);const char *mode=argv[1];
    observe=!strcmp(mode,"observe");
    if (!strcmp(mode,"wrap")||!strcmp(mode,"wrap_restart")) now_ms=UINT32_MAX-3U;
    if (observe) {
        assert(argc==3);stage="settle";cause=argv[2];target_chain=0;armed=true;
        begin();
    } else if (!strcmp(mode,"default_off")) {
        begin();
        for(unsigned i=0;i<32;i++){tick(UINT32_MAX/31U);usb=false;maru_rgb_usb_configured(false);usb=true;maru_rgb_usb_configured(true);}
        assert(MARU60_LED_POWER_QUALIFIED==0&&!epoch&&!flushes[0]&&!flushes[1]);off();
    } else if (!strcmp(mode,"normal")||!strcmp(mode,"wrap")) {
        begin();assert(en&&!running[0]&&!running[1]&&!flushes[0]&&!flushes[1]);
        tick(6);assert(!dma[0]&&!dma[1]);tick(1);assert(dma[0]==2&&dma[1]==2);
    } else if (!strcmp(mode,"restart")||!strcmp(mode,"wrap_restart")) {
        assert(argc==3);begin();active();for(unsigned i=0;i<3;i++)restart(argv[2]);
    } else if (!strcmp(mode,"resource")) {
        healthy[0]=false;begin();assert(!epoch&&!dma[0]&&!dma[1]);off();
        healthy[0]=true;rgb_matrix_driver.flush();active();
    } else if (!strcmp(mode,"latch")) {
        assert(argc==3);begin();stage="settle";cause=argv[2];target_chain=0;armed=true;event("settle",0);tick(7);off();
        fault_n=true;healthy[0]=true;usb=false;maru_rgb_usb_configured(false);usb=true;maru_rgb_usb_configured(true);tick(100);
        off();assert(!dma[0]&&!dma[1]);
    } else {
        assert(!strcmp(mode,"cancel")&&argc==6);
        stage=argv[2];cause=argv[3];target_chain=(unsigned)atoi(argv[4]);bool is_active=atoi(argv[5]);assert(target_chain<2);
        begin();if(is_active)active();
        unsigned old_dma[2]={dma[0],dma[1]},old_flush[2]={flushes[0],flushes[1]};
        unsigned old_pack[2]={packs[0],packs[1]},old_reg[2]={registers[0],registers[1]};
        armed=true;
        if (!strcmp(stage,"settle")) {event("settle",target_chain);tick(7);}
        else tick(is_active?0:7);
        assert(injected);
        if (!strcmp(stage,"settle") && !strcmp(cause,"off")) {
            // Direct OFF is non-latching: the next task may start a NEW epoch,
            // but must not reuse the old elapsed time or transmit immediately.
            assert(en&&!running[0]&&!running[1]&&epoch==2);
            assert(dma[0]==old_dma[0]&&dma[1]==old_dma[1]);
            armed=false;tick(6);assert(dma[0]==old_dma[0]&&dma[1]==old_dma[1]);
            tick(1);assert(dma[0]==old_dma[0]+2&&dma[1]==old_dma[1]+2);
            goto finish;
        }
        off();
        bool in_transport=strcmp(stage,"settle")&&strcmp(stage,"resume")&&strcmp(stage,"render")&&strcmp(stage,"color");
        unsigned allowed_key=(in_transport&&target_chain==1)?1:0;
        assert(dma[0]==old_dma[0]+allowed_key&&dma[1]==old_dma[1]);
        if(in_transport){assert(flushes[0]==old_flush[0]+1&&flushes[1]==old_flush[1]+(target_chain==1));}
        else {assert(flushes[0]==old_flush[0]&&flushes[1]==old_flush[1]);}
        if(!strcmp(stage,"entry")||!strcmp(stage,"sync")){
            assert(packs[target_chain]==old_pack[target_chain]);assert(registers[target_chain]==old_reg[target_chain]);
        }
    }
finish:
    if(!observe){assert(!unsafe_dma&&!early_dma&&!nonblack_first);}
    printf("RESULT mode=%s qualification=%d EN=%d epochs=%u key_calls=%u ug_calls=%u dma_key=%u dma_ug=%u callbacks_after_cancel=%u unsafe_mock_dma=%u early_mock_dma=%u nonblack_first=%u\n",mode,MARU60_LED_POWER_QUALIFIED,en,epoch,flushes[0],flushes[1],dma[0],dma[1],callbacks_after_cancel,unsafe_dma,early_dma,nonblack_first);
    return 0;
}
