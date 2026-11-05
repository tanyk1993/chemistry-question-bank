#!/usr/bin/env python3
"""Prepare JPJC 2026 H2 P2 (9476/02) -- the school's "questions + suggested answers"
docx -- as a QUESTION-ONLY, squared-up copy for `parts.py` (table shape).

SHAPE: the paper is body-level tables 0 = cover/instructions/examiner box, then
    1  Q1 and Q2   (13-column grid)
    2  Q3          (12-column grid)
    3  Q4          ( 7-column grid)
    4  Q5 and Q6   (12-column grid)
Every table has its own irregular grid (a `w:gridBefore`, leading blank cells of
span 1-3, label cells of different spans), exactly like JPJC 2024 H2 P2, so the
row re-emission of `jpjc_p2_prep` is reused (helpers imported from it): every
row is rewritten as [qnum 1][letter 1][roman 1][content 8][marks 1] from the
CONTENT of its cells, and the "For Examiner's Use" cells are dropped.

ANSWERS are typed into the same tables as extra rows in blue (0000FF; also
3333FF, 0033CC) with red (FF0000 / EE0000) mark ticks. Nothing marks an answer
row except the colour, and a picture-only answer has no colour at all. This
script REMOVES them (the task at this stage is the questions only), the same job
`inline_answers_prep_parts.prep` does for ASRJC/DHS, plus:

  FORCE_KEEP        rows with blue runs that are QUESTION text: 4(d) types the
                    minus sign of "SCN-" in blue, so rows (3, 12) and (3, 13)
                    would otherwise be deleted as answers.
  STRIP_CELL_ANS    cells that hold the question AND the start of its answer:
                    (1, 20, 3) = Q2(a)(i). The coloured paragraphs are removed,
                    the question paragraphs stay.
  FORCE_DELETE      answer rows with no coloured text at all (a pasted picture):
                    (1, 31) = the drawn monomers of 2(b)(ii); (2, 23), (2, 24) = the SF6 / CO2(600 K) answer graph of
                    3(e)(i); (4, 4) = the drawn structure of compound B, 5(a)(ii).
  OVERLAY           Fig 2.1 (Q2 intro cell) carries the school's ANSWER overlay:
                    five 'line' shapes (the red tangent and the blue dashed
                    half-life construction lines), the text boxes t1/2 (1),
                    t1/2 (2), (14.5, 0), (0, 1.50 x 10-2), and two stray text
                    boxes "0" and "5.0" printed over the 0.50 tick. They are
                    removed so the question carries the bare graph.

It REFUSES (raises) when a declared row is not what the entry says, when the
question numbers found are not exactly 1..6, or when any per-table count is off,
so a different paper cannot be half-processed silently.

Usage: python3 -m ingest.jpjc26_p2_prep <unz-in> <unz-out>
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .jpjc_p2_prep import (EXAMINER, LETTER, MARKS, QNUM, ROMAN, SPANS, _blank,
                           _has_content, _is_label_with_art, _own_text,
                           _set_span, _split_label_cell, _text)
from .oxml import NS, Wq

ANS_COLOURS = {"0000FF", "3333FF", "0033CC", "FF0000", "EE0000"}
FORCE_KEEP = {(3, 12), (3, 13)}
STRIP_CELL_ANS = {(1, 20, 3)}
FORCE_DELETE = {(1, 31), (2, 23), (2, 24), (4, 4)}
#: (table, row, cell): answer overlay on Fig 2.1
OVERLAY = (1, 19, 2)
OVERLAY_TEXT = {"0", "5.0", "t½ (1) = 10.25", "t½ (2) = 10.25",
                "(14.5, 0)", "(0, 1.50 x 10–2)"}
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _run_colour(r) -> str:
    c = r.find("w:rPr/w:color", NS)
    return (c.get(Wq + "val") or "").upper() if c is not None else ""


def _coloured(el):
    """answer-coloured runs with visible text, outside text boxes"""
    out = []
    for r in el.iter(Wq + "r"):
        if any(a.tag == Wq + "txbxContent" for a in r.iterancestors()):
            continue                    # text boxes belong to a figure
        if _run_colour(r) in ANS_COLOURS and any(
                (t.text or "").strip() for t in r.findall("w:t", NS)):
            out.append(r)
    return out


def _para_is_answer(p) -> bool:
    runs = [r for r in p.findall("w:r", NS)
            if any((t.text or "").strip() for t in r.findall("w:t", NS))]
    return bool(runs) and all(_run_colour(r) in ANS_COLOURS for r in runs)


def _txbx_text(r) -> str:
    return "".join(t.text or "" for t in r.iter(Wq + "t")
                   if any(a.tag == Wq + "txbxContent" for a in t.iterancestors())
                   and not any(a.tag == "{%s}Fallback" % MC
                               for a in t.iterancestors())).strip()


def _strip_overlay(tc) -> int:
    """remove the answer overlay anchors from the Fig 2.1 cell; return count"""
    n_line = n_box = 0
    for r in list(tc.iter(Wq + "r")):
        if not any(etree.QName(x).localname in ("AlternateContent", "drawing")
                   for x in r):
            continue
        prsts = {g.get("prst") for g in r.iter("{%s}prstGeom" % A_NS)}
        txt = _txbx_text(r)
        if txt in OVERLAY_TEXT:
            r.getparent().remove(r)
            n_box += 1
        elif prsts == {"line"}:
            r.getparent().remove(r)
            n_line += 1
    if (n_line, n_box) != (5, 6):
        raise SystemExit("Fig 2.1 overlay: removed %d lines / %d boxes, "
                         "expected 5 / 6" % (n_line, n_box))
    return n_line + n_box


def prep(unz_in: Path, unz_out: Path, keep_answers: bool = False) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)
    if len(tbls) != 5:
        raise SystemExit("expected 5 body tables (cover + 4 question), got %d"
                         % len(tbls))
    log = []

    # ---- 1. remove the answers (skipped with keep_answers: the answers stage
    # reads the SAME squared grid with the blue rows left in place) ----
    if not keep_answers:
        seen = set()
        n_del = n_forced = 0
        for ti in range(1, 5):
            tbl = tbls[ti]
            for ri, tr in enumerate(list(tbl.findall("w:tr", NS))):
                key = (ti, ri)
                if key in FORCE_KEEP:
                    seen.add(key)
                    if not _coloured(tr):
                        raise SystemExit("FORCE_KEEP %s has no coloured text" % (key,))
                    continue
                if key in FORCE_DELETE:
                    seen.add(key)
                    if _coloured(tr):
                        raise SystemExit("FORCE_DELETE %s has coloured text" % (key,))
                    if not tr.findall(".//w:drawing", NS) + tr.findall(".//w:object", NS):
                        raise SystemExit("FORCE_DELETE %s holds no picture" % (key,))
                    tbl.remove(tr)
                    n_forced += 1
                    continue
                for ci, tc in enumerate(tr.findall("w:tc", NS)):
                    if (ti, ri, ci) in STRIP_CELL_ANS:
                        seen.add((ti, ri, ci))
                        ps = [p for p in tc.findall("w:p", NS) if _para_is_answer(p)]
                        if not ps:
                            raise SystemExit("STRIP_CELL_ANS %s: no answer paragraph"
                                             % ((ti, ri, ci),))
                        for p in ps:
                            tc.remove(p)
                        log.append("cell %s: removed %d answer paragraph(s)"
                                   % ((ti, ri, ci), len(ps)))
                if _coloured(tr):
                    tbl.remove(tr)
                    n_del += 1
        missing = (FORCE_KEEP | FORCE_DELETE | STRIP_CELL_ANS) - seen
        if missing:
            raise SystemExit("FORCE entries never visited: %s" % sorted(missing))
        ti, ri, ci = OVERLAY
        # row indices of table 1 shifted after deletions: find the Q2 intro row by
        # its question number instead
        for tr in tbls[ti].findall("w:tr", NS):
            cs = tr.findall("w:tc", NS)
            if cs and _text(cs[0]) == "2":
                n_ov = _strip_overlay(cs[ci])
                break
        else:
            raise SystemExit("Q2 intro row not found")
        log.append("answers removed: %d coloured rows + %d picture-only rows; "
                   "Fig 2.1 answer overlay: %d shapes removed" % (n_del, n_forced, n_ov))

    # ---- 2. square the grid ---------------------------------------------
    n_exam = n_moved = 0
    seen_q = []
    rows = [(t, tr) for t in tbls[1:] for tr in t.findall("w:tr", NS)]
    for _t, tr in rows:
        cells = tr.findall("w:tc", NS)
        keep = []
        for tc in cells:
            if _text(tc) == EXAMINER:
                n_exam += 1
                continue
            keep.append(tc)
        cells = keep
        while cells and not _has_content(cells[-1]):
            cells.pop()
        q = L = R = None
        i = 0
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
    log.append("question tables: %d rows re-emitted as [1,1,1,8,1]; %d examiner "
               "cells dropped; %d art paragraph(s) moved out of a label cell"
               % (len(rows), n_exam, n_moved))
    if seen_q != [1, 2, 3, 4, 5, 6]:
        raise SystemExit("question numbers found %r, expected 1..6" % seen_q)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


if __name__ == "__main__":
    for line in prep(sys.argv[1], sys.argv[2], keep_answers="--keep-answers" in sys.argv):
        print(line)
