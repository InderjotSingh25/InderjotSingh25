#!/usr/bin/env python3
"""
make_ascii_svg.py [source-prepped.png] [output.svg]

Downsamples the prepped photo to a character grid and maps each cell's
brightness to a glyph from a density ramp (sparse -> dense). Renders it
as a single monochrome SVG where each row wipes in left-to-right,
staggered top-to-bottom, using SMIL so GitHub actually animates it.
"""
import sys
import os
import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#      ^ leading space clears the background to nothing

GRID_COLS = 100
CHAR_ASPECT = 0.52        # monospace glyphs are taller than wide

FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE * 1.0

FILL_COLOR = "#c9d1d9"    # light-gray, monochrome
BG_COLOR = "transparent"

ROW_DURATION = 0.9        # seconds for one row to wipe in
ROW_STAGGER = 0.045       # seconds between each row starting


def image_to_grid(path, cols=GRID_COLS):
    img = Image.open(path).convert("L")
    w, h = img.size
    rows = max(1, round(cols * (h / w) * CHAR_ASPECT))
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small).astype(np.float32) / 255.0  # 0=black,1=white
    return arr


def brightness_to_char(v):
    # v: 0 (black) -> 1 (white). Ramp is bright->dark, so invert index.
    idx = int(round((1 - v) * (len(RAMP) - 1)))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def build_svg(arr, out_path):
    rows, cols = arr.shape
    width = cols * CHAR_W
    height = rows * CHAR_H

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                  f'viewBox="0 0 {width:.0f} {height:.0f}" '
                  f'width="{width:.0f}" height="{height:.0f}">')
    lines.append(f'<rect width="100%" height="100%" fill="{BG_COLOR}"/>')
    lines.append(f'<style>text{{font-family:"SFMono-Regular",Consolas,'
                  f'"Liberation Mono",Menlo,monospace;font-size:{FONT_SIZE}px;'
                  f'fill:{FILL_COLOR};white-space:pre;}}</style>')

    for r in range(rows):
        row_chars = "".join(brightness_to_char(arr[r, c]) for c in range(cols))
        # strip trailing spaces so the clip box isn't wider than needed
        stripped = row_chars.rstrip()
        if not stripped.strip():
            continue
        row_w = len(stripped) * CHAR_W
        y = (r + 1) * CHAR_H
        start = r * ROW_STAGGER
        clip_id = f"clip{r}"

        escaped = (stripped.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))

        lines.append(f'<clipPath id="{clip_id}">')
        lines.append(f'  <rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">')
        lines.append(f'    <animate attributeName="width" '
                      f'from="0" to="{row_w:.1f}" '
                      f'begin="{start:.3f}s" dur="{ROW_DURATION:.2f}s" '
                      f'fill="freeze" calcMode="spline" '
                      f'keySplines="0.2 0 0.1 1" keyTimes="0;1"/>')
        lines.append('  </rect>')
        lines.append('</clipPath>')

        lines.append(f'<g clip-path="url(#{clip_id})">')
        lines.append(f'  <text x="0" y="{y:.1f}">{escaped}</text>')
        lines.append('</g>')

    lines.append('</svg>')
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[make_ascii_svg] wrote {out_path}  ({cols}x{rows} chars, "
          f"{width:.0f}x{height:.0f}px)")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    if not os.path.exists(src):
        print(f"error: {src} not found — run prep_photo.py first")
        sys.exit(1)
    arr = image_to_grid(src)
    build_svg(arr, out)


if __name__ == "__main__":
    main()
