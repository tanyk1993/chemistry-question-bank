"""Make a QUESTION-ONLY copy of a Word-exported "question paper + suggested
solutions" PDF, for the text gate and `question_bands`.

The answer text in this document shape (ASRJC 2024 H2 P1, see
`inline_answers_prep.py`) is coloured -- blue 0000CC (PDF span colour 0xCC) and a
darker blue 0000A0 (0xA0) in a few worked lines. Every span in those colours is
redacted (text only; lines, boxes and images are left alone), so the PDF's text
layer holds the questions and nothing else. Without this, the charset gate
reports every character unique to an answer as a "dropped glyph".

Usage: python3 -m ingest.redact_inline_answers_pdf in.pdf out.pdf [0xcc,0xa0]
"""
from __future__ import annotations

import sys

import pymupdf


def redact(src, dst, colours=(0xCC, 0xA0)) -> int:
    doc = pymupdf.open(src)
    n = 0
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for sp in line["spans"]:
                    if sp["color"] in colours and sp["text"].strip():
                        page.add_redact_annot(pymupdf.Rect(sp["bbox"]), fill=False)
                        n += 1
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    doc.save(dst)
    return n


if __name__ == "__main__":      # pragma: no cover
    cols = tuple(int(x, 16) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else (0xCC, 0xA0)
    print(redact(sys.argv[1], sys.argv[2], cols), "spans redacted")
