"""HCI 2026 H2 P2: answer-side figure crops from the school's WATERMARKED mark-scheme PDF.

The mark scheme carries a full-page raster watermark (one 794x1096 image per
page) behind the vector art. Cropping the page as-is drags the watermark into
every snip, so here the full-page image is deleted from an in-memory copy of
the page before rendering (white background), stray typed mark labels that sit
inside a figure's region are redacted (text only; line art is kept), and the
render is trimmed to its ink with a 12px border -- the same finish as
`figures.render()`.

usage: python3 -m ingest.crop_hci26_p2_answers ms.pdf outdir
writes outdir/<file>.png and prints the printed size in pt (finished PNG width
minus the border, over the render dpi).
"""
import subprocess
import sys
from pathlib import Path

import pymupdf

DPI = 400
BORDER = 12

#: file -> (page 1-based, (x0, y0, x1, y1) in pt, [typed texts to redact inside the region])
REGIONS = {
    "HCI_H2_P2_Q3_ans-biii_2026.png": (3, (130, 121, 528, 331), []),
    "HCI_H2_P2_Q3_ans-biv_2026.png":  (4, (140, 60, 530, 243), [237.0]),
    "HCI_H2_P2_Q4_ans-ai_2026.png":   (5, (138, 334, 240, 432), []),
    "HCI_H2_P2_Q4_ans-b_2026.png":    (6, (112, 452, 550, 612), []),
    "HCI_H2_P2_Q4_ans-ci_2026.png":   (7, (134, 55, 372, 163), []),
    "HCI_H2_P2_Q4_ans-cii_2026.png":  (7, (125, 188, 440, 300), []),
    "HCI_H2_P2_Q5_ans-aii_2026.png":  (7, (134, 360, 226, 430), []),
    "HCI_H2_P2_Q5_ans-bii_2026.png":  (8, (130, 45, 545, 158), []),
    "HCI_H2_P2_Q5_ans-biii_2026.png": (8, (140, 190, 325, 255), ["[1]"]),
    "HCI_H2_P2_Q5_ans-c_2026.png":    (8, (105, 346, 262, 447), ["[1]"]),
}


def crop_all(pdf, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, (pno, rect, redact) in REGIONS.items():
        doc = pymupdf.open(pdf)
        page = doc[pno - 1]
        for im in page.get_images(full=True):
            xref, w, h = im[0], im[2], im[3]
            if w >= 700 and h >= 1000:          # the full-page watermark raster
                page.delete_image(xref)
        clip = pymupdf.Rect(*rect)
        hit = False
        for t in redact:
            if isinstance(t, float):   # redact every typed word whose top is below y=t
                for w in page.get_text("words", clip=clip):
                    if w[1] >= t:
                        page.add_redact_annot(pymupdf.Rect(*w[:4]))
                        hit = True
                continue
            for r in page.search_for(t, clip=clip):
                page.add_redact_annot(r)
                hit = True
        if hit:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                                  graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        pix = page.get_pixmap(clip=clip, dpi=DPI, alpha=False)
        dst = outdir / name
        pix.save(str(dst))
        subprocess.run(["convert", str(dst), "-fuzz", "2%", "-trim", "+repage",
                        "-bordercolor", "white", "-border", str(BORDER), str(dst)],
                       check=True)
        from PIL import Image
        w, h = Image.open(dst).size
        sizes[name] = ((w - 2 * BORDER) / DPI * 72, (h - 2 * BORDER) / DPI * 72)
        print("%-34s p%d  %6.1f x %5.1f pt  (%d x %d px)%s" % (
            name, pno, sizes[name][0], sizes[name][1], w, h,
            "  redacted" if hit else ""))
    return sizes


if __name__ == "__main__":
    crop_all(sys.argv[1], sys.argv[2])
