"""JPJC 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.jpjc26_p1_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school JPJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_jpjc26_p1_questions <out> <build_dir>

Same family as JPJC 2024 H2 P1. Every edit asserts its
match count: a silent miss is how a fix ships unapplied.
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


def set_plan(qn, entries):
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...].
    Ordinals follow DOM order: stem figures first, then ONE option grid whose
    assets continue the sequence."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "JPJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- Q4: the graph is ONE figure (native chart + text-box axis labels) ------
set_plan(4, [("block", "stem1")])
sub(4, '<p class="c">Which of the following statements is correct?</p>',
    '<p class="qstem">Which of the following statements is correct?</p>')

# ---- Q9 (graphs), Q23 (stem structure + structures), Q28 (compound S + two-product rows)
set_plan(9, [("option", L) for L in "ABCD"])
set_plan(23, [("block", "stem1")] + [("option", L) for L in "ABCD"])
set_plan(28, [("block", "stem1")] + [("option", L) for L in "ABCD"])

# ---- single stem figures ----------------------------------------------------
for qn in (18, 19, 20, 24):
    set_plan(qn, [("block", "stem1")])
set_plan(30, [("block", "stem1"), ("block", "stem2")])   # T and W repeating units

# ---- Q7: the standard-state sign came through as a comma; tabs -> spaces ----
sub(7, "Δ<i>H</i><sup>,</sup>", "Δ<i>H</i><sup>⦵</sup>", count=2)
sub(7, r"\t+", "&emsp;&emsp;&emsp;", rx=True, count=2)
# ---- Q12: hand-aligned labels ------------------------------------------------
sub(12, r"\t+", "&emsp;&emsp;", rx=True, count=2)
# half-equations are equilibria: = -> reversible arrow (user, 2026-11-04)
sub(12, "e = Fe<sup>2+</sup>", "e \u21cc Fe<sup>2+</sup>")
sub(12, "2e = 2Br<sup>\u2013</sup>", "2e \u21cc 2Br<sup>\u2013</sup>")
sub(12, "+ e = Fe2+", "+ e \u21cc Fe2+", field="content_text")
sub(12, "+ 2e = 2Br\u2013", "+ 2e \u21cc 2Br\u2013", field="content_text")
# ---- Q8: stray subscript full stop -------------------------------------------
sub(8, 'NaC<i class="el">l</i><sub>.</sub>', 'NaC<i class="el">l</i>.')
# ---- Q25: hand-typed bullets -> ul.stmts --------------------------------------
sub(25, '<p class="qstem">70% of the reaction proceeds via an S<sub>N</sub>2 mechanism, producing enantiomer Y.</p>\n'
        '<p class="qstem">30% of the reaction proceeds via an S<sub>N</sub>1 mechanism.</p>',
    '<ul class="stmts"><li>70% of the reaction proceeds via an S<sub>N</sub>2 mechanism, producing enantiomer Y.</li>'
    '<li>30% of the reaction proceeds via an S<sub>N</sub>1 mechanism.</li></ul>')
# ---- Q29: runs of spaces between fragments -----------------------------------
sub(29, r"[ ]{5}", "&emsp;&emsp;", rx=True, count=4)

# ---- numbered statements: [blank | N | text] rows -> ol.stmts (house style) -
STM = re.compile(r'<table class="qt">((?:<tr><td></td><td>\d+</td><td>.*?</td></tr>)+)</table>', re.S)
ROW = re.compile(r'<tr><td></td><td>(\d+)</td><td>(.*?)</td></tr>', re.S)
for qn, r in sorted(Q.items()):
    def conv(m):
        rows = ROW.findall(m.group(1))
        if [int(n) for n, _t in rows] != list(range(1, len(rows) + 1)):
            return m.group(0)
        return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % t.strip() for _n, t in rows)
    new, n = STM.subn(conv, r["content_html"])
    if n and new != r["content_html"]:
        r["content_html"] = new
        LOG.append("Q%d statements table -> ol.stmts" % qn)

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
    if "Commented" in r["content_text"] or "LHS(" in r["content_text"]:
        bad.append("Q%d: Word comment text leaked" % qn)
assert not bad, "\n".join(bad)
assert len(PLAN) == 21, len(PLAN)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1),
    encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
