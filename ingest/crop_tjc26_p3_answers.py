"""TJC 2026 H2 P3: crop the answer-side figures from the Word-exported PDF ("QP and Ans": question paper with the mark scheme
painted in blue/red) (Claude's snips).

  Q1(b)(ii)  resonance structures of the nitrate ion  (taken from the docx's own PNG, word/media/image7.png: the PDF copy has
             stray school drawing lines over its right-hand bracket)
  Q1(c)(iii) Fig. 1.2 with the SO2 curve (the page as the school printed it)
  Q2(c)(iii) Boltzmann distribution diagram with legend
  Q3(c)(i)   cell diagram for the I3-/I- half-cell
  Q4(c)(ii)  cyclohexene + 4[O] -> hexanedioic acid ; Q4(c)(v) structure of polymer O ; Q4(d)(i) structure of P ;
  Q4(e)(i)   homolysis of benzoyl peroxide ; Q4(e)(ii) the two propagation steps
  Q5(c)(ii)  H-bond diagram of the maleic monoanion ; Q5(d) structures J-N (one grid, labels included)
  Q6(c)(ii)  the two drawings of the enantiomer of D-Threitol ; Q6(d) P (two drawings), Q, S, T and the ECF alternatives for S and T

Red text (school ticks "[1]", the tick glyphs) inside a region is whited out automatically (RED masks). Each crop is rendered
at 400 dpi, trimmed to its ink and given a 12 px white border; ink touching the region edge is refused (the box cut through
something). Typed labels (P:, Q:, "or") are NOT in the snips; they are typed in the solution. The J-N grid keeps its own labels.

usage: python3 ingest/crop_tjc26_p3_answers.py <word.pdf> <docx_media_dir> <outdir>      (writes sizes.json too)
"""
import io
import json
import os
import sys

import pymupdf
from PIL import Image, ImageChops, ImageDraw

DPI = 400
d = pymupdf.open(sys.argv[1])
media = sys.argv[2]
out = sys.argv[3]
os.makedirs(out, exist_ok=True)


def is_red(c):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return r > 180 and g < 90 and b < 90


# file stem -> (page, box, description)
FIGS = {
    "Q1_ans-ciii": (4,  (140.0, 100.0, 530.0, 292.0), "Q1(c)(iii) Fig. 1.2 with the SO2 curve"),
    "Q2_ans-ciii": (7, (125.0, 288.0, 542.0, 492.0), "Q2(c)(iii) Boltzmann distribution diagram"),
    "Q3_ans-ci":   (9,  (115.0, 340.0, 530.0, 508.0), "Q3(c)(i) cell diagram, I3-/I- half-cell"),
    "Q4_ans-cii":  (11, (137.0, 684.0, 364.0, 744.0), "Q4(c)(ii) cyclohexene + 4[O] -> hexanedioic acid"),
    "Q4_ans-cv":   (12, (138.0, 470.0, 360.0, 540.0), "Q4(c)(v) structure of polymer O"),
    "Q4_ans-di":   (13, (146.0, 281.0, 260.0, 400.0), "Q4(d)(i) structure of P"),
    "Q4_ans-ei":   (14, (137.0, 66.0, 482.0, 152.0),  "Q4(e)(i) homolysis of benzoyl peroxide"),
    "Q4_ans-eii":  (14, (145.0, 226.0, 542.0, 392.0), "Q4(e)(ii) first and second propagation steps"),
    "Q5_ans-cii":  (16, (129.0, 683.0, 249.0, 762.0), "Q5(c)(ii) hydrogen bond in the maleic monoanion"),
    "Q5_ans-d":    (18, (65.0, 62.0, 495.0, 308.0),   "Q5(d) structures of J, K, L, M, N"),
    "Q6_ans-cii":  (20, (120.0, 82.0, 330.0, 160.0),  "Q6(c)(ii) enantiomer of D-Threitol (first drawing)"),
    "Q6_ans-cii2": (20, (125.0, 182.0, 330.0, 251.0), "Q6(c)(ii) enantiomer of D-Threitol (alternative drawing)"),
    "Q6_ans-d":    (21, (79.0, 454.0, 184.0, 540.0),  "Q6(d) structure of P"),
    "Q6_ans-d2":   (21, (79.0, 562.0, 200.0, 648.0),  "Q6(d) structure of P (alternative)"),
    "Q6_ans-d3":   (21, (235.0, 454.0, 340.0, 542.0), "Q6(d) structure of Q"),
    "Q6_ans-d4":   (21, (79.0, 686.0, 190.0, 777.0),  "Q6(d) structure of S"),
    "Q6_ans-d5":   (21, (303.0, 686.0, 402.0, 776.0), "Q6(d) structure of T"),
    "Q6_ans-d6":   (22, (78.0, 105.0, 250.0, 182.0),  "Q6(d) alternative S (ECF)"),
    "Q6_ans-d7":   (22, (305.0, 105.0, 500.0, 185.0), "Q6(d) alternative T (ECF)"),
}
sizes, bad = [], []


def finish(key, im, desc):
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    edge = not (bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2)
    if edge:
        bad.append((key, bb, im.size))
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = key.split("_", 1)
    name = "TJC_H2_P3_%s_%s_2026.png" % (qn, s)
    o.save(os.path.join(out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))


for key, (pno, box, desc) in FIGS.items():
    pg = d[pno - 1]
    pix = pg.get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    dr = ImageDraw.Draw(im)
    for b in pg.get_text("dict", clip=pymupdf.Rect(*box))["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if is_red(s["color"]):
                    x0, y0, x1, y1 = s["bbox"]
                    dr.rectangle([(x0 - box[0] - 1) * DPI / 72, (y0 - box[1] - 1) * DPI / 72,
                                  (x1 - box[0] + 1) * DPI / 72, (y1 - box[1] + 1) * DPI / 72], fill=(255, 255, 255))
    if key.startswith("Q6_ans-d") or key == "Q4_ans-di":   # typed labels (P, Q, S, T, or) are not part of the snip
        for b in pg.get_text("dict", clip=pymupdf.Rect(*box))["blocks"]:
            for l in b.get("lines", []):
                for sp in l["spans"]:
                    if sp["text"].strip() in ("P", "Q", "S", "T", "or", "P:"):
                        x0, y0, x1, y1 = sp["bbox"]
                        dr.rectangle([(x0 - box[0] - 2) * DPI / 72, (y0 - box[1] - 2) * DPI / 72,
                                      (x1 - box[0] + 2) * DPI / 72, (y1 - box[1] + 2) * DPI / 72], fill=(255, 255, 255))
    if key in ("Q6_ans-d", "Q6_ans-d3", "Q6_ans-d4", "Q6_ans-d5"):   # table border above the cell: whiten the top strip
        dr.rectangle([0, 0, im.width, 30], fill=(255, 255, 255))
    # any remaining red (school ticks/[1], drawn or text): whiten reddish pixels, dilated to catch the anti-aliased fringe
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(im).astype(int)
    red = ((a[..., 0] - a[..., 1] > 70) & (a[..., 0] - a[..., 2] > 70)).astype(np.uint8) * 255
    red = Image.fromarray(red).filter(ImageFilter.MaxFilter(7))
    im.paste((255, 255, 255), mask=red)
    finish(key, im, desc)

# docx PNG for the resonance picture
im = Image.open(os.path.join(media, "image7.png")).convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
bg.alpha_composite(im)
im = bg.convert("RGB")
# scale to the printed width (about 333 pt) at 400 dpi would upsample a 665 px bitmap; keep native pixels, record printed width
bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
im = im.crop(bb)
o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
o.paste(im, (12, 12))
name = "TJC_H2_P3_Q1_ans-bii_2026.png"
o.save(os.path.join(out, name))
sizes.insert(0, {"path": name, "w": round(im.width * 333 / 665), "h": round(im.height * 333 / 665), "desc": "Q1(b)(ii) resonance structures of the nitrate ion (docx bitmap; printed width approx)"})
print(name, o.size, "(docx bitmap)")
with open(os.path.join(out, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=1)
if bad:
    raise SystemExit("EDGE INK (box cut through something): %r" % (bad,))
