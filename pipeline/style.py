"""Bright modern visual system: saturated flat colour, semi-realistic steel, split screens.

Design rules
  - Near-white background, heavy black type, one saturated accent per idea.
  - Steel is rendered with a vertical gradient + rivets + edge highlight so it reads
    as a real member, not a line drawing.
  - Everything is built for a phone screen: nothing smaller than ~34px.
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 25

# ---------------------------------------------------------------- palette
BG        = (247, 249, 252)
BG_DEEP   = (233, 238, 245)
INK       = (17, 22, 31)
MUTE      = (122, 134, 154)
RED       = (232, 25, 44)      # force, danger, failure
AMBER     = (255, 176, 32)     # warning, the growing bend
BLUE      = (10, 132, 255)     # reference, "correct" state
GREEN     = (18, 184, 134)     # safe / working
STEEL_HI  = (203, 212, 224)
STEEL_MID = (138, 148, 166)
STEEL_LO  = (74, 83, 98)

# Typeface system — keep these two for the life of the channel.
#   Montserrat ExtraBold/Black : display type, titles, big numbers
#   Inter SemiBold/Regular     : labels, captions, everything else
DISPLAY   = "/usr/share/fonts/opentype/montserrat/Montserrat-ExtraBold.otf"
DISPLAY_X = "/usr/share/fonts/opentype/montserrat/Montserrat-Black.otf"
UI_BOLD   = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
UI_SEMI   = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
UI        = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"

_FALLBACK = {DISPLAY: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             DISPLAY_X: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             UI_BOLD: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             UI_SEMI: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             UI: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"}


@lru_cache(maxsize=96)
def face(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(_FALLBACK[path], size)


def font(size, bold=True, display=False, black=False):
    if black:
        return face(DISPLAY_X, size)
    if display:
        return face(DISPLAY, size)
    return face(UI_SEMI if bold else UI, size)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def phase(p, a, b):
    return ease((p - a) / (b - a)) if b > a else float(p >= b)


def canvas(deep=False):
    return Image.new("RGBA", (W, H), (BG_DEEP if deep else BG) + (255,))


def over(img, fn):
    """Draw onto a transparent layer then composite — the only safe way to use alpha."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ---------------------------------------------------------------- type
def text(img, xy, s, size, color=INK, a=1.0, anchor="la", bold=True, track=0,
         display=False, black=False):
    if a <= 0:
        return
    f = font(size, bold, display, black)
    if track == 0:
        over(img, lambda d: d.text(xy, s, font=f, fill=color + (int(255 * a),), anchor=anchor))
        return
    # manual letter-spacing for display type
    d0 = ImageDraw.Draw(img)
    total = sum(d0.textlength(ch, font=f) + track for ch in s) - track
    x = xy[0] - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
    for ch in s:
        over(img, lambda d, ch=ch, x=x: d.text((x, xy[1]), ch, font=f,
                                               fill=color + (int(255 * a),), anchor="l" + anchor[1]))
        x += d0.textlength(ch, font=f) + track


def wrap(d, s, f, max_w):
    out, line = [], ""
    for word in s.split():
        t = (line + " " + word).strip()
        if d.textlength(t, font=f) > max_w and line:
            out.append(line)
            line = word
        else:
            line = t
    if line:
        out.append(line)
    return out


def title_block(img, lines, a, y=120, size=96, color=INK, accent=None):
    """Big left-aligned statement type with an accent bar that wipes in."""
    if a <= 0:
        return
    over(img, lambda d: d.rectangle([110, y, 110 + 14, y + len(lines) * size * 1.12],
                                    fill=(accent or RED) + (int(255 * ease(a)),)))
    for i, ln in enumerate(lines):
        la = phase(a, i * 0.12, i * 0.12 + 0.5)
        text(img, (160, y + i * size * 1.12 - 6), ln, size, color, la, display=True)


def lower_third(img, name, role, a, x=110, y=H - 240):
    """Character name card — solves 'who is this person?'."""
    if a <= 0:
        return
    f1, f2 = font(54, display=True), font(34, False)
    d0 = ImageDraw.Draw(img)
    w = max(d0.textlength(name, font=f1), d0.textlength(role, font=f2)) + 56
    k = ease_out(min(a * 1.6, 1.0))
    over(img, lambda d: d.rectangle([x, y, x + w * k, y + 130], fill=INK + (235,)))
    over(img, lambda d: d.rectangle([x, y, x + 10 * k, y + 130], fill=AMBER + (255,)))
    if a > 0.35:
        b = phase(a, 0.35, 0.6)
        text(img, (x + 30, y + 22), name, 54, (255, 255, 255), b, display=True)
        text(img, (x + 30, y + 84), role, 34, AMBER, b, bold=False)


def caption(img, s, a, y=H - 150):
    """Burned-in key phrase. Phones are muted by default — this carries the point."""
    if a <= 0:
        return
    f = font(46)
    d0 = ImageDraw.Draw(img)
    for i, ln in enumerate(wrap(d0, s, f, W - 320)):
        w = d0.textlength(ln, font=f)
        yy = y + i * 70
        over(img, lambda d, w=w, yy=yy: d.rounded_rectangle(
            [W / 2 - w / 2 - 24, yy, W / 2 + w / 2 + 24, yy + 62], 8, fill=INK + (int(240 * a),)))
        text(img, (W / 2, yy + 31), ln, 46, (255, 255, 255), a, "mm")


def stat(img, value, label, a, center, size=150, color=RED):
    if a <= 0:
        return
    text(img, (center[0], center[1]), value, size, color, a, "mm", black=True)
    text(img, (center[0], center[1] + size * 0.62), label, 38, MUTE, a, "mm", bold=False)


# ---------------------------------------------------------------- steel
def _band(d, pts, thick, c_hi, c_lo, strips=14):
    """A thick member drawn as shaded strips so it reads as a 3D surface."""
    for i in range(strips):
        t0 = i / strips
        off = (t0 - 0.5) * thick
        shade = lerp(c_hi, c_lo, t0 ** 0.8)
        d.line([(x, y + off) for x, y in pts], fill=shade + (255,), width=int(thick / strips) + 2)


def member(img, x0, x1, y, thick=74, bow=0.0, rivets=True, tint=None, shadow=True,
           n_plates=1, gap=0, a=1.0):
    """Semi-realistic riveted steel member. bow = sideways deflection in px."""
    if a <= 0:
        return
    pts = lambda off: [(x0 + (x1 - x0) * i / 48,
                        y + off + bow * math.sin(math.pi * i / 48)) for i in range(49)]
    hi = lerp(STEEL_HI, tint, 0.35) if tint else STEEL_HI
    lo = lerp(STEEL_LO, tint, 0.35) if tint else STEEL_LO
    plate_t = thick if n_plates == 1 else max(14, (thick - gap * (n_plates - 1)) / n_plates)

    def draw(d):
        for k in range(n_plates):
            off = (k - (n_plates - 1) / 2) * (plate_t + gap)
            p = pts(off)
            if shadow:
                d.line([(x, yy + plate_t * 0.55 + 8) for x, yy in p],
                       fill=(0, 0, 0, int(40 * a)), width=int(plate_t))
            _band(d, p, plate_t, hi, lo)
            # top edge highlight + bottom shadow line
            d.line([(x, yy - plate_t / 2 + 2) for x, yy in p], fill=(255, 255, 255, int(190 * a)), width=3)
            d.line([(x, yy + plate_t / 2 - 2) for x, yy in p], fill=lerp(lo, (0, 0, 0), .45) + (int(230 * a),), width=3)
            if rivets and plate_t > 26:
                n = max(4, int((x1 - x0) / 92))
                for i in range(n + 1):
                    t = i / n
                    rx = x0 + (x1 - x0) * t
                    ry = y + off + bow * math.sin(math.pi * t)
                    for dy in (-plate_t * 0.28, plate_t * 0.28):
                        d.ellipse([rx - 9, ry + dy - 9, rx + 9, ry + dy + 9],
                                  fill=lerp(hi, lo, 0.55) + (int(255 * a),))
                        d.ellipse([rx - 9, ry + dy - 9, rx + 3, ry + dy + 3],
                                  fill=lerp(hi, (255, 255, 255), 0.5) + (int(200 * a),))
    over(img, draw)


def lacing(img, x0, x1, y, span, a=1.0, color=None, n=9):
    """The thin diagonal straps that were supposed to tie the plates together."""
    if a <= 0:
        return
    c = (color or STEEL_MID) + (int(255 * a),)
    def draw(d):
        for i in range(n):
            t0, t1 = i / n, (i + 0.5) / n
            d.line([(x0 + (x1 - x0) * t0, y - span / 2), (x0 + (x1 - x0) * t1, y + span / 2)],
                   fill=c, width=7)
            d.line([(x0 + (x1 - x0) * t1, y + span / 2), (x0 + (x1 - x0) * (t1 + 0.5 / n), y - span / 2)],
                   fill=c, width=7)
    over(img, draw)


def arrow(img, start, end, color=RED, width=16, a=1.0, head=42):
    if a <= 0:
        return
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    def draw(d):
        d.line([start, end], fill=color + (int(255 * a),), width=width)
        for s in (-1, 1):
            b = ang + math.pi + s * 0.42
            d.line([end, (end[0] + head * math.cos(b), end[1] + head * math.sin(b))],
                   fill=color + (int(255 * a),), width=width)
    over(img, draw)


def dim_line(img, p0, p1, label, a=1.0, color=INK, size=36):
    """Dimension line with ticks — reads as an engineering drawing."""
    if a <= 0:
        return
    def draw(d):
        d.line([p0, p1], fill=color + (int(255 * a),), width=4)
        for p in (p0, p1):
            d.line([(p[0], p[1] - 16), (p[0], p[1] + 16)], fill=color + (int(255 * a),), width=4)
    over(img, draw)
    text(img, ((p0[0] + p1[0]) / 2, p0[1] - 34), label, size, color, a, "mm")


# ---------------------------------------------------------------- layout
def split(img, left_fn, right_fn, a=1.0, divider=True):
    """Two panels side by side — the compare-and-contrast workhorse."""
    half = Image.new("RGBA", (W // 2, H), (0, 0, 0, 0))
    for fn, x in ((left_fn, 0), (right_fn, W // 2)):
        panel = half.copy()
        fn(panel)
        img.alpha_composite(panel, (x, 0))
    if divider:
        over(img, lambda d: d.rectangle([W / 2 - 3, 0, W / 2 + 3, H], fill=INK + (int(255 * a),)))


def panel_label(img, s, color, a, x, y=70, w=W // 2):
    if a <= 0:
        return
    over(img, lambda d: d.rounded_rectangle([x + 60, y, x + w - 60, y + 86], 10,
                                            fill=color + (int(255 * a),)))
    text(img, (x + w / 2, y + 43), s, 46, (255, 255, 255), a, "mm")


def vignette_flash(img, a):
    """One-frame white flash for a hard cut."""
    if a <= 0:
        return
    over(img, lambda d: d.rectangle([0, 0, W, H], fill=(255, 255, 255, int(255 * a))))


def grid_bg(img, a=0.5):
    over(img, lambda d: [d.line([(x, 0), (x, H)], fill=(0, 0, 0, int(14 * a)), width=1)
                         for x in range(0, W, 80)])
    over(img, lambda d: [d.line([(0, y), (W, y)], fill=(0, 0, 0, int(14 * a)), width=1)
                         for y in range(0, H, 80)])
