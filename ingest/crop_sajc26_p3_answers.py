"""SAJC 2026 H2 P3: crop the 16 answer-side figures from the Word-exported answers PDF (Claude's snips).

  Q1(b)(ii)   handwritten sigma / pi orbital overlap diagram
  Q1(b)(iii)  handwritten electron-in-box diagram (sp2 boxes and p box)
  Q1(c)(v)    handwritten ClF3 diagrams (two versions, "or" included)
  Q2(a)       Daniell cell diagram
  Q2(c)(iv)   side-product structures (two, "OR" included)
  Q2(d)(i)    three structures (phenylhydroxylamine, 4-aminophenol, N-methyl-4-aminophenol) with names
  Q2(d)(v)    N-isopropyl-4-aminophenol
  Q3(b)(ii)   C6H5B(OH)2 + NH3 adduct
  Q3(b)(iii)  boroxine structure
  Q4(b)       F, G and the Geraniol | E structure table (reasoning table is typed)
  Q5(a)(ii)   SN2 mechanism with transition state
  Q5(b)(i)    structure of X
  Q5(b)(ii)   methylbenzene -> benzoic acid -> benzoyl chloride (reagent lines are typed)
  Q6(c)(ii)   displayed formula of alanine
  Q6(c)(iv)   isoleucine and threonine with chiral carbons starred
  Q6(d)(i)    step 1 with the four extra curly arrows

The school's difficulty letters (L/M/H, A/B) in the right margin are outside every box.
Each region is in PDF points (page index 0-based), rendered at 400 dpi, trimmed to its ink with a 12 px
white border; a crop whose ink touches the region edge is refused.
usage: python3 -m ingest.crop_sajc26_p3_answers <answers.pdf> <outdir>   (writes sizes.json too)
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
    "Q1_ans-bii":   (1,  (118.0, 474.0, 380.0, 610.0), "Q1(b)(ii) sigma and pi overlap diagram"),
    "Q1_ans-biii":  (2,  (190.0, 62.0, 395.0, 160.0),  "Q1(b)(iii) electron boxes for sp2 and p"),
    "Q1_ans-cv":    (3,  (135.0, 462.0, 485.0, 604.0), "Q1(c)(v) ClF3 shape and polarity"),
    "Q2_ans-a":     (4,  (165.0, 250.0, 475.0, 412.0), "Q2(a) Daniell cell"),
    "Q2_ans-civ":   (6,  (120.0, 190.0, 335.0, 344.0), "Q2(c)(iv) side-product structures"),
    "Q2_ans-di":    (7,  (120.0, 80.0, 462.0, 212.0),  "Q2(d)(i) three amines with names"),
    "Q2_ans-dv":    (8,  (270.0, 588.0, 365.0, 721.0), "Q2(d)(v) N-isopropyl-4-aminophenol"),
    "Q3_ans-bii":   (10, (262.0, 590.0, 380.0, 690.0), "Q3(b)(ii) boron-ammonia adduct"),
    "Q3_ans-biii":  (11, (232.0, 252.0, 408.0, 404.0), "Q3(b)(iii) boroxine"),
    "Q4_ans-b":     (14, (105.0, 78.0, 515.0, 384.0),  "Q4(b) F, G and geraniol / E structures"),
    "Q5_ans-aii":   (15, (120.0, 498.0, 400.0, 658.0), "Q5(a)(ii) SN2 mechanism"),
    "Q5_ans-bi":    (16, (122.0, 236.0, 310.0, 308.0), "Q5(b)(i) compound X"),
    "Q5_ans-bii":   (16, (120.0, 398.0, 475.0, 470.0), "Q5(b)(ii) methylbenzene to benzoyl chloride"),
    "Q6_ans-cii":   (22, (118.0, 470.0, 228.0, 552.0), "Q6(c)(ii) alanine displayed formula"),
    "Q6_ans-civ":   (23, (215.0, 100.0, 420.0, 205.0), "Q6(c)(iv) isoleucine and threonine with chiral C starred"),
    "Q6_ans-di":    (24, (120.0, 246.0, 470.0, 493.0), "Q6(d)(i) curly arrows added to step 1"),
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
    name = "SAJC_H2_P3_%s_%s_2026.png" % (qn, s)
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
