#include "hal/bright/bright.h"
#include "hal/device.h"
#include "hal/inputs/buttons.h"
#include "hal/inputs/touch.h"
#include "idf/launcher_platform.h"
#include "powerSave.h"
#include <Wire.h>
#include <interface.h>

// Waveshare ESP32-S3-Touch-LCD-3.49 V2. Power hold, panel reset and the
// backlight boost enable all sit on a TCA9554 on the system I2C bus, so it
// has to be configured before anything else -- see connections.md.
#define SYS_I2C_SDA 47
#define SYS_I2C_SCL 48
#define TOUCH_I2C_SDA 17
#define TOUCH_I2C_SCL 18
#define BOOT_BTN 0
#define PWR_BTN 16 // SYS_OUT: PWR key sense, active LOW

#define TCA9554_ADDR 0x20
#define TCA9554_REG_OUTPUT 0x01
#define TCA9554_REG_CONFIG 0x03 // 1 = input
#define EXIO_BL_EN 0x02         // EXIO1: AP3032 backlight boost enable
#define EXIO_LCD_RST 0x20       // EXIO5: panel reset
#define EXIO_SYS_EN 0x40        // EXIO6: battery power-hold latch

static uint8_t exioOut = EXIO_SYS_EN | EXIO_LCD_RST;

static void tca9554Write(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(TCA9554_ADDR);
    Wire.write(reg);
    Wire.write(val);
    Wire.endTransmission();
}

static void exioSet(uint8_t mask, bool high) {
    exioOut = high ? (exioOut | mask) : (exioOut & ~mask);
    tca9554Write(TCA9554_REG_OUTPUT, exioOut);
}

static DeviceButtons buttonsCfg() { return DeviceButtons{BOOT_BTN}; }

static DeviceTouch touchCfg() {
    DeviceTouch cfg;
    cfg.i2c_bus = &Wire1; // touch has its own bus; Wire is the expander's
    // Raw X runs along the 640 side and raw Y along the 172 side.
    // rotation:        0      1      2      3
    bool swapXY[4] = {true, false, true, false};
    bool mirrorX[4] = {false, true, false, false};
    bool mirrorY[4] = {false, true, false, false};
    for (int i = 0; i < 4; i++) {
        cfg.SwapXY[i] = swapXY[i];
        cfg.MirrorX[i] = mirrorX[i];
        cfg.MirrorY[i] = mirrorY[i];
    }
    return cfg;
}

/***************************************************************************************
** Function:    _setup_gpio()
** Location:    main.cpp
** Description: initial setup for the device
***************************************************************************************/
void _setup_gpio() {
    Wire.begin(SYS_I2C_SDA, SYS_I2C_SCL);
    // Output levels first, then direction, so SYS_EN never glitches low.
    // BL_EN stays off until the panel holds a frame (_post_setup_gpio).
    tca9554Write(TCA9554_REG_OUTPUT, exioOut);
    tca9554Write(TCA9554_REG_CONFIG, (uint8_t)~(EXIO_BL_EN | EXIO_LCD_RST | EXIO_SYS_EN));
    Wire.beginTransmission(TCA9554_ADDR);
    Wire.write(TCA9554_REG_CONFIG);
    uint8_t cfgReadback = 0xFF;
    if (Wire.endTransmission(false) == 0 && Wire.requestFrom((uint8_t)TCA9554_ADDR, (uint8_t)1) == 1)
        cfgReadback = Wire.read();
    launcherConsolePrintf("WS349: TCA9554 config=0x%02X (want 0x9D), SYS_EN latched\n", cfgReadback);

    // Backlight feedback pin LOW = full brightness once BL_EN is on.
    launcherGpioOutput(TFT_BL);
    launcherGpioWrite(TFT_BL, LOW);

    // Panel hardware reset through EXIO5 (no MCU reset pin on V2).
    exioSet(EXIO_LCD_RST, true);
    launcherDelayMs(30);
    exioSet(EXIO_LCD_RST, false);
    launcherDelayMs(250);
    exioSet(EXIO_LCD_RST, true);
    launcherDelayMs(120);

    hal_buttons_init(buttonsCfg(), 1);
    launcherGpioInputPullup(PWR_BTN);
}

/***************************************************************************************
** Function:    _post_setup_gpio()
** Location:    main.cpp
** Description: second stage gpio setup, run after TFT and before SD card initialization
***************************************************************************************/
void _post_setup_gpio() {
    hal_bright_attach(TFT_BL);
    exioSet(EXIO_BL_EN, true);

    Wire1.begin(TOUCH_I2C_SDA, TOUCH_I2C_SCL, 400000);
    if (!hal_touch_init(touchCfg())) launcherConsolePrintf("WS349: touch not responding on 0x3B\n");
}

/*********************************************************************
** Function: setBrightness
** location: settings.cpp
** set brightness value
**********************************************************************/
// Inverted rail: duty 0 is full brightness. Below ~91/255 of brightness
// (duty above 164) the panel looks dead, so the curve stops there.
static const HalBrightCurve BL_CURVE = {0, 164, 2.2f, true};

void _setBrightness(uint8_t brightval) {
    if (brightval == 0) {
        ledcWrite(TFT_BL, 255);
        exioSet(EXIO_BL_EN, false);
        return;
    }
    if (!(exioOut & EXIO_BL_EN)) exioSet(EXIO_BL_EN, true);
    hal_bright_set(TFT_BL, brightval, BL_CURVE);
}

/*********************************************************************
** Function: InputHandler
** Handles the variables PrevPress, NextPress, SelPress, AnyKeyPress and EscPress
**********************************************************************/
void InputHandler(void) {
    static unsigned long pwrDownAt = 0;
    static bool pwrWasDown = false;
    const bool pwrDown = launcherGpioRead(PWR_BTN) == LOW;

    if (pwrDown && !pwrWasDown) {
        pwrWasDown = true;
        pwrDownAt = launcherMillis();
    } else if (pwrDown && launcherMillis() - pwrDownAt >= 2000) {
        powerOff();
    } else if (!pwrDown && pwrWasDown) {
        pwrWasDown = false;
        AnyKeyPress = true;
        if (!wakeUpScreen()) EscPress = true;
        return;
    }

    hal_buttons_poll_1(buttonsCfg());

    static unsigned long touchAt = 0;
    LTouchPoint t;
    if (hal_touch_read(touchCfg(), t) && (launcherMillis() - touchAt > 200 || LongPress)) {
        touchAt = launcherMillis();
        if (!hal_touch_apply(t)) return;
    }
}

/*********************************************************************
** Function: powerOff
** location: mykeyboard.cpp
** Turns off the device (or try to)
**********************************************************************/
void powerOff() {
    _setBrightness(0);
    exioSet(EXIO_SYS_EN, false); // cuts the battery rail
    // Still here means USB is powering the board: sleep until BOOT.
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, LOW);
    vTaskDelay(pdMS_TO_TICKS(200));
    esp_deep_sleep_start();
}

/*********************************************************************
** Function: reboot
** Handles reboot process for devices
**********************************************************************/
void reboot() { ESP.restart(); }
