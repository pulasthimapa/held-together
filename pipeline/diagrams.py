"""Engineering explainers drawn in code — our own original visuals.

Each diagram is a function frame(p) -> PIL.Image with p running 0..1 across the scene.
The job of every one of these is to teach a structural idea to someone who has never
opened an engineering textbook: everyday object first, then the real thing.
"""
import math

from PIL import Image, ImageDraw

from style import (AMBER, BLUE, GREEN, H, INK, MUTE, RED, STEEL_LO,
                   STEEL_MID, W, arrow, canvas, caption, dim_line, ease, ease_out,
                   grid_bg, lacing, lerp, lower_third, member, over, panel_label, phase,
                   split, stat, text, title_block)

# Minimum seconds for a diagram, so short narration still gets a readable animation.
MIN_SECONDS = {"collapse": 7.0, "buckling_loop": 9.0, "builtup_lacing": 12.0,
               "straw_vs_steel": 7.0, "ruler_push": 7.0, "tension_compression": 8.0,
               "cantilever_build": 9.0, "men_grid": 7.0}


# ------------------------------------------------------------------ shared pieces
def cantilever(d, left_pier, right_pier, deck_y, frac, color=INK, width=5, rivet=False):
    """Elevation of a two-arm cantilever bridge between two river piers."""
    span = right_pier - left_pier
    anchor = span * 0.55
    top = deck_y - span * 0.28
    for pier, direction in ((left_pier, 1), (right_pier, -1)):
        outer = pier - direction * anchor
        tip = pier + direction * span * 0.36
        _partial(d, [(outer, deck_y), (pier, top), (tip, deck_y)], frac, color, width)
        _partial(d, [(outer, deck_y), (tip, deck_y)], frac, color, width)
        for k in range(1, 6):
            x = outer + (pier - outer) * k / 6
            y = deck_y - (deck_y - top) * k / 6
            _partial(d, [(x, deck_y), (x, y)], frac, color, max(2, width - 2))
            x2 = pier + (tip - pier) * k / 6
            y2 = top + (deck_y - top) * k / 6
            _partial(d, [(x2, deck_y), (x2, y2)], frac, color, max(2, width - 2))
    _partial(d, [(left_pier + span * 0.36, deck_y), (right_pier - span * 0.36, deck_y)],
             frac, color, width)


def _partial(d, pts, frac, fill, width):
    if frac <= 0:
        return
    segs = list(zip(pts, pts[1:]))
    lengths = [math.dist(a, b) for a, b in segs]
    remaining = sum(lengths) * min(frac, 1.0)
    for (a, b), ln in zip(segs, lengths):
        if remaining <= 0:
            break
        f = min(1.0, remaining / ln) if ln else 1.0
        d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=fill, width=width)
        remaining -= ln


def water(img, y=820):
    over(img, lambda d: d.rectangle([0, y, W, H], fill=(176, 206, 230, 255)))
    over(img, lambda d: d.rectangle([0, y, W, y + 8], fill=(140, 180, 214, 255)))


def meter(img, frac, a, xy=(1560, 300), w=72, h=420, label="STRENGTH"):
    """A vertical bar that drains — makes 'it gets weaker' a thing you can watch."""
    if a <= 0:
        return
    x, y = xy
    over(img, lambda d: d.rounded_rectangle([x, y, x + w, y + h], 10,
                                            fill=(255, 255, 255, int(255 * a)),
                                            outline=INK + (int(255 * a),), width=4))
    fh = (h - 12) * max(0.0, min(1.0, frac))
    col = GREEN if frac > 0.6 else (AMBER if frac > 0.3 else RED)
    over(img, lambda d: d.rounded_rectangle([x + 6, y + h - 6 - fh, x + w - 6, y + h - 6], 6,
                                            fill=col + (int(255 * a),)))
    text(img, (x + w / 2, y - 40), label, 32, INK, a, "mm")
    text(img, (x + w / 2, y + h + 26), f"{int(frac * 100)}%", 44, col, a, "mm", black=True)


# ------------------------------------------------------------------ 1. the hook
def straw_vs_steel(p):
    img = canvas()
    grid_bg(img)

    def left(pan):
        bow = 10 + 120 * phase(p, .4, .78)
        pts = [(170 + 600 * i / 40, 560 + bow * math.sin(math.pi * i / 40)) for i in range(41)]
        over(pan, lambda d: d.line(pts, fill=(255, 255, 255, 255), width=34))
        over(pan, lambda d: d.line(pts, fill=(222, 229, 238, 255), width=26))
        over(pan, lambda d: d.line([(x, y - 9) for x, y in pts], fill=(255, 255, 255, 235), width=6))
        a = phase(p, .26, .4)
        arrow(pan, (60, 560), (150, 560), RED, 14, a)
        arrow(pan, (900, 560), (810, 560), RED, 14, a)

    def right(pan):
        member(pan, 150, 810, 560, thick=96, bow=4 + 46 * phase(p, .5, .88))
        a = phase(p, .26, .4)
        arrow(pan, (40, 560), (130, 560), RED, 18, a)
        arrow(pan, (920, 560), (830, 560), RED, 18, a)

    split(img, left, right)
    panel_label(img, "A PLASTIC STRAW", MUTE, phase(p, .1, .22), 0)
    panel_label(img, "1,000 TONNES OF STEEL", RED, phase(p, .16, .28), W // 2)
    caption(img, "Same failure. Exactly the same physics.", phase(p, .8, .93))
    return img


# ------------------------------------------------------------------ 2. two forces
def tension_compression(p):
    img = canvas()
    grid_bg(img)
    title_block(img, ["TWO WAYS TO LOAD ANYTHING."], phase(p, 0, .16), y=80, size=62, accent=BLUE)

    # rope in tension: pull it and it just goes taut
    y1 = 400
    a1 = phase(p, .18, .32)
    sag = 70 * (1 - phase(p, .3, .5))
    pts = [(560 + 800 * i / 40, y1 + sag * math.sin(math.pi * i / 40)) for i in range(41)]
    over(img, lambda d: d.line(pts, fill=(168, 124, 70, int(255 * a1)), width=18))
    arrow(img, (520, y1), (420, y1), BLUE, 12, a1)
    arrow(img, (1400, y1), (1500, y1), BLUE, 12, a1)
    text(img, (330, y1), "PULL", 44, BLUE, a1, "rm", display=True)
    text(img, (960, y1 - 110), "TENSION  —  a rope works fine", 42, INK, phase(p, .34, .46), "mm")
    text(img, (960, y1 + 130), "it just pulls tight. Nothing to go wrong.", 36, MUTE,
         phase(p, .4, .52), "mm", bold=False)

    # same rope in compression: push it and it collapses
    y2 = 760
    a2 = phase(p, .55, .66)
    crumple = phase(p, .64, .85)
    pts2 = [(560 + 800 * i / 40,
             y2 + 120 * crumple * math.sin(3 * math.pi * i / 40) * math.sin(math.pi * i / 40))
            for i in range(41)]
    over(img, lambda d: d.line(pts2, fill=(168, 124, 70, int(255 * a2)), width=18))
    arrow(img, (420, y2), (520, y2), RED, 12, a2)
    arrow(img, (1500, y2), (1400, y2), RED, 12, a2)
    text(img, (330, y2), "PUSH", 44, RED, a2, "rm", display=True)
    text(img, (960, y2 + 150), "COMPRESSION  —  now it matters what the thing is made of",
         40, RED, phase(p, .78, .9), "mm")
    text(img, (960, y2 + 212), "The Quebec Bridge failed in compression.", 38, INK,
         phase(p, .88, .97), "mm", bold=False)
    return img


# ------------------------------------------------------------------ 3. ruler
def ruler_push(p):
    img = canvas()
    grid_bg(img)
    title_block(img, ["TRY THIS YOURSELF."], phase(p, 0, .18), y=90, size=78, accent=BLUE)
    push = phase(p, .22, .5)
    bow = 150 * phase(p, .32, .84) ** 1.4
    x0, x1, y = 430, 1490, 600
    pts = [(x0 + (x1 - x0) * i / 40, y + bow * math.sin(math.pi * i / 40)) for i in range(41)]
    over(img, lambda d: d.line([(x, yy + 14) for x, yy in pts], fill=(0, 0, 0, 36), width=30))
    over(img, lambda d: d.line(pts, fill=(255, 206, 74, 255), width=26))
    over(img, lambda d: d.line([(x, yy - 7) for x, yy in pts], fill=(255, 240, 190, 255), width=8))
    over(img, lambda d: [d.line([(x0 + (x1 - x0) * i / 20, y + bow * math.sin(math.pi * i / 20) - 10),
                                 (x0 + (x1 - x0) * i / 20, y + bow * math.sin(math.pi * i / 20) + 2)],
                                fill=(150, 110, 20, 200), width=3) for i in range(21)])
    arrow(img, (250, y), (x0 - 20, y), RED, 18, push)
    arrow(img, (1670, y), (x1 + 20, y), RED, 18, push)
    if bow > 30:
        a = phase(p, .52, .64)
        dim_line(img, (960, y + 6), (960, y + bow), "", a)
        text(img, (1010, y + bow / 2), "it bows", 46, RED, a, "lm", display=True)
    caption(img, "It never snaps. It bends sideways and keeps going.", phase(p, .7, .86))
    return img


# ------------------------------------------------------------------ 4. the loop
def buckling_loop(p):
    """The runaway loop, shown physically: real steel bowing while its strength drains."""
    img = canvas(deep=True)
    text(img, (W / 2, 120), "BUCKLING", 150, INK, phase(p, 0, .14), "mm", track=16, black=True)
    over(img, lambda d: d.rectangle([W / 2 - 280 * ease(phase(p, .1, .26)), 232,
                                     W / 2 + 280 * ease(phase(p, .1, .26)), 240], fill=RED + (255,)))

    # three accelerating cycles: each one bows further and drains more strength
    cycles = [(0.22, 0.42, 34, 0.74), (0.42, 0.62, 78, 0.45), (0.62, 0.86, 150, 0.12)]
    bow, strength = 10.0, 1.0
    for t0, t1, b, s in cycles:
        k = phase(p, t0, t1)
        if k > 0:
            bow = 10 + (b - 10) * k if bow < b else bow
            bow = max(bow, 10 + (b - 10) * k)
            strength = min(strength, 1.0 - (1.0 - s) * k)
    load = 1.0 + 0.9 * phase(p, .2, .86)
    member(img, 380, 1380, 430, thick=78, bow=bow, tint=lerp(STEEL_MID, RED, 1 - strength))
    arrow(img, (250, 430), (360, 430), RED, int(10 + 12 * load), phase(p, .16, .26))
    arrow(img, (1510, 430), (1400, 430), RED, int(10 + 12 * load), phase(p, .16, .26))
    meter(img, strength, phase(p, .2, .3), (1660, 300), 74, 360)

    # the running commentary, one line per cycle
    lines = [("it bows", .24), ("so it carries less", .44), ("so it bows further", .64)]
    for i, (s, t) in enumerate(lines):
        a = phase(p, t, t + .1)
        text(img, (880, 790 + i * 68), f"{i + 1}.  {s}", 48, [AMBER, RED, RED][i], a, "mm",
             display=True)
    caption(img, "Each turn of the loop is faster than the last.", phase(p, .88, .97), y=H - 90)
    return img


# ------------------------------------------------------------------ 5. built-up members
def builtup_lacing(p):
    img = canvas()

    def left(pan):
        member(pan, 110, 850, 450, thick=130, bow=6 + 10 * phase(p, .5, .95))
        a = phase(p, .35, .5)
        arrow(pan, (20, 450), (95, 450), BLUE, 14, a)
        arrow(pan, (940, 450), (865, 450), BLUE, 14, a)
        if a > 0:
            text(pan, (480, 680), "acts as ONE thick member", 40, BLUE, a, "mm")
            text(pan, (480, 744), "strong", 62, BLUE, phase(p, .5, .62), "mm", display=True)

    def right(pan):
        spread = 30 * phase(p, .55, .9)
        b = 10 + 66 * phase(p, .52, .96)
        lacing(pan, 130, 830, 450, 150 + spread * 3,
               phase(p, .22, .34) * (1 - phase(p, .72, .9)), STEEL_LO)
        member(pan, 110, 850, 450, thick=150 + spread * 3, bow=b, n_plates=4,
               gap=spread, rivets=False)
        a = phase(p, .35, .5)
        arrow(pan, (20, 450), (95, 450), RED, 14, a)
        arrow(pan, (940, 450), (865, 450), RED, 14, a)
        if a > 0:
            text(pan, (480, 680), "four plates bend SEPARATELY", 38, RED, a, "mm")
            text(pan, (480, 744), "far weaker", 62, RED, phase(p, .5, .62), "mm", display=True)

    split(img, left, right)
    panel_label(img, "LACED TIGHTLY", BLUE, phase(p, .06, .18), 0)
    panel_label(img, "LACED TOO LIGHTLY", RED, phase(p, .1, .22), W // 2)
    caption(img, "The Quebec Bridge had the second kind.", phase(p, .82, .94))
    return img


# ------------------------------------------------------------------ 6. the span decision
def span_longer(p):
    img = canvas()
    grid_bg(img)
    water(img, 840)
    title_block(img, ["MAKE THE SPAN LONGER,", "AND THE STEEL GETS HEAVIER."],
                phase(p, 0, .2), y=80, size=58, accent=AMBER)
    grow = phase(p, .34, .66)
    half = 320 + 90 * grow
    lp, rp = W / 2 - half, W / 2 + half
    over(img, lambda d: cantilever(d, lp, rp, 640, phase(p, .12, .34), INK, 5))
    over(img, lambda d: [d.rectangle([x - 18, 640, x + 18, 880], fill=INK + (255,)) for x in (lp, rp)])
    a = phase(p, .34, .44)
    dim_line(img, (lp, 920), (rp, 920), "490 m" if grow < 0.5 else "549 m", a, RED, 44)
    # the point most people miss: the bridge mostly carries itself
    b = phase(p, .68, .8)
    if b > 0:
        text(img, (W / 2, 1010), "A bridge this size mostly carries its own weight.", 44,
             INK, b, "mm")
        text(img, (W / 2, 1062), "More span → more steel → more weight → more steel again.",
             38, RED, phase(p, .78, .9), "mm", bold=False)
    return img


# ------------------------------------------------------------------ 7. how it is built
def cantilever_build(p):
    """Why nobody could simply stop and check: the bridge was built out over the water."""
    img = canvas()
    grid_bg(img)
    water(img, 840)
    title_block(img, ["BUILT OUT INTO MID-AIR."], phase(p, 0, .16), y=80, size=64, accent=BLUE)
    lp, rp, deck = W / 2 - 420, W / 2 + 420, 620
    over(img, lambda d: [d.rectangle([x - 18, deck, x + 18, 880], fill=INK + (255,)) for x in (lp, rp)])
    reach = phase(p, .2, .85)
    over(img, lambda d: cantilever(d, lp, rp, deck, reach, INK, 5))
    # a travelling crane creeping outwards
    cx = lp + (W / 2 - lp) * reach
    a = phase(p, .25, .35)
    if a > 0:
        over(img, lambda d: [d.rectangle([cx - 26, deck - 150, cx + 26, deck], fill=AMBER + (int(255 * a),)),
                             d.line([(cx, deck - 150), (cx + 130, deck - 90)], fill=INK + (int(255 * a),), width=7)])
    text(img, (W / 2, 1000), "No scaffolding. No support underneath.", 46, INK,
         phase(p, .6, .72), "mm")
    text(img, (W / 2, 1056), "Every day's work made the arms heavier — and longer.", 38,
         RED, phase(p, .72, .84), "mm", bold=False)
    return img


# ------------------------------------------------------------------ 8. the measurements
def bend_record(p):
    img = canvas()
    grid_bg(img)
    title_block(img, ["THE BEND KEPT GROWING."], phase(p, 0, .16), y=80, size=66, accent=AMBER)
    rows = [("early August", 0.18, STEEL_MID), ("27 August", 0.55, AMBER), ("29 August", 1.0, RED)]
    for i, (label, amt, col) in enumerate(rows):
        a = phase(p, .2 + i * .17, .38 + i * .17)
        if a <= 0:
            continue
        y = 400 + i * 190
        member(img, 460, 1460, y, thick=56, bow=10 + 80 * amt * ease_out(a), tint=col, a=a)
        text(img, (420, y), label, 40, INK, a, "rm")
        text(img, (1520, y), f"+{int(amt * 60)} mm", 44, col, phase(a, .5, 1), "lm", display=True)
    lower_third(img, "Norman McLure", "inspecting engineer, on site",
                phase(p, .52, .72), x=1240, y=140)
    caption(img, "Not old damage. The loop, already running.", phase(p, .86, .97))
    return img


# ------------------------------------------------------------------ 9. the telegram race
LON0, LON1, LAT0, LAT1 = -79.0, -67.5, 39.4, 47.8


def _xy(lat, lon):
    return (160 + (lon - LON0) / (LON1 - LON0) * (W - 320),
            150 + (LAT1 - lat) / (LAT1 - LAT0) * (H - 320))


def _clock(img, c, r, hours, minutes, a=1.0, label=None):
    if a <= 0:
        return
    A = int(255 * a)
    def draw(d):
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 255, 255, A),
                  outline=INK + (A,), width=6)
        for k in range(12):
            ang = math.pi / 2 - k * math.pi / 6
            d.line([(c[0] + .82 * r * math.cos(ang), c[1] - .82 * r * math.sin(ang)),
                    (c[0] + .95 * r * math.cos(ang), c[1] - .95 * r * math.sin(ang))],
                   fill=INK + (A,), width=4)
        hm = (hours % 12 + minutes / 60) * math.pi / 6
        mm = minutes * math.pi / 30
        d.line([c, (c[0] + .5 * r * math.sin(hm), c[1] - .5 * r * math.cos(hm))], fill=INK + (A,), width=10)
        d.line([c, (c[0] + .8 * r * math.sin(mm), c[1] - .8 * r * math.cos(mm))], fill=RED + (A,), width=6)
    over(img, draw)
    if label:
        text(img, (c[0], c[1] + r + 38), label, 34, INK, a, "mm")


def telegram_race(p):
    img = canvas()
    grid_bg(img, 0.8)
    QC, NY, PA = _xy(46.75, -71.29), _xy(40.71, -74.01), _xy(40.13, -75.51)
    over(img, lambda d: d.line([_xy(44.0, -76.3), _xy(45.4, -73.9), _xy(46.3, -72.6),
                                _xy(46.8, -71.2), _xy(47.6, -69.7)],
                               fill=(176, 206, 230, 255), width=12, joint="curve"))
    for pt, name, side, a in ((NY, "New York", 1, phase(p, .05, .15)),
                              (PA, "Pennsylvania office", -1, phase(p, .1, .2)),
                              (QC, "the bridge, Quebec", 1, phase(p, .15, .25))):
        if a <= 0:
            continue
        over(img, lambda d, pt=pt, a=a: d.ellipse([pt[0] - 14, pt[1] - 14, pt[0] + 14, pt[1] + 14],
                                                  fill=INK + (int(255 * a),)))
        text(img, (pt[0] + 28 * side, pt[1] - 6), name, 38, INK, a,
             "lm" if side > 0 else "rm")
    _clock(img, (330, 300), 100, 12, 16, phase(p, .2, .3), "12:16 pm — sent")
    over(img, lambda d: _partial(d, [NY, PA], phase(p, .3, .5), RED + (255,), 9))
    _clock(img, (330, 620), 100, 13, 3, phase(p, .5, .6), "just after 1 pm — arrives")
    # the leg that was never travelled
    dash = phase(p, .6, .8)
    if dash > 0:
        n = 30
        over(img, lambda d: [d.line([(PA[0] + (QC[0] - PA[0]) * i / n, PA[1] + (QC[1] - PA[1]) * i / n),
                                     (PA[0] + (QC[0] - PA[0]) * (i + .5) / n,
                                      PA[1] + (QC[1] - PA[1]) * (i + .5) / n)],
                                    fill=MUTE + (255,), width=6)
                             for i in range(int(n * dash))])
    x = phase(p, .82, .92)
    if x > 0:
        m = ((PA[0] + QC[0]) / 2, (PA[1] + QC[1]) / 2)
        over(img, lambda d: [d.line([(m[0] - 46, m[1] - 46 * s), (m[0] + 46, m[1] + 46 * s)],
                                    fill=RED + (int(255 * x),), width=14) for s in (-1, 1)])
        text(img, (m[0] + 76, m[1]), "never sent on", 52, RED, x, "lm", display=True)
    return img


# ------------------------------------------------------------------ 10. the men
def men_grid(p):
    img = canvas()
    grid_bg(img)
    text(img, (W / 2, 130), "86 MEN WERE ON THE STEEL", 64, INK, phase(p, .05, .2), "mm",
         display=True)
    fade = phase(p, .5, .82)
    appear = phase(p, .1, .38)

    def draw(d):
        for k in range(86):
            row, col = divmod(k, 22)
            x, y = 520 + col * 42, 290 + row * 42
            if k / 86 > appear:
                continue
            alpha = 1.0 if k < 11 else 1.0 - 0.86 * fade
            colr = INK if k < 11 else lerp(INK, RED, fade)
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=colr + (int(255 * alpha),))
    over(img, draw)
    text(img, (W / 2, 540), "33 of them from one small community: Kahnawake", 42, AMBER,
         phase(p, .32, .44), "mm")
    stat(img, "75", "did not come home", phase(p, .72, .88), (W / 2, 790), 190, RED)
    return img


# ------------------------------------------------------------------ 11. collapse
def collapse(p):
    img = canvas()
    grid_bg(img, 0.6)
    water(img, 860)
    lp, rp, deck = W / 2 - 420, W / 2 + 420, 620
    fall = phase(p, .18, .72)
    if fall <= 0:
        over(img, lambda d: cantilever(d, lp, rp, deck, 1.0, INK, 6))
    else:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        cantilever(ImageDraw.Draw(layer), lp, rp, deck, 1.0, INK + (255,), 6)
        drop = int((860 - deck + 300) * fall ** 1.7)
        south = layer.crop((0, 0, int(W / 2 + 60), H)).rotate(-16 * fall, center=(lp, deck),
                                                              resample=Image.BICUBIC)
        img.alpha_composite(layer.crop((int(W / 2 + 60), 0, W, H)), (int(W / 2 + 60), 0))
        faded = south.copy()
        faded.putalpha(south.getchannel("A").point(lambda v: int(v * (1 - 0.45 * fall))))
        img.alpha_composite(faded, (0, drop))
        water(img, 860)
    over(img, lambda d: [d.rectangle([x - 18, deck, x + 18, 900], fill=INK + (255,)) for x in (lp, rp)])
    secs = min(15, int(15 * phase(p, .18, .78)))
    text(img, (W / 2, 160), f"{secs}", 220, RED, phase(p, .1, .2), "mm", black=True)
    text(img, (W / 2, 300), "SECONDS", 56, INK, phase(p, .12, .22), "mm", track=10, display=True)
    return img


DIAGRAMS = {"straw_vs_steel": straw_vs_steel, "tension_compression": tension_compression,
            "ruler_push": ruler_push, "buckling_loop": buckling_loop,
            "builtup_lacing": builtup_lacing, "span_longer": span_longer,
            "cantilever_build": cantilever_build, "bend_record": bend_record,
            "telegram_race": telegram_race, "men_grid": men_grid, "collapse": collapse}
