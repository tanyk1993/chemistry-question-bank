"""Walk a QUESTION paper docx into per-question stems, options and figures --
the PARAGRAPH-FLOW shape (plain paragraphs, not one table per question).

SHAPE OF THIS DOCUMENT FAMILY -- verified against EJC 2024 H2 P1 (MCQ), do not
assume it matches `questions.py`'s table-shape family (RI 2024 H2 P1):

  No per-question table. Question numbers and option letters are each their OWN
  `w:r` run inside an ordinary paragraph, not a table cell -- confirmed by
  direct XML inspection across all 30 questions of this paper. Three option
  layouts occur, and (unlike the table family) they are NOT announced by any
  container difference -- only by run-level detail:

    - tab-inline   one paragraph, "A<tab>18.6%<tab>B<tab>37.3%..." (Q1, Q2)
    - one-per-para four separate paragraphs, each starting "A ...", "B ..." (Q8,
      Q11, Q20, Q21, and most of the paper)
    - embedded table  Q4 alone: the question still opens as a QSTART paragraph,
      but its four options sit in a nested `w:tbl` with [letter | molecule |
      shape | angle] columns -- handled by reusing questions.py's own
      `_split_options`/`_cell_html`, which already gets this layout right.

  A "1/2/3 only" multi-statement item (Q6, Q7, Q10, Q17, Q25, Q29) is written
  TWO different ways in this one document, and both must survive: most
  statements are typed plainly ("1The lattice energy...", digit glued straight
  onto the sentence, no `w:numPr` at all -- Q6, and statements 2-3 of Q10), but
  four of Q7's and the first of Q10's are genuine Word `w:numPr` numbered-list
  paragraphs (confirmed: only 5 numPr paragraphs in the whole document, at
  Q7's four relationships and Q10's very first statement) whose visible number
  is NOT in the extracted text at all -- Word supplies it at render time from
  the list definition. The two are handled differently on purpose: a typed
  digit is already indistinguishable from ordinary prose and needs nothing
  extra; a genuine numPr paragraph is grouped with any other CONSECUTIVE numPr
  paragraphs into one `<ol class="stmts">...</ol>` block (style-guide.md
  section 2), which is the only way to get its number to print at all.

QUESTION BOUNDARIES
  `QSTART` matches a paragraph (never one with `w:numPr`, which is content, not
  a new question) whose text starts with a number equal to the expected next
  question number, followed directly by a capital letter or "(" -- i.e. no
  gap between the number and the question's own first word, which is what
  keeps this from also matching an in-stem digit like "1 only" or a
  temperature like "25 C". Validated against all 30 questions: zero false
  positives, zero misses.

OPTION-MARKER DETECTION -- the hard part, arrived at by direct evidence, not
by guessing a rule and hoping:

  A bare single-letter run ("A", "B", "C" or "D", nothing else in the run) is
  the genuine option marker for EXACTLY ONE of two independent, structural
  reasons -- anything else is incidental text that happens to look like one:

  TEST 1 (tab-inline layout, e.g. Q1): the run immediately following it, in
  the SAME paragraph, carries a `<w:tab/>`. Word tab-separates a marker from
  its own content in this layout, confirmed in Q1's raw XML: the marker run
  "A" is followed by a run whose first child is `<w:tab/>` then
  `<w:t>18.6%</w:t>`. A chemical formula glued directly after a bold letter --
  Q11's displayed equation "A(g) <-> 2B(g) + C(g)" -- carries no tab anywhere,
  confirmed by direct inspection, so this test correctly rejects it.

  TEST 2 (one-per-paragraph prose layout, e.g. Q8/Q11/Q20/Q21): the run is the
  FIRST non-empty run of its OWN paragraph, AND that paragraph is not centred
  (`oxml.paragraph_is_centred` is False). The centred exclusion is load-bearing:
  Q11's displayed equation paragraph ALSO starts with a bare bold "A" as its
  first run, so "first run of paragraph" alone cannot tell it apart from the
  genuine option-A paragraph three paragraphs later. What does: every displayed
  equation and figure-caption paragraph in this document carries
  `<w:jc w:val="center"/>` (confirmed for Q11's equation, Q11's graph, and
  every other stem-only centred paragraph checked), while every genuine stem
  and option paragraph is `jc="both"` (justified) or unset. A centred paragraph
  is a DISPLAY element, never an option.

  Once "A" is accepted this way (test 2, no tab), scanning for "B" moves on to
  the NEXT paragraph rather than continuing within the same one -- unlike a
  test-1 acceptance, which does continue within the paragraph (needed for
  Q1's B/C/D, which live in the SAME paragraph as A). This is what stops
  option A's own self-reference (Q11: "The decomposition of A is
  endothermic.") from being mistaken for marker B: by the time that embedded
  "A" is reached, "A" has already been accepted at its own (non-centred, first
  -of-paragraph) paragraph, so the search has already moved on to hunting "B"
  in a LATER paragraph, and the embedded "A" is simply the wrong letter.

  Validated against all 30 questions of EJC 2024 H2 P1: every question finds
  exactly 4 markers, in order A,B,C,D, with correct (manually spot-checked)
  stem/option content -- including every previously-broken case (Q1's tab
  layout, Q11's self-referencing option and embedded equation, Q4's nested
  table, Q8/Q20/Q21's FIG-bearing prose options).

FIGURES
  Classified the same way `questions.py` classifies them (reusing
  `answers._classify_drawing` and the Equation-OLE ProgID check), but
  attributed to a region by PARAGRAPH POSITION relative to the marker
  boundaries found above, rather than by table row: a drawing's containing
  paragraph position is compared against the (pidx, run-index) boundaries to
  decide stem vs option A/B/C/D. Native-shape merging uses the SAME paragraph
  as its "same cell" equivalent -- adjacent shapes drawn in one paragraph are
  one picture, mirroring questions.py's "same cell" rule.

NOT YET DONE HERE (deliberately -- this is "1. questions", not "2. diagrams"):
  fraction/equation OLE objects are classified but not yet read from the PDF;
  option-figure captions (Q8-style) are not yet re-attached; nothing here has
  been run against the FIGURE gate. The TEXT gate (which only needs stem/
  option/extra text, not asset placement) is the acceptance check for this
  module; the figure gate is the acceptance check for the next phase.

Handoff SS8: MCQ and structured share question_number, so anything joining on
number alone must pin q.type. This module is MCQ-only, same restriction as
questions.py, and raises the same way on a structured paper (see the note at
the end of `parse()`).
"""
from __future__ import annotations

import re

from lxml import etree

from .oxml import NS, Wq, _tokens_from_run, _omml_tokens, tokens_to_html, \
    paragraph_is_centred, paragraph_html
from .answers import _classify_drawing, _load_rels, Figure
from .questions import (Question, OPT_RE, QNUM_RE, FIG_SENTINEL,
                        _split_options, _cell_html, _table_html)
from .render_questions import _strip_tags

OFFICE = "urn:schemas-microsoft-com:office:office"

#: A question paragraph starts with its number directly against a capital
#: letter or "(" -- no gap. This is what keeps "1 only" (an option's own text)
#: or "25 C" (a temperature) from being mistaken for question 1 or question 25.
QSTART = re.compile(r"^(\d{1,2})\s{0,2}(?=[A-Z(])")

_LETTERS = "ABCD"


def _has_numpr(p) -> bool:
    return p.find(".//" + Wq + "numPr") is not None


def _para_text(p) -> str:
    return "".join(t.text or "" for t in p.findall(".//" + Wq + "t"))


def _run_bare_text(r) -> str:
    return "".join(t.text or "" for t in r.findall(Wq + "t")).strip()


def _run_has_tab(r) -> bool:
    return r.find(Wq + "tab") is not None


def _strip_leading_qnum(p, qnum) -> None:
    """Remove a question's own printed number from the front of its first
    paragraph's text, in place.

    QSTART finds the question BOUNDARY by matching this same prefix, but the
    boundary paragraph is then rendered whole into the stem -- so left alone,
    the flow-shape stem printed "24 Alcohol X ..." while the table-shape stem
    (questions.py) never carries the number at all: there it lives in its own
    table cell (row 0, cell 0), never mixed into the stem text. Caught by
    comparing a live EJC row against a live RI row side by side.

    The number's own run(s) are plain `<w:t>` text (mutated directly, so no
    formatting is ever split), but EJC separates the number from the stem's
    first word with a `<w:tab/>`, which is invisible to QSTART (it matches
    only `<w:t>` text, deliberately -- see the module docstring's "no gap"
    rule) and so would otherwise survive as a stray leading space once the
    digits themselves are blanked. This tab shows up in TWO different run
    shapes across this one document (confirmed by direct inspection: Q24 vs
    Q19/Q27) -- its own run with no `<w:t>` at all, or sharing a run with the
    stem's first word (`<w:tab/>` then `<w:t>` as siblings in one `<w:r>`) --
    so it is found structurally, by checking whether a tab in the run
    immediately following the digits comes BEFORE that run's own first
    `<w:t>` (or the run has no `<w:t>` at all), rather than assumed to always
    be its own run. Only that one immediately-following run is ever touched,
    and only when the digit prefix ended cleanly on a run boundary -- if it
    ended mid-run (number and first word already sharing one run), there is
    no separate tab to find, and touching the next run at all would risk
    eating real content.
    """
    runs = [c for c in p if etree.QName(c).localname == "r"]
    if not runs:
        return
    text = "".join(t.text or "" for r in runs for t in r.findall(Wq + "t"))
    m = QSTART.match(text)
    if not m or int(m.group(1)) != qnum:
        return
    cut = m.end()
    consumed = 0
    for r in runs:
        if cut <= 0:
            break
        ts = r.findall(Wq + "t")
        run_len = sum(len(t.text or "") for t in ts)
        if run_len == 0:
            consumed += 1
            continue
        if cut >= run_len:
            for t in ts:
                t.text = ""
            cut -= run_len
            consumed += 1
        else:
            for t in ts:
                n = len(t.text or "")
                if cut <= 0:
                    break
                if cut >= n:
                    t.text = ""
                    cut -= n
                else:
                    t.text = (t.text or "")[cut:]
                    cut = 0
            return   # ended mid-run -- no separate tab to look for
    # Q20 carries the tab as TWO consecutive tab-only runs, not one (confirmed
    # by direct inspection) -- so this keeps consuming tab-only runs until it
    # either meets a real tab+text run (removes that one tab, then stops -- the
    # Q19/Q27 shape) or a run with no tab at all (genuine content, stop without
    # touching it).
    i = consumed
    while i < len(runs):
        r = runs[i]
        tab = r.find(Wq + "tab")
        if tab is None:
            return
        ts = r.findall(Wq + "t")
        if ts and list(r).index(tab) > list(r).index(ts[0]):
            return   # a tab AFTER real text in this run is not the separator
        r.remove(tab)
        if ts:
            return   # this run also carries the stem's first real word
        i += 1


def _children_html(children) -> str:
    """Render an explicit list of paragraph children (not the whole paragraph).

    Used when a marker boundary falls mid-paragraph and only some of its
    children belong to the segment being rendered.
    """
    def gen():
        for child in children:
            ln = etree.QName(child).localname
            if ln == "r":
                yield from _tokens_from_run(child)
            elif ln in ("oMath", "oMathPara"):
                yield from _omml_tokens(child)
            elif ln in ("hyperlink", "smartTag", "sdt", "ins"):
                for sub in child.iter():
                    if etree.QName(sub).localname == "r" and sub.getparent() is child:
                        yield from _tokens_from_run(sub)
            elif ln in ("pPr", "bookmarkStart", "bookmarkEnd", "proofErr",
                        "commentRangeStart", "commentRangeEnd", "del", "subDoc"):
                continue
            else:
                raise ValueError("unhandled paragraph child <w:%s>" % ln)
    return tokens_to_html(gen())


def _find_marker_boundaries(plain_paras):
    """(letter -> (pidx, run_index)) for A-D, or fewer on failure.

    See the module docstring for TEST 1 / TEST 2 and why each is trusted.
    """
    boundaries = {}
    expected_code = ord("A")
    for pidx, el, runs, centred in plain_paras:
        if runs is None or expected_code > ord("D"):
            continue
        if not runs:
            continue
        first_nonempty_idx = next(
            (i for i, rr in enumerate(runs) if _run_bare_text(rr)), None)
        ri = 0
        while ri < len(runs) and expected_code <= ord("D"):
            r = runs[ri]
            expected_letter = chr(expected_code)
            if _run_bare_text(r) == expected_letter:
                tab_follows = (ri + 1 < len(runs)) and _run_has_tab(runs[ri + 1])
                first_of_para = (ri == first_nonempty_idx) and not centred
                if tab_follows or first_of_para:
                    boundaries[expected_letter] = (pidx, ri)
                    expected_code += 1
                    if tab_follows:
                        ri += 1
                        continue        # keep scanning this same paragraph
                    break                # prose style: move to next paragraph
            ri += 1
    return boundaries


_STMT_NUM_RE = re.compile(r"^(\d)(?:<b>)?\t(?:</b>)?")


def _wrap_stmt_lists(htmls: list) -> list:
    """Merge consecutive bare '<li>...</li>' entries into one <ol class="stmts">.

    `htmls` entries are either ordinary block HTML or a lone '<li>...</li>'
    string emitted for a genuine w:numPr paragraph (see module docstring). A
    RUN of consecutive numPr paragraphs is one statement list and must become
    one <ol>, not several one-item lists.

    A list that is OPEN (buf non-empty) also absorbs a typed "N<tab>..."
    paragraph immediately following it, PROVIDED N is exactly the next
    number in sequence -- Q10's statement 1 is the paper's only other numPr
    paragraph (module docstring), but its statements 2 and 3 are typed
    digit-then-tab prose like every other question's, so without this they
    render as a one-item <ol> followed by two plain <p class="qstem eqn">
    paragraphs: visibly different indent and no hanging-indent on wrap,
    even though the source PDF prints all three statements at the identical
    indent with no period after any number (confirmed by rendering the
    paper's own exported PDF page). Folding the typed ones into the SAME
    <ol> as more <li>s reproduces that -- the existing ol.stmts CSS already
    renders a numPr list correctly (Q7), so no new styling is needed.
    Guarded on the number actually being 2, 3, 4... in order, and only
    while a list is already open, so this cannot touch Q6/Q17/Q25/Q29's
    statement blocks, which have no numPr paragraph at all and never open
    an <ol> here to begin with.
    """
    out, buf = [], []
    def flush():
        if buf:
            out.append('<ol class="stmts">' + "".join(buf) + "</ol>")
            buf.clear()
    for h in htmls:
        if h.startswith("<li>") and h.endswith("</li>"):
            buf.append(h)
            continue
        if buf:
            m = _STMT_NUM_RE.match(h)
            if m and int(m.group(1)) == len(buf) + 1:
                buf.append("<li>" + h[m.end():] + "</li>")
                continue
        flush()
        out.append(h)
    flush()
    return out


def _render_segments(plain_paras, boundaries):
    """('STEM' | 'A'..'D') -> assembled HTML, from the marker boundaries."""
    segs = [("STEM", None, boundaries["A"])] + \
           [(_LETTERS[i], boundaries[_LETTERS[i]],
             boundaries[_LETTERS[i + 1]] if i + 1 < 4 else None)
            for i in range(4)]

    result = {}
    for name, lo, hi in segs:
        htmls = []
        for pidx, el, runs, centred in plain_paras:
            if runs is None:
                lo_p = lo[0] if lo else -1
                hi_p = hi[0] if hi else 10 ** 9
                in_range = (lo_p <= pidx <= hi_p) if lo else (pidx < hi_p)
                if in_range:
                    h = _children_html(list(el))
                    if _strip_tags(h):
                        htmls.append("<li>" + h + "</li>")
                continue
            sel = []
            for ri, r in enumerate(runs):
                pos = (pidx, ri)
                after_lo = True if lo is None else (pos > lo)
                before_hi = True if hi is None else (pos < hi)
                if after_lo and before_hi:
                    sel.append(r)
            if not sel:
                continue
            h = paragraph_html(el) if len(sel) == len(runs) else _children_html(sel)
            # A TAG-AWARE emptiness check, not a raw h.strip(): a paragraph
            # that is nothing but a formatting spacer -- e.g. a stray
            # "<b><br></b>" between a question's last option and the next
            # question's opening paragraph -- has plenty of non-whitespace
            # TEXT (the tags themselves) but zero visible content, and a raw
            # .strip() lets it through. Caught here because option D's
            # segment runs to the end of the whole span (hi=None) and would
            # otherwise absorb that spacer as if it were part of D's answer.
            if _strip_tags(h) or FIG_SENTINEL in h:
                htmls.append(h)
        htmls = _wrap_stmt_lists(htmls)
        result[name] = "\n".join(htmls)
    return result


def _region_of(pidx, ri, boundaries):
    """'stem' | 'A'..'D' for a (pidx, run-index) position, once markers are known."""
    if pidx < boundaries["A"][0] or (pidx, ri) < boundaries["A"]:
        return "stem"
    order = [boundaries[l] for l in _LETTERS]
    for i in range(4):
        lo = order[i]
        hi = order[i + 1] if i + 1 < 4 else (10 ** 9, 0)
        if lo <= (pidx, ri) < hi:
            return _LETTERS[i]
    return _LETTERS[-1]


def _iter_top_figures(r):
    """Top-level drawing/object/pict elements inside one w:r, outermost only.

    A `<w:drawing>` group-shape can itself contain a NESTED `<w:object>` deep
    inside one of its text boxes -- confirmed in Q6's Hess-cycle diagram,
    whose outer group shape has a text box holding what turned out to be a
    second embedded object several levels down. A plain recursive `.iter()`
    walk finds both and counts the diagram twice. Once a drawing/object/pict
    is found here, its own descendants are not searched further -- whatever
    picture reference it needs (blip / chart / imagedata) is found by
    `_classify_drawing`'s own recursive search of THAT element, so nothing is
    lost by not recursing past it here. `mc:Fallback` subtrees are skipped
    entirely: they are a VML restatement of the SAME figure as the sibling
    `mc:Choice`, not a second one.
    """
    def walk(el):
        for child in el:
            ln = etree.QName(child).localname
            if ln == "Fallback":
                continue
            if ln in ("drawing", "object", "pict"):
                yield child
                continue
            yield from walk(child)
    yield from walk(r)


def _own_ole(d):
    """The OLEObject that belongs to THIS figure, not one nested inside a
    child figure a group shape happens to contain.

    Q6's Hess-cycle diagram is one `w:drawing` group shape whose text box
    happens to hold its OWN nested `w:object` several levels down (an
    embedded equation label). A plain `.//OLEObject` search on the outer
    drawing finds that nested object's ProgID and misclassifies the whole
    diagram as an equation. This walk stops at the first NESTED
    drawing/object/pict boundary it meets -- exactly where `_iter_top_figures`
    stops too -- so only an OLEObject that is genuinely part of `d` itself
    (not of some other figure `d` happens to contain) is considered.
    """
    def walk(el):
        for child in el:
            q = etree.QName(child)
            if q.namespace == OFFICE and q.localname == "OLEObject":
                return child
            if q.localname in ("drawing", "object", "pict"):
                continue    # a nested figure boundary -- not part of `d`
            found = walk(child)
            if found is not None:
                return found
        return None
    return walk(d)


def _collect_figures_flow(span, qnum, boundaries, rels, order_start):
    """Figures inside one paragraph-flow question span, in document order."""
    figures = []
    order = order_start
    pidx = 0
    for el in span:
        if etree.QName(el).localname != "p":
            continue
        # Position each drawing by (pidx, run-index within this paragraph),
        # the same coordinate system marker boundaries use.
        runs = [c for c in el if etree.QName(c).localname == "r"]
        for ri, r in enumerate(runs):
            for d in _iter_top_figures(r):
                fig = _classify_drawing(d, rels)
                ole = _own_ole(d)
                if ole is not None and (ole.get("ProgID") or "").startswith("Equation"):
                    fig.kind = "equation"
                fig.index = order
                fig.qnum = qnum
                fig.part = ("stem" if not boundaries
                           else _region_of(pidx, ri, boundaries))
                # "same paragraph AND same region" is this shape's merge unit
                # -- NOT paragraph alone. Q14 tab-separates two different
                # options' graphs onto one shared paragraph ("A...B..." on one
                # line, "C...D..." on the next, mirroring Q1's text layout);
                # merging by paragraph alone fused option A's graph with
                # option B's into one picture. Region already carries exactly
                # the distinction needed (which option, or the stem) at no
                # extra cost, since it is computed one line above.
                fig.cell = (pidx, fig.part)
                figures.append(fig)
                order += 1
        pidx += 1
    return figures, order


def parse(document_xml, rels_xml):
    """Return (questions, figures, anomalies) for a paragraph-flow question paper.

    Same contract as `questions.parse()` -- see that module's docstring for
    the return shape and handoff SS7's ordinal rule. Callers that need to
    support both document families dispatch on shape (e.g. try the table
    parser first; if it finds zero questions, this is the other shape).
    """
    rels = _load_rels(rels_xml)
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    kids = list(body)

    anomalies: list[str] = []

    starts = []
    expected = 1
    for i, c in enumerate(kids):
        if etree.QName(c).localname != "p":
            continue
        if _has_numpr(c):
            continue
        m = QSTART.match(_para_text(c))
        if m and int(m.group(1)) == expected:
            starts.append(i)
            expected += 1

    questions: list[Question] = []
    all_figures: list[Figure] = []
    order = 0

    for k, start_idx in enumerate(starts):
        qnum = k + 1
        end_idx = starts[k + 1] if k + 1 < len(starts) else len(kids)
        span = kids[start_idx:end_idx]
        _strip_leading_qnum(span[0], qnum)
        q = Question(qnum=qnum)
        questions.append(q)

        tbls = [el for el in span if etree.QName(el).localname == "tbl"]
        table_opt = None
        for tbl in tbls:
            rows = tbl.findall("w:tr", NS)
            opt_rows = [(i, _split_options(tr.findall("w:tc", NS)))
                       for i, tr in enumerate(rows)]
            opt_rows = [(i, o) for i, o in opt_rows if o]
            if opt_rows:
                table_opt = (tbl, rows, opt_rows)
                break

        if table_opt:
            tbl, rows, opt_rows = table_opt
            for el in span:
                if el is tbl:
                    break
                if etree.QName(el).localname == "p" and not _has_numpr(el):
                    h = paragraph_html(el)
                    q.n_placeholders += h.count(FIG_SENTINEL)
                    if h.strip():
                        q.stem_html = (q.stem_html + "\n" + h).strip() \
                            if q.stem_html else h
            first_opt = opt_rows[0][0]
            if first_opt > 0:
                hdr_cells = rows[first_opt - 1].findall("w:tc", NS)
                q.opt_headers = [_cell_html(c) for c in hdr_cells[1:]]
            for i, opts in opt_rows:
                for letter, content in opts:
                    vals = [_cell_html(c) for c in content]
                    q.options[letter] = vals
                    q.n_placeholders += sum(v.count(FIG_SENTINEL) for v in vals)
            # Figures inside the embedded table are not yet classified here --
            # none occur in EJC 2024 H2 P1's one table-shaped question (Q4).
            # Left as a documented gap rather than silently guessed at, so a
            # future paper that DOES put a figure in one of these cells fails
            # loudly (placeholder/figure mismatch below) instead of mis-filing it.
            if any(v.count(FIG_SENTINEL) for row in q.options.values() for v in row):
                anomalies.append(
                    "Q%d: figure inside embedded option table -- not yet "
                    "classified by questions_flow.py, see module docstring" % qnum)
            continue

        plain_paras = []   # (pidx, element, [w:r] or None if numPr, centred)
        pidx = 0
        for el in span:
            if etree.QName(el).localname != "p":
                continue
            if _has_numpr(el):
                plain_paras.append((pidx, el, None, False))
                pidx += 1
                continue
            runs = [c for c in el if etree.QName(c).localname == "r"]
            plain_paras.append((pidx, el, runs, paragraph_is_centred(el)))
            pidx += 1

        boundaries = _find_marker_boundaries(plain_paras)
        if len(boundaries) != 4:
            anomalies.append("Q%d: only found %d/4 option markers (%s) -- "
                             "left with no options" %
                             (qnum, len(boundaries), sorted(boundaries)))
            figs, order = _collect_figures_flow(span, qnum, {}, rels, order)
            all_figures.extend(figs)
            continue
        order_letters = sorted(boundaries.items(), key=lambda kv: kv[1])
        if [l for l, _ in order_letters] != list(_LETTERS):
            anomalies.append("Q%d: option markers found out of order: %s" %
                             (qnum, order_letters))
            figs, order = _collect_figures_flow(span, qnum, {}, rels, order)
            all_figures.extend(figs)
            continue

        segments = _render_segments(plain_paras, boundaries)
        q.stem_html = segments["STEM"]
        for L in _LETTERS:
            html = segments[L]
            q.options[L] = [html] if (html.strip() or FIG_SENTINEL in html) else [""]
        q.n_placeholders = (q.stem_html.count(FIG_SENTINEL)
                           + sum(v.count(FIG_SENTINEL)
                                 for row in q.options.values() for v in row))

        figs, order = _collect_figures_flow(span, qnum, boundaries, rels, order)
        all_figures.extend(figs)

    # Native-shape merging: adjacent shapes in the SAME paragraph are one
    # picture (this shape's equivalent of questions.py's "same cell" rule).
    merged: list = []
    for f in all_figures:
        if (merged and f.kind == "shape" and merged[-1].kind == "shape"
                and f.cell is not None and f.cell == merged[-1].cell
                and f.qnum == merged[-1].qnum):
            merged[-1].n_parts += 1
            continue
        f.n_parts = 1
        merged.append(f)
    if len(merged) != len(all_figures):
        anomalies.append("%d native shapes merged into %d pictures by paragraph"
                         % (len(all_figures), len(merged)))
    all_figures = merged
    for n, f in enumerate(all_figures):
        f.index = n

    by_q = {}
    for f in all_figures:
        by_q.setdefault(f.qnum, []).append(f)
    for q in questions:
        q.figures = by_q.get(q.qnum, [])
        q.n_stem_figs = sum(1 for f in q.figures if f.part == "stem")
        q.n_opt_figs = sum(1 for f in q.figures if f.part in _LETTERS)

    for q in questions:
        placeholders = q.n_placeholders
        if placeholders != len(q.figures):
            anomalies.append(
                "Q%d: %d placeholders but %d figures -- ordinals would rotate"
                % (q.qnum, placeholders, len(q.figures)))
        # Rewrite plain letter parts ('A') to the option-figure convention
        # ('option:A') that render_questions.py expects.
        for f in q.figures:
            if f.part in _LETTERS:
                f.part = "option:" + f.part
            elif f.part == "stem":
                pass
            # else: 'stem' from a no-boundaries question, left as-is.

    seen = [q.qnum for q in questions]
    if seen != sorted(seen) or len(set(seen)) != len(seen):
        anomalies.append("question numbers out of order or duplicated: %s" % seen)

    # THIS MODULE IS FOR MCQ PAPERS ONLY -- see questions.py's identical note.
    no_opts = [q.qnum for q in questions if len(q.options) < 2]
    if len(no_opts) > len(questions) // 4:
        raise ValueError(
            "%d of %d questions have fewer than two options. This looks like a "
            "STRUCTURED paper; ingest.questions_flow handles MCQ only. "
            "Questions without options: %s"
            % (len(no_opts), len(questions), no_opts[:10]))
    if no_opts:
        anomalies.append("questions with fewer than 2 options: %s" % no_opts)

    return questions, all_figures, anomalies
