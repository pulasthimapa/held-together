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


def build_prompt(cast, scene, prompt, wardrobe=None):
    """The full text sent to the image model for one picture of one scene.

    Studio scenes always get the permanent set and the hosts' signature wardrobe, so no
    episode file can move the podcast to a different room or change what the hosts wear.
    """
    world = world_of(cast, scene)
    parts = [style_for(cast, world)]
    if world == "host":
        parts.append(clean(cast["studio"]["description"]))
    parts.append(clean(prompt))
    for actor_id in scene.get("actors", []):
        # An episode may recolour a host's clothes (episode.yaml `wardrobe:`); otherwise
        # the signature look from cast.yaml is used.
        look = (wardrobe or {}).get(actor_id) or cast["actors"][actor_id].get("wardrobe")
        if look and world == "host":
            parts.append(clean(look))
    if world == "host":
        # The studio has two seats, so the model fills an empty one with a stranger unless
        # told otherwise. Only the hosts named in the scene may appear (seen in ep01 S04).
        people = [cast["actors"][a]["name"] for a in scene.get("actors", [])]
        if not people:
            parts.append("No people appear anywhere in the picture.")
        elif len(people) == 1:
            parts.append(f"{people[0]} is the only person in the picture: the camera is framed "
                         f"on {people[0]} alone, the other seat is out of shot, and no other "
                         f"person, shoulder, back of a head or silhouette appears anywhere.")
        else:
            parts.append(f"Only {' and '.join(people)} are in the picture; no third person "
                         f"appears anywhere.")
    if scene.get("actors"):
        names = ", ".join(cast["actors"][a]["name"] for a in scene["actors"])
        parts.append(f"The first reference images show {names}; keep each face, hair and build "
                     "exactly as in the references.")
    if world == "host":
        parts.append("The last reference image is the studio: keep the room, the table, the "
                     "microphones, the headphones, the shelves and the lighting exactly as in "
                     "it, seen from this scene's camera angle.")
    return clean(" ".join(parts))


def refs_for(cast, scene):
    refs = []
    for actor_id in scene.get("actors", []):
        sheet = SHEETS_DIR / f"{actor_id}.jpg"
        if not sheet.exists():
            raise SystemExit(f"Missing cast sheet for {actor_id}. Run the 'cast' stage first.")
        refs.append(sheet)
    if world_of(cast, scene) == "host":
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


def make_scene_images(ep_id):
    cast = load_cast()
    ep = load_episode(ep_id)
    img_dir = episode_dir(ep_id) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    archival_dir = episode_dir(ep_id) / "archival"
    total = 0
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
        for idx, prompt in enumerate(prompts):
            suffix = "" if idx == 0 else "bcd"[idx - 1]
            out = img_dir / f"{scene['id']}{suffix}.jpg"
            if out.exists():
                continue
            out.write_bytes(gemini.generate(build_prompt(cast, scene, prompt,
                                                         ep.get("wardrobe")), refs=refs,
                                            aspect="16:9"))
            total += 1
            print(f"scene image: {out.name}")
    print(f"images generated this run: {total}")
    contact_sheet(sorted(img_dir.glob("*.jpg")), episode_dir(ep_id) / "images_review.jpg")


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
