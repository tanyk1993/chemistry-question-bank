"""Prepare a table-shape MCQ question paper whose tables are
`[blank | number | content]` with options/statements NESTED inside the content
cell, for `questions.py`.

SHAPE (first seen: HCI 2024 H2 P1, 2026-10-12). Every question is a Word table
(so this is the table family, not the flow one), but:

  * row 0 is THREE cells, `[blank | "12" | stem]`. `questions.py` and
    `parse_dispatch.detect_shape` read the question number from cell 0 of row
    0, so on this layout the dispatcher says "flow" and the flow adapter finds
    no questions at all (the symptom: `max() iterable argument is empty`).
  * the options (and numbered statements) are not rows of the question table.
    They are a table NESTED inside the content cell: `[A][text][B][text]...`
    all on ONE nested row (a 1x4 inline option row), or one nested row per
    option, or a header + A-D grid. Q10 has TWO nested tables in one cell
    (statements, then options).
  * Q25, Q26 and Q27 share ONE table (Q26's and Q27's numbers sit in rows 3
    and 5), as ASRJC Q5/Q6 did (`inline_answers_prep.py`).

WHAT THIS DOES, on a COPY of the unzipped docx (the original is never touched):

  1. split a table that holds more than one question into one table per
     question (a row whose cell 1 is a bare number and cell 0 is blank starts
     a question);
  2. drop the leading blank cell of every row of a question table, so the
     number is cell 0 of row 0, exactly what `questions.py` reads;
  3. HOIST nested tables into rows of the question table, each hoisted row
     prefixed with one blank cell (the shape of an ordinary option row, so the
     one existing code path handles it). A nested table is hoisted when
       - it carries bare A-E option-letter cells, or
       - it is a numbered statement table (first column 1, 2, 3 ... in order), or
       - it sits in a row below row 0 (Q5's data table).
     A nested table in row 0 that is none of those stays where it is: it is
     STEM content and `questions._cell_html` renders it in place, between the
     paragraphs that surround it (Q26's formula/numeral table has a sentence
     after it, and hoisting would move that sentence above the table).

It REFUSES (raises) unless the question numbers it finds are exactly 1..N, so
a missed or doubled question cannot slip through.
"""
from __future__ import annotations

import copy
import re
import shutil
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_OPT = re.compile(r"^\s*([A-E])\s*$")


def _text(e) -> str:
    return "".join(e.itertext(W + "t")).strip()


def _cells(tr):
    return tr.findall("w:tc", NS)


def _is_start(tr) -> bool:
    c = _cells(tr)
    return len(c) >= 2 and not _text(c[0]) and bool(_QNUM.match(_text(c[1])))


def _blank_tc():
    tc = etree.Element(W + "tc")
    etree.SubElement(tc, W + "p")
    return tc


def _has_letters(nt) -> bool:
    return any(_OPT.match(_text(c)) for c in nt.iter(W + "tc"))


def _is_numbered(nt) -> bool:
    """A statements table: column 0 reads 1, 2, 3 ... in order."""
    rows = nt.findall("w:tr", NS)
    first = [_text(_cells(r)[0]) for r in rows if _cells(r)]
    first = [f for f in first if f]
    return bool(first) and first == [str(i + 1) for i in range(len(first))]


def _hoist(tbl, report, qn) -> None:
    rows = tbl.findall("w:tr", NS)
    for ri, tr in enumerate(rows):
        cs = _cells(tr)
        if not cs:
            continue
        host = cs[-1]
        anchor = tr
        for nt in list(host.findall("w:tbl", NS)):
            if not (_has_letters(nt) or _is_numbered(nt) or ri > 0):
                continue
            host.remove(nt)
            n = 0
            for r in nt.findall("w:tr", NS):
                r.insert(r.index(r.find("w:tc", NS)), _blank_tc())
                anchor.addnext(r)
                anchor = r
                n += 1
            report.append("Q%s: hoisted a nested table (%d rows) out of row %d"
                          % (qn, n, ri))


def prepare(src_unz, dst_unz):
    """Write the prepared copy of the unzipped docx; return report lines."""
    src_unz, dst_unz = Path(src_unz), Path(dst_unz)
    if dst_unz.exists():
        shutil.rmtree(dst_unz)
    shutil.copytree(src_unz, dst_unz)
    doc = dst_unz / "word" / "document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    report = []

    for tbl in list(body.findall("w:tbl", NS)):
        rows = tbl.findall("w:tr", NS)
        starts = [i for i, r in enumerate(rows) if _is_start(r)]
        if not starts:
            continue
        groups = []
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            groups.append(rows[s:e])
        made = [tbl]
        if len(groups) > 1:
            qs = [_text(_cells(g[0])[1]) for g in groups]
            report.append("split one table into questions %s" % qs)
            prev = tbl
            for g in groups[1:]:
                new = etree.Element(W + "tbl")
                for child in tbl:
                    if child.tag in (W + "tblPr", W + "tblGrid"):
                        new.append(copy.deepcopy(child))
                for r in g:
                    new.append(r)                      # moves the row
                prev.addnext(new)
                prev = new
                made.append(new)

        for t in made:
            trs = t.findall("w:tr", NS)
            qn = _text(_cells(trs[0])[1])
            for tr in trs:
                cs = _cells(tr)
                if cs and not _text(cs[0]) and len(cs) > 1:
                    tr.remove(cs[0])
            _hoist(t, report, qn)

    nums = []
    for tbl in body.findall("w:tbl", NS):
        tr = tbl.find("w:tr", NS)
        if tr is None:
            continue
        cs = _cells(tr)
        if cs and _QNUM.match(_text(cs[0])):
            nums.append(int(_text(cs[0])))
    if nums != list(range(1, len(nums) + 1)):
        raise RuntimeError("question numbers are not exactly 1..N: %r" % nums)
    report.append("question tables: %d (1..%d)" % (len(nums), len(nums)))

    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return report


if __name__ == "__main__":      # pragma: no cover
    import sys
    for line in prepare(sys.argv[1], sys.argv[2]):
        print(line)
