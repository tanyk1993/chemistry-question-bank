"""DHS 2026 H2 P1 (9476/01, 30 MCQ): question-only copy of the paper docx.

The "QP" file ends with the school's answer-key section ("Paper 1 MCQ - Answers":
three 10-column key tables, the multiple-completion tally, a floating picture).
Left in, the three key tables open on a bare number (1, 11, 21), so the table
adapter reads them as three extra questions. The answers stage is separate (and
deliberately not started), so everything after the Q30 table is cut from the
QUESTION copy and reported. The original directory is never touched.

usage: python3 -m ingest.dhs26_p1_prep <unz_dir> <unz_q_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS
from . import questions as _tbl

W = "{%s}" % NS["w"]


def prep(unz_dir, out_dir):
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    doc = out_dir / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)

    # the last real question: the table whose first cell is exactly "30"
    last = None
    for el in body:
        if etree.QName(el).localname != "tbl":
            continue
        rows = el.findall("w:tr", NS)
        c0 = rows[0].findall("w:tc", NS) if rows else []
        if c0 and _tbl.QNUM_RE.match(_tbl._cell_text(c0[0])) \
                and _tbl._cell_text(c0[0]).strip() == "30":
            last = el
    if last is None:
        raise SystemExit("dhs26_p1_prep: Q30 table not found")

    removed = []
    drop = False
    for el in list(body):
        if el is last:
            drop = True
            continue
        if not drop:
            continue
        if etree.QName(el).localname == "sectPr":
            continue
        txt = "".join(el.itertext()).strip()
        removed.append((etree.QName(el).localname, txt[:60]))
        body.remove(el)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return removed


if __name__ == "__main__":
    rem = prep(sys.argv[1], sys.argv[2])
    kept = [r for r in rem if r[1]]
    print("answer-key section removed from the question copy: %d elements "
          "(%d with text)" % (len(rem), len(kept)))
    for kind, txt in kept:
        print("  - %s: %s" % (kind, txt))
