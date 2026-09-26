"""Shared paths and helpers for the Held Together pipeline."""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CAST_FILE = ROOT / "cast" / "cast.yaml"
SHEETS_DIR = ROOT / "cast" / "sheets"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H, FPS = 1920, 1080, 25


def load_cast():
    return yaml.safe_load(CAST_FILE.read_text())


def episode_dir(ep_id):
    return ROOT / "episodes" / ep_id


def load_episode(ep_id):
    return yaml.safe_load((episode_dir(ep_id) / "episode.yaml").read_text())


def clean(text):
    return " ".join((text or "").split())


def env(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Missing environment variable {name}. Add it as a GitHub secret.")
    return value


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr[-3000:])
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd[:6]))} ...")
    return result.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])
