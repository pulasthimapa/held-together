"""Stage 3: narration in the cloned voice, one MP3 per scene (ElevenLabs API)."""
import time

import requests

from common import clean, env, episode_dir, load_episode

MODEL_ID = "eleven_multilingual_v2"
VOICE_SETTINGS = {"stability": 0.55, "similarity_boost": 0.85, "style": 0.15,
                  "use_speaker_boost": True}


def _tts(text, prev_text, next_text):
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{env('ELEVENLABS_VOICE_ID')}"
           "?output_format=mp3_44100_128")
    headers = {"xi-api-key": env("ELEVENLABS_API_KEY"), "Content-Type": "application/json"}
    body = {"text": text, "model_id": MODEL_ID, "voice_settings": VOICE_SETTINGS,
            "previous_text": prev_text, "next_text": next_text}
    for attempt in range(1, 4):
        resp = requests.post(url, json=body, headers=headers, timeout=300)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code == 422 and "previous_text" in body:
            body.pop("previous_text")
            body.pop("next_text")
            continue
        if resp.status_code in (401, 402, 403):
            raise SystemExit(f"ElevenLabs refused the request: {resp.text[:400]}")
        time.sleep(5 * attempt)
    raise RuntimeError(f"ElevenLabs failed: HTTP {resp.status_code} {resp.text[:400]}")


def make_narration(ep_id):
    ep = load_episode(ep_id)
    audio_dir = episode_dir(ep_id) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    spoken = [s for s in ep["scenes"] if s.get("narration")]
    chars = 0
    for i, scene in enumerate(spoken):
        out = audio_dir / f"{scene['id']}.mp3"
        if out.exists():
            continue
        text = clean(scene["narration"])
        prev_text = clean(spoken[i - 1]["narration"]) if i > 0 else ""
        next_text = clean(spoken[i + 1]["narration"]) if i + 1 < len(spoken) else ""
        out.write_bytes(_tts(text, prev_text, next_text))
        chars += len(text)
        print(f"narration: {out.name}")
    print(f"characters sent this run: {chars}")
