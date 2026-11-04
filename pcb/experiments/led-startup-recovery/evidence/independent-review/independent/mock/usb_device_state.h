#pragma once
enum { USB_DEVICE_STATE_UNCONFIGURED, USB_DEVICE_STATE_CONFIGURED, USB_DEVICE_STATE_SUSPEND };
struct usb_device_state { unsigned configure_state; };
void notify_usb_device_state_change_user(struct usb_device_state);
