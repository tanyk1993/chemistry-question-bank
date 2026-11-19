"""RVHS 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.rvhs26_p1_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school RVHS --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_rvhs26_p1_questions <out> <build_dir>

Table-shape paper (30 tables, one per question), school .doc converted with
LibreOffice. The user snips every stem figure (Q13, Q19, Q20, Q25 stem, Q29);
Claude snips the three all-diagram option sets (Q6, Q25, Q27:
crop_rvhs26_p1_options.py). Every edit asserts its match count: a silent miss is
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
FIGURE_DASH = "‒"
FIG = '<div class="fig">figure</div>'


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


# ------------------------------------------------ 0. table search text -----
# (done FIRST, from the extractor's own tables, before the markup is touched)
for qn in (2, 16):
    for old, new in table_text(Q[qn]["content_html"]):
        sub(qn, re.escape(old), new.replace("\\", "\\\\"), field="content_text", rx=True)

# ------------------------------------------------ 1. figure plan ----------
# Q13: the "gaseous reactants <=> gaseous products (kf, kb)" line and the reaction
#      profile are ONE diagram in print -> one combined snip (stem1).
# Q16: the only "figure" is the arrow in the options-table header; it is rebuilt
#      as a CSS arrow (corrections.MCQ_FIXUPS), so its asset is dropped.
DROP = {13: ["stem2"], 16: ["stem1"]}
for qn, slots in DROP.items():
    gone = [p for p in PLAN if p["question"] == qn and p["slot"] in slots]
    assert len(gone) == len(slots), (qn, gone)
    PLAN = [p for p in PLAN if p not in gone]
    LOG.append("Q%d asset plan: dropped %s" % (qn, slots))
sub(13, FIG + "\n" + FIG, FIG)

# ------------------------------------------------ 2. per-question edits ----
# Q5 / Q27: the three criteria are a bulleted list (house style: ul.stmts)
for qn, lead in ((5, "Given that this molecule"), (27, "A material made from polymer <b>Q</b>:")):
    m = re.search(r'(<p class="qstem">%s</p>\n)((?:<p class="qstem">[^\n]*?</p>\n){3})' % re.escape(lead),
                  Q[qn]["content_html"])
    assert m, qn
    items = re.findall(r'<p class="qstem">([^\n]*?)</p>', m.group(2))
    assert len(items) == 3, items
    sub(qn, re.escape(m.group(2)),
        '<ul class="stmts">' + "".join("<li>%s</li>" % t.strip() for t in items) + "</ul>\n",
        rx=True)

# Q7: the school typed U+2012 (figure dash) for the charge of SH- and HSO4-
assert Q[7]["content_html"].count(FIGURE_DASH) == 2
sub(7, FIGURE_DASH, MINUS, count=2)
for k, v in Q[7]["options"].items():
    Q[7]["options"][k] = v.replace(FIGURE_DASH, MINUS)
Q[7]["content_text"] = Q[7]["content_text"].replace(FIGURE_DASH, MINUS)
LOG.append("Q7 options/content_text: U+2012 -> U+2212")

# Q15: K_p typed as two italic runs
sub(15, "<i>K</i><i><sub>p</sub></i>", "<i>K</i><sub>p</sub>")

# Q17: a space typed inside an italic run after Cl
sub(17, '<i class="el">l</i><i> </i>decreases', '<i class="el">l</i> decreases')

# Q18: the space belongs before the italic K
sub(18, "The<i> K</i><sub>a</sub>", "The <i>K</i><sub>a</sub>")

# Q30: degree sign typed as Symbol omicron, set as a superscript
sub(30, "melting point / <sup>°</sup>C", "melting point / °C")

# ------------------------------------------------ 2b. school slips --------
# Fixed on the user's ruling (2026-11-19): every slip flagged at ingest is corrected.
SLIPS = [
    (4, "higher than that hydrogen chloride", "higher than that of hydrogen chloride"),
    (7, "Bronsted-Lowry", "Br\u00f8nsted-Lowry"),
    (14, "For the gaseous reaction", "For the reaction"),
    (15, "Equal amounts of SO<sub>2</sub> and O<sub>2</sub> gas was introduced",
         "Equal amounts of SO<sub>2</sub> and O<sub>2</sub> gases were introduced"),
    (24, "Equal amount of four", "Equal amounts of four"),
]
for qn, old, new in SLIPS:
    sub(qn, old, new)
    plain = lambda t: re.sub(r"<[^>]+>", "", t)
    o, n = plain(old), plain(new)
    assert Q[qn]["content_text"].count(o) == 1, (qn, o)
    Q[qn]["content_text"] = Q[qn]["content_text"].replace(o, n)
    for k, v in Q[qn]["options"].items():
        Q[qn]["options"][k] = v.replace(o, n)
    LOG.append("Q%d slip fixed in text/options: %r -> %r" % (qn, o, n))

# ------------------------------------------------ 3. global tidy ----------
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
        if FIGURE_DASH in r[key]:
            bad.append("Q%d: U+2012 left in %s" % (qn, key))
        if re.search(r" {2,}", r[key]) or "\t" in r[key]:
            bad.append("Q%d: space run / tab left in %s" % (qn, key))
    for k, v in r["options"].items():
        if FIGURE_DASH in v or re.search("[-]", v):
            bad.append("Q%d option %s: stray glyph" % (qn, k))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if re.search(r"<sup>\s*[o°]\s*</sup>|<(sub|sup|i|b)>\s*</\1>", r["content_html"]):
        bad.append("Q%d: superscript degree or empty inline element left" % qn)
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
