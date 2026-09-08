#!/usr/bin/env python3
"""
make_info_card.py

Hand-authors a small SVG that looks like `neofetch` output: a title bar,
then colored key/value rows. Content lives here (not in the contribution
graph — that already covers real GitHub stats, this card is for the
story numbers can't tell).

Edit the FIELDS list below with your own info, then run:
    python scripts/make_info_card.py

Set STATIC=1 to emit a single frozen frame (handy for local Quick Look
previews where SMIL doesn't animate).
"""
import os

USERNAME = "InderjotSingh25"
HOSTNAME = "github"

# --- Edit this section with your own details ---------------------------
FIELDS = [
    ("Now",        "Building things, breaking things, fixing them again"),
    ("Prev",       "TODO: your last role / what you were doing before"),
    ("Stack",      "TODO: e.g. Python · TypeScript · React · Docker"),
    ("Highlights", "TODO: e.g. Shipped X · Contributed to Y · Learned Z"),
]
ACCENT = "#39d353"        # GitHub-green accent for the title/keys
KEY_COLOR = "#7ee787"
VAL_COLOR = "#c9d1d9"
BG_COLOR = "transparent"
# -------------------------------------------------------------------

FONT = '"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace'
TITLE_SIZE = 15
ROW_SIZE = 13
LINE_H = 26
PAD_X = 18
PAD_TOP = 28
CARD_W = 470

STATIC = os.environ.get("STATIC") == "1"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_svg():
    rows = FIELDS
    height = PAD_TOP + 22 + 14 + len(rows) * LINE_H + 20

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                  f'viewBox="0 0 {CARD_W} {height}" width="{CARD_W}" height="{height}">')
    parts.append(f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>')
    parts.append(f'<style>'
                  f'.title{{font-family:{FONT};font-size:{TITLE_SIZE}px;font-weight:700;fill:{ACCENT};}}'
                  f'.key{{font-family:{FONT};font-size:{ROW_SIZE}px;font-weight:700;fill:{KEY_COLOR};}}'
                  f'.val{{font-family:{FONT};font-size:{ROW_SIZE}px;fill:{VAL_COLOR};}}'
                  f'</style>')

    title = f"{USERNAME}@{HOSTNAME}"
    underline_w = len(title) * (TITLE_SIZE * 0.62)

    def fade_in(delay):
        if STATIC:
            return ""
        return (f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-8 0" to="0 0" begin="{delay:.2f}s" dur="0.35s" '
                f'fill="freeze" additive="sum"/>')

    op0 = '1' if STATIC else '0'

    parts.append(f'<g opacity="{op0}">')
    parts.append(f'  <text x="{PAD_X}" y="{PAD_TOP}" class="title">{esc(title)}</text>')
    parts.append(f'  {fade_in(0.0)}')
    parts.append('</g>')
    parts.append(f'<line x1="{PAD_X}" y1="{PAD_TOP + 8}" x2="{PAD_X + underline_w:.0f}" '
                 f'y2="{PAD_TOP + 8}" stroke="{ACCENT}" stroke-width="1" opacity="0.6"/>')

    y = PAD_TOP + 8 + 26
    key_w = max(len(k) for k, _ in rows) + 1

    for i, (key, val) in enumerate(rows):
        delay = 0.25 + i * 0.16
        parts.append(f'<g opacity="{op0}">')
        parts.append(f'  <text x="{PAD_X}" y="{y}" class="key">{esc(key)}</text>')
        parts.append(f'  <text x="{PAD_X + key_w * 8.2:.0f}" y="{y}" class="val">{esc(val)}</text>')
        parts.append(f'  {fade_in(delay)}')
        parts.append('</g>')
        y += LINE_H

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    svg = build_svg()
    with open("info-card.svg", "w") as f:
        f.write(svg)
    print(f"[make_info_card] wrote info-card.svg (static={STATIC})")


if __name__ == "__main__":
    main()
