#!/usr/bin/env python3
"""
Velarca — a travel poster for a place that does not exist. (v2)

Renders entry.png (1024 x 1024): a vintage travel poster for the
invented bay of VELARCA, whose one landmark is a great natural stone
arch standing in a turquoise lagoon. The setting sun sits inside the
arch's opening, a whitewashed terraced village climbs the dark headland
on the left, one sailboat crosses the foreground water and a second,
tiny one is silhouetted inside the arch against the sun. The place's
name is the only copy on the poster, set large in cream serif capitals
at the top so the eye travels name -> sunlit arch -> lagoon horizon.

v2 over v1: a larger, more monumental arch with mottled rock texture
and strata bands, a radial sun glow, two-tone sunset clouds, a richer
sparkle field on the water, painterly grain over the whole picture,
and a cleaner composition (fewer houses, one foreground boat).

Everything is drawn with Pillow primitives at 2x and downscaled, so
the render is fully deterministic: no randomness without a fixed
seed, no network, no timestamps. Two runs produce a byte-identical
PNG. If the plain PNG ever exceeds the 1 MiB competition limit, the
image is palette-quantised inside this script until it fits.

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
SKY_TOP = (34, 30, 70)         # deep indigo-plum
SKY_MID = (110, 58, 100)       # mauve
SKY_LOW = (222, 112, 80)       # coral
SKY_HOR = (252, 182, 100)      # amber horizon
SEA_TOP = (240, 160, 94)       # sunlit water at the horizon
SEA_MID = (40, 130, 128)       # teal
SEA_DEEP = (13, 58, 82)        # deep teal foreground
ROCK = (78, 45, 58)            # plum-brown arch rock
ROCK_DARK = (50, 28, 44)
ROCK_RIM = (205, 112, 74)      # warm rim light on the sun side
HEADLAND = (41, 28, 52)        # dark violet headland silhouette
HOUSE = (244, 235, 215)        # whitewashed walls
ROOF = (182, 84, 50)           # terracotta
WINDOW = (255, 198, 92)        # lit windows
SAIL = (250, 244, 224)
HULL = (38, 24, 38)


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
    (0.26, SKY_MID),
    (0.47, SKY_LOW),
    (0.632, SKY_HOR),
    (0.648, SEA_TOP),
    (0.72, SEA_MID),
    (1.00, SEA_DEEP),
]).convert("RGBA")
d = ImageDraw.Draw(img, "RGBA")

rng = random.Random(20261122)

# Stars fading into the upper sky.
for _ in range(170):
    sx = rng.uniform(0, SIZE)
    sy = rng.uniform(0, 300) * (1 - rng.random() * 0.35)
    r = rng.uniform(0.7, 1.9)
    a = int(rng.uniform(50, 165) * (1 - sy / 340))
    if a <= 0:
        continue
    d.ellipse(B([sx - r, sy - r, sx + r, sy + r]), fill=(255, 246, 224, a))

# Two-tone sunset clouds: a lit amber belly under a mauve shadow top,
# drawn on their own layer and blurred so they read as thin cloud.
clouds = Image.new("RGBA", (W, W), (0, 0, 0, 0))
cd = ImageDraw.Draw(clouds)
for (cy, cw, off) in [(258, 320, -60), (312, 400, 90), (366, 260, -150),
                      (404, 340, 150), (292, 180, 260)]:
    cx = 512 + off + rng.uniform(-40, 40)
    cd.ellipse(B([cx - cw, cy - 13, cx + cw, cy + 3]), fill=(110, 60, 104, 74))
    cd.ellipse(B([cx - cw, cy - 2, cx + cw, cy + 9]), fill=(250, 168, 112, 66))
clouds = clouds.filter(ImageFilter.GaussianBlur(radius=6 * F))
img = Image.alpha_composite(img, clouds)
d = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------------------
# The sun, low and centred on the arch opening, with a radial glow
# ---------------------------------------------------------------------------
SUN_C = (638, 505)
SUN_R = 122
glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r, a in [(SUN_R * 2.5, 16), (SUN_R * 1.9, 26), (SUN_R * 1.45, 40)]:
    gd.ellipse(B([SUN_C[0] - r, SUN_C[1] - r, SUN_C[0] + r, SUN_C[1] + r]),
               fill=(255, 172, 88, a))
glow = glow.filter(ImageFilter.GaussianBlur(radius=18 * F))
img = Image.alpha_composite(img, glow)
d = ImageDraw.Draw(img, "RGBA")
d.ellipse(B([SUN_C[0] - SUN_R, SUN_C[1] - SUN_R, SUN_C[0] + SUN_R, SUN_C[1] + SUN_R]),
          fill=(255, 198, 100, 255))
d.ellipse(B([SUN_C[0] - SUN_R * 0.82, SUN_C[1] - SUN_R * 0.82,
             SUN_C[0] + SUN_R * 0.82, SUN_C[1] + SUN_R * 0.82]),
          fill=(255, 214, 130, 255))

# Distant headlands on the horizon, left and right of the arch.
d.polygon(P([(0, 648), (0, 606), (90, 592), (210, 600), (330, 620), (420, 636), (470, 648)]),
          fill=(92, 54, 86, 235))
d.polygon(P([(1024, 648), (1024, 612), (950, 600), (880, 612), (830, 630), (810, 648)]),
          fill=(92, 54, 86, 235))

# ---------------------------------------------------------------------------
# The great arch — Velarca's one landmark, larger and more monumental
# in v2. Drawn on its own layer so the opening can be cut clean through
# to the sun and the water behind it; rock texture is masked to the
# arch's own alpha so no translucent fill ever eats the opening.
# ---------------------------------------------------------------------------
arch = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ad = ImageDraw.Draw(arch)
# Two legs and a domed beam as one mass.
ad.rectangle(B([404, 380, 578, 706]), fill=ROCK + (255,))
ad.rectangle(B([698, 380, 872, 706]), fill=ROCK + (255,))
ad.ellipse(B([378, 246, 898, 528]), fill=ROCK + (255,))
# Slightly wider feet where the legs meet the water.
ad.polygon(P([(404, 706), (404, 636), (578, 636), (596, 706)]), fill=ROCK + (255,))
ad.polygon(P([(680, 706), (698, 636), (872, 636), (872, 706)]), fill=ROCK + (255,))
# Cut the opening: a tall rounded arch window through the rock, wide
# enough to frame the whole sun disc with sky to spare.
ad.rectangle(B([512, 446, 764, 706]), fill=(0, 0, 0, 0))
ad.ellipse(B([512, 344, 764, 556]), fill=(0, 0, 0, 0))
# Darker bases where the legs stand in the water.
ad.rectangle(B([404, 648, 578, 706]), fill=(58, 33, 48, 255))
ad.rectangle(B([698, 648, 872, 706]), fill=(58, 33, 48, 255))
# Rock texture: mottled patches and strata bands, on a separate layer
# masked by the arch alpha.
tex = Image.new("RGBA", (W, W), (0, 0, 0, 0))
td = ImageDraw.Draw(tex)
for _ in range(240):
    tx = rng.uniform(390, 890)
    ty = rng.uniform(250, 700)
    tr = rng.uniform(6, 30)
    shade = rng.choice([(0, 0, 0), (255, 190, 140), (30, 10, 26)])
    td.ellipse(B([tx - tr, ty - tr * 0.6, tx + tr, ty + tr * 0.6]),
               fill=shade + (rng.randint(18, 44),))
for (y0, y1, x0, x1) in [(330, 338, 430, 620), (356, 363, 660, 850),
                        (420, 427, 420, 560), (428, 435, 716, 856),
                        (300, 307, 520, 760)]:
    td.line(B([x0, y0, x1, y1]), fill=(30, 14, 26, 60), width=int(5 * F))
tex.putalpha(Image.composite(tex.split()[3], Image.new("L", (W, W), 0),
                             arch.split()[3]))
arch = Image.alpha_composite(arch, tex)
ad = ImageDraw.Draw(arch)
# Warm rim light where the sun strikes the opening's left inner edge,
# and a thinner one on the right.
ad.rectangle(B([512, 452, 526, 656]), fill=ROCK_RIM + (255,))
ad.rectangle(B([752, 470, 764, 640]), fill=(172, 92, 64, 255))
# Rim light along the dome's top edge.
ad.arc(B([378, 246, 898, 528]), start=185, end=355, fill=(158, 88, 70, 255),
       width=int(6 * F))
img = Image.alpha_composite(img, arch)
d = ImageDraw.Draw(img, "RGBA")

# A tiny distant sailboat silhouetted inside the arch, against the sun.
d.polygon(P([(606, 640), (670, 640), (660, 650), (616, 650)]), fill=(52, 26, 40, 255))
d.line(B([638, 588, 638, 640]), fill=(52, 26, 40, 255), width=int(2.6 * F))
d.polygon(P([(641, 590), (641, 636), (664, 636)]), fill=(52, 26, 40, 235))
d.polygon(P([(635, 598), (635, 636), (616, 636)]), fill=(52, 26, 40, 235))

# Foam where the arch legs meet the water.
for cx in (492, 784):
    for i in range(8):
        fx = cx + rng.uniform(-58, 58)
        fw = rng.uniform(16, 50)
        d.line(B([fx - fw, 696 + i * 3.2, fx + fw, 696 + i * 3.2]),
               fill=(255, 240, 210, int(125 - i * 13)), width=int(2.4 * F))

# Sun path on the water: broken gold dashes, plus a wider sparkle
# field of short glints scattered around the path.
for i in range(21):
    y = 668 + i * 11.5
    half = (72 * (1 - i / 32) + 8) * rng.uniform(0.45, 1.0)
    off = rng.uniform(-9, 9)
    a = int(205 - i * 10)
    if a <= 0:
        break
    d.line(B([SUN_C[0] - half + off, y, SUN_C[0] + half + off, y]),
           fill=(255, 192, 96, a), width=int(3.8 * F))
for _ in range(210):
    gx = SUN_C[0] + rng.gauss(0, 120)
    gy = rng.uniform(660, 990)
    gw = rng.uniform(3, 13) * (0.6 + (gy - 660) / 500)
    a = int(rng.uniform(28, 110) * (1 - abs(gx - SUN_C[0]) / 420))
    if a <= 4 or not (20 < gx < 1004):
        continue
    d.line(B([gx - gw, gy, gx + gw, gy]), fill=(255, 205, 120, a),
           width=int(2.2 * F))
# Subtle long wave bands in the foreground water.
for i in range(6):
    y = 856 + i * 26
    d.line(B([40, y, 984, y + rng.uniform(-4, 4)]),
           fill=(190, 230, 225, 10), width=int(3 * F))

# ---------------------------------------------------------------------------
# Left headland with the terraced village — fewer, larger houses in v2
# ---------------------------------------------------------------------------
d.polygon(P([(0, 1024), (0, 640), (70, 606), (168, 584), (262, 606),
             (330, 652), (372, 724), (388, 830), (396, 1024)]), fill=HEADLAND + (255,))
d.polygon(P([(0, 1024), (0, 700), (120, 668), (250, 690), (340, 760),
             (372, 880), (380, 1024)]), fill=(32, 21, 42, 255))
houses = [
    (84, 610, 36, 27), (142, 594, 33, 25), (202, 598, 36, 27),
    (72, 672, 33, 25), (128, 654, 37, 28), (186, 656, 33, 25),
    (102, 730, 36, 27), (162, 720, 33, 25), (222, 734, 30, 23),
    (128, 788, 35, 26), (188, 782, 36, 27),
]
for (hx, hy, hw, hh) in houses:
    d.rectangle(B([hx, hy, hx + hw, hy + hh]), fill=HOUSE + (255,))
    d.polygon(P([(hx - 4, hy), (hx + hw / 2, hy - 13), (hx + hw + 4, hy)]), fill=ROOF + (255,))
    for _ in range(2):
        wx = hx + rng.uniform(5, hw - 10)
        wy = hy + rng.uniform(6, hh - 11)
        d.rectangle(B([wx, wy, wx + 5, wy + 6.5]), fill=WINDOW + (255,))
# Dark cypress spires between the houses.
for (tx, ty, th) in [(112, 644, 38), (196, 640, 44), (268, 656, 34), (140, 706, 38), (224, 706, 42)]:
    d.polygon(P([(tx - 6, ty), (tx, ty - th), (tx + 6, ty)]), fill=(22, 36, 32, 255))

# A tiny chapel bell tower above the village.
d.rectangle(B([168, 544, 188, 596]), fill=HOUSE + (255,))
d.polygon(P([(163, 544), (178, 522), (193, 544)]), fill=ROOF + (255,))
d.ellipse(B([174, 553, 183, 564]), fill=HEADLAND + (255,))

# ---------------------------------------------------------------------------
# One foreground sailboat on the lagoon
# ---------------------------------------------------------------------------
def sailboat(cx, cy, s, flip=1):
    d.polygon(P([(cx - 36 * s, cy), (cx + 36 * s, cy), (cx + 23 * s, cy + 13 * s),
                 (cx - 23 * s, cy + 13 * s)]), fill=HULL + (255,))
    d.line(B([cx, cy - 55 * s, cx, cy]), fill=HULL + (255,), width=int(3 * F))
    d.polygon(P([(cx + 3 * s, cy - 53 * s), (cx + 3 * s, cy - 4 * s),
                 (cx + 32 * s * flip, cy - 4 * s)]), fill=SAIL + (255,))
    d.polygon(P([(cx - 3 * s, cy - 45 * s), (cx - 3 * s, cy - 4 * s),
                 (cx - 25 * s * flip, cy - 4 * s)]), fill=(238, 226, 198, 255))
    d.line(B([cx - 28 * s, cy + 24 * s, cx + 28 * s, cy + 24 * s]),
           fill=(255, 235, 200, 90), width=int(3 * F))

sailboat(430, 806, 1.15)

# Birds: small paired arcs in the upper sky.
for (bx, by, bs) in [(238, 300, 13), (282, 278, 10), (196, 262, 9), (842, 250, 11), (884, 276, 9)]:
    d.arc(B([bx - bs, by - bs * 0.6, bx, by + bs * 0.6]), start=200, end=330,
          fill=(30, 22, 40, 220), width=int(2.6 * F))
    d.arc(B([bx, by - bs * 0.6, bx + bs, by + bs * 0.6]), start=210, end=340,
          fill=(30, 22, 40, 220), width=int(2.6 * F))

# ---------------------------------------------------------------------------
# Foreground palm framing the bottom right corner
# ---------------------------------------------------------------------------
def palm(cx, cy, s, flip=1):
    pts = []
    for i in range(15):
        t = i / 14
        pts.append((cx + flip * 26 * s * t * t, cy - 118 * s * t))
    for j, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        d.line(B([x0, y0, x1, y1]), fill=(24, 16, 30, 255),
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
            d.line(B([x0, y0, x1, y1]), fill=(24, 16, 30, 255), width=int(4.5 * F))

palm(948, 1036, 1.05, flip=-1)
# Dark foreground rocks in the bottom right corner.
d.polygon(P([(742, 1024), (830, 972), (930, 962), (1010, 990), (1024, 1024)]),
          fill=(28, 18, 36, 255))

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

name_font = ImageFont.truetype(str(SERIF_BOLD), int(152 * F))
spaced_text(d, X(512), X(80), NAME, name_font, int(30 * F),
            CREAM + (255,), shadow=(int(3 * F), int(5 * F), (40, 20, 44, 170)))
# Gold rule with a centre diamond, under the name.
rule_y = 252
d.line(B([196, rule_y, 466, rule_y]), fill=GOLD + (255,), width=int(3.6 * F))
d.line(B([558, rule_y, 828, rule_y]), fill=GOLD + (255,), width=int(3.6 * F))
cx, cy, r = 512, rule_y, 12
d.polygon(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), fill=GOLD + (255,))
for ex in (180, 844):
    d.ellipse(B([ex - 4, rule_y - 4, ex + 4, rule_y + 4]), fill=GOLD + (255,))

# ---------------------------------------------------------------------------
# Painterly grain, paper frame, vignette, downscale, size guard
# ---------------------------------------------------------------------------
# Seeded low-res noise, upscaled smooth and blended at low strength so
# the flat colour fields gain a printed-paper tooth. Deterministic.
noise_small = Image.new("L", (256, 256))
npx = noise_small.load()
for yy in range(256):
    for xx in range(256):
        npx[xx, yy] = rng.randint(96, 160)
noise = noise_small.resize((W, W), Image.BILINEAR).filter(
    ImageFilter.GaussianBlur(radius=1.2 * F))
img = Image.composite(Image.blend(img.convert("RGB"), Image.new("RGB", (W, W), (128, 118, 104)), 0.10),
                      img.convert("RGB"), noise)

d = ImageDraw.Draw(img, "RGBA")
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
print(f"velarca v2: wrote {OUT_PATH} ({len(data)} bytes, {SIZE}x{SIZE})")
