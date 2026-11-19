"""RVHS 2026 H2 P1 answer snips: the eight structures in the Word-exported solutions PDF.
  Q22 options A-D (the bromoalkanes)         PDF p.7  -> RVHS_H2_P1_Q22_ans-1..4_2026.png
  Q23 products of options A-D (the alcohols) PDF p.7-8 -> RVHS_H2_P1_Q23_ans-1..4_2026.png
Each structure is a vector drawing sitting INSIDE a sentence ("Option B: <structure>, a secondary
alkyl halide ..."). The crop box is the drawing's own bounding box + 2 pt, pulled in on the left/right so it
never reaches the neighbouring text on the same line; the script asserts that no text word falls inside any
box. 400 dpi, trimmed to the ink, 12 px white border.
usage: python3 -m ingest.crop_rvhs26_p1_answers <solutions.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
d = pymupdf.open(sys.argv[1])
out = sys.argv[2]
# (qn, k, page index, box in pt)
BOXES = [
    (22, 1, 6, (144.0, 77.6, 336.0, 99.6)),
    (22, 2, 6, (141.0, 128.6, 255.5, 184.1)),
    (22, 3, 6, (141.0, 211.4, 254.0, 263.3)),
    (22, 4, 6, (140.5, 290.3, 227.5, 383.8)),
    (23, 1, 6, (295.0, 512.5, 375.0, 560.8)),
    (23, 2, 6, (289.5, 589.7, 368.8, 671.7)),
    (23, 3, 6, (291.0, 699.0, 407.0, 750.8)),
    (23, 4, 7, (308.5, 64.3, 415.5, 117.1)),
]
for qn, k, pno, box in BOXES:
    pg = d[pno]
    r = pymupdf.Rect(*box)
    stray = [w[4] for w in pg.get_text("words") if pymupdf.Rect(w[:4]).intersects(r)]
    assert not stray, (qn, k, stray)
    pix = pg.get_pixmap(clip=r, dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, (qn, k)
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "%s/RVHS_H2_P1_Q%d_ans-%d_2026.png" % (out, qn, k)
    o.save(name)
    print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (
        round(im.width * 72 / DPI), round(im.height * 72 / DPI)))
