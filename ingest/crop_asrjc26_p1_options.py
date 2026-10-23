import pymupdf
from PIL import Image, ImageChops
import io, sys
d = pymupdf.open('p1.pdf')
# region per option: (page, x0, y0, x1, y1) in PDF points; the option LETTER is outside x0 so it is never cropped
R = {
 (10,'A'):(11,100,160,300,266), (10,'B'):(11,100,266,300,367), (10,'C'):(11,100,367,300,487), (10,'D'):(11,100,487,300,612),
}
def content_bbox(page, reg):
    # NB: PyMuPDF treats a zero-width/height rect (an axis-aligned stroke) as EMPTY,
    # so intersects()/&/include_rect all silently ignore it (handoff S13C).  Use raw coordinates.
    xs0=[]; ys0=[]; xs1=[]; ys1=[]
    def add(x0,y0,x1,y1):
        if x1 < reg.x0 or x0 > reg.x1 or y1 < reg.y0 or y0 > reg.y1:
            return
        xs0.append(max(x0,reg.x0)); ys0.append(max(y0,reg.y0)); xs1.append(min(x1,reg.x1)); ys1.append(min(y1,reg.y1))
    for dr in page.get_drawings():
        r = dr['rect']
        if (r.x1-r.x0) > 400 or (r.y1-r.y0) > 400:
            continue
        add(r.x0, r.y0, r.x1, r.y1)
    for im in page.get_image_info():
        b=im['bbox']; add(b[0],b[1],b[2],b[3])
    for w in page.get_text('words'):
        cx=(w[0]+w[2])/2; cy=(w[1]+w[3])/2
        if reg.x0 <= cx <= reg.x1 and reg.y0 <= cy <= reg.y1:
            add(w[0],w[1],w[2],w[3])
    if not xs0: return None
    return pymupdf.Rect(min(xs0),min(ys0),max(xs1),max(ys1))
for (q, L), (pn, x0, y0, x1, y1) in R.items():
    page = d[pn-1]
    reg = pymupdf.Rect(x0, y0, x1, y1)
    bb = content_bbox(page, reg)
    clip = pymupdf.Rect(bb.x0-3, bb.y0-3, bb.x1+3, bb.y1+3) & pymupdf.Rect(0,0,595,842)
    pix = page.get_pixmap(clip=clip, dpi=400)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    bg = Image.new('RGB', im.size, (255,255,255))
    box = ImageChops.difference(im, bg).getbbox()
    im = im.crop(box)
    out = Image.new('RGB', (im.width+24, im.height+24), (255,255,255))
    out.paste(im, (12,12))
    fn = 'snips/ASRJC_H2_P1_Q%d_%s_2026.png' % (q, L)
    out.save(fn, dpi=(400,400))
    print(fn, out.size, 'printed pt %.0f x %.0f' % (out.width/400*72, out.height/400*72), [round(v,1) for v in clip])

# ---- Q7 / Q8: the four graphs are small PNGs inside the docx (150 dpi; media/image19-22 = Q7 A-D,
# image23-26 = Q8 A-D, in document order). Use them at native resolution (re-rendering the PDF
# only upsamples them). They are palette PNGs WITH transparency: composite on white first, or the
# background converts to black.
for q, first in ((7, 19), (8, 23)):
    for k, L in enumerate('ABCD'):
        im = Image.open('unz/word/media/image%d.png' % (first + k)).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
        im = im.crop(ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox())
        out = Image.new('RGB', (im.width + 24, im.height + 24), (255, 255, 255)); out.paste(im, (12, 12))
        out.save('snips/ASRJC_H2_P1_Q%d_%s_2026.png' % (q, L), dpi=(150, 150))
