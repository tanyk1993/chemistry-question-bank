"""TMJC 2026 H2 P1: crop the 15 answer-side figures from the Word-exported PDF
(Claude's snips). The PDF is the question paper with the school's answer typed in
blue under each question; only figures that belong to a SOLUTION are cropped.

  Q5  ans-1..4  the four graphs the school draws (p-T, p-V, pV-V, V-T); the typed
                "=> Option X is incorrect/correct" text beside each is NOT in the snip
  Q16 ans-1..3  the three reaction schemes (option 1, 2, 3) with cis/trans labels and,
                for option 3, the school's note box
  Q17 ans-1     dexamethasone with the eight chiral centres starred (red stars kept)
  Q24 ans-1     the reduction scheme with the functional groups boxed (school colours kept)
  Q26 ans-1     vinyl alcohol, inline in the Option B sentence
  Q18 ans-1     the school's four-option oxidation table, correct option boxed (the whole answer)
  Q19 ans-1     the elimination scheme with the eliminated groups circled (the whole answer)
  Q21 ans-1     the mechanism to Q (school colours kept; the whole answer)
  Q22 ans-1     compound A with the ketone and CH3CH(OH)- groups boxed and annotated
  Q25 ans-1     the fragments overlapped under the hexapeptide, residues numbered (the whole answer)

Regions are PDF points (page index 0-based); 400 dpi, trimmed to ink, 12 px white
border; ink touching the region edge is refused. The school's blue (and the red stars,
the coloured boxes) are kept: the site shows worked solutions in blue anyway.

usage: python3 -m ingest.crop_tmjc26_p1_answers <word.pdf> <outdir>
Writes the PNGs plus answer_sizes.json (printed widths, for gen_image_sizes).
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
    "Q5_ans-1":  (4, (100.0, 134.0, 231.0, 245.0), "Q5 graph p against T at constant V"),
    "Q5_ans-2":  (4, (100.0, 265.6, 231.0, 374.0), "Q5 graph p against V at constant T"),
    "Q5_ans-3":  (4, (100.0, 406.5, 231.0, 516.0), "Q5 graph pV against V at constant T"),
    "Q5_ans-4":  (4, (100.0, 541.2, 231.0, 652.0), "Q5 graph V against T at constant p"),
    "Q16_ans-1": (11, (104.0, 392.0, 480.0, 481.0), "Q16 option 1 scheme"),
    "Q16_ans-2": (11, (104.0, 495.0, 480.0, 596.0), "Q16 option 2 scheme"),
    "Q16_ans-3": (11, (104.0, 618.5, 480.0, 696.0), "Q16 option 3 scheme with note"),
    "Q17_ans-1": (12, (200.0, 353.5, 425.0, 528.0), "Q17 dexamethasone, chiral centres starred"),
    "Q24_ans-1": (18, (104.0, 574.0, 520.0, 668.0), "Q24 reduction scheme with functional groups boxed"),
    "Q26_ans-1": (21, (210.0, 465.0, 248.0, 524.0), "Q26 vinyl alcohol"),
    "Q18_ans-1": (13, (100.0, 86.0, 520.0, 430.0), "Q18 oxidation products of A-D, correct option boxed"),
    "Q19_ans-1": (13, (100.0, 650.8, 520.0, 772.0), "Q19 elimination scheme, option D"),
    "Q21_ans-1": (16, (160.0, 90.0, 470.0, 300.0), "Q21 mechanism to Q"),
    "Q22_ans-1": (16, (130.0, 692.0, 500.0, 770.0), "Q22 compound A annotated"),
    "Q25_ans-1": (20, (100.0, 90.0, 500.0, 700.0), "Q25 fragments overlapped to the hexapeptide"),
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
    name = "TMJC_H2_P1_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/answer_sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
