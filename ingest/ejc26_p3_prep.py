"""EJC 2026 H2 P3 (9476/03, structured, paragraph-flow): QUESTION-ONLY copy of the
school's "question paper + suggested solutions" docx, for `parts_flow.py`.

SHAPE: the paper's own flow paragraphs (the EJC 2026 P2 shape) with every answer
typed into a floating text box (an `mc:AlternateContent` anchor, 56 of them, blue
0000FF / 3333FF / 0070C0 / 0432FF, red FF0000 / EE0000 mark notes) or, for the
odd line, as coloured flow runs. Question figures are inline OLE objects
(`w:object`) and one anchored axes drawing (Fig. 1.2).

What this does, on a COPY of the unzipped docx (the original is never touched):
  1. `ejc26_p2_prep.prep` with COVER_END "Section A": types auto-numbers, merges
     split bold label runs, drops the cover and the repeated question numbers.
  2. Removes every answer anchor, i.e. each `mc:AlternateContent` in a body
     paragraph, EXCEPT the Fig. 1.2 axes anchor (KEEP_ANCHORS), from which the
     answer-coloured runs are removed instead (the axes labels `pH` and
     `volume of NaOH / cm3` are black).
  3. Removes flow runs in an answer colour outside any anchor (reported).
  4. Asserts the anchor count (56 = 55 removed + 1 stripped) so a changed document
     raises instead of being half applied.

usage: python3 -m ingest.ejc26_p3_prep <unz_dir> <out_unz_dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

from lxml import etree

from . import ejc26_p2_prep
from .oxml import NS

W = "{%s}" % NS["w"]
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
ANSWER_COLOURS = {"0000FF", "3333FF", "FF0000", "EE0000", "0070C0", "0432FF"}
N_ANCHORS = 56

#: anchors that carry QUESTION content: (index of the Fig. 1.2 anchor paragraph's
#: text-box set) -> identified by the black axes labels inside the anchor
KEEP_MARKER = "volume of NaOH"


def _colour(r):
    c = r.find("w:rPr/w:color", NS)
    return c.get(W + "val").upper() if c is not None else None


def _in_anchor(e) -> bool:
    while e is not None:
        if e.tag == MC + "AlternateContent":
            return True
        e = e.getparent()
    return False


def prep(unz_dir, out_dir):
    ejc26_p2_prep.COVER_END = "Section A"
    done, merged = ejc26_p2_prep.prep(unz_dir, out_dir)
    doc = Path(out_dir) / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    log = ["typed auto-numbers %d, merged split labels %d" % (len(done), merged)]

    anchors = list(body.iter(MC + "AlternateContent"))
    assert len(anchors) == N_ANCHORS, "anchors: expected %d got %d" % (N_ANCHORS, len(anchors))
    removed = kept = 0
    for ac in anchors:
        text = "".join(t.text or "" for t in ac.find(MC + "Choice").iter(W + "t"))
        if KEEP_MARKER in text:
            kept += 1
            # keep the drawing, drop its answer-coloured runs (and any now-empty run)
            for r in list(ac.find(MC + "Choice").iter(W + "r")):
                if _colour(r) in ANSWER_COLOURS:
                    r.getparent().remove(r)
            fb = ac.find(MC + "Fallback")
            if fb is not None:
                for r in list(fb.iter(W + "r")):
                    if _colour(r) in ANSWER_COLOURS:
                        r.getparent().remove(r)
        else:
            parent = ac.getparent()          # w:r
            gp = parent.getparent()          # w:p
            gp.remove(parent)
            removed += 1
    assert kept == 1 and removed == N_ANCHORS - 1, (kept, removed)
    log.append("answer anchors removed %d, axes anchor stripped %d" % (removed, kept))

    # coloured flow runs outside any anchor
    stray = []
    for r in list(body.iter(W + "r")):
        if _colour(r) in ANSWER_COLOURS and not _in_anchor(r):
            tx = "".join(t.text or "" for t in r.findall("w:t", NS))
            if tx.strip():
                stray.append(tx)
            r.getparent().remove(r)
    log.append("answer-coloured flow runs removed: %d %s" % (len(stray), stray[:10]))

    # The school types two "(b)" in Q4: the sulfur dioxide part follows (b)(v) and
    # is the paper's (c). Relabel its bold "(b)" run so the parser sees (c)(i)-(iv)
    # (same treatment as EJC 2026 P2 Q1's second "(b)").
    hits = []
    for p in body.findall("w:p", NS):
        txt = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        if txt.startswith("(b)") and txt[3:].lstrip().startswith("The amount of sulfur dioxide"):
            hits.append(p)
    assert len(hits) == 1, "Q4 second (b): expected 1 paragraph, got %d" % len(hits)
    done_relabel = False
    for r in hits[0].findall("w:r", NS):
        t = r.find("w:t", NS)
        if t is not None and (t.text or "").strip() == "(b)":
            t.text = "(c)"
            done_relabel = True
            break
    assert done_relabel, "Q4 second (b): label run not found"
    log.append("Q4 second (b) relabelled (c)")
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    return log


if __name__ == "__main__":      # pragma: no cover
    for line in prep(sys.argv[1], sys.argv[2]):
        print(line)
