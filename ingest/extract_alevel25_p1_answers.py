"""Extract worked solutions + answer key for the SEAB A Level 2025 H2 P1 (9729/01, MCQ),
from the COLLEGE (VJC) answers document.

Same shape as the 2024 VJC document (extract_alevel_p1_answers.py): a college line, a title, a
6x10 key table (body index 2), then every question is a run of paragraphs/tables opened by a
header paragraph "N<TAB>LETTER[ (1 only)]" (dropped: the letter goes to answer_key, the gloss is
already in the question's options). Headers must run 1..30 in order.

Q11 is NOT in the bank (user ruling 2026-10-29: needs the dG-K relationship, out of 9476), so
its worked solution and key are extracted and then left out of the outputs (REMOVED_QS); the
answers SQL is built for the 29 live questions.

Key: read THREE ways and all must agree -- the header letters (XML), the printed key table (XML
body table 0) and the key table in a PDF text layer. No Word PDF was supplied for 2025, so the
third source is a LibreOffice conversion of the docx (plain text only: the key table is not
affected by the glyph damage the README describes).

Figures (the user hand-snips everything; `FIG_PLAN`): every drawing / OLE object is a FIG
sentinel resolved by an explicit per-question plan consumed in DOCUMENT ORDER; the run raises
on a shortfall or leftover. Answer figures are named SEAB_H2_P1_Q<n>_ans-<slot>_2025.png.

Declared, asserted steps (nothing silent): STRAY_SHAPES (decorative hairlines from the school's
PDF round-trip, not figures), DROP_BLOCKS, `norm()` = mechanical typography only. Wording and
chemistry are NEVER changed here: those go to the user and are applied through `RULED_FIXES`
once ruled.

Usage:
  python3 -m ingest.extract_alevel25_p1_answers <answers document.xml> <answers.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("A Level", "H2", "P1", 2025)

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"
W = "{%s}" % NS["w"]

ARROW = ("html", " \u2192 ")
EQUIL = ("html", " \u21cc ")

REMOVED_QS = {11}      # not in the bank (see docstring)


LE_FRAC = ('|<span class="frac"><span class="fnum"><i>q</i><sub>+</sub> \u00d7 <i>q</i><sub>\u2212</sub></span>'
           '<span class="fden"><i>r</i><sub>+</sub> + <i>r</i><sub>\u2212</sub></span></span>|')


def IMG(slot):
    return ("img", slot)


# Per-question plan for FIG sentinels, in DOCUMENT ORDER after the collapsing rule
# (consecutive figure-only paragraphs become one). A question absent here has no FIG.
FIG_PLAN = {
    14: [IMG("ans-1")],     # 1-bromopropane -> propene -> 2-bromopropane scheme
    15: [IMG("ans-1")],     # the 6 isomers (acids + esters, labels inside): two consecutive objects = ONE snip
    19: [IMG("ans-1")],     # reaction L: termination (two radicals -> alkane), curly arrows
    20: [IMG("ans-1")],     # both Friedel-Crafts steps (one object)
    21: [IMG("ans-1"), IMG("ans-2"), IMG("ans-3")],   # one scheme per statement 1-3
    22: [IMG("ans-1")],     # the three amino acid structures with their names
    23: [IMG("ans-a"), IMG("ans-b"), IMG("ans-c"), IMG("ans-d")],   # one scheme per option
    25: [IMG("ans-1"), IMG("ans-2"), IMG("ans-3")],   # one route scheme per statement 1-3
    30: [("html", LE_FRAC)],  # the equation-editor object |q+ x q- / (r+ + r-)| -- typed
}
INLINE_FIGS = set()
WHOLE_TABLE_FIGS = set()

# Decorative hairline shapes from the school's PDF round-trip (a 0.4pt-wide grey bar anchored to
# the page): not figures. {qnum: number of FIG sentinels to drop}; asserted exactly.
STRAY_SHAPES = {2: 2}

# MECHANICAL typography on one question (exact, counted): not wording, not chemistry.
MECH_FIXES = {
    10: [("<td>\u20134x</td>", "<td>\u22124x</td>"),            # a minus, not a dash
         ("initial /atm", "initial / atm")],                  # unit spacing as in the other rows
}

DROP_BLOCKS = {}
BLOCK_PREFIX = {}
BR_KEEP = set()

# Rulings the user has made on school-text errors: qnum -> [(old, new)], each `old`
# must occur exactly once in that question's html. EMPTY until the user rules.
RULED_FIXES = {
    # Q22/Q30/Q7/Q29 rulings, then the user's blanket instruction to correct grammar
    # (subject-verb agreement, missing determiners/plurals).  (old, new[, expected_count])
    1: [("have different number of protons", "have different numbers of protons")],
    2: [("one mole of particle Q", "one mole of particles Q")],
    3: [("in molten state", "in the molten state")],
    4: [("as compared to 2s electron", "as compared to the 2s electron"),
        ("involves loss of an electron", "involves the loss of an electron"),
        ("Their 1<sup>st</sup> IE are similar", "Their 1<sup>st</sup> IEs are similar")],
    5: [("in molten state", "in the molten state", 2)],
    7: [("A Bronsted-Lowry acid-base pair differ from each other by one proton;",
         "The two species in a Bronsted-Lowry acid-base pair differ from each other by one proton;"),
        ("Bronsted", "Br\u00f8nsted", 7)],
    8: [("releases energy the process", "releases energy, the process")],
    9: [("increasing temperature broadens", "increasing the temperature broadens")],
    17: [("a halogenoarene, fluoroalkane (difficult to break very strong C\u2013F bond)",
          "a halogenoarene, a fluoroalkane (difficult to break the very strong C\u2013F bond)")],
    18: [("is an electron rich species", "is an electron-rich species"),
         ("where a H is abstracted", "where an H atom is abstracted")],
    19: [("Reaction K is initiation step", "Reaction K is an initiation step"),
         ("Reaction L is termination step", "Reaction L is a termination step")],
    20: [("presence of Lewis acid catalyst", "presence of the Lewis acid catalyst")],
    22: [("is \u221d-amino acid", "is an \u03b1-amino acid")],
    23: [("undergoes condensation reaction with amine to form amide",
          "undergoes a condensation reaction with an amine to form an amide"),
         ("undergoes condensation reaction with phenol to form ester",
          "undergoes a condensation reaction with phenol to form an ester"),
         ("undergoes condensation reaction with alcohol to form ester",
          "undergoes a condensation reaction with an alcohol to form an ester"),
         ("to form carboxylic acid", "to form a carboxylic acid")],
    24: [("In gaseous state", "In the gaseous state"),
         ("atoms in benzene ring", "atoms in the benzene ring"),
         ("electron\u2013donating", "electron-donating")],
    26: [("causes position of equilibrium (1) to shift left",
          "causes the position of equilibrium (1) to shift to the left"),
         ("and a less positive <i>E</i>(Ag<sup>+</sup>|Ag).</span>",
          "and a less positive <i>E</i>(Ag<sup>+</sup>|Ag). However, this is no longer a <i>standard</i> "
          "electrode potential, since [Ag<sup>+</sup>] is no longer 1 mol dm<sup>\u22123</sup>.</span>"),
         ("<span class=\"ans\">When <i>E</i>(Ag<sup>+</sup>|Ag) &lt; +0.80 V, <i>E</i><sub>cell</sub> will be more positive.</span></p>",
          "<span class=\"ans\">Standard electrode potentials are defined at 1 mol dm<sup>\u22123</sup> and 298 K, so the "
          "standard electrode potential of the silver half-cell remains +0.80 V and the standard cell potential "
          "remains +0.56 V.</span></p>\n<p><span class=\"ans\">(Only the actual, non-standard "
          "<i>E</i>(Ag<sup>+</sup>|Ag) falls below +0.80 V, which would make the actual "
          "<i>E</i><sub>cell</sub> more positive.)</span></p>")],
    29: [("<i>n</i><sub>cu</sub>", "<i>n</i><sub>Cu</sub>")],
    30: [("have higher effective nuclear charge", "have a higher effective nuclear charge"),
         ("This result in a smaller atomic volume compared to s-block elements",
          "This results in a smaller atomic volume compared to that of s-block elements"),
         ("has greater relative atomic mass to atomic radius ratio than Ca",
          "has a greater ratio of relative atomic mass to atomic radius than Ca"),
         ("LE \u03b1 ", "LE \u221d ")],
}

def asset_name(q, slot):
    return "SEAB_H2_P1_Q%d_%s_2025.png" % (q, slot)


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
    html = html.replace("\u00ad", "-")                   # soft hyphen typed where a hyphen was meant (Q7 "Bronsted-Lowry")
    # radical dot: the bank's glyph is U+2022, upright and OUTSIDE any italic run
    html = html.replace('<i class="el">l\u25cf</i>', '<i class="el">l</i>\u2022').replace("<i>\u25cf</i>", "\u2022")
    html = html.replace("\u25cf", "\u2022")
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
    # an en dash used as a MINUS: a negative value / sign ("= \u20130.25 V", "= \u2013(6)(96500)", "\u2013<i>n</i>F")
    html = re.sub(r"(?<=[\s=])\u2013(?=[\d(]|<i>)", "\u2212", html)
    # ... and as a subtraction between terms ("+1.36 \u2013 (+0.80)", "E(Cl2|Cl-) \u2013  E(Ag+|Ag)", "E.. \u2013 E..")
    html = re.sub(r" \u2013\s+(?=[(+]|<i>)", " \u2212 ", html)
    html = re.sub(r'(<sup class="pl-sym">\u29b5</sup>)=', r"\1 =", html)        # "E<theta>=" -> "E<theta> ="
    html = re.sub(r"<i>( +)", r"\1<i>", html)                                  # an italic run must not start with a space
    html = html.replace("</span>\u00f7<span", "</span> \u00f7 <span")          # between two fractions
    return html


def _cell(w, html, align="left"):
    return ('<span style="display:inline-block;min-width:%.1fem;text-align:%s">%s</span>'
            % (w, align, html))


def _build_q6(blocks):
    """'O2 : CO2 : CO : Fe' over '1 : 1 : 2 : (2/3 x 2 = 4/3)': typed with runs of spaces in the
    source; rebuilt as two rows of equal-width cells so the columns line up."""
    out, i, done = [], 0, 0
    while i < len(blocks):
        k, pl = blocks[i]
        if k == "p" and plain_text(pl) == "O2 : CO2 : CO : Fe" and i + 1 < len(blocks):
            top = [x.strip() for x in plain_text(pl).split(":")]
            bot = [x.strip() for x in plain_text(blocks[i + 1][1]).split(":")]
            if len(top) != 4 or len(bot) != 4:
                raise RuntimeError("Q6: ratio rows are %r / %r" % (top, bot))
            sp = ["O<sub>2</sub>", "CO<sub>2</sub>", "CO", "Fe"]
            ws_ = [3.0, 3.0, 3.0, 9.5]
            def row(cells):
                return "".join(_cell(ws_[j], c, "center") + (_cell(1.2, ":", "center") if j < 3 else "")
                               for j, c in enumerate(cells))
            out.append(("p", RAW + row(sp)))
            out.append(("p", RAW + row([clean(b, None) for b in bot])))
            i += 2
            done += 1
            continue
        out.append(blocks[i])
        i += 1
    if done != 1:
        raise RuntimeError("Q6: ratio block rebuilt %d time(s), expected 1" % done)
    return out


def _build_q7(blocks):
    """Species line + 'acid   base' label line (typed alignment) -> two rows of equal cells."""
    out, i, done = [], 0, 0
    while i < len(blocks):
        k, pl = blocks[i]
        if (k == "p" and i + 1 < len(blocks) and blocks[i + 1][0] == "p"
                and re.match(r"^(acid|base)\s+(acid|base)$", plain_text(blocks[i + 1][1]))):
            sp = clean(pl, None).split(" and ")
            lab = plain_text(blocks[i + 1][1]).split()
            if len(sp) != 2:
                raise RuntimeError("Q7: species line %r" % pl)
            r1 = _cell(6.0, sp[0], "center") + _cell(2.4, "and", "center") + _cell(6.0, sp[1], "center")
            r2 = _cell(6.0, lab[0], "center") + _cell(2.4, "", "center") + _cell(6.0, lab[1], "center")
            out += [("p", RAW + r1), ("p", RAW + r2)]
            i += 2
            done += 1
            continue
        out.append(blocks[i])
        i += 1
    if done != 3:
        raise RuntimeError("Q7: rebuilt %d acid/base pairs, expected 3" % done)
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

    if qn == 6:
        out = _build_q6(out)
    if qn == 7:
        out = _build_q7(out)
    if qn in STRAY_SHAPES:
        n = sum(p.count(FIG) for k, p in out if k == "p")
        if n != STRAY_SHAPES[qn]:
            raise RuntimeError("Q%d: expected %d stray shape(s), found %d" % (qn, STRAY_SHAPES[qn], n))
        out = [(k, p.replace(FIG, "") if k == "p" else p) for k, p in out]

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
        if not m.group(2).strip():            # nothing stacked on top: E_cell, not E<theta>cell
            return "<sub>%s</sub>" % m.group(3)
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
    for old, new in MECH_FIXES.get(qn, []):
        if body.count(old) != 1:
            raise RuntimeError("Q%d: mechanical fix %r occurs %d times" % (qn, old, body.count(old)))
        body = body.replace(old, new)
    if qn == 27:       # "x 2", "x 3": the multiplication sign typed as a letter after a gap
        body, n = re.subn(r"([\s>])x ([23])(</span>)", lambda m: m.group(1) + "\u00d7 " + m.group(2) + m.group(3), body)
        if n != 2:
            raise RuntimeError("Q27: expected 2 typed multiplication signs, found %d" % n)
    for fix in RULED_FIXES.get(qn, []):
        old, new = fix[0], fix[1]
        want = fix[2] if len(fix) > 2 else 1
        if body.count(old) != want:
            raise RuntimeError("Q%d: ruled fix %r occurs %d times (expected %d)" % (qn, old, body.count(old), want))
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
    """The key table in a PDF's text layer (page 1): {n: letter}. For 2025 the PDF is a
    LibreOffice conversion of the docx (no Word PDF was supplied); plain text only."""
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
        raise RuntimeError("the PDF key table has %d entries, expected 30" % len(pk))
    bad = {q: (letters[q], kt[q], pk[q]) for q in letters
           if not (letters[q] == kt[q] == pk[q])}
    if bad:
        raise RuntimeError("answer key disagrees (header, key table, PDF): %r" % bad)
    # RULED (user, 2026-10-29): Q26 asks about the STANDARD potentials, which NaCl does not change.
    # VJC's key C is overridden to A (the school key was verified above first; SEAB publishes no key).
    assert letters[26] == "C"
    letters[26] = "A"
    # the key is verified for all 30; the removed questions then drop out of the outputs
    for q in REMOVED_QS:
        ws.pop(q, None)
        letters = {k: v for k, v in letters.items() if k != q}
        assets = [a for a in assets if a["question"] != q]
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
    print("answer keys:      %d, header = key table = PDF text layer (all 30 checked; Q%s then removed)"
          % (len(keys), ",".join(map(str, sorted(REMOVED_QS)))))
