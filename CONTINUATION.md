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
- [x] Built on `auto` (`~/scripts/WaveShare_3.49_Launcher`, 5 min, no warnings in our files; app 1.25 MB =
      79% of the 1.5 MB test partition). Flashed 2026-10-19 (bootloader 0x0, partitions 0x8000,
      boot_app0 0xE000, app 0x10000). Boot log: TCA9554 config 0x9D, SYS_EN latched, SD mounted,
      touch probe OK, boot screen reached, serial console answers `help`.
- [x] Owner: screen is visible.
- [x] DeskBar-style CLI in `src/serial_console.cpp` (+1.7 KB): `ping`, `status`, `bl <0-100>`, `tap [x y]`
      (HAS_TOUCH), `screenshot` (USE_CANVAS + Arduino_GFX). Verified on device 2026-10-19: screenshot of the
      main menu, tap selects a tile, `nav prev` moves the highlight, status shows batt 94% / 4053 mV.
      Host tool: `python support_files/serial_cli.py COM11 status "tap 320 110" "nav next" screenshot -o x.png`.
      USB-CDC drops bytes when its TX buffer is full, so binary output must go through `consoleWriteAll()`.
      A tap on a dimmed screen only wakes it (same as a finger); send it twice.
- [x] (fix flashed; owner confirmed a ~1 s hold selected, matching the diagnosis) Owner: BOOT long press (held to 5 s) did nothing; other buttons OK. Cause: `hal_buttons_poll_1` sends
      Select at 0.55-1.2 s but Esc above 1.2 s. Fix: with HAS_2_BUTTONS (PWR is Esc) any hold >= 0.55 s is
      Select. Only this board uses poll_1 with HAS_2_BUTTONS.
- [x] Owner: finger touch, BOOT/PWR buttons, battery on/off all work.
- [x] (done, flashed; `bl 31` saved and survived a reboot: settings show "bright":31) Brightness: owner's 31% came back as 100 (device had `"bright":100` stored; likely the old long-hold=Esc
      bug discarded the slider value). Storage already goes to SD config.conf + NVS (saveConfigs ->
      saveIntoNVS). Add `DEFAULT_BRIGHT` (pre_compiler.h, default 100; this board 35) for first boot, make
      CLI `bl <n>` save, then `bl 31` on the device.
- [x] DeskBar Launcher build (TuneBar repo, branch `launcher-build`, 136037f): env `deskbar-launcher`,
      partitions `launcher_app5MB_littlefs.csv` (app 5 MB @0x10000, LittleFS label `littlefs` @0x510000;
      NOT `spiffs`, which the Launcher shrinks to 448 KB), no in-app OTA, CLI `launcher` (erase otadata +
      restart). Built on auto with `bash scripts/build_launcher_image.sh` -> `sketch/deskbar-2.6.1-launcher.bin`
      (7.27 MB; app 4.24 MB = 81% of slot). Copied to SD `E:\firmware\` via Launcher USB mode (hash verified).
- [ ] (PAUSED: owner is learning the current features first; decision D7 in notes/05-decisions.md)
      Likely fix on S3: in src/massStorage.cpp restoreUsbSerial(), call
      `usb_serial_jtag_ll_phy_enable_external(false)` (hal/usb_serial_jtag_ll.h) to map the internal
      FSLS PHY back to USB-Serial/JTAG; usb_new_phy(INT) left it on the OTG wrap. Plus: leave MSC
      on USB unplug and on any key/tap.
- [ ] BUG: after ejecting the SD drive, the Launcher left USB mode but the board never came back on USB
      (no COM11, no VID 303A device). `endUsbRaw()` -> `restoreUsbSerial()` in src/massStorage.cpp. Investigate.
- [ ] Owner: RESET, then install DeskBar from SD > firmware > deskbar-2.6.1-launcher.bin; verify app +
      LittleFS (music/stations) + `launcher` CLI return + BOOT-after-reset return.
- [ ] Bruce port (next): see notes/ports/bruce.md. Plan: branch `ws349-port` in the Bruce fork;
      `TFT_FULLFRAME_CANVAS` in lib/HAL/display/ardgfx.cpp (canvas + dirty flag in RUN_ON_MUTEX + 30 Hz
      flush task); `DEFAULT_DISABLED_MENUS` in src/core/config.h to hide RF/NRF24/IR/RFID/LoRa/GPS/
      Ethernet/FM; board folder boards/waveshare-esp32-s3-touch-lcd-349/.
- [ ] Owner visual check (remaining): picture, orientation (ROTATION 1 vs 3), colours/inversion, backlight, touch
      position, BOOT/PWR buttons, battery unplug test.
      Touch mirror/swap and ROTATION 1 vs 3 are guesses until tested on hardware.
      Backlight PWM is 5 kHz (HAL) vs 50 kHz in DeskBar: watch for flicker/whine.
- Local build attempt on windows-box was a mistake (owner: no local compiles). It was stopped;
  it left a 5.9 GB `.pio/` cache here. Ask the owner before deleting it.
- [x] Add `TOUCH_CTRL_AXS15231B` (committed; not yet compiled) to `src/hal/inputs/touch.cpp` (extends the AXS5106L driver; same report decode,
      different read: write `B5 AB A5 5A 00 00 00 08 00 00 00` to 0x3B on Wire1 17/18, read 8 bytes).
- [x] Scaffold `boards/waveshare-esp32-s3-touch-lcd-349/` (committed, NOT yet compiled) (BOOT via `hal_buttons_poll_1`, PWR=Esc / 2 s off,
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

## Build workflow (owner rule: never compile on windows-box)
1. Edit on windows-box, commit, push the branch to GitHub.
2. `ssh auto` (autobots, Linux ARM; NOT `sup`). Repos live under `~/scripts/<repo>`;
   `git pull` there (origin must be SSH: `git@github.com:rahulraj80/<repo>.git`).
3. Build with the absolute path `~/.local/bin/pio run -d ~/scripts/<repo> -e <env>`.
   Do NOT edit PATH on the server. `sed` is `/usr/bin/sed` there.
4. `scp auto:~/scripts/<repo>/.pio/build/<env>/{bootloader,partitions,firmware}.bin` back,
   flash COM11 from windows-box with esptool (0x0 / 0x8000 / 0x10000, 460800 baud).
5. Never force-push. Single-token commit subjects or a remote script avoid quoting traps.
Source: `opencode_knowledge/wiki/projects/tunebar/research/remote-build-and-flash-loop-on-auto.md`.

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
