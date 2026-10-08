"""Entry point.  python pipeline/run.py <stage> [--episode ep01] [--placeholders]

Stages, in order:
  cast    generate the cast reference sheets and the studio plate (once for the channel)
  images  generate the illustrations for every scene (including extra shot angles)
  video   OPTIONAL: generate AI video clips for scenes marked hero_video
  voice   narrate every scene, Elias and Maya in their own voices
  render  build the long video, captions file, description and vertical cuts
  all     images + voice + render
  check   validate everything and print what each stage would generate; spends nothing

Every stage runs check.preflight first (nothing is spent if it fails) and check.verify after.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check  # noqa: E402
import images  # noqa: E402
import render  # noqa: E402
import voice  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage",
                        choices=["check", "cast", "images", "video", "voice", "render", "all"])
    parser.add_argument("--episode", default="ep01")
    parser.add_argument("--placeholders", action="store_true",
                        help="render with grey placeholders for missing images/audio (testing)")
    args = parser.parse_args()

    stages = ["images", "voice", "render"] if args.stage == "all" else [args.stage]
    for stage in stages:
        check.preflight(stage, args.episode, inputs=not args.placeholders)
        if stage == "check":
            return
        run_stage(stage, args)
        if not args.placeholders:
            check.verify(stage, args.episode)


def run_stage(stage, args):
    if stage == "cast":
        images.make_cast_sheets()
    if stage == "images":
        images.make_scene_images(args.episode)
    if stage == "video":
        import video
        video.make_hero_clips(args.episode)
    if stage == "voice":
        voice.make_narration(args.episode)
    if stage == "render":
        render.render(args.episode, allow_placeholders=args.placeholders)


if __name__ == "__main__":
    main()
