"""Produce answer-figure images.

Two sources, chosen per figure for a reason:

  PNG  -> taken from the docx's word/media/ ORIGINALS. The Word-exported PDF
          downsamples embedded rasters to ~200 ppi, so the PDF copy is strictly
          worse.

  EMF and native Word shapes -> CROPPED from the Word-exported PDF, where they
          live as vector art with the real Symbol/Wingdings fonts embedded.

          This replaces handoff SS7's entire EMF chain (soffice --convert-to svg
          -> strip clip-paths -> remap Symbol -> crop to BoundingBox -> cairosvg).
          That chain existed to work around LibreOffice damage: clip paths that
          cut ascenders and whole labels, and Symbol-font substitution that
          renders glyphs as tofu. Measured on this document, LibreOffice also
          drops every OMML fraction. With a Word export in hand none of that
          machinery is needed.

LOCATING a figure: each part's label ("3(c)(iv)") is found as text, and the band
between it and the next label is that part's content. Within the band, vector
and raster objects are clustered; underline strokes are excluded, since this
mark scheme underlines mark-bearing keywords heavily and they would otherwise
merge every figure into its surrounding prose.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pymupdf

LABEL_RE = re.compile(r"^\d+(\([a-z]+\))+$", re.I)

#: A stroke this thin and this wide, sitting just under a text baseline, is an
#: underline rather than artwork.
UNDERLINE_MAX_H = 2.2
UNDERLINE_MIN_W = 12.0


def label_positions(doc) -> dict:
    """{'3(c)(iv)': (page_index, y_top)} for every part label in the PDF."""
    out = {}
    for pno in range(len(doc)):
        for w in doc[pno].get_text("words"):
            token = w[4].strip()
            if LABEL_RE.match(token) and token not in out:
                out[token] = (pno, w[1])
    return out


def _text_line_rects(page):
    rects = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            rects.append(pymupdf.Rect(line["bbox"]))
    return rects


def _is_underline(rect, text_rects) -> bool:
    if rect.height > UNDERLINE_MAX_H or rect.width < UNDERLINE_MIN_W:
        return False
    for t in text_rects:
        # sits within the text line, or just below its baseline
        if rect.x0 >= t.x0 - 4 and rect.x1 <= t.x1 + 8 and \
                (t.y0 - 2) <= rect.y0 <= (t.y1 + 4):
            return True
    return False


def figure_clusters(page, band: pymupdf.Rect, pad: float = 7.0):
    """Cluster artwork inside `band` into visually distinct figures."""
    text_rects = _text_line_rects(page)
    page_rect = page.rect
    boxes = []

    for dr in page.get_drawings():
        raw = pymupdf.Rect(dr["rect"])
        if not (raw.is_valid and raw.get_area() > 0):
            continue
        # Reject degenerate paths BEFORE clamping to the page. RI's chart page
        # carries a stroke spanning y = -6852 -> 470; clamped first it looks
        # like an innocent 470pt box, passes any size filter, and drags the
        # label and answer text into the chart's crop.
        if raw.height > page_rect.height or raw.width > page_rect.width:
            continue
        r = raw & page_rect
        if r.is_empty or r.get_area() <= 0:
            continue
        if not band.contains(pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)):
            continue
        if _is_underline(r, text_rects):
            continue
        # A rect spanning nearly the whole page is a clip path or a background
        # fill, not artwork. Left in, it swallows the surrounding prose: it is
        # what put the label and answer text of 4(a)(ii) inside the chart crop.
        if r.width > 0.88 * page_rect.width or r.height > 0.88 * page_rect.height:
            continue
        boxes.append(r)

    for im in page.get_images(full=True):
        for r in page.get_image_rects(im[0]):
            r = pymupdf.Rect(r)
            if band.contains(pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)):
                boxes.append(r)

    # Merge using PADDED boxes so nearby strokes group, but carry the TIGHT
    # union alongside and emit that. The pad is a grouping device; letting it
    # into the output rectangle is what swept the "Fig. 3.1" caption line into
    # the chart crop.
    merged: list[list[pymupdf.Rect]] = []   # [padded, tight]
    for b in boxes:
        grown = pymupdf.Rect(b.x0 - pad, b.y0 - pad, b.x1 + pad, b.y1 + pad)
        tight = pymupdf.Rect(b)
        overlapping = [m for m in merged if m[0].intersects(grown)]
        for m in overlapping:
            merged.remove(m)
            grown |= m[0]
            tight |= m[1]
        merged.append([grown, tight])

    changed = True
    while changed:
        changed = False
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                if merged[i][0].intersects(merged[j][0]):
                    merged[i][0] |= merged[j][0]
                    merged[i][1] |= merged[j][1]
                    merged.pop(j)
                    changed = True
                    break
            if changed:
                break

    # Artwork only: drop slivers left behind by stray rules. Test the PADDED
    # box, not the tight one: a lone arrow or charge label is legitimately
    # small, and filtering on tight boxes silently amputated pieces of several
    # mechanisms (3(c)(iv) lost more than half its width).
    out = [m[1] for m in merged if m[0].width > 22 and m[0].height > 14]
    out.sort(key=lambda r: (round(r.y0 / 12), r.x0))   # reading order
    return out


def render(page, rect: pymupdf.Rect, dest: Path, dpi: int = 400,
           margin: float = 3.0) -> Path:
    clip = pymupdf.Rect(rect.x0 - margin, rect.y0 - margin,
                        rect.x1 + margin, rect.y1 + margin) & page.rect
    pix = page.get_pixmap(clip=clip, dpi=dpi, alpha=False)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(dest))
    # Trim uniform white margin; keep a small even border.
    subprocess.run(["convert", str(dest), "-trim", "+repage",
                    "-bordercolor", "white", "-border", "12", str(dest)],
                   check=True)
    return dest


def copy_media_png(unz: Path, target: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = unz / "word" / target.replace("media/", "media/")
    dest.write_bytes(Path(src).read_bytes())
    return dest


def merge_to(clusters, n: int):
    """Merge the nearest clusters until exactly `n` remain.

    The docx already tells us how many distinct pictures a part has, so that
    count is ground truth and the clustering only has to decide WHERE the
    boundaries fall. Repeatedly merging the closest pair is stable and needs no
    magic gap threshold -- thresholds are what produced five fragments for a
    single reaction mechanism (arrows and charge labels sit far apart).
    """
    cl = [pymupdf.Rect(c) for c in clusters]
    if n <= 0 or not cl:
        return cl
    while len(cl) > n:
        best = None
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                a, b = cl[i], cl[j]
                dx = max(0, max(a.x0, b.x0) - min(a.x1, b.x1))
                dy = max(0, max(a.y0, b.y0) - min(a.y1, b.y1))
                d = (dx * dx + dy * dy) ** 0.5
                if best is None or d < best[0]:
                    best = (d, i, j)
        _d, i, j = best
        cl[i] |= cl[j]
        cl.pop(j)
    cl.sort(key=lambda r: (round(r.y0 / 12), r.x0))
    return cl
