"""RI 2026 H2 P1: crop the four all-diagram option sets, each from the Word PDF.
  Q11 (PDF p.5):  four graphs in a 2x2 grid. The option letter is printed INSIDE
                  each graph's box (level with the y-axis title), so it is painted
                  out (WHITE) before trimming; axis titles are kept.
  Q19 (PDF p.9):  four skeletal structures, 2x2, letters above (excluded)
  Q27 (PDF p.15): four amino-acid anions, 2x2, letters above (excluded)
  Q25 (PDF p.13): the four structures in the table's "compound" column (rows 1-4);
                  saved as the stem1-stem4 blocks, row numerals and reagents excluded
  Q29 (PDF p.16): four skeletal structures in one row, letters above (excluded)
Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px white border.
usage: python3 -m ingest.crop_ri26_p1_options <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops, ImageDraw

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
# qn: (page index, {letter: crop box in pt}, {letter: box to paint white, in pt})
SETS = {
    11: (4, {"A": (110, 136, 318, 306), "B": (321, 136, 535, 310),
             "C": (110, 320, 323, 494), "D": (323.5, 318, 540, 490)},
            {"A": (199, 137, 211, 153), "B": (417, 137, 429, 153),
             "C": (199, 322, 211, 339), "D": (417, 319, 429, 335)}),
    19: (8, {"A": (110, 220, 310, 290), "B": (320, 220, 535, 290),
             "C": (110, 306, 310, 386), "D": (320, 306, 535, 386)}, {}),
    27: (14, {"A": (110, 295, 310, 377), "B": (320, 295, 535, 377),
              "C": (110, 393, 310, 480), "D": (320, 393, 535, 480)}, {}),
    25: (12, {"stem1": (300, 396, 440, 452), "stem2": (300, 454, 440, 509),
              "stem3": (300, 510, 440, 567), "stem4": (300, 569, 440, 625)}, {}),
    29: (15, {"A": (95, 380, 200, 505), "B": (205, 380, 315, 505),
              "C": (320, 380, 428, 505), "D": (432, 380, 545, 505)}, {}),
}
for qn, (pno, rects, white) in SETS.items():
    for L, box in rects.items():
        pix = d[pno].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        if L in white:
            s = DPI / 72.0
            x0, y0, x1, y1 = white[L]
            ImageDraw.Draw(im).rectangle(
                [(x0 - box[0]) * s, (y0 - box[1]) * s, (x1 - box[0]) * s, (y1 - box[1]) * s],
                fill=(255, 255, 255))
        bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        assert bb, (qn, L)
        # ink touching the clip edge means the box cut through something
        assert bb[0] > 2 and bb[1] > 2 and bb[2] < im.width - 2 and bb[3] < im.height - 2, (
            qn, L, bb, im.size)
        im = im.crop(bb)
        o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
        o.paste(im, (12, 12))
        name = "%s/RI_H2_P1_Q%d_%s_2026.png" % (out, qn, L)  # Q25 slots are stem1-4
        o.save(name)
        print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (
            round(im.width * 72 / DPI), round(im.height * 72 / DPI)))
