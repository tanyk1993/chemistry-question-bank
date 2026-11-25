"""TJC 2026 H2 P2: crop the 8 question-side diagram assets from the Word PDF (Claude's snips).

  Q4  intro scheme (propanal + methylamine -> imine); Fig. 4.1 (mechanism); Fig. 4.2 (Maillard reaction, asparagine
      -> acrylamide); Fig. 4.3 (synthesis of imine R, with the two empty boxes for L and R)
  Q6  Fig. 6.1 (EMAR cell); Fig. 6.2 (ethane-1,2-diamine + CO2 -> carbamate); the same scheme repeated in (d);
      amine X

The mark scheme's own drawings (blue/red answers; e.g. the PCl3 shape, the E+ structure, the SN2 mechanism) are NOT
question figures and are not cropped here. Figure captions ("Fig. 4.1") are NOT in the snips; they are typed in the
question. A structure's own name label (amine X, ethane-1,2-diamine, carbamate) IS in the snip.
Each region is given in PDF points (page number is 1-based). Each crop is rendered at 400 dpi, trimmed to its ink and
given a 12 px white border. A crop whose ink touches the region edge is refused (the box cut through something).

usage: python3 -m ingest.crop_tjc26_p2_questions <word.pdf> <outdir>
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

# file stem -> (page number, (x0, y0, x1, y1) in pt, description)
FIGS = {
    "Q4_intro":  (7,  (85.0, 96.0, 545.0, 141.0),   "Q4 propanal + methylamine to imine"),
    "Q4_a":      (7,  (100.0, 170.0, 545.0, 441.0), "Q4(a) Fig. 4.1 mechanism"),
    "Q4_b":      (8,  (100.0, 141.0, 545.0, 468.0), "Q4(b) Fig. 4.2 Maillard reaction"),
    "Q4_c":      (9,  (100.0, 442.0, 545.0, 714.0), "Q4(c) Fig. 4.3 synthesis of imine R"),
    "Q6_intro":  (13, (85.0, 140.0, 545.0, 450.0),  "Q6 Fig. 6.1 EMAR cell"),
    "Q6_intro2": (13, (85.0, 530.0, 545.0, 598.0),  "Q6 Fig. 6.2 carbamate formation"),
    "Q6_d":      (15, (85.0, 165.0, 545.0, 252.0),  "Q6(d) carbamate formation scheme"),
    "Q6_d2":     (15, (85.0, 268.0, 545.0, 362.0),  "Q6(d) amine X"),
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (key, bb, im.size)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "TJC_H2_P2_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
