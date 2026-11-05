"""JPJC 2026 H2 P1: crop the all-diagram option sets (Q9 graphs incl. the 'time'
axis label). Q23 and Q28 option crops come from extract_questions' own crops.
usage: python3 -m ingest.crop_jpjc26_p1_options <word.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops
d = pymupdf.open(sys.argv[1]); out = sys.argv[2]
R = {'A': (105,128,290,292), 'B': (340,128,525,292), 'C': (105,292,290,448), 'D': (340,292,525,448)}
for L, (x0,y0,x1,y1) in R.items():
    pix = d[4].get_pixmap(clip=pymupdf.Rect(x0,y0,x1,y1), dpi=400)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    box = ImageChops.difference(im, Image.new('RGB', im.size, (255,255,255))).getbbox()
    im = im.crop(box)
    o = Image.new('RGB', (im.width+24, im.height+24), (255,255,255)); o.paste(im, (12,12))
    o.save('%s/JPJC_H2_P1_Q9_%s_2026.png' % (out, L))

# ---- Q28: each option is a table row [letter | product 1 | product 2]. The
# crop excludes the letter column and the table rules (the divider between the
# two cells is whited out), so the image is the two structures only.
Q28 = {'A': (218, 311), 'B': (315, 409), 'C': (413, 506), 'D': (510, 604)}
DIV = 277.0
for L, (y0, y1) in Q28.items():
    clip = pymupdf.Rect(115, y0, 440, y1)
    pix = d[11].get_pixmap(clip=clip, dpi=400)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    k = 400 / 72.0
    dx = int((DIV - clip.x0) * k)
    for x in range(max(dx - 6, 0), min(dx + 7, im.width)):
        for y in range(im.height):
            im.putpixel((x, y), (255, 255, 255))
    box = ImageChops.difference(im, Image.new('RGB', im.size, (255,255,255))).getbbox()
    im = im.crop(box)
    o = Image.new('RGB', (im.width+24, im.height+24), (255,255,255)); o.paste(im, (12,12))
    o.save('%s/JPJC_H2_P1_Q28_%s_2026.png' % (out, L))
