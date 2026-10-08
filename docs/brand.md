# Held Together — brand system

One rule holds the whole channel together: **the present is photographed, the past is painted.**
A viewer should know within half a second which world they are looking at, and should
recognise a frame from this channel without seeing the name.

Nothing in this document changes between episodes. If a new episode needs something not
described here, add it here first.

---

## 1. The three layers

| Layer | What it is | Look | Who lives there |
| --- | --- | --- | --- |
| **The studio** | The podcast. Now. | Photoreal portrait photography, 85mm, shallow depth of field | Elias, Maya |
| **The story** | The historical events | Painted narrative illustration (below) | Tom, Sam, Ruth, Walter, and every historical scene |
| **The explainer** | How the engineering works | Flat bright HTML/CSS motion graphics | No people — steel, forces, diagrams |

### The studio is permanent

The podcast room is as fixed as the hosts' faces, defined once in `cast/cast.yaml`
(`studio:`) in plain measurements: walnut panelling, deep teal acoustic panels, a round walnut
table about 1.2 m across, **a black broadcast microphone on a short desk stand in front of
each host** (no boom arms: fewer moving parts, less variation), a brass banker's lamp at the
centre, a shelf of engineering objects. **Elias always sits left, Maya right.**

**Studio pictures are edits, not new drawings.** The cast stage draws the empty room once,
then one approved *master frame* per camera with the hosts seated in it
(`cast/studio/<camera>.jpg`). Every studio scene is an edit of its camera's master: only the
expression, hands and any prop change. Room, seating, microphones, lens, framing and the
hosts' proportions are copied, so they cannot drift and pictures rarely need redrawing.

**The camera rig is fixed, like a real filmed podcast.** Tripods at seated eye level, each
with its own lens: A wide two-shot (35 mm), B Maya's single (85 mm), C Elias's single
(85 mm), D over Elias's shoulder (50 mm), E over Maya's shoulder (50 mm), F table insert
(100 mm macro). Each studio scene names one (`camera:`). The hosts sit naturally at their
microphones; emotion comes from face and hands. Dramatic angles belong to the painted past.

**Only Elias and Maya ever exist in the studio**, and prompts say so positively (listing
what must not appear tends to make the model draw it). A vision model then checks every
studio still and clip against both reference sheets, the wardrobe and the expected framing;
an unknown person, wrong clothes, a missing host, anyone standing or a boom-arm microphone
gets it thrown away and redrawn once, then reported.

The hosts wear the same signature clothes every episode (`wardrobe:`): Elias a charcoal
waistcoat over a white collarless shirt, Maya an amber linen overshirt over a white
T-shirt. An episode may change the *colours* of those clothes (`wardrobe:` in
`episode.yaml`); the garments and everything else stay. The troupe changes costume freely.

The explainer layer belongs to Maya's world: it is the modern analysis laid over the past.
That is why it is clean and bright rather than painted.

---

## 2. The painted style — and why this one

**Golden-age narrative illustration**: the bold, dramatic painted storytelling of roughly
1900 to 1930 — the illustrated magazines and industrial murals that were being made *at the
very time our stories happen*.

Chosen over the alternatives for four reasons:
1. **Period truth.** It is the visual language of the era we depict, so it never feels like a
   filter applied to history. It feels like history's own picture of itself.
2. **Industry suits it.** That tradition painted dockyards, furnaces, steel and working men
   with genuine grandeur. Our subject matter is its subject matter.
3. **Emotional range.** It carries heroic construction and sombre aftermath equally well,
   which a flat poster style cannot.
4. **Ownable.** Nobody in the engineering-story niche is working in it.

**The rules of the style**
- Visible, confident brushwork and palette-knife texture; canvas tooth showing in flat areas
- One strong light source, dramatic and directional; deep shadows with colour in them, never
  black
- Warm light against cool shadow — amber and gold against teal and slate
- Rich saturated colour, bright overall; luminous skies
- Heroic low camera angles for construction, eye level for people, high and still for grief
- Figures read as silhouettes first
- Simplified detail: suggested, not drawn tight; faces carried by light and gesture
- No outlines, no cel shading, no flat vector, no cartoon exaggeration

---

## 3. Palette

| Role | Colour | Used for |
| --- | --- | --- |
| Ink | `#11161F` | Type, structure lines |
| Paper | `#F7F9FC` | Explainer background |
| Crimson | `#E8192C` | Force, danger, failure, the accent |
| Amber | `#FFB020` | Warning, the growing bend, warm light |
| Teal | `#0A84FF` → deep `#2F4D78` | The correct case, shadow, water |
| Steel | `#CBD4E0` → `#4A5362` | Metal |

Amber and teal appear in the same frame in both worlds. That is the thread that ties the
photoreal studio to the painted past.

## 4. Type

- **Montserrat ExtraBold / Black** — titles, big numbers, name cards
- **Inter SemiBold / Regular** — labels, captions, everything else

Never substitute. These two carry the channel's identity as much as the palette does.

## 5. Motion

- Something changes visually every 5–7 seconds; a larger interrupt every 30–60 seconds
- Titles type on word by word; numbers pop; captions wipe
- Scenes cut between two or three angles rather than holding one slow zoom
- Hero moments are animated from our own stills, so the cast performs

## 6. Disclosure

Every upload ticks "Altered or synthetic content". Elias is labelled on screen as a composite
character. The channel never implies its hosts are real people.
