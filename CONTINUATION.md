# CONTINUATION — Waveshare 3.49" V2 port program

Read this first after any crash or interruption. Update it **before** starting
each piece of work and commit/push it with that work.

## Current state (2026-10-19)
- Planning is done. See `notes/README.md` (index), `notes/05-decisions.md`
  (owner rulings), `notes/ports/*.md` (per-firmware plans).
- Branch: `ws349-port` in this repo (pushed to origin `rahulraj80/WaveShare_3.49_Launcher`).
- BSP repo created: `C:\Users\rahul\OpenCode\WaveShare_3.49_BSP` (Apache-2.0, empty
  except LICENSE/README). Design: `notes/06-bsp-library-design.md`.

## In progress
- [x] DeskBar SD check: closed. Mount success is logged at debug level only;
      SD works at 4 MHz SPI (see R2).
- [x] Full flash backup done: `C:\Users\rahul\OpenCode\backups\deskbar-v2.6.1-full-20261019.bin`
      (+ .sha256). NOT in any repo (NVS secrets). Restore: esptool write_flash 0 <file>.
- [x] Submodules initialised.
- [ ] Baseline build `m5stack-cardputer` (pio is at `~/.platformio/penv/Scripts/pio.exe`, not on bash PATH).
- [x] Add `TOUCH_CTRL_AXS15231B` (committed; not yet compiled) to `src/hal/inputs/touch.cpp` (extends the AXS5106L driver; same report decode,
      different read: write `B5 AB A5 5A 00 00 00 08 00 00 00` to 0x3B on Wire1 17/18, read 8 bytes).
- [ ] Scaffold `boards/waveshare-esp32-s3-touch-lcd-349/` (BOOT via `hal_buttons_poll_1`, PWR=Esc / 2 s off,
      TCA9554 helper modelled on `boards/elecrow-esp32s3-5in/interface.cpp:34-98`).
- Finding: Arduino_GFX driver 22 default init = `axs15231b_180640_init_operations` (this panel family);
  `USE_CANVAS` keeps the driver unrotated and pushes full 172x640 frames, matching DeskBar.
- Owner approved flashing the device (nothing critical on it).
- DeskBar-as-Launcher-app plan: `notes/ports/deskbar.md`.

## Next up
1. Launcher Phase 0 (`notes/00-launcher-port-plan.md`): submodules, baseline
   build, board folder scaffold, dummy-TFT serial boot, SYS_EN latch test.
2. BSP skeleton: `library.json`, `ws349_board`, `ws349_expander`, liveness example.
3. Bruce port (`notes/ports/bruce.md`).

## Rules in force
- **NO `Co-Authored-By` or any AI attribution in commits/PRs (mandatory).**
- Fixes go to our forks only (`rahulraj80/*`), never upstream.
- Commit often; push the working branch so a local crash loses nothing.
- Update this file before starting anything.
- Hardware facts: DeskBar code > Waveshare V2 repo > wiki > web.
- Bruce: hide RF menus (CC1101/NRF24/IR). Meshtastic: no LoRa yet, port anyway.
  Marauder: add a PlatformIO env to our fork.
- Flash with esptool (bootloader 0x0, partitions 0x8000, app 0x10000, 460800 baud),
  not `pio -t upload`.

## Open hardware tests (owner)
- BOOT pressed just after reset → Launcher?
- TCA9554 state survives `esp_restart()` into another app?
