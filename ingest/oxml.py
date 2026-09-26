"""Word run/paragraph -> inline HTML, including OMML maths.

Design notes worth keeping:

* Everything is built as a list of (text, style) tokens and only turned into
  tags at the very end. That is what makes coalescing free -- Word splits a
  single phrase across many runs, and emitting tags per run produces the
  `<i>Data</i> <i>Booklet</i>` and 12-span-electron-configuration noise seen in
  WA2's stored markup. Handoff SS7 asks for coalescing; doing it structurally
  rather than with a post-hoc regex means it cannot be forgotten.

* Unknown constructs RAISE. A silently skipped OMML fraction is precisely the
  failure LibreOffice exhibits on this document (it drops every one), and it is
  invisible in the rendered output. Loud failure is the whole point.
"""
from __future__ import annotations

from lxml import etree

from .symbols import sym_to_text

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W, "m": M}
Wq = "{%s}" % W
Mq = "{%s}" % M


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Style(frozenset):
    """An immutable set of inline marks: 'b', 'i', 'u', 'sup', 'sub', 'el',
    'sr'."""

    ORDER = ("b", "i", "el", "sr", "u", "sup", "sub")
    TAG = {"b": "b", "i": "i", "u": "u", "sup": "sup", "sub": "sub",
           "el": 'i class="el"', "sr": 'span class="sr"'}

    def open_tags(self) -> str:
        return "".join("<%s>" % self.TAG[m] for m in self.ORDER if m in self)

    def close_tags(self) -> str:
        return "".join("</%s>" % self.TAG[m].split()[0]
                       for m in reversed(self.ORDER) if m in self)


EMPTY = Style()


def _run_style(r) -> Style:
    pr = r.find(Wq + "rPr")
    marks = set()
    if pr is not None:
        for tag, mark in (("b", "b"), ("i", "i"), ("u", "u")):
            el = pr.find(Wq + tag)
            # <w:b/> means on; <w:b w:val="0"/> means off.
            if el is not None and (el.get(Wq + "val") not in ("0", "false")):
                marks.add(mark)
        va = pr.find(Wq + "vertAlign")
        if va is not None:
            v = va.get(Wq + "val")
            if v == "superscript":
                marks.add("sup")
            elif v == "subscript":
                marks.add("sub")
        # A run the DOCUMENT explicitly sets in Times New Roman. Until now
        # <w:rFonts> was not read at all, so this override was dropped for
        # every adapter -- and it is load-bearing: in the body sans face a
        # capital I is a bare vertical stroke, so an oxidation state's "II"
        # reads as "ll" or "||". Word is doing here exactly what the `el`
        # mark below does for the element symbol l.
        #
        # On RI 2024 H2 P3 this fires on 9 runs out of 1898, and every one is
        # an oxidation-state Roman numeral -- copper(II), lead(II), Cu(I) --
        # with nothing else in the paper carrying the override. That is why
        # it is safe to key on the font at all: if Word had scattered TNR
        # through ordinary prose (which Word does do), this would wrap half
        # the paper in serif spans and a narrower rule would be needed.
        # CHECK THAT DISTRIBUTION ON A NEW PAPER before trusting this.
        #
        # Keyed on the font the document NAMES, never on a text pattern like
        # r"\((I|V|X)+\)": the document is the authority on its own
        # formatting, and a pattern would both miss cases and invent them.
        rf = pr.find(Wq + "rFonts")
        if rf is not None and "Times New Roman" in (
                (rf.get(Wq + "ascii") or "") + "|"
                + (rf.get(Wq + "hAnsi") or "")):
            marks.add("sr")
    return Style(marks)


def _symbol_font(r) -> str | None:
    """The run's Symbol/Wingdings/MT Extra font name, or None.

    Word can put a symbol glyph on the page two completely different ways
    that look identical on screen: an explicit <w:sym w:font="Symbol"
    w:char="F044"/> element (decoded by sym_to_text below), or by typing an
    ORDINARY character while the run's own font happens to be set to one of
    these symbol fonts -- which stores the literal character ("D") but
    DISPLAYS as that font's private-encoding glyph for it (Delta). Nothing
    before EJC 2024 H2 P1 needed the second form, so plain <w:t> text was
    always read as-is; Q29's two free-energy deltas ("the DG of the
    reaction") are typed exactly this way, confirmed against the doc's raw
    XML (a literal "D" inside a run whose w:rFonts ascii is "Symbol").
    """
    pr = r.find(Wq + "rPr")
    if pr is None:
        return None
    rf = pr.find(Wq + "rFonts")
    if rf is None:
        return None
    name = ((rf.get(Wq + "ascii") or rf.get(Wq + "hAnsi") or "")
            .strip().lower())
    return name if name in ("symbol", "wingdings", "mt extra") else None


def _tokens_from_run(r, *, in_math: bool = False):
    """Yield (text, Style) for one w:r / m:r."""
    style = _run_style(r)
    font = _symbol_font(r)
    parts = []
    for ch in r:
        ln = etree.QName(ch).localname
        if ln in ("t",):
            txt = ch.text or ""
            if font:
                # Route through the SAME table <w:sym> uses, one character at
                # a time: the run's raw text IS the symbol-font codepoint, in
                # the same F0xx private-use range Word offsets w:sym into.
                txt = "".join(
                    sym_to_text(font, "%04X" % (0xF000 | ord(c))) for c in txt)
            parts.append(txt)
        elif ln == "sym":
            parts.append(sym_to_text(ch.get(Wq + "font"), ch.get(Wq + "char")))
        elif ln == "tab":
            # A literal TAB character, not a space: unlike a space, nobody
            # types a tab by accident, so its presence is always a deliberate
            # Word tab-stop -- EJC 2024 H2 P1's "reaction 1  <equation>"/
            # "<equation>  E<sup>-o-</sup> = ..." lines (Q8, Q10, Q29) use one
            # to line up a trailing label in its own column, the same way
            # RI 2024 H2 P3's "equation N" lines do with literal repeated
            # spaces (see style-guide.md's `.eqn` convention). Kept distinct
            # from an ordinary space here so the paragraph-building layer
            # (render_questions.py's _para) can detect it structurally and
            # tag the paragraph `eqn`, rather than guessing from a text
            # pattern that would miss Q29 (a bare equation, no "reaction N"
            # label at all). content_text/options collapse \s+ to one space
            # regardless, so search/the text gate see no difference.
            parts.append("\t")
        elif ln == "br":
            # SS7: a w:br mid-sentence is a layout line-wrap, not a paragraph
            # break. Represented as a sentinel and resolved by the caller.
            parts.append("\x00BR\x00")
        elif ln in ("drawing", "object", "pict"):
            parts.append("\x00FIG\x00")
        elif ln == "AlternateContent":
            # Word wraps native shape drawings as Choice(<w:drawing> with real
            # shapes) + Fallback(<w:pict> VML stand-in). Both describe ONE
            # figure; counting both would shift every subsequent asset ordinal
            # and silently rotate the figures (handoff SS7's costliest defect).
            parts.append("\x00FIG\x00")
        elif ln in ("rPr", "lastRenderedPageBreak", "noBreakHyphen",
                    "softHyphen", "commentReference", "annotationRef",
                    "footnoteReference", "endnoteReference", "fldChar",
                    "instrText", "delText", "cr"):
            if ln == "noBreakHyphen":
                parts.append("‑")   # SS7 defect SS9: dropped -> "nitrogencontaining"
            elif ln == "cr":
                parts.append("\x00BR\x00")
            # everything else here is deliberately non-rendering
        else:
            raise ValueError("unhandled run child <%s>" % ln)
    text = "".join(parts)
    if not text:
        return

    # EJC 2024 H2 P2 types the standard-state ("plimsoll") symbol as a bare
    # LATIN CAPITAL LETTER O WITH LONG STROKE OVERLAY (U+A74A) in an ordinary
    # Arial run, not via OMML math (contrast the sSubSup handling above,
    # which is what OTHER papers' equation-editor "plimsoll above" objects
    # go through). Confirmed against the reference PDF's OWN text layer --
    # it contains the identical U+A74A codepoint at the same spot, so this
    # is genuinely what the source document encodes, not a misread on our
    # part; it just does not carry the sub/superscript formatting a reader
    # needs to recognise it, and U+A74A does not display as a standard-state
    # symbol in a normal web font. Substituted for the actual Unicode
    # standard-state character, raised the way every other run: ΔHꝊ,
    # EꝊ, GꝊ (Q3(a)(ii), (d)(i)-(iii)) all being ONE bare run confirms this
    # is always a full run on its own, never mixed with other text.
    if text == "Ꝋ":
        yield "<sup>⦵</sup>", EMPTY, True
        return

    # SS7 / defect SS2: a run whose entire content is the element symbol l gets the
    # serif face, so "AlCl3" does not read as "AICI3". Everything else italic
    # (Data Booklet, k, Ea) stays in the body face.
    #
    # This is a TEXT-pattern guess, unlike the `sr` mark above, which reads the
    # document's own font override. The two may well be the same phenomenon --
    # Word may set these l runs in Times New Roman too, which would make this
    # hack redundant. NOT ESTABLISHED: RI 2024 H2 P3 contains no `l` runs at
    # all, so it could not settle the question either way. Do not remove this
    # on the assumption that `sr` covers it without checking a paper that
    # actually has one.
    if text.strip() == "l":
        style = Style((style - {"i"}) | {"el"})
    yield text, style, False


# --------------------------------------------------------------------------
# OMML
# --------------------------------------------------------------------------

def _omml_tokens(el):
    """Flatten an OMML subtree into (text, Style) tokens.

    Only the constructs actually present are implemented; anything else raises
    so it gets looked at rather than dropped.
    """
    ln = etree.QName(el).localname

    if ln == "r":
        yield from _tokens_from_run(el, in_math=True)
        return

    if ln in ("oMath", "oMathPara", "num", "den", "e", "sup", "sub", "deg"):
        for ch in el:
            if etree.QName(ch).localname.endswith("Pr"):
                continue
            yield from _omml_tokens(ch)
        return

    if ln == "f":                                   # fraction
        num = el.find(Mq + "num")
        den = el.find(Mq + "den")
        yield '<span class="frac"><span class="fnum">', EMPTY, True
        if num is not None:
            yield from _omml_tokens(num)
        yield '</span><span class="fden">', EMPTY, True
        if den is not None:
            yield from _omml_tokens(den)
        yield "</span></span>", EMPTY, True
        return

    if ln in ("sSub", "sSup", "sSubSup"):
        base = el.find(Mq + "e")
        if base is not None:
            yield from _omml_tokens(base)
        sub = el.find(Mq + "sub")
        sup = el.find(Mq + "sup")
        if ln == "sSubSup" and sub is not None and sup is not None:
            # BOTH at once stack, they do not queue: E-standard-state-cell is
            # the plimsoll above and "cell" below, sharing one slot after the E.
            # Run in sequence they read as "E to the power of plimsoll, then
            # subscript cell", which is a different symbol.
            yield '<span class="stk post"><span>', EMPTY, True
            yield from _omml_tokens(sup)
            yield '</span><span>', EMPTY, True
            yield from _omml_tokens(sub)
            yield "</span></span>", EMPTY, True
            return
        for node, mark in ((sub, "sub"), (sup, "sup")):
            if node is None:
                continue
            for text, style, raw in _omml_tokens(node):
                yield text, Style(set(style) | {mark}), raw
        return

    if ln == "sPre":                                # PRE-sub/superscript
        # NUCLIDE NOTATION. The mass and atomic numbers sit one ABOVE the other
        # in front of the symbol. Emitting <sup>234</sup><sub>90</sub> puts them
        # side by side instead, which reads as a different quantity -- 234 then
        # 90 rather than 234-over-90 -- so they are stacked, using the same
        # inline-flex column the house `.frac` markup already uses.
        yield '<span class="stk"><span>', EMPTY, True
        sup = el.find(Mq + "sup")
        if sup is not None:
            yield from _omml_tokens(sup)
        yield '</span><span>', EMPTY, True
        sub = el.find(Mq + "sub")
        if sub is not None:
            yield from _omml_tokens(sub)
        yield "</span></span>", EMPTY, True
        base = el.find(Mq + "e")
        if base is not None:
            yield from _omml_tokens(base)
        return

    if ln == "d":                                   # delimiter
        # SS7 / defect SS13: the REAL delimiters live in m:begChr/m:endChr.
        # Hard-coding round brackets turns [.OH] into (.OH), which is a
        # different chemical species.
        pr = el.find(Mq + "dPr")
        beg, end = "(", ")"
        if pr is not None:
            b = pr.find(Mq + "begChr")
            e = pr.find(Mq + "endChr")
            if b is not None:
                beg = b.get(Mq + "val", "")
            if e is not None:
                end = e.get(Mq + "val", "")
        yield beg, EMPTY, False
        for ch in el.findall(Mq + "e"):
            yield from _omml_tokens(ch)
        yield end, EMPTY, False
        return

    if ln == "rad":                                 # radical
        deg = el.find(Mq + "deg")
        e = el.find(Mq + "e")
        yield "√", EMPTY, False
        if deg is not None and len(deg):
            yield from _omml_tokens(deg)
        yield "<span style=\"text-decoration:overline\">", EMPTY, True
        if e is not None:
            yield from _omml_tokens(e)
        yield "</span>", EMPTY, True
        return

    if ln == "nary":                                # summation / integral
        chr_el = el.find(Mq + "naryPr/" + Mq + "chr")
        yield (chr_el.get(Mq + "val") if chr_el is not None else "∑"), EMPTY, False
        for tag in ("sub", "sup", "e"):
            node = el.find(Mq + tag)
            if node is None:
                continue
            mark = {"sub": "sub", "sup": "sup"}.get(tag)
            for text, style, raw in _omml_tokens(node):
                yield text, (Style(set(style) | {mark}) if mark else style), raw
        return

    if ln.endswith("Pr") or ln in ("ctrlPr",):
        return

    raise ValueError("unhandled OMML element <m:%s>" % ln)


# --------------------------------------------------------------------------
# paragraph assembly
# --------------------------------------------------------------------------

def _combine_group_id(r):
    """The run's `w:eastAsianLayout` combine-characters group id, or None.

    Word's "Combine Characters" feature stacks up to ~6 characters into two
    half-height lines sharing one normal character's width -- EJC 2024 H2 P2
    uses it as a compact ion-charge notation (see `_flush_combine` below),
    typing e.g. "-3" this way right after "HCO" instead of using real
    sub/superscript runs.
    """
    pr = r.find(Wq + "rPr")
    if pr is None:
        return None
    eal = pr.find(Wq + "eastAsianLayout")
    if eal is None or eal.get(Wq + "combine") != "1":
        return None
    return eal.get(Wq + "id")


def _combine_run_text(r) -> str:
    """A combine-flagged run's bare `<w:t>` text, for grouping only.

    Every combine run actually seen is a single plain `w:t` (never a tab,
    symbol, drawing, ...), so this does not need `_tokens_from_run`'s full
    child-element handling.
    """
    t = r.find(Wq + "t")
    return t.text or "" if t is not None else ""


def paragraph_tokens(p):
    """Yield (text, Style) for a w:p, descending into any OMML."""
    pending: list = []
    pending_id = None

    def _flush_combine():
        nonlocal pending, pending_id
        if not pending:
            return []
        runs, pending, pending_id = pending, [], None
        text = "".join(_combine_run_text(r) for r in runs)
        # A SECOND, unrelated use of this same combine id: the standard-state
        # ("plimsoll") symbol (U+A74A, substituted below -- see
        # _tokens_from_run's own comment on the bare-run case) stacked over a
        # variable-length subscript label -- confirmed against the reference
        # PDF's own rendered page image (Q3(a)(ii)'s Table 3.1 and its two
        # "reaction 1" equation labels): the symbol sits raised, the label
        # sits lowered directly beneath it, at every length seen in this
        # document from "f" (1 char) to "reaction 1" (10 chars, shrunk to
        # fit) -- NOT the fixed-width two-row squeeze the ION-CHARGE notation
        # below uses. An EARLIER pass at this treated every one of these as
        # "a much longer run of text sharing one combine id is a coincidental
        # or vestigial tag... not a real combine" and let it fall through to
        # plain sequential text -- which is what let the standard-state
        # symbol itself through (its own bare-run special case still fired)
        # but silently dropped "at"/"sublimation"/"f"/"reaction 1" as
        # ordinary baseline text instead of subscript (found from the user's
        # own comparison against the source paper, 2026-09-26, after the
        # symbol itself had already been fixed). Splits cleanly on the
        # symbol -- confirmed on all 5 such groups in this document -- so
        # length is irrelevant here; only the ION notation below needs a
        # length check, because it has no fixed anchor character to split on.
        if "Ꝋ" in text:
            before, _, after = text.partition("Ꝋ")
            before, after = before.strip(), after.strip()
            html = (_esc(before) if before else "") + "<sup>⦵</sup>"
            if after:
                html += "<sub>%s</sub>" % _esc(after)
            return [(html, EMPTY, True)]
        # Word's real combine limit for the ION-CHARGE notation is a handful
        # of characters split into a TOP line and a BOTTOM line (the first
        # ceil(n/2) chars on top). A much longer run of text sharing one
        # combine id, with no standard-state symbol in it, is a coincidental
        # or vestigial tag, not a real combine -- rendered as ordinary
        # sequential text instead.
        if text and len(text) <= 3:
            top_n = -(-len(text) // 2)          # ceil(len/2)
            top, bottom = text[:top_n], text[top_n:]
            # Chemistry reads number-then-charge left to right (HCO3-, not
            # -3HCO). Word stacks the group TOP/BOTTOM instead, first-typed
            # on top -- confirmed against this document's own combine text
            # ("2-4" for CrO4(2-), "-3" for HCO3-/ClO3-, "-4" for ClO4-):
            # the BOTTOM half is always the subscript count, the TOP half
            # the superscript charge.
            return [("<sub>%s</sub><sup>%s</sup>" % (_esc(bottom), _esc(top)),
                     EMPTY, True)]
        out = []
        for r in runs:
            out.extend(_tokens_from_run(r))
        return out

    for child in p:
        ln = etree.QName(child).localname
        if ln == "r":
            cid = _combine_group_id(child)
            if cid is not None:
                if pending and pending_id != cid:
                    yield from _flush_combine()
                pending.append(child)
                pending_id = cid
                continue
            yield from _flush_combine()
            yield from _tokens_from_run(child)
        elif ln in ("oMath", "oMathPara"):
            yield from _flush_combine()
            yield from _omml_tokens(child)
        elif ln in ("hyperlink", "smartTag", "sdt", "ins"):
            yield from _flush_combine()
            for sub in child.iter():
                if etree.QName(sub).localname == "r" and sub.getparent() is child:
                    yield from _tokens_from_run(sub)
        elif ln in ("pPr", "bookmarkStart", "bookmarkEnd", "proofErr",
                    "commentRangeStart", "commentRangeEnd", "del"):
            continue
        elif ln in ("subDoc",):
            continue
        else:
            yield from _flush_combine()
            # Unknown block-level child: surface it rather than dropping it.
            raise ValueError("unhandled paragraph child <w:%s>" % ln)
    yield from _flush_combine()


def tokens_to_html(tokens) -> str:
    """Coalesce adjacent same-style tokens, then emit HTML."""
    merged: list[list] = []
    for text, style, raw in tokens:
        if merged and merged[-1][1] == style and merged[-1][2] == raw:
            merged[-1][0] += text
        else:
            merged.append([text, style, raw])

    out = []
    for text, style, raw in merged:
        if not text:
            continue
        piece = text if raw else _esc(text)
        out.append(style.open_tags() + piece + style.close_tags())
    html = "".join(out)
    # collapse whitespace but keep single spaces meaningful
    html = html.replace("\x00BR\x00", "<br>")
    return html


CENTRE = "\x00C\x00"


def paragraph_is_centred(p) -> bool:
    """w:jc=center ONLY.

    Handoff SS7: Word's 'distribute'/'both' is JUSTIFICATION (it is what dotted
    answer lines use), not centring. Treating it as centring would centre most
    of the document.
    """
    jc = p.find(Wq + "pPr/" + Wq + "jc")
    return jc is not None and jc.get(Wq + "val") == "center"


def paragraph_html(p) -> str:
    html = tokens_to_html(paragraph_tokens(p))
    if html.strip() and paragraph_is_centred(p):
        return CENTRE + html
    return html


def paragraph_numid(p) -> int | None:
    """This paragraph's `w:numPr/w:numId` value, or None if it isn't a list
    item at all.

    Reads the PARAGRAPH's own declaration only -- resolving it against a
    style's inherited numbering is not needed by any paper seen so far, and
    would risk inventing list membership a paragraph never actually states.

    Returns an int (not the raw XML string) so it compares directly against
    `load_numid_formats`'s int-keyed dict below -- merged from two
    independently-written copies of this function (RI 2024 H2 P3's origin
    commit kept the numId as a string; EJC 2024 H2 P2's local copy, which
    `parts_flow.py` also depends on, casts to int). Every caller in this
    codebase only ever does membership/dict-key checks, never string
    formatting, on the result, so standardising on int here is safe for
    both.
    """
    numid = p.find(Wq + "pPr/" + Wq + "numPr/" + Wq + "numId")
    if numid is None:
        return None
    val = numid.get(Wq + "val")
    return int(val) if val is not None else None


def load_numid_formats(numbering_xml) -> dict:
    """{numId: ilvl-0 w:numFmt value} for every numId in this document's
    numbering part -- "bullet", "decimal", "lowerLetter", "lowerRoman", etc.

    Shared groundwork for `load_bullet_numids` (below) and for
    `parts_flow.py`'s own auto-numbered-letter recovery: both need to know
    what KIND of list a numId renders as, not just whether it is a bullet.

    `numbering_xml=None` (a paper with no numbering part at all) returns an
    empty dict rather than raising -- RI 2024 H2 P3's own copy of this
    guard, absorbed here since `load_bullet_numids` is now built on top of
    this function instead of duplicating the two-hop lookup itself.
    """
    if numbering_xml is None:
        return {}
    tree = etree.parse(str(numbering_xml))
    root = tree.getroot()

    fmt_by_abstract = {}
    for absnum in root.findall(Wq + "abstractNum"):
        abs_id = absnum.get(Wq + "abstractNumId")
        lvl0 = absnum.find(Wq + "lvl[@" + Wq + "ilvl='0']")
        if lvl0 is None:
            continue
        numfmt = lvl0.find(Wq + "numFmt")
        if numfmt is not None:
            fmt_by_abstract[abs_id] = numfmt.get(Wq + "val")

    formats = {}
    for num in root.findall(Wq + "num"):
        num_id = num.get(Wq + "numId")
        absid_el = num.find(Wq + "abstractNumId")
        if absid_el is None or num_id is None:
            continue
        abs_id = absid_el.get(Wq + "val")
        fmt = fmt_by_abstract.get(abs_id)
        if fmt is not None:
            formats[int(num_id)] = fmt
    return formats


def load_bullet_numids(numbering_xml) -> set:
    """numId -> set, for every numId whose ilvl-0 `w:numFmt` is "bullet".

    Word's bullet GLYPH is generated from this part at render time and is
    never written into a run as literal text (`paragraph_tokens` explicitly
    skips `w:pPr`, which is where `w:numPr` lives), so a bulleted list is
    otherwise invisible to this module entirely.

    Deliberately excludes non-bullet formats (decimal, letter, roman) rather
    than treating every numPr paragraph the same -- a genuinely NUMBERED list
    whose numbers carry meaning ("step 1", "step 2"...) must keep rendering as
    plain paragraphs (visibly wrong in a preview, and so caught) rather than
    being silently mislabelled as an unordered list. Only ilvl 0 is read
    (every numPr list surveyed so far, across both RI 2024 H2 P3 and EJC
    2024 H2 P2, is single-level); re-survey and extend the caller if a
    future paper nests one.
    """
    return {nid for nid, fmt in load_numid_formats(numbering_xml).items()
            if fmt == "bullet"}
