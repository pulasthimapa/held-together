"""Optional stage: short AI-generated video clips for a handful of hero moments.

Only scenes that carry a `hero_video:` prompt are generated, and the render falls back
to the scene's stills if a clip is missing, so this stage is never required.

Run this AFTER the images stage: where a scene already has a still, that still seeds the
clip, so the characters keep the faces from their reference sheets instead of being
reinvented by the video model.

WARNING — the request shape below follows Google's long-running "predict" pattern for
Veo but has NOT been verified against the live API in this session (working rule 13).
If the first run fails, the error prints the raw response: fix MODEL / _request_body /
_extract_uri here rather than anywhere else, they are the only API-shaped code.

Cost: video is by far the most expensive thing in this pipeline. MAX_CLIPS and
MAX_SECONDS are hard stops so a bad episode file cannot run up a bill.
"""
import base64
import os
import time

import requests

from common import env, episode_dir, load_cast, load_episode
from images import world_of

# The brand rule (docs/brand.md) is appended to EVERY clip prompt here, so an episode file
# can never ask for the wrong look. Without it Veo drifts painted stills into photoreal
# within four seconds, and invents faces where the still had none.
CLIP_STYLE = {
    "host": ("Photoreal live-action footage in a podcast studio. Keep the exact faces, hair, "
             "glasses and clothing of the starting frame; do not change anyone's appearance "
             "and never add anyone: only Elias and Maya exist in this studio. Both stay seated "
             "at their microphones. Locked-off tripod camera; at most a very slow push in. "
             "The room, the table and the microphones stay exactly as in the starting frame. "
             "Not animation, not 3D, not cartoon."),
    "story": ("Keep the golden-age oil-painting look of the starting frame for the whole "
              "clip: visible brushwork, canvas texture, painted light. The image stays a "
              "moving painting from first frame to last. Not photoreal, not 3D, not CGI."),
}

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")

MAX_CLIPS = 8          # per episode
MAX_SECONDS = 8        # per clip
POLL_SECONDS = 10
POLL_LIMIT = 60        # give up after ~10 minutes on one clip


def _request_body(prompt, seconds, start_image=None):
    """`start_image` seeds the clip from one of our own stills, so the cast keeps its face."""
    instance = {"prompt": prompt}
    if start_image:
        instance["image"] = {
            "bytesBase64Encoded": base64.b64encode(start_image.read_bytes()).decode(),
            "mimeType": "image/jpeg"}
    return {"instances": [instance],
            "parameters": {"aspectRatio": "16:9",
                           "durationSeconds": min(seconds, MAX_SECONDS),
                           "personGeneration": "allow_adult"}}


def _extract_uri(done):
    """Pull the video download URI out of a finished operation, tolerating shapes."""
    def walk(node):
        if isinstance(node, dict):
            if "uri" in node and isinstance(node["uri"], str):
                return node["uri"]
            for v in node.values():
                hit = walk(v)
                if hit:
                    return hit
        elif isinstance(node, list):
            for v in node:
                hit = walk(v)
                if hit:
                    return hit
        return None
    return walk(done.get("response", done))


def _generate(prompt, seconds, key, start_image=None):
    start = requests.post(f"{BASE}/models/{MODEL}:predictLongRunning",
                          params={"key": key},
                          json=_request_body(prompt, seconds, start_image),
                          timeout=300)
    if start.status_code != 200:
        raise SystemExit(
            f"Veo request refused (HTTP {start.status_code}). The API shape in "
            f"pipeline/video.py may be out of date. Raw response:\n{start.text[:600]}")
    op = start.json().get("name")
    if not op:
        raise SystemExit(f"No operation name in Veo response:\n{start.text[:600]}")

    for _ in range(POLL_LIMIT):
        time.sleep(POLL_SECONDS)
        poll = requests.get(f"{BASE}/{op}", params={"key": key}, timeout=60).json()
        if poll.get("error"):
            raise SystemExit(f"Veo failed: {poll['error']}")
        if poll.get("done"):
            uri = _extract_uri(poll)
            if not uri:
                raise SystemExit(f"Veo finished but no video URI found:\n{str(poll)[:600]}")
            blob = requests.get(uri, params={"key": key}, timeout=300)
            blob.raise_for_status()
            return blob.content
    raise SystemExit("Veo timed out waiting for the clip.")


def make_hero_clips(ep_id):
    ep = load_episode(ep_id)
    out_dir = episode_dir(ep_id) / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = [s for s in ep["scenes"] if s.get("hero_video")]
    if not wanted:
        print("no scenes carry hero_video; nothing to do")
        return
    if len(wanted) > MAX_CLIPS:
        raise SystemExit(f"{len(wanted)} hero clips requested, limit is {MAX_CLIPS}. "
                         f"Remove some hero_video entries before running this stage.")
    key = env("GEMINI_API_KEY")
    cast = load_cast()
    made = 0
    for scene in wanted:
        out = out_dir / f"{scene['id']}.mp4"
        if out.exists():
            continue
        seconds = min(float(scene.get("hero_seconds", 6)), MAX_SECONDS)
        # Animate our own still where one exists, so the cast keeps its face (rule 7b).
        seed = episode_dir(ep_id) / "images" / f"{scene['id']}.jpg"
        seed = seed if seed.exists() else None
        print(f"hero clip {scene['id']}: {seconds:.0f}s"
              f"{' from our still' if seed else ' from the prompt alone'} …")
        prompt = " ".join(scene["hero_video"].split()) + " " + CLIP_STYLE[world_of(cast, scene)]
        out.write_bytes(_generate(prompt, seconds, key, seed))
        made += 1
        print(f"hero clip: {out.name}")
    print(f"hero clips generated this run: {made} (existing files are never redone)")
