"""Prepare NYJC 2026 H2 P2 (9476/02, 7 structured, 75 marks, paragraph-flow) for `parts_flow.py`.

What the generic `flow_parts_prep` does not cover on this paper:

1. Q1 and Q3 open with ONE bold run holding the question number AND the first part label
   ("1(a)", "3(a)"). `parts_flow` recognises a question number only as a run whose text is exactly
   a bare digit, so Q1 was lost and Q3 was filed under Q2. Here such a run is split into two bold
   runs ("1" + "(a)").
2. Auto-numbered (i)/(ii)/(iii) labels (Q4(a), Q7(c)(iv), Q7(d)) are typed in by
   `flow_parts_prep.prep` first, on the same copy; the Q3(a) criteria list is a bullet list and is
   left for the parser (rendered as ul.stmts).

The ORIGINAL document.xml is never touched: the result is a copy of the unzipped directory.

Run:  python3 -m ingest.nyjc26_p2_prep unz unz_prep
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

from lxml import etree

from . import flow_parts_prep
from .oxml import NS

W = "{%s}" % NS["w"]
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
COVER_END = "Answer all questions in the spaces provided"
_QPART = re.compile(r"^(\d{1,2})(\([a-z]\))$")


def _is_bold(r) -> bool:
    b = r.find("w:rPr/w:b", NS)
    return b is not None and b.get(W + "val") not in ("0", "false")


def split_qnum_part(p) -> int:
    """Split a leading bold run '1(a)' into bold '1' + bold '(a)'. Returns 1 if split."""
    for r in p.findall("w:r", NS):
        ts = r.findall("w:t", NS)
        txt = "".join(t.text or "" for t in ts)
        if not txt.strip():
            continue
        m = _QPART.match(txt)
        if not (m and _is_bold(r) and len(ts) == 1):
            return 0
        second = copy.deepcopy(r)
        for lr in second.findall("w:lastRenderedPageBreak", NS):
            second.remove(lr)
        ts[0].text = m.group(1)
        second.find("w:t", NS).text = m.group(2)
        r.addnext(second)
        return 1
    return 0


def prep(unz_dir, out_dir):
    done = flow_parts_prep.prep(unz_dir, out_dir, cover_end=COVER_END)
    doc = Path(out_dir) / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    n = 0
    for p in body.findall("w:p", NS):
        n += split_qnum_part(p)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    return done, n


if __name__ == "__main__":
    done, n = prep(sys.argv[1], sys.argv[2])
    print("typed auto-numbered labels:", len(done), "| split 'N(a)' runs:", n)
    if n != 2:
        raise SystemExit("expected exactly 2 split runs (Q1, Q3), got %d" % n)
