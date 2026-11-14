# Usage: uv run python scripts/publish_scheduled.py assets/2026-11/posts.json
#        uv run python scripts/publish_scheduled.py assets/2026-11/posts.json --browser [--publish]

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings
from src.tools.linkedin_api import RealLinkedInClient

BROWSER_SCRIPT = Path(__file__).resolve().parent / "publish_carousel_browser.py"


def parse_args():
    parser = argparse.ArgumentParser(description="Publish due scheduled LinkedIn posts")
    parser.add_argument("schedule", type=Path)
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Route carousel posts through the Edge composer script instead of skipping them.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="With --browser: actually click Post (default: stops before it, screenshot only).",
    )
    return parser.parse_args()


def run_browser_day(day: int, publish: bool) -> tuple[int, str]:
    cmd = [sys.executable, str(BROWSER_SCRIPT), "--day", str(day)]
    if publish:
        cmd.append("--publish")
    proc = subprocess.run(cmd, cwd=str(Path(__file__).resolve().parent.parent))
    return proc.returncode, " ".join(cmd)


async def main() -> int:
    args = parse_args()
    schedule = json.loads(args.schedule.read_text(encoding="utf-8"))
    state_path = args.schedule.with_name("posted.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    now = datetime.now(UTC)

    due = []
    for post in schedule:
        if post["id"] in state:
            continue
        due_at = datetime.fromisoformat(post["date"])
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=UTC)
        if due_at <= now:
            due.append((post, due_at))

    if not due:
        print("No due posts.")
        return 0

    settings = Settings(env="development")
    client = RealLinkedInClient(
        settings.linkedin_access_token,
        settings.linkedin_author_urn,
        settings.linkedin_version,
    )
    try:
        for post, due_at in due:
            if post.get("format") == "carousel":
                day = post["day"]
                if not args.browser:
                    pdf = Path(post.get("pdf", ""))
                    if not pdf.is_absolute():
                        pdf = args.schedule.parent / pdf
                    state[post["id"]] = {
                        "status": "manual_attachment_required",
                        "pdf": str(pdf),
                        "noted_at": datetime.now(UTC).isoformat(),
                        "note": "Attach this PDF in the LinkedIn composer (or run with --browser).",
                    }
                    state_path.write_text(
                        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    print(f"MANUAL {post['id']} due {due_at.isoformat()} -> attach {pdf}")
                    continue
                rc, cmd = run_browser_day(day, args.publish)
                if rc != 0:
                    print(f"ERROR {post['id']}: browser publish failed (rc={rc}) via: {cmd}")
                    continue
                if args.publish:
                    state[post["id"]] = {
                        "status": "published_via_browser",
                        "day": day,
                        "published_at": datetime.now(UTC).isoformat(),
                    }
                    state_path.write_text(
                        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    print(f"PUBLISHED {post['id']} via browser at {due_at.isoformat()}")
                else:
                    print(f"DRY-RUN {post['id']}: composer filled, screenshot saved. Not posted.")
                continue
            image = Path(post["image"])
            if not image.is_absolute():
                image = args.schedule.parent / image
            post_id = await client.publish_image_post(
                post["caption"], str(image), post.get("image_title", "Anton Petnitsky")
            )
            state[post["id"]] = {
                "post_id": post_id,
                "published_at": datetime.now(UTC).isoformat(),
            }
            state_path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"Published {post['id']} at {due_at.isoformat()}")
    finally:
        await client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
