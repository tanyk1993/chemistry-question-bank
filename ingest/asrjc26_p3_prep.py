#!/usr/bin/env python3
"""ASRJC 2026 H2 P3 (9476/03): QUESTION-ONLY copy of the school's "question paper +
suggested solutions" docx, for the table adapter (`parts.py`).

SHAPE: same family as ASRJC 2026 H2 P2 -- the paper's own 4-column grid with each
answer typed into a following row (blue 0000CC; one answer 0000FF; red FF0000 mark
notes). Table 0 = cover, 1 = examiner's-use box, 2..7 = Q1, Q2, Q3, Q4 (tables 5+6:
the Q4(d)(ii) answer graph pushes the rest of Q4 into a second table), Q5 = table 7.

FORCE_DELETE (answer rows with no coloured text at all, a picture-only answer):
  (5, 35)  Q4(c): the drawn structures of L, M, N and P.

usage: python3 -m ingest.asrjc26_p3_prep <unz_dir> <out_unz_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .inline_answers_prep_parts import prep

COLOURS = ("0000CC", "0000FF", "FF0000")
SKIP_TABLES = 2
FORCE_DELETE = {(5, 35)}


def run(unz: Path, out: Path):
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(unz, out)
    doc = out / "word" / "document.xml"
    return [str(x) for x in prep(doc, doc, force_delete=FORCE_DELETE,
                                 colours=COLOURS, skip_tables=SKIP_TABLES)]


if __name__ == "__main__":      # pragma: no cover
    for line in run(Path(sys.argv[1]), Path(sys.argv[2])):
        print(line)
