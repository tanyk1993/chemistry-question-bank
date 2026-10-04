"""ASRJC 2024 H2 P2 -- worked solutions from the combined QP + suggested-solutions docx.

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

SCOPE = ("ASRJC", "H2", "P2", 2024)
FIG = "\x00FIG\x00"
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"

#: Examiner "Comments" rows are parsed but NOT emitted (user decision 2026-09-30:
#: no examiner comments; the red "DNA:" marker notes are kept).
INCLUDE_COMMENTS = False

BLUE = "0000CC"
RED = "FF0000"

#: (table index, row index) forced to the QUESTION zone. 3(d)'s row holds the
#: red asterisks as blue/red text boxes over Fig 3.1 -- an answer, but it sits
#: in the question row, so it is planted via SYNTH_FIGURES instead.
FORCE_Q = {(4, 22)}

#: answers-doc label -> bank label, where they differ.
LABEL_MAP = {(6, "(f)(i)"): "(f)"}

#: Answer figures the user SNIPPED (slot suffix -> file ASRJC_H2_P2_Q<n>_ans-<slot>_2024.png).
#:   n_fig  FIG sentinels `parts.parse` finds in the ANSWER lines -- checked, so a
#:          re-parse that drifts fails loudly
#:   mode   'each'        one <img> per sentinel; the text around it is kept
#:          'bare'        one <img>, ALL typed text of the part dropped
#:          'lead_text'   one <img> first, every sentinel-bearing block dropped,
#:                        the typed working below it kept (3(a)(ii))
#:          'lead_notes'  one <img> first, only the red note lines kept (4(b)(ii))
FIGURE_PLAN = {
    (1, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="each"),
    (2, "(b)(i)"):   dict(slots=["bi-1", "bi-2"], n_fig=2, mode="each"),
    (2, "(b)(ii)"):  dict(slots=["bii"], n_fig=2, mode="bare"),
    (2, "(d)(ii)"):  dict(slots=["dii"], n_fig=1, mode="each"),
    (3, "(a)(ii)"):  dict(slots=["aii"], n_fig=13, mode="lead_text"),
    (4, "(b)(ii)"):  dict(slots=["bii"], n_fig=1, mode="lead_notes"),
    (4, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="each"),
    (4, "(c)(i)"):   dict(slots=["ci"], n_fig=1, mode="bare"),
}

AR, EQ = " \u2192 ", " \u21cc "          # reaction arrow, equilibrium arrow


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


_HA = "H<sub>3</sub>N<sup>+</sup>CHRCOOH"
#: Every FIG sentinel that is NOT a snipped picture, in DOM order per part, with
#: what it stands for (read off the rendered Word PDF, pages 2-18):
#:   * reaction / equilibrium arrows (ChemWindow glyph pictures) -> a character
#:   * 2(d)(i): the MathType working (no text layer) -> hand-typed lines ("\n"
#:     starts a new line); 5(c)(ii): the red cancel-out lines -> "" here, the
#:     struck terms are typed by TEXT_FIXES below.
#: The number of entries must equal the number of sentinels, or the run stops.
SENTINEL_FILL = {
    (1, "(b)(ii)"): [AR],
    (2, "(c)(ii)"): [AR, AR],
    (2, "(d)(i)"): [EQ, "\n".join([
        "<i>K</i><sub>a</sub> = " + _frac("[H<sub>3</sub>N<sup>+</sup>CHRCOO<sup>\u2212</sup>][H<sup>+</sup>]", "[" + _HA + "]"),
        "\u2248 " + _frac("[H<sup>+</sup>]<sup>2</sup>", "[" + _HA + "]<sub>i</sub>"),
        "10<sup>\u22122.2</sup> = " + _frac("[H<sup>+</sup>]<sup>2</sup>", "0.10"),
        "[H<sup>+</sup>] = 0.02512"])],
    (3, "(a)(i)"): [AR],
    (3, "(b)(i)"): [EQ],
    (3, "(b)(ii)"): [EQ],
    (3, "(b)(iii)"): [EQ],
    (5, "(a)(iii)"): [AR] * 4,
    (5, "(a)(iv)"): [EQ],
    (5, "(b)(i)"): [AR],
    (5, "(c)(i)"): [AR, AR],
    (5, "(c)(ii)"): [AR, AR, AR, "", "", ""],
    (5, "(c)(iii)"): [AR],
    (5, "(c)(iv)"): [AR, AR],
    (5, "(c)(v)"): [AR],
    (5, "(d)(i)"): [EQ, EQ],
    (5, "(d)(iii)"): [AR],
}

#: (qnum, label) -> [(regex, replacement)], applied once to the assembled ANSWER
#: lines of that part, and each MUST match (else a drift raises).
TEXT_FIXES = {
    # the school's own Q3 working says "L.E. of CaF2" for the magnesium bromide
    # answer (copied from another paper). The question asks for MgBr2.
    (3, "(a)(ii)"): [(r"L\.E\. of CaF<sub>2</sub>", "L.E. of MgBr<sub>2</sub>")],
    # Symbol 0xDE is mapped to a tick for EJC's papers; ASRJC's typed glyph is the
    # implication arrow (rendered page 8: "pH = 13 \u21d2 pOH = 1").
    (3, "(b)(ii)"): [(r"\u2713", "\u21d2")],
    # 5(a)(ii): "450oC" -> degree sign, with the same non-breaking space the
    # question side uses between a number and \u00b0C
    (5, "(a)(ii)"): [(r"450<sup>o</sup>C", "450&nbsp;\u00b0C")],
    # 5(c)(ii): the red cancel-out lines drawn over the working, typed as <s>
    (5, "(c)(ii)"): [
        (r"\u2463 x 3: 6LiOH \u2192 6Li \+", "\u2463 x 3: <s>6LiOH</s> \u2192 <s>6Li</s> +"),
        (r"\u2464: 6Li \+ N<sub>2</sub> \u2192 2Li<sub>3</sub>N", "\u2464: <s>6Li</s> + N<sub>2</sub> \u2192 <s>2Li<sub>3</sub>N</s>"),
        (r"\u2465 x 2: 2Li<sub>3</sub>N \+ 6H<sub>2</sub>O \u2192 6LiOH", "\u2465 x 2: <s>2Li<sub>3</sub>N</s> + 6H<sub>2</sub>O \u2192 <s>6LiOH</s>")],
    # 5(c)(iii): "G" with a stacked o-over-f -> the question side's own form
    (5, "(c)(iii)"): [(r'<span class="stk post"><span>o</span><span>f</span></span>',
                       '<i><sub>f</sub></i><sup class="pl-sym">\u29b5</sup>')],
}

#: A bare red "[1]" floating under a picture reads as noise; say what earns the
#: mark instead (user request 2026-10-04). Applies to the lone "[n]" note only.
NOTE_TEXT = {(1, "(b)(iii)"): "1 mark for correct dot-and-cross."}

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


#: The questions-stage prep (`inline_answers_prep_parts.prep`) already decided,
#: row by row, which rows are answers. Reusing its decisions keeps the two
#: stages from ever disagreeing about where a question ends and its answer begins.
PREP_ARGS = dict(force_delete={(9, 2)}, insert_labels={(9, 3): "(ii)"},
                 force_keep_strip={(6, 3)}, force_blank_figs={(4, 21)},
                 skip_tables=1)
#: kept rows that are ANSWERS all the same: 2(d)(ii)'s row holds the sketch plus
#: the red ticks (stripped from the questions copy); 2(b)(ii)'s row holds the U/V
#: structure pictures (blanked there).
EXTRA_ANSWER_ROWS = {(6, 3), (4, 21)}


def answer_rows(src_document_xml: Path):
    from . import inline_answers_prep_parts as P
    tmp = Path(str(src_document_xml) + ".prep.tmp")
    log = P.prep(src_document_xml, tmp, **PREP_ARGS)
    tmp.unlink()
    rows = {(l[0], l[1]) for l in log
            if len(l) == 4 and str(l[2]).startswith("delete")}
    return rows | EXTRA_ANSWER_ROWS


def mark_zones(src_document_xml: Path, dst_document_xml: Path):
    """Write a marked copy of document.xml; return a per-row zone log."""
    from . import inline_answers_prep_parts as P
    arows = answer_rows(src_document_xml)
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    # label insertion mirrors the questions stage so part labels line up
    for (ti, ri), lab in PREP_ARGS["insert_labels"].items():
        tr = tables[ti].findall("w:tr", NS)[ri]
        tc = tr.findall("w:tc", NS)[2]
        r = etree.SubElement(tc.find("w:p", NS), Wq + "r")
        etree.SubElement(r, Wq + "t").text = lab
    log = []
    for ti, tbl in enumerate(tables):
        if ti < PREP_ARGS["skip_tables"]:
            continue
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            tcs = tr.findall("w:tc", NS)
            text = _txt(tcs[-1]).strip()
            zone = "A" if (ti, ri) in arows else "Q"
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
    for tbl in tables[PREP_ARGS["skip_tables"]:]:
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


def split_part(html: str):
    """-> (answer_blocks, note_blocks_in_order, comment_items).

    `answer_blocks` is a list of ('p'|'ul', html, is_note) in DOM order.
    A `<ul>` group holds its own <li> items, each with a zone marker.
    """
    blocks, comments = [], []
    for line in html.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("<ul"):
            items = re.findall(r"<li>(.*?)</li>", s, flags=re.S)
            a_items = [_clean(i) for i in items if MA in i or MN in i]
            c_items = [_clean(i) for i in items if MC in i]
            if a_items:
                blocks.append(("ul", a_items, False))
            comments.extend(c_items)
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

            # ---- figure handling ----
            n_sent = sum(b[1].count(FIG) if b[0] == "p"
                         else sum(i.count(FIG) for i in b[1]) for b in blocks)
            if plan:
                used_plan.add(key)
                if n_sent != plan["n_fig"]:
                    raise SystemExit("Q%d%s: expected %d FIG sentinels in the "
                                     "answer, parser found %d"
                                     % (q.qnum, label, plan["n_fig"], n_sent))
            elif key in SENTINEL_FILL:
                if n_sent != len(SENTINEL_FILL[key]):
                    raise SystemExit("Q%d%s: SENTINEL_FILL has %d entries, parser "
                                     "found %d sentinels" % (q.qnum, label,
                                     len(SENTINEL_FILL[key]), n_sent))
            elif n_sent:
                raise SystemExit("Q%d%s: %d undeclared FIG sentinel(s) in the "
                                 "answer" % (q.qnum, label, n_sent))

            if key in SENTINEL_FILL:
                reps = iter(SENTINEL_FILL[key])
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
            fn = lambda s: "ASRJC_H2_P2_Q%d_ans-%s_2024.png" % (q.qnum, s)
            mode = plan["mode"] if plan else None
            if mode == "bare":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = []
            elif mode in ("lead_text", "lead_notes"):
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = [(k, b, n) for k, b, n in blocks
                          if k == "p" and FIG not in b
                          and (mode == "lead_text" or n)]
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
                t = re.sub(r"<td>(?=[^<]*\w)(.*?)</td>",
                           lambda m: "<td>%s</td>" % m.group(1), t)
                return t
            for kind, body, note in blocks:
                def wrap(t, note=note):
                    if re.fullmatch(r"\s*<img[^>]*>\s*", t):
                        return t.strip()
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
