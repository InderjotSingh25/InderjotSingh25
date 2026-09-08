#!/usr/bin/env python3
"""
prep_photo.py <source-photo.jpg>

Turns a flatly-lit face photo into a clean, high-contrast grayscale image
ready for ASCII conversion:
  1. Remove the background with rembg, so the subject is isolated.
  2. Boost local contrast with CLAHE (contrast-limited adaptive histogram
     equalization) so a flat face gets real highlights/shadows.
  3. Composite onto pure white so the background maps to the blank end
     of the ASCII ramp (white -> spaces).

Output: source-prepped.png (grayscale, same folder as the input).

If rembg isn't installed (e.g. you're just testing quickly), this script
falls back to skipping background removal and still applies CLAHE — the
portrait will look fine as long as the original background is fairly
plain and light.
"""
import sys
import os
import io
import numpy as np
import cv2
from PIL import Image

try:
    from rembg import remove as rembg_remove
    HAVE_REMBG = True
except ImportError:
    HAVE_REMBG = False


def remove_background(img: Image.Image) -> Image.Image:
    """Return an RGBA image with the background knocked out, if rembg is
    available. Otherwise return the image as-is with a full-opacity alpha
    channel (no-op fallback)."""
    if not HAVE_REMBG:
        print("[prep_photo] rembg not installed — skipping background "
              "removal, using CLAHE-only fallback.")
        return img.convert("RGBA")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out_bytes = rembg_remove(buf.getvalue())
    return Image.open(io.BytesIO(out_bytes)).convert("RGBA")


def clahe_boost(rgba: Image.Image) -> Image.Image:
    """Apply CLAHE on the L channel (LAB colorspace) to give a flatly-lit
    subject real local contrast, then return an RGBA image with the
    original alpha preserved."""
    rgb = np.array(rgba.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)

    lab2 = cv2.merge((l2, a, b))
    rgb2 = cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)

    boosted = Image.fromarray(rgb2).convert("RGBA")
    boosted.putalpha(rgba.getchannel("A"))
    return boosted


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Flatten onto a pure white canvas, then convert to grayscale."""
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white_bg, rgba).convert("RGB")
    return flat.convert("L")


def main():
    if len(sys.argv) < 2:
        print("usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src_path = sys.argv[1]
    out_path = os.path.join(os.path.dirname(src_path) or ".", "source-prepped.png")

    img = Image.open(src_path).convert("RGB")
    no_bg = remove_background(img)
    boosted = clahe_boost(no_bg)
    gray = composite_on_white(boosted)

    gray.save(out_path)
    print(f"[prep_photo] wrote {out_path}  ({gray.size[0]}x{gray.size[1]})")


if __name__ == "__main__":
    main()
