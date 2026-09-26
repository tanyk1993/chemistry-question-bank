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

from .oxml import (CENTRE, NS, Wq, load_bullet_numids, paragraph_html,
                    paragraph_numid)
from .answers import _classify_drawing, _load_rels, Figure

WPD = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

FIG_SENTINEL = "\x00FIG\x00"

#: numIds that are bullet lists, for the current document only. Populated by
#: `parse()` (from word/numbering.xml, when given) before any cell is
#: walked, and read by `_cell_html()`. Module-level rather than threaded
#: through `_row_cells` -> `_cell_html` -> `_table_html` -> `_cell_html`,
#: matching CENTRE/FIG_SENTINEL's existing style of assembly-time signals in
#: this single-document, single-pass batch script.
_BULLET_NUMIDS: set[str] = set()

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
#: A figure caption ("Fig. 3.1") or table caption ("Table 2.2"), alone on a
#: line apart from optional bold markup. Anchored whole-line on purpose: a
#: SENTENCE that merely opens with the same words -- "Fig. 2.1 shows the mole
#: fractions of..." -- is prose, not a caption, and this paper has one of
#: those for nearly every figure it prints.
CAPTION_RE = re.compile(
    r"^(?:<b>\s*)?(Fig(?:ure)?\.?|Table)\s*\d+\.\d+\.?\s*(?:</b>\s*)?$")
#: A figure placeholder with its caption glued to the same line. Word keeps
#: the drawing and its caption in ONE paragraph, so they arrive inseparable.
FIG_CAPTION_RE = re.compile(
    r"^((?:%s\s*)+)((?:<b>\s*)?(?:Fig(?:ure)?\.?|Table)\s*\d+\.\d+\.?(?:\s*</b>)?)\s*$"
    % re.escape(FIG_SENTINEL))

INLINE_MARKS_RE = re.compile(r"\[(\d+)\]\s*$")
#: The same allocation as INLINE_MARKS_RE, matched in the HTML so it can be
#: REPLACED, in place, by the styled badge once its value is safely in
#: Part.marks. Group 1 is the digits, group 2 keeps any close tags that
#: trail it, so the substitution cannot unbalance the markup.
#:
#: Replaced IN PLACE, not stripped -- see the "one value, one place" comment
#: at the call site below for why an earlier version of this stripped the
#: allocation and re-appended a synthesized badge at the very end of the
#: PART instead: that put the badge after every later paragraph and table
#: too, which is wrong whenever the paper prints "[n]" mid-part (RI 2024 H2
#: P3's own Q2(b)(i): "...stating its units. [1]" is followed by two more
#: paragraphs and a table that are actually shared intro for part (ii), not
#: more of (i)'s own content -- confirmed against the Word-exported PDF,
#: which prints the "[1]" in exactly that spot, well before the table).
#: Substituting in place, chunk by chunk as each is emitted, keeps the badge
#: exactly where the paper itself prints it, however many chunks follow.
INLINE_MARKS_HTML_RE = re.compile(r"\[(\d+)\]\s*((?:</[a-z]+>\s*)*)$")
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
            # The CENTRE sentinel is dropped HERE, and only here. A `table.qt
            # td` is already text-align:center by the existing CSS, so inside
            # a data cell the sentinel says nothing and would render as a
            # literal stray "C" (its surrounding U+0000 bytes are invisible,
            # the letter between them is not).
            #
            # It must NOT be stripped in `_cell_html` itself: that runs for
            # EVERY cell, including the wide content cell a question's prose
            # lives in, where centring is real information. This paper centres
            # all 15 of its "Fig. n.n" / "Table n.n" captions with a direct
            # <w:jc w:val="center">, and stripping there silently left-aligned
            # every one of them.
            cells.append("<td>%s</td>" % _cell_html(tc).replace(CENTRE, ""))
        if cells:
            rows.append("<tr>%s</tr>" % "".join(cells))
    if not rows:
        return ""
    return '<table class="qt">%s</table>' % "".join(rows)


def _cell_html(tc) -> str:
    """HTML for one cell's contents, CENTRE sentinels intact.

    Centring is preserved here deliberately: this runs for the wide content
    cell a question's prose lives in, where a centred paragraph is real
    information (every "Fig. n.n" / "Table n.n" caption in this paper is
    centred). Only `_table_html`, building a `<td>`, drops the sentinel --
    see the note there.

    Consecutive numPr paragraphs whose numId is a bullet (`_BULLET_NUMIDS`)
    are grouped into ONE `<ul class="stmts">`, not one `<p>` each: every list
    this pipeline has seen sits entirely inside a single cell (survey: RI
    2024 H2 P3's four multi-item lists, three numId changes mid-list among
    them -- Word starts a fresh <w:num> per list even within one cell), so
    grouping at cell level, flushed whenever a non-list paragraph or a
    nested table is hit, is enough; it does not need to reach across cells.
    """
    out = []
    buf: list[str] = []

    def _flush():
        if buf:
            # Joined with a literal space, not "": a browser ignores it
            # between block-level <li>s, but `_strip()` (content_text, the
            # search index) only removes tags, not text -- an empty join
            # would run "C8H14O6" straight into "hot acidic" with no word
            # boundary. The block must stay ONE line (no "\n"): reconcile()
            # and _render_owner() split html on "\n" and treat each line as
            # a unit, same as an already-one-line <table> block.
            out.append('<ul class="stmts">%s</ul>' % " ".join(buf))
            buf.clear()

    for child in tc:
        ln = etree.QName(child).localname
        if ln == "p":
            numid = paragraph_numid(child)
            if numid is not None and numid in _BULLET_NUMIDS:
                h = paragraph_html(child)
                if h.startswith(CENTRE):
                    h = h[len(CENTRE):]
                if h.strip():
                    buf.append("<li>%s</li>" % h)
                continue
            _flush()
            h = paragraph_html(child)
            if h.strip():
                out.append(h)
        elif ln == "tbl":
            _flush()
            h = _table_html(child)
            if h:
                out.append(h)
    _flush()
    return "\n".join(out)


def _split_captions(html: str) -> str:
    """Put every "Fig. n.n" / "Table n.n" caption on its own centred line.

    A figure and its caption are SEPARATE paragraphs in Word -- both centred
    -- but they arrive glued onto one line, because a row's content cells are
    joined without a break. The giveaway is a CENTRE sentinel sitting in the
    MIDDLE of a line: CENTRE is a paragraph-level marker, so one appearing
    anywhere but the start means two paragraphs were run together. That is
    the general rule this function restores, and on this paper it fires on
    exactly the 9 figure-caption lines and nothing else out of 144.

    Why it matters: a figure placeholder is an inline box, so a caption left
    on the same line renders BESIDE the figure rather than beneath it, which
    is not where the paper prints it.

    Captions are then centred unconditionally. Most carry a direct
    <w:jc w:val="center"> already; Fig. 5.2's is additionally pushed across
    with literal spaces, which mean nothing in HTML, so the padding is
    dropped in favour of real centring.

    Nothing is REORDERED. A Fig caption already sits after its figure and a
    Table caption before its table in this document; this only breaks the
    line between them. Sentinel count and order are untouched, so the
    placeholder/figure consistency check downstream still holds.
    """
    out = []
    for line in html.split("\n"):
        # Un-glue run-together paragraphs first, so a caption that was
        # carrying its own CENTRE marker mid-line becomes a line of its own.
        lead, *rest = line.split(CENTRE)
        segments = ([lead] if lead.strip() else []) \
            + [CENTRE + s for s in rest if s.strip()]
        for seg in (segments or [line]):
            centred = seg.startswith(CENTRE)
            body = seg[len(CENTRE):] if centred else seg
            m = FIG_CAPTION_RE.match(body)
            if m:
                # Still glued (one paragraph really did hold both).
                out.append((CENTRE if centred else "") + m.group(1).rstrip())
                out.append(CENTRE + m.group(2).strip())
            elif CAPTION_RE.match(body.strip()):
                out.append(CENTRE + body.strip())
            else:
                out.append(seg)
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


#: Consecutive FIG_SENTINEL runs, possibly whitespace-separated -- ADJACENCY
#: IN THE RENDERED TEXT is what "one picture" means here (see
#: `merge_owner_figures`), not sharing a table cell/paragraph.
#:
#: The whitespace only sits BETWEEN two sentinels (`\s*` gated behind a
#: second `%s`), never trailing after the LAST one in a run. A trailing
#: `(?:%s\s*)+` (the previous form of this regex) matches and therefore
#: DELETES the run's own trailing whitespace even when the "run" is a
#: single, non-adjacent figure -- caught via EJC 2024 H2 P2 Q4's Fig 4.1:
#: the drawing sits alone in its own centred paragraph, immediately
#: followed by its OWN separate centred "Fig. 4.1" caption paragraph, so
#: `merge_owner_figures` is called with `raw_figs` of length 1 and takes
#: the "already correct, nothing to merge" fast path -- but the ORIGINAL
#: regex still matched "FIG_SENTINEL\n" (the trailing `\s*` swallowing the
#: single newline that separates the figure paragraph's line from the
#: caption's) and replaced it with a bare sentinel, splicing the caption's
#: OWN leading CENTRE sentinel directly onto the same line as the figure's
#: -- `_render_owner`'s FIG_SENTINEL-splitting branch then re-prepends the
#: (correct) outer CENTRE onto that piece without ever stripping the
#: caption's now-embedded, second CENTRE, which leaked as a literal
#: "\x00C\x00" in the rendered caption. Confirmed by direct inspection of
#: `Question.intro_html` before `content_html()` ever runs: the raw string
#: reads `...</ol>\n\x00C\x00\x00FIG\x00\x00C\x00<b>Fig. 4.1</b>` -- one
#: newline consumed, two CENTRE sentinels left adjacent with nothing
#: between them. Silent (no visible defect) whenever the swallowed
#: paragraph break's own next paragraph is NOT independently centred, or
#: happens to look fine centred anyway -- which is presumably why no
#: earlier paper surfaced it -- but always a genuine loss of a paragraph
#: boundary, not specific to this one caption. Superseded ORIGIN's own
#: identical-purpose `_run_re` (an inline closure inside `parse()`, which
#: had exactly this bug uncaught since RI 2024 H2 P3 never happened to hit
#: the single-figure-then-own-caption-paragraph shape) -- see `parse()`,
#: which now calls this module-level function instead of its own closure.
_FIG_RUN_RE = re.compile(r"%s(?:\s*%s)*"
                         % (re.escape(FIG_SENTINEL), re.escape(FIG_SENTINEL)))


def merge_owner_figures(raw_figs: list, html: str,
                        anomalies: list | None = None) -> tuple:
    """(merged_figures, collapsed_html) -- one Figure per PRINTED picture.

    A picture composed of several native-shape layers, or a chart with shapes
    drawn over it, is several `Figure` records in `raw_figs` (one per drawing
    Word stores) but ONE placeholder's worth of adjacency in the rendered
    text. What distinguishes "one picture" from "several pictures in the same
    owner" is exactly that adjacency -- two placeholders sitting back to back
    with nothing but whitespace between them in the text a reader sees -- so
    the merge and the placeholder-collapse are tied together by construction
    (one regex) rather than two heuristics that can independently disagree
    (as an early version of this, keyed on "same cell" instead, did).

    Shared by both document shapes (`parts.py`'s table grid and
    `parts_flow.py`'s paragraph flow) -- the notion of "owner" differs (a
    table cell vs a paragraph span) but adjacency-in-rendered-text does not.
    """
    runs = [m.group(0).count(FIG_SENTINEL) for m in _FIG_RUN_RE.finditer(html)]
    if sum(runs) != len(raw_figs):
        if anomalies is not None:
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
    if len(merged) != len(raw_figs) and anomalies is not None:
        anomalies.append("%d native drawings merged into %d pictures"
                         % (len(raw_figs), len(merged)))
    return merged, _FIG_RUN_RE.sub(FIG_SENTINEL, html)


#: A mark badge that ended up ALONE on content_html's last joined line, with
#: nothing of its own to sit beside -- see `_write_mark`. Exported for
#: `parts_flow.py`, which reuses it at its own call sites (it processes
#: paragraph by paragraph, not row by row, so it does its own cross-
#: paragraph merge check against this same pattern).
_BADGE_ALONE_RE = re.compile(r'\s*<span class="mk">\[\d+\]</span>\s*')


def _write_mark(content_html: str) -> tuple[str, int | None]:
    """Wrap a trailing inline "[n]" in `<span class="mk">`, IN PLACE, at the
    exact point the source paper prints it -- and pull an orphaned badge back
    onto the content it belongs to.

    Exported for `parts_flow.py` (the flow-shape structured-paper sibling,
    EJC 2024 H2 P2), which calls this per paragraph as it walks the document
    and does its own additional cross-paragraph merge on top using
    `_BADGE_ALONE_RE` directly. `parts.py`'s OWN `parse()`, below, does not
    call this -- it does the equivalent substitution inline, at the ROW
    level (RI 2024 H2 P3's shape), including the cross-ROW "mark printed as
    its own row" case (`mark_only`, below) that has no paragraph-level
    equivalent here. Both are validated against their own paper; this one
    stays a separate, simpler function rather than being forced to also
    cover the row-level case it was never asked to.

    Two Word-side accidents otherwise strand the badge on its own line, found
    by rendering a preview and looking at it, not by any gate: the sentence
    and its "[n]" can arrive as two separate paragraphs in the SAME cell, or
    a table cell and a trailing marks-only cell can join as
    "<table>...</table>\n[4]" (content_html joins cells with "\n"). Either
    way, a badge that is the WHOLE of the last joined line has nothing to sit
    beside once rendered, so it is glued onto the previous line with a single
    space instead of staying a separate line.

    Trailing close tags after the "[n]" (captured by INLINE_MARKS_HTML_RE's
    own group 2) are preserved, moved after the badge, in case the
    allocation sits inside an inline element -- same reasoning as `parse()`'s
    own inline substitution below.

    Returns (html_with_badge, marks) -- marks is None if this row printed no
    inline allocation at all (most rows).
    """
    m = INLINE_MARKS_HTML_RE.search(content_html)
    if not m:
        return content_html, None
    marks = int(m.group(1))
    trailing = m.group(2) or ""
    html = (content_html[:m.start()]
            + '<span class="mk">[%d]</span>' % marks + trailing
            + content_html[m.end():])
    lines = html.split("\n")
    if len(lines) > 1 and _BADGE_ALONE_RE.fullmatch(lines[-1]):
        lines[-2] = lines[-2] + " " + lines[-1].strip()
        lines.pop()
        html = "\n".join(lines)
    return html, marks


def parse(document_xml, rels_xml, numbering_xml=None, scope=None):
    """Return (questions, figures, anomalies) for a structured question-paper
    docx (P2/P3 shape). `figures` is in document order -- handoff SS7:
    ordinal MUST follow DOM order, the frontend zips positionally.

    `numbering_xml` (word/numbering.xml) is optional so existing callers
    keep working unchanged; without it, numPr paragraphs (bullet/numbered
    lists) fall back to one plain <p> per line, as before -- the list
    STRUCTURE is lost but no text is. Pass it to get grouped <ul> lists.

    `scope` (school, level, paper, year) is accepted for interface symmetry
    with `parts_flow.parse()`, which uses it to recognise a deliberately
    combined part (`corrections.combined_figures_reason`). No table-shape
    paper has needed that override yet, so it is accepted and otherwise
    unused here -- add the same lookup to this module's own figure-merge
    step (below) if one ever does.
    """
    global _BULLET_NUMIDS
    _BULLET_NUMIDS = load_bullet_numids(numbering_xml)

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
                #
                # Marks are read BEFORE the content is emitted, because the
                # printed "[n]" is replaced by its styled badge IN PLACE, on
                # the way past -- not stripped for a badge to be re-appended
                # later at the end of the whole part (see INLINE_MARKS_HTML_RE's
                # own comment for why that was wrong: the paper can print
                # "[n]" mid-part, with more paragraphs/a table genuinely
                # belonging to the NEXT part following it in the same cell).
                # We also keep the numeric value in Part.marks, for the
                # marks-total check and for anything else that needs the
                # number without re-parsing the badge back out of the html --
                # but the badge itself is written exactly once, exactly
                # where the paper prints it. One value, one rendering.
                mm = INLINE_MARKS_RE.search(content_text)
                # Whatever precedes the match (INLINE_MARKS_RE is anchored to
                # the end of content_text) is empty once stripped -- i.e. the
                # WHOLE chunk is the mark allocation and nothing else. Compare
                # against the prefix, not against mm.group(0) itself: the
                # regex's own trailing \s* means group(0) can carry trailing
                # whitespace content_text.strip() has already dropped, which
                # made a naive equality check here false even for a genuine
                # mark-only chunk.
                mark_only = bool(mm) and not content_text[:mm.start()].strip()
                if mm and cur_part is not None:
                    cur_part.marks = int(mm.group(1))
                    # Anchored to the END of the content, never global: these
                    # papers use square brackets mid-text for real content --
                    # 1(a)(iii) carries "[1 MPa = 10^6 Pa]" immediately before
                    # its "[1]" allocation -- and a global strip would eat
                    # data. Trailing close-tags are preserved (moved after the
                    # badge) in case the allocation sits inside an inline
                    # element.
                    content_html = INLINE_MARKS_HTML_RE.sub(
                        r'<span class="mk">[\1]</span>\2', content_html).rstrip()
                    # The row's OWN cell can carry the sentence and the mark
                    # as two separate paragraphs (RI 2024 H2 P3 1(e)(i): one
                    # paragraph "...applied.", a second paragraph holding
                    # only "[1]") -- content_html for the whole row already
                    # has BOTH, joined with "\n" from the cell's own multi-
                    # paragraph text. If that leaves the badge alone on the
                    # LAST line, merge it onto the previous line with a
                    # space instead of a newline: left as two lines,
                    # _render_owner/_para would wrap the badge in its own
                    # <p>, and an otherwise-empty paragraph holding only a
                    # float collapses to zero height, so the badge visually
                    # drifts down to wherever the NEXT part's content starts
                    # (found by rendering and looking, not by any gate).
                    lines = content_html.split("\n")
                    if len(lines) > 1 and re.fullmatch(
                            r'\s*<span class="mk">\[\d+\]</span>\s*',
                            lines[-1]):
                        content_html = "\n".join(lines[:-2]
                            + [lines[-2].rstrip() + " " + lines[-1].strip()]) \
                            if len(lines) > 2 else \
                            lines[0].rstrip() + " " + lines[-1].strip()
                elif mm:
                    # Never silent: an allocation we can see but cannot attach
                    # is a mark that will go missing from the marks total.
                    anomalies.append(
                        "Q%s: inline marks %s with no part open -- not "
                        "captured, and left in the content"
                        % (cur_q.qnum if cur_q else "?", mm.group(0)))
                if mark_only and cur_part is not None and cur_part.html:
                    # The paper sometimes prints "[n]" as its OWN row/cell,
                    # separate from the sentence it belongs to (RI 2024 H2 P3
                    # 1(e)(i): "...applied." is one chunk, "[1]" arrives as
                    # the NEXT one). The normal _emit() path joins chunks with
                    # "\n", which _render_owner/_paragraphs turns into a
                    # fresh <p> -- so the badge would land alone in its own
                    # paragraph, containing nothing but a float. An empty
                    # paragraph holding only a float has no normal-flow
                    # content to give it height, so it collapses to zero and
                    # the badge visually drifts down to wherever the NEXT
                    # part's content happens to start (found by rendering and
                    # looking -- 1(e)(i)'s "[1]" appeared beside 1(e)(ii)'s
                    # "[2]" instead of by its own sentence). Appended directly
                    # onto the end of the part's existing html with a plain
                    # space instead, it stays inline content of the LAST
                    # paragraph already there, so float:right resolves against
                    # a paragraph that has real text height.
                    cur_part.html = (cur_part.html.rstrip()
                                     + " " + content_html.strip())
                elif content_html.strip() or FIG_SENTINEL in content_html:
                    _emit(content_html)

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
    by_owner_raw: dict[tuple, list[Figure]] = {}
    for f in figures:
        by_owner_raw.setdefault((f.qnum, f.part), []).append(f)

    ordered_figures: list[Figure] = []
    for q in questions:
        raw = by_owner_raw.get((q.qnum, None), [])
        q.intro_figures, q.intro_html = merge_owner_figures(
            raw, q.intro_html, anomalies)
        q.n_intro_placeholders = q.intro_html.count(FIG_SENTINEL)
        ordered_figures.extend(q.intro_figures)
        for p in q.parts:
            raw = by_owner_raw.get((p.qnum, p.label), [])
            p.figures, p.html = merge_owner_figures(raw, p.html, anomalies)
            p.n_placeholders = p.html.count(FIG_SENTINEL)
            ordered_figures.extend(p.figures)
    figures = ordered_figures
    for n, f in enumerate(figures):
        f.index = n

    # Captions onto their own centred lines. Deliberately AFTER figure
    # merging: `merge_owner_figures` decides what is one picture by looking at the
    # whitespace between placeholders in this very html, so reformatting it
    # first would change that judgement. Safe to run after the placeholder
    # counts are taken because it only breaks a line -- it never adds,
    # removes or reorders a sentinel -- so those counts still describe this
    # html, and the consistency check below still means what it says.
    for q in questions:
        q.intro_html = _split_captions(q.intro_html)
        for p in q.parts:
            p.html = _split_captions(p.html)

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
