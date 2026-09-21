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
    if h.startswith(CENTRE):
        return '<p class="c">%s</p>' % re.sub(r"<br ?/?>", " ", h[len(CENTRE):])
    return '<p class="qstem">%s</p>' % re.sub(r"<br ?/?>", " ", h)


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


def figure_kinds(q) -> list:
    """['block'|'frac'|'option'] for each of q.figures, in document order.

    Decided from the figure itself, not from the layout around it: an
    Equation.DSMT4 object is maths, a ChemDraw object or native shape is a
    picture. See questions.py for why the ProgID is the right evidence.
    """
    out = []
    for f in q.figures:
        if f.part.startswith("option"):
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
    crop. `storage_path` is a BARE FILENAME (SS8), named
    SCHOOL_LEVEL_PAPER_Qn_SLOT_YEAR.png.
    """
    kinds = figure_kinds(q)
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


def _subs(q, plan, fractions, frac_fmt, block, drop) -> list:
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
    """
    kinds = figure_kinds(q)
    # `plan is None` means "unknown, assume all placed"; an EMPTY plan means
    # nothing is placed. Conflating the two is what left Q12's dropped figure
    # still printing a div.fig after the asset itself was gone.
    placed = (None if plan is None
              else {p["index"] for p in plan if p["kind"] == "block"})
    fracs = list(fractions or [])
    out = []
    for i, k in enumerate(kinds):
        if k == "option":
            continue
        if k == "frac":
            n, d = fracs.pop(0) if fracs else ("", "")
            out.append(frac_fmt(n, d))
        elif placed is not None and i not in placed:
            out.append(drop)
        else:
            out.append(block)
    return out


def content_html(q, plan=None, fractions=None) -> str:
    """Render the question.

    `fractions` is [(num, den), ...] for this question's Equation objects, in
    document order, read from the Word PDF by question_figures.read_fraction.
    Without it the fraction is emitted as an empty `span.frac`, which is
    visibly wrong rather than quietly wrong.
    """
    kinds = figure_kinds(q)
    state = {"subs": iter(_subs(q, plan, fractions, _frac, FIG_DIV, ""))}

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
    letters = sorted(q.options)
    fig_letters = {f.part.split(":", 1)[1] for f in q.figures
                   if f.part.startswith("option:")}
    captioned = bool(letters) and set(letters) <= fig_letters and all(
        len(_strip_tags("".join(q.options[L]))) <= 40 for L in letters)
    if captioned:
        letters = []
    if letters and any(_strip_tags("".join(v)) for v in q.options.values()):
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
            tds = "".join("<td>%s</td>" % _inline(v) for v in vals)
            trs.append('<tr><td class="ol">%s</td>%s</tr>' % (L, tds))
        parts.append('<table class="opts-table">%s</table>' % "".join(trs))
    return _stack_adjacent("\n".join(parts))


def _strip_hdr(h: str) -> str:
    return h.replace(CENTRE, "").replace("\n", " ").strip()


def _inline(v: str) -> str:
    return v.replace(CENTRE, "").replace(FIG_SENTINEL, "").replace("\n", " ").strip()


def content_text(q, fractions=None) -> str:
    """Plain text for search. MUST be non-null -- see the module docstring."""
    subs = iter(_subs(q, None, fractions,
                      lambda n, d: "(%s)/(%s) " % (n, d), " ", " "))
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
    for L in sorted(q.options):
        val = " | ".join(_strip_tags(v) for v in q.options[L])
        bits.append("%s %s" % (L, val) if val else L)
    return re.sub(r"\s+", " ", " ".join(b for b in bits if b)).strip()


def options_json(q) -> dict:
    """{'A': 'text', ...} -- feeds chem_search_doc, so plain text only."""
    out = {}
    for L in sorted(q.options):
        txt = " | ".join(t for t in (_strip_tags(v) for v in q.options[L]) if t)
        if not txt and any(f.part == "option:" + L for f in q.figures):
            txt = "[structure %s]" % L
        out[L] = txt
    return out
