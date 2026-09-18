# Voices

Stock voices on the free voice plan, checked 2026-09-18. Ids are stable. The questionnaire lists these with the one-line description; the recommended mix is the top option.

## Recommended mix, American, one voice per concept
| Concept | Voice | Id | Why |
|---|---|---|---|
| Narrated demo | Eric, smooth and trustworthy | `cjVigY5qzO86Huf0OWal` | Calm authority without sounding like a newsreader |
| Proof-led | Sarah, mature and reassuring | `EXAVITQu4vr4xnSDxMaL` | Numbers land better in a reassuring register |
| Third concept or cutdowns | Brian, deep and resonant | `nPczCjzI2devNBz1zQrb` | Contrast with the other two |

## All American voices
| Voice | Id | Register |
|---|---|---|
| Eric | `cjVigY5qzO86Huf0OWal` | Smooth, trustworthy, middle-aged male |
| Sarah | `EXAVITQu4vr4xnSDxMaL` | Mature, reassuring, confident female |
| Brian | `nPczCjzI2devNBz1zQrb` | Deep, resonant, comforting male |
| Chris | `iP95p4xoKVk53GoZ742B` | Charming, down to earth male |
| Will | `bIHbv24MWmeRgasZH58o` | Relaxed optimist, young male |
| Matilda | `XrExE9yKIg1WjnnlVkGX` | Knowledgeable, professional female |
| Jessica | `cgSgspJ2msm6clMCkdW9` | Playful, bright, warm female |
| Bella | `hpp4J3VqNfWAUOO0d1Us` | Professional, bright, warm female |
| Roger | `CwhRBWXzGAHq8TQ4Fs17` | Laid back, casual, resonant male |
| River | `SAz9YHcvj6GT2YYXdXww` | Relaxed, neutral, informative |
| Liam | `TX3LPaxmHKxFdv7VOQHJ` | Energetic, young male |
| Bill | `pqHfZKP75CvOlQylNhV4` | Wise, mature, balanced male |
| Adam | `pNInz6obpgDQGcFmaJgB` | Dominant, firm male |
| Laura | `FGY2WhTYpPnrIDTdsKH5` | Enthusiast, quirky female |

## Other accents, offered only when asked
| Voice | Id | Accent |
|---|---|---|
| Daniel | `onwK4e9ZLuTAKqWW03F9` | British, steady broadcaster |
| George | `JBFqnCBsd6RMkjVDRZzb` | British, warm storyteller |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` | British, clear educator |
| Lily | `pFZP5JQG7iQjIQuC4Bku` | British, velvety |
| Charlie | `IKne3meq5aSn9XLyUdCD` | Australian, energetic |

## Model and delivery
- Model: `eleven_v3`. It returns word timestamps and it reads with intent. Settings: `{"stability": 0.5, "similarity_boost": 0.75}`. Speed is not a v3 setting; write shorter lines instead.
- Delivery tags go inside the voice line in square brackets and are not spoken: `[confident]`, `[warm]`, `[quiet]`, `[excited]`, `[pause]`. Use at most one per line, only where the read needs a push, for example on a single-word pivot: `[confident] Right there.`
- Tags are stripped from captions and word counts automatically.
- Plan word budgets at 2.1 words per second, as before. Measure the chosen voice on the first run and shorten if the check says so.

## Rule
One voice per concept. The voice never changes between the openings of one concept.
