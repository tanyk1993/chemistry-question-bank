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


# EQUATION OPTIONS READ AS FRACTIONS
# ----------------------------------
# An OPTION-position Equation.DSMT4 object defaults to "option" -- a croppable
# picture, same as a genuine structure -- because that object kind alone does
# not say whether the PDF prints something `question_figures.read_fraction`
# can actually read cleanly. Some can: a plain numerator/denominator split
# with one hairline rule.
#
# Each entry is only added after checking the PDF directly (get_drawings())
# for a genuine thin rule with ordinary text above and below it, sharing its
# x-range -- the same bar read_fraction() itself requires. Keyed by (school,
# level, paper, year, qnum) -> the set of option letters confirmed this way;
# an unlisted question's option-position equations all default to "option".
EQUATION_OPTIONS_AS_FRACTIONS = {
    ("EJC", "H2", "P1", 2024, 9): {"A", "B", "C", "D"},
}


def frac_option_letters(school, level, paper, year, qnum) -> set:
    """Option letters confirmed to be plain, readable fractions -- see above."""
    return EQUATION_OPTIONS_AS_FRACTIONS.get((school, level, paper, year, qnum), set())


# EQUATION OPTIONS RENDERED AS HOUSE MARKUP (not cropped images)
# ----------------------------------------------------------------
# Some OPTION-position Equation.DSMT4 objects are more than `read_fraction`'s
# simple one-rule split, but are still fully reconstructable BY HAND once
# read directly from the PDF. EJC 2024 H2 P1 Q13's four options use
# MathType's stretchy two-piece bracket glyphs (U+F0E9/F0EB/F0F9/F0FB,
# already in audit.FIGURE_BORNE) around concentration terms nested inside a
# square root or a fraction. All four share a "[H+] = " prefix, confirmed by
# rendering each option's FULL printed cell (not just the piece crop_in's
# vector-only clustering happened to find -- that clustering follows
# get_drawings()/get_images() only, and "[H+] = " is built entirely from
# TEXT glyphs, so for A/B specifically the auto-crop that was briefly live
# silently cropped OFF that prefix; caught only by re-rendering the whole
# cell and looking, not by any gate). The four read: [H+] = sqrt(Ka[acid]),
# [H+] = sqrt(Ka[salt]), [H+] = Ka x [acid]/[salt], [H+] = Ka x [salt]/[acid]
# -- standard weak-acid and buffer-equation forms, and internally consistent
# (same Ka, same "acid"/"salt" concentration labels, just recombined). User
# request, 2026-09-25: prefer real markup over a cropped image here, now
# that the expression is confirmed hand-reconstructable, so it reflows, is
# searchable, and matches how every other equation in the bank renders.
#
# `html` uses the house .frac (span.frac/.fnum/.fden) and NEW .sqrt
# (span.sqrt/.rad) conventions, plus <sup>/<sub> and <i> for the K (this
# document's OWN convention for an equilibrium constant, confirmed from
# Q10's Kc: `<i>K</i><sub>c</sub>`, parsed from ordinary prose runs -- not
# invented for this entry). No inline `style=` (style-guide.md #7, "never
# emit"). `text` is the same content flattened for
# content_text/options_json/search, in the same "(num)/(den)" shape
# render_questions.py already uses for a read fraction.
#
# Keyed (school, level, paper, year, qnum) -> {letter: (html, text)}. An
# unlisted question's option-position equations are unaffected (fall through
# to EQUATION_OPTIONS_AS_FRACTIONS, then to a plain cropped "option").
EQUATION_OPTIONS_AS_TEXT = {
    ("EJC", "H2", "P1", 2024, 13): {
        "A": ('[H<sup>+</sup>] = <span class="sqrt"><span class="rad">'
              '<i>K</i><sub>a</sub> [acid]</span></span>',
              '[H+] = √(Ka [acid])'),
        "B": ('[H<sup>+</sup>] = <span class="sqrt"><span class="rad">'
              '<i>K</i><sub>a</sub> [salt]</span></span>',
              '[H+] = √(Ka [salt])'),
        "C": ('[H<sup>+</sup>] = <i>K</i><sub>a</sub> <span class="frac">'
              '<span class="fnum">[acid]</span>'
              '<span class="fden">[salt]</span></span>',
              '[H+] = Ka ([acid])/([salt])'),
        "D": ('[H<sup>+</sup>] = <i>K</i><sub>a</sub> <span class="frac">'
              '<span class="fnum">[salt]</span>'
              '<span class="fden">[acid]</span></span>',
              '[H+] = Ka ([salt])/([acid])'),
    },
}


def eqtext_options(school, level, paper, year, qnum) -> dict:
    """{letter: (html, text)} for option equations rendered as markup -- see above."""
    return EQUATION_OPTIONS_AS_TEXT.get((school, level, paper, year, qnum), {})


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
