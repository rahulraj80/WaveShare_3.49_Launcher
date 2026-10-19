# DeskBar-AI as a Launcher-installable app

Repo: `C:\Users\rahul\OpenCode\TuneBar` (origin `rahulraj80/DeskBar-AI`, GPL-3.0).
DeskBar already runs natively on this board. This is about packaging, not porting.

## How the Launcher installs from SD
`src/sd_functions.cpp:439` (Install) → `updateFromSD()` (`:800`):
- App-only `.bin` (no table at 0x8000): installs just the app.
- Merged image (table at 0x8000): installs the app and copies data partitions
  of subtype 0x82 (SPIFFS) and 0x83 (LittleFS) with their contents, keeping
  non-"spiffs" labels and their declared sizes.

## What DeskBar needs
1. **Merged image including LittleFS.** DeskBar mounts LittleFS from the
   partition labelled **`spiffs`** (subtype littlefs, 0x1E0000;
   `sketch/src/file/file.cpp:83`, `partitions/7MB_app_ota_2MB_littlefs.csv`).
   `sketch/data/` (`audio/`, `stations.csv`, 552 KB) must be in the image, or
   DeskBar formats an empty FS. Build `firmware.bin` and `littlefs.bin`, then
   `esptool merge_bin` with bootloader/partitions → `deskbar-<ver>-launcher.bin`.
2. **No self-OTA under the Launcher.** `updater.cpp:297` and
   `web_remote.cpp:1709` call `Update.begin(U_FLASH)`, which writes to the next
   OTA slot. Under the Launcher that may be another installed app. Add a
   `LAUNCHER_BUILD` flag that hides or blocks in-app OTA and points the user to
   the Launcher catalogue.
3. **"Reboot to Launcher"** menu item and CLI command (`launcher`).
4. **Catalogue:** DeskBar's `releases/firmware_catalog.json` entries can be
   republished as `-launcher.bin` assets and listed in our fork catalogue (D3).

## Open
- Confirm the Launcher keyboot bootloader boots a pioarduino 3.3.7 / IDF 5.5
  app (expected yes; test on hardware).
- App size is about 4.2 MB. The Launcher layout leaves about 14 MB, so it fits.

## Backup of the original device state
`C:\Users\rahul\OpenCode\backups\deskbar-v2.6.1-full-20261019.bin` (16 MB full
read, 2026-10-19). Contains NVS secrets: **never commit it**. Restore with
`esptool write_flash 0 <file>` at 460800 baud.
