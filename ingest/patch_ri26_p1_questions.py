"""RI 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.extract_questions <unz> <word.pdf> <out> \
      --school RI --level H2 --paper P1 --year 2026
  python3 -m ingest.patch_ri26_p1_questions <out> <build_dir>

Table-shape paper (same family as RI 2024 H2 P1). The user snips every stem
figure; Claude snips the four all-diagram option sets (Q11, Q19, Q27, Q29:
crop_ri26_p1_options.py). Every edit asserts its match count: a silent miss is
how a fix ships unapplied.
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
EL = '<i class="el">l</i>'


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
            rows.append([re.sub(r"<[^>]+>", "", c.replace("<br>", " "))
                         for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)])
        old = re.sub(r" {2,}", " ", " ".join("".join(r) for r in rows))
        out.append((old, " ".join(" | ".join(c.strip() for c in r if c) for r in rows)))
    return out


# ------------------------------------------------ 1. table search text -----
# (done FIRST, from the extractor's own tables, before the markup is touched)
for old, new in table_text(Q[14]["content_html"]):
    sub(14, re.escape(old), new.replace("\\", "\\\\"), field="content_text", rx=True)

# ------------------------------------------------ 2. figure plan ----------
# Q11: the 2x2 grid of graphs IS the option set (letters printed inside the grid),
#      so the four "stem" figures become options A-D (Claude's crops).
# Q20: products 1-4 are ONE combined snip, numerals included (stem2).
# Q26: steps 1-3 are ONE combined snip, numerals included (stem2).
DROP = {11: ["stem1", "stem2", "stem3", "stem4"], 20: ["stem3", "stem4", "stem5"],
        26: ["stem3", "stem4"]}
for qn, slots in DROP.items():
    gone = [p for p in PLAN if p["question"] == qn and p["slot"] in slots]
    assert len(gone) == len(slots), (qn, gone)
    PLAN = [p for p in PLAN if p not in gone]
    LOG.append("Q%d asset plan: dropped %s" % (qn, slots))
for L in "ABCD":
    PLAN.append({"question": 11, "index": -1, "kind": "option", "slot": L,
                 "n_parts": 1, "ordinal": 0,
                 "storage_path": "RI_H2_P1_Q11_%s_2026.png" % L})
LOG.append("Q11 asset plan: added options A-D")

# ------------------------------------------------ 3. per-question edits ----
# Q4: the ratio is a displayed (centred) equation; rho is italic as printed
sub(4, '<p class="qstem">ρ= <span class="frac"><span class="fnum">value of property of aluminium </span>',
    '<p class="c"><i>ρ</i> = <span class="frac"><span class="fnum">value of property of aluminium</span>')
sub(4, "For which property is ρ more than 1?", "For which property is <i>ρ</i> more than 1?")
sub(4, "ρ= (value", "ρ = (value", field="content_text")

# Q7: the school typed U+2212 (minus) for the hyphens in the compound names.
# ("trans-but-ene", without the locant, is the school's own wording: kept.)
sub(7, "<i>cis</i>−but−2-ene and <i>trans−</i>but−ene",
    "<i>cis</i>-but-2-ene and <i>trans</i>-but-ene")
sub(7, "2−hydroxybenzoic acid and 4−hydroxybenzoic acid",
    "2-hydroxybenzoic acid and 4-hydroxybenzoic acid")
for k in ("B", "D"):
    assert MINUS in Q[7]["options"][k]
    Q[7]["options"][k] = Q[7]["options"][k].replace(MINUS, "-")
sub(7, MINUS, "-", field="content_text", count=6)

# Q8 / Q25: the header row's blank cell belongs over the row numbers (first column)
sub(8, '<tr><td><p class="c">reagent</p></td><td><p class="c">colour of resultant solution</p></td><td></td></tr>',
    '<tr><td></td><td><p class="c">reagent</p></td><td><p class="c">colour of resultant solution</p></td></tr>')
sub(8, '<p class="c"> sodium thiosulfate</p>', '<p class="c">sodium thiosulfate</p>')
sub(8, '<td><p class="qstem">(\\d)</p></td>', r'<td>\1</td>', rx=True, count=3)
sub(25, '<tr><td><p class="c">reducing agent</p></td><td><p class="c">compound</p></td><td></td></tr>',
    '<tr><td></td><td><p class="c">reducing agent</p></td><td><p class="c">compound</p></td></tr>')
sub(25, '<td><p class="qstem">(\\d)</p></td>', r'<td>\1</td>', rx=True, count=4)

# Q10: the equation was spaced out by hand
sub(10, r'<p class="c">H<sub>2</sub>O\(l\)\s+→\s+½ O<sub>2</sub>\(g\) \+ H<sub>2</sub>\(g\)\s*</p>',
    '<p class="c">H<sub>2</sub>O(%s) → ½O<sub>2</sub>(g) + H<sub>2</sub>(g)</p>' % EL, rx=True)
sub(10, "→ ½ O2(g)", "→ ½O2(g)", field="content_text")

# Q11: one option-grid placeholder instead of the layout table; options are figures
sub(11, r'<table class="qt center">.*?</table>', FIG, rx=True)
for L in "ABCD":
    Q[11]["options"][L] = "[structure %s]" % L
LOG.append("Q11 options -> [structure A-D]")

# Q12: stray superscript space
sub(12, "350<sup> </sup>K", "350 K")

# Q13: degree sign typed as a superscript o; K_p italics split over three runs
sub(13, "500 <sup>o</sup>C", "500 °C")
sub(13, "500 oC", "500 °C", field="content_text")
sub(13, "<i>K</i><i><sub>p</sub></i><i>, </i>for", "<i>K</i><sub><i>p</i></sub>, for")

# Q14: the two typed lines about the solutions are one block in print
sub(14, 'Solutions I and II are monobasic acids.</p>\n<p class="qstem">Solutions III',
    "Solutions I and II are monobasic acids.<br>Solutions III")

# Q15: "HCl" typed with a plain l in option C
sub(15, "is added to dilute HCl, a yellow", "is added to dilute HC%s, a yellow" % EL)

# Q20: products 1-4 -> one combined snip (numerals in the picture)
sub(20, '<ol class="stmts">' + ("<li>%s</li>" % FIG) * 4 + "</ol>", FIG)

# Q21 / Q22 / Q29: the letter labels under the scheme were aligned with runs of
# spaces; they are part of the snip instead
sub(21, r'\n<p class="c">\s+<b>T\s+</b></p>', "", rx=True)
sub(22, r'\n<p class="qstem">\s+<b>V</b>\s+<b>W</b></p>', "", rx=True)
sub(29, r'\n<p class="c">\s+<b>X</b>\s+<b>Y</b></p>', "", rx=True)

# Q22: degree signs typed as superscript o
sub(22, "−15<sup>o</sup>", "−15°")
sub(22, "+20<sup>o</sup>", "+20°")
sub(22, "−15o", "−15°", field="content_text")
sub(22, "+20o", "+20°", field="content_text")

# Q23: the two conditions are one block in print
sub(23, r'<p class="qstem">condition I\s+: room temperature\s*</p>\n<p class="qstem">condition II : heat under reflux</p>',
    '<p class="qstem">condition I : room temperature<br>condition II : heat under reflux</p>', rx=True)

# Q26: steps 1-3 -> one combined snip (numerals in the picture)
sub(26, '<ol class="stmts">' + ("<li>%s</li>" % FIG) * 3 + "</ol>", FIG)

# Q28: the three results are a bulleted list (house style: ul.stmts)
_b = re.findall(r'<p class="qstem">((?:<b>R</b> (?:does|gives)|When <b>R</b> is treated)[^\n]*?)</p>\n',
                Q[28]["content_html"])
assert len(_b) == 3, _b
sub(28, r'(?:<p class="qstem">(?:<b>R</b> (?:does|gives)|When <b>R</b> is treated)[^\n]*?</p>\n){3}',
    '<ul class="stmts">' + "".join("<li>%s</li>" % t.strip() for t in _b) + "</ul>\n", rx=True)

# ------------------------------------------------ 4. global tidy ----------
def tidy(s, html):
    if html:
        # a space typed inside an inline element belongs outside it
        s = re.sub(r" +</(i|b|sub|sup)>", r"</\1> ", s)
        s = re.sub(r"</(i|b)> +(?=[.,)])", r"</\1>", s)
        s = re.sub(r" +</(p|td|li)>", r"</\1>", s)
    # runs of typed spaces between words
    s = re.sub(r"(?<=\S) {2,}(?=\S)", " ", s)
    return s.strip() if not html else s


for qn, r in Q.items():
    for key, html in (("content_html", True), ("content_text", False)):
        r[key] = tidy(r[key], html)
    for k, v in r["options"].items():
        r["options"][k] = tidy(v, False)
LOG.append("global: spaces moved out of inline elements; space runs collapsed; "
           "trailing spaces in p/td/li removed")

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
        if re.search("[-]", r[key]):
            bad.append("Q%d: private-use glyph left in %s" % (qn, key))
        if re.search(r" {2,}", r[key]) or "\t" in r[key]:
            bad.append("Q%d: space run / tab left in %s" % (qn, key))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if re.search(r"<sup>\s*o\s*</sup>|<(sub|sup|i|b)>\s*</\1>", r["content_html"]):
        bad.append("Q%d: superscript-o degree or empty inline element left" % qn)
assert not bad, "GATE:\n" + "\n".join(bad)
assert sorted(Q) == list(range(1, 31))

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets (%d user stem snips, %d option crops)" % (
    len(Q), len(PLAN), sum(p["kind"] == "block" for p in PLAN),
    sum(p["kind"] == "option" for p in PLAN)))
