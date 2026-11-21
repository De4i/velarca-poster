#!/usr/bin/env python3
"""
Velarca — a travel poster for a place that does not exist. (v3)

Renders entry.png (1024 x 1024). v3 changes the rendering register:
the scene is a rich painterly gouache painting (poster/scene.png,
generated for this entry) of the invented bay of VELARCA — a great
natural stone arch in a turquoise lagoon with the sun inside its
opening, a whitewashed terraced village with a chapel and cafe,
bougainvillea, swimmers and two sailboats — alive with people and
warm light, in the manner of the classic travel posters. This script
composites the poster's typography onto the painting: the place's
name, the only copy on the poster, set large in cream serif capitals
across the open sky at the top over a soft shade gradient, finished
with the cream-and-gold paper frame. Eye path: name -> sunlit arch
-> sparkling lagoon.

The composite is fully deterministic: fixed assets, fixed geometry,
no randomness, no network, no timestamps. Two runs produce a
byte-identical PNG. If the plain PNG exceeds the 1 MiB competition
limit, the image is palette-quantised inside this script until it
fits.

Run:  python3 poster/build_poster.py
Out:  entry.png next to main.ts, at the repository root.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent          # poster/
ROOT = HERE.parent                               # repository root
OUT_PATH = ROOT / "entry.png"
SCENE_PATH = HERE / "scene.png"

SIZE = 1024                  # final canvas, px
F = 2                        # supersample factor while drawing
W = SIZE * F
MAX_BYTES = 1_048_576

FONT_DIR = Path("/usr/share/fonts/truetype")
SERIF_BOLD = FONT_DIR / "liberation" / "LiberationSerif-Bold.ttf"

PAPER = (246, 238, 216)
GOLD = (216, 164, 82)
GOLD_SOFT = (232, 190, 110)
CREAM = (252, 243, 218)


def B(box):
    return [v * F for v in box]


def P(pts):
    return [(x * F, y * F) for (x, y) in pts]


# ---------------------------------------------------------------------------
# The painting, fitted to the square canvas
# ---------------------------------------------------------------------------
scene = Image.open(SCENE_PATH).convert("RGB")
img = scene.resize((W, W), Image.LANCZOS).convert("RGBA")

# Soft shade gradient across the top sky so the cream name sits on a
# deeper ground and stays legible over the amber sky.
shade = Image.new("RGBA", (W, W), (0, 0, 0, 0))
spx = shade.load()
top_col = (58, 26, 34)
for y in range(int(330 * F)):
    t = y / (330 * F)
    a = int(168 * (1 - t) ** 1.6)
    for x in range(0, W, 8):
        for dx in range(8):
            spx[x + dx, y] = top_col + (a,)
img = Image.alpha_composite(img, shade)
d = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------------------
# The name — the only copy on the poster — and its gold rule
# ---------------------------------------------------------------------------
NAME = "VELARCA"

def spaced_text(draw, centre_x, top, text, font, tracking, fill, shadow=None):
    widths = []
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        widths.append(bbox[2] - bbox[0])
    total = sum(widths) + tracking * (len(text) - 1)
    x = centre_x - total / 2
    for ch, w in zip(text, widths):
        if shadow:
            draw.text((x + shadow[0], top + shadow[1]), ch, font=font, fill=shadow[2])
        draw.text((x, top), ch, font=font, fill=fill)
        x += w + tracking
    return total

name_font = ImageFont.truetype(str(SERIF_BOLD), int(150 * F))
spaced_text(d, 512 * F, 60 * F, NAME, name_font, int(22 * F),
            CREAM + (255,), shadow=(int(3 * F), int(5 * F), (46, 20, 30, 190)))
# Gold rule with a centre diamond, under the name.
rule_y = 244
d.line(B([206, rule_y, 468, rule_y]), fill=GOLD + (255,), width=int(3.6 * F))
d.line(B([556, rule_y, 818, rule_y]), fill=GOLD + (255,), width=int(3.6 * F))
cx, cy, r = 512, rule_y, 12
d.polygon(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), fill=GOLD + (255,))
for ex in (190, 834):
    d.ellipse(B([ex - 4, rule_y - 4, ex + 4, rule_y + 4]), fill=GOLD + (255,))

# ---------------------------------------------------------------------------
# Paper frame, gentle vignette, downscale, size guard
# ---------------------------------------------------------------------------
fw = 26
d.rectangle(B([fw, fw, SIZE - fw, SIZE - fw]), outline=PAPER + (255,), width=int(10 * F))
d.rectangle(B([fw + 16, fw + 16, SIZE - fw - 16, SIZE - fw - 16]),
            outline=GOLD_SOFT + (210,), width=int(2.4 * F))

img = img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)

vig = Image.new("L", (SIZE, SIZE), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-SIZE * 0.42, -SIZE * 0.42, SIZE * 1.42, SIZE * 1.42], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(radius=90))
black = Image.new("RGB", (SIZE, SIZE), (12, 9, 16))
img = Image.composite(img, Image.blend(img, black, 0.30), vig)

buf = io.BytesIO()
img.save(buf, format="PNG", optimize=True)
data = buf.getvalue()
if len(data) > MAX_BYTES:
    for colours in (256, 224, 192, 160, 128):
        q = img.quantize(colors=colours, method=Image.MEDIANCUT,
                         dither=Image.FLOYDSTEINBERG)
        buf = io.BytesIO()
        q.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            break

OUT_PATH.write_bytes(data)
print(f"velarca v3: wrote {OUT_PATH} ({len(data)} bytes, {SIZE}x{SIZE})")
