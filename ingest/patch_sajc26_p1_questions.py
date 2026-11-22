"""SAJC 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.sajc26_p1_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school SAJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_sajc26_p1_questions <out> <build_dir>

Table-shape paper (the school's three big tables are split one-per-question by
sajc26_p1_prep). Claude snips the 16 diagram assets (crop_sajc26_p1_figures.py).
Every edit asserts its match count: a silent miss is how a fix ships unapplied.

School slips (grammar / wording) are NOT changed here: they are listed for the
user to rule on (see the hand-off message); typography (degree signs, minus
signs, Unicode sub/superscripts, stray spaces, typed statements) is fixed.
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
FIGURE_DASH = "‒"
FIG = '<div class="fig">figure</div>'


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


# ------------------------------------------------ 1. figure plan ----------
# 16 assets: stem figures Q5, Q9, Q17, Q20, Q21, Q30; combined numbered snips
# Q23 (reactions 1-3) and Q25 (structures 1-3); option sets Q19 and Q22 (A-D).
# Q1 (fractions), Q2, Q3 carry no figure (the extractor's "figures" there are
# the OMML fractions / page furniture); Q25 and Q30 had extra stem slots.
def drop(qn, slots):
    global PLAN
    gone = [p for p in PLAN if p["question"] == qn and p["slot"] in slots]
    assert len(gone) == len(slots), (qn, slots, gone)
    PLAN = [p for p in PLAN if p not in gone]
    LOG.append("Q%d asset plan: dropped %s" % (qn, slots))


drop(1, ["stem1"])
drop(2, ["stem1"])
drop(3, ["stem1"])
drop(25, ["stem2", "stem3"])
drop(30, ["stem2"])
PLAN.append({"question": 23, "index": 0, "kind": "block", "slot": "stem1",
             "n_parts": 1, "ordinal": 1,
             "storage_path": "SAJC_H2_P1_Q23_stem1_2026.png"})
LOG.append("Q23 asset plan: added stem1 (combined numbered snip)")

# Q23: three reaction rows in a numbered table -> ONE combined snip with the numerals
sub(23, r'<table class="qt">.*?</table>', FIG, rx=True)
sub(23, "nucleophile? 1 2 3 A", "nucleophile? A", field="content_text")
# Q25: typed numerals "1" / "3" and two placeholders -> ONE combined snip
sub(25, r'<p class="qstem eqn">1\s*</p>\n<div class="fig">figure</div>\n'
        r'<p class="qstem eqn">3\s*</p>\n<div class="fig">figure</div>', FIG, rx=True)
sub(25, "What could J be? 1 3 A", "What could J be? A", field="content_text")
# Q30: the lead-in below the figure is a stem line, not a centred line
sub(30, '<p class="c">Which will decrease the cell potential? </p>',
    '<p class="qstem">Which will decrease the cell potential?</p>')

# ------------------------------------------------ 2. per-question edits ----
# Q1: the options are four stacked fractions; the extractor set the numerators
#     and denominators as subscripts
def frac(n, d):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)


FR = {"A": ("<i>L</i>", "24000"), "B": ("2<i>L</i>", "24000"),
      "C": ("24000", "<i>L</i>"), "D": ("24000", "2<i>L</i>")}
tbl = '<table class="opts-table">' + "".join(
    '<tr><td class="ol">%s</td><td>%s</td></tr>' % (k, frac(*FR[k])) for k in "ABCD") + "</table>"
sub(1, r'<table class="opts-table">.*?</table>', tbl.replace("\\", "\\\\"), rx=True)
OPT1 = {"A": "L/24000", "B": "2L/24000", "C": "24000/L", "D": "24000/(2L)"}
Q[1]["options"] = OPT1
sub(1, r"A \(L\)/\(24000\) \| B \(2L\)/\(24000\) \| C \(24000\)/\(L\) \| D \(24000\)/\(2L\) \|",
    "A L/24000 | B 2L/24000 | C 24000/L | D 24000/(2L) |", field="content_text", rx=True)

# Q4 / Q8 / Q16: typed statements "N<tab>text" -> house ol.stmts
STMT = re.compile(r'(?:<p class="qstem eqn">\s*(\d)\s*\t\s*(.*?)</p>\n?)+', re.S)
ONE = re.compile(r'<p class="qstem eqn">\s*(\d)\s*\t\s*(.*?)</p>', re.S)
for qn in (4, 8, 16):
    h = Q[qn]["content_html"]
    ms = list(STMT.finditer(h))
    assert len(ms) == 1, (qn, len(ms))
    items = ONE.findall(ms[0].group(0))
    assert [int(n) for n, _ in items] == list(range(1, len(items) + 1)), (qn, items)
    ol = '<ol class="stmts">' + "".join("<li>%s</li>" % t.strip() for _, t in items) + "</ol>\n"
    Q[qn]["content_html"] = h[:ms[0].start()] + ol + h[ms[0].end():]
    LOG.append("Q%d statements 1-%d -> ol.stmts" % (qn, len(items)))

# Q14 / Q20: the statements are an auto-numbered Word list (numbers lost in
# extraction): three plain paragraphs after "Which statements ...?"
for qn, lead in ((14, "Which statements account for this difference?"),
                 (20, "Which statements are correct?")):
    m = re.search(r'(<p class="qstem">%s</p>\n)((?:<p class="qstem">[^\n]*?</p>\n){3})'
                  % re.escape(lead), Q[qn]["content_html"])
    assert m, qn
    items = re.findall(r'<p class="qstem">([^\n]*?)</p>', m.group(2))
    assert len(items) == 3, items
    sub(qn, re.escape(m.group(2)),
        '<ol class="stmts">' + "".join("<li>%s</li>" % t.strip() for t in items) + "</ol>\n".replace("\\", "\\\\"),
        rx=True)
    # the search text lost the numbers: put them back
    plain = [re.sub(r"<[^>]+>", "", t).strip() for t in items]
    old = " ".join(plain)
    new = " ".join("%d %s" % (i + 1, t) for i, t in enumerate(plain))
    sub(qn, re.escape(old), new.replace("\\", "\\\\"), field="content_text", rx=True)

# Q24: the two properties are a bulleted list (house style: ul.stmts)
m = re.search(r'(<p class="qstem">Compound Z has the empirical formula[^\n]*</p>\n)'
              r'((?:<p class="qstem">It [^\n]*?</p>\n){2})', Q[24]["content_html"])
assert m
_b = re.findall(r'<p class="qstem">([^\n]*?)</p>', m.group(2))
assert len(_b) == 2, _b
sub(24, re.escape(m.group(2)),
    '<ul class="stmts">' + "".join("<li>%s</li>" % t.strip() for t in _b) + "</ul>\n".replace("\\", "\\\\"),
    rx=True)

# Q9: the two experiment lines are typed with tabs and runs of spaces
sub(9, '<p class="qstem eqn">Experiment', '<p class="qstem">Experiment', count=2)
Q[9]["content_html"] = Q[9]["content_html"].replace("\t", " ")
LOG.append("Q9 tabs in the experiment lines -> spaces")

# Q10: an empty superscript before the degree sign; Q4 / Q11: degree typed as a superscript o
sub(10, "1000<sup> </sup>°C", "1000 °C")
sub(4, "109.5<sup>o</sup>.", "109.5°.")
sub(4, "109.5o.", "109.5°.", field="content_text")
sub(11, "<i>T</i> <sup> o</sup>C", "<i>T</i> °C", count=2)
sub(11, "T oC", "T °C", field="content_text", count=2)

# Q25: the full stop was typed inside the subscript
sub(25, "KMnO<sub>4. </sub>The", "KMnO<sub>4</sub>. The")

# Q26: charges typed with an en dash -> minus sign
sub(26, "<sup>2–</sup>", "<sup>2" + MINUS + "</sup>")
sub(26, "]2–", "]2" + MINUS, field="content_text")
Q[26]["options"]["B"] = Q[26]["options"]["B"].replace("]2–", "]2" + MINUS)
assert "]2" + MINUS in Q[26]["options"]["B"]

# ------------------------------------------------ 2b. school slips --------
# Fixed on the user's ruling (2026-11-21): every slip flagged at ingest is corrected.
SLIPS = [
    (5, "is a plot of 1 mole of ideal gas", "is a plot for 1 mole of ideal gas", 1),
    (8, "its lattice energy at room temperature</li>", "its lattice energy at room temperature.</li>", 1),
    (9, "of ethyl ethanoate was reacted.", "of ethyl ethanoate were reacted.", 2),
    (9, "in experiment 2?", "in Experiment 2?", 1),
    (17, "In which order do the relative ease", "In which order does the relative ease", 1),
    (21, "Ester can be converted to alcohol", "An ester can be converted to an alcohol", 1),
    (21, "acid base reaction", "acid-base reaction", 1),
    (25, "gives orange precipitate", "gives an orange precipitate", 1),
]
for qn, old, new, n in SLIPS:
    sub(qn, old, new, count=n)
    plain = lambda t: re.sub(r"<[^>]+>", "", t)
    o, nw = plain(old).replace("</li>", ""), plain(new).replace("</li>", "")
    if qn == 8:
        o, nw = "its lattice energy at room temperature 3", "its lattice energy at room temperature. 3"
    assert Q[qn]["content_text"].count(o) == n, (qn, o, Q[qn]["content_text"].count(o))
    Q[qn]["content_text"] = Q[qn]["content_text"].replace(o, nw)
    for k, v in Q[qn]["options"].items():
        Q[qn]["options"][k] = v.replace(o, nw)
    LOG.append("Q%d slip fixed: %r -> %r" % (qn, o, nw))

# ------------------------------------------------ 3. global tidy ----------
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789" + MINUS))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
SUPRX = re.compile("[" + "".join(SUP) + "]+")
SUBRX = re.compile("[" + "".join(SUB) + "]+")


def tidy(s, html):
    s = s.replace(FIGURE_DASH, MINUS)       # figure dash typed for charges / exponents
    if html:
        s = SUPRX.sub(lambda m: "<sup>" + "".join(SUP[c] for c in m.group()) + "</sup>", s)
        s = SUBRX.sub(lambda m: "<sub>" + "".join(SUB[c] for c in m.group()) + "</sub>", s)
        # a space typed inside an inline element belongs outside it
        s = re.sub(r" +</(i|b|sub|sup)>", r"</\1> ", s)
        s = re.sub(r"</(i|b)> +(?=[.,)])", r"</\1>", s)
        s = re.sub(r" +</(p|td|li)>", r"</\1>", s)
    else:
        s = SUPRX.sub(lambda m: "".join(SUP[c] for c in m.group()), s)
        s = SUBRX.sub(lambda m: "".join(SUB[c] for c in m.group()), s)
    # runs of typed spaces between words
    s = re.sub(r"(?<=\S) {2,}(?=\S)", " ", s)
    return s.strip() if not html else s


for qn, r in Q.items():
    for key, html in (("content_html", True), ("content_text", False)):
        r[key] = tidy(r[key], html)
    for k, v in r["options"].items():
        r["options"][k] = tidy(v, False)
LOG.append("global: U+2012 -> U+2212; Unicode sub/superscripts -> markup; spaces moved "
           "out of inline elements; space runs collapsed")

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
for qn, ps in by_q.items():
    blocks = sorted((p for p in ps if p["kind"] == "block"), key=lambda p: p["slot"])
    opts = sorted((p for p in ps if p["kind"] == "option"), key=lambda p: p["slot"])
    for o, p in enumerate(blocks + opts, start=1):
        p["ordinal"] = o
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count(FIG)
    ps = by_q.get(qn, [])
    want = sum(1 for p in ps if p["kind"] == "block") + (
        1 if any(p["kind"] == "option" for p in ps) else 0)
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    opts = [p for p in ps if p["kind"] == "option"]
    if opts and not r["content_html"].rstrip().endswith(FIG):
        bad.append("Q%d: option figures but the last element is not their placeholder" % qn)
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
        if re.search("[\ue000-\uf8ff]", r[key]):
            bad.append("Q%d: private-use glyph left in %s" % (qn, key))
        if FIGURE_DASH in r[key]:
            bad.append("Q%d: U+2012 left in %s" % (qn, key))
        if re.search(r" {2,}", r[key]) or "\t" in r[key]:
            bad.append("Q%d: space run / tab left in %s" % (qn, key))
    for k, v in r["options"].items():
        if FIGURE_DASH in v or re.search("[\ue000-\uf8ff]", v):
            bad.append("Q%d option %s: stray glyph" % (qn, k))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if re.search(r"<sup>\s*[o°]\s*</sup>|<(sub|sup|i|b)>\s*</\1>", r["content_html"]):
        bad.append("Q%d: superscript degree or empty inline element left" % qn)
    if re.search(r'<p class="qstem eqn">', r["content_html"]):
        bad.append("Q%d: typed statement left as a paragraph" % qn)
    if re.search(r"[₀-₉⁰-⁹]", r["content_html"] + r["content_text"]):
        bad.append("Q%d: Unicode sub/superscript left" % qn)
assert not bad, "GATE:\n" + "\n".join(bad)
assert sorted(Q) == list(range(1, 31))

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets (%d stem snips, %d option crops)" % (
    len(Q), len(PLAN), sum(p["kind"] == "block" for p in PLAN),
    sum(p["kind"] == "option" for p in PLAN)))
