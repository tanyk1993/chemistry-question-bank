"""Prepare JPJC 2024 H2 P1 (table-shape MCQ) for `questions.py`.

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

Usage: python3 -m ingest.jpjc_p1_prep <src_unz_dir> <dst_unz_dir>
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

    # Q5: the four graph options each carry MathType axis labels (1/p, pV/T)
    # as separate OLE equation objects beside the graph's native shape. The
    # parser cannot attribute those extra pictures to an option letter (6
    # figures vs 4 letters) and the whole-graph snip contains them anyway, so
    # they are removed here; asserted: exactly 4 objects, all Equation.DSMT4.
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if rows and _first_cell_text(rows[0]) == "5":
            objs = [o for o in tbl.iter(W + "object")
                    if any(e.get("ProgID") == "Equation.DSMT4"
                           for e in o.iter("{urn:schemas-microsoft-com:office:office}OLEObject"))]
            if len(objs) != 4:
                raise RuntimeError("Q5: expected 4 axis-label equations, "
                                   "found %d" % len(objs))
            for o in objs:
                o.getparent().remove(o)
            report.append("Q5: removed 4 axis-label equation objects "
                          "(inside the option-graph snips)")

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
