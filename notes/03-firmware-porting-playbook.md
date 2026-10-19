# Playbook: porting a third-party firmware to the 3.49" V2

Use this for every firmware we bring to the board (Bruce, Marauder, NerdMiner,
Meshtastic UI, etc.). Read `01-hardware-reference.md` and
`02-display-adaptation-guide.md` first.

## 0. Triage (before writing code)

Record in `notes/ports/<firmware>.md`:

- Upstream repo, licence (GPL-3 forces source release of our patches), and
  the build we start from (prefer a **320×170/172** env, then 240×135).
- Graphics library (LVGL / LovyanGFX / M5GFX / Arduino_GFX / TFT_eSPI).
- Input model (buttons, encoder, keyboard, touch).
- Peripherals it needs that we lack: CC1101, NRF24, IR, GPS, LoRa, external
  SD on other pins. Can they go on the 22-pin header?
- Flash size it needs. The Launcher gives it an app slot in our 16 MB.
  Partition expectations: names/subtypes of `spiffs`/`littlefs`/`nvs` it mounts.
- Presentation mode from the guide's decision table.

## 1. Board-support minimum (every firmware, no exceptions)

Without these the device looks dead or switches off on battery:

1. I2C0 on 47/48 → TCA9554 0x20: set direction for bits 1, 5 and 6 as outputs
   **first**, then SYS_EN=1, LCD_RST=1, BL_EN=0.
2. GPIO42 output, pull-down, level 0.
3. Panel reset pulse via EXIO5, then AXS15231B init, then the first frame.
4. BL_EN=1. Brightness via LEDC (inverted duty, floor ≈91).
5. Touch on I2C1 17/18 @ 0x3B, if used.
6. `ARDUINO_USB_MODE=1`, `ARDUINO_USB_CDC_ON_BOOT=1`, `build_type = release`.

Package 1–5 as a tiny shared `ws349_board_begin()` (part of the compositor
library) so each port needs one call.

> **[open, test early]** The TCA9554 keeps its outputs across an ESP32
> software reset. If the Launcher sets SYS_EN=1 and BL_EN=1 before
> `esp_restart()` into the app, an *unmodified* firmware may stay powered and lit.
> It still needs its own panel driver, so this alone does not make a foreign
> binary usable. It does mean the battery latch survives app hand-off.

## 2. Return to Launcher

Power-on or the RESET button always opens the Launcher's boot screen (its bootloader
starts the Launcher on a power-on or deep-sleep-wake reset). From a running app: its serial
`launcher` command, a 100 ms deep sleep (`support_files/to_launcher.py` drives it). The
bootloader's GPIO key (CFG > GPIO on boot starts Launcher) is off by default and unused here:
BOOT held through a reset enters ROM download mode.

Every port must implement the serial `launcher` command (deep sleep 100 ms) and keep the
SD card on SPI (a deep-sleep hand-over doesn't power-cycle the card). Buttons follow the D2
table in every firmware, so users never relearn controls.

## 3. Display port

Pick the redirect technique for its graphics library (guide §5) and the mode
(guide §4). Keep the firmware's own resolution. Never hack its layout first:
the compositor approach is reversible, layout patches are not.

## 4. Input port

Map the firmware's input layer to compositor events (guide §6). Prefer
patching the firmware's input-abstraction file over sprinkling `#ifdef`s.

## 5. Build, flash and validate

- Add an env named `waveshare-esp32-s3-touch-lcd-349` (the same name as our
  Launcher env) in the firmware's PlatformIO config, so catalogue filtering
  lines up.
- Flash with esptool (bootloader 0x0 / partitions 0x8000 / app 0x10000,
  460800 baud) for standalone tests. Then test **installed via the Launcher**
  from SD and OTA, which is the real path.
- Run the guide's §8 validation list.

## 6. Distribute

- The Launcher's online installer queries `api.launcherhub.net` by `OTA_TAG`
  (category). Our device has no category there yet. Options: register one
  upstream, or point the Launcher at our own catalogue (DeskBar already
  publishes `releases/firmware_catalog.json` with `publish_ota.py`).
- Ship merged binaries in the format the Launcher installer expects (app-only
  vs merged image with partition table). Check `src/onlineLauncher.cpp`
  before the first release.

## 7. Upstreaming

If the board support is small and clean, offer it upstream to the firmware
author as a PR. That is the only way it survives their next release.
