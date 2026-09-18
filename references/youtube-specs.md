# YouTube Ad Specs

Pulled from Google's own help pages on 2026-09-16. The builder re-checks these pages at run time if the user asks for a spec refresh, and cites the page it used in SCRIPT.md.

## Sources
- About video ad specs: https://support.google.com/google-ads/answer/13547298
- Video ads specs and format requirements: https://support.google.com/google-ads/answer/17091270
- About video ad formats: https://support.google.com/google-ads/answer/2375464
- Video and audio formatting specifications: https://support.google.com/youtube/answer/4603579
- Video resolution and aspect ratios: https://support.google.com/youtube/answer/6375112
- Use square and vertical video: https://support.google.com/google-ads/answer/9128498
- YouTube Shorts ads asset specs: https://support.google.com/google-ads/answer/16041697

## Resolution and aspect ratio

| Orientation | Ratio | Recommended | Minimum acceptable |
|---|---|---|---|
| Horizontal | 16:9 | 1920 x 1080 | 1280 x 720 |
| Vertical | 9:16 | 1080 x 1920 | 720 x 1280 |
| Square | 1:1 | 1080 x 1080 | 480 x 480 |

Google states the player on the YouTube app adjusts automatically to ratios between 16:9 and 9:16. Do not add padding or black bars inside the file.

## Encoding

- Container: MP4 (Google lists MPEG-4 as recommended; MOV, WebM, ProRes and others are accepted).
- Video codec: H.264. Audio codec: AAC at 128 kbps or better.
- Frame rate: native, 24, 25, or 30 fps. Do not resample.
- Maximum file size: 256 GB.
- Builder default: 1920 x 1080, 30 fps, H.264 high profile, AAC 192 kbps, MP4.

## Duration by format

| Format | Skippable | Duration |
|---|---|---|
| Skippable in-stream | After 5 seconds | No maximum. Under 3 minutes recommended. |
| Non-skippable in-stream | No | 15 to 60 seconds depending on campaign subtype |
| Bumper | No | 6 seconds |
| In-feed | n/a | Any length. 15 to 20 seconds for awareness. |
| Shorts | Swipe to skip | Under 60 seconds recommended. Only the first 60 seconds play in the Shorts feed. 10 to 30 seconds recommended for action-oriented ads. |

Google's in-video spec sheet lists 15 seconds as the recommended length for in-video ads across 16:9, 9:16, and 1:1. Video action campaigns require at least 10 seconds.

## How the builder's lengths map

| Builder length | Fits |
|---|---|
| 15 seconds | Skippable in-stream, non-skippable in-stream (where 15 s is offered), in-feed, Shorts |
| 30 seconds | Skippable in-stream, non-skippable in-stream (where 30 s is offered), Shorts |
| 59 seconds | Skippable in-stream, Shorts (stays under the 60 s feed cutoff), in-feed |

## Craft consequences

- Skippable in-stream: the skip button appears at 5 seconds. Brand name and core promise must both land before 5 seconds. The hook is judged on whether it earns second six.
- Non-skippable: the viewer cannot leave, so pacing can breathe slightly, but the hook rules still apply because attention still leaves.
- A call to action overlay can appear at 3 or 10 seconds depending on campaign type. Do not put critical on-screen text in the lower left corner during those windows.
- Vertical safe area: keep logo, product, and text inside the central safe region on 1080 x 1920. Google's guidance is a reference image, not a number, so the builder keeps a 10 percent margin on all sides and 20 percent at the bottom for vertical.
- Horizontal safe area: keep text inside a 5 percent margin on all sides.

## Text assets that accompany the video

- In-video headline: 2 lines, 40 characters per line.
- Description: 2 lines, 35 characters per line.
- Thumbnail: 1280 x 720, JPG or PNG, under 2 MB.
- Companion banner: 300 x 60, under 150 KB.

The builder writes headline and description candidates into SCRIPT.md so they are ready for the campaign.
