"""Extract worked solutions + answer key for DHS 2024 H2 P1 (9729/01, MCQ).

Document shape: a SIXTH answer-doc shape for this bank, close to ACJC P1's
(one Word table per question) but not the same:

  * a compact ANSWER KEY table first (rows of question numbers over rows of
    letters, a blank spacer column between 1-5 and 6-10, etc.);
  * then ONE TABLE PER QUESTION. Row 0 is [number | key], the key cell holding
    the correct letter as its first paragraph and, in some questions, the first
    lines of the explanation after it (Q1, Q21, Q23, Q24, Q26, Q28, Q29).
    Later rows are one of
      - [mark | label | text]   per-option / per-statement verdict (3 cells):
        mark = a Wingdings 2 tick or cross, or the words "correct"/"incorrect"
        (Q30); the TEXT is the school's explanation of that option, so unlike
        ACJC these rows are the content, not the stem restated;
      - [blank | text]          the explanation (2 cells);
      - one cell spanning both columns (a nested table or a figure).
  * the answers are plain black text; there is no coloured answer layer.

Rendering (house style, style-guide.md section 6, flat MCQ shape: NO div.part):
  div.worked-solution > p / table.cmp. A run of consecutive per-option rows
  becomes ONE `table.cmp` with columns [mark | label | explanation] (no th, no
  thead), mirroring the printed table; every other row's text becomes `<p>`s.
  A nested Word table inside a cell is rendered as a nested `table.cmp`.

Everything editorial is DECLARED and PINNED here, and the run raises if a
declaration does not match what the document holds:
  * FIG_PLAN       the user's hand-snips, per question, in document order. The
                   count of figure sentinels after collapsing MUST equal the
                   plan, or the run stops (a figure silently missing or landing
                   on the wrong placeholder is the costliest defect, HANDOFF 7).
  * the answer key is read from the key table AND from each question's own row
    0, and both are cross-checked against the letters printed in the Word PDF.

Symbols: Wingdings 2 F050 tick / F04F cross (21 / 20 occurrences, matching the
printed marks), Wingdings F0F0 white right arrow ("Concept: [arrow] ..."),
Symbol F0BA equivalence (Q26). Symbol F0DE is a tick in EJC's document but the
double arrow "=>" in THIS one (Q3, "=> Options A & C are incorrect"); it is
rewritten to a literal "=>" in the tree before parsing, never in symbols.py.

Output (in <outdir>): worked_solutions.json, answer_key.json,
answer_assets.json, anomalies.txt.  Feeds
`gen_answers_migration.py --type mcq --school DHS --paper 1 --answer-key ...`.

Usage:
  python3 -m ingest.extract_dhs_p1_answers <unzipped docx dir> <answers.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf
from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("DHS", "H2", "P1", 2024)
FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"

# User hand-snips, per question, in DOCUMENT ORDER (after collapsing adjacent
# figure sentinels that make up ONE printed picture). slot -> filename is
# DHS_H2_P1_Q<n>_<slot>_2024.png. Single figure -> "ans-1"; several -> ans-a..
FIG_PLAN = {
    5: ["ans-1"],                 # the WHOLE shape/polarity table, one snip (user choice)
    9: ["ans-1"],                 # the energy-cycle diagram under statement 2
    18: ["ans-1"],                # annotated structure (sp carbons circled)
    19: ["ans-1"],                # scopolamine with chiral carbons starred
    20: ["ans-1"],                # ethane with its carbons labelled x and y
    24: ["ans-a", "ans-b"],       # the R -> S + T scheme; the three alkenes
    27: ["ans-1"],                # the threonine zwitterion, inside a sentence
}
#: a picture that sits inside a line of text (index.html forces
#: img.ws-fig to display:block; an inline style beats the stylesheet).
INLINE_FIGS = {(27, "ans-1")}
#: whole-table snips: question -> (pattern of the one table to swap for the picture)
WHOLE_TABLE_FIGS = {5}
#: the user named this file themselves; the slot stays "ans-1" so isAnswerSlot holds
PATH_OVERRIDE = {(5, "ans-1"): "DHS_H2_P1_Q5_ans_2024.png"}
INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"

# Pinned text edits: (qnum, regex, replacement, expected_count, reason)
TEXT_FIXES: list = [
    (16, r"10<sup>\u221214\u00f7</sup>", "10<sup>\u221214</sup> \u00f7", 3,
     "divide sign typed inside the superscript"),
    (17, r'\u221a<span style="text-decoration:overline">(.*?)</span>',
     r'<span class="sqrt"><span class="rad">\1</span></span>', 1,
     "house square-root markup, no inline style"),
    (11, r'<p><span class="ans">&emsp;(<span class="sr">I</span><sub>x</sub>O<sub>y</sub>)\s+:\s+(<span class="sr">I</span><sup>\u2212</sup>)\s+:\s+(<span class="sr">I</span><sub>2</sub>)</span></p>\n'
         r'<p><span class="ans">0\.02\s*:\s*0\.2\s*:\s*0\.12</span></p>\n'
         r'<p><span class="ans">1&emsp;:\s*10\s*:&emsp;6</span></p>',
     r'<table class="cmp"><tr><td>\1</td><td>\2</td><td>\3</td></tr>'
     r'<tr><td>0.02</td><td>0.2</td><td>0.12</td></tr>'
     r'<tr><td>1</td><td>10</td><td>6</td></tr></table>', 1,
     "space-aligned ratio lines rebuilt as a small table"),
    (1, r'<p><span class="ans">P: \[Ne\]3s<sup>2</sup>3p<sup>3</sup></span></p>\n'
        r'<p><span class="ans">No\. of unpaired electrons = 3</span></p>\n', "", 1,
     "stray phosphorus working (not part of Q1), removed at the user's request"),
    (15, r'<p>(<span class="ans">M\(OH\)<sub>2</sub>\(s\).*?</span>)</p>', r'<p class="c">\1</p>', 1,
     "dissociation equation centred"),
    (17, r"required to ppt each", "required to precipitate each", 1, "spell out ppt"),
    (17, r"minimum \[Ag<sup>\+</sup>\] to ppt AgC", "minimum [Ag<sup>+</sup>] to precipitate AgC", 1, "spell out ppt"),
    (17, r"to ppt Ag<sub>2</sub>CrO<sub>4</sub>", "to precipitate Ag<sub>2</sub>CrO<sub>4</sub>", 1, "spell out ppt"),
    (17, r"will be ppt out first", "will be precipitated out first", 1, "spell out ppt (passive)"),
]


def direct(el, tag):
    return [c for c in el if c.tag == Wq + tag]


def cell_text(tc):
    return "".join(t.text or "" for t in tc.iter(Wq + "t")).strip()


def colspan(tc):
    pr = tc.find(Wq + "tcPr")
    g = pr.find(Wq + "gridSpan") if pr is not None else None
    return int(g.get(Wq + "val")) if g is not None else 1


def _indent_gap(s):
    return sum(4 if c == "\t" else 1 for c in s)


def clean(html: str) -> str:
    """Source typing slips that render wrongly (all seen in this document):
    zero-width spaces; spaces / trailing punctuation typed INSIDE a <sub>/<sup>
    ("1 </sub>=<sub> </sub>", "CO<sub>2. </sub>"); a proportional sign typed as a
    subscript; a times sign wrapped in the serif-run span (.sr is for Roman
    numerals and the element I, not for operators)."""
    html = html.replace("​", "")
    html = re.sub(r"<(sub|sup)>(\s+)</\1>", r"\2", html)
    html = re.sub(r"<(sub|sup)>([^<]*?[^<\s.,;:])([.,;:\s]+)</\1>", r"<\1>\2</\1>\3", html)
    html = re.sub(r"<sub>(∝\s*)</sub>", r"\1", html)
    html = re.sub(r'<span class="sr">([×\s]+)</span>', r"\1", html)
    return html


def tidy(html: str) -> str:
    """Whitespace alignment -> &emsp; (HTML collapses runs of spaces/tabs and
    `.ws` paragraphs have no pre-wrap)."""
    html = clean(html)
    html = html.rstrip(" \t ")
    html = re.sub(r"^(?:[ \t ]|&nbsp;)*<br>", "", html)
    html = re.sub(r"\s*<br>\s*", " ", html)
    m = re.match(r"^([ \t ]+)", html)
    lead = ""
    if m:
        w = _indent_gap(m.group(1))
        html = html[m.end():]
        if w >= 4:
            lead = "&emsp;" * min(8, max(1, round(w / 8)))

    def gap(mm):
        w = _indent_gap(mm.group(0))
        return "&emsp;" * (1 if w <= 7 else 2 if w <= 20 else 3)

    html = re.sub(r"[  ]*\t[ \t ]*|[  ]{4,}", gap, html)
    return lead + html.rstrip()


def load_body(unz: Path):
    tree = etree.parse(str(unz / "word/document.xml"))
    body = tree.getroot().find("w:body", NS)
    # Symbol F0DE is "=>" here (EJC's document uses it as a tick): see docstring.
    n = 0
    for s in list(body.iter(Wq + "sym")):
        if s.get(Wq + "font") == "Symbol" and s.get(Wq + "char").upper() == "F0DE":
            t = etree.Element(Wq + "t")
            t.text = "⇒"
            s.getparent().replace(s, t)
            n += 1
    return body, n


def para_html(p):
    h = paragraph_html(p)
    return h if h is not None else ""


def collapse_figs(h: str) -> str:
    """Adjacent figure sentinels with nothing between them are ONE picture."""
    return re.sub(r"(?:%s\s*)+" % re.escape(FIG), FIG, h)


def cell_blocks(tc):
    """[("p", html) | ("blank",) | ("table", tbl_element)] in document order."""
    out = []
    for ch in tc:
        if ch.tag == Wq + "p":
            h = para_html(ch)
            if not re.sub(r"<[^>]+>|&nbsp;|\s", "", h.replace(CENTRE, "")
                          .replace(FIG, "F")):
                out.append(("blank",))
            else:
                out.append(("p", collapse_figs(h)))
        elif ch.tag == Wq + "tbl":
            out.append(("table", ch))
    return out


def nested_table_html(tbl) -> str:
    rows = []
    for tr in direct(tbl, "tr"):
        cells = []
        for tc in direct(tr, "tc"):
            cs = colspan(tc)
            attr = ' colspan="%d"' % cs if cs > 1 else ""
            cells.append("<td%s>%s</td>" % (attr, cell_inline(tc)))
        rows.append("<tr>%s</tr>" % "".join(cells))
    return '<table class="cmp">%s</table>' % "".join(rows)


def cell_inline(tc) -> str:
    """A cell's content as inline HTML: paragraphs joined by <br>, a blank
    paragraph kept as one extra <br> (max one), nested tables in place."""
    parts = []
    for b in cell_blocks(tc):
        if b[0] == "p":
            parts.append(tidy(b[1].replace(CENTRE, "")))
        elif b[0] == "blank":
            if parts and parts[-1] != "":
                parts.append("")
        else:
            parts.append(nested_table_html(b[1]))
    while parts and parts[-1] == "":
        parts.pop()
    out = ""
    for i, p in enumerate(parts):
        if i == 0:
            out = p
        elif p.startswith("<table") or parts[i - 1].endswith("</table>"):
            out += p
        else:
            out += "<br>" + p
    # an empty element in `parts` becomes a blank line between its neighbours
    return out.replace("<br><br><br>", "<br><br>")


def wrap_answer(html: str) -> str:
    html = html.strip()
    if not html:
        return ""
    if re.fullmatch(r"(?:<img[^>]*>|%s)\s*" % re.escape(FIG), html):
        return html
    return '<span class="ans">%s</span>' % html


def flow_blocks(blocks) -> list:
    """Cell blocks -> list of HTML block strings (a <p> per paragraph)."""
    out = []
    for b in blocks:
        if b[0] == "p":
            centred = b[1].startswith(CENTRE)
            h = tidy(b[1].replace(CENTRE, ""))
            if FIG in h and not re.sub(r"<[^>]+>|\s", "", h.replace(FIG, "")):
                out.append("<p>%s</p>" % FIG)     # a picture alone (Q20 wraps it in <b>)
            elif FIG in h:
                parts = h.split(FIG)
                for i, part in enumerate(parts):
                    t = part.strip()
                    if t:
                        out.append("<p>%s</p>" % wrap_answer(t))
                    if i < len(parts) - 1:
                        out.append("<p>%s</p>" % FIG)
            elif h:
                w = wrap_answer(h)
                out.append('<p class="c">%s</p>' % w if centred else "<p>%s</p>" % w)
        elif b[0] == "table":
            out.append(nested_table_html(b[1]))
    return out


def vmerge(tc):
    """None, "restart" or "cont" for a cell's w:vMerge."""
    pr = tc.find(Wq + "tcPr")
    vm = pr.find(Wq + "vMerge") if pr is not None else None
    if vm is None:
        return None
    return "restart" if vm.get(Wq + "val") == "restart" else "cont"


def option_row_html(cells, rowspan=1) -> str:
    """One per-option row. A text cell that is a vertical-merge CONTINUATION
    (Q30: options B and C share one explanation) emits no <td>; the cell that
    restarted the merge carries the rowspan."""
    mark = cell_inline(cells[0])
    label = cell_inline(cells[1])
    kind = vmerge(cells[2])
    if kind == "cont":
        text_td = ""
    else:
        attr = ' rowspan="%d"' % rowspan if rowspan > 1 else ""
        text_td = "<td%s>%s</td>" % (attr, cell_inline(cells[2]))
    return "<tr><td>%s</td><td>%s</td>%s</tr>" % (mark, label, text_td)


def render_question(qn: int, tbl, anomalies: list):
    rows = direct(tbl, "tr")
    head = direct(rows[0], "tc")
    assert cell_text(head[0]) == str(qn), (qn, cell_text(head[0]))
    key_blocks = cell_blocks(head[1])
    first = key_blocks[0]
    key = re.sub(r"<[^>]+>", "", first[1]).strip() if first[0] == "p" else ""
    if key not in ("A", "B", "C", "D"):
        raise SystemExit("Q%d: row-0 key cell does not open with a letter: %r"
                         % (qn, key))
    body = flow_blocks(key_blocks[1:])
    run = []

    def flush():
        if run:
            body.append('<table class="cmp">%s</table>' % "".join(run))
            run.clear()

    for i, tr in enumerate(rows[1:], start=1):
        cells = direct(tr, "tc")
        if len(cells) == 3:
            span = 1
            if vmerge(cells[2]) == "restart":
                for nxt in rows[i + 1:]:
                    nc = direct(nxt, "tc")
                    if len(nc) == 3 and vmerge(nc[2]) == "cont":
                        span += 1
                    else:
                        break
            run.append(option_row_html(cells, span))
            continue
        flush()
        tc = cells[-1]
        body.extend(flow_blocks(cell_blocks(tc)))
    flush()
    return key, "\n".join(body)


def substitute_figs(qn: int, html: str, assets: list):
    plan = FIG_PLAN.get(qn, [])
    n = html.count(FIG)
    if n != len(plan):
        raise SystemExit("Q%d: %d figure sentinel(s) in the document but "
                         "FIG_PLAN lists %d: %r" % (qn, n, len(plan), plan))
    it = iter(plan)

    def sub(_m):
        slot = next(it)
        path = PATH_OVERRIDE.get((qn, slot)) or "DHS_H2_P1_Q%d_%s_2024.png" % (qn, slot)
        assets.append({"question": qn, "slot": slot, "path": path,
                       "offset": len([a for a in assets if a["question"] == qn]) + 1})
        style = (' style="%s"' % INLINE_STYLE) if (qn, slot) in INLINE_FIGS else ""
        return '<img class="ws-fig" data-asset="%s" alt=""%s>' % (path, style)

    html = re.sub(re.escape(FIG), sub, html)
    return re.sub(r'<span class="sr">(<img[^>]*>)</span>', r"\1", html)


def read_key_table(tbl):
    rows = [[cell_text(c) for c in direct(tr, "tc")] for tr in direct(tbl, "tr")]
    key = {}
    for i, r in enumerate(rows):
        if r and r[0].isdigit() and i + 1 < len(rows):
            for num, let in zip(r, rows[i + 1]):
                if num.isdigit() and let in ("A", "B", "C", "D"):
                    key[int(num)] = let
    return key


def pdf_key(pdf_path: Path) -> dict:
    """The answer key as PRINTED in the Word PDF (page 1), read independently of
    the docx: each question number is paired with the letter directly below it."""
    page = pymupdf.open(str(pdf_path))[0]
    words = page.get_text("words")
    nums = [(w[0], w[1], w[2], w[3], w[4]) for w in words
            if w[4].isdigit() and 1 <= int(w[4]) <= 30 and w[1] < 300]
    lets = [(w[0], w[1], w[2], w[3], w[4]) for w in words
            if w[4] in ("A", "B", "C", "D") and w[1] < 300]
    out = {}
    for x0, y0, x1, y1, t in nums:
        cx = (x0 + x1) / 2
        cand = [l for l in lets if abs((l[0] + l[2]) / 2 - cx) < 6 and 0 < l[1] - y0 < 25]
        if len(cand) == 1:
            out[int(t)] = cand[0][4]
    return out


def main(argv=None):
    argv = argv or sys.argv[1:]
    unz, pdf, outdir = Path(argv[0]), Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    body, nsym = load_body(unz)
    tbls = direct(body, "tbl")
    anomalies = ["Symbol F0DE rewritten to '=>' x%d (not EJC's tick)" % nsym]
    table_key = read_key_table(tbls[0])
    printed = pdf_key(pdf)
    if len(table_key) != 30:
        raise SystemExit("key table gave %d letters, expected 30" % len(table_key))
    if printed != table_key:
        raise SystemExit("answer key (docx table) disagrees with the letters "
                         "printed in the Word PDF: %r"
                         % {k: (table_key.get(k), printed.get(k))
                            for k in range(1, 31) if table_key.get(k) != printed.get(k)})

    solutions, assets, row0_key = {}, [], {}
    qtbls = tbls[1:]
    if len(qtbls) != 30:
        raise SystemExit("expected 30 question tables, found %d" % len(qtbls))
    for qn, tbl in enumerate(qtbls, start=1):
        key, html = render_question(qn, tbl, anomalies)
        row0_key[qn] = key
        if key != table_key[qn]:
            raise SystemExit("Q%d: row-0 key %s != key table %s"
                             % (qn, key, table_key[qn]))
        for q, pat, repl, want, why in TEXT_FIXES:
            if q != qn:
                continue
            html, n = re.subn(pat, repl, html)
            if n != want:
                raise SystemExit("Q%d text fix %r matched %d, expected %d"
                                 % (qn, pat, n, want))
            anomalies.append("Q%d: text fix x%d -- %s" % (qn, n, why))
        if qn in WHOLE_TABLE_FIGS:
            html, n = re.subn(r'<table class="cmp">.*?</table>', "<p>%s</p>" % FIG,
                              html, flags=re.S)
            if n != 1:
                raise SystemExit("Q%d: expected exactly 1 table to swap, found %d" % (qn, n))
        html = substitute_figs(qn, html, assets)
        html, log = corrections.apply(html, SCOPE)
        if log:
            anomalies.append("Q%d corrections: %s" % (qn, log))
        if "\x00" in html:
            raise SystemExit("Q%d: NUL byte / unreplaced sentinel left in html" % qn)
        solutions[qn] = '<div class="worked-solution">\n%s\n</div>' % html

    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in solutions.items()}, indent=1,
                   ensure_ascii=False), encoding="utf8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(k): v for k, v in table_key.items()}, indent=1),
        encoding="utf8")
    (outdir / "answer_assets.json").write_text(
        json.dumps(assets, indent=1), encoding="utf8")
    (outdir / "anomalies.txt").write_text("\n".join(anomalies) + "\n",
                                          encoding="utf8")
    print("questions %d | key checked 3 ways (table, row 0, printed PDF) | "
          "assets %d" % (len(solutions), len(assets)))
    return solutions


if __name__ == "__main__":
    main()
