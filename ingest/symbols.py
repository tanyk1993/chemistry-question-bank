"""Symbol / Wingdings font glyph mapping.

WHY THIS FILE EXISTS AND WHY IT IS BORING ON PURPOSE
----------------------------------------------------
Word stores Symbol-font and Wingdings characters as `<w:sym w:font="Symbol"
w:char="F0B7"/>`, i.e. as a font-plus-codepoint pair, NOT as the Unicode
character they look like. Anything that does not map them explicitly silently
loses them. In the RI 2024 P2 mark scheme that would drop every radical dot in a
question that is entirely about .OH radicals.

This is also the layer that LLM-assisted editing gets confidently wrong, because
the codes are opaque and a plausible-looking wrong table produces output that
renders fine and is chemically incorrect. So: every entry below is justified,
every entry is covered by a test against a real document, and this file should
be changed only with evidence, never by inference.

GROUND TRUTH: the mapping is verified by the tests in tests/test_symbols.py
against the Word-exported PDF of the same document -- an INDEPENDENT renderer,
not our own conversion. See audit.py for why that distinction matters.
"""

# Adobe Symbol encoding. Word offsets these into the F0xx private-use range,
# so F0B7 here is Symbol character 0xB7.
SYMBOL = {
    "F0AE": "→",   # 0xAE arrowright           -> ; verified p1 "B3+(g) --> B4+(g)"
    "F0BE": "",         # 0xBE arrowhorizex         horizontal EXTENDER, not content.
                        #   F0BE+F0AE is a two-glyph long arrow; Word draws the shaft
                        #   with BE and the head with AE. The Word PDF extracts this as
                        #   U+23AF + U+2192. We emit only the head: the extender is a
                        #   typographic device, and WA2 house style uses a plain arrow.
                        #   audit.py normalises U+23AF away before diffing so this
                        #   deliberate choice does not read as a dropped character.
    "F0B4": "×",   # 0xB4 multiply             x ; "2.3 x 10^-4 s"
    "F0B7": "•",   # 0xB7 bullet               . ; the RADICAL DOT in .OH -- the
                        #   single highest-consequence entry in this table.
    "F02D": "−",   # 0x2D minus                - ; "8e-" (true minus, not hyphen)
    "F0B0": "°",   # 0xB0 degree               ; "bond angle: 120"
    "F070": "π",   # 0x70 pi
    "F073": "σ",   # 0x73 sigma; RI 2024 H2 P1 Q7 "There are 6 <s> and 2 <p>
                        #   bonds present." Question paper only -- the answers
                        #   family has no sigma.
    "F044": "∆",   # 0x44 Delta -> U+2206 INCREMENT, not U+0394. Chosen on
                        #   evidence, not inference: this same document also
                        #   writes Delta as a literal character (8 occurrences,
                        #   "<2206>H" in Q12/Q13), and its Word PDF extracts
                        #   those as U+2206. Mapping the w:sym form to the same
                        #   codepoint keeps the two character inventories
                        #   comparable in the text gate. Adobe's own symbol.txt
                        #   also gives 0x44 -> U+2206.
    "F05C": "∴",   # 0x5C therefore            ; ".'. reaction is first order"
    "F0B5": "∝",   # 0xB5 proportional         ; "k' [CH3CHO]"
    "F0BB": "≈",   # 0xBB approxequal          ; RI 2024 H2 P1 answers Q17,
                        #   the only occurrence in the document: "[CH3COO-]eqm
                        #   [CH3COO-]initial = 1 mol dm-3 since CH3COO- is a
                        #   weak acid with a small Kb" -- the standard weak-acid
                        #   approximation, so "eqm ~= initial" is exactly the
                        #   sense required. The Word-PDF text layer drops this
                        #   glyph too (pdftotext doesn't decode Symbol PUA
                        #   codepoints any more than it decodes the radical
                        #   dot), so this entry is evidenced by the standard
                        #   Adobe Symbol encoding table (0xBB=approxequal,
                        #   consistent with every neighbouring entry already in
                        #   this table: 0xAE/0xB0/0xB4/0xB5/0xB7/0xBE) plus the
                        #   chemistry, not an independent PDF cross-check.
    "F0AD": "↑",   # 0xAD arrowup              ; EJC 2024 H2 P1 answers Q17:
                        #   "the atomic radius [AD]es down the group" -- atomic
                        #   radius genuinely INCREASES down a group (more
                        #   shells), and "[AD] polarisability of electron
                        #   cloud" in the same question is likewise an
                        #   increase. Paired with F0AF (arrowdown) below;
                        #   distinguished from it by checking which direction
                        #   the surrounding chemistry actually goes in each of
                        #   the 3 occurrences, not by the Adobe table alone.
    "F0AF": "↓",   # 0xAF arrowdown            ; EJC 2024 H2 P1 answers Q17:
                        #   "volatility [AF]es (higher boiling point) down the
                        #   group" -- higher boiling point means LOWER
                        #   volatility, and the same paragraph's "[AF] in
                        #   tendency for X2 to be reduced" matches Group 17's
                        #   well-known decreasing oxidising power down the
                        #   group. 5 occurrences, all confirmed the same way.
    "F0DE": "✓",   # 0xDE (checkmark, not the Adobe-table "braceleftbt" the
                        #   raw codepoint might suggest -- this font substitutes
                        #   a tick glyph here). EJC 2024 H2 P1 answers: 31
                        #   occurrences, 30 of them the very first run of a
                        #   question's bare answer-letter paragraph (" B" ->
                        #   "✓ B"), i.e. a tick marking the final answer, plus
                        #   one more on Q2's concluding sentence ("Final
                        #   oxidation of Y is +4.") -- confirmed by walking
                        #   every occurrence against the paragraph it sits in,
                        #   not by the Adobe encoding table (which this
                        #   document's font does not follow at this codepoint).
    "F053": "Σ",   # 0x53 Sigma (uppercase)    ; EJC 2024 H2 P1 answers Q16:
                        #   "∆Hsol = |L.E.| - |[53]∆Hhyd|" -- a salt has TWO
                        #   hydration enthalpies (cation and anion) that get
                        #   summed, so "sum of ∆Hhyd" is exactly the missing
                        #   term; consistent with 0x73/sigma (lowercase) already
                        #   mapped above being the same letter's lowercase form.
}

# Wingdings.
WINGDINGS = {
    "F0A1": "⦵",   # CIRCLE WITH HORIZONTAL BAR -- the standard-state / plimsoll
                        #   symbol. Appears as E<sup>x</sup> and E<sup>x</sup>cell.
                        #   Matches WA2's live markup, which uses &#10677; (= U+29B5).
                        #   The source runs already carry w:vertAlign=superscript, so
                        #   the generic superscript handling wraps it in <sup>; do NOT
                        #   special-case it here.
    "F0FC": "✓",   # EJC 2024 H2 P1 answers Q4: "D[FC]:octahedral" -- the
                        #   reference PDF's own text layer extracts this exact
                        #   spot as "D✓:   octahedral" (D is the correct option),
                        #   while the same position on options A/B/C (wrong
                        #   answers, see F0FB below) extracts to nothing at all.
                        #   A per-option checkbox pair, checked only on the
                        #   correct option -- a second, independent "mark the
                        #   correct one" convention from F0DE's answer-line tick
                        #   above, used specifically inside an A/B/C/D option
                        #   list rather than on the final bare answer letter.
    "F0FB": "☐",   # EJC 2024 H2 P1 answers Q4: "A[FB]:bent" / "B[FB]:trigonal
                        #   planar" / "C[FB]:square planar" -- the UNCHECKED
                        #   counterpart of F0FC above, sitting on every WRONG
                        #   option in the same list (confirmed: the reference
                        #   PDF's text layer shows nothing at this position for
                        #   A/B/C, only "D✓" for the correct one -- consistent
                        #   with an empty checkbox glyph, which pdftotext does
                        #   not resolve to visible text any more than it does
                        #   most other Wingdings/Symbol PUA codepoints).
}

# MT Extra -- a THIRD font family, first seen on EJC 2024 H2 P1. Legacy
# Microsoft Equation Editor 3.0 documents encode some symbols in this font
# rather than Symbol; RI's papers never hit it, so it wasn't in this table
# until now.
MT_EXTRA = {
    "F083": "⇌",   # 0x83, the reversible-reaction harpoon arrow. Every one of
                        #   11 occurrences in EJC P1 sits between reactants and
                        #   products of a stated equilibrium: Q7's four AgCl/AgBr
                        #   dissolution-and-complexation equilibria, Q8's
                        #   photochromic reactions 1-3, Q10's Y(aq) <-> 2Z(aq),
                        #   Q29's two half-cell reduction potentials. The Word
                        #   PDF's own text layer extracts the SAME raw private-use
                        #   codepoint () at each of those positions rather
                        #   than resolving it -- i.e. pymupdf doesn't know this
                        #   font either, so the position-and-context match across
                        #   11 independent occurrences is the evidence, not a font
                        #   spec. See adobe_symbol.ADOBE_MT_EXTRA for the
                        #   independent cross-check entry.
}

#: Characters that are typographic scaffolding rather than content. The audit
#: layer strips these from BOTH sides before comparing, so that a deliberate
#: normalisation is never mistaken for a dropped glyph.
DECORATIVE = "⎯"   # HORIZONTAL LINE EXTENSION (arrow shaft)


class UnknownSymbol(KeyError):
    """Raised for an unmapped w:sym.

    Deliberately fatal. A silently dropped glyph is exactly the defect class
    this module exists to prevent, so an unrecognised code must stop the run
    and be looked at by a human rather than degrade quietly.
    """


def sym_to_text(font: str, char: str) -> str:
    """Map one <w:sym w:font=.. w:char=../> to its Unicode text.

    `char` is matched case-insensitively; Word writes uppercase hex but the
    spec does not require it.
    """
    table = {"symbol": SYMBOL, "wingdings": WINGDINGS,
              "mt extra": MT_EXTRA}.get((font or "").strip().lower())
    if table is None:
        raise UnknownSymbol(f"unmapped w:sym font {font!r} (char {char!r})")
    key = (char or "").strip().upper()
    if key not in table:
        raise UnknownSymbol(f"unmapped w:sym {font}:{key}")
    return table[key]
