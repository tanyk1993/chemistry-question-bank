#!/usr/bin/env python3
"""Square up JPJC 2024 H2 P2's question table so `parts.py` (table shape) applies.

SHAPE: the whole paper (Q1-Q6) is ONE body-level table (the second table; the
first is the NAME/CLASS cover block) with an irregular grid: every row carries a
`w:gridBefore`, a leading blank cell of span 1-3, and the label cells have
different spans from question to question, so `parts._classify` (cumulative
gridSpan against fixed slot widths) cannot place the slots. The cells of one row
are, in order:

    [lead: question number or blank] [letter] [roman] [content] [marks]
    [blank] ["For Examiner's Use" on some rows]

but ANY of them can be missing (a part with no roman has no roman cell; a
question-start row has no letter), and a blank cell can be the roman slot OR an
empty content cell. This script re-emits every row of that table with exactly

    [qnum 1][letter 1][roman 1][content 8][marks 1]

(spans 1,1,1,8,1, one regime), reusing the original `w:tc` elements so nothing in
a cell (nested tables, drawings, OMML) is touched. The "For Examiner's Use"
column cell is dropped.

Special case, row of Q6(b): the `(b)` label paragraph shares its cell with the
text boxes (axis numbers and axis titles) of the van Arkel chart. The label
paragraph stays in the letter slot; the chart's paragraphs move into the content
cell, in front of the content cell's own first drawing, so they sit with the
rest of the chart.

Worked on a COPY of the unzipped docx; nothing else is touched.

Usage: python3 -m ingest.jpjc_p2_prep <unz-in> <unz-out>
Raises on anything that is not the declared shape, so another paper cannot be
half-processed silently.
"""
from __future__ import annotations

import copy
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS, Wq

QNUM = re.compile(r"^\s*\d{1,2}\s*$")
LETTER = re.compile(r"^\s*\([a-z]\)\s*$")
ROMAN = re.compile(r"^\s*\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\)\s*$")
MARKS = re.compile(r"^\s*\[\d+\]\s*$")
EXAMINER = "For Examiner’s Use"

#: spans of the canonical row
SPANS = (1, 1, 1, 8, 1)


def _text(tc) -> str:
    return "".join(tc.itertext(Wq + "t")).strip()


def _has_content(tc) -> bool:
    return bool(_text(tc)) or any(
        tc.findall(".//w:" + tag, NS)
        for tag in ("drawing", "object", "pict", "tbl"))


def _set_span(tc, n):
    pr = tc.find("w:tcPr", NS)
    if pr is None:
        pr = etree.SubElement(tc, Wq + "tcPr")
        tc.insert(0, pr)
    g = pr.find("w:gridSpan", NS)
    if n == 1:
        if g is not None:
            pr.remove(g)
        return
    if g is None:
        g = etree.Element(Wq + "gridSpan")
        # gridSpan must follow tcW if present
        w = pr.find("w:tcW", NS)
        pr.insert(1 if w is not None else 0, g)
    g.set(Wq + "val", str(n))


def _blank(n):
    tc = etree.Element(Wq + "tc")
    pr = etree.SubElement(tc, Wq + "tcPr")
    if n != 1:
        g = etree.SubElement(pr, Wq + "gridSpan")
        g.set(Wq + "val", str(n))
    etree.SubElement(tc, Wq + "p")
    return tc


def _own_text(p) -> str:
    """Paragraph text excluding anything inside a text box."""
    return "".join(
        x.text or "" for x in p.iter(Wq + "t")
        if not any(a.tag == Wq + "txbxContent" for a in x.iterancestors())
    ).strip()


def _is_label_with_art(tc) -> bool:
    ps = tc.findall("w:p", NS)
    return (len(ps) == 1 and LETTER.match(_own_text(ps[0]))
            and bool(ps[0].findall(".//w:drawing", NS)))


def _split_label_cell(tc):
    """Q6(b): the label paragraph carries the chart's text boxes (anchored
    drawings) in its own runs. Take every run that holds a drawing out of it
    and return them as ONE new paragraph; the label paragraph keeps only the
    label text."""
    (p,) = tc.findall("w:p", NS)
    art = [r for r in p.findall("w:r", NS) if r.findall(".//w:drawing", NS)]
    if not art:
        raise SystemExit("label paragraph has no drawing runs to move")
    newp = etree.Element(Wq + "p")
    for r in art:
        p.remove(r)
        newp.append(r)
    if p.findall(".//w:drawing", NS):
        raise SystemExit("label paragraph still holds drawings")
    return tc, [newp]


def prep(unz_in: Path, unz_out: Path, multi: bool = False) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)
    if not multi and len(tbls) != 2:
        raise SystemExit("expected cover table + ONE question table, got %d tables"
                         % len(tbls))
    if multi and len(tbls) < 3:
        raise SystemExit("multi: expected cover table + several question tables")
    # multi=True is the ANSWERS docx: the same paper, with its question table
    # broken into one table per page-run (every table after the cover is squared up)
    qtbls = tbls[1:] if multi else [tbls[1]]
    log = []
    n_exam = n_moved = 0
    seen_q = []
    rows = [(tbl, tr) for tbl in qtbls for tr in tbl.findall("w:tr", NS)]
    for _tbl, tr in rows:
        cells = tr.findall("w:tc", NS)
        # --- drop the examiner column cell ------------------------------
        keep = []
        for tc in cells:
            if _text(tc) == EXAMINER:
                n_exam += 1
                continue
            keep.append(tc)
        cells = keep
        # trailing cells with nothing in them are layout, not content
        while cells and not _has_content(cells[-1]):
            cells.pop()
        q = L = R = None
        i = 0
        # lead slot
        if cells:
            if QNUM.match(_text(cells[0])):
                q = cells[0]
                seen_q.append(int(_text(cells[0])))
                i = 1
            elif not _has_content(cells[0]):
                i = 1
        # letter slot
        if i < len(cells):
            t = _text(cells[i])
            if LETTER.match(t) or ROMAN.match(t) and (
                    i + 1 < len(cells) and ROMAN.match(_text(cells[i + 1]))):
                L = cells[i]
                i += 1
            elif (not _has_content(cells[i])):
                i += 1
            elif _is_label_with_art(cells[i]):
                # Q6(b): label + chart text boxes in one cell
                L, others = _split_label_cell(cells[i])
                content_tc = cells[i + 1]
                first = next((p for p in content_tc.findall("w:p", NS)
                              if p.findall(".//w:drawing", NS)), None)
                at = (list(content_tc).index(first) if first is not None
                      else len(content_tc))
                for k, p in enumerate(others):
                    content_tc.insert(at + k, p)
                n_moved += len(others)
                i += 1
        # roman slot
        if i < len(cells):
            t = _text(cells[i])
            if ROMAN.match(t):
                R = cells[i]
                i += 1
            elif not _has_content(cells[i]) and i + 1 < len(cells):
                i += 1                      # a blank roman slot
        rest = cells[i:]
        # a roman text cell must not be left in `rest`
        for tc in rest:
            if ROMAN.match(_text(tc)) or LETTER.match(_text(tc)):
                raise SystemExit("unplaced label cell %r" % _text(tc))
        if len(rest) > 2:
            raise SystemExit("row has %d cells after the slots: %r"
                             % (len(rest), [_text(c)[:20] for c in rest]))
        if len(rest) == 0:
            content, marks = None, None
        elif len(rest) == 1:
            if MARKS.match(_text(rest[0])):
                content, marks = None, rest[0]
            else:
                content, marks = rest[0], None
        else:
            content, marks = rest
        # --- re-emit -----------------------------------------------------
        for tc in tr.findall("w:tc", NS):
            tr.remove(tc)
        trpr = tr.find("w:trPr", NS)
        if trpr is not None:
            for g in trpr.findall("w:gridBefore", NS):
                trpr.remove(g)
        for tc, n in zip((q, L, R, content, marks), SPANS):
            if tc is None:
                tc = _blank(n)
            else:
                _set_span(tc, n)
            tr.append(tc)
    log.append("question table: %d rows re-emitted as [1,1,1,8,1]; %d examiner "
               "cells dropped; %d chart-art paragraph(s) moved (Q6(b))"
               % (len(rows), n_exam, n_moved))
    if seen_q != [1, 2, 3, 4, 5, 6]:
        raise SystemExit("question numbers found %r, expected 1..6" % seen_q)
    if n_moved != (1 if not multi else n_moved) or (not multi and n_moved != 1):
        raise SystemExit("expected ONE chart paragraph moved (Q6(b)), got %d"
                         % n_moved)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2], multi="--multi" in sys.argv[3:]):
        print(line)
