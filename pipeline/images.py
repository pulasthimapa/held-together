"""Stage 1 and 2: cast reference sheets, then one illustration per scene.

Existing files are never regenerated, so re-running only fills gaps.
Delete a single image file to have it redrawn on the next run.
"""
from PIL import Image, ImageDraw, ImageFont

import gemini
from common import (FONT_SANS_BOLD, SHEETS_DIR, clean, episode_dir, load_cast,
                    load_episode)


def world_of(cast, scene):
    """Which visual world a scene belongs to (docs/brand.md).

    The present is photographed, the past is painted. A scene is in the studio only if a
    host appears in it; everything else — including every scene with no people at all — is
    the past, and is painted.
    """
    if scene.get("world") in ("host", "story"):
        return scene["world"]
    for actor_id in scene.get("actors", []):
        if cast["actors"].get(actor_id, {}).get("world") == "host":
            return "host"
    return "story"


MAX_REFS = 4  # the image model accepts at most four reference images per request


def studio_sheet(cast):
    return SHEETS_DIR / f"{cast['studio']['sheet']}.jpg"


HOSTS = ("elias", "maya")


def build_prompt(cast, scene, prompt, wardrobe=None):
    """The full text sent to the image model for one picture of one scene.

    Studio scenes are assembled entirely from cast.yaml: the permanent room, who exists in
    it (only Elias and Maya, both always referenced), the camera from the fixed rig, natural
    podcast posture and the hosts' clothes. The episode only supplies the camera choice and
    the expression or gesture, so no episode can move the hosts, invent a stranger in the
    empty chair, or put the camera somewhere a real podcast would not.
    """
    world = world_of(cast, scene)
    if world == "story":
        parts = [style_for(cast, "story"), clean(prompt)]
        if scene.get("actors"):
            names = ", ".join(cast["actors"][a]["name"] for a in scene["actors"])
            parts.append(f"The reference images show {names}; keep each face, hair and build "
                         "exactly as in the references, only the costume and setting change.")
        return clean(" ".join(parts))

    studio = cast["studio"]
    camera = scene.get("camera")
    if camera not in studio["cameras"]:
        raise SystemExit(f"{scene['id']}: studio scene needs camera: one of "
                         f"{', '.join(studio['cameras'])}")
    parts = [style_for(cast, "host"), clean(studio["description"]),
             clean(studio["cameras"][camera])]
    if camera == "insert":
        parts += [clean(prompt), "No people appear anywhere in the picture.",
                  "The reference image is the studio: keep the table, microphones and "
                  "lighting exactly as in it."]
        return clean(" ".join(parts))
    parts += [clean(studio["people"]), clean(studio["posture"]), clean(prompt)]
    for h in HOSTS:
        # An episode may recolour a host's clothes (episode.yaml `wardrobe:`).
        parts.append(clean((wardrobe or {}).get(h) or cast["actors"][h]["wardrobe"]))
    parts.append("Reference images: the first is Elias, the second is Maya; keep each face, "
                 "hair, glasses and build exactly as in them. The third is the studio: keep "
                 "the room, table, microphones, headphones, shelves and lighting exactly as in "
                 "it, seen from this camera position.")
    return clean(" ".join(parts))


def refs_for(cast, scene):
    world = world_of(cast, scene)
    if world == "host":
        names = [] if scene.get("camera") == "insert" else list(HOSTS)
    else:
        names = list(scene.get("actors", []))
    refs = []
    for actor_id in names:
        sheet = SHEETS_DIR / f"{actor_id}.jpg"
        if not sheet.exists():
            raise SystemExit(f"Missing cast sheet for {actor_id}. Run the 'cast' stage first.")
        refs.append(sheet)
    if world == "host":
        plate = studio_sheet(cast)
        if not plate.exists():
            raise SystemExit("Missing studio plate cast/sheets/studio.jpg. Run 'cast' first.")
        refs.append(plate)
    if len(refs) > MAX_REFS:
        raise SystemExit(f"{scene['id']}: {len(refs)} reference images, limit is {MAX_REFS}.")
    return refs


def style_for(cast, world):
    return cast[f"style_{world}"]


def make_cast_sheets():
    cast = load_cast()
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    made = []
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
        desc = clean(cast["studio"]["description"])
        prompt = style_for(cast, "host") + " " + cast["studio"]["plate_prompt"].format(
            description=desc)
        plate.write_bytes(gemini.generate(clean(prompt), aspect="16:9"))
        made.append(plate)
        print("studio plate: studio.jpg")
    contact_sheet(sorted(SHEETS_DIR.glob("*.jpg")), SHEETS_DIR.parent / "cast_review.jpg")
    return made


STUDIO_ATTEMPTS = 3  # a studio shot that fails the picture check is redrawn at most this often

CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "people": {"type": "array", "items": {"type": "object", "properties": {
            "where": {"type": "string"},
            "who": {"type": "string", "enum": ["elias", "maya", "someone_else"]},
            "clothes_match": {"type": "boolean"}},
            "required": ["where", "who", "clothes_match"]}},
        "anyone_standing_or_leaning_across": {"type": "boolean"},
        "summary": {"type": "string"}},
    "required": ["people", "anyone_standing_or_leaning_across", "summary"],
}


def check_studio_picture(cast, scene, picture, wardrobe=None):
    """Return a list of problems with one studio picture (empty means it passed).

    The image model sometimes fills the empty chair with an invented stranger or swaps a
    host's clothes. A vision model compares the picture with the hosts' reference sheets
    and the wardrobe text, so nothing reaches the edit without passing (CLAUDE.md F6, F8).
    """
    looks = {h: clean((wardrobe or {}).get(h) or cast["actors"][h]["wardrobe"]) for h in HOSTS}
    if scene.get("camera") == "insert":
        prompt = ("This is a close detail shot of a table. List every person visible, even "
                  "partly: a hand, a sleeve, a shoulder, a blurred figure. The list should "
                  "normally be empty.")
        refs = [picture]
    else:
        prompt = ("Image 1 is the reference for Elias. Image 2 is the reference for Maya. "
                  "Image 3 is a new picture from their podcast studio. List EVERY person "
                  "visible in image 3, even partly: a blurred foreground shoulder, the back of "
                  "a head, a hand at the edge. For each, judge by face, hair, build and skin "
                  "whether it is Elias, Maya, or someone_else; be strict, a different face or "
                  "hair is someone_else. Then say whether their clothes match: "
                  f"{looks['elias']} {looks['maya']} Also say whether anyone is standing or "
                  "leaning across the table.")
        refs = [SHEETS_DIR / "elias.jpg", SHEETS_DIR / "maya.jpg", picture]
    answer = gemini.inspect(prompt, refs, CHECK_SCHEMA)
    problems = []
    people = answer.get("people", [])
    if scene.get("camera") == "insert":
        if people:
            problems.append(f"a person appears in a table insert: {answer.get('summary')}")
        return problems
    for person in people:
        if person["who"] == "someone_else":
            problems.append(f"unknown person ({person['where']})")
        elif not person["clothes_match"]:
            problems.append(f"{person['who']} in the wrong clothes ({person['where']})")
    if answer.get("anyone_standing_or_leaning_across"):
        problems.append("someone standing or leaning across the table")
    seen = {p["who"] for p in people}
    if scene.get("camera") == "wide" and not {"elias", "maya"} <= seen:
        problems.append("the wide shot does not show both hosts")
    if scene.get("camera") in ("maya", "ots_maya") and "maya" not in seen:
        problems.append("Maya is not in her own shot")
    if scene.get("camera") in ("elias", "ots_elias") and "elias" not in seen:
        problems.append("Elias is not in his own shot")
    return problems


def make_scene_images(ep_id):
    cast = load_cast()
    ep = load_episode(ep_id)
    img_dir = episode_dir(ep_id) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    archival_dir = episode_dir(ep_id) / "archival"
    wardrobe = ep.get("wardrobe")
    studio_todo = [s for s in ep["scenes"] if s["type"] == "image"
                   and world_of(cast, s) == "host"
                   and not (img_dir / f"{s['id']}.jpg").exists()]
    if studio_todo:
        # Prove the picture check works before paying for any studio picture.
        gemini.inspect("Does this picture show a room? Answer with an empty people list.",
                       [studio_sheet(cast)], CHECK_SCHEMA)
        print(f"picture check ready ({gemini.INSPECT_MODEL})")
    total, rejected, failed = 0, 0, []
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
        refs = refs_for(cast, scene)
        studio = world_of(cast, scene) == "host"
        for idx, prompt in enumerate(prompts):
            suffix = "" if idx == 0 else "bcd"[idx - 1]
            out = img_dir / f"{scene['id']}{suffix}.jpg"
            if out.exists():
                continue
            full = build_prompt(cast, scene, prompt, wardrobe)
            tries = STUDIO_ATTEMPTS if studio else 1
            for attempt in range(1, tries + 1):
                data = gemini.generate(full, refs=refs, aspect="16:9")
                total += 1
                if not studio:
                    out.write_bytes(data)
                    break
                trial = img_dir / f"_{out.name}"
                trial.write_bytes(data)
                problems = check_studio_picture(cast, scene, trial, wardrobe)
                if not problems:
                    trial.rename(out)
                    break
                trial.unlink()
                rejected += 1
                print(f"  {out.name} attempt {attempt} rejected: {'; '.join(problems)}")
            if out.exists():
                print(f"scene image: {out.name}")
            else:
                failed.append(out.name)
    print(f"images generated this run: {total} (studio pictures rejected and redrawn: "
          f"{rejected})")
    contact_sheet(sorted(p for p in img_dir.glob("*.jpg") if not p.name.startswith("_")),
                  episode_dir(ep_id) / "images_review.jpg")
    if failed:
        raise SystemExit(f"These studio pictures failed the check {STUDIO_ATTEMPTS} times and "
                         f"were not saved: {', '.join(failed)}. Adjust their prompts.")


def contact_sheet(paths, out, cols=4, thumb_w=480):
    """One JPEG grid of labelled thumbnails, for quick review on a phone."""
    if not paths:
        return
    thumbs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        im.thumbnail((thumb_w, thumb_w))
        thumbs.append((p.stem, im))
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
