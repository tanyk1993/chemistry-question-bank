"""Prepare a STRUCTURED (P2/P3) "question paper + suggested solutions in the SAME
document" docx for the question-side adapter (`parts.py`).

SHAPE (first seen: ASRJC 2024 H2 P2, 2026-10-03). Same family as ACJC 2024 H2
P2 (`extract_acjc_p2_answers.py`): the school's file is the question paper's own
4-column SEAB grid with each part's answer typed into a following row, in
BLUE (0000CC here; ACJC uses 0000FF) with FF0000 red mark ticks ("[1]", "[1]
for ..."). Nothing marks an answer row except that colour, and an answer that is
only a picture (a ChemDraw structure, a drawn graph) has NO colour at all.

This is the QUESTIONS-STAGE counterpart of ACJC's `mark_zones()`: instead of
marking answer zones to extract them, it REMOVES them from a copy of
document.xml so `parts.parse` sees question text and nothing else (the task at
this stage is questions only -- answers must not leak into `content_html` /
`content_text`, and answer glyphs would otherwise trip `symbols.sym_to_text`).

RULES, in order, per table row (the original document.xml is never touched):

  * FORCE_KEEP_STRIP  keep the row, delete only its coloured runs. Used where
                      the QUESTION's own figure is anchored in the same row as
                      the answer (ASRJC Q2(d)(ii): the blank pH axes of Fig 2.1
                      live in the row that carries the red mark ticks).
  * FORCE_BLANK_FIGS  keep the row, delete its drawings/objects. Used where the
                      answer is a picture drawn into a box the question prints
                      EMPTY (ASRJC Q2(b)(ii): the U and V structures).
  * FORCE_DELETE      delete the row although it has no coloured text (an
                      answer that is only a picture, or a table whose headers
                      are black and whose values are blue).
  * otherwise         delete the row if ANY run in ANY of its cells is coloured
                      with an answer colour AND carries visible text. Checking
                      every cell, not just the last, matters: ASRJC Q2(a)'s
                      one-word answer sits in the roman-numeral cell.

It reports every decision, and REFUSES (raises) if a FORCE entry names a row
that does not exist or does not look the way the entry says -- a silent miss in
either direction would put an answer into a question or delete a question's
own text.
"""
from __future__ import annotations

import copy
import re

from lxml import etree

from .oxml import NS, Wq

ANSWER_COLOURS = ("0000CC", "FF0000")
FIG_TAGS = ("drawing", "object", "pict")


def _txt(el) -> str:
    return "".join(el.itertext(Wq + "t"))


def _run_colour(r) -> str:
    c = r.find("w:rPr/w:color", NS)
    return (c.get(Wq + "val") or "").upper() if c is not None else ""


def _coloured_runs(el, colours):
    return [r for r in el.iter(Wq + "r")
            if _run_colour(r) in colours and _txt(r).strip()]


def _figs(el):
    return [x for x in el.iter() if etree.QName(x).localname in FIG_TAGS]


def prep(src_document_xml, dst_document_xml, *, force_delete=(), insert_labels=None,
         force_keep_strip=(), force_blank_figs=(), colours=ANSWER_COLOURS,
         skip_tables=2):
    """Write the question-only copy; return a per-row decision log.

    `skip_tables`: leading tables that are the cover / examiner's-use boxes.
    ASRJC's has ONE cover table and starts Q1 in table 1 -- but its cover table
    is table 0 only; callers pass what the document needs.
    """
    force_delete, force_keep_strip = set(force_delete), set(force_keep_strip)
    force_blank_figs = set(force_blank_figs)
    insert_labels = dict(insert_labels or {})
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    log, seen = [], set()
    # INSERT_LABELS: {(table, row): "(ii)"} -- the source omits a part's roman
    # label (ASRJC Q4(c)(ii): only "[2]" and two bullets survive in the file,
    # and the PDF has no label either). The label is written into the row's
    # roman-numeral cell (3rd cell) so the parser opens the part. No question
    # TEXT is invented.
    for (ti, ri), lab in insert_labels.items():
        tr = tables[ti].findall("w:tr", NS)[ri]
        tc = tr.findall("w:tc", NS)[2]
        para = tc.find("w:p", NS)
        r = etree.SubElement(para, Wq + "r")
        etree.SubElement(r, Wq + "t").text = lab
        log.append((ti, ri, "insert-label " + lab, _txt(tr).strip()[:50]))
    for ti, tbl in enumerate(tables):
        if ti < skip_tables:
            continue
        for ri, tr in enumerate(list(tbl.findall("w:tr", NS))):
            key = (ti, ri)
            coloured = _coloured_runs(tr, colours)
            text = _txt(tr).strip()[:50]
            if key in force_keep_strip:
                seen.add(key)
                if not _figs(tr):
                    raise ValueError("FORCE_KEEP_STRIP %s holds no figure" % (key,))
                for r in coloured:
                    r.getparent().remove(r)
                log.append((ti, ri, "strip-coloured-keep-figs", text))
            elif key in force_blank_figs:
                seen.add(key)
                figs = _figs(tr)
                if not figs:
                    raise ValueError("FORCE_BLANK_FIGS %s holds no figure" % (key,))
                for f in figs:
                    # the whole run holding the drawing/object, not just the child
                    run = f
                    while run is not None and etree.QName(run).localname != "r":
                        run = run.getparent()
                    if run is not None and run.getparent() is not None:
                        run.getparent().remove(run)
                log.append((ti, ri, "blank-figs", text))
            elif key in force_delete:
                seen.add(key)
                if coloured:
                    raise ValueError("FORCE_DELETE %s has coloured text; it "
                                     "needs no force" % (key,))
                tbl.remove(tr)
                log.append((ti, ri, "delete(forced, no colour)", text))
            elif coloured:
                tbl.remove(tr)
                log.append((ti, ri, "delete(coloured)", text))
    missing = (force_delete | force_keep_strip | force_blank_figs) - seen
    if missing:
        raise ValueError("FORCE entries name rows that were never visited: %s"
                         % sorted(missing))
    # LAST, once row indices no longer matter: one table per question.
    for tbl in tables[skip_tables:]:
        log.extend(_split_questions(body, tbl))
    tree.write(str(dst_document_xml), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")


def _split_questions(body, tbl):
    """Split a table that holds MORE THAN ONE question into one table per
    question. `parts._regimes` groups rows by TOTAL cell width only, so two
    questions whose grids have the same total but different column boundaries
    (ASRJC Q3 = 1+1+2+4 and Q4 = 1+2+2+3, both 8, one Word table) end up in one
    regime and the roman-numeral slot is misread for the second. `parts.parse`
    carries its part cursor across table boundaries, so splitting is safe."""
    rows = tbl.findall("w:tr", NS)
    starts = []
    for i, r in enumerate(rows):
        tcs = r.findall("w:tc", NS)
        if tcs and _QNUM.match(_txt(tcs[0])):
            starts.append(i)
    if len(starts) < 2:
        return []
    groups = [rows[s:e] for s, e in zip(starts, starts[1:] + [len(rows)])]
    qs = [_QNUM.match(_txt(g[0].findall("w:tc", NS)[0])).group(1) for g in groups]
    prev = tbl
    for g in groups[1:]:
        new = etree.Element(Wq + "tbl")
        for child in tbl:
            if child.tag in (Wq + "tblPr", Wq + "tblGrid"):
                new.append(copy.deepcopy(child))
        for r in g:
            new.append(r)                      # moves the row
        prev.addnext(new)
        prev = new
    return [("split", "one table split into questions %s" % qs)]
