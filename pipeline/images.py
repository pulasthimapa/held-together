"""Stage 1 and 2: cast reference sheets, then one illustration per scene.

Existing files are never regenerated, so re-running only fills gaps.
Delete a single image file to have it redrawn on the next run.
"""
from PIL import Image, ImageDraw, ImageFont

import gemini
from common import (FONT_SANS_BOLD, SHEETS_DIR, clean, episode_dir, load_cast,
                    load_episode)


def make_cast_sheets():
    cast = load_cast()
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for actor_id, actor in cast["actors"].items():
        out = SHEETS_DIR / f"{actor_id}.jpg"
        if out.exists():
            continue
        prompt = cast["style"] + " " + cast["sheet_prompt"].format(
            description=clean(actor["description"]))
        out.write_bytes(gemini.generate(clean(prompt), aspect="16:9"))
        made.append(out)
        print(f"cast sheet: {out.name}")
    contact_sheet(sorted(SHEETS_DIR.glob("*.jpg")), SHEETS_DIR.parent / "cast_review.jpg")
    return made


def make_scene_images(ep_id):
    cast = load_cast()
    ep = load_episode(ep_id)
    img_dir = episode_dir(ep_id) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    archival_dir = episode_dir(ep_id) / "archival"
    for scene in ep["scenes"]:
        kind = scene["type"]
        prompt = None
        if kind == "image":
            prompt = scene["prompt"]
        elif kind == "archival" and not (archival_dir / f"{scene['id']}.jpg").exists():
            prompt = scene["fallback_prompt"]
        if not prompt:
            continue
        out = img_dir / f"{scene['id']}.jpg"
        if out.exists():
            continue
        refs = []
        for actor_id in scene.get("actors", []):
            sheet = SHEETS_DIR / f"{actor_id}.jpg"
            if not sheet.exists():
                raise SystemExit(f"Missing cast sheet for {actor_id}. Run the 'cast' stage first.")
            refs.append(sheet)
        full = cast["style"] + " " + clean(prompt)
        if refs:
            names = ", ".join(cast["actors"][a]["name"] for a in scene["actors"])
            full += (f" The reference images show {names}; keep each face, hair and build "
                     "exactly as in the references, only the costume and setting change.")
        out.write_bytes(gemini.generate(clean(full), refs=refs, aspect="16:9"))
        print(f"scene image: {out.name}")
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
