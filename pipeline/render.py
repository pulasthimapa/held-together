"""Stage 4: assemble the long-form video and the vertical cuts with ffmpeg."""
import re
import shutil
import subprocess

from PIL import Image, ImageDraw

import diagrams
from common import (FONT_SANS_BOLD, FONT_SERIF, FONT_SERIF_BOLD, FPS, H, ROOT, W, clean,
                    duration, episode_dir, load_episode, run)

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
    from PIL import ImageFont
    im = Image.new("RGB", (W, H), (10, 10, 10))
    d = ImageDraw.Draw(im)
    if scene.get("title"):
        d.text((W // 2, H // 2 - 30), scene["title"], font=ImageFont.truetype(FONT_SERIF_BOLD, 76),
               fill=(236, 227, 208), anchor="mm")
    if scene.get("subtitle"):
        d.text((W // 2, H // 2 + 60), scene["subtitle"], font=ImageFont.truetype(FONT_SERIF, 34),
               fill=(170, 160, 145), anchor="mm")
    im.save(path, quality=95)


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


def still_clip(image, audio, dur, motion, out):
    frames = int(dur * FPS)
    ain, afilter = audio_inputs(audio, dur)
    vf = (f"[0:v]{motion_filter(motion, frames)},"
          f"fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE}:d={FADE},format=yuv420p[v]")
    # A single (non-looped) image frame: zoompan expands it into `frames` output frames.
    run(["ffmpeg", "-y", "-i", str(image), *ain,
         "-filter_complex", f"{vf};{afilter}", "-map", "[v]", "-map", "[a]",
         "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])


def diagram_clip(name, audio, dur, out):
    frames = int(dur * FPS)
    ain, afilter = audio_inputs(audio, dur)
    silent_video = out.with_suffix(".video.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", *VIDEO_ARGS, str(silent_video)],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    draw = diagrams.DIAGRAMS[name]
    for i in range(frames):
        proc.stdin.write(draw(i / max(frames - 1, 1)).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"diagram render failed: {name}")
    vf = f"[0:v]fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE}:d={FADE},format=yuv420p[v]"
    run(["ffmpeg", "-y", "-i", str(silent_video), *ain, "-filter_complex", f"{vf};{afilter}",
         "-map", "[v]", "-map", "[a]", "-t", str(dur), *VIDEO_ARGS, *AUDIO_ARGS, str(out)])
    silent_video.unlink()


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
                image = clip_dir / f"{sid}_card.jpg"
                card_image(image, scene)
            else:
                image = base / "archival" / f"{sid}.jpg"
                if not image.exists():
                    image = base / "images" / f"{sid}.jpg"
                if not image.exists():
                    if not allow_placeholders:
                        raise SystemExit(f"Missing image for {sid}. Run the 'images' stage first.")
                    image = clip_dir / f"{sid}_placeholder.jpg"
                    placeholder(image, sid)
            still_clip(image, audio, dur, scene.get("motion", "in"), out)
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


def hook_filters(hook, size=62, max_width=900, top=220):
    """The opening hook as wrapped lines, shown for the first 3.5 seconds of a vertical cut."""
    from PIL import ImageFont
    font = ImageFont.truetype(FONT_SANS_BOLD, size)
    lines, current = [], ""
    for word in hook.split():
        trial = f"{current} {word}".strip()
        if font.getlength(trial) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    step = int(size * 1.55)
    return ",".join(
        f"drawtext=fontfile={FONT_SANS_BOLD}:text='{drawtext_escape(line)}':fontsize={size}:"
        f"fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=22:"
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
        style = ("FontName=DejaVu Sans,FontSize=11,Bold=1,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,"
                 "Alignment=2,MarginV=70")
        vf = (f"crop=608:1080:(iw-608)/2:0,scale=1080:1920,"
              f"subtitles='{ffmpeg_escape(srt)}':force_style='{style}',"
              f"{hook_filters(cut['hook'])},"
              f"drawtext=fontfile={FONT_SANS_BOLD}:text='Full story on the channel':"
              f"fontsize=56:fontcolor=white:box=1:boxcolor=0x9C3D24@0.9:boxborderw=24:"
              f"x=(w-text_w)/2:y=260:enable='gte(t,{end_start:.2f})'")
        cut_out = out_dir / f"{ep_id}_vertical_{cut['id']}.mp4"
        run(["ffmpeg", "-y", "-i", str(cut_raw), "-vf", vf,
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", *VIDEO_ARGS, *AUDIO_ARGS, str(cut_out)])
        print(f"vertical cut: {cut_out} ({t:.0f}s)")
    shutil.rmtree(build / "clips", ignore_errors=True)
