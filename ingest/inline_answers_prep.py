"""Prepare a "question paper + suggested solutions in the SAME document" docx
for the table-shape QUESTION adapter (`questions.py`).

SHAPE (first seen: ASRJC 2024 H2 P1, 2026-10-02). The school's "QP and Ans"
file is the question paper itself, with one extra row appended to each
question's own table -- a boxed answer row whose text starts "Ans: X" and runs
on into a worked explanation, all in blue. The question rows above it are
untouched, so `questions.py` could parse them as-is *if the answer row were
not there*. It must go before parsing for three reasons:

  1. The task at this stage is QUESTIONS ONLY; answers are a later stage and
     must not leak into `content_html` / `content_text` / `options`.
  2. The answer rows use glyphs the question text does not (Symbol F071 for
     E-theta, etc.), and `symbols.sym_to_text` raises on an unmapped glyph
     by design -- the run would die on content that is being thrown away.
  3. `questions.py` treats any row after the options as "extra_html"
     (kept so nothing is silently discarded) -- so it would file the whole
     worked solution into the stem.

TWO THINGS THIS DOES, on a COPY of document.xml (the original is never
touched):

  * drop every row whose text contains "Ans:" (a text-box-borne answer, as in
    Q3/Q22, puts the diagram labels BEFORE "Ans:" in document order, so test
    the whole row, not the start of it);
  * split a table that holds MORE THAN ONE question (ASRJC Q5 and Q6 share a
    table -- Q6's number is in row 5) into one table per question, because
    `questions.py` assumes "one top-level table per question".

  * HOIST a nested options table. ASRJC Q4 (columnar: molecule / shape /
    polarity, rows A-D) and Q6 (four graphs laid out 2x2 as [A][fig][B][fig])
    set their options as a table NESTED INSIDE the stem cell, so
    `questions.py` sees a stem with no option rows at all ("fewer than 2
    options"). The nested table's rows are moved up into the outer table,
    each prefixed with a blank cell -- the exact shape of an ordinary
    row-table / inline option row (cf. Q11, Q1) -- so the one existing code
    path handles them. Only done when the outer table has NO option-letter
    cell of its own and the nested table holds >= 4 bare A-E letter cells.

It reports what it dropped and split, and REFUSES (raises) if a table ends up
with no answer row or more than one -- a silent miss in either direction
would put an answer into a question or delete a question's own text.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS = re.compile(r"Ans\s*:")


def _text(e) -> str:
    return "".join(e.itertext())


_OPT = re.compile(r"^\s*([A-E])\s*$")


def _blank_tc():
    tc = etree.Element(W + "tc")
    etree.SubElement(tc, W + "p")
    return tc


def _hoist_nested_options(t) -> bool:
    """Move a stem-cell-nested options table up into `t`'s own rows."""
    rows = t.findall("w:tr", NS)
    # does the outer table already carry option letters below row 0?
    for r in rows[1:]:
        for c in r.findall("w:tc", NS):
            if _OPT.match(_text(c)):
                return False
    stem = rows[0].findall("w:tc", NS)[-1]
    nested = stem.findall("w:tbl", NS)
    if len(nested) != 1:
        return False
    nt = nested[0]
    letters = [c for c in nt.iter(W + "tc") if _OPT.match(_text(c))]
    if len(letters) < 4:
        return False
    stem.remove(nt)
    anchor = rows[0]
    for r in nt.findall("w:tr", NS):
        r.insert(r.index(r.find("w:tc", NS)), _blank_tc())   # leading blank
        anchor.addnext(r)
        anchor = r
    return True


def prepare(src_document_xml, dst_document_xml):
    """Write the prepared copy; return a list of human-readable report lines."""
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    report = []

    for tbl in list(body.findall("w:tbl", NS)):
        rows = tbl.findall("w:tr", NS)
        if not rows:
            continue
        # Skip the header/name tables: they open with no bare question number
        # anywhere and carry no answer row.
        has_q = any(
            _QNUM.match(_text(r.findall("w:tc", NS)[0]))
            for r in rows if r.findall("w:tc", NS))
        if not has_q:
            continue

        # 1. split at every later row that opens with a bare question number
        starts = [i for i, r in enumerate(rows)
                  if r.findall("w:tc", NS)
                  and _QNUM.match(_text(r.findall("w:tc", NS)[0]))]
        groups = []
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            groups.append(rows[s:e])
        # rows before the first start (none expected) stay with the first group
        if starts and starts[0] != 0:
            groups[0] = rows[:starts[0]] + groups[0]

        if len(groups) > 1:
            qs = [_QNUM.match(_text(g[0].findall("w:tc", NS)[0])).group(1)
                  for g in groups]
            report.append("split one table into questions %s" % qs)
            prev = tbl
            for g in groups[1:]:
                new = etree.SubElement(body, W + "tbl")      # placeholder pos
                body.remove(new)
                for child in tbl:
                    if child.tag in (W + "tblPr", W + "tblGrid"):
                        new.append(copy.deepcopy(child))
                for r in g:
                    new.append(r)                            # moves the row
                prev.addnext(new)
                prev = new

        # 2. drop answer rows from every table made from this one
        # (collect the possibly-several tables now holding these questions)
        made = [tbl]
        nxt = tbl
        for _ in range(len(groups) - 1):
            nxt = nxt.getnext()
            made.append(nxt)
        for t in made:
            trs = t.findall("w:tr", NS)
            qn = _text(trs[0].findall("w:tc", NS)[0]).strip()
            ans_rows = [r for r in trs if _ANS.search(_text(r))]
            if len(ans_rows) != 1:
                raise RuntimeError(
                    "Q%s: expected exactly one answer row, found %d -- "
                    "refusing to guess which rows are answer and which are "
                    "question" % (qn, len(ans_rows)))
            t.remove(ans_rows[0])
            report.append("Q%s: dropped answer row (%d chars)"
                          % (qn, len(_text(ans_rows[0]))))
            if _hoist_nested_options(t):
                report.append("Q%s: hoisted nested options table into the "
                              "outer table's rows" % qn)

    tree.write(str(dst_document_xml), xml_declaration=True,
               encoding="UTF-8", standalone=True)
    return report


if __name__ == "__main__":      # pragma: no cover
    import sys
    for line in prepare(Path(sys.argv[1]), Path(sys.argv[2])):
        print(line)
