# Films: wordless anime shorts (separate channel)

You give an idea; Claude writes the story and shot list; you approve the characters and
places; the pipeline makes every clip, checks it, and hands you numbered files for CapCut.

## Milestones

| # | Who | What happens |
|---|---|---|
| 1 | You | Give Claude the rough idea. |
| 2 | You approve | Claude writes `films/<film>/film.yaml` (story, characters, places, shot list) and sets `approved.script: true` once you say yes. |
| 3 | You approve | Run **sheets**. Look at `review_sheets.jpg` in the download. Say yes and Claude sets `approved.sheets: true`; say what to change and only that picture is redone. |
| 4 | Automatic | Run **all**. Every still and clip is generated and checked; failures are redone up to 3 times. |
| 5 | You | Download the clips (`S01.mp4`, `S02.mp4` ...) and edit in CapCut. |

## How to run

GitHub → **Actions** → **Make film clips** → **Run workflow** → choose the stage and the film.
When it finishes, open the run and download the zip under **Artifacts**. It has the clips,
`report.md` and the review pictures.

`check` is free and runs before every stage anyway. It refuses to start if a rule is broken,
if a milestone isn't approved, or if the key is missing.

## The two safeguards

**Nobody talks.** Evidence: in Held Together ep01, 3 of 7 Veo clips came back with voices. Two
had been asked to speak; the third (still mourners) talked anyway.
1. The linter blocks speaking words (says, asks, whispers, sings...) and quotation marks.
2. Every clip prompt carries the silence clause from `style.yaml` and asks only for named sounds.
3. A speech detector listens to every clip's own soundtrack. Veo draws mouths and voices
   together, so speech on the soundtrack means someone talked. It flagged all 3 talking ep01
   clips and none of the 4 silent ones.
4. A vision check looks for mouths moving across frames.
5. Shot rule: one actor per shot; anyone else stays still in the background.

**Faces stay natural.**
1. The expression is drawn into the still; the clip adds one small movement (`acting.yaml`).
2. Strong emotion hides the face (back, profile, hair shadow, hands), so the body carries it.
3. Extreme words (sobbing, screaming, shocked...) are blocked.
4. Close shots last 4-6 s; retries get shorter (8, 6, then 4 s) and lock the camera.
5. A vision check compares each still with the character sheets, and each clip's frames with
   its start frame: same face, natural features, no expression jumps, style held.

A shot that fails 3 times is still delivered, as `S07_flagged.mp4`, with the reason in
`report.md`, so you decide whether to use it, trim it or drop it.

## Cost

Prices from the Gemini API pricing page (updated 15 Oct 2026). Veo 3.1 Lite costs $0.05/s and
Fast $0.10/s at 720p; a 2K still costs $0.101. `budget_usd` in each film is a hard stop.
The pilot costs about $1.50. A 3-minute film of about 30 clips is estimated at about $23,
or $46 at worst.
