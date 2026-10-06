"""Prepare a paragraph-flow MCQ question paper whose question numbers are a
MIX of typed digits and Word AUTO-NUMBERING, for `questions_flow.py`.

SHAPE (first seen: CJC 2024 H2 P1, 2026-10-05). Like EJC 2024 H2 P1 the paper
flows in ordinary paragraphs with no per-question table, but the question
numbers are not all typed. Most are a literal digit glued to the stem
("4The value of pV ..."); six (Q1, Q2, Q5, Q10, Q11, Q12) are `w:numPr` list
paragraphs whose number exists only at render time, so the document text has
NO digit there and `questions_flow.QSTART` never sees the question begin.
Statement lists inside questions (1./2./3.) are ALSO numPr, and some
statements are typed ("2The Ka value ..."), so "is this a question number?"
cannot be answered from the paragraph alone.

THE RULE (sequence-based, so it needs no per-paper list):
  walk the body in order, tracking `last` = the last accepted question number.
  * a paragraph that starts with a typed 1-2 digit number followed by a
    capital letter or "(" is a question start ONLY IF number == last + 1.
    ("2The Ka value" inside Q3 is number 2 != 4, so it is a statement.)
  * a `w:numPr` paragraph at ilvl 0 is a question start ONLY IF its computed
    list number (the list's `w:start` plus how many earlier paragraphs used
    the same numId) == last + 1. A statement list restarts at 1 and Q1/Q2 are
    the only places where last + 1 == 1 or 2 coincides with a statement list,
    which does not happen in a paper that opens on Q1.
For each numPr question start, the numPr is removed and the digit is typed in
as a first run, i.e. the paragraph becomes the shape `questions_flow.py`
already handles. The ORIGINAL document.xml is never touched: the result is a
copy of the unzipped directory.

It REFUSES (raises) unless the accepted numbers are exactly 1..N with no gap,
because a missed question would silently glue two questions together.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
from .questions_flow import QSTART as _TYPED  # one definition of "typed start"


def _starts(numbering_xml: Path) -> dict:
    """{numId: start value of level 0}"""
    root = etree.parse(str(numbering_xml)).getroot()
    abstract = {}
    for a in root.findall("w:abstractNum", NS):
        aid = a.get(W + "abstractNumId")
        lvl = None
        for l in a.findall("w:lvl", NS):
            if l.get(W + "ilvl") == "0":
                lvl = l
                break
        st = lvl.find("w:start", NS) if lvl is not None else None
        abstract[aid] = int(st.get(W + "val")) if st is not None else 1
    out = {}
    for n in root.findall("w:num", NS):
        aid = n.find("w:abstractNumId", NS).get(W + "val")
        out[n.get(W + "numId")] = abstract.get(aid, 1)
    return out


def prep(unz_dir, out_dir) -> list:
    """Copy `unz_dir` to `out_dir`, typing in the auto-numbered question
    numbers. Returns [(qnum, kind)] for every accepted question start."""
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    starts = _starts(out_dir / "word/numbering.xml")

    doc = out_dir / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)

    last, seen_per_num, accepted = 0, {}, []
    for p in body.findall("w:p", NS):
        npr = p.find("w:pPr/w:numPr", NS)
        text = "".join(p.itertext())
        if npr is not None:
            nid_el = npr.find("w:numId", NS)
            ilvl_el = npr.find("w:ilvl", NS)
            nid = nid_el.get(W + "val") if nid_el is not None else None
            ilvl = ilvl_el.get(W + "val") if ilvl_el is not None else "0"
            if nid is not None and ilvl == "0" and text.strip():
                n = starts.get(nid, 1) + seen_per_num.get(nid, 0)
                seen_per_num[nid] = seen_per_num.get(nid, 0) + 1
                if n == last + 1:
                    npr.getparent().remove(npr)
                    run = etree.Element(W + "r")
                    t = etree.SubElement(run, W + "t")
                    t.text = str(n)
                    ppr = p.find("w:pPr", NS)
                    idx = list(p).index(ppr) + 1 if ppr is not None else 0
                    p.insert(idx, run)
                    last = n
                    accepted.append((n, "auto-numbered"))
            continue
        m = _TYPED.match(text)
        if m and int(m.group(1)) == last + 1:
            last = int(m.group(1))
            accepted.append((last, "typed"))

    nums = [n for n, _k in accepted]
    if nums != list(range(1, len(nums) + 1)):
        raise SystemExit("flow_numpr_prep: question numbers %s are not a "
                         "contiguous 1..N run" % nums)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return accepted


if __name__ == "__main__":
    import sys
    acc = prep(sys.argv[1], sys.argv[2])
    auto = [n for n, k in acc if k == "auto-numbered"]
    print("questions: %d; auto-numbered (typed in): %s" % (len(acc), auto))
