"""MI 2026 H2 P3 (9729/03) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QP.docx -d unz
  python3 -m ingest.extract_parts unz QP.pdf out \
      --school MI --level H2 --paper P3 --year 2026 --last-page 24
  python3 -m ingest.patch_mi26_p3_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school MI --year 2026 --paper 3 --level H2

Shape: SEAB 4-column table shape; no prep script. `oxml.py` needed `w:ptab`
(absolute-position tab) handled like `w:tab`. Answers are NOT read at this stage.

Marks as ingested: Q1 18, Q2 17, Q3 25, Q4 20, Q5 20 = 100 (80 as sat: Section B
is "answer one"), the same convention as the other P3s. No DBQ flag (P3 rule).

FIGURES (user snips, 5, all block figures):
  Q2(b)     Fig. 2.1: 4-step mechanism
  Q2(c)     4-chlorobutanoic acid -> X -> tetrahydrofuran scheme
  Q4(d)     SN1 reaction scheme of 2-chloro-2-methylpropane
  Q5(f)(i)  Cope rearrangement scheme
  Q5(f)(ii) Claisen rearrangement scheme

DECLARED FIXES: Q2(a) table row 4 cross-cell <p> tags; Q3(b) "&lt;" in
content_text; Q5(e) bond hyphens (plain hyphen, ruling 2026-11-01); ASCII
hyphen charges in Q1(b) set to minus; en dashes -> minus (charges, exponents,
negative values).
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
LOG = []
MINUS = "−"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, old, new, **kw):
    sub(qn, old, new, "content_html", **kw)
    sub(qn, old, new, "content_text", **kw)


for r in Q.values():
    for f in ("content_html", "content_text"):
        r[f] = r[f].replace("​", "")

# ---- Q2: cross-cell <p> in test 4 row ------------------------------------------------
sub(2, "<p><b>N</b>, C<sub>5</sub>H<sub>6</sub>O<sub>5</sub></td><td><b>M</b> and <b>N</b> "
       "both effervesce on addition of Na<sub>2</sub>CO<sub>3</sub>(aq).</p>\n"
       "<p><b>N</b> forms a yellow precipitate with warm alkaline I<sub>2</sub>(aq).</td>",
    "<p><b>N</b>, C<sub>5</sub>H<sub>6</sub>O<sub>5</sub></p></td><td><b>M</b> and <b>N</b> "
    "both effervesce on addition of Na<sub>2</sub>CO<sub>3</sub>(aq).\n"
    "<p><b>N</b> forms a yellow precipitate with warm alkaline I<sub>2</sub>(aq).</p></td>")
sub(2, "</td></tr></table></p>\n<p>For each of the four tests", "</td></tr></table>\n<p>For each of the four tests")

# ---- Q3: entity in text --------------------------------------------------------------
sub(3, "ΔH &lt; 0", "ΔH < 0", "content_text")

# ---- Q5: bond hyphens -----------------------------------------------------------------
both(5, "HOOC–CH=CH–CH=CH–COOH", "HOOC-CH=CH-CH=CH-COOH", count=2) if False else None
h_n = Q[5]["content_html"].count("HOOC–CH=CH–CH=CH–COOH")
t_n = Q[5]["content_text"].count("HOOC–CH=CH–CH=CH–COOH")
assert h_n >= 1 and t_n >= 1, (h_n, t_n)
sub(5, "HOOC–CH=CH–CH=CH–COOH", "HOOC-CH=CH-CH=CH-COOH", "content_html", count=h_n)
sub(5, "HOOC–CH=CH–CH=CH–COOH", "HOOC-CH=CH-CH=CH-COOH", "content_text", count=t_n)

# ---- Q1(b): ASCII-hyphen charges -> minus ---------------------------------------------
Q[1]["content_html"] = Q[1]["content_html"].replace("<sup>-</sup>", "<sup>" + MINUS + "</sup>")

# ---- dashes (ruling 2026-11-01) --------------------------------------------------------
CONTEXT = []
for qn, r in Q.items():
    for f in ("content_html", "content_text"):
        for m in re.finditer("–", r[f]):
            CONTEXT.append("Q%d %s: %r" % (qn, f[8:], r[f][max(0, m.start() - 12): m.end() + 8]))
        r[f] = r[f].replace("–", MINUS)

PLAN = json.loads((SRC / "asset_plan.json").read_text())

bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count('<div class="fig">')
    nblock = sum(1 for p in PLAN if p["question"] == qn)
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d assets" % (qn, nph, nblock))
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: empty sup/sub or stray <p>" % qn)
    if "[Total:" in h:
        bad.append("Q%d: [Total] in html" % qn)
    if not r["content_text"].rstrip().endswith("[Total: %d]" % r["marks"]):
        bad.append("Q%d: text does not end with [Total]" % qn)
    if h.count("<div") != h.count("</div>"):
        bad.append("Q%d: unbalanced div" % qn)
    if h.count("<p") - h.count("<pl") != h.count("</p>"):
        bad.append("Q%d: unbalanced p" % qn)
    if sum(p["marks"] or 0 for p in r["parts"]) != r["marks"]:
        bad.append("Q%d: parts sum mismatch" % qn)
    if "–" in h or "–" in r["content_text"]:
        bad.append("Q%d: en dash left" % qn)
    if "&lt;" in r["content_text"]:
        bad.append("Q%d: entity in content_text" % qn)
assert [Q[k]["marks"] for k in sorted(Q)] == [18, 17, 25, 20, 20]
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d" % (len(Q), len(PLAN)))
for l in LOG:
    print("  " + l)
print("en dashes converted (review): %d" % len(CONTEXT))
