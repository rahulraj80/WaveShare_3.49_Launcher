#!/usr/bin/env python3
"""Update an app the Launcher already installed, keeping its data.

    python support_files/update_app.py COM11 deskb1 firmware.bin

Writes the app image (an app-only firmware.bin, not a merged image) straight
into the existing slot of the app with that partition label. Its data
partitions (LittleFS/SPIFFS/FAT: settings, WiFi lists, ...) are not touched.

Don't update by installing a full image from the SD card again: the Launcher
then makes a new slot and writes the image's data partition over the old one.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import to_launcher  # noqa: E402

ROW = re.compile(r"^(\S+)\s+type=app\s+subtype=(ota_\d+)\s+offset=0x([0-9A-Fa-f]+)\s+size=0x([0-9A-Fa-f]+)", re.M)


def read_partitions(port):
    s = to_launcher.open_port(port)
    try:
        return to_launcher.ask(s, "partitions", quiet_s=1.5).decode("utf-8", "replace")
    finally:
        s.close()


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    port, label, image = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    data = image.read_bytes()
    if data[:1] != b"\xe9":
        print(f"{image} is not an app image (no 0xE9 magic); pass firmware.bin, not a merged .bin")
        return 1

    if to_launcher.main_for(port) != 0:
        return 1
    slots = {m.group(1): (m.group(2), int(m.group(3), 16), int(m.group(4), 16)) for m in ROW.finditer(read_partitions(port))}
    if label not in slots:
        print(f"no installed app labelled {label!r}; installed: {', '.join(slots) or 'none'}")
        return 1
    subtype, offset, size = slots[label]
    if len(data) > size:
        print(f"{image.name} is {len(data)} bytes but slot {label} holds {size}")
        return 1

    print(f"writing {image.name} ({len(data)} bytes) into {label} ({subtype}) at 0x{offset:06X}")
    time.sleep(0.5)
    cmd = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "-p", port, "-b", "460800",
           "write-flash", f"0x{offset:X}", str(image)]
    rc = subprocess.call(cmd)
    if rc != 0:
        return rc

    # esptool's reset boots whichever app was selected last; start this one.
    time.sleep(6)
    if to_launcher.main_for(port) != 0:
        return 1
    s = to_launcher.open_port(port)
    try:
        print(to_launcher.ask(s, f"boot {label}").decode("utf-8", "replace").strip())
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
