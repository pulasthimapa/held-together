"""Image generation through the Gemini Interactions API (Nano Banana models).

Docs checked 2026-09-27: https://ai.google.dev/gemini-api/docs/image-generation
- gemini-3.1-flash-image       : supports up to 4 character reference images
- gemini-3.1-flash-lite-image  : cheapest, 1K only, no reference images
"""
import base64
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


def generate(prompt, refs=(), aspect="16:9", attempts=3):
    """Return JPEG bytes. `refs` is a list of image file paths used as character references."""
    model = MODEL_WITH_REFS if refs else MODEL_CHEAP
    parts = [{"type": "text", "text": prompt}]
    for ref in list(refs)[:4]:
        parts.append({"type": "image", "mime_type": "image/jpeg",
                      "data": base64.b64encode(open(ref, "rb").read()).decode()})
    body = {
        "model": model,
        "input": parts,
        "response_format": {"type": "image", "mime_type": "image/jpeg",
                            "aspect_ratio": aspect, "image_size": "1K"},
    }
    headers = {"x-goog-api-key": env("GEMINI_API_KEY"), "Content-Type": "application/json"}
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(API_URL, json=body, headers=headers, timeout=300)
            if resp.status_code == 200:
                data = _find_last_image(resp.json())
                if data:
                    return base64.b64decode(data)
                last_error = "response contained no image"
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:400]}"
                if resp.status_code in (400, 401, 403):
                    break  # not retryable
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(5 * attempt)
    raise RuntimeError(f"Image generation failed ({model}): {last_error}")
