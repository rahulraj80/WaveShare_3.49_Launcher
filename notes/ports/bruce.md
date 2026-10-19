# Port: Bruce → 3.49" V2

Repo: `C:\Users\rahul\OpenCode\WaveShare_3.49_Bruce_firmware` (AGPL-3.0, PlatformIO, branch `main`).
**Difficulty: lowest of the three. Port first after the Launcher.**

## Why it's easy
- Bruce's `lib/HAL/display/` already has an **Arduino_GFX backend with QSPI
  (`TFT_DATABUS_N=1`) and `Arduino_AXS15231B` (`TFT_DISPLAY_DRIVER_N=22`)**
  (`ardgfx.h:36-44,202-203`, `ardgfx.cpp:56-127`). No board uses it yet.
- UI layout uses runtime `tftWidth/tftHeight` and handles 128 px heights, so
  172 is fine.
- The T-Display-S3 board (`boards/lilygo-t-display-s3/`, 320×170, 2 buttons,
  optional touch) is a near-twin, and its button scheme matches D2.

## Presentation
**Mode E (native 640×172)** through Bruce's own layout. Fall back to Mode A
(320×172 window plus rail) only if 640-wide layouts look broken. 640 px width
has never been tested in Bruce (the largest is 480), and there are 46 width or
height threshold comparisons in `src`.

## Work items
1. `boards/waveshare-esp32-s3-touch-lcd-349/` with `.ini`, `pins_arduino.h`
   and `interface.cpp`, copied from `_New-Device-Model` and the T-Display-S3.
   Use `custom_16Mb.csv` (4.4 MB app). Add Arduino_GFX to `lib_deps`.
   `FP/FM/FG = 1/2/3` to start.
2. **Full-frame canvas**: in `ardgfx.cpp`, when `TFT_FULLFRAME_CANVAS` is
   defined, wrap `_gfx` in an `Arduino_Canvas` (PSRAM) and flush from a
   ≤30 Hz task when dirty. Guard it so other boards are untouched.
3. Verify `Arduino_AXS15231B` against our init: 40 MHz, mode 3, no RASET,
   reset via expander (`TFT_RST=-1`). Expect a fix here, as in the Launcher's R1.
4. `_setup_gpio()` (runs before `tft.init()`, `main.cpp:448-520`):
   TCA9554 via plain `Wire` writes (Bruce's `io_expander.h` only knows
   AW9523/PCA9555), SYS_EN, LCD_RST pulse, GPIO42 low.
5. Touch: hand-written AXS15231B reader on `Wire1` (17/18), modelled on
   `boards/ES3C28P/interface.cpp:50+`. Feed `touchPoint` → `touchHeatMap()`.
6. Buttons: `ESP32_Button` on GPIO0 and GPIO16 per D2. `checkReboot()` =
   PWR hold 2 s → `powerOff()` (EXIO6←0).
7. `getBattery()`: ADC GPIO4 ×3, 18650 curve. `_setBrightness()`: inverted LEDC + BL_EN.
8. Add a "Reboot to Launcher" item (Bruce has no Launcher hand-back today).
9. Build a full (not LITE) version: we have 16 MB, and the Launcher can give
   it 4.4 MB.

## Peripherals Bruce expects that we lack
CC1101, NRF24, IR TX/RX, GPS, LoRa. These menus must be hidden via flags or
wired to the 22-pin header later. RF modules are a separate decision.
