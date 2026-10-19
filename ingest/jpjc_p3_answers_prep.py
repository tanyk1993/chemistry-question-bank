"""JPJC 2024 H2 P3 suggested solutions: attach each answer row to its own question part.

`jpjc_p3_prep --multi` squares every table to [qnum|letter|roman|content|marks]. In this
paper's solutions the layout is NOT "question and answer in the same row" (the P2 shape):
each lettered block prints ALL its question rows first, then a block of ANSWER rows that
repeat the roman labels, e.g.

    (a)(i) question   (a)(ii) question   (a)(iii) question
    (i)    answer     (ii)    answer     (iii)   answer

`parts.py` would read the second block as duplicate parts. This step moves every such
repeated-label row to the end of the row group of the part it answers and blanks its label
cells, so it becomes a continuation row of that part (the marker-zone code in
`extract_jpjc_p3_answers` then colours it as answer, as it does for P2).

Also: a label "(i)"/"(ii)".. typed in the LETTER slot is a roman numeral (letters stop at
(g)); it is moved to the roman slot.

Usage: python3 -m ingest.jpjc_p3_answers_prep <unz_prep_in> <unz_out>
Every assumption is asserted: it raises rather than guessing.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS, Wq

ROMAN = {"(i)", "(ii)", "(iii)", "(iv)", "(v)", "(vi)"}

#: The solutions' answer rows for Q4(c) are labelled "(i)" and "(ii)" but answer parts
#: (c)(ii) (the energy cycle + Hess' Law) and (c)(iii) (HCl vs CH3COOH): the (c)(i)
#: definition is typed straight under its own question. Declared fix; asserted.
ANSWER_RELABEL = {(4, "(c)", "(i)"): "(ii)", (4, "(c)", "(ii)"): "(iii)"}


def _text(el) -> str:
    return "".join(el.itertext(Wq + "t")).strip()


def _blank_cell(tc):
    for p in tc.findall("w:p", NS)[1:]:
        tc.remove(p)
    p = tc.find("w:p", NS)
    for ch in list(p):
        if etree.QName(ch).localname != "pPr":
            p.remove(ch)


def _set_text(tc, text):
    _blank_cell(tc)
    p = tc.find("w:p", NS)
    r = etree.SubElement(p, Wq + "r")
    etree.SubElement(r, Wq + "t").text = text


def prep(unz_in: Path, unz_out: Path) -> list[str]:
    unz_in, unz_out = Path(unz_in), Path(unz_out)
    if unz_out.exists():
        shutil.rmtree(unz_out)
    shutil.copytree(unz_in, unz_out)
    doc = unz_out / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    tbls = body.findall("w:tbl", NS)[1:]          # skip the cover table
    rows = [tr for tb in tbls for tr in tb.findall("w:tr", NS)]
    log = []

    q = letter = None
    seen = {}            # key -> list of row elements in its group (question row first)
    group_of = {}        # id(row) -> key (rows that belong to a part, incl. continuations)
    last_key = None
    relabelled = set()
    cur_dup = None       # key of the answer row whose continuation rows we are walking
    moves = []           # (answer row, key)
    n_roman_fix = 0
    for tr in rows:
        tcs = tr.findall("w:tc", NS)
        if len(tcs) != 5:
            raise SystemExit("row with %d cells; run jpjc_p3_prep --multi first" % len(tcs))
        t = [_text(c) for c in tcs[:3]]
        # a roman numeral typed in the letter slot
        if t[1] in ROMAN and not t[2]:
            _set_text(tcs[2], t[1])
            _blank_cell(tcs[1])
            t[2], t[1] = t[1], ""
            n_roman_fix += 1
        if t[0]:
            q = int(t[0])
            letter = None
        if t[1]:
            letter = t[1]
        if not (t[0] or t[1] or t[2]):                 # continuation row
            if last_key is None:
                raise SystemExit("continuation row before any part")
            if cur_dup is not None:                   # belongs to the answer row above it
                moves.append((tr, cur_dup))
                continue
            group_of[id(tr)] = last_key
            seen[last_key].append(tr)
            continue
        key = (q, letter, t[2])
        if t[2] and key in seen:                      # repeated label: an ANSWER row
            orig = key
            key = (q, letter, ANSWER_RELABEL.get(orig, t[2]))
            if key not in seen:
                raise SystemExit("relabelled answer row has no question part: %r" % (key,))
            if key != orig:
                relabelled.add(orig)
            moves.append((tr, key))
            cur_dup = key
            continue
        cur_dup = None
        seen[key] = [tr]
        group_of[id(tr)] = key
        last_key = key
    if relabelled != set(ANSWER_RELABEL):
        raise SystemExit("declared ANSWER_RELABEL did not all apply")
    # ----- relocate the answer rows
    for tr, key in moves:
        anchor = seen[key][-1]
        tcs = tr.findall("w:tc", NS)
        for c in tcs[:3]:
            _blank_cell(c)
        parent = tr.getparent()
        parent.remove(tr)
        anchor.addnext(tr)
        seen[key].append(tr)
        log.append("answer row moved under Q%s %s%s" % (key[0], key[1] or "", key[2]))
    # drop tables left with no rows
    dropped = 0
    for tb in body.findall("w:tbl", NS):
        if not tb.findall("w:tr", NS):
            body.remove(tb)
            dropped += 1
    log.append("%d answer rows relocated; %d roman labels moved out of the letter slot; "
               "%d emptied tables dropped" % (len(moves), n_roman_fix, dropped))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    return log


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print("\n".join(prep(sys.argv[1], sys.argv[2])))
