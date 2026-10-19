#!/usr/bin/env python3
"""Drive the Launcher's serial console from a host, adb-style.

    python support_files/serial_cli.py COM11 status "tap 320 86" "nav next"
    python support_files/serial_cli.py COM11 screenshot -o shot.png

Each argument is sent as one console line; replies are printed. A
`screenshot` reply (===BEGIN_BMP:<n>=== ... ===END_BMP===) is saved to -o
(PNG if Pillow is installed and the name ends in .png, BMP otherwise).

The port is opened with DTR and RTS cleared: on native USB-Serial/JTAG
boards asserting them on open resets the chip or holds it in download mode.
"""
import argparse
import io
import re
import sys
import time

import serial

BEGIN = re.compile(rb"===BEGIN_BMP:(\d+)===\r?\n")


def open_port(port, baud):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = port, baud, 0.1
    s.dtr = s.rts = False
    s.open()
    return s


def read_reply(s, quiet_s):
    """Read until the line goes quiet for quiet_s seconds."""
    buf, last = b"", time.time()
    while time.time() - last < quiet_s:
        chunk = s.read(65536)
        if chunk:
            buf += chunk
            last = time.time()
    return buf


def read_screenshot(s, timeout_s=20):
    buf, start = b"", time.time()
    while time.time() - start < timeout_s:
        buf += s.read(65536)
        m = BEGIN.search(buf)
        if m and len(buf) >= m.end() + int(m.group(1)):
            size = int(m.group(1))
            return buf[: m.start()], buf[m.end() : m.end() + size]
    raise TimeoutError("no complete ===BEGIN_BMP=== block received")


def save_image(bmp, path):
    if path.lower().endswith(".png"):
        try:
            from PIL import Image

            Image.open(io.BytesIO(bmp)).save(path)
            return
        except ImportError:
            path = path[:-4] + ".bmp"
    with open(path, "wb") as f:
        f.write(bmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("port")
    ap.add_argument("commands", nargs="+")
    ap.add_argument("-o", "--output", default="screenshot.png", help="screenshot file (.png or .bmp)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("-q", "--quiet", type=float, default=0.6, help="seconds of silence that end a reply")
    args = ap.parse_args()

    s = open_port(args.port, args.baud)
    try:
        s.reset_input_buffer()
        for cmd in args.commands:
            s.write((cmd + "\n").encode())
            s.flush()
            if cmd.strip().lower() == "screenshot":
                text, bmp = read_screenshot(s)
                sys.stdout.write(text.decode("utf-8", "replace"))
                save_image(bmp, args.output)
                print(f"saved {args.output} ({len(bmp)} bytes)")
                read_reply(s, args.quiet)  # drain ===END_BMP===
            else:
                sys.stdout.write(read_reply(s, args.quiet).decode("utf-8", "replace"))
    finally:
        s.close()


if __name__ == "__main__":
    main()
