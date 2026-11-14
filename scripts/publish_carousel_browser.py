"""Publish a carousel post to LinkedIn through Anton's logged-in Edge profile.

The Share on LinkedIn API app cannot register the document recipe
(verified: registerUpload feedshare-document -> 403 ACCESS_DENIED),
so carousels must go through the web composer. This script drives that
composer via Playwright + the installed Microsoft Edge (channel="msedge"),
reusing a persistent profile so no login is needed after the first manual
sign-in.

Default mode is a DRY RUN: it opens the composer, pastes the caption,
attaches the PDF, and stops before the "Post" button, saving a screenshot
next to the PDF. Pass --publish to click the real "Post" button.

Usage:
  uv run --with playwright python scripts/publish_carousel_browser.py --day 1
  uv run --with playwright python scripts/publish_carousel_browser.py --day 1 --publish
  ... --profile "D:\\Projects\\opencode-chrome\\.edge-profile"   # default

One-time setup: open that profile (or any Edge profile you control), sign in
to LinkedIn manually once, then close the browser and run this script.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_JSON = ROOT / "linkedin_assets" / "30-days" / "posts.json"
DEFAULT_PROFILE = Path(r"D:\Projects\opencode-chrome\.edge-profile")

# Locale-tolerant candidates. LinkedIn ships en / ru / be UI; we try both.
START_POST = [
    '[aria-label*="Start a post" i]',
    '[aria-label*="Начать публикацию" i]',
    'button:has-text("Start a post")',
    'button:has-text("Начать публикацию")',
]
CAPTION = [
    'div.ql-editor[contenteditable="true"]',
    '.ql-editor[contenteditable="true"]',
    'div[role="textbox"][contenteditable="true"]',
]
DOCUMENT = [
    'button[aria-label*="document" i]',
    'button[aria-label*="документ" i]',
    'button:has-text("Add a document")',
    'button:has-text("Добавить документ")',
]
POST_TEXTS = ["Post", "Опубликовать", "Publicar", "Publier"]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_post(day: int) -> dict:
    posts = json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    for post in posts:
        if post["day"] == day:
            return post
    raise SystemExit(f"day {day} not found in {POSTS_JSON}")


def wait_for_first_visible(page, selectors, timeout_ms: int):
    """Poll until one of the selectors resolves to a visible element; None if never."""
    tries = max(1, timeout_ms // 250)
    for _ in range(tries):
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return loc, sel
            except Exception:
                continue
        page.wait_for_timeout(250)
    return None, None


def save_screenshot(page, pdf: Path, tag: str) -> Path:
    out = pdf.with_name(pdf.stem + "_" + tag + ".png")
    page.screenshot(path=str(out))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--day", type=int, required=True, help="carousel day from posts.json (1-30)")
    ap.add_argument("--publish", action="store_true", help="actually click Post (default: stop before it)")
    ap.add_argument("--headless", action="store_true", help="run without a visible window (NOT recommended)")
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE, help="Edge user-data-dir with LinkedIn session")
    args = ap.parse_args()

    post = load_post(args.day)
    pdf = ROOT / "linkedin_assets" / "30-days" / post.get("pdf", f"carousels/day{args.day}/day{args.day}.pdf")
    if not pdf.is_file():
        raise SystemExit(f"PDF not found: {pdf}")
    caption = post["caption"]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "playwright not installed. Run: uv run --with playwright python scripts/publish_carousel_browser.py ..."
        )

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(args.profile),
            channel="msedge",
            headless=args.headless,
            viewport={"width": 1400, "height": 900},
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            log("opening LinkedIn feed…")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2_000)

            if "login" in page.url or "authwall" in page.url:
                shot = save_screenshot(page, pdf, "authwall")
                log(f"NOT LOGGED IN — screenshot: {shot}")
                log("Sign in to LinkedIn once in that profile, then re-run.")
                return 2

            log("opening post composer…")
            start, sel = wait_for_first_visible(page, START_POST, 15_000)
            if start is None:
                shot = save_screenshot(page, pdf, "composer_missing")
                log(f"could not find 'Start a post' — screenshot: {shot}")
                return 3
            start.click()
            page.wait_for_timeout(1_500)

            field, sel = wait_for_first_visible(page, CAPTION, 15_000)
            if field is None:
                shot = save_screenshot(page, pdf, "caption_missing")
                log(f"caption field not found — screenshot: {shot}")
                return 4
            field.click()
            try:
                field.insert_text(caption)
            except Exception:
                page.keyboard.insert_text(caption)
            log(f"caption inserted ({len(caption)} chars)")

            doc, sel = wait_for_first_visible(page, DOCUMENT, 10_000)
            if doc is None:
                shot = save_screenshot(page, pdf, "document_missing")
                log(f"document button not found — screenshot: {shot}")
                return 5
            with page.expect_file_chooser(timeout=15_000) as chooser_info:
                doc.click()
            chooser_info.value.set_files(str(pdf))
            log(f"uploading {pdf.name} …")
            page.wait_for_timeout(10_000)

            shot = save_screenshot(page, pdf, "ready")
            log(f"composed, not posted — screenshot: {shot}")

            if not args.publish:
                log("DRY RUN: stopping before the Post button. Re-run with --publish to publish.")
                return 0

            posted = False
            for text in POST_TEXTS:
                loc = page.locator(f'button:has-text("{text}")').first
                try:
                    if loc.count() > 0 and loc.is_visible() and loc.is_enabled():
                        loc.click()
                        posted = True
                        log(f"clicked Post ({text!r})")
                        break
                except Exception:
                    continue
            if not posted:
                log("Post button not found/enabled — not clicking anything.")
                return 6
            page.wait_for_timeout(8_000)
            shot = save_screenshot(page, pdf, "published")
            log(f"published. screenshot: {shot}")
            return 0
        finally:
            ctx.close()


if __name__ == "__main__":
    sys.exit(main())
