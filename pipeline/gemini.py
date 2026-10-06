"""Image generation through the Gemini Interactions API (Nano Banana models).

Docs checked 2026-09-27: https://ai.google.dev/gemini-api/docs/image-generation
- gemini-3.1-flash-image       : supports up to 4 character reference images
- gemini-3.1-flash-lite-image  : cheapest, 1K only, no reference images

We use the full model for every still. The lite model's 1K cap meant half the
episode's pictures were upscaled to 1080p and looked soft; the extra cost is pennies.
"""
import base64
import os
import time

import requests

from common import env

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL_WITH_REFS = "gemini-3.1-flash-image"
MODEL_CHEAP = "gemini-3.1-flash-lite-image"


def _find_last_image(node):
    """Walk the response JSON and return the base64 data of the last image block."""
    found = None
    if isinstance(node, dict):
        if node.get("type") == "image" and node.get("data"):
            found = node["data"]
        for key, value in node.items():
            if key == "summary":  # skip interim "thought" images
                continue
            deeper = _find_last_image(value)
            if deeper:
                found = deeper
    elif isinstance(node, list):
        for item in node:
            deeper = _find_last_image(item)
            if deeper:
                found = deeper
    return found


def generate(prompt, refs=(), aspect="16:9", attempts=3, size=None):
    """Return JPEG bytes. `refs` is a list of image file paths used as character references.

    Every scene uses the full image model. The lite model is capped at 1K, and these
    stills are shown at 1920x1080 and then pushed in on, so anything upscaled looks
    soft next to the code-drawn explainers. Set IMAGE_MODEL / IMAGE_SIZE to override.
    """
    model = os.environ.get("IMAGE_MODEL", MODEL_WITH_REFS)
    size = size or os.environ.get("IMAGE_SIZE", "2K")
    parts = [{"type": "text", "text": prompt}]
    for ref in list(refs)[:4]:
        parts.append({"type": "image", "mime_type": "image/jpeg",
                      "data": base64.b64encode(open(ref, "rb").read()).decode()})

    def body_for(image_size):
        return {"model": model, "input": parts,
                "response_format": {"type": "image", "mime_type": "image/jpeg",
                                    "aspect_ratio": aspect, "image_size": image_size}}

    headers = {"x-goog-api-key": env("GEMINI_API_KEY"), "Content-Type": "application/json"}
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(API_URL, json=body_for(size), headers=headers, timeout=300)
            if resp.status_code == 200:
                data = _find_last_image(resp.json())
                if data:
                    return base64.b64decode(data)
                last_error = "response contained no image"
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:400]}"
                if resp.status_code == 400 and size != "1K" and "image_size" in resp.text:
                    # this model or account does not offer the larger size; take 1K
                    print(f"  (image_size {size} refused, falling back to 1K)")
                    size = "1K"
                    continue
                if resp.status_code in (401, 403):
                    break  # not retryable
                if resp.status_code == 400:
                    break
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(5 * attempt)
    raise RuntimeError(f"Image generation failed ({model}, {size}): {last_error}")
