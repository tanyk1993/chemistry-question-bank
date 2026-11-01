"""HCI 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.nested_cell_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school HCI --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_hci26_p1_questions <out> <build_dir>

Same family as HCI 2024 H2 P1 (nested option tables). Every edit asserts its
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
                     "storage_path": "HCI_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- Q1: the user snipped structures I, II and III as ONE image ------------
# The typed I / II / III header row and the three figure cells go; the single
# snip replaces the whole table. (Typed numerals stay in content_text.)
sub(1, r'<table class="qt"><tr><td>I</td><td>II</td><td>III</td></tr>.*?</table>',
    '<div class="fig">figure</div>', rx=True)
set_plan(1, [("block", "stem1")])

# ---- Q3: ONE graph (the extractor found two shapes in it) ------------------
set_plan(3, [("block", "stem1")])
# empty superscripts inside the italic "pV / RT"
sub(3, '<i>pV</i><i><sup> </sup></i><i>/</i><i><sup> </sup></i><i>RT</i>',
    '<i>pV</i> / <i>RT</i>')

# ---- Q6: the E / F row is a column HEADING, not an option "E" -------------
sub(6, '<tr><td class="ol">E</td><td>F</td><td></td></tr>', "", count=1)
sub(6, '<table class="opts-table"><tr><td class="ol">A</td>',
    '<table class="opts-table"><tr><td class="ol"></td><td>E</td><td>F</td></tr>'
    '<tr><td class="ol">A</td>')
assert "E" in Q[6]["options"]
del Q[6]["options"]["E"]
sub(6, " E F", "", field="content_text")
LOG.append("Q6 options -> A-D with E/F column header")

# ---- Q7: four graphs = four option snips (A-D); one placeholder ------------
sub(7, '<div class="fig">figure</div>\n<div class="fig">figure</div>',
    '<div class="fig">figure</div>')
set_plan(7, [("option", L) for L in "ABCD"])

# ---- Q13, Q18, Q21, Q24: four option snips each (plan holds options only) --
for qn in (13, 18, 21, 24):
    assert Q[qn]["content_html"].count('<div class="fig">') == 1, qn
    set_plan(qn, [("option", L) for L in "ABCD"])

# ---- single stem figures ----------------------------------------------------
for qn in (15, 17, 20, 23, 25, 26, 28, 30):
    set_plan(qn, [("block", "stem1")])

# ---- Q25: caption padded with spaces ----------------------------------------
sub(25, '<p class="qstem">   fully protonated arginine                    </p>',
    '<p class="qstem">fully protonated arginine</p>')

# ---- hand-aligned labels (runs of spaces would collapse) --------------------
sub(12, r'\(aq\)\s{10,}reaction 1</p>', '(aq)&emsp;&emsp;&emsp;reaction 1</p>', rx=True)
sub(13, r'T\(aq\)\s{4,}∆', 'T(aq)&emsp;∆', rx=True)

# ---- numbered statements: [blank | N | text] rows -> ol.stmts (house style) -
STM = re.compile(r'<table class="qt">((?:<tr><td></td><td>\d+</td><td>.*?</td></tr>)+)</table>',
                 re.S)
ROW = re.compile(r'<tr><td></td><td>(\d+)</td><td>(.*?)</td></tr>', re.S)
for qn, r in sorted(Q.items()):
    def conv(m):
        rows = ROW.findall(m.group(1))
        if [int(n) for n, _t in rows] != list(range(1, len(rows) + 1)):
            return m.group(0)
        return '<ol class="stmts">%s</ol>' % "".join(
            "<li>%s</li>" % t.strip() for _n, t in rows)
    new, n = STM.subn(conv, r["content_html"])
    if n and new != r["content_html"]:
        r["content_html"] = new
        LOG.append("Q%d statements table -> ol.stmts" % qn)

# ---- Q8: the half-equation charges use the proper minus ---------------------
# Only SUPERSCRIPT / stacked-charge dashes are changed; prose dashes (Q20's
# step lists, Q27's chain ends) stay as the school typed them.
for qn, r in Q.items():
    h = r["content_html"]
    out, last = [], 0
    for m in re.finditer("–", h):
        before = h[:m.start()]
        in_sup = before.rfind("<sup>") > before.rfind("</sup>")
        in_stk = re.search(r'<span class="stk[^"]*"><span>[^<]*$', before) is not None \
            or re.search(r'<span class="stk[^"]*"><span>[^<]*</span><span>[^<]*$', before) is not None
        if in_sup or in_stk:
            out.append((m.start(), m.end()))
    if out:
        for a, b in reversed(out):
            h = h[:a] + "−" + h[b:]
        r["content_html"] = h
        LOG.append("Q%d content_html: %d charge dash -> minus" % (qn, len(out)))
        # the search text carries the same characters
        t = r["content_text"]
        if "–" in t and qn == 8:
            r["content_text"] = t.replace("–", "−")

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
assert len(PLAN) == 30, len(PLAN)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1),
    encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
