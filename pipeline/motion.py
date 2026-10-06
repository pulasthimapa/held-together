"""Composable pieces for building HTML/CSS motion-graphic scenes.

Scenes are Python functions returning (body_html, css). Everything animates through
CSS keyframes so web.py can seek frame by frame; never use JS timers or transitions.

The retention rules these pieces exist to serve (see docs/research-knowledge.md,
findings 18-19): something must change visually every 5-7 seconds, and each scene
needs its own entrance, development and payoff rather than a single slow zoom.
"""
import html as _html


def esc(s):
    return _html.escape(str(s))


# ---------------------------------------------------------------- type
def kinetic(text, cls="", delay=0.0, step=0.07, size=None, extra=""):
    """Word-by-word type-on. Each word rises, unblurs and settles."""
    words = str(text).split()
    spans = "".join(
        f'<i style="animation-delay:{delay + i * step:.2f}s">{esc(w)}</i> '
        for i, w in enumerate(words))
    style = f'style="{"font-size:%dpx;" % size if size else ""}{extra}"'
    return f'<div class="kinetic {cls}" {style}>{spans}</div>'


def title(text, top=90, size=72, accent="red", delay=0.0, step=0.07, left=110):
    words = "".join(f'<i style="animation-delay:{delay + i * step:.2f}s">{esc(w)}</i> '
                    for i, w in enumerate(str(text).split()))
    return (f'<div class="title display {accent}" '
            f'style="top:{top}px;left:{left}px;font-size:{size}px">{words}</div>')


def caption(text, delay=0.0, bottom=72):
    return (f'<div class="caption" style="animation-delay:{delay:.2f}s;bottom:{bottom}px">'
            f'{esc(text)}</div>')


def label(text, x, y, size=38, color="var(--ink)", delay=0.0, cls="riseIn", anchor="left",
          weight=600, extra=""):
    # The anchoring transform lives on a wrapper: an animation's transform would
    # otherwise replace it and the text would drift off its mark.
    tf = {"left": "", "center": "translateX(-50%)", "right": "translateX(-100%)"}[anchor]
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;'
            f'{"transform:" + tf + ";" if tf else ""}white-space:nowrap">'
            f'<div class="{cls}" style="font-size:{size}px;font-weight:{weight};color:{color};'
            f'animation-delay:{delay:.2f}s;{extra}">{esc(text)}</div></div>')


def stat(value, sub, x, y, delay=0.0, size=200, color="var(--red)"):
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;transform:translateX(-50%);'
            f'text-align:center">'
            f'<div class="big-stat black" style="position:relative;font-size:{size}px;'
            f'color:{color};animation-delay:{delay:.2f}s">{esc(value)}</div>'
            f'<div class="fade" style="font-size:38px;color:var(--mute);margin-top:14px;'
            f'animation-delay:{delay + 0.25:.2f}s">{esc(sub)}</div></div>')


def namecard(name, role, x=110, y=790, delay=0.6, out=None):
    fade_out = (f'<style>.nc{abs(hash(name)) % 9999}'
                f'{{animation:cardIn .5s {delay}s cubic-bezier(.2,.9,.25,1) both,'
                f'fade .4s {out}s reverse both}}</style>') if out else ""
    cls = f"nc{abs(hash(name)) % 9999}" if out else ""
    style = "" if out else f"animation-delay:{delay:.2f}s"
    return (f'{fade_out}<div class="namecard {cls}" style="left:{x}px;top:{y}px;{style}">'
            f'<div class="bar"></div><div class="txt">'
            f'<div class="n display">{esc(name)}</div>'
            f'<div class="r">{esc(role)}</div></div></div>')


# ---------------------------------------------------------------- steel
_STEEL_DEFS = """
<defs>
  <linearGradient id="st" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0"   stop-color="#dfe6f0"/>
    <stop offset=".18" stop-color="#cbd4e0"/>
    <stop offset=".55" stop-color="#8a94a6"/>
    <stop offset="1"   stop-color="#414a59"/>
  </linearGradient>
  <linearGradient id="stHot" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0"   stop-color="#f0c9cd"/>
    <stop offset=".5"  stop-color="#b86a74"/>
    <stop offset="1"   stop-color="#6d2a33"/>
  </linearGradient>
  <linearGradient id="stCool" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0"   stop-color="#cfe2ff"/>
    <stop offset=".5"  stop-color="#7aa2d8"/>
    <stop offset="1"   stop-color="#2f4d78"/>
  </linearGradient>
  <filter id="sh" x="-20%" y="-40%" width="140%" height="220%">
    <feDropShadow dx="0" dy="14" stdDeviation="12" flood-color="#11161f" flood-opacity=".28"/>
  </filter>
</defs>
"""


def _member_path(w, t, bow):
    """Filled outline of a member of length w and thickness t, bowing down by `bow`."""
    return (f"M0,0 Q{w/2},{bow*2} {w},0 L{w},{t} Q{w/2},{t + bow*2} 0,{t} Z")


def _centre_path(w, t, bow, frac=0.5):
    y = t * frac
    return f"M0,{y} Q{w/2},{y + bow*2} {w},{y}"


def member_svg(uid, x, y, w, t, bows, dur, delay=0.0, easing="cubic-bezier(.4,0,.8,1)",
               fill="st", rivets=True, extra_css="", svg_h=None):
    """A steel member that genuinely bends: the SVG path shape is animated.

    `bows` is a list of (percent, bow_px) keyframes.
    """
    svg_h = svg_h or (t + max(b for _, b in bows) * 2 + 40)
    kf_body = "".join(
        f'{p}% {{ d: path("{_member_path(w, t, b)}"); }}' for p, b in bows)
    kf_mid = "".join(
        f'{p}% {{ d: path("{_centre_path(w, t, b)}"); }}' for p, b in bows)
    css = (f'@keyframes bodyB{uid}{{{kf_body}}}'
           f'@keyframes midB{uid}{{{kf_mid}}}'
           f'#body{uid}{{animation:bodyB{uid} {dur}s {easing} {delay}s both}}'
           f'#mid{uid}{{animation:midB{uid} {dur}s {easing} {delay}s both}}'
           f'{extra_css}')
    rv = (f'<path id="mid{uid}" d="{_centre_path(w, t, bows[0][1])}" fill="none" '
          f'stroke="#e9eef5" stroke-width="7" stroke-linecap="round" '
          f'stroke-dasharray="1 76" opacity=".95"/>') if rivets else ""
    body = (f'<svg style="position:absolute;left:{x}px;top:{y}px" width="{w}" height="{svg_h}" '
            f'viewBox="0 0 {w} {svg_h}">{_STEEL_DEFS}'
            f'<path id="body{uid}" d="{_member_path(w, t, bows[0][1])}" fill="url(#{fill})" '
            f'filter="url(#sh)"/>{rv}</svg>')
    return body, css


def plates_svg(uid, x, y, w, t, n, gaps, bows, dur, delay=0.0):
    """A built-up member: n plates that can spread apart and bow independently."""
    plate_t = t / n
    paths, css = [], ""
    for k in range(n):
        kf = "".join(
            f'{p}% {{ d: path("{_member_path(w, plate_t, b)}"); '
            f'transform: translateY({k * (plate_t + g)}px); }}'
            for (p, b), (_, g) in zip(bows, gaps))
        css += (f'@keyframes pl{uid}_{k}{{{kf}}}'
                f'#pl{uid}_{k}{{animation:pl{uid}_{k} {dur}s cubic-bezier(.4,0,.8,1) '
                f'{delay}s both}}')
        paths.append(f'<path id="pl{uid}_{k}" d="{_member_path(w, plate_t, bows[0][1])}" '
                     f'fill="url(#st)"/>')
    h = t + max(b for _, b in bows) * 2 + n * max(g for _, g in gaps) + 60
    body = (f'<svg style="position:absolute;left:{x}px;top:{y}px" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{_STEEL_DEFS}{"".join(paths)}</svg>')
    return body, css


def lacing_svg(uid, x, y, w, h, delay=0.0, dur=0.8, color="#6c7casdf"):
    zig = []
    n = 11
    for i in range(n):
        x0, x1 = w * i / n, w * (i + 0.5) / n
        zig.append(f"M{x0},0 L{x1},{h} L{w * (i + 1) / n},0")
    css = (f'#lc{uid}{{stroke-dasharray:4000;stroke-dashoffset:4000;'
           f'animation:dash{uid} {dur}s {delay}s ease both}}'
           f'@keyframes dash{uid}{{to{{stroke-dashoffset:0}}}}')
    body = (f'<svg style="position:absolute;left:{x}px;top:{y}px" width="{w}" height="{h}">'
            f'<path id="lc{uid}" d="{" ".join(zig)}" fill="none" stroke="#5b6475" '
            f'stroke-width="7"/></svg>')
    return body, css


_ARROW_N = [0]


def arrow(x, y, length, delay=0.0, flip=False, color="red", grow=None, dur=1.0):
    """Force arrow pointing right, or left when flipped. `grow` swells it as load rises.

    `x` is always the left edge of the drawn arrow, flipped or not, so callers do not
    have to reason about the rotation origin.
    """
    _ARROW_N[0] += 1
    uid = _ARROW_N[0]
    cls = "arrow" + (" blue" if color == "blue" else "")
    rot = "rotate(180deg) " if flip else ""
    if grow:
        css = (f"@keyframes arw{uid}{{from{{transform:{rot}scaleY(1)}}"
               f"to{{transform:{rot}scaleY({grow})}}}}")
        anim = f"animation:arw{uid} {dur}s {delay}s cubic-bezier(.4,0,.8,1) both"
    else:
        css = ""
        anim = f"transform:{rot or 'none'};animation:fade .4s {delay}s ease both"
    return (f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{length}px;'
            f'transform-origin:center center;{anim}"></div>', css)


# ---------------------------------------------------------------- layout
def panel_label(text, side, color, delay=0.0):
    x = 100 if side == "left" else 1060
    return (f'<div class="panel-label" style="left:{x}px;background:{color};'
            f'animation-delay:{delay:.2f}s">{esc(text)}</div>')


def divider(delay=0.0):
    return (f'<div class="divider" style="animation:wipeY .5s {delay}s ease both;'
            f'transform-origin:top center"></div>'
            f'<style>@keyframes wipeY{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}</style>')


def stage(body, deep=False, grid=True, vignette=False):
    cls = "stage" + (" grid" if grid else "") + (" deep" if deep else "")
    v = '<div class="vignette"></div>' if vignette else ""
    return f'<div class="{cls}">{body}{v}</div>'


def water(y=840, delay=0.0):
    return (f'<div style="position:absolute;left:0;top:{y}px;width:1920px;height:{1080 - y}px;'
            f'background:linear-gradient(180deg,#b0cee6,#8fb4d4);'
            f'animation:riseIn .7s {delay}s cubic-bezier(.2,.9,.25,1) both"></div>')
