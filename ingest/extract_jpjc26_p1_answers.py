"""Extract worked solutions + answer key for JPJC 2026 H2 P1 (9476/01, MCQ).

Same shape as JPJC 2024 P1 (one body table, [number | key | explanation]) with
two differences: a question can span several ROWS (a numbered row, then rows
with a blank number cell holding MathType objects / spacers; Q4 even repeats its
number on a second row), so rows are GROUPED by question; and every docx key
cell is filled. The key is read two independent ways (docx key cells, and the
letters printed beside each number in the Word PDF) and the two must agree.

Usage: python3 -m ingest.extract_jpjc26_p1_answers <unz> <answers.pdf> <outdir> [--count-figs]
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

SCOPE = ("JPJC", "H2", "P1", 2026)
FIG = D.FIG
REMOVED = set()
KEY_OVERRIDE: dict = {}
# ChemDraw structures / schemes (and Q11's two annotated dG equations) are
# hand-snipped by the user, in DOCUMENT ORDER; slots must be ans-...
FIG_PLAN: dict = {
    7: ["ans-1"],                          # Hess cycle (the Hess's Law line under it is typed)
    18: ["ans-1"],                         # limonene + Br2 -> product, chiral centres starred
    20: ["ans-1"],                         # compound N, sigma/pi counts annotated
    22: ["ans-1", "ans-2", "ans-3"],       # cyclobutane, 2,2-dimethylpropane, 2-methylpropane
    23: ["ans-1"],                         # step 1 mechanism
    24: ["ans-a", "ans-b", "ans-c", "ans-d"],   # one scheme per option A-D
    25: ["ans-1"],                         # 70 / 30 split tree (the rotation arithmetic is typed)
    28: ["ans-1"],                         # compound S -> products scheme
    29: ["ans-a", "ans-b", "ans-c", "ans-d"],   # fragment-overlap arrows, options A-D
    30: ["ans-1", "ans-2"],                # propene -> T; diamine + diacid -> W
}
INLINE_FIGS: set = set()
# MathType (Equation.DSMT4) fractions: typed as house .frac markup (style-guide
# SS1 rule, per-question editorial call), in DOCUMENT ORDER.
def _f(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


FRAC_FILL: dict = {}


def _p(inner):
    return '<p><span class="ans">%s</span></p>' % inner


_H = "<sub>%s</sub>"
_ST = "<sup>\u2212%s</sup>"
SO3 = '<span class="stk post"><span>2\u2212</span><span>3</span></span>'
# MathType (Equation.DSMT4) objects hold the school's calculation lines; they
# are typed here from the printed PDF, in house .frac markup. `n_figs` pins how
# many sentinels the document has for that question (a change = stop and look);
# a FIG left in the html is a hand-snipped structure.
HTML_OVERRIDE: dict = {
    2: (1, "\n".join([
        _p('C<sub><i>x</i></sub>H<sub><i>y</i></sub> + (<i>x</i> + %s)O<sub>2</sub> \u2192 <i>x</i>CO<sub>2</sub> + %sH<sub>2</sub>O' % (_f("<i>y</i>", "4"), _f("<i>y</i>", "2"))),
        _p('mole ratio of C<sub><i>x</i></sub>H<sub><i>y</i></sub> to CO<sub>2</sub> = 20 : 60 = 1 : 3'),
        _p('\u2234 <i>x</i> = 3'),
        _p('mole ratio of C<sub><i>x</i></sub>H<sub><i>y</i></sub> to H<sub>2</sub>O = 20 : 40 = 1 : 2'),
        _p('%s = 2 \u21d2 <i>y</i> = 4' % _f("<i>y</i>", "2")),
    ])),
    5: (1, "\n".join([
        _p('amt of %s used = 0.100 \u00d7 %s = 0.00250 mol' % (SO3, _f("25.0", "1000"))),
        _p('amt of electrons produced during [O] = 2 \u00d7 0.00250'),
        _p('= amt of electrons used for [R]'),
        _p('amt of metal ions reacted = 0.100 \u00d7 %s = 0.00500 mol' % _f("50.0", "1000")),
        _p('mol ratio of metal ions to electrons = 0.00500 : (2 \u00d7 0.00250) = 1 : 1'),
        _p('Since the metal ions undergo reduction: <i>M</i><sup>3+</sup> + e \u2192 <i>M</i><sup>2+</sup>'),
        _p('\u2234 final oxidation number of the metal ion = +2'),
    ])),
    7: (2, "\n".join([
        "<p>%s</p>" % FIG,
        _p("Using Hess's Law: \u0394<i>H</i><sub>f</sub> = %s(+38) + %s(\u2212214) = \u221288 kJ mol<sup>\u22121</sup>" % (_f("1", "2"), _f("1", "2"))),
    ])),
    8: (3, "\n".join([
        _p('Using the relationship: |lattice energy| \u221d |%s|' % _f("<i>q</i><sub>+</sub><i>q</i><sub>\u2212</sub>", "<i>r</i><sub>+</sub> + <i>r</i><sub>\u2212</sub>")),
        _p('Statements 1 and 2 are correct as Mg<sup>2+</sup> has a larger ionic charge(+2) compared to that of Na<sup>+</sup>(+1) and Mg<sup>2+</sup> has a smaller ionic radius compared to Na<sup>+</sup>.'),
        _p('Hence the magnitude of lattice energy of MgC<i class="el">l</i><sub>2</sub> is larger (lattice energy of MgC<i class="el">l</i><sub>2</sub> is more exothermic).'),
        _p('Statement 3 is correct as <u>Mg</u><u><sup>2+</sup></u> is smaller than Na<sup>+</sup>while the anion (C<i class="el">l</i><sup>\u2212</sup>) remains identical, the interionic distance (<i>r</i><sub>+</sub> + <i>r</i><sub>\u2212</sub>) is shorter in MgC<i class="el">l</i><sub>2</sub> than in NaC<i class="el">l</i>.'),
    ])),
    10: (1, "\n".join([
        _p('amt of HNO<sub>3</sub> = 0.01 \u00d7 %s = 1.00 \u00d7 10<sup>\u22124</sup> mol' % _f("10", "1000")),
        _p('\u2234 new [HNO<sub>3</sub>] = 1.00 \u00d7 10<sup>\u22124</sup> \u00d7 %s = 0.00100 mol dm<sup>\u22123</sup>' % _f("1000", "100")),
        _p('[H<sup>+</sup>] = 0.00100 mol dm<sup>\u22123</sup>'),
        _p('\u2234 <i>pH</i> = \u2212lg 0.00100 = 3'),
    ])),
    11: (2, "\n".join([
        _p('Let the solubility of ZnF<sub>2</sub> be x mol dm<sup>\u22123</sup>'),
        _p('For saturated solution <b>G</b>:'),
        _p('<i>K</i><sub>sp</sub> = [Zn<sup>2+</sup>][F<sup>\u2212</sup>]<sup>2</sup> = (<i>x</i>)(2<i>x</i>)<sup>2</sup> = 4<i>x</i><sup>3</sup> = 3.2 \u00d7 10<sup>\u22122</sup>'),
        _p('<i>x</i> = 0.200 mol dm<sup>\u22123</sup>'),
        _p('\u2234 [F<sup>\u2212</sup>] = 2 \u00d7 0.200 = 0.400 mol dm<sup>\u22123</sup>'),
        _p('When BaF<sub>2</sub> just precipitates, IP = <i>K</i><sub>sp</sub>(BaF<sub>2</sub>)'),
        _p('[Ba<sup>2+</sup>][F<sup>\u2212</sup>]<sup>2</sup> = 1.6 \u00d7 10<sup>\u22127</sup>'),
        _p('[Ba<sup>2+</sup>](0.4)<sup>2</sup> = 1.6 \u00d7 10<sup>\u22127</sup>'),
        _p('\u2234 [Ba<sup>2+</sup>] = 1.00 \u00d7 10<sup>\u22126</sup> mol dm<sup>\u22123</sup>'),
    ])),
    14: (0, "\n".join([
        _p('Using Q = It = <i>ne</i>F'),
        _p('(0.1)(160 \u00d7 60) = <i>n</i>(96500)'),
        _p('<i>ne</i> = 0.00995 mol'),
        _p('amt of M = %s = 0.00503 mol' % _f("0.295", "58.7")),
        _p('mol ratio of M:e = 0.00503 : 0.00995 = 1 : 2'),
        _p('\u2234 value of <i>x</i> = 2'),
    ])),
    25: (2, "\n".join([
        "<p>%s</p>" % FIG,
        _p('observed rotation = fraction giving net optical activity \u00d7 rotation of pure enantiomer'),
        _p('= %s \u00d7 (\u221213.5) = \u22129.45\u00b0' % _f("70", "100")),
    ])),
}
INLINE_STYLE = D.INLINE_STYLE
PATH_OVERRIDE: dict = {}
TEXT_FIXES: list = [
    # Q4: the X+ equation lost its spacing (it is an OMML object); centred as printed
    (4, r'<p><span class="ans">X<sup>\+</sup>\(g\)[^\n]*</span></p>',
     '<p class="c"><span class="ans">X<sup>+</sup>(g) \u2192 X<sup>2+</sup>(g) + e<sup>\u2212</sup></span></p>', 1,
     "equation spacing restored; centred as printed"),
    # Q4: the school's bullet is broken: "Since   Since its" + an empty equation object,
    # then the sentence continues in the next bullet. Joined into ONE sentence (flagged to the user).
    (4, r'<p><span class="ans">Option B \(Correct\):[^\n]*Since its</span></p>\n<p>' + FIG + r'</p>\n<p><span class="ans">E\+ ion retains',
     '<p><span class="ans">Option B (Correct): Element E belongs to Group 2. Since its E<sup>+</sup> ion retains', 1,
     "school's broken bullet joined into one sentence; empty object dropped"),
    # Word list bullets (w:numPr) carry no glyph in the text
    (4, r'<p><span class="ans">(A large drop|Large drop in 2nd|Compared to D|Option B \(Correct\)|E\+ is ns)',
     '<p><span class="ans">\u2022&emsp;\\1', 5, "Word list bullets typed"),
    (6, r'<p><span class="ans">(There are no intermolecular|Volume of gas particles are)',
     '<p><span class="ans">\u2022&emsp;\\1', 2, "Word list bullets typed"),
]


def question_rows(big):
    """qn -> (key cell text, [explanation cells of every row of that question])"""
    out, cur = {}, None
    for tr in D.direct(big, "tr"):
        cs = D.direct(tr, "tc")
        if len(cs) < 3:
            raise SystemExit("row with %d cells" % len(cs))
        num = D.cell_text(cs[0]).strip()
        key = D.cell_text(cs[1]).strip()
        if num.isdigit():
            qn = int(num)
            if cur != qn:
                if qn in out:
                    raise SystemExit("question %d reappears after Q%s" % (qn, cur))
                out[qn] = [key, [], []]
                cur = qn
            elif key != out[qn][0]:
                raise SystemExit("Q%d: key %r on a repeated row != %r" % (qn, key, out[qn][0]))
            if len(cs) == 3:
                out[qn][1].append(cs[2])
            else:                       # Q22: three side-by-side columns
                out[qn][2].append(cs[2:])
        elif num == "" and cur is not None:
            if key:
                raise SystemExit("Q%s: key on a continuation row" % cur)
            out[cur][1].append(cs[2])
        else:
            raise SystemExit("unexpected number cell %r" % num)
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


#: Q22: structures sit under centred names; img.ws-fig is display:block, so auto margins centre it
CENTRED_FIGS = {22}
CENTRE_STYLE = "margin:.7em auto"
def substitute_figs(qn, html, assets):
    plan = FIG_PLAN.get(qn, [])
    n = html.count(FIG)
    if n != len(plan):
        raise SystemExit("Q%d: %d figure sentinel(s) in the document but FIG_PLAN lists %d: %r"
                         % (qn, n, len(plan), plan))
    it = iter(plan)

    def sub(_m):
        slot = next(it)
        path = PATH_OVERRIDE.get((qn, slot)) or "JPJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)
        assets.append({"question": qn, "slot": slot, "path": path,
                       "offset": len([a for a in assets if a["question"] == qn]) + 1})
        style = (' style="%s"' % INLINE_STYLE) if (qn, slot) in INLINE_FIGS else ""
        if qn in CENTRED_FIGS:
            style = ' style="%s"' % CENTRE_STYLE
        return '<img class="ws-fig" data-asset="%s" alt=""%s>' % (path, style)

    html = re.sub(re.escape(FIG), sub, html)
    return re.sub(r'<span class="sr">(<img[^>]*>)</span>', r"\1", html)


def main(argv=None):
    argv = argv or sys.argv[1:]
    unz, pdf, outdir = Path(argv[0]), Path(argv[1]), Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    body, _n = D.load_body(unz)
    tbls = D.direct(body, "tbl")
    if len(tbls) != 3:      # heading table, key table, body table
        raise SystemExit("expected 3 tables, found %d" % len(tbls))
    rows = question_rows(tbls[2])
    if sorted(rows) != list(range(1, 31)):
        raise SystemExit("question rows are not exactly 1..30: %r" % sorted(rows))
    anomalies = []
    printed = pdf_keys(pdf)
    key, solutions, assets = {}, {}, []
    for qn in range(1, 31):
        if qn in REMOVED:
            anomalies.append("Q%d skipped (removed on the question side)" % qn)
            continue
        k = rows[qn][0]
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
        blocks = []
        for _c in rows[qn][1]:
            blocks.extend(D.cell_blocks(_c))
        html = "\n".join(D.flow_blocks(blocks))
        for _grp in rows[qn][2]:
            tds = ["<td>%s</td>" % "\n".join(D.flow_blocks(D.cell_blocks(_c))) for _c in _grp]
            html += '\n<table class="cmp"><tr>%s</tr></table>' % "".join(tds)
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
        if qn in HTML_OVERRIDE:
            want, new = HTML_OVERRIDE[qn]
            if html.count(FIG) != want:
                raise SystemExit("Q%d: %d sentinels, override pinned for %d" % (qn, html.count(FIG), want))
            html = new
            anomalies.append("Q%d: calculation typed from the printed PDF (MathType objects)" % qn)
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
