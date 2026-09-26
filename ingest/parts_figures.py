"""Locate and crop STRUCTURED-PAPER (P2/P3) figures from the Word-exported PDF.

`question_figures.py` bands an MCQ paper by bare question numbers in the left
margin. A structured paper prints a finer, better landmark: the part labels
themselves -- "(c)", "(iii)" -- each at its own x offset, exactly mirroring the
4-column grid `parts.py` reads out of the docx. Matching the two gives a
figure's owner for free, with no proximity guessing: on RI 2024 H2 P3 all 72
of the parser's labels are located in the PDF, with none missing and none
spurious.

Everything below banding -- `figure_clusters`, `merge_to`, `render` -- is
reused unchanged from `figures.py`.

THE DOCX FIGURE COUNT IS NOT THE PRINTED PICTURE COUNT HERE
-----------------------------------------------------------
`question_figures.crop_plan` is built on the opposite assumption: "the docx
already told us how many distinct pictures the question has, so that count is
ground truth and clustering only decides WHERE the boundaries fall." On an MCQ
paper that holds. On this paper it does not, and trusting it would have
produced five images for a part that prints one chart. Verified by rendering
the pages and looking at them:

  1(c)   docx 5   prints 1   a chart, plus 2 shapes drawn over it, plus 2
                             radical-dot shapes sitting inline in the reaction
                             equations above it (typography, not figures)
  2(c)   docx 2   prints 1   a PNG base with the three curves drawn over it
  5(d)   docx 2   prints 1   an energy-level diagram whose arrow and levels
                             are separate shapes
  4(e)   docx 1   prints 1   one EMF -- but clustering SPLITS it into 3

So neither count is reliable alone: the docx over-counts composed artwork and
inline typography, and clustering over-splits a single drawn structure. The
README's "a chart plus shapes drawn over it is one picture" is the same
observation, generalised: what Word stores as several drawings, the page
prints as one picture.

WHAT THIS MODULE ASSUMES, AND HOW IT FAILS
------------------------------------------
One printed picture per part-band. That is true for all 11 figure-bearing
owners on RI 2024 H2 P3, checked by eye, and it is what makes the crop
well-defined: take the union of every artwork cluster in the band.

It is an ASSUMPTION, not a law, so `split_risk` looks for the layout that
would break it -- two groups of artwork with a full line of body text between
them, which is how a paper prints two genuinely separate diagrams under one
part. That is reported as an anomaly rather than silently fused, because a
part with two diagrams cropped as one is precisely the kind of defect that
survives a marks total and a text gate.
"""
from __future__ import annotations

import re

import pymupdf

from .figures import figure_clusters, render

#: Part labels, each at its own x offset in the printed left margin. The
#: ranges are deliberately narrow and non-overlapping: they are what tells a
#: roman-numeral sub-part from a single-letter part, which is ambiguous as
#: text -- "(i)" is both. Same reasoning as `parts._classify`, applied to the
#: page instead of the grid.
QNUM_RE = re.compile(r"^(\d{1,2})$")
LETTER_RE = re.compile(r"^\(([a-z])\)$")
ROMAN_RE = re.compile(r"^\(([ivx]{1,4})\)$")
QNUM_X = 55.0
LETTER_X = (55.0, 80.0)
ROMAN_X = (80.0, 115.0)

#: These three x-offsets are a fact about a SCHOOL'S DOCX TEMPLATE (its own
#: tab-stop/indent settings), not a universal constant -- confirmed by direct
#: measurement (`doc[p].get_text("words")`) on EJC 2024 H2 P3, whose left
#: margin sits ~17-27pt further right than RI's at every one of the three
#: levels (qnum 72 vs 55, letter 86 vs 55-80, roman 107 vs 80-115), but is
#: internally CONSISTENT across the whole document (checked on all 5
#: questions, all 3 levels, before trusting it) -- exactly the same
#: per-school-template-not-per-paper relationship `corrections.py`'s tables
#: already assume for other departures. Keyed on school alone, not
#: (school, level, paper, year), on the same reasoning: a school's Word
#: template does not change paper to paper. Add a new entry here, by the same
#: direct-measurement method, before trusting this module on a fourth school.
LAYOUT_OVERRIDES = {
    "EJC": {"QNUM_X": 80.0, "LETTER_X": (80.0, 100.0), "ROMAN_X": (100.0, 130.0)},
}


def _layout(scope):
    """(QNUM_X, LETTER_X, ROMAN_X) for this paper's school, RI's own values
    (the module's original, still-default constants) if no override is on
    file."""
    school = scope[0] if scope else None
    ov = LAYOUT_OVERRIDES.get(school, {})
    return (ov.get("QNUM_X", QNUM_X), ov.get("LETTER_X", LETTER_X),
            ov.get("ROMAN_X", ROMAN_X))
#: The running header and page number sit above this; they are not content.
HEADER_Y = 50.0
#: Body text starts at the left text margin. Artwork and figure-internal
#: labels (axis ticks, series names) are indented or centred well right of it,
#: which is what lets `split_risk` tell a paragraph from a chart's own text.
BODY_X_MAX = 145.0
#: A line of PROSE: it begins at one of the left text margins (a question's
#: own, or a sub-part's indent) AND runs most of the column's width.
#: Measured against this paper, both halves are needed. Width alone would
#: catch nothing useful; x-position alone would catch a chart's own y-axis
#: labels, which also sit left ("mole fraction" at x0=137, "0.8" at x0=134).
#: Real prose here starts at x0 = 65-119 and runs 240-470pt; the widest
#: figure-internal label is 63pt.
PROSE_X_MAX = 125.0
PROSE_MIN_W = 200.0


def landmarks(doc, scope=None) -> list:
    """[(label, page, y)] for every printed part label, in document order.

    A letter and a roman numeral printed on the SAME line are one landmark
    ("3(f)(i)"), matching `parts.py`, which creates no bare-letter Part when a
    row carries both.

    `scope` (school, level, paper, year) selects the school's own margin
    geometry via `_layout()` -- see `LAYOUT_OVERRIDES` above.
    """
    qnum_x, letter_x, roman_x = _layout(scope)
    marks = []
    for pno in range(len(doc)):
        for w in doc[pno].get_text("words"):
            t = w[4].strip()
            x, y = w[0], w[1]
            if y < HEADER_Y:
                continue
            if QNUM_RE.match(t) and x < qnum_x:
                marks.append((pno, round(y, 1), "q", t))
            elif LETTER_RE.match(t) and letter_x[0] <= x < letter_x[1]:
                marks.append((pno, round(y, 1), "l", t))
            elif ROMAN_RE.match(t) and roman_x[0] <= x < roman_x[1]:
                marks.append((pno, round(y, 1), "r", t))
    # Sort by kind EXPLICITLY (q, then l, then r), not alphabetically by the
    # kind letter -- plain tuple sort puts "l" ('l' < 'q') before "q" on a
    # line that prints a question number and its first part-letter together
    # ("2 (a) The industrial synthesis..." -- EJC's own convention, one
    # printed line, unlike RI's which never puts a qnum and a letter on the
    # same line). That misattributed the letter to the PREVIOUS question
    # (rendered as "1(a)" on the page that actually opens Q2), before `seq`
    # ever saw the qnum bump. Found on EJC 2024 H2 P3 Q2's opening line.
    _KIND_ORDER = {"q": 0, "l": 1, "r": 2}
    marks.sort(key=lambda m: (m[0], m[1], _KIND_ORDER[m[2]], m[3]))

    joined, i = [], 0
    while i < len(marks):
        p, y, k, t = marks[i]
        nxt = marks[i + 1] if i + 1 < len(marks) else None
        if (k == "l" and nxt and nxt[0] == p and abs(nxt[1] - y) < 3
                and nxt[2] == "r"):
            joined.append((p, y, "l+r", t + nxt[3]))
            i += 2
        else:
            joined.append((p, y, k, t))
            i += 1

    seq, qn, letter = [], None, None
    for p, y, k, t in joined:
        if k == "q":
            qn, letter = int(t), None
            seq.append(("Q%d" % qn, p, y))
        elif k == "l":
            letter = t
            seq.append(("%d%s" % (qn, t), p, y))
        elif k == "l+r":
            letter = t[:3]
            seq.append(("%d%s" % (qn, t), p, y))
        elif k == "r" and letter is not None:
            seq.append(("%d%s%s" % (qn, letter, t), p, y))
    return seq


def bands(doc, seq) -> dict:
    """{label: [(page, y0, y1)]} -- each label's band runs to the next one.

    Returned as spans rather than one rect so a part that straddles a page
    break keeps all of its artwork, exactly as `question_figures.question_bands`
    does for a question.
    """
    out = {}
    for i, (lab, p, y) in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        spans = []
        if nxt and nxt[1] == p:
            spans.append((p, y - 4, nxt[2] - 4))
        else:
            spans.append((p, y - 4, doc[p].rect.y1))
            if nxt:
                for mid in range(p + 1, nxt[1]):
                    spans.append((mid, 0.0, doc[mid].rect.y1))
                spans.append((nxt[1], 0.0, nxt[2] - 4))
        out[lab] = spans
    return out


def _band_rect(doc, pno, y0, y1) -> pymupdf.Rect:
    r = doc[pno].rect
    return pymupdf.Rect(r.x0, max(r.y0, y0), r.x1, min(r.y1, y1))


def _text_lines(page) -> list:
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            out.append(pymupdf.Rect(line["bbox"]))
    return out


def _is_text_line_box(rect, text_lines) -> bool:
    """True if this 'cluster' is really a box sitting on a line of text.

    `figures._is_underline` rejects a THIN rule lying under text, which is the
    mark scheme's problem. This paper has the other shape: page 24 draws two
    boxes 12.6pt tall -- a full text-line height, so they pass every thinness
    test -- directly over the two prose lines introducing Fig. 4.2. Clustered
    as artwork they dragged the crop's top edge up over the prose, and
    4(c)(iii) came out with two sentences printed above the diagram.

    A rect no taller than a text line, sitting on that line and covering most
    of its width, is decoration. Real artwork in this family is taller than a
    line (the shortest here is 4(e)'s reaction equation at 39pt) or clearly
    offset from one.
    """
    for t in text_lines:
        if t.height <= 0 or rect.height > t.height * 1.4:
            continue
        overlap_y = min(rect.y1, t.y1) - max(rect.y0, t.y0)
        if overlap_y <= 0 or overlap_y / max(rect.height, 0.1) < 0.6:
            continue
        overlap_x = min(rect.x1, t.x1) - max(rect.x0, t.x0)
        if overlap_x > 0 and overlap_x / max(min(rect.width, t.width), 0.1) > 0.5:
            return True
    return False


def clusters_in(doc, spans) -> list:
    """[(page, Rect)] for every distinct piece of artwork in a band."""
    out = []
    for pno, y0, y1 in spans:
        page = doc[pno]
        lines = _text_lines(page)
        for rect in figure_clusters(page, _band_rect(doc, pno, y0, y1)):
            if _is_text_line_box(rect, lines):
                continue
            out.append((pno, rect))
    return out


def split_risk(doc, pno, rects) -> bool:
    """True if a full line of BODY text separates two groups of this artwork.

    The one layout that breaks "one picture per part-band": a part that prints
    two separate diagrams with a sentence between them.

    Uses the full PROSE test (left margin AND most of the column's width), not
    x-position alone. Position alone reports 5(d), whose energy-level diagram
    carries the axis label "energy" out at the left -- a false alarm on a part
    that plainly prints one figure. A real separating sentence still trips it,
    because a sentence is wide.
    """
    if len(rects) < 2:
        return False
    lines = [t for t in _text_lines(doc[pno])
             if t.x0 <= PROSE_X_MAX and t.width >= PROSE_MIN_W]
    ys = sorted((r.y0, r.y1) for r in rects)
    for (_, prev_bottom), (next_top, _) in zip(ys, ys[1:]):
        if next_top - prev_bottom < 8:
            continue
        if any(prev_bottom < t.y0 and t.y1 < next_top for t in lines):
            return True
    return False


def crop_owner(doc, spans) -> tuple:
    """((page, Rect) | None, anomaly | None) -- the ONE picture in this band.

    The union of the band's artwork, which is what the page prints as a single
    figure. Clusters cannot be unioned across pages (different coordinate
    spaces), so if a band's artwork straddles a page break the larger side
    wins and the split is reported.
    """
    cl = clusters_in(doc, spans)
    if not cl:
        return None, "no artwork found in band"
    by_page: dict = {}
    for p, r in cl:
        by_page.setdefault(p, []).append(r)

    note = None
    if len(by_page) > 1:
        best = max(by_page, key=lambda p: sum(r.get_area() for r in by_page[p]))
        note = ("artwork on %d pages (%s); cropped the largest, page %d"
                % (len(by_page), sorted(by_page), best))
        by_page = {best: by_page[best]}

    pno = next(iter(by_page))
    rects = by_page[pno]
    if note is None and split_risk(doc, pno, rects):
        note = ("body text separates two groups of artwork -- this part may "
                "print TWO figures, which this module would fuse into one")
    union = pymupdf.Rect(rects[0])
    for r in rects[1:]:
        union |= r
    union = _grow_to_labels(doc[pno], union)
    union, left_in = _clip_prose(doc[pno], union)
    if left_in and note is None:
        note = ("crop still contains a line of body prose -- clipping it "
                "would have removed most of the figure")
    return (pno, union), note


#: How far outside the artwork a figure's own label may sit and still belong
#: to it. The axis title "T / K" is printed clear of the arrow head it
#: annotates; 24pt covers that without reaching the next column of anything.
LABEL_REACH = 24.0


def _grow_to_labels(page, union) -> pymupdf.Rect:
    """Widen the crop to cover the figure's OWN labels.

    The union is built from artwork, and a chart's tick labels and axis title
    are text, so they fall outside it: Fig. 1.1's crop sliced through the
    final "0" of "1200" and lost "T / K" altogether.

    HORIZONTAL ONLY, deliberately. Growing vertically would creep toward the
    prose above and the caption below -- the caption is the thing most likely
    to be swept in, since it sits directly beneath and is centred under the
    figure. Restricting this to x fixes the clipped labels without opening
    that door, and `_clip_prose` still runs afterwards as a backstop.

    Only NON-prose lines qualify, by the same test used elsewhere, so a
    sentence beside a narrow figure cannot drag the crop across the page.
    """
    out = pymupdf.Rect(union)
    for t in _text_lines(page):
        if t.x0 <= PROSE_X_MAX and t.width >= PROSE_MIN_W:
            continue
        if t.y1 <= union.y0 or t.y0 >= union.y1:
            continue                      # not beside the artwork at all
        if t.x1 < union.x0 - LABEL_REACH or t.x0 > union.x1 + LABEL_REACH:
            continue                      # too far out to be its label
        out = pymupdf.Rect(min(out.x0, t.x0), out.y0,
                           max(out.x1, t.x1), out.y1)
    return out


def _clip_prose(page, union) -> tuple:
    """Pull the crop's edges in off any line of body prose. (rect, leftover).

    A figure crop must not contain the sentences around the figure. Filtering
    the offending boxes out before clustering is not possible from here --
    page 24 draws a 12.6pt box over each of its two prose lines, and
    `figure_clusters` has already fused them into the single cluster by the
    time this module sees it, so 4(c)(iii) came out with two sentences printed
    above the ZBFB diagram.

    Clipping the finished rect instead is simpler and says exactly what is
    meant. Each edge only moves while doing so leaves at least half the
    figure, so a misread never eats the picture -- it reports instead.
    """
    prose = [t for t in _text_lines(page)
             if t.x0 <= PROSE_X_MAX and t.width >= PROSE_MIN_W]
    out = pymupdf.Rect(union)
    floor = union.height * 0.5
    for _ in range(8):
        inside = [t for t in prose if t.y1 > out.y0 + 1 and t.y0 < out.y1 - 1]
        if not inside:
            return out, False
        top = min(inside, key=lambda t: t.y0)
        bottom = max(inside, key=lambda t: t.y1)
        if top.y0 - out.y0 <= out.y1 - bottom.y1:
            if out.y1 - (top.y1 + 2) < floor:
                break
            out = pymupdf.Rect(out.x0, top.y1 + 2, out.x1, out.y1)
        else:
            if (bottom.y0 - 2) - out.y0 < floor:
                break
            out = pymupdf.Rect(out.x0, out.y0, out.x1, bottom.y0 - 2)
    return out, True


#: How close two artwork rects' y-ranges must sit to count as pieces of the
#: SAME printed picture (a chart's base image plus the shapes drawn over it,
#: a structure's ring plus its separately-clustered substituent). Verified
#: against EJC 2024 H2 P3's 5(b) (three rects 0pt apart forming one picture,
#: an unrelated fourth 122pt below it) and 2(b) (two rects 56pt apart, two
#: separate pictures) -- real gaps between distinct figures in this family
#: run 55pt+; real gaps within one figure's own clustered pieces run close to
#: 0. 30pt sits well inside that margin either way.
FIGURE_GROUP_GAP = 30.0


def _group_by_gap(rects, gap=FIGURE_GROUP_GAP) -> list:
    """Partition same-page rects into top-to-bottom groups, merging any two
    whose y-ranges sit within `gap` of each other (or overlap)."""
    order = sorted(rects, key=lambda r: r.y0)
    groups = [[order[0]]]
    bottom = order[0].y1
    for r in order[1:]:
        if r.y0 - bottom <= gap:
            groups[-1].append(r)
            bottom = max(bottom, r.y1)
        else:
            groups.append([r])
            bottom = r.y1
    return groups


def _union_group(page, rects) -> tuple:
    """(Rect, leftover_prose_flag) -- one grown, prose-clipped crop for a
    group of same-page rects. Shared by `crop_owner()`'s single-picture path
    and `crop_owner_multi()`'s several-pictures path so both grow/clip the
    same way."""
    union = pymupdf.Rect(rects[0])
    for r in rects[1:]:
        union |= r
    union = _grow_to_labels(page, union)
    return _clip_prose(page, union)


def crop_owner_multi(doc, spans, expected_count: int) -> tuple:
    """([(page, Rect)], [anomaly]) -- `expected_count` DISTINCT pictures in
    this band, in document (top-to-bottom / page) order.

    `expected_count == 1` is the ordinary case and defers to `crop_owner()`
    unchanged -- nothing about a single-figure owner's behaviour changes.
    For `expected_count > 1` (style-guide.md SS5: "one owner can print more
    than one genuinely distinct picture"), the split is found two ways, tried
    in order:

      1. ONE FIGURE PER PAGE, if the band's artwork spans exactly as many
         pages as figures expected -- EJC 2024 H2 P3's 1(c)(ii) shape (a
         by-product structure on one page, Fig. 1.2 on the next). This
         replaces `crop_owner()`'s own "cropped the largest page, dropped the
         rest" fallback, which is exactly wrong here: neither page is a
         mistake to discard.
      2. A Y-GAP SPLIT on a single page, when the artwork clusters into
         exactly `expected_count` groups by `_group_by_gap()` -- EJC 2024 H2
         P3's 2(b) and 5(b) shape (two distinct drawings separated by more
         than a text line's height, on the same page). This is the same
         signal `split_risk()` already uses to FLAG the risk; here it is
         used to act on it, not just report it.

    Either heuristic failing to produce exactly `expected_count` groups falls
    back to the old single-union behaviour (logged loudly) rather than
    guessing -- under-cropping is a visible, reviewable defect; a wrong guess
    at which pixels belong to which figure is not.
    """
    cl = clusters_in(doc, spans)
    if not cl:
        return [], ["no artwork found in band"]
    by_page: dict = {}
    for p, r in cl:
        by_page.setdefault(p, []).append(r)

    if expected_count <= 1:
        got, note = crop_owner(doc, spans)
        return ([got] if got else []), ([note] if note else [])

    anomalies = []
    if len(by_page) == expected_count:
        results = []
        for pno in sorted(by_page):
            union, left_in = _union_group(doc[pno], by_page[pno])
            if left_in:
                anomalies.append("page %d: crop still contains a line of "
                                 "body prose" % pno)
            results.append((pno, union))
        return results, anomalies

    if len(by_page) == 1:
        pno = next(iter(by_page))
        groups = _group_by_gap(by_page[pno])
        if len(groups) == expected_count:
            results = []
            for grp in groups:
                union, left_in = _union_group(doc[pno], grp)
                if left_in:
                    anomalies.append("page %d: crop still contains a line "
                                     "of body prose" % pno)
                results.append((pno, union))
            return results, anomalies
        anomalies.append(
            "expected %d distinct figures but grouped into %d on page %d "
            "by Y-gap -- falling back to one union crop"
            % (expected_count, len(groups), pno))
    else:
        anomalies.append(
            "expected %d distinct figures across %d pages -- ambiguous, "
            "falling back to one union crop" % (expected_count, len(by_page)))

    got, note = crop_owner(doc, spans)
    if note:
        anomalies.append(note)
    return ([got] if got else []), anomalies


def crop_all(doc, owners, scope=None) -> tuple:
    """owners is [(label, storage_path)]; returns (items, anomalies).

    `items` is [(page, Rect, storage_path)], ready for
    `question_figures.write_crops`. `scope` is forwarded to `landmarks()` --
    see `LAYOUT_OVERRIDES` above.

    `owners` may repeat the SAME label with different storage_paths -- that
    is exactly how `render_parts.asset_plan()` now reports a multi-figure
    owner (style-guide.md SS5), one entry per surviving figure, slot/slot2/...
    All paths for one label are grouped here and handed to
    `crop_owner_multi()` together, in the order given, so its "how many
    pictures does this band actually print" logic sees the true expected
    count instead of being asked once per path independently.
    """
    seq = landmarks(doc, scope)
    bd = bands(doc, seq)
    by_label: dict = {}
    for lab, path in owners:
        by_label.setdefault(lab, []).append(path)

    items, anomalies = [], []
    for lab, paths in by_label.items():
        spans = bd.get(lab)
        if not spans:
            anomalies.append("%s: no printed label found in the PDF" % lab)
            continue
        crops, notes = crop_owner_multi(doc, spans, len(paths))
        for note in notes:
            anomalies.append("%s: %s" % (lab, note))
        if len(crops) < len(paths):
            anomalies.append("%s: expected %d figure(s), only %d cropped -- "
                             "every later ordinal in this question would "
                             "shift" % (lab, len(paths), len(crops)))
        for (pno, rect), path in zip(crops, paths):
            items.append((pno, rect, path))
    return items, anomalies
