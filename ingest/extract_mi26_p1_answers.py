"""Extract worked solutions + answer key for MI 2026 H2 P1 (MCQ, 30 Q).

DOCUMENT SHAPE (first seen: MI 2026 H2 P1, 2026-11-07). The school's key file is
the QUESTION PAPER ITSELF (one Word table per question, but TWO questions can
share a table: Q9/Q10 and Q13/Q14), with
  * the correct option marked by a YELLOW HIGHLIGHT (the option letter and its text;
    a statement number is highlighted too in Q13/Q26, only the letter row counts),
  * the working typed in BLUE (0000CC) next to the options or in an extra row; inside
    a blue note, colour-name words ("red", "light blue", "pink") are coloured as the
    colour they name, and Q23's stem carries blue sentences mixed with black stem text.
Question numbers are Word auto-numbers (AUTONUMLGL, empty cached result): a question
starts at every row whose first cell holds that field; counted 1..30 in document
order (the Student PDF is the independent check on the numbering).

WHAT IS KEPT: only the blue runs (plus the colour-name words) of a paragraph that holds
at least one blue run. Black text (the question) is never copied. A note typed beside
an option (the option's own row has its letter, or its statement number, in the cell to
the left) is prefixed with that label in bold, because "IMF negligible only at high T"
means nothing without the option it rejects.
KEY: read two independent ways -- the highlighted letter cell (docx) and the yellow
filled rectangle behind a letter in the Word PDF -- and the two must agree.
FIGURES: answer-side pictures are hand-snipped by the user; `FIG_PLAN` lists, per
question, the figure-only paragraphs/tables that are answer-side, in document order. The
run raises if the plan and the document disagree.

Usage: python3 -m ingest.extract_mi26_p1_answers <document.xml> <answers.pdf> <outdir> [--list]
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import extract_asrjc26_p1_answers as A
from .oxml import NS, Wq, paragraph_html

SCOPE = ("MI", "H2", "P1", 2026)
W = "{%s}" % NS["w"]
M = "{%s}" % NS["m"]
FIG, CENTRE = A.FIG, A.CENTRE
BLUE = {"0000CC"}
BLACK = {None, "", "auto", "000000"}

# Answer-side pictures: {question: [(kind, slot), ...]} in DOCUMENT ORDER inside the
# question's rows. kind "fig" = a figure-only paragraph (consecutive ones collapse to
# one picture); "table" = a nested answer table snipped whole. The question's own
# figures (stem structure, option graphs, apparatus) are never listed here.
FIG_PLAN: dict = {
    2: [("typed", "ans-1")],      # p/n/e table, plain text -> typed table.cmp
    18: [("typed", "ans-1")],     # ICE table; circled digits = order of filling in -> typed
    21: [("fig", "ans-1")],       # colour-coded 2-methylbutane
    23: [("fig", "ans-1")],       # annotated structure
    24: [("fig", "ans-1")],       # annotated structure (the stem's own figure is skipped)
    25: [("fig", "ans-1")],       # L / M / N structures
    27: [("table", "ans-1")],     # E-theta table with notes (holds inline pictures)
    28: [("table", "ans-1")],     # E-theta table with ticks (holds inline pictures)
}
SKIP_QFIGS: dict = {4: 1, 8: 4, 24: 1, 27: 1}   # figure-only paragraphs that belong to the QUESTION: {q: count of leading ones}


def asset_name(q, slot):
    return "MI_H2_P1_Q%d_%s_2026.png" % (q, slot.replace("-", "_") if slot != "ans-1" else "ans")


def direct(el, tag):
    return [c for c in el if c.tag == W + tag]


def ptext(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def run_colour(r):
    rp = r.find(W + "rPr")
    c = rp.find(W + "color") if rp is not None else None
    return c.get(W + "val") if c is not None else None


def run_highlight(r):
    rp = r.find(W + "rPr")
    h = rp.find(W + "highlight") if rp is not None else None
    return h.get(W + "val") if h is not None else None


def has_figure(p):
    return bool(p.findall(".//" + W + "drawing") or p.findall(".//" + W + "pict")
                or p.findall(".//" + W + "object"))


def blue_runs(p):
    return [r for r in p.iter(W + "r")
            if run_colour(r) in BLUE and "".join(t.text or "" for t in r.findall(W + "t")).strip()]


def blue_only_copy(p):
    """A copy of paragraph p with black text runs removed (mixed stem + answer lines)."""
    q = copy.deepcopy(p)
    for r in list(q.iter(W + "r")):
        txt = "".join(t.text or "" for t in r.findall(W + "t"))
        if run_colour(r) in BLACK and txt.strip() and not r.findall(W + "sym"):
            r.getparent().remove(r)
    return q


def question_groups(document_xml):
    """[(qn, [rows...])] -- from each row whose first cell holds AUTONUMLGL to the next."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    out, qn = [], 0
    for tbl in direct(body, "tbl"):
        rows = direct(tbl, "tr")
        starts = [i for i, r in enumerate(rows) if direct(r, "tc")
                  and any("AUTONUMLGL" in (it.text or "") for it in direct(r, "tc")[0].iter(W + "instrText"))]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            qn += 1
            out.append((qn, rows[s:e]))
    return out


def label_of(row, tc_index):
    """The option letter / statement number in the cell just left of tc_index, same row."""
    tcs = direct(row, "tc")
    for j in range(tc_index - 1, -1, -1):
        t = "".join(x.text or "" for x in tcs[j].iter(W + "t")).strip()
        if not t:
            continue
        return t if re.fullmatch(r"[A-D1-4]", t) else None
    return None


def key_from_docx(rows):
    got = []
    for tr in rows:
        for tc in direct(tr, "tc"):
            t = "".join(x.text or "" for x in tc.iter(W + "t")).strip()
            if re.fullmatch(r"[A-D]", t) and any(run_highlight(r) == "yellow" for r in tc.iter(W + "r")):
                got.append(t)
    return got


def pdf_keys(pdf):
    """Letters sitting on a yellow fill in the Word PDF, in reading order."""
    import pymupdf
    doc = pymupdf.open(str(pdf))
    keys = []
    for page in doc:
        rects = [pymupdf.Rect(d["rect"]) for d in page.get_drawings()
                 if d.get("fill") and tuple(round(c, 2) for c in d["fill"]) == (1.0, 1.0, 0.0)]
        found = []
        for r in rects:
            if r.width > 20:        # a highlighted phrase in the stem, not an option letter
                continue
            words = [w for w in page.get_text("words", clip=r + (-1, -1, 1, 1))
                     if re.fullmatch(r"[A-D]", w[4])]
            if words:
                found.append((round(r.y0), r.x0, words[0][4]))
        keys += [k for _, _, k in sorted(found)]
    return keys


def render_table(tbl_el):
    rows = []
    for tr in direct(tbl_el, "tr"):
        cells = []
        for tc in direct(tr, "tc"):
            paras = []
            for p in direct(tc, "p"):
                h = paragraph_html(p).replace(CENTRE, "")
                if h.strip():
                    paras.append(A.clean(h, None))
            cells.append("<td>%s</td>" % " ".join(paras))
        rows.append("<tr>%s</tr>" % "".join(cells))
    return '<table class="cmp">%s</table>' % "".join(rows)


def build(qn, rows, listing=False):
    """-> (worked_solution html, [asset dicts], list of figure descriptors seen)"""
    plan = list(FIG_PLAN.get(qn, []))
    skip_q = SKIP_QFIGS.get(qn, 0)
    out, assets, seen = [], [], []
    last_label, fig_run = None, False

    def take_fig(kind, what):
        nonlocal fig_run
        seen.append("%s:%s" % (kind, what))
        return None

    def emit_img(slot):
        path = asset_name(qn, slot)
        assets.append({"question": qn, "slot": slot, "path": path, "offset": len(assets) + 1})
        out.append('<p><img class="ws-fig" data-asset="%s" alt=""></p>' % path)

    qfig_seen = 0
    prev_fig = False
    for ri, tr in enumerate(rows):
        for ci, tc in enumerate(direct(tr, "tc")):
            for child in tc:
                if child.tag == W + "tbl":
                    blue = [r for r in child.iter(W + "r") if run_colour(r) in BLUE]
                    seen.append("table:%s" % ("answer" if blue else "question"))
                    if not blue:
                        continue
                    kind = plan.pop(0) if plan else (("typed", "x") if listing else None)
                    if not kind or kind[0] not in ("table", "typed"):
                        raise RuntimeError("Q%d: answer table not in FIG_PLAN" % qn)
                    if kind[0] == "table":
                        emit_img(kind[1])
                    else:
                        out.append(render_table(child))
                    last_label = None
                    prev_fig = False
                    continue
                if child.tag != W + "p":
                    continue
                if blue_runs(child):
                    src = blue_only_copy(child) if any(
                        run_colour(r) in BLACK and "".join(t.text or "" for t in r.findall(W + "t")).strip()
                        for r in child.iter(W + "r")) else child
                    h = paragraph_html(src)
                    h = A.clean(h, qn)
                    if not h.replace(CENTRE, "").strip():
                        continue
                    lab = label_of(tr, ci)
                    prefix = ""
                    if lab and lab != last_label:
                        prefix = "<b>%s</b>: " % lab
                    last_label = lab
                    body = A.wrap_answer(h.replace(CENTRE, ""))
                    out.append("<p>%s%s</p>" % (prefix, body))
                    prev_fig = False
                elif has_figure(child) and not ptext(child).replace(" ", "").strip():
                    if prev_fig:                       # consecutive figure paragraphs = one picture
                        continue
                    qfig_seen += 1
                    prev_fig = True
                    if qfig_seen <= skip_q:
                        seen.append("fig:question")
                        continue
                    seen.append("fig:answer?")
                    kind = plan.pop(0) if plan else (("fig", "ans-%d" % (len(assets) + 1)) if listing else None)
                    if not kind or kind[0] != "fig":
                        raise RuntimeError("Q%d: figure paragraph (row %d) not in FIG_PLAN" % (qn, ri))
                    emit_img(kind[1])
                    last_label = None
                elif has_figure(child):
                    prev_fig = False
                else:
                    prev_fig = False if ptext(child).strip() else prev_fig
    if plan:
        raise RuntimeError("Q%d: FIG_PLAN entries unused: %r" % (qn, plan))
    body = "\n".join(out)
    return '<div class="worked-solution">\n%s\n</div>' % body, assets, seen


def extract(document_xml, pdf, listing=False):
    groups = question_groups(document_xml)
    if [q for q, _ in groups] != list(range(1, 31)):
        raise RuntimeError("expected 30 questions, got %d" % len(groups))
    keys, ws, assets, seen_all = {}, {}, [], {}
    for qn, rows in groups:
        ks = key_from_docx(rows)
        if len(ks) != 1:
            raise RuntimeError("Q%d: %d highlighted option letters: %r" % (qn, len(ks), ks))
        keys[qn] = ks[0]
        html, a, seen = build(qn, rows, listing)
        ws[qn] = html
        assets += a
        seen_all[qn] = seen
    pk = pdf_keys(pdf)
    if len(pk) != 30:
        raise RuntimeError("the Word PDF shows %d highlighted letters, expected 30: %r" % (len(pk), pk))
    bad = {q: (keys[q], pk[q - 1]) for q in keys if keys[q] != pk[q - 1]}
    if bad:
        raise RuntimeError("answer key disagrees (docx, PDF): %r" % bad)
    return ws, assets, keys, seen_all


if __name__ == "__main__":      # pragma: no cover
    doc, pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    listing = "--list" in sys.argv
    try:
        ws, assets, keys, seen = extract(doc, pdf, listing)
    except RuntimeError as e:
        print("STOP:", e); raise SystemExit(1)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in keys.items()}, indent=2), encoding="utf-8")
    print("worked solutions: %d; answer figures: %d; keys: %d (docx = PDF)" % (len(ws), len(assets), len(keys)))
    print("".join(keys[q] for q in sorted(keys)))
    if listing:
        for q in sorted(seen):
            if any(x != "table:question" and x != "fig:question" for x in seen[q]):
                print(q, seen[q])
