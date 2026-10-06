"""Render HTML/CSS motion graphics to frames with headless Chromium.

Why HTML and not PIL: CSS gives us real motion design — spring easing, masks, blur,
3D transforms, kinetic type, blend modes — which is what separates a motion graphic
from a slideshow. Chromium is already in the runner, so this costs nothing.

Determinism: every animation is declared in CSS, globally paused, and seeked frame by
frame through the Web Animations API. The same input always produces the same frames.
"""
import subprocess
from pathlib import Path

from common import FPS, H, W

SCENES_DIR = Path(__file__).parent / "scenes"

# Paused up front so nothing has advanced before the first seek.
_BOOT = """
document.getAnimations().forEach(a => { a.pause(); });
window.__seek = (ms) => {
  document.getAnimations().forEach(a => {
    try { a.currentTime = ms; } catch (e) {}
  });
};
window.__seek(0);
"""


def _page(pw, scale=1):
    browser = pw.chromium.launch(args=["--force-color-profile=srgb",
                                       "--disable-lcd-text",
                                       "--hide-scrollbars",
                                       "--force-device-scale-factor=1"])
    page = browser.new_page(viewport={"width": W // scale, "height": H // scale},
                            device_scale_factor=scale)
    return browser, page


def render_html(html_path, duration, out_video, fps=FPS, extra_css=""):
    """Render one HTML scene to a silent mp4 of `duration` seconds."""
    from playwright.sync_api import sync_playwright

    frames = max(1, int(duration * fps))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "mjpeg",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(fps), str(out_video)],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    with sync_playwright() as pw:
        browser, page = _page(pw)
        page.goto(Path(html_path).resolve().as_uri(), wait_until="load")
        if extra_css:
            page.add_style_tag(content=extra_css)
        page.wait_for_timeout(120)          # let fonts settle before the first frame
        page.evaluate(_BOOT)
        step = 1000.0 / fps
        for i in range(frames):
            page.evaluate("ms => window.__seek(ms)", i * step)
            ff.stdin.write(page.screenshot(type="jpeg", quality=94))
        browser.close()

    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"HTML render failed: {html_path}")
    return out_video


def render_markup(body_html, duration, out_video, extra_css="", fps=FPS):
    """Render a scene given as an HTML body fragment plus its own CSS."""
    css_href = (SCENES_DIR / "motion.css").resolve().as_uri()
    doc = (f'<!doctype html><html><head><meta charset="utf-8">'
           f'<link rel="stylesheet" href="{css_href}">'
           f"<style>{extra_css}</style></head><body>{body_html}</body></html>")
    tmp = out_video.parent / f"{out_video.stem}.html"
    tmp.write_text(doc)
    try:
        return render_html(tmp, duration, out_video, fps)
    finally:
        tmp.unlink(missing_ok=True)
