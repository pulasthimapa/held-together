"""Entry point.  python pipeline/run.py <stage> [--episode ep01] [--placeholders]

Stages, in order:
  cast    generate the five cast reference sheets (once for the whole channel)
  images  generate one illustration per scene
  voice   narrate every scene in the cloned voice
  render  build the long video, captions file and vertical cuts
  all     images + voice + render
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import images  # noqa: E402
import render  # noqa: E402
import voice  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["cast", "images", "voice", "render", "all"])
    parser.add_argument("--episode", default="ep01")
    parser.add_argument("--placeholders", action="store_true",
                        help="render with grey placeholders for missing images/audio (testing)")
    args = parser.parse_args()

    if args.stage == "cast":
        images.make_cast_sheets()
    if args.stage in ("images", "all"):
        images.make_scene_images(args.episode)
    if args.stage in ("voice", "all"):
        voice.make_narration(args.episode)
    if args.stage in ("render", "all"):
        render.render(args.episode, allow_placeholders=args.placeholders)


if __name__ == "__main__":
    main()
