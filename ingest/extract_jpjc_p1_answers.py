"""Extract worked solutions + answer key for JPJC 2024 H2 P1 (9729/01, MCQ).

Shape: ONE body table, one row per question [number | key | explanation], no
separate key table. The key is therefore read two independent ways (the docx
key cells, and the letters printed beside each number in the Word PDF) and the
two must agree. Q3's key cell is BLANK in the school's document (the
explanation implies D): supplied by KEY_OVERRIDE, reported as an anomaly.
Q16 was removed on the question side (flawed question): skipped here.

Usage: python3 -m ingest.extract_jpjc_p1_answers <unz> <answers.pdf> <outdir> [--count-figs]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

from . import corrections
from . import extract_dhs_p1_answers as D
from .oxml import Wq

SCOPE = ("JPJC", "H2", "P1", 2024)
FIG = D.FIG
REMOVED = {16}
KEY_OVERRIDE = {3: "D"}          # blank key cell; BCl3 6 e- vs PH3 8 e- = option D
# ChemDraw structures / schemes (and Q11's two annotated dG equations) are
# hand-snipped by the user, in DOCUMENT ORDER; slots must be ans-...
FIG_PLAN: dict = {
    3: ["ans-1"],                       # dot-and-cross diagrams of BCl3 and PH3 (one snip)
    11: ["ans-a", "ans-b"],             # dG = dH - TdS with the +ve/-ve braces (x2)
    19: ["ans-1"],                      # the three alcohols
    20: ["ans-1"],                      # retinol and Y with the circled C=C / chiral C*
    21: ["ans-1"],                      # the nitrile / ketone skeleton with sp / sp2 / sp3 marks
    23: ["ans-1"],                      # IBr addition mechanism scheme
    25: ["ans-a", "ans-b", "ans-c", "ans-d"],   # one scheme per option A-D
    26: ["ans-1"],                      # phenylacetic acid -> methyl ester
    27: ["ans-1"],                      # the two tetrahedral-intermediate schemes
    28: ["ans-1"],                      # oligopeptide with circled amide links
}
INLINE_FIGS: set = set()
# MathType (Equation.DSMT4) fractions: typed as house .frac markup (style-guide
# SS1 rule, per-question editorial call), in DOCUMENT ORDER.
def _f(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


FRAC_FILL: dict = {
    5: [_f("1", "p"), _f("1", "p"), _f("\u03c1RT", "M<sub>r</sub>"),
        _f("pV", "T"), _f("pV", "T")],
    8: [_f("15.00", "1000"), _f("20.00", "1000")],
    9: [_f("M<sub>p</sub>", "M<sub>Q</sub>"),
        _f("mass of H<sub>2</sub>O", "mass of CO<sub>2</sub>"),
        _f("(<i>x</i>) \u00d7 18.0", "(<i>x</i>) \u00d7 44.0")],
    10: [_f("100", "47"), _f("<i>m</i>(butane)", "58")],
}
INLINE_STYLE = D.INLINE_STYLE
PATH_OVERRIDE: dict = {}
TEXT_FIXES: list = [
    (14, r'<p><span class="ans">Equilibrium can only', '<p><span class="ans">\u2022&emsp;Equilibrium can only', 1,
     "third bullet is a Word list bullet (w:numPr), the glyph is not in the text; the other two are typed"),
    (25, r'<p><span class="ans">(?:&emsp;)+[^\n]*(?:produced with Na|orange crystals with 2,4-DNPH)</span></p>\n?', "", 8,
     "typed caption lines are inside the user's snips (user ruling 2026-10-17): not typed"),
]


def question_rows(big):
    out = {}
    for tr in D.direct(big, "tr"):
        cs = D.direct(tr, "tc")
        if len(cs) == 3 and D.cell_text(cs[0]).strip().isdigit():
            qn = int(D.cell_text(cs[0]).strip())
            if qn in out:
                raise SystemExit("question %d appears twice" % qn)
            out[qn] = cs
    return out


def pdf_keys(pdf):
    """letter printed in the 2nd column on the same line as each number"""
    out = {}
    for page in pymupdf.open(str(pdf)):
        words = page.get_text("words")
        for w in words:
            if w[4].isdigit() and 1 <= int(w[4]) <= 30 and w[0] < 70:
                ys = [l for l in words if l[4] in ("A", "B", "C", "D")
                      and 70 < l[0] < 100 and abs(l[1] - w[1]) < 3]
                out[int(w[4])] = ys[0][4] if len(ys) == 1 else None
    return out


_LEAD = ("=", ")", "and ", ",")
_TAIL = ("=", "\u00d7", "(i.e.", "(i.e.)")


def _plain(line):
    return re.sub(r"<[^>]+>", "", line).replace("&emsp;", " ").strip()


def fill_fracs(qn, html):
    """typed fractions for the MathType objects; a fraction continues the
    sentence it sits in (a Word inline object) rather than starting a block."""
    fills = FRAC_FILL.get(qn)
    if not fills:
        return html
    n = html.count(FIG)
    if n != len(fills):
        raise SystemExit("Q%d: %d sentinels, FRAC_FILL has %d" % (qn, n, len(fills)))
    out = []
    it = iter(fills)
    for line in html.split("\n"):
        if line == "<p>%s</p>" % FIG:
            out.append("<p>%s</p>" % next(it))      # a block of its own for now
        else:
            out.append(line)
    # merge: <p>..tail</p> + <p>FRAC</p> ; <p>FRAC</p> + <p>lead..</p>
    def is_frac(l):
        return l.startswith('<p><span class="frac">') and l.endswith("</span></span></p>") \
            and _plain(l) and l.count('class="frac"') == 1 and l.startswith('<p><span class="frac">')

    def body(l):
        if l.startswith('<p><span class="ans">'):
            return l[len('<p><span class="ans">'):-len("</span></p>")]
        return l[len("<p>"):-len("</p>")]

    def wrap(inner):
        return '<p><span class="ans">%s</span></p>' % inner

    merged = []
    for l in out:
        prev = merged[-1] if merged else ""
        if is_frac(l) and prev.startswith("<p>") and _plain(prev).endswith(_TAIL):
            merged[-1] = wrap(body(prev) + " " + body(l))
        elif l.startswith('<p><span class="ans">') and _plain(l).startswith(_LEAD) \
                and prev.startswith("<p>") and prev.endswith('</span></span></p>') \
                and 'class="frac"' in prev:
            sep = "" if _plain(l).startswith((")", ",")) else " "
            merged[-1] = wrap(body(prev) + sep + body(l))
        else:
            merged.append(l)
    return "\n".join(merged)


def substitute_figs(qn, html, assets):
    plan = FIG_PLAN.get(qn, [])
    n = html.count(FIG)
    if n != len(plan):
        raise SystemExit("Q%d: %d figure sentinel(s) in the document but FIG_PLAN lists %d: %r"
                         % (qn, n, len(plan), plan))
    it = iter(plan)

    def sub(_m):
        slot = next(it)
        path = PATH_OVERRIDE.get((qn, slot)) or "JPJC_H2_P1_Q%d_%s_2024.png" % (qn, slot)
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
    body, _n = D.load_body(unz)
    tbls = D.direct(body, "tbl")
    if len(tbls) != 1:
        raise SystemExit("expected 1 body table, found %d" % len(tbls))
    rows = question_rows(tbls[0])
    if sorted(rows) != list(range(1, 31)):
        raise SystemExit("question rows are not exactly 1..30: %r" % sorted(rows))
    anomalies = []
    printed = pdf_keys(pdf)
    key, solutions, assets = {}, {}, []
    for qn in range(1, 31):
        if qn in REMOVED:
            anomalies.append("Q%d skipped (removed on the question side)" % qn)
            continue
        k = D.cell_text(rows[qn][1]).strip()
        if qn in KEY_OVERRIDE:
            if k:
                raise SystemExit("Q%d: key cell now %r, drop the override" % (qn, k))
            anomalies.append("Q%d: key cell BLANK in the source; %s supplied (user to confirm)"
                             % (qn, KEY_OVERRIDE[qn]))
            k = KEY_OVERRIDE[qn]
            if printed.get(qn) is not None:
                raise SystemExit("Q%d printed key present %r" % (qn, printed.get(qn)))
        else:
            if printed.get(qn) != k:
                raise SystemExit("Q%d: docx key %r != printed %r" % (qn, k, printed.get(qn)))
        if k not in "ABCD" or len(k) != 1:
            raise SystemExit("Q%d: bad key %r" % (qn, k))
        key[qn] = k
        html = "\n".join(D.flow_blocks(D.cell_blocks(rows[qn][2])))
        nmin = len(re.findall("<sup>[^<]*–[^<]*</sup>", html))
        if nmin:
            html = re.sub(r"<sup>([^<]*)</sup>",
                          lambda m: "<sup>%s</sup>" % m.group(1).replace("–", "−"), html)
            anomalies.append("Q%d: en dash -> minus in %d superscript(s)" % (qn, nmin))
        for q, pat, repl, want, why in TEXT_FIXES:
            if q != qn:
                continue
            html, n = re.subn(pat, repl, html)
            if n != want:
                raise SystemExit("Q%d text fix %r matched %d, expected %d" % (qn, pat, n, want))
            anomalies.append("Q%d: text fix x%d -- %s" % (qn, n, why))
        html = fill_fracs(qn, html)
        if "--count-figs" in argv:
            print("Q%d figs=%d" % (qn, html.count(FIG)))
        else:
            html = substitute_figs(qn, html, assets)
        html, log = corrections.apply(html, SCOPE)
        if log:
            anomalies.append("Q%d corrections: %s" % (qn, log))
        solutions[qn] = '<div class="worked-solution">\n%s\n</div>' % html
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in solutions.items()}, indent=1, ensure_ascii=False), encoding="utf8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(k): v for k, v in key.items()}, indent=1), encoding="utf8")
    (outdir / "answer_assets.json").write_text(json.dumps(assets, indent=1), encoding="utf8")
    (outdir / "anomalies.txt").write_text("\n".join(anomalies) + "\n", encoding="utf8")
    print("questions %d | key checked (docx vs printed PDF) | assets %d" % (len(solutions), len(assets)))
    print("\n".join(anomalies))


if __name__ == "__main__":
    main()
