"""TJC 2026 H2 P3: crop the 12 question-side diagram assets from the Word PDF (Claude's snips).

  Q1  Fig 1.1 (nitrate ion, electron arrangement); Fig 1.2 (pV/RT against p, ideal gas and CO2)
  Q2  (a) the reaction CH3COCH3 + 2CH3OH -> A + H2O, with the structure of A
  Q4  Fig 4.1 (cyclohexene -> epoxide); Fig 4.2 (epoxide -> cyclohexane-1,2-diol); Fig 4.3 (polymer O pathway);
      Fig 4.4 (cyclohexene -> cyclohexanone oxime); benzoyl peroxide; Fig 4.5 (back-biting)
  Q5  (c) fumaric acid and maleic acid with their pKa values
  Q6  (c) D-Threitol (3-D structure); (d) the structure of R

The school's file is the question paper with the mark scheme painted into it (answers blue, notes red), so two crops need care:
  * Fig 1.2 carries the school's blue SO2 answer curve and its "SO2" label. They are removed from a COPY of page 4
    (vector redaction of the blue path and the blue text only; no fill, so the black curve, the ideal-gas line and the axes
    are untouched) before the page is rendered.
  * Fig 4.2 is printed TWICE in the school's file (two OLE pictures one under the other; the first labels the epoxide
    "cyclohexene oxide", the second "epoxide", as in Fig 4.1 and in the question text). Q4_bi is the second one
    ("epoxide"); the first one is written to the sub-folder not_for_upload/ as a spare.
The mark scheme's own drawings (the cell diagram, the Boltzmann sketch, structures J-N, P-T ...) are NOT question figures
and are not cropped. Figure captions ("Fig. 1.1") are NOT in the snips; they are typed in the question. A structure's own
name label (cyclohexene, epoxide, benzoyl peroxide, D-Threitol, fumaric acid + pKa lines) IS in the snip.
Each region is given in PDF points (page number is 1-based). Each crop is rendered at 400 dpi, trimmed to its ink and
given a 12 px white border. A crop whose ink touches the region edge is refused (the box cut through something).

usage: python3 -m ingest.crop_tjc26_p3_questions <word.pdf> <outdir>
Writes the PNGs plus sizes.json (printed widths, for gen_image_sizes).
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
os.makedirs(os.path.join(out, "not_for_upload"), exist_ok=True)

# ---- page 4: strip the school's blue SO2 answer (path + label) from the in-memory copy only
pg4 = d[3]
n_red = 0
for dr in pg4.get_drawings():
    if dr.get("color") == (0.0, 0.0, 1.0):
        r = dr["rect"]
        pg4.add_redact_annot(pymupdf.Rect(r.x0 - 0.6, r.y0 - 0.6, r.x1 + 0.6, r.y1 + 0.6), fill=False)
        n_red += 1
for b in pg4.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            if s["color"] == 0xFF and s["text"].strip() and s["bbox"][1] < 300:      # blue "SO2" label, Fig 1.2 only
                r = pymupdf.Rect(s["bbox"])
                pg4.add_redact_annot(pymupdf.Rect(r.x0 - 0.3, r.y0 - 0.3, r.x1 + 0.3, r.y1 + 0.3), fill=False)
                n_red += 1
assert n_red == 3, n_red          # 1 blue path + the two blue text spans "SO", "2"
pg4.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                     text=pymupdf.PDF_REDACT_TEXT_REMOVE)
assert not any(dr.get("color") == (0.0, 0.0, 1.0) for dr in pg4.get_drawings()), "blue path still present"

# file stem -> (page number, (x0, y0, x1, y1) in pt, description, sub-folder or "")
FIGS = {
    "Q1_b":   (2,  (270.0, 546.0, 400.0, 606.0),  "Q1(b) Fig. 1.1 nitrate ion", ""),
    "Q1_ci":  (4,  (140.0, 100.0, 530.0, 292.0),  "Q1(c) Fig. 1.2 pV/RT against p (ideal gas, CO2)", ""),
    "Q2_a":   (5,  (170.0, 100.0, 480.0, 162.0),  "Q2(a) propanone + methanol -> A + H2O", ""),
    "Q4_b":   (10, (200.0, 603.0, 470.0, 703.0),  "Q4(b) Fig. 4.1 cyclohexene -> epoxide", ""),
    "Q4_bi":  (11, (190.0, 203.0, 470.0, 311.0),  "Q4(b)(i) Fig. 4.2 epoxide -> cyclohexane-1,2-diol (second copy, 'epoxide')", ""),
    "Q4_bi_first_copy": (11, (190.0, 84.0, 470.0, 200.0), "Q4 Fig. 4.2 first copy ('cyclohexene oxide'), spare", "not_for_upload"),
    "Q4_cii": (12, (100.0, 100.0, 545.0, 225.0),  "Q4(c)(ii) Fig. 4.3 pathway to polymer O", ""),
    "Q4_d":   (13, (100.0, 85.0, 545.0, 214.0),   "Q4(d) Fig. 4.4 cyclohexene -> cyclohexanone oxime", ""),
    "Q4_ei":  (13, (220.0, 666.0, 480.0, 771.0),  "Q4(e)(i) benzoyl peroxide", ""),
    "Q4_eii": (14, (130.0, 458.0, 470.0, 523.0),  "Q4(e)(ii) Fig. 4.5 back-biting", ""),
    "Q5_c":   (16, (150.0, 403.0, 520.0, 552.0),  "Q5(c) fumaric acid and maleic acid + pKa values", ""),
    "Q6_c":   (19, (230.0, 590.0, 430.0, 684.0),  "Q6(c) D-Threitol 3-D structure", ""),
    "Q6_d":   (20, (70.0, 640.0, 330.0, 712.0),   "Q6(d) structure of R", ""),
}
sizes = []
for key, (pno, box, desc, sub) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "TJC_H2_P3_%s_2026.png" % key
    o.save(os.path.join(out, sub, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    if not sub:
        sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(os.path.join(sub, name), o.size, "printed approx %d x %d pt" % (w, h))
with open(os.path.join(out, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=1)
