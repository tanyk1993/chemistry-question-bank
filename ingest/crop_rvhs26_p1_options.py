"""RVHS 2026 H2 P1: crop the three all-diagram option sets from the Word PDF.
  Q6  (PDF p.3):  four graphs in a 2x2 grid (raster images in the paper); the option
                  letters are printed outside the pictures (excluded).
  Q25 (PDF p.12): four amino-acid structures stacked in one column, letters at left
                  (excluded).
  Q27 (PDF p.13): four polymer repeat units stacked in one column, letters at left
                  (excluded).
Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border.
usage: python3 -m ingest.crop_rvhs26_p1_options <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
# qn: (page index, {letter: crop box in pt})
SETS = {
    6: (2, {"A": (115.5, 412.7, 263.4, 565.0), "B": (340.4, 412.7, 486.4, 561.5),
            "C": (115.5, 574.0, 256.5, 724.7), "D": (340.4, 574.0, 485.5, 725.2)}),
    25: (11, {"A": (116.9, 214.4, 242.0, 293.0), "B": (116.9, 302.6, 246.7, 381.2),
              "C": (116.9, 390.8, 246.7, 469.5), "D": (116.9, 479.2, 242.0, 557.8)}),
    27: (12, {"A": (116.0, 399.0, 225.0, 469.5), "B": (116.0, 478.0, 225.0, 548.5),
              "C": (116.0, 557.5, 292.0, 641.0), "D": (116.0, 650.0, 292.0, 734.0)}),
}
for qn, (pno, rects) in SETS.items():
    for L, box in rects.items():
        pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        assert bb, (qn, L)
        # ink touching the clip edge means the box cut through something
        assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (
            qn, L, bb, im.size)
        im = im.crop(bb)
        o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
        o.paste(im, (12, 12))
        name = "%s/RVHS_H2_P1_Q%d_%s_2026.png" % (out, qn, L)
        o.save(name)
        print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (
            round(im.width * 72 / DPI), round(im.height * 72 / DPI)))
