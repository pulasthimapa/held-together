"""Stage 4: assemble the long-form video and the vertical cuts with ffmpeg."""
import re
import shutil

from PIL import Image, ImageDraw

import diagrams
import style as S
import web
from common import (FONT_SANS_BOLD, FPS, H, ROOT, W, clean,
                    duration, episode_dir, load_episode, run)

NAME_CARD_SECONDS = 3.4   # how long a person's name card stays on screen

TAIL = 0.6          # breathing room after each narrated line (seconds)
FADE = 0.35
VIDEO_ARGS = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
              "-r", str(FPS)]
AUDIO_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


# ---------- timing and captions ----------

def scene_timing(ep_id, scene):
    audio = episode_dir(ep_id) / "audio" / f"{scene['id']}.mp3"
    if scene.get("narration") and audio.exists():
        dur = duration(audio) + TAIL
    else:
        audio = None
        dur = float(scene.get("hold", 3))
    dur += float(scene.get("hold_after", 0))
    if scene["type"] == "diagram":
        dur = max(dur, diagrams.MIN_SECONDS.get(scene["diagram"], 0))
    return audio, round(dur, 2)


def caption_chunks(text, max_words=7):
    words = clean(text).split()
    chunks, current = [], []
    for w in words:
        current.append(w)
        if len(current) >= max_words or (re.search(r"[.,:;?!]$", w) and len(current) >= 3):
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def captions_for(scenes_with_times):
    """scenes_with_times: list of (scene, start, spoken_seconds). Returns SRT text."""
    lines, n = [], 1
    for scene, start, spoken in scenes_with_times:
        if not scene.get("narration") or spoken <= 0:
            continue
        chunks = caption_chunks(scene["narration"])
        total = sum(len(c) for c in chunks)
        t = start
        for c in chunks:
            d = spoken * len(c) / total
            lines.append(f"{n}\n{srt_time(t)} --> {srt_time(t + d)}\n{c}\n")
            n += 1
            t += d
    return "\n".join(lines)


# ---------- per-scene clips ----------

def placeholder(path, label):
    im = Image.new("RGB", (W, H), (60, 58, 55))
    d = ImageDraw.Draw(im)
    from PIL import ImageFont
    d.text((W // 2, H // 2), label, font=ImageFont.truetype(FONT_SANS_BOLD, 90),
           fill=(200, 190, 170), anchor="mm")
    im.save(path, quality=90)


def card_image(path, scene):
    """Title / statement card in the channel's bright house style."""
    im = S.canvas()
    S.grid_bg(im, 0.7)
    title, sub = scene.get("title", ""), scene.get("subtitle", "")
    if title:
        d0 = ImageDraw.Draw(im)
        f = S.font(96, display=True)
        lines = S.wrap(d0, title, f, W - 420)
        y = H / 2 - (len(lines) * 108) / 2 - (30 if sub else 0)
        S.over(im, lambda d: d.rectangle([W / 2 - 150, y - 56, W / 2 + 150, y - 44],
                                         fill=S.RED + (255,)))
        for i, ln in enumerate(lines):
            S.text(im, (W / 2, y + i * 108 + 54), ln, 96, S.INK, 1.0, "mm", display=True)
        y += len(lines) * 108
    else:
        y = H / 2
    if sub:
        S.text(im, (W / 2, y + 60), sub, 42, S.MUTE, 1.0, "mm", bold=False)
    im.convert("RGB").save(path, quality=95)


def name_card_overlay(path, name, role):
    """Transparent PNG laid over a scene so the viewer knows who they are looking at."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    S.lower_third(im, name, role, 1.0, x=110, y=H - 300)
    im.save(path)


MAX_SHOT = 7.0      # research: change something visually at least this often
MIN_SHOT = 2.6      # below this a cut reads as a glitch rather than an edit


def shot_plan(dur, n_images):
    """Split a scene into shots so no single picture is held longer than MAX_SHOT.

    Returns a list of (image_index, seconds, motion). Alternating the camera move
    between shots is what stops a sequence of cuts feeling like a slideshow.
    """
    if n_images <= 1 and dur <= MAX_SHOT:
        return [(0, dur, None)]
    want = max(1, min(n_images if n_images > 1 else 99,
                      int(dur // MAX_SHOT) + (1 if dur % MAX_SHOT > MIN_SHOT else 0)))
    want = max(want, 1)
    if n_images > 1:
        want = max(want, n_images)
    each = dur / want
    while each < MIN_SHOT and want > 1:
        want -= 1
        each = dur / want
    moves = ["in", "left", "out", "right"]
    return [(i % max(n_images, 1), each, moves[i % len(moves)]) for i in range(want)]


def scene_images(base, sid):
    """All stills for a scene: S12.jpg, then S12b.jpg, S12c.jpg … for extra angles."""
    found = []
    for suffix in ("", "b", "c", "d"):
        for folder in ("archival", "images"):
            p = base / folder / f"{sid}{suffix}.jpg"
            if p.exists():
                found.append(p)
                break
    return found


def motion_filter(kind, frames):
    z_end = 1.12
    if kind == "out":
        z = f"{z_end}-({z_end}-1)*on/{frames}"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif kind in ("left", "right"):
        z = "1.1"
        travel = "(iw-iw/zoom)"
        x = f"{travel}*on/{frames}" if kind == "right" else f"{travel}*(1-on/{frames})"
        y = "ih/2-(ih/zoom/2)"
    else:  # push in
        z = f"1+({z_end}-1)*on/{frames}"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return (f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}")


def audio_inputs(audio, dur):
    if audio:
        return ["-i", str(audio)], f"[1:a]apad,atrim=0:{dur},aformat=sample_rates=44100:channel_layouts=stereo[a]"
    return (["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo"],
            "[1:a]anull[a]")


def still_clip(image, audio, dur, motion, out, name_card=None):
    frames = int(dur * FPS)
    ain, afilter = audio_inputs(audio, dur)
    base = (f"[0:v]{motion_filter(motion, frames)},"
            f"fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE}:d={FADE},format=yuv420p")
    extra_in = []
    if name_card:
        # the card sits still while the picture moves underneath it
        hold = min(NAME_CARD_SECONDS, max(dur - 0.6, 1.0))
        extra_in = ["-i", str(name_card)]
        vf = (f"{base}[bg];"
              f"[2:v]format=rgba,fade=t=in:st=0.35:d=0.3:alpha=1,"
              f"fade=t=out:st={hold:.2f}:d=0.4:alpha=1[nc];"
              f"[bg][nc]overlay=0:0:enable='lt(t,{hold + 0.5:.2f})'[v]")
    else:
        vf = f"{base}[v]"
    # A single (non-looped) image frame: zoompan expands it into `frames` output frames.
    run(["ffmpeg", "-y", "-i", str(image), *ain, *extra_in,
         "-filter_complex", f"{vf};{afilter}", "-map", "[v]", "-map", "[a]",
         "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])


def diagram_clip(name, audio, dur, out):
    """Explainers are HTML/CSS motion graphics rendered by headless Chromium."""
    ain, afilter = audio_inputs(audio, dur)
    silent_video = out.with_suffix(".video.mp4")
    body, css = diagrams.DIAGRAMS[name](dur)
    web.render_markup(body, dur, silent_video, css)
    vf = f"[0:v]fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE}:d={FADE},format=yuv420p[v]"
    run(["ffmpeg", "-y", "-i", str(silent_video), *ain, "-filter_complex", f"{vf};{afilter}",
         "-map", "[v]", "-map", "[a]", "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])
    silent_video.unlink()


def hero_clip(source, audio, dur, out, name_card=None):
    """Use a generated video clip as the picture, looped/slowed to fill the scene."""
    ain, afilter = audio_inputs(audio, dur)
    clip_len = duration(source)
    # slow slightly rather than loop when it is close, which reads as deliberate
    speed = max(0.5, min(1.0, clip_len / dur)) if clip_len < dur else 1.0
    vf = (f"[0:v]setpts=PTS/{speed:.4f},scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps={FPS},"
          f"fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE}:d={FADE},format=yuv420p")
    extra = []
    if name_card:
        hold = min(NAME_CARD_SECONDS, max(dur - 0.6, 1.0))
        extra = ["-i", str(name_card)]
        vf += (f"[bg];[2:v]format=rgba,fade=t=in:st=0.35:d=0.3:alpha=1,"
               f"fade=t=out:st={hold:.2f}:d=0.4:alpha=1[nc];"
               f"[bg][nc]overlay=0:0:enable='lt(t,{hold + 0.5:.2f})'[v]")
    else:
        vf += "[v]"
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(source), *ain, *extra,
         "-filter_complex", f"{vf};{afilter}", "-map", "[v]", "-map", "[a]",
         "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])


def multi_shot_clip(images, audio, dur, scene, out, name_card, clip_dir, sid):
    """Cut a scene into several shots so the picture changes every few seconds.

    One long slow zoom is what made the first cut feel like a slideshow. Here the
    narration stays continuous while the picture hard-cuts underneath it, which is
    the standard retention edit (research findings 18-19).
    """
    plan = shot_plan(dur, len(images))
    if len(plan) == 1:
        still_clip(images[0], audio, dur, scene.get("motion", "in"), out, name_card)
        return
    parts = []
    for i, (img_i, seconds, motion) in enumerate(plan):
        part = clip_dir / f"{sid}_shot{i}.mp4"
        frames = int(seconds * FPS)
        vf = (f"[0:v]{motion_filter(motion or 'in', frames)},format=yuv420p"
              # only the first and last shot get a fade; the rest hard-cut
              + (f",fade=t=in:st=0:d={FADE}" if i == 0 else "")
              + (f",fade=t=out:st={seconds - FADE}:d={FADE}" if i == len(plan) - 1 else "")
              + "[v]")
        run(["ffmpeg", "-y", "-i", str(images[img_i % len(images)]),
             "-f", "lavfi", "-t", f"{seconds}", "-i", "anullsrc=r=44100:cl=stereo",
             "-filter_complex", f"{vf};[1:a]anull[a]", "-map", "[v]", "-map", "[a]",
             "-t", f"{seconds}", *VIDEO_ARGS, *AUDIO_ARGS, str(part)])
        parts.append(part)
    silent = clip_dir / f"{sid}_shots.mp4"
    concat(parts, silent)
    # lay the continuous narration (and any name card) over the cut sequence
    ain, afilter = audio_inputs(audio, dur)
    extra, vf = [], "[0:v]null[v]"
    if name_card:
        hold = min(NAME_CARD_SECONDS, max(dur - 0.6, 1.0))
        extra = ["-i", str(name_card)]
        vf = (f"[2:v]format=rgba,fade=t=in:st=0.35:d=0.3:alpha=1,"
              f"fade=t=out:st={hold:.2f}:d=0.4:alpha=1[nc];"
              f"[0:v][nc]overlay=0:0:enable='lt(t,{hold + 0.5:.2f})'[v]")
    run(["ffmpeg", "-y", "-i", str(silent), *ain, *extra,
         "-filter_complex", f"{vf};{afilter}", "-map", "[v]", "-map", "[a]",
         "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])
    for p in parts:
        p.unlink(missing_ok=True)
    silent.unlink(missing_ok=True)


def build_clips(ep_id, allow_placeholders=False):
    ep = load_episode(ep_id)
    base = episode_dir(ep_id)
    clip_dir = base / "build" / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    timeline = []
    for scene in ep["scenes"]:
        sid = scene["id"]
        audio, dur = scene_timing(ep_id, scene)
        if scene.get("narration") and not audio and not allow_placeholders:
            raise SystemExit(f"Missing narration for {sid}. Run the 'voice' stage first.")
        out = clip_dir / f"{sid}.mp4"
        kind = scene["type"]
        if kind == "diagram":
            diagram_clip(scene["diagram"], audio, dur, out)
        else:
            if kind == "card":
                images = [clip_dir / f"{sid}_card.jpg"]
                card_image(images[0], scene)
            else:
                images = scene_images(base, sid)
                if not images:
                    if not allow_placeholders:
                        raise SystemExit(f"Missing image for {sid}. Run the 'images' stage first.")
                    ph = clip_dir / f"{sid}_placeholder.jpg"
                    placeholder(ph, sid,
                                scene.get("prompt") or scene.get("fallback_prompt") or "")
                    images = [ph]
            card = None
            if scene.get("name"):
                card = clip_dir / f"{sid}_name.png"
                name_card_overlay(card, scene["name"], scene.get("role", ""))
            hero = base / "video" / f"{sid}.mp4"
            if kind == "card":
                still_clip(images[0], audio, dur, scene.get("motion", "in"), out, card)
            elif scene.get("hero_video") and hero.exists():
                hero_clip(hero, audio, dur, out, card)
            else:
                multi_shot_clip(images, audio, dur, scene, out, card, clip_dir, sid)
        spoken = (duration(audio) if audio else 0)
        timeline.append((scene, out, dur, spoken))
        print(f"clip {sid}: {dur:.1f}s")
    return timeline


# ---------- assembly ----------

def concat(clips, out):
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out)])
    listing.unlink()


def add_music_and_master(video, out):
    music = sorted((ROOT / "assets" / "music").glob("*.mp3"))
    total = duration(video)
    if music:
        fc = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total},volume=0.12,"
              f"afade=t=out:st={total - 4}:d=4[m];[0:a][m]amix=inputs=2:duration=first:"
              f"dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        run(["ffmpeg", "-y", "-i", str(video), "-i", str(music[0]), "-filter_complex", fc,
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", *AUDIO_ARGS, str(out)])
    else:
        run(["ffmpeg", "-y", "-i", str(video), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
             "-c:v", "copy", *AUDIO_ARGS, str(out)])


def ffmpeg_escape(path):
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def drawtext_escape(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def hook_filters(hook, size=60, max_width=940, top=200):
    """The opening hook as wrapped lines, shown for the first 3.5 seconds of a vertical cut."""
    font = S.font(size, display=True)
    lines, current = [], ""
    for word in hook.split():
        trial = f"{current} {word}".strip()
        if font.getlength(trial) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    step = int(size * 1.5)
    return ",".join(
        f"drawtext=fontfile={S.DISPLAY}:text='{drawtext_escape(line)}':fontsize={size}:"
        f"fontcolor=white:box=1:boxcolor=0x11161F@0.92:boxborderw=20:"
        f"x=(w-text_w)/2:y={top + i * step}:enable='lt(t,3.5)'"
        for i, line in enumerate(lines))


def render(ep_id, allow_placeholders=False):
    ep = load_episode(ep_id)
    base = episode_dir(ep_id)
    out_dir = base / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    build = base / "build"
    timeline = build_clips(ep_id, allow_placeholders)

    # Long-form
    raw = build / "long_raw.mp4"
    concat([c for _, c, _, _ in timeline], raw)
    long_out = out_dir / f"{ep_id}_long.mp4"
    add_music_and_master(raw, long_out)
    t, rows = 0.0, []
    for scene, _, dur, spoken in timeline:
        rows.append((scene, t, spoken))
        t += dur
    (out_dir / f"{ep_id}_long.srt").write_text(captions_for(rows))
    print(f"long-form: {long_out} ({t / 60:.1f} min)")

    # Vertical cuts
    by_id = {scene["id"]: (scene, clip, dur, spoken) for scene, clip, dur, spoken in timeline}
    for cut in ep.get("cuts", []):
        items = [by_id[s] for s in cut["scenes"]]
        cut_raw = build / f"cut_{cut['id']}_raw.mp4"
        concat([clip for _, clip, _, _ in items], cut_raw)
        t, rows = 0.0, []
        for scene, _, dur, spoken in items:
            rows.append((scene, t, spoken))
            t += dur
        srt = build / f"cut_{cut['id']}.srt"
        srt.write_text(captions_for(rows))
        end_start = max(t - 3, 0)
        # libass lays out in its own 288px-tall space unless the file says otherwise,
        # so sizes here are multiplied by 1920/288 on screen: FontSize 11 -> ~73px,
        # MarginV 34 -> ~227px up from the bottom, which lands in the lower band.
        style = ("FontName=Inter SemiBold,FontSize=11,Bold=1,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,"
                 "Alignment=2,MarginV=34")
        # Letterbox rather than crop: a centre crop cut the sides off every diagram.
        # A mild 1.18x zoom first trims 5% from each side — inside the 110px safe margin
        # every diagram is drawn with — so the picture fills more of a phone screen.
        # The bands top and bottom are where the hook and the captions live.
        vf = (f"scale=1274:-2,crop=1080:in_h:(in_w-1080)/2:0,"
              f"pad=1080:1920:0:420:color=0x11161F,"
              f"subtitles='{ffmpeg_escape(srt)}':force_style='{style}',"
              f"{hook_filters(cut['hook'])},"
              f"drawtext=fontfile={S.UI_BOLD}:text='Full story on the channel':"
              f"fontsize=52:fontcolor=white:box=1:boxcolor=0xE8192C@0.95:boxborderw=24:"
              f"x=(w-text_w)/2:y=1300:enable='gte(t,{end_start:.2f})'")
        cut_out = out_dir / f"{ep_id}_vertical_{cut['id']}.mp4"
        run(["ffmpeg", "-y", "-i", str(cut_raw), "-vf", vf,
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", *VIDEO_ARGS, *AUDIO_ARGS, str(cut_out)])
        print(f"vertical cut: {cut_out} ({t:.0f}s)")
    shutil.rmtree(build / "clips", ignore_errors=True)
