# Held Together — production pipeline

Turns an episode file (`episodes/ep01/episode.yaml`) into a finished long video, a
captions file and three vertical cuts, using your cloned voice. Everything runs on
GitHub Actions; nothing runs on your computer.

## One-time setup

1. Create a **private** GitHub repository called `held-together` and upload this folder
   (or let Claude push it for you).
2. In the repository: **Settings → Secrets and variables → Actions → New repository secret**.
   Add three secrets:

   | Name | Where to find it |
   | --- | --- |
   | `GEMINI_API_KEY` | Google AI Studio → API keys |
   | `ELEVENLABS_API_KEY` | ElevenLabs → Profile → API keys |
   | `ELEVENLABS_VOICE_ID` | ElevenLabs → Voices → your clone → "ID" (copy button) |

   Never paste these keys into chat or into files.
3. Optional: put one royalty-free track from the YouTube Audio Library in `assets/music/`
   as an `.mp3`. It is mixed quietly under the narration.
4. Optional but recommended: save a public-domain archival photo for scene S18 as
   `episodes/ep01/archival/S18.jpg` (Library and Archives Canada holds photographs of the
   1907 collapse and the Kahnawake memorial). Without it, an illustration is used.

## Making an episode

Go to **Actions → Produce episode → Run workflow** and pick a stage. Run them in order;
each takes a few minutes. You can do this from the GitHub mobile app.

| Stage | What it does | Check after |
| --- | --- | --- |
| `cast` | Draws the five cast reference sheets (once for the whole channel) | Download `review-cast` and check the faces |
| `images` | Draws one illustration per scene using the cast sheets | Download `review-images` and check every scene |
| `voice` | Narrates every scene in your cloned voice | Nothing to check yet |
| `render` | Builds the videos | Download `videos-ep01` |

Generated images and audio are committed back to the repository, so re-running a stage
only fills gaps and you never pay twice. To redo one scene, delete its file
(`episodes/ep01/images/S12.jpg`, or `audio/S12.mp3`) in GitHub and re-run that stage.
To redo a cast face, delete `cast/sheets/<name>.jpg` and re-run `cast`.

## Outputs

- `ep01_long.mp4` — 16:9 episode for YouTube
- `ep01_long.srt` — captions to upload alongside it
- `ep01_vertical_*.mp4` — 9:16 cuts for Shorts, TikTok, Reels and Facebook

When uploading to YouTube, tick **Altered or synthetic content** (the narration is a
cloned voice).

## Approximate cost per episode

About 30 AI images (a few cents each) and about 8,000 characters of narration.
Check the Google AI Studio and ElevenLabs usage pages after the first run.
