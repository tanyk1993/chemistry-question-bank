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

Each entry is (scope, pattern, replacement, reason, approved_by), where scope
is (school, level, paper, year) or None for a rewrite safe on every paper.

SCOPING IS NOT OPTIONAL. The RI "Fig. 3.1" -> "Fig. 4.1" entry below is a fix
for one specific mistake in RI's OWN 2024 H2 P2 mark scheme. RI's 2024 H2 P3
prints a perfectly correct "Fig. 3.1" for an unrelated question -- left
unscoped, this same regex would silently rename that real figure the moment
P3's answers were ingested, and the text gate could not have seen the damage,
because the rewrite runs before the comparison, so both sides would agree on
the (now wrong) text. `apply(html, scope)` skips any entry whose scope
differs from the caller's; an entry with scope=None always runs.

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


# DROPPED PART FIGURES (structured papers)
# -----------------------------------------
# The same principle as DROPPED_FIGURES above, for the parts_flow.py /
# render_parts.py (P2/P3) pipeline, which has no ordinal-in-question concept
# to key on -- a structured paper's parser already gives every figure a part
# label, so this is keyed by (school, level, paper, year, qnum, part_label)
# directly, dropping every figure parts_flow.py found under that ONE part.
# (Never wired up before this paper: `dropped_blocks()` above is imported
# only by extract_questions.py/render_questions.py, the MCQ side -- no
# structured paper had needed a drop until now.)
#
# EJC 2024 H2 P3 Q2(a)(vi) parses one native Word `shape` figure with no
# printed counterpart at all: the PDF's own artwork search for that part's
# band comes back completely empty (confirmed directly, not inferred --
# `parts_figures.crop_owner()` reports "no artwork found in band"), and nor
# does a read of the printed page show anything there -- just prose and the
# usual dotted answer lines. Most likely a leftover, invisible drawing
# object in EJC's own Word template rather than anything the paper intends
# to show.
DROPPED_PART_FIGURES = {
    ("EJC", "H2", "P3", 2024, 2, "(a)(vi)"):
        "One native Word shape parses here with no target file and no "
        "printed counterpart -- the PDF's own artwork search for this "
        "part's band is empty, and the printed page shows only prose and "
        "answer-space dots. Not a real figure; almost certainly a leftover "
        "invisible drawing object in EJC's template.",
}


def dropped_part_figures(school, level, paper, year, qnum, part_label) -> str | None:
    """Reason string if EVERY figure parsed under this part should be
    dropped (no printed counterpart), else None -- see DROPPED_PART_FIGURES
    above. `part_label` is `None` for a question's own intro (not yet
    needed by any entry, but accepted for symmetry with `asset_plan()`'s own
    owner list)."""
    return DROPPED_PART_FIGURES.get((school, level, paper, year, qnum, part_label))


# COMBINED FIGURES
# ----------------
# The opposite deliberate departure: several of the document's OWN distinct
# drawings, printed under one part, collapsed into ONE cropped image instead
# of one per drawing. Default behaviour (`parts_flow.merge_owner_figures`)
# only merges drawings that sit with nothing between them -- correctly
# leaving two diagrams separated by real body text (a sentence, a second
# "conditions:" label) as two separate crops, because that is usually a
# genuine pair of pictures. Sometimes it isn't: EJC 2024 H2 P2 Q3(d) prints
# two small Latimer diagrams ("Acidic conditions:" / "Basic conditions:")
# that the user chose to snip as one combined image rather than two (user,
# 2026-09-26: "yes please combine them into the image"). Keyed by (school,
# level, paper, year, qnum, part) -> reason; an unlisted part is unaffected.
COMBINED_FIGURES = {
    ("EJC", "H2", "P2", 2024, 3, "(d)"):
        "Two Latimer diagrams (acidic conditions, basic conditions), "
        "separated only by the 'Basic conditions:' label -- user chose to "
        "snip them as one combined image rather than crop each separately.",
}


def combined_figures_reason(school, level, paper, year, qnum, part) -> str | None:
    """Reason string if this part's figures should be combined into ONE
    image, else None -- see COMBINED_FIGURES above."""
    return COMBINED_FIGURES.get((school, level, paper, year, qnum, part))


# ASSET FILENAME OVERRIDES
# ------------------------
# `render_parts.asset_plan()`'s own naming convention
# (`SCHOOL_LEVEL_PAPER_Q<n>_<slot>_<year>.png`) is a DEFAULT, not a promise:
# the user is free to save a crop under a different filename, and once that
# has happened and been committed live (`gen_parts_assets_fix_migration.py`),
# every FUTURE `asset_plan()` build must keep emitting that SAME corrected
# name -- or a later migration built from a fresh extraction silently
# reverts the fix. Found on EJC 2024 H2 P2, 2026-09-26: the formatting-
# review patch's own asset-resync step (`gen_parts_patch_migration.py`)
# rebuilt `asset_plan.json` from scratch, which used the stock names again
# and would have undone that same morning's filename-mismatch fix if it had
# been run -- caught from the dry run's own RETURNING output before it was
# committed, not by any automated check. Keyed by
# (school, level, paper, year, qnum, slot) -> the filename actually live in
# the storage bucket. An unlisted (school, level, paper, year, qnum, slot)
# keeps `asset_plan()`'s own generated default, unaffected.
ASSET_RENAMES = {
    ("EJC", "H2", "P2", 2024, 2, "intro"): "EJC_H2_P2_q2_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 2, "b"): "EJC_H2_P2_q2b_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 3, "a"): "EJC_H2_P2_q3a_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 3, "b"): "EJC_H2_P2_q3b_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 3, "bii"): "EJC_H2_P2_Q3_bii-w_2024.png",
    ("EJC", "H2", "P2", 2024, 3, "d"): "EJC_H2_P2_q3d_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 4, "intro"): "EJC_H2_P2_q4_stem_2024.png",
    ("EJC", "H2", "P2", 2024, 4, "intro2"): "EJC_H2_P2_Q4_fig1_2024.png",
    ("EJC", "H2", "P2", 2024, 4, "g"): "EJC_H2_P2_Q4_fig2_2024.png",
}


def renamed_asset_path(school, level, paper, year, qnum, slot, default_path):
    """The filename actually live in storage for this asset, or
    `default_path` unchanged if it was never renamed -- see ASSET_RENAMES
    above."""
    return ASSET_RENAMES.get((school, level, paper, year, qnum, slot),
                             default_path)


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
        ("RI", "H2", "P2", 2024),
        r"Fig\.\s*3\.1",
        "Fig. 4.1",
        "RI's mark scheme captions the Q4 kinetics graph 'Fig. 3.1' and the "
        "4(a)(ii) answer text refers to it by that name, but the figure belongs "
        "to Q4, whose question-paper figures are 4.1/4.2 (cf. handoff SS4 item "
        "14). Confirmed present in RI's own Word file, so it is their error, "
        "not a conversion artefact.",
        "user, 2026-09-18",
    ),
    (
        ("EJC", "H2", "P2", 2024),
        "Acidic conditions:\n\nBasic conditions:\n",
        "",
        "Q3(d)'s Latimer-diagram image (corrections.COMBINED_FIGURES already "
        "merges its two pictures into one crop) already labels 'Acidic "
        "conditions' and 'Basic conditions' inside the picture itself; the "
        "text-only lines duplicating those same labels read as a formatting "
        "defect once the diagram is in place, not real question content.",
        "user, 2026-09-26",
    ),
    (
        ("EJC", "H2", "P2", 2024),
        # The CENTRE sentinel ("\x00C\x00", oxml.py) precedes this paragraph
        # because Word centres it -- matched literally rather than imported,
        # since a text-substitution table has no other reason to depend on
        # oxml.py, and the byte sequence itself will not change.
        "\n\x00C\x00<b>Question 4 starts on the next page\\.<br></b>",
        "",
        "A literal page-turn note typed into the docx body at the end of "
        "Q3(e)(iii) (not PDF footer furniture -- it is real body text), "
        "meaningless once questions are not paginated the same way in the "
        "app as in the printed paper.",
        "user, 2026-09-26",
    ),
]


def apply(html: str, scope: tuple | None = None) -> tuple[str, list[str]]:
    """Return (corrected_html, [descriptions of what changed]).

    `scope` is (school, level, paper, year), matching a CORRECTIONS entry's
    own scope. An entry scoped to a DIFFERENT paper is skipped -- see the
    module docstring for why this must not be optional. An entry with
    scope=None (safe on every paper) always runs, whatever `scope` is.
    """
    log = []
    for entry_scope, pattern, replacement, reason, who in CORRECTIONS:
        if entry_scope is not None and entry_scope != scope:
            continue
        new, n = re.subn(pattern, replacement, html)
        if n:
            log.append("%dx %s -> %r (%s; approved: %s)"
                       % (n, pattern, replacement, reason, who))
            html = new
    return html, log
