"""TMJC 2026 H2 P1: crop the 42 question-side diagram assets from the Word PDF
(Claude's snips, for the user to check).

  Q1   deflection diagrams, options A-D
  Q5   gas-law graphs, options A-D
  Q9   energy profile diagram
  Q11  concentration-time graph
  Q17  dexamethasone structure
  Q18  structures, options A-D
  Q19  inline substrate in the stem + structures A-D
  Q21  mechanism schemes (slots stem1..stem4 in reading order) + structures A-D
  Q22  structures A-D
  Q24  reduction scheme (stem1), compound (stem2), statements 1-4 as one snip (stem3)
  Q25  the three tripeptide fragments (stem1) + hexapeptides A-D
  Q26  PVA segment (stem1) + inline poly(vinyl acetate) in option C (stem2)

Regions are in PDF points (page index 0-based). Rendered at 400 dpi, trimmed
to ink, 12 px white border. A crop whose ink touches the region edge is
refused (the box cut through something). Option letters (A-D) are typed text
in the paper and are left out of the snips: the option grid supplies them.

usage: python3 -m ingest.crop_tmjc26_p1_figures <word.pdf> <outdir>
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
    "Q1_A": (1, (120.0, 164.0, 322.0, 304.0), "Q1 option A"),
    "Q1_B": (1, (340.0, 164.0, 535.0, 304.0), "Q1 option B"),
    "Q1_C": (1, (120.0, 326.0, 322.0, 470.0), "Q1 option C"),
    "Q1_D": (1, (340.0, 326.0, 535.0, 470.0), "Q1 option D"),
    "Q5_A": (3, (140.0, 540.0, 285.0, 642.0), "Q5 option A"),
    "Q5_B": (3, (365.0, 540.0, 500.0, 642.0), "Q5 option B"),
    "Q5_C": (3, (135.0, 658.5, 285.0, 762.0), "Q5 option C"),
    "Q5_D": (3, (365.0, 658.5, 500.0, 764.0), "Q5 option D"),
    "Q9_stem1": (7, (170.0, 85.5, 456.0, 296.5), "Q9 energy profile diagram"),
    "Q11_stem1": (8, (132.0, 145.0, 494.0, 364.0), "Q11 concentration-time graph"),
    "Q17_stem1": (12, (188.0, 108.0, 440.0, 302.0), "Q17 dexamethasone structure"),
    "Q18_A": (12, (124.0, 640.0, 300.0, 705.0), "Q18 option A"),
    "Q18_B": (12, (344.0, 640.0, 540.0, 705.0), "Q18 option B"),
    "Q18_C": (12, (124.0, 708.0, 300.0, 768.0), "Q18 option C"),
    "Q18_D": (12, (344.0, 706.0, 540.0, 770.0), "Q18 option D"),
    "Q19_A": (13, (126.0, 516.0, 300.0, 573.0), "Q19 option A"),
    "Q19_B": (13, (343.0, 516.0, 540.0, 573.0), "Q19 option B"),
    "Q19_C": (13, (126.0, 574.0, 300.0, 628.0), "Q19 option C"),
    "Q19_D": (13, (343.0, 574.0, 540.0, 628.0), "Q19 option D"),
    "Q19_stem1": (13, (311.0, 452.0, 441.0, 500.0), "Q19 inline substrate in the stem"),
    "Q21_stem1": (15, (115.0, 162.0, 530.0, 262.0), "Q21 step 1 scheme"),
    "Q21_stem2": (15, (115.0, 288.0, 365.0, 360.0), "Q21 step 2 scheme"),
    "Q21_stem3": (15, (115.0, 388.0, 345.0, 456.0), "Q21 step 3 scheme"),
    "Q21_stem4": (15, (190.0, 486.0, 435.0, 592.0), "Q21 2-methylbutane-2,3-diol reaction"),
    "Q21_A": (15, (120.0, 636.0, 330.0, 703.0), "Q21 option A"),
    "Q21_B": (15, (372.0, 636.0, 540.0, 703.0), "Q21 option B"),
    "Q21_C": (15, (120.0, 704.0, 330.0, 770.0), "Q21 option C"),
    "Q21_D": (15, (372.0, 704.0, 540.0, 770.0), "Q21 option D"),
    "Q22_A": (16, (124.0, 424.0, 205.0, 486.0), "Q22 option A"),
    "Q22_B": (16, (343.0, 424.0, 455.0, 486.0), "Q22 option B"),
    "Q22_C": (16, (124.0, 490.0, 205.0, 560.0), "Q22 option C"),
    "Q22_D": (16, (343.0, 490.0, 460.0, 560.0), "Q22 option D"),
    "Q24_stem1": (18, (134.0, 119.0, 490.0, 172.0), "Q24 ester reduction scheme"),
    "Q24_stem2": (18, (236.0, 214.0, 392.0, 278.0), "Q24 compound reduced"),
    "Q24_stem3": (18, (120.0, 296.0, 262.0, 518.0), "Q24 statements 1-4 structures"),
    "Q25_stem1": (19, (108.0, 117.0, 516.0, 309.0), "Q25 tripeptide fragments"),
    "Q25_A": (19, (124.0, 336.0, 420.0, 451.0), "Q25 option A"),
    "Q25_B": (19, (124.0, 452.0, 420.0, 556.0), "Q25 option B"),
    "Q25_C": (19, (124.0, 557.0, 420.0, 653.0), "Q25 option C"),
    "Q25_D": (19, (124.0, 654.0, 420.0, 768.0), "Q25 option D"),
    "Q26_stem1": (21, (230.0, 108.0, 395.0, 181.0), "Q26 PVA segment"),
    "Q26_stem2": (21, (323.0, 268.0, 418.0, 328.0), "Q26 inline poly(vinyl acetate)"),
}
# sub-rectangles (PDF pt) painted white before trimming
MASKS = {
    "Q26_stem2": [(409.0, 285.0, 418.0, 305.0)],     # the typed full stop after the image
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
    name = "TMJC_H2_P1_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
