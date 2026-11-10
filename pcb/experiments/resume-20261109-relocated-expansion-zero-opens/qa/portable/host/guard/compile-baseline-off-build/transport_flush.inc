void ws2812_flush(void) {
    if (state_machine == NULL || dma_channel == NULL || transfer_failed) return;
    sync_ws2812_transfer();
    if (transfer_failed) return;

    for (int i = 0; i < WS2812_LED_COUNT; i++) {
#if defined(WS2812_RGBW)
        WS2812_BUFFER[i] = rgbw8888_to_u32(ws2812_leds[i].r, ws2812_leds[i].g, ws2812_leds[i].b, ws2812_leds[i].w);
#else
        WS2812_BUFFER[i] = rgbw8888_to_u32(ws2812_leds[i].r, ws2812_leds[i].g, ws2812_leds[i].b, 0);
#endif
    }

    dmaChannelSetSourceX(dma_channel, (uint32_t)WS2812_BUFFER);
    dmaChannelSetCounterX(dma_channel, WS2812_LED_COUNT);
    dmaChannelSetModeX(dma_channel, RP_DMA_MODE_WS2812);
    dmaChannelEnableX(dma_channel);
}
