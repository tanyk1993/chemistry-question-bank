"""Extract worked solutions + answer key for the SEAB A Level 2024 H2 P1 (9729/01, MCQ),
from the COLLEGE (VJC) answers document.

Document shape (paragraph flow, like EJC 2024 P1): a title, a 6x10 key table (body index 2),
then every question is a run of ordinary paragraphs/tables opened by a header paragraph
"N<TAB>LETTER[ (1 only)]" (which is dropped: the letter goes to answer_key, the "(1 only)"
gloss is already in the question's own options). Question boundaries are those headers, which
must run 1..30 in order.

Key: read THREE independent ways and all must agree -- the header letters (XML), the printed
key table (XML body table 0) and the key table in the Word PDF's text layer.

Figures (the user hand-snips everything; `FIG_PLAN`): every drawing / OLE object is a FIG
sentinel resolved by an explicit per-question plan consumed in DOCUMENT ORDER; the run raises
on a shortfall or leftover. Answer figures are named SEAB_H2_P1_Q<n>_ans-<slot>_2024.png.

Declared, asserted steps (nothing silent): DROP_BLOCKS (typed labels that live inside a
user snip), WHOLE_TABLE_FIGS (a table the user snips whole), RAW builders (Q8 label column,
Q9 half-life chain, Q15 oxidation-state grids: whitespace-aligned lines rebuilt with
inline-blocks), `norm()` = mechanical typography only. Wording and chemistry are NEVER changed
here: those go to the user and are applied through `RULED_FIXES` once ruled.

Usage:
  python3 -m ingest.extract_alevel_p1_answers <answers document.xml> <answers.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("A Level", "H2", "P1", 2024)

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"
W = "{%s}" % NS["w"]

ARROW = ("html", " \u2192 ")
EQUIL = ("html", " \u21cc ")


def IMG(slot):
    return ("img", slot)


# Per-question plan for FIG sentinels, in DOCUMENT ORDER after the collapsing rule
# (consecutive figure-only paragraphs become one). A question absent here has no FIG.
FIG_PLAN = {
    11: [IMG("ans-1")],     # Boltzmann curves, red curve at (T-50) C, label inside the snip
    18: [IMG("ans-1")],     # C2H5- (Lewis structure with lone pair and charge)
    19: [IMG("ans-1")],     # the four dibromo products, with the 1/3 degree labels INSIDE the snip
    20: [IMG("ans-1")],     # HBr + propene scheme (both carbocations / products)
    22: [IMG("ans-a"), IMG("ans-b"), IMG("ans-c"), IMG("ans-d")],   # one scheme per option
    25: [IMG("ans-1")],     # amide base hydrolysis scheme
    29: [IMG("ans-1")],     # the WHOLE table (ion / configuration / energy-level diagrams)
}
INLINE_FIGS = set()
WHOLE_TABLE_FIGS = {29}

# Typed labels that live INSIDE a user snip (so are not typed again). Each rule
# must match exactly one paragraph.
DROP_BLOCKS = {
    19: [("p", r"^\s*1\u00b0(?:\s+[13]\u00b0)*\s*$", "1/3 degree labels live inside the snip (row 1)"),
         ("p", r"^\s*3\u00b0(?:\s+[13]\u00b0)*\s*$", "1/3 degree labels live inside the snip (row 2)")],
}
BLOCK_PREFIX = {}
BR_KEEP = set()

# Rulings the user has made on school-text errors: qnum -> [(old, new)], each `old`
# must occur exactly once in that question's html. EMPTY until the user rules.
RULED_FIXES = {
    # user rulings 2026-10-22 (school-text errors)
    9:  [(">0.0016</span>", ">0.016</span>"),
         ("from 0.0016 mol", "from 0.016 mol"),
         ("to 0.0001 mol", "to 0.001 mol")],
    1:  [('<span style="display:block">20.2</span>', '<span style="display:block">20</span>')],  # nucleon number of Ne-20 (20.2 is the Ar-like relative atomic mass)
    20: [("the one</span></p>\n<p><span class=\"ans\">formed from", "the one formed from")],  # school typed a hard line break mid-sentence
    27: [("0.030188 \u00d7 63.5", "0.031088 \u00d7 63.5")],
    18: [("can act donate", "can donate")],
    19: [("\u0392-selinene", "\u03b2-selinene"),
         ("to form bromoalkene", "to form dibromoalkanes")],
    # grammar
    2:  [("shared paired of", "shared pair of")],
    3:  [("2 lone pair around", "2 lone pairs around")],
    5:  [("principal quantum 3", "principal quantum number 3")],
    12: [("thus act as", "thus acts as")],
    21: [("atoms is substituted", "atoms are substituted"),
         ("for hydrogen to substituted", "for hydrogen to be substituted"),
         ("needs to be free", "need to be free"),
         # user ruling 2026-10-22: stray typed gap before -NH2 in option D
         ('relative to<span style="display:inline-block;width:1.4em"></span>\u2013NH', "relative to \u2013NH")],
}

def asset_name(q, slot):
    return "SEAB_H2_P1_Q%d_%s_2024.png" % (q, slot)


# ---------------------------------------------------------------------------
def direct(el, tag):
    return [c for c in el if c.tag == W + tag]


def plain(el):
    return "".join(el.itertext())


_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS_P = re.compile(r"Answer\s*:\s*<b>\s*([A-D])\s*</b>")


def cell_colspan(tc):
    tcPr = tc.find(Wq + "tcPr")
    if tcPr is None:
        return None
    gs = tcPr.find(Wq + "gridSpan")
    if gs is None:
        return None
    v = gs.get(Wq + "val")
    return int(v) if v else None


def _indent_gap(match_text):
    width = sum(4 if c == "\t" else 1 for c in match_text)
    return width


SPACE_EM = 0.28      # one Arial space, in em: the source aligns with typed spaces


def spacer(em):
    return '<span style="display:inline-block;width:%.1fem"></span>' % em


def tidy(html: str, qn=None) -> str:
    """Layout line-wrap <br> -> space (kept where BR_KEEP says they are real
    line breaks); leading typed spaces -> a spacer of the same width; a run of
    spaces or a tab inside a line -> a gap."""
    html = html.rstrip(" \t\u00a0")   # trailing alignment padding is not content
    html = re.sub(r"^(?:[ \t\u00a0]|&nbsp;)*<br>", "", html)
    # typed spaces INSIDE a leading <b>/<i> are indentation, not content
    html = re.sub(r"^((?:<[bi]>)+)([ \t\u00a0]+)", r"\2\1", html)
    if qn in BR_KEEP:
        lines = [tidy(x) for x in re.split(r"[ \t\u00a0]*<br>", html)
                 if re.sub(r"<[^>]+>|[ \t\u00a0]", "", x)]
        return "<br>".join(lines)
    html = re.sub(r"\s*<br>\s*", " ", html)
    m = re.match(r"^([ \t\u00a0]+)", html)
    lead = ""
    if m:
        w = _indent_gap(m.group(1))
        html = html[m.end():]
        if w >= 4:
            lead = spacer(w * SPACE_EM)

    def gap(mm):
        w = _indent_gap(mm.group(0))
        return spacer(max(1.0, w * SPACE_EM))

    html = re.sub(r"[ \u00a0]*\t[ \t\u00a0]*|[ \u00a0]{4,}", gap, html)
    return lead + html.rstrip()


RAW = "\x01RAW\x01"          # marks a block that is already final html (skips clean())
_HDR = re.compile(r"^\s*(\d{1,2})\s+([A-D])\b(?:\s*\(.*\))?\s*$")


def plain_text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\x00C\x00|\x01RAW\x01", "", html)).strip()


def read_table(tbl):
    rows = []
    for tr in direct(tbl, "tr"):
        row = []
        for cell in direct(tr, "tc"):
            paras = []
            for p in direct(cell, "p"):
                h = paragraph_html(p).replace(CENTRE, "")
                if h.strip():
                    paras.append(h if FIG in h else clean(h, None))
            row.append((" ".join(paras), cell_colspan(cell)))
        rows.append(row)
    return rows


def read_blocks(qn, elems):
    """[("p", html) | ("table", rows)] for one question's body elements, empties dropped."""
    blocks = []
    for child in elems:
        if child.tag == W + "p":
            h = paragraph_html(child)
            if h and h.replace(CENTRE, "").strip():
                blocks.append(("p", h))
        elif child.tag == W + "tbl":
            rows = read_table(child)
            if qn in WHOLE_TABLE_FIGS and any(FIG in t for r in rows for t, _ in r):
                blocks.append(("p", FIG))          # the user snips this table whole
            else:
                blocks.append(("table", rows))
    return blocks


def question_groups(document_xml):
    """({qnum: [body elements]}, {qnum: header letter}); headers must run 1..30."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    kids = [c for c in body if c.tag in (W + "p", W + "tbl")]
    groups, letters, cur = {}, {}, None
    nxt = 1
    for el in kids[3:]:                         # 0 = college, 1 = title, 2 = key table
        if el.tag == W + "p":
            m = _HDR.match(plain_text(paragraph_html(el)))
            if m and int(m.group(1)) == nxt:
                cur = nxt
                groups[cur] = []
                letters[cur] = m.group(2)
                nxt += 1
                continue
        if cur is not None:
            groups[cur].append(el)
    if sorted(groups) != list(range(1, 31)):
        raise RuntimeError("expected question headers 1-30, got %s" % sorted(groups))
    return groups, letters


def fig_only(html):
    s = html.replace(CENTRE, "").replace(FIG, "").strip()
    return html.count(FIG) > 0 and not s


def _sc(m):
    """Spaces inside a sup/sub move outside it (leading ones are dropped)."""
    tag, lead, core, trail, nxt = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    if not core.strip():
        return " " if (lead or core or trail) else ""
    out = "<%s>%s</%s>" % (tag, core, tag)
    if trail:
        out += " " if nxt.isalnum() else trail
    return out


def norm_pre(html):
    """Before tidy(): zero-width / non-breaking spaces, spaces inside sup/sub."""
    html = html.replace("\u200b", "")
    html = html.replace("\u00a0,", ",").replace("\u00a0", " ")
    html = re.sub(r"<(sub|sup)>(\s*\x00FIG\x00\s*)</\1>", r"\2", html)
    # trailing alignment padding that sits inside closing tags (<b>\t</b>)
    html = re.sub(r"(?:[ \t\u00a0]|&nbsp;)+((?:</[a-z]+>)+)\s*$", r"\1", html)
    return re.sub(r"<(sup|sub)>(\s*)([^<]*?)(\s*)</\1>(?=(.?))", _sc, html)


def clean(html, qn):
    return norm(tidy(norm_pre(html), qn))


def norm(html):
    """MECHANICAL typography only; wording and chemistry are never touched."""
    # the scan-line / macron glyph standing in for a charge sign
    html = re.sub(r"(?<=[A-Za-z)\]])[\u00af\u23ba]", "<sup>\u2212</sup>", html)
    # minus signs inside charges / exponents
    html = re.sub(r"<sup>([^<]*)</sup>",
                  lambda m: "<sup>%s</sup>" % re.sub("[\u2012\u2013\u2010-]", "\u2212", m.group(1)),
                  html)
    html = html.replace("\u2012", "\u2212")
    html = re.sub(r"(?<=\d) \u2013 (?=\d)", " \u2212 ", html)       # subtraction
    html = re.sub(r"(?<![\w)\]])-(?=lg\b)", "\u2212", html)           # -lg(...)
    html = re.sub(r"<(sub)>(\d)([.,;:])</sub>", r"<sub>\2</sub>\3", html)
    html = html.replace("</b><b>", "").replace("</i><i>", "")
    html = html.replace("<b> </b>", " ")
    html = re.sub(r"<b>[ ]+", "<b>", html)
    html = html.replace("<i> </i>", " ")
    html = re.sub(r"<i>([A-Za-z])<sub>([^<]*)</sub>( ?)</i>", r"<i>\1</i><sub>\2</sub>\3", html)
    html = html.replace("<sup>\u03b8</sup>", '<sup class="pl-sym">\u29b5</sup>')   # standard-state sign
    html = html.replace("\u2206", "\u0394")
    html = html.replace("(<i>s</i>)", "(s)")                               # state symbols are upright
    html = html.replace("<i>e</i><sup>", "e<sup>")
    html = re.sub(r'<span class="sr">([IVX]+)([.,;]?) </span>', r'<span class="sr">\1</span>\2 ', html)
    html = re.sub(r"\u00d7(?=\d|<span class=\"frac\")", "\u00d7 ", html)
    # the multiplication sign typed as a letter x between factors ("5.00 x (20.0 x 60)")
    html = re.sub(r"(?<!where)(?<!Let)(?<=[\w)\]>\u00bd%]) x (?=[\d(\[A-Za-z<\u00bd])", " \u00d7 ", html)
    html = re.sub(r"<sub>([A-Za-z0-9]+) [x\u00d7] ?</sub>", "<sub>\\1</sub> \u00d7", html)
    html = re.sub(r"<b></b>", "", html)
    # standard-state sign inside the stacked E<theta><cell> notation
    html = html.replace('<span class="stk post"><span>\u03b8</span>',
                        '<span class="stk post"><span><span class="pl-sym">\u29b5</span></span>')
    html = re.sub(r'(?<!\w)(?<!<i>)E(?=<sup class="pl-sym">|<span class="stk post">)', "<i>E</i>", html)
    html = re.sub(r'(?<!\w)(?<!<i>)K(?=<sub>[ac]\b)', "<i>K</i>", html)
    return html


def _right(w, txt):
    return ('<span style="display:inline-block;min-width:%.1fem;text-align:right">%s</span>'
            % (w, txt))


def _cell(w, html, align="left"):
    return ('<span style="display:inline-block;min-width:%.1fem;text-align:%s">%s</span>'
            % (w, align, html))


def _build_q8(payload):
    """'cation charge (q+):<TAB>Ca2+ > K+' -> label column + value (tab stops rebuilt)."""
    m = re.match(r"^((?:cation|anion) (?:charge|size) \(.*?\):)[\s\u00a0]*(.+)$", payload.strip())
    if not m:
        return None
    return RAW + _cell(11.5, clean(m.group(1), None)) + clean(m.group(2), None)


def _build_q9(blocks):
    """The 't1/2 t1/2 t1/2' label line and the '0.0016 -> 0.008 -> ...' chain below it:
    typed with spaces in the source; rebuilt as two aligned rows (labels over the arrows)."""
    out, i = [], 0
    while i < len(blocks):
        k, pl = blocks[i]
        if (k == "p" and plain_text(pl) == "t1/2 t1/2 t1/2"
                and i + 1 < len(blocks) and "\u2192" in blocks[i + 1][1]):
            vals = [v.strip() for v in re.split(r"\u2192", plain_text(blocks[i + 1][1]).rstrip("."))]
            if len(vals) != 4:
                raise RuntimeError("Q9: expected 4 chain values, got %r" % vals)
            w = 3.3
            lab = "".join(_cell(w, "", "center") + _cell(w, "t<sub>1/2</sub>", "center")
                          for _ in range(3)) + _cell(w, "", "center")
            row = "".join(_cell(w, v + ("." if j == 3 else ""), "center")
                          + (_cell(w, "\u2192", "center") if j < 3 else "")
                          for j, v in enumerate(vals))
            # labels sit over the arrows: [blank][t][blank][t][blank][t]  then values+arrows
            out.append(("p", CENTRE + RAW + lab))
            out.append(("p", CENTRE + RAW + row))
            i += 2
            continue
        out.append(blocks[i])
        i += 1
    return out


# Q15: oxidation-state grids typed with runs of spaces. (ox. states over each species, the
# species line, the R.A/O.A roles); asserted against the raw text, then rebuilt.
Q15_GRIDS = [
    # (line1 text, line2 text, line3 text), species cells, oxidation cells, role cells
    ("0 0 +2 \u20131", "Mg + Cl2 \u2192 MgCl2", "R.A O.A",
     ["Mg", "C<i class=\"el\">l</i><sub>2</sub>", "MgC<i class=\"el\">l</i><sub>2</sub>"],
     ["0", "0", ("+2", "\u22121")], ["R.A", "O.A", ""]),
    ("0 0 +2 \u20132", "Mg + S \u2192 MgS", "R.A O.A",
     ["Mg", "S", "MgS"], ["0", "0", ("+2", "\u22122")], ["R.A", "O.A", ""]),
    ("0 0 +1 \u20131", "Na + Br2 \u2192 NaBr", "R.A O.A",
     ["Na", "Br<sub>2</sub>", "NaBr"], ["0", "0", ("+1", "\u22121")], ["R.A", "O.A", ""]),
    ("0 0 +1 \u20132", "Na + O2 \u2192 Na2O", "R.A O.A",
     ["Na", "O<sub>2</sub>", "Na<sub>2</sub>O"], ["0", "0", ("+1", "\u22122")], ["R.A", "O.A", ""]),
]


def _build_q15(blocks):
    out, i, g = [], 0, 0
    while i < len(blocks):
        k, pl = blocks[i]
        if k == "p" and re.match(r"^0 0 [+\u2013\u2212-]\d", plain_text(pl)):
            if g >= len(Q15_GRIDS) or i + 2 >= len(blocks):
                raise RuntimeError("Q15: unexpected oxidation-state block")
            l1, l2, l3, sp, ox, ro = Q15_GRIDS[g]
            got = tuple(plain_text(blocks[i + j][1]).replace("\u2013", "\u2013") for j in range(3))
            if got != (l1, l2, l3):
                raise RuntimeError("Q15 grid %d: raw text %r != expected %r" % (g, got, (l1, l2, l3)))
            W_ = 4.6
            def row(cells, extra=None):
                a = _cell(W_, cells[0]) + _cell(1.8, "") + _cell(W_, cells[1])
                return a
            def ox_cell(v):
                if isinstance(v, tuple):
                    return _cell(2.0, v[0]) + _cell(2.0, v[1])
                return v
            r_ox = (_cell(W_, ox[0]) + _cell(1.8, "") + _cell(W_, ox[1]) + _cell(1.8, "")
                    + _cell(6.0, ox_cell(ox[2])))
            r_sp = (_cell(W_, sp[0]) + _cell(1.8, "+") + _cell(W_, sp[1]) + _cell(1.8, "\u2192")
                    + _cell(6.0, sp[2]))
            r_ro = (_cell(W_, ro[0]) + _cell(1.8, "") + _cell(W_, ro[1]))
            out += [("p", RAW + r_ox), ("p", RAW + r_sp), ("p", RAW + r_ro)]
            g += 1
            i += 3
            continue
        out.append(blocks[i])
        i += 1
    if g != len(Q15_GRIDS):
        raise RuntimeError("Q15: rebuilt %d of %d grids" % (g, len(Q15_GRIDS)))
    return out


def _visible(html):
    return bool(re.sub(r"<[^>]+>|\s|&nbsp;|\x00C\x00|\x01RAW\x01", "", html.replace(FIG, "F")))


def prepare(qn, blocks):
    out = list(blocks)
    for kind, pat, _why in DROP_BLOCKS.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out)
               if k == kind and (pat is None or re.search(pat, p))]
        if len(hit) != 1:
            raise RuntimeError("Q%d: drop rule %r/%r matched %d block(s), "
                               "expected 1" % (qn, kind, pat, len(hit)))
        del out[hit[0]]

    if qn == 8:
        out = [(k, (_build_q8(p) or p) if k == "p" else p) for k, p in out]
        if sum(1 for k, p in out if k == "p" and p.startswith(RAW)) != 4:
            raise RuntimeError("Q8: expected 4 aligned label lines")
    if qn == 9:
        out = _build_q9(out)
        if sum(1 for k, p in out if k == "p" and p.startswith(CENTRE + RAW)) != 2:
            raise RuntimeError("Q9: half-life chain not rebuilt")
    if qn == 15:
        out = _build_q15(out)

    out = [(k, p if (k != "p" or FIG in p or RAW in p) else clean(p, qn)) for k, p in out]
    out = [(k, p) for k, p in out if k != "p" or _visible(p)]
    for pat, prefix in BLOCK_PREFIX.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(pat, p)]
        if len(hit) != 1:
            raise RuntimeError("Q%d: prefix rule %r matched %d block(s)" % (qn, pat, len(hit)))
        out[hit[0]] = ("p", prefix + out[hit[0]][1])

    merged = []
    for kind, payload in out:
        if (kind == "p" and fig_only(payload) and merged
                and merged[-1][0] == "p" and fig_only(merged[-1][1])):
            continue                      # collapse into the previous figure
        if kind == "p" and fig_only(payload):
            payload = FIG                 # one figure, however many objects
        merged.append((kind, payload))
    return merged


def wrap_answer(html):
    html = html.strip()
    if not html:
        return ""
    return '<span class="ans">%s</span>' % html


# Pictures that sit IN a line of text rather than in a block of their own.
# index.html forces img.ws-fig to display:block, so these carry an inline style
# (inline styles beat the stylesheet; sizeFig only touches max-width/height).
INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"


_STK = re.compile(r'<span class="stk( post)?"><span>((?:<span class="pl-sym">[^<]*</span>)|[^<]*)</span>'
                  r'<span>([^<]*)</span></span>')


def inline_stk(html):
    """`.stk` CSS is scoped to .stem in index.html, so in a worked solution it would collapse
    to a run-on '23490Th'. Same stacking, as inline styles (self-contained)."""
    def f(m):
        post = bool(m.group(1))
        box = ("display:inline-block;vertical-align:middle;position:relative;top:-.06em;"
               "line-height:1;font-size:.72em;text-align:%s;margin:%s" %
               ("left" if post else "right", "0 0 0 .08em" if post else "0 .08em 0 0"))
        return ('<span style="%s"><span style="display:block">%s</span>'
                '<span style="display:block">%s</span></span>' % (box, m.group(2), m.group(3)))
    return _STK.sub(f, html)


def render(qn, blocks):
    plan = iter(FIG_PLAN.get(qn, []))
    assets = []

    def take():
        try:
            return next(plan)
        except StopIteration:
            raise RuntimeError("Q%d: more FIG placeholders than FIG_PLAN "
                               "entries" % qn)

    def img_html(slot):
        path = asset_name(qn, slot)
        assets.append((slot, path))
        return '<img class="ws-fig" data-asset="%s" alt="">' % path

    out = []
    skip = 0
    for idx, (kind, payload) in enumerate(blocks):
        if skip:
            skip -= 1
            continue
        if kind == "table":
            rows_html = []
            for row in payload:
                cells = []
                for text, span in row:
                    parts = text.split(FIG)
                    buf = parts[0]
                    for nxt in parts[1:]:
                        item = take()
                        if item[0] != "html":
                            raise RuntimeError("Q%d: an image planned inside "
                                               "a table cell" % qn)
                        buf += item[1] + nxt
                    attr = ' colspan="%d"' % span if span else ""
                    cells.append("<td%s>%s</td>" % (attr, buf.strip()))
                rows_html.append("<tr>%s</tr>" % "".join(cells))
            out.append('<table class="cmp">%s</table>' % "".join(rows_html))
            continue

        centred = payload.startswith(CENTRE)
        text = payload.replace(CENTRE, "")
        if text.startswith(RAW):
            text = text[len(RAW):]
            inner = wrap_answer(text)
            out.append('<p class="c">%s</p>' % inner if centred else "<p>%s</p>" % inner)
            continue
        if FIG in text:
            text = clean(text, qn)
        if FIG not in text:
            inner = wrap_answer(text)
            if inner:
                out.append('<p class="c">%s</p>' % inner if centred
                           else "<p>%s</p>" % inner)
            continue

        # a paragraph carrying figures: typed ones stay inline, a real picture
        # gets its own paragraph (img.ws-fig is display:block in index.html, so
        # mid-sentence placement splits the sentence regardless).
        segs = text.split(FIG)
        pending = segs[0]
        prefix = ""
        for i, nxt in enumerate(segs[1:], start=1):
            item = take()
            if item[0] == "html":
                pending += item[1] + nxt
                continue
            if (qn, item[1]) in INLINE_FIGS:
                im = img_html(item[1]).replace(
                    'alt=""', 'alt="" style="%s"' % INLINE_STYLE)
                prefix += wrap_answer(pending) + im
                pending = nxt
                continue
            if pending.strip() or prefix:
                out.append("<p>%s</p>" % (prefix + wrap_answer(pending)))
                prefix = ""
            tail = nxt
            im = img_html(item[1])
            # a punctuation mark right after the picture belongs to it, not
            # to a line of its own (", yellow ppt is observed.")
            m = re.match(r"^\s*([,.;:])", tail)
            if m:
                im += '<span class="ans">%s</span>' % m.group(1)
                tail = tail[m.end():]
            out.append("<p>%s</p>" % im)
            pending = tail
        if pending.strip() or prefix:
            out.append("<p>%s</p>" % (prefix + wrap_answer(pending)))

    left = list(plan)
    if left:
        raise RuntimeError("Q%d: %d FIG_PLAN entries unused: %r"
                           % (qn, len(left), left))
    body = inline_stk("\n".join(out))
    for old, new in RULED_FIXES.get(qn, []):
        if body.count(old) != 1:
            raise RuntimeError("Q%d: ruled fix %r occurs %d times" % (qn, old, body.count(old)))
        body = body.replace(old, new)
    body, log = corrections.apply(body, SCOPE)
    if log:
        print("Q%d corrections applied: %s" % (qn, log))
    return '<div class="worked-solution">\n%s\n</div>' % body, assets


def key_table(document_xml):
    """{n: letter} from the printed key table (body table 0: 6 rows x 5 (no, letter) pairs)."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    tbl = direct(body, "tbl")[0]
    cells = [plain(tc).strip() for tr in direct(tbl, "tr") for tc in direct(tr, "tc")]
    out = {}
    for a, b in zip(cells[0::2], cells[1::2]):
        if a.isdigit() and len(b) == 1 and b in "ABCD":
            out[int(a)] = b
    return out


def pdf_keys(pdf):
    """The key table in the Word PDF's text layer (page 1): {n: letter}."""
    import subprocess
    txt = subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-layout", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    out = {}
    for line in txt.splitlines()[:14]:
        head = line[:50]
        for n, l in re.findall(r"\b(\d{1,2})\s+([A-D])\b", head):
            out.setdefault(int(n), l)
    return out


def extract(document_xml, pdf):
    groups, letters = question_groups(document_xml)
    ws, assets = {}, []
    for qn in sorted(groups):
        blocks = prepare(qn, read_blocks(qn, groups[qn]))
        html, a = render(qn, blocks)
        ws[qn] = html
        for off, (slot, path) in enumerate(a, start=1):
            assets.append({"question": qn, "slot": slot, "path": path, "offset": off})
    kt = key_table(document_xml)
    pk = pdf_keys(pdf)
    if sorted(kt) != list(range(1, 31)):
        raise RuntimeError("key table has %d entries, expected 30" % len(kt))
    if sorted(pk) != list(range(1, 31)):
        raise RuntimeError("the Word PDF key table has %d entries, expected 30" % len(pk))
    bad = {q: (letters[q], kt[q], pk[q]) for q in letters
           if not (letters[q] == kt[q] == pk[q])}
    if bad:
        raise RuntimeError("answer key disagrees (header, key table, PDF): %r" % bad)
    return ws, assets, letters


if __name__ == "__main__":      # pragma: no cover
    doc, pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    ws, assets, keys = extract(doc, pdf)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_assets.json").write_text(
        json.dumps(assets, indent=2), encoding="utf-8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in keys.items()}, indent=2),
        encoding="utf-8")
    print("worked solutions: %d" % len(ws))
    print("answer figures:   %d" % len(assets))
    print("answer keys:      %d, header = key table = Word PDF" % len(keys))
