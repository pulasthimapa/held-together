# Held Together — production pipeline

Turns an episode file (`episodes/<ep>/episode.yaml`) plus its fact sheet into a finished long
video, captions, a YouTube description and vertical cuts. Everything runs on GitHub Actions.

Format and rules: `CLAUDE.md`. Look and studio: `docs/brand.md`. Hosts, studio, troupe:
`cast/cast.yaml`.

## Secrets (Settings → Secrets and variables → Actions)

| Name | What |
| --- | --- |
| `GEMINI_API_KEY` | Google AI Studio → API keys (images and video; prepaid credit must be topped up) |
| `ELEVENLABS_API_KEY` | ElevenLabs → Developers → API keys (the `sk_…` value, not the key ID) |
| `ELEVENLABS_VOICE_ELIAS` | Voice ID for Elias: older English man, measured |
| `ELEVENLABS_VOICE_MAYA` | Voice ID for Maya: younger woman, bright and quick |

Both host voices are required and must differ; the voice stage refuses to run otherwise.

## Making an episode

**Actions → Produce episode → Run workflow**, one stage at a time, waiting for green.

| Stage | What it does | Check after |
| --- | --- | --- |
| `check` | Validates everything and prints what each stage would generate. Free. | Read the "plan" lines |
| `cast` | Draws missing cast sheets and the studio plate (rarely needed) | `review-cast` |
| `images` | Draws every scene still | `review-images` |
| `video` | Animates the hero moments from their stills (optional) | `review-video` (frames from each clip) |
| `voice` | Voices Elias and Maya | The log prints each host's pitch |
| `render` | Builds the videos and the description | `videos-<ep>` |

Every stage first runs the same checks as `check`, so nothing is spent if the episode is
invalid, a secret is missing, or a narrated line is not in the fact sheet. After the stage
it verifies what came back (valid 16:9 images, two distinct voices, clips long enough, an
episode of 8:00 or more, cuts of 61 s or more). Bad paid output is deleted so the next run
redoes it. Whatever was generated is committed back to the repo even if the stage fails,
so you never pay twice. To redo one file, delete it in GitHub and re-run its stage.

## Outputs

- `<ep>_long.mp4` and `<ep>_long.srt` — the YouTube episode and captions
- `<ep>_description.txt` — disclosure, sources, and where sources disagree (rules 1, 10)
- `<ep>_vertical_*.mp4` — 9:16 cuts for Shorts, TikTok, Reels and Facebook

Tick **Altered or synthetic content** on every YouTube upload.
