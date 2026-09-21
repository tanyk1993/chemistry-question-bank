"""Deliberate, recorded departures from the source document.

Handoff SS6D: "Consider recording what changed from the original so the bank does
not drift silently from the papers." That is the whole point of this file. A
correction applied here is applied ONCE, in one place, with a reason attached,
and the driver prints every hit. A correction made by hand in a SQL string is
invisible six months later.

Precedent: handoff SS4 item 8 corrected "as follow" -> "as follows" in RI's own
question paper. Schools' mark schemes contain ordinary human errors, and quietly
reproducing them into a revision tool is not fidelity, it is a bug with a
pedigree. But neither should they be changed without a trace.

Each entry is (pattern, replacement, reason, approved_by).

DROPPED FIGURES
---------------
The same principle applied to pictures. A figure whose content the extractor
has ALREADY captured as text is not placed a second time: it is dropped, here,
with a reason, and the driver prints it. Keyed by (school, level, paper, year,
qnum) -> {block ordinal in document order: reason}, where the ordinal counts
only BLOCK figures (fractions and option structures are not candidates).

A drop renumbers the `stem` slots after it, because the slots stay contiguous
-- so a figure must be dropped BEFORE the paper is loaded, or the later assets
in that question have to be re-uploaded under their new names.
"""
from __future__ import annotations

import re

DROPPED_FIGURES = {
    ("RI", "H2", "P1", 2024, 12): {
        1: "RI's Word file contains the enthalpy data table TWICE: once as a "
           "real w:tbl, which oxml.py descends into and renders as "
           "table.qt, and once as a picture of that same table sitting "
           "beside it. Placing the picture as well would print the table "
           "twice in the app, and the markup version is the better one -- it "
           "reflows, it is searchable, and its 1/2 coefficients come through "
           "as span.frac. This leaves Q12 with no assets at all. "
           "(user, 2026-09-21: \"2 representations. i prefer the bottom one\")",
    },
}


def dropped_blocks(school, level, paper, year, qnum) -> dict:
    """{block ordinal: reason} for figures deliberately not placed."""
    return DROPPED_FIGURES.get((school, level, paper, year, qnum), {})


CORRECTIONS = [
    (
        r"Fig\.\s*3\.1",
        "Fig. 4.1",
        "RI's mark scheme captions the Q4 kinetics graph 'Fig. 3.1' and the "
        "4(a)(ii) answer text refers to it by that name, but the figure belongs "
        "to Q4, whose question-paper figures are 4.1/4.2 (cf. handoff SS4 item "
        "14). Confirmed present in RI's own Word file, so it is their error, "
        "not a conversion artefact.",
        "user, 2026-09-18",
    ),
]


def apply(html: str) -> tuple[str, list[str]]:
    """Return (corrected_html, [descriptions of what changed])."""
    log = []
    for pattern, replacement, reason, who in CORRECTIONS:
        new, n = re.subn(pattern, replacement, html)
        if n:
            log.append("%dx %s -> %r (%s; approved: %s)"
                       % (n, pattern, replacement, reason, who))
            html = new
    return html, log
