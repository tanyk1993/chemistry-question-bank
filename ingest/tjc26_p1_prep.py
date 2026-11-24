"""TJC 2026 H2 P1 (9476/01, 30 MCQ): question-only copy of the "QP + suggested
answers in one docx" file, for `questions.py` (table shape).

SHAPE (first seen: TJC 2026 H2 P1, 2026-11-24). One Word table per question,
EXCEPT:
  * a 3-row answer-KEY table at the top (cells "1".."10", "C","B",.. ): its
    first cell is a bare number, so it must be dropped, not read as Q1;
  * Q11+Q12 share a table, and so do Q13+Q14 (split at the second number);
  * the answer text (blue, starting "Answer: X") is either an extra row INSIDE
    the question's table (Q1, Q2, Q5-Q17) or body-level paragraphs after the
    table (Q3, Q4, Q18-Q30). The body-level ones are never read by
    `questions.py` (it walks tables only); the in-table rows are dropped here
    so they cannot leak into the stem as extra_html.

WHAT THIS DOES, on a COPY of the unzipped docx (the original is never touched):
  1. remove the answer-key table;
  2. split every table at each row whose first cell is a bare 1-2 digit number
     into one table per question;
  3. drop every row whose text starts with "Answer";
  4. REFUSE (raise) unless the question numbers are exactly 1..30 and no
     question table still holds an "Answer" row.

Usage: python3 -m ingest.tjc26_p1_prep <src_unz_dir> <dst_unz_dir>
"""
from __future__ import annotations

import copy
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS = re.compile(r"^\s*Answer\s*:")
EXPECTED = list(range(1, 31))


def _text(e) -> str:
    return "".join(e.itertext(W + "t")).strip()


def _cells(tr):
    return tr.findall("w:tc", NS)


def _first(tr) -> str:
    c = _cells(tr)
    return _text(c[0]) if c else ""


def _is_key_table(tbl) -> bool:
    rows = tbl.findall("w:tr", NS)
    return bool(rows) and len(_cells(rows[0])) >= 10 and all(
        _QNUM.match(_text(c)) for c in _cells(rows[0]))


def prepare(src_unz, dst_unz):
    src_unz, dst_unz = Path(src_unz), Path(dst_unz)
    if dst_unz.exists():
        shutil.rmtree(dst_unz)
    shutil.copytree(src_unz, dst_unz)
    doc = dst_unz / "word" / "document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    report, found = [], []

    for tbl in list(body.findall("w:tbl", NS)):
        if _is_key_table(tbl):
            body.remove(tbl)
            report.append("removed the answer-key table")
            continue
        rows = tbl.findall("w:tr", NS)
        starts = [i for i, r in enumerate(rows) if _QNUM.match(_first(r))]
        if not starts:
            continue
        groups = [rows[s:(starts[n + 1] if n + 1 < len(starts) else len(rows))]
                  for n, s in enumerate(starts)]
        qnums = [int(_QNUM.match(_first(g[0])).group(1)) for g in groups]
        found.extend(qnums)
        if len(groups) > 1:
            report.append("split one table into questions %s" % qnums)
            prev = tbl
            for g in groups[1:]:
                new = etree.Element(W + "tbl")
                for child in tbl:
                    if child.tag in (W + "tblPr", W + "tblGrid"):
                        new.append(copy.deepcopy(child))
                for r in g:
                    new.append(r)                       # moves the row
                prev.addnext(new)
                prev = new

    # drop the in-table answer rows, per question table
    dropped = 0
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if not rows or not _QNUM.match(_first(rows[0])):
            continue
        qn = _first(rows[0])
        for r in rows:
            if any(_ANS.match(_text(c)) for c in _cells(r)):
                tbl.remove(r)
                dropped += 1
                report.append("Q%s: dropped in-table answer row (%d chars)"
                              % (qn, len(_text(r))))
    report.append("%d in-table answer rows dropped" % dropped)

    if sorted(found) != EXPECTED:
        raise RuntimeError("question numbers found %s, expected 1..30"
                           % sorted(found))
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if rows and _QNUM.match(_first(rows[0])):
            for r in rows:
                if "Answer" in _text(r):
                    raise RuntimeError("Q%s still holds an 'Answer' row: %r"
                                       % (_first(rows[0]), _text(r)[:60]))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    report.append("OK: questions 1..30 each have their own table")
    return report


if __name__ == "__main__":          # pragma: no cover
    for line in prepare(sys.argv[1], sys.argv[2]):
        print(line)
