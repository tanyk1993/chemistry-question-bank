"""MI 2026 H2 P1: crop the all-diagram option set (Q8: four graphs, each an
embedded raster with a typed y-axis title sitting directly above it, e.g.
"Boiling point of X2"). The user ruled (2026-11-07) that the title is part of
the figure, so each crop = title line + raster, and options{} carries only the
"[structure A]" search token (no separate caption under the graph).
usage: python3 -m ingest.crop_mi26_p1_options <word.pdf> <outdir>"""
import io, sys
import numpy as np
import pymupdf
from scipy import ndimage
from PIL import Image, ImageChops
d = pymupdf.open(sys.argv[1]); out = sys.argv[2]
page = d[4]                                   # PDF page 5
imgs = sorted(page.get_image_info(), key=lambda i: (round(i["bbox"][1] / 100), i["bbox"][0]))
assert len(imgs) == 4, len(imgs)
for L, info in zip("ABCD", imgs):
    r = pymupdf.Rect(info["bbox"])
    # the axis title is the one text line whose bottom edge meets the raster's top edge
    title = [pymupdf.Rect(ln["bbox"]) for b in page.get_text("dict")["blocks"] for ln in b.get("lines", [])
             if "".join(sp["text"] for sp in ln["spans"]).strip()
             and abs(ln["bbox"][3] - r.y0) < 3 and ln["bbox"][0] >= r.x0 - 3 and ln["bbox"][2] <= r.x1 + 3]
    assert len(title) == 1, (L, title)
    full = r | title[0]
    full = pymupdf.Rect(full.x0 - 1.5, full.y0 - 1.5, max(full.x1, r.x1) + 1.5, full.y1)
    r = full
    img_rect = pymupdf.Rect(info["bbox"])
    pix = page.get_pixmap(clip=r, dpi=400)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    # the embedded rasters carry a few stray specks on their top/right edge
    # (JPEG residue, 9-18 px at 400 dpi); whiten a dark blob under 40 px ONLY when it
    # sits within 30 px of the top/right edge (the i-dots in 'chlorine' are small too).
    a = np.array(im)
    lab, n = ndimage.label(a.min(axis=2) < 140, structure=np.ones((3, 3)))
    H, Wd = a.shape[:2]
    sc = 400 / 72.0
    top, right = int((img_rect.y0 - r.y0) * sc), int((img_rect.x1 - r.x0) * sc)   # raster's top/right in px
    for i, sl in enumerate(ndimage.find_objects(lab)):
        inside = sl[0].start >= top - 2 and sl[1].stop <= right + 2               # inside the raster (not the title text)
        near_edge = inside and (sl[0].start - top < 30 or right - sl[1].stop < 30)
        if near_edge and (lab[sl] == i + 1).sum() < 40:
            a[sl][lab[sl] == i + 1] = 255
    # faint (grey > 140) specks in the top-right corner of B and D: whiten the corner too
    g = a.min(axis=2)
    y0c, x1c = max(top, 0), min(right, Wd)
    c = g[y0c:y0c + 35, x1c - 35:x1c] < 240
    a[y0c:y0c + 35, x1c - 35:x1c][c] = 255
    im = Image.fromarray(a)
    box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    im = im.crop(box)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255)); o.paste(im, (12, 12))
    o.save("%s/MI_H2_P1_Q8_%s_2026.png" % (out, L))
    print(L, [round(v, 1) for v in info["bbox"]], o.size)
