"""SAJC 2026 H2 P2: crop the 13 question-side diagram assets from the Word PDF (Claude's snips).

  Q2  Fig 2.1 (blank energy axes with the d-orbital levels)
  Q3  scheme X -> A + B + D; Fig 3.1 (ethanoyl chloride hydrolysis); blank axes for the
      [ethanoyl chloride] against time sketch
  Q4  buta-1,3-diene; blank energy axes; Fig 4.1 (Diels-Alder); Fig 4.2 (cis-1,4-polybutadiene);
      buta-1,2-diene; Fig 4.3 (carbon skeleton for the p orbitals)
  Q5  diacetone alcohol scheme; Table 5.2 (whole table as one picture, caption typed);
      scheme T -> U + V

Figure captions ("Fig 2.1") and table captions are NOT in the snips; they are typed in the question.
A structure's own name label (buta-1,3-diene, cis-1,4-polybutadiene) IS in the snip.
Each region is given in PDF points (page index is 0-based). Each crop is rendered at 400 dpi,
trimmed to its ink and given a 12 px white border. A crop whose ink touches the region edge is
refused (the box cut through something).

usage: python3 -m ingest.crop_sajc26_p2_questions <word.pdf> <outdir>
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
    "Q2_aii":   (5,  (195.0, 316.0, 440.0, 474.0), "Q2(a)(ii) Fig 2.1 energy axes with d-orbital levels"),
    "Q3_intro": (9,  (118.0, 104.0, 470.0, 238.0), "Q3 acid hydrolysis of X giving A, B and D"),
    "Q3_b":     (10, (85.0, 116.0, 505.0, 228.0),  "Q3(b) Fig 3.1 hydrolysis of ethanoyl chloride"),
    "Q3_biv":   (11, (125.0, 130.0, 455.0, 342.0), "Q3(b)(iv) blank axes [ethanoyl chloride] against time"),
    "Q4_intro": (13, (250.0, 145.0, 345.0, 203.0), "Q4 buta-1,3-diene"),
    "Q4_bii":   (14, (125.0, 186.0, 240.0, 452.0), "Q4(b)(ii) blank energy axis"),
    "Q4_c":     (15, (190.0, 145.0, 425.0, 222.0), "Q4(c) Fig 4.1 Diels-Alder reaction"),
    "Q4_d":     (16, (160.0, 442.0, 470.0, 553.0), "Q4(d) Fig 4.2 cis-1,4-polybutadiene"),
    "Q4_e":     (17, (255.0, 90.0, 365.0, 152.0),  "Q4(e) buta-1,2-diene"),
    "Q4_eii":   (17, (230.0, 358.0, 415.0, 456.0), "Q4(e)(ii) Fig 4.3 carbon skeleton of buta-1,2-diene"),
    "Q5_c":     (21, (175.0, 116.0, 440.0, 200.0), "Q5(c) propanone to diacetone alcohol"),
    "Q5_c2":    (21, (58.0, 247.8, 538.0, 531.0),  "Q5(c) Table 5.2 aldol stages (whole table)"),
    "Q5_ciii":  (22, (160.0, 104.0, 490.0, 236.0), "Q5(c)(iii) T to U and V"),
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
    name = "SAJC_H2_P2_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
