"""TJC 2026 H2 P2: crop the answer-side figures from the Word-exported PDF ("H2 P2 Review": question paper with the mark
scheme inline in blue/red) (Claude's snips).

  Q2(b)(iii)  the two energy cycles (with the school's "OR" between them)
  Q3(a)(i)    PCl3 shape drawing (the school's 3D drawing with the lone pair; the stock ball-and-stick picture beside it is
              NOT cropped: it shows a four-ligand molecule and carries a stock-photo watermark)
  Q3(a)(iii)  H3PO3 dot-and-cross diagram (handwritten)
  Q3(b)(i)    structure of D
  Q3(b)(iii)  cis and trans isomers of D
  Q3(b)(iv)   equation: butanone + 3I2 + 4NaOH -> sodium propanoate + CHI3 + 3NaI + 3H2O
  Q4(a)(ii)   structure of E+ ; red note: the curly-arrow picture for step 4
  Q4(b)(ii)   G with the three curly arrows
  Q4(b)(iii)  structure of the alpha-amino acid ; red note: "pattern recognition" picture
  Q4(c)(ii)   L ; R ; red note: condensation of two Q molecules
  Q4(d)       SN2 mechanism (two rows)
  Q6(a)       half-equation at the positive terminal

The school's red mark ticks "[1]" that sit beside a drawing are whited out (MASKS). Region boxes are in PDF points (page
number 1-based); each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border; ink touching the
region edge is refused. Typed labels (L:, R:, Note:) are NOT in the snips; they are typed in the solution.

usage: python3 ingest/crop_tjc26_p2_answers.py <word.pdf> <outdir>      (writes sizes.json too)
"""
import io
import json
import sys

import pymupdf
from PIL import Image, ImageChops, ImageDraw

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]

# file stem -> (page, box, description, [white masks])
FIGS = {
    "Q2_ans-biii":  (4,  (140.0, 222.0, 482.0, 478.0), "Q2(b)(iii) energy cycles (both versions, with OR)", []),
    "Q3_ans-ai":    (5,  (140.0, 158.0, 300.0, 245.0), "Q3(a)(i) shape of PCl3", [(222.0, 224.0, 247.0, 244.0)]),
    "Q3_ans-aiii":  (5,  (140.0, 455.0, 340.0, 552.0), "Q3(a)(iii) dot-and-cross diagram of H3PO3", [(306.0, 531.0, 340.0, 550.0)]),
    "Q3_ans-bi":    (6,  (140.0, 205.0, 300.0, 300.0), "Q3(b)(i) structure of D", [(240.0, 288.0, 262.0, 304.0)]),
    "Q3_ans-biii":  (6,  (140.0, 441.0, 480.0, 532.0), "Q3(b)(iii) cis and trans isomers of D", []),
    "Q3_ans-biv":   (6,  (140.0, 636.0, 552.0, 680.0), "Q3(b)(iv) equation with alkaline aqueous iodine", []),
    "Q4_ans-aii":   (7,  (140.0, 569.0, 300.0, 618.0), "Q4(a)(ii) structure of E+", [(259.0, 606.0, 282.0, 622.0)]),
    "Q4_ans-aii2":  (7,  (175.0, 622.0, 540.0, 706.0), "Q4(a)(ii) note: curly arrows for step 4", []),
    "Q4_ans-bii":   (8,  (140.0, 668.0, 540.0, 748.0), "Q4(b)(ii) G with three curly arrows", []),
    "Q4_ans-biii":  (9,  (140.0, 122.0, 300.0, 214.0), "Q4(b)(iii) the alpha-amino acid", [(226.0, 197.0, 246.0, 213.0)]),
    "Q4_ans-biii2": (9,  (140.0, 252.0, 540.0, 392.0), "Q4(b)(iii) note: pattern recognition", []),
    "Q4_ans-cii":   (10, (157.5, 262.0, 300.0, 316.0), "Q4(c)(ii) structure of L", [(237.5, 297.0, 262.0, 313.0)]),
    "Q4_ans-cii2":  (10, (159.0, 336.0, 300.0, 452.0), "Q4(c)(ii) structure of R", [(212.0, 434.0, 236.0, 450.0)]),
    "Q4_ans-cii3":  (10, (140.0, 470.0, 540.0, 590.0), "Q4(c)(ii) note: condensation of two Q", []),
    "Q4_ans-d":     (11, (85.0, 56.0, 545.0, 215.0),   "Q4(d) SN2 mechanism", []),
    "Q6_ans-a":     (14, (85.0, 56.0, 540.0, 104.0),   "Q6(a) half-equation at the positive terminal", [(439.0, 87.0, 460.0, 103.0)]),
}
sizes, bad = [], []
for key, (pno, box, desc, masks) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    if masks:
        dr = ImageDraw.Draw(im)
        for (x0, y0, x1, y1) in masks:
            dr.rectangle([(x0 - box[0]) * DPI / 72, (y0 - box[1]) * DPI / 72, (x1 - box[0]) * DPI / 72, (y1 - box[1]) * DPI / 72],
                         fill=(255, 255, 255))
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    if not (bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2):
        bad.append((key, bb, im.size))          # ink touches the region edge: the box cut through something
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = key.split("_", 1)
    name = "TJC_H2_P2_%s_%s_2026.png" % (qn, s)
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
if bad:
    raise SystemExit("EDGE INK (box cut through something): %r" % (bad,))
