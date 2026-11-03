"""HCI 2026 H2 P3: answer-side figure crops from the school's WATERMARKED mark-scheme PDF.

The mark scheme carries a full-page raster watermark (one 794x1096 image per
page) behind the vector art. Cropping the page as-is drags the watermark into
every snip, so here the full-page image is deleted from an in-memory copy of
the page before rendering (white background), stray typed mark labels that sit
inside a figure's region are redacted (text only; line art is kept), and the
render is trimmed to its ink with a 12px border -- the same finish as
`figures.render()`.

usage: python3 -m ingest.crop_hci26_p3_answers ms.pdf outdir
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
    "HCI_H2_P3_Q1_ans-a_2026.png":    (1, (138, 150, 482, 302), []),
    "HCI_H2_P3_Q1_ans-dii_2026.png":  (3, (136, 290, 456, 518), []),
    "HCI_H2_P3_Q2_ans-ei_2026.png":   (4, (140, 598, 300, 646), []),      # carries its typed [1]
    "HCI_H2_P3_Q2_ans-eiii_2026.png": (4, (140, 684, 240, 757), []),      # carries its typed [1]
    "HCI_H2_P3_Q3_ans-aii_2026.png":  (5, (144, 198, 400, 316), ["[1] each"]),  # typed "[1] each" stays as text
    "HCI_H2_P3_Q3_ans-bii_2026.png":  (5, (138, 608, 490, 722), []),
    "HCI_H2_P3_Q3_ans-biii_2026.png": (6, (138, 58, 270, 202), []),
    "HCI_H2_P3_Q3_ans-civ_2026.png":  (7, (138, 52, 290, 146), []),
    "HCI_H2_P3_Q3_ans-cv_2026.png":   (7, (138, 150, 545, 216), []),
    "HCI_H2_P3_Q3_ans-cv2_2026.png":  (7, (138, 288, 222, 342), []),
    "HCI_H2_P3_Q4_ans-biv_2026.png":  (8, (138, 664, 404, 780), []),
    "HCI_H2_P3_Q4_ans-ciii_2026.png": (9, (144, 572, 456, 664), []),
    "HCI_H2_P3_Q5_ans-ai_2026.png":   (10, (138, 259, 490, 366), []),
    "HCI_H2_P3_Q5_ans-bii_2026.png":  (11, (136, 58, 504, 285), []),
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
