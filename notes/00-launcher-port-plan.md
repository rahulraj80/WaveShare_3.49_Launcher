# Plan: port the Launcher to the Waveshare ESP32-S3-Touch-LCD-3.49 V2

Env name: **`waveshare-esp32-s3-touch-lcd-349`**. The convention is
`<vendor>-<device>`, matching the existing `waveshare-esp32-s3-lcd-147`.
V1 is discontinued, so no `-v2` suffix. If V1 support is ever wanted, add
`-v1` then.

Process: `boards/NEW_BOARD_GUIDE.md`. Hardware facts: `01-hardware-reference.md`.

## What the repo already gives us

| Need | Existing support | Gap |
|---|---|---|
| AXS15231B QSPI display | DisplayDrivers `TFT_DATABUS_N=1`, `TFT_DISPLAY_DRIVER_N=22` (used by `CYD-3248W535C`, 320×480) | Unverified on a 172×640 panel that needs full-frame streaming with no RASET. Reset is on the expander. |
| Full-frame push | `USE_CANVAS=1` (PSRAM framebuffer, `display()` pushes all) | That matches this panel. Cost: about 220 KB per UI update, fine at 40 MHz. |
| Landscape | `ROTATION`, `TFT_CANVAS_ROTATE_OUTPUT=1` (t-watch-ultra) | Must confirm the rotation path doesn't depend on MADCTL. DeskBar never uses MADCTL. |
| Touch | HAL `TOUCH_CTRL_*` families | **No AXS15231B touch.** Add `TOUCH_CTRL_AXS15231B` modelled on `TOUCH_CTRL_AXS5106L` (`src/hal/inputs/touch.cpp`). |
| Backlight, inverted PWM | `hal_bright_set(..., {.invert=true})` | BL_EN on the expander must move with it, done in `interface.cpp`. |
| Battery | `ANALOG_BAT_PIN=4`, `ANALOG_BAT_MULTIPLIER` | Calibrate the multiplier against ×3 and the curve. |
| IO expander | none in the HAL; raw-Wire TCA9534 in `boards/elecrow-esp32s3-5in/interface.cpp` (register-compatible) | Board-local helper (about 30 lines). Only promote it to `src/hal/` if a second board needs it. |
| Power latch, power off | board-local pattern (`lilygo-t-deck`) | SYS_EN in `_setup_gpio`, EXIO6←0 in `powerOff()`. |
| SD | SPI SD support | Pins 38/39/40/41. DeskBar logs mount failures (see open questions). |
| 16 MB partitions | `support_files/custom_16Mb.csv` | none |

Init order is fine: `_setup_gpio()` runs before `tft->begin()`
(`src/main.cpp:265,280`). The expander latch and panel reset go there.

## Phases

### Phase 0: bring-up scaffolding
1. `git submodule update --init` (DisplayDrivers, Arduino_GFX, ...). They are
   empty in this checkout.
2. Build one known env (`m5stack-cardputer`) to confirm the toolchain.
3. Copy `boards/_New-Device-Model/` to `boards/waveshare-esp32-s3-touch-lcd-349/`.
   Register the env **commented out** in `platformio.ini` `default_envs` and
   `.github/workflows/main.yml`, in alphabetical order.
4. First build with `USE_DUMMY_TFT=1` and serial only. Prove boot, the
   SYS_EN latch (unplug USB and it stays alive) and the serial console.

### Phase 1: display
1. Flags: `TFT_DATABUS_N=1`, `TFT_DISPLAY_DRIVER_N=22`, CS 9, SCLK 10, D0–D3
   11–14, `TFT_RST=-1`, `TFT_TE=21`, `TFT_WIDTH=172`, `TFT_HEIGHT=640`,
   `USE_CANVAS=1`, landscape `ROTATION`, `TFT_IPS`/inversion as needed.
2. `_setup_gpio`: TCA9554 direction, then SYS_EN=1, BL_EN=0, LCD_RST pulse
   (30/250/30 ms), GPIO42 low with pull-down.
3. Liveness test with `validate_cycle.py` (solid fills) **before** judging
   anything else.
4. If driver 22 doesn't render: compare its init and write path against
   `TuneBar/src/axs15231b/esp_lcd_axs15231b.c` (0x2C/0x3C continuation, no
   RASET, 40 MHz, mode 3). Fix it **in DisplayDrivers upstream** (a bmorcelli
   repo) rather than forking locally, so the CYD-3248W535C gets the same driver.
5. Then BL_EN=1 after the first frame. Brightness through `hal_bright_*` with
   invert, clamped to the visible floor.

### Phase 2: touch and inputs
1. Add `TOUCH_CTRL_AXS15231B` to `src/hal/inputs/touch.cpp`,
   `src/hal/README.md` and the `_New-Device-Model` template. It uses a
   `TwoWire` on I2C1 (17/18) at 0x3B, polled (INT is on the expander), with
   swap/mirror from `DeviceTouch`. The same driver then serves `CYD-3248W535C`,
   which currently uses `bb_captouch` outside the HAL. Migrate it only if the
   board is available for testing.
2. Buttons per decision D2 (`05-decisions.md`): BOOT click/double/hold =
   Next/Prev/Select; PWR click = Back; PWR hold 2 s = power off.
3. Launcher-return key: `LAUNCHER_GPIO_KEYS='{{"BOOT", 0}}'` (as on
   `lilygo-t-display-c5`). Hardware-test the timing: press just after reset,
   not held through it.

### Phase 3: UI fit at 640×172 (shared code: every board is affected)
From the code survey:
- Main menu grid is fixed at 3 columns (`src/display.cpp:988-995`,
  `src/main.cpp:615-617`). Make the column count width-aware
  (e.g. `cols = max(3, tftWidth/160)`), keeping both places in sync.
  Check t-display-s3 and lcd-147 for regressions.
- "Short panel" checks use `panelHeight()`, the **native** height (640 here)
  (`display.cpp:405,594,1102,1232`, `webInterface.cpp:2204`). Use the rotated
  height. lcd-147 has the same latent bug.
- Touch keyboard (`mykeyboard.cpp`): fixed 36 px top buttons; hard-coded
  `fillRect(0,54,…)`; a 2 px offset between drawn keys and hit boxes
  (`:363` vs `:545`).
- Touch footer (`TouchFooter`) takes 20 of 172 px. Consider
  `HAS_TOUCH_NO_BORDER` plus side touch zones (left/right 80 px = prev/next)
  instead. The width is plentiful, the height is not.
- `FP/FM/FG`: start with 1/2/3, then judge on the panel against the ≥12–16 px
  readability rule in `02-display-adaptation-guide.md`.
- There is no swipe support anywhere. Adding horizontal swipe = prev/next in
  `touchHeatMap` would help every touch board. Optional.

### Phase 4: power, battery, SD, polish
- `powerOff()`: backlight off, then EXIO6←0. `getBattery()` via ADC ×3.
- SD over SPI 38–41. Test mount with a known-good FAT32 card.
- `connections.md` filled in from `01-hardware-reference.md`.
- "Flip 180°" setting, default off, 0°/180° only (D4). Restrict the rotation
  menu (`settings.cpp:778`) to `ROTATION` and `ROTATION^2` and flip touch
  mapping with it. IMU auto-flip later, also default off.

### Phase 5: app lifecycle
- Install DeskBar-AI (about 4.2 MB) through the Launcher from SD. Boot it.
  Return to the Launcher.
- Check that DeskBar's LittleFS data partition expectations are satisfied by
  the Launcher's runtime partition layout (`partition_install_layout.cpp`).
- OTA catalogue = LauncherHub ∪ fork catalogue (D3): `-D EXTRA_CATALOG_URL`
  gated menu source in `src/onlineLauncher.cpp` `ota_function()`, entries
  installed with the existing `installExtFirmware(url)`. Treat a LauncherHub
  404 for our `OTA_TAG` as an empty list, not an error.
- Uncomment the env in both lists once built and tested on hardware.

## Definition of done
Boot on battery without USB. All menus are navigable by touch, BOOT and PWR.
Brightness works including the floor. Battery % is shown. Power off and reboot
work. SD install of DeskBar-AI works and returns to the Launcher. CI builds.
