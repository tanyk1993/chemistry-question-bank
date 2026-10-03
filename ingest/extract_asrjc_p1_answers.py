"""Extract worked solutions for ASRJC 2024 H2 P1 (MCQ, ONE document for both
the question paper and the suggested solutions).

Document shape: the school's "QP and Ans" file is the question paper itself --
one Word table per question -- with one extra ROW appended to each question's
own table: a boxed answer row whose first paragraph reads "Ans: X" and which
runs on into the worked explanation, all in blue. (Q5 and Q6 share one table;
`inline_answers_prep.py` documents the split the QUESTION adapter needs. Here
the same grouping is redone, but the answer row is KEPT and the question rows
are the part thrown away -- the mirror image of the questions stage.)

So the answer, the explanation and the figures all live in that one row. Run
on the ORIGINAL document.xml, never the prepared copy (the prepared copy has
had every answer row deleted).

What is read from the row
-------------------------
* `answer_key`: the letter in "Ans: <b>X</b>". Cross-checked below against the
  letters printed in the Word PDF (`ANSWER_KEY_PDF`), read off the rendered
  pages independently of the XML.
* The explanation: every paragraph / nested table of the row, minus the "Ans"
  paragraph. Paragraphs go through `paragraph_html` (so OMML fractions come
  out as `span.frac`); a nested table becomes `table.cmp` (no th).

Figures (user hand-snips; `FIG_PLAN`)
-------------------------------------
Every drawing / OLE object in the row is a `\\x00FIG\\x00` sentinel. Each one is
resolved by an explicit per-question plan, consumed in DOCUMENT ORDER, and the
run REFUSES (raises) if a plan is short or has leftovers -- a figure silently
going missing or landing on the wrong placeholder is the costliest defect this
pipeline has (HANDOFF section 7).

  * a real picture  -> the user's snip, `<img class="ws-fig" data-asset=..>`
  * a typeset arrow (ChemWindow arrow objects) -> the character, typed
  * a short MathType fraction (Q6 m/M, Q13 Kc) -> `span.frac`, typed

Two collapsing rules, both from the user's own combined snips:
  * consecutive paragraphs that hold ONLY figures collapse into ONE figure
    (Q3's annotated diagram is a picture plus several floating text boxes; Q22's
    whole scheme; Q30's Data Booklet rows are four stacked pictures);
  * `TABLE_AS_IMAGE`: Q4's and Q18's whole answer table is snipped as ONE
    picture (typed explanations inside it are therefore not typed -- a worked
    solution is not searched, HANDOFF section 8, so nothing is lost to search).
    style-guide.md section 6: a combined snip replaces the whole typed body.

Whitespace-aligned lines
------------------------
The source aligns equations and ratios with runs of spaces and tabs, which HTML
collapses and `.ws` paragraphs do not preserve (only `.stem p.eqn` has
pre-wrap). Leading runs become `&emsp;` indentation, mid-line runs/tabs become
`&emsp;` gaps; Q19's hand-aligned ratio block is rebuilt as a small table.

Q20 is SKIPPED: it was unloaded from the live bank on 2026-10-02 (to be
discussed at the tagging stage), so it has no row to update.

Output feeds `gen_answers_migration.py --type mcq --school ASRJC --paper 1
--answer-key answer_key.json`.

Usage:
  python3 -m ingest.extract_asrjc_p1_answers <original document.xml> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("ASRJC", "H2", "P1", 2024)
SKIP = {20}

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"
W = "{%s}" % NS["w"]

# The letters printed in the Word PDF, one "Ans: X" per page (page n holds
# question n; Q4 and Q5 share page 4). Read from the rendered PDF text, NOT
# from the docx, so the check can disagree with the XML parse.
ANSWER_KEY_PDF = {
    1: "B", 2: "B", 3: "D", 4: "C", 5: "C", 6: "D", 7: "D", 8: "B", 9: "C",
    10: "C", 11: "D", 12: "B", 13: "C", 14: "D", 15: "D", 16: "C", 17: "D",
    18: "A", 19: "D", 20: "C", 21: "A", 22: "A", 23: "A", 24: "C", 25: "D",
    26: "D", 27: "B", 28: "D", 29: "C", 30: "C",
}

# Whole answer TABLE snipped as one picture.
TABLE_AS_IMAGE = {4, 18}

# The user's snip covers the ENTIRE worked solution (Q9: Methods 1 and 2, the
# typed Method 2 is dropped -- 2026-10-03), so the typed body is not emitted.
WHOLE_IMAGE = {9}

# Blocks dropped on purpose, per question: [(kind, regex-or-None, why)]. A
# paragraph rule must match exactly once and a table rule drops the one table
# there is; anything else raises. Q16: the passage about what THIS college
# used in its own titration and the screened-methyl-orange table are specific
# to the setting college (user, 2026-10-03).
DROP_BLOCKS = {
    16: [("p", r"^In reality, we have performed this titration before"),
         ("table", None)],
}

ARROW = ("html", " → ")
EQUIL = ("html", " ⇌ ")
_MM = ('<span class="frac"><span class="fnum"><i>m</i></span>'
       '<span class="fden"><i>M</i></span></span>')
_KC = ('<span class="frac"><span class="fnum">[Ag(NH<sub>3</sub>)<sub>2</sub>X]'
       '</span><span class="fden">[NH<sub>3</sub>]<sup>2</sup>[AgX]</span></span>')


def IMG(slot):
    return ("img", slot)


# Per-question plan for FIG sentinels, in document order AFTER the collapsing
# rules above. Q20 absent (skipped); a question absent here must have no FIG.
FIG_PLAN = {
    3: [IMG("ans-1")],                      # annotated tyrosine diagram
    4: [IMG("ans-1")],                      # whole table
    6: [("html", _MM), ("html", _MM)],      # m/M, twice (MathType)
    9: [IMG("ans-1")],                      # Methods 1 AND 2, one snip
    13: [("html", _KC), EQUIL, EQUIL],      # Kc fraction; two equilibria
    15: [EQUIL],
    16: [IMG("ans-1")],                     # titration curve
    17: [IMG("ans-1")],                     # displayed formula
    18: [IMG("ans-1")],                     # whole table
    22: [IMG("ans-1")],                     # whole annotated scheme
    24: [IMG("ans-a"), IMG("ans-b")],       # acid + alcohol; small alcohol
    29: [EQUIL] * 3,
    30: [IMG("ans-1"), IMG("ans-2")],       # Data Booklet E-theta table: the
                                            # excess-Zn one, then (page 31) the
                                            # excess-Sn one
}

# Answer-figure files, in the user's own naming (never invented here): a lone
# figure is `..._Qn_ans_2024.png` with slot "ans-1" (the slot must be suffixed
# -- index.html's isAnswerSlot needs ans[-_]), several are `..._ans-a_...`.
def asset_name(q, slot):
    if slot == "ans-1":
        return "ASRJC_H2_P1_Q%d_ans_2024.png" % q
    return "ASRJC_H2_P1_Q%d_%s_2024.png" % (q, slot)


# ---------------------------------------------------------------------------
def direct(el, tag):
    return [c for c in el if c.tag == W + tag]


def plain(el):
    return "".join(el.itertext())


_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS_P = re.compile(r"Ans\s*:\s*<b>\s*([A-D])\s*</b>")


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


def tidy(html: str) -> str:
    """Layout line-wrap <br> -> space; whitespace alignment -> &emsp;."""
    html = html.rstrip(" \t ")    # trailing alignment padding is not content
    html = re.sub(r"^(?:[ \t ]|&nbsp;)*<br>", "", html)
    html = re.sub(r"\s*<br>\s*", " ", html)
    m = re.match(r"^([ \t ]+)", html)
    lead = ""
    if m:
        w = _indent_gap(m.group(1))
        html = html[m.end():]
        if w >= 4:
            lead = "&emsp;" * min(8, max(1, round(w / 8)))

    def gap(mm):
        w = _indent_gap(mm.group(0))
        return "&emsp;" * (1 if w <= 7 else 2 if w <= 20 else 3)

    html = re.sub(r"[  ]*\t[ \t ]*|[  ]{4,}", gap, html)
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
                                paras.append(tidy(h))
                        row.append(("<br>".join(paras), cell_colspan(cell)))
                    rows.append(row)
                blocks.append(("table", rows))
    return blocks


def question_groups(document_xml):
    """{qnum: answer_row} -- the one row per question holding 'Ans:'."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    out = {}
    for tbl in direct(body, "tbl"):
        rows = direct(tbl, "tr")
        starts = [i for i, r in enumerate(rows)
                  if direct(r, "tc") and _QNUM.match(plain(direct(r, "tc")[0]))]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            grp = rows[s:e]
            qn = int(_QNUM.match(plain(direct(grp[0], "tc")[0])).group(1))
            ans = [r for r in grp if re.search(r"Ans\s*:", plain(r))]
            if len(ans) != 1:
                raise RuntimeError("Q%d: expected exactly one answer row, "
                                   "found %d" % (qn, len(ans)))
            if qn in out:
                raise RuntimeError("Q%d appears twice" % qn)
            out[qn] = ans[0]
    return out


def fig_only(html):
    s = html.replace(CENTRE, "").replace(FIG, "").strip()
    return html.count(FIG) > 0 and not s


def prepare(qn, blocks):
    """Pull the key, drop the 'Ans' paragraph, apply the collapsing rules."""
    key = None
    out = []
    for kind, payload in blocks:
        if kind == "p" and key is None and re.search(r"Ans\s*:", payload):
            m = _ANS_P.search(payload)
            if not m:
                raise RuntimeError("Q%d: cannot read the answer letter from %r"
                                   % (qn, payload))
            key = m.group(1)
            rest = _ANS_P.sub("", payload, count=1).replace(CENTRE, "")
            if rest.strip():
                if fig_only(rest):
                    out.append(("p", rest.strip()))
                else:
                    out.append(("p", rest))
            continue
        out.append((kind, payload))
    if key is None:
        raise RuntimeError("Q%d: no 'Ans:' paragraph found" % qn)

    if qn in WHOLE_IMAGE:
        out = [("p", FIG)]
    for kind, pat, in [(d[0], d[1]) for d in DROP_BLOCKS.get(qn, [])]:
        hit = [i for i, (k, p) in enumerate(out)
               if k == kind and (pat is None or re.search(pat, p))]
        if len(hit) != 1:
            raise RuntimeError("Q%d: drop rule %r/%r matched %d block(s), "
                               "expected 1" % (qn, kind, pat, len(hit)))
        del out[hit[0]]
    if qn in TABLE_AS_IMAGE:
        out = [("p", FIG) if k == "table" else (k, p) for k, p in out]

    merged = []
    for kind, payload in out:
        if (kind == "p" and fig_only(payload) and merged
                and merged[-1][0] == "p" and fig_only(merged[-1][1])):
            continue                      # collapse into the previous figure
        if kind == "p" and fig_only(payload):
            payload = FIG                 # one figure, however many objects
        merged.append((kind, payload))
    return key, merged


# Q19: a ratio block lined up with runs of spaces; rebuilt as a table.
Q19_START = re.compile(r"^\s*<b>L\s*:\s*M</b>")
Q19_TABLE = [
    ["", "<b>L : M</b>"],
    ["Number of H atoms", "= 1 : 9"],
    ["Relative rate of subt", "= 18 : 1"],
    ["Overall ratio", "= 18 : 9"],
    ["", "= 2 : 1"],
]


def wrap_answer(html):
    html = html.strip()
    if not html:
        return ""
    return '<span class="ans">%s</span>' % html


# Pictures that sit IN a line of text rather than in a block of their own.
# index.html forces img.ws-fig to display:block, so these carry an inline style
# (inline styles beat the stylesheet; sizeFig only touches max-width/height).
INLINE_FIGS = {(24, "ans-b")}
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
        text = tidy(payload.replace(CENTRE, ""))
        if qn == 19 and Q19_START.match(text.replace("&emsp;", "")):
            rows_html = []
            for r in Q19_TABLE:
                rows_html.append("<tr>%s</tr>"
                                 % "".join("<td>%s</td>" % c for c in r))
            out.append('<table class="cmp">%s</table>' % "".join(rows_html))
            skip = 4
            continue
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


def extract(document_xml):
    groups = question_groups(document_xml)
    if sorted(groups) != list(range(1, 31)):
        raise RuntimeError("expected questions 1-30, got %s" % sorted(groups))
    keys, ws, assets = {}, {}, []
    for qn in sorted(groups):
        key, blocks = prepare(qn, read_blocks(groups[qn]))
        keys[qn] = key
        if qn in SKIP:
            continue
        html, a = render(qn, blocks)
        ws[qn] = html
        for off, (slot, path) in enumerate(a, start=1):
            assets.append({"question": qn, "slot": slot, "path": path,
                           "offset": off})
    bad = {q: (keys[q], ANSWER_KEY_PDF[q]) for q in keys
           if keys[q] != ANSWER_KEY_PDF[q]}
    if bad:
        raise RuntimeError("answer key disagrees with the Word PDF: %r" % bad)
    return ws, assets, {q: keys[q] for q in keys if q not in SKIP}


if __name__ == "__main__":      # pragma: no cover
    doc, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    ws, assets, keys = extract(doc)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_assets.json").write_text(
        json.dumps(assets, indent=2), encoding="utf-8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in keys.items()}, indent=2),
        encoding="utf-8")
    print("worked solutions: %d (Q%s skipped)" % (len(ws), sorted(SKIP)))
    print("answer figures:   %d" % len(assets))
    print("answer keys:      %d, matches the Word PDF" % len(keys))
