"""TMJC 2026 H2 P2: crop the 13 question-side diagram assets from the Word PDF (Claude's snips, at the user's request).

The school's PDF is the question paper with the mark scheme overlaid in blue / red / green (and a teal curve). The answer
layer is first stripped at the content-stream level (strip_answer_colours.clean), so every crop below shows only what the
candidate was given; the Fig. 2.1 "Run B" white label box is dropped explicitly.
  Q2  Fig. 2.1 (Run A graph on its grid, no constructions); Fig. 2.2 (blank rate vs [OH-] axes, x-axis label included)
  Q3  Fig. 3.1 (battery picture); (d) separation flow chart
  Q4  noradrenaline + dopamine; 3,4-dihydroxybenzaldehyde (O1 labelled); (c) scheme step I / step II;
      (d) four-step scheme with the boxes left EMPTY
  Q5  6-aminohexanoic acid; leucine; Table 5.1 (given cells only); Fig. 5.1 (two nylon-6 chains, no H bond drawn)
  Q6  (d) nucleation picture
NOT cropped: Q2(b)(v) Boltzmann diagram. It is drawn in black but it is the school's ANSWER (axes, curve, shaded areas
and Ea labels; the question prints only a blank space above the answer lines). Captions ("Fig. 2.1", "Table 5.1") are typed
in the question, not in the snips. A structure's own name label IS in the snip.
Each region is in PDF points (page number 1-based). Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px
white border. A crop whose ink touches the region edge is refused (the box cut through something).

usage: python3 -m ingest.crop_tmjc26_p2_questions <word.pdf> <outdir>
Writes the PNGs plus sizes.json (printed widths, for gen_image_sizes).
"""
import io
import json
import os
import sys

import pymupdf
from PIL import Image, ImageChops

from ingest import strip_answer_colours

DPI = 400
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
clean_pdf = os.path.join(out, "_question_layer.pdf")
strip_answer_colours.clean(src, clean_pdf, {5: [(143.95, 495.26, 55.35, 22.35)]})
d = pymupdf.open(clean_pdf)

# file stem -> (page number, (x0, y0, x1, y1) in pt, description)
FIGS = {
    "Q2_a":      (5,  (70.0, 226.0, 560.0, 575.0),  "Q2(a) Fig. 2.1 [OCl-] against time, Run A"),
    "Q2_biv":    (7,  (180.0, 110.0, 406.0, 241.0), "Q2(b)(iv) Fig. 2.2 axes, rate against [OH-]"),
    "Q3_intro":  (9,  (100.0, 110.5, 532.0, 296.0), "Q3 Fig. 3.1 NMC battery"),
    "Q3_d":      (12, (125.0, 168.0, 490.0, 424.0), "Q3(d) separation of Mn2+ and Ni2+ flow chart"),
    "Q4_intro":  (14, (120.0, 108.0, 520.0, 200.0), "Q4 noradrenaline and dopamine"),
    "Q4_a":      (14, (225.0, 440.0, 430.0, 536.0), "Q4 3,4-dihydroxybenzaldehyde"),
    "Q4_c":      (15, (68.0, 90.0, 548.0, 180.0),   "Q4(c) noradrenaline synthesis, steps I and II"),
    "Q4_d":      (16, (66.0, 155.0, 575.0, 636.0),  "Q4(d) four-step synthesis of dopamine (blank boxes)"),
    "Q5_intro":  (17, (200.0, 98.0, 410.0, 152.0),  "Q5 6-aminohexanoic acid"),
    "Q5_aii":    (17, (228.0, 330.0, 385.0, 414.0), "Q5(a)(ii) leucine"),
    "Q5_b":      (18, (60.0, 154.0, 540.0, 462.0),  "Q5(b) Table 5.1 (given cells only)"),
    "Q5_ci":     (18, (128.0, 546.0, 362.0, 650.0), "Q5(c)(i) Fig. 5.1 two nylon-6 chains"),
    "Q6_d":      (23, (58.0, 148.5, 572.0, 300.0),  "Q6(d) nucleation of hydrated ions"),
}
# rects (pt) whitened after rendering: the printed mark "[3]" sits against the foot of Table 5.1
# a raster picture whose own edge is the region edge (the box starts just under the line of text above it)
EDGE_OK = {"Q6_d": "top"}
MASKS = {"Q5_b": [(515.0, 453.4, 545.0, 480.0)]}
# first version of Q2_biv stopped at x = 370 pt and lost the "[OH-]" axis label (x 374-401 pt): re-snipped, new file name (CDN cache)
NAME = {"Q2_biv": "TMJC_H2_P2_Q2_biv_v2_2026.png"}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    for (mx0, my0, mx1, my1) in MASKS.get(key, []):
        k = DPI / 72.0
        im.paste((255, 255, 255), (round((mx0 - box[0]) * k), round((my0 - box[1]) * k), round((mx1 - box[0]) * k), round((my1 - box[1]) * k)))
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and (bb[1] > 2 or EDGE_OK.get(key) == "top") and bb[2] < im.width - 2 and bb[3] < im.height - 2, (key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = NAME.get(key, "TMJC_H2_P2_%s_2026.png" % key)
    o.save(os.path.join(out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open(os.path.join(out, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=1)
