#!/usr/bin/env python3
"""DHS 2026 H2 P3 (9476/03): QUESTION-ONLY copy of the school's "question paper +
suggested solutions" docx, for the table adapter (`parts.py`).

SHAPE: same family as ACJC / ASRJC 2026 P3 -- the paper's own 4-column SEAB grid
with each answer typed into a following row (blue 0000FF, a lighter blue 3333FF
for a few worked lines, red FF0000 mark notes). Tables 0..3 are the cover, the
examiner's-use box, the cover details and the instructions; the questions start
at table 4 (Q1 = tables 4-6, Q2 = 6-7, Q3 = 8, Q4 = 9, Q5 = 10). A question may
span more than one table; `parts.parse` carries its part cursor across tables.

`inline_answers_prep_parts.prep()` deletes every row that carries coloured text.
This module adds what that rule cannot see, each DECLARED and ASSERTED (a changed
document raises instead of being half-applied):

  KEEP_ROWS      rows whose QUESTION text carries a stray school-coloured run, so
                 the colour rule would delete real question text. The runs are
                 recoloured black first:
                   (9, 34)  Q4(c)(ii): the minus sign of HSO4- is blue.
                   (10, 0)  Q5(a) stem: the italic l of NOCl is blue.
  FORCE_DELETE   picture-only ANSWER rows (no coloured text at all):
                   (5, 6)   Q1(b)(i)   the drawn imide product
                   (6, 18)  Q1(d)(ii)  the drawn PVC
                   (6, 37)  Q1(e)(iii) the first-order graph (a PNG)
                   (6, 66)  Q2(b)(ii)  the three-step mechanism
                   (7, 7)   Q2(b)(iv) the two products
                   (7, 24)  Q2(c)(iii) the pH-volume curve
                   (10, 15) Q5(b)     the three-step synthetic route
                   (10, 41) Q5(d)(ii) the electrochemical cell

usage: python3 -m ingest.dhs26_p3_prep <unz_dir> <out_unz_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .inline_answers_prep_parts import prep, _txt, _coloured_runs
from .oxml import NS, Wq

COLOURS = ("0000FF", "3333FF", "FF0000")
SKIP_TABLES = 4

#: (table, row) -> text the row must contain (asserted), question text with a
#: stray coloured run
KEEP_ROWS = {
    (9, 34): "In the nitration of arenes",
    (10, 0): "Nitrosyl chloride",
}

#: (table, row) -> picture-only answer rows (no coloured text)
FORCE_DELETE = {
    (5, 6), (6, 18), (6, 37), (6, 66), (7, 7), (7, 24), (10, 15), (10, 41),
}


def run(unz: Path, out: Path):
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(unz, out)
    doc = out / "word" / "document.xml"

    # 1. recolour the stray coloured runs in KEEP_ROWS (asserted)
    tree = etree.parse(str(doc))
    tables = tree.getroot().find("w:body", NS).findall("w:tbl", NS)
    log = []
    for (ti, ri), must in KEEP_ROWS.items():
        tr = tables[ti].findall("w:tr", NS)[ri]
        if must not in _txt(tr):
            raise ValueError("KEEP_ROWS %s does not contain %r" % ((ti, ri), must))
        runs = _coloured_runs(tr, COLOURS)
        if not runs:
            raise ValueError("KEEP_ROWS %s has no coloured run to neutralise" % ((ti, ri),))
        for r in runs:
            r.find("w:rPr/w:color", NS).set(Wq + "val", "000000")
        log.append("keep %s: %d coloured run(s) recoloured black (%s)"
                   % ((ti, ri), len(runs), "".join(_txt(r) for r in runs)[:20]))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)

    # 2. strip the answer rows
    log += [str(x) for x in prep(doc, doc, force_delete=FORCE_DELETE,
                                 colours=COLOURS, skip_tables=SKIP_TABLES)]
    return log


if __name__ == "__main__":      # pragma: no cover
    for line in run(Path(sys.argv[1]), Path(sys.argv[2])):
        print(line)
