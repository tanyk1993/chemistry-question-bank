"""SAJC 2026 H2 P3: crop the 11 question-side diagram assets from the Word PDF (Claude's snips).

  Q1  Fig 1.1 (graph of log ionisation energy against electrons removed, axis labels in the snip); chloroformyl fluoride
  Q2  4-aminophenol scheme (nitrobenzene -> paracetamol); phenylhydroxylamine + methanol scheme;
      phenylhydroxylamine + ROH scheme
  Q3  phenylboronic acid
  Q5  thiophenol -> 2-phenylthioethanol scheme; benzoyl chloride; Table 5.1 (PET / PIB, whole table as one picture,
      caption typed)
  Q6  collagen portion; Table-like tooth-bleaching scheme (step 1 / step 2 box, as one picture)

Figure captions ("Fig 1.1") and table captions are NOT in the snips; they are typed in the question.
A structure's own name label (chloroformyl fluoride, phenylboronic acid, benzoyl chloride, phenylhydroxylamine ...) IS in the snip.
Each region is given in PDF points (page index is 0-based). Each crop is rendered at 400 dpi,
trimmed to its ink and given a 12 px white border. A crop whose ink touches the region edge is
refused (the box cut through something).

usage: python3 -m ingest.crop_sajc26_p3_questions <word.pdf> <outdir>
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
    "Q1_a":     (1,  (90.0, 248.0, 505.0, 486.0),  "Q1(a) Fig 1.1 log(ionisation energy) against electrons removed"),
    "Q1_b":     (3,  (250.0, 88.0, 368.0, 192.0),  "Q1(b) chloroformyl fluoride"),
    "Q2_biii":  (9,  (66.0, 112.0, 522.0, 266.0),  "Q2(b)(iii) nitrobenzene to paracetamol scheme"),
    "Q2_d":     (11, (96.0, 88.0, 512.0, 230.0),   "Q2(d) phenylhydroxylamine + methanol"),
    "Q2_div":   (13, (96.0, 100.0, 512.0, 240.0),  "Q2(d)(iv) phenylhydroxylamine + ROH"),
    "Q3_b":     (15, (250.0, 276.0, 365.0, 386.0), "Q3(b) phenylboronic acid"),
    "Q5_intro": (21, (70.0, 184.0, 520.0, 268.0),  "Q5 thiophenol to 2-phenylthioethanol"),
    "Q5_b":     (22, (255.0, 88.0, 358.0, 196.0),  "Q5(b) benzoyl chloride"),
    "Q5_bii":   (23, (150.0, 130.5, 460.0, 244.0), "Q5(b)(ii) Table 5.1 PET and PIB (whole table)"),
    "Q6_c":     (29, (56.0, 100.0, 548.0, 232.0),  "Q6(c) portion of collagen"),
    "Q6_d":     (31, (98.0, 126.0, 516.0, 485.0), "Q6(d) tooth-bleaching scheme (steps 1 and 2)"),
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (
        key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "SAJC_H2_P3_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
