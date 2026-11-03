#!/usr/bin/env python3
"""Square up HCI 2026 H2 P3's question tables so `parts.py` (table shape) applies.

SHAPE (same family as HCI 2026 H2 P2): every question lives in a body-level
table, but each row carries ONE extra BLANK leading cell before the SEAB slots
(qnum | letter | roman | content), so row 0 / cell 0 is never a bare question
number and `parts_dispatch.detect_shape` says "flow".

  body tables 0-1   candidate block + title block (cover; not touched)
  table 2   Q1(a)        4 grid cols  (blank | qnum | letter | content), no roman
                         column at all (parts.py reads a 3-cell regime natively)
  table 3   Q1(b)-(d)    6 grid cols  (blank | qnum | letter | roman | content | sliver)
  table 4   Q2(a)-(e)(iii)  5 grid cols (blank | qnum | letter | roman | content)
  table 5   Q3           6 grid cols  (... | sliver 14)
  table 6   Q4 / Q5(...) 5 grid cols
  table 7   Q5           5 grid cols

What this does, on a COPY of the unzipped docx (the original is never touched):
  * drops the leading blank cell of every row (a lone span-N spacer row is
    narrowed by one);
  * in a 6-column grid, removes the trailing hairline "sliver" column: the cell
    covering it loses one grid unit (or, if it is a lone blank cell, is removed).

Usage: python3 -m ingest.hci26_p3_prep <unz-in> <unz-out>
Raises unless the expected table count is found and every dropped cell is
blank, so a different paper cannot be half-processed silently.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS, Wq

EXPECT_TABLES = 8          # 2 cover + 6 question tables
EXPECT_NCOLS = {2: 4, 3: 6, 4: 5, 5: 6, 6: 5, 7: 5}


def _text(tc) -> str:
    return "".join(tc.itertext(Wq + "t")).strip()


def _span(tc) -> int:
    g = tc.find(Wq + "tcPr/" + Wq + "gridSpan")
    return int(g.get(Wq + "val")) if g is not None else 1


def _set_span(tc, n: int) -> None:
    tcpr = tc.find(Wq + "tcPr")
    g = tcpr.find(Wq + "gridSpan") if tcpr is not None else None
    if n == 1:
        if g is not None:
            tcpr.remove(g)
        return
    if g is None:
        g = etree.SubElement(tcpr, Wq + "gridSpan")
    g.set(Wq + "val", str(n))


def prep(unz_in: Path, unz_out: Path) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)
    if len(tbls) != EXPECT_TABLES:
        raise SystemExit("expected %d body tables (2 cover + 6 question), got %d"
                         % (EXPECT_TABLES, len(tbls)))
    log = []
    for ti in range(2, EXPECT_TABLES):
        tbl = tbls[ti]
        ncols = len(tbl.findall(Wq + "tblGrid/" + Wq + "gridCol"))
        if ncols != EXPECT_NCOLS[ti]:
            raise SystemExit("table %d: expected %d grid columns, got %d"
                             % (ti, EXPECT_NCOLS[ti], ncols))
        n_dropped = n_narrowed = n_sliver = 0
        for tr in tbl.findall("w:tr", NS):
            cells = tr.findall("w:tc", NS)
            if _text(cells[0]):
                raise SystemExit("table %d: leading cell holds text %r"
                                 % (ti, _text(cells[0])[:30]))
            if _span(cells[0]) != 1:
                raise SystemExit("table %d: leading cell spans %d"
                                 % (ti, _span(cells[0])))
            tr.remove(cells[0])
            n_dropped += 1
            cells = cells[1:]
            if ncols == 6:
                # grid col 5 is the hairline sliver; after the leading drop it
                # is the LAST unit of the row (when the row reaches it at all).
                col = 1
                for tc in cells:
                    s = _span(tc)
                    if col + s - 1 == 5:          # this cell covers the sliver
                        if s > 1:
                            _set_span(tc, s - 1)
                            n_sliver += 1
                        else:
                            if _text(tc):
                                raise SystemExit("table %d: sliver cell holds text %r"
                                                 % (ti, _text(tc)[:30]))
                            tr.remove(tc)
                            n_sliver += 1
                    col += s
        log.append("question table %d (%d grid cols): dropped %d leading blank cells, "
                   "sliver trimmed %d" % (ti - 2, ncols, n_dropped, n_sliver))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2]):
        print(line)
