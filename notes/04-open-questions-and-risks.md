# Open questions and risks

Ranked by how much they can derail the plan. Update this file as items close.

## Risks

| # | Risk | Why it matters | Mitigation |
|---|---|---|---|
| R1 | DisplayDrivers' AXS15231B driver (22) doesn't drive this 172×640 panel | It was validated only on a 320×480 CYD. This panel needs full-frame streaming, 0x2C/0x3C continuation and expander reset. | Phase 1 liveness test. Patch the driver upstream from DeskBar's working code. |
| R2 | ~~SD never mounted in DeskBar logs~~ **Closed 2026-10-19** | False alarm: DeskBar logs mount success at `log_d`, and its build is `CORE_DEBUG_LEVEL=1`, so success is never printed. The owner confirms SD music playback works. | Use DeskBar's settings in the Launcher: SPI CS38/MOSI39/MISO40/SCK41 at **4 MHz** to start (`TuneBar/sketch/src/file/file.cpp:115-128`). |
| R3 | No Launcher-return key | A user installs an app and can't get back | BOOT just after reset via keyboot (D2), hardware-test the timing; fallback `BOOT_LOGIC_ON_NVS`; plus a "Reboot to Launcher" item in every port |
| R4 | Ported firmware drops power on battery | SYS_EN on the expander. Every foreign binary is affected. | Board-support minimum in each port. Test whether the expander state survives `esp_restart` |
| R5 | Panel quirks: glow when off, stuck right column | Cosmetic but visible. Could be a 173-column panel. | 173-wide write probe. Keep it out of the critical path. |
| R6 | Launcher UI changes regress other boards | Phase 3 edits shared code | Build every env in `default_envs`. Screenshot t-display-s3, lcd-147 and cardputer. |
| R7 | TFT_eSPI-based firmwares are hard to redirect | Marauder is TFT_eSPI-only. Bruce can avoid it via its Arduino_GFX backend. | Full-frame `TFT_eSprite` adapter in the BSP (see `ports/marauder.md`) |
| R8 | IRAM pressure | DeskBar sits at IRAM 100% | The compositor flush path must not add IRAM_ATTR code. |

## Questions

Answered 2026-10-19 → see `05-decisions.md` (forks only, buttons, catalogue
union, flip, battery). Still open:

1. **BSP repo**: approve `WaveShare_3.49_BSP` (Apache-2.0) as a new repo (D5)?
2. **Meshtastic radio**: is an SX1262 module available to wire to the 22-pin
   header, or is the port BLE/WiFi/MQTT-only?
3. **Bruce RF peripherals** (CC1101, NRF24, IR): hide those menus, or plan
   header wiring?
4. **Marauder build system**: OK to add a PlatformIO env to our fork (it's
   Arduino-IDE only upstream)?
5. **Hardware tests needed from you**: BOOT-after-reset Launcher key timing;
   whether TCA9554 state survives `esp_restart()` into another app.
