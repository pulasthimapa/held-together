"""Offline tests: no API key, no spend.  python films/engine/test_films.py

Uses Held Together's ep01 clips as real Veo output (3 talk, 4 do not) for the speech check,
and fake Veo / vision responses for the retry, flagging and budget logic.
"""
import copy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rules  # noqa: E402
import qc  # noqa: E402
import film as F  # noqa: E402
import gemini  # noqa: E402
import veo  # noqa: E402

EP01 = rules.ROOT / "episodes" / "ep01"
PASS_STILL = {"people": [], "faces_natural": True, "face_problem": "", "expression_matches": True,
              "is_hand_drawn_anime": True, "text_visible": False, "summary": "ok"}
PASS_CLIP = {"same_people_throughout": True, "new_person_appears": False,
             "faces_natural_all_frames": True, "face_problem": "", "mouth_moves_as_if_talking": False,
             "expression_jump": False, "style_held": True, "summary": "ok"}


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        ok.failed += 1


ok.failed = 0


def test_lint():
    film, style, acting, d = rules.load("pilot")
    errors, warnings = rules.lint(film, style, acting, d)
    ok(not errors, f"pilot film lints clean {errors}")
    bad = copy.deepcopy(film)
    s = bad["shots"][0]
    s["motion"] = 'she asks "are you coming home?" and starts sobbing'
    s["framing"], s["seconds"], s["intensity"] = "close-up", 8, "strong"
    bad["characters"]["kid"] = {"name": "Mia", "age": 6, "identity": "a girl"}
    errors, warnings = rules.lint(bad, style, acting, d)
    text = " ".join(errors)
    for needle in ("'asks' invites talking", "quotation marks", "'sobbing'",
                   "close shots last 4-6 s", "strong emotion hides the face"):
        ok(needle in text, f"linter catches {needle}")
    ok(any("only allows adults" in w for w in warnings), "linter warns about child characters")


def test_prompts():
    film, style, acting, _ = rules.load("pilot")
    s1 = film["shots"][0]
    still = rules.still_prompt(film, s1, style, acting)
    motion = rules.motion_prompt(film, s1, style, acting)
    ok("Every mouth is gently closed" in still, "still prompt closes mouths")
    ok("nobody speaks" in motion and "no voices" in motion, "motion prompt carries the silence clause")
    ok("Faces stay on-model" in motion, "motion prompt carries the face clause")
    ok("Nana blinks slowly once" in motion, "motion prompt uses the acting beat")
    ok("locked-off camera with no camera movement" in rules.motion_prompt(film, s1, style, acting, 2),
       "retries lock the camera")
    ok([rules.clip_seconds({"seconds": 8}, a) for a in (1, 2, 3)] == [8, 6, 4], "retries get shorter")
    print("\nSTILL PROMPT S01:\n" + still + "\n\nMOTION PROMPT S01:\n" + motion + "\n")


def test_speech_on_real_veo_clips():
    talking = {"S04", "S05", "S31"}
    for clip in sorted((EP01 / "video").glob("S*.mp4")):
        flagged = qc.speech_problem(clip) is not None
        ok(flagged == (clip.stem in talking),
           f"speech check on ep01 {clip.stem}: {'talks' if flagged else 'silent'}")


def _make_clip(path, audio=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=640x360:d=6"]
    cmd += ["-i", str(audio)] if audio else ["-f", "lavfi", "-i", "anoisesrc=d=6:c=pink:a=0.1"]
    subprocess.run(cmd + ["-t", "6", "-shortest", "-c:v", "libx264", "-c:a", "aac", str(path)], check=True)


def test_clip_flow():
    film, style, acting, _ = rules.load("pilot")
    tmp = Path(tempfile.mkdtemp())
    silent, talky = tmp / "silent.mp4", tmp / "talky.mp4"
    _make_clip(silent)
    _make_clip(talky, EP01 / "audio" / "S01.mp3")
    for sub in ("stills", "clips", "rejected"):
        (tmp / sub).mkdir()
    shot = film["shots"][0]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=640x360:d=1",
                    "-frames:v", "1", str(tmp / "stills" / "S01.jpg")], check=True)
    gemini.inspect = lambda prompt, images, schema: PASS_CLIP

    # 1) first try talks -> rejected; second try is silent -> delivered as S01.mp4
    outputs = [talky.read_bytes(), silent.read_bytes()]
    veo.generate = lambda *a, **k: outputs.pop(0)
    budget, report = F.Budget(5), F.Report(tmp)
    F.make_clip(film, style, acting, tmp, budget, report, shot)
    r = report.data["clips"]["S01"]
    ok((tmp / "clips" / "S01.mp4").exists() and r["tries"] == 2 and "talks" in r["notes"][0],
       f"talking clip rejected, silent retry delivered ({r})")
    ok(abs(budget.spent - (6 * 0.05 + 0.01 + 6 * 0.05 + 0.01)) < 1e-9,
       f"spend tracked per try (${budget.spent:.2f})")

    # 2) every try talks -> delivered as S01_flagged.mp4 and reported
    (tmp / "clips" / "S01.mp4").unlink()
    veo.generate = lambda *a, **k: talky.read_bytes()
    F.make_clip(film, style, acting, tmp, F.Budget(5), report, shot)
    ok((tmp / "clips" / "S01_flagged.mp4").exists()
       and report.data["clips"]["S01"]["result"].startswith("FLAGGED"), "all tries fail -> flagged file")

    # 3) budget cap stops before the call that would cross it
    (tmp / "clips" / "S01_flagged.mp4").unlink()
    try:
        F.make_clip(film, style, acting, tmp, F.Budget(0.2), report, shot)
        ok(False, "budget cap stops spending")
    except F.BudgetStop:
        ok(True, "budget cap stops spending")

    # 4) a face problem from the vision check is a rejection too
    veo.generate = lambda *a, **k: silent.read_bytes()
    gemini.inspect = lambda p, i, s: dict(PASS_CLIP, faces_natural_all_frames=False,
                                          face_problem="eyes drift apart")
    problems = qc.check_clip(film, shot, silent, tmp / "stills" / "S01.jpg", acting, tmp / "rejected")
    ok(problems == ["unnatural face: eyes drift apart"], f"face problem rejects the clip {problems}")
    shutil.rmtree(tmp)


def test_still_check():
    film, style, acting, _ = rules.load("pilot")
    shot = film["shots"][0]
    sheets = {"nana": "x"}
    gemini.inspect = lambda p, i, s: dict(PASS_STILL, people=[
        {"where": "centre", "who": "nana", "matches_reference": True, "mouth_open": True},
        {"where": "doorway", "who": "someone_else", "matches_reference": False, "mouth_open": False}])
    problems = qc.check_still(film, shot, "still.jpg", sheets, acting)
    ok("open mouth (centre)" in problems and "unexpected person (doorway)" in problems,
       f"still check catches open mouth and stranger {problems}")
    gemini.inspect = lambda p, i, s: dict(PASS_STILL, people=[
        {"where": "centre", "who": "nana", "matches_reference": True, "mouth_open": False}])
    ok(qc.check_still(film, shot, "still.jpg", sheets, acting) == [], "clean still passes")


def test_estimate():
    film, *_ = rules.load("pilot")
    exp, worst = rules.estimate(film, "clips")
    ok(abs(exp - (14 * 0.05 + 0.02) * 1.5) < 1e-9, f"clip estimate ${exp:.2f} expected, ${worst:.2f} worst")


if __name__ == "__main__":
    test_lint()
    test_prompts()
    test_speech_on_real_veo_clips()
    test_clip_flow()
    test_still_check()
    test_estimate()
    print(f"\n{'ALL PASSED' if not ok.failed else f'{ok.failed} FAILED'}")
    sys.exit(1 if ok.failed else 0)
