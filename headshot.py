#!/usr/bin/env python3
"""Crop a photo to the site's headshot shape (4:5, 800 by 1000 pixels).

    python3 headshot.py input.jpg docs/images/people/name.jpg [--focus X Y]

The crop is the largest 4:5 box that fits in the photo, centered on the
focus point (fractions of width and height, default 0.5 0.4, which is where
a face usually is). Shift the focus to move the box.
"""

import argparse
from PIL import Image, ImageOps

OUT_W, OUT_H = 800, 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--focus", nargs=2, type=float, default=[0.5, 0.4])
    ap.add_argument("--zoom", type=float, default=1.0,
                    help="values above 1 crop tighter around the focus point")
    a = ap.parse_args()

    im = ImageOps.exif_transpose(Image.open(a.src)).convert("RGB")
    W, H = im.size
    ratio = OUT_W / OUT_H
    if W / H > ratio:
        h = H; w = int(H * ratio)
    else:
        w = W; h = int(W / ratio)
    w = int(w / a.zoom); h = int(h / a.zoom)
    fx, fy = a.focus
    x0 = min(max(int(W * fx - w / 2), 0), W - w)
    y0 = min(max(int(H * fy - h / 2), 0), H - h)
    # Never enlarge a small photo; it only gets softer.
    out_w = min(OUT_W, w)
    out_h = int(out_w / ratio)
    im.crop((x0, y0, x0 + w, y0 + h)).resize((out_w, out_h), Image.LANCZOS) \
      .save(a.dst, quality=86, optimize=True)
    print(f"{a.src}: {W}x{H} -> crop {w}x{h} at ({x0},{y0}) -> {a.dst} ({out_w}x{out_h})")


if __name__ == "__main__":
    main()
