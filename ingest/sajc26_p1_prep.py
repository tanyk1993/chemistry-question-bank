"""Prepare SAJC 2026 H2 P1 (9476/01, 30 MCQ) for `questions.py` (table shape).

SHAPE (first seen: SAJC 2026 H2 P1, 2026-11-21). The questions sit in THREE
body-level Word tables rather than one table per question:

  * table A (32 rows):  Q1-Q7  (rows `[N | stem]`, then option rows `[blank | A | text]`)
  * table B (102 rows): Q8-Q29
  * table C (6 rows):   a blank lead-in row, then Q30

`parse_dispatch` / `questions.py` only read a question number from cell 0 of
ROW 0 of a table, so only Q1 and Q8 were parsed (2 of 30).

WHAT THIS DOES, on a COPY of the unzipped docx (the original is never touched):
split every table at each row whose first cell is a bare 1-2 digit number into
one table per question (same technique as jpjc26_p1_prep.py); rows BEFORE the
first such row (table C's blank lead-in) stay in the original table. It
REFUSES (raises) unless the question numbers found are exactly 1..30.

Usage: python3 -m ingest.sajc26_p1_prep <src_unz_dir> <dst_unz_dir>
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
EXPECTED = list(range(1, 31))


def _text(e) -> str:
    return "".join(e.itertext(W + "t")).strip()


def _first_cell_text(tr) -> str:
    tcs = tr.findall("w:tc", NS)
    return _text(tcs[0]) if tcs else ""


def prepare(src_unz, dst_unz):
    """Write the prepared copy; return human-readable report lines."""
    src_unz, dst_unz = Path(src_unz), Path(dst_unz)
    if dst_unz.exists():
        shutil.rmtree(dst_unz)
    shutil.copytree(src_unz, dst_unz)
    doc = dst_unz / "word" / "document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    report, found = [], []

    for tbl in list(body.findall("w:tbl", NS)):
        rows = tbl.findall("w:tr", NS)
        starts = [i for i, r in enumerate(rows)
                  if _QNUM.match(_first_cell_text(r))]
        if not starts:
            continue
        groups = [rows[s:(starts[n + 1] if n + 1 < len(starts) else len(rows))]
                  for n, s in enumerate(starts)]
        qnums = [int(_QNUM.match(_first_cell_text(g[0])).group(1))
                 for g in groups]
        found.extend(qnums)
        lead = rows[:starts[0]]
        if len(groups) == 1 and not lead:
            continue
        if lead:
            report.append("table with %d lead-in row(s): question rows split "
                          "off from Q%d" % (len(lead), qnums[0]))
        if len(groups) > 1:
            report.append("split one table into questions %s" % qnums)
        prev = tbl
        # the first group stays in `tbl` only when there is no lead-in
        move = groups if lead else groups[1:]
        for g in move:
            new = etree.Element(W + "tbl")
            for child in tbl:
                if child.tag in (W + "tblPr", W + "tblGrid"):
                    new.append(copy.deepcopy(child))
            for r in g:
                new.append(r)                       # moves the row
            prev.addnext(new)
            prev = new

    if sorted(found) != EXPECTED:
        raise RuntimeError("question numbers found %s, expected 1..30"
                           % sorted(found))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    report.append("OK: questions 1..30 each have their own table")
    return report


if __name__ == "__main__":          # pragma: no cover
    for line in prepare(sys.argv[1], sys.argv[2]):
        print(line)
