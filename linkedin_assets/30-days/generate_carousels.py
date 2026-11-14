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


from carousels_specs import DECKS



def main():
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


if __name__ == "__main__":
    main()
