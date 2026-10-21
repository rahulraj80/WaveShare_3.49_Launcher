# Port: Meshtastic → 3.49" V2

Repo: `C:\Users\rahul\OpenCode\WaveShare_3.49_Meshtastic_firmware` (GPL-3.0, PlatformIO, branch `develop`).
**Difficulty: medium. Port second.**

## The blocker that isn't about code
**The board has no LoRa radio.** Without one, Meshtastic boots with a
`NO_RADIO` critical error and runs as an isolated node (BLE, WiFi, MQTT and
UI still work). For real mesh use, an SX1262 module wired to the 22-pin
header is needed (`USE_SX1262` plus `LORA_*`/`SX126X_*` pins in `variant.h`;
hackaday-communicator is the template). **Decide before investing.**

## Presentation
**Mode E (native)** through BaseUI. `TFTDisplay` renders the OLED-style UI at
any `TFT_WIDTH × TFT_HEIGHT` without scaling. 640×172 counts as "High"
resolution. The fixed ArialMT 10/16/24 fonts are readable at our ppi.
MUI (device-ui/LVGL) has no 640×172 view. Skip MUI.

## Work items
1. `variants/esp32s3/waveshare_s3_touch_lcd_349/` with `variant.h`,
   `platformio.ini` and `variant_display.h`, plus `boards/<name>.json`
   (copy an OPI-PSRAM JSON such as `hackaday-communicator.json`).
   `default_16MB.csv`.
2. Display: use the **`VARIANT_DISPLAY_DRIVER`** hook
   (`src/graphics/TFTDisplay.cpp:1479-1487`). It's unused so far, so it's ours
   to define. Supply an LGFX-surface class backed by a PSRAM 640×172 shadow
   frame and a full-frame flush via the BSP. Needed because `TFTDisplay::display()`
   sends dirty row spans as partial windows, which this panel ignores.
   Precedent for an ultra-wide panel: `hackaday-communicator` (428×142,
   Arduino_GFX).
3. `earlyInitVariant()`: BSP board begin (SYS_EN first).
4. Touch: `VARIANT_TOUCHSCREEN 1` with the AXS15231B reader. Note that
   `USE_ARDUINO_GFX` disables touch in TFTDisplay, which is one more reason
   for the variant driver.
5. Buttons: `BUTTON_PIN 0` (single = next, long = select) and PWR via
   `CANCEL_BUTTON_PIN 16` (single = back). Reconcile its built-in 4 s shutdown
   long-press with D2 (2 s).
6. RTC PCF85063 and IMU QMI8658 are already supported by the I2C scan.
   Point them at I2C0 47/48.
7. Battery: `BATTERY_PIN 4`, `ADC_MULTIPLIER 3`.
8. "Reboot to Launcher" in the system menu.

## Boot loop fixed and verified (2026-10-21)
- Symptom: reset every 1-2 s with `reset_reason=intWatchdog` right after `TransmitHistory`; no display/touch logs.
- Cause: ESP32 defaults `HAS_RADIO=1` (`src/platform/esp32/architecture.h`). `main.cpp` therefore ran `SPI.begin(SCK=5, MISO=19, MOSI=27, CS=18)`, claiming FSPI/SPI2 (the AXS15231B QSPI host) and repurposing GPIO19 (USB D-) and GPIO18 (touch SCL). The QSPI `spi_bus_initialize` then aborted and USB died, so later output was lost.
- Fix: `#define HAS_RADIO 0` in `variant.h`; guard the ESP32 LoRa SPI init and `initLoRa()` with `#if HAS_RADIO` in `src/main.cpp`. No other functional change.
- Verified on hardware: boot reaches `Do TFT init`, panel init, frame alloc, flush task, `Applied screen brightness: 153`, `TouchScreen initialized`, `Display on`; 90 s capture with no reset; `NO_RADIO` critical error 3 is expected.
- Framebuffer screenshot (320x86 nearest-neighbour 3x): `C:\Users\rahul\AppData\Local\Temp\opencode\meshtastic_frame_3x.png` - green Meshtastic boot splash, `meshtastic.org` wordmark, UNSET region, clock. Colours correct after undoing the dump's extra byte swap.
- Final image: `meshta-final.bin` 2,316,896 B, SHA256 B9CF6D4AD2CB4043999541FD6DBFBCDD927C3A7BC7CF157C9B40538E81AE35F1, flashed to `meshta` @0xC60000.

