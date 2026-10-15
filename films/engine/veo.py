"""Veo 3.1 image-to-video through the Gemini API.

Same request shape as pipeline/video.py, which produced Held Together's ep01 clips, plus the
`resolution` parameter (docs: ai.google.dev/gemini-api/docs/veo, updated 2026-10-08).
Image-to-video only accepts personGeneration "allow_adult" (same page).
"""
import base64
import time

import requests

from common import env
from rules import VEO_MODELS

BASE = "https://generativelanguage.googleapis.com/v1beta"
POLL_SECONDS = 10
POLL_LIMIT = 60  # ~10 minutes per clip


class Refused(Exception):
    """Veo finished without a video (usually a safety filter). Worth one more try."""


def generate(prompt, start_image, seconds, model="lite", resolution="720p"):
    key = env("GEMINI_API_KEY")
    body = {"instances": [{"prompt": prompt, "image": {
                "bytesBase64Encoded": base64.b64encode(open(start_image, "rb").read()).decode(),
                "mimeType": "image/jpeg"}}],
            "parameters": {"aspectRatio": "16:9", "durationSeconds": int(seconds),
                           "resolution": resolution, "personGeneration": "allow_adult"}}
    start = requests.post(f"{BASE}/models/{VEO_MODELS[model]}:predictLongRunning",
                          params={"key": key}, json=body, timeout=300)
    if start.status_code != 200:
        raise SystemExit(f"Veo request refused (HTTP {start.status_code}):\n{start.text[:600]}")
    op = start.json().get("name")
    if not op:
        raise SystemExit(f"No operation name in Veo response:\n{start.text[:600]}")
    for _ in range(POLL_LIMIT):
        time.sleep(POLL_SECONDS)
        poll = requests.get(f"{BASE}/{op}", params={"key": key}, timeout=60).json()
        if poll.get("error"):
            raise Refused(str(poll["error"])[:300])
        if poll.get("done"):
            uri = _find_uri(poll.get("response", poll))
            if not uri:
                raise Refused(f"no video returned: {str(poll)[:300]}")
            blob = requests.get(uri, params={"key": key}, timeout=300)
            blob.raise_for_status()
            return blob.content
    raise Refused("timed out waiting for the clip")


def _find_uri(node):
    if isinstance(node, dict):
        if isinstance(node.get("uri"), str):
            return node["uri"]
        node = list(node.values())
    if isinstance(node, list):
        for v in node:
            hit = _find_uri(v)
            if hit:
                return hit
    return None
