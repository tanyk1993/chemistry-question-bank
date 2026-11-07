"""Prepare MI 2026 H2 P1 (table-shape MCQ) for `questions.py`.

SHAPE (first seen: MI 2026 H2 P1, 2026-11-07). One Word table per question,
rows `[number | stem (gridSpan)]`, then option rows `[blank | A | text]`
(or a column-header row for the 'row compares' questions) -- the usual table
family. The ONE difference: the question number is not typed. Cell 0 of row 0
holds a Word auto-number field (` AUTONUMLGL  \\e `) with an EMPTY cached result,
so `questions.py` (which reads a bare 1-2 digit number from cell 0 of row 0)
sees no number and `parse_dispatch` calls the paper 'flow'.

WHAT THIS DOES, on a COPY of the unzipped docx (the original is never touched):
write the number into every such cell, counting in document order (that is
what AUTONUMLGL does: a plain running count, 1, 2, 3 ...). It REFUSES (raises)
unless exactly 30 fields are found, all in cell 0 of row 0 of a body-level
table, so a missed or extra field cannot slip through. The printed PDF is
the independent check on the numbering (see the verification step).

Usage: python3 -m ingest.mi26_p1_prep <src_unz_dir> <dst_unz_dir>
"""
from __future__ import annotations

import copy
import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
EXPECTED = 30


def prepare(src_unz, dst_unz):
    src_unz, dst_unz = Path(src_unz), Path(dst_unz)
    if dst_unz.exists():
        shutil.rmtree(dst_unz)
    shutil.copytree(src_unz, dst_unz)
    doc = dst_unz / "word" / "document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)

    all_fields = [it for it in tree.getroot().iter(W + "instrText")
                  if "AUTONUMLGL" in (it.text or "")]
    report, n = [], 0
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if not rows:
            continue
        tcs = rows[0].findall("w:tc", NS)
        if not tcs:
            continue
        cell0 = tcs[0]
        fields = [it for it in cell0.iter(W + "instrText")
                  if "AUTONUMLGL" in (it.text or "")]
        if not fields:
            continue
        if len(fields) != 1:
            raise RuntimeError("table has %d AUTONUMLGL fields in cell 0" % len(fields))
        n += 1
        p = cell0.find("w:p", NS)
        # the field's end marker is the last run of the field; put the number after it
        run = etree.SubElement(p, W + "r")
        rpr = etree.SubElement(run, W + "rPr")
        etree.SubElement(rpr, W + "b")
        t = etree.SubElement(run, W + "t")
        t.text = str(n)
    if n != EXPECTED or len(all_fields) != EXPECTED:
        raise RuntimeError("AUTONUMLGL fields: %d in question cells, %d in document, expected %d"
                           % (n, len(all_fields), EXPECTED))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    report.append("OK: wrote auto-numbers 1..%d into the question cells" % n)
    return report


if __name__ == "__main__":          # pragma: no cover
    for line in prepare(sys.argv[1], sys.argv[2]):
        print(line)
