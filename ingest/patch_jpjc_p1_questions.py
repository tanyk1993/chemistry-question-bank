"""JPJC 2024 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.jpjc_p1_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school JPJC --level H2 --paper P1 --year 2024 --no-crops
  python3 -m ingest.patch_jpjc_p1_questions <out> <build_dir>

Every edit asserts its match count: a silent miss is how a fix ships unapplied.
The user snips every figure by hand (standing rule), so the asset plan here is
the SNIP LIST; slots follow DOM order (HANDOFF SS7).
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
FIG = '<div class="fig">figure</div>'


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def set_plan(qn, entries):
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...].
    Stem figures first, then ONE option grid whose assets continue the
    sequence."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "JPJC_H2_P1_Q%d_%s_2024.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


def bold(qn, old, new, count=1):
    """Restore bold that Word applies through the paragraph STYLE (the
    extractor reads only run-level <w:b/>); html only, text is unaffected."""
    sub(qn, old, new, count=count)


# ---- Q5: four graphs = four option snips (A-D) --------------------------------
# (axis-label equation objects were removed by jpjc_p1_prep; the snips carry
# the axis titles). One placeholder, options A-D.
assert Q[5]["content_html"].count(FIG) == 1
assert Q[5]["options"] == {L: "[structure %s]" % L for L in "ABCD"}

# ---- Q6: a stray anchored shape with no printed picture; nothing to snip ----------
set_plan(6, [])

# ---- Q9: ONE apparatus picture; the second 'figure' is a hidden image -------------
set_plan(9, [("block", "stem1")])
sub(9, '<p class="c">The increases in mass', '<p class="qstem">The increases in mass')

# ---- Q10: three Word bullets (w:numPr) came out as bare paragraphs ----------------
sub(10, '<p class="qstem">∆<i>H</i><sub>c</sub> of butane is –2877 kJ mol<sup>–1</sup>.</p>\n'
        '<p class="qstem">250 g of water is heated from 12 °C to 100 °C.</p>\n'
        '<p class="qstem">The burner transfers 47% of the heat released from the burning '
        'fuel to the water.</p>',
    '<ul class="stmts"><li>∆<i>H</i><sub>c</sub> of butane is –2877 kJ mol<sup>–1</sup>.</li>'
    '<li>250 g of water is heated from 12 °C to 100 °C.</li>'
    '<li>The burner transfers 47% of the heat released from the burning fuel to the '
    'water.</li></ul>')

# ---- Q12: four graphs = four option snips; the empty A-D table goes --------------
# (the extractor only found B, C, D as pictures: A is a snip too)
sub(12, FIG + r'\n<table class="opts-table">(?:<tr><td class="ol">[A-D]</td><td></td></tr>){4}</table>',
    FIG, rx=True)
Q[12]["options"] = {L: "[structure %s]" % L for L in "ABCD"}
set_plan(12, [("option", L) for L in "ABCD"])

# ---- Q13: Graph 1 + Graph 2 side by side = ONE snip -------------------------------
set_plan(13, [("block", "stem1")])
sub(13, '<p class="c">Which of the following illustrates', '<p class="qstem">Which of the following illustrates')

# ---- Q15: the first placeholder is a stray anchored text box; ONE graph ------------
sub(15, FIG + '\n<p class="qstem">The  graph shows', '<p class="qstem">The graph shows')
sub(15, "that of amylase was kept constant.</p>\n" + FIG,
    "that of amylase was kept constant.</p>\n" + FIG)   # the graph, after the stem
assert Q[15]["content_html"].count(FIG) == 1
set_plan(15, [("block", "stem1")])

# ---- Q20: the header cell 'E' was read as an option letter ------------------------
sub(20, '<tr><td class="ol">E</td><td></td><td></td></tr>', "")
sub(20, '<table class="opts-table"><tr><td class="ol">A</td>',
    '<table class="opts-table"><tr><td class="ol"></td><td>retinol</td><td><b>E</b></td></tr>'
    '<tr><td class="ol">A</td>')
assert "E" in Q[20]["options"]
del Q[20]["options"]["E"]
assert Q[20]["content_text"].endswith(" | E")
Q[20]["content_text"] = Q[20]["content_text"][:-len(" | E")].rstrip()

# ---- Q22: a comma set inside a subscript --------------------------------------------
sub(22, 'CC<i class="el">l</i><sub>4, </sub>CH', 'CC<i class="el">l</i><sub>4</sub>, CH')

# ---- Q25: A is printed beside B in the 2x2 grid: all four = option snips ----------
sub(25, FIG + r'\n<table class="opts-table"><tr><td class="ol">A</td><td>[^\n]*?</td></tr>'
        r'(?:<tr><td class="ol">[BCD]</td><td></td></tr>){3}</table>', FIG, rx=True)
Q[25]["options"] = {L: "[structure %s]" % L for L in "ABCD"}
assert "A (CH3)2C(OH)CH2CH2CH2CHO" in Q[25]["content_text"]   # A's formula stays searchable
set_plan(25, [("option", L) for L in "ABCD"])

# ---- Q26: 'methyl phenylacetate' is the scheme's own caption (inside the snip) -----
sub(26, r'<p class="qstem">\s+methyl </p>\n<p class="qstem">phenylacetate</p>\n', "", rx=True)

# ---- bold the extractor cannot see (style-inherited; the Word PDF shows it) -------
bold(2, "<td>F</td>", "<td><b>F</b></td>")
bold(2, "<td>Ne</td>", "<td><b>Ne</b></td>")
bold(2, "<td>Na</td>", "<td><b>Na</b></td>")
bold(2, "<td>Mg</td>", "<td><b>Mg</b></td>")
bold(2, '<td>A<i class="el">l</i></td>', '<td><b>A<i class="el">l</i></b></td>')
bold(8, "An element M can", "An element <b>M</b> can")
bold(8, "of M<sup>n+</sup>", "of <b>M</b><sup>n+</sup>")
bold(8, "oxidation state of M?", "oxidation state of <b>M</b>?")
bold(20, "forms product E.", "forms product <b>E</b>.")
bold(20, "retinol and E have?", "retinol and <b>E</b> have?")
bold(23, "following cannot be", "following <b>cannot</b> be")
bold(25, "compound F, C", "compound <b>F</b>, C")
bold(25, "produces compound G.", "produces compound <b>G</b>.")
bold(25, "Compound G produces", "Compound <b>G</b> produces")
bold(25, "What could F be?", "What could <b>F</b> be?")
bold(28, "Compound W is", "Compound <b>W</b> is")
bold(28, "in compound W?", "in compound <b>W</b>?")
bold(30, "to electrode X.", "to electrode <b>X</b>.")
bold(30, "Electrons move from electrode X to electrode Y",
     "Electrons move from electrode <b>X</b> to electrode <b>Y</b>")


# ---- user rulings (2026-10-17) -------------------------------------------------
# Q16 REMOVED: two statements are incorrect (A: adding Ca(NO3)2 lowers the pH;
# B: solubility of Ca(OH)2 falls with temperature) and the school's own rationale
# for B ("increasing temperature increases solubility of solids") is wrong.
# Same treatment as HCI 2024 H2 P1 Q15: numbers of the other questions unchanged.
del Q[16]
LOG.append("Q16 removed (flawed question, user ruling)")
for f in ("content_html", "content_text"):
    sub(18, "Which of the following row correctly", "Which of the following rows correctly", field=f)
    sub(5, "the behavior of", "the behaviour of", field=f)
    sub(5, "(measure in K)", "(measured in K)", field=f)
    sub(30, "Aluminum ions", "Aluminium ions", field=f)
    sub(11, "at 378K", "at 378 K", field=f)
    sub(11, "at 1300K", "at 1300 K", field=f)
    # printed paper shows an en dash (the source used a Symbol minus glyph)
    sub(4, "dipole\u2212induced dipole", "dipole\u2013induced dipole", field=f)
    # name: hyphens (the source used Symbol minus glyphs)
    sub(23, "but\u22121\u2212ene", "but-1-ene", field=f)
# Q3: the user edited this live in the admin editor ('a molecule of ...')
for f in ("content_html", "content_text"):
    sub(3, "Why is the molecule of BC", "Why is a molecule of BC", field=f)
    sub(3, "whereas the molecule of PH", "whereas a molecule of PH", field=f)
# exponents: hyphen-minus -> U+2212 (one convention across the bank)
sub(2, "<sup>-1</sup>", "<sup>\u22121</sup>", count=4)
sub(2, "mol-1", "mol\u22121", field="content_text", count=4)

# ---- minus: ONE convention, U+2212 (Q10's two en dashes are a sign and an exponent) -
for f in ("content_html", "content_text"):
    n = Q[10][f].count("–")
    assert n == 2, (f, n)
    Q[10][f] = Q[10][f].replace("–", "−")
    LOG.append("Q10 %s: %d en dash -> minus" % (f, n))
for qn, r in Q.items():
    if qn != 4:            # Q4's en dash in "dipole–induced dipole" is intended
        assert "–" not in r["content_html"], "Q%d still has an en dash" % qn

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count(FIG)
    ps = by_q.get(qn, [])
    want = sum(1 for p in ps if p["kind"] == "block") + (
        1 if any(p["kind"] == "option" for p in ps) else 0)
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    ords = [p["ordinal"] for p in sorted(ps, key=lambda p: p["ordinal"])]
    if ords != list(range(1, len(ords) + 1)):
        bad.append("Q%d: ordinals %r" % (qn, ords))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
assert not bad, "\n".join(bad)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1),
    encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
