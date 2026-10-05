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
    # ASRJC 2024 H2 P1 (2026-10-02) ------------------------------------------
    ("ASRJC", "H2", "P1", 2024, 10): {
        1: "Reaction 1's arrow: an anchored zero-height line shape. Reactions "
           "1 and 2 are now snipped together as one picture, so the typed "
           "reaction-1 line is removed by MCQ_FIXUPS.",
        3: "Reaction 2 is ONE printed scheme (phenol + 3Br2 -> tribromophenol "
           "+ 3HBr, label 'reaction 2'): two structure objects, two text "
           "boxes and an arrow line, all floating. The user snips the whole "
           "scheme as ONE picture, so the structure objects and the shape "
           "group collapse onto a single placeholder (block #2).",
        4: "Part of reaction 2's scheme -- see #3.",
    },
    ("ASRJC", "H2", "P1", 2024, 11): {
        2: "The Boltzmann graph is ONE printed picture. Word stores it as an "
           "inline PNG plus a small 10 x 12 pt anchored shape and the parser "
           "counts two figures, but only one placeholder exists in the text. "
           "One asset (stem1) is the whole graph.",
    },
    ("ASRJC", "H2", "P1", 2024, 12): {
        2: "The gas-syringe diagram is ONE printed picture: an inline PNG "
           "(the syringe) plus three floating text-box labels ('sealed end', "
           "'gaseous mixture', 'piston'). The user snips them together, so "
           "the PNG's placeholder collapses onto the label group's (block #1).",
    },
    ("ASRJC", "H2", "P1", 2024, 18): {
        2: "The four structures are snipped as ONE picture (numbers 1-4 "
           "included): one placeholder, block #1. (user, 2026-10-02)",
        3: "see #2.", 4: "see #2.",
    },
    ("ASRJC", "H2", "P1", 2024, 22): {
        2: "The three equations are snipped as ONE picture (numbers 1-3 "
           "included): one placeholder, block #1. (user, 2026-10-02)",
        3: "see #2.",
    },
    ("ASRJC", "H2", "P1", 2024, 24): {
        2: "Both structures are snipped as ONE picture (labels X and Y "
           "included): one placeholder, block #1. (user, 2026-10-02)",
    },
}


def dropped_blocks(school, level, paper, year, qnum) -> dict:
    """{block ordinal: reason} for figures deliberately not placed."""
    return DROPPED_FIGURES.get((school, level, paper, year, qnum), {})


# GLYPH FIGURES (MCQ question papers)
# -----------------------------------
# A "figure" that is really a TYPOGRAPHIC CHARACTER drawn as a picture: the
# reaction / equilibrium arrow set as a tiny ChemWindow (WMF) object or a
# zero-height anchored line shape beside the equation text. Uploading a 30 x 6
# pt crop for it is pointless and loses searchability; the real character is
# typed instead, in place, so the equation stays ONE paragraph.
#
# Keyed like DROPPED_FIGURES -- (school, level, paper, year, qnum) -- to
# {block ordinal: glyph}, where "block ordinal" counts every non-option,
# non-equation figure in document order (the SAME numbering DROPPED_FIGURES
# uses, and a glyph figure counts in it, so adding one never renumbers a drop).
# A glyph figure gets no asset and no `div.fig`: render_questions substitutes
# the character inline. Declared per question, after looking at the rendered
# page -- never inferred from a figure's size.
GLYPH_FIGURES = {
    # ASRJC 2024 H2 P1 (2026-10-02). Every one of these was checked against the
    # rendered Word PDF: each is a plain arrow sitting inside an equation line.
    ("ASRJC", "H2", "P1", 2024, 9):  {1: "\u2192", 2: "\u2192", 3: "\u2192", 4: "\u2192"},
    ("ASRJC", "H2", "P1", 2024, 12): {3: "\u21cc"},
    ("ASRJC", "H2", "P1", 2024, 13): {1: "\u21cc", 2: "\u21cc", 3: "\u21cc", 4: "\u21cc"},
    ("ASRJC", "H2", "P1", 2024, 14): {1: "\u2192", 2: "\u2192", 3: "\u2192", 4: "\u2192"},
}


def glyph_blocks(school, level, paper, year, qnum) -> dict:
    """{block ordinal: character} for figures typed as a glyph, not placed."""
    return GLYPH_FIGURES.get((school, level, paper, year, qnum), {})


# MCQ FIXUPS
# ----------
# Per-question regex touch-ups applied to an MCQ row's `content_html` and
# `content_text` AFTER rendering -- for the handful of things a registry of
# dropped/typed figures cannot express (a label to delete, a gap to re-space).
# Each entry is (scope_with_qnum, field, pattern, replacement, expected_count,
# reason). `expected_count` is MANDATORY and enforced by the driver: a fixup
# that matches 0 or 3 times when 1 was expected stops the run, because a silent
# miss is exactly how a "fix" ships unapplied. Every application is printed
# into anomalies.txt.
_AS = ("ASRJC", "H2", "P1", 2024)
MCQ_FIXUPS = [
    # --- Q10: reactions 1 and 2 ------------------------------------------------
    (_AS + (10,), "html",
     r'<p class="c">BrO.*?reaction 1</p>\n', "", 1,
     "Reactions 1 AND 2 are snipped together as ONE picture (labels "
     "'reaction 1' / 'reaction 2' included; user, 2026-10-02), so the typed "
     "reaction-1 line is removed and the single placeholder stands for both."),
    (_AS + (10,), "html",
     r'<p class="c">\x00C\x00\t+reaction 2</p>\n?', "", 1,
     "'reaction 2' is the right-hand label of the reaction-2 scheme; the user "
     "snips the scheme WITH its label, so the typed duplicate is removed."),
    (_AS + (10,), "text", r"BrO3.*?reaction 1 ", "", 1,
     "the reaction-1 equation is inside the combined snip."),
    (_AS + (10,), "text", r"reaction 2 ", "", 1,
     "same label, in the search text."),
    # --- Q18 / Q22 / Q24: figure rows snipped as one picture (user, 2026-10-02)
    (_AS + (18,), "html", r'<table class="qt center">.*?</table>\n',
     '<div class="fig">figure</div>\n', 1,
     "the four structures and their numbers 1-4 are ONE snip."),
    (_AS + (18,), "text", r"\? 1 2 3 4 A ", "? A ", 1, "figure-borne numbers."),
    (_AS + (22,), "html", r'<table class="qt center">.*?</table>\n',
     '<div class="fig">figure</div>\n', 1,
     "the three equations and their numbers 1-3 are ONE snip."),
    (_AS + (22,), "text", r"\? 1 2 3 A ", "? A ", 1, "figure-borne numbers."),
    (_AS + (24,), "html", r'<table class="qt">.*?</table>\n',
     '<div class="fig">figure</div>\n', 1,
     "the two structures and their labels X / Y are ONE snip."),
    (_AS + (24,), "text", r"\? XY Test", "? Test", 1, "figure-borne labels."),
    # --- Q5: two bullet statements ------------------------------------------------
    (_AS + (5,), "html",
     r'<p class="qstem">(the gas in the vessel was heated[^<]*)</p>\n'
     r'<p class="qstem">(the vessel was filled with .*?)</p>',
     '<ul class="stmts"><li>\\1</li><li>\\2</li></ul>', 1,
     "the two changes are Word bullet paragraphs (w:numPr) -- questions.py has "
     "no numPr-list merging (style-guide.md section 9), so they came out as "
     "bare paragraphs with the bullets lost. style-guide section 2: bullets "
     "are ul.stmts."),
    # --- Q12: the equilibrium line ---------------------------------------------
    (_AS + (12,), "html",
     r"(2H<sub>2</sub>S\(g\))\s{4,}(\u2206<i>H</i>)<sub>\s*</sub>(&gt; 0)",
     "\\1&emsp;&emsp;\\2 \\3", 1,
     "an 11-space run hand-aligning the enthalpy label (HTML would collapse it "
     "to one space) and an empty <sub>."),
    # --- Q13: four equilibria, each with a hand-aligned K label ------------------
    (_AS + (13,), "html", r'<p class="qstem">(?=Ag[CI])', '<p class="c">', 4,
     "the four equilibrium equations are centred (user, 2026-10-02); "
     "style-guide section 2: a centred equation is p.c."),
    (_AS + (13,), "html", r"<i><sup>(\s*)</sup></i>", "\\1", 2,
     "italic superscripts holding ONLY spaces (the alignment gap itself, "
     "typed into a <sup>); the spaces are kept, the empty tags go."),
    (_AS + (13,), "html", r"<i>(\s+)K</i>", "\\1<i>K</i>", 1,
     "a run of spaces typed INSIDE the italic K."),
    (_AS + (13,), "html", r"\s{4,}(<i>K</i>)", "&emsp;&emsp;\\1", 4,
     "hand-aligned K labels (Ksp, Kc1, Ksp, Kc2) -- runs of 8-45 spaces that "
     "HTML would collapse."),
    (_AS + (13,), "html", r"(</sub>)\s{4,}</p>", "\\1</p>", 1,
     "trailing spaces after the first K label."),
]


def mcq_fixups(school, level, paper, year, qnum) -> list:
    """[(field, pattern, replacement, expected_count, reason)] for one question."""
    return [e[1:] for e in MCQ_FIXUPS if e[0] == (school, level, paper, year, qnum)]


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
    # ACJC 2024 H2 P2 (2026-09-29). Four owners whose parsed "figures" are NOT
    # pictures the paper prints, each confirmed by rendering the printed page:
    ("ACJC", "H2", "P2", 2024, 1, "(b)(ii)"):
        "One EMPTY Word text box (34 x 33 pt, no text, no fill) anchored under "
        "1(b)(ii). The printed page shows nothing there -- the student is told "
        "to sketch ON Fig. 1.1, printed once, in 1(b)(i). Not a figure.",
    ("ACJC", "H2", "P2", 2024, 6, None):
        "Four references to the SAME 18 x 15.85 pt EMF (media/image10.emf) -- "
        "the reversible-arrow glyph sitting between the two sides of each "
        "equation in Table 6.2 (the four rows). A character drawn as a "
        "picture, not a figure: the arrows are typed as U+21CC by the "
        "CORRECTIONS entry below, which is why the placeholders go.",
    ("ACJC", "H2", "P2", 2024, 6, "(e)(iv)"):
        "The same reversible-arrow EMF (media/image10.emf) as Table 6.2, here "
        "in the H2CO3 + CO3(2-) <=> 2HCO3(-) equation. Typed as U+21CC.",
    ("ACJC", "H2", "P2", 2024, 6, "(f)"):
        "Two references to media/image11.wmf -- the capital-sigma glyphs in "
        "'dS = SUM m dS(products) - SUM n dS(reactants)', set as pictures. "
        "Typed as U+03A3 by the CORRECTIONS entry below.",
    # ACJC 2024 H2 P3 (2026-10-01). Reversible-arrow glyphs set as 15 x 10 pt
    # Word drawing GROUPS (wordprocessingGroup) beside the text, each confirmed
    # against the printed page. A character drawn as a picture, not a figure:
    # typed as U+21CC by the CORRECTIONS entries below (same treatment as ACJC
    # 2024 H2 P2 Table 6.2).
    ("ACJC", "H2", "P3", 2024, 1, "(b)"):
        "One 15 x 10 pt drawing group = the reversible arrow in 'equation 1' "
        "([Al(H2O)6]3+ + EDTA4- <=> [Al(EDTA)]- + 6H2O). Typed as U+21CC.",
    ("ACJC", "H2", "P3", 2024, 4, "(a)"):
        "One 15 x 10 pt drawing group = the reversible arrow in the zincate "
        "half-equation Zn(OH)4 2- + 2e- <=> Zn + 4OH-. Typed as U+21CC.",
    ("ACJC", "H2", "P3", 2024, 4, "(b)(i)"):
        "One 15 x 10 pt drawing group = the reversible arrow in "
        "2SO2 + O2 <=> 2SO3. Typed as U+21CC.",
    ("ACJC", "H2", "P3", 2024, 5, None):
        "One 15 x 10 pt drawing group = the reversible arrow in the OXO "
        "equation CH2=CH2 + CO + H2 <=> CH3CH2CHO. Typed as U+21CC.",
}


# LEAD-IN MOVES (structured papers)
# ---------------------------------
# A paper prints a passage AFTER one part's "[n]" and BEFORE the next part's
# label -- prose that introduces the NEXT part(s) -- but Word keeps it in the
# same table cell as the part above, so the parser files it under that part,
# below its mark. ACJC 2024 H2 P2 Q6: the "Process 2 is thought to proceed via
# two steps..." passage sits under (b)(ii)'s [2], and the coral-skeleton passage
# under (c)(iii)'s [1], though each introduces what follows. Declared here, the
# same way a dropped figure is: the lines after the part's LAST mark badge move
# to the START of the next part (the reading order the paper prints; the label
# then sits beside the first sentence of the passage, as any part's intro does).
# Refused (logged, nothing moved) when the tail holds a figure or table, since
# moving one would change which part owns its asset. Keyed
# (school, level, paper, year, qnum, part_label of the part the tail is now in).
LEADIN_MOVES = {
    # ASRJC 2024 H2 P2 (2026-10-03). Each passage is printed between one
    # part's [n] and the next part's label.
    ("ASRJC", "H2", "P2", 2024, 5, "(a)(ii)"):
        "'The hydrogen required for the Haber-Bosch process...' with equations "
        "5.1 and 5.2 introduces (a)(iii) and (a)(iv).",
    ("ASRJC", "H2", "P2", 2024, 5, "(c)(ii)"):
        "'The standard enthalpy change of reaction...' and the Gibbs-energy "
        "table introduce (c)(iii).",
    ("ASRJC", "H2", "P2", 2024, 5, "(d)(ii)"):
        "'It is suggested that a molten salt mixture...' introduces (d)(iii).",
    ("ACJC", "H2", "P2", 2024, 6, "(b)(ii)"):
        "'Process 2 is thought to proceed via the two steps...' introduces "
        "(b)(iii) (mechanism) and (b)(iv) (rate-determining step); printed "
        "between (b)(ii)'s [2] and (b)(iii).",
    ("ACJC", "H2", "P2", 2024, 6, "(c)(iii)"):
        "The two coral-skeleton paragraphs introduce (d)-(f); printed between "
        "(c)(iii)'s [1] and (d).",
}


def leadin_move_reason(school, level, paper, year, qnum, part_label) -> str | None:
    return LEADIN_MOVES.get((school, level, paper, year, qnum, part_label))


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


# GLYPH PICTURES (structured papers)
# ----------------------------------
# A reaction arrow the source sets as a tiny Word OBJECT picture between the two
# sides of an equation. The picture is NOT a figure: the sentinel is replaced by
# the real character before lead-in moves, reconcile() and asset planning, so no
# asset is planned for it. (scope, regex, replacement, reason). Each pattern is
# anchored on the chemistry either side so it can never hit a real figure.
_A = ("ASRJC", "H2", "P2", 2024)
GLYPH_PICTURES = [
    (_A, r"(O<sub>2</sub>\(g\)) \x00FIG\x00 (2POC)", "\\1 \u2192 \\2",
     "Q1(c) equation 1.1 forward arrow"),
    (_A, r"(N<sub>2</sub>\(g\)) \x00FIG\x00(2NH<sub>3</sub>\(g\))\s{4,}(\u2206)",
     "\\1 \u21cc \\2\u2003\u2003\u2003\\3",
     "Q5(a) equilibrium arrow (rendered page shows the harpoon pair); the 29-space gap before dH is the source's own alignment"),
    (_A, r"(H<sub>2</sub>O\(g\)) \x00FIG\x00(CO\(g\))", "\\1 \u2192 \\2",
     "Q5 equation 5.1 forward arrow"),
    (_A, r"(H<sub>2</sub>O\(g\)) \x00FIG\x00(CO<sub>2</sub>)", "\\1 \u2192 \\2",
     "Q5 equation 5.2 forward arrow"),
    (_A, r"(2LiOH) \x00FIG\x00 (2Li)", "\\1 \u2192 \\2", "Q5(c) stage 1 arrow"),
    (_A, r"(N<sub>2</sub>) \x00FIG\x00 (2Li<sub>3</sub>N)", "\\1 \u2192 \\2", "Q5(c) stage 2 arrow"),
    (_A, r"(3H<sub>2</sub>O) \x00FIG\x00(3LiOH)", "\\1 \u2192 \\2",
     "Q5(c) and (c)(iii) stage 3 arrow"),
    (_A, r"(\u00bd?H<sub>2</sub>O)\s+\x00FIG\x00 (LiOH)", "\\1 \u2192 \\2",
     "Q5(d) equation 5.3 arrow"),
    (("ASRJC", "H2", "P3", 2024),
     r"(O<sub>2</sub>\(g\)) \x00FIG\x00 (2SO<sub>3</sub>\(g\))", "\\1 \u21cc \\2",
     "Q2(c) stage I equilibrium arrow (a drawn harpoon pair in the source)"),
]


def apply_glyph_pictures(html: str, scope: tuple | None = None):
    log = []
    for sc, pat, rep, why in GLYPH_PICTURES:
        if sc != scope:
            continue
        html, n = re.subn(pat, rep, html)
        if n:
            log.append("%dx glyph picture typed: %s" % (n, why))
    return html, log


_P3 = ("ASRJC", "H2", "P3", 2024)

#: Pictures that sit INSIDE a sentence, placed in the markup as
#: `<img data-asset="FILE.png">` (matched by filename) rather than as a block
#: `div.fig` placeholder. They still need an `question_assets` row, but with an
#: ordinal AFTER every block figure of the same question: the frontend fills
#: `div.fig` placeholders from ALL of a question's stem assets in ordinal order,
#: so an inline asset in the middle of the sequence would be consumed by a block
#: placeholder. Keyed by scope; value is [(qnum, part_label, slot)].
INLINE_ASSETS = {
    ("ASRJC", "H2", "P3", 2024): [(1, "(e)(ii)", "eii2")],
}


def inline_assets(school, level, paper, year, qnum) -> list:
    return [(part, slot) for (q, part, slot)
            in INLINE_ASSETS.get((school, level, paper, year), []) if q == qnum]


CORRECTIONS = [
    # ---- ASRJC 2024 H2 P3 (2026-10-04)
    (_P3, r"[ \t]*<br>[ \t]*", " ",
     "Soft line breaks (w:br) typed to wrap a sentence at the printed margin (1(b), 1(d)(ii), 1(d)(iii), "
     "2(c)(iii), 3(c), 3(c)(i), 4(a), 4(b), 4(d), 5(b), 5(b)(iii), 5(c)(iii)). No genuine break uses <br> here.",
     "housekeeping, same as ASRJC P2, 2026-10-04"),
    (_P3, r"(\d) (\u00b0C)", "\\1&nbsp;\\2",
     "Q5(b): keep a number and its degree-Celsius unit on one line (same rule the user set on ASRJC P2).",
     "housekeeping, 2026-10-04"),
    (_P3, r"(stage <b>I</b>) {10,}(2SO)", "\\1\u2003\u2003\u2003\\2",
     "Q2(c): the 30-space gap between 'stage I' and the equation is the source's own alignment; "
     "browsers collapse it, so it becomes three em-spaces (same treatment as ASRJC P2 Q5(a)).",
     "housekeeping, 2026-10-04"),
    (_P3, r"<i>K</i><sub>c\x00FIG\x00\.\s*</sub>\[1\]<sub>\s*</sub>",
     '<i>K</i><sub>c</sub>(<span class="frac"><span class="fnum">1</span><span class="fden">RT</span></span>). '
     '<span class="mk">[1]</span>',
     "2(c)(ii): Kp = Kc(1/RT) is a MathType Equation.3 object (no text layer) sitting inside a run of "
     "subscript-formatted whitespace, which also swallowed the [1] mark. Short and simple, so it is typed "
     "as house .frac markup (style-guide SS3) instead of cropped; R and T upright, as printed.",
     "editorial call, 2026-10-04; confirm"),
    (_P3, r"(<b>Table 2\.2</b>\n)<table class=\"qt\">[^\n]*</table>", "\\1\x00C\x00\x00FIG\x00",
     "2(b) Table 2.2: three structures sit in picture cells of a four-column table (the renderer cannot place "
     "a figure inside a cell). The whole table body is snipped as ONE image; the 'Table 2.2' caption stays typed.",
     "whole-table snip, precedent ACJC 2024 H2 P3 Q2(b) Table 2.1 (user, 2026-10-01); confirm"),
    (_P3, r"<table class=\"qt\"><tr><td>\x00FIG\x00</td><td>\x00FIG\x00</td><td>\x00FIG\x00</td></tr>"
          r"<tr><td>benzoyl chloride</td><td>chlorobenzene</td><td>3-chloro-1-phenylbutane</td></tr></table>",
     "\x00C\x00\x00FIG\x00",
     "3(b): the three structures and their names sit in a borderless 2-row table; snipped as ONE image that "
     "already carries the names (style-guide SS6 bare-image rule), so the typed name row goes.",
     "combined-snip convention (ASRJC P2 2(b)); confirm"),
    (_P3, r"(<b>Table 5\.1</b>\n)<table class=\"qt\">[^\n]*</table>", "\\1\x00C\x00\x00FIG\x00",
     "5(c) Table 5.1: the three equations are picture cells; the whole table body (header row, step "
     "numbers and equations) is snipped as ONE image; the 'Table 5.1' caption stays typed.",
     "whole-table snip, precedent ACJC 2024 H2 P3 Q2(b) Table 2.1 (user, 2026-10-01); confirm"),
    (_P3, r"\n<b>\s+Z\s+</b>(<span class=\"mk\">\[1\]</span>)", "\\n\x00C\x00<b>Z</b> \\1",
     "4(d)(ii): the compound label Z is padded with ~60 literal spaces to centre it under the structure; "
     "typed as a centred label with the mark after it.",
     "housekeeping, 2026-10-04"),
    (_P3, r"(following structure\. )\n\x00FIG\x00\n(The C<sub>2</sub>O<sub>4</sub><sup>2\u2013</sup> ligand is "
          r"represented using) O\s+O\.",
     '\\1\n\\2 <img data-asset="ASRJC_H2_P3_Q1_eii2_2024.png" alt="">.',
     "1(e)(ii): the O-arc-O ligand symbol is a small drawing floating over typed 'O   O'; Word anchors it in the "
     "PREVIOUS paragraph, so its placeholder came out before the sentence it belongs in. It becomes an INLINE "
     "image (matched by filename, planned via corrections.INLINE_ASSETS) and the typed 'O O' goes.",
     "user's snip of the symbol replaces the typed letters; confirm"),
    (_P3, "\u0399", "I",
     "2(c)(iii) 'reaction in stage I': the roman numeral I is typed in the Symbol font (w:sym F049 = "
     "Greek capital iota). Rendered page shows a bold upright I, like the other 'stage I' mentions, "
     "so it is converted to Latin I for search and consistency.",
     "housekeeping, 2026-10-04"),
    # ---- ASRJC 2024 H2 P2 (2026-10-03)
    (_A, r"[ \t]*<br>[ \t]*", " ",
     "Soft line breaks (w:br) typed to wrap a sentence at the printed margin: "
     "1(c)(iii) 'in / equation 1.1', 2(b)(ii) 'at / pH 3.0', 2(c)(ii) 'structure / of V', "
     "3(b) 'listed in / Table 3.2', 4(c)(i) 'and / (C6H5)3C-Cl'. No genuine break uses <br> here.",
     "housekeeping, 2026-10-03"),
    (_A, r"\n\x00C\x00glutamic acid\n\x00C\x00tyrosine\n\x00C\x00\x00FIG\x00\n\x00C\x00\x00FIG\x00",
     "\n\x00C\x00\x00FIG\x00",
     "2(b): the two amino-acid structures are snipped as ONE image that already carries the "
     "names 'glutamic acid' / 'tyrosine' as pixels; typed captions and the second placeholder go "
     "(style-guide SS6 bare-image rule).",
     "user's combined-snip convention; confirm 2026-10-03"),
    (_A, r"\n\x00C\x00<b>U</b>\n\x00C\x00<b>V</b> (<span class=\"mk\">\[2\]</span>)",
     '\n<table class="qt"><tr><td><b>U</b></td><td><b>V</b></td></tr>'
     '<tr><td>&nbsp;<br>&nbsp;<br>&nbsp;</td><td>&nbsp;<br>&nbsp;<br>&nbsp;</td></tr></table> \\1',
     "2(b)(ii): the printed answer box is a two-column table headed U and V; the parser "
     "flattened it to two stacked paragraphs.",
     "housekeeping, 2026-10-03"),
    (_A, r"\x00FIG\x00\n   Nicotinic acid\n\x00C\x00<b>E</b>\n\x00FIG\x00\nNicotinamide",
     "\x00C\x00\x00FIG\x00",
     "4(b): the whole two-step scheme (nicotinic acid, step 1, box E, step 2 / NH3, nicotinamide) "
     "is ONE printed picture with its labels; snipped as one image, typed labels dropped.",
     "bare-image rule; confirm 2026-10-03"),
    (_A, r"\n\x00C\x00<b>T</b>(?=$)", "",
     "Q2 stem: the user's snip of the tetrapeptide includes the bold label T as pixels, so the typed caption is dropped (bare-image rule).",
     "user, 2026-10-03"),
    (_A, r"(\d) (\u00b0C)", "\\1&nbsp;\\2",
     "Q1(b)/Q5(a): keep a number and its degree-Celsius unit on one line (user, 2026-10-04: '106' and '\u00b0C' split across lines).",
     "user, 2026-10-04"),
    (_A, r"</li></ul>\n<ul class=\"stmts\"><li>", "</li><li>",
     "4(c)(ii): the two bullets are one list.", "housekeeping, 2026-10-03"),
    # ---- ACJC 2024 H2 P2 (2026-09-29): characters the source draws as pictures
    # Word set the reversible arrow and the capital sigma as tiny EMF/WMF
    # PICTURES anchored beside the text (the text itself keeps a run of spaces
    # where the picture sits), exactly as ACJC 2024 H2 P1's Q13/Q14 did. The
    # pictures are dropped (DROPPED_PART_FIGURES) and the real characters typed:
    # searchable, and no pixel-sized crop to upload. Each was checked against the
    # rendered page (Table 6.2, 6(e)(iv), 6(f)), not inferred from the docx.
    (
        ("ACJC", "H2", "P2", 2024),
        r"[ \t]*<br>[ \t]*",
        " ",
        "Four SOFT line breaks (w:br) the author typed to wrap a sentence at "
        "the printed page's right margin -- Q1(a)(iv) 'are / 2300 kJ...', "
        "Q2 intro 'converted to / trans-2-...', Q2(b) 'between / 2-methyl...', "
        "Q6(c)(iii) 'in / Table 6.2'. In the app the column is a different "
        "width, so each would leave a ragged mid-sentence break. No genuine "
        "line break in this paper uses <br> (checked: only these four exist).",
        "housekeeping, 2026-09-29",
    ),
    (
        ("ACJC", "H2", "P2", 2024),
        r"<b></b>|<i>\s+</i>",
        "",
        "Empty <b>/<i> shells left where a picture-only run (the arrow "
        "pictures in Table 6.2) or a run of answer-line spaces (Q3(a)(ii)) "
        "sat inside formatting.",
        "housekeeping, 2026-09-29",
    ),
    (
        ("ACJC", "H2", "P2", 2024),
        r"(?<=\((?:g|l)\))[ \t]{4,}(?=[A-Z])",
        " \u21cc ",
        "Table 6.2's four equations: the reversible arrow is a picture sitting "
        "in an 8-space gap after '(g)'/'(l)' (CO2(g) <=> CO2(aq), etc.).",
        "carried over from ACJC 2024 H2 P1 Q13/Q14 (user-approved there); flagged for confirmation here, 2026-09-29",
    ),
    (
        ("ACJC", "H2", "P2", 2024),
        r"(?<=</sup>)[ \t]{4,}(?=2HCO<sub>3</sub>)",
        " \u21cc ",
        "6(e)(iv): 'H2CO3 + CO3(2-) <=> 2HCO3(-)' -- the arrow is a picture in "
        "the space between the two sides.",
        "carried over from ACJC 2024 H2 P1 Q13/Q14 (user-approved there); flagged for confirmation here, 2026-09-29",
    ),
    (
        ("ACJC", "H2", "P2", 2024),
        r"= m(∆<i>S</i><sub>f</sub><sup>o</sup>\(products\)) − n(∆<i>S</i>"
        r"<sub>f</sub><sup>o</sup>\(reactants\))",
        "= \u03a3m\\1 − \u03a3n\\2",
        "6(f): the two capital-sigma glyphs in the entropy-change formula are "
        "pictures (media/image11.wmf), so the extraction read "
        "'= m dS(products) - n dS(reactants)' with both sigmas missing.",
        "carried over from ACJC 2024 H2 P1 Q13/Q14 (user-approved there); flagged for confirmation here, 2026-09-29",
    ),
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
    (
        ("EJC", "H2", "P3", 2024),
        # Same convention as the "Question 4 starts on the next page" entry
        # above for EJC 2024 H2 P2 -- this school's own template prints a
        # literal page-turn note as real body text (not PDF footer
        # furniture) wherever a question straddles a page break. No leading
        # "\n" here (unlike that entry): this one is Q3's very own paragraph
        # between (d) and (e), not glued onto a preceding part's text.
        "\x00C\x00<b>Question 3 continues on the next page\\.<br></b>",
        "",
        "A literal page-turn note typed into the docx body between Q3(d) "
        "and Q3(e), meaningless once questions are not paginated the same "
        "way in the app as in the printed paper.",
        "user, 2026-09-27",
    ),
    (
        ("EJC", "H2", "P3", 2024),
        # Every OTHER figure caption in this paper's docx is its own
        # paragraph with jc="center" (confirmed by direct inspection of all
        # 10: Fig. 1.1-1.4, 2.1, 3.1, 3.2, 4.1, 5.1's own two occurrences).
        # This one paragraph -- "Fig. 5.1" with its "[2]" mark allocation
        # glued onto the same line -- is jc="both" (justify) instead, a
        # one-off typo in EJC's own Word file, not a conversion artefact.
        # Matched AFTER `_write_mark` has already wrapped "[2]" (parts_flow's
        # per-paragraph pass runs before extract_parts.py calls corrections
        # .apply()), so the pattern targets the <span class="mk"> form, not
        # the bare "[2]" oxml.paragraph_html() would emit on its own.
        # Prepending the CENTRE sentinel here (oxml.py never added it, since
        # the source paragraph itself isn't centred) makes it render the
        # same way as every other caption in the paper.
        '\n<b>\tFig\\. 5\\.1</b>\t<span class="mk">\\[2\\]</span>',
        '\n\x00C\x00<b>\tFig. 5.1</b>\t<span class="mk">[2]</span>',
        "Q5(b)(iii)'s 'Fig. 5.1' caption paragraph is typed jc=\"both\" in "
        "EJC's own Word file, unlike every other caption in this paper "
        "(all jc=\"center\"); centring it here matches the rest.",
        "user, 2026-09-27",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"Eqm 2 and 4",
        "Equilibria 2 and 4",
        "Q7 statement 2 abbreviates 'Equilibria' as 'Eqm' (singular form used "
        "for a plural referent, referring to equilibria 2 and 4 by the "
        "numbering scheme (∆G1..∆G4) set up earlier in the same answer) -- a "
        "short form in the source, spelled out per house style.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"\beqm \(2\)",
        "equilibrium (2)",
        "Q14 abbreviates 'equilibrium' as 'eqm' when referring back to its "
        "own numbered equilibrium (2) (the H2C2O4 dissociation) -- a short "
        "form in the source, spelled out per house style.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"\beqm \(1\)",
        "equilibrium (1)",
        "Q14 abbreviates 'equilibrium' as 'eqm' when referring back to its "
        "own numbered equilibrium (1) (the CaC2O4 dissolution) -- a short "
        "form in the source, spelled out per house style.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"solubitlity",
        "solubility",
        "Q16 option D: genuine spelling typo in the source document "
        "('solubitlity' for 'solubility').",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"↑es",
        "increases",
        "Q17 statements 1 and 2 use the raw up-arrow-plus-'es' shorthand "
        "('atomic radius ↑es', 'number of electrons ↑es') in place of the "
        "word -- the arrow glyph itself (symbols.py SYMBOL['F0AD']) is a "
        "legitimate, evidenced transcription of the source's Symbol-font "
        "character, but reads as a typo/short form once rendered as running "
        "prose, so it is spelled out per house style.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"↓es",
        "decreases",
        "Q17 statements 2 and 3 use the raw down-arrow-plus-'es' shorthand "
        "('volatility ↓es', 'E⦵(X2|X–) ↓es', 'Oxidising power ... ↓es') in "
        "place of the word -- same rationale as the '↑es' entry above.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"↓ing",
        "decreasing",
        "Q17 statement 1 uses the raw down-arrow-plus-'ing' shorthand "
        "('X–X bond energy ↓ing down the group') in place of the word -- "
        "same rationale as the '↑es' entry above.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"↑ polarisability",
        "increased polarisability",
        "Q17 statement 2 uses the raw up-arrow shorthand ('resulting in ↑ "
        "polarisability of electron cloud') in place of the word -- same "
        "rationale as the '↑es' entry above.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"a ↓ in tendency",
        "a decrease in tendency",
        "Q17 statement 3 uses the raw down-arrow shorthand ('there is a ↓ "
        "in tendency for X2 to be reduced') in place of the word -- same "
        "rationale as the '↑es' entry above.",
        "user, 2026-09-28",
    ),
    (
        ("EJC", "H2", "P1", 2024),
        r"tadical",
        "radical",
        "Q19 option C: genuine spelling typo in the source document "
        "('tadical' for 'radical').",
        "user, 2026-09-28",
    ),
    (
        ("ACJC", "H2", "P1", 2024),
        r"I<sup>-</sup>\)",
        "I<sup>−</sup>)",
        "Q28's explanation types the iodide charge in 'E-o(I2/I-)' with a "
        "plain ASCII hyphen, unlike every other singly-charged anion in the "
        "same document (MnO4-, X-, Y-, all typed with the proper U+2212 "
        "minus, confirmed by the raw run text) -- the same class of defect "
        "as RI 2024 H2 P1's Q11 wrong-minus-glyph fix (HANDOFF.md SS13), "
        "found the same way: a visual comparison against the surrounding "
        "consistent usage, not any charset gate (which is blind to a "
        "correct character used in the wrong position when the right one "
        "exists elsewhere in the document).",
        "user, 2026-09-28",
    ),
    # ---- ACJC 2024 H2 P3 (2026-10-01) ------------------------------------
    # Characters the source draws as pictures -> real characters (see
    # DROPPED_PART_FIGURES); each sits in a run of spaces where the picture was.
    (
        ("ACJC", "H2", "P3", 2024),
        r"(EDTA<sup>4\u2212</sup>\(aq\))[ \t]{4,}(\[A<i class=\"el\">l</i>\(EDTA\))",
        "\\1 \u21cc \\2",
        "Q1(b) equation 1: the reversible arrow is a picture in the gap "
        "between EDTA4-(aq) and [Al(EDTA)]-(aq).",
        "same treatment as ACJC 2024 H2 P2 Table 6.2 (user-approved there); flagged for confirmation here, 2026-10-01",
    ),
    (
        ("ACJC", "H2", "P3", 2024),
        r"(2e<sup>\u2212</sup>)[ \t]{4,}(Zn\(s\))",
        "\\1 \u21cc \\2",
        "Q4(a): reversible arrow picture in the zincate half-equation.",
        "same treatment as ACJC 2024 H2 P2 Table 6.2 (user-approved there); flagged for confirmation here, 2026-10-01",
    ),
    (
        ("ACJC", "H2", "P3", 2024),
        r"(O<sub>2</sub>\(g\))[ \t]{4,}(2SO<sub>3</sub>)",
        "\\1 \u21cc \\2",
        "Q4(b)(i): reversible arrow picture in 2SO2 + O2 <=> 2SO3.",
        "same treatment as ACJC 2024 H2 P2 Table 6.2 (user-approved there); flagged for confirmation here, 2026-10-01",
    ),
    (
        ("ACJC", "H2", "P3", 2024),
        r"(H<sub>2</sub>\(g\))[ \t]{4,}(CH<sub>3</sub>CH<sub>2</sub>CHO\(g\))",
        "\\1 \u21cc \\2",
        "Q5 intro: reversible arrow picture in the OXO equation.",
        "same treatment as ACJC 2024 H2 P2 Table 6.2 (user-approved there); flagged for confirmation here, 2026-10-01",
    ),
    # Q1(d)(ii): the two "1." / "2." sub-items are a Word auto-numbered list
    # (numId 42, decimal). parts.py only groups BULLET lists, so the numbers
    # were lost and the two items ran together as plain paragraphs.
    (
        ("ACJC", "H2", "P3", 2024),
        r"(the amount of Cu atoms to cover <b>both</b> sides of the graphene "
        r"with a depth of 500 atoms)\n(the time required to achieve this "
        r"using a current of 5\.0 A\.\s*<span class=\"mk\">\[3\]</span>)",
        '<ol class="stmts"><li>\\1</li> <li>\\2</li></ol>',
        "Q1(d)(ii): restore the auto-numbered '1. / 2.' list as <ol class=stmts> "
        "(CSS for ol.stmts already exists in index.html).",
        "pending user confirmation, 2026-10-01",
    ),
    # Q3(d): the stem's equation 'R-COOH + Pb(CH3CO2)4 --Cu(CH3CO2)2--> alkene +
    # ...' is native Word shapes (a text box labelling an arrow line) laid over
    # a typed line. Typing it did not work in the app (user, 2026-10-01), so one
    # snip of the WHOLE equation line (slot d) replaces both: the typed
    # duplicate and the second placeholder are removed.
    (
        ("ACJC", "H2", "P3", 2024),
        r"\x00C\x00\x00FIG\x00R\u2013COOH \+ Pb\(CH<sub>3</sub>CO<sub>2</sub>\)<sub>4</sub>"
        r"[^\n]*?Pb\(CH<sub>3</sub>CO<sub>2</sub>\)<sub>2</sub>",
        "",
        "Q3(d): the typed equation line is replaced by a single picture of the "
        "whole equation (reactants, Cu(CH3CO2)2-labelled arrow, products).",
        "user, 2026-10-01 (typed version reverted to image)",
    ),
    # Standard-state symbol: Q3(a)(i) types U+A74A (oxml.py turns it into the
    # real plimsoll <sup class="pl-sym">), but every other question types a
    # plain superscript letter 'o' -- E(o), dG(o), dG(o)sol -- which renders as
    # a small circle with no bar. All 'o' superscripts in this paper are
    # standard-state marks (checked: Q1(d)(iii), Q4(a), Q4(a)(i)-(ii), Q5(c)(iv)).
    (
        ("ACJC", "H2", "P3", 2024),
        r"<sup>o</sup>",
        '<sup class="pl-sym">\u29b5</sup>',
        "Standard-state symbol typed as a superscript letter o; replaced with "
        "the same plimsoll markup oxml.py already emits for Q3(a)(i).",
        "user, 2026-10-01",
    ),
    # Q2(b) Table 2.1: snipped whole (header row, names, structures, pKb).
    (
        ("ACJC", "H2", "P3", 2024),
        r'<table class="qt"><tr><td>name</td><td>structure</td>.*?</table>',
        "\x00FIG\x00",
        "Q2(b) Table 2.1: the whole table is one picture (slot b).",
        "user, 2026-10-01",
    ),
    # Q3(d) Fig. 3.2: a 4-row step table whose cells hold six separate
    # native-shape pictures plus a few typed fragments. Annotating it is the
    # whole task ((d)(i) 'add five half arrows', (d)(ii) 'add two full arrows'),
    # so it is placed as ONE picture of the entire boxed figure.
    (
        ("ACJC", "H2", "P3", 2024),
        r'<table class="qt"><tr><td>step 1</td>.*?</table>',
        "\x00FIG\x00",
        "Q3(d) Fig. 3.2: the four-step table collapses into one picture of the "
        "whole figure (steps 1-4 with their labels).",
        "pending user confirmation, 2026-10-01",
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
