"""ACJC 2024 H2 P2 -- worked solutions from the "Solutions" docx.

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

SCOPE = ("ACJC", "H2", "P2", 2024)
FIG = "\x00FIG\x00"
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"

#: Examiner "Comments" rows are parsed but NOT emitted (user decision 2026-09-30:
#: no examiner comments; the red "DNA:" marker notes are kept).
INCLUDE_COMMENTS = False

BLUE = "0000FF"
RED = "FF0000"

#: (table index, row index) forced to the QUESTION zone. 3(d)'s row holds the
#: red asterisks as blue/red text boxes over Fig 3.1 -- an answer, but it sits
#: in the question row, so it is planted via SYNTH_FIGURES instead.
FORCE_Q = {(4, 22)}

#: answers-doc label -> bank label, where they differ.
LABEL_MAP = {(6, "(f)(i)"): "(f)"}

#: Answer figures. key (qnum, bank label) -> dict:
#:   slots   answer slot suffixes (each becomes `ans-<slot>`), DOM order
#:   n_fig   how many FIG sentinels `parts.parse` finds in the ANSWER lines --
#:           checked, so a re-parse that drifts fails loudly
#:   mode    'each'   one <img> per sentinel, text kept
#:           'bare'   one <img> only, ALL typed text of the part dropped (the
#:                    user's combined snip already shows labels/captions)
#:           'split'  custom, see SPLITS
#:           'synth'  no sentinel in the answer zone (3(d)); image added first
FIGURE_PLAN = {
    (1, "(b)(ii)"): dict(slots=["bii"], n_fig=1, mode="each"),
    (1, "(c)"):     dict(slots=["c"], n_fig=1, mode="each"),
    (2, "(d)"):     dict(slots=["d"], n_fig=1, mode="each"),
    (3, "(d)"):     dict(slots=["d"], n_fig=0, mode="synth"),
    (3, "(e)"):     dict(slots=["e"], n_fig=1, mode="each"),
    (4, "(b)(ii)"): dict(slots=["bii"], n_fig=2, mode="bare"),
    (4, "(c)"):     dict(slots=["c", "c2"], n_fig=19, mode="split"),
    (5, "(a)(iii)"): dict(slots=["aiii"], n_fig=2, mode="bare"),
    (5, "(b)"):     dict(slots=["b"], n_fig=2, mode="bare"),
    (6, "(b)(i)"):  dict(slots=["bi"], n_fig=1, mode="each"),
    (6, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="each"),
}


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


def _e(exp):
    return "10<sup>%s</sup>" % exp


#: MathType objects (no text layer) hand-typed from the rendered answers PDF,
#: in DOM order within the part; each entry replaces ONE FIG sentinel.
#: Cross-checked numerically: 0.66/44=0.015, 116/61=1.90, 1.90e-3*1e-8/1.50e-5
#: =1.267e-6, 6e-9/1.08e-2=5.556e-7, 4.5e-7/4.7e-11=9.57e3 -- each matches the
#: value the mark scheme prints beside it.
_b = lambda s: "[%s]" % s
OBJECT_FRACS = {
    (6, "(c)(i)"): [
        _frac("[HCO<sub>3</sub><sup>−</sup>][H<sup>+</sup>]", "[H<sub>2</sub>CO<sub>3</sub>]")],
    (6, "(c)(ii)"): [
        _frac("0.66", "44"),
        _frac("116", "61"),
        _frac("[1.90 × %s][1 × %s]" % (_e("−3"), _e("−8")),
              "[1.50 × %s]" % _e("−5"))],
    (6, "(e)(iii)"): [
        _frac("6 × %s" % _e("−9"), "1.08 × %s" % _e("−2"))],
    (6, "(e)(iv)"): [
        _frac("4.5 × %s" % _e("−7"), "4.7 × %s" % _e("−11"))],
}

#: (qnum, label) -> [(regex, replacement)], applied to the assembled ANSWER
#: lines of that part, once, and each MUST match (else a drift raises).
TEXT_FIXES = {
    # t-half: the docx builds it as a fraction 1/2 nested inside a subscript
    # (a MathType-era hack); typed as t<sub>½</sub>.
    (3, "(b)(iii)"): [(
        r"t<sub><span class=\"frac\">.*?</span></span></sub>(?==)",
        "<i>t</i><sub>½</sub> ")],
    # 6(e)(v): the equilibrium arrow is a tiny glyph PICTURE anchored ahead of
    # the equation; its visual slot is the run of spaces after "(s)".
    # 6(a)(i): the printed answer lines are "pair 1: ............HCO3- and ...";
    # leader dots of 4 ellipsis characters fall under the shared 5-dot rule.
    (6, "(a)(i)"): [(r"\s*…+\s*", " ")],
    # 3(b)(ii): equation-editor "ClCN" -- element l, as the same paper's
    # (b)(i)/(b)(iii) already have it.
    (3, "(b)(ii)"): [(r"\[ClCN\]", '[C<i class="el">l</i>CN]')],
    (6, "(e)(v)"): [
        (r"<b>\x00FIG\x00</b>(?=CaCO)", ""),
        (r"(?<=\(s\)) (?=Ca<sup>2\+</sup>)", " ⇌ ")],
}

#: Fewer figures than sentinels are declared above, but the FIG markers in
#: these lines are glyph pictures or objects already dealt with; nothing else.


#: Q3's equation-editor lines are typed with no spaces around = / x / /; Q6's
#: fractions likewise. Spaced for readability, TEXT nodes only.
SPACE_OPS = {(3, "(b)(ii)"), (3, "(b)(iii)"), (3, "(c)(i)"), (6, "(e)(iv)"),
             (6, "(e)(iii)"), (6, "(c)(ii)")}

#: A superscript minus typed as an ASCII hyphen (10<sup>-3</sup>, g cm<sup>-3</sup>)
#: in a paper that otherwise uses one dash consistently: en dash in Q3 (as its
#: own question text), U+2212 in Q6. Per-question, so no cross-question guess.
MINUS_STYLE = {1: "−", 3: "–", 6: "−"}


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
            fn = lambda s: "ACJC_H2_P2_Q%d_ans-%s_2024.png" % (q.qnum, s)
            mode = plan["mode"] if plan else None
            if mode == "bare":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = []
            elif mode == "synth":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
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
                    if re.fullmatch(r"\s*<img[^>]*>\s*", t):
                        return t.strip()
                    return '<span class="%s">%s</span>' % ("note" if note else "ans", t)
                if kind == "p":
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
