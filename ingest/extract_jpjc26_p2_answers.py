"""JPJC 2026 H2 P2 -- worked solutions from the "suggested solutions" docx.

Adapted from extract_hci_p2_answers.py (same parts.py table adapter and the
marker-zone technique, section 20 of HANDOFF). The solutions docx IS the
question paper (JC2 Prelim 9729/02), with the answers typed into the same SEAB
grid: blue 0000FF / 3333FF / 0033CC = answer, red FF0000 = marker note, green
538135 = "Examiner's comments" (not emitted, standing ruling). Differences
from HCI: the grid is split across ELEVEN tables (one per page-run) and is as
irregular as the question table, so `jpjc_p2_prep.py --multi` squares every
table up first (spans 1,1,1,8,1); the Word comments (teacher edit notes) are not
read at all.

Usage:
  python3 -m ingest.jpjc_p2_prep <unz> <unz_prep> --multi
  python3 -m ingest.extract_jpjc_p2_answers <unz_prep> <questions.json> <outdir>
Output feeds the answers migration generator (see HANDOFF).
"""
from __future__ import annotations

import argparse
import os
import json
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from . import parts_dispatch
from .parts import _strip_answer_dots
from .oxml import NS, Wq

SCOPE = ("JPJC", "H2", "P2", 2026)
FIG = "\x00FIG\x00"
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"

#: Examiner "Comments" rows are parsed but NOT emitted (user decision 2026-09-30:
#: no examiner comments; the red "DNA:" marker notes are kept).
INCLUDE_COMMENTS = False

BLUE = "0000FF"
RED = "FF0000"
GREEN = "538135"
#: a run is ANSWER text in any of these blues (the file mixes three)
ANSWER_BLUES = ("0000FF", "3333FF", "0033CC")
#: unmarked picture paragraphs that ARE answer figures: (table, row, direct-paragraph index)
#: (table numbers are those of the squared-up docx, cover table = 0). Filled from DISCOVER.
ANS_FIG = {
    (1, 4, 1),                 # Q1(a)(ii): the energy cycle (ChemSketch object)
    (1, 31, 0),                # Q2(b)(ii): the two monomers (two ChemSketch objects)
    (2, 23, 0), (2, 24, 0),    # Q3(e)(i): the SF6 / CO2 (600 K) graph (shapes + picture)
    (4, 4, 0),                 # Q5(a)(ii): compound B
    (4, 6, 9), (4, 6, 14),     # Q5(b): the step 2 and step 3 schemes
    (4, 18, 0),                # Q6(a): n = pV/RT equation (typed in black, no colour)
    (4, 25, 0),                # Q6(b)(ii): the two isomers
    (4, 28, 0),                # Q6(c): structures of X, Y and Z
}
FORCE_A = set()
DROP = set()
#: paragraphs that look like answers by colour but are question content: (table, row, para)
FORCE_Q = {(1, 19, 15)}        # Fig 2.1 intro cell: the school's blue/red overlay (answer figure, snipped for (a)(i))
#: whole rows that are QUESTION text although they carry blue runs (the minus of SCN- in 4(d)):
QROWS = {(3, 12), (3, 13)}
LABEL_MAP = {(5, "(d)"): "(c)", (5, "(c)"): "(d)"}   # the bank relabelled Q5 (c) Hueckel, (d) phenol (user ruling)

def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


_SQ = lambda inner: '<span class="sqrt"><span class="rad">%s</span></span>' % inner


#: slot -> JPJC_H2_P2_Q<n>_ans-<slot>_2026.png. n_fig counts the FIG sentinels the parser finds
#: in the part's MARKED blocks (0 = the picture sits in question content and is added in front).
FIGURE_PLAN = {
    (1, "(a)(ii)"): dict(slots=["aii"], n_fig=1, mode="marked", fill=["@!aii"]),   # energy cycle
    (2, "(a)(i)"):  dict(slots=["ai"], n_fig=0, mode="lead_text"),                # Fig 2.1 with the construction lines
    (2, "(b)(ii)"): dict(slots=["bii"], n_fig=1, mode="lead_text"),               # the two monomers
    (3, "(e)(i)"):  dict(slots=["ei"], n_fig=2, mode="lead_text"),
    (4, "(c)"):     dict(slots=["c"], n_fig=1, mode="marked", fill=["@!c"]),      # the cell diagram
    (5, "(a)(ii)"): dict(slots=["aii"], n_fig=1, mode="lead_text"),               # compound B
    (5, "(b)"):     dict(slots=["b2", "b3"], n_fig=2, mode="each"),               # steps 2 and 3
    (6, "(b)(ii)"): dict(slots=["bii"], n_fig=1, mode="marked", fill=["@!bii"]),
    (6, "(c)"):     dict(slots=["c"], n_fig=1, mode="marked", fill=["@!c"]),
}
_KF = "<i>k</i><sub>f</sub>"
_KB = "<i>k</i><sub>b</sub>"
_HCO = "[HCO<sub>3</sub><sup>\u2212</sup>]"
_CO = "[CO<sub>3</sub><sup>2\u2212</sup>]"
#: MathType equation objects (no text in the docx): typed here, in DOM order
SENTINEL_FILL = {
    (2, "(a)(iv)"): [_frac("Rate", "[0.015][0.150]")],
    (3, "(a)(iii)"): [_frac(_CO, _HCO), _frac(_HCO, _CO), _frac(_HCO, _CO)],
    (3, "(b)"): ["HCO<sub>3</sub><sup>\u2212</sup>, which is the conjugate base of carbonic acid",
                 "the conjugate base of 2-chlorophenol",
                 "the conjugate base of 2-chlorophenol ",
                 "HCO<sub>3</sub><sup>\u2212</sup>"],
    (3, "(c)(ii)"): ["\u21cc", "\u21cc"],
    (6, "(a)"): ["<i>n</i> = " + _frac("<i>pV</i>", "<i>RT</i>") + " = "
                 + _frac("103.875 \u00d7 10<sup>3</sup> \u00d7 100 \u00d7 10<sup>\u22126</sup>", "8.31 \u00d7 (227 + 273)"),
                 _frac("0.250", "2.50 \u00d7 10<sup>\u22123</sup>")],
}
#: user rulings pending / taken (flip when the user rules): see the delivery note
KSP_FIX = True       # Q3(c)(i): 8.34 -> 8.39 x 10^-12 (4 x (1.28e-4)^3 = 8.39e-12)
E3_NOTE = True       # Q3(e)(iii): add "See the graph in (e)(i)."
#: parts whose answer is a MathType/oMath block the parser cannot read: typed from the PDF
TYPED = {
    (4, "(b)(iii)"): [
        "<i>E</i> = <i>E</i><sup>\u03b8</sup> + " + _frac("0.0592", "<i>n</i>") + " log<sub>10</sub>("
        + _frac("[oxidised form]", "[reduced form]") + ")",
        "= +0.772 + " + _frac("0.0592", "1") + " log<sub>10</sub>(" + _frac("0.00250", "0.100") + ")",
        "= +0.677 V"],
}
TEXT_FIXES = {
    (1, "(a)(ii)"): [(r"= -L\.E \+ \[-1950 \+ 2\(-380\)\] = -80\.0", "= \u2212L.E + [\u22121950 + 2(\u2212380)] = \u221280.0"),
                     (r"\(s\) =\u22122630", "(s) = \u22122630")],
    (1, "(a)(iii)"): [(r"\) x 0\.01 = mc", ") \u00d7 0.01 = mc"),
                      (r"\(80 x 1000\) x 0\.01 = \(100x 4\.18 x\u2206T\)", "(80 \u00d7 1000) \u00d7 0.01 = (100 \u00d7 4.18 \u00d7 \u2206T)"),
                      (r"26\.9\u00b0C", "26.9 \u00b0C")],
    (1, "(a)(iv)"): [(r"298K", "298 K")],
    (1, "(c)"): [(r"<sup>\u03b8</sup>= ", "<sup>\u03b8</sup> = "),
                 (r"\+1\.07 \u2013 \(\+1\.89\) = \u20130\.82", "+1.07 \u2212 (+1.89) = \u22120.82")],
    (2, "(a)(i)"): [(r"</?i>", ""),
                    (r"= k(?=[ \[\u2019])", "= <i>k</i>"),
                    (r"<sup>([xy])</sup>", r"<sup><i>\1</i></sup>"),
                    (r"pseudo x<sup>th</sup>", "pseudo <i>x</i><sup>th</sup>"),
                    (r"\(accept 10-10\.50\)", "(accept 10\u201310.50)"),
                    (r"ie\. x =1\.", "i.e. <i>x</i> = 1.")],
    (2, "(a)(ii)"): [(r"\[0-0\.015\]", "[0\u22120.015]"), (r"\[14\.5-0\]", "[14.5\u22120]"),
                     (r"at t = 0 min", "at <i>t</i> = 0 min")],
    (2, "(a)(iii)"): [(r"(\[OH<sup>[^<]*</sup>\]) x 1\.5", "\\1 \u00d7 1.5"),
                      (r"the rate x1\.5", "the rate \u00d7 1.5")],
    (3, "(a)(ii)"): [(r"with shift", "will shift")],
    (3, "(a)(iii)"): [(r"<sub>a2</sub> \u2013 pH", "<sub>a2</sub> \u2212 pH"),
                      (r'lg(<span class="frac">)', r"lg \1")],
    (3, "(b)"): [(r"However, the anion the conjugate", "However, the conjugate")],
    (3, "(c)(i)"): [(r"= 4 x \(", "= 4 \u00d7 (")],
    (4, "(b)(i)"): [(r"\+0\.772V", "+0.772 V")],
    (4, "(b)(ii)"): [(r"\(-2\.0, 0\.653\)", "(\u22122.0, 0.653)"),
                     (r"0\.889-0\.653", "0.889 \u2212 0.653"),
                     (r"2\.0-\(-2\.0\)", "2.0 \u2212 (\u22122.0)"),
                     (r"</span>=0\.0590", "</span> = 0.0590"),
                     (r"Hence, n = ", "Hence, <i>n</i> = ")],
    (4, "(c)"): [(r'<span class="sr">I</span>', "I"), (r"<sup>\s*[^<\s]\s*</sup>(?=\(aq\))", "<sup>\u2212</sup>")],
    (4, "(d)(i)"): [(r"(SCN<sup>[^<]*</sup>)\s*react with", "\\1 reacts with"),
                    (r"to decreases", "to decrease"),
                    (r"Fe<sup>3\+</sup>decreases", "Fe<sup>3+</sup> decreases")],
    (4, "(d)(ii)"): [(r"<sub>Fe3\+/Fe2\+</sub>", "<sub>Fe<sup>3+</sup>/Fe<sup>2+</sup></sub>"),
                     (r"<sub>I2/I[^<]</sub>", "<sub>I<sub>2</sub>/I<sup>\u2212</sup></sub>")],
    (5, "(a)(i)"): [(r'Step <span class="sr">([IV]+): </span>', r"Step \1: "), (r"50<sup>o</sup>C", "50 \u00b0C")],
    (5, "(b)"): [(r"^\+$", ""),
                 (r"CH<sub>3</sub>CH<sub>2</sub>CO \+ A", "CH<sub>3</sub>CH<sub>2</sub>CO<sup>+</sup> + A")],
    (5, "(c)"): [(r"<i> </i>", " "), (r"\u03c0electrons", "\u03c0 electrons"),
                 (r"([46]) = 4n \+ 2", r"\1 = 4<i>n</i> + 2"), (r"where n = ", "where <i>n</i> = "),
                 (r"^\s+", "")],
    (6, "(a)"): [(r"\bMr =", "<i>M</i><sub>r</sub> =")],
}
OL_PARTS = set()

#: Marking-criteria lines are emitted as red notes (span.note), model-answer text stays blue
#: (span.ans) -- user request 2026-10-14. Rule 1: any line that STARTS with a mark token
#: ([1], [1/2], [0.5], [-0.5] ...) is a criteria line. Rule 2 (NOTE_LINES): criteria lines that do
#: not start with a mark; (qnum, label) -> [regex on the block text]; each must match >= 1 block.
MARK_START = re.compile(r"\s*(?:<b>)?\s*\[\s*(?:[\u2013\u2212\-]?\d+(?:\.\d+)?|\d/\d)\b")
NOTE_LINES = {}

#: Post-assembly fixes on a question's whole worked-solution html: qnum -> [(regex, replacement, expected_count)].
POST_FIXES = {
    3: [(r'</ul>\n<ul class="stmts">', "", 3),
        # (a)(ii): the space after the bracket sat in an empty superscript
        (r'\]drops', '] drops', 1),
        (r'build /maintain', 'build/maintain', 1)],
    4: [(r'(<p><span class="ans">From the equation provided,</span></p>)',
         r'\1\n<p><span class="ans"><i>gradient</i> = ' + _frac("0.0592", "<i>n</i>").replace("\\", "\\\\") + '</span></p>', 1)],
    6: [(r'<p><span class="ans">trans isomer cis isomer</span></p>\n?', "", 1),
        (r'\n<p><span class="ans">Compound X Compound Y Compound Z</span></p>', "", 1)],
}
NOTE_TEXT = {}
AR, EQ = " \u2192 ", " \u21cc "




#: Superscript signs: the paper types en dashes and hyphens; the minus sign is
#: U+2212 (the question side uses both, so one rule is applied here).
def _sup_minus(t):
    return re.sub(r"<sup>([^<]*)</sup>",
                  lambda m: "<sup>%s</sup>" % re.sub(r"[\u2013\-](?=\d|$|\s)", "\u2212", m.group(1)), t)


def _txt(el):
    return "".join(el.itertext(Wq + "t"))


def _blue(r):
    c = r.find("w:rPr/w:color", NS)
    return c is not None and (c.get(Wq + "val") or "").upper() == BLUE


def _has_fig(el):
    return any(etree.QName(x).localname in ("drawing", "object", "pict")
               for x in el.iter())


def _vis_colours(tr):
    out = set()
    for rr in tr.iter(Wq + "r"):
        if _txt(rr).strip():
            c = rr.find("w:rPr/w:color", NS)
            out.add((c.get(Wq + "val") or "").upper() if c is not None else "")
    return out


#: Rows whose "(iv)" label sits in ONE merged label cell (gridSpan 2 or 3) instead of the
#: letter + roman slots, so `parts.py` never sees a new part and folds the row into the
#: previous one: row index -> (letter to supply, roman text, expected gridSpan).
#: Splitting is on the in-memory copy; each entry must match or it raises.
LABEL_CELL_FIX = {}


def _fix_label_cells(tbl):
    import copy as _copy
    rows = tbl.findall("w:tr", NS)
    for ri, (letter, roman, span) in LABEL_CELL_FIX.items():
        tcs = rows[ri].findall("w:tc", NS)
        hit = [tc for tc in tcs if _txt(tc).strip() == roman]
        gs = hit[0].find("w:tcPr/w:gridSpan", NS) if hit else None
        got = int(gs.get(Wq + "val")) if gs is not None else 1
        if len(hit) != 1 or got != span or tcs.index(hit[0]) > 1:
            raise SystemExit("LABEL_CELL_FIX row %d: label cell %r span %s not as declared"
                             % (ri, roman, got))
        old = hit[0]
        def mk(text):
            c = _copy.deepcopy(old)
            g = c.find("w:tcPr/w:gridSpan", NS)
            if g is not None:
                c.find("w:tcPr", NS).remove(g)
            for t in list(c.iter(Wq + "t")):
                t.text = ""
            for r in list(c.iter(Wq + "r")):
                r.getparent().remove(r)
            if text:
                p = next(c.iter(Wq + "p"))
                rr = etree.SubElement(p, Wq + "r")
                etree.SubElement(rr, Wq + "t").text = text
            return c
        new = ([mk("")] if span == 3 else []) + [mk(letter), mk(roman)]
        for n in new:
            old.addprevious(n)
        old.getparent().remove(old)


def _run_colour(rr):
    c = rr.find("w:rPr/w:color", NS)
    return (c.get(Wq + "val") or "").upper() if c is not None else ""


def _para_zone(p):
    """'A' answer, 'N' red marker note, 'C' green examiner comment, '' = question."""
    blue = red = green = tot = 0
    for rr in p.iter(Wq + "r"):
        tx = _txt(rr).strip()
        if not tx:
            continue
        v = _run_colour(rr)
        tot += 1
        blue += v in ANSWER_BLUES
        red += v == RED
        green += v == GREEN
    if not tot:
        return ""
    if blue:
        return "A"
    if red == tot:
        return "N"
    if green == tot:
        return "C"
    return ""


def mark_zones(src_document_xml: Path, dst_document_xml: Path):
    """Write a marked copy of document.xml; return a per-paragraph zone log.

    Zones are decided PER PARAGRAPH by run colour (the rows mix question text
    and answers); the qnum/letter/roman label cells are never touched.
    """
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    assert len(tables) >= 3, len(tables)
    log = []
    used_fig = set()
    for ti, tbl in enumerate(tables):
        if ti == 0:
            continue                      # cover page
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            tcs = tr.findall("w:tc", NS)
            content = tcs[3]
            direct = content.findall("w:p", NS)
            for p in content.iter(Wq + "p"):
                pi = direct.index(p) if p in direct else None
                top = p
                while top not in direct and top.getparent() is not None and top.getparent() is not content:
                    top = top.getparent()
                topi = direct.index(top) if top in direct else None
                zone = _para_zone(p)
                key = (ti, ri, pi)
                if key in ANS_FIG:
                    zone = "A"
                    used_fig.add(key)
                if (ti, ri, topi) in FORCE_Q or (ti, ri) in DROP or (ti, ri) in QROWS:
                    zone = ""
                if zone:
                    mk = {"A": MA, "N": MN, "C": MC}[zone]
                    r = etree.Element(Wq + "r")
                    etree.SubElement(r, Wq + "t").text = mk
                    ppr = p.find("w:pPr", NS)
                    p.insert(0 if ppr is None else 1, r)
                    log.append((ti, ri, pi, zone, _txt(p).strip()[:50]))
    if used_fig != ANS_FIG:
        raise SystemExit("ANS_FIG entries not found: %s" % sorted(ANS_FIG - used_fig))
    tree.write(str(dst_document_xml), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


def _clean(line: str) -> str:
    line = re.sub("[⁣]?[ANC][⁣]", "", line)
    line = line.replace("\x00C\x00", " ").replace("\t", " ")
    line = re.sub(r"\s*<br>\s*", " ", line).strip()
    line = _strip_answer_dots(line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


NL = "\x02NL\x02"


def split_part(html: str):
    """-> (answer_blocks, comment_items).

    `answer_blocks` is a list of ('p'|'ul', html, is_note) in DOM order.
    A `<ul>` group holds its own <li> items, each with a zone marker.
    A Word table is ONE block: its cell paragraphs arrive as separate lines, so
    the lines from `<table` to `</table>` are joined (NL tokens become <br>).
    """
    blocks, comments = [], []
    lines, buf = [], None
    for line in html.split("\n"):
        if buf is not None:
            buf.append(line)
            if "</table>" in line:
                lines.append(NL.join(buf))
                buf = None
            continue
        if line.lstrip().startswith("<table") and "</table>" not in line:
            buf = [line]
            continue
        lines.append(line)
    if buf is not None:
        lines.append(NL.join(buf))
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("<ul"):
            items = re.findall(r"<li>(.*?)</li>", s, flags=re.S)
            marked = [i for i in items if MA in i or MN in i]
            a_items = [_clean(i) for i in marked]
            c_items = [_clean(i) for i in items if MC in i]
            if a_items:
                blocks.append(("ul", a_items, all(MN in i and MA not in i for i in marked)))
            comments.extend(c_items)
            continue
        if s.startswith("<table"):
            if MA in s or MN in s:
                # a cell holding a marked paragraph is an ANSWER cell (given cells stay plain)
                s = re.sub(r"<td([^>]*)>((?:(?!</td>).)*?%s(?:(?!</td>).)*?)</td>" % re.escape(MA),
                           lambda m: '<td%s><span class="ans">%s</span></td>' % (m.group(1), m.group(2)),
                           s, flags=re.S)
                body = _clean(s).replace(NL, "<br>")
                body = re.sub(r"(<br>\s*){2,}", "<br>", body)
                body = re.sub(r"(<td[^>]*>)\s*<br>|<br>\s*(</td>)", r"\1\2", body)
                blocks.append(("p", body, False))
            continue
        if MC in s:
            body = _clean(s)
            if re.fullmatch(r"(<[^>]+>)*Comments(</[^>]+>)*", body):
                continue
            if body:
                comments.append(body)
        elif MN in s:
            blocks.append(("p", _clean(s), True))
        elif MA in s:
            blocks.append(("p", _clean(s), False))
    return blocks, comments


def _img(path):
    return '<img class="ws-fig" data-asset="%s" alt="">' % path


def build(unz: Path, outdir: Path, bank_questions: list, first_ordinals: dict,
          workdir: Path):
    """-> (worked: {qnum: html}, assets: [...], report: [str])"""
    report = []
    marked = workdir / "marked"
    if marked.exists():
        shutil.rmtree(marked)
    shutil.copytree(unz, marked)
    zlog = mark_zones(unz / "word/document.xml", marked / "word/document.xml")

    numbering = marked / "word/numbering.xml"
    questions, _figs, anomalies, shape = parts_dispatch.parse(
        marked / "word/document.xml", marked / "word/_rels/document.xml.rels",
        numbering if numbering.exists() else None, scope=SCOPE)
    report.append("container shape: %s; %d questions parsed" % (shape, len(questions)))

    bank_labels = {q["question_number"]: [p["label"] for p in q["parts"]]
                   for q in bank_questions}
    bank_marks = {(q["question_number"], p["label"]): p["marks"]
                  for q in bank_questions for p in q["parts"]}

    worked, assets = {}, []
    used_plan = set()
    for q in questions:
        blocks_out = []
        seen_labels = set()
        for p in q.parts:
            label = LABEL_MAP.get((q.qnum, p.label), p.label)
            blocks, comments = split_part(p.html)
            key = (q.qnum, label)
            plan = FIGURE_PLAN.get(key)
            if key in TYPED and not blocks:
                blocks = [("p", ln, False) for ln in TYPED[key]]
            if key == (3, "(e)(iii)") and E3_NOTE and not blocks:
                blocks = [("p", "See the graph in (e)(i).", True)]
            if not blocks and not comments and not plan:
                continue
            if label not in bank_labels.get(q.qnum, []):
                report.append("!! Q%d %s: answer part has no bank part" % (q.qnum, label))
                continue
            if label in seen_labels:
                report.append("!! Q%d %s: duplicate answer part" % (q.qnum, label))
            seen_labels.add(label)

            fn = lambda s, qn=q.qnum: "JPJC_H2_P2_Q%d_ans-%s_2026.png" % (qn, s)
            # ---- figure handling ----
            n_sent = sum(b[1].count(FIG) if b[0] == "p"
                         else sum(i.count(FIG) for i in b[1]) for b in blocks)
            fill_list = (plan["fill"] if plan and plan["mode"] == "marked"
                         else SENTINEL_FILL.get(key))
            if plan:
                used_plan.add(key)
                if n_sent != plan["n_fig"]:
                    raise SystemExit("Q%d%s: expected %d FIG sentinels in the "
                                     "answer, parser found %d"
                                     % (q.qnum, label, plan["n_fig"], n_sent))
                if plan["mode"] == "marked" and len(fill_list) != n_sent:
                    raise SystemExit("Q%d%s: fill has %d entries for %d sentinels"
                                     % (q.qnum, label, len(fill_list), n_sent))
            elif key in SENTINEL_FILL:
                if n_sent != len(SENTINEL_FILL[key]):
                    raise SystemExit("Q%d%s: SENTINEL_FILL has %d entries, parser "
                                     "found %d sentinels" % (q.qnum, label,
                                     len(SENTINEL_FILL[key]), n_sent))
            elif n_sent:
                if os.environ.get("DISCOVER"):
                    report.append("?? Q%d%s: %d FIG sentinel(s): %s" % (q.qnum, label, n_sent,
                        " | ".join(re.sub(r"<[^>]+>", "", b[1] if b[0] == "p" else " ".join(b[1])).replace(FIG, "<FIG>")[:90] for b in blocks)))
                else:
                    raise SystemExit("Q%d%s: %d undeclared FIG sentinel(s) in the "
                                     "answer" % (q.qnum, label, n_sent))

            if fill_list is not None:
                reps = iter(fill_list)
                def sub(_m, reps=reps):
                    return next(reps)
                new = []
                for kind, body, note in blocks:
                    if kind == "p":
                        body = re.sub(re.escape(FIG), sub, body)
                    else:
                        body = [re.sub(re.escape(FIG), sub, i) for i in body]
                    new.append((kind, body, note))
                blocks = new
                if list(reps):
                    raise SystemExit("Q%d%s: unused SENTINEL_FILL entries" % (q.qnum, label))
                # "@!slot" -> the whole block that holds it is the image;
                # "@slot" -> an inline image
                new, last = [], None
                for kind, body, note in blocks:
                    if kind == "p" and not body.strip():
                        new.append((kind, body, note))   # empty spacer: transparent to the collapse
                        continue
                    if kind == "p" and re.search(r"@!([\w-]+)", body):
                        slot = re.search(r"@!([\w-]+)", body).group(1)
                        if slot != last:
                            new.append(("p", "<p>%s</p>" % _img(fn(slot)), False))
                        last = slot
                        continue
                    last = None
                    if kind == "p":
                        body = re.sub(r"@([\w-]+)", lambda m: _img(fn(m.group(1))), body)
                    new.append((kind, body, note))
                blocks = new

            if os.environ.get("DUMP") == "%d%s" % (q.qnum, label):
                for _b in blocks:
                    print("DUMP", repr(_b))
            blocks = [(k, b.replace("\u200b", "") if k == "p" else [i.replace("\u200b", "") for i in b], n)
                      for k, b, n in blocks]
            if key == (3, "(c)(i)") and KSP_FIX:
                TEXT_FIXES.setdefault(key, []).append((r"8\.34 ([x\u00d7])", "8.39 \\1"))
            for rx, rep in TEXT_FIXES.get(key, []):
                hit = False
                new = []
                for kind, body, note in blocks:
                    if kind == "p":
                        nb, n = re.subn(rx, rep, body)
                        hit |= bool(n)
                        body = nb
                    new.append((kind, body, note))
                if not hit:
                    if os.environ.get("SOFTFIX"):
                        report.append("?? Q%d%s: TEXT_FIXES pattern did not match: %s" % (q.qnum, label, rx))
                        continue
                    raise SystemExit("Q%d%s: TEXT_FIXES pattern did not match: %s"
                                     % (q.qnum, label, rx))
                blocks = new

            # fills may carry several lines ("\n"): one block each
            exp = []
            for kind, body, note in blocks:
                if kind == "p" and "\n" in body:
                    exp += [("p", ln, note) for ln in body.split("\n")]
                else:
                    exp.append((kind, body, note))
            blocks = exp
            # house sign conventions
            def _fx(t):
                t = t.replace("\uf02d", "")     # a Symbol minus typed after a hyphen minus (shows as a box in Word)
                t = _sup_minus(t)
                t = "".join(pc if pc.startswith("<") else re.sub(r" {2,}", " ", pc)
                            for pc in re.split(r"(<[^>]+>)", t))
                return t.replace("<sup>\u29b5</sup>", '<sup class="pl-sym">\u29b5</sup>')
            blocks = [(k, _fx(b) if k == "p" else [_fx(i) for i in b], n)
                      for k, b, n in blocks]

            # ---- plain "[n]" marks join the styled ones (the source types both) ----
            _plain = lambda t: re.sub(
                r'(<span class="mk">\[\d\]</span>)|(?<![\w\[])\[([1-9])\](?![\w\]])',
                lambda m: m.group(1) or '<span class="mk">[%s]</span>' % m.group(2), t)
            blocks = [(k, (_plain(b) if not n else b) if k == "p"
                       else [_plain(i) for i in b], n)
                      for k, b, n in blocks]
            # ---- trailing redundant part-mark ----
            marks = bank_marks.get(key)
            mk_all = []
            for kind, body, note in blocks:
                if kind == "p" and not note:
                    mk_all += re.findall(r'<span class="mk">\[(\d+)\]</span>', body)
            if mk_all and marks is not None and any(int(x) != marks for x in mk_all):
                report.append("!! Q%d %s: the answer shows mark(s) %s, the question part is [%s]"
                              % (q.qnum, label, mk_all, marks))
            if len(mk_all) == 1 and marks is not None and int(mk_all[0]) == marks:
                blocks = [(k, re.sub(r'\s*<span class="mk">\[\d+\]</span>', "", b)
                           if k == "p" and not n else b, n) for k, b, n in blocks]
            blocks = [(k, re.sub(r'<span class="mk">(\[\d+\])</span>', r"\1", b)
                       if k == "p" else b, n) for k, b, n in blocks]
            blocks = [(k, b, n) for k, b, n in blocks
                      if (k == "ul" and b) or (k == "p" and b.strip())]

            # ---- render ----
            body_html = []
            mode = plan["mode"] if plan else None
            if mode == "bare":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = []
            elif mode in ("lead_text", "lead_notes"):
                labs = plan.get("labels") or [None] * len(plan["slots"])
                for sl, lb in zip(plan["slots"], labs):
                    if lb:
                        body_html.append("<p><b>%s</b></p>" % lb)
                    body_html.append("<p>%s</p>" % _img(fn(sl)))
                # HCI: a lead_text part keeps its <ul> mark-scheme bullets too
                blocks = [(k, b, n) for k, b, n in blocks
                          if (k == "ul" and mode == "lead_text") or
                          (k == "p" and FIG not in b
                           and (mode == "lead_text" or n)
                           and not re.fullmatch(r"\s*or\s*", b, flags=re.I))]
            elif mode == "each":
                slots = iter(plan["slots"])
                new = []
                for kind, body, note in blocks:
                    if kind == "p" and FIG in body:
                        # the picture on its own line, the text around it after/before
                        pieces = re.split("(%s)" % re.escape(FIG), body)
                        for pc in pieces:
                            if pc == FIG:
                                new.append(("p", _img(fn(next(slots))), note))
                            elif pc.strip():
                                new.append(("p", pc.strip(), note))
                        continue
                    new.append((kind, body, note))
                blocks = new
            # ---- marking-criteria lines -> red notes (see MARK_START / NOTE_LINES) ----
            def _txt_of(k, b):
                return b if k == "p" else " | ".join(b)
            blocks = [(k, b, True if (k == "p" and not n and not b.lstrip().startswith("<table")
                                      and MARK_START.match(b)) else n) for k, b, n in blocks]
            for rx in NOTE_LINES.get(key, []):
                hit = False
                nb = []
                for k, b, n in blocks:
                    first = b if k == "p" else (b[0] if b else "")
                    if not n and re.search(rx, first) and not first.lstrip().startswith("<table"):
                        n, hit = True, True
                    nb.append((k, b, n))
                if not hit:
                    raise SystemExit("Q%d%s: NOTE_LINES pattern matched no block: %s" % (q.qnum, label, rx))
                blocks = nb
            # a lone red "[n]" note equal to a one-mark part is the part mark again
            if marks == 1 and not mk_all:
                lone = [b for b in blocks if b[0] == "p" and b[2]
                        and re.fullmatch(r"\s*\[1\]\s*", b[1])]
                others = [b for b in blocks if b[0] == "p" and b[2] and b not in lone
                          and re.search(r"\[\d\]", b[1])]
                if len(lone) == 1 and not others and not any(
                        b[0] == "p" and not b[2] and re.search(r"\[\d\]", b[1])
                        for b in blocks):
                    blocks = [b for b in blocks if b not in lone]

            if key in NOTE_TEXT:
                hit = [i for i, b in enumerate(blocks)
                       if b[0] == "p" and b[2] and re.fullmatch(r"\s*\[\d\]\s*", b[1])]
                if len(hit) != 1:
                    raise SystemExit("Q%d%s: NOTE_TEXT needs exactly one lone red mark"
                                     % (q.qnum, label))
                blocks[hit[0]] = ("p", NOTE_TEXT[key], True)
            # tables (1(a)(i)): a comparison table, values in answer spans
            def _table(t):
                t = t.replace('class="qt"', 'class="cmp"')
                t = re.sub(r"</?b>", "", t)
                t = re.sub(r"(<br>\s*)+(</td>)", r"\2", t)
                t = re.sub(r"(</ul>)(\s*<br>)+|(<br>\s*)+(<ul)", lambda m: m.group(1) or m.group(4), t)
                t = re.sub(r"<td>(?=[^<]*\w)(.*?)</td>",
                           lambda m: "<td>%s</td>" % m.group(1), t)
                # answer cells (carry a [0.5] mark, or the "-" fill-ins) -> blue; given cells stay plain
                t = re.sub(r"<td([^>]*)>((?:(?!</td>).)*?\[0\.5\](?:(?!</td>).)*?)</td>",
                           r'<td\1><span class="ans">\2</span></td>', t, flags=re.S)
                t = re.sub(r"<td([^>]*)>-</td>", r'<td\1><span class="ans">-</span></td>', t)
                return t
            for kind, body, note in blocks:
                def wrap(t, note=note):
                    if re.fullmatch(r"\s*(<p>)?\s*<img[^>]*>\s*(</p>)?\s*", t):
                        return re.sub(r"</?p>", "", t).strip()
                    return '<span class="%s">%s</span>' % ("note" if note else "ans", t)
                if kind == "p" and body.lstrip().startswith("<table"):
                    body_html.append(_table(body.strip()))
                elif kind == "p":
                    body_html.append("<p>%s</p>" % wrap(body))
                else:
                    body_html.append('<ul class="stmts">%s</ul>'
                                     % "".join("<li>%s</li>" % wrap(i) for i in body))
            if comments and INCLUDE_COMMENTS:
                body_html.append('<p class="mark-note"><b>Comments</b></p>')
                body_html.append('<ul class="marks mark-note">%s</ul>'
                                 % "".join("<li>%s</li>" % c for c in comments))
            if key in OL_PARTS:
                items = re.findall(r'<p><span class="ans">(.*?)</span></p>', "\n".join(body_html), flags=re.S)
                assert len(items) == len(body_html), (key, len(items), len(body_html))
                body_html = ['<ol class="stmts">%s</ol>' % "".join("<li><span class=\"ans\">%s</span></li>" % i for i in items)]
            blocks_out.append(
                '<div class="part"><span class="lab">%s</span>'
                '<div class="body">%s</div></div>' % (label, "\n".join(body_html)))

            if plan:
                for k, s in enumerate(plan["slots"]):
                    assets.append(dict(question=q.qnum, slot="ans-" + s,
                                       path=fn(s), part=label))
        # every bank part that carries marks must have an answer
        missing = [l for l in bank_labels.get(q.qnum, [])
                   if l not in seen_labels and bank_marks.get((q.qnum, l))]
        if missing:
            report.append("!! Q%d: bank parts with marks but no answer: %s" % (q.qnum, missing))
        _ord = {l: i for i, l in enumerate(bank_labels.get(q.qnum, []))}
        blocks_out = [b for _, b in sorted(((_ord.get(re.search(r'class="lab">([^<]*)<', b).group(1), 99), b) for b in blocks_out), key=lambda x: x[0])]
        html_q = "\n".join(blocks_out)
        html_q = re.sub(r"<(sup|sub)> </\1>", "", html_q)           # empty spacer scripts
        html_q = re.sub(r'<p><span class="ans"><b> </b></span></p>\n?', "", html_q)
        html_q = re.sub(r"<b></b>", "", html_q)                       # empty bold runs
        html_q = re.sub(r"(<(sup|sub)>[^<]*?)\s+(</\2>)", r"\1\3 ", html_q)   # space inside a script -> after it
        html_q = re.sub(r"(\d) x (10<sup>)", "\\1 \u00d7 \\2", html_q)      # typed "x" -> multiplication sign
        html_q = re.sub(r" {2,}", " ", html_q)
        # the source sets "C3H8" / "H2O" / "H2" as ONE subscript on P (digits not lowered
        # again): nest the digits so P<sub>C<sub>3</sub>H<sub>8</sub></sub> reads correctly
        html_q = re.sub(r"<sub>((?:[A-Z][a-z]?\d*)+)</sub>",
                        lambda m: "<sub>%s</sub>" % re.sub(r"(\d+)", r"<sub>\1</sub>", m.group(1))
                        if re.search(r"\d", m.group(1)) else m.group(0), html_q)
        html_q = html_q.replace("\u200b", "")
        html_q = html_q.replace("<sup>\u03b8</sup>", '<sup class="pl-sym">\u29b5</sup>')       # theta -> the house standard-state sign
        html_q = re.sub(r"(<i>[GH]</i>)\u00b0(<sub>)", lambda m: m.group(1) + '<sup class="pl-sym">\u29b5</sup>' + m.group(2), html_q)
        for rx, rep, cnt in POST_FIXES.get(q.qnum, []):
            html_q, n = re.subn(rx, rep, html_q)
            if n != cnt:
                raise SystemExit("Q%d POST_FIXES %r matched %d, expected %d" % (q.qnum, rx, n, cnt))
        worked[q.qnum] = '<div class="worked-solution">\n%s\n</div>' % html_q
    unused = set(FIGURE_PLAN) - used_plan
    if unused:
        raise SystemExit("FIGURE_PLAN entries never matched a part: %s" % sorted(unused))

    # ordinals: offsets after the question side, DOM order per question
    per_q = {}
    for a in assets:
        per_q[a["question"]] = per_q.get(a["question"], 0) + 1
        a["offset"] = per_q[a["question"]]
    # DOM order must equal plan order: verify by position in the html
    for qn, html in worked.items():
        pos = [(html.find(a["path"]), a["path"]) for a in assets if a["question"] == qn]
        if [p for p, _ in pos] != sorted(p for p, _ in pos) or any(p < 0 for p, _ in pos):
            raise SystemExit("Q%d: asset order does not follow DOM order: %s" % (qn, pos))
    return worked, assets, report, anomalies, zlog


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("questions_json")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    bank = json.loads(Path(a.questions_json).read_text(encoding="utf-8"))
    worked, assets, report, anomalies, zlog = build(Path(a.unz), out, bank, {}, out)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in worked.items()}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "answer_assets.json").write_text(
        json.dumps([{k: v for k, v in x.items() if k != "part"} for x in assets],
                   indent=1), encoding="utf-8")
    (out / "zones.txt").write_text("\n".join(map(str, zlog)), encoding="utf-8")
    print("\n".join(report))
    print("answer figures:", len(assets))
    for x in assets:
        print("  Q%d %-10s %-8s %s" % (x["question"], x["part"], x["slot"], x["path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
