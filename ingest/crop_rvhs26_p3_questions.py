"""RVHS 2026 H2 P3: crop the 10 question-side figures from the Word PDF (the user asked Claude to do the snips on
this paper, as on RVHS 2026 P2). Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border;
ink touching the clip edge means the box cut through something and the run reports it.
Figure captions ("Fig. 2.1", "Table 5.1") are typed in the builder, so the boxes stop above them.
usage: python3 -m ingest.crop_rvhs26_p3_questions <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
# slot file name: (page number 1-based, crop box in pt)
BOXES = {
    "Q2_a":    (6,  (120, 285, 540, 528)),   # Fig. 2.1 DMFC diagram (caption typed)
    "Q2_d":    (9,  (230, 112, 440, 160)),   # Fig. 2.2 PTFE repeat unit
    "Q2_diii": (10, (280, 152, 420, 245)),   # Fig. 2.3 R group (sulfonic acid)
    "Q3_c":    (12, (120, 128, 540, 196)),   # Fig. 3.1 ozonolysis scheme
    "Q3_d":    (14, (170, 138, 520, 255)),   # compounds U and V with their labels
    "Q4_bi":   (16, (200, 112, 480, 168)),   # N2O resonance structures I and II
    "Q4_f":    (18, (105, 97, 550, 233)),    # noradrenaline / adrenaline table
    "Q5_d":    (22, (80, 134, 545, 346)),    # Table 5.1 (Hofmann reactions), caption typed
    "Q5_eii":  (22, (130, 472, 545, 628)),   # three-step synthesis scheme
    "Q5_eiii": (23, (270, 422, 420, 480)),   # diene
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
    name = "%s/RVHS_H2_P3_%s_%s_2026.png" % (out, qn, s)
    o.save(name)
    print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (round(im.width * 72 / DPI), round(im.height * 72 / DPI)),
          "EDGE INK" if edge else "")
