# Held Together: research knowledge base

Checked 29 September 2026. A finding counts as **Verified** only when two independent sources support it. **Single source** findings are working hypotheses.

## Access limits (read first)

- Reddit is blocked from the workspace. YouTube video pages were rate-limited. X, Facebook and Bluesky refused or were not reachable. Chrome was not connected.
- So YouTube, Reddit, X and Facebook comment sections were **not** analysed. The only comment threads read were two Hacker News threads, plus the comment section of one Substack post.
- To fill this gap, connect Claude in Chrome and repeat the comment analysis on the Kurzgesagt video and the top r/NewTubers threads.

## Findings

| # | Finding | Status | Evidence | What it means for Held Together |
| --- | --- | --- | --- | --- |
| 1 | YouTube demonetises templated, mass-produced content whole-channel when a "significant portion" of it qualifies. Only names, settings or images changing between videos is a named example. | Verified | YouTube policy as reported by [Tubefilter](https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/) and [Yahoo Tech](https://tech.yahoo.com/social-media/articles/youtube-reveals-ai-slop-videos-090000379.html). Enforced in January 2026: 16 channels terminated, including CuentosFacinantes, 6M subscribers ([Hollywood Reporter](https://www.hollywoodreporter.com/business/digital/faceless-creators-youtube-ai-damage-1236617586/), [HackerNoon](https://hackernoon.com/youtubes-ai-slop-crackdown-cant-tell-a-directed-ai-film-from-a-bot-farm)) | A recurring cast is fine, but the plot, structure and opening must genuinely differ each episode. Never reuse a story skeleton. |
| 2 | "Emotionally manipulative formulas" and shock content without narrative purpose are a demonetisation category. Animal-rescue-style distress bait is the example. | Verified (policy) | Tubefilter and Yahoo Tech, reporting the same YouTube text | Emotion must come from real events told truthfully. No invented suffering, no graphic collapse imagery, no "you won't believe" framing. |
| 3 | Human-made faceless channels also get caught by YouTube's detection. | Verified | Kurzgesagt (25M+ subscribers) was wrongly flagged and had its worst-performing video since 2013; YouTube confirmed the error ([Dexerto](https://www.dexerto.com/youtube/youtubes-ai-slop-detector-incorrectly-targets-kurzgesagt-as-other-creators-fear-same-fate-3395930/), [Kotaku](https://kotaku.com/youtube-mistakenly-penalizes-popular-science-channel-kurzgesagt-for-ai-generated-slop-2000722702)). Doctor NOS (1.7M) says most faceless channels covering his topics were demonetised (Hollywood Reporter). | Build visible human signals: Indeepa's own voice for the Engineer's note, sources in every description, a behind-the-scenes post each month. Small channels can't easily reach YouTube support, so prevention matters more than appeals. |
| 4 | AI research produces confident false facts, and those facts spread into other videos. | Verified | Kurzgesagt tested AI research on brown dwarfs: about 20% of the facts couldn't be sourced. They later found another YouTube video repeating the same invented claims ([video summary](https://my.infocaptor.com/hub/summaries/kurzgesagt-in-a-nutshell/ai-slop-is-killing-our-channel-_zfN9wnPvU0); recapped independently on [Hacker News](https://news.ycombinator.com/item?id=45504156)). | Every claim in a script needs an opened source in the fact sheet. Numbers that sources disagree on get the safer wording. A search snippet or an AI summary is never a source. |
| 5 | Serious narrated channels invest heavily in research and review. | Verified | Kurzgesagt: about 100 hours of research per video, 2–3 fact-checkers and 1–3 expert reviewers. Fall of Civilizations: praised as richly researched, 100M+ downloads ([Wikipedia](https://en.wikipedia.org/wiki/Fall_of_Civilizations_(podcast))). | Our advantage is Indeepa's chartered-track engineering judgement. His review is the expert review step, and it should be mentioned on screen. |
| 6 | Real primary voices (letters, last words, telegrams) are what make narrated history land emotionally. | Single source | Fall of Civilizations reviews: it reconstructs people's last surviving words (Wikipedia, citing critics) | Use real documents where they exist, such as McLure's letters and Cooper's telegram, paraphrased and credited. Test on Episode 1 before treating this as a rule. |
| 7 | Titles and thumbnails are designed first; click-through rate and view duration drive distribution. | Single source | MrBeast's internal production guide ([Tubefilter](https://www.tubefilter.com/2024/09/17/mrbeast-internal-production-guide-leaked-key-points/), [Simon Willison](https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/)). Both describe one document. | Write the title and thumbnail idea before the script, and reject a story that has no clear thumbnail moment. |
| 8 | TikTok pays only for original videos of 60 seconds or more. Watermarked reposts earn nothing. The UK is eligible (10K followers, 100K views in 30 days). | Single source | [PostLink](https://postlinkapp.com/blog/tiktok-creator-rewards-program), updated July 2026. Confirm on TikTok's own page before relying on it. | Every vertical cut must be at least 61 seconds, and uploaded natively without a YouTube watermark. The Episode 1 "ring" cut was 58 s and has been extended. |
| 9 | Some faceless operators are adding hired on-camera hosts. | Single source | Noah Morris, who runs six channels (Hollywood Reporter) | Not needed for us yet. Indeepa's real recorded voice is the cheaper human signal. Revisit if monetisation is refused. |

## Comment analysis

**Hacker News, "Kurzgesagt: AI Slop Is Killing Our Channel"** (60 points, 7 comments)
- *Accountability:* one commenter argued that AI makes content so cheap that creators have no reason to care about accuracy, and banned channels are easily recreated.
- *Detection:* several said most viewers can't tell AI-made misinformation from real content.
- *Dissent:* one said slop is easy to spot and ignore.
- *Relevance:* audiences worry about accuracy more than about AI itself. Visible sourcing is a trust signal, not just a policy shield.

**Hacker News, "YouTube Mistakenly Penalizes Kurzgesagt"** (29 points, 4 comments)
- Commenters called "just don't look like AI" an impossible standard, and warned that false flags will hurt YouTube itself.
- *Relevance:* we can't control how YouTube's detector reads our content. We can control proof of human work: the credited expert, the sources, the real voice.

**Substack comments on Ryan McBeth's demonetised video** (about 20 comments)
- Viewers blamed YouTube's automated moderation and pledged support.
- *Relevance:* weak. That case was about sensitive topics, not AI. Recorded only because it was read.

## Sources opened

[Tubefilter policy](https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/) · [Yahoo Tech](https://tech.yahoo.com/social-media/articles/youtube-reveals-ai-slop-videos-090000379.html) · [Hollywood Reporter](https://www.hollywoodreporter.com/business/digital/faceless-creators-youtube-ai-damage-1236617586/) · [The Next Web](https://thenextweb.com/news/youtube-ai-slop-crackdown-faceless-creators-collateral-damage) · [HackerNoon](https://hackernoon.com/youtubes-ai-slop-crackdown-cant-tell-a-directed-ai-film-from-a-bot-farm) · [Dexerto](https://www.dexerto.com/youtube/youtubes-ai-slop-detector-incorrectly-targets-kurzgesagt-as-other-creators-fear-same-fate-3395930/) · [Kotaku](https://kotaku.com/youtube-mistakenly-penalizes-popular-science-channel-kurzgesagt-for-ai-generated-slop-2000722702) · [Kurzgesagt video summary](https://my.infocaptor.com/hub/summaries/kurzgesagt-in-a-nutshell/ai-slop-is-killing-our-channel-_zfN9wnPvU0) · [HN thread 1](https://news.ycombinator.com/item?id=45504156) · [HN thread 2](https://news.ycombinator.com/item?id=49225764) · [Fall of Civilizations](https://en.wikipedia.org/wiki/Fall_of_Civilizations_(podcast)) · [MrBeast guide, Tubefilter](https://www.tubefilter.com/2024/09/17/mrbeast-internal-production-guide-leaked-key-points/) · [Simon Willison](https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/) · [PostLink TikTok](https://postlinkapp.com/blog/tiktok-creator-rewards-program) · [Ryan McBeth Substack](https://ryanmcbeth.substack.com/p/youtube-demonitized-my-latest-roundup/comments)
