"""SAJC 2026 H2 P2: crop the 10 answer-side figures from the Word-exported answers PDF (Claude's snips).

  Q1(d)(i)   handwritten dot-and-cross diagram of MgCO3
  Q2(a)(ii)  Fig 2.1 with the d orbitals labelled and filled
  Q3(a)(iii) structure of X (both ester orders, "or" included)
  Q3(b)(iv)  [ethanoyl chloride] against time (exponential decay, two equal half-lives)
  Q4(b)(ii)  energy level diagram (butane, actual / expected buta-1,3-diene, -224, -208, -16)
  Q4(d)      two repeat units of trans-1,4-polybutadiene
  Q4(e)(ii)  p orbitals drawn on Fig 4.3
  Q5(c)(i)   Table 5.2 stage 3 equation (equation cell of the stage 3 row only)
  Q5(c)(ii)  Table 5.2 stage 2 equation with the three curly arrows and dipoles (equation cell only)
  Q5(c)(iii) structure of T with the school's carbon numbering, with U and V numbered the same way

The school's difficulty letters (L/M/H, A/B) in the right margin are outside every box.
Each region is in PDF points (page index 0-based), rendered at 400 dpi, trimmed to its ink with a 12 px
white border; a crop whose ink touches the region edge is refused.
usage: python3 -m ingest.crop_sajc26_p2_answers <answers.pdf> <outdir>   (writes sizes.json too)
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
    "Q1_ans-di":   (3,  (125.0, 64.0, 415.0, 156.0),  "Q1(d)(i) dot-and-cross diagram of magnesium carbonate"),
    "Q2_ans-aii":  (5,  (195.0, 362.0, 440.0, 524.0), "Q2(a)(ii) Fig 2.1 completed"),
    "Q3_ans-aiii": (8,  (125.0, 508.0, 485.0, 612.0), "Q3(a)(iii) structure of X"),
    "Q3_ans-biv":  (10, (125.0, 90.0, 455.0, 304.0),  "Q3(b)(iv) [ethanoyl chloride] against time"),
    "Q4_ans-bii":  (13, (130.0, 62.0, 432.0, 262.0),  "Q4(b)(ii) energy level diagram"),
    "Q4_ans-d":    (14, (95.0, 515.0, 345.0, 592.0), "Q4(d) trans-1,4-polybutadiene, two repeat units"),
    "Q4_ans-eii":  (15, (200.0, 522.0, 430.0, 620.0), "Q4(e)(ii) p orbitals on Fig 4.3"),
    "Q5_ans-ci":   (18, (212.0, 552.0, 508.0, 646.0), "Q5(c)(i) stage 3 equation"),
    "Q5_ans-cii":  (18, (212.0, 466.5, 508.0, 546.5), "Q5(c)(ii) stage 2 with curly arrows"),
    "Q5_ans-ciii": (19, (128.0, 385.0, 300.0, 648.0), "Q5(c)(iii) structure of T (numbered), U and V"),
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = key.split("_", 1)
    name = "SAJC_H2_P2_%s_%s_2026.png" % (qn, s)
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
