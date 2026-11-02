#!/usr/bin/env python3
"""Square up HCI 2026 H2 P2's question tables so `parts.py` (table shape) applies.

SHAPE (same family as HCI 2024 H2 P2/P3): every question lives in a body-level
table, but each row carries ONE extra BLANK leading cell before the SEAB slots
(qnum | letter | roman | content), so row 0 / cell 0 is never a bare question
number and `parts_dispatch.detect_shape` says "flow".

  tables 0-1   candidate block + title block (cover; not touched)
  tables 2-7   5-column grids (blank | qnum | letter | roman | content):
               drop the leading blank cell on every row
               (a lone span-5 spacer row is narrowed to span 4)
  table 8      Q5(c)-(l), a 7-column grid  595 | 38 | 227 | 58 | 501 | 586 | 8948
               (blank | qnum-in-three-pieces | hairline | letter | roman | content).
               Every row starts with blank cells that end at or before grid
               column 3; those are replaced by ONE blank qnum cell, and a cell
               that STARTS in the hairline column 3 (the "(i)".."(l)" letter
               cells and the intro cell) loses one grid unit, so each row
               totals 4 units like the other tables.

Worked on a COPY of the unzipped docx; nothing else is touched (a table is not
a semantic unit in this family -- `parts.py` carries state across tables).

Usage: python3 -m ingest.hci26_p2_prep <unz-in> <unz-out>
Raises unless the expected table count is found and every dropped cell is
blank, so a different paper cannot be half-processed silently.
"""
from __future__ import annotations

import copy
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
    if len(tbls) != 9:
        raise SystemExit("expected 9 body tables (2 cover + 7 question), got %d"
                         % len(tbls))
    log = []
    for ti in range(2, 9):
        tbl = tbls[ti]
        ncols = len(tbl.findall(Wq + "tblGrid/" + Wq + "gridCol"))
        n_dropped = n_narrowed = 0
        for tr in tbl.findall("w:tr", NS):
            cells = tr.findall("w:tc", NS)
            if ncols == 5:
                if len(cells) == 1:
                    if _span(cells[0]) != 5:
                        raise SystemExit("table %d: lone cell span %d"
                                         % (ti, _span(cells[0])))
                    if _text(cells[0]):
                        raise SystemExit("table %d: spacer row holds text" % ti)
                    _set_span(cells[0], 4)
                    n_narrowed += 1
                    continue
                if _text(cells[0]):
                    raise SystemExit("table %d: leading cell holds text %r"
                                     % (ti, _text(cells[0])[:30]))
                tr.remove(cells[0])
                n_dropped += 1
            elif ncols == 7:
                # grid columns: 0 | 1 2 3 (qnum, in pieces) | 4 letter | 5 roman | 6 content
                col, lead, rest = 0, [], []
                for tc in cells:
                    s = _span(tc)
                    start, end = col, col + s - 1
                    col += s
                    if not rest and end <= 3 and not _text(tc):
                        lead.append(tc)
                    else:
                        rest.append((tc, start, end))
                if col != 7:
                    raise SystemExit("table 8: row totals %d grid units" % col)
                for tc in lead:
                    tr.remove(tc)
                n_dropped += len(lead)
                # one blank qnum cell, copied from a removed lead cell
                q = copy.deepcopy(lead[-1])
                for t in list(q.iter(Wq + "t")):
                    t.text = ""
                _set_span(q, 1)
                first = rest[0][0]
                first.addprevious(q)
                for tc, start, end in rest:
                    if start == 3:
                        _set_span(tc, _span(tc) - 1)
                        n_narrowed += 1
            else:
                raise SystemExit("table %d: unexpected %d grid columns"
                                 % (ti, ncols))
        log.append("question table %d: dropped %d leading blank cells, "
                   "narrowed %d" % (ti - 2, n_dropped, n_narrowed))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2]):
        print(line)
