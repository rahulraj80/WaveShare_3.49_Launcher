Waveshare ESP32-S3-Touch-LCD-3.49 **V2** (silkscreen `Rev1.1` = V2; V1 swaps
LCD_BL/EXIO_INT and LCD_TE/LCD_RST). ESP32-S3R8, 16 MB flash, 8 MB OPI PSRAM.
Full reference with sources: `notes/01-hardware-reference.md`.

## Display: AXS15231B over QSPI (SPI3_HOST)
| CS | SCLK | D0 | D1 | D2 | D3 | TE | RST |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 9 | 10 | 11 | 12 | 13 | 14 | 21 | TCA9554 EXIO5 |

- Native 172x640 portrait, used as 640x172 landscape.
- QSPI writes only work as whole frames, so the board uses `USE_CANVAS`
  (220 KB PSRAM framebuffer, driver unrotated).

## Backlight
- GPIO42 feeds the AP3032 boost feedback node: **LOW = brightest**, HIGH = off.
- TCA9554 EXIO1 (BL_EN) gates the boost. Both must agree.
- Below about 91/255 brightness (duty above 164) the screen looks dead, so
  the curve stops there.

## SD card on the SD host (SDMMC, 1-bit)
| CLK | CMD | D0 | D3 |
| :---: | :---: | :---: | :---: |
| 41 | 39 | 40 | 38 (held high) |

DeskBar drives the same card over SPI (CS 38, MOSI 39, MISO 40, SCK 41) at
4 MHz; the Launcher uses the SD host, which is several times faster.

## I2C buses
- **I2C0 (Wire)**: SDA 47 / SCL 48.
  - TCA9554 0x20, ES8311 0x18, ES7210 0x40, PCF85063 0x51, QMI8658 0x6B.
- **I2C1 (Wire1)**: SDA 17 / SCL 18.
  - AXS15231B touch 0x3B. Its INT is on EXIO0, so touch is polled.

## TCA9554 (0x20)
| Bit | Function | Launcher sets |
| --- | --- | --- |
| 0 | TOUCH_INT | input |
| 1 | BL_EN | output, on after the panel holds a frame |
| 2/3 | IMU_INT1/2 | input |
| 4 | RTC_INT | input |
| 5 | LCD_RST | output, pulsed 1/30 ms, 0/250 ms, 1/120 ms |
| 6 | SYS_EN | output, **high first thing**: battery power-hold latch |
| 7 | NS_MODE (speaker amp) | input (unused) |

## Inputs
- **BOOT (GPIO0)**: single = Next, double = Prev, hold = Select.
  - Also the Launcher key: press it **just after** reset or power-on, not
    held through the reset edge (that enters download mode).
- **PWR (GPIO16 = SYS_OUT, active LOW)**: single = Esc, hold 2 s = power off.
- Touch: AXS15231B, single point.

## Power
- Battery: 18650 on GPIO4, `V = ADC x 3`. No gauge or charge-status pin.
- Power off: backlight off, then EXIO6 low. On USB power the board stays up,
  so it deep-sleeps with wake on BOOT.

## Device specific initialization
- SYS_EN (EXIO6) must be driven high before anything else, or the board
  dies on battery when PWR is released.
- Write the TCA9554 output register before its direction register, so
  SYS_EN never glitches low.
- Flash at 460800 baud; 921600 fails on this board.
