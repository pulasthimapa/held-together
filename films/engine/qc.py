"""Automatic checks. A still or clip that fails is redrawn; one that cannot be checked never passes.

Speech check  - Silero VAD (offline, free) listens to the clip's own soundtrack. Veo draws the
                mouths and the voices together, so speech on the soundtrack means someone talked.
                Tested 15 Oct 2026 on the 7 Held Together ep01 clips: it flagged exactly the 3
                that talk (S04, S05, S31) and passed the 4 silent ones, plus synthetic music.
Vision check  - the Gemini vision model compares frames with the approved sheets / start frame:
                who is in frame, natural faces, closed mouths, expression, style.
"""
import importlib.util
import os
import subprocess
from pathlib import Path

import numpy as np

import gemini  # Held Together's client (pipeline/gemini.py)
from common import duration
from rules import acting_for, clean

SPEECH_LONGEST_S = 0.5   # any continuous speech this long fails the clip
SPEECH_TOTAL_S = 1.0     # or this much speech in total

_vad = None


def _vad_session():
    global _vad
    if _vad is None:
        import onnxruntime as ort
        # Locate the model inside the pip package without importing it (its __init__ needs
        # torch, which we avoid: onnxruntime alone runs the model).
        spec = importlib.util.find_spec("silero_vad")
        path = os.environ.get("SILERO_VAD_ONNX") or str(
            Path(spec.submodule_search_locations[0]) / "data" / "silero_vad.onnx")
        _vad = ort.InferenceSession(path)
    return _vad


def speech_seconds(path):
    """(total seconds of speech, longest continuous run) on a file's soundtrack."""
    sr, n, ctx_n = 16000, 512, 64
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
                          "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if x.size == 0:
        return 0.0, 0.0
    x = np.pad(x, (0, (-len(x)) % n))
    sess = _vad_session()
    state = np.zeros((2, 1, 128), np.float32)
    ctx = np.zeros((1, ctx_n), np.float32)
    flags = []
    for i in range(0, len(x), n):
        chunk = np.concatenate([ctx, x[i:i + n][None, :]], axis=1)
        out, state = sess.run(None, {"input": chunk, "state": state,
                                     "sr": np.array(sr, np.int64)})
        ctx = chunk[:, -ctx_n:]
        flags.append(float(out[0][0]) > 0.5)
    hop, run, best = n / sr, 0, 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return round(sum(flags) * hop, 2), round(best * hop, 2)


def speech_problem(clip):
    total, longest = speech_seconds(clip)
    if longest >= SPEECH_LONGEST_S or total >= SPEECH_TOTAL_S:
        return f"someone talks ({total:.1f}s of speech on the soundtrack)"
    return None


# ------------------------------------------------------------------ stills

def _still_schema(ids):
    return {"type": "object", "properties": {
        "people": {"type": "array", "items": {"type": "object", "properties": {
            "where": {"type": "string"},
            "who": {"type": "string", "enum": list(ids) + ["someone_else"]},
            "matches_reference": {"type": "boolean"},
            "mouth_open": {"type": "boolean"}},
            "required": ["where", "who", "matches_reference", "mouth_open"]}},
        "faces_natural": {"type": "boolean"},
        "face_problem": {"type": "string"},
        "expression_matches": {"type": "boolean"},
        "is_hand_drawn_anime": {"type": "boolean"},
        "text_visible": {"type": "boolean"},
        "summary": {"type": "string"}},
        "required": ["people", "faces_natural", "face_problem", "expression_matches",
                     "is_hand_drawn_anime", "text_visible", "summary"]}


def check_still(film, shot, still, sheets, acting):
    """Problems with one start frame (empty list = pass)."""
    chars = film["characters"]
    cast = shot.get("cast", [])
    act = acting_for(shot, acting)
    intro = " ".join(f"Image {i + 1} is the reference sheet for {chars[c]['name']} (id {c}): "
                     f"{clean(chars[c]['identity'])}." for i, c in enumerate(cast))
    last = len(cast) + 1
    expect = (f"{chars[shot['acting']]['name']} should show: {act['still']}."
              if act else "No particular expression is required.")
    prompt = (f"{intro} Image {last} is a new frame from a wordless hand-drawn anime film. "
              f"List EVERY person visible in image {last}, even small, partly visible or far "
              f"away. For each, say who it is by face, hair, build and clothes (someone_else if "
              f"it matches no sheet; be strict), whether they match their sheet, and whether "
              f"their mouth is open. faces_natural is false if any face has distorted, melted "
              f"or asymmetric features, misplaced or mismatched eyes, extra or missing features, "
              f"an uncanny or exaggerated expression, or if any hand is malformed; describe it "
              f"in face_problem. {expect} Set expression_matches accordingly. "
              f"is_hand_drawn_anime is false if the picture looks photoreal, 3D or CGI. "
              f"text_visible is true if any readable letters, numbers or signs appear.")
    answer = gemini.inspect(prompt, [sheets[c] for c in cast] + [still], _still_schema(cast))
    problems = []
    people = answer.get("people", [])
    for p in people:
        if p["who"] == "someone_else":
            problems.append(f"unexpected person ({p['where']})")
        elif not p["matches_reference"]:
            problems.append(f"{p['who']} does not match the sheet ({p['where']})")
        if p.get("mouth_open"):
            problems.append(f"open mouth ({p['where']})")
    if not cast and people:
        problems.append("people in a shot that should be empty")
    seen = {p["who"] for p in people}
    problems += [f"{chars[c]['name']} missing" for c in cast if c not in seen]
    if not answer.get("faces_natural", False):
        problems.append(f"unnatural face: {answer.get('face_problem', '')}".strip())
    if act and not answer.get("expression_matches", False):
        problems.append("expression does not match the acting note")
    if not answer.get("is_hand_drawn_anime", False):
        problems.append("not in the hand-drawn anime style")
    if answer.get("text_visible"):
        problems.append("readable text in the picture")
    return problems


# ------------------------------------------------------------------ clips

CLIP_SCHEMA = {"type": "object", "properties": {
    "same_people_throughout": {"type": "boolean"},
    "new_person_appears": {"type": "boolean"},
    "faces_natural_all_frames": {"type": "boolean"},
    "face_problem": {"type": "string"},
    "mouth_moves_as_if_talking": {"type": "boolean"},
    "expression_jump": {"type": "boolean"},
    "style_held": {"type": "boolean"},
    "summary": {"type": "string"}},
    "required": ["same_people_throughout", "new_person_appears", "faces_natural_all_frames",
                 "face_problem", "mouth_moves_as_if_talking", "expression_jump",
                 "style_held", "summary"]}


def frames(clip, out_dir, points=(0.25, 0.5, 0.75, 0.97)):
    d = duration(clip)
    paths = []
    for i, p in enumerate(points):
        f = Path(out_dir) / f"{Path(clip).stem}_f{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * p:.2f}", "-i", str(clip),
                        "-frames:v", "1", str(f)], check=True)
        paths.append(f)
    return paths


def check_clip(film, shot, clip, still, acting, work_dir):
    """Problems with one clip (empty list = pass). Speech first: it is free."""
    problem = speech_problem(clip)
    if problem:
        return [problem]
    act = acting_for(shot, acting)
    intended = " ".join(x for x in [act["beat"] if act else "", clean(shot["motion"])] if x)
    shots = frames(clip, work_dir)
    prompt = ("Image 1 is the approved starting frame of a clip from a wordless hand-drawn "
              "anime film. Images 2 to 5 are frames from later in the same clip, in time order. "
              f"The only intended movement is: {intended}. Judge strictly. "
              "same_people_throughout: everyone keeps the face, hair and clothes of image 1. "
              "new_person_appears: anyone not in image 1 appears. faces_natural_all_frames: "
              "false if any face in any frame is distorted, melted, asymmetric, has misplaced "
              "eyes or teeth, or an uncanny or exaggerated expression (describe in "
              "face_problem). mouth_moves_as_if_talking: true if any mouth is open or changes "
              "shape between frames as in speech or singing. expression_jump: true if any face "
              "changes expression far more than the intended movement. style_held: false if "
              "the picture turns photoreal, 3D or changes art style.")
    answer = gemini.inspect(prompt, [still] + shots, CLIP_SCHEMA)
    for f in shots:
        f.unlink(missing_ok=True)
    problems = []
    if not answer.get("same_people_throughout", False):
        problems.append("a face or outfit changes during the clip")
    if answer.get("new_person_appears"):
        problems.append("a new person appears")
    if not answer.get("faces_natural_all_frames", False):
        problems.append(f"unnatural face: {answer.get('face_problem', '')}".strip())
    if answer.get("mouth_moves_as_if_talking"):
        problems.append("mouth moves as if talking")
    if answer.get("expression_jump"):
        problems.append("expression changes too much")
    if not answer.get("style_held", False):
        problems.append("art style drifts")
    return problems
