"""SAJC 2026 H2 P1: crop the 16 diagram assets from the Word PDF (Claude's snips).

  stem figures : Q5 graph, Q9 reaction scheme, Q17 compounds W-Z, Q20 polymer,
                 Q21 LiAlH4 scheme, Q30 voltaic cell
  numbered snips (numerals included, one image): Q23 reactions 1-3, Q25 structures 1-3
  option sets  : Q19 (A-D) and Q22 (A-D); the option letters are printed outside
                 the pictures and are excluded

Each region is given in PDF points (page index is 0-based). Each crop is
rendered at 400 dpi, trimmed to its ink and given a 12 px white border. A crop
whose ink touches the region edge is refused (the box cut through something).
Q5, Q17, Q22 and Q23 are raster pictures in the school's file; their regions are
the picture boxes padded by 3 pt.

usage: python3 -m ingest.crop_sajc26_p1_figures <word.pdf> <outdir>
Writes the PNGs plus sizes.json (printed widths, for gen_image_sizes).
"""
import io
import json
import sys

import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]

# file stem -> (page index, (x0, y0, x1, y1) in pt, description)
FIGS = {
    "Q5_stem1":  (2, (194.5, 107.5, 420.0, 269.0), "Q5 graph of 1 mole of ideal gas"),
    "Q9_stem1":  (3, (172.0, 337.0, 446.0, 371.0), "Q9 hydrolysis equation with H+ over the arrow"),
    "Q17_stem1": (6, (158.8, 134.1, 460.2, 243.1), "Q17 compounds W, X, Y, Z"),
    "Q19_A":     (7, (100.0, 106.0, 260.0, 157.0), "Q19 option A"),
    "Q19_B":     (7, (100.0, 157.0, 260.0, 207.0), "Q19 option B"),
    "Q19_C":     (7, (100.0, 208.0, 260.0, 281.0), "Q19 option C"),
    "Q19_D":     (7, (100.0, 283.0, 260.0, 356.0), "Q19 option D"),
    "Q20_stem1": (7, (255.0, 410.0, 380.0, 492.0), "Q20 vinyl alcohol polymer"),
    "Q21_stem1": (8, (150.0, 118.0, 496.0, 358.0), "Q21 LiAlH4 reduction scheme"),
    "Q22_A":     (9, (99.3, 134.1, 217.4, 189.9), "Q22 option A"),
    "Q22_B":     (9, (99.3, 197.8, 221.6, 253.5), "Q22 option B"),
    "Q22_C":     (9, (99.3, 261.4, 164.4, 313.1), "Q22 option C"),
    "Q22_D":     (9, (99.3, 321.0, 157.5, 370.8), "Q22 option D"),
    "Q23_stem1": (9, (98.0, 431.8, 537.0, 591.7), "Q23 reactions 1-3 (numbered)"),
    "Q25_stem1": (10, (86.0, 349.0, 245.0, 541.0), "Q25 structures 1-3 (numbered)"),
    "Q30_stem1": (12, (100.0, 386.0, 520.0, 609.0), "Q30 voltaic cell"),
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (
        key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "SAJC_H2_P1_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
