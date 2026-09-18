# The Ad Spec (`ad.json`)

One file describes one ad and every file it produces. The builder writes it after the script gate. A full example is in `examples/sample-ad/ad.json`.

## Top level
| Key | What it holds |
|---|---|
| `name` | Ad name, used for the folder |
| `product` | Folder name under `products/`. Brand colors, font, and logo come from its `brand.json`. |
| `playbook`, `patterns` | Which playbook and which pattern IDs the ad uses |
| `voice` | Default voice: id, model, settings. Speed at most 1.15. |
| `voices` | Named voices, for example `daniel` and `sarah`. A deliverable picks one with `voice`. |
| `scenes` | Every scene, keyed by id |
| `deliverables` | Named orderings of scenes with a duration: the hook variants and the cutdowns |
| `kit` | The files to produce: deliverable, format, folder, optional fps |
| `ad_text` | Headlines of at most 40 characters and descriptions of at most 35 |
| `music` | Optional path to a licensed track |

## Every scene has
- `type`: one of the types below.
- `bg`: a color role from the brand: `dark`, `primary`, `accent`, `soft1`, `soft2`.
- `vo`: the voice line for this scene. One clause. Optional only for scenes used in silent deliverables.
- `hold`: seconds the scene stays in a silent deliverable. Ignored in voiced ones.
- `cues`: optional. Names mapped to a word in `vo`. Elements that reference the name land on that word.

## Scene types
| Type | Fields | Pattern | 16:9 | 9:16 | 1:1 |
|---|---|---|---|---|---|
| `hook-text` | `text`, optional `typeAt`, `typeDur` | A1, A2, E5 | Large typed line, logo top-left | Same, narrower | Same |
| `text-card` | `text` with `*keyword*` for the accent word | D7, C6 | Centered big text | Same | Same |
| `pivot` | `from`, `chips` (two), `tag` | C1 | Chips left and right of the agent disc | Stacked | Stacked |
| `conversation` | `channel`, `messages` (`who`, `meta`, `text`, `bot`, `cue`), `badge` (`text`, `cue`) | D4 | Wide card | Full-width card | Full-width card |
| `workflow` | `title`, `steps` (`title`, `sub`, `cue`), three or four | D8, E2 | Row with connectors | Stack with connectors | Two-by-two grid |
| `pills` | `title`, `items` (`label`, `cue`, `dark`), five at most | D5 | Centered column | Full-width column | Full-width column |
| `number` | `value`, `suffix`, `label`, `source`, `cue` | I1, E4 | Huge count-up | Same | Same |
| `shield` | `layers`, `label` | I4 | Layers build in | Same | Same, smaller |
| `closer` | `line`, `button`, `url` | B5, E10, H2 | Logo, line, button, address. Fully still. | Same | Same |

Text fields accept `**bold**`. `text-card` also accepts `*keyword*`.

Screenshot scenes are not in the engine yet. In screenshot mode, add a `screenshot` type before use: image path, crop, and a pan or scroll direction.

## Deliverables
```json
"30s-hookA": { "duration": 30, "scenes": ["hookA", "pivot", "convo", "flow", "pills", "number", "shield", "closer"], "hook_pattern": "A1 pain question" }
```
The last scene must be a `closer`. Give every hook variant a `hook_pattern` so the campaign plan can say what it is betting on.

Every deliverable also carries `concept` (a short name shared by all versions of one story) and `voice` (a key from `voices`). A text-driven version sets `"silent": true`; its scenes then use `hold` instead of voice timing, it gets no captions, and its music is mixed alone.

```json
"30s-proof":  { "duration": 30, "scenes": ["hookB", "pp", "pf", "pa", "ps", "closer"], "concept": "proof-led", "voice": "sarah" },
"30s-silent": { "duration": 30, "scenes": ["t1", "t2", "convo", "flow", "number", "pills", "t7", "closer"], "concept": "silent-scroller", "silent": true }
```

## Kit
```json
{ "d": "30s-hookA", "fmt": "1x1", "folder": "formats", "fps": 25 }
```
The first kit entry is the master. It is the one reviewed at the silent concept gate and the one the thumbnail is taken from.

## Tool stages
Run from the project root: `python tools/build.py <ad-folder> <stage>`
| Stage | What it does | Cost |
|---|---|---|
| `check` | Validates the spec, prints word budgets, flags long scripts and late brand mentions | Nothing |
| `plan` | Estimated timeline per deliverable | Nothing |
| `player` | Writes `working/player.html`, which plays any deliverable in any format | Nothing |
| `stills --d <deliverable> --fmt <format>` | One still per scene, plus an overflow check | Seconds |
| `master` | Silent render of the first kit entry | About 3.5 minutes for 30 seconds |
| `voice [--only <deliverable>]` | Generates the voice, re-times scenes and cues to the real speech, writes captions. Stops if any deliverable runs long. | Voice characters. Identical lines are generated once. |
| `kit [--only <deliverable>:<format>]` | Renders and finishes the files, writes thumbnail, ad text, and the report | About 7 seconds of render per second of video |
