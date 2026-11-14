#!/usr/bin/env python
"""Generate 10-slide LinkedIn carousel decks (1080x1350).

Data-driven: each slide is a spec dict rendered by one of a few layout
primitives, so content can be reviewed without touching layout code.

Outputs per deck: PNG per slide in carousels/<deck>/ + a multi-page PDF.
The Share on LinkedIn API token cannot register the feedshare-document
recipe (403 ACCESS_DENIED), so the PDF must be attached manually in the
LinkedIn post editor. See README.md.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "carousels"
OUT.mkdir(parents=True, exist_ok=True)

A_B = "C:/Windows/Fonts/arialbd.ttf"
A_R = "C:/Windows/Fonts/arial.ttf"
C_B = "C:/Windows/Fonts/consolab.ttf"
C_R = "C:/Windows/Fonts/consola.ttf"


def font(size, bold=False, mono=False):
    return ImageFont.truetype(C_B if bold and mono else C_R if mono else A_B if bold else A_R, size)


def wrap(text, width):
    out = []
    for line in text.split("\n"):
        out.extend(textwrap.wrap(line, width, break_long_words=False, break_on_hyphens=False) or [""])
    return out


def draw_wrapped(d, xy, text, fnt, fill, max_width, gap=9, max_lines=None, center=False):
    x, y = xy
    lines = wrap(text, max(8, int(max_width / (fnt.size * 0.54))))
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        if center:
            w = d.textlength(line, font=fnt)
            d.text(((1080 - w) / 2, y), line, font=fnt, fill=fill)
        else:
            d.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


BG, PANEL, PANEL2, BLACK = "#0E161F", "#18232E", "#22313F", "#070C12"
TEXT, MUTED = "#F2F6FA", "#B4C3CF"
GREEN, RED, GOLD, BLUE = "#72E29B", "#FF8FA0", "#F5C978", "#8EC8FF"

FOOTER = "Anton Petnitsky  ·  Python / agents / backend"


def frame(label):
    im = Image.new("RGB", (1080, 1350), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1080, 14), fill=GOLD)
    d.text((66, 46), label.upper(), font=font(23, True), fill=GOLD)
    return im, d


def footer(d):
    d.line((66, 1250, 1014, 1250), fill=PANEL2, width=2)
    d.text((66, 1268), FOOTER, font=font(21, True), fill=MUTED)


def head(d, text, y=140, size=53):
    return draw_wrapped(d, (66, y), text, font(size, True), TEXT, 950, gap=9, max_lines=4)


def box(d, box_, text, fill=PANEL2, color=TEXT, size=25, pad=22, bold=True, gap=7):
    d.rounded_rectangle(box_, 18, fill=fill)
    x1, y1, x2, y2 = box_
    draw_wrapped(d, (x1 + pad, y1 + pad), text, font(size, bold), color, x2 - x1 - 2 * pad, gap=gap)


def arrow_down(d, x, y0, y1):
    d.line((x, y0, x, y1), fill=GOLD, width=6)
    d.polygon([(x, y1 + 2), (x - 13, y1 - 18), (x + 13, y1 - 18)], fill=GOLD)


def render_slide(spec):
    im, d = frame(spec["label"])
    kind = spec["kind"]

    if kind == "cover":
        y = head(d, spec["headline"], 250, 64)
        if spec.get("sub"):
            draw_wrapped(d, (66, y + 34), spec["sub"], font(28), MUTED, 950, gap=12)
        draw_wrapped(d, (66, 1180 - 60), "10 slides  ·  swipe", font(22, True), BLUE, 950, gap=8)

    elif kind == "head_body":
        y = head(d, spec["headline"], 150)
        body_end = y
        if spec.get("body"):
            body_end = draw_wrapped(d, (66, y + 26), spec["body"], font(30), TEXT, 950, gap=14)
        if spec.get("panel"):
            box_ = spec["panel"]
            panel_text = box_[0]
            lines = wrap(panel_text, max(8, int((1014 - 66 - 44) / (27 * 0.54))))
            panel_h = len(lines) * 34 + 44
            top = min(max(body_end + 70, 700), 1180 - panel_h)
            box(d, (66, top, 1014, top + panel_h), panel_text,
                box_[1] if len(box_) > 1 else PANEL2,
                box_[2] if len(box_) > 2 else TEXT, 27)

    elif kind == "two_box":
        head(d, spec["headline"], 150, 52)
        if spec.get("note"):
            draw_wrapped(d, (66, 300), spec["note"], font(23), MUTED, 950, gap=8)
        left, right = spec["left"], spec["right"]
        box(d, (66, 400, 500, 900), left["title"] + "\n\n" + left["body"],
            left.get("fill", PANEL), TEXT, 26, pad=26)
        box(d, (580, 400, 1014, 900), right["title"] + "\n\n" + right["body"],
            right.get("fill", PANEL), right.get("color", TEXT), 26, pad=26)
        if spec.get("left_tag"):
            d.text((110, 352), spec["left_tag"].upper(), font=font(20, True), fill=MUTED)
        if spec.get("right_tag"):
            d.text((624, 352), spec["right_tag"].upper(), font=font(20, True), fill=MUTED)
        if spec.get("caption"):
            draw_wrapped(d, (66, 950), spec["caption"], font(28, True), TEXT, 950, gap=13)

    elif kind == "steps":
        head(d, spec["headline"], 150, 52)
        steps = spec["steps"]
        n = len(steps)
        if n <= 4:
            box_h, gap, size, fgap = 128, 168, 26, 6
        elif n == 5:
            box_h, gap, size, fgap = 104, 130, 24, 5
        else:
            box_h, gap, size, fgap = 82, 106, 21, 4
        y = 315
        for i, step in enumerate(steps):
            last = i == len(steps) - 1
            box(d, (66, y, 1014, y + box_h), f"{i+1:02d}   {step}",
                GREEN if last else PANEL, BG if last else TEXT, size, pad=20, gap=fgap)
            if not last:
                arrow_down(d, 540, y + box_h, y + box_h + int(gap * 0.24))
            y += int(gap)
        if spec.get("caption"):
            draw_wrapped(d, (66, y - 10), spec["caption"], font(23), MUTED, 950, gap=9)

    elif kind == "terminal":
        head(d, spec["headline"], 150, 52)
        d.rounded_rectangle((66, 360, 1014, 360 + 84 * len(spec["lines"]) + 60), 18, fill=BLACK)
        y = 400
        for line in spec["lines"]:
            if line.startswith("$"):
                d.text((110, y), line, font=font(26, True, mono=True), fill=GREEN)
            else:
                d.text((110, y), line, font=font(24, mono=True), fill="#DCE5E9")
            y += 84
        if spec.get("body"):
            draw_wrapped(d, (66, y + 30), spec["body"], font(28, True), TEXT, 950, gap=13)

    elif kind == "stats":
        head(d, spec["headline"], 150, 52)
        stats = spec["stats"]
        n = len(stats)
        total_w = 1014 - 66
        gap = 24
        w = (total_w - gap * (n - 1)) // n
        x = 66
        d.rounded_rectangle((66, 380, 1014, 830), 18, fill=PANEL)
        for big, small in stats:
            d.text((x + 28, 430), big, font=font(76, True), fill=GOLD)
            draw_wrapped(d, (x + 28, 560), small, font(20), TEXT, w - 56, gap=6, max_lines=5)
            x += w + gap
        if spec.get("caption"):
            draw_wrapped(d, (66, 880), spec["caption"], font(22), MUTED, 950, gap=9)

    elif kind == "checklist":
        head(d, spec["headline"], 150, 52)
        y = 350
        for i, item in enumerate(spec["items"]):
            box(d, (66, y, 1014, y + 112), f"{i+1:02d}   {item}", PANEL, TEXT, 24, gap=6)
            y += 132
        if spec.get("caption"):
            draw_wrapped(d, (66, y + 8), spec["caption"], font(24, True), TEXT, 950, gap=10)

    elif kind == "quote":
        head(d, spec["headline"], 150, 52)
        q_lines = wrap(spec["quote"], max(8, int((1014 - 66 - 48) / (34 * 0.54))))
        q_h = len(q_lines) * 50 + 46
        box(d, (66, 430, 1014, 430 + q_h), spec["quote"], PANEL, GOLD, 34, gap=16)
        if spec.get("caption"):
            draw_wrapped(d, (66, 860), spec["caption"], font(26), MUTED, 950, gap=12)

    elif kind == "cta":
        head(d, spec["headline"], 210, 62)
        draw_wrapped(d, (66, 480), spec["body"], font(30), TEXT, 950, gap=15)
        box(d, (66, 1000, 720, 1110), spec["save"], GREEN, BG, 28)

    else:
        raise ValueError(f"unknown layout: {kind}")

    footer(d)
    return im


DECKS = {}

DECKS["day1"] = [
    dict(label="AI Agents · proof first · 1/10", kind="cover",
         headline="An agent says done. The page says otherwise.",
         sub="A 10-slide checklist for deciding an agent actually finished the job — not just that the pointer moved."),
    dict(label="AI Agents · the lie · 2/10", kind="head_body",
         headline="A click is an action, not a result.",
         body="The failure I see most often: the agent waits, clicks, and closes the ticket as done.\n\nThe request returned. The screen changed. The backend did nothing.",
         panel=( "The log says: OK.\nThe user still can't proceed.", RED, BG)),
    dict(label="AI Agents · the loop · 3/10", kind="steps",
         headline="Observe → act → assert.",
         steps=["Observe the current state before touching anything",
                "Take one deliberate action",
                "Assert the state changed as intended",
                "Only then claim success"],
         caption="No assert step = no finished task."),
    dict(label="AI Agents · two layers · 4/10", kind="two_box",
         headline="Two truth layers. Check both.",
         note="An agent reading only the page can be confidently wrong.",
         left_tag="Layer 1 · UI", left={"title": "What the page shows", "body": "Field updated?\nDialog closed?\nSpinner gone?", "fill": PANEL2},
         right_tag="Layer 2 · system", right={"title": "What the system did", "body": "Backend 200?\nRow persisted?\nklippy_state: ready?", "fill": GOLD, "color": BG},
         caption="Green UI + dead backend = false done."),
    dict(label="AI Agents · failure mode · 5/10", kind="head_body",
         headline="A green screen can hide a broken process.",
         body="I hit this with Klipper: Mainsail loaded fine, nginx returned 200 — and the printer itself had been in error state for hours.",
         panel=( "Check the process,\nnot the dress code.", PANEL2, TEXT)),
    dict(label="AI Agents · rule 1 · 6/10", kind="checklist",
         headline="Never accept 'done' without a named success condition.",
         items=["The field value after submit is the expected one",
                "The response status is 2xx and the payload matches the contract",
                "The persisted row exists and matches what was sent",
                "A reload shows the same state — not just the toast",
                "The log line exists and contains the entity ID",
                "A second run is idempotent, not a duplicate"],
         caption="Name the condition before you let the agent press the button."),
    dict(label="AI Agents · rule 2 · 7/10", kind="terminal",
         headline="Proof in code, not in a log line.",
         lines=["$ agent.run_task(task)", "before = page.locator(field).input_value()", "agent.click_submit()", "assert page.locator(field).input_value() != before", "assert db.saved(field.id) is not None"],
         body="Read, act, assert — the whole job fits in five lines."),
    dict(label="AI Agents · rule 3 · 8/10", kind="quote",
         headline="An agent that cannot refuse is not safe at scale.",
         quote="No named success condition? Stop, ask, or fail — never guess.",
         caption="Ambiguity in the spec is the agent's silent failure mode. Surface it, don't smooth it over."),
    dict(label="AI Agents · minimum proof · 9/10", kind="checklist",
         headline="Minimum viable proof contract.",
         items=["State readable before and after the action",
                "A deterministic check, not a human eyeball",
                "The check fails loudly — exit code, exception, alert",
                "The failure message says WHAT did not change",
                "The log lets you replay the decision"],
         caption="If any of these is missing, the task is not done — it is attempted."),
    dict(label="AI Agents · keep this · 10/10", kind="cta",
         headline="Save this for your next agent postmortem.",
         body="Every agent incident I've debugged reduces to one missing check: the one that would have noticed nothing happened.",
         save="Save for later review"),
]

DECKS["day2"] = [
    dict(label="Klipper · debug order · 1/10", kind="cover",
         headline="HTTP 200 lied to me. Klipper was already dead.",
         sub="The debugging order for a green screen with a dead system — learned on a real 3D printer."),
    dict(label="Klipper · what happened · 2/10", kind="head_body",
         headline="The page loaded. The printer didn't.",
         body="Mainsail came up. Nginx answered 200 on every probe. Klippy — the layer that actually moves the motors — was stuck in error.",
         panel=( "RP2040 disabled.\nACCEL_AUTOCONFIG blocks\nstill in printer.cfg.", RED, BG)),
    dict(label="Klipper · the layers · 3/10", kind="two_box",
         headline="Two layers, one lie.",
         left_tag="Interface", left={"title": "nginx", "body": "Mainsail renders\nHTTP 200 everywhere\nlooks fine", "fill": PANEL2},
         right_tag="Process", right={"title": "klippy", "body": "RP2040 MCU\nunreachable\nerror state since boot", "fill": RED, "color": BG},
         caption="The status code only proves the first layer answered."),
    dict(label="Klipper · why dashboards lie · 4/10", kind="head_body",
         headline="A dashboard proves the shell, not the system.",
         body="UI checks routes and pages. It cannot see the process inside deciding whether your command does anything.",
         panel=( "A green interface\nis a report, not a proof.", PANEL2, TEXT)),
    dict(label="Klipper · debug order · 5/10", kind="steps",
         headline="Debug order: process before looks.",
         steps=["Is the process itself alive and ready?",
                "Is its configuration exact and wired correctly?",
                "Did the transport between layers actually arrive?",
                "Only then: is the user-visible state correct?"],
         caption="Skip a layer and you will fix the wrong thing."),
    dict(label="Klipper · the command · 6/10", kind="terminal",
         headline="Ask the process, not the page.",
         lines=["$ curl -s 127.0.0.1:7125/printer/objects/query?klippy_state", '"state":"ready"   ← good', '"state":"error"  ← this was the answer', "# the 200 came from nginx, not from klippy"],
         body="Status must come from the component that can also fail."),
    dict(label="Klipper · root cause · 7/10", kind="steps",
         headline="The root cause chain.",
         steps=["Accelerometer disconnected for a reason",
                "printer.cfg kept the ACCEL_AUTOCONFIG blocks",
                "Startup queried the dead RP2040",
                "klippy_state = error, UI still 200"],
         caption="Every hop is visible only from the process layer."),
    dict(label="Klipper · the fix · 8/10", kind="head_body",
         headline="Disable config with the hardware — not just the hardware.",
         body="Commenting out the RP2040 blocks (not deleting — config history matters), then restart and re-home:\n\nklippy_state: ready.",
         panel=( "Success = the motors\nmove, not the page.", GREEN, BG)),
    dict(label="Klipper · generalize · 9/10", kind="head_body",
         headline="Every dependency has an order. Write it down.",
         body="Postgres before the backend. Backend before the proxy. Process before the page. If the order is tribal knowledge, the outage is retraining every on-call.",
         panel=( "Timing is part of\nthe contract.", PANEL2, TEXT)),
    dict(label="Klipper · keep this · 10/10", kind="cta",
         headline="Save this for the next green screen you don't trust.",
         body="HTTP 200 is a message from the door, not from the house. When in doubt, ask the innermost component that can tell the truth.",
         save="Save for your next incident"),
]

DECKS["day3"] = [
    dict(label="Botka · reject first · 1/10", kind="cover",
         headline="More generation did not make Botka better.",
         sub="The review gate that turned my Russian-language exam prep pipeline into something worth publishing."),
    dict(label="Botka · the problem · 2/10", kind="head_body",
         headline="Volume is not quality.",
         body="The pipeline generated questions fast. Nobody complained about the number.\n\nLearners complained about being unfairly scored.",
         panel=( "Output grew.\nTrust dropped.", RED, BG)),
    dict(label="Botka · the pipeline · 3/10", kind="steps",
         headline="Every item passes one gate.",
         steps=["Source exists and is verifiable",
                "Not a duplicate of anything banked",
                "Exactly one defensible correct answer",
                "Explanation survives a hostile read",
                "Human reviewer approves",
                "Only then: published"],
         caption="Generation is a step, not the goal."),
    dict(label="Botka · inside the gate · 4/10", kind="checklist",
         headline="What the gate actually rejects.",
         items=["Duplicates and near-duplicates",
                "Two defensible answers (ambiguous stem)",
                "Explanation that doesn't match the answer",
                "Key rule students can't look up",
                "Grammar masquerading as subject knowledge",
                "Explanation too vague to teach anything"],
         caption="Most rejects are invisible in development. Users see them first."),
    dict(label="Botka · what I found · 5/10", kind="stats",
         headline="The audit was not gentle.",
         stats=[("45%", "of screened Russian items tested the wrong skill"),
                ("6 203", "items audited by the topic-fit check"),
                ("2 777", "items archived with a reversible backup")],
         caption="Source: topic-fit check over 6,203 audited items, Russian track."),
    dict(label="Botka · the rule · 6/10", kind="quote",
         headline="Curation is the feature.",
         quote="Deleting plausible garbage beats shipping fluent filler.",
         caption="One sound answer teaches more than ten confident, wrong ones."),
    dict(label="Botka · human review · 7/10", kind="head_body",
         headline="Human review lives where uncertainty concentrates.",
         body="Deterministic checks (duplicates, schema, answer counts) catch the bulk mechanically. Humans see grammar, semantics and taste — the parts a model can confidently get wrong.",
         panel=( "Machines filter the volume.\nHumans decide the border.", PANEL2, TEXT)),
    dict(label="Botka · the metric · 8/10", kind="two_box",
         headline="Measure rejection, not generation.",
         left_tag="Vanity", left={"title": "Volume metrics", "body": "questions/day\nitems published\ndataset size", "fill": PANEL2},
         right_tag="Real", right={"title": "Health metrics", "body": "rejection rate\nappeals per 100\nreviewer disagreement", "fill": GOLD, "color": BG},
         caption="A pipeline you can't trust is measured by how much it refuses."),
    dict(label="Botka · your audit · 9/10", kind="checklist",
         headline="Five questions for your content pipeline.",
         items=["Can a senior reviewer defend every published item?",
                "Are duplicates caught before the learner sees them?",
                "Is the correct answer actually unique?",
                "Does the explanation teach the mechanism, not just the key?",
                "Could you restore the archive if the audit was wrong?"],
         caption="If any answer is 'no', your pipeline publishes debt."),
    dict(label="Botka · keep this · 10/10", kind="cta",
         headline="Save this for your next content audit.",
         body="The unglamorous gate is why a learner opens the app and trusts it. Volume is easy. Verification is the product.",
         save="Save for your next audit"),
]

for deck, slides in DECKS.items():
    deck_dir = OUT / deck
    deck_dir.mkdir(parents=True, exist_ok=True)
    images = []
    for i, spec in enumerate(slides, start=1):
        im = render_slide(spec)
        path = deck_dir / f"{i:02}.png"
        im.save(path)
        images.append(im)
        print(path)
    pdf_path = deck_dir / f"{deck}.pdf"
    images[0].save(pdf_path, "PDF", resolution=100, save_all=True, append_images=images[1:])
    print(pdf_path)
