"""TJC 2026 H2 P1: crop the 5 answer-side figures from the Word-exported PDF
(Claude's snips). The PDF is the question paper with the answer typed in blue
under each question; only figures that belong to a SOLUTION are cropped.

  Q5  ans-1  NO2 (radical, one dative bond) and N2O4 (two dative bonds)
  Q20 ans-1  general ester H-CO-O-R
  Q20 ans-2  the four esters HCOC4H9 (one combined snip)
  Q24 ans-1  compound Y with the chiral centres starred and the C=C circled
  Q30 ans-1  the complex with the charge on each ligand marked

Regions are PDF points (page index 0-based); 400 dpi, trimmed to ink, 12 px
white border; ink touching the region edge is refused.

usage: python3 -m ingest.crop_tjc26_p1_answers <word.pdf> <outdir>
Writes the PNGs plus answer_sizes.json (printed widths, for gen_image_sizes).
"""
import io
import json
import sys

import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]

FIGS = {
    "Q5_ans-1":  (5, (68.0, 298.0, 258.0, 356.0), "Q5 NO2 and N2O4 structures"),
    "Q20_ans-1": (13, (68.0, 502.5, 215.0, 531.0), "Q20 general ester H-CO-O-R"),
    "Q20_ans-2": (13, (68.0, 571.5, 275.0, 775.0), "Q20 the four esters HCOOC4H9"),
    "Q24_ans-1": (15, (68.0, 545.0, 178.0, 616.0), "Q24 compound Y, chiral centres starred, C=C circled"),
    "Q30_ans-1": (19, (98.0, 497.5, 325.0, 652.0), "Q30 complex with ligand charges marked"),
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
    name = "TJC_H2_P1_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/answer_sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
