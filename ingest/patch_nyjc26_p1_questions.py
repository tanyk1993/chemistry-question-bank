"""NYJC 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.nyjc26_p1_prep <unz> <word.pdf> <unz_q>
  python3 -m ingest.extract_questions <unz_q> <word.pdf> <out> \
      --school NYJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_nyjc26_p1_questions <out> <build_dir>

Every edit asserts its match count: a silent miss is how a fix ships unapplied.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
PLAN = json.loads((SRC / "asset_plan.json").read_text())
LOG = []
MINUS = "−"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def table_text(html):
    """(squashed, spaced) renderings of every table.qt in `html`: the extractor's
    search text runs a row's cells together; the spaced form separates them."""
    out = []
    for t in re.findall(r'<table class="qt">.*?</table>', html, flags=re.S):
        rows = []
        for tr in re.findall(r"<tr>(.*?)</tr>", t, flags=re.S):
            rows.append([re.sub(r"<[^>]+>", "", c).replace("<br>", " ")
                         for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)])
        old = re.sub(r" {2,}", " ", " ".join("".join(r) for r in rows))
        out.append((old, " ".join(" | ".join(c for c in r if c) for r in rows)))
    return out


# ------------------------------------------------ 1. table search text -----
# (done FIRST, from the extractor's own tables, before the markup is touched)
for qn in (1, 5, 8, 9, 16, 24):
    for old, new in table_text(Q[qn]["content_html"]):
        sub(qn, re.escape(old.replace("<br>", " ")), new.replace("\\", "\\\\"),
            field="content_text", rx=True)

# ------------------------------------------------ 2. figure plan ----------
# user snips every stem figure; Claude snips the two all-diagram option sets
# (Q2 structures, Q11 graphs).
DROP = {3: ["stem1", "stem2"], 10: ["stem2", "stem3"], 11: ["stem%d" % i for i in range(1, 9)]}
for qn, slots in DROP.items():
    gone = [p for p in PLAN if p["question"] == qn and p["slot"] in slots]
    assert len(gone) == len(slots), (qn, gone)
    PLAN = [p for p in PLAN if p not in gone]
    LOG.append("Q%d asset plan: dropped %s" % (qn, slots))


def add_plan(qn, slot, kind):
    PLAN.append({"question": qn, "index": -1, "kind": kind, "slot": slot,
                 "n_parts": 1, "ordinal": 0,
                 "storage_path": "NYJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d asset plan: added %s" % (qn, slot))


add_plan(11, "stem1", "block")        # the T1 graph (user)
for L in "ABCD":
    add_plan(11, L, "option")         # four graphs (Claude)
add_plan(13, "stem1", "block")        # titration curves I and II (user)

# ------------------------------------------------ 3. glyphs / symbols ------
# Q10: the reaction arrow is a bare Symbol-font character.
sub(10, "T  U", "T → U")
sub(10, "T  U", "T → U", field="content_text")
# Q11, Q12: the school's file prints a Calibri "N-ARY PRODUCT" (∏) where the
# reversible arrow should be (its own Word PDF shows the same glyph). The stems say
# "react to form an equilibrium mixture" / give Kp, so the arrow is certain (flagged).
sub(11, "(g) ∏ 2HI(g)", "(g) ⇌ 2HI(g)", field="content_text")
sub(12, "(g) ∏ 2SO", "(g) ⇌ 2SO", field="content_text")
sub(11, "(g) ∏ 2H", "(g) ⇌ 2H")
sub(12, "(g) ∏ 2SO", "(g) ⇌ 2SO")

# ------------------------------------------------ 4. per-question fixes ----
# Q1: header cells lost their rowspan / colspan
sub(1, '<tr><td>element</td><td>ionisation energy / kJ mol<sup>–1</sup></td></tr>'
       '<tr><td></td><td>8th</td><td>9th</td><td>10th</td></tr>',
    '<tr><td rowspan="2">element</td><td colspan="3">ionisation energy / kJ mol<sup>–1</sup></td></tr>'
    '<tr><td>8th</td><td>9th</td><td>10th</td></tr>')

# Q2: stray space inside the superscripts is handled globally (section 6)

# Q3: the two fractions are typed (stacked .frac); statements as a list
def _frac(n, d):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
_half12 = _frac("1", "12")
_f1 = _frac("average mass of isotopes of oxygen",
            _half12 + " the mass of one atom of carbon-12")
_f2 = _frac("average mass of one mole of hydrogen",
            _half12 + " the mass of one mole of carbon-12")
_q3 = Q[3]["content_html"]
_new3 = ('<p class="qstem">Which statements are correct?</p>\n'
         '<ol class="stmts"><li>Relative isotopic mass of oxygen is given by the following expression'
         '<p class="c">' + _f1 + '</p></li>'
         '<li>Relative atomic mass of hydrogen is given by the following expression'
         '<p class="c">' + _f2 + '</p></li>'
         '<li>Relative molecular mass is the sum of the relative atomic masses of all the atoms '
         'within the molecule.</li></ol>\n')
_i, _j = _q3.index('<p class="qstem eqn"> \tWhich'), _q3.index('<table class="opts-table">')
Q[3]["content_html"] = _q3[:_i] + _new3 + _q3[_j:]
Q[3]["content_text"] = Q[3]["content_text"].replace(
    "following expression 2", "following expression average mass of isotopes of oxygen / "
    "(1/12 the mass of one atom of carbon-12) 2", 1).replace(
    "following expression 3", "following expression average mass of one mole of hydrogen / "
    "(1/12 the mass of one mole of carbon-12) 3", 1)
LOG.append("Q3 content_html: statements rebuilt as ol.stmts, fractions typed (no snips)")

# Q5: header cells lost their rowspan / colspan
sub(5, '<tr><td></td><td>melting point / °C</td><td>boiling point / °C</td>'
       '<td>electrical conductivity</td></tr>'
       '<tr><td></td><td></td><td></td><td>solid</td><td>liquid</td><td>aqueous solution</td></tr>',
    '<tr><td rowspan="2"></td><td rowspan="2">melting point / °C</td>'
    '<td rowspan="2">boiling point / °C</td><td colspan="3">electrical conductivity</td></tr>'
    '<tr><td>solid</td><td>liquid</td><td>aqueous solution</td></tr>')

# Q6: the degree sign was typed as a superscript letter "o"
sub(6, "20<sup> o</sup>C", "20 °C")
sub(6, "(<sup>o</sup>C)", "(°C)", count=2)
sub(6, "<i>V </i>(dm³)", "<i>V</i> (dm<sup>3</sup>)")
sub(6, "(dm³)", "(dm3)", field="content_text")
sub(6, " oC", " °C", field="content_text", count=1)
sub(6, "(oC)", "(°C)", field="content_text", count=2)

# Q9 / Q16: table header cells are fine as extracted

# Q10: three drawing pieces = ONE printed graph; keep one placeholder
sub(10, '<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>',
    '<div class="fig">figure</div>')

# Q11: stem graph (user) + four option graphs (Claude): rebuild the figure block
_q11 = Q[11]["content_html"]
_i = _q11.index('<div class="fig">figure</div>')
Q[11]["content_html"] = (
    _q11[:_i] + '<div class="fig">figure</div>\n'
    '<p class="qstem">The experiment is repeated at a lower temperature, <i>T</i><sub>2</sub>.</p>\n'
    '<p class="qstem">Which new graph would be obtained?</p>\n'
    '<div class="fig">figure</div>')
sub(11, "A B C D A B C D", "A B C D", field="content_text")
for L in "ABCD":
    Q[11]["options"][L] = "[structure %s]" % L
LOG.append("Q11 content_html: stem graph + option-graph grid placeholder; options -> [structure A-D]")
sub(11, "(g)       ∆<i>H </i>=", "(g)&emsp;&emsp;∆<i>H</i> =")

# Q13: the two titration curves (+ their captions I and II) are ONE snip
sub(13, r'\n<table class="qt">.*?</table>', '\n<div class="fig">figure</div>', rx=True)
sub(13, " I II Which statement", " Which statement", field="content_text")

# Q16: E(standard) typed before each couple (the symbol was a figure the parser dropped);
# the school's "CI-" (capital I) is the element chlorine, written Cl
sub(16, "<td>(I<sub>2</sub>/I<sup>−</sup>) is less positive<b> </b>than (C<i class=\"el\">l</i>"
        "<sub>2</sub>/C<i><span class=\"sr\">I</span></i><sup>−</sup>).</td>",
    "<td><i>E</i><sup>⦵</sup>(I<sub>2</sub>/I<sup>−</sup>) is less positive than "
    "<i>E</i><sup>⦵</sup>(C<i class=\"el\">l</i><sub>2</sub>/C<i class=\"el\">l</i>"
    "<sup>−</sup>).</td>")
sub(16, "(I2/I−) is less positive than (Cl2/CI−).",
    "E⦵(I2/I−) is less positive than E⦵(Cl2/Cl−).", field="content_text")

# Q23: statements 1-3 are a real list; the search text lost their numbers
sub(23, "of the compound reacts with two moles of 2,4-DNPH. gives two moles",
    "of the compound 1 reacts with two moles of 2,4-DNPH. 2 gives two moles", field="content_text")
sub(23, "on warming. gives one mole of CHI3", "on warming. 3 gives one mole of CHI3", field="content_text")

# Q30: "Sc3+," came through as a stacked pair
sub(30, '<span class="stk post"><span>3+</span><span>, </span></span>which',
    "<sup>3+</sup>, which")

# ------------------------------------------------ 5. typed statements -> ol.stmts
STMT = re.compile(r'(?:<p class="qstem eqn">\s*(\d)\s*\t\s*(.*?)</p>\n?)+', re.S)
ONE = re.compile(r'<p class="qstem eqn">\s*(\d)\s*\t\s*(.*?)</p>', re.S)
for qn in (6, 14, 17, 26, 30):
    h = Q[qn]["content_html"]
    ms = list(STMT.finditer(h))
    assert len(ms) == 1, (qn, len(ms))
    items = ONE.findall(ms[0].group(0))
    assert [int(n) for n, _ in items] == list(range(1, len(items) + 1)), (qn, items)
    ol = '<ol class="stmts">' + "".join("<li>%s</li>" % t.strip() for _, t in items) + "</ol>\n"
    Q[qn]["content_html"] = h[:ms[0].start()] + ol + h[ms[0].end():]
    LOG.append("Q%d statements 1-%d -> ol.stmts" % (qn, len(items)))

# ------------------------------------------------ 6. global tidy ----------
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789" + MINUS))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
SUPRX = re.compile("[" + "".join(SUP) + "]+")
SUBRX = re.compile("[" + "".join(SUB) + "]+")


def tidy(s, html):
    # Unicode super/subscript characters -> real markup (HTML) / plain digits (text)
    if html:
        s = SUPRX.sub(lambda m: "<sup>" + "".join(SUP[c] for c in m.group()) + "</sup>", s)
        s = SUBRX.sub(lambda m: "<sub>" + "".join(SUB[c] for c in m.group()) + "</sub>", s)
        # a trailing space typed inside an inline element belongs outside it
        s = re.sub(r" +</(i|b|sub|sup)>", r"</\1> ", s)
        s = re.sub(r"</(i|b)> +(?=[.,)])", r"</\1>", s)
    else:
        s = SUPRX.sub(lambda m: "".join(SUP[c] for c in m.group()), s)
        s = SUBRX.sub(lambda m: "".join(SUB[c] for c in m.group()), s)
    # a figure-dash/en dash in front of a digit is a minus sign (negative numbers, exponents)
    s = re.sub(r"(?<!\d)–(?=\d)", MINUS, s)
    s = re.sub(r"(?<=10)–(?=\d)", MINUS, s)  # exponent minus typed in plain text
    # runs of typed spaces between words
    s = re.sub(r"(?<=\S) {2,}(?=\S)", " ", s)
    s = s.replace("<br></td>", "</td>")
    return s


for qn, r in Q.items():
    for key, html in (("content_html", True), ("content_text", False)):
        r[key] = tidy(r[key], html)
    for k, v in r["options"].items():
        r["options"][k] = tidy(v, False)
LOG.append("global: unicode sub/superscripts -> markup; en dash before a digit -> U+2212; "
           "space runs collapsed; trailing <br> in option cells removed")
# the same tidy applied to the Q16 ⦵ sign: (already U+29B5)

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
for qn, ps in by_q.items():
    blocks = sorted((p for p in ps if p["kind"] == "block"), key=lambda p: p["slot"])
    opts = [p for p in ps if p["kind"] == "option"]
    for o, p in enumerate(blocks + sorted(opts, key=lambda p: p["slot"]), start=1):
        p["ordinal"] = o
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count('<div class="fig">')
    ps = by_q.get(qn, [])
    want = sum(1 for p in ps if p["kind"] == "block") + (
        1 if any(p["kind"] == "option" for p in ps) else 0)
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
        if re.search(r"[-∏]", r[key]):
            bad.append("Q%d: private-use / product glyph left in %s" % (qn, key))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if "\t" in r["content_html"] and qn != 8:
        bad.append("Q%d: leftover tab" % qn)
    if re.search(r'<p class="qstem eqn">\d', r["content_html"]):
        bad.append("Q%d: typed statement left as a paragraph" % qn)
    if re.search(r"[⁰-₟²³¹]", r["content_html"]):
        bad.append("Q%d: unicode super/subscript left" % qn)
assert not bad, "\n".join(bad)
assert sorted(Q) == list(range(1, 31))

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
exp = {2: 4, 8: 1, 10: 1, 11: 5, 13: 1, 23: 1, 25: 1, 26: 1}
got = {q: len(v) for q, v in by_q.items()}
assert got == exp, got
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
