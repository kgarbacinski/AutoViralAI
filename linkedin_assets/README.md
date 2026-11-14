# LinkedIn assets

## Output

- `2026-11/` — the four posts published manually on 2026-11-14
  (3 image posts + 1 text post; record of IDs in `2026-11/posted.json`).
- `30-days/` — the full 30-day personal-brand plan, **all posts are native
  document carousels**. `posts.json` is the machine-readable schedule,
  `posts.md` the human-readable one. Images in `30-days/images/` stay as
  cover fallbacks; carousels in `30-days/carousels/dayN/`.

## All 30 posts are carousels (10 slides each)

`30-days/carousels/dayN/` — `NN.png` per slide (1080×1350, Arial/Consolas),
`dayN.pdf` the file to post. Slide copy lives in `carousels_specs.py`
(data), the renderer in `generate_carousels.py`. Regenerate:

```powershell
python linkedin_assets/30-days/generate_carousels.py
```

## Publishing — why not the API

The Share on LinkedIn app (`Mukller`, product "Share on LinkedIn",
scopes `openid profile w_member_social`) **cannot register the document
recipe**. Verified 2026-11-14: `registerUpload` with
`feedshare-document` / `feedshare-pdf` / `feedshare-native-document` →
`403 ACCESS_DENIED` (with `supportedUploadMechanism: SYNCHRONOUS_UPLOAD`
on `rest/assets` the error is `Not enough permissions: partnerApiAssets`).
Image recipe works fine (200) — that is why 2026-11-14 posts are image posts.
Content analytics API is likewise blocked (`partnerApiSocialActions` /
`r_member_social`); the Community Management API requires a legal
organization + vetting and is unavailable to a personal profile.

So carousels go to the feed through the **web composer**, driven by
`scripts/publish_carousel_browser.py` (Playwright + installed Google Chrome;
`--browser chrome|chromium` to use Playwright's bundled Chromium instead;
persistent profile at `D:\Projects\opencode-chrome\.linkedin-profile` by
default — the Edge profile died with Edge, which Anton removed on 2026-11-14;
overridable with `--profile`).

```powershell
# dry-run: fill the composer, attach the PDF, stop BEFORE the Post button
uv run --with playwright python scripts/publish_carousel_browser.py --day 1

# actually publish (clicks the real "Post" button)
uv run --with playwright python scripts/publish_carousel_browser.py --day 1 --publish
```

One-time setup: run the script, sign into LinkedIn **manually once** in the
window that opens (use the default profile or `--profile`); the script reuses
the session afterwards.
If the session is dead it screenshots the auth-wall and exits with code 2.

Dry-run screenshots land next to the PDF (`dayN_ready.png`,
`dayN_published.png`); a failed composer selector likewise screenshots
(`dayN_*_missing.png`) and exits non-zero.

`scripts/publish_scheduled.py` — the daily scheduler. Without `--browser`,
due carousels are skipped as `manual_attachment_required` (nothing gets
posted). With `--browser`, due carousels are filled in the composer;
add `--publish` to actually click Post. Never assume it posted: check the
printed result and `posted.json`.

Manual fallback: open the composer in LinkedIn, paste the caption, attach
the PDF, click Post yourself. It takes about a minute.

## Cadence

2–3 posts per week (Tue / Thu / Sat, 11:00), one post per day maximum.
Posts are fenced by `scripts/publish_scheduled.py` + `posted.json`
(idempotent). Do not batch-publish: 2026-11-14 had 3 posts at once and
that was rolled back to the current cadence. Nothing publishes without
explicit approval; the scheduler only announces/publishes what is due.

## Metrics

Log impressions / saves / comments manually (the API cannot read them).
First 30–60 minutes after publishing decide the distribution window —
be online to reply to comments quickly.
