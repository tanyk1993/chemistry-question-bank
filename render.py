"""Emit `worked_solution` HTML in the bank's live house style.

Conventions here were read off REAL ROWS (VJC WA2 Q1 and Q3, live in Supabase),
not off the handoff note's summary of them. Where the two disagreed, the data won.

What WA2 uses that RI 2024 P2 does NOT need -- verified absent from the source,
so deliberately not emitted:
  ul.marks          RI's mark scheme has no mark-point breakdown
  p.mark-note       ... no examiner notes (zero coloured runs carrying text)
  span.note         ... ditto
  span.mk           ... zero "[n]" mark allocations anywhere in the document
Emitting empty versions of these would be inventing structure the source does
not have.

One deliberate divergence from WA2, agreed with the user:
  WA2 splits <span class="ans"> at Word RUN boundaries, producing e.g. twelve
  spans for one electron configuration (and one span holding 87 spaces). That
  contradicts handoff SS7's "coalesce adjacent identical inline tags". We
  coalesce. The rendered result is identical -- nested same-class spans collapse
  visually -- but the stored HTML is ~40% smaller and reviewable by eye.
"""
from __future__ import annotations

import re

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"


def slot_for(label: str, ordinal_within_part: int = 0) -> str:
    """'(c)(ii)' -> 'ans-cii'   (second figure in the same part -> 'ans-cii2')

    Naming follows RI P2's own question-side house style (no parens, no dashes:
    'cii', 'di', 'di2'), prefixed 'ans-' so the frontend's
    isAnswerSlot = /^(ans|sol)[-_]/i holds it back until the answer is revealed.

    NOTE this differs from WA2's answer slots ('ans-a-iii', with dashes). The two
    precedents genuinely conflict; the user chose within-paper consistency, since
    that is what you see scanning the storage bucket. Recorded here so it is not
    relitigated next session.
    """
    bare = re.sub(r"[()]", "", label)
    suffix = "" if ordinal_within_part == 0 else str(ordinal_within_part + 1)
    return f"ans-{bare}{suffix}"


def asset_filename(school: str, level: str, paper: str, qnum: int,
                   slot: str, year: int) -> str:
    """RI_H2_P2_Q3_ans-cii_2024.png -- schema SS8's documented convention."""
    return f"{school}_{level}_{paper}_Q{qnum}_{slot}_{year}.png"


def _wrap_answer(html: str) -> str:
    """Wrap a paragraph's content in span.ans, leaving figures outside it.

    span.ans carries the answer colour. A figure is not prose and WA2 does not
    put <img> inside it, so a paragraph that is only a figure stays bare.
    """
    if not html.strip():
        return ""
    if html.strip().startswith("<img") and html.count("<img") == 1 \
            and re.fullmatch(r"\s*<img[^>]*>\s*", html):
        return html.strip()
    return '<span class="ans">%s</span>' % html


def part_html(part, filenames: list[str]) -> str:
    """Render one Part to `div.part`.

    `filenames` are this part's answer-figure filenames, in document order.
    """
    body = part.html
    # Resolve figure sentinels positionally, in the order they appear.
    it = iter(filenames)

    def _sub(_m):
        try:
            fn = next(it)
        except StopIteration:
            # More placeholders than files: never silently swallow one.
            raise ValueError("figure placeholder without a file in %s"
                             % part.full_label)
        return '<img class="ws-fig" data-asset="%s" alt="">' % fn

    body = re.sub(re.escape(FIG), _sub, body)
    leftover = list(it)
    if leftover:
        raise ValueError("unplaced figures in %s: %s" % (part.full_label, leftover))

    paras = [ln for ln in body.split("\n") if ln.strip()]
    rendered = []
    for p in paras:
        wrapped = _wrap_answer(p)
        if wrapped:
            rendered.append("<p>%s</p>" % wrapped)
    inner = "\n".join(rendered) if rendered else ""

    return ('<div class="part"><div class="lab">%s</div>'
            '<div class="body">%s</div></div>' % (part.label, inner))


def question_html(parts, files_by_part: dict) -> str:
    """Assemble one question's full `worked_solution` column value."""
    blocks = [part_html(p, files_by_part.get(p.full_label, [])) for p in parts]
    return '<div class="worked-solution">\n%s\n</div>' % "\n".join(blocks)


def part_html_grouped(part, names_per_reference: list[str]) -> str:
    """Like part_html, but `names_per_reference` has ONE entry per figure
    reference, with composite members repeating the same filename.

    A chart with three construction lines drawn over it is four references and
    one picture. Emitting four <img> tags would mint three phantom assets and
    shift every later ordinal; silently dropping the extras would hide a
    miscount. Repeating the name makes the intent explicit and lets us collapse
    runs of it deterministically.
    """
    it = iter(names_per_reference)
    emitted: list[str] = []

    def _sub(_m):
        try:
            fn = next(it)
        except StopIteration:
            raise ValueError("figure placeholder without a file in %s"
                             % part.full_label)
        if emitted and emitted[-1] == fn:
            return ""          # same composite picture, already emitted
        emitted.append(fn)
        return '<img class="ws-fig" data-asset="%s" alt="">' % fn

    body = re.sub(re.escape(FIG), _sub, part.html)
    leftover = list(it)
    if leftover:
        raise ValueError("unplaced figures in %s: %s" % (part.full_label, leftover))

    paras = [ln for ln in body.split("\n") if ln.strip()]
    rendered = []
    for para in paras:
        centred = para.startswith(CENTRE)
        para = para.replace(CENTRE, "")
        inner = _wrap_answer(para)
        if not inner:
            continue
        # .ws p.c is styled in the live index.html, so centring survives into
        # the app. A .figcap would NOT -- that rule is scoped to .stem only.
        rendered.append('<p class="c">%s</p>' % inner if centred
                        else "<p>%s</p>" % inner)
    return ('<div class="part"><div class="lab">%s</div>'
            '<div class="body">%s</div></div>'
            % (part.label, "\n".join(rendered)))


def question_html_grouped(parts, names_by_part: dict) -> str:
    blocks = [part_html_grouped(p, names_by_part.get(p.full_label, []))
              for p in parts]
    return '<div class="worked-solution">\n%s\n</div>' % "\n".join(blocks)
