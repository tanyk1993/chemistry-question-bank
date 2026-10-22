#!/usr/bin/env python3
"""ACJC 2026 H2 P3 (9476/03): make a QUESTION-ONLY copy of the school's
"question paper + suggested solutions" docx, for the table adapter (`parts.py`).

SHAPE: same family as ACJC 2026 H2 P2 and ASRJC 2024 H2 P2/P3 -- the question
paper's own SEAB grid with every answer typed into a following row (blue
0000FF / 0070C0 / 3333FF, red FF0000 "Comments"). Tables 0 and 1 are the cover
and the examiner's-use box; Q1..Q5 are tables 2..6 (a question may span more
than one table; `parts.parse` carries its part cursor across tables).

`inline_answers_prep_parts.prep()` deletes every row that carries coloured
text. This module adds what that rule cannot see, each DECLARED and ASSERTED
(a changed document raises instead of being half-applied):

  FORCE_DELETE   answer rows with no coloured text at all (a picture-only answer)
  DROP_FIG_RUNS  runs holding a drawing, removed from a paragraph that also has
                 question text:
                   (4, 7)  Q3(a)(iv): the paragraph "Use the concepts ... [2]"
                           anchors a floating group (the answer's delta-minus
                           labels; its text-box content is "d-d-d-...").
  INK            Word "Ink" annotations (a teacher's pen marks, `w14:contentPart`)
                 are not question content. Q1(d)(ii) holds exactly ONE (once the answer rows are gone), anchored
                 off the right margin; left in, the parser plans a phantom figure
                 (and a snip the user would be asked to make) for it. Removed,
                 and the count is asserted.
  DROP_PARAS     paragraphs removed from a row that mixes question and answer:
                   (5, 28) Q4's total row: the blue "Total: AOA/AOB" lines go,
                           "[Total: 20]" stays.
                   (6, 18) Q5(d)(ii): the row runs on across a page break; the
                           glycinate question ends at "[2]" (paragraph 11) and
                           everything after it is the answer + comments.

usage: python3 -m ingest.acjc26_p3_prep <unz_dir> <out_unz_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .inline_answers_prep_parts import prep, _txt
from .oxml import NS, Wq

COLOURS = ("0000FF", "0070C0", "3333FF", "FF0000")
SKIP_TABLES = 2

#: (table, row) -> picture-only answer rows (no coloured text)
FORCE_DELETE = {
    (2, 4),    # Q1(b)(i): "S:" + the amine structure
    (2, 22),   # Q1(e)(i): the hand-drawn curly arrows
}

#: (table, row) -> (cell index, first paragraph index to drop, "from" or a tuple of
#: indices, text the FIRST dropped paragraph must start with ("" = no check))
DROP_PARAS = {
    (5, 28): (3, (0, 1, 2), "Total:"),
    (6, 18): (3, tuple(range(12, 33)), ""),
}
#: how many Ink annotations the document is declared to hold (all removed)
INK_EXPECTED = 1
INK_URI = "wordprocessingInk"

#: (table, row) -> (cell index, paragraph index): every run holding a drawing/object
#: in that paragraph is removed (at least one must exist); the text stays
DROP_FIG_RUNS = {
    (4, 7): (3, 4),
}
#: the paragraph that must SURVIVE just before a DROP_PARAS cut (sanity anchor)
KEEP_ANCHOR = {
    (6, 18): (11, "[2]"),
}


def drop_paras(document_xml: Path, out_xml: Path) -> list:
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    log = []
    for (ti, ri), (ci, idxs, startswith) in DROP_PARAS.items():
        tr = tables[ti].findall("w:tr", NS)[ri]
        tc = tr.findall("w:tc", NS)[ci]
        paras = tc.findall("w:p", NS)
        if max(idxs) >= len(paras):
            raise ValueError("DROP_PARAS %s: cell has only %d paragraphs"
                             % ((ti, ri), len(paras)))
        if (ti, ri) in KEEP_ANCHOR:
            ai, atxt = KEEP_ANCHOR[(ti, ri)]
            if _txt(paras[ai]).strip() != atxt:
                raise ValueError("DROP_PARAS %s: anchor paragraph %d is %r, "
                                 "expected %r" % ((ti, ri), ai,
                                                  _txt(paras[ai]).strip(), atxt))
        if startswith and not _txt(paras[idxs[0]]).strip().startswith(startswith):
            raise ValueError("DROP_PARAS %s: first dropped paragraph is %r, "
                             "expected it to start %r"
                             % ((ti, ri), _txt(paras[idxs[0]]).strip()[:30],
                                startswith))
        for i in idxs:
            tc.remove(paras[i])
        log.append("dropped %d paragraph(s) of table %d row %d" % (len(idxs), ti, ri))
    for (ti, ri), (ci, pi) in DROP_FIG_RUNS.items():
        tr = tables[ti].findall("w:tr", NS)[ri]
        p = tr.findall("w:tc", NS)[ci].findall("w:p", NS)[pi]
        runs = [r for r in p.findall("w:r", NS)
                if any(etree.QName(x).localname in ("drawing", "object", "pict")
                       for x in r.iter())]
        if not runs:
            raise ValueError("DROP_FIG_RUNS %s: no drawing run found" % ((ti, ri),))
        for r in runs:
            p.remove(r)
        log.append("dropped %d drawing run(s) of table %d row %d paragraph %d"
                   % (len(runs), ti, ri, pi))
    tree.write(str(out_xml), xml_declaration=True, encoding="UTF-8", standalone=True)
    return log


def drop_ink(document_xml: Path) -> list:
    tree = etree.parse(str(document_xml))
    n = 0
    for dr in list(tree.getroot().iter(Wq + "drawing")):
        gd = next(dr.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}graphicData"), None)
        if gd is None or INK_URI not in (gd.get("uri") or ""):
            continue
        run = dr
        while run is not None and etree.QName(run).localname != "r":
            run = run.getparent()
        run.getparent().remove(run)
        n += 1
    if n != INK_EXPECTED:
        raise ValueError("expected %d Ink annotation(s), found %d" % (INK_EXPECTED, n))
    tree.write(str(document_xml), xml_declaration=True, encoding="UTF-8", standalone=True)
    return ["removed %d Ink annotation(s)" % n]


def run(unz: Path, out: Path):
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(unz, out)
    doc = out / "word" / "document.xml"
    log = drop_paras(unz / "word" / "document.xml", doc)
    log += [str(x) for x in prep(doc, doc, force_delete=FORCE_DELETE,
                                 colours=COLOURS, skip_tables=SKIP_TABLES)]
    # AFTER the answer rows are gone: the answers hold 52 more Ink strokes
    log += drop_ink(doc)
    return log


if __name__ == "__main__":      # pragma: no cover
    for line in run(Path(sys.argv[1]), Path(sys.argv[2])):
        print(line)
