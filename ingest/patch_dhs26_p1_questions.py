"""DHS 2026 H2 P1 (9476/01) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_question_migration.

usage:
  python3 -m ingest.dhs26_p1_prep <unz> <unz_q>        # question copy, answer key cut
  python3 -m ingest.extract_questions <unz_q> <word.pdf> <out> \
      --school DHS --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_dhs26_p1_questions <out> <build_dir>
  python3 -m ingest.gen_question_migration <build_dir> - <dest.sql> \
      --school DHS --year 2026 --paper 1 --level H2        # '-' = answer_key left NULL

Shape: table family, one Word table per question (30). Answers are NOT read at
this stage (answer_key stays NULL; the answers stage is separate).

FIGURES. The asset plan is the SNIP LIST. The user snips every figure by hand,
EXCEPT the questions whose four options are all diagrams (Q6, Q20, Q25, Q26,
Q27), cut for the user from the Word PDF (the extractor's own option crops are
fragmented on this paper). Q21's product table is built as a real table whose
eight structure cells are inline images (ASRJC 2026 P1 Q5 precedent). Q24 option
A (the SN1 equation) is typed markup (corrections.EQUATION_OPTIONS_AS_TEXT).
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
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...] in
    block < option < inline order; ordinal = position."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "DHS_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- every question: a space typed INSIDE a <sup>/<sub> (Fe<sup>3+ </sup>) ---------
SPACE_RX = r"<(sup|sub)>([^<]*?)[  ]+</\1>"
for qn, r in Q.items():
    h = r["content_html"]
    h2 = re.sub(SPACE_RX, r"<\1>\2</\1> ", h)
    if h2 != h:
        r["content_html"] = h2
        LOG.append("Q%d: space moved out of a sup/sub x%d"
                   % (qn, len(re.findall(SPACE_RX, h))))

# ---- Q6: a lone space in a <sup> before the degree sign; trailing spaces after the equation
sub(6, "–10<sup></sup> °C", "–10 °C")   # (the generic rule above leaves an empty <sup>)
sub(6, r"\)\s{3,}</p>", ")</p>", rx=True)

# ---- Q15: zero-width spaces typed inside the equation -------------------------------
for f in ("content_html", "content_text"):
    s = Q[15][f]
    n = s.count("​")
    assert n == 2, "Q15 %s: expected 2 ZWSP, got %d" % (f, n)
    Q[15][f] = s.replace("​", "")
    LOG.append("Q15 %s: %d zero-width spaces removed" % (f, n))

# ---- Q21: the product table, built as a table with 8 inline structure images -------
sub(21, FIG + "\n", "")
sub(21, "reaction 2  product", "reaction 2 product")      # content_text is already single-spaced
for L in "ABCD":
    sub(21, '<tr><td class="ol">%s</td><td></td>' % L,
        '<tr><td class="ol">%s</td><td><img data-asset="DHS_H2_P1_Q21_%s1_2026.png" alt=""></td>'
        % (L, L))
# the second (reaction 2) image cell: the empty <td></td> between the two mechanism cells
for L in "ABCD":
    s = Q[21]["content_html"]
    m = re.search(r'(<tr><td class="ol">%s</td><td><img [^>]+></td><td>[^<]+</td>)<td></td>' % L, s)
    assert m, "Q21 row %s: reaction-2 cell not found" % L
    Q[21]["content_html"] = s.replace(
        m.group(0), m.group(1) + '<td><img data-asset="DHS_H2_P1_Q21_%s2_2026.png" alt=""></td>' % L, 1)
    LOG.append("Q21 row %s: reaction-2 image cell" % L)
set_plan(21, [("inline", "%s%d" % (L, c)) for L in "ABCD" for c in (1, 2)])

# ---- Q22: an empty bold paragraph under the structure ---------------------------------
sub(22, r'<p class="qstem"><b>\s+</b></p>\n', "", rx=True)
# the "V" caption is part of the user's snip (2026-10-28): drop the typed caption
sub(22, '<p class="c"><b>V</b></p>\n', "")
sub(22, "anaesthetic. V One mole of V", "anaesthetic. One mole of V", field="content_text")

# ---- Q24: option A typed (no asset) ----------------------------------------------------
assert not [p for p in PLAN if p["question"] == 24], "Q24 should have no assets"

# ---- Q28: the two half-cell lines are one centred pair ---------------------------------
sub(28, r'<p class="qstem">\s+half-cell 2:\s+Fe', '<p class="c">half-cell 2: Fe', rx=True)

# ---- checks ------------------------------------------------------------------------------
bad = []
rank = {"block": 0, "option": 1, "inline": 2}
for qn in sorted(Q):
    ps = sorted([p for p in PLAN if p["question"] == qn], key=lambda p: p["ordinal"])
    ks = [rank[p["kind"]] for p in ps]
    if ks != sorted(ks):
        bad.append("Q%d: plan order breaks block<option<inline" % qn)
    if [p["ordinal"] for p in ps] != list(range(1, len(ps) + 1)):
        bad.append("Q%d: ordinals not 1..n" % qn)
    r = Q[qn]
    nblock = sum(1 for p in ps if p["kind"] == "block")
    nopt = sum(1 for p in ps if p["kind"] == "option")
    nph = r["content_html"].count(FIG)
    if nph != nblock + (1 if nopt else 0):
        bad.append("Q%d: %d placeholders for %d block + %d option assets" % (qn, nph, nblock, nopt))
    for p in ps:
        if p["kind"] == "inline" and 'data-asset="%s"' % p["storage_path"] not in r["content_html"]:
            bad.append("Q%d: inline %s is not in the html" % (qn, p["storage_path"]))
    if "​" in r["content_html"] or re.search(SPACE_RX, r["content_html"]):
        bad.append("Q%d: leftover ZWSP / sup-sub space" % qn)
assert not bad, "\n".join(bad)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d" % (len(Q), len(PLAN)))
for l in LOG:
    print("  " + l)
