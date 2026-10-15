"""Wordless anime shorts: approved shot list -> numbered, checked clips for CapCut.

    python films/engine/film.py <stage> --film <id>

Stages (milestones in brackets):
  check   lint the film and print the cost; spends nothing. Runs before every other stage.
  sheets  character sheets + location plates for approval              [milestone 3]
  stills  one start frame per shot, each checked against the sheets    [needs approved.sheets]
  clips   animate every still, check for talking and strange faces     [milestone 4]
  all     stills then clips

Output: films/<id>/clips/S01.mp4, S02.mp4 ... plus report.md and review pictures.
A shot that fails all its tries is delivered as S07_flagged.mp4 and listed in report.md.
Files that already exist are never paid for twice; delete one to redo it.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import rules  # noqa: E402  (also puts pipeline/ on the path)
import gemini  # noqa: E402
import qc  # noqa: E402
import veo  # noqa: E402

WORKERS = 3


class Budget:
    """Running spend for this run. Stops before a call would take it over the film's cap."""

    def __init__(self, cap):
        self.cap, self.spent, self.lock = float(cap), 0.0, threading.Lock()

    def charge(self, usd, what):
        with self.lock:
            if self.spent + usd > self.cap:
                raise BudgetStop(f"stopped before {what}: ${self.spent:.2f} spent, "
                                 f"cap ${self.cap:.2f} (budget_usd in film.yaml)")
            self.spent += usd


class BudgetStop(Exception):
    pass


class Report:
    def __init__(self, film_dir):
        self.path = film_dir / "report.json"
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.lock = threading.Lock()

    def set(self, kind, sid, **info):
        with self.lock:
            self.data.setdefault(kind, {})[sid] = info
            self.path.write_text(json.dumps(self.data, indent=1))

    def write_markdown(self, film, film_dir, budget):
        lines = [f"# {film['title']}: run report", "",
                 f"Spent this run (estimate from the price list): ${budget.spent:.2f}", ""]
        for kind in ("stills", "clips"):
            rows = self.data.get(kind, {})
            if not rows:
                continue
            lines += [f"## {kind.capitalize()}", "", "| Shot | Result | Tries | Notes |",
                      "| --- | --- | --- | --- |"]
            for sid in sorted(rows):
                r = rows[sid]
                lines.append(f"| {sid} | {r['result']} | {r['tries']} | "
                             f"{'; '.join(r.get('notes', [])) or ''} |")
            lines.append("")
        (film_dir / "report.md").write_text("\n".join(lines))


# ------------------------------------------------------------------ stages

def stage_check(film, style, acting, film_dir, stage):
    errors, warnings = rules.lint(film, style, acting, film_dir)
    for w in warnings:
        print(f"warning: {w}")
    if stage in ("stills", "clips", "all"):
        if not film["approved"].get("script"):
            errors.append("approved.script is false: the story is not approved yet (milestone 2)")
        if not film["approved"].get("sheets"):
            errors.append("approved.sheets is false: approve review_sheets.jpg first (milestone 3)")
        missing = [str(p.relative_to(film_dir)) for p in _sheet_paths(film, film_dir).values()
                   if not p.exists()]
        if missing:
            errors.append(f"sheets missing: {', '.join(missing)}")
    if stage != "check" and not os.environ.get("GEMINI_API_KEY"):
        errors.append("GEMINI_API_KEY is not set (it lives in the repo's GitHub secrets)")
    if stage == "clips":
        missing = [s["id"] for s in film["shots"] if not (film_dir / "stills" / f"{s['id']}.jpg").exists()]
        if missing:
            errors.append(f"stills missing for {', '.join(missing)}: run the stills stage")
    if errors:
        raise SystemExit("Check failed, nothing was spent:\n" + "\n".join(f"  - {e}" for e in errors))
    exp, worst = rules.estimate(film, stage)
    print(f"check passed: {len(film['shots'])} shots, "
          f"{sum(int(s.get('seconds', 6)) for s in film['shots'])}s of clips. "
          f"Stage '{stage}': about ${exp:.2f} expected, ${worst:.2f} worst case; "
          f"run cap ${film['budget_usd']}.")
    if stage in ("clips", "all", "check"):
        qc.speech_seconds(_tone(film_dir))  # proves the speech model loads, before any spend
        print("speech check ready")


def _tone(film_dir):
    tone = film_dir / ".tone.wav"
    if not tone.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "sine=f=440:d=1", str(tone)], check=True)
    return tone


def _sheet_paths(film, film_dir):
    paths = {c: film_dir / "sheets" / f"{c}.jpg" for c in film["characters"]}
    paths.update({f"place:{l}": film_dir / "sheets" / f"place_{l}.jpg" for l in film["locations"]})
    return paths


def stage_sheets(film, style, acting, film_dir, budget):
    (film_dir / "sheets").mkdir(exist_ok=True)
    for key, out in _sheet_paths(film, film_dir).items():
        if out.exists():
            continue
        if key.startswith("place:"):
            prompt = rules.plate_prompt(film, key[6:], style)
        else:
            prompt = rules.sheet_prompt(film, key, style)
        budget.charge(rules.IMAGE_PRICE, f"sheet {out.name}")
        out.write_bytes(gemini.generate(prompt, aspect="16:9"))
        print(f"sheet: {out.name}")
    _grid(sorted(_sheet_paths(film, film_dir).values()), film_dir / "review_sheets.jpg", cols=3)
    print("Look at review_sheets.jpg. If you approve, set approved.sheets: true.")


def stage_stills(film, style, acting, film_dir, budget, report):
    out_dir = film_dir / "stills"
    rejected = film_dir / "rejected"
    out_dir.mkdir(exist_ok=True)
    rejected.mkdir(exist_ok=True)
    sheets = _sheet_paths(film, film_dir)
    for shot in film["shots"]:
        sid, out = shot["id"], out_dir / f"{shot['id']}.jpg"
        if out.exists():
            continue
        refs = [sheets[c] for c in shot.get("cast", [])] + [sheets[f"place:{shot['location']}"]]
        prompt = rules.still_prompt(film, shot, style, acting)
        notes = []
        for attempt in range(1, rules.ATTEMPTS + 1):
            budget.charge(rules.IMAGE_PRICE + rules.CHECK_PRICE, f"still {sid}")
            tmp = rejected / f"{sid}_try{attempt}.jpg"
            tmp.write_bytes(gemini.generate(prompt, refs=refs, aspect="16:9"))
            problems = qc.check_still(film, shot, tmp, sheets, acting)
            if not problems:
                shutil.move(tmp, out)
                report.set("stills", sid, result="passed", tries=attempt, notes=notes)
                print(f"still {sid}: passed on try {attempt}")
                break
            notes.append(f"try {attempt}: {', '.join(problems)}")
            print(f"still {sid} try {attempt} rejected: {', '.join(problems)}")
        else:
            shutil.copy(tmp, out)  # best effort, so the film is never blocked by one picture
            report.set("stills", sid, result="FLAGGED - look at it", tries=rules.ATTEMPTS, notes=notes)
    _grid([out_dir / f"{s['id']}.jpg" for s in film["shots"]], film_dir / "review_stills.jpg")


def make_clip(film, style, acting, film_dir, budget, report, shot):
    sid = shot["id"]
    clips, rejected = film_dir / "clips", film_dir / "rejected"
    still = film_dir / "stills" / f"{sid}.jpg"
    if (clips / f"{sid}.mp4").exists() or (clips / f"{sid}_flagged.mp4").exists():
        return
    notes, last = [], None
    model, res = shot.get("model", "lite"), shot.get("resolution", "720p")
    for attempt in range(1, rules.ATTEMPTS + 1):
        seconds = rules.clip_seconds(shot, attempt)
        prompt = rules.motion_prompt(film, shot, style, acting, attempt)
        budget.charge(seconds * rules.VEO_PRICE[(model, res)] + rules.CHECK_PRICE, f"clip {sid}")
        try:
            data = veo.generate(prompt, still, seconds, model, res)
        except veo.Refused as exc:
            notes.append(f"try {attempt}: Veo returned no video ({exc})")
            print(f"clip {sid} try {attempt}: no video ({exc})")
            continue
        last = rejected / f"{sid}_try{attempt}.mp4"
        last.write_bytes(data)
        problems = qc.check_clip(film, shot, last, still, acting, rejected)
        if not problems:
            shutil.move(last, clips / f"{sid}.mp4")
            report.set("clips", sid, result="passed", tries=attempt, notes=notes)
            print(f"clip {sid}: passed on try {attempt} ({seconds}s)")
            return
        notes.append(f"try {attempt}: {', '.join(problems)}")
        print(f"clip {sid} try {attempt} rejected: {', '.join(problems)}")
    if last:
        shutil.copy(last, clips / f"{sid}_flagged.mp4")
    report.set("clips", sid, result="FLAGGED - check or drop" if last else "NO CLIP",
               tries=rules.ATTEMPTS, notes=notes)


def stage_clips(film, style, acting, film_dir, budget, report):
    (film_dir / "clips").mkdir(exist_ok=True)
    (film_dir / "rejected").mkdir(exist_ok=True)
    with ThreadPoolExecutor(WORKERS) as pool:
        jobs = [pool.submit(make_clip, film, style, acting, film_dir, budget, report, s)
                for s in film["shots"]]
        errors = [j.exception() for j in jobs if j.exception()]
    clips = sorted((film_dir / "clips").glob("S*.mp4"))
    _clip_grid(clips, film_dir / "review_clips.jpg", film_dir / "rejected")
    if errors:
        raise errors[0]


# ------------------------------------------------------------------ review pictures

def _grid(paths, out, cols=4, tw=480, th=270):
    from PIL import Image
    paths = [p for p in paths if Path(p).exists()]
    if not paths:
        return
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows), (20, 20, 20))
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            im = im.convert("RGB")
            im.thumbnail((tw, th))
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out, quality=85)
    print(f"review picture: {out.name}")


def _clip_grid(clips, out, work):
    frames = []
    for c in clips:
        frames += qc.frames(c, work, points=(0.05, 0.5, 0.95))
    _grid(frames, out, cols=3)
    for f in frames:
        f.unlink(missing_ok=True)


# ------------------------------------------------------------------ main

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["check", "sheets", "stills", "clips", "all"])
    p.add_argument("--film", required=True)
    args = p.parse_args(argv)
    film, style, acting, film_dir = rules.load(args.film)
    stage_check(film, style, acting, film_dir, args.stage)
    if args.stage == "check":
        return
    budget, report = Budget(film["budget_usd"]), Report(film_dir)
    try:
        if args.stage == "sheets":
            stage_sheets(film, style, acting, film_dir, budget)
        if args.stage in ("stills", "all"):
            stage_stills(film, style, acting, film_dir, budget, report)
        if args.stage in ("clips", "all"):
            stage_clips(film, style, acting, film_dir, budget, report)
    except BudgetStop as stop:
        print(f"BUDGET: {stop}")
        raise SystemExit(1)
    finally:
        report.write_markdown(film, film_dir, budget)
        print(f"spent this run (estimate): ${budget.spent:.2f}")


if __name__ == "__main__":
    main()
