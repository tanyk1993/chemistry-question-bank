"""RVHS 2026 H2 P2: crop the 5 answer-side figures from the Word-exported solutions PDF (400 dpi, trimmed, 12 px border).
The school's 1(d) mechanism sits on a yellow highlight; the yellow is removed (blue channel raised to min(R,G), which turns
yellow-on-black anti-aliasing into grey) so the figure shows on white.
usage: python3 -m ingest.crop_rvhs26_p2_answers <soln.pdf> <outdir>"""
import io, sys
import numpy as np
import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
BOXES = {  # file slot: (page 1-based, box pt, whiten yellow)
    "Q1_ans-d":    (1, (115, 478, 522, 763), True),
    "Q1_ans-eii":  (2, (143, 128, 540, 285), False),
    "Q2_ans-ci":   (2, (115, 436.5, 540, 686), False),
    "Q2_ans-dii":  (3, (143, 70, 540, 165), False),
    "Q3_ans-diii": (4, (142, 388, 500, 574), False),
}
for slot, (pno, box, yellow) in BOXES.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    if yellow:
        a = np.array(im).astype(int)
        a[..., 2] = np.maximum(a[..., 2], np.minimum(a[..., 0], a[..., 1]))
        im = Image.fromarray(a.astype("uint8"))
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, slot
    edge = bb[0] <= 2 or bb[1] <= 2 or bb[2] >= im.width - 2 or bb[3] >= im.height - 2
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = slot.split("_", 1)
    name = "%s/RVHS_H2_P2_%s_%s_2026.png" % (out, qn, s)
    o.save(name)
    print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (round(im.width * 72 / DPI), round(im.height * 72 / DPI)), "EDGE INK" if edge else "")
