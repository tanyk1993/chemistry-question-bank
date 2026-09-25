"""Emit `content_html`, `content_text` and `options` for MCQ questions.

MARKUP CONVENTION -- read off index.html's live CSS, not invented:

  p.qstem          stem prose (handoff SS7)
  div.fig          block figure placeholder, filled BY ORDINAL in DOM order
  table.qt         a data table inside the stem (Q12's enthalpy table)
  table.opts-table the options grid; td.ol is the letter column, which
                   index.html styles bold on a tinted background
  p.c              centred paragraph inside the stem

Handoff SS6E records `p`/`opts-table` as the MCQ convention that has not yet
been unified with the structured `qpart`/`pl`/`mk` one. This emits the MCQ side
of that split as it already exists in the CSS; unifying them is a separate job
and is deliberately NOT attempted here.

TWO THINGS THAT SILENTLY BREAK IF GOT WRONG
-------------------------------------------
1. `content_text` must be non-null. `content_search` is
   GENERATED ALWAYS AS chem_search_doc(content_text, keywords, options), and
   `content_html` is NOT an input -- so a null content_text inserts fine,
   renders fine, and is invisible to search (handoff SS8).

2. Exactly ONE `.fig` placeholder is emitted for the whole set of option
   figures, never one per option. index.html collects every option-slotted
   asset into a single `.optgrid` and drops it into the first placeholder left
   over after the stem figures; emitting four would leave three stray
   placeholders, which the frontend then REMOVES along with the assets they
   would have carried.
"""
from __future__ import annotations

import html
import re

from . import corrections
from .oxml import CENTRE

FIG_SENTINEL = "\x00FIG\x00"
FIG_DIV = '<div class="fig">figure</div>'

#: A superscript IMMEDIATELY followed by a subscript (or the reverse) with
#: nothing between them is one stacked symbol, not two sequential ones --
#: E-standard-state-cell, written in Word as two adjacent runs rather than as
#: an OMML sSubSup. Rendered in sequence it reads as "E to the power of
#: plimsoll, then subscript cell", which is a different quantity. Deliberately
#: strict about adjacency: anything with text or markup in between is left
#: alone, because a genuine exponent followed later by an unrelated subscript
#: must not be fused.
_STACK_AB = re.compile(r"<sup>([^<>]{1,12})</sup><sub>([^<>]{1,12})</sub>")
_STACK_BA = re.compile(r"<sub>([^<>]{1,12})</sub><sup>([^<>]{1,12})</sup>")


def _stack_adjacent(h: str) -> str:
    h = _STACK_AB.sub(
        r'<span class="stk post"><span>\1</span><span>\2</span></span>', h)
    return _STACK_BA.sub(
        r'<span class="stk post"><span>\2</span><span>\1</span></span>', h)


# ---------------------------------------------------------------------------
# block vs inline, and why the ordinal order is what it is
# ---------------------------------------------------------------------------
# index.html has two separate mechanisms (handoff SS7):
#
#   BLOCK   `div.fig` placeholders, collected in DOM order and filled from the
#           question's assets sorted by ORDINAL. Position-matched.
#   INLINE  `img[data-asset="FILE.png"]`, matched by FILENAME in resolveAssets()
#           before the placeholder loop runs.
#
# A figure sharing a paragraph with text must be inline. RI 2024 H2 P1 Q12
# writes "1/2 N2(g) + 1/2 O2(g) -> NO(g)" with the halves as legacy Equation
# Editor objects, so each is a figure mid-sentence; hoisted out as block
# placeholders they detach from their own equation and the table reads as
# nonsense.
#
# THE ORDINAL RULE THAT MAKES THIS SAFE: resolveAssets() sets src on the inline
# images, but the placeholder loop afterwards still walks the FULL stem asset
# list -- inline ones included. So if an inline asset held a lower ordinal than
# a block one, it would be consumed by the first `div.fig` and every later
# figure would shift by one. Block figures are therefore numbered FIRST, in DOM
# order, and inline figures take the ordinals after them. Inline matching is by
# filename, so their ordinal only has to be unique and out of the way.



#: <span class="frac"><span class="fnum">X</span><span class="fden">Y</span></span>
_FRAC_RE = re.compile(
    r'<span class="frac"><span class="fnum">(.*?)</span>'
    r'<span class="fden">(.*?)</span></span>', re.S)


def _strip_tags(s: str) -> str:
    # Flatten fractions BEFORE dropping tags. Without this the numerator and
    # denominator run together: Q1's four options all reduce to strings like
    # "6.02 x 102324000", which is meaningless in `options` and poisons
    # content_search, where these strings actually get indexed.
    s = _FRAC_RE.sub(lambda m: "(%s)/(%s)" % (_strip_tags(m.group(1)),
                                              _strip_tags(m.group(2))), s)
    s = s.replace(FIG_SENTINEL, " ").replace(CENTRE, "")
    # An EXPONENT loses its meaning when the tags are dropped: "10<sup>23</sup>"
    # becomes "1023", so Q1's options all read like six-figure integers. Marked
    # with a caret, narrowly -- only a superscript of digits directly after a
    # digit. "1<sup>st</sup> ionisation" and "cm<sup>3</sup>" are deliberately
    # left alone, because they tokenise as "1st" and "cm3" and that is how
    # someone would search for them.
    s = re.sub(r"(?<=\d)<sup>([+-]?\d+[+-]?)</sup>", r"^\1", s)
    s = re.sub(r"<br ?/?>", " ", s)
    # Two adjacent BLOCK elements with nothing textual between their tags --
    # "<li>A</li><li>B</li>", "<p>A</p><p>B</p>" -- must not glue into one
    # word once the tags themselves are dropped below. A <p> already gets a
    # separating "\n" from how _blocks() joins lines (collapsed to a space by
    # the final \s+ pass at the end of this function), but an <ol class=
    # "stmts">'s <li>s sit on a single line with no separator of their own --
    # confirmed live on Q7's four numbered relationships, content_text reading
    # "...(∆G3 + ∆G4)∆G2 = ∆G4..." with no space at the join, and reproduced
    # (worse: two whole sentences fused) once Q10's typed statements 2 and 3
    # were folded into its <ol> alongside statement 1 (questions_flow.py's
    # _wrap_stmt_lists). The trailing space this adds is harmless everywhere
    # else -- the final \s+ collapse below absorbs it.
    s = re.sub(r"</(li|p|tr|div)>", r"</\1> ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _para(h: str) -> str:
    """One stem paragraph, honouring the centring sentinel.

    A mid-sentence <br> is Word's layout line-wrap, not content (handoff SS7 /
    oxml.py leaves the decision to the caller). The app reflows the stem to its
    own width, so keeping the source's wrap points would break sentences at
    arbitrary places -- Q9 wraps between "across" and "Period 3".
    """
    h = re.sub(r"<br ?/?>", " ", h)
    centred = h.startswith(CENTRE)
    body = h[len(CENTRE):] if centred else h
    # A LEADING tab is pure indentation styling, not a value with anything to
    # line up against -- Q19's "\tWhich statement is correct?" and Q23's
    # "\tWhich compound will produce..." both open with one. It already
    # renders invisibly today (collapsed like any other whitespace), so drop
    # it rather than let the eqn/pre-wrap treatment below turn it into an
    # unexplained gap before the question text.
    body = re.sub(r"^\t+", "", body)
    if centred:
        return '<p class="c">%s</p>' % body
    # oxml.py preserves a genuine Word tab as a literal "\t" (never emitted
    # for anything but a real <w:tab/>, so its presence is always deliberate
    # column alignment, not an accident). `eqn` + index.html's
    # `white-space:pre-wrap`+`tab-size` reproduces that column instead of
    # collapsing it to nothing -- EJC 2024 H2 P1 Q8's "reaction 1  <eqn>",
    # Q10's "reaction 1:  <eqn>  ∆H = ...", Q29's bare "<eqn>  E-o- = ...".
    cls = "qstem eqn" if "\t" in body else "qstem"
    return '<p class="%s">%s</p>' % (cls, body)


def _next_sub(state) -> str:
    """The next figure substitution in document order."""
    if state is None:
        return FIG_DIV
    return next(state["subs"], FIG_DIV)


def _sub_cell(text: str, state) -> str:
    """Replace this fragment's figures in place, in document order."""
    out = text
    while FIG_SENTINEL in out:
        out = out.replace(FIG_SENTINEL, _next_sub(state), 1)
    return out


_INLINE_TAGS = ("b", "i", "u", "sub", "sup", "span")


def _rebalance(frag: str) -> str:
    """Drop inline tags left dangling when a paragraph is split.

    Splitting `<b>FIG</b>Which row ...` leaves the text fragment starting with
    a `</b>` whose opener went with the figure. Browsers forgive it; a diff
    against the next extraction does not, and it is wrong in the bank.
    """
    for t in _INLINE_TAGS:
        opens = len(re.findall(r"<%s(?:\s[^>]*)?>" % t, frag))
        closes = len(re.findall(r"</%s>" % t, frag))
        for _ in range(closes - opens):
            frag = re.sub(r"</%s>" % t, "", frag, count=1)
        for _ in range(opens - closes):
            frag = re.sub(r"<%s(?:\s[^>]*)?>(?!.*<%s)" % (t, t), "", frag,
                          count=1, flags=re.S)
    return frag


def _mixed_para(line: str, state) -> list:
    """A paragraph holding both text and figures.

    A figure that is genuinely mid-sentence stays where it is -- Q12's 1/2
    coefficients are `span.frac` and belong inside their own equation. A BLOCK
    figure cannot: `div.fig` is a block element, and leaving it in place put
    Q19's whole electrochemical cell inside a `<b>` in the middle of "Which row
    gives ...". Word had simply kept the diagram and the sentence in one
    paragraph; the paper prints them stacked. So a block placeholder is hoisted
    out and the text around it becomes its own paragraph(s).
    """
    centred = line.startswith(CENTRE)
    body = line[len(CENTRE):] if centred else line
    out, buf = [], ""
    for i, frag in enumerate(body.split(FIG_SENTINEL)):
        if i:
            sub = _next_sub(state)
            if sub.startswith("<div"):
                text = _rebalance(buf)
                if _strip_tags(text):
                    out.append(_para((CENTRE if centred else "") + text))
                buf = ""
                out.append(sub)
            else:
                buf += sub      # span.frac and friends stay in the sentence
        buf += frag
    text = _rebalance(buf)
    if _strip_tags(text) or FIG_SENTINEL in text:
        out.append(_para((CENTRE if centred else "") + text))
    return out


def _blocks(chunk: str, state=None) -> list:
    """Split a cell's HTML into block elements.

    A figure alone in its paragraph (or cell) becomes a `div.fig` placeholder;
    one sharing space with text becomes an inline `<img data-asset>`. See the
    block-vs-inline note at the top of this module.
    """
    out = []
    for line in chunk.split("\n"):
        if not line.strip():
            continue
        # A TABLE is handled cell by cell. Q12's three thermochemical equations
        # are images inside its data table; hoisting them out as block
        # placeholders would dismantle the table and orphan the enthalpy values
        # from the equations they belong to.
        if line.lstrip().startswith("<table"):
            def _cell(m):
                inner = m.group(1)
                if FIG_SENTINEL not in inner:
                    return m.group(0)
                return "<td>%s</td>" % _sub_cell(inner, state)
            out.append(re.sub(r"<td>(.*?)</td>", _cell, line, flags=re.S)
                       .replace(CENTRE, ""))
            continue
        if line.lstrip().startswith(("<ol", "<ul")):
            # A pre-built numbered/bulleted statement list (style-guide.md
            # section 2: "Numbered statements -- emit ol.stmts", "Bullets --
            # emit ul.stmts"). Built by the caller as a single already-complete
            # <ol class="stmts">...</ol> or <ul class="stmts">...</ul> line, so
            # it must pass through whole -- wrapping it in <p class="qstem">
            # like ordinary prose would nest a list inside a paragraph, which
            # is invalid and which browsers "fix" by hoisting the list out,
            # silently splitting it from the sentence introducing it.
            # Same mid-sentence-<br>-is-not-content reasoning as _para()
            # above applies here too -- exposed by Q10's statement 3 (a
            # genuine w:br in the source) once _wrap_stmt_lists folds it
            # into this <ol> instead of leaving it as its own <p>, which
            # used to run it through _para()'s stripping.
            line = re.sub(r"<br ?/?>", " ", line)
            def _li(m):
                inner = m.group(1)
                if FIG_SENTINEL not in inner:
                    return m.group(0)
                return "<li>%s</li>" % _sub_cell(inner, state)
            out.append(re.sub(r"<li>(.*?)</li>", _li, line, flags=re.S)
                       .replace(CENTRE, ""))
            continue
        if FIG_SENTINEL in line:
            if _strip_tags(line.replace(FIG_SENTINEL, "")):
                out.extend(_mixed_para(line, state))
            else:
                # A DROPPED figure substitutes to "" and must leave nothing
                # behind -- not an empty div.fig, which the app would render as
                # a broken image box.
                out.extend([s for s in (_next_sub(state)
                                        for _ in range(line.count(FIG_SENTINEL)))
                            if s])
            continue
        out.append(_para(line))
    return out


def _is_blank(cell: str) -> bool:
    return not (_strip_tags(cell) or FIG_SENTINEL in cell)


def _normalise(rows: list) -> list:
    """Square up a table: drop trailing empty columns, align short rows.

    Two defects came from skipping this. A single stray empty cell in the
    source widened RI 2024 H2 P1 Q10 and Q11 by a phantom column (two of them
    on Q11, which also made a plain prose question render as a table at all).

    And Q25's structure matrix has a 3-cell heading row over 4-cell data rows,
    because the data rows carry a leading row NUMBER the heading does not. Left
    unpadded, every structure displayed one column to the LEFT of its heading --
    what sat under "structure of Q" was actually P. That one is worse than a
    cosmetic fault: it is wrong content, presented confidently, and nothing on
    screen looks broken.

    So a FIRST row shorter than the rest is padded on the LEFT (it is a heading
    over a labelled grid); any other short row is padded on the right.
    """
    rows = [list(r) for r in rows]
    width = max(len(r) for r in rows)
    while width > 1 and all(len(r) < width or _is_blank(r[width - 1]) for r in rows):
        rows = [r[:width - 1] if len(r) >= width else r for r in rows]
        width -= 1
    out = []
    for i, r in enumerate(rows):
        pad = width - len(r)
        if pad <= 0:
            out.append(r)
        elif i == 0:
            out.append([""] * pad + r)
        else:
            out.append(r + [""] * pad)
    return out


def _extra_table(rows: list, state=None) -> list:
    """Render non-option, non-stem rows.

    A single-column run is just more stem prose. A genuine grid (Q25's 4x3
    structure matrix, Q7's numbered statements) keeps its shape, because the
    row and column headings carry meaning: Q25 cannot be read at all without
    "structure of P / Q / R" sitting above the right columns.
    """
    if not rows:
        return []
    rows = _normalise(rows)
    width = max(len(r) for r in rows)
    if width == 1:
        out = []
        for r in rows:
            out.extend(_blocks(r[0], state))
        return out
    trs = []
    for r in rows:
        tds = []
        for cell in r:
            inner = "".join(_blocks(cell, state)) if cell.strip() or FIG_SENTINEL in cell else ""
            tds.append("<td>%s</td>" % inner)
        trs.append("<tr>%s</tr>" % "".join(tds))
    return ['<table class="qt center">%s</table>' % "".join(trs)]


def figure_kinds(q, frac_letters=frozenset(), eqtext_map=None) -> list:
    """['block'|'frac'|'option'|'eqtext'] for each of q.figures, in document order.

    Decided from the figure itself, not from the layout around it: an
    Equation.DSMT4 object is maths, a ChemDraw object or native shape is a
    picture. See questions.py for why the ProgID is the right evidence.

    An OPTION-position figure is the one exception, and only when explicitly
    told to be: an Equation.DSMT4 object sitting in an option is "option", the
    same as a picture, UNLESS its letter is in `frac_letters`
    (corrections.frac_option_letters) -- a per-question, per-letter allowlist,
    populated only once someone has actually looked at the PDF and confirmed
    it prints a plain, single-rule numerator/denominator fraction that
    `question_figures.read_fraction` can read cleanly.

    This is NOT decidable from kind alone. EJC 2024 H2 P1's Q9 and Q13 are
    both option-position Equation.DSMT4 objects, and they are NOT the same
    kind of content: Q9 is a clean fraction, e.g. "(X + Y + Z) / W" -- one
    hairline rule, one line of PDF text above it, one below, all inside
    `RULE_MAX_W`'s (widened) budget. Q13 is a Ka expression with concentration
    brackets built from MathType's stretchy two-piece glyphs (confirmed by
    direct inspection: U+F0E9/F0EB/F0F9/F0FB, already in `audit.FIGURE_BORNE`
    as figure-borne from the SAME investigation) -- there is no clean
    numerator/denominator split to read, and text-decoding it would silently
    mangle the expression. Defaulting every option-position equation to
    "frac" once produced exactly that: Q13 handed to `read_fraction` found
    nothing.

    Q13's four options ARE hand-reconstructable as markup, though -- just not
    by `read_fraction`'s simple one-rule reader -- so `corrections.py`'s
    `eqtext_options` (`eqtext_map` here) carries them pre-built. Checked
    BEFORE `frac_letters`: a letter in `eqtext_map` gets "eqtext" regardless
    of what `frac_letters` says, since the two are alternative treatments for
    the same underlying problem (an option too complex for `read_fraction`)
    and a question should only ever be in one of the two registries.
    """
    eqtext_map = eqtext_map or {}
    out = []
    for f in q.figures:
        if f.part.startswith("option"):
            letter = f.part.split(":", 1)[1]
            if letter in eqtext_map:
                out.append("eqtext")
            elif f.kind == "equation" and letter in frac_letters:
                out.append("frac")
            else:
                out.append("option")
        elif f.kind == "equation":
            out.append("frac")
        else:
            out.append("block")
    return out


def asset_plan(q, school="RI", level="H2", paper="P1", year=2024) -> list:
    """Per-asset {slot, ordinal, storage_path}, block figures first.

    Fractions get NO asset -- they are rendered as `span.frac` markup, the same
    house style WA2 and RI P2 use, so there is nothing to upload and nothing to
    crop. An "eqtext" option (corrections.eqtext_options) gets none either,
    for the same reason. `storage_path` is a BARE FILENAME (SS8), named
    SCHOOL_LEVEL_PAPER_Qn_SLOT_YEAR.png.
    """
    frac_letters = corrections.frac_option_letters(school, level, paper, year, q.qnum)
    eqtext_map = corrections.eqtext_options(school, level, paper, year, q.qnum)
    kinds = figure_kinds(q, frac_letters, eqtext_map)
    dropped = corrections.dropped_blocks(school, level, paper, year, q.qnum)
    plan, nb, nseen = [], 0, 0
    for i, kind in enumerate(kinds):
        if kind != "block":
            continue
        nseen += 1
        if nseen in dropped:
            # Deliberately not placed -- see corrections.DROPPED_FIGURES. The
            # index is simply absent from the plan, and content_html/_text read
            # the plan, so the placeholder disappears with the asset.
            continue
        nb += 1
        plan.append({"question": q.qnum, "index": i, "kind": "block",
                     "slot": "stem%d" % nb, "n_parts": q.figures[i].n_parts})
    seen: set = set()
    for i, kind in enumerate(kinds):
        if kind != "option":
            continue
        letter = q.figures[i].part.split(":", 1)[1]
        if letter in seen:
            continue
        seen.add(letter)
        # slot MUST be the bare letter: index.html's isOptSlot = /^[A-E]$/ is
        # what routes the asset into the option grid.
        plan.append({"question": q.qnum, "index": i, "kind": "option",
                     "slot": letter, "n_parts": q.figures[i].n_parts})
    for ordinal, item in enumerate(plan, start=1):
        item["ordinal"] = ordinal
        item["storage_path"] = "%s_%s_%s_Q%d_%s_%d.png" % (
            school, level, paper, q.qnum, item["slot"], year)
    return plan


def _frac(num: str, den: str) -> str:
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (num, den))


def _subs(q, plan, fractions, frac_fmt, block, drop, frac_letters=frozenset(),
         eqtext_map=None) -> list:
    """One substitution per non-option figure, in document order.

    Both renderers go through here, and that is the point. content_text used to
    do its own thing -- replace every sentinel it met with the next fraction --
    which is right only for a question whose figures are ALL fractions. On Q12,
    whose first figure is a picture, the picture swallowed the 1/2 that belonged
    to the equation below it, so the search text read "the table. (1)/(2) 2NO(g)"
    and the third equation lost its coefficient entirely. The markup was right
    and the search text was wrong, silently, because the two shared no code.

    A block figure that is not in `plan` was dropped on purpose
    (corrections.DROPPED_FIGURES) and substitutes to `drop`. Passing plan=None
    means "assume every figure is placed".

    `frac_letters` is `corrections.frac_option_letters` -- see figure_kinds.
    `eqtext_map` is `corrections.eqtext_options` -- an "eqtext" option, like an
    "option" (picture) one, gets nothing from this sequential walk; its fixed
    per-letter value is looked up directly by the caller instead (see
    `_consume_option_fracs`), so it is skipped here the same way.
    """
    kinds = figure_kinds(q, frac_letters, eqtext_map)
    # `plan is None` means "unknown, assume all placed"; an EMPTY plan means
    # nothing is placed. Conflating the two is what left Q12's dropped figure
    # still printing a div.fig after the asset itself was gone.
    placed = (None if plan is None
              else {p["index"] for p in plan if p["kind"] == "block"})
    fracs = list(fractions or [])
    out = []
    for i, k in enumerate(kinds):
        if k in ("option", "eqtext"):
            continue
        if k == "frac":
            n, d = fracs.pop(0) if fracs else ("", "")
            out.append(frac_fmt(n, d))
        elif placed is not None and i not in placed:
            out.append(drop)
        else:
            out.append(block)
    return out


def _consume_option_fracs(q, kinds, subs_iter, from_start: bool = False) -> dict:
    """{letter: value} for OPTION-position figures classified 'frac'.

    `_subs()` no longer skips these (figure_kinds gives them 'frac', not
    'option'), so its returned list already carries one entry for each, in
    the SAME relative document order as `q.figures` -- just interleaved with
    every stem/extra entry that comes before them.

    `from_start=False` (content_html, content_text): the caller has ALREADY
    walked every sentinel in `q.stem_html`/`q.extra_html` on this SAME
    iterator (via `_blocks`/`_extra_table`/`fx`), which -- because a
    question's stem always precedes its options -- has already advanced
    `subs_iter` past everything ahead of the first option-frac entry. This
    then only has to pick those out in order, never re-consuming anything the
    caller already took.

    `from_start=True` (options_json): no stem walk happens at all, so this
    has to burn through every OTHER non-option entry itself first (`_subs()`
    still emitted a value for it, just not one this function keeps) or the
    first option-frac would wrongly take a value meant for the stem.
    """
    out = {}
    for i, f in enumerate(q.figures):
        is_opt_frac = kinds[i] == "frac" and f.part.startswith("option:")
        if not from_start and not is_opt_frac:
            continue           # caller already consumed this one itself
        if kinds[i] in ("option", "eqtext"):
            continue            # _subs() never emitted anything for these
        val = next(subs_iter, "")
        if is_opt_frac:
            out[f.part.split(":", 1)[1]] = val
    return out


def content_html(q, plan=None, fractions=None, frac_letters=frozenset(),
                 eqtext_map=None) -> str:
    """Render the question.

    `fractions` is [(num, den), ...] for this question's Equation objects, in
    document order, read from the Word PDF by question_figures.read_fraction.
    Without it the fraction is emitted as an empty `span.frac`, which is
    visibly wrong rather than quietly wrong.

    `frac_letters` is `corrections.frac_option_letters` -- see figure_kinds.
    `eqtext_map` is `corrections.eqtext_options` -- see figure_kinds.
    """
    eqtext_map = eqtext_map or {}
    kinds = figure_kinds(q, frac_letters, eqtext_map)
    state = {"subs": iter(_subs(q, plan, fractions, _frac, FIG_DIV, "",
                                frac_letters, eqtext_map))}

    parts: list = []
    parts.extend(_blocks(q.stem_html, state))
    run: list = []
    for row in q.extra_html:
        if len(row) > 1:
            run.append(row)
            continue
        if run:
            parts.extend(_extra_table(run, state))
            run = []
        parts.extend(_extra_table([row], state))
    if run:
        parts.extend(_extra_table(run, state))

    # ONE placeholder for the whole option grid -- never one per option.
    if any(k == "option" for k in kinds):
        parts.append(FIG_DIV)

    # A CAPTIONED FIGURE OPTION gets no options table. Q8's four options are
    # graphs captioned "constant V" / "constant T"; the frontend prints that
    # caption under its own diagram in the option grid (index.html, .optcap),
    # so emitting a table of the same four strings below the grid repeats every
    # one of them and separates the caption from the graph it describes -- the
    # detached 2x2 table this was meant to fix, in a new position.
    #
    # Scoped to kind == "option" ONLY: a "frac" option (EJC Q9/Q13's stacked
    # fractions, see figure_kinds) has no image at all -- there is nothing for
    # the frontend's asset grid to show under a caption, so it must fall
    # through to the ordinary options table below instead, where the fraction
    # itself gets substituted in.
    letters = sorted(q.options)
    fig_letters = {f.part.split(":", 1)[1] for i, f in enumerate(q.figures)
                   if f.part.startswith("option:") and kinds[i] == "option"}
    captioned = bool(letters) and set(letters) <= fig_letters and all(
        len(_strip_tags("".join(q.options[L]))) <= 40 for L in letters)
    if captioned:
        letters = []
    # Pulled from the SAME iterator content_html's stem/extra rendering just
    # walked -- must happen after that (a question's stem always precedes its
    # options) and before the options are built, so each frac substitutes into
    # the right letter's cell. See _consume_option_fracs.
    frac_subs = _consume_option_fracs(q, kinds, state["subs"])
    # An "eqtext" letter's markup is a fixed lookup, not pulled from the subs
    # iterator (see _subs) -- merged in here so the table-cell substitution
    # below (originally built for "frac" alone) handles both the same way.
    # The two registries are mutually exclusive per letter (figure_kinds), so
    # this merge can never silently drop one in favour of the other.
    combined_subs = {**frac_subs, **{L: html for L, (html, _t) in eqtext_map.items()}}
    if letters and any(_strip_tags("".join(v)) or FIG_SENTINEL in "".join(v)
                       for v in q.options.values()):
        # Trim trailing empty columns before deciding the width -- one stray
        # blank cell in the source otherwise adds a phantom column to every row.
        body = [list(q.options[L]) or [""] for L in letters]
        if q.opt_headers:
            body.insert(0, list(q.opt_headers))
        body = _normalise(body)
        if q.opt_headers:
            headers, body = body[0], body[1:]
        else:
            headers = None
        ncol = max((len(v) for v in body), default=1) or 1
        trs = []
        if headers:
            hdr = "".join("<td>%s</td>" % _strip_hdr(h) for h in headers)
            trs.append('<tr><td class="ol"></td>%s</tr>' % hdr)
        for L, vals in zip(letters, body):
            vals = list(vals) + [""] * (ncol - len(vals))
            tds = "".join("<td>%s</td>" % _inline(v, combined_subs.get(L, ""))
                         for v in vals)
            trs.append('<tr><td class="ol">%s</td>%s</tr>' % (L, tds))
        parts.append('<table class="opts-table">%s</table>' % "".join(trs))
    return _stack_adjacent("\n".join(parts))


def _strip_hdr(h: str) -> str:
    return h.replace(CENTRE, "").replace("\n", " ").strip()


def _inline(v: str, sub: str = "") -> str:
    """One options-table cell, with any figure sentinel replaced by `sub`.

    `sub` defaults to "" -- dropping the sentinel entirely -- which is right
    for a real picture option: the image itself is inserted separately by the
    frontend's own asset-grid build, matched by slot letter, never by this
    text substitution (see the module docstring's rule 2). A "frac" option
    (EJC Q9/Q13) has no separate image at all, so its caller passes the
    already-rendered `<span class="frac">` markup here instead.
    """
    return v.replace(CENTRE, "").replace(FIG_SENTINEL, sub).replace("\n", " ").strip()


def content_text(q, fractions=None, frac_letters=frozenset(), eqtext_map=None) -> str:
    """Plain text for search. MUST be non-null -- see the module docstring.

    `frac_letters` is `corrections.frac_option_letters` -- see figure_kinds.
    `eqtext_map` is `corrections.eqtext_options` -- see figure_kinds.
    """
    eqtext_map = eqtext_map or {}
    kinds = figure_kinds(q, frac_letters, eqtext_map)
    subs = iter(_subs(q, None, fractions,
                      lambda n, d: "(%s)/(%s) " % (n, d), " ", " ",
                      frac_letters, eqtext_map))
    def fx(h):
        out = h
        while FIG_SENTINEL in out:
            out = out.replace(FIG_SENTINEL, next(subs, " "), 1)
        return out
    bits = [_strip_tags(fx(q.stem_html))]
    for row in q.extra_html:
        bits.extend(_strip_tags(fx(c)) for c in row)
    if q.opt_headers:
        bits.append(" | ".join(_strip_tags(h) for h in q.opt_headers))
    # Pulled from the SAME iterator the stem/extra walk above just advanced --
    # see _consume_option_fracs.
    frac_subs = _consume_option_fracs(q, kinds, subs)
    combined_subs = {**frac_subs, **{L: t for L, (_h, t) in eqtext_map.items()}}
    for L in sorted(q.options):
        val = " | ".join(
            _strip_tags(v.replace(FIG_SENTINEL, combined_subs.get(L, "")))
            for v in q.options[L])
        bits.append("%s %s" % (L, val) if val else L)
    return re.sub(r"\s+", " ", " ".join(b for b in bits if b)).strip()


def options_json(q, fractions=None, frac_letters=frozenset(), eqtext_map=None) -> dict:
    """{'A': 'text', ...} -- feeds chem_search_doc, so plain text only.

    `frac_letters` is `corrections.frac_option_letters` -- see figure_kinds.
    `eqtext_map` is `corrections.eqtext_options` -- see figure_kinds.
    """
    eqtext_map = eqtext_map or {}
    kinds = figure_kinds(q, frac_letters, eqtext_map)
    subs = iter(_subs(q, None, fractions,
                      lambda n, d: "(%s)/(%s)" % (n, d), " ", " ",
                      frac_letters, eqtext_map))
    # No stem to walk here (options_json never touches q.stem_html), so this
    # has to burn through every earlier non-option entry itself -- see
    # _consume_option_fracs's from_start note.
    frac_subs = _consume_option_fracs(q, kinds, subs, from_start=True)
    combined_subs = {**frac_subs, **{L: t for L, (_h, t) in eqtext_map.items()}}
    out = {}
    for L in sorted(q.options):
        txt = " | ".join(
            t for t in (_strip_tags(v.replace(FIG_SENTINEL, combined_subs.get(L, "")))
                       for v in q.options[L]) if t)
        if not txt and any(f.part == "option:" + L for f in q.figures):
            txt = "[structure %s]" % L
        out[L] = txt
    return out
