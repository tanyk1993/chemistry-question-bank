"""TJC 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.tjc26_p1_prep <unz> <unz_prep>
  python3 -m ingest.redact_inline_answers_pdf word.pdf q.pdf   (colours 0xff,0x3333ff,0xff0000)
  python3 -m ingest.extract_questions <unz_prep> <q.pdf> <out> \
      --school TJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_tjc26_p1_questions <out> <build_dir>

Table-shape paper, one table per question after tjc26_p1_prep (answer-key table
and in-table answer rows removed). Claude snips the 10 diagram assets
(crop_tjc26_p1_figures.py). Every edit asserts its match count.

User rulings (2026-11-24): Q5 "dinitrogen tetroxide"; Q9 "a Period 3 element";
Q13 "changes ... are shown"; Q14 "engines"; Q21 "head-on"; Q25 comma removed;
Q29 "properties of"; Q4 "Boiling point / K". Typography fixed without asking
(minus signs, degree sign, stray spaces, typed statements).
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
FIG = '<div class="fig">figure</div>'


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def sub_opts(qn, old, new, keys):
    for k in keys:
        assert old in Q[qn]["options"][k], (qn, k, old)
        Q[qn]["options"][k] = Q[qn]["options"][k].replace(old, new)


# ------------------------------------------------ 1. figure plan ----------
# 10 assets: Q2 graph, Q3 structure, Q15 both graphs (one snip), Q22 four cell
# structures, Q24 structure, Q27 cell, Q30 complex.
gone = [p for p in PLAN if p["question"] == 3 and p["slot"] == "stem2"]
assert len(gone) == 1
PLAN = [p for p in PLAN if p not in gone]
LOG.append("Q3 asset plan: dropped stem2 (one structure only)")
# Q15: four placeholders for one combined graph snip: keep only the last
h = Q[15]["content_html"]
assert h.count(FIG) == 4
parts = h.split(FIG)
Q[15]["content_html"] = "".join(parts[:4]) + FIG + parts[4]
assert Q[15]["content_html"].count(FIG) == 1
Q[15]["content_html"] = re.sub(r"\n{2,}", "\n", Q[15]["content_html"]).lstrip()
LOG.append("Q15: four figure placeholders -> one (after 'graphs were obtained')")
assert [p["slot"] for p in PLAN if p["question"] == 15] == ["stem1"]

# ------------------------------------------------ 2. per-question edits ----
# Q2: the options are the points A-D on the graph
Q[2]["options"] = {L: "[point %s]" % L for L in "ABCD"}
LOG.append("Q2 options -> [point A-D] (labels are inside the figure)")

# Q3: the question line was centred
sub(3, '<p class="c">What are the values of the bond angles x, y and z?</p>',
    '<p class="qstem">What are the values of the bond angles x, y and z?</p>')

# Q4: header slash; the search text ran the table cells together
sub(4, "Boiling point/ K", "Boiling point / K")
sub(4, "CompoundBoiling point/ K HBr207 NH3240 HF293 H2O373",
    "Compound Boiling point / K HBr 207 NH3 240 HF 293 H2O 373", field="content_text")

# Q5 (user): dinitrogen tetroxide
sub(5, "dinitrogen dioxide", "dinitrogen tetroxide")
sub(5, "dinitrogen dioxide", "dinitrogen tetroxide", field="content_text")

# Q8: search text of the fraction
sub(8, "V (1)/(p) at constant T", "V 1/p at constant T", field="content_text")

# Q9 (user)
sub(9, "an oxide of Period 3 element", "an oxide of a Period 3 element")
sub(9, "an oxide of Period 3 element", "an oxide of a Period 3 element", field="content_text")

# Q13 (user): changes ... are shown
sub(13, "The Gibbs free energy change of reaction at two",
    "The Gibbs free energy changes of reaction at two")
sub(13, "The Gibbs free energy change of reaction at two",
    "The Gibbs free energy changes of reaction at two", field="content_text")
# signs in the option table are hyphens
sub(13, r"<td>-</td>", "<td>" + MINUS + "</td>", count=4, rx=True)
sub(13, r"(?<= )-(?= \|)", MINUS, field="content_text", count=4, rx=True)
Q[13]["options"] = {k: v.replace("-", MINUS) for k, v in Q[13]["options"].items()}
sub(13, r"(?<==\s)-(?=\d)", MINUS, count=1, rx=True)
sub(13, r"(?<==\s)-(?=\d)", MINUS, field="content_text", count=1, rx=True)

# Q11: negative values typed with a hyphen
sub(11, r"<td>-(?=\d)", "<td>" + MINUS, count=4, rx=True)
sub(11, r"(?<= )-(?=\d)", MINUS, field="content_text", count=4, rx=True)
Q[11]["options"] = {k: re.sub(r"^-(?=\d)", MINUS, v) for k, v in Q[11]["options"].items()}

# Q14 (user): engines
sub(14, "internal combustion engine.", "internal combustion engines.")
sub(14, "internal combustion engine.", "internal combustion engines.", field="content_text")

# Q15: empty bold superscript after option C
sub(15, r"<b><sup>\s*</sup></b>", "", rx=True)

# Q12: the empty subscript hid the space before the arrow
sub(12, r"aq<sub>\s*</sub>→", "aq →", rx=True)

# Q21 (user): head-on
sub(21, "head on overlap", "head-on overlap")
sub(21, "head on overlap", "head-on overlap", field="content_text")
sub_opts(21, "head on overlap", "head-on overlap", "D")

# Q25 (user): comma
sub(25, "molecular formula, C", "molecular formula C")
sub(25, "molecular formula, C", "molecular formula C", field="content_text")

# Q28: the three statements sit in a table -> house ol.stmts
m = re.search(r'<table class="qt">(.*?)</table>', Q[28]["content_html"], re.S)
assert m
rows = re.findall(r"<tr><td>(\d)</td><td>(.*?)</td></tr>", m.group(1), re.S)
assert [int(n) for n, _ in rows] == [1, 2, 3], rows
ol = '<ol class="stmts">' + "".join("<li>%s</li>" % t.strip() for _, t in rows) + "</ol>"
Q[28]["content_html"] = Q[28]["content_html"].replace(m.group(0), ol)
sub(28, "1pH of", "1 pH of", field="content_text")
sub(28, "2The number", "2 The number", field="content_text")
sub(28, "3Increasing", "3 Increasing", field="content_text")
LOG.append("Q28 statements table -> ol.stmts")

# Q29 (user): of
sub(29, "properties about the first", "properties of the first")
sub(29, "properties about the first", "properties of the first", field="content_text")

# Q30: "student G / student H" typed with tabs -> two-row table
m = re.search(r'<p class="qstem eqn">student G\t(.*?)</p>\n<p class="qstem eqn">student H\t(.*?)</p>',
              Q[30]["content_html"], re.S)
assert m
tbl = ('<table class="qt"><tr><td>student G</td><td>%s</td></tr>'
       '<tr><td>student H</td><td>%s</td></tr></table>' % (m.group(1).strip(), m.group(2).strip()))
Q[30]["content_html"] = Q[30]["content_html"].replace(m.group(0), tbl)
LOG.append("Q30 student G/H -> two-row table")

# ------------------------------------------------ 3. global tidy ----------
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789" + MINUS))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
SUPRX = re.compile("[" + "".join(SUP) + "]+")
SUBRX = re.compile("[" + "".join(SUB) + "]+")


def tidy(s, html):
    s = s.replace("‒", MINUS).replace("º", "°")
    # exponent / unit minus typed as hyphen or en dash
    s = re.sub(r"\b(mol|dm|s)[-–](?=\d)", lambda m: m.group(1) + MINUS, s)
    s = re.sub(r"<sup>[-–](?=\d)", "<sup>" + MINUS, s)
    # charges typed with an en dash
    s = re.sub(r"<sup>(\d?)–</sup>", lambda m: "<sup>" + m.group(1) + MINUS + "</sup>", s)
    s = re.sub(r"<span>(\d?)–</span>", lambda m: "<span>" + m.group(1) + MINUS + "</span>", s)
    s = re.sub(r"(?<=[A-Za-z0-9])–(?=\s|$|\|)", MINUS, s)
    if html:
        s = SUPRX.sub(lambda m: "<sup>" + "".join(SUP[c] for c in m.group()) + "</sup>", s)
        s = SUBRX.sub(lambda m: "<sub>" + "".join(SUB[c] for c in m.group()) + "</sub>", s)
        s = re.sub(r"<(sub|sup)>\s*</\1>", "", s)
        s = re.sub(r'<i><span class="sr">\s*</span></i>', "", s)
        s = re.sub(r" +</(i|b|sub|sup)>", r"</\1> ", s)
        s = re.sub(r"</(i|b)> +(?=[.,)])", r"</\1>", s)
        s = re.sub(r"<(i|b)></\1>", "", s)
        s = re.sub(r" +</(p|td|li)>", r"</\1>", s)
        s = re.sub(r'(<p class="[^"]*">) +', r"\1", s)
    else:
        s = SUPRX.sub(lambda m: "".join(SUP[c] for c in m.group()), s)
        s = SUBRX.sub(lambda m: "".join(SUB[c] for c in m.group()), s)
    s = re.sub(r"(?<=\S) {2,}(?=\S)", " ", s)
    return s.strip() if not html else s


for qn, r in Q.items():
    for key, html in (("content_html", True), ("content_text", False)):
        r[key] = tidy(r[key], html)
    for k, v in r["options"].items():
        r["options"][k] = tidy(v, False)
LOG.append("global: minus signs, degree sign, charge dashes, empty inline elements, "
           "stray spaces")

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
for qn, ps in by_q.items():
    blocks = sorted((p for p in ps if p["kind"] == "block"), key=lambda p: p["slot"])
    for o, p in enumerate(blocks, start=1):
        p["ordinal"] = o
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count(FIG)
    want = len(by_q.get(qn, []))
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
        if re.search("[-]", r[key]):
            bad.append("Q%d: private-use glyph left in %s" % (qn, key))
        if "‒" in r[key] or "º" in r[key]:
            bad.append("Q%d: U+2012 / ordinal sign left in %s" % (qn, key))
        if re.search(r" {2,}", r[key]) or "\t" in r[key]:
            bad.append("Q%d: space run / tab left in %s" % (qn, key))
        if re.search(r"\b(mol|dm|s)[-–]\d", r[key]):
            bad.append("Q%d: hyphen exponent left in %s" % (qn, key))
    for k, v in r["options"].items():
        if re.search("[-]", v) or re.search(r"\b(mol|dm|s)[-–]\d", v):
            bad.append("Q%d option %s: stray glyph / hyphen exponent" % (qn, k))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if re.search(r"<(sub|sup|i|b)>\s*</\1>", r["content_html"]):
        bad.append("Q%d: empty inline element left" % qn)
    if re.search(r'<p class="qstem eqn">', r["content_html"]):
        bad.append("Q%d: typed statement left as a paragraph" % qn)
    if re.search(r"[₀-₉⁰-⁹]", r["content_html"] + r["content_text"]):
        bad.append("Q%d: Unicode sub/superscript left" % qn)
    if "tetroxide" not in r["content_text"] and qn == 5:
        bad.append("Q5 tetroxide missing")
assert not bad, "GATE:\n" + "\n".join(bad)
assert sorted(Q) == list(range(1, 31))
assert len(PLAN) == 10, len(PLAN)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
