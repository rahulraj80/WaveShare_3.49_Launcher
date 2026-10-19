# Port: ESP32 Marauder → 3.49" V2

Repo: `C:\Users\rahul\OpenCode\WaveShare_3.49_ESP32Marauder` (MIT, **Arduino IDE sketch**, branch `master`, shallow clone).
**Difficulty: highest. Port third.**

## Why it's hard
- **TFT_eSPI only**, drawing straight to the panel. There's no sprite,
  canvas or display abstraction, and TFT_eSPI has no QSPI AXS15231B driver.
- No embedded PlatformIO env (only a native unit-test env). Variants are
  selected with a `#define` in `configs.h` plus a copied `User_Setup_*.h`.
- Pixel-literal layouts tuned for 240×320 (`MenuFunctions.cpp:166,197,407-420,1195,1287,1317,1326`).
- Touch, the status bar and on-screen buttons all sit behind `#ifdef HAS_ILI9341`.
- Uses **hardware vertical scroll** for logs, which must be emulated.

## Presentation (this is your option 2)
Use the **Cardputer geometry (240×135 landscape)** as the virtual screen, at
**2× = 480×270**. Show a 480×172 viewport with a 160×172 navigation rail
(scroll up/down, select, back, position indicator) = **Mode C**.
- 2× makes Marauder's size-1 text about 2 mm tall, which is readable.
- Alternative if 2× scrolling annoys: Mode A at 1× (240×135 window plus a
  400 px rail), but the text will be small.

## Work items
1. Add a PlatformIO env for our board, or keep Arduino IDE with a documented
   recipe. Recommend PlatformIO for CI/release parity with the other forks.
2. `configs.h`: new `MARAUDER_WS349` variant cloned from
   `MARAUDER_CARDPUTER` (S3, 240×135, `C_BTN 0`, dedicated SD SPI). Set
   `SD_CS 38 / SD_MOSI 39 / SD_MISO 40 / SD_SCK 41`, which uses the existing
   `spiExt` path in `SDInterface.cpp:142-165`.
3. **Display redirect**: make `display_obj.tft` draw into a full-frame
   `TFT_eSprite` (240×135, PSRAM) and hand frames to the BSP compositor.
   `TFT_eSprite : TFT_eSPI`, so most calls compile unchanged. The likely
   minimal change is to swap the type at `Display.h:104` behind
   `#ifdef MARAUDER_WS349`, then fix the methods sprites lack.
4. Emulate `scrollScreenBuffer()` / TOP_FIXED_AREA scrolling in the sprite.
5. Input: new `HAS_WS349_TOUCH` path in `Display::updateTouch()`. Touch goes
   through the compositor's inverse map to virtual coordinates. Refactor the
   `HAS_ILI9341` gates into a capability flag. BOOT/PWR per D2 via `Switches`
   (hold_lim 600 ms).
6. `setup()`: BSP board begin before `display_obj.init()`.
7. 16 MB partition scheme with app plus SPIFFS (EvilPortal assets).
8. Keep the MIT notice. The BSP is Apache-2.0, which is compatible.
