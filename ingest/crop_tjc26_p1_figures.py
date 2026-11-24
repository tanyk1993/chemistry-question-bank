"""TJC 2026 H2 P1: crop the 11 question-side diagram assets from the Word PDF
(Claude's snips, for the user to check).

  Q2   graph of third ionisation energy against atomic number (points A-D)
  Q3   structure of ethyl cyanoacrylate with angles x, y, z
  Q15  the two kinetics graphs (rate vs [NO]; [NOCl] vs time) as ONE snip
  Q22  four structures in the table cells: row 1 compound I, row 2 compounds I
       and II, row 3 compound I (slots stem1..stem4, in reading order)
  Q24  structure of compound Y (the typed "Y" label stays text)
  Q27  electrochemical cell
  Q30  iron complex ion

Each region is in PDF points (page index 0-based). Rendered at 400 dpi, trimmed
to its ink, 12 px white border. A crop whose ink touches the region edge is
refused (the box cut through something). `MASKS` whitens a sub-rectangle that
holds text from another element (Q15: the stem line above the graphs).

usage: python3 -m ingest.crop_tjc26_p1_figures <word.pdf> <outdir>
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
    "Q2_stem1":  (2, (140.0, 183.0, 432.0, 435.0), "Q2 graph of third ionisation energy (points A-D)"),
    "Q3_stem1":  (3, (205.0, 140.0, 425.0, 222.0), "Q3 structure of ethyl cyanoacrylate, angles x y z"),
    "Q15_stem1": (10, (125.0, 474.0, 550.0, 640.0), "Q15 rate vs [NO] and [NOCl] vs time graphs"),
    "Q22_stem1": (14, (125.0, 433.0, 255.0, 485.0), "Q22 row 1 compound I (butanone)"),
    "Q22_stem2": (14, (125.0, 490.0, 255.0, 549.0), "Q22 row 2 compound I (phenylamine)"),
    "Q22_stem3": (14, (260.0, 490.0, 402.0, 549.0), "Q22 row 2 compound II (phenylmethanol)"),
    "Q22_stem4": (14, (125.0, 554.0, 255.0, 612.0), "Q22 row 3 compound I (chlorobenzene)"),
    "Q24_stem1": (15, (255.0, 388.0, 372.0, 441.0), "Q24 structure of compound Y"),
    "Q27_stem1": (17, (122.9, 332.7, 502.1, 506.8), "Q27 electrochemical cell"),
    "Q30_stem1": (19, (172.0, 108.0, 448.0, 312.0), "Q30 iron complex ion"),
}
# sub-rectangles (PDF pt) painted white before trimming
MASKS = {
    "Q15_stem1": [(100.0, 466.0, 300.0, 484.0)],     # "following graphs were obtained."
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    for (mx0, my0, mx1, my1) in MASKS.get(key, []):
        s = DPI / 72.0
        x0, y0 = int((mx0 - box[0]) * s), int((my0 - box[1]) * s)
        x1, y1 = int((mx1 - box[0]) * s), int((my1 - box[1]) * s)
        im.paste((255, 255, 255), (max(x0, 0), max(y0, 0), max(x1, 0), max(y1, 0)))
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (
        key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "TJC_H2_P1_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
