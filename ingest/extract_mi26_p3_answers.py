"""MI 2026 H2 P3 (9729/03) -- worked solutions from the "Ans_key" docx.

Same family as the JPJC 2026 P2 extractor (the marker-zone technique, section 20 of HANDOFF): the key IS
the question paper (the same SEAB-style grid, five body tables, no cover table), with the answers typed
into extra rows: blue 0000FF = answer, red FF0000 = marking note. No examiner comments, no Word comments.
Unlike JPJC the grid is NOT squared up first: `parts.py` reads the two row shapes as they are, and the
content cell is found by width (>= 3500 twips; row (3,6) has two, healthy / infected tissue).

Answer pictures carry no colour: ANS_FIG lists the picture-only paragraphs that are answers; DROP_PARA
lists paragraphs INSIDE a drawn answer (labels, arrows, text boxes) that the user's snip carries.

Usage:
  python3 -m ingest.extract_mi26_p3_answers <unz> <questions.json> <outdir>
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

SCOPE = ("MI", "H2", "P3", 2026)
FIG = "\x00FIG\x00"
MA, MC, MN = "\u2063A\u2063", "\u2063C\u2063", "\u2063N\u2063"

#: examiner comments: none in this file (the key carries only blue answers and red marks)
INCLUDE_COMMENTS = False

BLUE = "0000FF"
RED = "FF0000"
GREEN = "538135"
ANSWER_BLUES = ("0000FF",)
#: unmarked picture paragraphs that ARE answer figures: (table, row, direct-paragraph index)
#: (table numbers are those of the answers docx, no cover table: Q1 = table 0).
ANS_FIG = {
    (1, 1, 2),                 # Q1(c)(i): structures of HOBr and HOCl
    (4, 1, 0), (4, 2, 0), (4, 3, 0), (4, 4, 0),   # Q2(b)(i): Fig. 2.1 steps 1-4 with the curly arrows
    (6, 1, 2),                 # Q2(c)(i): intermediate X
    (6, 3, 3),                 # Q2(c)(iii): side product
    (18, 0, 2),                # Q5(e)(ii): phenol + 3[O] -> muconic acid
    (18, 1, 8),                # Q5(f)(i): structure of P
    (19, 0, 8),                # Q5(f)(ii): structure of Q
}
FORCE_A = set()
DROP = set()
#: paragraphs that sit INSIDE an answer figure (labels, arrows, text boxes): never emitted;
#: the picture the user snips carries them. (table, row) -> set of direct-paragraph indices
DROP_PARA = {
    (0, 2): {1},               # Q1(a)(ii): the cell diagram (all labels are text boxes)
    (13, 1): {1, 2},           # Q4(d)(i): the mechanism with the red marking letters
    (11, 0): {7},              # Q4(a): the sketched graph (axis labels are text boxes)
}
FORCE_Q = set()
QROWS = set()
LABEL_MAP = {}
#: lines holding a marked FIG sentinel move from one parsed part to the start of another:
#: (qnum, from label) -> to label. Q2: the four Fig. 2.1 step rows sit in the (b) stem; the arrows answer (b)(i).
MOVE_FIG = {(2, "(b)"): "(b)(i)"}

#: slot -> MI_H2_P2_Q<n>_ans-<slot>_2026.png.  mode "marked": the picture paragraph is part of
#: the marked blocks (n_fig sentinels, filled with @!slot = the whole block is the image);
#: mode "lead_text": the picture sits in dropped / question content and is put in FRONT.
FIGURE_PLAN = {
    (1, "(a)(ii)"): dict(slots=["aii"], n_fig=0, mode="lead_text"),
    (1, "(c)(i)"):  dict(slots=["ci"], n_fig=1, mode="marked", fill=["@!ci"]),
    (1, "(d)"):     dict(slots=["d"], n_fig=1, mode="marked", fill=["@!d"]),
    (2, "(a)"):     dict(slots=["a"], n_fig=3, mode="marked", fill=["@!a", "", ""]),
    (2, "(b)(i)"):  dict(slots=["bi"], n_fig=4, mode="marked", fill=["@!bi", "", "", ""]),
    (2, "(c)(i)"):  dict(slots=["ci"], n_fig=1, mode="marked", fill=["@!ci"]),
    (2, "(c)(iii)"): dict(slots=["ciii"], n_fig=1, mode="marked", fill=["@!ciii"]),
    (3, "(e)"):     dict(slots=["e"], n_fig=1, mode="marked", fill=["@!e"]),
    (4, "(a)"):     dict(slots=["a"], n_fig=0, mode="lead_text"),
    (4, "(d)(i)"):  dict(slots=["di"], n_fig=0, mode="lead_text"),
    (5, "(e)(i)"):  dict(slots=["ei"], n_fig=3, mode="marked", fill=["@!ei", "", ""]),
    (5, "(e)(ii)"): dict(slots=["eii"], n_fig=1, mode="marked", fill=["@!eii"]),
    (5, "(f)(i)"):  dict(slots=["fi"], n_fig=1, mode="marked", fill=["@!fi"]),
    (5, "(f)(ii)"): dict(slots=["fii"], n_fig=1, mode="marked", fill=["@!fii"]),
}
#: red marker lines that sat in a dropped picture paragraph: re-added as notes
NOTE_EXTRA = {}
SENTINEL_FILL = {}
TYPED = {}
TEXT_FIXES = {}
OL_PARTS = set()
KSP_FIX = False
E3_NOTE = False
MARK_START = re.compile(r"\s*(?:<b>)?\s*\[\s*(?:[\u2013\u2212\-]?\d+(?:\.\d+)?|\d/\d)\b")
NOTE_LINES = {}
POST_FIXES = {
    1: [(r'<i>p</i><sub>O<sub>2</sub></sub> = <i> </i>2\.39', '<i>p</i><sub>O<sub>2</sub></sub> = 2.39', 1),
        (r'<span class="stk post"><span>\u03b8</span><span></span></span><b><span class="sr"> ?= ?</span></b> ?',
         '<sup class="pl-sym">\u29b5</sup> = ', 1),
        (r'H\u2013O bond', 'H-O bond', -1)],
    3: [(r'<span class="sr">I</span>', 'I', 1),
        (r'<td>\[1\]</td>', '<td><span class="note">[1]</span></td>', 1),
        (r'(?<![\w/])p(?=<sub>)', '<i>p</i>', -1),
        (r'(?<![\w])K(?=<sub>(?:sp|p)</sub>)', '<i>K</i>', -1),
        (r'<sub>H2\(g\)</sub>', '<sub>H<sub>2</sub>(g)</sub>', 1),
        (r'<sub>CH3OH\(g\)</sub>', '<sub>CH<sub>3</sub>OH(g)</sub>', 1),
        (r'(?<![\w>])p\u221dn', '<i>p</i> \u221d <i>n</i>', 1),
        (r'\(x\)\(2x\)', '(<i>x</i>)(2<i>x</i>)', 1),
        (r'= 4x<sup>3</sup>', '= 4<i>x</i><sup>3</sup>', 1),
        (r'<span class="ans">x = solubility', '<span class="ans"><i>x</i> = solubility', 1),
        (r'\(6600\)\(V\)', '(6600)(<i>V</i>)', 1),
        (r'hence V = 2\.89', 'hence <i>V</i> = 2.89', 1),
        (r'\u2212 ?2\(406\) \+ x', '\u22122(406) + <i>x</i>', 1),
        (r'\(g\) = x</span>', '(g) = <i>x</i></span>', 1),
        (r'<span class="ans">pV = nRT', '<span class="ans"><i>pV</i> = <i>nRT</i>', 1)],
    4: [(r'1\.5 ?: ?6 ?: ?1', '1.5 : 6 : 1', 1)],
}
NOTE_TEXT = {}


def _p3_house(h):
    """MI P3 house pass: math-run hyphens/dashes -> minus sign, bond dashes -> hyphen,
    charges/subscripts typed as <sup><sub>..</sub></sup> folded into the subscript, spaces round '='."""
    # charge stacked after a subscript: eta(OH-) etc.  -> <sub>OH<sup>-</sup></sub>
    h = re.sub(r"(<sub>(?:[^<]|<sub>[^<]*</sub>)*)</sub><sup><sub>([^<]*)</sub></sup>",
               lambda m: "%s<sup>%s</sup></sub>" % (m.group(1), m.group(2)), h)
    parts = re.split(r"(<[^>]+>)", h)
    out = []
    for i, seg in enumerate(parts):
        if seg.startswith("<") or not seg:
            out.append(seg)
            continue
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        prv = parts[i - 1] if i else ""
        seg = re.sub(r"(?<![\w)\]])\u2013(?=\d)", "\u2212", seg)          # unary minus before a number
        seg = re.sub(r"\(\u2013$", "(\u2212", seg)                         # "(" then <i>T</i>
        seg = re.sub(r"(?<=\s)\u2013$", "\u2212", seg)                      # " -" then a tag
        seg = re.sub(r"(?<=[A-Za-z])\u2013(?=[A-Z])", "-", seg)             # bond dash O-H
        seg = re.sub(r"(?<=\s)\u2013(?=[A-Z])", "-", seg)                  # group prefix -CH(OH)CH3
        seg = re.sub(r"(?<=[A-Z])\u2013$", "-", seg)                        # C-<i>Cl</i>
        seg = re.sub(r"(?<=[\w)\]])\u2013(?=\s|$)", "\u2212", seg) if False else seg
        if seg == "-":
            seg = " \u2212 "                                                # hyphen between two math terms
        seg = re.sub(r"=\s*-$", "= \u2212", seg)                            # "=" "-" then a tag
        seg = re.sub(r"^-(?=\d)", "\u2212", seg) if "fnum" in prv else seg
        seg = re.sub(r"(?<=\s)-(?=\s*$)", "\u2212", seg)                    # ' - ' before a fraction/term
        seg = re.sub(r"=\s*-(?=[\d(<])", "= \u2212", seg)
        seg = re.sub(r"(?<=\S)\u00d7(?=\S)", " \u00d7 ", seg)
        seg = " = " if seg.strip() == "=" else seg
        seg = re.sub(r"(?<=\s)=(?=[\[\(\w])", "= ", seg)
        seg = re.sub(r"(?<=\S)=(?=\S)", " = ", seg)
        seg = re.sub(r"(?<=\S)=$", " =", seg)
        seg = re.sub(r"^=(?=\S)", "= ", seg)
        out.append(seg)
    h = "".join(out)
    # standard-state sign stacked over a subscript: the live `.stk` rules are scoped to `.stem`
    # and an answer sits in `.ws`, so it showed as a flat "E⦵cell" -- inline styles instead
    _stk = ('<span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;'
            'line-height:1;font-size:.72em;text-align:left;margin-left:.08em">'
            '<span style="display:block"><span class="pl-sym">\u29b5</span></span>'
            '<span style="display:block">%s</span></span>')
    h = re.sub(r'<span class="stk post"><span>\u29b5</span><span>(.*?)</span></span>',
               lambda m: _stk % m.group(1), h)
    h = h.replace("\u03b7", "<i>n</i>")      # school types eta for amount (mol): bank standard is n (ruling 2026-11-09)
    h = re.sub(r"<sup>(\d*)-</sup>", "<sup>\\1\u2212</sup>", h)
    return h
AR, EQ = " \u2192 ", " \u21cc "

#: Superscript signs: the paper types en dashes and hyphens; the minus sign is
#: U+2212 (the question side uses both, so one rule is applied here).
def _sup_minus(t):
    return re.sub(r"<sup>([^<]*)</sup>",
                  lambda m: "<sup>%s</sup>" % re.sub(r"[\u2013\-](?=\d|$|\s)", "\u2212", m.group(1)), t)


MQ = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def _txt(el):
    return "".join(el.itertext(Wq + "t", MQ + "t"))


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
    if c is None:
        c = rr.find("m:rPr/w:color", NS)
    return (c.get(Wq + "val") or "").upper() if c is not None else ""


def _para_zone(p):
    """'A' answer, 'N' red marker note, 'C' green examiner comment, '' = question."""
    blue = red = green = tot = 0
    # Word-equation runs (m:r, text in m:t) carry the answer colour too
    for rr in list(p.iter(Wq + "r")) + list(p.iter(MQ + "r")):
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
    assert len(tables) == 20, len(tables)
    log = []
    used_fig = set()
    for ti, tbl in enumerate(tables):
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            tcs = tr.findall("w:tc", NS)
            grid = [int(g.get(Wq + "w")) for g in tbl.findall("w:tblGrid/w:gridCol", NS)]
            pos, cells_w = 0, []
            for tc in tcs:
                gs = tc.find("w:tcPr/w:gridSpan", NS)
                n = int(gs.get(Wq + "val")) if gs is not None else 1
                cells_w.append((tc, sum(grid[pos:pos + n])))
                pos += n
            contents = [tc for tc, w in cells_w if w >= 3500]
            if not contents:
                # grid spans inconsistent with the cell widths (Fig. 2.1 "step n" rows):
                # fall back to the declared tcW
                def _tcw(tc):
                    e = tc.find("w:tcPr/w:tcW", NS)
                    return int(e.get(Wq + "w")) if e is not None else 0
                contents = [tc for tc in tcs if _tcw(tc) >= 3500]
            if not contents:
                raise SystemExit("row (%d,%d): no content cell" % (ti, ri))
            for content in contents:
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
                  if pi is not None and pi in DROP_PARA.get((ti, ri), ()):
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
        for (mq, src), dst in MOVE_FIG.items():
            if mq != q.qnum:
                continue
            ps = {p.label: p for p in q.parts}
            lines = ps[src].html.split("\n")
            moved = [ln for ln in lines if FIG in ln and MA in ln]
            ps[src].html = "\n".join(ln for ln in lines if ln not in moved)
            ps[dst].html = "\n".join(moved + [ps[dst].html])
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

            fn = lambda s, qn=q.qnum: "MI_H2_P3_Q%d_ans-%s_2026.png" % (qn, s)
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

            blocks = blocks + [("p", t, True) for t in NOTE_EXTRA.get(key, [])]
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
        # ---- MI P2 cleanup: unicode scripts, minus signs, italic variables ----
        _SUP = {"\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u2074": "4", "\u2075": "5", "\u2076": "6",
                "\u207a": "+", "\u207b": "\u2212"}
        html_q = re.sub("[\u00b2\u00b3\u2070\u2074-\u2076\u207a\u207b]+",
                        lambda m: "<sup>%s</sup>" % "".join(_SUP[c] for c in m.group(0)), html_q)
        html_q = re.sub(r"</sup><sup>", "", html_q)
        html_q = re.sub(r"\(\u2013(?=\d)", "(\u2212", html_q)            # (-3123)
        html_q = re.sub(r"\u2013lg", "\u2212lg", html_q)
        html_q = re.sub(r"(?<=[\w\)\]>]) \u2013 (?=[\w\(\[<+])",
                        lambda m: " \u2212 ", html_q)
        html_q = html_q.replace("1.5 \u2212 3.5", "1.5 \u2013 3.5")          # a range keeps its en dash
        html_q = re.sub(r"\(100-30\.4\)", "(100 \u2212 30.4)", html_q)
        html_q = html_q.replace("(+) / (-)", "(+) / (\u2212)")
        html_q = html_q.replace('<i><span class="sr">I</span></i>', "<i>I</i>")
        html_q = html_q.replace("n<sub>e</sub>", "<i>n</i><sub>e</sub>")
        html_q = html_q.replace("<sub>n</sub>", "<sub><i>n</i></sub>").replace("where n =", "where <i>n</i> =")
        html_q = html_q.replace("<sub>t</sub>", "<sub><i>t</i></sub>")
        html_q = re.sub(r"</u><u>", "", html_q)
        html_q = html_q.replace("/ <br>", "/ ").replace(" </span></td>", "</span></td>")
        html_q = _p3_house(html_q)
        for rx, rep, cnt in POST_FIXES.get(q.qnum, []):
            html_q, n = re.subn(rx, rep, html_q)
            if cnt >= 0 and n != cnt:
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
