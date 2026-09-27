"""Extract worked solutions for EJC 2024 H2 P1 (MCQ, paragraph-flow shape).

Document shape: paragraph-flow, NOT a table grid (contrast RI 2024 H2 P1's
extract_ri_p1_answers.py, which is a [Qn|answer] table). Every question's
content is a run of ordinary <w:p> paragraphs; the question boundary is the
bare single-letter answer paragraph at the end of each block (" B", " A",
...), located here by anchoring on the ALREADY-VERIFIED answer key sequence
from ejc-2024-h2-p1-ingest-notes.md, not by any digit-glued-to-text regex
(unreliable on this document -- see chat notes, 2026-09-28).

All 34 visuals in this document are OLE-embedded objects (19 Equation.DSMT4,
15 ChemDraw.Document.6.0) -- a fundamentally different situation from RI P1
(native Word drawings only, no OLE at all). Every one of the 19 equations was
visually reviewed and judged simple enough to type as real house markup (see
equations.py, sibling scratch module content now inlined below); all 15
ChemDraw structures need a manual snip EXCEPT one trivial "C=C" text
fragment (Q21's second object), which is typed directly. The user combined
Q4's four VSEPR shapes and Q23's four reaction schemes into one snipped
image each (chat, 2026-09-28), so those two questions have only ONE asset
slot despite having 4 OLE placeholders each in the source -- the first FIG
placeholder in each gets the <img>, the other three are dropped (already
shown in the combined picture).

`oxml.paragraph_html()` already turns any w:object into the \x00FIG\x00
sentinel (oxml.py line ~157) the same way it does an inline drawing, so this
extractor reuses it unmodified for all ordinary text/equation runs, and only
does manual FIG-sentinel substitution afterwards -- exactly the same pattern
RI P1's extractor uses for its own floating-figure FIG splits.

Three NEW Symbol/Wingdings codepoints were found and added to symbols.py
while building this extractor (F0AD/F0AF arrows, F0DE checkmark, F053
Sigma, F0FB/F0FC Wingdings checkbox pair) -- see that file's own comments
for the evidence trail. Do not assume a future EJC document uses the same
codes without re-checking; Word's Symbol/Wingdings PUA mapping is a font
setting, not a spec.

Output feeds `gen_answers_migration.py --type mcq --school EJC --paper 1`.
"""
import re
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/claude/chemistry-question-bank')
from lxml import etree
from ingest.oxml import NS, Wq, paragraph_html

CENTRE = "\x00C\x00"
FIG = "\x00FIG\x00"

# ---------------------------------------------------------------------------
# Verified answer key (ejc-2024-h2-p1-ingest-notes.md), used ONLY to anchor
# question boundaries -- the bare single-letter paragraph at the end of each
# block. The first 30 bare-letter paragraphs in document order match this
# sequence exactly (confirmed 2026-09-28); a further 30 appear later in a
# compact answer-key SUMMARY table at the end of the document and are
# correctly excluded by the [:30] slice below.
# ---------------------------------------------------------------------------
ANSWER_KEY = "B A B D A B A B C A B C C D C B B C B A B A D D A B C C B C".split()
assert len(ANSWER_KEY) == 30

FRAC = lambda num, den: ('<span class="frac"><span class="fnum">%s</span>'
                          '<span class="fden">%s</span></span>' % (num, den))

# 19 typed Equation.DSMT4 replacements -- see docstring; each one visually
# reviewed against the rendered WMF/EMF preview and (for Q13) matched to the
# house Ka/[H+] convention already live for this paper's Q13 OPTIONS
# (corrections.EQUATION_OPTIONS_AS_TEXT).
EQUATIONS = {
    'image1.wmf': '= %s &times; 0.32 g = 0.2238 g' % FRAC(
        '2 &times; 55.8', '2 &times; 55.8 + 3 &times; 16.0'),
    'image2.wmf': '% by mass of Fe in ore = ' + FRAC('0.2238', '0.6') + ' = 37.3%',
    'image3.wmf': 'n(Y<sup>2+</sup>) = %s &times; 0.400 = 0.0100 mol' % FRAC('25.0', '1000'),
    'image4.wmf': 'n(MnO<sub>4</sub><sup>&ndash;</sup>) = %s &times; 0.10 = 0.00400 mol' % FRAC('40.00', '1000'),
    'image5.wmf': FRAC('charge, <i>q</i>', 'mass, <i>m</i>') + ' ratio',
    'image6.wmf': '%s = 0.0417' % FRAC('1', '24'),
    'image7.wmf': '%s = 0.0625' % FRAC('3', '48'),
    'image8.wmf': '%s = 0.0339' % FRAC('2', '59'),
    'image9.wmf': '%s = 0.0396' % FRAC('4', '101'),
    'image10.wmf': FRAC('<i>q</i>', '<i>m</i>'),
    'image15.wmf': (FRAC('<i>p</i><sub>1</sub><i>V</i><sub>1</sub>', '<i>T</i><sub>1</sub>')
        + ' = ' + FRAC('<i>p</i><sub>2</sub><i>V</i><sub>2</sub>', '<i>T</i><sub>2</sub>')
        + ' &rArr; <i>p</i><sub>2</sub> = <i>p</i><sub>1</sub> &times; '
        + FRAC('<i>V</i><sub>1</sub>', '<i>V</i><sub>2</sub>')
        + ' &times; ' + FRAC('<i>T</i><sub>2</sub>', '<i>T</i><sub>1</sub>')),
    'image16.wmf': (
        '<i>p</i><sub>K</sub> = 40 kPa &times; %s &times; %s<br>= 8 kPa<br>'
        '<i>p</i><sub>L</sub> = 20 kPa &times; %s &times; %s<br>= 20 kPa'
        % (FRAC('100 cm&sup3;', '(100 + 400) cm&sup3;'),
           FRAC('(227 + 273) K', '(227 + 273) K'),
           FRAC('400 cm&sup3;', '(100 + 400) cm&sup3;'),
           FRAC('(227 + 273) K', '(127 + 273) K'))),
    'image17.wmf': 'final pressure of mixture = <i>p</i><sub>K</sub> + <i>p</i><sub>L</sub><br>= 8 kPa + 20 kPa<br>= 28 kPa',
    'image18.wmf': '%s &times; 100 = 60%%' % FRAC('1.2', '2.0'),
    'image19.wmf': '[H<sup>+</sup>] = 10<sup>&minus;2</sup> = 0.0100 mol dm<sup>&minus;3</sup>',
    'image20.wmf': ('[H<sup>+</sup>] after mixing = %s<br>= 0.00500 mol dm<sup>&minus;3</sup>'
        % FRAC('0.0100<i>V</i> + 0.0100<i>V</i>', '<i>V</i> + <i>V</i> + 2<i>V</i>')),
    'image21.wmf': 'pH = &minus;lg[H<sup>+</sup>] = &minus;lg(0.00500) = 2.3',
    'image22.wmf': ('<i>K</i><sub>a</sub> = %s &asymp; %s'
        % (FRAC('[H<sup>+</sup>][A<sup>&ndash;</sup>]', '[HA]'),
           FRAC('[H<sup>+</sup>][salt]', '[acid]'))),
    'image23.wmf': '[H<sup>+</sup>] &asymp; <i>K</i><sub>a</sub> %s' % FRAC('[acid]', '[salt]'),
}

# Every question's OLE objects, in document order, as (ProgID, media file).
# Built once from the docx's own w:object/o:OLEObject + v:imagedata rId ->
# target chain (see chat notes) -- hardcoded here since it does not change
# between runs and re-deriving it from the raw XML on every call would need
# the same rels-file plumbing this comment is standing in for.
QUESTION_OBJECTS = {
    1: ['image1.wmf', 'image2.wmf'],
    2: ['image3.wmf', 'image4.wmf'],
    3: ['image5.wmf', 'image6.wmf', 'image7.wmf', 'image8.wmf', 'image9.wmf', 'image10.wmf'],
    4: ['image11.emf', 'image12.emf', 'image13.emf', 'image14.emf'],
    5: ['image15.wmf', 'image16.wmf', 'image17.wmf'],
    11: ['image18.wmf'],
    12: ['image19.wmf', 'image20.wmf', 'image21.wmf'],
    13: ['image22.wmf', 'image23.wmf'],
    20: ['image24.emf', 'image25.emf'],
    21: ['image26.emf', 'image27.emf'],
    23: ['image28.emf', 'image29.emf', 'image30.emf', 'image31.emf'],
    25: ['image32.emf'],
    27: ['image33.emf'],
    28: ['image34.emf'],
}

# Per-question FIG substitution plan: what replaces each FIG placeholder, IN
# ORDER. 'EQ' = look up EQUATIONS by that question's next media filename.
# An explicit string replaces the placeholder literally (typed structure
# text, or an <img>). None DROPS the placeholder entirely (already shown by
# an earlier combined image in the same question -- Q4 and Q23, combined
# into one snip each per the user's explicit instruction, 2026-09-28).
ASSET_IMG = {
    4:  '<img class="ws-fig" data-asset="EJC_H2_P1_Q4_ans_2024.png" alt="">',
    20: ['<img class="ws-fig" data-asset="EJC_H2_P1_Q20_ans-a_2024.png" alt="">',
         '<img class="ws-fig" data-asset="EJC_H2_P1_Q20_ans-b_2024.png" alt="">'],
    21: ['<img class="ws-fig" data-asset="EJC_H2_P1_Q21_ans_2024.png" alt="">',
         'C=C'],
    23: '<img class="ws-fig" data-asset="EJC_H2_P1_Q23_ans_2024.png" alt="">',
    25: '<img class="ws-fig" data-asset="EJC_H2_P1_Q25_ans_2024.png" alt="">',
    27: '<img class="ws-fig" data-asset="EJC_H2_P1_Q27_ans_2024.png" alt="">',
    28: '<img class="ws-fig" data-asset="EJC_H2_P1_Q28_ans_2024.png" alt="">',
}


def fig_replacements(qnum):
    """Ordered list of literal strings (or None to drop) for each FIG in
    this question, matching QUESTION_OBJECTS[qnum] 1:1."""
    objs = QUESTION_OBJECTS.get(qnum, [])
    if qnum in (4, 23):
        # combined single snip: first placeholder gets the image, the rest
        # are already shown in it
        return [ASSET_IMG[qnum]] + [None] * (len(objs) - 1)
    if qnum == 20:
        return list(ASSET_IMG[20])
    if qnum == 21:
        return list(ASSET_IMG[21])
    if qnum in ASSET_IMG:
        return [ASSET_IMG[qnum]]
    # everything else is an equation
    return [EQUATIONS[fn] for fn in objs]


def cell_text(p):
    return "".join(t.text or "" for t in p.iter(Wq + "t"))


def find_boundaries(paras):
    ans_re = re.compile(r'^\s*([A-D])\s*$')
    hits = [i for i, p in enumerate(paras) if ans_re.match(cell_text(p))]
    boundaries = hits[:30]
    letters = [cell_text(paras[i]).strip() for i in boundaries]
    if letters != ANSWER_KEY:
        raise ValueError("answer-key mismatch at boundary detection: "
                          "got %r, expected %r" % (letters, ANSWER_KEY))
    return boundaries


def strip_qnum_prefix(html, qnum):
    """Strip this question's own leading number (however it was typed --
    bold, plain, followed by a tab, glued to the next word) from the FIRST
    paragraph of its block. The prefix is always the literal digits of
    `qnum`, immediately after any opening <b> tag.

    Only the DIGITS are removed, never the `<b>` tag itself: the qnum often
    shares one continuous bold run with real content after it (e.g. Q4's
    "<b>4\\tA☐</b>" -- the "4" and the option letter "A" are one run),
    and deleting the whole match would either leave an orphaned `</b>` with
    no opener, or silently un-bold content that should stay bold to match
    its sibling options (B/C/D keep theirs). `_strip_empty_b` below cleans
    up the one case this leaves behind: a run that really was JUST the
    number, now an empty `<b></b>`."""
    prefix = str(qnum)
    m = re.match(r'^(<b>)?' + re.escape(prefix), html)
    if not m:
        raise ValueError("Q%d: expected leading '%s', got %r" % (qnum, prefix, html[:30]))
    tag = m.group(1) or ""
    return tag + html[m.end():]


def _strip_empty_b(html):
    return re.sub(r'<b>\s*</b>', '', html)


def render_block(qnum, paras, start, end):
    """Render one question's worked_solution body (no outer wrapper -- flat
    MCQ shape, style-guide.md #6)."""
    fig_queue = iter(fig_replacements(qnum))
    out = []
    first_content_seen = False

    for i in range(start, end):  # end is the answer-letter paragraph, excluded
        html = paragraph_html(paras[i])
        if not html.strip():
            continue

        # CENTRE sentinel is the very first bytes of the string (added by
        # paragraph_html AFTER the body), so it must come off BEFORE the
        # qnum-prefix strip below, which expects the string to start with
        # an optional `<b>` and then the digits themselves.
        centred = html.startswith(CENTRE)
        html = html.replace(CENTRE, "")

        if not first_content_seen:
            html = _strip_empty_b(strip_qnum_prefix(html, qnum))
            first_content_seen = True

        # substitute FIG placeholders in order
        def _sub(_m):
            try:
                repl = next(fig_queue)
            except StopIteration:
                raise ValueError("Q%d: FIG placeholder with no replacement left" % qnum)
            return repl if repl is not None else ""
        html = re.sub(re.escape(FIG), _sub, html)

        # collapse tabs used as label/content separators (checkbox-letter or
        # statement-number lead-ins, e.g. "A☐:\tForward reaction...")
        # to a single space -- typed indentation, not the .eqn trailing-
        # label-alignment convention (style-guide.md #2), which is for a
        # VALUE aligned after real content, not a label before it.
        html = re.sub(r'\s*\t\s*', ' ', html).strip()
        if not html:
            continue

        out.append('<p class="c">%s</p>' % html if centred else '<p>%s</p>' % html)

    leftover = list(fig_queue)
    if leftover:
        raise ValueError("Q%d: %d unplaced FIG replacement(s) left over" % (qnum, len(leftover)))
    return "\n".join(out)


def parse(document_xml_path):
    tree = etree.parse(document_xml_path)
    body = tree.getroot().find("w:body", NS)
    paras = list(body.iter(Wq + "p"))

    boundaries = find_boundaries(paras)
    starts = [4] + [b + 1 for b in boundaries[:-1]]

    results = {}
    for qnum, (s, e) in enumerate(zip(starts, boundaries), start=1):
        results[qnum] = '<div class="worked-solution">\n%s\n</div>' % render_block(qnum, paras, s, e)
    return results


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "work/unz/word/document.xml"
    dest = sys.argv[2] if len(sys.argv) > 2 else "out/worked_solutions.json"

    results = parse(doc)
    print(f"Questions rendered: {sorted(results)}")
    print(f"Count: {len(results)}")

    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {dest} ({len(results)} questions)")
