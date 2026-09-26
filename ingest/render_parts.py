"""House markup for a STRUCTURED (P2/P3) question, from `parts.parse`.

The frontend contract is handoff SS7's, unchanged, and shared with
`render_questions.py`:

  BLOCK   `div.fig` placeholders, collected in DOM order and filled from the
          question's assets sorted by ORDINAL.
  INLINE  `img[data-asset="FILE.png"]`, matched by filename.

Every figure in this family is alone in its own paragraph, so they are all
block placeholders. That makes the ordinal rule easy to satisfy and easy to
check: one placeholder per owner, one asset per owner, same order.

Part markup follows what RI P2's live rows already use, and what index.html's
CSS is written against:

    <div class="qpart"><span class="pl">(a)(ii)</span> text <span
    class="mk">[2]</span></div>

The "[n]" badge is written by `parts.py`, IN PLACE, at the exact point in the
source where the paper prints the allocation -- not synthesized here and
appended after everything in the part. An earlier version of this module did
that (always tacking `<span class="mk">` onto the very end of `inner`,
regardless of how many paragraphs or tables followed), which is wrong
whenever the paper prints "[n]" mid-part: RI 2024 H2 P3's Q2(b)(i) prints its
"[1]" right after "...stating its units.", then two more paragraphs and a
table that are actually shared intro text for part (ii) -- so the trailing
badge sat below that table, visibly detached from the sentence it belongs
to, and a plain single-paragraph part with no trailing blocks had the
opposite problem once a CSS fix pinned the trailing badge to the part's
TOP-right corner to solve the table case: the badge then sat beside the
FIRST line of a wrapped paragraph instead of its last. Writing the badge
where the paper itself prints it, once, avoids needing a position rule that
guesses at a single "correct" corner for every shape of part.

RECONCILING THE DOCX AGAINST THE PRINTED PAGE
---------------------------------------------
`parts.py` reports one figure per drawing Word stores. The page prints fewer:
a chart with shapes drawn over it is one picture, and so is a PNG with its
curves overlaid (see `parts_figures.py`, which establishes the printed count
from the PDF). The html therefore has to be collapsed to one placeholder per
owner before it can be zipped to one asset per owner -- otherwise the
placeholder loop runs off the end of the asset list and every later figure in
the question shifts, which handoff SS7 records as this pipeline's costliest
defect class.
"""
from __future__ import annotations

import re

from .oxml import CENTRE
from .parts import CAPTION_RE, FIG_SENTINEL

FIG_DIV = '<div class="fig">figure</div>'

#: A table whose every cell is empty. RI draws 5(d)'s energy-level diagram
#: over a borderless Word table used purely as a positioning grid; the shapes
#: are the picture and the table is scaffolding, so it renders as an empty
#: 30-cell grid in the app. Two of this paper's six tables are this.
_EMPTY_TABLE_RE = re.compile(
    r"<table class=\"qt\">(?:\s*<tr>(?:\s*<td>\s*</td>)*\s*</tr>)+\s*</table>")


def _strip(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s.replace(CENTRE, "")
                  .replace(FIG_SENTINEL, "")).strip()


def reconcile(html: str) -> str:
    """Collapse ADJACENT duplicate figure placeholders, keep DISTINCT ones,
    and tidy up. Three things, the first now shape-aware:

      1. Several placeholders for the SAME printed picture -> keep the FIRST
         and drop the rest. First, not last, because the paper prints the
         picture where the picture starts; RI 2024 H2 P3's 1(c) has a
         trailing pair that belongs to a duplicate chart insertion sitting
         hidden behind the real one. "Same picture" is decided the way
         style-guide.md SS5 says every multi-figure owner is decided: by
         ADJACENCY in the rendered text, never by "same owner" alone -- a
         sentinel is a duplicate only if NO real content (prose beyond a
         repeated caption) has appeared since the last one KEPT. EJC 2024 H2
         P3's 1(c)(ii), 2(b) and 5(b) each print TWO genuinely distinct
         drawings under one part/owner, with a real sentence between them
         ("The student then changed M to Q...", "3-bromomandelic acid can be
         formed from benzaldehyde in 3 steps.") -- collapsing those to one
         placeholder would silently lose the second figure and shift every
         later asset in the question, exactly the SS7 defect class this
         module exists to prevent. Both are kept, and `asset_plan()` below
         plans one asset per SURVIVING sentinel, not one per owner.
      2. A caption repeated verbatim -> keep one. Same duplicate-insertion
         case as (1); a caption does not itself count as "real content" for
         the adjacency test, so two distinct figures each captioned "Fig.
         X.Y" are unaffected by this rule.
      3. An all-empty layout table -> drop it.
    """
    lines = html.split("\n")
    out = []
    seen_any_fig = False
    content_since_last_fig = False
    last_caption = None
    for line in lines:
        centred = line.startswith(CENTRE)
        body = line[len(CENTRE):] if centred else line

        body = _EMPTY_TABLE_RE.sub("", body)
        has_fig = FIG_SENTINEL in body

        if has_fig:
            if seen_any_fig and not content_since_last_fig:
                # Adjacent to the last KEPT figure (nothing but maybe a
                # caption between them) -- the same duplicate-insertion
                # case (1) describes. Drop it.
                body = body.replace(FIG_SENTINEL, "")
                has_fig = False
            else:
                # First figure in this owner, or real content intervened
                # since the last one kept -- a genuinely distinct figure.
                seen_any_fig = True
                content_since_last_fig = False

        plain = _strip(body)
        if plain and CAPTION_RE.match(plain):
            if plain == last_caption:
                continue
            last_caption = plain
        elif plain:
            last_caption = None
            if not has_fig:
                content_since_last_fig = True

        if not plain and not has_fig:
            continue
        out.append((CENTRE if centred else "") + body)
    return "\n".join(out)


def slot_for(label: str | None, i: int = 0) -> str:
    """The asset slot for an owner's i-th (0-based) DISTINCT figure: 'intro'
    or the part label without its brackets ('c', 'ciii') for the first, with
    a numeric suffix for the 2nd+ ('intro2', 'ciii2') -- one owner CAN print
    more than one genuinely distinct picture (style-guide.md SS5; confirmed on
    EJC 2024 H2 P2 Q4 and EJC 2024 H2 P3's 1(c)(ii)/2(b)/5(b)). Bare and
    filename-safe, per handoff SS8."""
    base = "intro" if not label else label.replace("(", "").replace(")", "")
    return base if i == 0 else "%s%d" % (base, i + 1)


def asset_plan(q, school="RI", level="H2", paper="P3", year=2024,
               start_ordinal=1) -> list:
    """One asset per SURVIVING figure placeholder, in document order.

    Counted from the owner's html AFTER `reconcile()` has run (the caller
    always calls reconcile() first -- see extract_parts.py), not from the raw
    `.figures` list length: `reconcile()` may have collapsed adjacent
    duplicates (RI's case) or kept several distinct ones (EJC's), and the
    asset plan must match what `content_html()`/`_render_owner()` actually
    place, not what the docx originally stored. Ordinal order must equal DOM
    order of the placeholders, because that is how the frontend pairs them --
    both are built from the same walk here, so they cannot disagree.
    """
    plan = []
    n = start_ordinal
    owners = [(None, q.intro_html)]
    owners += [(p.label, p.html) for p in q.parts]
    for label, html in owners:
        n_figs = html.count(FIG_SENTINEL)
        if not n_figs:
            continue
        for i in range(n_figs):
            slot = slot_for(label, i)
            plan.append({
                "question": q.qnum,
                "part": label,
                "slot": slot,
                "ordinal": n,
                "storage_path": "%s_%s_%s_Q%d_%s_%d.png"
                                % (school, level, paper, q.qnum, slot, year),
                "n_refs": n_figs,
            })
            n += 1
    return plan


#: RI positions "equation 1" / "reaction 1" etc. with runs of literal spaces
#: (verified against the rendered page, not the docx's own centring: the
#: label sits at the SAME left indent as the surrounding stem text, then a
#: gap, then the formula, then -- for equation 1 only -- a further gap and a
#: trailing note). It is not full-line centring; browsers collapse the runs
#: to one space and the columns run together. `class="eqn"` (below, CSS in
#: index.html) preserves the whitespace instead of centring the line.
#: Scoped to this exact label shape so it cannot fire on unrelated body text
#: that happens to contain a double space.
EQN_LINE_RE = re.compile(r"^(?:equation|reaction)\s+\d+\s{2,}")


def _para(line: str) -> str:
    centred = line.startswith(CENTRE)
    body = line[len(CENTRE):] if centred else line
    # Already a block element from parts.py (a data table, or a <ul> grouped
    # from consecutive numPr paragraphs) -- pass through, don't wrap in <p>.
    if body.lstrip().startswith(("<table", "<ul")):
        return body
    classes = []
    if centred:
        classes.append("c")
    if EQN_LINE_RE.match(body):
        classes.append("eqn")
    cls = ' class="%s"' % " ".join(classes) if classes else ""
    return "<p%s>%s</p>" % (cls, body)


def _render_owner(html: str, lead_inline: bool) -> str:
    """Owner html -> block elements, figures as div.fig placeholders.

    `lead_inline` leaves the first paragraph unwrapped so a part's text
    continues the line its label sits on; <p> is a block box, so wrapping it
    would push the question text below the label. Later paragraphs are
    genuine blocks. A centred first line keeps its <p class="c">, because it
    cannot be centred inline.
    """
    out = []
    for line in html.split("\n"):
        if not line.strip():
            continue
        if FIG_SENTINEL in line:
            # Text can share the figure's line: 4(e) prints "BCA" and
            # "complex A" as captions UNDER its reaction equation, and they
            # arrive in the same paragraph as the drawing. Split on the
            # placeholder and emit the pieces in order -- the figure stays a
            # block, and its labels become the paragraph beneath it, which is
            # where the paper puts them.
            #
            # Fragments with no word character are dropped: 4(c)(iii) leaves a
            # bare ". " behind its drawing, and a paragraph containing one
            # full stop is noise, not content.
            centred = line.startswith(CENTRE)
            body = line[len(CENTRE):] if centred else line
            for i, piece in enumerate(body.split(FIG_SENTINEL)):
                if i:
                    out.append(FIG_DIV)
                if re.search(r"\w", _strip(piece)):
                    out.append(_para((CENTRE if centred else "")
                                     + piece.strip()))
            continue
        if lead_inline and not out and not line.startswith(CENTRE):
            out.append(line)
        else:
            out.append(_para(line))
    return "\n".join(out)


def content_html(q) -> str:
    """The question's stem markup: intro blocks, then one div.qpart each.

    The "[n]" mark badge is NOT synthesized here -- `parts.py` already wrote
    it, as `<span class="mk">`, in place inside `p.html` at the exact point
    the source paper prints it (see that module's INLINE_MARKS_HTML_RE for
    why: appending a badge here, always after everything else in the part,
    puts it in the wrong place whenever the paper prints "[n]" mid-part).
    """
    out = []
    if q.intro_html.strip():
        out.append(_render_owner(q.intro_html, lead_inline=False))
    for p in q.parts:
        inner = _render_owner(p.html, lead_inline=True) if p.html.strip() else ""
        out.append('<div class="qpart"><span class="pl">%s</span> %s</div>'
                   % (p.label, inner))
    return "\n".join(out)


def content_text(q) -> str:
    """Plain text for search and for the character gate.

    No separate "[n]" append here either, for the same reason: the badge is
    already literal text inside `p.html` (parts.py wrote it there), and
    `_strip(p.html)` keeps that text while only stripping the tags around
    it. Appending "[%d]" % p.marks here too would duplicate it -- the same
    "one value, one place" bug content_html() itself used to have (see its
    docstring), just on the text side instead of the html side.
    """
    bits = [_strip(q.intro_html)]
    for p in q.parts:
        bits.append(p.label)
        bits.append(_strip(p.html))
    if q.marks_total is not None:
        bits.append("[Total: %d]" % q.marks_total)
    return " ".join(b for b in bits if b)
