"""ASRJC 2024 H2 P3 -- worked solutions from the combined QP + suggested-solutions docx.

Adapted from extract_acjc_p2_answers.py (same marker-zone technique). Differences:
  blue is 0000CC, no examiner "Comments" rows, red ticks sit inline with the answer,
  Q3/Q4 share one Word table (split per question first), and several answer
  rows carry no colour at all (picture answers).

SHAPE OF THIS DOCUMENT (verified 2026-09-29, differs from RI's flat 2-column
answers grid -- see answers.py):

  It is the QUESTION PAPER itself (same 4-column SEAB grid, one Word table per
  question, so `parts.parse` reads it unchanged) with each part's answer
  typed into a following row in BLUE (0000FF; underline = mark keyword), red
  (FF0000) marker notes ("DNA: ...") inside the answer row, and an examiner
  "Comments" row under nearly every part:

      question row  ->  answer row  ->  "Comments" row   (repeat)  ->  [Total: n]

  So rather than write a second table walker, `mark_zones()` injects an
  invisible marker (U+2063 A/N/C U+2063) into the first run of every paragraph
  in an answer / red-note / comments row of a COPY of the docx, `parts.parse`
  runs on the copy, and `split_part()` sorts each parsed line by its marker.
  Everything the question side already knows (labels, symbols, OMML
  fractions, sub/superscripts, floating shapes) is inherited for free.

  What the marker approach does NOT solve, so is declared explicitly below:
    * ANSWER FIGURES: an answer row's drawings are picture ANSWERS (structures,
      graphs, mechanisms), not glyphs. Their count after `parts.merge_owner_
      figures` is unreliable (4(c)'s Hess cycles are ~28 native shapes), so
      each figure-bearing part is declared in FIGURE_PLAN and checked against
      the sentinel count (a drift raises).
    * MathType (Equation.DSMT4) objects -- no text layer, hand-typed as
      `.frac` markup: SENTINEL_FILL.
    * Glyph pictures (the equilibrium arrow): typed as characters.
    * 3(d): the answer IS the question's own Fig 3.1 with red asterisks laid
      over it as text boxes, so the "answer" row is the question row.

Answers-doc label vs bank label: the docx calls 6(f)'s only sub-part "(f)(i)"
while the question side stores it as "(f)" (LABEL_MAP).

Output feeds `gen_answers_migration.py --type structured --paper 2`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from . import parts_dispatch
from .parts import _strip_answer_dots
from .oxml import NS, Wq

SCOPE = ("ASRJC", "H2", "P3", 2024)
FIG = "\x00FIG\x00"
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"

#: Examiner "Comments" rows are parsed but NOT emitted (user decision 2026-09-30:
#: no examiner comments; the red "DNA:" marker notes are kept).
INCLUDE_COMMENTS = False

BLUE = "0000CC"
RED = "FF0000"

#: P3's combined doc is the question paper's own grid with answers typed into
#: following rows (blue 0000CC / red FF0000 ticks / purple 7030A0 italics).
#: Unlike P2 there is no questions-stage prep to reuse (the live questions came
#: from the separate QP file), so the answer rows are decided here:
#:   * a row is an ANSWER row if any run in any cell has visible text in an
#:     answer colour; FORCE_A adds the uncoloured picture-answer rows, DROP
#:     removes answer-looking rows we deliberately do not carry.
ANSWER_COLOURS = ("0000CC", "FF0000", "3333CC", "7030A0", "0000FF")
FORCE_A = {(3, 2), (4, 21), (4, 25), (4, 47), (10, 2)}
#: Q5(e)'s two route diagrams (rows 10-14) are not carried (user-agreed, optional).
DROP = {(11, 10), (11, 11), (11, 13), (11, 14)}
FORCE_Q = set()

#: answers-doc label -> bank label, where they differ.
LABEL_MAP = {}

#: Answer figures the user SNIPPED (slot -> ASRJC_H2_P3_Q<n>_ans-<slot>_2024.png).
#: (see extract_asrjc_p2_answers.FIGURE_PLAN for the modes)
#:   n_fig  FIG sentinels `parts.parse` finds in the ANSWER lines (checked)
#:   mode   'each'       one <img> per sentinel; surrounding text kept
#:          'lead_notes' the images first (one per slot, in order), every
#:                       sentinel-bearing block dropped, only the red note
#:                       lines kept (a bare "Or" note is dropped); `labels`
#:                       puts a typed bold label before each image
#:          'marked'     `fill` lists, per sentinel in DOM order, what it
#:                       stands for: typed text, "@slot" (inline <img>) or
#:                       "@!slot" (the whole block that holds it becomes the
#:                       <img>; consecutive repeats collapse)
FIGURE_PLAN = {
    (1, "(e)(ii)"): dict(slots=["eii"], n_fig=1, mode="each"),
    (2, "(d)(ii)"): dict(slots=["dii-D", "dii-E"], n_fig=5, mode="lead_notes",
                         labels=["D", "E"]),
    (3, "(c)(ii)"): dict(slots=["cii"], n_fig=6, mode="lead_notes"),
    (3, "(d)(i)"):  dict(slots=["di-P", "di-step2"], n_fig=2, mode="marked",
                         fill=["@di-P", "@di-step2"]),
    (3, "(e)(i)"):  dict(slots=["ei"], n_fig=1, mode="each"),
    (3, "(f)"):     dict(slots=["f"], n_fig=1, mode="each"),
    (3, "(g)(i)"):  dict(slots=["gi"], n_fig=1, mode="each"),
    (3, "(g)(ii)"): dict(slots=["gii"], n_fig=1, mode="each"),
    (4, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="each"),
    # 4(c): two inline "CH3C(=O)R" glyphs (typed), one stray empty anchor (""),
    # then the four V/W/X/Y structures = one snip
    (4, "(c)"):     dict(slots=["c"], n_fig=7, mode="marked",
                         fill=["CH<sub>3</sub>C(=O)R", "CH<sub>3</sub>C(=O)R", "",
                               "@!c", "@!c", "@!c", "@!c"]),
    (4, "(d)(ii)"): dict(slots=["dii"], n_fig=1, mode="each"),
    (5, "(b)(i)"):  dict(slots=["bi"], n_fig=1, mode="each"),
    (5, "(c)(ii)"): dict(slots=["cii"], n_fig=1, mode="each"),
    (5, "(c)(iv)"): dict(slots=["civ"], n_fig=1, mode="each"),
    # 5(e): N's picture inside the deduction table is not carried ("N is shown
    # below"), then the M/N/L(+Or) table = one snip
    (5, "(e)"):     dict(slots=["e"], n_fig=5, mode="marked",
                         fill=["", "@!e", "@!e", "@!e", "@!e"]),
}

AR, EQ = " \u2192 ", " \u21cc "          # reaction arrow, equilibrium arrow


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


_SO3, _SO2, _O2 = "[SO<sub>3</sub>]", "[SO<sub>2</sub>]", "[O<sub>2</sub>]"
_K = lambda x: "<i>K</i><sub>%s</sub>" % x
_P = lambda x: "<i>p</i><sub>%s</sub>" % x

#: Every FIG sentinel that is NOT a snipped picture, in DOM order per part, read
#: off the rendered Word PDF: reaction / equilibrium arrows (ChemWindow glyph
#: pictures) and the MathType working (no text layer) hand-typed as `.frac`.
SENTINEL_FILL = {
    (1, "(d)(i)"): [EQ, EQ + "[Co(NH<sub>3</sub>)<sub>6</sub>]<sup>2+</sup>(aq)"],
    (1, "(d)(ii)"): [EQ],
    (2, "(a)"): ["\n".join([
        "32.06 = " + _frac("(31.97 \u00d7 94.99) + (32.97 \u00d7 0.75) + (<i>w</i> \u00d7 4.25) + (35.97 \u00d7 0.01)", "100"),
        "3206 = 3061.9175 + 4.25<i>w</i>",
        "<i>w</i> = 33.90"])],
    (2, "(c)(i)"): [
        _K("c") + " = " + _frac(_SO3 + "<sup>2</sup>", _SO2 + "<sup>2</sup>" + _O2),
        _K("p") + " = " + _frac("(" + _P("SO<sub>3</sub>") + ")<sup>2</sup>",
                                "(" + _P("SO<sub>2</sub>") + ")<sup>2</sup>(" + _P("O<sub>2</sub>") + ")")],
    (2, "(c)(ii)"): ["\n".join([
        _K("p") + " = " + _frac("(" + _SO3 + "<i>RT</i>)<sup>2</sup>",
                                "(" + _SO2 + "<i>RT</i>)<sup>2</sup>(" + _O2 + "<i>RT</i>)"),
        "= " + _frac(_SO3 + "<sup>2</sup>", _SO2 + "<sup>2</sup>" + _O2 + "<i>RT</i>"),
        "= " + _frac(_SO3 + "<sup>2</sup>", _SO2 + "<sup>2</sup>" + _O2)
        + " (" + _frac("1", "<i>RT</i>") + ")",
        "= " + _K("c") + " (" + _frac("1", "<i>RT</i>") + ") (shown)"])],
    (2, "(c)(iv)"): [EQ],
    (5, "(a)"): [AR, AR, EQ],
}

#: (qnum, label) -> [(regex, replacement)], applied once to the assembled ANSWER
#: lines of that part, and each MUST match (else a drift raises).
TEXT_FIXES = {
    # QUOTE-field junk: OMML inside a field instruction (never displayed in Word,
    # absent from the PDF) -- the parser reads it as visible text
    (2, "(c)(ii)"): [
        (r'^K<sub>c</sub>=<span class="frac">.*?</span></span>Using', "Using"),
        (r'^\[1\]\[SO<sub>3</sub>\]=.*$', "[1]")],
    # the school names the wrong compound (copied from another paper): the
    # question's compound is 3-chloro-1-phenylbutane
    (3, "(b)"): [(r"1-chloro-2-phenylethane", "3-chloro-1-phenylbutane")],
    # Symbol 0xDE is the implication arrow here (rendered: "K_c(...) \u21d2 K_c constant")
    (2, "(c)(v)"): [(r"\u2713", "\u21d2")],
    # 5(e): N's own picture is not carried
    (5, "(e)"): [(r"<b>N </b>is (?=<br>)", "<b>N</b> is shown in the structures below."),
                 # the school writes "K" for the chloroalkane L (twice)
                 (r"group in (?:<b>)?K (?:</b>)?", "group in L ")],
}

NOTE_TEXT = {}

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


def mark_zones(src_document_xml: Path, dst_document_xml: Path):
    """Write a marked copy of document.xml; return a per-row zone log."""
    from . import inline_answers_prep_parts as P
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    log = []
    for ti, tbl in enumerate(tables):
        if ti < 2:
            continue
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            tcs = tr.findall("w:tc", NS)
            text = _txt(tr).strip()
            key = (ti, ri)
            zone = "A" if ((_vis_colours(tr) & set(ANSWER_COLOURS)) or key in FORCE_A) else "Q"
            if key in FORCE_Q:
                zone = "Q"
            if key in DROP:
                zone = "X"
            log.append((ti, ri, zone, text[:50]))
            if zone != "A":
                continue
            for tc in tcs:
                for p in tc.iter(Wq + "p"):
                    tot = red = 0
                    for rr in p.iter(Wq + "r"):
                        tx = _txt(rr).strip()
                        if not tx:
                            continue
                        c = rr.find("w:rPr/w:color", NS)
                        v = (c.get(Wq + "val") or "").upper() if c is not None else ""
                        tot += len(tx)
                        red += len(tx) if v == RED else 0
                    mk = MN if (tot and red == tot) else MA
                    r = etree.Element(Wq + "r")
                    etree.SubElement(r, Wq + "t").text = mk
                    ppr = p.find("w:pPr", NS)
                    p.insert(0 if ppr is None else 1, r)
    for tbl in tables[2:]:
        P._split_questions(body, tbl)
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
            if not blocks and not comments and not plan:
                continue
            if label not in bank_labels.get(q.qnum, []):
                report.append("!! Q%d %s: answer part has no bank part" % (q.qnum, label))
                continue
            if label in seen_labels:
                report.append("!! Q%d %s: duplicate answer part" % (q.qnum, label))
            seen_labels.add(label)

            fn = lambda s, qn=q.qnum: "ASRJC_H2_P3_Q%d_ans-%s_2024.png" % (qn, s)
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
                blocks = [(k, b, n) for k, b, n in blocks
                          if k == "p" and FIG not in b
                          and (mode == "lead_text" or n)
                          and not re.fullmatch(r"\s*or\s*", b, flags=re.I)]
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
        worked[q.qnum] = ('<div class="worked-solution">\n%s\n</div>'
                          % "\n".join(blocks_out))
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
