# Production Rules

Rules learned from shipping ads. They apply to every ad the builder makes. When rules conflict, follow the hierarchy of authority.

## Hierarchy of authority

1. **Product brand** (`products/<name>/brand-spec.md` and `brand.json`). Colors, fonts, timings, tone. Locked.
2. **These production rules.** Layout, audio, output.
3. **Playbook** (`references/playbooks/*.md`). Structure and craft for the chosen ad type.
4. **Pattern library** (`references/pattern-library.md`). Style and motion vocabulary. Inspiration only. A pattern never overrides a brand color, a timing, or a voice choice.

## One spec, many files

An ad is one file, `ad.json`. It holds the scenes, the voice lines, the hook variants, the cutdowns, and the list of files to produce. The engine draws any scene in 16:9, 9:16, or 1:1, so a scene is written once. See `references/ad-spec.md`.

**Default output is the full kit, a creative bank, not one idea in eight sizes:**
| Folder | Files |
|---|---|
| `master/` | Each concept's 30 second version in 16:9. The first narrated concept appears three times, once per opening. |
| `formats/` | The first concept's hook A in 9:16 and in 1:1 at 25 fps. The other concepts in the shapes their placement needs, for example the silent version in 9:16 and 1:1. |
| `cutdowns/` | 15 seconds in 16:9 and 9:16, and a 6 second bumper in 16:9, from the first concept |
| `upload/` | One caption file per voiced deliverable, thumbnail, ad text at platform limits |
| `working/` | Player page, voice clips, timelines, silent renders, stills, reports |
| root | `ad.json`, `QUESTIONNAIRE.md`, `CAMPAIGN-PLAN.md`, `RUN-LOG.md`, `index.html`, the review pages |

**Concepts.** The recommended mix is three: a narrated demo built on a moment, a proof-led version built on numbers and breadth, and a silent text-driven version for muted feeds. A customer story is offered only when footage exists. The user can choose any subset.

**Voices.** One voice per concept, so the bank does not sound like one reader. The voice never changes between the openings of one concept, because the opening test must measure the opening. The silent concept has no voice and its music sits higher, at minus 16 LUFS.

Vertical and square versions of hooks B and C are not rendered by default. Once the test names a winner, add two lines to the kit and rerun.

## Hook variants

- Three by default. Each is a different opening on the same body. Everything after the hook is identical, so a test isolates the hook.
- Each variant uses a different hook pattern from the library. Do not write three versions of the same idea.
- A hook may reuse a body scene as the opener, for example the number. When it does, drop that scene from the body of that variant.
- Every variant must get the brand name spoken, and on screen, before second five. The check stage enforces the spoken part.
- State what each hook is betting on in `CAMPAIGN-PLAN.md`.

## Cutdowns

- **15 seconds:** hook, one proof scene, the number, the closer. Lines are rewritten shorter, not sped up.
- **6 second bumper:** the number and the closer. One line of voice, the brand name as the last word.
- Cutdowns reuse the master's scenes wherever the line can stay the same, so the voice is generated once.

## Two material modes

The builder checks `products/<name>/screenshots/` and declares the mode in `SCRIPT.md`.

**Screenshot mode.** At least one real product screenshot exists.
- Feature scenes maximize screenshot area: accent background, white pill title top-left, the screenshot filling the rest.
- Screenshots large and focused. Pre-crop to the zone of interest. Do not zoom with code.
- Scenes must move: pan, scroll, or crossfade. Never static.
- Real materials only. Do not draw a fake version of a screen when a real one exists.

**Illustrated mode.** No screenshots in the folder.
- The product story is told with typography and illustrated cards: conversation, workflow, pills, number, shield, text card.
- Cards may suggest the product's shape and flow. They should not be built to pass as a real screenshot. Keep them clearly designed: rounded cards, simplified controls, no browser chrome, no logos of tools the product does not integrate with.
- Public imagery from the product's own website may be used as is. Note the source in the storyboard.
- Any number on screen comes from the product brief or a public claim, or is marked illustrative. Never invent a customer result.
- Tell the user once, at the start, that the run is in illustrated mode and why.

## Layout

The engine owns layout. Safe margins are built in:
- 16:9: 5 percent on all sides.
- 9:16: 10 percent on the sides and top, 20 percent at the bottom, where platform buttons and captions sit.
- 1:1: 7.5 percent on all sides.

The stills stage reports any element that spills outside the frame. A spill fails the gate.

Logo and web address appear only on the opener and the closer. Never on feature scenes. No captions on product scenes in a narrated ad.

## Voice and timing

- **Plan at 2.1 words per second** for generated voices, pauses included. The craft target for a human read is 2.5 to 2.7. The check stage prints a word budget per deliverable.
- **Check timing before the first render.** `check` and `plan` cost nothing. `voice` costs a few hundred characters and must pass before any render.
- If a deliverable runs long, shorten the lines. Speed is not a setting on the current model.
- If the closer would hold much longer than its target, the script has room. The plan says how many words.
- One clause per scene. Cuts land just before each line. Cues land on their words. The voice stage does both from the real audio.
- Never read the web address aloud.
- Voice model `eleven_v3` with the American recommended mix in `references/voices.md`. One delivery tag at most per line, only where the read needs a push. Tags are never spoken and are stripped from captions.
- Music at about 18 percent under the voice, fading out over the last 1.2 seconds. Two-pass loudness to minus 14 LUFS, true peak at or under minus 1.5.
- Music comes from the workspace library `music/library.json`, chosen per concept by mood: `music` on each deliverable names a mood (calm, confident, upbeat, warm, tense) or a file. Different concepts get different tracks. If the library is empty, a placeholder bed is used and every report says so; `tools/music.py` fills the library with free tracks.
- A product may still carry its own track in `products/<name>/audio/`; it wins over the library when no mood is set.

## Frame rates
- YouTube files: 30 fps.
- LinkedIn files: 25 fps. LinkedIn asks for under 30.

## Stops and checks
One stop: the summary after the questionnaire. Nothing is written or rendered before the go. After it, the builder runs to the finished kit without asking again, and checks itself instead:
1. The timing check must pass for every deliverable before any voice or render.
2. Stills of every deliverable are captured and looked at. Any overflow or layout problem is fixed before rendering.
3. Two finished files are spot-checked for sync at a cue time.
4. The script page and the concept page are written into the folder as a record of the decisions, so anyone can review after the fact.

Careful mode, on request: stop at the script page and at the silent master before spending voice quota and render time.

Missing material stops the run. If a brand file, a product brief, or a required asset is missing, ask for it. Never guess a brand color or invent a feature.

## Output
- No burned-in subtitles unless asked. Caption files are always written.
- `RUN-LOG.md` records mode, sources, gates passed, voice characters used, render times, and every flag raised.
- `working/kit-report.json` lists every file with size, frame rate, duration, loudness, and music status.
