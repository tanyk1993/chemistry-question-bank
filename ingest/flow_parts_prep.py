"""Prepare a paragraph-flow STRUCTURED paper (parts_flow.py's shape) whose
part / sub-part labels are partly Word AUTO-NUMBERING (`w:numPr`, no label text
in the paragraph) and partly typed.

Written for CJC 2024 H2 P2 (2026-10-08), the structured sibling of
`flow_numpr_prep.py` (which does the same for MCQ question numbers).

`parts_flow.parse()` finds every label as a leading BOLD run whose text is
exactly "(a)" / "(i)" / a bare digit. An auto-numbered paragraph has no such
run, so its label is silently lost and its text is filed under the previous
part (CJC P2: Q1's (a)-(d), Q3(a)(ii)-(iv), Q4(e)(ii)-(v), Q5(f)(i)-(iv) and
Q5(g) are all auto-numbered; the typed ones sit between them).

What this does, on a COPY of the unzipped docx:

1. For every body paragraph carrying `w:numPr` at level 0 with visible text and
   a letter/roman format, compute the label Word would print -- the abstractNum
   level's `numFmt` / `lvlText` / `start`, counted per `numId` in document
   order -- and insert it as a leading BOLD run, then drop the numPr so
   nothing is counted twice. Bullets are left alone.
2. Optionally drop everything before the first body paragraph whose text starts
   with `cover_end` (the cover page: its bold "2 hours" otherwise parses as a
   question 2, and its logo drawings would be planned as figures).

It RAISES rather than guesses when a numPr paragraph's format is neither
lowerLetter nor lowerRoman nor decimal, so a new school's shape cannot be
silently mislabelled.

Run:  python3 -m ingest.flow_parts_prep unz unz_prep "Answer all the questions"
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]


def _roman(n: int) -> str:
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def _level0(numbering_xml: Path) -> dict:
    """{numId: (numFmt, lvlText, start)} for ilvl 0."""
    root = etree.parse(str(numbering_xml)).getroot()
    abstract = {}
    for a in root.findall("w:abstractNum", NS):
        for l in a.findall("w:lvl", NS):
            if l.get(W + "ilvl") == "0":
                fmt = l.find("w:numFmt", NS).get(W + "val")
                txt = l.find("w:lvlText", NS).get(W + "val")
                st = l.find("w:start", NS)
                abstract[a.get(W + "abstractNumId")] = (
                    fmt, txt, int(st.get(W + "val")) if st is not None else 1)
    out = {}
    for n in root.findall("w:num", NS):
        aid = n.find("w:abstractNumId", NS).get(W + "val")
        out[n.get(W + "numId")] = abstract[aid]
    return out


def _label(fmt: str, lvl_text: str, n: int) -> str:
    if fmt == "lowerLetter":
        body = chr(ord("a") + n - 1)
    elif fmt == "lowerRoman":
        body = _roman(n)
    elif fmt == "decimal":
        body = str(n)
    else:
        raise SystemExit("flow_parts_prep: unhandled numFmt %r" % fmt)
    return lvl_text.replace("%1", body)


def prep(unz_dir, out_dir, cover_end: str | None = None) -> list:
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    fmts = _level0(out_dir / "word/numbering.xml")

    doc = out_dir / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)

    if cover_end:
        kids = list(body)
        cut = None
        for i, el in enumerate(kids):
            if el.tag == W + "p" and "".join(el.itertext()).strip().startswith(cover_end):
                cut = i
                break
        if cut is None:
            raise SystemExit("flow_parts_prep: cover_end %r not found" % cover_end)
        for el in kids[:cut]:
            if el.tag != W + "sectPr":
                body.remove(el)

    counts, done = {}, []
    for p in body.findall("w:p", NS):
        npr = p.find("w:pPr/w:numPr", NS)
        if npr is None:
            continue
        nid_el, il_el = npr.find("w:numId", NS), npr.find("w:ilvl", NS)
        nid = nid_el.get(W + "val") if nid_el is not None else None
        il = il_el.get(W + "val") if il_el is not None else "0"
        if nid is None or il != "0" or nid not in fmts:
            continue
        fmt, lvl_text, start = fmts[nid]
        if fmt == "bullet":
            continue
        # Word counts every numbered paragraph, empty or not, so count first
        counts[nid] = counts.get(nid, 0) + 1
        if not "".join(p.itertext()).strip():
            continue
        label = _label(fmt, lvl_text, start + counts[nid] - 1)
        npr.getparent().remove(npr)
        run = etree.Element(W + "r")
        rpr = etree.SubElement(run, W + "rPr")
        etree.SubElement(rpr, W + "b")
        t = etree.SubElement(run, W + "t")
        t.text = label
        ppr = p.find("w:pPr", NS)
        idx = list(p).index(ppr) + 1 if ppr is not None else 0
        p.insert(idx, run)
        done.append((nid, label, "".join(p.itertext())[len(label):len(label) + 50]))

    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    return done


if __name__ == "__main__":
    res = prep(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    for r in res:
        print(r)
