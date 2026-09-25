"""Canonical Adobe Symbol / Wingdings encodings -- REFERENCE DATA ONLY.

WHY THIS IS A SEPARATE FILE FROM symbols.py
-------------------------------------------
symbols.py is the table the EXTRACTOR uses. This is the table the AUDIT uses to
decode the same glyphs out of the reference PDF. They must never be the same
object, and the audit must never import symbols.py's version.

That is not fussiness. The first version of the audit demapped the reference PDF
using the extractor's own table, and a deliberate sabotage test (deleting the
radical-dot mapping) produced IDENTICAL output with and without the bug -- both
sides lost the character simultaneously, so the comparison could not fail. That
is the exact failure handoff SS9 records: "a text diff of EMF records vs converted
SVG compared a file against its own conversion, so it could not see a character
that had no glyph to render with."

Independence is the entire value of the check. Keeping the reference encoding in
its own module, sourced from the published font encoding rather than from what we
happen to have implemented, is what preserves it.

`cross_check()` additionally asserts the two tables agree -- so a divergence is
reported rather than silently splitting the extractor and its own auditor.
"""
from __future__ import annotations

# Adobe Symbol font encoding, standard glyph names -> Unicode.
# Word stores these offset into the F000 private-use block.
ADOBE_SYMBOL = {
    0x2D: "−",   # minus
    0x44: "∆",   # Delta -> U+2206 increment (Adobe symbol.txt); see symbols.py
    0x5C: "∴",   # therefore
    0x70: "π",   # pi
    0x73: "σ",   # sigma
    0xAE: "→",   # arrowright
    0xB0: "°",   # degree
    0xB4: "×",   # multiply
    0xB5: "∝",   # proportional
    0xB7: "•",   # bullet
    0xBE: "⎯",   # arrowhorizex -- the arrow SHAFT. Decoded to its true
                      # character here (unlike the extractor, which drops it as
                      # typographic scaffolding); audit.normalise strips it from
                      # both sides afterwards, so the deliberate difference is
                      # handled openly rather than by two tables quietly
                      # disagreeing.
}

# Wingdings. Only the codes this document family actually uses.
ADOBE_WINGDINGS = {
    0xA1: "⦵",   # circle with horizontal bar -- standard-state symbol
}

# MT Extra -- NOT a standard Adobe encoding (unlike Symbol/Wingdings, MT Extra
# has no published Adobe glyph list; it's a Microsoft Equation Editor 3.0
# private font). Kept as its own table anyway, sourced independently from
# symbols.MT_EXTRA's own reasoning -- reconstructed from where the glyph
# appears in the document and cross-checked against the Word PDF's raw
# codepoints, not copied from the extractor's table. See symbols.py for the
# evidence.
ADOBE_MT_EXTRA = {
    0x83: "⇌",   # reversible-reaction harpoon arrow
}


def decode(cp: int) -> str | None:
    """Decode one private-use codepoint, or None if unknown."""
    if not 0xF000 <= cp <= 0xF0FF:
        return None
    low = cp & 0xFF
    if low in ADOBE_SYMBOL:
        return ADOBE_SYMBOL[low]
    if low in ADOBE_WINGDINGS:
        return ADOBE_WINGDINGS[low]
    return ADOBE_MT_EXTRA.get(low)


def cross_check(extractor_symbol: dict, extractor_wingdings: dict,
                 extractor_mt_extra: dict | None = None) -> list[str]:
    """Report disagreements between the extractor's table and this one.

    A divergence means the extractor and its auditor have drifted apart, which
    is how a check quietly stops being a check.
    """
    problems = []
    for key, got in extractor_symbol.items():
        want = ADOBE_SYMBOL.get(int(key[2:], 16))
        if want is None:
            problems.append("extractor maps Symbol %s but the reference "
                            "encoding has no entry for it" % key)
        elif got != want and not (got == "" and want == "⎯"):
            problems.append("Symbol %s: extractor=%r reference=%r"
                            % (key, got, want))
    for key, got in extractor_wingdings.items():
        want = ADOBE_WINGDINGS.get(int(key[2:], 16))
        if want is None:
            problems.append("extractor maps Wingdings %s but the reference "
                            "encoding has no entry for it" % key)
        elif got != want:
            problems.append("Wingdings %s: extractor=%r reference=%r"
                            % (key, got, want))
    for key, got in (extractor_mt_extra or {}).items():
        want = ADOBE_MT_EXTRA.get(int(key[2:], 16))
        if want is None:
            problems.append("extractor maps MT Extra %s but the reference "
                            "encoding has no entry for it" % key)
        elif got != want:
            problems.append("MT Extra %s: extractor=%r reference=%r"
                            % (key, got, want))
    return problems
