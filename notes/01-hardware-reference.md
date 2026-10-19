# Waveshare ESP32-S3-Touch-LCD-3.49 **V2** — hardware reference

Scope: everything a firmware needs to bring this board up. Each fact carries a
source and a confidence tag:

- **[tested]**: used by DeskBar-AI (`C:\Users\rahul\OpenCode\TuneBar`), which runs
  correctly on our V2 board. This beats every other source.
- **[vendor]**: from Waveshare's V2 repo
  (`C:\Users\rahul\OpenCode\ESP32-S3-Touch-LCD-3.49-V2`, `ESP-IDF/11_FactoryProgram/main/user_config.h`).
- **[open]**: not settled. Do not build on it without a measurement.

> **Revision trap.** `Rev1.1` on the silkscreen means **V2**. V1 is discontinued
> (all units shipped since 2026-06-08 are V2). V1 and V2 swap
> `LCD_BL`↔`EXIO_INT` and `LCD_TE`↔`LCD_RST`. Pin maps found on the web are
> usually V1. See `opencode_knowledge/wiki/projects/tunebar/lessons/verify-revision-label-before-editing-pins.md`.

> **Do not trust** `TuneBar/docs/HARDWARE_AND_DRAM.md` pin tables (wrong I2C,
> ADC, SD and PWM values) or `ESP32-S3-Touch-LCD-3.49-V2/BUILD_GUIDE.md`
> (wrong amp pin and PWM timer). Use the code.

## SoC and memory

| Item | Value | Source |
|---|---|---|
| MCU | ESP32-S3R8, rev v0.2 | [tested] esptool |
| Flash | 16 MB QIO | [tested] |
| PSRAM | 8 MB **OPI** (`memory_type = qio_opi`) | [tested] `TuneBar/platformio.ini` |
| USB | native USB-Serial/JTAG, VID:PID 303A:1001 | [tested] |
| Also on board | CH343P USB-UART bridge on UART0 (GPIO43/44) | [tested] |

Build flags required for `Serial` on the native USB port:
`-D ARDUINO_USB_MODE=1 -D ARDUINO_USB_CDC_ON_BOOT=1`.

## GPIO map

| GPIO | Function | Notes |
|---|---|---|
| 0 | BOOT button | active low; the only "free" user button |
| 4 | Battery ADC (ADC1_CH3) | 12 dB atten, **V_bat = V_adc × 3** [tested] |
| 6 | I2S DIN (from ES7210) | |
| 7 | I2S MCLK | |
| 8 | TCA9554 INT (EXIO_INT) | **not** the backlight on V2 |
| 9 | LCD QSPI CS | |
| 10 | LCD QSPI SCLK | |
| 11–14 | LCD QSPI D0–D3 | |
| 15 | I2S BCLK | |
| 16 | SYS_OUT = PWR key sense | input, pull-up, active low [tested] |
| 17 / 18 | **Touch I2C** SDA / SCL (I2C_NUM_1) | [tested]: DeskBar uses this bus and touch works. Closes the wiki's "touch on 47/48?" caveat. |
| 21 | LCD TE | defined, unused by DeskBar |
| 38–41 | SD card | SPI: CS 38 / MOSI 39 / MISO 40 / SCK 41 at 4 MHz [tested]: DeskBar plays music from SD. SDMMC 1-bit: CMD 39 / D0 40 / CLK 41 (vendor) |
| 42 | Backlight PWM / AP3032 feedback | **inverted**, see below |
| 45 | I2S DOUT (to ES8311) | |
| 46 | I2S LRCK | |
| 47 / 48 | System I2C SDA / SCL (I2C_NUM_0) | 400 kHz, internal pull-ups |

## I2C devices

| Bus | Device | Addr |
|---|---|---|
| 0 (47/48) | TCA9554 IO expander | 0x20 |
| 0 | ES8311 DAC codec | 0x18 |
| 0 | ES7210 mic ADC | 0x40 |
| 0 | PCF85063 RTC | 0x51 |
| 0 | QMI8658 IMU | 0x6B |
| 1 (17/18) | AXS15231B touch | 0x3B |

## TCA9554 expander (0x20) — the board's control plane

| Bit | Mask | Function | Required state |
|---|---|---|---|
| 0 | 0x01 | TOUCH_INT | input |
| 1 | 0x02 | **BL_EN** (AP3032 boost enable) | output; 1 = backlight rail on |
| 2 | 0x04 | IMU_INT1 | input |
| 3 | 0x08 | IMU_INT2 | input |
| 4 | 0x10 | RTC_INT | input |
| 5 | 0x20 | **LCD_RST** | output; idles 1 |
| 6 | 0x40 | **SYS_EN** (battery power-hold latch) | output; **must be 1 early in boot** |
| 7 | 0x80 | NS_MODE / NS4150B speaker amp enable | output |

Gotchas [tested]:
- `set_level` on a bit configured as input does nothing silently. Always write
  the direction register (0x03) first, then read it back.
- On battery, if SYS_EN is not driven high **unconditionally**, the board
  powers off when the PWR key is released.
- "EXIO1" is bit 1 (mask 0x02), not bit 0. Name every constant by mask.
- DeskBar's `tca9554.cpp` comments mislabel EXIO1/EXIO2 and it drives EXIO2
  (IMU_INT1) as an output. Do not copy that part.
- **[open]** The TCA9554 is not reset by an ESP32 reset, so its outputs
  probably survive `esp_restart()` into another firmware. That matters for
  the launcher (see `03-firmware-porting-playbook.md`). Verify on hardware.

## Display — AXS15231B, QSPI, 172 × 640 native portrait

| Item | Value | Source |
|---|---|---|
| Bus | SPI3_HOST, QSPI, SPI mode 3, **40 MHz** | [tested] `TuneBar/src/lvgl_port/lvgl_port.cpp:406-417` |
| Framing | 32-bit cmd: opcode 0x02 (cmd) / 0x32 (pixels) / 0x0B (read), `(op<<24)\|(cmd<<8)` | [tested] |
| Reset | via EXIO5: 1 → 30 ms → 0 → 250 ms → 1 → 30 ms | [tested] `tca9554.cpp:68-78` |
| Init | SLPOUT, MADCTL=0x00, COLMOD=0x55, then 0x11 (100 ms), 0x29 (100 ms) | [tested] |
| Colour | RGB565, byte-swapped (`LV_COLOR_16_SWAP 1`) | [tested] |
| Rotation | **No MADCTL rotation.** MADCTL stays 0; the flush reorders pixels in software | [tested] |
| Partial update | **Not supported in practice.** In QSPI mode only CASET is sent (no RASET); RAMWR (0x2C) at y=0 then RAMWRC (0x3C). Every frame is streamed top-to-bottom in full. | [tested] `esp_lcd_axs15231b.c:298-321` |
| Buffers | 2 × 220 KB full frames in PSRAM + one 22 KB internal DMA bounce buffer (172×64×2), chunked flush, ISR semaphore per chunk | [tested] |
| Frame rate | DeskBar caps at 30 Hz (33 ms) to limit bus traffic | [tested] |

Bandwidth: one frame is 640×172×2 = 220,160 B. At 40 MHz × 4 lines
(about 20 MB/s) that is ≈11 ms of wire time. 30 fps full-frame is easy, 60 fps
is the ceiling.

Rules learned the hard way [tested]:
- Only one task touches the QSPI bus. A panel on/off call from another core
  during a DMA flush deadlocks the SPI driver.
- The vendor driver's `disp_on_off(false)` sends **DISPON**, because the
  argument is inverted.
- After any "screen off" where the flush was skipped, force a full redraw on
  wake. The panel RAM is not trusted.
- `build_type = release` is mandatory. A debug `-Og` full-frame draw trips the
  5 s task watchdog and causes a boot loop.

Open display issues **[open]**:
- **Glow when off.** No combination reached true black.
- **Stuck rightmost column.** Hypothesis: the panel has 173 columns and only
  172 are written. Unproven.

Physical: 3.49" diagonal → about 190 ppi, active area about 85 × 23 mm.
An 8 px glyph is about 1 mm tall, which is unreadable. **16 px is the
practical minimum for text.** This drives the scaling rules in
`02-display-adaptation-guide.md`.

## Backlight — two pins, inverted

| State | GPIO42 | EXIO1 (BL_EN) |
|---|---|---|
| ON / max | LOW (PWM duty 0) | 1 |
| OFF | HIGH (duty 255) | 0 |

- LEDC low-speed, timer 3, channel 1, 8-bit, **50 kHz**, clock `RC_FAST`.
  `duty = 255 − brightness` [tested].
- Initialise GPIO42 as an output with **pull-down**, level 0, before the panel
  comes up.
- Visible floor is about 91/255 brightness. Below that the screen looks dead,
  so clamp the UI slider (see the vendor README warning).
- Recommended order: GPIO42 low, BL_EN=0, init the panel, draw the first
  frame, then BL_EN=1. This avoids a garbage flash.

## Touch — AXS15231B integrated, I2C_NUM_1 @ 0x3B, 400 kHz

- Read: write 11 bytes `B5 AB A5 5A 00 00 00 0E 00 00 00`, then read
  (vendor reads 32; 8 are enough for one point).
- `buf[1]` = number of points (single-touch in practice). `buf[0]` = gesture
  code. `buf[2]>>6` = event type.
- `X = ((buf[2]&0x0F)<<8) | buf[3]` along the 640 axis.
  `Y = ((buf[4]&0x0F)<<8) | buf[5]` along the 172 axis.
- DeskBar landscape mapping [tested]: `x = 640 − rawX`, `y = 172 − rawY`
  (normal); raw values pass through unchanged when flipped 180°.
- INT is on EXIO0 (expander), so poll. No reset GPIO.
- Latent DeskBar bug: the 8-byte command array is sent as 11 bytes. Do not copy it.

## Power

- Charger ETA6098. No fuel gauge and no PMIC on I2C: battery state is ADC only.
- Battery: `mV = adc_mV × 3`. Live check 2026-10-19 via DeskBar CLI `batt`: ADC 1361 mV → 4.09 V. "Charging" is a heuristic (≥ about 4.02 V);
  there is no charge-status pin.
- Power off = EXIO6 (SYS_EN) ← 0. DeskBar uses a 2 s PWR hold.
- No deep or light sleep in DeskBar. "Screen off" = backlight off and flush
  skipped.

## Audio, IMU, RTC

- I2S: MCLK 7, BCLK 15, LRCK 46, DOUT 45, DIN 6. ES8311 out, ES7210 in.
  NS4150B amp enable on EXIO7.
- ES7210: regs 0x04/0x05 divider 256, reg 0x02 = 0xC1, stereo 16 kHz.
  See `TuneBar/docs/AUDIO_HARDWARE_LEARNINGS.md`.
- QMI8658 at 0x6B: DeskBar uses it for 0°/180° auto-flip (±0.5 g on Ay,
  350 ms hysteresis).

## Flashing and serial

- Flash a **matched set**: bootloader 0x0, partitions 0x8000, app 0x10000.
  An app on a mismatched bootloader boot-loops every 100 ms, which shows up on
  Windows as a repeating USB connect chime.
- Use `-b 460800`. 921600 fails on this board. `--no-stub` recovers a reset loop.
- Opening the port with DTR/RTS asserted holds the chip in download mode.
  Clear both before `open()`.
- Recovery: hold BOOT and tap RESET.
- COM port is single-owner. Close monitors before flashing.

## Diagnostics we already have

- `C:\Users\rahul\OpenCode\waveshare_3.49inch\validate_cycle.py`:
  serial-synchronised webcam capture with mean-BGR per state. Use it to prove
  the panel latches pixels before debugging anything else.
- The DeskBar serial CLI (`bl <n>`, simulated taps and swipes) is the
  remote-control pattern worth copying. Read-only commands that don't change the
  screen: `ping`, `help`, `status`, `batt`, `telemetry`. Open COM11 with DTR/RTS
  cleared before `open()` so the board doesn't reset.

- **Launcher CLI (our fork)**: `support_files/serial_cli.py COM11 <cmd>...`. Commands: `ping`, `status`,
  `bl <0-100>`, `tap [x y]`, `nav <next|prev|sel|esc>`, `screenshot -o file.png` (landscape PNG of the
  framebuffer). Native USB-CDC drops bytes if the TX buffer is full: loop on `Serial.write()` for bulk data.
