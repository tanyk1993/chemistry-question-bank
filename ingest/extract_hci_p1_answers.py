"""Extract worked solutions + answer key for HCI 2024 H2 P1 (9729/01, MCQ).

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
--year 2024 --paper 1 --level H2 --answer-key answer_key.json`.

Usage:
  python3 -m ingest.extract_hci_p1_answers <unzipped docx dir> <answers.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import corrections
from . import extract_dhs_p1_answers as D
from .oxml import Wq

SCOPE = ("HCI", "H2", "P1", 2024)
FIG = D.FIG

#: user hand-snips, per question, in DOCUMENT ORDER (after collapsing adjacent
#: figure sentinels that make up ONE printed picture). slot -> filename is
#: HCI_H2_P1_Q<n>_<slot>_2024.png.  Filled in once the sentinels are counted.
FIG_PLAN: dict = {
    2: ["ans-1"],                 # electron-in-box diagrams: Li+, Ti+, Mg, S (one snip)
    17: ["ans-1"],                # the four chain diagrams with captions (one snip)
    18: ["ans-a", "ans-b"],       # stage 1 scheme; stage 2 scheme
    19: ["ans-a", "ans-b", "ans-c"],  # B: five monosubstituted products; D: radical, dimer (inline)
    21: ["ans-1"],                # the three oxidation products + arrow + caption (one snip)
    23: ["ans-1"],                # C: bromoalkane -> alcohol scheme
    26: ["ans-1"],                # III's carboxylate with the internal hydrogen bond
}
INLINE_FIGS: set = {(19, "ans-b"), (19, "ans-c")}
INLINE_STYLE = D.INLINE_STYLE
PATH_OVERRIDE: dict = {}
#: Q5's table contains struck-through (corrected) wording; rendered as <s>
STRIKE_QS = {5}

#: pinned text edits: (qnum, regex, replacement, expected_count, reason)
TEXT_FIXES: list = [
    (8, r"KJ mol<sup>\u22121</sup>", "kJ mol<sup>\u22121</sup>", 1,
     "capital K: the SI prefix kilo is lower case (user ruling 2026-10-13)"),
    (8, r"mp / <sup>o</sup>C", "mp / \u00b0C", 1,
     "degree sign typed as a superscript letter o (user ruling)"),
    (11, r"monoanions are exothermic", "monoanions is exothermic", 1,
     "subject-verb agreement: '1st electron affinity ... is' (user ruling)"),
    (13, r"(min<sup>\u22121</sup>) (Option 2 is correct)", r"\1. \2", 1,
     "missing full stop before the next sentence (user ruling)"),
    (13, r'<span class="fden">t1/2</span>', '<span class="fden">t<sub>1/2</sub></span>', 1,
     "t1/2 unsubscripted in the fraction, unlike the rest of the paragraph (user ruling)"),
    (28, r"one of the key bond formed", "one of the key bonds formed", 1,
     "plural (user ruling)"),
    (28, r"an acid base reaction", "an acid\u2013base reaction", 1,
     "hyphenation of a compound modifier (user ruling)"),
    (29, r"\+0\.77V", "+0.77 V", 1, "space before the unit, as on the question side (user ruling)"),
    (29, r"\+0\.36V", "+0.36 V", 1, "same (user ruling)"),
    (3, r"D: T-shaped: 88", "D: T-shaped, 88", 1,
     "colon -> comma, as options A-C (user ruling)"),
    (18, r'<p><span class="ans">&emsp;</span></p>\n', "", 1,
     "empty paragraph ahead of the first scheme"),
    (13, r'<span class="fnum">ln2</span>', '<span class="fnum">ln 2</span>', 2,
     "the source prints 'ln 2' with a space; the OMML runs lost it"),
    (29, r'E<sup class="pl-sym">\u29b5</sup>Fe<sup>3\+</sup>/Fe<sup>2\+</sup>',
     'E<sup class="pl-sym">\u29b5</sup><sub>Fe<sup>3+</sup>/Fe<sup>2+</sup></sub>', 1,
     "the couple is a subscript on E (printed small and lowered)"),
    (29, r'E<sup class="pl-sym">\u29b5</sup>H<sup>\+</sup>/H<sub>2</sub>',
     'E<sup class="pl-sym">\u29b5</sup><sub>H<sup>+</sup>/H<sub>2</sub></sub>', 1,
     "same: subscript couple"),
    (29, r'E<sub>\(H\+/H2\)</sub>', 'E<sub>(H<sup>+</sup>/H<sub>2</sub>)</sub>', 1,
     "the charge and the 2 sat flat inside a subscript"),
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
        path = PATH_OVERRIDE.get((qn, slot)) or "HCI_H2_P1_Q%d_%s_2024.png" % (qn, slot)
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
    if len(tbls) != 2:
        raise SystemExit("expected 2 body tables (key + answers), found %d" % len(tbls))
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
