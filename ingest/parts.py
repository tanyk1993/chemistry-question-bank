"""Walk a STRUCTURED QUESTION paper docx (P2/P3) into questions -> parts ->
sub-parts, with figures attached by (qnum, part label).

SHAPE OF THIS DOCUMENT FAMILY -- verified against RI 2024 H2 P3 (9729), which
this module was written against. Do NOT assume it matches `questions.py`
(MCQ) or `answers.py` (the flat 2-column ANSWERS grid) -- it resembles both
and is neither.

  It is the 4-column SEAB grid named in handoff SS7 (qnum | letter | roman |
  content), BUT:

  1. TABLE BOUNDARIES DO NOT ALIGN WITH QUESTION BOUNDARIES. `questions.py`'s
     rule -- "row 0 not a bare integer means the table continues the previous
     question" -- assumes a question always starts a fresh table. It does not
     here: Q3 begins mid-table, at row 11 of a table whose first ten rows are
     the tail of Q2(c). A table is not a semantic unit in this family at all;
     `answers.py`'s "walk every row of every table, state carries across
     table boundaries" is the right precedent, extended from 2 columns to 4.

  2. COLUMN WIDTH IS NOT A DOCUMENT-WIDE CONSTANT, NOT EVEN A PER-TABLE ONE.
     Within ONE <w:tbl>, the grid can be redefined partway through: RI's
     Q2(c)/Q3 table uses 8 grid units per row for its first 11 rows and 7 for
     the rest, and naively deriving "the" column width from the whole table
     conflates the two scales and misreads every row in the smaller regime.
     The fix: re-derive unit widths whenever a row's TOTAL cell-width changes
     (a cheap, reliable regime boundary -- verified constant within each
     regime, changed only at the genuine grid redefinition), not once per
     table.

  3. SLOT PRESENCE IS DECIDED BY GRID POSITION (cumulative gridSpan), NOT BY
     PATTERN-MATCHING TEXT AFTER STRIPPING LEADING BLANKS. `questions.py`
     strips a variable number of leading blank cells and reads what is left;
     that loses which grid slot survived the strip, and "(i)" is genuinely
     ambiguous as text -- it is both a valid roman numeral AND a valid single
     letter. Position resolves it: whichever slot's cumulative width the cell
     sits at, is what it is, irrespective of its text. A slot's own regex
     (bare digits / a single letter / a roman numeral) is still checked before
     accepting a value, so a row of section boilerplate that happens to land
     at the right grid position (see 4) is not mistaken for a new question.

  4. SECTION BOILERPLATE ("Section A", "Answer ALL questions...", "Section
     B", "Answer ONE question from this section.", "[Total: 20]",
     "Additional answer space...") is not confined to its own standalone
     table (RI's cover-adjacent "Section A" instruction is its own table;
     "Section B"'s is two trailing rows appended to the SAME table as Q3(f)).
     It must be recognised and excluded wherever it falls, not assumed to
     live in a separate table.

  5. MARKS ARE PRINTED INLINE, not on their own row. "...Suggest the
     structure of product A.[1]" carries the part's mark allocation as a
     trailing "[n]" in the same cell as the question text; the question's
     running total is a separate "[Total: 20]" row at the end of the
     question. Neither `answers.py` (RI's mark scheme has no marks at all)
     nor `questions.py` (MCQ is 1 mark, uncontested) needed this.

Handoff SS0 item 4: P3 puts the rubric's organic Rules 6/11 back under real
load, and Rule 12 (tag count <= marks) needs the marks this module extracts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

from .oxml import NS, Wq, paragraph_html
from .answers import _classify_drawing, _load_rels, Figure

WPD = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

FIG_SENTINEL = "\x00FIG\x00"

#: A bare question number cell: "1".."99".
QNUM_RE = re.compile(r"^\s*(\d{1,2})\s*$")
#: A single-letter part label: "(a)".."(z)".
LETTER_RE = re.compile(r"^\s*\(([a-z])\)\s*$")
#: A roman-numeral sub-part label. Enumerated rather than a general roman
#: pattern, deliberately: an unbounded roman regex would accept "(c)" read as
#: the roman numeral 100, which is never what a SEAB paper means at this
#: depth. Papers seen so far do not go past (x); extend the tuple, do not
#: loosen the pattern, if one does.
_ROMAN_SEQ = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x")
ROMAN_RE = re.compile(r"^\s*\((%s)\)\s*$" % "|".join(_ROMAN_SEQ))

#: Marks printed inline at the end of a part's own text: "...[1]", "...[3]".
INLINE_MARKS_RE = re.compile(r"\[(\d+)\]\s*$")
#: The question's running total, its own row: "[Total: 20]".
TOTAL_MARKS_RE = re.compile(r"^\s*\[Total:\s*(\d+)\]\s*$", re.I)

#: Section / instruction boilerplate that is not question content, wherever
#: it falls (SS7 point 4 -- it is not confined to a table of its own).
_BOILERPLATE_RES = [
    re.compile(r"^\s*Section\s+[A-Z]\s*$", re.I),
    re.compile(r"^\s*Answer\s+(ALL|all|one|ONE)\b.*question", re.I),
    # No \b after "space": RI's footer cell holds two paragraphs back to
    # back with no separator between them ("...spaceIf you use..."), so a
    # trailing word boundary there never matches.
    re.compile(r"^\s*Additional answer space", re.I),
    re.compile(r"^\s*If you use the following pages\b", re.I),
]
#: A row that is nothing but the dotted answer-writing rule. Handwriting
#: space, not content; kept out of `content_html` the same way a blank
#: spacer row is.
_DOTTED_RE = re.compile(r"^[\s.․…‧]*$")


def _boilerplate(text: str) -> bool:
    return any(r.match(text) for r in _BOILERPLATE_RES)


def _is_cover_table(rows_xml) -> bool:
    """The 'For Examiner's Use' marks-summary grid on the cover. Its row 0
    cell 0 is literally that string -- SS7's OTHER kind of front matter
    (questions.py's cover-page rule was 'a figure before Q1', which does not
    catch this table because it has no figures, only rows that happen to
    contain bare digits '1', '2', '3' in the exact QNUM slot position and
    would otherwise be read as Q1/Q2/Q3 starting here)."""
    first_row = rows_xml[0].findall(Wq + "tc")
    return bool(first_row) and "for examiner" in _cell_text(first_row[0]).lower()


@dataclass
class Part:
    qnum: int
    label: str                       # "(a)" or "(a)(i)" -- no question number
    html: str = ""
    marks: int | None = None
    figures: list = field(default_factory=list)
    n_placeholders: int = 0

    @property
    def full_label(self) -> str:
        return f"{self.qnum}{self.label}"


@dataclass
class Question:
    qnum: int
    section: str | None = None       # 'A' / 'B', from the boilerplate seen
    intro_html: str = ""             # stem text before the first (a)
    parts: list = field(default_factory=list)
    marks_total: int | None = None   # from "[Total: N]"
    intro_figures: list = field(default_factory=list)
    n_intro_placeholders: int = 0


def _cell_text(tc) -> str:
    return "".join(tc.itertext(Wq + "t")).strip()


def _gridspan(tc) -> int:
    g = tc.find(Wq + "tcPr/" + Wq + "gridSpan")
    return int(g.get(Wq + "val")) if g is not None else 1


def _table_html(tbl) -> str:
    """A nested table inside a cell. As in `questions.py`: content in this
    family, not layout -- e.g. a data table handed to the student."""
    rows = []
    for tr in tbl.findall(Wq + "tr"):
        cells = []
        for tc in tr.findall(Wq + "tc"):
            cells.append("<td>%s</td>" % _cell_html(tc))
        if cells:
            rows.append("<tr>%s</tr>" % "".join(cells))
    if not rows:
        return ""
    return '<table class="qt">%s</table>' % "".join(rows)


def _cell_html(tc) -> str:
    out = []
    for child in tc:
        ln = etree.QName(child).localname
        if ln == "p":
            h = paragraph_html(child)
            if h.strip():
                out.append(h)
        elif ln == "tbl":
            h = _table_html(child)
            if h:
                out.append(h)
    return "\n".join(out)


def _row_cells(tr):
    """[(tc, text, html, width)] for one row's REAL <w:tc> elements -- one
    entry per actual cell in the XML, whatever grid width it spans. This is
    deliberately NOT python-docx's `row.cells`, which duplicates a merged
    cell's text once per spanned grid column and would make every gridSpan>1
    cell look like several identical cells in a row."""
    out = []
    for tc in tr.findall(Wq + "tc"):
        out.append((tc, _cell_text(tc), _cell_html(tc), _gridspan(tc)))
    return out


def _regimes(rows):
    """Split `rows` (list of per-row cell-lists) into runs sharing the same
    total cell width. SS7 point 2: the grid can be redefined mid-table, and
    total width is what reveals it -- verified constant within a regime,
    changed only at a real redefinition."""
    out = []
    i = 0
    while i < len(rows):
        total = sum(w for *_, w in rows[i])
        j = i
        while j < len(rows) and sum(w for *_, w in rows[j]) == total:
            j += 1
        out.append((i, j))
        i = j
    return out


def _unit_widths(rows):
    """(w0, w1, w2) for one regime: the qnum/letter/roman slot widths, each
    the MINIMUM width ever seen at that cumulative position (a wider cell
    there is a merge that skipped the slot, not the slot itself). w1/w2 are
    None when the regime never uses that many real cells -- SS7 point 3's
    "(i)" ambiguity is avoided entirely by never treating a 3-cell regime
    (qnum, letter, content -- no roman column at all) as if a 4th slot
    existed just because some OTHER cell happens to land at that offset."""
    max_cells = max(len(r) for r in rows)

    def min_width_at(pos):
        vals = []
        for cells in rows:
            c = 0
            for *_, w in cells:
                if c == pos:
                    vals.append(w)
                    break
                c += w
        return min(vals) if vals else None

    w0 = min_width_at(0) if max_cells >= 1 else None
    w1 = min_width_at(w0) if (w0 is not None and max_cells >= 2) else None
    w2 = (min_width_at(w0 + w1)
          if (w1 is not None and max_cells >= 4) else None)
    return w0, w1, w2


def _classify(cells, w0, w1, w2, anomalies=None):
    """One row -> (qnum, letter, roman, content_cells).

    A slot is CONSUMED whenever its grid position and width match, whether or
    not it carries a label -- an empty cell at the qnum slot still occupies
    that slot, and failing to advance past it (matching on width AND text
    together) was the first version of this function's bug: it left the
    slot's blank cell in front of the real letter cell, which then fell
    through into `content_cells` as if "(a)" were question prose.

    A label VALUE is only assigned when the cell's text also matches that
    slot's own pattern. Position alone would accept boilerplate that happens
    to land at the right offset (SS7 point 4) as a new label; conversely, if
    a slot-width cell carries text that does NOT match its pattern, that is
    reported rather than silently dropped -- SS9's rule that a check which
    cannot fail is not a check applies here too, to a slot that could
    silently absorb unexpected content."""
    pos = 0
    qnum = letter = roman = None
    i, n = 0, len(cells)
    if i < n and w0 is not None and pos == 0 and cells[i][3] == w0:
        text = cells[i][1]
        m = QNUM_RE.match(text)
        if m:
            qnum = int(m.group(1))
        elif text and anomalies is not None:
            anomalies.append("qnum slot holds unexpected text: %r" % text[:40])
        pos += cells[i][3]
        i += 1
    if i < n and w1 is not None and pos == w0 and cells[i][3] == w1:
        text = cells[i][1]
        m = LETTER_RE.match(text)
        if m:
            letter = "(%s)" % m.group(1)
        elif text and anomalies is not None:
            anomalies.append("letter slot holds unexpected text: %r" % text[:40])
        pos += cells[i][3]
        i += 1
    if i < n and w2 is not None and pos == w0 + w1 and cells[i][3] == w2:
        text = cells[i][1]
        m = ROMAN_RE.match(text)
        if m:
            roman = "(%s)" % m.group(1)
        elif text and anomalies is not None:
            anomalies.append("roman slot holds unexpected text: %r" % text[:40])
        pos += cells[i][3]
        i += 1
    return qnum, letter, roman, cells[i:]


def parse(document_xml, rels_xml):
    """Return (questions, figures, anomalies) for a structured question-paper
    docx (P2/P3 shape). `figures` is in document order -- handoff SS7:
    ordinal MUST follow DOM order, the frontend zips positionally."""
    rels = _load_rels(rels_xml)
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)

    questions: list[Question] = []
    anomalies: list[str] = []
    by_qnum: dict[int, Question] = {}
    cur_q: Question | None = None
    cur_letter: str | None = None
    cur_roman: str | None = None
    cur_part: Part | None = None
    cur_section: str | None = None

    def _emit(html_piece: str):
        """Attach a rendered content piece to whatever is currently open."""
        nonlocal cur_q, cur_part
        if not html_piece.strip() and FIG_SENTINEL not in html_piece:
            return
        n_fig = html_piece.count(FIG_SENTINEL)
        if cur_part is not None:
            cur_part.html = (cur_part.html + "\n" + html_piece).strip() \
                if cur_part.html else html_piece
            cur_part.n_placeholders += n_fig
        elif cur_q is not None:
            cur_q.intro_html = (cur_q.intro_html + "\n" + html_piece).strip() \
                if cur_q.intro_html else html_piece
            cur_q.n_intro_placeholders += n_fig
        else:
            anomalies.append("content before Q1: %r" % html_piece[:60])

    for tbl in body.findall("w:tbl", NS):
        rows_xml = tbl.findall("w:tr", NS)
        if not rows_xml:
            continue
        if _is_cover_table(rows_xml):
            continue
        rows = [_row_cells(tr) for tr in rows_xml]
        # Drop rows with no real cells at all (shouldn't occur, but a table
        # row with zero <w:tc> would break width derivation).
        rows_nonempty_idx = [i for i, r in enumerate(rows) if r]
        if not rows_nonempty_idx:
            continue

        for start, end in _regimes(rows):
            regime_rows = rows[start:end]
            w0, w1, w2 = _unit_widths(regime_rows)

            for cells in regime_rows:
                # Boilerplate, the question total, and pure answer-space rows
                # are recognised from the RAW row text, before `_classify()`
                # ever runs -- SS7 #4's text can sit at the qnum slot's grid
                # position (a standalone-table row is one wide cell, which
                # matches width w0 there), and classifying it first would
                # consume it as an (unmatched, logged) qnum cell and leave an
                # EMPTY content_cells behind, so the boilerplate text would
                # never reach the checks below at all.
                raw_text = " ".join(t for _, t, _, _ in cells if t)
                if _boilerplate(raw_text):
                    m = re.match(r"^\s*Section\s+([A-Z])\s*$", raw_text, re.I)
                    if m:
                        cur_section = m.group(1).upper()
                    continue
                m = TOTAL_MARKS_RE.match(raw_text)
                if m:
                    if cur_q is not None:
                        cur_q.marks_total = int(m.group(1))
                    continue
                has_fig = any(FIG_SENTINEL in h for _, _, h, _ in cells)
                if not has_fig and _DOTTED_RE.match(raw_text):
                    continue  # pure answer-space / dotted-line row

                qn, lt, rm, content_cells = _classify(cells, w0, w1, w2, anomalies)

                content_html = "\n".join(
                    h for _, _, h, _ in content_cells if h.strip()
                    or FIG_SENTINEL in h)
                content_text = " ".join(
                    t for _, t, _, _ in content_cells if t)

                # --- new question ---
                if qn is not None:
                    if qn in by_qnum:
                        anomalies.append(
                            "Q%d relabelled a second time -- table/question "
                            "boundaries may be more tangled than assumed"
                            % qn)
                        cur_q = by_qnum[qn]
                    else:
                        cur_q = Question(qnum=qn, section=cur_section)
                        questions.append(cur_q)
                        by_qnum[qn] = cur_q
                    cur_letter = None
                    cur_roman = None
                    cur_part = None

                if cur_q is None:
                    if content_text:
                        anomalies.append(
                            "content before first question: %r"
                            % content_text[:60])
                    continue

                # --- new part / sub-part ---
                # A bare-letter Part is only created when the row sets JUST
                # the letter. When letter and roman are set together on one
                # row (Q1(d)(i), Q2(a)(i): no separate intro line for the
                # bare letter at all), creating "(d)" first would leave a
                # spurious empty Part ahead of the real "(d)(i)" one.
                if lt is not None:
                    cur_letter, cur_roman = lt, None
                    if rm is None:
                        cur_part = Part(qnum=cur_q.qnum, label=cur_letter)
                        cur_q.parts.append(cur_part)
                if rm is not None:
                    if cur_letter is None:
                        anomalies.append(
                            "Q%d%s: roman numeral with no letter part open"
                            % (cur_q.qnum, rm))
                    else:
                        cur_roman = rm
                        cur_part = Part(qnum=cur_q.qnum,
                                         label=cur_letter + cur_roman)
                        cur_q.parts.append(cur_part)

                # --- content, and any inline mark allocation it carries ---
                if content_html.strip() or FIG_SENTINEL in content_html:
                    _emit(content_html)
                mm = INLINE_MARKS_RE.search(content_text)
                if mm:
                    target = cur_part if cur_part is not None else None
                    if target is not None:
                        target.marks = int(mm.group(1))

    # --- figures, in true document order, attributed to question + part ---
    figures: list[Figure] = []
    order = 0
    cur_q_id = None
    cur_label = None   # None while in the intro, else "(a)" / "(a)(i)"

    # Rebuild a qnum/letter/roman cursor over the DOM a second time, mirroring
    # the first pass exactly, so a figure's row context is known independent
    # of any Part object bookkeeping above (kept deliberately separate, as in
    # `questions.py`, so a figure-attribution bug cannot also corrupt text).
    cur_letter2 = cur_roman2 = None
    for tbl in body.findall("w:tbl", NS):
        rows_xml = tbl.findall("w:tr", NS)
        if not rows_xml:
            continue
        if _is_cover_table(rows_xml):
            continue
        rows = [_row_cells(tr) for tr in rows_xml]
        for start, end in _regimes(rows):
            regime_rows = rows[start:end]
            w0, w1, w2 = _unit_widths(regime_rows)
            for tr, cells in zip(rows_xml[start:end], regime_rows):
                text = " ".join(t for _, t, _, _ in cells if t)
                if _boilerplate(text) or TOTAL_MARKS_RE.match(text):
                    continue
                qn, lt, rm, content_cells = _classify(cells, w0, w1, w2)
                if qn is not None:
                    cur_q_id = qn
                    cur_letter2 = cur_roman2 = None
                if lt is not None:
                    cur_letter2, cur_roman2 = lt, None
                if rm is not None:
                    cur_roman2 = rm
                cur_label = (
                    (cur_letter2 + cur_roman2) if cur_roman2
                    else cur_letter2 if cur_letter2 else None)

                for el in tr.iter():
                    ln = etree.QName(el).localname
                    if ln not in ("drawing", "object", "pict"):
                        continue
                    if any(etree.QName(a).localname == "Fallback"
                           for a in el.iterancestors()):
                        continue  # AlternateContent VML restatement
                    if any(etree.QName(a).localname in
                           ("drawing", "object", "pict")
                           for a in el.iterancestors()):
                        # Nested inside ANOTHER drawing -- a group shape's own
                        # text box embedding a copy of the same image for
                        # legacy-shape support (found on Q4(c)(iii): the
                        # Choice branch's group shape has an internal txbx
                        # referencing the identical media/image11.emf, one
                        # level below the drawing already being counted).
                        # oxml.py's own run walker never recurses into a
                        # drawing's children, so a nested one is invisible to
                        # it and must be invisible here too, or it silently
                        # doubles this figure's placeholder/figure count.
                        continue
                    if not any(etree.QName(a).localname == "tc"
                               for a in el.iterancestors()):
                        continue  # not inside a real cell of THIS row
                    if cur_q_id is None:
                        anomalies.append("figure before Q1 ignored (cover page)")
                        continue
                    fig = _classify_drawing(el, rels)
                    fig.index = order
                    fig.qnum = cur_q_id
                    fig.part = cur_label
                    fig.anchored = el.find(".//{%s}anchor" % WPD) is not None
                    fig.cell = next((id(a) for a in el.iterancestors()
                                     if etree.QName(a).localname == "tc"), None)
                    figures.append(fig)
                    order += 1

    # Group raw figures into "one picture" clusters by ADJACENCY IN THE
    # RENDERED TEXT, not by sharing a table cell. `questions.py`'s rule --
    # merge consecutive same-kind='shape' figures in the same cell -- is
    # right for a picture built from several native-shape layers sitting on
    # top of each other, but wrong here: Q1(c)'s intro is ONE wide cell that
    # holds THREE SEPARATE reaction-scheme structures plus a chart, each one
    # surrounded by its own reaction-equation text. Same cell, four distinct
    # pictures. What actually distinguishes "one picture" is whether two
    # placeholders sit back to back with nothing but whitespace between them
    # in the text a reader sees -- which is exactly what the collapse regex
    # below tests too, so the two are tied together by construction instead
    # of two separate heuristics that can (and here, did) disagree. This
    # also generalises the README's "a chart plus shapes drawn over it is
    # one picture" note to any kind mix, not just consecutive shapes.
    _run_re = re.compile(r"(?:%s\s*)+" % re.escape(FIG_SENTINEL))

    def _merge_owner(raw_figs, html):
        runs = [m.group(0).count(FIG_SENTINEL) for m in _run_re.finditer(html)]
        if sum(runs) != len(raw_figs):
            anomalies.append(
                "%d figures but placeholder runs sum to %d for the same "
                "owner -- left unmerged, ordinals may still rotate"
                % (len(raw_figs), sum(runs)))
            return raw_figs, html
        merged, i = [], 0
        for n in runs:
            group = raw_figs[i:i + n]
            i += n
            rep = group[0]
            rep.n_parts = n
            merged.append(rep)
        if len(merged) != len(raw_figs):
            anomalies.append("%d native drawings merged into %d pictures"
                             % (len(raw_figs), len(merged)))
        return merged, _run_re.sub(FIG_SENTINEL, html)

    by_owner_raw: dict[tuple, list[Figure]] = {}
    for f in figures:
        by_owner_raw.setdefault((f.qnum, f.part), []).append(f)

    ordered_figures: list[Figure] = []
    for q in questions:
        raw = by_owner_raw.get((q.qnum, None), [])
        q.intro_figures, q.intro_html = _merge_owner(raw, q.intro_html)
        q.n_intro_placeholders = q.intro_html.count(FIG_SENTINEL)
        ordered_figures.extend(q.intro_figures)
        for p in q.parts:
            raw = by_owner_raw.get((p.qnum, p.label), [])
            p.figures, p.html = _merge_owner(raw, p.html)
            p.n_placeholders = p.html.count(FIG_SENTINEL)
            ordered_figures.extend(p.figures)
    figures = ordered_figures
    for n, f in enumerate(figures):
        f.index = n

    # --- placeholder/figure consistency, per handoff SS7's costliest defect
    # class: a mismatch here means every later ordinal would rotate. ---
    for q in questions:
        if q.n_intro_placeholders != len(q.intro_figures):
            anomalies.append(
                "Q%d intro: %d placeholders but %d figures"
                % (q.qnum, q.n_intro_placeholders, len(q.intro_figures)))
        for p in q.parts:
            if p.n_placeholders != len(p.figures):
                anomalies.append(
                    "Q%d%s: %d placeholders but %d figures"
                    % (p.qnum, p.label, p.n_placeholders, len(p.figures)))

    seen = [q.qnum for q in questions]
    if seen != sorted(seen) or len(set(seen)) != len(seen):
        anomalies.append("question numbers out of order or duplicated: %s" % seen)

    # THIS MODULE IS FOR STRUCTURED (P2/P3) PAPERS ONLY. An MCQ paper run
    # through here would find question numbers, find no lettered parts at
    # all, and file every option row as unlabelled intro prose -- the same
    # silent-wrong-answer failure `questions.py` refuses loudly for the
    # reverse case.
    no_parts = [q.qnum for q in questions if not q.parts]
    if len(no_parts) > len(questions) // 2:
        raise ValueError(
            "%d of %d questions have no lettered parts at all. This looks "
            "like an MCQ paper; ingest.parts handles STRUCTURED papers only "
            "(see the note in the source). Questions with no parts: %s"
            % (len(no_parts), len(questions), no_parts[:10]))

    return questions, figures, anomalies
