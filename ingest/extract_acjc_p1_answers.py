"""Extract worked solutions for ACJC 2024 H2 P1 (MCQ, table-per-question shape).

Document shape: a FOURTH distinct answer-doc shape for this bank (contrast
RI's flat [Qn|answer] grid, extract_ri_p1_answers.py, and EJC's paragraph-
flow doc, extract_ejc_p1_answers.py). ACJC's solutions docx is one Word
TABLE per question -- reproducing the stem, then each option A-D as its own
row, then a trailing row holding the actual worked explanation. There is no
formatting (bold/shading) marking which option is correct inside a
question's own table; the correct letter lives in a SEPARATE compact
answer-key summary table (5 rows x 12 cols, "1 D 6 B 11 C ...") elsewhere in
the document -- see ACJC_ANSWER_KEY below.

Q27 has NO table in this document at all (consistent with the paper's own
skip list -- Q26 and Q27 were excluded from the live bank at the questions
stage; Q26 has a table here but is dropped by SKIP below for the same
reason).

Explanation-row detection: an option row is identified structurally -- any
cell whose text is exactly one of A-E AND is bold. The LAST such row's index
+ 1 starts the explanation; everything from there to the end of the table is
walked the same way RI's extractor walks a part's content cell (paragraphs
-> <p>, a nested w:tbl -> <table class="cmp">), reusing that script's
`wrap_answer` bare-if-lone-image rule and FIG-sentinel substitution
approach almost unchanged.

Figures: two questions (Q16, Q19) have an explanation that is ENTIRELY
image content with no separately-extractable text -- Q16 additionally has
"amine"/"nitrile" pointer-arrow labels baked inside floating text-box
shapes anchored to the picture (wps:txbx-style overlay, the same pattern
already documented for EJC 2024 H2 P2's answer doc), which are therefore
NOT visible to paragraph_html() at all (it treats the whole w:drawing as one
opaque FIG sentinel) -- consistent with asking the user to hand-snip the
WHOLE composed area rather than trying to reconstruct the labels as text.
Both are user-supplied hand-snips (bare image, no surrounding typed text,
style-guide.md #6's combined-figure convention).

Five more questions have a SIMPLE embedded OLE object sitting inline in
otherwise-real explanation text: Q1 (the same "9/2" stoichiometric
coefficient, embedded twice), Q12 ("1/2"), Q14 (the Kw expression), Q22 and
Q24 (x2). Corrected 2026-09-28 after live-site review: Q1/Q12/Q14 are all
`ProgID="Equation.DSMT4"` -- pure numeric/algebraic fractions, not
pictures. An earlier pass cropped all five as images regardless of ProgID,
per what was (mis)read as the user's request; that reading was wrong on two
counts, both found only once the user reported what actually rendered:

1. This bank already has a standing rule for exactly this ProgID -- see RI
   2024 H2 P1's own questions-stage notes (`claude/handoff-archive-
   2026-09-24.md`): "ProgID decides block vs inline: ... `Equation.DSMT4`
   are maths. ... READ off the Word PDF and emitted as `span.frac`, not
   cropped." Q1/Q12/Q14 are exactly that case (verified against
   `work/answers_unz`: `ProgID="Equation.DSMT4"` x5, one each in Q1 (x2,
   same value) /Q12/Q14; the SIXTH object, Q22's, is
   `ProgID="ChemDraw_x64.Document.6.0"` -- a genuine picture, correctly
   still cropped. Q24's two figures carry no ProgID at all -- plain
   `w:drawing`/`pic:pic` -- also genuine pictures, correctly cropped).
2. Regardless of ProgID, `index.html`'s `img.q-fig, img.ws-fig` rule is
   unconditionally `display:block`. An image substituted INLINE mid-
   sentence (the approach below, `FIG` substituted in place within one
   `<p>`) still renders as a block box once the browser lays it out --
   CSS forces an anonymous-block split around it, breaking one sentence
   into three stacked, disconnected-looking lines. This is what the user
   saw as "weird floating fractions" (Q1/Q14) and a "diagram bleeding into
   the question" (Q22, and by the same mechanism Q24, not separately
   named but carrying the identical defect).

Fix, entirely on the content side (no `index.html`/CSS change):
Q1/Q12/Q14's three equation objects are now typed as `span.frac` markup
(`FRAC_REPLACEMENTS` below), matching the bank's one fraction convention
and needing no image asset at all. Q22/Q24's three genuine pictures stay as
`<img class="ws-fig">`, but each now gets ITS OWN paragraph (`render_
question`'s "p" branch below splits payload on the FIG sentinel into
separate `<p>` blocks) instead of sitting mid-sentence -- consistent with
the CSS block-display it will get regardless, and with how Q16/Q19's own
bare-image explanations already render cleanly.

Two new Symbol/Wingdings codepoints were found and added to symbols.py
while building this extractor: Wingdings F0E0 (a reaction arrow, all 7
occurrences -- a first pass mistook an unrelated literal minus sign a few
words after one of them, in Q10, for an 8th occurrence of the same glyph;
see the symbols.py comment for why that reading was wrong) and Symbol F0B8
(divide, two straightforward division steps in Q29/Q30).

`corrections.apply()` (ingest/corrections.py) is run on every question's
assembled body HTML, scoped to ("ACJC", "H2", "P1", 2024), for consistency
with every other extractor in this bank -- there is currently no ACJC-scoped
entry, so this is a no-op until one is needed.

Output feeds `gen_answers_migration.py --type mcq --school ACJC --paper 1`.
"""
import re
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/claude/tanyk1993/chemistry-question-bank')
from lxml import etree
from ingest.oxml import NS, Wq, paragraph_html
from ingest import corrections

SCOPE = ("ACJC", "H2", "P1", 2024)
SKIP = {26, 27}

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"

# Verified from the document's own compact answer-key summary table
# (5 rows x 12 cols: "1 D 6 B 11 C 16 A 21 D 26 B" / "2 B 7 A 12 C 17 D 22 C
# 27 B" / ...), cross-checked against each question's own explanation text
# where it names the correct option (e.g. Q10 "A is correct", Q22 "Student
# E is correct"). All 30, including the 2 excluded from the live bank.
ANSWER_KEY = {
    1: "D", 2: "B", 3: "B", 4: "C", 5: "D", 6: "B", 7: "A", 8: "D", 9: "A",
    10: "B", 11: "C", 12: "C", 13: "D", 14: "A", 15: "D", 16: "A", 17: "D",
    18: "D", 19: "C", 20: "A", 21: "D", 22: "C", 23: "B", 24: "C", 25: "B",
    26: "B", 27: "B", 28: "B", 29: "B", 30: "D",
}

# Questions whose ENTIRE explanation is one bare image (no typed text
# survives alongside it -- style-guide.md #6's bare-image convention for a
# combined/composed figure). Rendered directly, bypassing the normal block
# walk. Q16/Q19 are user hand-snips (composed diagram + labels, see the
# module docstring). Q1 joined this set 2026-09-28, after a live-site
# review: its two Equation.DSMT4 "9/2" fractions were first typed as
# span.frac (matching Q12/Q14 below), but the SECOND paragraph --
# "40    80  40  160", the volumes lined up under each term of the
# equation above via literal tabs -- relies on white-space:pre-wrap, which
# `.ws`/`.worked-solution` paragraphs don't get (only `.stem p.eqn` does).
# Without it the tabs collapse to single spaces and the alignment that
# makes the line mean anything is lost ("the numbers are not rendering
# below the equation"). Rather than add a CSS rule for one paragraph, the
# whole block (equation + aligned volumes + the second calculation line)
# is cropped as ONE image straight from the answers PDF page (page index 1,
# the vector text itself -- not an OLE-object screenshot), preserving the
# source's own alignment exactly. `work/final_assets/ACJC_H2_P1_Q1_ans_
# 2024.png` replaces the earlier (now-wrong) Q1 crop of just the "9/2".
BARE_IMAGE = {
    1: "ACJC_H2_P1_Q1_ans_2024.png",
    16: "ACJC_H2_P1_Q16_ans_2024.png",
    19: "ACJC_H2_P1_Q19_ans_2024.png",
}

# Q12/Q14's Equation.DSMT4 objects are pure fractions -- typed as span.frac
# (the bank's one fraction convention, index.html's bare, unscoped
# `.frac`/`.fnum`/`.fden` rules), never cropped as images. Values verified
# against the surrounding worked arithmetic: Q12 "k[2a]^1[1/2 a]^2[4a]^2 =
# 8ka^5" (2^1 x (1/2)^2 x 4^2 = 8, matching); Q14 is the Ka expression
# itself, read straight off the surrounding "(Ka = ...)" text in the Word
# PDF. (Q1 had a third such object, also "9/2" -- see BARE_IMAGE above for
# why it ended up handled differently.)
FRAC_REPLACEMENTS = {
    12: '<span class="frac"><span class="fnum">1</span><span class="fden">2</span></span>',
    14: ('<span class="frac"><span class="fnum">[H<sup>+</sup>][OH<sup>−</sup>]</span>'
         '<span class="fden">[H<sub>2</sub>O]</span></span>'),
}

# Per-question FIG replacement plan, in document order, for the two
# questions whose figure is a genuine picture (Q22's ChemDraw fragment,
# Q24's two plain w:drawing structure fragments -- see module docstring).
# Q1 (whole-answer bare image) and Q12/Q14 (span.frac) never reach this
# dict.
FIG_ASSETS = {
    22: ["ACJC_H2_P1_Q22_ans_2024.png"],
    24: ["ACJC_H2_P1_Q24_ans-a_2024.png", "ACJC_H2_P1_Q24_ans-b_2024.png"],
}

# question -> [(slot, path), ...] for gen_answers_migration.py's assets
# file. Q12/Q14 are text (span.frac) and need no row.
#
# Slot naming, corrected 2026-09-28: index.html's `isAnswerSlot` is
# `/^(ans|sol)[-_]/i` -- it requires a HYPHEN OR UNDERSCORE after "ans",
# so a bare slot of exactly "ans" (what every single-figure question here
# used until now) does NOT match it and is therefore NOT filtered out of
# the STEM-side asset list (`qAssets = q.assets.filter(a =>
# !isAnswerSlot(a.slot))` keeps it, wrongly, because isAnswerSlot("ans")
# is false). For Q16/Q19 this stayed invisible by accident: they already
# have one stem-side `.fig` placeholder, which consumes the first stem
# asset slot and leaves the (wrongly-included) answer asset never
# appended (`if(!placed)` short-circuits once any image lands). Q22 has
# NO stem-side figure at all, so nothing "absorbs" it -- its answer image
# was appended straight into the stem, unconditionally, visible without
# ever clicking "Show answer" ("the alcohol structure still appears in
# the stem"). Fixed at the source: every single-figure slot below is now
# suffixed ("ans-1"), matching the convention this bank already uses for
# multi-figure questions (Q24's "ans-a"/"ans-b", gen_answers_migration.py's
# own docstring example "ans-cv") -- never bare "ans" again.
ANSWER_ASSETS = [
    (1, "ans-1", "ACJC_H2_P1_Q1_ans_2024.png"),
    (16, "ans-1", "ACJC_H2_P1_Q16_ans_2024.png"),
    (19, "ans-1", "ACJC_H2_P1_Q19_ans_2024.png"),
    (22, "ans-1", "ACJC_H2_P1_Q22_ans_2024.png"),
    (24, "ans-a", "ACJC_H2_P1_Q24_ans-a_2024.png"),
    (24, "ans-b", "ACJC_H2_P1_Q24_ans-b_2024.png"),
]


def direct(el, tag):
    return [c for c in el if c.tag == Wq + tag]


def cell_text(tc):
    return "".join(t.text or "" for t in tc.iter(Wq + "t")).strip()


def is_opt_row(tr):
    for tc in direct(tr, "tc"):
        if cell_text(tc) in ("A", "B", "C", "D", "E"):
            for r in tc.iter(Wq + "r"):
                rPr = r.find(Wq + "rPr")
                b = rPr.find(Wq + "b") if rPr is not None else None
                if b is not None:
                    return True
    return False


def cell_colspan(tc):
    """A w:gridSpan on a nested-table cell means it visually spans that many
    grid columns (Q13's ICE table: the "4Q(g) + R(g) [arrow] S(g)" header
    cell spans the same 3 columns the I/C/E rows fill with Q/R/S values).
    Emitting a plain <td> without colspan silently under-counts that row
    against its siblings -- the header lands 2 cells wide while the data
    rows are 4, so the columns no longer line up. Returns None (no
    attribute) when there's no gridSpan, matching the common case."""
    tcPr = tc.find(Wq + "tcPr")
    if tcPr is None:
        return None
    gs = tcPr.find(Wq + "gridSpan")
    if gs is None:
        return None
    val = gs.get(Wq + "val")
    return int(val) if val else None


def render_block_from_cell(tc):
    """Same shape as extract_ri_p1_answers.py's helper of the same name."""
    blocks = []
    for child in tc:
        if child.tag == Wq + "p":
            html = paragraph_html(child)
            if html and html.strip():
                blocks.append(("p", html))
        elif child.tag == Wq + "tbl":
            rows = []
            for tr in direct(child, "tr"):
                row = []
                for cell in direct(tr, "tc"):
                    paras = []
                    for p in direct(cell, "p"):
                        h = paragraph_html(p)
                        if h and h.strip():
                            paras.append(h.replace(CENTRE, ""))
                    row.append(("<br>".join(paras), cell_colspan(cell)))
                rows.append(row)
            blocks.append(("table", rows))
    return blocks


def parse_blocks(document_xml_path):
    """{qnum: [blocks]} for every retained question's explanation region."""
    tree = etree.parse(document_xml_path)
    body = tree.getroot().find("w:body", NS)
    qtables = direct(body, "tbl")[2:]

    out = {}
    for tbl in qtables:
        rows = direct(tbl, "tr")
        qnum = int(cell_text(direct(rows[0], "tc")[0]))
        if qnum in SKIP:
            continue
        opt_idx = [i for i, tr in enumerate(rows[1:], start=1) if is_opt_row(tr)]
        last_opt = max(opt_idx) if opt_idx else 0
        blocks = []
        for tr in rows[last_opt + 1:]:
            for tc in direct(tr, "tc"):
                blocks.extend(render_block_from_cell(tc))
        out[qnum] = blocks
    return out


def wrap_answer(html):
    if not html.strip():
        return ""
    if re.fullmatch(r"\s*<img[^>]*>\s*", html):
        return html.strip()
    return '<span class="ans">%s</span>' % html


def render_question(qnum, blocks):
    if qnum in BARE_IMAGE:
        img = '<img class="ws-fig" data-asset="%s" alt="">' % BARE_IMAGE[qnum]
        return '<div class="worked-solution">\n<p>%s</p>\n</div>' % img

    it = iter(FIG_ASSETS.get(qnum, []))

    def sub_fig(_m):
        try:
            return '<img class="ws-fig" data-asset="%s" alt="">' % next(it)
        except StopIteration:
            raise ValueError(f"Q{qnum}: FIG placeholder with no replacement left")

    frac = FRAC_REPLACEMENTS.get(qnum)

    out = []
    for kind, payload in blocks:
        if kind == "p":
            centred = payload.startswith(CENTRE)
            payload = payload.replace(CENTRE, "")
            if frac is not None:
                # Equation.DSMT4 fraction: typed text, stays inline in the
                # same paragraph as the surrounding prose (it has a text
                # baseline to sit on, unlike a real picture -- see below).
                payload = re.sub(re.escape(FIG), lambda _m: frac, payload)
                inner = wrap_answer(payload)
                if inner:
                    out.append('<p class="c">%s</p>' % inner if centred else "<p>%s</p>" % inner)
            elif FIG in payload:
                # A genuine picture (Q22/Q24): index.html's img.ws-fig rule
                # is unconditionally display:block, so an inline mid-
                # sentence placement gets forced onto its own box by the
                # browser regardless of the markup -- splitting the
                # sentence into disconnected-looking fragments around it.
                # Give it that own paragraph explicitly instead of fighting
                # the CSS: split on FIG, each image becomes its own bare
                # <p><img></p>, same treatment Q16/Q19's bare-image
                # explanations already get cleanly.
                parts = payload.split(FIG)
                for i, part in enumerate(parts):
                    text = part.strip()
                    if text:
                        inner = wrap_answer(text)
                        if inner:
                            out.append("<p>%s</p>" % inner)
                    if i < len(parts) - 1:
                        img_html = sub_fig(None)
                        # A short punctuation-only tail right after THIS
                        # image (a bare "." closing the sentence, say)
                        # reads as an orphaned line of its own -- fold it
                        # into the image's paragraph instead. Only trips
                        # for a tail with no letters/digits, so real
                        # trailing prose (Q24's "or carbonyl compounds...")
                        # is untouched and still gets its own <p>.
                        nxt = parts[i + 1].strip() if i + 1 < len(parts) else ""
                        if nxt and len(nxt) <= 3 and not re.search(r"[A-Za-z0-9]", nxt):
                            img_html += '<span class="ans">%s</span>' % nxt
                            parts[i + 1] = ""
                        out.append("<p>%s</p>" % img_html)
            else:
                inner = wrap_answer(payload)
                if inner:
                    out.append('<p class="c">%s</p>' % inner if centred else "<p>%s</p>" % inner)
        elif kind == "table":
            rows_html = []
            for row in payload:
                cells_html = []
                for text, colspan in row:
                    text = re.sub(re.escape(FIG), (lambda _m: frac) if frac is not None else sub_fig, text)
                    attr = ' colspan="%d"' % colspan if colspan else ""
                    cells_html.append("<td%s>%s</td>" % (attr, text))
                rows_html.append("<tr>%s</tr>" % "".join(cells_html))
            out.append('<table class="cmp">%s</table>' % "".join(rows_html))

    leftover = list(it)
    if leftover:
        raise ValueError(f"Q{qnum}: unplaced FIG replacement(s) left over: {leftover}")

    body = "\n".join(out)
    body, log = corrections.apply(body, SCOPE)
    if log:
        print(f"Q{qnum} corrections applied: {log}")
    return '<div class="worked-solution">\n%s\n</div>' % body


def parse(document_xml_path):
    blocks_by_q = parse_blocks(document_xml_path)
    return {q: render_question(q, blocks) for q, blocks in blocks_by_q.items()}


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "work/answers_unz/word/document.xml"
    dest = sys.argv[2] if len(sys.argv) > 2 else "work/out/worked_solutions.json"

    results = parse(doc)
    live = sorted(results)
    print(f"Questions rendered: {live}")
    print(f"Count: {len(live)}")

    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w") as f:
        json.dump({str(q): html for q, html in results.items()}, f, indent=2)
    print(f"\nwrote {dest} ({len(results)} questions)")
