"""Locate and crop QUESTION-paper figures from the Word-exported PDF.

`figures.py` bands the page by MARK-SCHEME part labels ("3(c)(iv)"). A question
paper has no such labels: its landmarks are bare question numbers in the left
margin, and a question's band runs from its own number to the next one, which
may be on the following page. Everything downstream of banding -- clustering,
underline rejection, degenerate-path rejection, merge_to -- is reused unchanged
from `figures.py`, because none of it is specific to the mark scheme.

STACKED FRACTIONS ARE READ, NOT CROPPED
---------------------------------------
RI 2024 H2 P1 Q12 writes its coefficients as legacy Equation Editor objects:
"1" over a rule over "2". Cropping those would put five tiny images into a data
table for content the bank already has house markup for (`span.frac > .fnum +
.fden`, used by WA2 and RI P2). Worse, they are barely croppable -- the digits
are text, so the only thing `get_drawings()` sees is the rule itself, which the
artwork size filter then discards as a sliver.

Handoff SS4 records this as measured-feasible on the answers PDF: "a short thin
rule with small text above and below sharing its x-range". That is what
`read_fraction` implements, and a fraction it cannot read confidently is
reported rather than guessed at.
"""
from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from .figures import figure_clusters, merge_to, render

#: A bare question number in the left margin.
QNUM_RE = re.compile(r"^(\d{1,2})$")
#: Question numbers sit in the left margin; option letters and body text do not.
MARGIN_X = 130.0
#: A fraction rule: thin, short, with digits above and below.
RULE_MAX_H = 2.5
RULE_MAX_W = 40.0


def question_bands(doc, first=1, last=30) -> dict:
    """{qnum: [(page_index, y_top, y_bottom), ...]} covering each question.

    A band ends at the next question number, or at the bottom of the page when
    the question runs on. Both pieces are returned so a question split across a
    page break still gets all of its artwork.
    """
    marks = []       # (page, y, qnum)
    for pno in range(len(doc)):
        for w in doc[pno].get_text("words"):
            m = QNUM_RE.match(w[4].strip())
            if not m or w[0] > MARGIN_X:
                continue
            n = int(m.group(1))
            if first <= n <= last:
                marks.append((pno, w[1], n))
    marks.sort()
    # Keep the FIRST sighting of each number, in order, and only when it
    # continues the sequence -- page numbers and stray digits in the margin
    # would otherwise open spurious bands.
    seq, want = [], first
    for pno, y, n in marks:
        if n == want:
            seq.append((pno, y, n))
            want += 1
    bands: dict = {}
    for i, (pno, y, n) in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        spans = []
        if nxt and nxt[0] == pno:
            spans.append((pno, y - 4, nxt[1] - 4))
        else:
            spans.append((pno, y - 4, doc[pno].rect.y1))
            if nxt:
                for mid in range(pno + 1, nxt[0]):
                    spans.append((mid, 0.0, doc[mid].rect.y1))
                spans.append((nxt[0], 0.0, nxt[1] - 4))
            else:
                # THE LAST QUESTION has no following number to close its band,
                # so without this it stops at the foot of its own page. RI 2024
                # H2 P1 Q30 runs onto the next page and keeps all four of its
                # option structures there; truncating the band loses every one
                # of them and the four crops come back as fragments of the stem.
                for after in range(pno + 1, len(doc)):
                    if doc[after].get_text("text").strip():
                        spans.append((after, 0.0, doc[after].rect.y1))
        bands[n] = spans
    return bands


def _band_rect(doc, pno, y0, y1) -> pymupdf.Rect:
    r = doc[pno].rect
    return pymupdf.Rect(r.x0, max(r.y0, y0), r.x1, min(r.y1, y1))


def clusters_for(doc, spans) -> list:
    """[(page_index, Rect)] for every distinct piece of artwork in a band."""
    out = []
    for pno, y0, y1 in spans:
        page = doc[pno]
        band = _band_rect(doc, pno, y0, y1)
        # Band-level clustering keeps BOTH defaults on. A question paper has
        # no underlines, but it does have ruled tables, and a table's rules are
        # long thin strokes beside text -- exactly what the underline filter
        # rejects. Turning it off here pulled Q12's whole enthalpy table and
        # Q19's results table into their stem crops. The relaxed settings
        # belong only inside a matrix cell, where the content is known to be
        # one small skeletal structure.
        for rect in figure_clusters(page, band):
            out.append((pno, rect))
    return out


def read_fraction(doc, spans) -> list:
    """Find stacked fractions in a band and return them as (num, den) strings.

    Deliberately narrow: a short thin horizontal rule, with exactly one text
    span centred above it and one below, both within its x-range. Anything
    less clear-cut returns nothing, because a wrong coefficient is invisible in
    the rendered output and changes the chemistry.
    """
    found = []
    for pno, y0, y1 in spans:
        page = doc[pno]
        band = _band_rect(doc, pno, y0, y1)
        words = [w for w in page.get_text("words")
                 if band.contains(pymupdf.Point((w[0] + w[2]) / 2,
                                                (w[1] + w[3]) / 2))]
        for dr in page.get_drawings():
            r = pymupdf.Rect(dr["rect"])
            if not r.is_valid or r.height > RULE_MAX_H or r.width > RULE_MAX_W:
                continue
            if r.width < 4:
                continue
            if not band.contains(pymupdf.Point((r.x0 + r.x1) / 2,
                                               (r.y0 + r.y1) / 2)):
                continue
            above = [w for w in words
                     if w[3] <= r.y0 + 1 and w[3] > r.y0 - 14
                     and w[0] >= r.x0 - 3 and w[2] <= r.x1 + 3]
            below = [w for w in words
                     if w[1] >= r.y1 - 1 and w[1] < r.y1 + 14
                     and w[0] >= r.x0 - 3 and w[2] <= r.x1 + 3]
            if len(above) == 1 and len(below) == 1:
                found.append({
                    "page": pno, "y": r.y0,
                    "num": above[0][4].strip(), "den": below[0][4].strip(),
                })
    found.sort(key=lambda f: (f["page"], f["y"]))
    return found


def crop_plan(doc, qnum, spans, n_wanted, exclude=None) -> list:
    """[(page_index, Rect)] of exactly `n_wanted` figures, in reading order.

    The docx already told us how many distinct pictures the question has, so
    that count is ground truth and clustering only decides WHERE the boundaries
    fall -- the same contract `figures.merge_to` is built on.
    """
    cl = clusters_for(doc, spans)
    if exclude:
        cl = [(p, r) for p, r in cl
              if not any(p == ep and r.intersects(er) for ep, er in exclude)]
    if not cl:
        return []
    by_page: dict = {}
    for p, r in cl:
        by_page.setdefault(p, []).append(r)
    # Merge within each page, distributing the wanted count by how much artwork
    # each page carries; a question that straddles a page break is rare but its
    # figures must not all collapse onto one side.
    if len(by_page) == 1:
        p = next(iter(by_page))
        return [(p, r) for r in merge_to(by_page[p], n_wanted)]
    # A band can reach onto a later page while all of its figures sit on the
    # first one -- Q30's stem band runs to the end of the paper, and the top of
    # the next page holds the overhang of option A's structure, not stem
    # artwork. Rects cannot be merged ACROSS pages (different coordinate
    # spaces), so take the earliest page that can supply the whole count.
    pages = sorted(by_page)
    for p in pages:
        if len(by_page[p]) >= n_wanted:
            return [(p, r) for r in merge_to(by_page[p], n_wanted)]
    out = []
    left = n_wanted
    for i, p in enumerate(pages):
        want = left if i == len(pages) - 1 else min(len(by_page[p]), left)
        for r in merge_to(by_page[p], want):
            out.append((p, r))
        left -= want
    return out


def write_crops(doc, items, outdir: Path, dpi: int = 400) -> list:
    """Render each (page, rect, filename) and return the paths written."""
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for pno, rect, name in items:
        written.append(render(doc[pno], rect, outdir / name, dpi=dpi))
    return written


# ---------------------------------------------------------------------------
# cropping by PRINTED LANDMARK rather than by proximity
# ---------------------------------------------------------------------------
# merge_to merges the NEAREST clusters until the wanted count remains. Across a
# whole question that is the wrong metric whenever figures are laid out in a
# grid: two structures stacked in one column are closer to each other than one
# structure is to its own detached methyl group, so the column fuses and the
# single structure shatters. Measured on RI 2024 H2 P1 Q25, which came back as
# one tall image of a whole column plus four fragments.
#
# The paper already prints the boundaries -- option letters, row numbers,
# column headings -- so the fix is to band by those, exactly as figures.py
# bands the mark scheme by its part labels, and to cluster only inside a cell.

OPT_RE = re.compile(r"^[A-E]$")


def option_cells(doc, spans, letters="ABCD") -> dict:
    """{letter: (page, Rect)} for each printed option letter.

    Handles both layouts in this paper: a single column (Q3) and a 2x2 grid
    (Q8). Letters are grouped into rows by y, then each cell runs to the next
    letter across and to the next letter row down -- so Q8's crop includes the
    "constant V" caption under its graph, which is the only thing telling that
    option apart from the others.
    """
    found = []
    for pno, y0, y1 in spans:
        page = doc[pno]
        for w in page.get_text("words"):
            if OPT_RE.match(w[4].strip()) and y0 <= w[1] <= y1 and w[0] < 470:
                found.append((pno, w[1], w[0], w[4].strip()))
    if not found:
        return {}
    found.sort()
    # group into rows (same page, y within a few points)
    rows: list = []
    for pno, y, x, L in found:
        if rows and rows[-1][0] == pno and abs(rows[-1][1] - y) < 6:
            rows[-1][2].append((x, L))
        else:
            rows.append([pno, y, [(x, L)]])
    for r in rows:
        r[2].sort()

    out = {}
    for i, (pno, y, cells) in enumerate(rows):
        page = doc[pno]
        # bottom: the next letter row on this page, else the span's end
        below = next((r[1] for r in rows[i + 1:] if r[0] == pno), None)
        if below is None:
            below = max((y1 for p, _y0, y1 in spans if p == pno),
                        default=page.rect.y1)
        for j, (x, L) in enumerate(cells):
            right = cells[j + 1][0] - 4 if j + 1 < len(cells) else page.rect.x1
            # figure_clusters selects by cluster CENTRE, so a cell trimmed
            # tightly to the letters drops strokes whose midpoint falls just
            # outside -- Q8's graphs lost their axis labels that way. The left
            # edge reaches back past the letter, and the top above it, because
            # artwork is drawn beside and below the letter, never on it.
            left = x - 8
            out[L] = (pno, pymupdf.Rect(left, y - 6, right, below - 4))
    return out


def _ink_gaps(page, x0, x1, y0, y1, min_gap=4.0) -> list:
    """Empty horizontal strips between y0 and y1 inside the column [x0, x1]."""
    iv = [(d["rect"].y0, d["rect"].y1) for d in page.get_drawings()
          if d["rect"].x1 >= x0 and d["rect"].x0 <= x1]
    iv += [(w[1], w[3]) for w in page.get_text("words")
           if w[2] >= x0 and w[0] <= x1]
    iv = sorted((a, b) for a, b in iv if b >= y0 and a <= y1)
    merged: list = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + 0.5:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(merged[i][1], merged[i + 1][0]) for i in range(len(merged) - 1)
            if merged[i + 1][0] - merged[i][1] >= min_gap]


def _snap_rows(page, x0, x1, bounds, tol=25.0) -> list:
    """Move each interior row boundary onto the blank strip the page shows.

    A borderless grid has no rule to cut on, so the boundaries start as the
    midpoints between the printed row numbers -- and a row number sits at the
    centre of its LABEL, not of its artwork. Where one row's structure is tall
    and the next row's is short, that midpoint falls inside the taller
    structure, and its tail is cropped into the row below: RI 2024 H2 P1 Q25
    row 4 column 2 came out with the bottoms of row 3 floating above it.

    The page itself says where the rows divide -- there is a clear band of
    nothing between them. Each boundary is snapped to the nearest such band,
    per column, because the columns break at different heights. Out of
    tolerance, the midpoint stands: a guess that moves a boundary 40pt is worse
    than one that leaves it where the labels put it.
    """
    gaps = _ink_gaps(page, x0, x1, bounds[0], bounds[-1])
    if not gaps:
        return list(bounds)
    out = [bounds[0]]
    for b in bounds[1:-1]:
        mid = min(((a + z) / 2 for a, z in gaps), key=lambda m: abs(m - b))
        out.append(mid if abs(mid - b) <= tol else b)
    out.append(bounds[-1])
    return out


def matrix_cells(doc, spans, nrows: int, ncols: int, row_labels=None,
                 y_limit: float | None = None) -> list:
    """[(page, Rect)] for a rows x cols structure grid, in reading order.

    Q25 lays four candidate answers against three named columns. The column
    x-ranges come from the "structure of ..." headings and the row y-ranges
    from the printed row numbers, so the cells are the paper's own, not a
    guess. Returns [] if the landmarks are not all found -- a half-located
    grid would crop confidently and wrongly.
    """
    row_labels = row_labels or [str(i + 1) for i in range(nrows)]
    for pno, y0, y1 in spans:
        page = doc[pno]
        # The options themselves sit below the grid and are full of the same
        # digits -- Q25's option A reads "1 and 2 only". Without this bound the
        # row-number search finds two candidates for "1" and gives up.
        top = y1 if y_limit is None else min(y1, y_limit)
        words = [w for w in page.get_text("words") if y0 <= w[1] <= top]
        heads = [w for w in words if w[4].strip().lower() == "structure"]
        if len(heads) != ncols:
            continue
        heads.sort(key=lambda w: w[0])
        head_y = max(w[3] for w in heads)
        # row numbers sit left of the first column
        left_edge = heads[0][0] - 10
        rows = []
        for lab in row_labels:
            hit = [w for w in words
                   if w[4].strip() == lab and w[0] < left_edge and w[1] > head_y]
            if len(hit) != 1:
                rows = []
                break
            rows.append(hit[0][1])
        if not rows:
            continue
        rows.sort()
        bounds_x = [heads[0][0] - 12]
        for k in range(1, ncols):
            bounds_x.append((heads[k - 1][2] + heads[k][0]) / 2)
        bounds_x.append(page.rect.x1 - 20)
        bounds_y = [head_y + 2]
        for k in range(1, nrows):
            bounds_y.append((rows[k - 1] + rows[k]) / 2)
        bounds_y.append(min(top, max(rows) + (rows[-1] - rows[-2] if nrows > 1
                                              else 40)))
        pad = 2.0     # cells selected by CENTRE; see option_cells
        col_y = [_snap_rows(page, bounds_x[c], bounds_x[c + 1], bounds_y)
                 for c in range(ncols)]
        cells = []
        for r in range(nrows):
            for c in range(ncols):
                cells.append((pno, pymupdf.Rect(bounds_x[c] - pad,
                                                col_y[c][r] - pad,
                                                bounds_x[c + 1] + pad,
                                                col_y[c][r + 1] + pad)))
        return cells
    return []


def crop_in(doc, pno, rect, n_wanted: int) -> list:
    """Cluster inside one cell and merge down to `n_wanted` pictures."""
    page = doc[pno]
    cl = figure_clusters(page, rect, reject_underlines=False,
                         min_w=10.0, min_h=6.0)
    if not cl:
        return []
    return [(pno, r) for r in merge_to(cl, n_wanted)]


def options_table_top(doc, pno, letter_y: float, lookback: float = 90.0,
                      min_width: float = 90.0) -> float | None:
    """y of the options table's TOP RULE, if it has one above the first letter.

    A row-table question (RI 2024 H2 P1 Q19, Q27) prints its column headings
    ABOVE the first option letter, inside the options table. Ending the stem
    band at the letter therefore leaves the heading row inside the stem, and its
    crop comes back carrying the table's header shell -- borders and headings,
    no data. Ending it at the table's top rule instead cuts where the reader
    would say the figure ends.

    Returns None when no such rule is found, so a prose-option question keeps
    the old behaviour rather than being cropped somewhere arbitrary.
    """
    page = doc[pno]
    best = None
    for dr in page.get_drawings():
        r = pymupdf.Rect(dr["rect"])
        if not r.is_valid:
            continue
        if r.height > 2.5 or r.width < min_width:
            continue
        if not (letter_y - lookback <= r.y0 < letter_y - 2):
            continue
        if best is None or r.y0 < best:
            best = r.y0
    return best
