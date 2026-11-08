// Independent reviewer fixture; real maru_rgb.c + maru60.c; all hardware mocked.
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "maru_rgb.h"
#include "rgb_matrix_drivers.h"
#include "color.h"
#include "usb_device_state.h"
void keyboard_pre_init_kb(void);
void housekeeping_task_kb(void);
void suspend_power_down_kb(void);
void notify_usb_device_state_change_kb(struct usb_device_state);
bool shutdown_kb(bool);
uint32_t maru_layout_options;
static uint32_t now, enabled_at;
static unsigned epochs, calls[2], resumes[2], first[2], suspend_calls;
static bool en, running[2], fault_n=true, health[2]={true,true}, configured;
static RGB pixels[2][MARU_KEY_LED_COUNT];
static const uint32_t duration=MARU60_LED_POWER_SETTLE_MS;
void gpio_set_pin_output(int p){(void)p;}
void gpio_set_pin_input_high(int p){(void)p;}
void gpio_write_pin_low(int p){if(p==GP22){assert(!running[0]&&!running[1]);en=false;}}
void gpio_write_pin_high(int p){assert(p==GP22&&!running[0]&&!running[1]);en=true;enabled_at=now;epochs++;}
bool gpio_read_pin(int p){return p==GP22?en:fault_n;}
uint32_t timer_read32(void){return now;}
uint32_t timer_elapsed32(uint32_t t){return now-t;}
RGB hsv_to_rgb(HSV h){return(RGB){h.v,h.v,h.v};}
static void flush(unsigned n){
 assert(MARU60_LED_POWER_QUALIFIED&&configured&&en&&fault_n&&health[0]&&health[1]);
 assert(running[0]&&running[1]&&maru_rgb_can_flush());
 assert((uint32_t)(now-enabled_at)>=duration);
 if(first[n]!=epochs){
  for(unsigned i=0;i<(n?MARU_UG_LED_COUNT:MARU_KEY_LED_COUNT);i++)assert(!pixels[n][i].r&&!pixels[n][i].g&&!pixels[n][i].b);
  first[n]=epochs;
 }
 calls[n]++;
}
#define CHAIN(name,n) \
void maru_##name##_init(void){} \
bool maru_##name##_ready(void){return health[n];} \
void maru_##name##_stop(void){running[n]=false;} \
void maru_##name##_resume(void){running[n]=true;resumes[n]++;} \
void maru_##name##_set_color(int i,uint8_t r,uint8_t g,uint8_t b){assert(i>=0&&i<(n?MARU_UG_LED_COUNT:MARU_KEY_LED_COUNT));pixels[n][i]=(RGB){r,g,b};} \
void maru_##name##_set_color_all(uint8_t r,uint8_t g,uint8_t b){for(unsigned i=0;i<(n?MARU_UG_LED_COUNT:MARU_KEY_LED_COUNT);i++)pixels[n][i]=(RGB){r,g,b};} \
void maru_##name##_flush(void){flush(n);}
CHAIN(key,0)
CHAIN(ug,1)
void keyboard_pre_init_user(void){}
void housekeeping_task_user(void){}
void suspend_power_down_user(void){assert(!en&&!running[0]&&!running[1]);suspend_calls++;}
bool process_record_user(uint16_t code,keyrecord_t*r){(void)code;(void)r;return true;}
bool shutdown_user(bool b){assert(!en&&!running[0]&&!running[1]);return b;}
void notify_usb_device_state_change_user(struct usb_device_state s){(void)s;}
void maru_report_sync_notify(struct usb_device_state s){(void)s;}
void maru_report_sync_task(void){}
uint32_t via_get_layout_options(void){return maru_layout_options;}
void via_set_layout_options(uint32_t v){maru_layout_options=v;}
static void usb(unsigned s){configured=s==USB_DEVICE_STATE_CONFIGURED;notify_usb_device_state_change_kb((struct usb_device_state){s});}
static void off(void){assert(!en&&!running[0]&&!running[1]&&!maru_rgb_can_flush());}
static void check_settle(void){
 unsigned a=calls[0],b=calls[1],r0=resumes[0],r1=resumes[1];
 assert(en&&!running[0]&&!running[1]&&!maru_rgb_can_flush());
 for(unsigned i=0;i<3;i++){housekeeping_task_kb();rgb_matrix_driver.flush();}
 now+=duration-1U;housekeeping_task_kb();rgb_matrix_driver.flush();
 assert(calls[0]==a&&calls[1]==b&&!running[0]&&!running[1]);
 now++;housekeeping_task_kb();assert(maru_rgb_can_flush());
 assert(calls[0]==a+1&&calls[1]==b+1&&resumes[0]==r0+1&&resumes[1]==r1+1);
 for(unsigned i=0;i<3;i++)housekeeping_task_kb();
 assert(calls[0]==a+1&&calls[1]==b+1);
 rgb_matrix_driver.flush();assert(calls[0]==a+2&&calls[1]==b+2);
}
int main(int argc,char**argv){
 assert(argc==2);const char *mode=argv[1];
 now=UINT32_MAX-duration/2U;
 // USB notification before RGB initialization cannot submit or assert EN.
 usb(USB_DEVICE_STATE_CONFIGURED);housekeeping_task_kb();assert(!en&&!epochs);usb(USB_DEVICE_STATE_UNCONFIGURED);
 keyboard_pre_init_kb();rgb_matrix_driver.init();off();
 rgb_matrix_driver.set_color(-1,255,255,255);rgb_matrix_driver.set_color(RGB_MATRIX_LED_COUNT,255,255,255);rgb_matrix_driver.set_color_all(99,101,103);
 for(unsigned i=0;i<4;i++){now+=1000;housekeeping_task_kb();rgb_matrix_driver.flush();off();}
 if(!strcmp(mode,"missing-key"))health[0]=false;
 if(!strcmp(mode,"missing-ug"))health[1]=false;
 if(!strcmp(mode,"cold-fault"))fault_n=false;
 usb(USB_DEVICE_STATE_CONFIGURED);housekeeping_task_kb();
 if(!MARU60_LED_POWER_QUALIFIED){off();assert(!epochs&&!calls[0]&&!calls[1]);puts("PASS independent defaultOFF wrapper path");return 0;}
 if(!strcmp(mode,"cold-fault")){
  off();fault_n=true;usb(USB_DEVICE_STATE_UNCONFIGURED);usb(USB_DEVICE_STATE_CONFIGURED);now+=duration;housekeeping_task_kb();off();puts("PASS independent cold-fault latch");return 0;
 }
 if(!strcmp(mode,"missing-key")||!strcmp(mode,"missing-ug")){off();health[0]=health[1]=true;housekeeping_task_kb();}
 if(!strcmp(mode,"settling-off")){
  now+=duration;maru_rgb_power_off();off();housekeeping_task_kb();assert(epochs==2);check_settle();
 } else if(!strcmp(mode,"settling-suspend")){
  now+=duration;usb(USB_DEVICE_STATE_SUSPEND);suspend_power_down_kb();off();
  now+=duration;housekeeping_task_kb();off();usb(USB_DEVICE_STATE_CONFIGURED);housekeeping_task_kb();assert(epochs==2);check_settle();
 } else {
  check_settle();
  if(!strcmp(mode,"active-suspend")){
   usb(USB_DEVICE_STATE_SUSPEND);suspend_power_down_kb();off();
   for(unsigned i=0;i<3;i++){now+=duration;housekeeping_task_kb();rgb_matrix_driver.flush();off();}
   usb(USB_DEVICE_STATE_CONFIGURED);housekeeping_task_kb();check_settle();assert(suspend_calls==1);
  } else if(!strcmp(mode,"active-fault")||!strcmp(mode,"active-health")){
   if(!strcmp(mode,"active-fault"))fault_n=false;else health[1]=false;
   assert(!maru_rgb_can_flush());off();fault_n=true;health[1]=true;
   for(unsigned i=0;i<3;i++){usb(USB_DEVICE_STATE_UNCONFIGURED);usb(USB_DEVICE_STATE_CONFIGURED);now+=duration;housekeeping_task_kb();rgb_matrix_driver.flush();off();}
  } else if(!strcmp(mode,"enable-loss")){
   en=false;assert(!maru_rgb_can_flush());off();housekeeping_task_kb();check_settle();
  } else if(!strcmp(mode,"zone-cycle")){
   maru_rgb_toggle_keys();assert(maru_rgb_can_flush());maru_rgb_toggle_underglow();off();now+=duration;housekeeping_task_kb();off();
   maru_rgb_toggle_underglow();housekeeping_task_kb();check_settle();
  } else if(!strcmp(mode,"shutdown")){assert(shutdown_kb(true));off();}
 }
 printf("PASS independent scenario=%s duration=%u epochs=%u calls=%u,%u\n",mode,duration,epochs,calls[0],calls[1]);return 0;
}
