"""RVHS 2026 H2 P2: crop the 11 question-side figures from the Word PDF (the user's standing
rule was 'user snips'; on 2026-11-20 the user asked Claude to do the snips on this paper).
Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border; ink touching the
clip edge means the box cut through something and the run stops.
usage: python3 -m ingest.crop_rvhs26_p2_questions <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
# slot file name: (page number 1-based, crop box in pt)
BOXES = {
    "Q1_intro": (2, (120, 112, 500, 266)),    # compound P
    "Q1_b":     (3, (118, 138, 540, 284)),    # Q and R with labels
    "Q1_c":     (4, (150, 100, 500, 262)),    # compound S
    "Q1_d":     (5, (130, 114, 530, 264)),    # methoxybenzene -> P
    "Q1_e":     (6, (230, 122, 430, 262)),    # compound T
    "Q2_intro": (8, (200, 88, 420, 250)),     # dextromethorphan + name (no Fig. caption)
    "Q2_c":     (10, (58, 98, 541, 550)),     # Fig. 2.2 pathway (no caption)
    "Q2_c2":    (10, (86, 636, 541, 706)),    # Fig. 2.3 Grignard scheme (no caption)
    "Q2_d":     (12, (130, 88, 530, 184)),    # cyanoacetic acid scheme
    "Q2_di":    (12, (260, 225, 460, 292)),   # anion X
    "Q5_intro": (22, (84, 290, 545, 560.5)),    # Fig. 5.1 graph (no caption)
}
for slot, (pno, box) in BOXES.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, slot
    edge = bb[0] <= 2 or bb[1] <= 2 or bb[2] >= im.width - 2 or bb[3] >= im.height - 2
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = slot.split("_", 1)
    name = "%s/RVHS_H2_P2_%s_%s_2026.png" % (out, qn, s)
    o.save(name)
    print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (round(im.width * 72 / DPI), round(im.height * 72 / DPI)),
          "EDGE INK" if edge else "")
