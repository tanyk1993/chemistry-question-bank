"""TMJC 2026 H2 P1 (9476/01, 30 MCQ) questions: patch the extractor output
(declared, asserted) and write the final questions.json / asset_plan.json for
gen_question_migration.

usage (from the repo root):
  python3 -m ingest.tmjc26_p1_prep <unz> <unz_prep>
  python3 -m ingest.redact_inline_answers_pdf word.pdf q.pdf 0xff,0x8000,0xb050
  python3 -m ingest.extract_questions <unz_prep> q.pdf <out> \
      --school TMJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_tmjc26_p1_questions <out> <build_dir>

Shape: table family (one table per question after tmjc26_p1_prep; the school
typed the suggested answers into the same tables: blue 0000FF answers, green
explanations). Every edit asserts its match count.

FIGURES. Claude cuts all 42 diagram assets at the user's request
(crop_tmjc26_p1_figures.py); the asset plan below is the snip list.
Equilibrium arrows that the docx holds as little Equation objects (Q11, Q12,
Q14) are typed as the equilibrium sign.

NOT edited (left as the school set them): Q23 "Reaction 1 / Reaction 2" bullets
are kept as a bullet list; the question text of every question otherwise stands.
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
GAP = '<span class="gap"></span>'
MINUS = "−"
ARROW = "⇌"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def set_plan(qn, entries):
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...] in the
    ordinal order block < option < inline; ordinal = position in `entries`."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "TMJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


def plain(h):
    return re.sub(r"<[^>]+>", "", h)


def listify(qn, after, n, tag="ol", number_text=False):
    """The `n` qstem paragraphs after the paragraph containing `after` become one
    <ol|ul class="stmts">. A typed leading "N<tab>" is dropped. With number_text
    the item numbers are added to content_text (the list numerals are CSS)."""
    s = Q[qn]["content_html"]
    assert s.count(after) == 1, (qn, after)
    j = s.index("</p>", s.index(after)) + 4
    rest, pos, items = s[j:], 0, []
    for _ in range(n):
        m = re.match(r'\n?<p class="qstem(?: eqn)?">(.*?)</p>', rest[pos:], re.S)
        assert m, "Q%d: expected %d paragraphs after %r" % (qn, n, after)
        items.append(re.sub(r"^\d\t\s*", "", m.group(1)).strip())
        pos += m.end()
    html = "\n<%s class=\"stmts\">%s</%s>" % (
        tag, "".join("<li>%s</li>" % t for t in items), tag)
    Q[qn]["content_html"] = s[:j] + html + rest[pos:]
    LOG.append("Q%d: %d paragraphs -> %s.stmts" % (qn, n, tag))
    if number_text:
        txt = Q[qn]["content_text"]
        for i, t in enumerate(items, 1):
            p = " ".join(plain(t).split()[:4])      # the item's first words
            assert txt.count(p) >= 1, (qn, p)
            txt = txt.replace(p, "%d %s" % (i, p), 1)
        Q[qn]["content_text"] = txt
        LOG.append("Q%d: item numbers added to content_text" % qn)


# ---- Q2: bullets, then numbered items ----------------------------------------------
listify(2, "Substance X has the following properties.", 3, "ul")
listify(2, "Which of the following could be substance X?", 4, "ol", number_text=True)

# ---- Q4: search text ran the header cells together ----------------------------------
sub(4, "highest | | | | lowest | |", "highest ... lowest", field="content_text")

# ---- Q5: four graphs = the option grid (A-D), one placeholder -------------------------
h = Q[5]["content_html"]
assert h.count(FIG) == 2
Q[5]["content_html"] = h.replace(FIG + "\n" + FIG, FIG)
assert Q[5]["content_html"].count(FIG) == 1
Q[5]["options"] = {L: "[structure %s]" % L for L in "ABCD"}
set_plan(5, [("option", L) for L in "ABCD"])

# ---- Q7: the answer rows were read as a plain table: rebuild as the options table ----
rows = [("A", "0", "1"), ("B", "1", "0"), ("C", "1", "1"), ("D", "2", "0")]
sub(7, r'<table class="qt"><tr><td></td><td>order with <br>respect to \[NO<sub>2</sub>\]</td>'
       r'<td>order with <br>respect to \[SO<sub>2</sub>\]</td></tr>.*?</table>',
    '<table class="opts-table"><tr><td class="ol"></td>'
    '<td>order with respect to [NO<sub>2</sub>]</td><td>order with respect to [SO<sub>2</sub>]</td></tr>'
    + "".join('<tr><td class="ol">%s</td><td>%s</td><td>%s</td></tr>' % r for r in rows)
    + "</table>", rx=True)
sub(7, "[NO2] / mol dm–3[SO2] / mol dm–3relative rate 0.0050.0051.00 0.0060.0061.44 0.0080.0061.92",
    "[NO2] / mol dm–3 | [SO2] / mol dm–3 | relative rate 0.005 | 0.005 | 1.00 "
    "0.006 | 0.006 | 1.44 0.008 | 0.006 | 1.92", field="content_text")
sub(7, "order with respect to [NO2]order with respect to [SO2] A01 B10 C11 D20",
    "order with respect to [NO2] | order with respect to [SO2] A 0 | 1 B 1 | 0 C 1 | 1 D 2 | 0",
    field="content_text")
Q[7]["options"] = {L: "%s | %s" % (a, b) for L, a, b in rows}
LOG.append("Q7 options -> 4 rows (A 0|1 B 1|0 C 1|1 D 2|0)")

# ---- Q8: signed values are minus signs; the unit exponent; the standard-state sign ----
sub(8, "mol⁻<sup>1</sup>", "mol<sup>" + MINUS + "1</sup>", count=5)
sub(8, "mol⁻1", "mol" + MINUS + "1", field="content_text", count=5)
Q[8]["options"] = {k: v.replace("mol⁻1", "mol" + MINUS + "1") for k, v in Q[8]["options"].items()}
sub(8, "∆<i>H</i><sup>⦵</sup>", '∆<i>H</i><sup class="pl-sym">⦵</sup>')
for f, rx in (("content_html", r"(?<=[>\s])[–-] ?(?=\d)"), ("content_text", r"(?<=[)\s])[–-] ?(?=\d)")):
    n = len(re.findall(rx, Q[8][f]))
    assert n == 5, (f, n)              # 3 table values + options A and B
    Q[8][f] = re.sub(rx, MINUS, Q[8][f])
    LOG.append("Q8 %s: %d negative values -> U+2212" % (f, n))
Q[8]["options"] = {k: re.sub(r"^[–-] ?(?=\d)", MINUS, v) for k, v in Q[8]["options"].items()}
assert Q[8]["options"]["A"].startswith(MINUS + "1369")
assert Q[8]["options"]["B"].startswith(MINUS + "403")

# ---- Q10: the three reactions are numbered statements ---------------------------------
listify(10, "Which reactions result in a decrease in the entropy of the system?", 3, "ol",
        number_text=True)

# ---- Q11: reversible arrow typed; the delta-H label is separated by a gap -------------
FRAC_EMPTY = '<span class="frac"><span class="fnum"></span><span class="fden"></span></span>'
sub(11, r'(\(g\)) ' + re.escape(FRAC_EMPTY) + r' (2H)', r"\1 " + ARROW + r" \2", rx=True)
sub(11, r"(2H<span class=\"sr\">I</span>\(g\))\t\t(∆<i>H</i> &gt; 0)", r"\1" + GAP + r"\2", rx=True)
sub(11, "H2(g) + I2(g) ()/() 2HI(g) ∆H > 0", "H2(g) + I2(g) " + ARROW + " 2HI(g) ∆H > 0",
    field="content_text")

# ---- Q12 / Q14: reversible arrows typed -----------------------------------------------
sub(12, r"\(l\) " + re.escape(FRAC_EMPTY) + r" H", "(l) " + ARROW + " H", rx=True)
sub(12, "H2O(l) ()/() H2PO4", "H2O(l) " + ARROW + " H2PO4", field="content_text")
sub(14, r"\(aq\) " + re.escape(FRAC_EMPTY) + r" HCO", "(aq) " + ARROW + " HCO", rx=True)
sub(14, r"\(s\) " + re.escape(FRAC_EMPTY) + r" Ca", "(s) " + ARROW + " Ca", rx=True)
sub(14, "(aq) ()/() HCO3", "(aq) " + ARROW + " HCO3", field="content_text")
sub(14, "CaCO3(s) ()/() Ca2+", "CaCO3(s) " + ARROW + " Ca2+", field="content_text")
# Q14: statement 1 had the charge/subscript pair glued to "shifts", and a trailing space
sub(14, '<span>2– </span><span>3</span></span>shifts the equilibrium position of  CaCO',
    '<span>2–</span><span>3</span></span> shifts the equilibrium position of CaCO')
listify(14, "Which statements are consequences of ocean acidification?", 3, "ol", number_text=True)

# ---- Q16, Q27: typed "1<tab>..." statements -> ol.stmts -------------------------------
listify(16, "exhibits both enantiomerism and cis-trans isomerism?", 3, "ol")
listify(27, "Which aqueous solutions are chemically stable when left exposed to air?", 3, "ol")
for qn in (16, 27):
    assert re.search(r"\b1 .*\b2 .*\b3 ", Q[qn]["content_text"]), qn

# ---- Q17: option text powers (search text only) -------------------------------------
# (kept as the extractor wrote them: 2^7 ... 2^10)

# ---- Q18, Q22: four option diagrams, nothing else to do -------------------------------
set_plan(18, [("option", L) for L in "ABCD"])
set_plan(22, [("option", L) for L in "ABCD"])
set_plan(1, [("option", L) for L in "ABCD"])

# ---- Q19: the starting material sits INSIDE the sentence: inline image -----------------
sub(19, '<p class="qstem">Which product can be formed when  </p>\n' + FIG + '\n'
        '<p class="qstem"> is heated with ethanolic sodium hydroxide?</p>',
    '<p class="qstem">Which product can be formed when <img data-asset="TMJC_H2_P1_Q19_stem1_2026.png" '
    'alt="" style="vertical-align:middle"> is heated with ethanolic sodium hydroxide?</p>')
assert Q[19]["content_html"].count(FIG) == 1
set_plan(19, [("option", L) for L in "ABCD"] + [("inline", "stem1")])

# ---- Q21: four stem schemes (blocks) + four option structures --------------------------
set_plan(21, [("block", "stem%d" % i) for i in (1, 2, 3, 4)] + [("option", L) for L in "ABCD"])

# ---- Q23: Reaction 1 / Reaction 2 are bullets in the paper ------------------------------
listify(23, "Consider the mechanisms of the following two reactions.", 2, "ul")

# ---- Q24: two stem schemes + ONE snip for the four numbered products (numerals inside) ----
h = Q[24]["content_html"]
m = re.search(r'<ol class="stmts">(?:<li><div class="fig">figure</div></li>){4}</ol>', h)
assert m, "Q24 numbered figure list not found"
Q[24]["content_html"] = h.replace(m.group(0), FIG)
assert Q[24]["content_html"].count(FIG) == 3
LOG.append("Q24: ol.stmts of 4 figures -> one combined figure (numerals inside the snip)")
set_plan(24, [("block", "stem%d" % i) for i in (1, 2, 3)])

# ---- Q25: the three tripeptide fragments are ONE snip; four option structures -----------
h = Q[25]["content_html"]
m = re.search(r'<table class="qt"><tr><td><div class="fig">figure</div></td>'
              r'<td><div class="fig">figure</div></td></tr><tr><td><div class="fig">figure</div></td>'
              r'</tr></table>', h)
assert m, "Q25 fragment table not found"
Q[25]["content_html"] = h.replace(m.group(0), FIG)
assert Q[25]["content_html"].count(FIG) == 2
sub(25, "it<b> </b>is partially", "it is partially")
set_plan(25, [("block", "stem1")] + [("option", L) for L in "ABCD"])

# ---- Q26: PVA segment (block) + poly(vinyl acetate) segment INLINE in option C ---------
h = Q[26]["content_html"]
assert h.count(FIG) == 2
Q[26]["content_html"] = h.replace(
    '<p class="qstem">Which statement about PVA is <b>incorrect</b>?</p>\n' + FIG + '\n',
    '<p class="qstem">Which statement about PVA is <b>incorrect</b>?</p>\n')
assert Q[26]["content_html"].count(FIG) == 1
sub(26, "It can be made from poly(vinyl acetate), .",
    'It can be made from poly(vinyl acetate), <img data-asset="TMJC_H2_P1_Q26_stem2_2026.png" alt="" '
    'style="vertical-align:middle">.')
Q[26]["options"]["C"] = "It can be made from poly(vinyl acetate)."
set_plan(26, [("block", "stem1"), ("inline", "stem2")])

# ---- the Data Booklet note: search text follows the house wording (style-guide addendum) ----
for qn in (4, 27):
    sub(qn, "Use of the Data Booklet is relevant to this question.",
        "Use of the data booklet is relevant to this question.", field="content_text")

# ---- Q26: option C's search text lost its structure ------------------------------------
sub(26, "poly(vinyl acetate), . D", "poly(vinyl acetate). D", field="content_text")

# ------------------------------------------------ global tidy -----------------------------
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789" + MINUS))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
SUPRX = re.compile("[" + "".join(SUP) + "]+")
SUBRX = re.compile("[" + "".join(SUB) + "]+")


def tidy(s, html):
    s = s.replace("‒", MINUS).replace("º", "°")
    s = re.sub(r"\b(mol|dm|s|cm)[-–](?=\d)", lambda m: m.group(1) + MINUS, s)
    s = re.sub(r"<sup>[-–](?=\d)", "<sup>" + MINUS, s)
    s = re.sub(r"<sup>(\d?)[-–]</sup>", lambda m: "<sup>" + m.group(1) + MINUS + "</sup>", s)
    s = re.sub(r"<span>(\d?)[-–]</span>", lambda m: "<span>" + m.group(1) + MINUS + "</span>", s)
    s = re.sub(r"(?<=[A-Za-z0-9)])[-–](?=[\s,.;:()|]|$)", MINUS, s) if not html else s
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
        s = re.sub(r"(?<=× 10)[-–](?=\d)", MINUS, s)       # 10-10 in the search text
        s = SUPRX.sub(lambda m: "".join(SUP[c] for c in m.group()), s)
        s = SUBRX.sub(lambda m: "".join(SUB[c] for c in m.group()), s)
    s = re.sub(r"(?<=\S) {2,}(?=\S)", " ", s)
    return s.strip() if not html else s


for qn, r in Q.items():
    for key, html in (("content_html", True), ("content_text", False)):
        r[key] = tidy(r[key], html)
    for k, v in r["options"].items():
        r["options"][k] = tidy(v, False)
    # a charge typed with an en dash inside a stacked pair (HPO4 2-, CO3 2-)
    r["content_html"] = re.sub(r"<span>(\d?)–</span>", lambda m: "<span>" + m.group(1) + MINUS + "</span>",
                               r["content_html"])
LOG.append("global: minus signs, degree sign, charge dashes, empty inline elements, stray spaces")

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count(FIG)
    ps = by_q.get(qn, [])
    want = sum(1 for p in ps if p["kind"] == "block") + (
        1 if any(p["kind"] == "option" for p in ps) else 0)
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    ords = [p["ordinal"] for p in sorted(ps, key=lambda p: p["ordinal"])]
    if ords != list(range(1, len(ords) + 1)):
        bad.append("Q%d: ordinals %r" % (qn, ords))
    rank = {"block": 0, "option": 1, "inline": 2}
    ks = [rank[p["kind"]] for p in sorted(ps, key=lambda p: p["ordinal"])]
    if ks != sorted(ks):
        bad.append("Q%d: plan order breaks block<option<inline" % qn)
    for p in ps:
        if p["kind"] == "inline" and 'data-asset="%s"' % p["storage_path"] not in r["content_html"]:
            bad.append("Q%d: inline %s is not in the html" % (qn, p["storage_path"]))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
        if re.search(r"[-]", r[key]):
            bad.append("Q%d: private-use glyph left in %s" % (qn, key))
        if "‒" in r[key] or "º" in r[key]:
            bad.append("Q%d: U+2012 / ordinal sign left in %s" % (qn, key))
        if "\t" in r[key]:
            bad.append("Q%d: tab left in %s" % (qn, key))
        if re.search(r"\b(mol|dm|s|cm)[-–]\d", r[key]):
            bad.append("Q%d: hyphen exponent left in %s" % (qn, key))
        if ARROW not in r[key] and re.search(r"\(\)/\(\)", r[key]):
            bad.append("Q%d: empty arrow left in %s" % (qn, key))
        if re.search(r"[₀-₉⁰-⁹]", r[key]):
            bad.append("Q%d: Unicode sub/superscript left in %s" % (qn, key))
    if 'class="fnum"></span>' in r["content_html"]:
        bad.append("Q%d: empty fraction left" % qn)
    if re.search(r"<(sub|sup|i|b)>\s*</\1>", r["content_html"]):
        bad.append("Q%d: empty inline element left" % qn)
    if re.search(r'<p class="qstem eqn">', r["content_html"]):
        bad.append("Q%d: typed statement left as a paragraph" % qn)
    if re.search(r"[  ]{3,}", plain(r["content_html"])):
        bad.append("Q%d: a run of 3+ spaces is left in content_html" % qn)
    if "<sup>⦵</sup>" in r["content_html"]:
        bad.append("Q%d: bare standard-state sign" % qn)
    if sorted(r["options"]) not in (list("ABCD"),):
        if qn != 7 or sorted(r["options"]) != list("ABCD"):
            bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
    if re.search(r"<sup>\s*[–-]", r["content_html"]):
        bad.append("Q%d: dash-minus left in a superscript" % qn)
assert not bad, "GATE:\n" + "\n".join(bad)
assert sorted(Q) == list(range(1, 31))
assert len(PLAN) == 42, len(PLAN)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
