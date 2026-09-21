"""Walk a QUESTION paper docx into per-question stems, options and figures.

SHAPE OF THIS DOCUMENT FAMILY -- verified against RI 2024 H2 P1 (MCQ), do not
assume it matches the ANSWERS document, which `answers.py` handles:

  One top-level table per question. Row 0 is [qnum | stem], the stem cell
  gridSpan'd across the rest of the row. Blank spacer rows follow. Option rows
  carry a bare letter cell (A-E) followed by that option's content cells; a row
  may hold SEVERAL option pairs side by side (Q1 has A and B on one row, Q2 has
  all four).

  Three option layouts occur and all three must survive:
    - prose      [A][text]                     -- Q3
    - inline     [A][text][B][text]            -- Q1, Q2
    - row-table  header row, then [A][v1][v2]  -- Q9, Q10, Q19, Q27
  A "row-table" option is a tuple, not a string, and flattening it to one cell
  loses the column headings that make the question readable.

  A table whose row 0 does NOT begin with a bare integer is a CONTINUATION of
  the previous question. RI P1 Q30 runs onto a second page that way, carrying
  its four option structures with it. Treating it as a new question silently
  drops those options.

Handoff SS8: MCQ and structured share question_number, so anything joining on
number alone must pin q.type. Nothing here writes to the DB, but the migration
generator downstream relies on this module reporting type='mcq'.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

from .oxml import NS, Wq, paragraph_html
from .answers import _classify_drawing, _load_rels, Figure

WPD = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
OFFICE = "urn:schemas-microsoft-com:office:office"

#: Row 0 cell 0 of a question table: a bare question number, nothing else.
QNUM_RE = re.compile(r"^\s*(\d{1,2})\s*$")
#: An option marker cell: exactly one capital letter A-E.
OPT_RE = re.compile(r"^\s*([A-E])\s*$")

FIG_SENTINEL = "\x00FIG\x00"


@dataclass
class Question:
    qnum: int
    stem_html: str = ""
    #: option letter -> list of cell HTML strings. One entry for prose options,
    #: several for a row-table option.
    options: dict = field(default_factory=dict)
    #: column headings for a row-table option layout, [] otherwise.
    opt_headers: list = field(default_factory=list)
    #: rows of the question that are neither stem nor option -- e.g. Q25's
    #: structure matrix. Kept so nothing is silently discarded.
    extra_html: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    n_stem_figs: int = 0
    n_opt_figs: int = 0
    #: one entry per option figure, in document order, naming its option letter
    opt_fig_letters: list = field(default_factory=list)
    #: every \x00FIG\x00 seen while parsing, INCLUDING those on rows consumed as
    #: option-figure rows. Compared against len(figures) as a gate.
    n_placeholders: int = 0

    @property
    def layout(self) -> str:
        if not self.options:
            return "none"
        if self.opt_headers:
            return "row-table"
        if any(len(v) > 1 for v in self.options.values()):
            return "row-table"
        return "prose"


def _cell_text(tc) -> str:
    return "".join(tc.itertext(Wq + "t")).strip()


def _table_html(tbl) -> str:
    """Render a NESTED table (a data table inside a question cell).

    `answers.py` deliberately skips nested-table paragraphs, because in the
    mark-scheme family they are layout. In a QUESTION paper they are content:
    RI 2024 H2 P1 Q12 carries its three thermochemical equations and their
    enthalpy values in a nested 4-row table, and the question cannot be
    answered without them. Skipping it drops the data silently -- the question
    still renders, just unanswerable.
    """
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
    """Cell contents in document order, descending into nested tables."""
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


def _gridspan(tc) -> int:
    g = tc.find(Wq + "tcPr/" + Wq + "gridSpan")
    return int(g.get(Wq + "val")) if g is not None else 1


def _split_options(cells):
    """Split a row's cells into [(letter, [content cells]), ...].

    Returns [] when the row carries no option marker at all.
    """
    marks = [i for i, c in enumerate(cells) if OPT_RE.match(_cell_text(c))]
    if not marks:
        return []
    out = []
    for n, i in enumerate(marks):
        end = marks[n + 1] if n + 1 < len(marks) else len(cells)
        letter = OPT_RE.match(_cell_text(cells[i])).group(1)
        out.append((letter, cells[i + 1:end]))
    return out


def parse(document_xml, rels_xml):
    """Return (questions, figures, anomalies) for a question-paper docx.

    `figures` is in document order. Handoff SS7: ordinal MUST follow DOM order of
    the placeholders, because the frontend zips them positionally.
    """
    rels = _load_rels(rels_xml)
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)

    questions: list[Question] = []
    anomalies: list[str] = []
    current: Question | None = None

    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if not rows:
            continue
        c0 = rows[0].findall("w:tc", NS)
        if not c0:
            continue
        m = QNUM_RE.match(_cell_text(c0[0]))

        if m:
            current = Question(qnum=int(m.group(1)))
            questions.append(current)
            # Row 0 minus the number cell is the stem.
            stem_cells = c0[1:]
            body_rows = rows[1:]
        else:
            if current is None:
                txt = _cell_text(c0[0])
                if txt:
                    anomalies.append("content before first question: %r" % txt[:60])
                continue
            # Continuation table (RI P1 Q30's second page).
            stem_cells = []
            body_rows = rows
            anomalies.append("continuation table attached to Q%d" % current.qnum)

        for tc in stem_cells:
            h = _cell_html(tc)
            current.n_placeholders += h.count(FIG_SENTINEL)
            if h.strip():
                current.stem_html = (current.stem_html + "\n" + h).strip() \
                    if current.stem_html else h

        # Two passes. The first finds the option rows, because how many content
        # cells an option has is what tells a COLUMN HEADING apart from ordinary
        # content -- and that is only knowable once the options are known.
        #
        # Rows carry a VARIABLE number of leading empty indent cells (Q7 has
        # two, Q9's option rows have one), so leading blanks are stripped
        # entirely rather than by a fixed count.
        stripped = []
        for tr in body_rows:
            cells = tr.findall("w:tc", NS)
            while len(cells) > 1 and not _cell_text(cells[0]) \
                    and FIG_SENTINEL not in _cell_html(cells[0]):
                cells = cells[1:]
            stripped.append(cells)

        opt_rows = [(i, _split_options(c)) for i, c in enumerate(stripped)]
        opt_rows = [(i, o) for i, o in opt_rows if o]
        n_opt_cols = max((len(c) for _, o in opt_rows for _, c in o), default=0)
        first_opt = opt_rows[0][0] if opt_rows else len(stripped)

        pending_letters: list = []
        caption_letters: list = []
        for i, cells in enumerate(stripped):
            if not cells:
                continue
            htmls = [_cell_html(c) for c in cells]
            if not any(h.strip() or FIG_SENTINEL in h for h in htmls):
                continue
            current.n_placeholders += sum(h.count(FIG_SENTINEL) for h in htmls)

            opts = _split_options(cells)
            if opts:
                for letter, content in opts:
                    vals = [_cell_html(c) for c in content]
                    # Q24/Q26/Q29 put the option LETTERS on one row and their
                    # structures on the row beneath, so an option legitimately
                    # has no content cells of its own. Recorded as empty here
                    # and filled from the figure pass.
                    current.options.setdefault(letter, [])
                    if any(v.strip() for v in vals):
                        current.options[letter] = vals
                    n = sum(v.count(FIG_SENTINEL) for v in vals)
                    current.opt_fig_letters.extend([letter] * n)
                pending_letters = [l for l, _ in opts]
                continue

            # A figure-only row beneath a letters row (Q8, Q26, Q29): align
            # figure-bearing cells to the letters above them, by column.
            fig_cells = [h for h in htmls if FIG_SENTINEL in h]
            if fig_cells and pending_letters:
                if len(fig_cells) == len(pending_letters):
                    for letter, h in zip(pending_letters, fig_cells):
                        current.opt_fig_letters.extend(
                            [letter] * h.count(FIG_SENTINEL))
                    caption_letters = list(pending_letters)
                    pending_letters = []
                    continue
                anomalies.append(
                    "Q%d: %d figure cells under %d option letters -- cannot "
                    "align, left unattributed"
                    % (current.qnum, len(fig_cells), len(pending_letters)))

            # A CAPTION ROW: short text directly beneath a figure-only row,
            # one cell per option. Q8's four graphs are captioned "constant V"
            # / "constant T", and those captions are the whole difference
            # between the options -- without them the four options read
            # "[structure A]".."[structure D]", which is unanswerable in the
            # bank and unsearchable. Left in extra_html they printed as a
            # detached 2x2 grid above the graphs, attached to nothing.
            if (caption_letters and not fig_cells
                    and len(cells) == len(caption_letters)
                    and all(len(h) < 120 for h in htmls)
                    and any(h.strip() for h in htmls)):
                for letter, h in zip(caption_letters, htmls):
                    if h.strip():
                        current.options[letter] = [h]
                caption_letters = []
                continue
            caption_letters = []

            # A COLUMN HEADING is the row directly above the first option row
            # with exactly as many cells as an option has content cells
            # (Q9: 3 headings over 3 values). Q7/Q15/Q23/Q28 open with numbered
            # statement rows -- 2 cells against 1-cell options -- so they fail
            # this test and stay in the stem, which is where they belong.
            if (i == first_opt - 1 and n_opt_cols > 1
                    and len(cells) == n_opt_cols
                    and all(len(h) < 120 for h in htmls)):
                current.opt_headers = htmls
                continue

            current.extra_html.append(htmls)

    # --- figures, in true document order, attributed to question + region ---
    figures: list[Figure] = []
    order = 0
    cur_q = None
    region = "stem"
    for el in body.iter():
        ln = etree.QName(el).localname
        if ln == "tr":
            cells = el.findall("w:tc", NS)
            if cells:
                m = QNUM_RE.match(_cell_text(cells[0]))
                if m:
                    cur_q = int(m.group(1))
                    region = "stem"
                elif _split_options(cells):
                    region = "option"
        elif ln in ("drawing", "object", "pict"):
            # Skip the mc:Fallback half of an AlternateContent pair: it is a VML
            # restatement of the SAME figure, and counting it would offset every
            # later ordinal and silently rotate the figures.
            if any(etree.QName(a).localname == "Fallback"
                   for a in el.iterancestors()):
                continue
            # Every question figure in this family lives inside a table row.
            # Body-level drawings are page furniture -- the school crest on the
            # cover, and a trailing decorative shape after the last question.
            # The trailing one is the dangerous case: it sits AFTER Q30's table,
            # so it inherits cur_q=30 and would add a phantom sixth figure to a
            # five-figure question, rotating that question's assets.
            if not any(etree.QName(a).localname == "tr"
                       for a in el.iterancestors()):
                anomalies.append("body-level figure ignored (page furniture)")
                continue
            if cur_q is None:
                anomalies.append("figure before Q1 ignored (cover page)")
                continue
            fig = _classify_drawing(el, rels)
            # An embedded OLE object names its editor. RI 2024 H2 P1 carries 34
            # ChemDraw.Document.6.0 structures and 3 Equation.DSMT4 objects, and
            # the two want opposite treatment: a structure is a picture, an
            # equation is inline maths the bank already has markup for. Reading
            # the ProgID settles it on evidence rather than on a layout guess
            # about whether the figure shares a line with text -- which
            # misfiled Q19's cell diagram.
            ole = el.find(".//{%s}OLEObject" % OFFICE)
            if ole is not None and (ole.get("ProgID") or "").startswith("Equation"):
                fig.kind = "equation"
            fig.index = order
            fig.qnum = cur_q
            fig.part = region
            fig.anchored = el.find(".//{%s}anchor" % WPD) is not None
            fig.cell = next((id(a) for a in el.iterancestors()
                             if etree.QName(a).localname == "tc"), None)
            figures.append(fig)
            order += 1

    # A native Word SHAPE has no media file; a diagram built from several of
    # them is still ONE picture (handoff SS7: "a chart plus shapes drawn over it
    # is one picture, not four"). Q14's rate curve is 4 shapes, Q19's cell
    # diagram is 2, Q8's graphs A and C are 2 apiece. Counting each shape as a
    # figure asks the cropper for more pictures than the page contains, and
    # merge_to cannot split one cluster into four.
    merged: list = []
    for f in figures:
        if (merged and f.kind == "shape" and merged[-1].kind == "shape"
                and f.cell is not None and f.cell == merged[-1].cell):
            merged[-1].n_parts += 1
            continue
        f.n_parts = 1
        merged.append(f)
    if len(merged) != len(figures):
        anomalies.append("%d native shapes merged into %d pictures by cell"
                         % (len(figures), len(merged)))
    figures = merged
    for n, f in enumerate(figures):
        f.index = n

    # Collapse the PLACEHOLDERS to match. A merged picture must leave exactly
    # one \x00FIG\x00 behind, or the placeholder/figure gate below fires and
    # the ordinals would rotate. Merged shapes are always adjacent inside one
    # cell, so a run of adjacent sentinels is the run that merged -- and the
    # gate is what proves that held, question by question.
    run_re = re.compile(r"(?:%s\s*){2,}" % re.escape(FIG_SENTINEL))

    def _collapse(h):
        return run_re.sub(FIG_SENTINEL, h)

    for q in questions:
        before = q.n_placeholders
        q.stem_html = _collapse(q.stem_html)
        q.extra_html = [[_collapse(c) for c in row] for row in q.extra_html]
        q.options = {k: [_collapse(c) for c in v] for k, v in q.options.items()}
        after = (q.stem_html.count(FIG_SENTINEL)
                 + sum(c.count(FIG_SENTINEL) for r in q.extra_html for c in r)
                 + sum(c.count(FIG_SENTINEL) for v in q.options.values() for c in v))
        q.n_placeholders = before - (before - after) if after else before
        q.n_placeholders = after + max(0, before - after) - (before - after)

    by_q = {}
    for f in figures:
        by_q.setdefault(f.qnum, []).append(f)
    for q in questions:
        q.figures = by_q.get(q.qnum, [])
        q.n_stem_figs = sum(1 for f in q.figures if f.part == "stem")
        q.n_opt_figs = sum(1 for f in q.figures if f.part == "option")

    # --- placeholder/figure consistency -------------------------------------
    # Handoff SS7's costliest defect class: if the number of \x00FIG\x00
    # placeholders and the number of figures disagree, every later ordinal
    # shifts and the figures silently rotate. Neither count alone can reveal
    # that, so they are compared here and a mismatch is fatal to the run.
    for q in questions:
        # Option figures reach the html in two different ways: Q24 and Q30 put
        # them in the option cells themselves, while Q8/Q26/Q29 put the letters
        # on one row and the structures on the next, which the parser consumes.
        # Only the consumed ones need adding back, or they are counted twice.
        opt_in_html = sum(c.count(FIG_SENTINEL)
                          for v in q.options.values() for c in v)
        n_opt = len([f for f in q.figures if f.part.startswith("option")])
        placeholders = (q.stem_html.count(FIG_SENTINEL)
                        + sum(c.count(FIG_SENTINEL)
                              for r in q.extra_html for c in r)
                        + opt_in_html
                        + max(0, n_opt - opt_in_html))
        if placeholders != len(q.figures):
            anomalies.append(
                "Q%d: %d placeholders but %d figures -- ordinals would rotate"
                % (q.qnum, placeholders, len(q.figures)))
        # Attach the option letter to each option figure, in document order.
        opt_figs = [f for f in q.figures if f.part == "option"]
        # opt_fig_letters was built from the UNMERGED sentinels, so a merged
        # picture consumes n_parts of them (Q8's graphs A and C are two shapes
        # each).
        if sum(f.n_parts for f in opt_figs) == len(q.opt_fig_letters):
            k = 0
            for f in opt_figs:
                letters = set(q.opt_fig_letters[k:k + f.n_parts])
                k += f.n_parts
                if len(letters) != 1:
                    anomalies.append("Q%d: merged picture spans options %s"
                                     % (q.qnum, sorted(letters)))
                    continue
                f.part = "option:" + letters.pop()
        elif opt_figs:
            anomalies.append(
                "Q%d: %d option figures but %d attributed to letters"
                % (q.qnum, len(opt_figs), len(q.opt_fig_letters)))

    seen = [q.qnum for q in questions]
    if seen != sorted(seen) or len(set(seen)) != len(seen):
        anomalies.append("question numbers out of order or duplicated: %s" % seen)

    # THIS MODULE IS FOR MCQ PAPERS ONLY.
    #
    # A structured paper (P2/P3) is the 4-column SEAB grid of handoff SS7 --
    # qnum | letter | roman | content -- with part labels "(a)", "(b)(ii)"
    # where an MCQ has option letters A-E. Run through this parser it does not
    # crash: it finds the question numbers, finds no options, and quietly files
    # every part into `extra_html`, producing rows that render as a wall of
    # untagged prose with no parts, no marks and no part labels. That is a
    # silent wrong answer, which is the failure mode this codebase spends most
    # of its effort avoiding, so it is made loud here instead.
    #
    # Supporting structured papers needs a sibling parser and renderer for the
    # part hierarchy; everything below this layer -- figures, symbols, gates --
    # already transfers.
    no_opts = [q.qnum for q in questions if len(q.options) < 2]
    if len(no_opts) > len(questions) // 4:
        raise ValueError(
            "%d of %d questions have fewer than two options. This looks like a "
            "STRUCTURED paper; ingest.questions handles MCQ only (see the note "
            "in the source). Questions without options: %s"
            % (len(no_opts), len(questions), no_opts[:10]))
    if no_opts:
        anomalies.append("questions with fewer than 2 options: %s" % no_opts)

    return questions, figures, anomalies
