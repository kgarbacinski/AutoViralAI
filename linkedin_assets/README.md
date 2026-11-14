# LinkedIn assets

## Output

- `2026-11/` — first four published posts (3 image posts published 2026-11-14, 1 text post).
- `30-days/` — the 30-day personal-brand plan. `posts.json` is the machine-readable
  schedule, `posts.md` the human-readable version. Images in `30-days/images/`.

## Days 1–3 are carousels

`30-days/carousels/day{1,2,3}/`

- `NN.png` — one 1080×1350 slide each (dark board, 10 slides).
- `dayN.pdf` — the multi-page file to attach. Slides are numbered, so the deck
  works without captions.

**Publishing requires manual attachment.** The LinkedIn app (`Mukller`, Share on
LinkedIn product, scopes `openid profile w_member_social`) cannot register the
document recipe: `registerUpload` with `feedshare-document` (and `feedshare-pdf` /
`feedshare-native-document`) returns `403 ACCESS_DENIED`. Image recipes (`feedshare-image`)
work fine. Until the app is upgraded (Community Management API + company page + vetting —
not available to a personal profile), the PDF must be attached by hand in the
LinkedIn post editor when publishing those three days. `scripts/publish_scheduled.py`
skips carousel entries and writes a `manual_attachment_required` marker into
`posted.json` instead of attempting an API upload.

The caption goes in the post text; the PDF carries the slides.

Alt text for accessibility is in `posts.json` (`alt_text`).

## Regenerating the carousels

```powershell
python linkedin_assets/30-days/generate_carousels.py
```

Uses PIL from the system Python (the uv venv has no Pillow). Arial/Consolas from
`C:/Windows/Fonts/`. The generator is data-driven: slide copy lives in the `DECKS`
dict; layout primitives (`cover`, `head_body`, `two_box`, `steps`, `terminal`,
`stats`, `checklist`, `quote`, `cta`) live in `render_slide`. If a new deck is
added, re-check layout overflow after editing — several layouts autosize panels
to the copy length.

Nothing here is published automatically. Publishing on the scheduled dates is
explicitly gated by `scripts/publish_scheduled.py` and Anton's approval per post.
