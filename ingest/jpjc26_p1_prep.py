"""Prepare JPJC 2026 H2 P1 (table-shape MCQ) for `questions.py`.

Same shape as JPJC 2024 P1 (see jpjc_p1_prep.py); the 2024-only Q5 axis-label
equation removal is dropped (2026 Q5 is a calculation).

SHAPE (first seen: JPJC 2024 H2 P1, 2026-10-16). One Word table per question
(`questions.py`, table family), EXCEPT that three tables hold more than one
thing:

  * the COVER-PAGE table carries Q1 as its last rows (rows 24-29: `[1 | stem]`
    ... option rows) after the name/instruction rows;
  * Q9's table also holds Q10 (a second `[10 | stem]` row, then its options);
  * Q13's table also holds Q14.

`parse_dispatch` / `questions.parse` only read a question number from cell 0 of
ROW 0 of a table, so Q1, Q10 and Q14 were silently missing (27 of 30 parsed).

WHAT THIS DOES, on a COPY of the unzipped docx (the original is never touched):
split every table at each row whose first cell is a bare 1-2 digit number into
one table per question; rows BEFORE the first such row (the cover page) stay in
the original table. It REFUSES (raises) unless the question numbers found are
exactly 1..30, so a missed or doubled question cannot slip through.

Usage: python3 -m ingest.jpjc26_p1_prep <src_unz_dir> <dst_unz_dir>
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

    # Q4 sits as a whole question table NESTED in a single merged cell (the
    # first row of the Q5 table): hoist it out as a sibling table so the
    # splitter below sees it. Asserted: exactly one such table.
    hoisted = 0
    for tbl in list(body.findall("w:tbl", NS)):
        rows = tbl.findall("w:tr", NS)
        if not rows:
            continue
        tcs = rows[0].findall("w:tc", NS)
        if len(tcs) != 1:
            continue
        inner = tcs[0].findall("w:tbl", NS)
        if len(inner) == 1 and _QNUM.match(_first_cell_text(inner[0].find("w:tr", NS))) \
                and not _text(rows[0]).startswith("NAME"):
            tbl.addprevious(inner[0])               # moves the nested table
            tbl.remove(rows[0])                     # drop the now-empty wrapper row
            hoisted += 1
            report.append("hoisted nested question table (Q%s) out of a merged cell"
                          % _first_cell_text(inner[0].find("w:tr", NS)))
    if hoisted != 1:
        raise RuntimeError("expected to hoist exactly 1 nested question table, got %d" % hoisted)

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
            report.append("table with %d lead-in rows (cover page): "
                          "question rows split off from Q%d" %
                          (len(lead), qnums[0]))
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
