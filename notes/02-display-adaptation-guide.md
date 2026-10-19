# Fitting other firmwares onto a 640 × 172 screen

No ESP32 firmware targets 640 × 172. Every port has to put content designed
for another resolution onto a 3.7 : 1 strip, roughly 85 × 23 mm. This guide
gives one shared mechanism and several **presentation modes** on top of it, so
each new port is a configuration choice, not a new display driver.

## 1. The physical constraint: the panel only takes full frames

The AXS15231B in QSPI mode on this board does not accept a row window
(see `01-hardware-reference.md`). Every refresh streams all 220 KB.

That decides the architecture:

- The panel always shows a **composed 640 × 172 frame**.
- A ported firmware never draws to the panel directly. It draws to a
  **virtual screen** (its native resolution) held in PSRAM.
- A **compositor** builds the panel frame from:
  1. one or more rectangles of the virtual screen, each at a scale;
  2. our own **chrome**: navigation buttons, scroll indicator, status.
- Every mode below costs the same bus time, about 11 ms per frame.
  Scrolling, zoom and split views add no bus cost, only PSRAM copies.

```
  ported firmware ──draws──▶ virtual screen (W×H, PSRAM)
                                 │  dirty flag / frame counter
  touch, BOOT, PWR ──▶ input mapper ◀── mode config
                                 │
                        compositor (mode) ──▶ 640×172 frame ──▶ QSPI flush (≤30 Hz)
```

PSRAM copy budget: composing one frame reads up to 220 KB and writes 220 KB.
At 30 fps that is about 13 MB/s, well within OPI PSRAM bandwidth.
Recompose **only when the virtual screen is dirty or the viewport moved**.
Otherwise skip the flush entirely.

## 2. The readability constraint

At about 190 ppi, a classic 6×8 font at scale 1 is about 1 mm tall. Rules:

- Plan for the **ported UI's smallest text to land at ≥ 12 px, ideally 16 px**.
- **Integer scale factors only** (1×, 2×). Fractional nearest-neighbour
  scaling of bitmap fonts is unreadable. Fractional *downscaling* needs area
  averaging, which costs CPU and blurs text.
- A firmware that already draws at text size ≥ 2 can run at 1×. One that
  draws at text size 1 needs 2× or a source patch.

## 3. Source resolutions we will meet

| Source | Typical devices | At 1× | At 2× |
|---|---|---|---|
| 320 × 170 / 172 | T-Display-S3, Waveshare/Seeed 1.47" | **fits exactly**, 320 px spare | 640×344, 50% visible |
| 240 × 135 | M5StickC Plus/Plus2, T-Display | fits, 400 px spare | 480×270, 64% visible |
| 160 × 80 | T-Dongle-S3 | tiny | 320×160 fits, 320 px spare |
| 240 × 240 | round watches, small squares | 172 of 240 rows | — |
| 320 × 240 | CYD, M5 Core, Cardputer-ish | 172 of 240 rows (72%) | — |
| 536 × 240 | T-Display-S3 AMOLED | 172 of 240 rows | — |
| 480 × 320 | CYD 3.5" | 54% of rows | — |
| 172 × 320 / 170 × 320 portrait | same panels rotated | use them in landscape | — |

**The 320 × 170/172 class is the jackpot.** Firmware written for it runs
pixel-perfect in half our screen and leaves 320 px for controls. Look for a
T-Display-S3 or LCD-1.47 build of any firmware first.

## 4. Presentation modes

All modes are configurations of the same compositor. Options 1–3 from the
original brief map to modes B, C and D. Mode A is new and cheapest.

### Mode A: native window + control rail (recommended first)

- The virtual screen is shown 1:1 (or 2×) in a fixed rectangle. The rest of
  the strip is a touch control rail.
- 320×172 source: content at x 0–319, rail at 320–639 (320 px: D-pad,
  OK, Back, plus a firmware-specific key row).
- 240×135 source: centre it vertically (18 px bands) with a 400 px rail, or
  use 2× (480×270) with vertical scroll, which falls into mode C.
- Rail side should be configurable (left/right) for handedness and the IMU flip.
- **Best for button-driven firmware** (most of the catalogue). The rail
  emulates the buttons the firmware expects.

### Mode B: fold (your option 1, "two 320×172 columns")

- The virtual screen is 320 × 344. Rows 0–171 go in the left column and rows
  172–343 in the right column.
- Shows a 320×240 or 320×344 source in full at 1× with no scrolling. The cost
  is a visual seam: content wraps from the bottom-left to the top-right.
- Works for list or log UIs (sniffers, serial monitors, menus longer than
  172 px). Poor for anything spatial (maps, games, graphs that cross the seam).
- Variant **B2, dual screen**: two independent 320×172 virtual screens, e.g.
  firmware main view plus a status or log pane. Useful when we control the
  firmware source.
- Leaves no room for chrome, so input must be touch-in-place or physical keys.
  Reserve a thin 8–12 px strip or a long-press overlay for Back.

### Mode C: viewport + navigation rail (your option 2)

- The virtual screen is 480 wide × any height (320×240 at 1.5× is not
  integer; prefer 480-wide **sources**, or 240-wide sources at 2×).
- A 480 × 172 viewport scrolls vertically over it. The 160 × 172 rail holds
  scroll up/down, select, back and a position indicator.
- Auto-follow: if the firmware has a "selected item" or cursor concept,
  scroll to keep it visible. This needs a hook in the firmware or a
  heuristic on dirty regions (scroll to the last changed rows).
- Good for touch-light firmware with tall menus.

### Mode D: fit-width pan and zoom (your option 3)

- The virtual screen is scaled to 640 wide (integer: 320-wide sources at 2×,
  so 320×240 becomes 640×480). A 172 px viewport pans with swipes.
- Taps map back through the inverse transform to virtual coordinates, so
  **touch-native firmware works unchanged**.
- Downsides: only 36% of a 2× 320×240 screen is visible, so the user loses
  context. Swipe-vs-tap disambiguation must not steal taps the firmware needs
  (use a 10–15 px drag threshold and a 150 ms hold before panning).
- Add a "minimap" mode on long-press: a 0.5× fold of the whole screen
  (a 320×240 source at 0.717 fits 229×172) to jump around.

### Mode E: native rewrite (no compositor)

- For firmware we care about deeply (DeskBar itself, the Launcher), lay the
  UI out for 640×172 directly. Always best, always most work.

### Choosing

| Firmware trait | Mode |
|---|---|
| Has a 320×170/172 build | **A** at 1× |
| 240×135 or 160×80 build | **A** (2× for 160×80) |
| 320×240, button-driven, list UI | **B** fold, or **C** |
| 320×240 or 480×320, touch-driven | **D** |
| We own the source and it matters | **E** |

## 5. How a firmware gets its virtual screen

Most ESP32 firmwares draw through one of five libraries. The redirection
differs for each:

| Library | Redirect technique | Effort |
|---|---|---|
| **LVGL** | set `hor_res/ver_res` to the virtual size; `flush_cb` copies into the virtual buffer and marks it dirty | lowest |
| **LovyanGFX / M5GFX** | custom `Panel_Device` (or `Panel_FrameBuffer`) whose memory is the virtual buffer | low |
| **Arduino_GFX** | `Arduino_Canvas` over a no-op/compositor `Databus`; call our flush in `flush()` | low |
| **DisplayDrivers** (this Launcher) | `USE_CANVAS` plus a hook at canvas push | low |
| **TFT_eSPI** | no clean hook; it writes registers directly. Either fork with a "sprite as screen" macro shim, or add a custom `TFT_eSPI` processor file whose `pushPixels`/`setWindow` write to RAM | medium–high |

TFT_eSPI is common in pentest firmware (Bruce, Marauder). Budget for it.

## 6. Input mapping

Physical inputs: **BOOT (GPIO0)**, **PWR (GPIO16 sense)** and touch. That's all.

Ported firmware expects one of:

| Expected input | Our mapping |
|---|---|
| 1–3 buttons (M5StickC, T-Display) | rail buttons; BOOT = primary; long-PWR is reserved for power off |
| 5-way / D-pad / encoder | rail D-pad; swipe = scroll in modes C/D |
| Keyboard (Cardputer, T-Deck) | on-screen keyboard overlay (full 640×172; fits 12×4 keys at 53×~35 px) |
| Touch at native coords | inverse compositor transform (modes A, B and D) |

Reserve one gesture **globally** for "back to Launcher / system menu" so a
ported firmware can never trap the user. The candidate is a 3 s BOOT hold or
a PWR double-press. See `03-firmware-porting-playbook.md`.

## 7. Implementation shape (shared code, flash-size conscious)

- One small C/C++ module, e.g. `ws349_compositor`, independent of any
  graphics library. API sketch:
  - `vs_init(w, h, mode, cfg)` allocates the virtual buffer in PSRAM.
  - `vs_buffer()`, `vs_mark_dirty(y0, y1)`
  - `vs_input(touch, buttons)` returns mapped virtual touch or button events.
  - `vs_task()` composes and flushes (single bus owner, core 0, ≤30 Hz).
- Plus one adapter per graphics library (section 5): a few dozen lines each.
- The panel driver, expander and backlight code are shared with the Launcher
  board port. Write them once.
- Keep chrome drawing primitive (filled rects plus one bitmap font at 2×) so
  the module adds a few KB of flash, not an LVGL dependency.
- Live in a separate repo or library so ported firmwares can depend on it
  without vendoring the Launcher.

## 8. Validation per port

1. Liveness: solid fills via `validate_cycle.py` before judging anything.
2. Smallest text in the ported UI measured at ≥12 px on the panel.
3. Every screen of the firmware reachable using only rail, touch and BOOT.
4. "Back to Launcher" works from every screen.
5. Battery: unplug USB, confirm the device stays on (SYS_EN) and the
   backlight is lit.
6. Frame budget: compose plus flush < 33 ms, and no flush when idle (measure
   current draw).
