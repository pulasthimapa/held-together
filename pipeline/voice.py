"""Stage 3: narration, one MP3 per scene (ElevenLabs API).

Two speakers: Elias (the engineer of the period) and Maya (the modern engineer). A scene's
`speaker:` picks the voice. Set these repository secrets:

    ELEVENLABS_VOICE_ELIAS   older male, measured, weathered
    ELEVENLABS_VOICE_MAYA    younger female, clear, curious

Both host voices are REQUIRED. There is deliberately no fallback: a silent fallback once
voiced the whole of ep01 in one voice, and nobody could tell from the log.
"""
import os
import time

import requests

from common import clean, env, episode_dir, load_episode

MODEL_ID = "eleven_multilingual_v2"
# Elias carries weight and should sound settled; Maya is brighter and a little quicker.
VOICE_SETTINGS = {
    "elias": {"stability": 0.62, "similarity_boost": 0.85, "style": 0.18,
              "use_speaker_boost": True},
    "maya": {"stability": 0.48, "similarity_boost": 0.82, "style": 0.28,
             "use_speaker_boost": True},
}
DEFAULT_SPEAKER = "elias"


def voice_id_for(speaker):
    name = f"ELEVENLABS_VOICE_{speaker.upper()}"
    voice = os.environ.get(name, "").strip()
    if not voice:
        raise SystemExit(f"Secret {name} is missing or not passed to the workflow. "
                         f"Each host needs their own voice; refusing to fall back.")
    return voice


def check_voices(speakers):
    """Fail before spending anything if a voice is missing or two hosts share one."""
    ids = {s: voice_id_for(s) for s in speakers}
    if len(set(ids.values())) < len(ids):
        raise SystemExit(f"Two hosts share one voice ID: {sorted(ids)}. Give each their own.")
    for s, v in ids.items():
        print(f"voice for {s}: …{v[-4:]}")


def _tts(text, prev_text, next_text, speaker=DEFAULT_SPEAKER):
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id_for(speaker)}"
           "?output_format=mp3_44100_128")
    headers = {"xi-api-key": env("ELEVENLABS_API_KEY"), "Content-Type": "application/json"}
    settings = VOICE_SETTINGS.get(speaker, VOICE_SETTINGS[DEFAULT_SPEAKER])
    body = {"text": text, "model_id": MODEL_ID, "voice_settings": settings,
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
    check_voices(sorted({s.get("speaker", DEFAULT_SPEAKER) for s in spoken}))
    chars = 0
    for i, scene in enumerate(spoken):
        out = audio_dir / f"{scene['id']}.mp3"
        if out.exists():
            continue
        speaker = scene.get("speaker", DEFAULT_SPEAKER)
        text = clean(scene["narration"])
        # Only pass neighbouring lines from the SAME speaker: ElevenLabs uses them for
        # prosody, and feeding it the other voice's words makes the delivery drift.
        def neighbour(j):
            return (clean(spoken[j]["narration"])
                    if 0 <= j < len(spoken)
                    and spoken[j].get("speaker", DEFAULT_SPEAKER) == speaker else "")
        out.write_bytes(_tts(text, neighbour(i - 1), neighbour(i + 1), speaker))
        chars += len(text)
        print(f"narration: {out.name} ({speaker})")
    print(f"characters sent this run: {chars}")
