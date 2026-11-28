"""TMJC 2026 H2 P2: crop the answer-side figures from the Word-exported PDF (question paper with the mark scheme overlaid in
blue / red / green, teal curve) (Claude's snips).

  Q1(d)     ion-dipole drawing (Cl- ... H-O-H)
  Q2(a)(iii) Fig. 2.1 with Run B and the half-life construction lines (the school's red dashes for Run A are part of it)
  Q2(b)(iv) Fig. 2.2 with the school's curve
  Q2(b)(v)  Boltzmann distribution diagram (axes, curve, hatched areas, Ea labels, legend: all drawn by the school)
  Q3(d)(ii) [Ni(NH3)6]2+
  Q4(a)     cis and trans isomers (amine as NH3+)
  Q4(c)(ii) nucleophilic addition mechanism, steps 1 and 2 (the school's green/red "marking points" boxes are whited out;
            they are typed as notes in the solution)
  Q4(d)     four-step scheme with every box filled in
  Q5(a)(i)  predominant species at pH 3.0
  Q5(b)     Table 5.1 completed (answers in the cells; the red [1] ticks are whited out)
  Q5(c)(i)  Fig. 5.1 with the hydrogen bond, lone pair, dipoles and label

The pictures keep the school's blue, red dashed and teal drawing colours; only the red MARKING text (ticks, "[1]", notes) is masked.
Typed labels that sit above a drawing ("cis-trans isomerism", "Nucleophilic addition") are masked and typed in the solution.
Each region is in PDF points (page number 1-based), rendered at 400 dpi, trimmed to its ink with a 12 px white border; a crop whose ink
touches the region edge is refused.

usage: python3 -m ingest.crop_tmjc26_p2_answers <word.pdf> <outdir>      (writes sizes.json too)
"""
import io
import json
import os
import sys

import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
os.makedirs(out, exist_ok=True)

# file stem -> (page, box, description, [white masks])
FIGS = {
    "Q1_ans-d":    (4,  (180.0, 114.0, 312.0, 228.0), "Q1(d) ion-dipole interaction between Cl- and water", []),
    "Q2_ans-aiii": (5,  (70.0, 226.0, 560.0, 575.0),  "Q2(a)(iii) Fig. 2.1 with Run B and the half-life constructions", []),
    "Q2_ans-biv":  (7,  (185.0, 106.0, 406.0, 241.0), "Q2(b)(iv) Fig. 2.2 rate against [OH-] (the school's curve)", []),
    "Q2_ans-bv":   (7,  (122.0, 366.0, 506.0, 562.0), "Q2(b)(v) Boltzmann distribution, catalysed and uncatalysed", []),
    "Q3_ans-dii":  (12, (232.0, 566.0, 392.0, 700.0), "Q3(d)(ii) octahedral [Ni(NH3)6]2+", [(382.0, 680.0, 402.0, 699.0)]),
    "Q4_ans-a":    (14, (95.0, 246.0, 320.0, 358.0),  "Q4(a) cis and trans isomers", [(96.0, 246.0, 235.0, 260.0)]),
    "Q4_ans-cii":  (15, (112.0, 288.0, 500.0, 450.0), "Q4(c)(ii) mechanism of step I", [(444.0, 270.0, 582.0, 419.0)]),
    "Q4_ans-d":    (16, (66.0, 155.0, 575.0, 636.0),  "Q4(d) four-step synthesis of dopamine, answers filled in", []),
    "Q5_ans-ai":   (17, (205.0, 250.0, 368.0, 282.0), "Q5(a)(i) predominant species at pH 3.0", []),
    "Q5_ans-b":    (18, (60.0, 154.0, 540.0, 462.0),  "Q5(b) Table 5.1 completed",
                    [(515.0, 453.4, 545.0, 480.0), (186.0, 253.0, 207.0, 271.0), (403.0, 426.0, 425.0, 444.0), (440.0, 383.0, 532.0, 401.0)]),
    "Q5_ans-ci":   (18, (128.0, 546.0, 338.0, 650.0), "Q5(c)(i) hydrogen bonding between two nylon-6 chains", []),
}
EDGE_OK = {}
sizes, bad = [], []
for key, (pno, box, desc, masks) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    k = DPI / 72.0
    for (mx0, my0, mx1, my1) in masks:
        im.paste((255, 255, 255), (round((mx0 - box[0]) * k), round((my0 - box[1]) * k), round((mx1 - box[0]) * k), round((my1 - box[1]) * k)))
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    if not (bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2):
        bad.append((key, bb, im.size))
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = key.split("_", 1)
    name = "TMJC_H2_P2_%s_%s_2026.png" % (qn, s)
    o.save(os.path.join(out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open(os.path.join(out, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=1)
if bad:
    raise SystemExit("EDGE INK (box cut through something): %r" % (bad,))
