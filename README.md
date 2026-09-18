# Video Ad Builder

A Claude Code skill that turns a brief, or ten short answers, into a paid-media video ad kit. You answer questions. It writes, times, voices, renders, and checks. You get a folder of finished files and a one-page campaign plan.

**What you get from one run**

| | |
|---|---|
| Creative concepts | A narrated demo built on a moment, a proof-led version built on numbers, and a silent text-driven version for muted feeds. Each with its own voice. |
| Openings to test | Three different first-five-seconds on the same body, so the platform can tell you which hook works. |
| Shapes | Widescreen for YouTube, vertical for Shorts, square at 25 fps for LinkedIn. Real layouts, not crops. |
| Cutdowns | A 15 second version and a 6 second bumper for sequencing. |
| Uploads | Captions for every version, thumbnail, headlines and descriptions within platform limits. |
| Plan | A campaign plan with a "Done when" bar, the hook test, the sequence, targeting inputs, and a claims table. |

Everything is built from the product's public brand cues and its own claims. Nothing is invented and passed off as real. What is illustrative is marked so.

## Quick start

You need Node.js 18 or newer, Python 3.10 or newer, and ffmpeg.

```bash
git clone https://github.com/Yuval-EL/video-ad-builder
cd video-ad-builder
python tools/setup.py
```

Setup installs the browser engine, prepares a workspace, and runs a check that tells you in plain words if anything is missing.

Then, in Claude Code:

```
/plugin marketplace add Yuval-EL/video-ad-builder
/plugin install video-ad-builder@yuval-plugins   # the plugin's dependencies install on their own
/video-ad-builder
```

Without a marketplace, from any folder you want to work in:

```bash
python <path-to>/video-ad-builder/tools/install-local.py
```

That writes the skill into the folder's `.claude/skills/` and `/video-ad-builder` works there.

## Music

Setup fetches a small library of free tracks by mood from Mixkit, licensed for commercial video with no attribution. The builder picks a different track per concept. Add your own tracks to `music/` any time, or a product's own track to its `audio/` folder.

## Voice

Voiced ads use ElevenLabs. The free plan covers about twenty 30 second voiceovers a month.

1. Create an account at elevenlabs.io.
2. Profile, then API Keys, then Create. Give it Text to Speech, Voices, and User permissions.
3. Put the key in your workspace: a file named `.env` containing `ELEVENLABS_API_KEY=your_key`.

The key never leaves your machine and is never printed. Silent, text-driven ads need no key at all.

## How a run feels

1. **Check.** The first run checks the machine and offers a demo that builds a finished ad in about two minutes.
2. **Start.** Freestyle, ten short questions. Or share a brief you already have, confirm what the builder took from it, and answer three guiding questions.
3. **Summary.** One screen. Say go.
4. **Done.** About fifteen minutes later the kit page opens with every file playing, the plan underneath, and any flags in plain words.

Afterwards, "make hook B the master and give me its vertical" renders just that.

## Where things live

- The plugin folder holds the engine, the tools, and the sample. It is never written to by a run.
- Your workspace, the folder you open Claude Code in, holds `products/` (one folder per product, built from its website), `output/` (one folder per ad), and `.env`.

## Adding a product

Give the builder a website address. It reads the public page, pulls colors, font, logo, claims, and the call to action, and shows a brand card to confirm. Drop screenshots into the product's `screenshots/` folder and the builder switches from illustrated cards to real screens.

## Cost and time on a typical laptop

| | |
|---|---|
| Your time | Ten answers, one go |
| Build time, full kit | 12 to 15 minutes, unattended |
| Voice quota, full kit | About 900 characters |
| Render speed | About 3 seconds of work per second of video |

## What it will not do

- Invent a customer result, a metric, or an integration.
- Draw a card that could pass as a real screenshot of the product.
- Read a web address aloud, burn in subtitles unless asked, or ship without a claims table.

## License

MIT.
