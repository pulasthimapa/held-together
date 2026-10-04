# Held Together: research knowledge base

Checked 29 September 2026. A finding counts as **Verified** only when two independent sources support it. **Single source** findings are working hypotheses.

## Access limits (read first)

Second pass on 29 September 2026. Every route was tried:
- **Browsers:** Claude in Chrome was not connected, the Claude desktop app's built-in browser was not connected, and the linked computer was offline.
- **Reddit:** readable through the public Arctic Shift archive. Its search was rate-limited after a few calls, but comment trees stayed readable. Four r/NewTubers threads were analysed. The large subreddits (r/youtube, r/PartneredYoutube) could not be searched, so the high-engagement threads there are **not** covered.
- **YouTube:** video metadata was readable, but comments were not. Mirror sites block automated readers, and that block was respected. The official Creator Insider video on the policy ([link](https://www.youtube.com/watch?v=14Vm0CiyUVE)) was found but could not be watched.
- **X:** signed in by the user on 4 October 2026 and read (see the X section). Facebook and Bluesky: not yet analysed.
- To close the gaps, connect Claude in Chrome or open the desktop app, then read the comment sections of the Kurzgesagt and Creator Insider videos and the top r/PartneredYoutube threads.

**Update, 4 October 2026 (third pass):** the desktop app's built-in browser reconnected. YouTube comments are now read first-hand (3 videos below, about 20 top comments each, sorted by YouTube's default "Top"). X showed a login page and was not signed in, so it was skipped. Facebook was not attempted (the connection dropped before sign-in). Reddit is still blocked in that browser. A YouTube "Top" sample is biased toward popular, agreeable comments, so treat it as indicative, not statistical.

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
| 10 | YouTube's own position: AI tools are fine, and "content farming" at volume is the target. The policy judges the output, not the tools used. | Verified | Matt Halprin, YouTube's trust and safety chief, quoted in [TechCrunch](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/); tool-agnostic wording reported by [Quasa](https://quasa.io/media/youtube-inauthentic-content-buckets-explained-in-2026-interview) | Our risk is volume and sameness, not the fact that we use AI. Keep the one-a-week pace. |
| 11 | Viewers in story niches reject content they recognise as AI, and "real voices matter for storytelling". | Verified (audience sentiment, small samples) | r/NewTubers horror-channel thread: the top comment (10 points) said viewers reject "AI slop", backed by two more. r/NewTubers "Is faceless good": a commenter said they now distrust new faceless channels because of AI. HN Kurzgesagt threads (finding 3). | The cloned voice is our biggest audience risk. Track comments that mention AI. If they recur, switch the main narration to Indeepa's real voice. |
| 12 | Human-made faceless channels still earn. | Verified | r/NewTubers: a faceless documentary/gaming channel with about 20k subscribers and about $1k a month (9 points). Kurzgesagt and Doctor NOS earn at scale (findings 3 and 5). | The format is viable. Earnings depend on quality and on being judged human-made. |
| 13 | For faceless documentary makers, the slowest steps are research, turning facts into a story, and finding visuals that aren't the same stock clips as everyone else. | Verified (practitioner reports) | r/NewTubers production-bottleneck thread (21 points, 31 comments): 7 comments on research and script, 6 on visuals, one citing 50+ references per video. Kurzgesagt's 100 research hours (finding 5). | Our pipeline automates the right parts: consistent cast art and code-drawn diagrams instead of stock footage. Story structure is locked before any images are drawn, as one commenter advised. |
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

**r/NewTubers "For those running faceless/documentary channels, what part of your production takes the most time?"** (21 points, 31 comments)
- Research and script were the biggest group (7 comments). The highest-scored comment (10 points) cited 50+ references per video.
- Visuals were next (6): finding footage that isn't the same stock clips as everyone else.
- One commenter (5 points) advised locking a three-act structure before gathering any assets.
- One warned that automating the research-to-script step produces generic content.
- *Relevance:* keep the research human-checked and the story structure fixed before images are generated.

**r/NewTubers "Can Faceless Channels Still Be Monetised Now?"** (15 comments)
- A faceless channel at about 20k subscribers and about $1k a month reported that quality is what matters (9 points).
- One sceptic (6 points) asked for evidence of harm. A reply cited Real Engineering and Kurzgesagt as suppressed; that is unverified for Real Engineering.
- One commenter pointed to YouTube's official Creator Insider explainer.
- *Relevance:* monetisation is possible, and official YouTube sources should be checked before trusting any rumour.

**r/NewTubers "Is faceless content a good way to start a YouTube channel?"** (33 comments)
- Most said content quality matters more than showing a face. The top comment (15 points) used Let's Game It Out, 6M+ subscribers, as the example.
- One advised testing five videos on different topics (8 points).
- The dissent: showing a face "will always be king", and one person now distrusts new faceless channels because of AI.
- *Relevance:* the format is fine, but trust must be earned through signs of human work.

**r/NewTubers "New horror stories faceless youtube channel"** (AI voice and stock footage, 8 comments)
- The top comment (10 points) said to give up because viewers reject "AI slop". Two more agreed (4 and 2 points).
- Practical replies: judge after five videos, work on thumbnails and retention, avoid repetitive stock visuals, and remember that real voices matter for storytelling.
- *Relevance:* this is the strongest evidence yet that an AI narrator in a story niche is penalised by viewers, not just by YouTube.

**Substack comments on Ryan McBeth's demonetised video** (about 20 comments)
- Viewers blamed YouTube's automated moderation and pledged support.
- *Relevance:* weak. That case was about sensitive topics, not AI. Recorded only because it was read.

### YouTube comments, read directly on 4 October 2026

**Kurzgesagt, "AI Slop Is Destroying The Internet"** (25.6M subscribers, 11M views, about 11 months old)
- Top comment, 107K likes: "Dead internet theory has become dead internet reality." Another, 66K: AI fatigue is making the writer spend less time on social media.
- 9.1K likes: "By humans, for humans" will become a sought-after phrase in what people buy and consume.
- 24K likes (TheMattShea): trust, not attention, is the scarce resource; channels viewers know to be human-made will thrive.
- 13K likes: a wish for a show/hide AI content filter. 1K likes: a viewer arrived after YouTube's system mistook Kurzgesagt itself for slop.
- *Relevance:* viewers actively reward visible human authorship. This supports rules 4, 5a and 11 (real-voice Engineer's note, real-voice switch, behind-the-scenes posts). It also supports the "Altered or synthetic content" tick: hiding AI use would cost the trust that these comments value.

**Brick Immortar, "Ego in Engineering: The Quebec Bridge Collapse"** (401K subscribers, 678K views, 5 years old; same story as our episode 1)
- No comment in the top 20 mentions AI or the narrator's voice. This is a human-narrated channel, so it says nothing about AI narration either way.
- The strongest emotion is about people, not steel. A 886-like comment: as an engineer the writer encouraged production workers to flag anything unusual, and dismissing workers because "you don't have an engineering degree" is foolish. A 510-like comment lists the lessons: workers are expendable, engineers are treated as right even when physics disagrees, managers rarely pay. Several tradespeople and engineers share their own experiences of being ignored.
- 3K-like comment: Canadian engineering graduates wear the Iron Ring on the little finger so it touches their drawings, as a reminder of this disaster. Another top comment links the creator's separate Iron Ring video.
- Praise: "professionalism", "meticulous research", "criminally underrated". A Quebec resident says the bridge is neglected today and the dead deserve better.
- *Relevance:* (1) our ep01 angle of the ignored warning and the Iron Ring is exactly what viewers respond to, but it is not new, so our telling must differ (the telegram, the 15 seconds, the Engineer's note). Rule 3 applies against this competitor. (2) Viewers add their own stories in the comments, which fits the "think about their own version" goal; end each episode with one question that invites it. (3) Research quality is named and rewarded.

**Creator Insider, "YouTube's Inauthentic Content Policy - Explained!"** (922K subscribers, 45K views, about 2 months old)
- Almost all top comments are from creators who were demonetised. The recurring points: the rules themselves are accepted; the automated detection is the problem, false flags hit work with human scripts, animation and voice; appeals get canned answers; no human review; a channel monetised for years was suddenly flagged; ads may still run on a suspended channel's videos.
- A 26-like comment says the policy contradicts itself: "no templates", yet a recurring series needs a format.
- *Relevance:* (1) Our recurring cast and fixed episode format sit close to what the detector may call "repetitive", even though the rules allow it. Rule 3 (vary the opening, structure and ending) and rule 5b are our defence. (2) Mitigation to add: keep a dated evidence folder per episode (fact sheet, script drafts, Indeepa's recordings, project files) so an appeal can show human authorship. (3) These are creators' claims, not YouTube's; they are unverified individually. The pattern across hundreds of comments is the signal.

### X (Twitter), read directly on 4 October 2026 (signed in by the user)

**Search "youtube inauthentic content faceless" (Top tab, 9 posts)**
- Mostly course sellers and fear-bait: "BREAKING" demonetisation waves, "appeal blueprint" bundles, unverifiable claims of "$10,000,000 deleted in one day" or "150 channels in a day". Engagement was low (4 to 92 likes). One post (21 likes) argues faceless channels will struggle in 2027 because supply is exploding.
- *Relevance:* treat X advice on this topic as marketing, not evidence. None of these claims was used. The only useful signal is that the fear is widespread and monetised by sellers.

**Gato Macabro Miedo (@MacabroGato), 31 May 2026, 262 likes, 132 replies**
- A Spanish horror-storytelling channel with 170K+ subscribers says it was demonetised for "inauthentic content" and that its appeal failed.
- @TeamYouTube replied the same day. After a manual review, it said a significant portion of the channel did not align with the policy on mass-produced content, and the channel stayed demonetised.
- Replies were viewers vouching that the content is original and high quality. One notes each video clearly takes real work.
- *Relevance:* (1) A storytelling channel with a real audience was still judged mass-produced even after manual review, so story niches are not safe by default. (2) Viewer support did not change the outcome. (3) This is the creator's account plus YouTube's reply; the channel's actual content was not reviewed here, so we cannot say whether the ruling was fair.

**Other TeamYouTube replies (June and September 2026)**
- Same wording each time: manual review, "significant portion" mass-produced. One creator (1 Sep) says they have project files, timelines, scripts and production records and asks whether they can submit them; that thread had no answer when read.
- *Relevance:* supports rule 5d (keep evidence), but it is not proven that evidence changes the result. Not a guarantee.

**New findings from this pass**

| # | Finding | Status | Evidence | So what |
| --- | --- | --- | --- | --- |
| 14 | Viewers reward visible human authorship and trust. | Verified | Kurzgesagt comments (107K, 24K and 9.1K likes) plus the earlier r/NewTubers horror-channel thread (finding 11). | Keep the real-voice Engineer's note; label AI use openly. |
| 15 | The audience for a disaster story reacts most to how workers were ignored, and shares personal stories. | Single source (one video's comments; consistent with the Iron Ring tradition) | Brick Immortar Quebec Bridge comments. | Build the emotional peak on the ignored warning; close with an open question. |
| 17 | Story channels are being flagged "mass-produced" even after YouTube's manual review. | Single source (one 170K-subscriber channel's account plus YouTube's replies on X; matches Creator Insider comments) | @MacabroGato thread and @TeamYouTube replies. | Differentiate each episode; do not rely on a story niche being safe. |
| 16 | Creators fear automated false flags more than the written policy. | Verified | Creator Insider comments plus the Next Web, Dexerto and Kotaku coverage of Kurzgesagt's false flag (already in sources). | Keep authorship evidence per episode; avoid mass production. |

## Sources opened

[Reddit (via Arctic Shift archive): production time](https://www.reddit.com/r/NewTubers/comments/1vteeja/) · [monetisation](https://www.reddit.com/r/NewTubers/comments/1vopp09/) · [is faceless good](https://www.reddit.com/r/NewTubers/comments/1vlhpax/) · [horror AI channel](https://www.reddit.com/r/NewTubers/comments/1vfw38j/) · [TechCrunch, Matt Halprin](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/) · [Quasa](https://quasa.io/media/youtube-inauthentic-content-buckets-explained-in-2026-interview) · [Tubefilter policy](https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/) · [Yahoo Tech](https://tech.yahoo.com/social-media/articles/youtube-reveals-ai-slop-videos-090000379.html) · [Hollywood Reporter](https://www.hollywoodreporter.com/business/digital/faceless-creators-youtube-ai-damage-1236617586/) · [The Next Web](https://thenextweb.com/news/youtube-ai-slop-crackdown-faceless-creators-collateral-damage) · [HackerNoon](https://hackernoon.com/youtubes-ai-slop-crackdown-cant-tell-a-directed-ai-film-from-a-bot-farm) · [Dexerto](https://www.dexerto.com/youtube/youtubes-ai-slop-detector-incorrectly-targets-kurzgesagt-as-other-creators-fear-same-fate-3395930/) · [Kotaku](https://kotaku.com/youtube-mistakenly-penalizes-popular-science-channel-kurzgesagt-for-ai-generated-slop-2000722702) · [Kurzgesagt video summary](https://my.infocaptor.com/hub/summaries/kurzgesagt-in-a-nutshell/ai-slop-is-killing-our-channel-_zfN9wnPvU0) · [HN thread 1](https://news.ycombinator.com/item?id=45504156) · [HN thread 2](https://news.ycombinator.com/item?id=49225764) · [Fall of Civilizations](https://en.wikipedia.org/wiki/Fall_of_Civilizations_(podcast)) · [MrBeast guide, Tubefilter](https://www.tubefilter.com/2024/09/17/mrbeast-internal-production-guide-leaked-key-points/) · [Simon Willison](https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/) · [PostLink TikTok](https://postlinkapp.com/blog/tiktok-creator-rewards-program) · [Ryan McBeth Substack](https://ryanmcbeth.substack.com/p/youtube-demonitized-my-latest-roundup/comments) · YouTube (comments read 4 Oct 2026): [Kurzgesagt](https://www.youtube.com/watch?v=_zfN9wnPvU0) · [Brick Immortar](https://www.youtube.com/watch?v=e4DTMe0huXM) · [Creator Insider](https://www.youtube.com/watch?v=14Vm0CiyUVE)
