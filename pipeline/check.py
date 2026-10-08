"""Guards. Every stage runs `preflight` before it can spend money and `verify` after.

preflight  - the episode, cast, fact sheet and secrets are all valid for this stage, and the
             stage's inputs exist. Prints what the stage is about to generate (rule 14).
verify     - what the stage produced is actually right. Bad paid output is deleted so the
             next run redoes it instead of silently building on it.

Every problem is collected and reported together, so one failed run shows everything that
needs fixing, not just the first thing.
"""
import os
import re
import subprocess

from PIL import Image

from common import (SHEETS_DIR, clean, duration, episode_dir, load_cast, load_episode)

HOSTS = ("elias", "maya")
SCENE_TYPES = {"image", "diagram", "archival", "card"}
MIN_LONG_SECONDS = 8 * 60          # YouTube mid-rolls need 8:00 (support.google.com/youtube/answer/6175006)
MIN_CUT_SECONDS = 61               # TikTok rewards floor (rule 9)
HOST_PITCH_GAP_HZ = 40             # Maya's median pitch must sit this far above Elias's

# Words that would pull a scene into the wrong visual world (docs/brand.md).
BANNED = {
    "host": [r"\b3d\b", r"pixar", r"cartoon", r"animated", r"animation", r"illustrat",
             r"painting", r"painted", r"\bbob\b", r"\bstand", r"leaning (forward|across)",
             r"low angle", r"high angle", r"handheld", r"looks? (in|at) the camera",
             r"\bstranger", r"\bguest"],
    "story": [r"photoreal", r"photograph", r"\b3d\b", r"pixar", r"cartoon", r"\bcgi\b"],
}


class Problems(list):
    def add(self, msg):
        self.append(msg)

    def stop_if_any(self, heading):
        if self:
            lines = "\n".join(f"  - {p}" for p in self)
            raise SystemExit(f"{heading} ({len(self)} problem(s)):\n{lines}")


def _world(cast, scene):
    from images import world_of
    return world_of(cast, scene)


def _expected_images(ep):
    """{scene_id: [file stems]} for every picture the images stage should produce."""
    out = {}
    for s in ep["scenes"]:
        if s["type"] == "image":
            n = 1 + len(s.get("shots", []))
            out[s["id"]] = [s["id"] + ("" if i == 0 else "bcd"[i - 1]) for i in range(n)]
        elif s["type"] == "archival":
            out[s["id"]] = [s["id"]]
    return out


# ------------------------------------------------------------------ preflight

def check_cast(cast, p):
    for h in HOSTS:
        a = cast["actors"].get(h)
        if not a:
            p.add(f"cast: host '{h}' is missing")
            continue
        for key in ("world", "description", "persona", "speech", "wardrobe"):
            if not a.get(key):
                p.add(f"cast: {h} has no '{key}'")
        if a.get("world") != "host":
            p.add(f"cast: {h} must be world: host")
    st = cast.get("studio") or {}
    for key in ("description", "plate_prompt", "sheet"):
        if not st.get(key):
            p.add(f"cast: studio has no '{key}'")
    for key in ("style_host", "style_story", "sheet_prompt_host", "sheet_prompt_story"):
        if not cast.get(key):
            p.add(f"cast: '{key}' is missing")


def check_episode(cast, ep, p):
    import diagrams
    import video
    from images import MAX_REFS

    ids = [s.get("id") for s in ep["scenes"]]
    seen = set()
    for i in ids:
        if i in seen:
            p.add(f"episode: duplicate scene id {i}")
        seen.add(i)
    hero = 0
    first_elias = None
    for s in ep["scenes"]:
        sid, kind = s.get("id"), s.get("type")
        if kind not in SCENE_TYPES:
            p.add(f"{sid}: unknown type '{kind}'")
            continue
        if kind == "image" and not s.get("prompt"):
            p.add(f"{sid}: image scene has no prompt")
        if kind == "archival" and not s.get("fallback_prompt"):
            p.add(f"{sid}: archival scene has no fallback_prompt")
        if kind == "diagram" and s.get("diagram") not in diagrams.DIAGRAMS:
            p.add(f"{sid}: diagram '{s.get('diagram')}' does not exist")
        if s.get("narration") and s.get("speaker", "elias") not in HOSTS:
            p.add(f"{sid}: speaker '{s.get('speaker')}' is not a host")
        for a in s.get("actors", []):
            if a not in cast["actors"]:
                p.add(f"{sid}: actor '{a}' is not in cast.yaml")
        if p and any(m.startswith(f"{sid}: actor") for m in p):
            continue
        world = _world(cast, s)
        if world == "host":
            cams = cast["studio"].get("cameras", {})
            if s.get("camera") not in cams:
                p.add(f"{sid}: studio scene needs camera: one of {', '.join(cams)}")
            for a in s.get("actors", []):
                if a not in HOSTS:
                    p.add(f"{sid}: '{a}' cannot appear in the studio; only Elias and Maya")
            refs = 1 if s.get("camera") == "insert" else len(HOSTS) + 1
        else:
            refs = len(s.get("actors", []))
        if kind in ("image", "archival") and refs > MAX_REFS:
            p.add(f"{sid}: {refs} reference images, limit {MAX_REFS}")
        if s.get("host_shot") and world != "host":
            p.add(f"{sid}: host_shot scene is not in the studio world")
        if world == "story":
            for a in s.get("actors", []):
                if cast["actors"][a].get("world") == "host":
                    p.add(f"{sid}: host '{a}' placed in a painted story scene")
        texts = [s.get("prompt", ""), s.get("fallback_prompt", ""), s.get("hero_video", "")]
        texts += list(s.get("shots", []))
        for t in texts:
            for pat in BANNED[world]:
                if re.search(pat, (t or "").lower()):
                    word = re.sub(r"\\b", "", pat)
                    p.add(f"{sid}: prompt says '{word}' but this is a {world} scene "
                          f"(docs/brand.md)")
        if s.get("hero_video"):
            hero += 1
            if float(s.get("hero_seconds", 6)) > video.MAX_SECONDS:
                p.add(f"{sid}: hero_seconds over {video.MAX_SECONDS}")
            if kind != "image":
                p.add(f"{sid}: hero_video needs an image scene to seed from")
        if "elias" in s.get("actors", []) and first_elias is None:
            first_elias = s
    for host, look in (ep.get("wardrobe") or {}).items():
        if host not in HOSTS:
            p.add(f"episode wardrobe: '{host}' is not a host (the troupe is costumed per scene)")
        elif cast["actors"][host]["name"] not in str(look):
            p.add(f"episode wardrobe: the {host} line must name {cast['actors'][host]['name']}")
    if hero > video.MAX_CLIPS:
        p.add(f"episode: {hero} hero clips, limit {video.MAX_CLIPS}")
    # F2: Elias is labelled as a composite character the first time he is seen.
    if first_elias is None:
        p.add("episode: Elias never appears on screen (F1)")
    elif "composite" not in (first_elias.get("role") or "").lower():
        p.add(f"{first_elias['id']}: Elias's first appearance needs role '... composite "
              f"character' (F2)")
    if not any("maya" in s.get("actors", []) for s in ep["scenes"]):
        p.add("episode: Maya never appears on screen (F1)")
    # 5c: end on an open question.
    spoken = [s for s in ep["scenes"] if s.get("narration")]
    if spoken and "?" not in spoken[-1]["narration"]:
        p.add(f"{spoken[-1]['id']}: the last line must ask viewers a question (rule 5c)")
    for cut in ep.get("cuts", []):
        for sid in cut.get("scenes", []):
            if sid not in seen:
                p.add(f"cut {cut.get('id')}: scene {sid} does not exist")
        if not cut.get("hook"):
            p.add(f"cut {cut.get('id')}: no hook text")


def check_factsheet(ep_id, ep, p):
    import yaml
    path = episode_dir(ep_id) / "factsheet.yaml"
    if not path.exists():
        p.add(f"no fact sheet at {path.relative_to(path.parents[2])} (rule 1)")
        return
    fs = yaml.safe_load(path.read_text())
    sources = fs.get("sources", {})
    for key, src in sources.items():
        if not str(src.get("url", "")).startswith("https://"):
            p.add(f"fact sheet: source {key} has no https URL")
    entries = fs.get("scenes", {})
    for s in ep["scenes"]:
        if not s.get("narration"):
            continue
        e = entries.get(s["id"])
        if not e:
            p.add(f"{s['id']}: narrated but not in the fact sheet (rule 1)")
            continue
        if e.get("kind") not in ("fact", "explanation", "opinion"):
            p.add(f"{s['id']}: fact sheet kind must be fact / explanation / opinion")
        if e.get("kind") == "fact":
            claims = e.get("claims") or []
            if not claims:
                p.add(f"{s['id']}: kind fact but no claims listed")
            for c in claims:
                if not c.get("s"):
                    p.add(f"{s['id']}: claim '{c.get('c')}' has no source")
                for k in c.get("s", []):
                    if k != "computed" and k not in sources:
                        p.add(f"{s['id']}: source '{k}' is not defined in the fact sheet")
    for sid in entries:
        if sid not in {s["id"] for s in ep["scenes"]}:
            p.add(f"fact sheet: {sid} is not a scene in the episode")


def check_secrets(stage, p):
    need = {"cast": ["GEMINI_API_KEY"], "images": ["GEMINI_API_KEY"],
            "video": ["GEMINI_API_KEY"],
            "voice": ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ELIAS", "ELEVENLABS_VOICE_MAYA"]}
    for name in need.get(stage, []):
        if not os.environ.get(name, "").strip():
            p.add(f"secret {name} is missing or not passed to the workflow")
    if stage == "voice":
        e, m = (os.environ.get("ELEVENLABS_VOICE_ELIAS", "").strip(),
                os.environ.get("ELEVENLABS_VOICE_MAYA", "").strip())
        if e and m and e == m:
            p.add("ELEVENLABS_VOICE_ELIAS and ELEVENLABS_VOICE_MAYA are the same voice")


def check_inputs(stage, cast, ep_id, ep, p):
    """The things a stage builds on must already exist."""
    base = episode_dir(ep_id)
    if stage == "images":
        for a in {a for s in ep["scenes"] for a in s.get("actors", [])}:
            if not (SHEETS_DIR / f"{a}.jpg").exists():
                p.add(f"cast sheet {a}.jpg missing: run 'cast' first")
        if not (SHEETS_DIR / f"{cast['studio']['sheet']}.jpg").exists():
            p.add("studio plate missing: run 'cast' first")
    if stage == "video":
        for s in ep["scenes"]:
            if s.get("hero_video") and not (base / "images" / f"{s['id']}.jpg").exists():
                p.add(f"{s['id']}: no still to seed the clip from: run 'images' first "
                      f"(an unseeded clip invents faces)")
    if stage == "render":
        for sid, stems in _expected_images(ep).items():
            kind = next(s["type"] for s in ep["scenes"] if s["id"] == sid)
            if kind == "archival" and (base / "archival" / f"{sid}.jpg").exists():
                continue
            if not (base / "images" / f"{stems[0]}.jpg").exists():
                p.add(f"{sid}: image missing: run 'images'")
        for s in ep["scenes"]:
            if s.get("narration") and not (base / "audio" / f"{s['id']}.mp3").exists():
                p.add(f"{s['id']}: narration audio missing: run 'voice'")


def plan(stage, cast, ep_id, ep):
    """What the stage will pay for this run (rule 14)."""
    base = episode_dir(ep_id)
    if stage == "cast":
        n = sum(1 for a in cast["actors"] if not (SHEETS_DIR / f"{a}.jpg").exists())
        n += 0 if (SHEETS_DIR / f"{cast['studio']['sheet']}.jpg").exists() else 1
        return f"cast: {n} image(s) to generate"
    if stage == "images":
        missing = [st for stems in _expected_images(ep).values() for st in stems
                   if not (base / "images" / f"{st}.jpg").exists()]
        return (f"images: {len(missing)} to generate: {', '.join(missing) or 'none'} "
                f"(studio pictures are checked and may be redrawn up to 3 times)")
    if stage == "video":
        todo = [(s["id"], min(float(s.get("hero_seconds", 6)), 8)) for s in ep["scenes"]
                if s.get("hero_video") and not (base / "video" / f"{s['id']}.mp4").exists()]
        secs = sum(t for _, t in todo)
        return (f"video: {len(todo)} clip(s), {secs:.0f} s to generate: "
                f"{', '.join(i for i, _ in todo) or 'none'} (a studio clip that fails the "
                f"picture check is redrawn once)")
    if stage == "voice":
        todo = [s for s in ep["scenes"] if s.get("narration")
                and not (base / "audio" / f"{s['id']}.mp3").exists()]
        chars = sum(len(clean(s["narration"])) for s in todo)
        return f"voice: {len(todo)} line(s), {chars} characters to generate"
    return f"{stage}: no paid calls"


# Measured on ep01's first voicing: 7,711 characters made 430 s of speech.
SECONDS_PER_CHAR = 430 / 7711


def estimate_lengths(ep_id, ep):
    """Episode and cut lengths, using real audio where it exists and an estimate elsewhere."""
    import diagrams
    import render
    times = {}
    for s in ep["scenes"]:
        audio = episode_dir(ep_id) / "audio" / f"{s['id']}.mp3"
        if s.get("narration") and not audio.exists():
            dur = len(clean(s["narration"])) * SECONDS_PER_CHAR + render.TAIL
            dur += float(s.get("hold_after", 0))
            if s["type"] == "diagram":
                dur = max(dur, diagrams.MIN_SECONDS.get(s["diagram"], 0))
        else:
            dur = render.scene_timing(ep_id, s)[1]
        times[s["id"]] = dur
    cuts = {c["id"]: sum(times[i] for i in c["scenes"]) for c in ep.get("cuts", [])}
    return sum(times.values()), cuts


def check_lengths(ep_id, ep, p, margin=1.05):
    """Refuse to pay for narration that would make an episode too short to monetise."""
    total, cuts = estimate_lengths(ep_id, ep)
    print(f"estimated length: {int(total // 60)}:{int(total % 60):02d}; cuts: "
          + ", ".join(f"{k} {v:.0f}s" for k, v in cuts.items()))
    if total < MIN_LONG_SECONDS * margin:
        p.add(f"estimated episode length {total:.0f} s is too close to 8:00; lengthen the "
              f"script before voicing")
    for k, v in cuts.items():
        if v < MIN_CUT_SECONDS * margin:
            p.add(f"cut {k}: estimated {v:.0f} s, too close to {MIN_CUT_SECONDS} s; add a scene")



def preflight(stage, ep_id, inputs=True):
    cast, ep = load_cast(), load_episode(ep_id)
    p = Problems()
    check_cast(cast, p)
    p.stop_if_any("Cast file is not valid")
    check_episode(cast, ep, p)
    check_factsheet(ep_id, ep, p)
    if stage in ("check", "voice"):
        check_lengths(ep_id, ep, p)
    if stage != "check":
        check_secrets(stage, p)
        if inputs:
            check_inputs(stage, cast, ep_id, ep, p)
    p.stop_if_any(f"Preflight failed for '{stage}', nothing was spent")
    stages = ["cast", "images", "video", "voice"] if stage == "check" else [stage]
    for st in stages:
        print("plan:", plan(st, cast, ep_id, ep))
    print(f"preflight ok: {stage} {ep_id}")


# ------------------------------------------------------------------ verify

def _image_ok(path):
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            w, h = im.size
        return 1.6 <= w / h <= 1.95, f"{w}x{h}"
    except Exception as exc:  # noqa: BLE001 — any unreadable file is a failure
        return False, str(exc)


def median_pitch(path):
    """Median voiced pitch in Hz (autocorrelation). Good enough to tell two voices apart."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float)
    fs, n, found = 16000, 640, []
    for i in range(0, len(x) - n, n):
        w = x[i:i + n]
        if np.sqrt((w ** 2).mean()) < 800:
            continue
        w = w - w.mean()
        ac = np.correlate(w, w, "full")[n - 1:]
        lo, hi = fs // 400, fs // 60
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.4 * ac[0]:
            found.append(fs / k)
    return float(np.median(found)) if found else 0.0


def verify(stage, ep_id):
    cast, ep = load_cast(), load_episode(ep_id)
    base = episode_dir(ep_id)
    p = Problems()
    if stage == "cast":
        for name in list(cast["actors"]) + [cast["studio"]["sheet"]]:
            f = SHEETS_DIR / f"{name}.jpg"
            ok, info = _image_ok(f) if f.exists() else (False, "missing")
            if not ok:
                p.add(f"cast sheet {f.name}: {info}")
    if stage == "images":
        for stems in _expected_images(ep).values():
            for st in stems:
                f = base / "images" / f"{st}.jpg"
                if not f.exists():
                    if (base / "archival" / f"{st}.jpg").exists():
                        continue
                    p.add(f"{f.name} missing")
                    continue
                ok, info = _image_ok(f)
                if not ok:
                    f.unlink()
                    p.add(f"{f.name} was not a valid 16:9 image ({info}); deleted so it is redrawn")
    if stage == "video":
        for s in ep["scenes"]:
            if not s.get("hero_video"):
                continue
            f = base / "video" / f"{s['id']}.mp4"
            if not f.exists():
                p.add(f"{f.name} missing")
            elif duration(f) < 3:
                f.unlink()
                p.add(f"{f.name} shorter than 3 s; deleted")
        _clip_review(ep, base)
    if stage == "voice":
        pitch = {h: [] for h in HOSTS}
        for s in ep["scenes"]:
            if not s.get("narration"):
                continue
            f = base / "audio" / f"{s['id']}.mp3"
            if not f.exists():
                p.add(f"{f.name} missing")
                continue
            if len(pitch[s.get("speaker", "elias")]) < 4:
                pitch[s.get("speaker", "elias")].append(median_pitch(f))
        if all(pitch.values()):
            e = sorted(pitch["elias"])[len(pitch["elias"]) // 2]
            m = sorted(pitch["maya"])[len(pitch["maya"]) // 2]
            print(f"voice pitch: elias ~{e:.0f} Hz, maya ~{m:.0f} Hz")
            if m - e < HOST_PITCH_GAP_HZ:
                for f in (base / "audio").glob("*.mp3"):
                    f.unlink()
                p.add(f"Maya ({m:.0f} Hz) does not sound distinct from Elias ({e:.0f} Hz). "
                      f"Check ELEVENLABS_VOICE_MAYA is a female voice. All audio deleted so "
                      f"the next run re-voices it.")
    if stage == "render":
        out = base / "output"
        long_f = out / f"{ep_id}_long.mp4"
        if not long_f.exists():
            p.add("long video missing")
        else:
            d = duration(long_f)
            print(f"long video: {int(d // 60)}:{int(d % 60):02d}")
            if d < MIN_LONG_SECONDS:
                p.add(f"long video is {d:.0f} s, under 8:00: no mid-roll ads possible")
        for cut in ep.get("cuts", []):
            f = out / f"{ep_id}_vertical_{cut['id']}.mp4"
            if not f.exists():
                p.add(f"{f.name} missing")
            elif duration(f) < MIN_CUT_SECONDS:
                p.add(f"{f.name} is {duration(f):.0f} s, under {MIN_CUT_SECONDS} s (rule 9)")
    p.stop_if_any(f"Verification failed after '{stage}'")
    print(f"verified: {stage} {ep_id}")


def _clip_review(ep, base):
    """Frames at 1 s, middle and end of every hero clip, so a style drift is visible."""
    clips = [base / "video" / f"{s['id']}.mp4" for s in ep["scenes"] if s.get("hero_video")]
    clips = [c for c in clips if c.exists()]
    if not clips:
        return
    tw, th = 480, 270
    sheet = Image.new("RGB", (tw * 3, th * len(clips)), (20, 20, 20))
    tmp = base / "video" / "_frame.jpg"
    for r, clip in enumerate(clips):
        d = duration(clip)
        for c, t in enumerate((1.0, d / 2, max(d - 0.5, 0))):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(clip),
                            "-frames:v", "1", "-vf", f"scale={tw}:{th}", str(tmp)], check=True)
            with Image.open(tmp) as im:
                sheet.paste(im.convert("RGB"), (c * tw, r * th))
    tmp.unlink(missing_ok=True)
    sheet.save(base / "clips_review.jpg", quality=85)
    print(f"review sheet: {base / 'clips_review.jpg'}")


# ------------------------------------------------------------------ description

def write_description(ep_id, out_path):
    """The YouTube description: disclosure, sources and every noted disagreement (rules 1, 10)."""
    import yaml
    ep = load_episode(ep_id)
    fs = yaml.safe_load((episode_dir(ep_id) / "factsheet.yaml").read_text())
    lines = [ep["title"], "",
             "A true story. Our hosts, Elias and Maya, are fictional characters: Elias is a "
             "composite of the engineers of his era, and Maya speaks for engineering today. "
             "Everyone in the story is real. Both voices and all images are AI-generated "
             "from our own scripts and research.", "",
             "Where the sources disagree:"]
    lines += [f"- {d}" for d in fs.get("disagreements", [])]
    lines += ["", "Sources:"]
    lines += [f"- {s['title']}: {s['url']}" for s in fs["sources"].values()]
    out_path.write_text("\n".join(lines) + "\n")
    print(f"description: {out_path}")
