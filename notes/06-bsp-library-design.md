# `WaveShare_3.49_BSP` — shared board-support and compositor library (design)

Status: proposed (see decision D5 in `05-decisions.md`). Licence: Apache-2.0.

## Why
Four firmwares (Launcher, Bruce, Meshtastic, Marauder) plus future ports all
need the same bring-up and the same full-frame QSPI flush. Writing it once:
- keeps the hard-won hardware facts (`01-hardware-reference.md`) in one place;
- keeps each firmware fork's diff small (one board folder plus a `lib_deps` line).

The Launcher is the exception. It uses its own DisplayDrivers stack and keeps
board code in `boards/<env>/interface.cpp` (repo rule: no new libraries for one
board). It reuses the BSP's **knowledge**, not necessarily its code.

## Layout
```
WaveShare_3.49_BSP/
  library.json            # PlatformIO lib manifest, frameworks: arduino, espidf
  LICENSE                 # Apache-2.0
  src/
    ws349_board.h/.c      # ws349_board_begin(): I2C0, TCA9554, SYS_EN, LCD_RST, GPIO42
    ws349_expander.h/.c   # tiny TCA9554 (dir write + readback, set/clear by mask)
    ws349_backlight.h/.c  # LEDC 50 kHz inverted + BL_EN, floor clamp
    ws349_panel.h/.c      # AXS15231B QSPI init + full-frame chunked DMA flush (from Espressif Apache code)
    ws349_touch.h/.c      # AXS15231B I2C1 @0x3B read, flip-aware mapping
    ws349_buttons.h/.c    # BOOT/PWR click/double/hold per D2 (optional)
    ws349_power.h/.c      # battery mV/% (18650 curve), power-off
    ws349_compositor.h/.c # virtual screen(s) -> 640x172 frame, modes A-E, rail chrome, input inverse-map
  adapters/
    arduino_gfx/          # Arduino_Canvas-backed output (Bruce, Meshtastic)
    tft_espi/             # full-frame TFT_eSprite in PSRAM + push (Marauder)
    lovyangfx/            # Panel_FrameBuffer-style (later, if needed)
  examples/
    01_liveness/          # solid fills + serial [STATE] lines for validate_cycle.py
    02_touch_buttons/     # prints mapped events
    03_compositor_modes/  # 320x172, 240x135@2x, 320x240 fold, pan/zoom demos
```

## Core API (C, so every framework can use it)
```c
esp_err_t ws349_board_begin(void);              // must be first; latches power
esp_err_t ws349_panel_begin(void);              // reset via EXIO5, init, black frame, BL on
void      ws349_panel_flush(const uint16_t *fb640x172); // full frame, blocks until DMA done
void      ws349_set_flip(bool flip180);
bool      ws349_touch_read(int16_t *x, int16_t *y);     // panel coords, flip applied
void      ws349_backlight_set(uint8_t pct);             // clamped to visible floor
uint16_t  ws349_battery_mv(void);
void      ws349_power_off(void);

// compositor
typedef enum { WS349_NATIVE, WS349_WINDOW_RAIL, WS349_FOLD, WS349_VIEWPORT_RAIL, WS349_PANZOOM } ws349_mode_t;
uint16_t *ws349_vs_create(uint16_t w, uint16_t h, ws349_mode_t mode, uint8_t scale);
void      ws349_vs_dirty(void);                  // firmware drew something
void      ws349_vs_task_start(int core, int hz); // single bus owner; recompose only when dirty/moved
bool      ws349_vs_input(ws349_event_t *ev);     // touch->virtual coords or rail buttons
```

## Rules baked in
- One task owns the QSPI bus. Everything else posts "dirty" or "flip".
- No flush when nothing changed, to save current and avoid heat.
- RGB565 byte swap happens in compose, not in the firmware.
- `ws349_board_begin()` is idempotent and safe after a Launcher hand-off
  (the expander may already be configured).
- No IRAM_ATTR beyond the DMA-done ISR. DeskBar's IRAM is already 100%.
