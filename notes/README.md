# notes/ — Waveshare ESP32-S3-Touch-LCD-3.49 V2

Working notes for porting the Launcher and other ESP32 firmwares to the
640 × 172 Waveshare 3.49" V2.

| File | What it is |
|---|---|
| [00-launcher-port-plan.md](00-launcher-port-plan.md) | Phased plan to add this board to the Launcher |
| [01-hardware-reference.md](01-hardware-reference.md) | Verified pins, expander map, display, touch, backlight and power facts, with sources |
| [02-display-adaptation-guide.md](02-display-adaptation-guide.md) | How to show non-640×172 firmware UIs: compositor and presentation modes |
| [03-firmware-porting-playbook.md](03-firmware-porting-playbook.md) | Step-by-step checklist for each third-party firmware port |
| [04-open-questions-and-risks.md](04-open-questions-and-risks.md) | Risks and decisions still pending |
| [05-decisions.md](05-decisions.md) | Owner decisions: forks, buttons, catalogue, flip, licences |
| [06-bsp-library-design.md](06-bsp-library-design.md) | Proposed shared `WaveShare_3.49_BSP` library |
| [ports/bruce.md](ports/bruce.md) · [ports/meshtastic.md](ports/meshtastic.md) · [ports/marauder.md](ports/marauder.md) | Plan for each firmware port (recommended order: Bruce, Meshtastic, Marauder) |

Source-of-truth order for hardware facts:
1. DeskBar-AI (`C:\Users\rahul\OpenCode\TuneBar`), which runs on this board.
2. Waveshare V2 repo (`C:\Users\rahul\OpenCode\ESP32-S3-Touch-LCD-3.49-V2`).
3. The knowledge wiki (`C:\Users\rahul\OpenCode\opencode_knowledge\wiki\projects\tunebar\`).
4. Anything from the web: verify before use.
