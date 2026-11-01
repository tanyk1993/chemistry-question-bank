"""Extract worked solutions + answer key for HCI 2026 H2 P1 (9476/01, MCQ).

Document shape (a seventh answer-doc shape in this bank, the simplest MCQ one):

  * an ANSWER KEY table first: three pairs of rows (question numbers over
    letters), ten per pair;
  * then ONE big table for the whole paper. Each question is ONE row of three
    cells [number | key letter | explanation]; the explanation cell holds every
    paragraph, nested table (Q5, Q8, Q19, Q23, Q27) and ChemDraw/MathType
    object of that question. Blank spacer rows sit between most questions
    (Q8/Q9, Q14/Q15, Q16/Q17 have none, hence rows are found by a bare number
    in cell 0, never by position);
  * answers are plain black text, no coloured layer, no per-option marks.

Everything reuses the DHS P1 helpers (`extract_dhs_p1_answers`): the cell
walker, tidy/clean, nested-table renderer, key-table reader and the independent
printed-key reader. What is HCI-specific is declared and PINNED below, and the
run raises if a declaration does not match what the document holds.

Output (in <outdir>): worked_solutions.json, answer_key.json, answer_assets.json,
anomalies.txt.  Feeds `gen_answers_migration.py --type mcq --school HCI
--year 2026 --paper 1 --level H2 --answer-key answer_key.json`.

Usage:
  python3 -m ingest.extract_hci26_p1_answers <unzipped docx dir> <answers.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import corrections
from . import extract_dhs_p1_answers as D
from .oxml import Wq

SCOPE = ("HCI", "H2", "P1", 2026)
FIG = D.FIG

#: user hand-snips, per question, in DOCUMENT ORDER (after collapsing adjacent
#: figure sentinels that make up ONE printed picture). slot -> filename is
#: HCI_H2_P1_Q<n>_<slot>_2024.png.  Filled in once the sentinels are counted.
FIG_PLAN: dict = {
    17: ["ans-1"],                # compound L structure (in option 1's cell)
    21: ["ans-1", "ans-2"],       # the two acidic structures (own lines)
    22: ["ans-1"],                # product of propanal + HCN (inline in C)
    26: ["ans-1", "ans-2"],       # annotated peptide; hydrolysis products
}
INLINE_FIGS: set = {(21, "ans-1"), (21, "ans-2"), (22, "ans-1")}
INLINE_STYLE = D.INLINE_STYLE
PATH_OVERRIDE: dict = {}
#: Q5's table contains struck-through (corrected) wording; rendered as <s>
STRIKE_QS = set()

#: pinned text edits: (qnum, regex, replacement, expected_count, reason)
TEXT_FIXES: list = [
    (22, r"<sub>\. </sub>", ". ", 1, "stray subscript on the full stop after CN-"),
    (18, r"<b> </b>", " ", 1, "empty bold run"),
    # Q21: one line, structures inline, as in the school's scheme (user ruling)
    (21, r'<p><span class="ans">Only</span></p>\s*<p>\x00FIG\x00</p>\s*<p><span class="ans">and</span></p>\s*<p>\x00FIG\x00</p>\s*<p><span class="ans">contain',
         '<p><span class="ans">Only \x00FIG\x00 and \x00FIG\x00 contain', 1, "structures inline in one paragraph"),
    # Q14: rows B and C share one merged explanation cell in the school's table
    (14, r'(<tr><td>B</td><td)>(.*?</td></tr>)<tr><td>C</td><td></td></tr>',
         r'\1 rowspan="2">\2<tr><td>C</td></tr>', 1, "B and C share a merged cell (rowspan=2)"),
    # Q29: unit spacing and the electron charge (user ruling)
    (29, r"0\.497mol", "0.497 mol", 1, "space before unit"),
    (29, r"0\.124mol", "0.124 mol", 1, "space before unit"),
    (29, r"\+ 4e</span>", "+ 4e<sup>\u2212</sup></span>", 1, "electron charge"),
    # Q30: state symbols; split the two run-together equations in I
    (30, r"(2\[Cr\(H<sub>2</sub>O\)<sub>6</sub>\]<sup>3\+</sup>\(aq\) \+  Zn\(s\)  →  2\[Cr\(H<sub>2</sub>O\)<sub>6</sub>\]<sup>2\+</sup>)\(s\)",
         r"\1(aq)", 1, "Cr2+ complex is aqueous"),
    (30, r"(NH<sub>4</sub><sup>\+</sup>)\(<i class=\"el\">l</i>\)", r"\1(aq)", 1, "NH4+ is aqueous"),
    (30, r'(\(<i class="el">l</i>\)) (\[Cr\(H<sub>2</sub>O\)<sub>3</sub>\(OH\)<sub>3</sub>\]\(s\) \+ 3OH)',
         r'\1</span></p>\n<p><span class="ans">\2', 1, "split run-together equations in I"),
]


def question_rows(big):
    out = {}
    for tr in D.direct(big, "tr"):
        cs = D.direct(tr, "tc")
        if len(cs) == 3 and D.cell_text(cs[0]).isdigit():
            qn = int(D.cell_text(cs[0]))
            if qn in out:
                raise SystemExit("question %d appears twice" % qn)
            out[qn] = cs
    return out


def mark_strikes(tc):
    """Rewrite a struck run (w:strike) as a run wrapped in literal <s> text so
    the stock paragraph walker keeps it; undone to real tags after rendering."""
    n = 0
    for r in tc.iter(Wq + "r"):
        pr = r.find(Wq + "rPr")
        if pr is None or pr.find(Wq + "strike") is None:
            continue
        for t in r.findall(Wq + "t"):
            t.text = "\ue001" + (t.text or "") + "\ue002"
            n += 1
    return n


def unstrike(html):
    html = html.replace("\ue001", "<s>").replace("\ue002", "</s>")
    return re.sub(r"<s>(\s*)</s>", r"\1", html)


def render(qn, cs):
    key = D.cell_text(cs[1])
    if key not in ("A", "B", "C", "D"):
        raise SystemExit("Q%d: key cell is %r" % (qn, key))
    nstrike = mark_strikes(cs[2]) if qn in STRIKE_QS else 0
    html = "\n".join(D.flow_blocks(D.cell_blocks(cs[2])))
    if qn in STRIKE_QS:
        html = unstrike(html)
        if html.count("<s>") != nstrike:
            raise SystemExit("Q%d: %d strike runs but %d <s> after rendering"
                             % (qn, nstrike, html.count("<s>")))
    return key, html


def substitute_figs(qn, html, assets):
    plan = FIG_PLAN.get(qn, [])
    n = html.count(FIG)
    if n != len(plan):
        raise SystemExit("Q%d: %d figure sentinel(s) in the document but "
                         "FIG_PLAN lists %d: %r" % (qn, n, len(plan), plan))
    it = iter(plan)

    def sub(_m):
        slot = next(it)
        path = PATH_OVERRIDE.get((qn, slot)) or "HCI_H2_P1_Q%d_%s_2026.png" % (qn, slot)
        assets.append({"question": qn, "slot": slot, "path": path,
                       "offset": len([a for a in assets if a["question"] == qn]) + 1})
        style = (' style="%s"' % INLINE_STYLE) if (qn, slot) in INLINE_FIGS else ""
        return '<img class="ws-fig" data-asset="%s" alt=""%s>' % (path, style)

    html = re.sub(re.escape(FIG), sub, html)
    return re.sub(r'<span class="sr">(<img[^>]*>)</span>', r"\1", html)


def main(argv=None):
    argv = argv or sys.argv[1:]
    unz, pdf, outdir = Path(argv[0]), Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    body, _n = D.load_body(unz)      # Symbol F0DE -> "=>" (none expected here)
    tbls = D.direct(body, "tbl")
    if len(tbls) != 3:
        raise SystemExit("expected 3 body tables (key + Q1-25 + Q26-30), found %d" % len(tbls))
    anomalies = []
    table_key = D.read_key_table(tbls[0])
    printed = D.pdf_key(pdf)
    if len(table_key) != 30:
        raise SystemExit("key table gave %d letters, expected 30" % len(table_key))
    if printed != table_key:
        raise SystemExit("answer key (docx table) disagrees with the letters "
                         "printed in the Word PDF: %r"
                         % {k: (table_key.get(k), printed.get(k))
                            for k in range(1, 31) if table_key.get(k) != printed.get(k)})
    rows = question_rows(tbls[1])
    for qn, cs in question_rows(tbls[2]).items():
        if qn in rows:
            raise SystemExit("question %d appears in both answer tables" % qn)
        rows[qn] = cs
    if sorted(rows) != list(range(1, 31)):
        raise SystemExit("question rows are not exactly 1..30: %r" % sorted(rows))

    solutions, assets = {}, []
    for qn in range(1, 31):
        key, html = render(qn, rows[qn])
        if key != table_key[qn]:
            raise SystemExit("Q%d: row key %s != key table %s" % (qn, key, table_key[qn]))
        # one convention for charges and exponents: the proper minus U+2212
        nmin = len(re.findall("<sup>[^<]*\u2013[^<]*</sup>", html))
        if nmin:
            html = re.sub(r"<sup>([^<]*)</sup>",
                          lambda m: "<sup>%s</sup>" % m.group(1).replace("\u2013", "\u2212"),
                          html)
            anomalies.append("Q%d: en dash -> minus in %d superscript(s)" % (qn, nmin))
        for q, pat, repl, want, why in TEXT_FIXES:
            if q != qn:
                continue
            html, n = re.subn(pat, repl, html)
            if n != want:
                raise SystemExit("Q%d text fix %r matched %d, expected %d"
                                 % (qn, pat, n, want))
            anomalies.append("Q%d: text fix x%d -- %s" % (qn, n, why))
        if "--count-figs" in argv:
            print("Q%d figs=%d" % (qn, html.count(FIG)))
        else:
            html = substitute_figs(qn, html, assets)
        html, log = corrections.apply(html, SCOPE)
        if log:
            anomalies.append("Q%d corrections: %s" % (qn, log))
        if "\x00" in html and "--count-figs" not in argv:
            raise SystemExit("Q%d: NUL byte / unreplaced sentinel left" % qn)
        solutions[qn] = '<div class="worked-solution">\n%s\n</div>' % html

    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in solutions.items()}, indent=1,
                   ensure_ascii=False), encoding="utf8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(k): v for k, v in table_key.items()}, indent=1), encoding="utf8")
    (outdir / "answer_assets.json").write_text(json.dumps(assets, indent=1), encoding="utf8")
    (outdir / "anomalies.txt").write_text("\n".join(anomalies) + "\n", encoding="utf8")
    print("questions %d | key checked (table, row, printed PDF) | assets %d"
          % (len(solutions), len(assets)))
    return solutions


if __name__ == "__main__":
    main()
