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


def _tokens_from_run(r, *, in_math: bool = False):
    """Yield (text, Style) for one w:r / m:r."""
    style = _run_style(r)
    parts = []
    for ch in r:
        ln = etree.QName(ch).localname
        if ln in ("t",):
            parts.append(ch.text or "")
        elif ln == "sym":
            parts.append(sym_to_text(ch.get(Wq + "font"), ch.get(Wq + "char")))
        elif ln == "tab":
            parts.append(" ")
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

def paragraph_tokens(p):
    """Yield (text, Style) for a w:p, descending into any OMML."""
    for child in p:
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
                    "commentRangeStart", "commentRangeEnd", "del"):
            continue
        elif ln in ("subDoc",):
            continue
        else:
            # Unknown block-level child: surface it rather than dropping it.
            raise ValueError("unhandled paragraph child <w:%s>" % ln)


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
