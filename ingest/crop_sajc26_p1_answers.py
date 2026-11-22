"""SAJC 2026 H2 P1: crop the 12 answer-side figures from the Word-exported answers PDF
(Claude's snips).  The answers PDF is the question paper with the solution typed in blue
under each question; only the figures that belong to a SOLUTION are cropped here.

  Q3  ans-1  handwritten oxidation-state working (2Cr2O7 2- + 3L -> 4Cr3+ + 3L5+)
  Q4  ans-1  hydrogen-bonded structure of ice
  Q16 ans-1  hand-drawn 4-amino-3-hydroxybutanoic acid
  Q16 ans-2  the 4-membered cyclic ester (beta-lactone)
  Q19 ans-1  hand-drawn comparison of C and D (one combined snip, both rows)
  Q20 ans-1  the monomer, H2C=CH(OH) with C1 / C2 labels (inline in the sentence)
  Q22 ans-1..4  the elimination schemes for options A-D
  Q23 ans-1  the three reactions with the nucleophiles boxed and labelled
  Q25 ans-1  hand-drawn oxidative-cleavage working for structures 1-3

Regions are PDF points (page index 0-based).  Each crop is rendered at 400 dpi, trimmed
to its ink and given a 12 px white border; ink touching the region edge is refused.

usage: python3 -m ingest.crop_sajc26_p1_answers <answers.pdf> <outdir>
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
    "Q3_ans-1":  (1, (93.0, 433.0, 310.0, 548.0), "Q3 handwritten oxidation-state working"),
    "Q4_ans-1":  (2, (93.0, 361.0, 210.0, 527.0), "Q4 structure of ice"),
    "Q16_ans-1": (11, (160.0, 531.0, 310.0, 582.0), "Q16 4-amino-3-hydroxybutanoic acid"),
    "Q16_ans-2": (11, (138.0, 640.0, 196.5, 728.0), "Q16 4-membered cyclic ester"),
    "Q19_ans-1": (14, (221.0, 196.0, 505.0, 350.0), "Q19 hand-drawn comparison of C and D"),
    "Q20_ans-1": (15, (361.2, 478.0, 412.5, 529.0), "Q20 monomer (inline)"),
    "Q22_ans-1": (17, (100.0, 462.0, 330.0, 532.0), "Q22 option A scheme"),
    "Q22_ans-2": (17, (100.0, 562.0, 350.0, 634.0), "Q22 option B scheme"),
    "Q22_ans-3": (17, (100.0, 662.0, 290.0, 716.0), "Q22 option C scheme"),
    "Q22_ans-4": (18, (100.0, 60.0, 375.0, 150.0), "Q22 option D scheme"),
    "Q23_ans-1": (18, (100.0, 426.0, 530.0, 592.0), "Q23 reactions with nucleophiles marked"),
    "Q25_ans-1": (20, (100.0, 345.0, 450.0, 640.0), "Q25 hand-drawn oxidative cleavage working"),
}
# white-out boxes (PDF pt) for typed text that sits inside a region: "N 2025 Q23" beside Q16's drawing
MASKS = {"Q16_ans-1": [(100.0, 543.0, 164.5, 555.5)], "Q16_ans-2": [(195.9, 706.0, 300.0, 726.0)]}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    for (mx0, my0, mx1, my1) in MASKS.get(key, []):
        k = DPI / 72.0
        im.paste((255, 255, 255), (max(0, round((mx0 - box[0]) * k)), max(0, round((my0 - box[1]) * k)),
                                   round((mx1 - box[0]) * k), round((my1 - box[1]) * k)))
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
with open("%s/answer_sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
