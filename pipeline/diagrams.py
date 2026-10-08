"""Engineering explainers as HTML/CSS motion graphics.

Each builder returns (body_html, css) for a scene of `dur` seconds. web.py renders them
with headless Chromium, seeking frame by frame, so the output is deterministic.

The teaching rule for every one of these: an everyday object first, then the real thing.
The retention rule: something changes visually every few seconds — entrance, development,
payoff — never one slow move held for fifteen seconds.
"""
import motion as M

# Minimum seconds so a short line of narration still gets a readable animation.
MIN_SECONDS = {"collapse": 8.0, "buckling_loop": 10.0, "builtup_lacing": 13.0,
               "straw_vs_steel": 8.0, "ruler_push": 8.0, "tension_compression": 10.0,
               "cantilever_build": 10.0, "men_grid": 9.0, "span_longer": 10.0,
               "telegram_race": 12.0, "bend_record": 10.0}


# ------------------------------------------------------------------ 1. hook
def straw_vs_steel(dur):
    css = ""
    # left: a drinking straw folding. right: the same thing in steel.
    straw = ('<svg style="position:absolute;left:150px;top:430px" width="660" height="300">'
             '<path id="straw" d="M0,40 Q330,40 660,40 L660,74 Q330,74 0,74 Z" fill="#e3e9f2"/>'
             '<path d="M0,44 Q330,44 660,44" stroke="#fff" stroke-width="5" fill="none"/>'
             '</svg>')
    css += ('@keyframes strawB{0%{d:path("M0,40 Q330,40 660,40 L660,74 Q330,74 0,74 Z")}'
            '100%{d:path("M0,40 Q330,300 660,40 L660,74 Q330,334 0,74 Z")}}'
            f'#straw{{animation:strawB {dur * .55:.1f}s cubic-bezier(.5,0,.75,1) 1.2s both}}')
    steel, c2 = M.member_svg("hk", 1110, 420, 660, 86,
                             [(0, 6), (100, 92)], dur * .55, delay=1.6)
    css += c2
    a1, ca1 = M.arrow(60, 452, 110, 0.7, False, "red", 1.6, dur * .6)
    a2, ca2 = M.arrow(840, 452, 110, 0.7, True, "red", 1.6, dur * .6)
    a3, ca3 = M.arrow(1000, 452, 110, 1.2, False, "red", 1.9, dur * .6)
    a4, ca4 = M.arrow(1800, 452, 110, 1.2, True, "red", 1.9, dur * .6)
    css += ca1 + ca2 + ca3 + ca4
    body = (M.divider(0.2)
            + M.panel_label("A PLASTIC STRAW", "left", "var(--mute)", 0.1)
            + M.panel_label("1,000 TONNES OF STEEL", "right", "var(--red)", 0.45)
            + straw + steel + a1 + a2 + a3 + a4
            + M.caption("Same failure. Exactly the same physics.", dur * .7))
    return M.stage(body), css


# ------------------------------------------------------------------ 2. two forces
def tension_compression(dur):
    css = ""
    rope_t = ('<svg style="position:absolute;left:560px;top:330px" width="800" height="160">'
              '<path id="ropeT" d="M0,60 Q400,130 800,60" stroke="#a87c46" stroke-width="18" '
              'fill="none" stroke-linecap="round"/></svg>')
    css += ('@keyframes rT{0%{d:path("M0,60 Q400,130 800,60")}'
            '100%{d:path("M0,60 Q400,62 800,60")}}'
            '#ropeT{animation:rT .9s 1.1s cubic-bezier(.2,.9,.25,1) both}')
    rope_c = ('<svg style="position:absolute;left:560px;top:700px" width="800" height="240">'
              '<path id="ropeC" d="M0,90 Q400,90 800,90" stroke="#a87c46" stroke-width="18" '
              'fill="none" stroke-linecap="round"/></svg>')
    css += ('@keyframes rC{0%{d:path("M0,90 Q400,90 800,90")}'
            '100%{d:path("M0,90 C200,-40 300,230 400,90 C500,-40 600,230 800,90")}}'
            f'#ropeC{{animation:rC .8s {dur * .62:.1f}s cubic-bezier(.6,0,.9,1) both}}')
    a1, c1 = M.arrow(400, 382, 120, 0.9, True, "blue")
    a2, c2 = M.arrow(1400, 382, 120, 0.9, False, "blue")
    a3, c3 = M.arrow(400, 782, 120, dur * .56, False, "red")
    a4, c4 = M.arrow(1400, 782, 120, dur * .56, True, "red")
    css += c1 + c2 + c3 + c4
    body = (M.title("TWO WAYS TO LOAD ANYTHING.", 80, 62, "blue")
            + rope_t + a1 + a2 + rope_c + a3 + a4
            + M.label("PULL", 330, 368, 46, "var(--blue)", 0.9, "riseIn", "right")
            + M.label("TENSION — a rope works fine", 960, 250, 44, "var(--ink)", 1.5,
                      "riseIn", "center")
            + M.label("it just pulls tight. nothing to go wrong.", 960, 500, 36,
                      "var(--mute)", 1.9, "fade", "center", 500)
            + M.label("PUSH", 330, 768, 46, "var(--red)", dur * .56, "riseIn", "right")
            + M.label("COMPRESSION — now it matters what the thing is made of", 960, 876, 42,
                      "var(--red)", dur * .74, "riseIn", "center")
            + M.caption("The Quebec Bridge failed in compression.", dur * .86, 28))
    return M.stage(body), css


# ------------------------------------------------------------------ 3. ruler
def ruler_push(dur):
    rule = ('<svg style="position:absolute;left:430px;top:470px" width="1060" height="340">'
            '<path id="rulerB" d="M0,60 Q530,60 1060,60 L1060,96 Q530,96 0,96 Z" '
            'fill="#ffce4a" stroke="#d9a21f" stroke-width="3"/>'
            '<path id="rulerT" d="M0,66 Q530,66 1060,66" stroke="#fff3cd" stroke-width="7" '
            'fill="none"/>'
            '<path id="rulerTick" d="M0,78 Q530,78 1060,78" stroke="#9a7415" stroke-width="20" '
            'fill="none" stroke-dasharray="2 50"/></svg>')
    b0 = 'M0,60 Q530,60 1060,60 L1060,96 Q530,96 0,96 Z'
    b1 = 'M0,60 Q530,380 1060,60 L1060,96 Q530,416 0,96 Z'
    css = (f'@keyframes rb{{0%{{d:path("{b0}")}}100%{{d:path("{b1}")}}}}'
           f'#rulerB{{animation:rb {dur * .55:.1f}s cubic-bezier(.45,0,.75,1) 1.1s both}}'
           '@keyframes rt{0%{d:path("M0,66 Q530,66 1060,66")}'
           '100%{d:path("M0,66 Q530,386 1060,66")}}'
           f'#rulerT{{animation:rt {dur * .55:.1f}s cubic-bezier(.45,0,.75,1) 1.1s both}}'
           '@keyframes rk{0%{d:path("M0,78 Q530,78 1060,78")}'
           '100%{d:path("M0,78 Q530,398 1060,78")}}'
           f'#rulerTick{{animation:rk {dur * .55:.1f}s cubic-bezier(.45,0,.75,1) 1.1s both}}')
    a1, c1 = M.arrow(250, 522, 150, 0.8, False, "red", 1.7, dur * .55)
    a2, c2 = M.arrow(1520, 522, 150, 0.8, True, "red", 1.7, dur * .55)
    css += c1 + c2
    body = (M.title("TRY THIS YOURSELF.", 90, 78, "blue")
            + rule + a1 + a2
            + M.label("it bows", 1560, 640, 52, "var(--red)", dur * .6, "popIn", "left",
                      800, "font-family:Montserrat,sans-serif")
            + M.caption("It never snaps. It bends sideways and keeps going.", dur * .72))
    return M.stage(body), css


# ------------------------------------------------------------------ 4. the loop
def buckling_loop(dur):
    body_svg, css = M.member_svg("bl", 380, 400, 1000, 82,
                                 [(0, 8), (30, 32), (60, 76), (100, 156)],
                                 dur * .78, delay=0.9)
    a1, c1 = M.arrow(214, 432, 150, 0.6, False, "red", 2.0, dur * .78)
    a2, c2 = M.arrow(1556, 432, 150, 0.6, True, "red", 2.0, dur * .78)
    css += c1 + c2
    # the member reddens as it weakens
    css += ('@keyframes hot{from{filter:none}to{filter:hue-rotate(-28deg) saturate(2.4) '
            'brightness(.92)}}'
            f'#bodybl{{animation:bodyBbl {dur * .78:.1f}s cubic-bezier(.4,0,.8,1) .9s both,'
            f'hot {dur * .78:.1f}s linear .9s both}}')
    # strength meter draining
    css += ('@keyframes drain{0%{transform:scaleY(1);background:var(--green)}'
            '32%{transform:scaleY(.74);background:var(--green)}'
            '46%{background:var(--amber)}62%{transform:scaleY(.45);background:var(--amber)}'
            '80%{background:var(--red)}100%{transform:scaleY(.12);background:var(--red)}}'
            f'#drainbar{{animation:drain {dur * .78:.1f}s cubic-bezier(.4,0,.8,1) .9s both}}')
    meter = ('<div class="meter" style="left:1668px;top:300px;height:380px">'
             '<div class="fill" id="drainbar" style="height:100%"></div></div>')
    steps = "".join(
        M.label(t, 960, 700 + i * 72, 50, c, d, "popIn", "center", 700,
                "font-family:Montserrat,sans-serif")
        for i, (t, c, d) in enumerate([
            ("1. it bows", "var(--amber)", dur * .22),
            ("2. so it carries less", "var(--red)", dur * .45),
            ("3. so it bows further", "var(--red)", dur * .65)]))
    body = (M.title("BUCKLING", 96, 128, "red", left=620)
            + body_svg + a1 + a2 + meter
            + M.label("STRENGTH", 1707, 252, 30, "var(--ink)", 0.8, "fade", "center")
            + steps
            + M.caption("Each turn of the loop is faster than the last.", dur * .84, 40))
    return M.stage(body, deep=True), css


# ------------------------------------------------------------------ 5. built-up members
def builtup_lacing(dur):
    css = ""
    solid, c1 = M.member_svg("sl", 110, 400, 740, 132, [(0, 6), (100, 22)], dur * .6, 1.4)
    plates, c2 = M.plates_svg("pl", 1070, 400, 740, 132, 4,
                              [(0, 2), (55, 2), (100, 30)],
                              [(0, 6), (55, 26), (100, 88)], dur * .6, 1.4)
    lace, c3 = M.lacing_svg("lc", 1090, 404, 700, 132, 0.8, 0.9)
    css += c1 + c2 + c3
    css += ('@keyframes laceGo{0%{opacity:1}70%{opacity:1}100%{opacity:0}}'
            f'#lclc{{animation:dashlc .9s .8s ease both,laceGo {dur * .6:.1f}s 1.4s linear both}}')
    a1, ca1 = M.arrow(20, 452, 80, 1.1, False, "blue")
    a2, ca2 = M.arrow(858, 452, 80, 1.1, True, "blue")
    a3, ca3 = M.arrow(980, 452, 80, 1.1, False, "red")
    a4, ca4 = M.arrow(1818, 452, 80, 1.1, True, "red")
    css += ca1 + ca2 + ca3 + ca4
    body = (M.divider(0.15)
            + M.panel_label("LACED TIGHTLY", "left", "var(--blue)", 0.1)
            + M.panel_label("LACED TOO LIGHTLY", "right", "var(--red)", 0.4)
            + solid + lace + plates + a1 + a2 + a3 + a4
            + M.label("acts as ONE thick member", 480, 736, 40, "var(--blue)", dur * .5,
                      "riseIn", "center")
            + M.label("strong", 480, 796, 62, "var(--blue)", dur * .56, "popIn", "center",
                      800, "font-family:Montserrat,sans-serif")
            + M.label("four ribs bend SEPARATELY", 1440, 736, 38, "var(--red)", dur * .5,
                      "riseIn", "center")
            + M.label("far weaker", 1440, 796, 62, "var(--red)", dur * .56, "popIn", "center",
                      800, "font-family:Montserrat,sans-serif")
            + M.caption("The Quebec Bridge had the second kind.", dur * .78))
    return M.stage(body), css


# ------------------------------------------------------------------ 6. the span decision
def span_longer(dur):
    def truss(x, w, uid, delay):
        return (f'<svg style="position:absolute;left:{x}px;top:380px" width="{w}" height="300">'
                f'<path id="{uid}" d="M0,260 L{w/2},0 L{w},260 Z" fill="none" stroke="#11161f" '
                f'stroke-width="6"/>'
                + "".join(f'<line x1="{w*k/12}" y1="260" x2="{w*k/12}" '
                          f'y2="{260 - 260*min(k,12-k)/6}" stroke="#11161f" stroke-width="3"/>'
                          for k in range(1, 12))
                + f'<line x1="0" y1="260" x2="{w}" y2="260" stroke="#11161f" stroke-width="6"/>'
                f'</svg>')
    css = ('@keyframes grow{from{transform:scaleX(1)}to{transform:scaleX(1.26)}}'
           f'#spanwrap{{transform-origin:center center;'
           f'animation:grow 1.1s {dur * .34:.1f}s cubic-bezier(.2,.9,.25,1) both}}'
           '@keyframes dimGrow{from{width:640px}to{width:880px}}'
           f'#dim{{animation:dimGrow 1.1s {dur * .34:.1f}s cubic-bezier(.2,.9,.25,1) both}}')
    bridge = (f'<div id="spanwrap" style="position:absolute;left:0;top:0;width:1920px;'
              f'height:1080px">{truss(320, 560, "t1", 0.5)}{truss(1040, 560, "t2", 0.7)}'
              f'<div style="position:absolute;left:584px;top:640px;width:32px;height:230px;'
              f'background:var(--ink)"></div>'
              f'<div style="position:absolute;left:1304px;top:640px;width:32px;height:230px;'
              f'background:var(--ink)"></div></div>')
    dim = ('<div style="position:absolute;left:600px;top:872px">'
           '<div id="dim" class="wipeIn" style="height:5px;background:var(--red);width:640px;'
           'animation-delay:1.3s"></div></div>')
    body = (M.water(860, 0.2)
            + M.title("MAKE THE SPAN LONGER,", 70, 58, "amber")
            + M.title("AND THE STEEL GETS HEAVIER.", 142, 58, "amber", delay=0.35)
            + bridge + dim
            + M.label("1,600 ft", 960, 902, 44, "var(--red)", 1.5, "fade", "center", 700,
                      f"animation:fade .4s 1.5s ease both,fade .3s {dur * .42:.1f}s "
                      f"reverse both")
            + M.label("1,800 ft", 960, 902, 44, "var(--red)", dur * .48, "popIn", "center", 700,
                      "font-family:Montserrat,sans-serif")
            + M.label("A bridge this size mostly carries its own weight.", 960, 954, 44,
                      "var(--ink)", dur * .64, "riseIn", "center")
            + M.label("more span → more steel → more weight → more steel again", 960, 1004, 36,
                      "var(--red)", dur * .76, "riseIn", "center", 500))
    return M.stage(body), css


# ------------------------------------------------------------------ 7. how it is built
def cantilever_build(dur):
    """Two arms creeping out from their piers towards each other, with nothing below."""
    def arm(uid, x, flip):
        webs = "".join(
            f'<line x1="{640 * k / 9}" y1="260" x2="{640 * k / 9}" '
            f'y2="{260 - 260 * min(k, 9 - k) / 4.5}" stroke="#11161f" stroke-width="3"/>'
            for k in range(1, 9))
        mirror = " style='transform:scaleX(-1);transform-origin:center'" if flip else ""
        return (f'<svg style="position:absolute;left:{x}px;top:380px" width="640" height="300">'
                f'<g id="{uid}"{mirror}>'
                f'<path d="M0,260 L320,0 L640,260 Z" fill="none" stroke="#11161f" '
                f'stroke-width="6"/>{webs}'
                f'<line x1="0" y1="260" x2="640" y2="260" stroke="#11161f" '
                f'stroke-width="6"/></g></svg>')
    css = ('@keyframes revealR{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}'
           '@keyframes revealL{from{clip-path:inset(0 0 0 100%)}to{clip-path:inset(0 0 0 0)}}'
           f'#armA{{animation:revealR {dur * .6:.1f}s linear .6s both}}'
           f'#armB{{animation:revealL {dur * .6:.1f}s linear .6s both}}'
           '@keyframes craneA{from{transform:translateX(0)}to{transform:translateX(470px)}}'
           '@keyframes craneB{from{transform:translateX(0)}to{transform:translateX(-470px)}}'
           f'#craneA{{animation:craneA {dur * .6:.1f}s linear .6s both}}'
           f'#craneB{{animation:craneB {dur * .6:.1f}s linear .6s both}}')

    def crane(uid, x):
        return (f'<div id="{uid}" style="position:absolute;left:{x}px;top:500px">'
                '<div style="width:30px;height:140px;background:var(--amber)"></div>'
                '<div style="position:absolute;left:24px;top:-8px;width:130px;height:8px;'
                'background:var(--ink);transform:rotate(22deg);transform-origin:left"></div></div>')

    pier = lambda x: (f'<div style="position:absolute;left:{x}px;top:640px;width:34px;'
                      f'height:240px;background:var(--ink)"></div>')
    body = (M.water(860, 0.2)
            + M.title("BUILT OUT INTO MID-AIR.", 80, 64, "blue")
            + arm("armA", 160, False) + arm("armB", 1120, True)
            + pier(464) + pier(1424) + crane("craneA", 200) + crane("craneB", 1690)
            + M.label("no scaffolding. nothing underneath.", 960, 940, 46, "var(--ink)",
                      dur * .55, "riseIn", "center")
            + M.label("every day's work made the arms longer, heavier, harder to stop",
                      960, 1000, 36, "var(--red)", dur * .7, "riseIn", "center", 500))
    return M.stage(body), css


# ------------------------------------------------------------------ 8. the measurements
def bend_record(dur):
    css = ""
    # Real measurements only (Royal Commission 1908, Vol. I p. 87; STRUCTURE magazine):
    # one rib of lower chord 9-L, about 3/4 in out of line a little over a week before
    # 27 August, 2 1/4 in on 27 August. No later measurement was taken.
    rows = [("mid-August", 30, "st", 0.0, "\u00be in"),
            ("27 August", 90, "stHot", 0.3, "2\u00bc in")]
    out = ""
    for i, (when, bow, fill, t, value) in enumerate(rows):
        d = dur * (0.18 + t)
        svg, c = M.member_svg(f"br{i}", 480, 360 + i * 185, 980, 46,
                              [(0, 4), (100, bow)], 0.9, d, fill=fill)
        css += c
        css += (f'#br{i}wrap{{animation:riseIn .5s {d:.2f}s cubic-bezier(.2,.9,.25,1) both}}')
        out += (f'<div id="br{i}wrap" style="position:absolute;left:0;top:0">{svg}'
                + M.label(when, 440, 376 + i * 185, 40, "var(--ink)", d, "fade", "right")
                + M.label(value, 1500, 376 + i * 185, 44,
                          ["var(--amber)", "var(--red)"][i], d + 0.5,
                          "popIn", "left", 700, "font-family:Montserrat,sans-serif")
                + '</div>')
    body = (M.title("THE BEND KEPT GROWING.", 80, 66, "amber")
            + out
            + M.label("one rib of lower chord 9-L, out of line", 960, 820, 34, "var(--mute)",
                      dur * .45, "fade", "center")
            + M.namecard("Norman McLure", "inspecting engineer, on site", 1240, 140, dur * .5)
            + M.caption("Not old damage. The loop, already running.", dur * .82))
    return M.stage(body), css


# ------------------------------------------------------------------ 9. the telegram race
def telegram_race(dur):
    NY, PA, QC = (1180, 700), (980, 790), (1420, 300)
    css = ('@keyframes drawL{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}'
           '@keyframes tick{to{transform:rotate(360deg)}}')
    river = ('<svg style="position:absolute;left:0;top:0" width="1920" height="1080">'
             '<path d="M900,560 Q1150,440 1340,330 T1700,170" stroke="#b0cee6" '
             'stroke-width="14" fill="none" class="drawIn" '
             'style="animation-delay:.2s;animation-duration:1.2s"/>'
             f'<path id="legA" d="M{NY[0]},{NY[1]} L{PA[0]},{PA[1]}" stroke="#e8192c" '
             'stroke-width="10" fill="none" stroke-dasharray="300" '
             f'style="--len:300;animation:drawL .9s {dur * .28:.1f}s ease both"/>'
             f'<path id="legB" d="M{PA[0]},{PA[1]} L{QC[0]},{QC[1]}" stroke="#7a869a" '
             'stroke-width="7" fill="none" stroke-dasharray="14 18" '
             f'style="--len:700;stroke-dashoffset:700;animation:drawL 1.4s {dur * .5:.1f}s ease both"/>'
             '</svg>')

    def pin(xy, name, delay, side=1):
        return (f'<div style="position:absolute;left:{xy[0]-14}px;top:{xy[1]-14}px;width:28px;'
                f'height:28px;border-radius:50%;background:var(--ink);'
                f'animation:statPop .45s {delay}s cubic-bezier(.16,1.3,.4,1) both"></div>'
                + M.label(name, xy[0] + 30 * side, xy[1] - 20, 38, "var(--ink)", delay + 0.1,
                          "riseIn", "left" if side > 0 else "right"))

    def clock(x, y, hh, mm, delay, cap):
        ang_h, ang_m = (hh % 12 + mm / 60) * 30, mm * 6
        return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:190px;height:190px;'
                f'border:7px solid var(--ink);border-radius:50%;background:#fff;'
                f'animation:statPop .5s {delay}s cubic-bezier(.16,1.3,.4,1) both">'
                f'<div style="position:absolute;left:50%;top:50%;width:7px;height:52px;'
                f'background:var(--ink);transform-origin:top center;'
                f'transform:translate(-50%,0) rotate({ang_h + 180}deg)"></div>'
                f'<div style="position:absolute;left:50%;top:50%;width:5px;height:74px;'
                f'background:var(--red);transform-origin:top center;'
                f'transform:translate(-50%,0) rotate({ang_m + 180}deg)"></div></div>'
                + M.label(cap, x + 95, y + 206, 32, "var(--ink)", delay + 0.2, "fade", "center"))

    cross = (f'<div style="position:absolute;left:{(PA[0]+QC[0])//2 - 50}px;'
             f'top:{(PA[1]+QC[1])//2 - 50}px;width:100px;height:100px;'
             f'animation:statPop .5s {dur*.78:.1f}s cubic-bezier(.16,1.3,.4,1) both">'
             '<div style="position:absolute;top:44px;width:100px;height:14px;'
             'background:var(--red);transform:rotate(45deg)"></div>'
             '<div style="position:absolute;top:44px;width:100px;height:14px;'
             'background:var(--red);transform:rotate(-45deg)"></div></div>')
    body = (river
            + pin(NY, "New York", 0.2) + pin(PA, "Phoenixville, Pennsylvania", 0.45, -1)
            + pin(QC, "the bridge, Quebec", 0.7)
            + clock(150, 70, 12, 16, dur * .14, "12:16 pm — sent")
            + clock(150, 390, 13, 15, dur * .30, "1:15 pm — arrives")
            + clock(150, 710, 15, 0, dur * .46, "about 3 pm — read")
            + cross
            + M.label("no stop order", (PA[0] + QC[0]) // 2 + 80, (PA[1] + QC[1]) // 2 - 28,
                      52, "var(--red)", dur * .82, "riseIn", "left", 800,
                      "font-family:Montserrat,sans-serif"))
    return M.stage(body), css


# ------------------------------------------------------------------ 10. the men
def men_grid(dur):
    dots = ""
    for k in range(86):
        row, col = divmod(k, 22)
        x, y = 520 + col * 42, 300 + row * 42
        appear = 0.5 + k * 0.012
        if k < 11:
            anim = f"animation:statPop .4s {appear:.2f}s cubic-bezier(.16,1.3,.4,1) both"
        else:
            anim = (f"animation:statPop .4s {appear:.2f}s cubic-bezier(.16,1.3,.4,1) both,"
                    f"gone .5s {dur * .55 + (k % 22) * 0.012:.2f}s ease both")
        dots += (f'<div style="position:absolute;left:{x-14}px;top:{y-14}px;width:28px;'
                 f'height:28px;border-radius:50%;background:var(--ink);{anim}"></div>')
    css = ('@keyframes gone{from{opacity:1;background:var(--ink);transform:none}'
           'to{opacity:.14;background:var(--red);transform:translateY(26px)}}')
    body = (M.label("86 MEN AT WORK ON THE BRIDGE", 960, 120, 64, "var(--ink)", 0.1, "riseIn",
                    "center", 800, "font-family:Montserrat,sans-serif")
            + dots
            + M.label("33 of the dead came from one community: Kahnawake", 960, 540, 42,
                      "var(--amber)", dur * .34, "riseIn", "center")
            + M.stat("75", "did not come home", 960, 700, dur * .72, 190))
    return M.stage(body), css


# ------------------------------------------------------------------ 11. collapse
def collapse(dur):
    css = (f'@keyframes fall{{0%{{transform:none;opacity:1}}'
           f'30%{{transform:translateY(40px) rotate(-5deg)}}'
           f'100%{{transform:translateY(560px) rotate(-22deg);opacity:.35}}}}'
           f'#southArm{{transform-origin:right center;'
           f'animation:fall {dur * .55:.1f}s cubic-bezier(.5,0,.9,1) {dur * .18:.1f}s both}}'
           '@keyframes shake{0%,100%{transform:none}25%{transform:translateX(-6px)}'
           '75%{transform:translateX(6px)}}'
           f'#shaker{{animation:shake .12s {dur * .18:.1f}s 6 both}}'
           '@keyframes counter{from{opacity:0}to{opacity:1}}')
    def arm(uid, x, flip):
        webs = "".join(
            f'<line x1="{700 * k / 10}" y1="280" x2="{700 * k / 10}" '
            f'y2="{280 - 280 * min(k, 10 - k) / 5}" stroke="#11161f" stroke-width="3"/>'
            for k in range(1, 10))
        mirror = ' style="transform:scaleX(-1)"' if flip else ""
        return (f'<svg id="{uid}" style="position:absolute;left:{x}px;top:380px" width="700" '
                f'height="300"><g{mirror} transform-origin="center">'
                f'<path d="M0,280 L350,0 L700,280 Z" fill="none" stroke="#11161f" '
                f'stroke-width="7"/>{webs}'
                f'<line x1="0" y1="280" x2="700" y2="280" stroke="#11161f" '
                f'stroke-width="7"/></g></svg>')
    pier = lambda x: (f'<div style="position:absolute;left:{x}px;top:640px;width:36px;'
                      f'height:250px;background:var(--ink);z-index:3"></div>')
    body = (M.water(880, 0.0)
            + f'<div id="shaker">{arm("southArm", 160, False)}{arm("northArm", 1060, True)}</div>'
            + pier(492) + pier(1392)
            + M.stat("4\u20138", "SECONDS", 960, 110, dur * .12, 230))
    return M.stage(body, vignette=True), css


DIAGRAMS = {"straw_vs_steel": straw_vs_steel, "tension_compression": tension_compression,
            "ruler_push": ruler_push, "buckling_loop": buckling_loop,
            "builtup_lacing": builtup_lacing, "span_longer": span_longer,
            "cantilever_build": cantilever_build, "bend_record": bend_record,
            "telegram_race": telegram_race, "men_grid": men_grid, "collapse": collapse}
