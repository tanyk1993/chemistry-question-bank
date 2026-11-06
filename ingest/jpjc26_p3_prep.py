#!/usr/bin/env python3
"""Prepare JPJC 2026 H2 P3 (9476/03) question paper as a squared-up copy for
`parts.py` (table shape).

SHAPE: same family as JPJC 2026 H2 P2 / JPJC 2024 H2 P2 (irregular per-table
grids; every table has its own `w:gridCol` list, leading blank cells of span
1-4, label cells of different spans). Body-level tables:

    0  cover / instructions / examiner box   (not touched)
    1  Q1 and Q2   (12-column grid)
    2  Q3          (12-column grid)
    3  Q4 and Q5   (17-column grid)           (Section B, answer one)

The docx is QUESTIONS ONLY (no typed answers; the one blue run is the minus
sign of "L-" in 4(f)(i), question text). The row re-emission of `jpjc_p2_prep`
is reused (helpers imported from it): every row is rewritten as
[qnum 1][letter 1][roman 1][content 8][marks 1] from the CONTENT of its cells
and the "For Examiner's Use" cells are dropped. Differences from the P2 script:

  * the examiner cell of Q4(e) reads "For For   For Examiner's Use" (a stray
    paste); any cell whose text starts "For" and ends "Use" and contains
    "Examiner" is dropped;
  * the "BLANK PAGE" rows (table 1 row between Q1(a)(ii) and Q1(b); the trailing
    rows of table 3) are removed;
  * blank cells BETWEEN the content cell and the marks cell are ignored (Q5(e)
    last row: content | blank | [2]);
  * BOLD: the school marks the compound labels (J, L, M, N ... W, X, Y, Z) and
    the table / figure captions bold with `<w:bCs/>` ONLY (no `<w:b/>`), which
    Word prints bold but `oxml._run_style` (reads `w:b` only) drops. Every run
    that has `w:bCs` and no `w:b` gets a `w:b` in the prepped COPY.

It REFUSES (raises) when the question numbers found are not exactly 1..5, when
the table count is not 4, or when a row has more cells than the slots allow, so a
different paper cannot be half-processed silently.

Usage: python3 -m ingest.jpjc26_p3_prep <unz-in> <unz-out>
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .jpjc_p2_prep import (LETTER, MARKS, QNUM, ROMAN, SPANS, _blank,
                           _is_label_with_art, _set_span,
                           _split_label_cell, _text)
from .oxml import NS, Wq

_M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _has_content(tc) -> bool:
    """Text, a picture/object/nested table, or an OMML equation (answers docx: a
    Word-equation-only cell, e.g. 5(c)(i) K_stab, has no w:t at all)."""
    return bool(_text(tc)) or any(
        tc.findall(".//w:" + tag, NS) for tag in ("drawing", "object", "pict", "tbl")
    ) or tc.find(".//{%s}oMath" % _M) is not None


EXPECT_TABLES = 4                      # cover + 3 question tables
EXPECT_QS = [1, 2, 3, 4, 5]
EXAMINER_RE = re.compile(r"^For\b.*Examiner.s Use$", re.S)
AO_RE = re.compile(r"^(?:AO[AB]?\s*(?:\(?\d\)?)?\s*)+$")      # answers docx: assessment-objective tag cells


def _is_examiner(tc) -> bool:
    t = " ".join(_text(tc).split())
    return bool(EXAMINER_RE.match(t) or AO_RE.match(t))


def prep(unz_in: Path, unz_out: Path, keep_answers: bool = False) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)
    n_exp = 6 if keep_answers else EXPECT_TABLES     # answers docx: cover + one table per Q
    if len(tbls) != n_exp:
        raise SystemExit("expected %d body tables, got %d" % (n_exp, len(tbls)))
    log = []

    # ---- 0. complex-script bold -> bold --------------------------------
    n_bcs = 0
    for r in body.iter(Wq + "r"):
        pr = r.find(Wq + "rPr")
        if pr is None:
            continue
        bcs = pr.find(Wq + "bCs")
        if bcs is None or bcs.get(Wq + "val") in ("0", "false"):
            continue
        if pr.find(Wq + "b") is None:
            b = etree.Element(Wq + "b")
            bcs.addprevious(b)
            n_bcs += 1
    log.append("bCs-only runs given w:b: %d" % n_bcs)

    # ---- 1. drop the BLANK PAGE rows -------------------------------------
    n_blank = 0
    for tbl in tbls[1:]:
        for tr in list(tbl.findall("w:tr", NS)):
            if "BLANK PAGE" in "".join(tr.itertext(Wq + "t")):
                tbl.remove(tr)
                n_blank += 1
    if n_blank != (0 if keep_answers else 2):
        raise SystemExit("unexpected BLANK PAGE row count %d" % n_blank)

    # ---- 2. square the grid ----------------------------------------------
    n_exam = n_moved = 0
    seen_q = []
    rows = [(t, tr) for t in tbls[1:] for tr in t.findall("w:tr", NS)]
    for _t, tr in rows:
        cells = tr.findall("w:tc", NS)
        keep = []
        for tc in cells:
            if _is_examiner(tc):
                n_exam += 1
                continue
            keep.append(tc)
        cells = keep
        while cells and not _has_content(cells[-1]):
            cells.pop()
        q = L = R = None
        i = 0
        stray = None
        # answers docx: a floating graph/table can be anchored in the leading blank cell
        if (len(cells) > 2 and _has_content(cells[0]) and not QNUM.match(_text(cells[0]))
                and not LETTER.match(_text(cells[0])) and not ROMAN.match(_text(cells[0]))):
            stray = cells.pop(0)
            cells.insert(0, _blank(1))
        if cells:
            if QNUM.match(_text(cells[0])):
                q = cells[0]
                seen_q.append(int(_text(cells[0])))
                i = 1
            elif not _has_content(cells[0]):
                i = 1
        if i < len(cells):
            t = _text(cells[i])
            if LETTER.match(t) or ROMAN.match(t) and (
                    i + 1 < len(cells) and ROMAN.match(_text(cells[i + 1]))):
                L = cells[i]
                i += 1
            elif not _has_content(cells[i]):
                i += 1
            elif _is_label_with_art(cells[i]):
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
        if i < len(cells):
            t = _text(cells[i])
            if ROMAN.match(t):
                R = cells[i]
                i += 1
            elif not _has_content(cells[i]) and i + 1 < len(cells):
                i += 1
        rest = cells[i:]
        for tc in rest:
            if ROMAN.match(_text(tc)) or LETTER.match(_text(tc)):
                raise SystemExit("unplaced label cell %r" % _text(tc))
        # blank spacer cells between content and marks are layout only
        rest = [tc for tc in rest if _has_content(tc)]
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
        if stray is not None:
            if content is None:
                content = stray
            else:
                first = content.find("w:p", NS)
                for k, p_ in enumerate(stray.findall("w:p", NS)):
                    content.insert(list(content).index(first) + k, p_)
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
    log.append("BLANK PAGE rows removed: %d" % n_blank)
    log.append("question tables: %d rows re-emitted as [1,1,1,8,1]; %d examiner "
               "cells dropped; %d art paragraph(s) moved out of a label cell"
               % (len(rows), n_exam, n_moved))
    if seen_q != EXPECT_QS:
        raise SystemExit("question numbers found %r, expected %r"
                         % (seen_q, EXPECT_QS))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2], keep_answers="--keep-answers" in sys.argv):
        print(line)
