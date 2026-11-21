#!/usr/bin/env python3
"""
Velarca — a travel poster for a place that does not exist.

Renders entry.png (1024 x 1024): a vintage flat-style travel poster for
the invented bay of VELARCA, whose one landmark is a great natural stone
arch standing in a turquoise lagoon. The setting sun sits inside the
arch's opening, a whitewashed terraced village climbs the dark headland
on the left, and two small sailboats cross the water. The place's name
is the only copy on the poster, set large in cream serif capitals at
the top so the eye travels name -> sunlit arch -> lagoon horizon.

Everything is drawn with Pillow primitives at 2x and downscaled, so the
edges are smooth and the render is fully deterministic: no randomness
without a fixed seed, no network, no timestamps. Two runs produce a
byte-identical PNG. If the plain PNG ever exceeds the 1 MiB competition
limit, the image is palette-quantised inside this script until it fits.

Run:  python3 poster/build_poster.py
Out:  entry.png next to main.ts, at the repository root.
"""

from __future__ import annotations

import io
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent          # poster/
ROOT = HERE.parent                               # repository root
OUT_PATH = ROOT / "entry.png"

SIZE = 1024                  # final canvas, px
F = 2                        # supersample factor while drawing
W = SIZE * F
MAX_BYTES = 1_048_576

FONT_DIR = Path("/usr/share/fonts/truetype")
SERIF_BOLD = FONT_DIR / "liberation" / "LiberationSerif-Bold.ttf"
SERIF = FONT_DIR / "liberation" / "LiberationSerif-Regular.ttf"

# ---------------------------------------------------------------------------
# Palette — sunset over a teal lagoon, plum rock, cream paper
# ---------------------------------------------------------------------------
PAPER = (246, 238, 216)
GOLD = (216, 164, 82)
GOLD_SOFT = (232, 190, 110)
CREAM = (252, 243, 218)
SKY_TOP = (38, 34, 74)         # deep indigo-plum
SKY_MID = (104, 62, 102)       # mauve
SKY_LOW = (214, 116, 84)       # coral
SKY_HOR = (250, 178, 102)      # amber horizon
SEA_TOP = (238, 158, 96)       # sunlit water at the horizon
SEA_MID = (44, 128, 128)       # teal
SEA_DEEP = (16, 62, 84)        # deep teal foreground
ROCK = (74, 44, 58)            # plum-brown arch rock
ROCK_DARK = (52, 30, 46)
ROCK_RIM = (196, 110, 76)      # warm rim light on the sun side
HEADLAND = (43, 30, 54)        # dark violet headland silhouette
HOUSE = (243, 234, 214)        # whitewashed walls
ROOF = (178, 84, 52)           # terracotta
WINDOW = (255, 196, 92)        # lit windows
SAIL = (250, 244, 224)
HULL = (40, 26, 40)


def X(v: float) -> float:
    return v * F


def P(pts):
    return [(x * F, y * F) for (x, y) in pts]


def B(box):
    return [v * F for v in box]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(width, height, stops):
    """Vertical gradient image; stops = [(pos0..1, colour), ...]."""
    img = Image.new("RGB", (1, height))
    px = img.load()
    for y in range(height):
        t = y / max(1, height - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                px[0, y] = lerp(c0, c1, (t - p0) / max(1e-6, p1 - p0))
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((width, height))


# ---------------------------------------------------------------------------
# Canvas: sky, then sea, joined at the horizon
# ---------------------------------------------------------------------------
HORIZON = 648

img = vgrad(W, W, [
    (0.00, SKY_TOP),
    (0.30, SKY_MID),
    (0.50, SKY_LOW),
    (0.632, SKY_HOR),
    (0.648, SEA_TOP),
    (0.72, SEA_MID),
    (1.00, SEA_DEEP),
])
d = ImageDraw.Draw(img, "RGBA")

rng = random.Random(20261121)

# Stars fading into the upper sky.
for _ in range(150):
    sx = rng.uniform(0, SIZE)
    sy = rng.uniform(0, 300) * (1 - rng.random() * 0.35)
    r = rng.uniform(0.7, 1.9)
    a = int(rng.uniform(50, 165) * (1 - sy / 340))
    if a <= 0:
        continue
    d.ellipse(B([sx - r, sy - r, sx + r, sy + r]), fill=(255, 246, 224, a))

# Soft horizontal cloud bands, drawn on their own layer and blurred hard
# so they read as thin sunset cloud, not solid shapes.
clouds = Image.new("RGBA", (W, W), (0, 0, 0, 0))
cd = ImageDraw.Draw(clouds)
for (cy, cw, col, al) in [
    (268, 300, (250, 170, 120), 52),
    (318, 380, (238, 138, 110), 58),
    (372, 250, (252, 186, 118), 54),
    (300, 170, (120, 74, 116), 66),
    (408, 330, (246, 156, 104), 42),
]:
    cx = 512 + (rng.uniform(-140, 140))
    cd.ellipse(B([cx - cw, cy - 8, cx + cw, cy + 8]), fill=col + (al,))
clouds = clouds.filter(ImageFilter.GaussianBlur(radius=7 * F))
img = Image.alpha_composite(img.convert("RGBA"), clouds)
d = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------------------
# The sun, low and centred on the arch opening, with a warm halo
# ---------------------------------------------------------------------------
SUN_C = (637, 512)
SUN_R = 108
for r, a in [(SUN_R * 1.22, 46)]:
    d.ellipse(B([SUN_C[0] - r, SUN_C[1] - r, SUN_C[0] + r, SUN_C[1] + r]),
              fill=(255, 176, 92, a))
d.ellipse(B([SUN_C[0] - SUN_R, SUN_C[1] - SUN_R, SUN_C[0] + SUN_R, SUN_C[1] + SUN_R]),
          fill=(255, 196, 100, 255))

# Distant headlands on the horizon, left and right of the arch.
d.polygon(P([(0, 648), (0, 606), (90, 592), (210, 600), (330, 620), (420, 636), (470, 648)]),
          fill=(88, 52, 84, 235))
d.polygon(P([(1024, 648), (1024, 612), (950, 600), (880, 612), (830, 630), (810, 648)]),
          fill=(88, 52, 84, 235))

# ---------------------------------------------------------------------------
# The great arch — Velarca's one landmark. Drawn on its own layer so the
# opening can be cut clean through to the sun and the water behind it.
# ---------------------------------------------------------------------------
arch = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ad = ImageDraw.Draw(arch)
# Two legs and a domed beam as one mass.
ad.rectangle(B([446, 400, 570, 700]), fill=ROCK + (255,))
ad.rectangle(B([706, 400, 830, 700]), fill=ROCK + (255,))
ad.ellipse(B([424, 292, 852, 540]), fill=ROCK + (255,))
# The dome's top silhouette stays smooth and stony.
# Slightly wider feet where the legs meet the water.
ad.polygon(P([(446, 700), (446, 640), (570, 640), (586, 700)]), fill=ROCK + (255,))
ad.polygon(P([(690, 700), (706, 640), (830, 640), (830, 700)]), fill=ROCK + (255,))
# Cut the opening: a tall rounded arch window through the rock, wide
# enough to frame the sun's disc.
ad.rectangle(B([548, 452, 728, 700]), fill=(0, 0, 0, 0))
ad.ellipse(B([548, 362, 728, 560]), fill=(0, 0, 0, 0))
# Shading: darker bases in the water, on the two legs only so the
# opening stays clear. Solid colours here: on this layer a translucent
# fill would replace the layer's alpha and let the sea show through.
ad.rectangle(B([446, 646, 570, 700]), fill=(61, 36, 51, 255))
ad.rectangle(B([706, 646, 830, 700]), fill=(61, 36, 51, 255))
# Warm rim light where the sun strikes the opening's left inner edge.
ad.rectangle(B([548, 460, 560, 650]), fill=ROCK_RIM + (255,))
# Short pale strata dashes on the beam's shoulders.
ad.line(B([472, 428, 540, 420]), fill=(150, 84, 66, 255), width=int(4 * F))
ad.line(B([736, 420, 804, 428]), fill=(150, 84, 66, 255), width=int(4 * F))
# Rim light along the dome's top edge.
ad.arc(B([424, 292, 852, 540]), start=185, end=355, fill=(150, 84, 70, 255), width=int(5 * F))
arch.putalpha(arch.split()[3])
img = Image.alpha_composite(img.convert("RGBA"), arch)
d = ImageDraw.Draw(img, "RGBA")

# Foam where the arch legs meet the water.
for cx in (512, 762):
    for i in range(7):
        fx = cx + rng.uniform(-52, 52)
        fw = rng.uniform(16, 46)
        d.line(B([fx - fw, 694 + i * 3.2, fx + fw, 694 + i * 3.2]),
               fill=(255, 240, 210, int(120 - i * 13)), width=int(2.4 * F))

# Sun path on the water: broken gold dashes that shorten, thin and fade
# as they come toward the viewer.
for i in range(19):
    y = 672 + i * 11.5
    half = (64 * (1 - i / 30) + 8) * rng.uniform(0.45, 1.0)
    off = rng.uniform(-9, 9)
    a = int(200 - i * 10.5)
    if a <= 0:
        break
    d.line(B([SUN_C[0] - half + off, y, SUN_C[0] + half + off, y]),
           fill=(255, 190, 96, a), width=int(3.8 * F))

# ---------------------------------------------------------------------------
# Left headland with the terraced village
# ---------------------------------------------------------------------------
d.polygon(P([(0, 1024), (0, 640), (70, 606), (168, 584), (262, 606),
             (330, 652), (372, 724), (388, 830), (396, 1024)]), fill=HEADLAND + (255,))
d.polygon(P([(0, 1024), (0, 700), (120, 668), (250, 690), (340, 760),
             (372, 880), (380, 1024)]), fill=(34, 23, 44, 255))
# Whitewashed houses with terracotta roofs, staggered up the slope in
# three loose rows that follow the headland's top edge.
houses = [
    (74, 612, 30, 23), (118, 598, 27, 21), (160, 592, 31, 24), (206, 598, 27, 21),
    (248, 612, 30, 23), (62, 668, 27, 21), (104, 654, 31, 24), (150, 648, 27, 21),
    (194, 652, 31, 24), (240, 666, 27, 21), (88, 722, 30, 23), (134, 710, 27, 21),
    (178, 710, 31, 24), (224, 724, 27, 21), (116, 776, 29, 22), (164, 770, 30, 23),
]
for (hx, hy, hw, hh) in houses:
    d.rectangle(B([hx, hy, hx + hw, hy + hh]), fill=HOUSE + (255,))
    d.polygon(P([(hx - 4, hy), (hx + hw / 2, hy - 12), (hx + hw + 4, hy)]), fill=ROOF + (255,))
    for _ in range(2):
        wx = hx + rng.uniform(5, hw - 9)
        wy = hy + rng.uniform(6, hh - 10)
        d.rectangle(B([wx, wy, wx + 4.5, wy + 6]), fill=WINDOW + (255,))
# Dark cypress spires between the houses.
for (tx, ty, th) in [(100, 640, 34), (188, 636, 40), (268, 652, 32), (128, 700, 34), (216, 700, 38)]:
    d.polygon(P([(tx - 6, ty), (tx, ty - th), (tx + 6, ty)]), fill=(24, 38, 34, 255))

# A tiny chapel bell tower above the village.
d.rectangle(B([168, 546, 186, 594]), fill=HOUSE + (255,))
d.polygon(P([(164, 546), (177, 526), (190, 546)]), fill=ROOF + (255,))
d.ellipse(B([173, 554, 181, 564]), fill=HEADLAND + (255,))

# ---------------------------------------------------------------------------
# Sailboats on the lagoon
# ---------------------------------------------------------------------------
def sailboat(cx, cy, s, flip=1):
    d.polygon(P([(cx - 34 * s, cy), (cx + 34 * s, cy), (cx + 22 * s, cy + 12 * s),
                 (cx - 22 * s, cy + 12 * s)]), fill=HULL + (255,))
    d.line(B([cx, cy - 52 * s, cx, cy]), fill=HULL + (255,), width=int(3 * F))
    d.polygon(P([(cx + 3 * s, cy - 50 * s), (cx + 3 * s, cy - 4 * s),
                 (cx + 30 * s * flip, cy - 4 * s)]), fill=SAIL + (255,))
    d.polygon(P([(cx - 3 * s, cy - 42 * s), (cx - 3 * s, cy - 4 * s),
                 (cx - 24 * s * flip, cy - 4 * s)]), fill=(238, 226, 198, 255))
    d.line(B([cx - 26 * s, cy + 22 * s, cx + 26 * s, cy + 22 * s]),
           fill=(255, 235, 200, 90), width=int(3 * F))

sailboat(452, 786, 0.95)
sailboat(856, 838, 0.8, flip=-1)

# Birds: small paired arcs in the morning of the sky.
for (bx, by, bs) in [(238, 300, 13), (282, 278, 10), (196, 262, 9), (842, 250, 11), (884, 276, 9)]:
    d.arc(B([bx - bs, by - bs * 0.6, bx, by + bs * 0.6]), start=200, end=330,
          fill=(30, 22, 40, 220), width=int(2.6 * F))
    d.arc(B([bx, by - bs * 0.6, bx + bs, by + bs * 0.6]), start=210, end=340,
          fill=(30, 22, 40, 220), width=int(2.6 * F))

# ---------------------------------------------------------------------------
# Foreground palms framing the bottom corners
# ---------------------------------------------------------------------------
def palm(cx, cy, s, flip=1):
    # Curved trunk built from stacked segments, tapering toward the top.
    pts = []
    for i in range(15):
        t = i / 14
        pts.append((cx + flip * 26 * s * t * t, cy - 118 * s * t))
    for j, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        d.line(B([x0, y0, x1, y1]), fill=(26, 18, 32, 255),
               width=max(2, int((9 - j * 0.45) * F)))
    tx, ty = pts[-1]
    for ang in (-168, -138, -106, -74, -42, -14):
        a = math.radians(ang if flip > 0 else 180 - ang)
        frond = []
        for i in range(13):
            t = i / 12
            frond.append((tx + math.cos(a) * 96 * s * t,
                          ty + math.sin(a) * 62 * s * t + 30 * s * t * t))
        for (x0, y0), (x1, y1) in zip(frond, frond[1:]):
            d.line(B([x0, y0, x1, y1]), fill=(26, 18, 32, 255), width=int(4.5 * F))

palm(948, 1036, 1.05, flip=-1)
# Dark foreground rocks in the bottom right corner.
d.polygon(P([(742, 1024), (830, 972), (930, 962), (1010, 990), (1024, 1024)]),
          fill=(30, 20, 38, 255))

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

name_font = ImageFont.truetype(str(SERIF_BOLD), int(138 * F))
spaced_text(d, X(512), X(88), NAME, name_font, int(26 * F),
            CREAM + (255,), shadow=(int(3 * F), int(4 * F), (40, 20, 44, 160)))
# Gold rule with a centre diamond, under the name.
rule_y = 248
d.line(B([212, rule_y, 470, rule_y]), fill=GOLD + (255,), width=int(3.4 * F))
d.line(B([554, rule_y, 812, rule_y]), fill=GOLD + (255,), width=int(3.4 * F))
cx, cy, r = 512, rule_y, 11
d.polygon(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), fill=GOLD + (255,))
for ex in (196, 828):
    d.ellipse(B([ex - 4, rule_y - 4, ex + 4, rule_y + 4]), fill=GOLD + (255,))

# ---------------------------------------------------------------------------
# Paper frame, vignette, downscale, size guard
# ---------------------------------------------------------------------------
fw = 26
d.rectangle(B([fw, fw, SIZE - fw, SIZE - fw]), outline=PAPER + (255,), width=int(10 * F))
d.rectangle(B([fw + 16, fw + 16, SIZE - fw - 16, SIZE - fw - 16]),
            outline=GOLD_SOFT + (210,), width=int(2.4 * F))

img = img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)

# Gentle corner vignette.
vig = Image.new("L", (SIZE, SIZE), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-SIZE * 0.42, -SIZE * 0.42, SIZE * 1.42, SIZE * 1.42], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(radius=90))
black = Image.new("RGB", (SIZE, SIZE), (10, 8, 18))
img = Image.composite(img, Image.blend(img, black, 0.42), vig)

buf = io.BytesIO()
img.save(buf, format="PNG", optimize=True)
data = buf.getvalue()
if len(data) > MAX_BYTES:
    for colours in (256, 224, 192, 160):
        q = img.quantize(colors=colours, method=Image.MEDIANCUT,
                         dither=Image.FLOYDSTEINBERG)
        buf = io.BytesIO()
        q.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            break

OUT_PATH.write_bytes(data)
print(f"velarca: wrote {OUT_PATH} ({len(data)} bytes, {SIZE}x{SIZE})")
