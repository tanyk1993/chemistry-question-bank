"""HCI 2024 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.nested_cell_prep <unz> <unz_prep>
  python3 -m ingest.extract_questions <unz_prep> <word.pdf> <out> \
      --school HCI --level H2 --paper P1 --year 2024 --no-crops
  python3 -m ingest.patch_hci_p1_questions <out> <build_dir>

Every edit asserts its match count: a silent miss is how a fix ships unapplied.
(Q13's typed axis-title duplicate is removed earlier, by corrections.MCQ_FIXUPS,
because it carries a stray CENTRE sentinel the extractor refuses to emit.)
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
    Ordinals follow DOM order (HANDOFF SS7): stem figures first, then ONE
    option grid whose assets continue the sequence."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "HCI_H2_P1_Q%d_%s_2024.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- Q4: two Word bullet paragraphs (w:numPr) came out as bare paragraphs ---
sub(4, '<p class="qstem">all carbon-oxygen bonds are of the same length</p>\n'
       '<p class="qstem">π electrons are delocalised throughout the structure</p>',
    '<ul class="stmts"><li>all carbon-oxygen bonds are of the same length</li>'
    '<li>π electrons are delocalised throughout the structure</li></ul>')

# ---- Q8: four graphs = four option snips (A-D); the typed letter rows go ----
# (the option grid supplies the letters; the graphs' own axis titles are inside
# the user's snips). Native Word shapes: nothing to crop reliably.
sub(8, r'<p class="qstem"><b>\s+A\s+B</b></p>\n<div class="fig">figure</div>\n'
       r'<p class="qstem"><b>\s+C\s+D</b></p>\n<div class="fig">figure</div>',
    '<div class="fig">figure</div>', rx=True)
Q[8]["options"] = {L: "[structure %s]" % L for L in "ABCD"}
set_plan(8, [("option", L) for L in "ABCD"])

# ---- Q12: 'sucrose [arrow over H+(aq)] glucose + fructose' = ONE snip -------
# The arrow is a picture sharing a paragraph with the typed words, so the
# extractor split the equation across three lines. The scheme is snipped whole
# and the typed words are removed from the markup (kept in the search text).
sub(12, r'<p class="c">sucrose\s*</p>\n(<div class="fig">figure</div>)\n'
        r'<p class="c">\s*glucose\s*\+\s*fructose</p>', r'\1', rx=True)

# ---- Q13: the y-axis title is a text-box shape, not a second picture -------
set_plan(13, [("block", "stem1")])

# ---- Q19: Z is a STEM figure printed under the options, not an option ------
sub(19, r'(<p class="qstem">Which statement regarding[^\n]*</p>\n)'
        r'<div class="fig">figure</div>\n(<table class="opts-table">.*?</table>)',
    r'\1\2\n<div class="fig">figure</div>', rx=True)
set_plan(19, [("block", "stem1")])

# ---- Q20: typed, not snipped ------------------------------------------------
# The four '+' charges are floating text boxes, and option A's '+' sits on the
# PREVIOUS PDF page from its formula, so the options cannot be snipped as the
# page prints them. Typed from the printed layout (charge above the carbon).
# D: the printed structure has a bond from the CH down to O-.
Q20_OPTS = {
    "A": "CH<sub>2</sub>(Br)−C<sup>+</sup>HCH<sub>3</sub>",
    "B": "C<sup>+</sup>H<sub>2</sub>−CH(Br)CH<sub>3</sub>",
    "C": "C<sup>+</sup>H<sub>2</sub>−CH(OH)CH<sub>3</sub>",
    "D": "CH<sub>2</sub>(Br)−CH(O<sup>−</sup>)CH<sub>3</sub>",
}
Q20_TXT = {
    "A": "CH2(Br)−C+HCH3",
    "B": "C+H2−CH(Br)CH3",
    "C": "C+H2−CH(OH)CH3",
    "D": "CH2(Br)−CH(O−)CH3",
}
STEM20 = ("What is the intermediate that leads to the major product in the "
          "reaction between propene and aqueous bromine?")
Q[20]["content_html"] = (
    '<p class="qstem">%s</p>\n<table class="opts-table">%s</table>' % (
        STEM20, "".join('<tr><td class="ol">%s</td><td>%s</td></tr>'
                        % (L, Q20_OPTS[L]) for L in "ABCD")))
Q[20]["options"] = dict(Q20_TXT)
Q[20]["content_text"] = STEM20 + " " + " ".join(
    "%s %s" % (L, Q20_TXT[L]) for L in "ABCD")
set_plan(20, [])
LOG.append("Q20 rebuilt as typed options")

# ---- Q25: hand-aligned X / Y / Z labels (5 spaces would collapse) ----------
sub(25, r'(<p class="qstem">[XYZ])\s{5}', r'\1&emsp;', count=3, rx=True)

# ---- wording fixes, ruled item by item by the user (2026-10-12) -------------
# Q28 statement 3: comma after "water"
for f in ("content_html", "content_text"):
    sub(28, "formed, when dissolved in water will give",
        "formed, when dissolved in water, will give", field=f)
# Q13 statement 3: "if the initial concentration"
for f in ("content_html", "content_text"):
    sub(13, "if initial concentration is", "if the initial concentration is",
        field=f)
# Q9: doubled "of"
sub(9, "dm<sup>–3</sup> of FeC<sub>2</sub>O<sub>4</sub>",
    "dm<sup>–3</sup> FeC<sub>2</sub>O<sub>4</sub>")
sub(9, "mol dm–3 of FeC2O4", "mol dm–3 FeC2O4", field="content_text")
# Q29: space before the unit
for f in ("content_html", "content_text"):
    sub(29, "+0.77V", "+0.77 V", field=f)

# ---- minus signs: ONE convention, the proper minus U+2212 (style-guide) ------
# Every en dash in this paper is a charge or an exponent (asserted below), so
# the swap cannot touch prose. Bond dashes in typed Q20 are already U+2212.
for qn, r in Q.items():
    h = r["content_html"]
    for m in re.finditer("–", h):
        before = h[:m.start()]
        in_sup = before.rfind("<sup>") > before.rfind("</sup>")
        in_stk = before.rfind('<span class="stk') > before.rfind("</span></span>")
        in_stk = in_stk or re.search(r"<span>[^<]*$", before) is not None
        assert in_sup or in_stk, "Q%d: en dash outside sup/stk: %r" % (
            qn, h[max(0, m.start() - 20):m.start() + 10])
    for f in ("content_html", "content_text"):
        n = r[f].count("–")
        if n:
            r[f] = r[f].replace("–", "−")
            LOG.append("Q%d %s: %d en dash -> minus" % (qn, f, n))
    assert "–" not in json.dumps(r["options"], ensure_ascii=False), qn

# ---------------------------------------------------------------- GATE -----
# placeholders in content_html == stem assets + (1 if any option asset)
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
