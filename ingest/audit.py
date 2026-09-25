"""Acceptance gates.

Handoff SS9: "A check that cannot fail is not a check." Two gates that passed
cleanly last time while three figures were rotated and a label was missing:
a marks total (cannot see figures swapped between slots) and a text diff of EMF
records against their own conversion (compared a file to itself).

The gates here are built to avoid both traps:

TEXT GATE (this file)
    Compares OUR extraction against the WORD-EXPORTED PDF -- an independent
    renderer we did not produce. That independence is the whole point. On this
    document it is what proved LibreOffice silently drops the radical dot, the
    multiplication sign, and every OMML fraction -- including the 3/2 in
    "3BE(B-H) + <3/2> BE(O=O)", which is load-bearing chemistry: the paper's own
    stated answer of -1019 kJ/mol only reproduces with 3/2, not with 2.

FIGURE GATE (figure_gate)
    Simulates the CONSUMER: walks placeholders in DOM order and zips them to
    assets in ordinal order exactly as index.html does, then checks each image
    against the label it will actually render under. A marks total cannot see a
    rotation; this can.

Neither gate subsumes the other. The text gate is blind to figure placement;
the figure gate is blind to dropped glyphs.
"""
from __future__ import annotations

import re
import subprocess
from collections import Counter

from lxml import etree

from . import adobe_symbol
from .oxml import Wq
from .symbols import DECORATIVE, SYMBOL, WINGDINGS, MT_EXTRA


class GateFailure(AssertionError):
    pass


#: Characters that occur ONLY inside figure images in this paper, and so are
#: legitimately absent from the extracted body text. Each needs a reason: an
#: undocumented exemption list is how a gate quietly stops catching things.
#:
#: Figure-borne text is the FIGURE gate's responsibility, not the text gate's.
#: If one of these ever appears in body text too, the gate will stop reporting
#: it -- so keep the list short and specific.
FIGURE_BORNE = {
    "\u00bd": 'chart construction-line labels "1st t\u00bd" / "2nd t1/2"',
    "<": 'energy-profile diagram label "\u2206H < 0" (4(b)(ii))',
    # EJC 2024 H2 P1 -- both are genuinely figure content, confirmed by
    # tracing each codepoint to the one question it comes from, not assumed
    # from the character alone:
    "/": 'EJC P1 Q11\u2019s graph axis label "amount of A / mol" -- the axis '
         'label is drawn as part of the native-shape graph, not extractable '
         'text; the SAME question\u2019s stem prose never uses a bare slash',
    "\uf05b": 'EJC P1 Q13\u2019s buffer-equation options -- Symbol-font '
              'stretchy left-bracket piece from the embedded Equation.DSMT4 '
              'objects (\u201c[H+] = Ka\u00d7[acid]/[salt]\u201d). Rendered '
              'as house markup, not a cropped image (corrections.py\u2019s '
              'EQUATION_OPTIONS_AS_TEXT), but with plain ASCII "[" "]" '
              'standing in for MathType\u2019s own stretchy-bracket glyph -- '
              'the PDF\u2019s own codepoint stays legitimately absent from '
              'the extraction even though the bracket ITSELF is now real, '
              'searchable text',
    "\uf05d": 'EJC P1 Q13 -- the matching stretchy right-bracket piece, same '
              'equation objects as \\uf05b above',
    "\uf0e9": 'EJC P1 Q13 -- stretchy bracket CORNER piece (top), same '
              'Equation.DSMT4 objects as \\uf05b above',
    "\uf0eb": 'EJC P1 Q13 -- stretchy bracket CORNER piece (bottom), same '
              'Equation.DSMT4 objects as \\uf05b above',
    "\uf0f9": 'EJC P1 Q13 -- stretchy bracket CORNER piece (top, right side), '
              'same Equation.DSMT4 objects as \\uf05b above',
    "\uf0fb": 'EJC P1 Q13 -- stretchy bracket CORNER piece (bottom, right '
              'side), same Equation.DSMT4 objects as \\uf05b above',
}


def classify(problems: list[str]) -> tuple[list[str], list[str]]:
    """Split gate output into (real, figure-borne-and-expected)."""
    real, expected = [], []
    for p in problems:
        hit = next((ch for ch in FIGURE_BORNE
                    if ("U+%04X" % ord(ch)) in p), None)
        (expected if hit else real).append(
            p + ("  [expected: %s]" % FIGURE_BORNE[hit] if hit else ""))
    return real, expected


def pdf_text(path, first_page: int | None = None,
             last_page: int | None = None) -> str:
    """Text of the reference PDF, optionally restricted to a page range.

    A question paper's cover page and running footer are not question content:
    the cover's "Additional Materials:" and the footer's "(c) Raffles
    Institution" are the only source of a colon and a copyright sign in the
    whole document. Comparing against them would report two permanent failures
    that are not defects -- and a gate that always fails gets ignored, which is
    worse than no gate. Narrowing the reference is honest; adding them to
    FIGURE_BORNE would not be, because they are neither figures nor expected.
    """
    cmd = ["pdftotext", "-layout"]
    if first_page:
        cmd += ["-f", str(first_page)]
    if last_page:
        cmd += ["-l", str(last_page)]
    out = subprocess.run(cmd + [str(path), "-"],
                         capture_output=True, text=True, check=True)
    return out.stdout


def demap_private_use(s: str) -> str:
    """Translate raw F0xx private-use codepoints in PDF-extracted text.

    pdftotext emits Symbol/Wingdings glyphs as their raw private-use codepoints
    when the embedded subset carries no usable ToUnicode map. The PDF is then
    saying "Symbol character 0xB4" in exactly the same way the docx's <w:sym>
    does -- so we decode it with the SAME table.

    This does not weaken the gate. If our extraction genuinely dropped a glyph,
    the reference still has it and we still do not, so the comparison fails. All
    this does is stop the two sides arguing in different alphabets.
    """
    out = []
    for ch in s:
        # Decoded with the INDEPENDENT reference encoding, never with the
        # extractor's own table -- see adobe_symbol.py for why.
        sub = adobe_symbol.decode(ord(ch))
        out.append(sub if sub is not None else ch)
    return "".join(out)


def normalise(s: str) -> str:
    """Reduce text to what both sides can agree on.

    PDF extraction flattens superscripts, may reorder columns, and inserts
    layout whitespace. Comparing raw would produce noise, and a noisy gate gets
    ignored -- which is worse than no gate. So: strip tags, fold whitespace,
    drop purely typographic characters.
    """
    s = demap_private_use(s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace(" ", " ")
    for ch in DECORATIVE:
        s = s.replace(ch, "")
    # Unify the dash/minus family: the source mixes them and the distinction
    # is not one we are trying to police here.
    s = re.sub(r"[‐-―−‒-]", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def charset_gate(extracted: str, reference_pdf,
                 ignore_re: list[str] | None = None,
                 first_page: int | None = None,
                 last_page: int | None = None) -> list[str]:
    """Any character the PDF has and we do not is a candidate dropped glyph.

    This is the cheap, high-value half: it needs no knowledge of WHICH glyph to
    worry about in advance, which is exactly the property the previous EMF check
    lacked.
    """
    problems_pre = adobe_symbol.cross_check(SYMBOL, WINGDINGS, MT_EXTRA)
    ref = pdf_text(reference_pdf, first_page, last_page)
    for pat in (ignore_re or []):
        ref = re.sub(pat, " ", ref)
    ref_n = normalise(ref)
    ours = Counter(normalise(extracted))
    theirs = Counter(ref_n)
    ignorable = set(" \t\n") | set(DECORATIVE)
    problems = list(problems_pre)
    for ch, n in sorted(theirs.items()):
        if ch in ignorable:
            continue
        if ours.get(ch, 0) == 0:
            # Show where it occurs, so a human can classify the failure
            # (real drop vs figure-borne text vs running header) in seconds
            # instead of re-deriving it.
            i = ref_n.find(ch)
            ctx = ref_n[max(0, i - 38):i + 38].strip() if i >= 0 else ""
            problems.append("character %r (U+%04X) x%d in reference, absent "
                            "from extraction | ...%s..." % (ch, ord(ch), n, ctx))
    return problems


def correspondence_gate(docx_pdf_pages: int, reference_pdf) -> list[str]:
    """Cheap sanity check that the PDF actually matches the docx we parsed.

    A stale PDF produces a wall of phantom failures, and a gate that cries wolf
    gets switched off. Better to fail on the mismatch itself.
    """
    out = subprocess.run(["pdfinfo", str(reference_pdf)],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    pages = int(m.group(1)) if m else -1
    if docx_pdf_pages and pages != docx_pdf_pages:
        return ["reference PDF has %d pages, docx renders %d -- the two files "
                "may not correspond" % (pages, docx_pdf_pages)]
    return []


def figure_gate(placements, expectations) -> list[str]:
    """Check figures against the captions they will RENDER under.

    `placements` is [(part_label, filename)] built the way the frontend builds
    it -- DOM order of placeholders zipped to assets sorted by ordinal -- NOT
    the way the extractor happens to hold them. Reproducing the consumer's own
    logic is what makes this able to catch a rotation.

    `expectations` maps part_label -> a substring expected in that figure's
    ground-truth text (its embedded text records, or a recorded expectation for
    figures that carry no text).
    """
    problems = []
    for label, filename, ground_truth in placements:
        want = expectations.get(label)
        if want is None:
            problems.append("no recorded expectation for %s (%s) -- an "
                            "unverifiable figure is an unchecked figure"
                            % (label, filename))
            continue
        if want.lower() not in (ground_truth or "").lower():
            problems.append("%s renders %s, whose content %r does not contain "
                            "the expected %r" % (label, filename,
                                                 (ground_truth or "")[:60], want))
    return problems


# --------------------------------------------------------------------------
# FORMATTING GATE -- whitespace / numPr, proactive rather than corrective
# --------------------------------------------------------------------------
#
# Two unrelated defects have now each bitten more than one paper, and both
# have the same shape: they look fine in the raw XML and only show up wrong
# once rendered, so they were previously found by eye, after the fact.
#
#   TAB / MULTI-SPACE. A literal <w:tab/> or 2+ consecutive spaces inside a
#   run's own text is how Word authors hand-align a trailing label into its
#   own column -- RI 2024 H2 P3's "equation N" convention (repeated spaces)
#   and EJC 2024 H2 P1's Q8/Q10/Q29 (real tab-stops). Both need deliberate
#   handling (the `eqn` CSS class, style-guide.md) or the alignment is lost
#   on render. Neither is wrong to HAVE -- the point is to catch a NEW one
#   before it ships unhandled, not after.
#
#   numPr ADJACENT TO A TYPED CONTINUATION. Word's own `w:numPr` numbered-list
#   paragraphs carry NO visible number in the extracted text at all -- Word
#   supplies it at render time from the list definition. When a multi-
#   statement item mixes a genuine numPr paragraph with typed "2 ...",
#   "3 ..." continuations of the SAME list (questions_flow.py's
#   _wrap_stmt_lists; EJC 2024 H2 P1 Q10), the adapter has to recognise and
#   fold them together, or the numbered item silently loses its number. Every
#   numPr paragraph is reported, and so is any paragraph immediately
#   following one that starts with a digit -- a candidate continuation.
#
# This is a REPORT, not a hard gate: it does not know which hits are already
# handled by a convention and which are new. It exists so a human spends
# seconds confirming each candidate instead of finding the bug live.

_MULTISPACE = re.compile(r"  +")
_LEADING_DIGIT = re.compile(r"^\s*\d")


def _para_raw(p) -> tuple[str, bool]:
    """(text, has_tab) for one w:p -- w:t and w:tab only, in document order.

    Deliberately shallow: no symbol-font decoding, no OMML descent. This is a
    structural scan for a literal tab character and run-length of spaces, not
    a renderer -- see oxml.py for the real thing.
    """
    parts = []
    has_tab = False
    for r in p.findall(".//" + Wq + "r"):
        for ch in r:
            ln = etree.QName(ch).localname
            if ln == "t":
                parts.append(ch.text or "")
            elif ln == "tab":
                parts.append("\t")
                has_tab = True
    return "".join(parts), has_tab


def formatting_gate(document_xml_path) -> list[str]:
    """Flag every paragraph carrying a tab, a double space, or a w:numPr --
    plus any paragraph right after a numPr run that looks like it continues
    it by hand. See the module comment above for why these three and not
    something a rule could silently miss.

    Walks EVERY w:p in the document (`.//`), table cells included, so it
    works unchanged on both the table-shape (questions.py) and paragraph-flow
    (questions_flow.py) adapters -- neither is assumed.
    """
    tree = etree.parse(str(document_xml_path))
    paras = tree.getroot().findall(".//" + Wq + "p")

    problems = []
    in_numpr_run = False
    for i, p in enumerate(paras):
        raw, has_tab = _para_raw(p)
        stripped = raw.strip()
        has_numpr = p.find(".//" + Wq + "numPr") is not None

        if has_tab:
            problems.append("paragraph %d: literal tab -- %r" % (i, stripped[:70]))

        m = _MULTISPACE.search(raw)
        if m:
            problems.append(
                "paragraph %d: %d consecutive spaces -- %r"
                % (i, len(m.group()), stripped[:70]))

        if has_numpr:
            if not in_numpr_run:
                problems.append("paragraph %d: w:numPr -- %r" % (i, stripped[:70]))
            in_numpr_run = True
        else:
            if in_numpr_run and stripped and _LEADING_DIGIT.match(raw):
                problems.append(
                    "paragraph %d: follows a w:numPr paragraph and starts with "
                    "a digit -- %r (confirm this is meant to continue that "
                    "list -- see questions_flow.py's _wrap_stmt_lists -- not a "
                    "fresh item that silently lost its own number)"
                    % (i, stripped[:70]))
            in_numpr_run = False
    return problems
