"""Walk a STRUCTURED QUESTION paper docx into questions -> parts -> sub-parts,
the PARAGRAPH-FLOW shape (plain paragraphs, not the SEAB 4-column table grid
`parts.py` was built for and is verified against).

SHAPE OF THIS DOCUMENT FAMILY -- verified against EJC 2024 H2 P2 by direct XML
inspection of all four questions. Mirrors `questions_flow.py`'s relationship
to `questions.py` (EJC's own MCQ paper needed the same kind of sibling
adapter, for the same reason: no per-question table at all).

  No table for the QUESTION GRID. A question number, a part letter, and a
  roman-numeral sub-part are each the paragraph's own LEADING TEXT, glued
  directly onto the next character with no space ("1This question...",
  "(a)Sodium chlorate...", "(i)By writing..."), the same convention
  `parts.py` documents for its table-cell text -- just written as ordinary
  paragraph text instead of a table cell's. A handful of standalone
  `<w:tbl>` elements DO still occur, body-level siblings of these paragraphs
  (a Hess-cycle enthalpy table, a structure/Ksp data table) -- these are
  CONTENT, handed to whichever part is open when they're reached, rendered
  the same way `parts.py` renders a nested content table (reusing
  `parts._table_html`/`_cell_html` directly, since that rendering is
  agnostic to whether the table sits inside a grid cell or beside a flow
  paragraph).

QUESTION / PART / SUB-PART BOUNDARIES -- found the same way for all three,
by direct run inspection, not by guessing a text pattern and hoping:

  The label is its OWN run (or two: a text run holding exactly "(a)" or "(i)"
  or a bare digit, sometimes followed by an empty run of the same styling),
  set BOLD, with ordinary (non-bold) prose starting in the very next
  non-empty run. This is a STRUCTURAL fact, not a text-pattern guess, and it
  is what makes it reliable where a text-only pattern is not: EJC 2024 H2
  P2's Q2 opens "21,2-dimethylcyclohexene..." -- a question number glued
  directly onto a compound name that ITSELF starts with a digit ("1,2-") --
  which defeats any rule requiring the character after the number to be a
  letter (`questions_flow.QSTART`'s own rule, built for EJC's MCQ paper,
  would reject this). It does not defeat the bold-run test: verified across
  the whole document, matching a paragraph's first run being bold AND its
  own full text being EXACTLY a bare digit finds all 4 questions, in order,
  with zero false positives -- in particular it correctly rejects "25.0 cm3"
  (an unrelated volume inside Q1, not bold) and a typed "2ClO2- -> ClO3- +
  Cl-" list line inside a disproportionation-equation list (styled with the
  ListParagraph paragraph style but not a bold run, and typed rather than a
  genuine w:numPr paragraph -- see LISTS below). The identical test,
  restricted to "(a)".."(z)" or a roman numeral instead of a bare digit,
  finds every part/sub-part label with the same zero-error result (24 letter
  + 15 roman matches across the paper, none missed, none spurious).

  LETTER AND ROMAN CAN OPEN ON THE SAME PARAGRAPH, unlike EJC's own MCQ
  paper: Q1(c)'s "(c) (i) G, an isomer of 1,2-dimethylcyclohexene..." carries
  BOTH labels as two separate leading bold runs before the real content
  starts (a THIRD bold run, "G", follows immediately -- a bold compound
  letter, not a label, and correctly ends the leading-label scan because it
  fails the letter/roman/digit shape test). Handled the same way `parts.py`
  handles a table row that sets both in one cell: no separate bare-letter
  Part is created, the roman sub-part is opened directly.

MARKS -- the opposite convention from RI's P2/P3. Every one of this paper's
48 mark allocations is its OWN paragraph, "[n]" alone, never inline at the
end of the preceding sentence (confirmed: zero inline occurrences, 48
paragraph-alone occurrences). Left alone, a lone "[n]" paragraph renders as
its own floated line with nothing to sit beside -- precisely the defect RI's
P3 build found and fixed (`claude/p3-live-formatting-fixes.md`, "Mark
position fix, v2"). Reusing `parts._write_mark` on each paragraph as it is
appended -- rather than re-solving this here -- covers the wrapping; gluing
a now-orphaned badge back onto the PREVIOUS paragraph (a separate `_append`
call, unlike RI where it is one call's own internal last line) is this
module's own job, done in `_append` by testing the freshly-wrapped piece
against `parts._BADGE_ALONE_RE` before deciding whether to join with "\n" or
with a bare space.

LISTS -- reuses `oxml.paragraph_numid`/`load_bullet_numids` exactly as
`parts.py`'s table-cell list-grouping does, just grouping consecutive numPr
PARAGRAPHS instead of consecutive numPr paragraphs within one cell. This
paper's typed "1./2./3." disproportionation-equation lines (ListParagraph
style but no real w:numPr) are left as plain paragraphs -- the same reasoned
choice `questions_flow.py` documents for EJC's MCQ paper's equivalent typed
lines: a typed digit is already indistinguishable from ordinary prose and
needs nothing extra to read correctly.

A SECOND, decimal-format numId gets the same "group consecutive numPr
paragraphs" treatment but into an `<ol>` instead of a `<ul>`: Q4's Procedure
A and B (numId 8/9) are each ten steps with Word's own "1./2./3." auto-
numbering and NO typed digit anywhere -- confirmed by direct text
inspection of all twenty paragraphs -- so without this they lose their
numbering entirely, unlike the typed disproportionation lines above, which
already carry their own digit as ordinary text and need nothing extra
(user, 2026-09-26: "Procedures A and B to be given with numbered steps
(same as the source QP)"). Reuses the existing `ol.stmts` CSS, the same
class `questions_flow._wrap_stmt_lists` already relies on to render a
genuine numPr list correctly.

FIGURES -- reuses `questions_flow.py`'s own figure walk
(`_iter_top_figures`/`_own_ole`, the same de-duplication for
AlternateContent/nested-drawing legacy shapes) and `parts.merge_owner_figures`
for the "several drawings, one printed picture" collapse (see that
function's own docstring -- the adjacency test is shape-agnostic, table cell
or paragraph span).

NOT YET DONE HERE (deliberately -- this is "ingest questions", not
"diagrams"): figures are classified and placeholder-collapsed but the actual
crop/asset step (`parts_figures.py`) is unmodified and untested against this
shape; it locates artwork by PRINTED PART LABEL position in the PDF margin,
which does not depend on the docx's own container shape, but has only been
verified against RI's table-shape paper. Treat a first run against this
paper's figures as a fresh check, not an assumed pass.
"""
from __future__ import annotations

import re

from lxml import etree

from .oxml import (NS, Wq, paragraph_html, paragraph_numid,
                    load_bullet_numids, load_numid_formats)
from .answers import _classify_drawing, _load_rels, Figure
from .questions_flow import _iter_top_figures, _own_ole
from . import parts as _parts_mod
from . import corrections
from .parts import (Question, Part, FIG_SENTINEL, QNUM_RE, LETTER_RE,
                    ROMAN_RE, TOTAL_MARKS_RE, _boilerplate, _DOTTED_RE,
                    _write_mark, _BADGE_ALONE_RE, merge_owner_figures,
                    _ROMAN_SEQ)


def _has_numpr(p) -> bool:
    return p.find(".//" + Wq + "numPr") is not None


def _run_bare_text(r) -> str:
    return "".join(t.text or "" for t in r.findall(Wq + "t")).strip()


def _run_is_bold(r) -> bool:
    rpr = r.find(Wq + "rPr")
    return rpr is not None and rpr.find(Wq + "b") is not None


def _para_runs(p) -> list:
    return [c for c in p if etree.QName(c).localname == "r"]


#: "(i)", "(v)", "(x)" are valid as BOTH a bare part letter and a roman
#: sub-part numeral -- `parts.py`'s table-shape parser gets this for free
#: from grid position (SS7 point 3); the flow shape has no such position, so
#: it is resolved by context instead (see `_leading_labels`'s `letter_open`).
_AMBIGUOUS_ROMAN_LETTERS = {"i", "v", "x"}


def _leading_labels(runs: list, letter_open: bool = False,
                    roman_idx: int = 0) -> list:
    """[(kind, value, [run_indices])] for a paragraph's LEADING run of bold,
    exactly-matching qnum/letter/roman labels.

    A label is not always ONE run: Word sometimes splits "(b)" into three
    single-character runs, "(", "b", ")" (confirmed directly -- Q3(b)'s own
    label is stored exactly this way, while Q3's own "(c) (i)" a few parts
    later is each a single whole run, "(c) " then "(i) " -- both shapes occur
    in this one document). Handled by accumulating consecutive bold runs'
    text and testing the ACCUMULATED string after every run, closing the
    label the moment it fully matches -- this is safe (does not stop early
    on some other valid-looking prefix) because these three label shapes
    (bare digit, "(x)", roman-in-parens) cannot be a strict textual prefix of
    a longer valid instance of themselves ("(b)" fully matches only once the
    closing paren arrives; "(iii)" would still be an incomplete match, not a
    false positive, after only "(i" or "(ii").

    Stops at the first non-empty run that is not bold, or whose accumulated
    bold text never resolves to one of the three shapes before hitting a
    non-bold run -- that text is real content (see module docstring: a bold
    compound letter like "G" correctly ends the scan this way, rather than
    being mistaken for a label). Empty runs (Word often splits a label's own
    formatting run from a trailing empty one of identical style) are skipped
    without ending the scan or being added to the accumulated text.

    `letter_open` is whether a part letter is already open BEFORE this
    paragraph, and `roman_idx` is how many romans have already opened under
    it (0 if none yet, meaningless when no letter is open). Together they
    resolve "(i)"/"(v)"/"(x)" by EXPECTED SEQUENCE POSITION, not just
    context: a bare `letter_open` check alone is not enough, because it is
    true for the rest of the question once ANY letter has opened, and would
    misread a genuine NEXT LETTER reusing one of these three characters
    ("(i)" as EJC 2024 H2 P2 Q4's ninth part, after (h)'s own (h)(i)-(h)(iii)
    sub-parts) as a fourth roman under the PREVIOUS letter instead. Roman
    numerals never restart mid-letter, so "(i)" only continues the current
    letter when it is genuinely that letter's FIRST sub-part (`roman_idx ==
    0`); otherwise it can only be a new letter. Updated as the scan itself
    opens a letter or roman (the "(c)(i)..." case: after "(c)" is read,
    `roman_idx` resets to 0, so the immediately following "(i)" in the SAME
    paragraph correctly reads as that letter's first sub-part).
    """
    out = []
    buf = ""
    buf_runs: list = []
    for i, r in enumerate(runs):
        txt = _run_bare_text(r)
        if txt == "":
            continue
        if not _run_is_bold(r):
            break
        buf += txt
        buf_runs.append(i)
        m_q = QNUM_RE.match(buf)
        m_letter = LETTER_RE.match(buf)
        m_roman = ROMAN_RE.match(buf)
        if m_q:
            out.append(("qnum", int(m_q.group(1)), buf_runs))
        elif m_letter and m_roman:
            expected = _ROMAN_SEQ[roman_idx] if roman_idx < len(_ROMAN_SEQ) \
                else None
            if letter_open and m_roman.group(1) == expected:
                out.append(("roman", "(%s)" % m_roman.group(1), buf_runs))
                roman_idx += 1
            else:
                out.append(("letter", "(%s)" % m_letter.group(1), buf_runs))
                letter_open, roman_idx = True, 0
        elif m_letter:
            out.append(("letter", "(%s)" % m_letter.group(1), buf_runs))
            letter_open, roman_idx = True, 0
        elif m_roman:
            out.append(("roman", "(%s)" % m_roman.group(1), buf_runs))
            roman_idx += 1
        else:
            continue   # not a complete match yet -- keep accumulating
        buf, buf_runs = "", []
    return out


def _resolve_labels(runs: list, letter_open: bool, roman_idx: int,
                    numid: int | None, letter_numids: set) -> list:
    """`_leading_labels`, plus recovery for a label Word generated by its OWN
    list numbering instead of typing -- confirmed against EJC 2024 H2 P2's
    live document.xml/numbering.xml: Q2's very first part prints "(a) (i)
    Explain why...", but "(a)" never appears as run text anywhere in that
    paragraph -- only the hand-typed bold roman "(i)" does. The paragraph
    DOES carry `w:numPr` for numId 4, whose ilvl-0 definition is
    `numFmt="lowerLetter"`, `lvlText="(%1)"`, `start="1"` -- a REAL,
    live auto-numbered list, unlike every other paragraph in this document
    that also happens to carry numId 4 (documented elsewhere in this module
    as decorative hanging-indent only): checked directly, this is the ONLY
    numId-4 paragraph in the whole file whose own bold-run text does not
    already spell out a letter, which is exactly what makes the numbering
    load-bearing here and redundant everywhere else.

    Detection is NOT simply "no letter came back": run under the caller's
    real (letter closed) state, `_leading_labels`' OWN ambiguous-roman
    fallback already reads a bare leading "(i)"/"(v)"/"(x)" as a fresh
    letter when nothing else is open (that is the correct call when there
    genuinely is no letter to be had elsewhere) -- so the naive check would
    never fire, it would just see labels[0] == ("letter", "(i)", ...) and
    conclude a letter was already found. The real test is whether that
    letter came from an UNAMBIGUOUS typed token (any of "a".."z" except
    "i"/"v"/"x") -- if so, it is genuinely typed and stands. Only when the
    leading token is one of the ambiguous three, AND this numId is a real
    letter-format list, is the fallback's guess overridden: Word's own
    numbering always starts a fresh instance at "(a)" (`start="1"`), so that
    implied letter is prepended and the paragraph's own runs are
    re-resolved with it OPEN -- which is what lets the hand-typed "(i)"
    read as that letter's own first roman sub-part instead of being
    mistaken for the letter itself.
    """
    labels = _leading_labels(runs, letter_open=letter_open,
                             roman_idx=roman_idx)
    if letter_open or numid not in letter_numids:
        return labels
    if (labels and labels[0][0] == "letter"
            and labels[0][1][1:-1] not in _AMBIGUOUS_ROMAN_LETTERS):
        return labels          # a genuine, unambiguous typed letter
    if labels and labels[0][0] == "qnum":
        return labels          # never override a question-number label
    return [("letter", "(a)", [])] + _leading_labels(
        runs, letter_open=True, roman_idx=0)


def _blank_runs(runs: list, indices: list) -> None:
    """Erase the given runs' own text, in place -- their label has already
    been read into a Part/Question; leaving the literal "(a)" or "(i)" text
    in place would duplicate it in the rendered content, which stores the
    label separately (`Part.label`)."""
    for i in indices:
        for t in runs[i].findall(Wq + "t"):
            t.text = ""


def _force_combine(raw_figs: list, html: str) -> tuple:
    """Collapse ALL of one owner's figures into ONE representative Figure and
    ONE placeholder, regardless of adjacency -- unlike `merge_owner_figures`,
    which only fuses drawings with nothing between them in the rendered
    HTML. Used only where `corrections.combined_figures_reason` names this
    exact part -- a deliberate, recorded departure (see that function's own
    docstring), not a parsing default.

    All FIG_SENTINEL occurrences but the LAST are simply removed from the
    HTML: with `n` placeholders at positions p1 < p2 < ... < pn, that leaves
    whatever text sat BETWEEN them (a "Basic conditions:" label, say)
    sitting directly before the single surviving placeholder, in original
    reading order -- exactly the layout of one combined image captioned by
    both of the original labels, printed one after another above it.
    """
    if not raw_figs:
        return raw_figs, html
    rep = raw_figs[0]
    rep.n_parts = sum(getattr(f, "n_parts", 1) for f in raw_figs)
    n = html.count(FIG_SENTINEL)
    if n > 1:
        html = re.sub(re.escape(FIG_SENTINEL), "", html, count=n - 1)
    return [rep], html


def parse(document_xml, rels_xml, numbering_xml=None, scope=None):
    """Return (questions, figures, anomalies) for a paragraph-flow STRUCTURED
    question paper. Same contract as `parts.parse()` -- see that module's
    docstring for the return shape and handoff SS7's ordinal rule.

    `scope` is (school, level, paper, year), matching `corrections.py`'s own
    convention -- passed through to `corrections.combined_figures_reason` so
    a deliberately-combined part (see `_force_combine`) is recognised.
    Omitted, no part is ever force-combined (safe default, matches every
    call site that has not been updated to pass a scope).
    """
    bullet_numids = load_bullet_numids(numbering_xml) if numbering_xml else set()
    # `parts._table_html`/`_cell_html` (reused below for content tables) read
    # bullet membership from this module global -- keep it in sync for the
    # duration of this call.
    _parts_mod._BULLET_NUMIDS = bullet_numids
    # numIds whose ilvl-0 format actually renders a letter ("(a)", "(b)"...)
    # via Word's own numbering engine -- see `_resolve_labels`'s docstring
    # for why this matters (exactly one paragraph in EJC 2024 H2 P2 relies
    # on it for its only copy of that label).
    numid_formats = load_numid_formats(numbering_xml) if numbering_xml else {}
    letter_numids = {nid for nid, fmt in numid_formats.items()
                     if fmt in ("lowerLetter", "upperLetter")}
    # numIds whose ilvl-0 format is Word's own auto-numbered "1./2./3." --
    # a genuine ordered list with NO typed digit at all (unlike the
    # decimal-numid statement lists `questions_flow._wrap_stmt_lists`
    # handles, which type "1<tab>...", "2<tab>..." themselves and only need
    # folding into one <ol>). EJC 2024 H2 P2 Q4's Procedure A/B steps are
    # numId 8/9, both decimal, confirmed by direct XML inspection to have
    # NO leading digit run at all -- left unhandled, `bullet_numids` below
    # only groups BULLET-format numids, so these fell straight through to
    # plain-paragraph treatment and Word's own numbering was silently lost
    # (user, 2026-09-26: "Procedures A and B to be given with numbered
    # steps (same as the source QP)"). numId 1 is also decimal-format here
    # but is never actually used by any paragraph in this document (defined
    # in numbering.xml, referenced nowhere) -- harmless to include.
    decimal_numids = {nid for nid, fmt in numid_formats.items()
                      if fmt == "decimal"}

    rels = _load_rels(rels_xml)
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    kids = list(body)

    anomalies: list[str] = []

    # --- question boundaries: a paragraph whose first run is bold and is
    # EXACTLY a bare digit. Sequential-number matching (like
    # questions_flow.QSTART) is not needed here: the bold-run test alone was
    # verified to have zero false positives across this whole paper.
    starts = []
    for i, c in enumerate(kids):
        if etree.QName(c).localname != "p" or _has_numpr(c):
            continue
        labels = _leading_labels(_para_runs(c))
        if labels and labels[0][0] == "qnum":
            starts.append((i, labels[0][1]))

    questions: list[Question] = []
    all_figures: list[Figure] = []
    fig_order = 0

    for k, (start_idx, qnum) in enumerate(starts):
        end_idx = starts[k + 1][0] if k + 1 < len(starts) else len(kids)
        span = kids[start_idx:end_idx]
        q = Question(qnum=qnum)
        questions.append(q)

        cur_letter: str | None = None
        roman_count = 0    # romans opened under cur_letter -- disambiguates
                           # "(i)"/"(v)"/"(x)" as letter vs roman, see
                           # `_leading_labels`
        cur_part: Part | None = None
        bullet_buf: list[str] = []      # pending <li> items, this owner only
        decimal_buf: list[str] = []     # pending <li> items for a Word-numbered
                                         # "1./2./3." list, this owner only --
                                         # see `decimal_numids` above
        decimal_nid: int | None = None  # numId decimal_buf's items belong to
        decimal_next_start: dict = {}   # numId -> next item's number, so a
                                         # list interrupted by a non-numPr
                                         # paragraph (a "Synthesis"/
                                         # "Isolation"/"Purification"
                                         # sub-heading, EJC 2024 H2 P2 Q4's
                                         # Procedure A/B) resumes counting
                                         # instead of restarting at 1 -- the
                                         # source PDF numbers Procedure A's
                                         # steps continuously 1-10 straight
                                         # through all three sub-headings
                                         # (confirmed via pdftotext -layout,
                                         # and load-bearing: Q4(c)(ii) asks
                                         # about "step 5" by that absolute
                                         # number), even though each
                                         # sub-heading paragraph breaks the
                                         # run of consecutive numPr
                                         # paragraphs this module groups.

        def _append(html_piece: str):
            nonlocal cur_part
            if not html_piece.strip() and FIG_SENTINEL not in html_piece:
                return
            html_piece, marks = _write_mark(html_piece)
            target = cur_part if cur_part is not None else q
            attr = "html" if cur_part is not None else "intro_html"
            existing = getattr(target, attr)
            if existing and _BADGE_ALONE_RE.fullmatch(html_piece):
                # This paragraph is nothing but a "[n]" badge -- EJC's own
                # convention, always its own paragraph (see module
                # docstring). Glue it onto the PREVIOUS paragraph's line
                # with a space rather than leaving it to float alone.
                new = existing + " " + html_piece.strip()
            else:
                new = (existing + "\n" + html_piece).strip() if existing \
                    else html_piece
            setattr(target, attr, new)
            if marks is not None and cur_part is not None:
                cur_part.marks = marks

        def _flush_bullets():
            nonlocal bullet_buf
            if not bullet_buf:
                return
            html = '<ul class="stmts">%s</ul>' \
                   % "".join("<li>%s</li>" % it for it in bullet_buf)
            bullet_buf = []
            _append(html)

        def _flush_decimal():
            nonlocal decimal_buf, decimal_nid
            if not decimal_buf:
                return
            # Reuses the existing `ol.stmts` CSS -- already correct for a
            # browser-auto-numbered list with no typed digit in the `<li>`
            # text (`questions_flow._wrap_stmt_lists`'s own docstring notes
            # this same CSS already renders a genuine numPr list correctly).
            # `start=` resumes this numId's own count across an interrupting
            # sub-heading rather than restarting at 1 -- see
            # `decimal_next_start`'s comment above for why that matters here.
            start = decimal_next_start.get(decimal_nid, 1)
            attr = ' start="%d"' % start if start != 1 else ""
            html = '<ol class="stmts"%s>%s</ol>' \
                   % (attr, "".join("<li>%s</li>" % it for it in decimal_buf))
            decimal_next_start[decimal_nid] = start + len(decimal_buf)
            decimal_buf = []
            _append(html)

        # --- figures, attributed by paragraph/table position within this
        # span -- a SEPARATE walk, mirroring parts.py's own two-pass design
        # ("so a figure-attribution bug cannot also corrupt text"). Run
        # BEFORE the content pass below, deliberately: that pass blanks each
        # label run's own text in place once it has read the label (so the
        # rendered content does not repeat it), which would otherwise erase
        # the very text this walk reads to track which part a figure is in.
        cur_letter2 = cur_roman2 = None
        roman_count2 = 0
        pidx2 = 0
        for el in span:
            ln = etree.QName(el).localname
            if ln not in ("p", "tbl"):
                continue
            if ln == "p":
                labels2 = _resolve_labels(
                    _para_runs(el), letter_open=cur_letter2 is not None,
                    roman_idx=roman_count2, numid=paragraph_numid(el),
                    letter_numids=letter_numids)
                for kind, value, _ in labels2:
                    if kind == "letter":
                        cur_letter2, cur_roman2 = value, None
                        roman_count2 = 0
                    elif kind == "roman":
                        roman_count2 += 1
                        cur_roman2 = value
            label = (cur_letter2 + cur_roman2) if cur_roman2 \
                else cur_letter2 if cur_letter2 else None
            # `_iter_top_figures` is a generic top-down walk that stops the
            # instant it meets a drawing/object/pict (and skips `Fallback`
            # outright) -- it does not care whether it started from a run, a
            # paragraph, or a whole table, only that it starts ABOVE any
            # figure boundary. For a `p`, feed it each of the paragraph's own
            # direct-child runs (matches `questions_flow.py`'s per-run
            # convention, and keeps run-index available if ever needed). For
            # a `tbl`, call it ONCE on the table itself rather than first
            # flattening to every `.//w:r` -- flattening was the bug: a
            # floating text-box figure's Choice/Fallback pair each carry
            # their OWN nested run with the embedded ChemDraw object several
            # levels down inside `w:txbxContent` (EJC Q3(b)(ii)'s Table 3.2
            # "W" structure -- confirmed by direct XML inspection), and
            # `.findall(".//w:r")` surfaces those nested runs as independent
            # top-level runs, so `_iter_top_figures` re-finds the SAME
            # picture a second and third time (once for the outer
            # `mc:Choice` drawing, once each for the nested object inside
            # Choice's and Fallback's own text-box content) -- 3 Figure
            # objects for what is one printed picture, only one of which the
            # rendered HTML ever places a placeholder for. Walking from the
            # table itself instead respects the same boundary the `p` branch
            # already gets for free from `_para_runs` only listing DIRECT
            # children.
            if ln == "p":
                for r in _para_runs(el):
                    for d in _iter_top_figures(r):
                        fig = _classify_drawing(d, rels)
                        ole = _own_ole(d)
                        if ole is not None and (
                                ole.get("ProgID") or "").startswith("Equation"):
                            fig.kind = "equation"
                        fig.index = fig_order
                        fig.qnum = qnum
                        fig.part = label
                        fig.cell = (pidx2, label)
                        all_figures.append(fig)
                        fig_order += 1
            else:  # tbl
                for d in _iter_top_figures(el):
                    fig = _classify_drawing(d, rels)
                    ole = _own_ole(d)
                    if ole is not None and (
                            ole.get("ProgID") or "").startswith("Equation"):
                        fig.kind = "equation"
                    fig.index = fig_order
                    fig.qnum = qnum
                    fig.part = label
                    fig.cell = (pidx2, label)
                    all_figures.append(fig)
                    fig_order += 1
            pidx2 += 1

        pidx = 0
        for el in span:
            ln = etree.QName(el).localname
            if ln == "tbl":
                _flush_bullets()
                _flush_decimal()
                h = _parts_mod._table_html(el)
                if h:
                    _append(h)
                pidx += 1
                continue
            if ln != "p":
                continue

            if _has_numpr(el):
                nid = paragraph_numid(el)
                if nid is not None and nid in bullet_numids:
                    # A genuine bulleted list item -- buffer for <ul>. See
                    # module docstring: NOT the common case in this paper.
                    h = paragraph_html(el)
                    if h.strip():
                        bullet_buf.append(h)
                    pidx += 1
                    continue
                if nid is not None and nid in decimal_numids:
                    # Word's own "1./2./3." auto-numbering with no typed
                    # digit at all -- buffer for <ol>. Q4's Procedure A/B
                    # steps (numId 8/9); see `decimal_numids` above.
                    h = paragraph_html(el)
                    if h.strip():
                        decimal_buf.append(h)
                    decimal_nid = nid
                    pidx += 1
                    continue
                # numPr here is NOT a bulleted or decimal list item, but is not
                # always mere decoration either -- most numId-4 paragraphs
                # (lowerLetter "(%1)" at ilvl 0) carry their own typed bold
                # letter too, making the numbering redundant, and fall
                # through to the SAME label-detection path as an ordinary
                # paragraph so that typed label is read normally. Exactly
                # one paragraph in this document (Q2's opening part) has no
                # typed letter at all and genuinely depends on this
                # numbering for its "(a)" -- `_resolve_labels` (below)
                # recovers that one case; see its own docstring. Falls
                # through deliberately either way (no `continue`).
            _flush_bullets()
            _flush_decimal()

            runs = _para_runs(el)
            text = "".join(_run_bare_text(r) for r in runs)
            stripped = text.strip()

            if _boilerplate(stripped):
                pidx += 1
                continue
            m = TOTAL_MARKS_RE.match(stripped)
            if m:
                q.marks_total = int(m.group(1))
                pidx += 1
                continue
            has_fig = (el.find(".//" + Wq + "drawing") is not None
                      or el.find(".//" + Wq + "object") is not None
                      or el.find(".//" + Wq + "pict") is not None)
            if not has_fig and _DOTTED_RE.match(stripped):
                pidx += 1
                continue

            labels = _resolve_labels(runs, letter_open=cur_letter is not None,
                                     roman_idx=roman_count,
                                     numid=paragraph_numid(el),
                                     letter_numids=letter_numids)
            # `label_run_idx` is taken from the FULL match, including a
            # leading qnum -- that run's own text ("2" for Q2's opening
            # paragraph) must still be blanked, or it leaks into the
            # rendered intro as literal text right before the tab that
            # follows it ("2\tThis question is about..."). Only the
            # OPEN/APPEND loop below drops that entry afterwards, so it is
            # not treated as (say) a stray letter/roman open on nothing --
            # this span's own opening paragraph already gave us `qnum`.
            label_run_idx = [i for _, _, idxs in labels for i in idxs]
            if pidx == 0 and labels and labels[0][0] == "qnum":
                labels = labels[1:]

            for kind, value, _ in labels:
                if kind == "letter":
                    cur_letter = value
                    roman_count = 0
                    cur_part = Part(qnum=qnum, label=cur_letter)
                    q.parts.append(cur_part)
                elif kind == "roman":
                    if cur_letter is None:
                        anomalies.append(
                            "Q%d%s: roman numeral with no letter part open"
                            % (qnum, value))
                    else:
                        roman_count += 1
                        cur_part = Part(qnum=qnum, label=cur_letter + value)
                        q.parts.append(cur_part)
                elif kind == "qnum":
                    anomalies.append(
                        "Q%d: unexpected second question-number label at "
                        "paragraph %d" % (qnum, pidx))

            if label_run_idx:
                _blank_runs(runs, label_run_idx)
            html = paragraph_html(el)
            _append(html)
            pidx += 1

        _flush_bullets()
        _flush_decimal()

    # Native-shape merging: adjacent shapes in the SAME paragraph are one
    # picture (questions_flow.py's own rule for this document family).
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

    by_owner_raw: dict[tuple, list[Figure]] = {}
    for f in all_figures:
        by_owner_raw.setdefault((f.qnum, f.part), []).append(f)

    ordered_figures: list[Figure] = []
    for q in questions:
        raw = by_owner_raw.get((q.qnum, None), [])
        if scope and corrections.combined_figures_reason(*scope, q.qnum, None):
            q.intro_figures, q.intro_html = _force_combine(raw, q.intro_html)
        else:
            q.intro_figures, q.intro_html = merge_owner_figures(
                raw, q.intro_html, anomalies)
        q.n_intro_placeholders = q.intro_html.count(FIG_SENTINEL)
        ordered_figures.extend(q.intro_figures)
        for p in q.parts:
            raw = by_owner_raw.get((p.qnum, p.label), [])
            if scope and corrections.combined_figures_reason(
                    *scope, p.qnum, p.label):
                p.figures, p.html = _force_combine(raw, p.html)
            else:
                p.figures, p.html = merge_owner_figures(raw, p.html, anomalies)
            p.n_placeholders = p.html.count(FIG_SENTINEL)
            ordered_figures.extend(p.figures)
    all_figures = ordered_figures
    for n, f in enumerate(all_figures):
        f.index = n

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

    # --- marks cross-check, same as parts.py's own ---
    for q in questions:
        got = sum(p.marks or 0 for p in q.parts)
        if q.marks_total is not None and got != q.marks_total:
            anomalies.append("Q%d: parts sum to %d but the paper prints "
                             "[Total: %d]" % (q.qnum, got, q.marks_total))

    # THIS MODULE IS FOR STRUCTURED (paragraph-flow) PAPERS ONLY -- same
    # guard as parts.py, for the same reason (see that module's note).
    no_parts = [q.qnum for q in questions if not q.parts]
    if len(no_parts) > len(questions) // 2:
        raise ValueError(
            "%d of %d questions have no lettered parts at all. This looks "
            "like an MCQ paper; ingest.parts_flow handles STRUCTURED "
            "paragraph-flow papers only. Questions with no parts: %s"
            % (len(no_parts), len(questions), no_parts[:10]))

    return questions, all_figures, anomalies
