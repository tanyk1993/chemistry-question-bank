"""ACJC 2024 H2 P3 -- worked solutions from the "Solutions" docx.

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
      `.frac` markup: OBJECT_FRACS.
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

SCOPE = ("ACJC", "H2", "P3", 2024)
FIG = "\x00FIG\x00"
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"

#: Examiner "Comments" rows are parsed but NOT emitted (user decision 2026-09-30:
#: no examiner comments; the red "DNA:" marker notes are kept).
INCLUDE_COMMENTS = False

BLUE = "0000FF"
RED = "FF0000"

FORCE_Q = set()

#: parts whose answer zone holds a raw <table> (the ICE table) to keep.
TABLE_PARTS = {(5, "(a)(i)")}

#: answers-doc label -> bank label. The answers docx numbers Q5(b) one slot
#: ahead of the bank from (b)(iv) on (the bank's (b)(iii) is the S_N2 mechanism).
LABEL_MAP = {(5, "(b)(iv)"): "(b)(iii)", (5, "(b)(v)"): "(b)(iv)",
             (5, "(b)(vi)"): "(b)(v)"}

#: Answer figures. key (qnum, bank label) -> dict:
#:   slots   answer slot suffixes (each becomes `ans-<slot>`), DOM order
#:   n_fig   FIG sentinels `parts.parse` finds in the ANSWER lines (checked)
#:   mode    'each'    one <img> per sentinel, text kept
#:           'groups'  `groups`=[k1,k2..] consecutive sentinels per image; an
#:                     image is emitted where its group starts, FIG-only
#:                     paragraphs of the group vanish, text is kept
#:           'end'     FIG paragraphs vanish, text kept, ONE image appended
#:           'tail'    text kept up to the first FIG paragraph; that paragraph
#:                     and everything after become ONE image
#:           'line'    each paragraph holding a FIG becomes one image
#:           'synth'   no sentinel in the answer zone; image added first
#:           'synth2'  as synth, two images with "OR" between (3(d)(i))
FIGURE_PLAN = {
    (1, "(c)(i)"):   dict(slots=["ci"], n_fig=1, mode="each"),
    (2, "(a)(i)"):   dict(slots=["ai"], n_fig=1, mode="each"),
    # typed σ/π lines dropped: the combined snip already carries them
    (2, "(a)(ii)"):  dict(slots=["aii"], n_fig=2, mode="bare"),
    (2, "(c)(ii)"):  dict(slots=["cii"], n_fig=2, mode="tail"),
    (3, "(d)(i)"):   dict(slots=["di"], n_fig=0, mode="synth"),
    (3, "(d)(ii)"):  dict(slots=["dii"], n_fig=3, mode="bare"),
    (4, "(a)(i)"):   dict(slots=["ai"], n_fig=1, mode="each"),
    (4, "(c)(i)"):   dict(slots=["ci"], n_fig=0, mode="synth"),
    # the hand-drawn "Alternative answer" is deliberately NOT ingested
    # (user decision 2026-10-01): main printed mechanism only.
    (4, "(d)(ii)"):  dict(slots=["dii"], n_fig=7, mode="bare"),
    (5, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="each"),
}


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


#: MathType objects, hand-typed from the rendered PDF (Kp expression and its
#: numerical substitution, p.21). Each entry replaces ONE FIG sentinel in DOM
#: order. The ICE table (a raw <table> in the answer zone) is handled in split_part.
_P = lambda s: "<i>P</i><sub>%s</sub>" % s
OBJECT_FRACS = {
    (5, "(a)(i)"): [
        _frac(_P("CH<sub>3</sub>CH<sub>2</sub>CHO"),
              _P("CH<sub>2</sub>=CH<sub>2</sub>") + _P("CO") + _P("H<sub>2</sub>")),
        _frac("39.2", "(0.4)(0.4)(0.4)")],
}

_HP = "[HPO<sub>4</sub><sup>2–</sup>]"
_H2P = "[H<sub>2</sub>PO<sub>4</sub><sup>–</sup>]"
_PL = '<sup class="pl-sym">⦵</sup>'
TEXT_FIXES = {
    # Q1(a): the hydrolysis equation's equilibrium arrow is a glyph picture.
    (1, "(a)"): [(r"\x00FIG\x00", " ⇌ ")],
    # Q1(b)(iii): equation-editor text typed flat inside the fractions.
    (1, "(b)(iii)"): [
        (r"\[HPO4 2-\]", _HP),
        (r"\[H2PO4-\]", _H2P),
        (r"\[H\+\]", "[H<sup>+</sup>]")],
    # Q3(a)(i): E-plimsoll typed without italics / spacing.
    # Q2(b): ranking typed in words (user decision) instead of a snip.
    (2, "(b)"): [(r"^.*Increasing basicity.*$",
                  "Basicity increases in the order: N-propylethanamide "
                  "&lt; phenylamine &lt; ethylamine")],
    # Q1(d)(iii): E-plimsoll typed as a superscript letter o.
    (1, "(d)(iii)"): [(r"<sup>o</sup>", _PL)],
    (3, "(a)(i)"): [
        (r"(?<![\w>])E(?=<sup class=\"pl-sym\">)", "<i>E</i>"),
        (r"(<sup class=\"pl-sym\">⦵</sup>)=\s*", r"\1 = ")],
    # Q4(a)(ii): theta typed as a stacked span / <sup>θ</sup>; the paper's own
    # standard-state symbol is the plimsoll (as in the question text).
    (4, "(a)(ii)"): [
        (r'E<span class="stk post"><span>θ</span><span>cell</span></span>=\+0\.40-\(-1\.25\) =\+1\.65 V',
         "<i>E</i>" + _PL + "<sub>cell</sub> = +0.40 − (−1.25) = +1.65 V"),
        (r"∆G<sup>θ</sup>=-\(2\)", "∆<i>G</i>" + _PL + " = −(2)"),
        (r"=-3\.18×10<sup>5</sup> Jmol", "= −3.18 × 10<sup>5</sup> J mol"),
        (r"=-318 kJmol", "= −318 kJ mol")],
    (4, "(a)(iii)"): [(r"<sup> </sup>", "")],
    # Q5(a)(i): second Kp not italic.
    (5, "(a)(i)"): [(r"(?<![>\w])K<sub>p</sub> = ", "<i>K</i><sub>p</sub> = ")],
    (5, "(c)(iv)"): [(r"∆G<sup>o</sup><sub>sol</sub>", "∆<i>G</i>" + _PL + "<sub>sol</sub>")],
}

SPACE_OPS = set()
MINUS_STYLE = {1: "–", 3: "–", 4: "−", 5: "−"}


def _space_ops(html: str) -> str:
    out = []
    for piece in re.split(r"(<[^>]+>)", html):
        if piece.startswith("<"):
            out.append(piece)
        else:
            piece = re.sub(r"\s*([=÷×])\s*", r" \1 ", piece)
            out.append(piece)
    return re.sub(r"[ ]{2,}", " ", "".join(out)).strip()


def _txt(el):
    return "".join(el.itertext(Wq + "t"))


def _blue(r):
    c = r.find("w:rPr/w:color", NS)
    return c is not None and (c.get(Wq + "val") or "").upper() == BLUE


def _has_fig(el):
    return any(etree.QName(x).localname in ("drawing", "object", "pict")
               for x in el.iter())


def mark_zones(src_document_xml: Path, dst_document_xml: Path):
    """Write a marked copy of document.xml; return a per-row zone log."""
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    log = []
    for ti, tbl in enumerate(body.findall("w:tbl", NS)):
        if ti < 2:          # cover + examiner's-use tables
            continue
        state = "q"
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            tcs = tr.findall("w:tc", NS)
            content = tcs[-1]
            text = _txt(content).strip()
            paras = [p for p in content if etree.QName(p).localname == "p"]
            labelled = any(_txt(c).strip() for c in tcs[:-1])
            has_blue = any(_blue(r) and _txt(r).strip()
                           for r in content.iter(Wq + "r"))
            if (ti, ri) in FORCE_Q:
                zone = "Q"
            elif text.startswith("Comments"):
                zone = "C"
            elif text.startswith("[Total"):
                zone = None
            elif has_blue:
                zone = "A"
            elif not labelled and not text and state == "q_done":
                zone = "A"          # figure-only answer row right after a question row
            elif not labelled and not text and not _has_fig(content):
                zone = None
            else:
                zone = "Q"
            log.append((ti, ri, zone, text[:50]))
            state = {"Q": "q_done", "A": "a", "C": "c", None: state}[zone]
            if zone not in ("A", "C"):
                continue
            for p in paras:
                mk = MC if zone == "C" else MA
                if zone == "A":
                    tot = red = 0
                    for rr in p.iter(Wq + "r"):
                        tx = _txt(rr).strip()
                        if not tx:
                            continue
                        c = rr.find("w:rPr/w:color", NS)
                        v = (c.get(Wq + "val") or "").upper() if c is not None else ""
                        tot += len(tx)
                        red += len(tx) if v == RED else 0
                    if tot and red == tot:
                        mk = MN
                r = etree.Element(Wq + "r")
                etree.SubElement(r, Wq + "t").text = mk
                ppr = p.find("w:pPr", NS)
                p.insert(0 if ppr is None else 1, r)
    tree.write(str(dst_document_xml), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


def _clean(line: str) -> str:
    line = re.sub("[⁣]?[ANC][⁣]", "", line)
    line = line.replace("\t", " ")
    line = re.sub(r"\s*<br>\s*", " ", line).strip()
    line = _strip_answer_dots(line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


def split_part(html: str, allow_tables: bool = False):
    """-> (answer_blocks, note_blocks_in_order, comment_items).

    `answer_blocks` is a list of ('p'|'ul', html, is_note) in DOM order.
    A `<ul>` group holds its own <li> items, each with a zone marker.
    """
    blocks, comments = [], []
    for line in html.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("<table") and allow_tables and any(b[0] == "p" for b in blocks):
            # answer-zone table (Q5(a)(i)'s ICE table): unmarked, so it is
            # attached to the answer that precedes it. Glyph-picture cells are
            # the equilibrium arrow.
            t = s.replace(FIG, "⇌")
            t = re.sub(r"<td>([^<][^<]*?(?:<(?:sub|sup)>.*?</(?:sub|sup)>[^<]*?)*)</td>",
                       lambda m: '<td><span class="ans">%s</span></td>' % m.group(1)
                       if m.group(1).strip() else m.group(0), t)
            blocks.append(("p", t, False))
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
            key = (q.qnum, label)
            blocks, comments = split_part(p.html, allow_tables=key in TABLE_PARTS)
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
            elif key in OBJECT_FRACS:
                pass
            elif n_sent and key not in OBJECT_FRACS and key not in TEXT_FIXES:
                raise SystemExit("Q%d%s: %d undeclared FIG sentinel(s) in the "
                                 "answer" % (q.qnum, label, n_sent))

            if key in OBJECT_FRACS:
                reps = iter(OBJECT_FRACS[key])
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
                    raise SystemExit("Q%d%s: unused OBJECT_FRACS entries" % (q.qnum, label))

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

            if key in SPACE_OPS:
                blocks = [(k, _space_ops(b) if k == "p" else b, n)
                          for k, b, n in blocks]
            ms = MINUS_STYLE.get(q.qnum)
            if ms:
                def fix(t):
                    t, a = re.subn(r"(<sup>)-(?=\d)", lambda m: m.group(1) + ms, t)
                    t, b = re.subn(r"(<sup>\d*)-(?=</sup>)", lambda m: m.group(1) + ms, t)
                    return t, a + b
                nb = []
                for k, b, n in blocks:
                    if k == "p":
                        b, c = fix(b)
                    else:
                        cc = [fix(i) for i in b]
                        b, c = [x for x, _ in cc], sum(n_ for _, n_ in cc)
                    nb.append((k, b, n))
                blocks = nb
                comments = [fix(c)[0] for c in comments]

            # ---- trailing redundant part-mark ----
            marks = bank_marks.get(key)
            mk_all = []
            for kind, body, note in blocks:
                if kind == "p":
                    mk_all += re.findall(r'<span class="mk">\[(\d+)\]</span>', body)
            if len(mk_all) == 1 and marks is not None and int(mk_all[0]) == marks:
                blocks = [(k, re.sub(r'\s*<span class="mk">\[\d+\]</span>', "", b)
                           if k == "p" else b, n) for k, b, n in blocks]
            blocks = [(k, re.sub(r'<span class="mk">(\[\d+\])</span>', r"\1", b)
                       if k == "p" else b, n) for k, b, n in blocks]
            blocks = [(k, b, n) for k, b, n in blocks
                      if (k == "ul" and b) or (k == "p" and b.strip())]

            # ---- render ----
            body_html = []
            fn = lambda s: "ACJC_H2_P3_Q%d_ans-%s_2024.png" % (q.qnum, s)
            mode = plan["mode"] if plan else None
            if mode == "bare":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = []
            elif mode == "synth":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
            elif mode == "synth2":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                body_html.append('<p><span class="ans">OR</span></p>')
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][1])))
            elif mode == "end":
                blocks = [(k, b.replace(FIG, ""), n) for k, b, n in blocks]
                blocks = [x for x in blocks if x[1].strip()]
                tail_img = "<p>%s</p>" % _img(fn(plan["slots"][0]))
            elif mode == "tail":
                keep = []
                for kind, body, note in blocks:
                    if FIG in body:
                        break
                    keep.append((kind, body, note))
                blocks = keep
                tail_img = "<p>%s</p>" % _img(fn(plan["slots"][0]))
            elif mode == "line":
                new = []
                si = iter(plan["slots"])
                for kind, body, note in blocks:
                    if FIG in body:
                        body = _img(fn(next(si)))
                    new.append((kind, body, note))
                blocks = new
            elif mode == "groups":
                new = []
                gi, left, started = 0, plan["groups"][0], False
                for kind, body, note in blocks:
                    if FIG not in body:
                        new.append((kind, body, note))
                        continue
                    out, rest = "", body
                    while FIG in rest:
                        head, rest = rest.split(FIG, 1)
                        out += head
                        if not started:
                            out += _img(fn(plan["slots"][gi]))
                            started = True
                        left -= 1
                        if left == 0:
                            gi += 1
                            if gi < len(plan["groups"]):
                                left, started = plan["groups"][gi], False
                    out += rest
                    if out.strip():
                        new.append((kind, out, note))
                assert left == 0 and gi == len(plan["groups"]), (gi, left)
                blocks = new
            elif mode == "split":
                # 4(c): Hess cycle | "OR" | energy-level diagram | working.
                # Sentinels 0..6 = diagram 1 (the 7th shares a paragraph with
                # "OR"), 7..18 = diagram 2.
                ps = [b for b in blocks if b[0] == "p"]
                order = []
                fig_i = 0
                text_after = []
                for kind, body, note in ps:
                    if FIG in body:
                        rest = body.replace(FIG, "").strip()
                        fig_i += body.count(FIG)
                        if rest:
                            order.append(("t", rest))
                    else:
                        text_after.append((kind, body, note))
                assert fig_i == 19
                body_html.append("<p>%s</p>" % _img(fn("c")))
                body_html.append('<p><span class="ans">OR</span></p>')
                body_html.append("<p>%s</p>" % _img(fn("c2")))
                blocks = text_after
                assert [t for _, t in order] == ["OR"], order
            elif mode == "each":
                slots = iter(plan["slots"])
                new = []
                for kind, body, note in blocks:
                    if kind == "p":
                        body = re.sub(re.escape(FIG), lambda _m: _img(fn(next(slots))), body)
                    else:
                        body = [re.sub(re.escape(FIG), lambda _m: _img(fn(next(slots))), i)
                                for i in body]
                    new.append((kind, body, note))
                blocks = new
            for kind, body, note in blocks:
                def wrap(t, note=note):
                    if re.fullmatch(r"\s*<img[^>]*>\s*", t) or t.startswith("<table"):
                        return t.strip()
                    return '<span class="%s">%s</span>' % ("note" if note else "ans", t)
                if kind == "p" and body.startswith("<table"):
                    body_html.append(body)
                elif kind == "p":
                    body_html.append("<p>%s</p>" % wrap(body))
                else:
                    body_html.append('<ul class="stmts">%s</ul>'
                                     % "".join("<li>%s</li>" % wrap(i) for i in body))
            if mode in ("tail", "end"):
                body_html.append(tail_img)
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
