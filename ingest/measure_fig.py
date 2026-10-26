"""Printed size of a figure, measured on the school's Word-exported PDF.

The image-size SQL (HANDOFF 33.4) sets `question_assets.display_width_pt` to the
width the figure is PRINTED at, so the site shows it at the paper's own scale.
That width is read here: the union bounding box of everything drawn inside a
hand-chosen page REGION -- vector drawings, text lines and embedded images,
each clipped to the region. Choose the region to hug the figure and to leave
out the neighbouring typed text (the lead-in line, the red mark notes).

  python3 -m ingest.measure_fig paper.pdf 2:140,320,545,545 7:100,165,480,470

(page numbers are 1-based, the region is x0,y0,x1,y1 in PDF points; the
output is `page  region -> W x H pt`). Import `measure()` to use in code.
"""
from __future__ import annotations

import sys


def measure(pdf_path, page_no, region):
    """-> (width_pt, height_pt) of the union bbox inside `region`, or None."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    pg = doc[page_no - 1]
    clip = pymupdf.Rect(*region)
    boxes = []
    for d in pg.get_drawings():
        boxes.append(pymupdf.Rect(d["rect"]))
    for im in pg.get_image_info():
        boxes.append(pymupdf.Rect(im["bbox"]))
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            if "".join(s["text"] for s in ln["spans"]).strip():
                boxes.append(pymupdf.Rect(ln["bbox"]))
    got = None
    for r in boxes:
        r = r & clip
        if r.is_empty or r.width <= 0 and r.height <= 0:
            continue
        got = r if got is None else got | r
    return None if got is None else (got.width, got.height)


def main(argv):
    pdf, specs = argv[0], argv[1:]
    for s in specs:
        pg, reg = s.split(":")
        region = [float(x) for x in reg.split(",")]
        m = measure(pdf, int(pg), region)
        print("p%s %-22s -> %s" % (pg, reg, "nothing found" if m is None
                                  else "%.0f x %.0f pt" % m))


if __name__ == "__main__":
    main(sys.argv[1:])
