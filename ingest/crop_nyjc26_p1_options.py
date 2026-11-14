"""NYJC 2026 H2 P1: crop the two all-diagram option sets, each from the Word PDF.
  Q2  (PDF p.2): four skeletal structures, letters A-D to their left (excluded)
  Q11 (PDF p.8): four graphs, letters A-D above them (excluded); each crop keeps
                 the graph's own axis title, 0.50 / 0.23 / 0 and 'time'.
Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border.
usage: python3 -m ingest.crop_nyjc26_p1_options <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
SETS = {
    2: (1, {"A": (140, 540, 215, 590), "B": (140, 598, 215, 645),
            "C": (140, 655, 220, 695), "D": (140, 703, 215, 760)}),
    11: (7, {"A": (14, 362, 266, 492), "B": (278, 362, 532, 492),
             "C": (14, 513, 266, 640), "D": (278, 513, 532, 640)}),
}
for qn, (pno, rects) in SETS.items():
    for L, box in rects.items():
        pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=400)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        assert bb, (qn, L)
        im = im.crop(bb)
        o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
        o.paste(im, (12, 12))
        name = "%s/NYJC_H2_P1_Q%d_%s_2026.png" % (out, qn, L)
        o.save(name)
        print(name.split("/")[-1], o.size)
