# Audience Research Output Contract

`/audience-research` writes a file named `research-<segment-slug>.md`. `/video-ad-builder` reads it to pre-fill the questionnaire. Every heading below must be present, in this order, even if a section says "not found."

```markdown
# Audience research: <segment name>

## Segment
One paragraph. Role, company type, company size, tools they live in.

## Sources reached
Bulleted list of source name, URL, date accessed, and how many items were read. Sources that could not be reached are listed under "Not reached" with the reason.

## Top pains (ranked)
1. <pain>. Evidence: <paraphrased summary>, <source>.
2. ...
Five maximum. Each pain has at least one cited source.

## Language they use
Ten to fifteen short phrases in the buyer's own vocabulary, paraphrased, no direct quotes longer than eight words. Grouped by theme.

## Objections and fears
What stops them from buying or switching. Three to five items, each cited.

## Trust signals they respond to
What makes them believe a vendor. Security, integrations, peer references, hard numbers, and so on. Cited.

## Buying triggers
Events that make them look for a solution now. Cited.

## Recommended message angle
One paragraph. The single problem to lead with, the promise, and the proof that would land.

## Suggested questionnaire answers
- Purpose: <one line>
- Audience: <one line>
- Tone: <one word or two>
- Key message: <one sentence>
- Capabilities to feature: <two to four, mapped to pains above>
- Hook style: <pattern ID and why>
- Trust devices: <pattern IDs and why>
- Call to action style: <pattern ID and why>
```

## How the builder maps this file to the questionnaire

| Questionnaire item | Filled from |
|---|---|
| 4. Describe the ad | Recommended message angle plus Key message |
| 5. Purpose and audience | Purpose plus Audience plus Segment |
| 6. Tone | Tone |
| 7. Capabilities to feature | Capabilities to feature, cross-checked against the product folder |
| Pattern selection | Hook style, Trust devices, Call to action style |

Items 1, 2, 3, 8, 9, and 10 are never filled from research. Items 8 and 9 may be filled from the skill's own inputs (channel, length, voice) if they were passed on the command line.
