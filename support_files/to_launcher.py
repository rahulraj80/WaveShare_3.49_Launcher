#!/usr/bin/env python3
"""Bring the board to the Launcher's main menu over USB, without touching it.

    python support_files/to_launcher.py COM11

The keyboot bootloader starts the Launcher only after a power-on or a deep-sleep
wake; every soft reset (a flash, `reboot`, esptool's reset) boots the installed
app. So:
  1. If the Launcher already answers `version`, we are done.
  2. Otherwise ask the running app to `launcher` (our DeskBar and Bruce builds
     deep-sleep for 100 ms), wait for the Launcher's boot screen and send
     `nav sel` before its countdown boots the app again.
Exit code 0 when the Launcher answers at the end, 1 otherwise.
"""
import sys
import time

import serial

BOOT_PROMPT = b"Press the button to enter the Launcher!"


def open_port(port):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = port, 115200, 0.1
    s.dtr = s.rts = False
    s.open()
    return s


def ask(s, cmd, quiet_s=1.2):
    s.reset_input_buffer()
    s.write((cmd + "\n").encode())
    buf, last = b"", time.time()
    while time.time() - last < quiet_s:
        chunk = s.read(4096)
        if chunk:
            buf += chunk
            last = time.time()
    return buf


def in_launcher(port):
    try:
        s = open_port(port)
    except serial.SerialException:
        return False
    try:
        reply = ask(s, "version")
        # Still on the boot screen: its countdown would boot the app, so enter the menu.
        if BOOT_PROMPT in reply:
            ask(s, "nav sel")
        return b"Launcher" in reply
    finally:
        s.close()


def main():
    return main_for(sys.argv[1] if len(sys.argv) > 1 else "COM11")


def main_for(port):
    if in_launcher(port):
        print("already in the Launcher")
        return 0

    s = open_port(port)
    s.write(b"launcher\n")
    s.flush()
    print("asked the app to hand over (deep sleep)...")

    # The USB port drops while the chip sleeps and comes back with the
    # Launcher's boot screen; keep reopening it and watch for the prompt.
    deadline = time.time() + 20
    buf = b""
    while time.time() < deadline:
        try:
            chunk = s.read(4096)
        except serial.SerialException:
            s.close()
            while time.time() < deadline:
                try:
                    s = open_port(port)
                    break
                except serial.SerialException:
                    time.sleep(0.05)
            continue
        buf += chunk
        if BOOT_PROMPT in buf:
            s.write(b"nav sel\n")
            s.flush()
            break
    s.close()

    time.sleep(1.5)
    if in_launcher(port):
        print("in the Launcher")
        return 0
    print("Launcher did not answer: is the running app one of our builds (with a `launcher` command)?")
    return 1


if __name__ == "__main__":
    sys.exit(main())
