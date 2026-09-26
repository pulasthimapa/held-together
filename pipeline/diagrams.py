"""Engineering diagrams drawn in code: our own original visuals.

Each diagram is a function frame(p) -> PIL.Image, where p runs from 0 to 1 over the
scene. render.py pipes the frames straight into ffmpeg.
"""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import FONT_SERIF, FONT_SERIF_BOLD, H, W

PAPER = (236, 227, 208)
INK = (46, 42, 38)
FAINT = (150, 140, 122)
RUST = (156, 61, 36)
WATER = (120, 138, 150)

# Minimum seconds for a diagram, so short narration still gets a readable animation.
MIN_SECONDS = {"collapse": 6.0}


@lru_cache(maxsize=1)
def paper():
    rnd = random.Random(7)
    base = Image.new("RGB", (W, H), PAPER)
    noise = Image.effect_noise((W // 2, H // 2), 18).resize((W, H)).convert("RGB")
    base = Image.blend(base, noise, 0.06)
    draw = ImageDraw.Draw(base)
    for _ in range(40):  # faint fibres
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        draw.line([(x, y), (x + rnd.randint(-80, 80), y + rnd.randint(-8, 8))],
                  fill=(222, 212, 192), width=1)
    return base.filter(ImageFilter.GaussianBlur(0.6))


def font(size, bold=False):
    return ImageFont.truetype(FONT_SERIF_BOLD if bold else FONT_SERIF, size)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def phase(p, start, end):
    """Progress 0..1 of a sub-animation running between p=start and p=end."""
    return ease((p - start) / (end - start)) if end > start else float(p >= end)


def partial_line(draw, pts, frac, fill, width):
    """Draw a polyline revealed up to `frac` of its length."""
    if frac <= 0:
        return
    segs = list(zip(pts, pts[1:]))
    lengths = [math.dist(a, b) for a, b in segs]
    remaining = sum(lengths) * min(frac, 1.0)
    for (a, b), ln in zip(segs, lengths):
        if remaining <= 0:
            break
        f = min(1.0, remaining / ln) if ln else 1.0
        draw.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)],
                  fill=fill, width=width)
        remaining -= ln


def text_fade(img, xy, text, size, alpha, color=INK, bold=False, anchor="la"):
    if alpha <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font(size, bold),
                               fill=color + (int(255 * alpha),), anchor=anchor)
    img.alpha_composite(layer)


def cantilever(draw, left_pier, right_pier, deck_y, frac, color=INK, width=4):
    """Simple elevation of a two-arm cantilever bridge between two river piers."""
    span = right_pier - left_pier
    anchor = span * 0.55
    top = deck_y - span * 0.28
    for pier, direction in ((left_pier, 1), (right_pier, -1)):
        outer = pier - direction * anchor
        tip = pier + direction * span * 0.36
        pts = [(outer, deck_y), (pier, top), (tip, deck_y)]
        partial_line(draw, pts, frac, color, width)
        partial_line(draw, [(outer, deck_y), (tip, deck_y)], frac, color, width)
        for k in range(1, 6):  # diagonals
            x = outer + (pier - outer) * k / 6
            y = deck_y - (deck_y - top) * k / 6
            partial_line(draw, [(x, deck_y), (x, y)], frac, color, 2)
            x2 = pier + (tip - pier) * k / 6
            y2 = top + (deck_y - top) * k / 6
            partial_line(draw, [(x2, deck_y), (x2, y2)], frac, color, 2)
    # suspended span between the tips
    partial_line(draw, [(left_pier + span * 0.36, deck_y), (right_pier - span * 0.36, deck_y)],
                 frac, color, width)


def span_lengthened(p):
    img = paper().copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    water_y = 760
    d.rectangle([0, water_y, W, H], fill=WATER + (255,))
    text_fade(img, (W // 2, 90), "Making the main span longer", 56, phase(p, 0, 0.1),
              bold=True, anchor="mm")
    grow = phase(p, 0.35, 0.65)
    half = 330 + 70 * grow
    lp, rp = W / 2 - half, W / 2 + half
    cantilever(d, lp, rp, 640, phase(p, 0.05, 0.35))
    for x in (lp, rp):
        d.rectangle([x - 16, 640, x + 16, water_y + 40], fill=INK)
    a = phase(p, 0.35, 0.45)
    if a > 0:
        d.line([(lp, 830), (rp, 830)], fill=RUST + (int(255 * a),), width=4)
        for x in (lp, rp):
            d.line([(x, 810), (x, 850)], fill=RUST + (int(255 * a),), width=4)
        label = "about 490 m" if grow < 0.5 else "about 550 m"
        text_fade(img, (W // 2, 880), f"Main span: {label}", 44, a, RUST, True, "mm")
    text_fade(img, (W // 2, 980), "Longer span  =  heavier steel  =  more load on every member",
              40, phase(p, 0.7, 0.8), anchor="mm")
    return img.convert("RGB")


def chord(draw, x0, x1, y, bow, n_plates=4, gap=14, lace=True, color=INK, spread=0.0):
    """A built-up compression chord drawn as parallel plates that bow sideways."""
    pts_sets = []
    for k in range(n_plates):
        offset = (k - (n_plates - 1) / 2) * (gap + spread)
        pts = []
        for i in range(41):
            t = i / 40
            x = x0 + (x1 - x0) * t
            pts.append((x, y + offset + bow * math.sin(math.pi * t)))
        draw.line(pts, fill=color, width=5)
        pts_sets.append(pts)
    if lace:
        top, bottom = pts_sets[0], pts_sets[-1]
        for i in range(0, 40, 2):
            draw.line([top[i], bottom[i + 1]], fill=FAINT, width=2)
            draw.line([bottom[i + 1], top[i + 2]], fill=FAINT, width=2)


def arrow(draw, start, end, color, width=8):
    draw.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for side in (-1, 1):
        a = ang + math.pi + side * 0.45
        draw.line([end, (end[0] + 30 * math.cos(a), end[1] + 30 * math.sin(a))],
                  fill=color, width=width)


def chord_ripple(p):
    img = paper().copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    text_fade(img, (W // 2, 110), "Lower chord  -  carrying the bridge in compression",
              50, phase(p, 0, 0.12), bold=True, anchor="mm")
    bow = 4 + 70 * phase(p, 0.3, 1.0)
    chord(d, 360, 1560, 560, bow)
    a = phase(p, 0.1, 0.25)
    if a > 0:
        c = RUST + (int(255 * a),)
        arrow(d, (160, 560), (330, 560), c)
        arrow(d, (1760, 560), (1590, 560), c)
    text_fade(img, (W // 2, 900), "Each day, more steel went on. The bend kept growing.",
              42, phase(p, 0.55, 0.7), anchor="mm")
    return img.convert("RGB")


def collapse(p):
    img = paper().copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    water_y = 760
    d.rectangle([0, water_y, W, H], fill=WATER + (255,))
    fall = phase(p, 0.15, 0.75)
    left_pier, right_pier, deck_y = W / 2 - 420, W / 2 + 420, 620
    if fall <= 0:
        cantilever(d, left_pier, right_pier, deck_y, 1.0)
    else:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        cantilever(ImageDraw.Draw(layer), left_pier, right_pier, deck_y, 1.0)
        drop = int((water_y - deck_y + 260) * fall ** 1.6)
        angle = -14 * fall
        south = layer.crop((0, 0, int(W / 2 + 60), H)).rotate(
            angle, center=(left_pier, deck_y), resample=Image.BICUBIC)
        north = layer.crop((int(W / 2 + 60), 0, W, H))
        img.alpha_composite(north, (int(W / 2 + 60), 0))
        faded = south.copy()
        faded.putalpha(south.getchannel("A").point(lambda v: int(v * (1 - 0.6 * fall))))
        img.alpha_composite(faded, (0, drop))
        d = ImageDraw.Draw(img)
        d.rectangle([0, water_y, W, H], fill=WATER + (255,))
        mist = phase(p, 0.55, 0.85)
        if mist > 0:
            haze = Image.new("RGBA", img.size, (240, 236, 228, int(170 * mist * (1 - phase(p, 0.85, 1.0)))))
            img.alpha_composite(haze)
    for x in (left_pier, right_pier):
        d.rectangle([x - 16, deck_y, x + 16, water_y + 40], fill=INK)
    text_fade(img, (W // 2, 950), "15 seconds", 64, phase(p, 0.8, 0.95), RUST, True, "mm")
    return img.convert("RGB")


def buckling(p):
    img = paper().copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    # Left panel: a single column buckling under rising load
    text_fade(img, (480, 80), "Compression: it bows, then bows more", 32,
              phase(p, 0, 0.08), bold=True, anchor="mm")
    load = phase(p, 0.05, 0.4)
    bow = 6 + 120 * phase(p, 0.2, 0.45) ** 1.5
    top, bottom, cx = 340, 900, 480
    pts = [(cx + bow * math.sin(math.pi * i / 40), top + (bottom - top) * i / 40)
           for i in range(41)]
    d.line(pts, fill=INK, width=12)
    d.rectangle([cx - 90, bottom, cx + 90, bottom + 24], fill=INK)
    if load > 0:
        arrow(d, (cx, top - 120 - 60 * load), (cx, top - 12), RUST + (255,), width=int(6 + 8 * load))
    # Right panel: built-up chord, plates tied with light lacing, separating
    text_fade(img, (1400, 80), "Built-up chord: plates tied with light lacing", 32,
              phase(p, 0.45, 0.53), bold=True, anchor="mm")
    if p > 0.45:
        spread = 40 * phase(p, 0.6, 0.85)
        cbow = 10 + 60 * phase(p, 0.6, 0.9)
        chord(d, 1000, 1800, 520, cbow, n_plates=3, gap=34, lace=phase(p, 0.6, 0.85) < 0.7,
              spread=spread)
        text_fade(img, (1400, 760), "Lacing too light to make the plates act as one", 34,
                  phase(p, 0.62, 0.72), anchor="mm")
    text_fade(img, (W // 2, 990), "A bend that keeps growing under rising load is a warning.",
              42, phase(p, 0.86, 0.94), RUST, True, "mm")
    return img.convert("RGB")


DIAGRAMS = {"span_lengthened": span_lengthened, "chord_ripple": chord_ripple,
            "collapse": collapse, "buckling": buckling}
