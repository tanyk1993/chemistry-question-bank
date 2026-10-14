#!/usr/bin/env python3
"""Square up HCI 2024 H2 P2's question tables so `parts.py` (table shape) applies.

SHAPE: every question lives in a body-level table, but each row carries ONE or
TWO extra BLANK leading cells before the SEAB slots (qnum | letter | roman |
content), so row 0 / cell 0 is never a bare question number and
`parts_dispatch.detect_shape` says "flow" and finds no questions.

  tables 0-2 (Q1-Q2(d)(ii), Q2(d)(iii), Q3-Q4)  one leading blank cell per row
  table 3 (Q5)   a 10-column grid; ONE blank leading cell per row in the
                 revised export (the first export had two on rows 0-13).

Worked on a COPY of the unzipped docx; nothing else is touched (a table is not
a semantic unit in this family -- `parts.py` carries state across tables).

Usage: python3 -m ingest.hci_p2_prep <unz-in> <unz-out>
Raises unless exactly the expected number of leading cells is dropped and every
dropped cell is blank, so a different paper cannot be half-processed silently.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS, Wq


def _text(tc) -> str:
    return "".join(tc.itertext(Wq + "t")).strip()


def _span(tc) -> int:
    g = tc.find(Wq + "tcPr/" + Wq + "gridSpan")
    return int(g.get(Wq + "val")) if g is not None else 1


def prep(unz_in: Path, unz_out: Path) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)
    log = []

    # the cover tables (candidate block, title block, and in the first export
    # an examiner box) come first; the LAST four tables are the question tables.
    q_tbls = tbls[-4:]
    if len(tbls) < 5:
        raise SystemExit("expected cover tables plus 4 question tables, got %d"
                         % len(tbls))
    dropped_by_table = []
    for ti, tbl in enumerate(q_tbls):
        n_dropped = 0
        for tr in tbl.findall("w:tr", NS):
            cells = tr.findall("w:tc", NS)
            k = 1      # every row, every table, in the revised export
            if len(cells) <= k:
                continue
            for tc in cells[:k]:
                if _text(tc):
                    raise SystemExit("table %d: a leading cell to drop holds "
                                     "text %r" % (ti, _text(tc)[:30]))
            for tc in cells[:k]:
                tr.remove(tc)
            n_dropped += k
        dropped_by_table.append(n_dropped)
        log.append("question table %d: dropped %d leading blank cells"
                   % (ti, n_dropped))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2]):
        print(line)
