"""RVHS 2026 H2 P1 (9476/01, 30 MCQ): prepare the question paper for
`questions.py` (table shape: one Word table per question, numbered 1-30).

SHAPE. The school sent a binary `.doc`, converted here with LibreOffice
(`soffice --convert-to docx`). Unlike NYJC 2026 P1 the question numbers survive
(each question is a table whose first cell is the bare number), so no numbering
repair is needed. What the conversion does leave behind are `w:sym` elements the
extractor cannot resolve, so this prep normalises them on a COPY of the unzipped
docx (the original is untouched):

  1. A bare 2-hex Symbol code ("2d") -> Word's "F0xx" form ("F02D"): the minus
     sign in Q1, Q2, Q9 (12x). Same LibreOffice quirk as NYJC 2026 P1.
  2. `Symbol 6f` (Q30, "melting point / <o>C") is Symbol-font omicron used by the
     setters as a degree sign; the Word PDF prints a small raised circle. -> the
     degree sign (F0B0).
  3. Font `Chemical;Euclid Extra` (LibreOffice joins the two fallbacks):
       F03D  the equilibrium arrow (Q7 B, Q15, Q17), same glyph as "Chemical"
             F03D in symbols.py -> the font name is cut to "Chemical".
       F029  the short curved chain-end bond mark printed at both ends of an
             addition-polymer repeat unit (Q28 statements 1-4, 13 marks). Typed
             as an en dash, the standard way to write a repeat unit in text.
             (If the user prefers the printed marks, Q28 is snipped instead.)

usage: python3 -m ingest.rvhs26_p1_prep <unz_dir> <unz_prep_dir>
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS

W = "{%s}" % NS["w"]
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def prep(unz_dir, out_dir):
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    doc = out_dir / "word" / "document.xml"
    tree = etree.parse(str(doc))
    root = tree.getroot()

    bare = degree = arrows = bonds = 0
    for sy in list(root.iter(W + "sym")):
        font = (sy.get(W + "font") or "").strip()
        ch = (sy.get(W + "char") or "").strip()
        if font == "Symbol" and re.fullmatch(r"[0-9A-Fa-f]{2}", ch):
            if ch.lower() == "6f":
                sy.set(W + "char", "F0B0")
                degree += 1
            else:
                sy.set(W + "char", "F0" + ch.upper())
                bare += 1
        elif font == "Chemical;Euclid Extra":
            if ch.upper() == "F03D":
                sy.set(W + "font", "Chemical")
                arrows += 1
            elif ch.upper() == "F029":
                # replace the symbol by a plain en dash run content
                t = etree.Element(W + "t")
                t.text = "–"
                t.set(XML_SPACE, "preserve")
                sy.addprevious(t)
                sy.getparent().remove(sy)
                bonds += 1
            else:
                raise SystemExit("unexpected Chemical;Euclid Extra code %s" % ch)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return bare, degree, arrows, bonds


if __name__ == "__main__":
    bare, degree, arrows, bonds = prep(sys.argv[1], sys.argv[2])
    print("bare Symbol codes fixed: %d; omicron->degree: %d; equilibrium "
          "arrows: %d; chain-end bond marks -> en dash: %d"
          % (bare, degree, arrows, bonds))
    assert (bare, degree, arrows, bonds) == (12, 1, 3, 13), (
        bare, degree, arrows, bonds)
