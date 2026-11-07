"""MI 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.mi26_p1_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school MI --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_mi26_p1_questions <out> <build_dir>

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


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


# ---- figure plan (declared): stem figures by the user; Q8 option graphs cropped by Claude
EXPECT = {4: ["stem1"], 6: ["stem1"], 8: list("ABCD"), 24: ["stem1"], 27: ["stem1"]}
got = {}
for p in PLAN:
    got.setdefault(p["question"], []).append(p["slot"])
assert got == EXPECT, got

# ---- Q1: d(x2-y2) subscript came through as a tangle of nested sub/sup ----
sub(1, '<sub>x</sub><sup><sub>2</sub></sup><sub>-y</sub><sup><sub>2</sub></sup>',
    '<sub><i>x</i><sup>2</sup>−<i>y</i><sup>2</sup></sub>')
sub(1, "dx2-y2", "dx2−y2", field="content_text")

# ---- Q8: each graph's axis title ("Boiling point of X2" ...) is part of the snipped
# figure (user ruling 2026-11-07), so options{} holds only the figure-only search token
# (index.html skips "[structure A]" as a caption). The title words stay searchable
# because they remain in content_text.
CAP = {"A": "Boiling point of X2", "B": "Bond length of X2",
       "C": "Electronegativity of X", "D": "Ionic radius of X\u2013"}
for k, o in CAP.items():
    assert Q[8]["options"][k] == o, (k, Q[8]["options"][k])
    Q[8]["options"][k] = "[structure %s]" % k
LOG.append("Q8 options -> [structure A-D] (titles are inside the figures)")

# ---- Q9: the E / F row is a column HEADING, not an option "E" ----
sub(9, '<tr><td class="ol">E</td><td><b>F</b></td><td></td></tr>', "")
sub(9, '<table class="opts-table"><tr><td class="ol">A</td>',
    '<table class="opts-table"><tr><td class="ol"></td><td><b>E</b></td><td><b>F</b></td></tr>'
    '<tr><td class="ol">A</td>')
assert "E" in Q[9]["options"]
del Q[9]["options"]["E"]
sub(9, " E F | |", "", field="content_text")
LOG.append("Q9 options -> A-D with E/F column header")

# ---- Q24: the user's structure snip already contains the "humulene" label; drop the typed one ----
sub(24, '<p class="c">humulene</p>\n', "")
sub(24, "product? humulene A 0", "product? A 0", field="content_text")

# ---- Q12: stray italic on the chloride charge (A and B only) ----
sub(12, '<i><sup>−</sup></i>', '<sup>−</sup>', count=2)

# ---- Q13: '(BE = Bond Energy)' is a line inside statement 2, not a paragraph ----
sub(13, '<p class="qstem"><i>(BE = Bond Energy)</i></p></li>',
    '<br><i>(BE = Bond Energy)</i></li>')

# ---- Q14, Q27: ASCII hyphen standing in for the minus of mol dm-3 / s-1 ----
sub(14, "<sup>-", "<sup>−", count=4)
sub(14, "dm-3", "dm−3", field="content_text", count=3)
sub(14, "s-1", "s−1", field="content_text", count=1)
sub(27, "<sup>-", "<sup>−", count=2)
sub(27, "dm-3", "dm−3", field="content_text", count=2)

# ---- Q15, Q17: hand-spaced gaps in centred equations ----
sub(15, "(g)   (fast)", "(g)&emsp;(fast)")
sub(15, "(g)   (slow)", "(g)&emsp;(slow)")
sub(17, "(g)  ⇌  2NO", "(g) ⇌ 2NO")
sub(17, "(g)        ΔH", "(g)&emsp;&emsp;ΔH")

# ---- Q19: charge on HCO3- in the denominator: spaces + en dash -> minus ----
sub(19, '<span class="stk post"><span>  –</span><span>3</span></span>',
    '<span class="stk post"><span>−</span><span>3</span></span>')
sub(19, "([H2CO3])/([HCO –3)] ratio", "[H2CO3]/[HCO3−] ratio", field="content_text")

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count('<div class="fig">')
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
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if "<p class=\"qstem\"><i>(BE" in r["content_html"] or "\t" in r["content_html"]:
        bad.append("Q%d: leftover tab/para" % qn)
assert not bad, "\n".join(bad)
assert len(PLAN) == 8, len(PLAN)
assert sorted(Q) == list(range(1, 31))

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1),
    encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
