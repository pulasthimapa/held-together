"""Stage 1 and 2: cast reference sheets and studio masters, then every scene picture.

Existing files are never regenerated, so re-running only fills gaps.
Delete a single image file to have it redrawn on the next run.

HOW STUDIO PICTURES ARE MADE (the expensive lesson of ep01)
Drawing every studio shot from scratch gave the image model a free hand with the camera,
the seating, the microphones and the empty chair, and it used it: strangers in the other
seat, wrong clothes, hosts at different scales. So the studio is drawn once:

  cast stage   ->  studio plate (the empty room), then one MASTER frame per camera with
                   the hosts seated in it. Each master is checked and approved by eye.
  images stage ->  every studio scene is an EDIT of its camera's master. Only the
                   expression, hands and any prop change; everything else is copied.

An edit has almost nothing left to get wrong, which is what keeps re-draws near zero.
"""
from PIL import Image, ImageDraw, ImageFont

import gemini
from common import (FONT_SANS_BOLD, ROOT, SHEETS_DIR, clean, episode_dir, load_cast,
                    load_episode)

HOSTS = ("elias", "maya")
MAX_REFS = 4          # the image model accepts at most four reference images per request
STUDIO_ATTEMPTS = 2   # a studio picture that fails the check is redrawn once, then reported


def world_of(cast, scene):
    """Which visual world a scene belongs to (docs/brand.md): photographed studio or
    painted past. A scene is in the studio if it names a camera, says world: host, or has a
    host in it; everything else is the past."""
    if scene.get("world") in ("host", "story"):
        return scene["world"]
    if scene.get("camera"):
        return "host"
    for actor_id in scene.get("actors", []):
        if cast["actors"].get(actor_id, {}).get("world") == "host":
            return "host"
    return "story"


def style_for(cast, world):
    return cast[f"style_{world}"]


def studio_sheet(cast):
    return SHEETS_DIR / f"{cast['studio']['sheet']}.jpg"


def master_path(cast, camera):
    return ROOT / "cast" / cast["studio"]["masters_dir"] / f"{camera}.jpg"


def used_cameras(cast):
    """Cameras that some episode actually uses. Masters are only drawn for these, so no
    money is spent on an angle nobody has asked for yet."""
    import yaml
    used = set()
    for f in sorted((ROOT / "episodes").glob("*/episode.yaml")):
        for s in (yaml.safe_load(f.read_text()) or {}).get("scenes", []):
            if s.get("camera"):
                used.add(s["camera"])
    return [c for c, v in cast["studio"]["cameras"].items() if v["in_frame"] and c in used]


def camera_of(cast, scene):
    camera = scene.get("camera")
    if camera not in cast["studio"]["cameras"]:
        raise SystemExit(f"{scene['id']}: studio scene needs camera: one of "
                         f"{', '.join(cast['studio']['cameras'])}")
    return camera


def _looks(cast, wardrobe=None):
    return {h: clean((wardrobe or {}).get(h) or cast["actors"][h]["wardrobe"]) for h in HOSTS}


# ------------------------------------------------------------------ prompts

def master_prompt(cast, camera):
    """The text for a camera's master frame: the room, the camera, who sits where."""
    st, cam = cast["studio"], cast["studio"]["cameras"][camera]
    looks = _looks(cast)
    people = cam["in_frame"]
    parts = [style_for(cast, "host"), clean(cam["master"]), clean(st["description"])]
    if people:
        if len(people) == 1:
            name = cast["actors"][people[0]]["name"]
            # A single says only who IS in it: naming the other host invites them in.
            parts.append(f"This frame shows {name} alone, seated naturally in the chair at "
                         f"the table, upright or leaning back slightly, speaking into the desk "
                         f"microphone with eyes across the table, the way people sit on a "
                         f"real filmed podcast. Face and hands at chest height carry the "
                         f"emotion.")
        else:
            parts += [clean(st["people"]), clean(st["posture"])]
        parts += [looks[h] for h in people]
        order = ", ".join(f"image {i + 1} is {cast['actors'][h]['name']}"
                          for i, h in enumerate(people))
        parts.append(f"Reference images: {order}; match each face, hair, glasses, skin and "
                     f"build exactly. The last reference image is the empty studio from the "
                     f"wide camera: it is the same room, seen here from this camera.")
    else:
        parts.append("The reference image is the empty studio from the wide camera: it is "
                     "the same room, seen here from this camera.")
    return clean(" ".join(parts))


def edit_prompt(cast, scene, prompt, wardrobe=None):
    """The text for a studio scene: an edit of the camera's approved master frame."""
    camera = camera_of(cast, scene)
    cam = cast["studio"]["cameras"][camera]
    names = [cast["actors"][h]["name"] for h in cam["in_frame"]]
    who = " and ".join(names) if names else "the table"
    keep = ("the camera position, lens, framing and crop; the lighting and colour grade; the "
            "room, shelves, table, lamp and desk microphones exactly where they are")
    if names:
        keep += (f"; and {who}'s faces, hair, glasses, build, seats, size in the frame and "
                 f"distance from the microphone" if len(names) > 1 else
                 f"; and {who}'s face, hair, glasses, build, seat, size in the frame and "
                 f"distance from the microphone")
    label = clean(cam["master"]).split(":")[0]
    parts = [f"Edit image 1, a frame from our podcast's {label}. "
             f"Keep everything in it exactly as it is: {keep}. "
             f"Change only what this moment needs: {clean(prompt)}"]
    if names:
        parts.append("Expression, head angle and hands may change; posture stays natural and "
                     "seated, as on a real filmed podcast. Everything else stays identical "
                     "to image 1.")
        recolour = [clean(v) for k, v in (wardrobe or {}).items() if k in cam["in_frame"]]
        if recolour:
            parts.append("Recolour the clothes as follows, keeping the garments: "
                         + " ".join(recolour))
        later = ", ".join(f"image {i + 2} is {n}" for i, n in enumerate(names))
        parts.append(f"The other reference images are for faces only ({later}); do not copy "
                     f"their background, clothes or pose.")
    else:
        parts.append("Add or change only the object described; the frame stays empty of people.")
    parts.append(clean(style_for(cast, "host")))
    return clean(" ".join(parts))


def story_prompt(cast, scene, prompt):
    parts = [style_for(cast, "story"), clean(prompt)]
    if scene.get("actors"):
        names = ", ".join(cast["actors"][a]["name"] for a in scene["actors"])
        parts.append(f"The reference images show {names}; keep each face, hair and build "
                     "exactly as in the references, only the costume and setting change.")
    return clean(" ".join(parts))


def build_prompt(cast, scene, prompt, wardrobe=None):
    if world_of(cast, scene) == "host":
        return edit_prompt(cast, scene, prompt, wardrobe)
    return story_prompt(cast, scene, prompt)


def refs_for(cast, scene):
    """Studio: the camera's master first (the picture being edited), then the faces in it.
    Story: the actors' painted sheets."""
    if world_of(cast, scene) == "host":
        camera = camera_of(cast, scene)
        master = master_path(cast, camera)
        if not master.exists():
            raise SystemExit(f"Missing studio master cast/studio/{camera}.jpg. Run 'cast'.")
        refs = [master] + [SHEETS_DIR / f"{h}.jpg"
                           for h in cast["studio"]["cameras"][camera]["in_frame"]]
    else:
        refs = [SHEETS_DIR / f"{a}.jpg" for a in scene.get("actors", [])]
    for r in refs:
        if not r.exists():
            raise SystemExit(f"Missing reference {r.name}. Run the 'cast' stage first.")
    if len(refs) > MAX_REFS:
        raise SystemExit(f"{scene['id']}: {len(refs)} reference images, limit is {MAX_REFS}.")
    return refs


# ------------------------------------------------------------------ the picture check

CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "people": {"type": "array", "items": {"type": "object", "properties": {
            "where": {"type": "string"},
            "who": {"type": "string", "enum": ["elias", "maya", "someone_else"]},
            "clothes_match": {"type": "boolean"}},
            "required": ["where", "who", "clothes_match"]}},
        "anyone_standing_or_leaning_across": {"type": "boolean"},
        "microphones_on_desk_stands": {"type": "boolean"},
        "summary": {"type": "string"}},
    "required": ["people", "anyone_standing_or_leaning_across",
                 "microphones_on_desk_stands", "summary"],
}


def check_studio_picture(cast, scene, picture, wardrobe=None):
    """Return a list of problems with one studio picture (empty means it passed).

    A vision model compares the picture with the hosts' reference sheets, their wardrobe and
    the camera's expected framing (CLAUDE.md F6, F8). Kept as the safety net behind the
    master-and-edit method, not as the way to get pictures right.
    """
    camera = scene.get("camera")
    expected = cast["studio"]["cameras"][camera]["in_frame"]
    looks = _looks(cast, wardrobe)
    if not expected:
        prompt = ("This is a close detail shot of a table. List every person visible, even "
                  "partly: a hand, a sleeve, a shoulder, a blurred figure. Microphones in this "
                  "studio stand on short desk stands on the table: say whether any visible "
                  "microphone is on a desk stand (true if none is visible).")
        refs = [picture]
    else:
        prompt = ("Image 1 is the reference for Elias. Image 2 is the reference for Maya. "
                  "Image 3 is a new picture from their podcast studio. List EVERY person "
                  "visible in image 3, even partly: a blurred foreground shoulder, the back of "
                  "a head, a hand at the edge. For each, judge by face, hair, build and skin "
                  "whether it is Elias, Maya, or someone_else; be strict, a different face or "
                  "hair is someone_else. Say whether their clothes match: "
                  f"{looks['elias']} {looks['maya']} Say whether anyone is standing or "
                  "leaning across the table, and whether every visible microphone stands on a "
                  "short desk stand on the table (not on a boom arm).")
        refs = [SHEETS_DIR / "elias.jpg", SHEETS_DIR / "maya.jpg", picture]
    answer = gemini.inspect(prompt, refs, CHECK_SCHEMA)
    people = answer.get("people", [])
    problems = []
    for person in people:
        if person["who"] == "someone_else":
            problems.append(f"unknown person ({person['where']})")
        elif person["who"] not in expected:
            problems.append(f"{person['who']} should not be in this camera ({person['where']})")
        elif not person["clothes_match"]:
            problems.append(f"{person['who']} in the wrong clothes ({person['where']})")
    seen = {p["who"] for p in people}
    for h in expected:
        if h not in seen:
            problems.append(f"{cast['actors'][h]['name']} missing from this camera")
    if answer.get("anyone_standing_or_leaning_across"):
        problems.append("someone standing or leaning across the table")
    if not answer.get("microphones_on_desk_stands", True):
        problems.append("microphone on a boom arm instead of a desk stand")
    return problems


def _generate_checked(prompt, refs, out, cast, scene, wardrobe=None, check=True):
    """Generate one picture; studio pictures must pass the check. Returns (ok, tries)."""
    tries = STUDIO_ATTEMPTS if check else 1
    for attempt in range(1, tries + 1):
        data = gemini.generate(prompt, refs=refs, aspect="16:9")
        if not check:
            out.write_bytes(data)
            return True, attempt
        trial = out.with_name(f"_{out.name}")
        trial.write_bytes(data)
        problems = check_studio_picture(cast, scene, trial, wardrobe)
        if not problems:
            trial.rename(out)
            return True, attempt
        # Keep the rejected picture (gitignored, uploaded with the review images) so a
        # rejection can be looked at instead of guessed at.
        trial.rename(out.with_name(f"_rejected_{out.stem}_{attempt}.jpg"))
        print(f"  {out.name} attempt {attempt} rejected: {'; '.join(problems)}")
    return False, tries


def _prove_checker(cast):
    gemini.inspect("Does this picture show a room? Answer with an empty people list.",
                   [studio_sheet(cast)], CHECK_SCHEMA)
    print(f"picture check ready ({gemini.INSPECT_MODEL})")


# ------------------------------------------------------------------ stages

def make_cast_sheets():
    cast = load_cast()
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    made, failed = [], []
    for actor_id, actor in cast["actors"].items():
        out = SHEETS_DIR / f"{actor_id}.jpg"
        if out.exists():
            continue
        world = actor.get("world", "story")
        prompt = style_for(cast, world) + " " + cast[f"sheet_prompt_{world}"].format(
            description=clean(actor["description"]))
        out.write_bytes(gemini.generate(clean(prompt), aspect="16:9"))
        made.append(out)
        print(f"cast sheet: {out.name} ({world})")
    plate = studio_sheet(cast)
    if not plate.exists():
        prompt = style_for(cast, "host") + " " + cast["studio"]["plate_prompt"].format(
            description=clean(cast["studio"]["description"]))
        plate.write_bytes(gemini.generate(clean(prompt), aspect="16:9"))
        made.append(plate)
        print("studio plate: studio.jpg")
    # One master per camera with people in it. The insert has no master: it is a close-up
    # of whatever object the scene needs, drawn from the plate.
    todo = [c for c in used_cameras(cast) if not master_path(cast, c).exists()]
    if todo:
        _prove_checker(cast)
        master_path(cast, todo[0]).parent.mkdir(parents=True, exist_ok=True)
    for camera in todo:
        out = master_path(cast, camera)
        refs = [SHEETS_DIR / f"{h}.jpg" for h in cast["studio"]["cameras"][camera]["in_frame"]]
        ok, _ = _generate_checked(master_prompt(cast, camera), refs + [plate], out, cast,
                                  {"id": f"master {camera}", "camera": camera})
        if ok:
            made.append(out)
            print(f"studio master: {camera}.jpg")
        else:
            failed.append(camera)
    review = sorted(SHEETS_DIR.glob("*.jpg")) + sorted(master_path(cast, "x").parent.glob("[!_]*.jpg"))
    contact_sheet(review, SHEETS_DIR.parent / "cast_review.jpg")
    if failed:
        raise SystemExit(f"Studio masters failed the picture check twice: {', '.join(failed)}")
    return made


def make_scene_images(ep_id):
    cast = load_cast()
    ep = load_episode(ep_id)
    img_dir = episode_dir(ep_id) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    archival_dir = episode_dir(ep_id) / "archival"
    wardrobe = ep.get("wardrobe")
    if any(s["type"] == "image" and world_of(cast, s) == "host"
           and not (img_dir / f"{s['id']}.jpg").exists() for s in ep["scenes"]):
        _prove_checker(cast)  # before paying for any studio picture
    total, failed = 0, []
    for scene in ep["scenes"]:
        kind = scene["type"]
        prompts = []
        if kind == "image":
            # `shots` holds extra angles of the same beat so the edit can cut
            # within a scene instead of holding one picture for fifteen seconds.
            prompts = [scene["prompt"]] + list(scene.get("shots", []))
        elif kind == "archival" and not (archival_dir / f"{scene['id']}.jpg").exists():
            prompts = [scene["fallback_prompt"]]
        if not prompts:
            continue
        studio = world_of(cast, scene) == "host"
        if studio and scene.get("camera") == "insert":
            refs = [studio_sheet(cast)]
        else:
            refs = refs_for(cast, scene)
        for idx, prompt in enumerate(prompts):
            suffix = "" if idx == 0 else "bcd"[idx - 1]
            out = img_dir / f"{scene['id']}{suffix}.jpg"
            if out.exists():
                continue
            if studio and scene.get("camera") == "insert":
                text = clean(" ".join([style_for(cast, "host"),
                                       clean(cast["studio"]["cameras"]["insert"]["master"]),
                                       clean(prompt),
                                       "The reference image is the same studio from the wide "
                                       "camera; match its table, lamp, microphone stands and "
                                       "colours."]))
            else:
                text = build_prompt(cast, scene, prompt, wardrobe)
            ok, tries = _generate_checked(text, refs, out, cast, scene, wardrobe, check=studio)
            total += tries
            if ok:
                print(f"scene image: {out.name}" + (f" (after {tries} tries)" if tries > 1 else ""))
            else:
                failed.append(out.name)
    print(f"images generated this run: {total}")
    contact_sheet(sorted(p for p in img_dir.glob("*.jpg") if not p.name.startswith("_")),
                  episode_dir(ep_id) / "images_review.jpg")
    if failed:
        raise SystemExit(f"These studio pictures failed the check twice and were not saved: "
                         f"{', '.join(failed)}. Look at their prompts before re-running.")


def contact_sheet(paths, out, cols=4, thumb_w=480):
    """One JPEG grid of labelled thumbnails, for quick review on a phone."""
    if not paths:
        return
    thumbs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        im.thumbnail((thumb_w, thumb_w))
        label = p.stem if p.parent == SHEETS_DIR else f"{p.parent.name}/{p.stem}"
        thumbs.append((label, im))
    th = max(t.height for _, t in thumbs) + 40
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * th), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT_SANS_BOLD, 24)
    for i, (label, im) in enumerate(thumbs):
        x, y = (i % cols) * thumb_w, (i // cols) * th
        sheet.paste(im, (x, y))
        draw.text((x + 8, y + im.height + 6), label, fill=(230, 230, 230), font=font)
    sheet.save(out, quality=85)
    print(f"review sheet: {out}")
