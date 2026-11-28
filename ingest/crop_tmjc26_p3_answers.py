"""TMJC 2026 H2 P3: crop the answer-side figures from the Word-exported mark-scheme PDF (question paper with the school's suggested
solutions overlaid: answers in blue, marking notes/ticks in red, a few green remarks) (Claude's snips, at the user's request).

  Q1(a)(ii)  structural equation with the bond-energy tallies under each species
  Q1(b)(i)   energy cycle for reaction 2
  Q2(b)(ii)  alkaline hydrolysis mechanism with the tetrahedral intermediate, curly arrows, lone pairs, dipoles
  Q2(e)      structures of A, B, C and D
  Q3(d)(i)   completed Cr3+ and Cu+ d-orbital templates
  Q4(c)(i)   ethanoyl chloride, AlCl3
  Q4(c)(iii) ethene -> chloroethanol -> chloroethanoic acid -> F
  Q4(c)(iv)/(v) stage 2 scheme with the alkoxide intermediate and the intramolecular substitution arrows in the box
  Q5(a)(iv)  skeletal structure of 2,2,3,3-tetramethylbutane
  Q5(c)(i)   both radical equations with single-headed curly arrows
  Q5(c)(ii)  ICl + 2-methylpropene mechanism and major product
  Q5(d)(i)   three-step scheme with intermediates I and II drawn in the boxes
The school's RED marking text (ticks, "[1] for ...", scale notes) and GREEN remarks are removed from the pictures at pixel level
(they are typed as notes in the solution where they carry marking information); the answer-line dots under the answers are removed
too. Blue answers and black question drawings are kept.
Each region is in PDF points (page number 1-based), rendered at 400 dpi, trimmed to its ink with a 12 px white border; a crop whose
ink touches the region edge is refused.

usage: python3 crop_tmjc26_p3_answers.py <ms.pdf> <outdir>      (writes sizes.json too)
"""
import io, json, os, sys
import numpy as np
import pymupdf
from PIL import Image
from scipy import ndimage

DPI = 400
K = DPI / 72.0
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
os.makedirs(out, exist_ok=True)

FIGS = {
    "Q1_ans-aii":  (2,  (115.0, 388.0, 535.0, 530.0), "Q1(a)(ii) structural equation with bond-energy tallies"),
    "Q1_ans-bi":   (3,  (95.0, 324.0, 552.0, 442.0),  "Q1(b)(i) energy cycle for reaction 2"),
    "Q2_ans-bii":  (9,  (112.0, 288.0, 548.0, 546.0), "Q2(b)(ii) alkaline hydrolysis mechanism"),
    "Q2_ans-e":    (11, (118.0, 440.0, 525.0, 578.0), "Q2(e) structures of A, B, C and D"),
    "Q3_ans-di":   (14, (150.0, 415.0, 525.0, 492.0), "Q3(d)(i) completed Cr3+ and Cu+ templates"),
    "Q4_ans-ci":   (17, (130.0, 672.0, 300.0, 726.0), "Q4(c)(i) ethanoyl chloride, AlCl3"),
    "Q4_ans-ciii": (18, (120.0, 484.0, 500.0, 705.0), "Q4(c)(iii) synthetic route to compound F"),
    "Q4_ans-civ":  (19, (140.0, 300.0, 490.0, 683.0), "Q4(c)(iv)(v) stage 2 with the alkoxide intermediate and mechanism"),
    "Q5_ans-aiv":  (22, (272.0, 445.6, 358.0, 490.0), "Q5(a)(iv) 2,2,3,3-tetramethylbutane"),
    "Q5_ans-ci":   (24, (95.0, 176.0, 506.8, 326.5),  "Q5(c)(i) acyloxy radical equations with single-headed arrows"),
    "Q5_ans-cii":  (24, (88.0, 505.0, 511.0, 762.0),  "Q5(c)(ii) ICl addition mechanism and major product"),
    "Q5_ans-di":   (25, (88.0, 300.0, 532.0, 545.0),  "Q5(d)(i) three-step scheme, intermediates drawn"),
}
# extra white masks (pt): answer-line dots that sit right under the box's top border and so merge into it
MASKS = {"Q2_ans-bii": [(360.0, 295.0, 503.0, 308.0)],   # the school's stray square bracket above the intermediate
         "Q5_ans-cii": [(326.0, 662.4, 506.0, 665.0)]}

def dotlines(page, box):
    """(y0, y1) in pt of every run of answer-line dots inside the box"""
    ys = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                t = sp["text"].strip()
                if len(t) >= 5 and set(t) <= set(".… "):
                    bb = sp["bbox"]
                    if bb[3] >= box[1] - 2 and bb[1] <= box[3] + 2:
                        ys.append((bb[1], bb[3]))
    return ys

sizes, bad = [], []
for key, (pno, box, desc) in FIGS.items():
    page = d[pno - 1]
    pix = page.get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    a = np.array(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 170) & (r - np.maximum(g, b) > 45)
    green = (g - np.maximum(r, b) > 35) & (g > 90)
    pink = (r > 200) & (r - np.maximum(g, b) > 14)          # anti-aliased halo of the red/green marking text
    gl = (g > 170) & (g - np.maximum(r, b) > 14)
    m = red | green | pink | gl
    m = ndimage.binary_dilation(m, structure=np.ones((3, 3)), iterations=2) & ~((b - np.maximum(r, g)) > 60)
    a[m] = 255
    # answer-line dots: rows of >= 8 tiny blobs sharing a y (text-based bands plus pixel-pattern detection)
    dark = (a.max(axis=2) < 235)
    lab, n = ndimage.label(dark, structure=np.ones((3, 3)))
    if n:
        objs = ndimage.find_objects(lab)
        bands = [((y0 - box[1]) * K - 3, (y1 - box[1]) * K + 3) for (y0, y1) in dotlines(page, box)]
        small = []
        for idx, sl in enumerate(objs, 1):
            h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
            if h <= 2.4 * K and w <= 2.4 * K:
                small.append((idx, sl, (sl[0].start + sl[0].stop) / 2))
        cys = np.array([c for _, _, c in small]) if small else np.array([])
        for idx, sl, cy in small:
            in_row = int((np.abs(cys - cy) <= 2.5).sum()) >= 8
            if in_row or any(lo <= cy <= hi for lo, hi in bands):
                a[sl][lab[sl] == idx] = 255
    for (mx0, my0, mx1, my1) in MASKS.get(key, []):
        a[round((my0 - box[1]) * K):round((my1 - box[1]) * K), round((mx0 - box[0]) * K):round((mx1 - box[0]) * K)] = 255
    im = Image.fromarray(a.astype("uint8"))
    ink = np.array(im).min(axis=2) < 235
    ys, xs = np.where(ink)
    assert len(ys), key
    bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    if not (bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2):
        bad.append((key, bb, im.size))
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = key.split("_", 1)
    name = "TMJC_H2_P3_%s_%s_2026.png" % (qn, s)
    o.save(os.path.join(out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open(os.path.join(out, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=1)
if bad:
    print("EDGE INK (box cut through something): %r" % (bad,))
