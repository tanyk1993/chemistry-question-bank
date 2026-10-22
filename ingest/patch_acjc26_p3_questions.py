"""ACJC 2026 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_acjc26_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `acjc26_p3_prep` (strips the blue/red answer rows out of a COPY of the
school's solutions docx) -> `extract_parts` (table shape; crops stubbed because
the user snips every figure; school ACJC, level H2, paper P3, year 2026; run
against the redacted Word PDF) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 corrections.GLYPH_PICTURES (extractor side, not here): Q2(c)'s equilibrium arrow
   is a drawn harpoon pair; it is typed as "⇌".
 acjc26_p3_prep (not here): one stray Word Ink stroke in Q1(d)(ii) is removed (it
   would have become a phantom figure); the answer-only drawings go with their rows.
 Q1  (e): Fig. 1.2 is ONE picture (the extractor found 2 placeholders plus typed
       "2" / "beta-keto ester" lines that belong to the picture) and Fig. 1.3 is
       ONE picture (3 placeholders plus typed "step 1" / "step 2" captions).
     (f): the three structures (propanone, methanol, enolate ion) are ONE picture.
     (d)(ii): a soft <br> becomes a space.
 Q3  (a)(iii): the mark sat in a centred, space-padded paragraph of its own.
     (b): Table 3.1 rebuilt (the extractor mis-nests <p> across its cells).
 Q4  (a): Fig. 4.1 (apparatus) and Fig. 4.2 (graph) are two pictures; one
       placeholder was extracted -> a second one, asset slot a2, and a typed
       "Fig. 4.1" caption. "equation 4.1" gets class eqn. E-standard sign.
 Q5  the question total is not printed in this file: 20 = the sum of the parts.
 generic: whitespace inside inline tags, runs of spaces, en/figure dash and hyphen
     inside <sup> and as a minus -> U+2212, a soft <br> -> space, "<sup>o</sup>C"
     -> degree sign.
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
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, old, new, count=1, rx=False):
    """Apply one change to content_html AND content_text, each asserted."""
    sub(qn, old, new, count=count, rx=rx)
    sub(qn, old, new, field="content_text", count=count, rx=rx)


P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"
FIG = '<div class="fig">figure</div>'

# ======================================================================= Q1
# (e) Fig. 1.2 is one picture; the typed "2" and "beta-keto ester" lines belong to it
sub(1, FIG + '\n<p>2</p>\n' + FIG + r'\n<p>\s+beta-keto ester</p>\n<p class="c"><b>Fig 1.2</b></p>',
    FIG + '\n<p class="c"><b>Fig 1.2</b></p>', rx=True)
sub(1, r"strong base\.\n\s+2\s+\n\s+beta-keto ester\nFig 1\.2\n",
    "strong base.\nFig 1.2\n", field="content_text", rx=True)
# (e) Fig. 1.3 (steps 1 and 2) is one picture; "step 1" / "step 2" are inside it
sub(1, FIG + '\n<p class="c">step 1</p>\n' + FIG + '\n<p class="c">step 2</p>\n' + FIG
    + '\n<p class="c"><b>Fig. 1.3</b></p>',
    FIG + '\n<p class="c"><b>Fig. 1.3</b></p>')
sub(1, r"Fig\. 1\.3\. \nstep 1\s+step 2\s+\nFig\. 1\.3 ", "Fig. 1.3. \nFig. 1.3 ",
    field="content_text", rx=True)
# (f) propanone / methanol / enolate ion with their captions: one picture
sub(1, '<div class="qpart"><span class="pl">(f)</span> The carbon‒oxygen bond lengths in propanone, '
    'methanol and the enolate ion shown in Fig. 1.2 are analysed. \n' + FIG + '\n' + FIG + '</div>',
    '<div class="qpart"><span class="pl">(f)</span> The carbon‒oxygen bond lengths in propanone, '
    'methanol and the enolate ion shown in Fig. 1.2 are analysed. \n' + FIG + '</div>')

# ======================================================================= Q3
# (a)(iii): the mark follows the caption in a centred paragraph padded with spaces
sub(3, r'<p class="c">3-methylbutanone\s+</p>\n<p class="c">\s+<span class="mk">\[2\]</span></p></div>',
    '<p class="c">3-methylbutanone</p>\n<p><span class="mk">[2]</span></p></div>', rx=True)
# (b): Table 3.1 rebuilt
sub(3, r'<table class="qt"><tr><td>test</td>.*?</table></p>',
    '<table class="qt">'
    '<tr><td>test</td><td>reagents and conditions</td><td>organic compounds formed</td><td>other information</td></tr>'
    '<tr><td>1</td><td>excess H<sub>2</sub>/Ni</td><td><b>B</b>, C<sub>12</sub>H<sub>24</sub>O<sub>2</sub></td>'
    '<td><b>B</b> contains one chiral centre.</td></tr>'
    '<tr><td>2</td><td>excess Br<sub>2</sub>(aq) in absence of ultra-violet light</td>'
    '<td>C<sub>12</sub>H<sub>22</sub>O<sub>4</sub>Br<sub>2</sub></td><td></td></tr>'
    '<tr><td>3</td><td>HCl(aq), heat</td>'
    '<td><b>C</b>, C<sub>2</sub>H<sub>4</sub>O<sub>2</sub><br><b>D</b>, C<sub>10</sub>H<sub>18</sub>O</td>'
    '<td><b>D</b> also reacts in test 4 to form <b>E</b>, <b>F</b>, and CH<sub>3</sub>COCH<sub>3</sub>.</td></tr>'
    '<tr><td>4</td><td>excess hot concentrated acidified KMnO<sub>4</sub></td>'
    '<td><b>C</b>, C<sub>2</sub>H<sub>4</sub>O<sub>2</sub><br><b>E</b>, C<sub>2</sub>H<sub>2</sub>O<sub>4</sub><br>'
    '<b>F</b>, C<sub>5</sub>H<sub>8</sub>O<sub>3</sub><br>and CH<sub>3</sub>COCH<sub>3</sub></td>'
    '<td><b>C</b>, <b>E</b> and <b>F</b> effervesce with Na<sub>2</sub>CO<sub>3</sub>(aq).<br>'
    '<b>E</b> further oxidises to form CO<sub>2</sub>.<br>'
    '<b>F</b> forms a yellow precipitate with alkaline aqueous iodine but does <b>not</b> react with '
    'Fehling’s reagent.</td></tr></table>', rx=True)
sub(3, r"testreagents and conditionsorganic compounds formedother information1excess H2/Ni.*?"
    r"does not react with Fehling’s reagent\.\n",
    "test reagents and conditions organic compounds formed other information "
    "1 excess H2/Ni B, C12H24O2 B contains one chiral centre. "
    "2 excess Br2(aq) in absence of ultra-violet light C12H22O4Br2 "
    "3 HCl(aq), heat C, C2H4O2 D, C10H18O D also reacts in test 4 to form E, F, and CH3COCH3. "
    "4 excess hot concentrated acidified KMnO4 C, C2H4O2 E, C2H2O4 F, C5H8O3 and CH3COCH3 "
    "C, E and F effervesce with Na2CO3(aq). E further oxidises to form CO2. "
    "F forms a yellow precipitate with alkaline aqueous iodine but does not react with Fehling’s reagent.\n",
    field="content_text", rx=True)

# ======================================================================= Q4
# (a): Fig. 4.1 (apparatus) and Fig. 4.2 (graph) are two pictures
sub(4, '</ul>\n' + FIG + '\n<p class="c"><b>Fig. 4.2</b></p>',
    '</ul>\n' + FIG + '\n<p class="c"><b>Fig. 4.1</b></p>\n' + FIG + '\n<p class="c"><b>Fig. 4.2</b></p>')
sub(4, "was obtained.\n\nFig. 4.2 (a)(i)", "was obtained.\nFig. 4.1\nFig. 4.2 (a)(i)", field="content_text")
# "equation N.N" lines are hand-aligned with runs of spaces; EQN_LINE_RE only matches an integer
sub(4, '<p>equation 4.1 ', '<p class="eqn">equation 4.1 ')
# the standard-state sign (house markup: sup.pl-sym)
sub(4, "<i>E</i><sup>o</sup> values", '<i>E</i><sup class="pl-sym">⦵</sup> values')
sub(4, "Eo values", "E⦵ values", field="content_text")

# ======================================================================= Q5
# the paper prints no question total for Q5 in this file

# ------------------------------------------------ user rulings (2026-10-21): grammar
both(4, "ions exists as", "ions exist as")
both(4, "ions and magnesium ions, Suggest why", "ions and magnesium ions, suggest why")
both(5, "ions forms many", "ions form many")
sub(1, "and by-product <b>T</b> are obtained.", "and by-product <b>T</b> is obtained.")
sub(1, "and by-product T are obtained.", "and by-product T is obtained.", field="content_text")
sub(4, "</sup>and Cr<sub>2</sub>", "</sup> and Cr<sub>2</sub>")
sub(4, "CrO42−and Cr2O72−", "CrO42− and Cr2O72−", field="content_text")

# ------------------------------------------------------------- degree Celsius
sub(2, "250 <sup>o</sup>C", "250 °C")
sub(2, "250 oC", "250 °C", field="content_text")
sub(4, "25 <sup>o</sup>C", "25 °C", count=3)
sub(4, "25 oC", "25 °C", field="content_text", count=3)

# ------------------------------------------------------------- soft <br>
# the <br> left outside a table cell are typed line wraps inside a sentence
for qn, old, new in ((1, "kJ mol<sup>−1</sup>. <br>Using", "kJ mol<sup>−1</sup>. Using"),
                     (4, "acidified solution of <br>0.02 mol", "acidified solution of 0.02 mol"),
                     (5, "initial pH of <br>0.10 mol", "initial pH of 0.10 mol"),
                     (5, "titrated against <br>0.15 mol", "titrated against 0.15 mol")):
    sub(qn, old, new)


# ---------------------------------------------------------------- generic tidy
def tidy(qn):
    s = Q[qn]["content_html"]
    n_ws = n_dash = n_td = n_stray = n_empty = n_exp = 0
    s, n_exp = re.subn(r"(?<=[A-Za-z0-9)])<sup>[ \t]+", "<sup>", s)

    def rep(m):
        nonlocal n_ws
        open_t, lead, body, trail, close_t = m.groups()
        if not lead and not trail:
            return m.group(0)
        n_ws += 1
        return (" " if lead else "") + open_t + body + close_t + (" " if trail else "")
    s = re.sub(r'(<(?:sup|sub|i|b|i class="el")>)([ \t]*)([^<]*?)([ \t]*)(</(?:sup|sub|i|b)>)', rep, s)
    s, n_empty = re.subn(r"<(sub|sup|i)></\1>", "", s)

    def dash(m):
        nonlocal n_dash
        if re.search(r"[-–‒]", m.group(0)):
            n_dash += 1
        return re.sub(r"[-–‒]", "−", m.group(0))
    s = re.sub(r"<sup>[^<]*</sup>", dash, s)

    def td(m):
        nonlocal n_td
        inner = m.group(2)
        o, c = len(P_OPEN.findall(inner)), inner.count(P_CLOSE)
        if o > c:
            n_td += o - c
            inner += P_CLOSE * (o - c)
        return m.group(1) + inner + "</td>"
    s = re.sub(r"(<td[^>]*>)(.*?)</td>", td, s, flags=re.S)
    out, depth, i = [], 0, 0
    for m in re.finditer(r"<p(?:\s[^>]*)?>|</p>", s):
        out.append(s[i:m.start()])
        if m.group(0) == P_CLOSE:
            if depth == 0:
                n_stray += 1
            else:
                depth -= 1
                out.append(P_CLOSE)
        else:
            depth += 1
            out.append(m.group(0))
        i = m.end()
    out.append(s[i:])
    s = "".join(out)
    s, n_tr = re.subn(r"[ \t]+</p>", "</p>", s)
    lines = s.split("\n")
    n_run = 0
    for k, ln in enumerate(lines):
        if ln.startswith('<p class="eqn">'):
            continue
        new = re.sub(r"(?<=\S)[ \t]{3,}(?=\S)", " ", ln)
        if new != ln:
            n_run += 1
            lines[k] = new
    s = "\n".join(lines)
    Q[qn]["content_html"] = s
    LOG.append("Q%d tidy: %d exponent-leading spaces, %d spaces moved out of inline tags, %d empty sub/sup, "
               "%d dash->U+2212 in sup, %d trailing spaces before </p>, %d td <p> closed, %d stray </p>, "
               "%d lines with a space run collapsed"
               % (qn, n_exp, n_ws, n_empty, n_dash, n_tr, n_td, n_stray, n_run))


for qn in sorted(Q):
    tidy(qn)

# the same minus-sign / space-run normalisation for the search text
for qn in sorted(Q):
    t = Q[qn]["content_text"]
    n = 0
    for pat in (r"(?<=dm)[-–‒](?=\d)", r"(?<=mol)[-–‒](?=\d)", r"(?<= s)[-–‒](?=1)", r"(?<=10)[-–‒](?=\d)",
                r"(?<=OH)[-–‒](?=\s|$)", r"(?<=\d)[-–‒](?=\d{3,})", r"(?<=\s)‒(?=\d)",
                r"(?<=N3)[-–‒](?=[\s,.])"):
        t, k = re.subn(pat, "−", t)
        n += k
    t = re.sub(r"(?<=\S)[ \t]{3,}(?=\S)", " ", t)
    Q[qn]["content_text"] = t
    LOG.append("Q%d text: %d minus signs normalised" % (qn, n))


# ------------------------------------------------ marks the extractor missed
for qn, tot in ((5, 20),):
    assert Q[qn]["marks"] in (None, tot), (qn, Q[qn]["marks"])
    Q[qn]["marks"] = tot
    LOG.append("Q%d marks = %d (sum of the parts; no [Total] line in the file)" % (qn, tot))


# ---------------------------------------------------------- the asset plan
def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


def drop(qn, slot):
    x = get(qn, slot)
    PLAN.remove(x)
    LOG.append("asset plan: Q%d slot %s dropped (merged into the previous picture)" % (qn, slot))


# Q1(e): Fig. 1.2 = e, Fig. 1.3 = e2 (was e2..e5); Q1(f): one picture (was f, f2)
for slot in ("e3", "e4", "e5", "f2"):
    drop(1, slot)
# Q4(a): the graph (Fig. 4.2) is its own picture
a = get(4, "a")
a2 = dict(a)
a2.update({"slot": "a2", "storage_path": a["storage_path"].replace("_a_", "_a2_")})
PLAN.insert(PLAN.index(a) + 1, a2)
LOG.append("asset plan: Q4 added slot a2 (%s)" % a2["storage_path"])

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 11, len(PLAN)

# structural checks
for qn in Q:
    h = Q[qn]["content_html"]
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<td") == h.count("</td>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "[Total" not in h, "Q%d still has a [Total] line" % qn
    n_mk = len(re.findall(r'<span class="mk">', h))
    n_parts = len([p for p in Q[qn]["parts"] if p["marks"]])
    assert n_mk == n_parts, "Q%d: %d mark badges vs %d parts with marks" % (qn, n_mk, n_parts)
assert [Q[k]["marks"] for k in sorted(Q)] == [21, 16, 18, 20, 20]
for qn in Q:
    assert sum(p["marks"] or 0 for p in Q[qn]["parts"]) == Q[qn]["marks"], qn

# section_label is NULL for structured papers (HANDOFF SS23)
for qn in Q:
    Q[qn]["section"] = None

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets" % (len(Q), len(PLAN)))
