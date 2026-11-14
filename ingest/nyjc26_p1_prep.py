"""NYJC 2026 H2 P1 (9476/01, 30 MCQ): prepare the question paper for
`questions_flow.py`.

SHAPE. The school sent a binary `.doc` (no .docx), converted here with
LibreOffice (`soffice --convert-to docx`). The result is paragraph-flow
(MCQ-L1 stems, MCQ-L2 option paragraphs, ordinary tables for data and
row-style options), but the QUESTION NUMBERS are gone: Word supplied them
from the style's list numbering and the conversion keeps no digit anywhere.
Neither `flow_numpr_prep` (no numPr on the stems) nor the typed-number rule
of `questions_flow.QSTART` can find the question starts.

WHAT THIS DOES (on a COPY of the unzipped docx; the original is untouched):
  1. Read the printed question starts from the Word-exported PDF (a line that
     opens "N<spaces>text" with N == last + 1, pages 2-16 only). The PDF is
     the independent record of where each question begins.
  2. Walk the docx body in order; for question N find the next body paragraph
     whose text opens with the same first words as the printed stem, and type
     "N " in as a first run.
  3. Drop the no-op list markers LibreOffice writes (`numPr` with numId 0).
  4. Normalise a bare 2-hex Symbol code ("73") to Word's "F073" form.
  5. Q9 (tab-line options): give each marker letter its own run + a tab run.
  6. Drop the answers-page block (everything from the "Please write in the
     following format on the last page" paragraph on): it is the setters'
     answer table, answer-side material, not part of the question paper.
It REFUSES (raises) unless all 30 starts are found, in order, each in exactly
one paragraph, so a missed or mis-matched question cannot slip through.

usage: python3 -m ingest.nyjc26_p1_prep <unz_dir> <word.pdf> <unz_q_dir>
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
EXPECTED = 30
FIRST_PAGE, LAST_PAGE = 2, 16
TAIL_MARK = "Please write in the following format"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def pdf_starts(pdf: str):
    """[(n, normalised first ~30 chars of the printed stem)] for n = 1..30."""
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                         capture_output=True, text=True, check=True).stdout
    pages = txt.split("\f")
    last, out = 0, []
    for pno in range(FIRST_PAGE, LAST_PAGE + 1):
        for line in pages[pno - 1].splitlines():
            m = re.match(r"^\s*(\d{1,2})\s+(\S.*)$", line)
            if m and int(m.group(1)) == last + 1:
                last += 1
                out.append((last, _norm(m.group(2))[:30]))
    if [n for n, _ in out] != list(range(1, EXPECTED + 1)):
        raise SystemExit("pdf_starts: found %s, wanted 1..%d"
                         % ([n for n, _ in out], EXPECTED))
    return out


def prep(unz_dir, pdf, out_dir):
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    doc = out_dir / "word" / "document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    kids = list(body)

    # --- 3. cut the answers page ---------------------------------------
    cut = None
    for i, el in enumerate(kids):
        if el.tag == W + "p" and TAIL_MARK in "".join(el.itertext()):
            cut = i
            break
    if cut is None:
        raise SystemExit("answers-page marker not found")
    removed = 0
    for el in kids[cut:]:
        if el.tag == W + "sectPr":
            continue
        body.remove(el)
        removed += 1

    # --- 4. numPr with numId 0 means "no numbering". LibreOffice writes it on
    # 142 stem/option paragraphs; `questions_flow` reads ANY numPr as list content
    # and so never sees the typed option letters. Drop the no-ops. Real lists
    # (numId 3: Q23's statements 1-3) are kept. --------------------------------
    nop = 0
    for npr in list(body.iter(W + "numPr")):
        nid = npr.find("w:numId", NS)
        if nid is not None and nid.get(W + "val") == "0":
            npr.getparent().remove(npr)
            nop += 1

    # --- 5. LibreOffice writes ONE symbol (Q19 option D, sigma) as a bare
    # 2-hex-digit code ("73") where Word writes "F073"; the extractor's Symbol
    # table is keyed on the F0xx form. -----------------------------------------
    fixed_sym = 0
    for sy in body.iter(W + "sym"):
        ch = sy.get(W + "char") or ""
        if re.fullmatch(r"[0-9A-Fa-f]{2}", ch):
            sy.set(W + "char", "F0" + ch.upper())
            fixed_sym += 1

    # --- 6. Q9's four options share ONE tab-separated line. `questions_flow`
    # accepts a marker only if the NEXT run opens with a tab. Here B's tab sits in
    # B's own run, and C / D carry trailing spaces and no tab at all. Normalise:
    # letter alone in its run, a tab-only run straight after it. ----------------
    split_marks = 0
    for p in body.findall("w:p", NS):
        st = p.find("w:pPr/w:pStyle", NS)
        if st is None or st.get(W + "val") != "MCQOp1rx4cleft":
            continue
        runs = p.findall("w:r", NS)
        for r in runs:
            ts = r.findall("w:t", NS)
            if len(ts) != 1 or not re.fullmatch(r"[ABCD]\s*", ts[0].text or ""):
                continue
            ts[0].text = ts[0].text.strip()
            for tb in r.findall("w:tab", NS):
                r.remove(tb)
            nxt = r.getnext()
            first = None
            if nxt is not None and nxt.tag == W + "r":
                first = next((c for c in nxt if c.tag != W + "rPr"), None)
            if first is None or first.tag != W + "tab":
                tr = etree.Element(W + "r")
                etree.SubElement(tr, W + "tab")
                r.addnext(tr)
            split_marks += 1

    # --- 1/2. type the question numbers --------------------------------
    starts = pdf_starts(pdf)
    paras = [p for p in body if p.tag == W + "p"]
    pos, report = 0, []
    for n, want in starts:
        hit = None
        while pos < len(paras):
            p = paras[pos]
            pos += 1
            t = _norm("".join(p.itertext()))
            if t and t.startswith(want[:24]):
                hit = p
                break
        if hit is None:
            raise SystemExit("Q%d: no paragraph starts with %r" % (n, want))
        run = etree.Element(W + "r")
        t = etree.SubElement(run, W + "t")
        t.text = "%d " % n
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        ppr = hit.find("w:pPr", NS)
        hit.insert(list(hit).index(ppr) + 1 if ppr is not None else 0, run)
        report.append((n, "".join(hit.itertext())[:50]))
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return report, removed, nop, fixed_sym, split_marks


if __name__ == "__main__":
    rep, removed, nop, fixed_sym, split_marks = prep(sys.argv[1], sys.argv[2], sys.argv[3])
    print("question numbers typed in: %d; answers-page elements removed: %d; "
          "no-op numPr (numId 0) dropped: %d; bare symbol codes fixed: %d; "
          "tab-line option markers tidied: %d"
          % (len(rep), removed, nop, fixed_sym, split_marks))
    for n, s in rep:
        print("  Q%-2d %s" % (n, s))
