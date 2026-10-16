#!/usr/bin/env python3
"""Render docs/loop.svg, the animated self-learning loop shown in the README.

A pulse runs the 8 pipeline steps. Every lap is one strategy version, and the
engagement log on the right gains a row per lap (numbers from the README's
Day 1 -> Day 45 timeline). Pure SVG + SMIL so GitHub animates it inline.

    python3 scripts/render_loop_svg.py
"""

import math
from html import escape
from pathlib import Path

W, H = 880, 404
CX, CY, R = 205, 196, 118
LAP = 3.0
LAPS = 4
CYCLE = LAP * LAPS

BG, EDGE, TEXT, DIM, FAINT = "#0d1117", "#21262d", "#e6edf3", "#7d8590", "#30363d"
BLUE, LBLUE, AMBER, GREEN, PURPLE, LPURPLE = (
    "#4A90D9",
    "#5BA0E0",
    "#E8A838",
    "#50C878",
    "#9B59B6",
    "#AF7AC5",
)

STEPS = [
    ("research", BLUE),
    ("extract", LBLUE),
    ("generate", LBLUE),
    ("rank", AMBER),
    ("publish", GREEN),
    ("measure", PURPLE),
    ("learn", LPURPLE),
    ("adapt", LPURPLE),
]

# (strategy label, day, post, likes) - one per lap
LAPS_DATA = [
    ("generic tips", "01", '"here\'s a generic coding tip"', 12),
    ("hot takes", "07", '"most devs don\'t need Docker"', 340),
    ("contrarian x3", "30", "every post that week", 500),
    ("old vs new tech", "45", '"jQuery vs React"', 800),
]


def t(x, y, s, color, size=13, extra="", anchor=None):
    w = len(s) * size * 0.6
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" textLength="{w:.1f}" '
        f'lengthAdjust="spacingAndGlyphs"{a}{extra}>{escape(s)}</text>'
    )


def lap_window(i, fade=0.002):
    """opacity values/keyTimes: visible only during lap i of the cycle."""
    a, b = i / LAPS, (i + 1) / LAPS
    if i == 0:
        return "1;1;0;0", f"0;{b - fade:.4f};{b:.4f};1"
    if i == LAPS - 1:
        return "0;0;1;1", f"0;{a - fade:.4f};{a:.4f};1"
    return "0;0;1;1;0;0", f"0;{a - fade:.4f};{a:.4f};{b - fade:.4f};{b:.4f};1"


def main():
    out = []
    # ring
    out.append(
        f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="{FAINT}" stroke-width="2" stroke-dasharray="2 6"/>'
    )
    # pulse with a short trail
    path = f"M {CX} {CY - R} A {R} {R} 0 1 1 {CX - 0.01} {CY - R} Z"
    for lag, r, op in ((0.12, 3, 0.25), (0.06, 4.5, 0.5), (0, 7, 1)):
        out.append(
            f'<circle r="{r}" fill="{GREEN}" opacity="{op}">'
            f'<animateMotion path="{path}" dur="{LAP}s" begin="-{LAP - lag:.2f}s" repeatCount="indefinite"/></circle>'
        )
    # nodes flash as the pulse passes them
    for k, (name, color) in enumerate(STEPS):
        ang = math.radians(-90 + k * 360 / len(STEPS))
        x, y = CX + R * math.cos(ang), CY + R * math.sin(ang)
        f = k / len(STEPS)
        if k == 0:
            vals, keys = "1;.35;.35;1", "0;.1;.97;1"
        else:
            vals, keys = ".35;.35;1;.35;.35", f"0;{f - 0.02:.3f};{f:.3f};{min(f + 0.1, 0.99):.3f};1"
        pw = len(name) * 7.2 + 18
        out.append(
            f'<g opacity=".35"><animate attributeName="opacity" values="{vals}" keyTimes="{keys}" dur="{LAP}s" repeatCount="indefinite"/>'
            f'<rect x="{x - pw / 2:.1f}" y="{y - 12:.1f}" width="{pw:.1f}" height="24" rx="12" fill="{BG}" stroke="{color}" stroke-width="2"/>'
            + t(x, y + 4.5, name, color, 12, ' font-weight="700"', anchor="middle")
            + "</g>"
        )
    # hub: current strategy version
    out.append(
        f'<circle cx="{CX}" cy="{CY}" r="62" fill="#111a14" stroke="{GREEN}" stroke-opacity=".35"/>'
    )
    out.append(t(CX, CY - 16, "strategy", DIM, 11, anchor="middle"))
    for i, (label, *_rest) in enumerate(LAPS_DATA):
        vals, keys = lap_window(i)
        out.append(
            f'<g opacity="{vals.split(";")[0]}"><animate attributeName="opacity" values="{vals}" keyTimes="{keys}" dur="{CYCLE}s" repeatCount="indefinite"/>'
            + t(CX, CY + 6, f"v{i + 1}", GREEN, 22, ' font-weight="700"', anchor="middle")
            + t(CX, CY + 26, label, TEXT, 11, anchor="middle")
            + "</g>"
        )

    # engagement log
    lx, ly = 420, 70
    out.append(t(lx, ly, "$ tail -f engagement.log", GREEN, 13, ' font-weight="700"'))
    bar_max = W - 40 - lx
    for i, (_l, day, post, likes) in enumerate(LAPS_DATA):
        y = ly + 40 + i * 62
        a = i / LAPS
        show = (
            f'<animate attributeName="opacity" values="{"1;1" if i == 0 else "0;0;1;1"}" '
            f'keyTimes="{"0;1" if i == 0 else f"0;{a - 0.002:.4f};{a:.4f};1"}" dur="{CYCLE}s" repeatCount="indefinite"/>'
        )
        grow = (
            f'<animate attributeName="width" values="0;0;{bar_max * likes / 800:.1f};{bar_max * likes / 800:.1f}" '
            f'keyTimes="0;{a:.4f};{min(a + 0.08, 1):.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
        )
        last = i == LAPS - 1
        out.append(
            f'<g opacity="{1 if i == 0 else 0}">{show}'
            + t(lx, y, f"day {day}", DIM, 12)
            + t(lx + 62, y, post, TEXT, 12)
            + t(
                W - 40,
                y,
                f"{likes}+ engagement" if likes == 500 else f"{likes} likes",
                GREEN if last else TEXT,
                12,
                ' font-weight="700"',
                anchor="end",
            )
            + f'<rect x="{lx}" y="{y + 10}" width="0" height="8" rx="4" fill="{GREEN if last else BLUE}" opacity="{1 if last else 0.7}">{grow}</rect>'
            + "</g>"
        )
    out.append(
        f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;.8;.82;1" dur="{CYCLE}s" repeatCount="indefinite"/>'
        + t(
            lx,
            ly + 40 + LAPS * 62 - 8,
            "↑ written and ranked by the agent. approved by a human.",
            AMBER,
            12,
        )
        + "</g>"
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated self-learning loop: research, extract, generate, rank, publish, measure, learn, adapt. Each lap is a new strategy version; engagement grows from 12 to 800 likes.">
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace;white-space:pre}}</style>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>
{t(28, 34, "the loop, running", DIM, 12)}
{"".join(out)}
{t(W - 28, H - 16, "every lap = 1 strategy rewrite. nobody edits the prompt by hand.", "#4b5563", 11, anchor="end")}
</svg>
'''
    dest = Path(__file__).resolve().parent.parent / "docs" / "loop.svg"
    dest.write_text(svg)
    print(f"wrote {dest} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
