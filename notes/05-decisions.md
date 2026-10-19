# Decisions log

Owner rulings, newest first. When a later decision changes an earlier one,
edit the entry rather than appending a contradiction.

## 2026-10-19

### D1. Where fixes go
All changes go to **our forks** (`github.com/rahulraj80/WaveShare_3.49_*`),
never to the upstream originals. Upstream PRs can be revisited later.

| Local folder (`C:\Users\rahul\OpenCode\`) | origin | upstream | Licence |
|---|---|---|---|
| `WaveShare_3.49_Launcher` | rahulraj80/WaveShare_3.49_Launcher | bmorcelli/Launcher | MIT |
| `WaveShare_3.49_Bruce_firmware` | rahulraj80/WaveShare_3.49_Bruce_firmware | BruceDevices/firmware | AGPL-3.0 |
| `WaveShare_3.49_ESP32Marauder` | rahulraj80/WaveShare_3.49_ESP32Marauder | justcallmekoko/ESP32Marauder | MIT |
| `WaveShare_3.49_Meshtastic_firmware` | rahulraj80/WaveShare_3.49_Meshtastic_firmware | meshtastic/firmware | GPL-3.0 |
| `TuneBar` (DeskBar-AI) | rahulraj80/DeskBar-AI | VaAndCob/TuneBar | GPL-3.0 |

The Meshtastic repo was renamed from `..._Meshstatic_...`. The local folder
and `origin` URL were updated on 2026-10-19.

### D2. Button convention (same in the Launcher and every port)
Physical keys: **BOOT** (GPIO0) and **PWR** (GPIO16 sense, active low).
Touch stays the primary input. Buttons are a complete fallback.

| Key | Single | Double | Hold |
|---|---|---|---|
| BOOT | Next / Down | Prev / Up | 0.6 s: **Select** |
| PWR | **Back / Esc** | — (reserved) | 2 s: power off (with an on-screen countdown; release cancels) |

- Timings: click ≤ 300 ms, double-click gap ≤ 250 ms, hold 600 ms.
  These match Bruce's T-Display-S3 settings (`long_press_time=600`).
- PWR hold-to-off keeps DeskBar's 2 s convention. Power off = backlight off,
  then EXIO6 (SYS_EN) ← 0.
- PWR double is left unassigned on purpose, for firmware-specific use.
- **Return to Launcher** (corrected 2026-10-20; the earlier "BOOT just after reset" plan was
  wrong): Power-on or the RESET button always opens the Launcher's boot screen (its bootloader
  starts the Launcher on a power-on or deep-sleep-wake reset). From a running app: its serial
  `launcher` command, a 100 ms deep sleep (`support_files/to_launcher.py` drives it). The
  bootloader's GPIO key (CFG > GPIO on boot starts Launcher) is off by default and unused here:
  BOOT held through a reset enters ROM download mode.

### D3. Firmware catalogue = union
The Launcher OTA menu shows **LauncherHub ∪ our fork's catalogue**:
- LauncherHub: unchanged (`category=OTA_TAG`). Our category doesn't exist
  yet, so it returns 404. Treat that as "empty" and don't show an error.
- Fork catalogue: a static JSON in the Launcher fork
  (`catalog/waveshare-esp32-s3-touch-lcd-349.json`, served from
  `raw.githubusercontent.com`). Entries are
  `{name, version, description, link}` where `link` is a merged/app `.bin`
  installed with the existing `installExtFirmware(url)`. No new installer code.
- Compiled in only when the board defines `-D EXTRA_CATALOG_URL='"…"'`, so
  other boards build unchanged.
- Release binaries live as GitHub Release assets in each firmware fork. The
  catalogue only links to them.

### D4. Display flip
- Setting **"Flip 180°"**, **default off**. Only 0° and 180° landscape are
  offered; 90/270 are never offered.
- The optional IMU auto-flip (QMI8658, as DeskBar does) only switches between
  the same two orientations. It's a later add-on, also default off.
- Touch mapping and the compositor both read the same flip flag.

### D5. Shared board/display library
Recommendation: a **new repo, `WaveShare_3.49_BSP`** (Apache-2.0), consumed
by every port as a PlatformIO `lib_deps` git URL. **Pending your go-ahead.**
Why not inside DeskBar-AI:
- DeskBar is **GPL-3** (inherited from VaAndCob/TuneBar). Code placed there
  would be GPL and would relicense our MIT Marauder and Launcher builds.
- Sources we need are permissive: Espressif `esp_lcd_axs15231b` (Apache-2.0)
  and the Waveshare V2 examples (Apache-2.0). Apache-2.0 is compatible with
  MIT, GPL-3 and AGPL-3 consumers.
- Rule for the BSP: write it from the Apache vendor/Espressif code and our
  measured facts. **Don't paste GPL DeskBar code** unless it's your own
  authorship that you choose to relicense.

### D6. Battery
18650, 2000 mAh. ADC on GPIO4, `V_bat = V_adc × 3` (DeskBar, tested).
If the Waveshare wiki and DeskBar disagree, DeskBar wins.

### D7. SD card as a USB drive: manual toggle (2026-10-19)
Not automatic. The Launcher's **USB** tile hands the SD card to the PC and cuts the firmware off
from it. It switches back when (a) the USB cable is unplugged or the PC ejects the drive, or
(b) any button press or tap on the device. After switching back the board must be COM11 again
(fix the current exit bug).
