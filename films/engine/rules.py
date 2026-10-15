"""Film files, prompt builder, linter and cost estimate. Nothing in this file spends money."""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FILMS = ROOT / "films"
sys.path.insert(0, str(ROOT / "pipeline"))  # reuse Held Together's tested Gemini client

from common import clean  # noqa: E402

# Model IDs: ai.google.dev/gemini-api/docs/veo (last updated 2026-10-08, checked 15 Oct 2026).
VEO_MODELS = {"lite": "veo-3.1-lite-generate-preview", "fast": "veo-3.1-fast-generate-preview"}
# USD per second, audio included: ai.google.dev/gemini-api/docs/pricing (updated 2026-10-15).
VEO_PRICE = {("lite", "720p"): 0.05, ("lite", "1080p"): 0.08,
             ("fast", "720p"): 0.10, ("fast", "1080p"): 0.12}
IMAGE_PRICE = 0.101   # gemini-3.1-flash-image at 2K, same page
CHECK_PRICE = 0.01    # one vision check: a deliberately generous estimate
ATTEMPTS = 3          # tries per still and per clip before a shot is flagged

FRAMINGS = ["extreme close-up", "close-up", "medium close-up", "medium", "medium wide",
            "wide", "extreme wide", "insert"]
CLOSE = {"extreme close-up", "close-up", "medium close-up"}

# Safeguard 1: words that make Veo give someone lines. Blocked in everything we write.
SPEECH = re.compile(
    r"\b(say|says|said|saying|speak\w*|spoke\w*|talk\w*|tell|tells|telling|told|ask|asks|"
    r"asked|asking|answer\w*|repl(y|ies|ied|ying)|shout\w*|yell\w*|scream\w*|whisper\w*|"
    r"sing|sings|singing|sang|song|songs|call(s|ed|ing)? out|mutter\w*|murmur\w*|chat\w*|"
    r"conversation\w*|dialogue\w*|voice\w*|word|words|narrat\w*|laugh\w*|giggl\w*|"
    r"exclaim\w*|cr(y|ies) out|lip.?sync\w*|mouths? (open\w*|mov\w*)|lips? mov\w*)\b", re.I)
QUOTES = re.compile(r"[\"“”]")
# Safeguard 2: words that push faces past what the model can draw cleanly.
EXTREME = re.compile(
    r"\b(sob\w*|bawl\w*|wail\w*|hysteric\w*|shriek\w*|devastat\w*|anguish\w*|agon\w*|"
    r"bursts? into tears|breaks? down|grimac\w*|gasp\w*|horrif\w*|terrif\w*|shock\w*|"
    r"jaw drops?|open.mouthed|crying|cries|wide.eyed|panic\w*|rage|furious)\b", re.I)


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())


def load(film_id):
    film_dir = FILMS / film_id
    return (load_yaml(film_dir / "film.yaml"), load_yaml(FILMS / "style.yaml"),
            load_yaml(FILMS / "acting.yaml"), film_dir)


def acting_for(shot, acting):
    emotion = shot.get("emotion", "none")
    if emotion == "none":
        return None
    return acting[emotion][shot.get("intensity", "soft")]


def sentence(text):
    text = clean(text).rstrip(".")
    return text[:1].upper() + text[1:] + "." if text else ""


# ------------------------------------------------------------------ prompts

def sheet_prompt(film, cid, style):
    c = film["characters"][cid]
    return " ".join([clean(style["sheet"]), clean(style["look"]),
                     f"The character is {c['name']}, {clean(c['identity'])}."])


def plate_prompt(film, loc, style):
    return " ".join([clean(style["plate"]), clean(style["look"]),
                     "Soft neutral daylight.", sentence(film["locations"][loc])])


def still_prompt(film, shot, style, acting):
    chars = film["characters"]
    cast = shot.get("cast", [])
    act = acting_for(shot, acting)
    parts = [clean(style["look"]),
             f"Lighting and colour: {clean(style['moods'][shot['mood']])}.",
             f"{shot['framing'].capitalize()} shot. Setting: {sentence(film['locations'][shot['location']])}",
             sentence(shot["action"])]
    for cid in cast:
        parts.append(f"{chars[cid]['name']} is {clean(chars[cid]['identity'])}, exactly as in "
                     f"the attached reference sheet.")
    if act:
        parts.append(f"{chars[shot['acting']]['name']}: {act['still']}.")
    if cast:
        parts.append(clean(style["still_mouths"]))
        if len(cast) > 1:
            parts.append(f"Only {chars[shot['acting']]['name']} shows strong feeling; everyone "
                         f"else is quiet and still.")
    else:
        parts.append("No people anywhere in the frame.")
    return " ".join(parts)


def motion_prompt(film, shot, style, acting, attempt=1):
    """Attempts 2 and 3 lock the camera: fewer moving parts, fewer chances to go wrong."""
    chars = film["characters"]
    cast = shot.get("cast", [])
    act = acting_for(shot, acting)
    camera = shot.get("camera", style["camera_default"]) if attempt == 1 else \
        "locked-off camera with no camera movement"
    parts = ["Hand-drawn anime animation. Keep the exact art style, colours, characters and "
             "setting of the starting frame for the whole clip.", f"Camera: {clean(camera)}."]
    if act:
        parts.append(f"{chars[shot['acting']]['name']} {act['beat']}.")
    parts.append(sentence(shot["motion"]))
    if cast:
        parts += [clean(style["silence"]), clean(style["face"])]
        if len(cast) > 1:
            parts.append(clean(style["crowd"]))
    else:
        parts.append("No people appear at any point.")
    parts.append(f"Sound: only {clean(shot['sound']).rstrip('.')}; no voices, no singing, "
                 f"no music.")
    return " ".join(parts)


def clip_seconds(shot, attempt):
    """Retries get shorter (8 -> 6 -> 4 s): faces drift less in shorter clips."""
    seconds = int(shot.get("seconds", 6))
    if shot.get("resolution", "720p") != "720p":
        return 8  # 1080p only exists at 8 s
    return {1: seconds, 2: min(seconds, 6), 3: 4}[min(attempt, 3)]


# ------------------------------------------------------------------ linter

def lint(film, style, acting, film_dir):
    """Returns (errors, warnings). Errors stop the run before anything is spent."""
    errors, warnings = [], []
    chars, locs = film.get("characters", {}), film.get("locations", {})

    def scan(where, text):
        text = text or ""
        for m in SPEECH.finditer(text):
            errors.append(f"{where}: '{m.group(0)}' invites talking. Describe a silent action.")
        if QUOTES.search(text):
            errors.append(f"{where}: quotation marks make Veo speak the words. Remove them.")
        for m in EXTREME.finditer(text):
            errors.append(f"{where}: '{m.group(0)}' is too extreme for a clean face. Use the "
                          f"acting library (e.g. emotion: tears / grief, intensity: strong).")

    for key in ("id", "approved", "budget_usd", "characters", "locations", "shots"):
        if key not in film:
            errors.append(f"film.yaml is missing '{key}'")
    if errors:
        return errors, warnings

    for cid, c in chars.items():
        scan(f"character {cid}", c.get("identity"))
        if int(c.get("age", 99)) < 18:
            warnings.append(f"{cid} is {c['age']}: Veo image-to-video only allows adults "
                            f"(personGeneration allow_adult, docs 2026-10-08). Shots with "
                            f"{c['name']} may be refused; keep children small or seen from behind.")
    for loc, text in locs.items():
        scan(f"location {loc}", text)

    seen = set()
    for i, s in enumerate(film["shots"]):
        sid = s.get("id", f"shot #{i + 1}")
        if not re.fullmatch(r"S\d{2}", str(sid)):
            errors.append(f"{sid}: shot ids are S01, S02 ... so the files sort in CapCut")
        if sid in seen:
            errors.append(f"{sid}: duplicate shot id")
        seen.add(sid)
        for key in ("location", "mood", "framing", "action", "motion", "sound"):
            if not s.get(key):
                errors.append(f"{sid}: missing '{key}'")
        if s.get("location") not in locs:
            errors.append(f"{sid}: unknown location '{s.get('location')}'")
        if s.get("mood") not in style["moods"]:
            errors.append(f"{sid}: unknown mood '{s.get('mood')}' (use {', '.join(style['moods'])})")
        if s.get("framing") not in FRAMINGS:
            errors.append(f"{sid}: framing must be one of {', '.join(FRAMINGS)}")
        cast = s.get("cast", [])
        for cid in cast:
            if cid not in chars:
                errors.append(f"{sid}: unknown character '{cid}'")
        if len(cast) > 3:
            errors.append(f"{sid}: at most 3 characters per shot (4 reference images incl. place)")
        emotion = s.get("emotion", "none")
        if emotion != "none":
            if emotion not in acting:
                errors.append(f"{sid}: emotion '{emotion}' is not in acting.yaml")
            elif s.get("intensity", "soft") not in acting[emotion]:
                errors.append(f"{sid}: intensity must be soft or strong")
            if s.get("acting") not in cast:
                errors.append(f"{sid}: 'acting' must name the one character who performs")
        if s.get("intensity") == "strong" and s.get("framing") in CLOSE and emotion != "tears":
            errors.append(f"{sid}: strong emotion hides the face; use medium or wider framing")
        seconds = s.get("seconds", 6)
        if seconds not in (4, 6, 8):
            errors.append(f"{sid}: seconds must be 4, 6 or 8")
        if s.get("framing") in CLOSE and seconds == 8:
            errors.append(f"{sid}: close shots last 4-6 s; faces drift in 8 s clips")
        model, res = s.get("model", "lite"), s.get("resolution", "720p")
        if (model, res) not in VEO_PRICE:
            errors.append(f"{sid}: model/resolution must be lite or fast at 720p or 1080p")
        if res == "1080p" and seconds != 8:
            errors.append(f"{sid}: 1080p clips must be 8 s (Veo rule)")
        if len(cast) > 1 and s.get("framing") in CLOSE:
            warnings.append(f"{sid}: two faces in a close shot is where wrong-person talking "
                            f"starts; consider one face plus a shoulder or back")
        for key in ("action", "motion", "sound", "camera"):
            scan(f"{sid} {key}", s.get(key))
    return errors, warnings


# ------------------------------------------------------------------ cost

def estimate(film, stage):
    """Expected and worst-case USD for a stage, using the Gemini API price list."""
    shots = film["shots"]
    sheets = (len(film["characters"]) + len(film["locations"])) * IMAGE_PRICE
    stills_one = len(shots) * (IMAGE_PRICE + CHECK_PRICE)
    clips_one = sum(int(s.get("seconds", 6)) * VEO_PRICE[(s.get("model", "lite"),
                                                         s.get("resolution", "720p"))]
                    + CHECK_PRICE for s in shots)
    table = {"sheets": (sheets, sheets),
             "stills": (stills_one * 1.3, stills_one * ATTEMPTS),
             "clips": (clips_one * 1.5, clips_one * ATTEMPTS)}
    if stage == "all":
        return tuple(table["stills"][i] + table["clips"][i] for i in (0, 1))
    return table.get(stage, (0.0, 0.0))
