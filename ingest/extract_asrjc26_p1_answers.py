"""Extract worked solutions + answer key for ASRJC 2026 H2 P1 (9476/01, MCQ).

Document shape (ASRJC 2024 P1 family, HANDOFF section 21): the school's file is
the question paper itself -- ONE Word table per question -- with the key and the
worked solution typed into the SAME table, in blue (purple for an "Extension"):
a row whose first paragraph reads "Ans: X" (Q27-Q30: "Answer: X") that runs on
into the worked explanation. Q4 and Q16 carry their explanation in extra rows
BELOW the answer row, so every row from the answer row to the end of the
question's table is read. Run on the ORIGINAL solutions document.xml.

Key: read two independent ways and both must agree -- the letter in each answer
row (XML) and the "Ans: X" letters printed in the Word PDF.

The school's own "Topic:" / "LO n:" lines are NOT part of the worked solution:
they are dropped and written to `school_lo_lines.json` for the TAGS stage.

Figures (the user hand-snips; `FIG_PLAN`): every drawing / OLE object is a FIG
sentinel, resolved by an explicit per-question plan consumed in DOCUMENT ORDER;
the run raises on a shortfall or leftover. `TABLE_SNIPS` replaces a whole table
by its snips; `LO_FIGS` are pictures that sit inside the dropped LO block.

Declared, asserted steps (nothing silent): `LO_END`, `TABLE_SNIPS`, `REBUILD`,
`TEXT_FIXES`; `norm()` is mechanical typography only. Wording and chemistry are
NEVER changed here: those go to the user and are applied through ruled fixes.

Usage:
  python3 -m ingest.extract_asrjc26_p1_answers <solutions document.xml> <solutions.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("ASRJC", "H2", "P1", 2026)

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"
W = "{%s}" % NS["w"]

ARROW = ("html", " \u2192 ")
EQUIL = ("html", " \u21cc ")


def IMG(slot):
    return ("img", slot)


# Per-question plan for FIG sentinels, in DOCUMENT ORDER after the collapsing
# rule (consecutive figure-only paragraphs become one). A question absent here
# must have no FIG sentinel (after LO_FIGS and TABLE_SNIPS).
_F_NRT = ('<span class="frac"><span class="fnum"><i>pV</i></span>'
          '<span class="fden"><i>RT</i></span></span>')
_F_NR273 = ('<span class="frac"><span class="fnum"><i>pV</i></span>'
            '<span class="fden"><i>R</i>(273+37)</span></span>')
_F_CT = ('<span class="frac"><span class="fnum"><i>C</i><sub>t</sub></span>'
         '<span class="fden"><i>C</i><sub>o</sub></span></span> = '
         '(<span class="frac"><span class="fnum">1</span><span class="fden">2</span></span>)'
         '<sup><i>n</i></sup>')
_F_0667 = ('<span class="frac"><span class="fnum">0.0667</span>'
           '<span class="fden">1 + 0.0667</span></span> = '
           '(<span class="frac"><span class="fnum">1</span><span class="fden">2</span></span>)'
           '<sup><i>n</i></sup>')

FIG_PLAN = {
    4: [IMG("ans-1")],                       # ethoxyethane + BCl3 scheme
    6: [("html", _F_NRT), ("html", _F_NR273), ("html", _F_NR273), ("html", _F_NR273)],
    12: [("html", _F_CT), ("html", _F_0667)],
    14: [EQUIL, ARROW],                      # in the table: <=> then ->
    17: [IMG("ans-1")],                      # hybridisation-labelled molecule
    19: [ARROW, ARROW],                      # in the table
    20: [IMG("ans-1")],                      # reaction energy diagram
    23: [ARROW, ARROW, ARROW],
    25: [IMG("ans-1")],                      # starred structure + its note box
}
# Pictures inside the dropped LO block (consumed, never placed): Q25's
# "esters" reaction table sits under its LO 3 line.
LO_FIGS = {25: 1}
# The whole table (or, for Q5, the two halves split by the page break) is the
# user's snip(s). Q5: header + rows A-B, then rows C-D.
TABLE_SNIPS = {5: ["ans-a", "ans-b"], 18: ["ans-1"]}
INLINE_FIGS = set()

# The last block of the LO zone where the leading-run rule is not enough
# (Q10's LO 2 has three bullet-less continuation lines; Q25's LO block holds
# a picture). Each must match exactly one block.
# One LO line the user ruled to KEEP in the worked solution (Q17: it is the lead-in
# sentence before the hybridisation diagram). It is still copied to lo_lines.
LO_KEEP = {}
LO_END = {10: r"^LO 3:", 25: r"^LO 1: Know that amides"}

# Answer-figure files: SCHOOL_H2_P1_Q<n>_<slot>_2026.png; a lone figure is
# slot "ans-1" and file "..._ans_2026.png" (the user's own naming, as ASRJC 2024).
def asset_name(q, slot):
    if slot == "ans-1":
        return "ASRJC_H2_P1_Q%d_ans_2026.png" % q
    return "ASRJC_H2_P1_Q%d_%s_2026.png" % (q, slot)


# Paragraphs whose `<br>` are real line breaks (kept) rather than layout wraps.
BR_KEEP = set()
DROP_BLOCKS = {
    # Q21: the school's explanation describes molecule 3 as the alkene CH3CH2CH=CH2, but the
    # question's molecule 3 is C6H5CH3 (user ruled "make the change", 2026-10-23).
    21: [("p", r"Molecule 3 is an alkene", "school error: wrong molecule 3")],
}
BLOCK_PREFIX = {}

# ---------------------------------------------------------------------------
def direct(el, tag):
    return [c for c in el if c.tag == W + tag]


def plain(el):
    return "".join(el.itertext())


_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS_P = re.compile(r"Ans(?:wer)?\s*:\s*<b>\s*([A-D])\s*</b>")


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


def read_blocks(ans_row):
    """[("p", html) | ("table", rows)] for one answer row, empties dropped."""
    blocks = []
    for tc in direct(ans_row, "tc"):
        for child in tc:
            if child.tag == W + "p":
                h = paragraph_html(child)
                if h and h.replace(CENTRE, "").strip():
                    blocks.append(("p", h))
            elif child.tag == W + "tbl":
                rows = []
                for tr in direct(child, "tr"):
                    row = []
                    for cell in direct(tr, "tc"):
                        paras = []
                        for p in direct(cell, "p"):
                            h = paragraph_html(p).replace(CENTRE, "")
                            if h.strip():
                                paras.append(clean(h, None))
                        row.append(("<br>".join(paras), cell_colspan(cell)))
                    rows.append(row)
                blocks.append(("table", rows))
    return blocks


def question_groups(document_xml):
    """{qnum: [answer row, rows below it...]} -- from the one row per question
    holding 'Ans:' / 'Answer:' to the end of that question's rows."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    out = {}
    rx = re.compile(r"Ans(?:wer)?\s*:")
    for tbl in direct(body, "tbl"):
        if not rx.search(plain(tbl)):
            continue                      # cover-page tables
        rows = direct(tbl, "tr")
        starts = [i for i, r in enumerate(rows)
                  if direct(r, "tc") and _QNUM.match(plain(direct(r, "tc")[0]))]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            grp = rows[s:e]
            qn = int(_QNUM.match(plain(direct(grp[0], "tc")[0])).group(1))
            idx = [i for i, r in enumerate(grp) if rx.search(plain(r))]
            if len(idx) != 1:
                raise RuntimeError("Q%d: expected exactly one answer row, "
                                   "found %d" % (qn, len(idx)))
            if qn in out:
                raise RuntimeError("Q%d appears twice" % qn)
            out[qn] = grp[idx[0]:]
    return out


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
    html = re.sub(r"<b>[ ]+", "<b>", html)
    html = html.replace("<i> </i>", " ")
    html = re.sub(r"<i>([A-Za-z])<sub>([^<]*)</sub>( ?)</i>", r"<i>\1</i><sub>\2</sub>\3", html)
    html = html.replace("<sup>\u03b8</sup>", '<sup class="pl-sym">\u29b5</sup>')   # standard-state sign
    html = html.replace("\u2206", "\u0394")
    html = html.replace("<i>e</i><sup>", "e<sup>")
    # degree sign typed as a superscript letter o (Q4 bond angles)
    html = re.sub(r"(?<=\d)<sup>o</sup>", "\u00b0", html)
    # a full stop / comma typed inside a charge superscript (F<sup>-.</sup>)
    html = re.sub(r"<sup>([^<]*?[\u2212+])([.,;])</sup>", r"<sup>\1</sup>\2", html)
    # box-drawing dash used as a range dash (Q15 "7 \u2500 11")
    html = html.replace("\u2500", "\u2013")
    # an emptied bold/italic run: keep the word break it carried
    html = re.sub(r"(?<=\S)<b></b>(?=\S)", " ", html)
    html = html.replace("<b></b>", "").replace("<i></i>", "")
    html = re.sub(r'<span class="sr">([IVX]+)([.,;]?) </span>', r'<span class="sr">\1</span>\2 ', html)
    html = re.sub(r"\u00d7(?=\d|<span class=\"frac\")", "\u00d7 ", html)
    return html


def _right(w, txt):
    return ('<span style="display:inline-block;min-width:%.1fem;text-align:right">%s</span>'
            % (w, txt))


# Lines the source aligns with runs of spaces: rebuilt so they align in any
# font. Q30's four half-reactions: the E value lines up in a column.
ALIGN_RULES = {}
ALIGN_MANY = {30: (re.compile(r"^(.+?)<span[^>]*></span>([\u2212+]\d\.\d\d V)$"), 4)}


def _apply_align(qn, out):
    for pat, fn in ALIGN_RULES.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(pat, p)]
        if len(hit) != 1:
            raise RuntimeError("Q%d: align rule %r matched %d block(s)" % (qn, pat, len(hit)))
        out[hit[0]] = ("p", re.sub(pat, fn, out[hit[0]][1]))
    if qn in ALIGN_MANY:
        rx, want = ALIGN_MANY[qn]
        n = 0
        for i, (k, p) in enumerate(out):
            if k == "p" and rx.match(p):
                m = rx.match(p)
                out[i] = ("p", '<span style="display:inline-block;min-width:21em">%s</span>%s'
                          % (m.group(1), m.group(2)))
                n += 1
        if n != want:
            raise RuntimeError("Q%d: align-many matched %d line(s), expected %d" % (qn, n, want))
    return out


LO_RX = re.compile(r"^(Topic\s*:|LO\b)")


def _plain(h):
    return re.sub(r"<[^>]+>", "", h.replace(FIG, "").replace(CENTRE, "")).replace("\u00a0", " ").strip()


# Declared text fixes, applied to the raw block html BEFORE clean(): every one
# must match exactly `count` time(s) in its question or the run raises.
# (qn, old-regex, new, count, why)
TEXT_FIXES = [
    (21, r"C<sub>6</sub>H<sub>5</sub>CH<sub>3</sub> undergoes",
     "Molecule 3, C<sub>6</sub>H<sub>5</sub>CH<sub>3</sub>, undergoes", 1,
     "the sentence now introduces molecule 3 after the wrong alkene paragraph was dropped"),
    # --- school errors, each ruled "correct" by the user (2026-10-23) ---
    (3, r"metaillic", "metallic", 1, "school typo"),
    (3, r"repectively", "respectively", 1, "school typo"),
    (6, r'(?<=fden">)pv(?=</span>)', "pV", 1, "school typo: lowercase v"),
    (7, r"steeper for He\.", "steeper for Ne.", 1, "school error: He should be Ne"),
    (9, r"lattice energy of CoO<sub>2</sub>", "lattice energy of CoO", 1,
     "school error: CoO2 should be CoO"),
    (10, r" - T", " \u2212 T", 1, "ASCII hyphen used as minus"),
    (10, r"= -\u2206", "= \u2212\u2206", 2, "ASCII hyphen used as minus"),
    (10, r"Hence -\u2206", "Hence \u2212\u2206", 1, "ASCII hyphen used as minus"),
    (11, r"</span></span> \(3\)", "</span></span>", 1, "stray '(3)' factor"),
    (13, r"is incorrect\s*$", "is incorrect.", 1, "missing full stop"),
    (16, r"<b><i>\(ii\)</i></b>", "<b><i>1</i></b>", 1,
     "note sits under row 1; school wrote (ii)"),
    (17, r"total number of total number of", "total number of", 1, "school duplication"),
    (19, r"CH<sub>3</sub>CH<sub>2</sub>CH<sub>3</sub>\u2013Br", "CH<sub>3</sub>CH<sub>2</sub>CH<sub>2</sub>\u2013Br", 1,
     "school error: 1-bromopropane is CH3CH2CH2-Br"),
    (28, r'<u>CaC</u>(<i class="el"><u>l</u></i>)<u><sub>2</sub></u>', r"<u>NaC</u>\1", 1,
     "option B is NaCl(aq); school header said CaCl2"),
    (6, r"\(37273\)", "(37+273)", 1,
     "the '+' of (37+273) is lost by the OMML reader; the Word PDF prints it"),
    (19, r"<b>\u2013(117|43)</b>", "<b>\u2212\\1</b>", 2,
     "minus sign: an en dash lets '\u2013 / 117' split across two lines in the narrow cell"),
    (12, r't<sub><span class="frac">.*?</span></span></sub>', "<i>t</i><sub>\u00bd</sub>", 2,
     "t-half is a subscript fraction (1/2) the reader turns into broken sub/frac markup"),
]


def _fix_text(qn, out):
    for q, pat, new, count, _why in TEXT_FIXES:
        if q != qn:
            continue
        n = 0
        for i, (k, p) in enumerate(out):
            if k == "p":
                m = len(re.findall(pat, p))
                if m:
                    n += m
                    out[i] = ("p", re.sub(pat, new, p))
            elif k == "table":
                rows = []
                for row in p:
                    cells = []
                    for cell in row:
                        txt = cell[0]
                        m = len(re.findall(pat, txt))
                        if m:
                            n += m
                            cell = (re.sub(pat, new, txt),) + tuple(cell[1:])
                        cells.append(cell)
                    rows.append(cells)
                out[i] = ("table", rows)
        if n != count:
            raise RuntimeError("Q%d: text fix %r matched %d time(s), expected %d"
                               % (qn, pat, n, count))
    return out


def _drop_lo(qn, out, lo_lines):
    """Drop the school's Topic / LO block (kept in lo_lines for the TAGS stage)."""
    if qn in LO_END:
        hit = [i for i, (k, p) in enumerate(out)
               if k == "p" and re.search(LO_END[qn], _plain(p))]
        if len(hit) != 1:
            raise RuntimeError("Q%d: LO_END %r matched %d block(s)"
                               % (qn, LO_END[qn], len(hit)))
        end = hit[0]
    else:
        i = 0
        while i < len(out) and out[i][0] == "p" and LO_RX.match(_plain(out[i][1])):
            i += 1
        end = i - 1
    if end < 0:
        raise RuntimeError("Q%d: no Topic/LO block found" % qn)
    zone, rest = out[:end + 1], out[end + 1:]
    nfig = sum(p.count(FIG) for k, p in zone if k == "p")
    if nfig != LO_FIGS.get(qn, 0):
        raise RuntimeError("Q%d: %d picture(s) inside the LO block, LO_FIGS says %d"
                           % (qn, nfig, LO_FIGS.get(qn, 0)))
    keep = []
    for k, p in zone:
        if k != "p":
            raise RuntimeError("Q%d: a table inside the LO block" % qn)
        t = _plain(p)
        if t:
            lo_lines.setdefault(qn, []).append(t)
            if qn in LO_KEEP and re.search(LO_KEEP[qn], t):
                keep.append((k, p))
    if qn in LO_KEEP and len(keep) != 1:
        raise RuntimeError("Q%d: LO_KEEP %r matched %d line(s)" % (qn, LO_KEEP[qn], len(keep)))
    return keep + rest


def _rebuild(qn, out):
    """Declared structural rebuilds (each raises if its anchor is missing)."""
    if qn == 4:                           # "1" / "Correct" / text -> a bold lead line
        res, i = [], 0
        while i < len(out):
            k, p = out[i]
            if (k == "p" and re.fullmatch(r"\d", _plain(p)) and i + 1 < len(out)
                    and out[i + 1][0] == "p"
                    and _plain(out[i + 1][1]) in ("Correct", "Incorrect")):
                res.append(("p", "<b>%s&emsp;%s</b>" % (_plain(p), _plain(out[i + 1][1]))))
                i += 2
                continue
            res.append((k, p))
            i += 1
        if len(res) != len(out) - 3:
            raise RuntimeError("Q4: expected to merge 3 number/verdict pairs")
        return res
    if qn == 16:                          # the explanation table, flattened by the reader
        i = next((j for j, (k, p) in enumerate(out)
                  if k == "p" and _plain(p).startswith("Ammonia reacting as")), None)
        if i is None or _plain(out[i + 1][1]) != "Explanation":
            raise RuntimeError("Q16: table header not found")
        head, rows, cur = out[:i], [], None
        for k, p in out[i + 2:]:
            if k != "p":
                raise RuntimeError("Q16: unexpected table")
            t = _plain(p)
            if re.fullmatch(r"\d", t):
                cur = [p, None, []]
                rows.append(cur)
            elif cur is not None and cur[1] is None:
                cur[1] = p
            elif cur is not None:
                cur[2].append(p)
            else:
                raise RuntimeError("Q16: text before row 1")
        if len(rows) != 4 or any(r[1] is None or not r[2] for r in rows):
            raise RuntimeError("Q16: expected 4 complete rows, got %r" % rows)
        tbl = [[("<b>Ammonia reacting as:</b>", 2), ("<b>Explanation</b>", None)]]
        for num, lab, expl in rows:
            tbl.append([(num, None), (lab, None), ("<br>".join(expl), None)])
        return head + [("table", tbl)]
    if qn == 12:
        # two aligned lines -> a table; the three ratio lines -> a table
        seq = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(r"\d+(\.\d+)?% (U|Pb)", _plain(p))]
        if len(seq) != 2 or seq[1] != seq[0] + 1:
            raise RuntimeError("Q12: the U / Pb sequence lines were not found")
        rows = []
        for i in seq:
            t = _plain(out[i][1])
            parts = [x.strip() for x in re.split(r"\s*\u2192\s*", t)]
            if len(parts) != 5:
                raise RuntimeError("Q12: sequence line has %d parts" % len(parts))
            rows.append(parts)
        u = ["<u>6.25%</u> U" if "6.25%" in c else c for c in rows[0]]
        pb = ["<u>93.75%</u> Pb" if "93.75%" in c else c for c in rows[1]]
        tbl = [[(c, None) for c in u], [(c, None) for c in pb]]
        # arrows between the cells are typed as their own column: build explicitly
        def interleave(r):
            cells = []
            for n, c in enumerate(r):
                cells.append((c, None))
                if n < len(r) - 1:
                    cells.append(("\u2192", None))
            return cells
        tbl = [interleave(u), interleave(pb)]
        ratio = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(r"U\s*:\s*Pb|6\.25 %\s*:|0\.0667 : 1", _plain(p))]
        if len(ratio) != 3 or ratio != list(range(ratio[0], ratio[0] + 3)):
            raise RuntimeError("Q12: the ratio lines were not found")
        rt = [[("U", None), (":", None), ("Pb", None)],
              [("6.25 %", None), (":", None), ("93.75 %", None)],
              [("0.0667", None), (":", None), ("1", None)]]
        res = out[:seq[0]] + [("table", tbl)] + out[seq[1] + 1:ratio[0]] + [("table", rt)] + out[ratio[2] + 1:]
        return res
    return out


def prepare(qn, blocks, lo_lines):
    """Pull the key, drop the 'Ans' paragraph and the LO block, apply the
    collapsing rules and the declared rebuilds."""
    key = None
    out = []
    for kind, payload in blocks:
        if kind == "p" and key is None and re.search(r"Ans(?:wer)?\s*:", payload):
            m = _ANS_P.search(payload)
            if not m:
                raise RuntimeError("Q%d: cannot read the answer letter from %r"
                                   % (qn, payload))
            key = m.group(1)
            rest = _ANS_P.sub("", payload, count=1).replace(CENTRE, "")
            if rest.strip():
                out.append(("p", rest.strip() if fig_only(rest) else rest))
            continue
        out.append((kind, payload))
    if key is None:
        raise RuntimeError("Q%d: no 'Ans:' paragraph found" % qn)

    for kind, pat, _why in DROP_BLOCKS.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out)
               if k == kind and (pat is None or re.search(pat, p))]
        if len(hit) != 1:
            raise RuntimeError("Q%d: drop rule %r/%r matched %d block(s), "
                               "expected 1" % (qn, kind, pat, len(hit)))
        del out[hit[0]]

    out = _drop_lo(qn, out, lo_lines)
    out = _fix_text(qn, out)

    # whole table(s) are the user's snip(s)
    if qn in TABLE_SNIPS:
        tidx = [i for i, (k, p) in enumerate(out) if k == "table"]
        if len(tidx) != 1:
            raise RuntimeError("Q%d: TABLE_SNIPS expects exactly one table, found %d"
                               % (qn, len(tidx)))
        out[tidx[0]:tidx[0] + 1] = [("snip", sl) for sl in TABLE_SNIPS[qn]]

    # tidy (layout) then norm (typography), then the declared rebuilds
    out = [(k, clean(p, qn) if k == "p" and FIG not in p else p)
           for k, p in out]
    out = _rebuild(qn, out)
    out = _apply_align(qn, out)

    merged = []
    for kind, payload in out:
        if (kind == "p" and fig_only(payload) and merged
                and merged[-1][0] == "p" and fig_only(merged[-1][1])):
            continue                      # collapse into the previous figure
        if kind == "p" and fig_only(payload):
            payload = FIG                 # one figure, however many objects
        merged.append((kind, payload))
    return key, merged


def wrap_answer(html):
    html = html.strip()
    if not html:
        return ""
    return '<span class="ans">%s</span>' % html


# Pictures that sit IN a line of text rather than in a block of their own.
# index.html forces img.ws-fig to display:block, so these carry an inline style
# (inline styles beat the stylesheet; sizeFig only touches max-width/height).
INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"


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
        if kind == "snip":
            out.append("<p>%s</p>" % img_html(payload))
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

        if "\x00NL\x00" in payload:           # an OMML equation stack: one line each
            for line in payload.replace(CENTRE, "").split("\x00NL\x00"):
                line = clean(line, qn)
                if line.strip():
                    out.append("<p>%s</p>" % wrap_answer(line))
            continue
        centred = payload.startswith(CENTRE)
        text = payload.replace(CENTRE, "")
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
    body = "\n".join(out)
    body, log = corrections.apply(body, SCOPE)
    if log:
        print("Q%d corrections applied: %s" % (qn, log))
    return '<div class="worked-solution">\n%s\n</div>' % body, assets


def pdf_keys(pdf):
    """The 'Answer: X' letters printed in the Word PDF, in page order."""
    import pymupdf
    doc = pymupdf.open(str(pdf))
    text = "\n".join(pg.get_text() for pg in doc)
    return re.findall(r"Ans(?:wer)?:\s*([A-D])\b", text)


LO_LINES = {}


def extract(document_xml, pdf):
    groups = question_groups(document_xml)
    if sorted(groups) != list(range(1, 31)):
        raise RuntimeError("expected questions 1-30, got %s" % sorted(groups))
    keys, ws, assets = {}, {}, []
    for qn in sorted(groups):
        key, blocks = prepare(qn, [b for r in groups[qn] for b in read_blocks(r)], LO_LINES)
        keys[qn] = key
        html, a = render(qn, blocks)
        ws[qn] = html
        for off, (slot, path) in enumerate(a, start=1):
            assets.append({"question": qn, "slot": slot, "path": path,
                           "offset": off})
    pk = pdf_keys(pdf)
    if len(pk) != 30:
        raise RuntimeError("the Word PDF prints %d 'Answer:' letters, expected 30"
                           % len(pk))
    bad = {q: (keys[q], pk[q - 1]) for q in keys if keys[q] != pk[q - 1]}
    if bad:
        raise RuntimeError("answer key disagrees (row, PDF): %r" % bad)
    return ws, assets, keys


if __name__ == "__main__":      # pragma: no cover
    doc, pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    ws, assets, keys = extract(doc, pdf)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_assets.json").write_text(
        json.dumps(assets, indent=2), encoding="utf-8")
    (outdir / "school_lo_lines.json").write_text(
        json.dumps({str(q): v for q, v in sorted(LO_LINES.items())}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in keys.items()}, indent=2),
        encoding="utf-8")
    print("worked solutions: %d" % len(ws))
    print("answer figures:   %d" % len(assets))
    print("answer keys:      %d, row = Word PDF" % len(keys))
