"""Extract worked solutions for RI 2024 H2 P1 (MCQ, no part structure).

Document shape: flat [Qn | explanation] 2-column grid across several
top-level tables (like RI P2's answers.py grid), but with NO part labels at
all -- a bare "Qn" in the first cell starts a new question, everything else
is that question's content. A handful of questions (13, 16, 25) carry a
nested comparison table inside their content cell.

Excluded from the live bank entirely (see ri-2024-h2-p1-tags.md /
HANDOFF.md SS6H): Q7, Q14, Q24, Q30 -- deliberately not ingested as
questions, so they get no worked_solution either.

Reuse note: this is the flat-table-grid MCQ shape (RI's own house style).
EJC 2024 H2 P1's answer doc is a DIFFERENT shape -- sequential paragraphs
ending in a summary table, not a [Qn|answer] grid (see
ejc-2024-h2-p1-ingest-notes.md) -- so `parse()` here will need a real flow-
shape rewrite for that paper, not just a filename/EXCLUDED swap. What IS
directly reusable for any flat-MCQ paper: `render_question()`'s no-`.part`
wrapper shape (confirmed against WA2's live rows, see ingest/README.md),
the FIG-sentinel-per-paragraph split for floating figures, and
`wrap_answer()`'s bare-if-lone-image rule.

Output feeds `gen_answers_migration.py --type mcq` (added 2026-09-27
alongside this script, since the existing generator only pinned
`q.type = 'structured'`).
"""
import re
import sys
import json

sys.path.insert(0, '/home/claude/chemistry-question-bank')
from lxml import etree
from ingest.oxml import NS, Wq, paragraph_html

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"

EXCLUDED = {7, 14, 24, 30}

QLABEL_RE = re.compile(r'^\s*Q\s*(\d+)\s*$', re.I)

# Figure filenames, in DOCUMENT ORDER, per question (confirmed against the
# reference PDF + user's own snip list).
FILENAMES = {
    12: ["RI_H2_P1_Q12_ans_2024.png"],
    22: ["RI_H2_P1_Q22_ans_2024.png"],
    23: ["RI_H2_P1_Q23_ans_2024.png"],
    25: [f"RI_H2_P1_Q25_ans-{c}_2024.png" for c in "abcdefgh"],
    26: ["RI_H2_P1_Q26_ans_2024.png"],
    27: ["RI_H2_P1_Q27_ans_2024.png"],
    28: ["RI_H2_P1_Q28_ans_2024.png"],
    29: ["RI_H2_P1_Q29_ans_2024.png"],
}


def cell_text(tc):
    return "".join(tc.itertext("{%s}t" % NS['w'])).strip() if False else \
        "".join(t.text or "" for t in tc.iter(Wq + "t")).strip()


def direct(el, tag):
    return [c for c in el if c.tag == Wq + tag]


def render_block_from_cell(tc):
    """Return a list of 'blocks': each is ('p', html) or ('table', rows).

    rows for a table block: list[list[str]] of per-cell rendered HTML
    (each cell's paragraphs joined with '<br>').
    """
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
                    row.append("<br>".join(paras))
                rows.append(row)
            blocks.append(("table", rows))
    return blocks


def parse(document_xml_path):
    tree = etree.parse(document_xml_path)
    body = tree.getroot().find("w:body", NS)

    questions = {}   # qnum -> list of blocks
    order = []
    current = None

    for tbl in direct(body, "tbl"):
        for tr in direct(tbl, "tr"):
            cells = direct(tr, "tc")
            if not cells:
                continue
            first_txt = cell_text(cells[0])
            m = QLABEL_RE.match(first_txt)
            if m:
                current = int(m.group(1))
                if current not in questions:
                    questions[current] = []
                    order.append(current)
                content_cells = cells[1:]
            else:
                if current is None:
                    continue
                content_cells = cells[1:] if len(cells) > 1 and not first_txt else cells
                if first_txt:
                    # a stray non-blank first cell on a continuation row:
                    # surface it rather than silently dropping content
                    if len(cells) > 1:
                        content_cells = cells
            for tc in content_cells:
                questions[current].extend(render_block_from_cell(tc))

    return questions, order


def wrap_answer(html):
    if not html.strip():
        return ""
    if re.fullmatch(r"\s*<img[^>]*>\s*", html) or \
       (html.strip().startswith("<img") and html.count("<img") == 1
        and re.fullmatch(r"\s*<img[^>]*>\s*", html.strip())):
        return html.strip()
    return '<span class="ans">%s</span>' % html


def render_question(qnum, blocks, filenames):
    it = iter(filenames)

    def sub_fig(_m):
        try:
            return '<img class="ws-fig" data-asset="%s" alt="">' % next(it)
        except StopIteration:
            raise ValueError(f"Q{qnum}: figure placeholder without a file")

    out = []
    for kind, payload in blocks:
        if kind == "p":
            centred = payload.startswith(CENTRE)
            payload = payload.replace(CENTRE, "")
            # A paragraph carrying a FIG sentinel ALONGSIDE real text is
            # usually a floating (wp:anchor) figure whose XML position is
            # not its visual position (README: "wp:anchor figures are
            # stored in a different row than they render in"). Rather than
            # cram <img> and prose into one <p> (looks squished, and wrongly
            # implies the figure sits inline with that sentence), split on
            # the sentinel into separate <p> blocks -- each following the
            # same bare-if-figure-only rule as everywhere else in the bank.
            segments = re.split(re.escape(FIG), payload)
            for i, seg in enumerate(segments):
                if i > 0:
                    out.append('<p>%s</p>' % sub_fig(None))
                inner = wrap_answer(seg)
                if not inner:
                    continue
                out.append('<p class="c">%s</p>' % inner if centred else "<p>%s</p>" % inner)
        elif kind == "table":
            rows_html = []
            for row in payload:
                cells_html = []
                for cell in row:
                    cell_sub = re.sub(re.escape(FIG), sub_fig, cell)
                    cells_html.append("<td>%s</td>" % cell_sub)
                rows_html.append("<tr>%s</tr>" % "".join(cells_html))
            out.append('<table class="cmp">%s</table>' % "".join(rows_html))
    leftover = list(it)
    if leftover:
        raise ValueError(f"Q{qnum}: unplaced figures left over: {leftover}")
    return '<div class="worked-solution">\n%s\n</div>' % "\n".join(out)


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "work/unz/word/document.xml"
    dest = sys.argv[2] if len(sys.argv) > 2 else "out/worked_solutions.json"

    questions, order = parse(doc)

    print(f"Questions found (document order): {order}")
    print(f"Count: {len(order)}")
    live = [q for q in order if q not in EXCLUDED]
    print(f"Live (excluding {sorted(EXCLUDED)}): {len(live)} -> {live}")

    results = {}
    for q in live:
        html = render_question(q, questions[q], FILENAMES.get(q, []))
        results[q] = html

    from pathlib import Path
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {dest} ({len(results)} questions)")
