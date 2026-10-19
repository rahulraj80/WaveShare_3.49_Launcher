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
- [ ] Launcher Phase 0 (next).

## Next up
1. Launcher Phase 0 (`notes/00-launcher-port-plan.md`): submodules, baseline
   build, board folder scaffold, dummy-TFT serial boot, SYS_EN latch test.
2. BSP skeleton: `library.json`, `ws349_board`, `ws349_expander`, liveness example.
3. Bruce port (`notes/ports/bruce.md`).

## Rules in force
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
