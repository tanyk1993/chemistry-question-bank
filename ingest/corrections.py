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
    # DHS 2024 H2 P1 (2026-10-10). Q14: the equilibrium arrow between
    # E(g) + F(g) and G(g) is a drawn arrow in its own paragraph; typed.
    ("DHS", "H2", "P1", 2024, 14): {1: "\u21cc"},
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


# CJC 2024 H2 P1 (2026-10-05) -------------------------------------------------
# Declared after looking at the rendered Word PDF, page by page (user supplied
# docx + Word PDF; the user snips every figure by hand).
_CJ = ("CJC", "H2", "P1", 2024)

_ONE_PICTURE = ("ONE printed picture: Word stores it as several floating "
                "shapes / text boxes (and, for Q30, a duplicated jpeg), so the "
                "parser counts several figures. The user snips it as ONE "
                "image; the first figure keeps the placeholder, the rest are "
                "dropped.")
DROPPED_FIGURES.update({
    (*_CJ, 3): {2: "Phenol and thiophenol are snipped as ONE picture WITH "
                    "their names and pK<sub>a</sub> captions, so the two "
                    "typed caption lines are removed by MCQ_FIXUPS."},
    (*_CJ, 8): {n: "Figure 1 and Figure 2 side by side: " + _ONE_PICTURE
                for n in range(2, 11)},
    (*_CJ, 15): {n: "The P-Q-R solubility graph: " + _ONE_PICTURE
                 for n in range(2, 10)},
    (*_CJ, 30): {n: "The absorbance graph with its two x-axes: " + _ONE_PICTURE
                 for n in range(2, 6)},
})
GLYPH_FIGURES.update({
    # an equilibrium arrow drawn as a shape sitting inside the equation line
    (*_CJ, 16): {1: "\u21cc"},
    (*_CJ, 29): {1: "\u21cc", 2: "\u21cc"},
})

# NO-OPTION-TEXT questions (flow-shape MCQ). The options A-D exist only as
# labels printed INSIDE a figure, so the question has no option paragraphs at
# all. CJC Q8: "which of the options A, B, C or D corresponds to the boiling
# point of element J?" -- A-D are marked points on Figure 2.
NO_OPTION_TEXT = {
    _CJ: {8},
}


# CJC 2026 H2 P1 (2026-10-25) -------------------------------------------------
# Declared after looking at the rendered Word PDF page by page. The user snips
# every figure by hand; this only says how many placeholders each question has.
_CJ26 = ("CJC", "H2", "P1", 2026)

# Q5's table of successive ionisation energies has its rows labelled A and B.
# That is stem DATA; the real options A-D are the four paragraphs after the
# statements. Without this the table is read as the option table.
DATA_TABLE_QUESTIONS = {_CJ26: {5}}

DROPPED_FIGURES.update({
    (*_CJ26, 9): {2: "The Boltzmann graph is ONE printed picture: the axes and "
                     "curves (block #1) and the two E<sub>a</sub> labels with "
                     "their dotted lines (block #2) are separate Word shapes. "
                     "The user snips them together; block #1 keeps the "
                     "placeholder."},
})
GLYPH_FIGURES.update({
    # the equilibrium arrow drawn as a shape group inside the Q18 equation line
    (*_CJ26, 18): {1: "\u21cc"},
})


_DB = "Use of the Data Booklet is relevant to this question."
_PLS = '<span class="stk post"><span><span class="pl-sym">\u29b5</span></span><span>%s</span></span>'
MCQ_FIXUPS.extend([
    # search text: table cells ran together
    (_CJ26 + (4,), "text", r"isomersboiling point / \u00b0C hexane68\.7 2\u2013methylpentane60\.0 "
     r"2,2\u2013dimethylbutane49\.7",
     "isomers | boiling point / \u00b0C hexane | 68.7 2\u2013methylpentane | 60.0 "
     "2,2\u2013dimethylbutane | 49.7", 1, "table cells run together in the search text."),
    (_CJ26 + (5,), "text", r"A5801820274011600148001840023300 B9402050297041406590788014900",
     "A | 580 | 1820 | 2740 | 11600 | 14800 | 18400 | 23300 "
     "B | 940 | 2050 | 2970 | 4140 | 6590 | 7880 | 14900", 1,
     "table cells run together in the search text."),
    (_CJ26 + (18,), "text", r"metal sulfideKsp / mol2 dm\u20126 PbS9\.04 \u00d7 10\u201229 FeS4\.90 \u00d7 10\u201218",
     "metal sulfide | Ksp / mol2 dm\u20126 PbS | 9.04 \u00d7 10\u201229 FeS | 4.90 \u00d7 10\u201218", 1,
     "table cells run together in the search text."),
    # Q8: the standard-state sign sits OVER the f / c subscript, as printed
    (_CJ26 + (8,), "html", r"<i><sup>\u29b5 </sup></i><sub>f </sub>", _PLS % "f", 3,
     "standard-state sign stacked over the subscript f, as printed."),
    (_CJ26 + (8,), "html", r"<i><sup>\u29b5 </sup></i><sub>c </sub>", _PLS % "c", 1,
     "standard-state sign stacked over the subscript c, as printed."),
    (_CJ26 + (8,), "text", r"\u29b5 f \(", "\u29b5f (", 3, "stray space in the search text."),
    (_CJ26 + (8,), "text", r"\u29b5 c \(", "\u29b5c (", 1, "stray space in the search text."),
    # Q16 / Q20: a stacked pair with a BLANK line (the source's blank
    # super/subscript slot) is just a plain sub/superscript
    (_CJ26 + (16,), "html", r'CO<span class="stk post"><span> </span><span>3</span></span>\+ NH',
     "CO<sub>3</sub> + NH", 1, "H2CO3 printed with a blank charge slot; plain subscript."),
    (_CJ26 + (20,), "html", r'cm<span class="stk post"><span>3</span><span> </span></span>of',
     "cm<sup>3</sup> of", 1, "cm3 printed with a blank subscript slot; plain superscript."),
    # Q21: the structures are snipped WITH their two names, so the typed caption
    # line goes (same ruling as CJC 2024 H2 P1 Q3, ASRJC 2024 H2 P1 Q18/Q24)
    (_CJ26 + (21,), "html", r'<p class="qstem eqn">\s*Methylbenzene\s+\(3-nitrophenyl\)methanol</p>\n?', "", 1,
     "the two names are inside the user's snip; typed caption line removed."),
    (_CJ26 + (21,), "text", r"Methylbenzene \(3-nitrophenyl\)methanol ", "", 1,
     "same caption, in the search text."),
])
MCQ_FIXUPS.append((_CJ26 + (8,), "html", r"SO<sub>2\.</sub> </li>", "SO<sub>2</sub>.</li>", 1,
                  "the full stop was typed inside the subscript."))
MCQ_FIXUPS.extend([
    # user ruling 2026-10-25: the source's capital I is a typo for a small l
    (_CJ26 + (1,), "html", r"kJ moI<sup>-1</sup>", "kJ mol<sup>-1</sup>", 1, "moI -> mol (user, 2026-10-25)."),
    (_CJ26 + (1,), "text", r"kJ moI-1", "kJ mol-1", 1, "moI -> mol in the search text."),
    (_CJ26 + (1,), "opt:B", r"kJ moI-1", "kJ mol-1", 1, "moI -> mol in option B."),
    # user ruling 2026-10-25: render the density unit correctly
    (_CJ26 + (30,), "html", r"g cm\u203e<sup>3</sup>", "g cm<sup>\u20133</sup>", 1, "density unit g cm-3 (user, 2026-10-25)."),
    (_CJ26 + (30,), "text", r"g cm\u203e3", "g cm\u20133", 1, "density unit in the search text."),
])
# user 2026-10-25 (Q8 screenshot): a bold TAB typed before the first line of a stem
# renders as an indent; the school's page has none.
for _q in (4, 8, 27, 28):
    MCQ_FIXUPS.append((_CJ26 + (_q,), "html", r'<p class="qstem eqn"><b>\t</b>',
                       '<p class="qstem eqn">', 1,
                       "leading bold tab removed (renders as a first-line indent)."))
# formatting audit 2026-10-25 (user: "check the formatting of all the questions")
MCQ_FIXUPS.extend([
    # a degree sign set as a SUPERSCRIPT is raised twice ("boiling point / \u02daC")
    (_CJ26 + (4,), "html", r"<sup>\u00b0</sup>C", "\u00b0C", 1, "degree sign was also superscripted."),
    (_CJ26 + (30,), "html", r"<sup>\u00b0</sup>C", "\u00b0C", 1, "degree sign was also superscripted."),
    # a typed tab in the middle of a stem paragraph (white-space:pre-wrap shows it as a gap)
    (_CJ26 + (5,), "html", r"below, \t", "below, ", 1, "stray tab inside the stem."),
    (_CJ26 + (18,), "html", r"above\?\t</p>", "above?</p>", 1, "stray trailing tab in the stem."),
    # the school's own worked-solution copy heads the table "Step 1 / 2 / 3"
    (_CJ26 + (21,), "html", r"<td>step ([123])</td>", r"<td>Step \1</td>", 3, "table headings capitalised (school's solutions copy)."),
    (_CJ26 + (21,), "text", r"\bstep 1 \| step 2 \| step 3\b", "Step 1 | Step 2 | Step 3", 1, "table headings in the search text."),
])
for _q in (6, 7, 27, 28, 30):
    MCQ_FIXUPS.append((_CJ26 + (_q,), "text", re.escape(_DB),
                       "Use of the data booklet is relevant to this question.", 1,
                       "house wording (style-guide addendum 2026-10-11)."))


def data_table_questions(school, level, paper, year) -> set:
    """Question numbers whose lettered table is stem data, not the options."""
    return DATA_TABLE_QUESTIONS.get((school, level, paper, year), set())


_EMPTY_FRAC = ('<span class="frac"><span class="fnum"></span>'
               '<span class="fden"></span></span>')


def _stk(top, bottom):
    return '<span class="stk"><span>%s</span><span>%s</span></span>' % (top, bottom)


def cube_root(inner: str) -> str:
    """Cube-root markup: an inline-block with a stretchable SVG radical sign.

    A font radical glyph plus an overline never lined up (the bar floated off
    the sign), so the sign is an SVG that stretches to the radicand's height.
    This is exactly what is live on CJC 2024 H2 P1 Q16 (patch 3) and what the
    answers extractor emits; keep the three in step. A shared `.nroot` CSS
    component or MathML would be nicer (open item in HANDOFF.md).
    """
    svg = ('<svg viewBox="0 0 10 100" preserveAspectRatio="none" '
           'style="position:absolute;left:.45em;top:0;width:.7em;height:100%;'
           'overflow:visible" aria-hidden="true"><path d="M0 60 L2 56 L5 94 '
           'L10 0" fill="none" stroke="currentColor" stroke-width="1.3" '
           'vector-effect="non-scaling-stroke"/></svg>')
    deg = ('<span style="position:absolute;left:.25em;top:-.05em;font-size:.65em;'
           'line-height:1">3</span>')
    return ('<span style="display:inline-block;vertical-align:middle;'
            'position:relative;padding-left:1.15em;white-space:nowrap">' + deg
            + svg + '<span style="display:inline-block;border-top:1.3px solid '
            'currentColor;padding:.15em .15em 0 .05em">' + inner + '</span></span>')


_Q16_FRAC = ('<span class="frac"><span class="fnum">q</span>'
             '<span class="fden">4</span></span>')
_Q16_ROOT_OPEN = '<sup>3</sup>√<span style="text-decoration:overline">'


MCQ_FIXUPS.extend([
    # --- Q11: stray underline on the reaction arrows, stray option tabs -----
    (_CJ + (11,), "html", r"<u>(\u2192) ?</u> ?", r"\1 ", 4,
     "the source underlines each reaction arrow (an authoring slip); live it "
     "rendered as an arrow with a line through the text (user, 2026-10-06)."),
    (_CJ + (11,), "html", r"<b>\t</b>", "", 5,
     "typed tabs at the start/end of each option row shifted B and C to the "
     "centre."),
    # --- Q1: hard line breaks typed to mimic the printed wrap --------------
    (_CJ + (1,), "html", r"<br>[ \t]+", " ", 3,
     "options A, B and D carry a manual line break plus a run of spaces (and, "
     "in B and D, a tab) where the printed page merely wraps; left in, the "
     "app forces a mid-sentence newline with a ragged indent."),
    # --- Q3: structures + names + pKa are ONE snip -------------------------
    (_CJ + (3,), "html",
     r'<p class="qstem eqn">\s+phenol\t\s+thiophenol\t</p>\n', "", 1,
     "the names 'phenol' / 'thiophenol' are inside the combined snip (user "
     "snips both structures WITH their captions); the typed line, hand-aligned "
     "by spaces and a tab under the two pictures, is removed. The words stay "
     "in content_text for search."),
    (_CJ + (3,), "html",
     r'<p class="qstem eqn">\s+p<i>K</i><sub>a</sub> = 10\.0\t\s+'
     r'p<i>K</i><sub>a</sub> = 6\.50\t</p>\n', "", 1,
     "the pKa captions, same reason."),
    (_CJ + (3,), "html",
     r"Thiophenol and phenol are both acting as weak acids in aqueous "
     r"solutions\.", "Thiophenol and phenol both act as weak acids in "
     "aqueous solution.", 1,
     "stem reworded for grammar at the user's request (2026-10-05); the "
     "source reads 'are both acting as weak acids in aqueous solutions'."),
    (_CJ + (3,), "text",
     r"Thiophenol and phenol are both acting as weak acids in aqueous "
     r"solutions\.", "Thiophenol and phenol both act as weak acids in "
     "aqueous solution.", 1, "same rewording, in the search text."),
    (_CJ + (3,), "html", r"<li>\t</b>When", "<li>When", 1,
     "a stray close-bold tag and a tab at the start of statement 3."),
    (_CJ + (3,), "html", r'<p class="qstem">\.</p>\n', "", 1,
     "a lone '.' paragraph between the statements and the options; the "
     "printed page shows the same stray full stop (source typo)."),
    (_CJ + (3,), "text", r"in phenol\. \. A ", "in phenol. A ", 1,
     "the same stray full stop, in the search text."),
    # --- Q8: no option text; one combined figure ---------------------------
    (_CJ + (8,), "html", r'<p class="qstem"><b></b></p>\n?', "", 1,
     "an empty bold paragraph left where the last figure marker was."),
    (_CJ + (8,), "html", r'<p class="qstem eqn">With reference',
     '<p class="qstem">With reference', 1,
     "prose paragraph carrying a trailing tab, so it was tagged eqn."),
    (_CJ + (8,), "html", r"\?\t</p>", "?</p>", 1, "the trailing tab."),
    # --- Q9: four nuclide objects (MathType) typed as house .stk -----------
    (_CJ + (9,), "html", r"\[ H = " + _EMPTY_FRAC,
     "[ H = " + _stk(1, 1), 1,
     "nuclide Equation.DSMT4 object (mass over atomic number) -- no text "
     "layer, typed by hand from the printed page: hydrogen-1."),
    (_CJ + (9,), "html", r"D = " + _EMPTY_FRAC + "H",
     "D = " + _stk(2, 1) + "H", 1, "deuterium: 2 over 1."),
    (_CJ + (9,), "html", r"C = " + _EMPTY_FRAC + "C",
     "C = " + _stk(12, 6) + "C", 1, "carbon-12: 12 over 6."),
    (_CJ + (9,), "html", r"O =" + _EMPTY_FRAC + "O",
     "O = " + _stk(16, 8) + "O", 1, "oxygen-16: 16 over 8."),
    (_CJ + (9,), "text",
     r"\[ H = \(\)/\(\) H; D = \(\)/\(\) H; C = \(\)/\(\) C; O =\(\)/\(\) O \]",
     "[ H = (1)/(1) H; D = (2)/(1) H; C = (12)/(6) C; O = (16)/(8) O ]", 1,
     "the same four nuclides in the search text, in the house '(n)/(d)' form."),
    # --- Q16: stray tab in a superscript ------------------------------------
    (_CJ + (16,), "html", r"\)<sup>\t</sup>", ")", 1,
     "an empty superscript holding only a tab after option B's bracket."),
    # --- Q16: cube roots drawn with the stretchable SVG hook (patch 3) -------
    # Order matters: strip B's leading tab first, then the two radical forms.
    (_CJ + (16,), "html", "<b>\t</b>2\\(", "2(", 1,
     "a typed tab before option B shifted it off the label column."),
    (_CJ + (16,), "html",
     "(?:<b>\t</b>)?" + re.escape(_Q16_ROOT_OPEN + _Q16_FRAC + "</span>"),
     cube_root(_Q16_FRAC), 2,
     "options B and D: cube root of q/4 as an SVG radical (live since "
     "patch 3; regenerating must not revert it to the overline glyph form)."),
    (_CJ + (16,), "html",
     "(?:<b>\t</b>)?" + re.escape(_Q16_ROOT_OPEN + "q</span>"),
     cube_root("<i>q</i>"), 1,
     "option C: cube root of q, with q italic like the stem's q."),
    # --- Q28: a prose paragraph tagged eqn by a leading tab ----------------
    (_CJ + (28,), "html", r'<p class="qstem eqn"><b>\t</b>Which one of',
     '<p class="qstem">Which one of', 1,
     "a leading tab made this prose line an eqn paragraph."),
    # --- Q29: option B 'F2' read as a combined-character stack -------------
    (_CJ + (29,), "html",
     r'F<span class="stk post"><span>\t\t</span><span>2</span></span>',
     "F<sub>2</sub>", 1,
     "the subscript 2 is a Word 'combine characters' group with a blank top "
     "half; the ion-charge stack rule turned it into a stacked pair. It is "
     "just F2 (compare option text and the stem's F2)."),
])


# DHS 2024 H2 P1 (2026-10-10) -------------------------------------------------
# Declared after reading the Word PDF page by page. The user snips every
# figure by hand; nothing here crops.
_DH = ("DHS", "H2", "P1", 2024)
MCQ_FIXUPS.extend([
    # --- Q3: two Word bullet paragraphs (w:numPr) lost their bullets --------
    (_DH + (3,), "html",
     r'<p class="qstem">(the SO<sub>2</sub> : CO<sub>2</sub> mole ratio[^<]*)</p>\n'
     r'<p class="qstem">(the relative deviation[^<]*(?:<sub>[^<]*</sub>[^<]*)*\?)</p>',
     '<ul class="stmts"><li>\\1</li><li>\\2</li></ul>', 1,
     "the two criteria are Word bullet paragraphs (w:numPr); questions.py has "
     "no numPr-list merging (style-guide.md section 9), so the bullets were "
     "lost. style-guide section 2: bullets are ul.stmts."),
    # --- Q5: four bulleted molecules ------------------------------------------
    (_DH + (5,), "html",
     r'<p class="qstem">(NC<i class="el">l</i><sub>3</sub>)</p>\n'
     r'<p class="qstem">(HCN)</p>\n'
     r'<p class="qstem">(BeC<i class="el">l</i><sub>2</sub>)</p>\n'
     r'<p class="qstem">(SOC<i class="el">l</i><sub>2</sub>)</p>',
     '<ul class="stmts"><li>\\1</li><li>\\2</li><li>\\3</li><li>\\4</li></ul>', 1,
     "the four molecules are Word bullet paragraphs (w:numPr); same reason "
     "as Q3."),
    # --- Q13: the reaction scheme is ONE snip (arrow + catalyst Y + A+B, C+D)
    (_DH + (13,), "html", r'<p class="c"><b>\s*A</b> \+ <b>B</b>[^\n]*</p>\n', "", 1,
     "the whole scheme 'A + B --Y--> C + D' is snipped as ONE picture "
     "(catalyst Y sits above the arrow); the typed A + B / C + D line is the "
     "same content, so it is removed and the single placeholder stands for it."),
    (_DH + (13,), "text", r"A \+ B C \+ D ", "", 1,
     "the scheme is inside the snip."),
    # --- Q14: the equilibrium arrow is typed (GLYPH_FIGURES) --------------------
    (_DH + (14,), "html",
     r'<p class="c"><b>E</b>\(g\)\s+\+\s+<b>F</b>\(g\)\s+\u21cc\s+<b>G</b>\(g\)\s*</p>',
     '<p class="c"><b>E</b>(g) + <b>F</b>(g) \u21cc <b>G</b>(g)</p>', 1,
     "the typed arrow joined the three pieces into one line already; this "
     "only squeezes the hand-typed runs of spaces (HTML collapses them)."),
    # --- Q16: options are three printed columns ---------------------------------
    # --- Q15: the dissociation equation is centred (user, 2026-10-10) -----------
    (_DH + (15,), "html", r'<p class="qstem eqn">(M\(OH\)<sub>2</sub>\(s\))',
     '<p class="c eqn">\\1', 1,
     "centre the equilibrium equation in the stem; 'eqn' kept so the spaces and "
     "tabs that align the dH tag still show (pre-wrap)."),
    (_DH + (16,), "html",
     r'<td>((?:(?!<td>).)*?)\s{3,}(<i>K</i><sub>b</sub> of (?:(?!= ).)*?)\s*'
     r'(= [\d.]+ × 10<sup>[^<]*</sup> mol dm<sup>[^<]*</sup>)</td>',
     '<td>\\1</td><td>\\2 \\3</td>', 4,
     "each option has two cells: the pair, then 'Kb of ... = value' kept in ONE "
     "cell (user, 2026-10-10: the value was splitting into its own column); the "
     "source hand-aligned them with spaces and tabs that HTML collapses."),
    # --- Q21: the scheme is ONE snip, compound names included -------------------
    (_DH + (21,), "html", r'<p class="qstem eqn">\s*but-2-ene-1,4-diol\s+ketobutanedioic acid</p>\n', "", 1,
     "the two compound names sit under the scheme and are snipped WITH it; "
     "the typed line (tab-aligned, fragile) is removed. Both names are "
     "already in the stem sentence, so search loses nothing."),
    (_DH + (21,), "text", r"but-2-ene-1,4-diol ketobutanedioic acid ", "", 1,
     "figure-borne captions."),
    # --- Q27: statements table = [number | text], statement 3's figure in the
    #     SAME cell as its text (user, 2026-10-10: it was splitting into a third
    #     column). Also squares up row 1, which had a phantom leading cell.
    (_DH + (27,), "html",
     r'<table class="qt center"><tr><td></td>'
     r'(<td><p class="qstem">1</p></td><td>(?:(?!</tr>).)*?</td>)</tr>'
     r'(<tr><td><p class="qstem">2</p></td><td>(?:(?!</tr>).)*?</td>)<td></td></tr>'
     r'<tr>(<td><p class="qstem">3</p></td><td><p class="qstem">The predominant(?:(?!</p>).)*?)</p></td>'
     r'<td>(<div class="fig">figure</div>)</td></tr></table>',
     '<table class="qt center"><tr>\\1</tr>\\2</tr><tr>\\3</p>\\4</td></tr></table>', 1,
     "statements table squared to two columns; the zwitterion placeholder moves "
     "into statement 3's own cell (DOM order unchanged: it is still the 4th "
     "figure)."),
])



# --- HCI 2024 H2 P1 (2026-10-12) -----------------------------------------
_HC = ("HCI", "H2", "P1", 2024)
MCQ_FIXUPS.extend([
    # Q13: the graph's x-axis title is typed text right after the picture. The
    # user's snip carries BOTH axis titles, so the typed duplicate goes (the
    # same ruling as DHS P1 Q13/Q21). The paragraph also holds a second
    # CENTRE sentinel mid-line, which Postgres would refuse as a NUL byte.
    (_HC + (13,), "html", r'<p class="c">\x00C\x00\s*time / min</p>\n?', "", 1,
     "'time / min' is inside the user's graph snip; typed duplicate removed."),
    (_HC + (13,), "text", r"graph below\. time / min ", "graph below. ", 1,
     "same axis title, in the search text."),
])


def no_option_text(school, level, paper, year) -> set:
    """Question numbers whose options exist only as labels in a figure."""
    return NO_OPTION_TEXT.get((school, level, paper, year), set())


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
    # CJC 2026 H2 P2 (2026-10-26). The Q4(c) reaction scheme prints ONCE (page
    # 13) under (c), but Word anchors its later text boxes ("C8H12N2", "Stage II",
    # ...) in the paragraph of (c)(i). Same picture; the snip of 4(c) covers it,
    # so (c)(i) carries no figure of its own. ((c)(ii) DOES: the B/C/D boxes.)
    ("CJC", "H2", "P2", 2026, 4, "(c)(ii)"):
        "The three empty answer boxes (B, D, C) are shapes in a 2x2 table: "
        "answer space, not content. Not snipped (user, 2026-10-26: answer boxes "
        "are not usually snipped); the table is removed below.",
    ("CJC", "H2", "P2", 2026, 4, "(c)(i)"):
        "Text boxes of the page-13 reaction scheme (C8H12N2, Stage II) anchored "
        "in this part's paragraph; part of the ONE scheme snipped under 4(c).",
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
    # CJC 2024 H2 P2 (2026-10-08)
    ("CJC", "H2", "P2", 2024, 2, "(b)"):
        "'The most important oxide of phosphorus is phosphorus(V) oxide...' "
        "introduces (c); printed between (b)'s [2] and (c).",
    ("CJC", "H2", "P2", 2024, 2, "(c)"):
        "'The structure of phosphorus(V) sulfide, P4S10, ...' introduces (d); "
        "printed between (c)'s [1] and (d).",
    # DHS 2024 H2 P3 (2026-10-11)
    ("DHS", "H2", "P3", 2024, 2, "(b)(iii)"):
        "'There are three different types of 3,4-dimethylhexane molecule' (X, Y, Z) "
        "introduces (b)(iv) and (b)(v); printed between (b)(iii)'s [2] and (b)(iv).",
    ("DHS", "H2", "P3", 2024, 2, "(d)(i)"):
        "The NO2 decomposition lead-in (equation and rate constant) introduces "
        "(d)(ii); printed between (d)(i)'s [2] and (d)(ii).",
    ("DHS", "H2", "P3", 2024, 5, "(d)(i)"):
        "'The formation of the organoboron intermediate ... one-step mechanism' "
        "introduces (d)(ii); printed between (d)(i)'s [1] and (d)(ii).",
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
    # CJC 2024 H2 P2 (2026-10-08)
    ("CJC", "H2", "P2", 2024, 3, "(a)(iii)"):
        "The combustion equation with three empty answer boxes is four native "
        "text-box shapes (three boxes plus the frame holding the typed "
        "equation) that print as ONE picture; snipped as one image. The text "
        "boxes also hold the examiner's answer as hidden text, which the "
        "question must not carry.",
    ("CJC", "H2", "P2", 2024, 4, None):
        "The copper reaction scheme is one ChemDraw object plus two floating "
        "'step I' / 'step II' text boxes that print as ONE scheme; snipped as "
        "one image.",
    # CJC 2026 H2 P2 (2026-10-26)
    ("CJC", "H2", "P2", 2026, 1, "(a)(ii)"):
        "Fig. 1.1 is ONE printed figure of two side-by-side boxes (Ca2+ and F-); "
        "Word stores each box + its ion circle as separate drawings. Snipped as "
        "one image covering both boxes.",
    ("CJC", "H2", "P2", 2026, 2, "(b)(ii)"):
        "The compressibility graph (axes, HCl curve, ideal-gas line, axis "
        "labels) is a chart plus floating text boxes that print as ONE graph; "
        "snipped as one image.",
    ("CJC", "H2", "P2", 2026, 5, "(a)(i)"):
        "The pH curve is one chart plus three floating equivalence-point "
        "callouts that print as ONE graph; snipped as one image.",
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


EQUATION_OPTIONS_AS_TEXT.update({
    # Q7's options C and D are two plain single-rule fractions (MathType
    # objects, no text layer); A and B are the same expressions typed on one
    # line. Typed from the printed page (checked against the Word PDF).
    _CJ + (7,): {
        "C": ('<span class="frac"><span class="fnum">50 x 10<sup>\u2012'
              '3</sup> x 6.02 x 10<sup>23</sup></span>'
              '<span class="fden">28</span></span>',
              '(50 x 10\u20123 x 6.02 x 10^23)/(28)'),
        "D": ('<span class="frac"><span class="fnum">50 x 10<sup>3</sup> '
              'x 6.02 x 10<sup>23</sup></span>'
              '<span class="fden">28</span></span>',
              '(50 x 10^3 x 6.02 x 10^23)/(28)'),
    },
})


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
     "Q2(c) stage I equilibrium arrow (a drawn harpoon pair in the source)"),    # --- CJC 2024 H2 P2 (2026-10-08) ------------------------------------
    (("CJC", "H2", "P2", 2024),
     r"A sample each of <b>\x00FIG\x00</b> and",
     "A sample each of " + _stk(28, 14) + "Si<sup>+</sup> and",
     "Q1(d): nuclide Equation.DSMT4 object (28 over 14 Si+) -- no text layer, "
     "typed by hand from the printed page."),
    (("CJC", "H2", "P2", 2024),
     r"deflection of <b>\x00FIG\x00</b>and",
     "deflection of " + _stk(28, 14) + "Si<sup>+</sup> and",
     "Q1(d): the same nuclide object, second occurrence."),
    (("CJC", "H2", "P2", 2024),
     r"(<b>en\s*</b>)\x00FIG\x00(<b>\t</b>\[Cu\(H<sub>2</sub>O\)<sub>4)",
     "\\1 \u21cc \\2",
     "Q4(d) equilibrium arrow, first Kstab equation (a drawn harpoon pair)"),
    (("CJC", "H2", "P2", 2024),
     r"(2<b>en\s*</b>)\x00FIG\x00(<b>\t</b>\[Cu\(H<sub>2</sub>O\)<sub>2)",
     "\\1 \u21cc \\2",
     "Q4(d) equilibrium arrow, second Kstab equation"),
    (("CJC", "H2", "P2", 2024),
     r"(3<b>en\s*</b>)\x00FIG\x00(<b>\t</b>\[Cu\()",
     "\\1 \u21cc \\2",
     "Q4(d) equilibrium arrow, third Kstab equation"),
    (("CJC", "H2", "P2", 2024),
     r"(2e\u203e) \x00FIG\x00 (H<sub>2</sub>C<sub>2</sub>O<sub>4)\s*</sub>\s{10,}(E<sup)",
     "\\1 \u21cc \\2</sub>\u2003\u2003\u2003\u2003\\3",
     "Q4(e)(v) equilibrium arrow; the 24-space gap before E is the source's own alignment"),
    # --- CJC 2024 H2 P3 (2026-10-09) ------------------------------------
    (("CJC", "H2", "P3", 2024),
     r"(CO\(g\) \+ 3H<sub>2</sub>\(g\)) \x00FIG\x00 (CH<sub>4</sub>)",
     "\\1 ⇌ \\2",
     "Q2(b) Fischer-Tropsch equilibrium arrow (a drawn harpoon pair)"),
    (("CJC", "H2", "P3", 2024),
     r"(H<sub>2</sub>O) \x00FIG\x00 (\s*N<sub>2</sub>H<sub>5</sub>)",
     "\\1 ⇌\\2",
     "Q5(b) hydrazine dissociation equilibrium arrow"),
    (("CJC", "H2", "P3", 2024),
     r"\x00FIG\x00 (N\(CH<sub>3</sub>\)<sub>3</sub> \+ A<i class=\"el\">l</i>C<i class=\"el\">l</i><sub>3</sub>)\s{8,}"
     r"(\(CH<sub>3</sub>\)<sub>3</sub>NA<i class=\"el\">l</i>)",
     "\\1 → \\2",
     "Q4(d)(iii) forward arrow (a drawn long arrow anchored at the start of the line)"),
    (("CJC", "H2", "P3", 2024),
     r"\A\x00FIG\x00(Suggest a simple chemical test .*?\[2\]</span>\n\x00C\x00\x00FIG\x00)\Z",
     "\\1",
     "Q4(b)(iii): the same pair of structures is anchored twice (at the start and at "
     "the end of the part); the printed page shows ONE picture, below the question line"),
    # --- ACJC 2026 H2 P2 (2026-10-20) -----------------------------------
    (("ACJC", "H2", "P2", 2026),
     r"(H<sub>2</sub>O) \x00FIG\x00  (HOOCCH=CHCOO<sup>−</sup> \+ H<sub>3</sub>O)",
     "\\1 ⇌ \\2",
     "Q1 equation 1.1 equilibrium arrow (a drawn harpoon pair)"),
    (("ACJC", "H2", "P2", 2026),
     r"(H<sub>2</sub>O) \x00FIG\x00  (<sup>−</sup>OOCCH=CHCOO)",
     "\\1 ⇌ \\2",
     "Q1 equation 1.2 equilibrium arrow"),
    (("ACJC", "H2", "P2", 2026),
     r"(2CH<sub>3</sub>CH<sub>2</sub>OH\(g\)) \x00FIG\x00 (CH<sub>3</sub>COOCH<sub>2</sub>CH<sub>3</sub>\(g\))",
     "\\1 ⇌ \\2",
     "Q4(b) equation 4.2 equilibrium arrow"),
    # --- ACJC 2026 H2 P3 (2026-10-21) -----------------------------------
    (("ACJC", "H2", "P3", 2026),
     r'(PC<i class="el">l</i><sub>5</sub>\(g\)) <sub> </sub>\x00FIG\x00<sub>\s*</sub>(PC<i class="el">l</i><sub>3</sub>\(g\))',
     "\\1 \u21cc \\2",
     "Q2(c) thermal decomposition of PCl5: equilibrium arrow (a drawn harpoon pair)"),
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


_CP2 = ("CJC", "H2", "P2", 2024)
_D3 = ("DHS", "H2", "P3", 2024)

CORRECTIONS = [
    # ---- DHS 2024 H2 P3 (2026-10-11)
    (_D3, r"[ \t]*<br>[ \t]*", " ",
     "Soft line breaks (w:br) typed to wrap a sentence at the printed margin "
     "(1(d)(i) 'seen in / Fig. 1.3', 1(d)(iii) 'for / steps 1 and 2', 3(d) "
     "'C9H10O3. / Q effervesces'). No genuine break uses <br> here.",
     "housekeeping, same as ASRJC/CJC/DHS P2"),
    # ---- CJC 2024 H2 P2 (2026-10-08)
    (_CP2, r"[ \t]*<br>[ \t]*", " ",
     "Soft line breaks (w:br) typed to wrap a sentence at the printed margin "
     "(4(e)(iii), 5(f), 5(f)(iv), 6(a)(ii), 6(a)(iii), 6(b)(i)). No genuine "
     "break uses <br> here.",
     "housekeeping, same as ASRJC P2/P3"),
    (_CP2, r"e\u203e", "e<sup>\u2212</sup>",
     "Q4(e)(v): the electron's charge is typed as U+203E (OVERLINE); the page "
     "shows a raised minus, 2e-.",
     "housekeeping, 2026-10-08"),
    (_CP2, r"\]\u203e", "]<sup>\u2212</sup>",
     "Q3(c): [BH4]- typed with U+203E (OVERLINE) for the charge; the page "
     "shows a raised minus.",
     "housekeeping, 2026-10-08"),
    (_CP2, r"<u>(\u2192)</u>", "\\1",
     "Q6(b): the equation's arrow is underlined in the source (an authoring "
     "slip); the printed page shows a plain arrow. Same slip as CJC P1 Q11.",
     "housekeeping, 2026-10-08"),
    (_CP2, r"\t+(<i>K</i><sub>stab)", "\u2003\u2003\u2003\\1",
     "Q4(d): the three Kstab equations are lined up with literal tabs, which "
     "HTML collapses; an em-space gap keeps each Kstab value apart from its "
     "equation.",
     "housekeeping, 2026-10-08"),
    (_CP2, r"(Number of \u03c3 bonds:)\s+(Number of \u03c0 bonds:)",
     "\\1\u2003\u2003\u2003\u2003\\2",
     "Q5(c): two answer slots on one line, separated by a tab stop in the "
     "source; an em-space gap replaces it.",
     "housekeeping, 2026-10-08"),
    (_CP2, r"dessicant", "desiccant",
     "Q2 stem: source typo ('dessicant'). PROPOSED, flagged to the user for "
     "confirmation.",
     "proposed 2026-10-08, awaiting user"),
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
    # --- CJC 2024 H2 P3 (2026-10-09) ------------------------------------
    (
        ("CJC", "H2", "P3", 2024),
        r'<b><i>\x00FIG\x00</i></b>(<b>\t</b>Lidocaine is commonly used .*?operations\.\n\x00C\x00\x00FIG\x00)',
        r"\1",
        "Q4(e): the lidocaine structure is anchored twice (before the sentence and "
        "after it); the printed page shows ONE picture, below the sentence.",
        "user accepted the live render, 2026-10-09",
    ),
    (
        ("CJC", "H2", "P3", 2024),
        r'silver is <br>10\.49 g cm',
        "silver is 10.49 g cm",
        "Q5(d)(ii): a manual line break mid-sentence (a justification artefact of "
        "the printed page), removed.",
        "user accepted the live render, 2026-10-09",
    ),
    (
        ("CJC", "H2", "P3", 2024),
        r'to form <br>4-bromobutan-1-ol',
        "to form 4-bromobutan-1-ol",
        "Q4 intro: a manual line break mid-sentence (a justification artefact of "
        "the printed page), removed.",
        "user accepted the live render, 2026-10-09",
    ),
]


# ---------------------------------------------------------------------------
# ASRJC 2026 H2 P3 (2026-10-24) -- LOCAL, UNPUSHED (user: hold every ingest/
# change until the paper is finished).
_A3_26 = ("ASRJC", "H2", "P3", 2026)
_KF = ('<span class="frac"><span class="fnum">[Ni(NH<sub>3</sub>)<sub>6</sub><sup>2+</sup>]</span>'
       '<span class="fden">[Ni(H<sub>2</sub>O)<sub>6</sub><sup>2+</sup>][NH<sub>3</sub>]<sup>6</sup></span></span>')
GLYPH_PICTURES.extend([
    (_A3_26,
     r"(6NH<sub>3</sub>\(aq\))\s+\x00FIG\x00\s+(\[Ni\(NH<sub>3</sub>\)<sub>6</sub>\]<sup>2\+</sup>\(aq\))",
     "\\1 ⇌ \\2",
     "Q1(b) Kstab equilibrium arrow (a drawn harpoon pair, ChemWindow object)"),
    (_A3_26,
     r"(<i>K</i><sub>stab</sub>  = )\x00FIG\x00",
     "\\1" + _KF.replace("\\", "\\\\"),
     "Q1(b) the Kstab fraction is a MathType object with no text layer (the extractor dropped it); "
     "typed from the printed page: [Ni(NH3)6 2+] over [Ni(H2O)6 2+][NH3]^6"),
    (_A3_26,
     r"(EDTA<sup>4−</sup>\(aq\))\s+\x00FIG\x00\s+(\[Ni\(EDTA\)\]<sup>2−</sup>\(aq\))",
     "\\1 ⇌ \\2",
     "Q1(b)(iii) equilibrium arrow (a drawn harpoon pair)"),
    (_A3_26,
     r"\x00FIG\x00\nYou can use N\s+N to represent",
     'You can use <img data-asset="ASRJC_H2_P3_Q1_biv_2026.png" alt=""> to represent',
     "Q1(b)(iv): the N-arc-N ligand symbol is a small 120 x 36 picture floating over typed 'N   N'; Word anchors "
     "it in the PREVIOUS paragraph. It becomes an INLINE image (corrections.INLINE_ASSETS) and the typed "
     "'N N' goes."),
    (_A3_26,
     r"(2N<sub>2</sub>O<sub>5</sub>)\x00FIG\x00 (4NO<sub>2</sub>)",
     "\\1 → \\2",
     "Q4(d) decomposition forward arrow (a drawn arrow object)"),
])
INLINE_ASSETS[_A3_26] = [(1, "(b)(iv)", "biv")]
CORRECTIONS.extend([
    (_A3_26,
     r'<table class="qt"><tr><td>\x00FIG\x00</td><td>\x00FIG\x00</td><td>\x00FIG\x00</td></tr>'
     r'<tr><td><b>P</b></td><td><b>Q</b></td><td><b>R</b></td></tr></table>',
     "\x00C\x00\x00FIG\x00",
     "Q2(b): the three structures and their P / Q / R labels sit in a borderless 2-row table; snipped as ONE "
     "image that already carries the labels, so the typed label row goes.",
     "combined-snip convention (ACJC 2026 P3 Q1(a)); confirm"),
    (_A3_26,
     r'<table class="qt"><tr><td>\x00FIG\x00</td><td>\x00FIG\x00</td></tr></table>(\n\x00C\x00<b>Fig\. 2\.2</b>)',
     "\x00C\x00\x00FIG\x00\\1",
     "Q2(d) Fig. 2.2: the two representations of pyrrole sit side by side in a borderless table; snipped as ONE "
     "image. The 'Fig. 2.2' caption stays typed.",
     "combined-snip convention; confirm"),
    (_A3_26,
     r'<table class="qt"><tr><td>step 1</td><td>\x00FIG\x00</td></tr><tr><td>step 2</td><td>\x00FIG\x00</td></tr></table>',
     "\x00C\x00\x00FIG\x00",
     "Q4(b) Fig. 4.2: steps 1 and 2 (typed step labels + two scheme objects) snipped as ONE image; the "
     "'Fig. 4.2' caption stays typed.",
     "combined-snip convention (ACJC 2026 P3 Q1(e) Fig. 1.3); confirm"),
    (_A3_26,
     r'<table class="qt"><tr><td>step 3</td><td>\x00FIG\x00</td></tr><tr><td>step 4</td><td>\x00FIG\x00</td></tr>'
     r'<tr><td>step 5</td><td>\x00FIG\x00</td></tr></table>',
     "\x00C\x00\x00FIG\x00",
     "Q4(b) Fig. 4.3: steps 3, 4 and 5 snipped as ONE image; the 'Fig. 4.3' caption stays typed.",
     "combined-snip convention; confirm"),
])


# ---- CJC 2026 H2 P2 (2026-10-26) ------------------------------------------
_CJ2_26 = ("CJC", "H2", "P2", 2026)
CORRECTIONS.extend([
    (_CJ2_26,
     r'(<span class="mk">\[1\]</span>)\n(<b>\t\t</b>During the canning process)',
     "\\1\n\x00QL\x00\n\\2",
     "Q5(a)(i): the 'During the canning process...' passage and the pH curve "
     "introduce (a)(ii)-(v) and print flush with the question stem, not inside "
     "(a)(i)'s block; rendered at question level (render_parts.QLEVEL). The "
     "figure keeps its (a)(i) owner and ordinal.",
     "user, 2026-10-26"),
    # ---- symbol standardisation (user, 2026-10-26): minus = U+2212, range = en dash, times = U+00D7
    (_CJ2_26, r"(\d) \u2012 ?(\d)", "\\1 \u2013 \\2",
     "Q5(a)(ii) indicator table: pH RANGES typed with a figure dash; en dash.",
     "user, 2026-10-26"),
    (_CJ2_26, "\u2012", "\u2212",
     "Minus / negative sign typed as U+2012 (exponents, charges, -44.9, -2653, "
     "-1577); standardised to the true minus U+2212 (symbols.py F02D).",
     "user, 2026-10-26"),
    (_CJ2_26, r"(<sup>[^<]*)\u2013", "\\1\u2212",
     "Minus typed as an en dash inside a superscript (10-13, dm-3, O-, 3-); U+2212.",
     "user, 2026-10-26"),
    (_CJ2_26, "\u2500", "\u2212",
     "Q2 table: '-35.0' typed with a box-drawing dash U+2500; U+2212.",
     "user, 2026-10-26"),
    (_CJ2_26, r"(<sup>\d?)-(</sup>)", "\\1\u2212\\2",
     "Q6(e)(i): charges typed with a hyphen (HCO3-, CO3 2-); U+2212.",
     "user, 2026-10-26"),
    (_CJ2_26, r"<span>2-</span>", "<span>2\u2212</span>",
     "Q6 Omega fraction: the CO3 2- charge in the OMML stack typed with a hyphen.",
     "user, 2026-10-26"),
    (_CJ2_26, r"(\d) x (10)", "\\1 \u00d7 \\2",
     "Q5: times typed as the letter x (5.13 x 10-13, 1.38 x 10-4); U+00D7, as Q6.",
     "user, 2026-10-26"),
    (_CJ2_26, r"<b><br></b>", "",
     "Q4(c)(i): an empty bold run holding only a soft line break at the start "
     "of the part.",
     "housekeeping, 2026-10-26"),
    (_CJ2_26, r"[ \t]*<br>[ \t]*", " ",
     "Soft line breaks (w:br) typed to wrap a sentence at the printed margin: "
     "Q5 intro 'is / 5.13 x 10-13', Q5(a)(iii) leading break, Q5(b) '... mol dm-3 / "
     "lactic acid'. In the app the column is a different width, so each would "
     "leave a ragged mid-sentence break. Must stay BEFORE the Q4(c)(iii) table "
     "entry below, which adds genuine <br> inside cells.",
     "housekeeping, same as ACJC 2024 P2 / ASRJC P3 (2026-10-26)"),
    (_CJ2_26,
     r"(?m)^(the arrangement of two water molecules around one Ca<sup>2\+</sup>\(aq\) ion)\n"
     r"(the arrangement of two water molecules around one F<sup>\u2012</sup>\(aq\) ion\.)$",
     '<ul class="stmts"><li>\\1</li><li>\\2</li></ul>',
     "Q1(a)(ii): the two '\u2022' criteria are a NESTED (level-1) bullet list inside "
     "the roman-numbered list; oxml.load_bullet_numids reads only level 0, so "
     "they came out as plain paragraphs. House style is ul.stmts (style-guide "
     "SS2).",
     "housekeeping, 2026-10-26"),
    (_CJ2_26, r"<b> {20,}(Fig\. 1\.1)</b>", "\x00C\x00<b>\\1</b>",
     "Q1(a)(ii): the 'Fig. 1.1' caption is centred in the source with a run of "
     "leading spaces, which HTML collapses; centred with the house sentinel "
     "instead (every other Fig./Table caption in this paper is a centred paragraph).",
     "housekeeping, 2026-10-26"),
    (_CJ2_26, r"<i>G</i><sup>\ua74b</sup>",
     '\u2206<i>G</i><sup class="pl-sym">\u29b5</sup>',
     "Q1(b)(iii): the source writes Delta-G-standard as a Word SYMBOL field "
     "(`symbol 68 \\f \"Symbol\"`, the Delta, which the extractor does not read) "
     "followed by 'G' and U+A74B (small o with long stroke, typed for the "
     "standard-state sign). Typed as Delta + the house plimsoll (pl-sym), "
     "as in this paper's own Table 1.1 header.",
     "housekeeping, 2026-10-26; confirm"),
    (_CJ2_26, r"<sup>\s*o</sup>(?=(?:</b><b>)?C)", "\u00b0",
     "Degree Celsius typed as a superscript letter 'o' (80oC, 30oC, 0oC, 25oC, "
     "'boiling point / oC' in the Q2 table); typed as the degree sign.",
     "housekeeping, 2026-10-26; confirm"),
    (_CJ2_26, r"(\d) (\u00b0C)", "\\1&nbsp;\\2",
     "Q1(b)(iii): keep '25' and '\u00b0C' on one line (same rule as ASRJC P2/P3).",
     "housekeeping, 2026-10-26"),
    (_CJ2_26,
     r'(?s)(in the boxes provided below\.)\n<table class="qt">.*?</table>',
     "\\1",
     "Q4(c)(ii): the empty B/D/C answer-box table is removed (answer space, "
     "not snipped); the instruction line stays.",
     "user, 2026-10-26"),
    (_CJ2_26,
     r"<td>Stage I\n\(2 steps\)</td><td>1\.\n2\. </td>",
     "<td>Stage I<br>(2 steps)</td><td>1.<br>2.</td>",
     "Q4(c)(iii) table: the two-paragraph cells ('Stage I' / '(2 steps)' and "
     "'1.' / '2.') carry a literal newline, which the renderer's line-by-line "
     "wrapping turns into <p> and </p> in DIFFERENT cells (unbalanced markup); "
     "rebuilt with a <br> inside each cell.",
     "housekeeping, 2026-10-26"),
])


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
