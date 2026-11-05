"""JPJC 2026 H2 P1 answers: crop the Q24 (schemes A-D) and Q29 (arrow sequences
A-D) answer figures from the Word PDF. The school drew some options at a
different scale (Q24 A/B vs C/D; Q29 D vs A-C), so each figure is rendered at a
dpi that brings its typeface to the set's reference size (option A), then every
figure in a set is padded to one canvas width (left aligned).
usage: python3 -m ingest.crop_jpjc26_p1_answers <answers.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops
d = pymupdf.open(sys.argv[1]); out = sys.argv[2]
SETS = {
  24: (5, 108, 540, {'a': (58, 215), 'b': (237, 392), 'c': (417, 503), 'd': (520, 604)}, None),
  29: (7, 200, 450, {'a': (61, 109), 'b': (124, 166), 'c': (182, 224), 'd': (240, 286)}, None),
}


def scale_ref(page, rect):
    """median arrow length (drawings under 6 pt tall) in the band: the sequence and
    scheme text here are vector outlines (no text spans), the arrows are the one
    thing drawn at the same size as the lettering around them"""
    ws = sorted(dr['rect'].x1 - dr['rect'].x0 for dr in page.get_drawings()
                if dr['rect'].y0 >= rect.y0 - 1 and dr['rect'].y1 <= rect.y1 + 1
                and rect.x0 - 1 <= dr['rect'].x0 and dr['rect'].x1 <= rect.x1 + 1
                and 15 < dr['rect'].x1 - dr['rect'].x0 < 150 and dr['rect'].y1 - dr['rect'].y0 < 6)
    return ws[len(ws) // 2]


for qn, (pg, x0, x1, bands, lab) in SETS.items():
    page = d[pg]
    rects = {}
    for k, (y0, y1) in bands.items():
        rects[k] = pymupdf.Rect(x0, y0, x1, y1)
    ref = scale_ref(page, rects['a'])
    ims = {}
    for k, r in rects.items():
        dpi = int(round(400 * ref / scale_ref(page, r)))
        pix = page.get_pixmap(clip=r, dpi=dpi)
        im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
        box = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
        ims[k] = im.crop(box)
        print(qn, k, 'dpi %.0f' % dpi, ims[k].size)
    W = max(i.width for i in ims.values())
    for k, im in ims.items():
        o = Image.new('RGB', (W + 24, im.height + 24), (255, 255, 255))
        o.paste(im, (12, 12))
        o.save('%s/JPJC_H2_P1_Q%d_ans-%s_2026.png' % (out, qn, k))
