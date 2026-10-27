"""CJC 2026 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_cjc26_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `cjc26_p2_prep` (COVER_END="Section A": merges split bold labels, types
auto-numbers, drops the cover) on the question-only docx -> `extract_parts`
(flow shape; --first-page 1; school CJC, level H2, paper P3, year 2026) ->
THIS script -> gen_parts_migration. The user snips every figure; the extractor's
own plan (42 assets: native Word shapes) is replaced by the 19 printed pictures.

Every `sub()` asserts its match count. What is patched, and why:
 Q1 (g)(iii): the figure (monomer A) is anchored before its lead-in; moved after
      "Monomer A has the following structure."  (f): a stray <br> inside a bold run.
 Q2 (b): soft <br> -> space; HSO4- uses U+2212.  (b)(ii): 4 placeholders for 3
      printed schemes (Steps 2, 3, 4); the user snipped all three as ONE image
      (slot bi, CJC_H2_P3_Q2_bi_2026.png) -> 1.  (c): a placeholder with no printed
      picture dropped.  Marks: 18 (the [Total] line sits inside 2(c)).
 Q3 intro: the titration curve is anchored before "A 25.0 cm3 ..."; moved after it.
 Q4 (b): 22 shape placeholders + typed "P:" / "S:" = ONE picture (the user snipped
      both orbital-box diagrams, labels included, as one image).  (f)(i): soft <br>.
      (f)(ii): the typed caption "4-ethylguaiacol" is inside the snip.
 Q5 (c)(ii): "BLANK PAGE" page furniture removed.
 generic: whitespace inside inline tags, runs of spaces, en/figure dash and hyphen
     inside <sup> and as a minus -> U+2212, a soft <br> -> space.
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
    sub(qn, old, new, count=count, rx=rx)
    sub(qn, old, new, field="content_text", count=count, rx=rx)


P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"
FIG = '<div class="fig">figure</div>'

# ======================================================================= Q1
# (f): a soft <br> in a bold run opens the paragraph with a blank line
sub(1, '<p><b><br>\t\t</b>Complete the following', '<p><b>\t\t</b>Complete the following')
# (g)(iii): monomer A's picture follows its lead-in line
sub(1, FIG + '\n<p>Monomer <b>A </b>has the following structure.</p>',
    '<p>Monomer <b>A </b>has the following structure.</p>\n' + FIG)

# ======================================================================= Q2
sub(2, "through<br>electrophilic", "through electrophilic")
sub(2, "throughelectrophilic", "through electrophilic", field="content_text")
# HSO4-: the minus is U+2212 (the stacked sup/sub markup is the house pattern)
sub(2, '<span class="stk post"><span>-</span><span>4</span></span>',
    '<span class="stk post"><span>\u2212</span><span>4</span></span>')
sub(2, "HSO-4", "HSO\u22124", field="content_text")
# (b)(ii): three printed schemes (Steps 2, 3, 4) = ONE user snip, four placeholders
sub(2, FIG * 1 + '\n' + FIG + '\n' + FIG + '\n' + FIG + '\n<p><b>\t\t\t\t\t\t\t',
    FIG + '\n<p><b>\t\t\t\t\t\t\t')
# (c): no printed picture under (c); the extractor planned one
sub(2, '[9]</span></p>\n' + FIG + '</div>', '[9]</span></p></div>')

# ======================================================================= Q3
# intro: the titration curve prints AFTER "A 25.0 cm3 ... shown below."
sub(3, FIG + '\n<p><b>\t\t</b>A 25.0 cm<sup>3</sup> sample of oxalic acid was titrated against 0.150 mol dm<sup>‒3</sup> '
    'potassium hydroxide. The resulting pH curve was plotted as shown below.</p>',
    '<p><b>\t\t</b>A 25.0 cm<sup>3</sup> sample of oxalic acid was titrated against 0.150 mol dm<sup>‒3</sup> '
    'potassium hydroxide. The resulting pH curve was plotted as shown below.</p>\n' + FIG)

# (f): the printed "Y" label sits outside the user's snip; typed back as a caption
sub(3, 'to form product <b>Y.</b>\n' + FIG, 'to form product <b>Y.</b>\n' + FIG + '\n<p class="c"><b>Product Y</b></p>')
sub(3, "to form product Y.", "to form product Y.\nProduct Y", field="content_text")

# ======================================================================= Q4
# (b): one picture for both orbital-box diagrams; typed "P:" / "S:" are inside it
sub(4, '(FIG)' if False else '(?:' + FIG + r'\n){11}<p>P:</p>\n(?:' + FIG + r'\n){11}<p>S: <span class="mk">\[2\]</span></p></div>',
    FIG + '\n<p><span class="mk">[2]</span></p></div>', rx=True)
sub(4, "lower than that of phosphorus.\n\nP:\n\nS: [2]", "lower than that of phosphorus. [2]", field="content_text")
# (f)(i): soft <br> typed inside a sentence
sub(4, "the flask was <br>110 atm", "the flask was 110 atm")
# (f)(ii): the typed name sits inside the user's snip
sub(4, FIG + '\n<p>     \t\t\t4-ethylguaiacol</p>', FIG)
sub(4, "below.\n\n     \t\t\t4-ethylguaiacol\nSuggest", "below.\nSuggest", field="content_text")

# ======================================================================= Q5
sub(5, '\n<p class="c"><br><b>BLANK PAGE</b></p></div>', '</div>')
sub(5, "[3]\nBLANK PAGE [Total: 20]", "[3]", field="content_text")

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
assert Q[2]["marks"] is None
assert sum(p["marks"] or 0 for p in Q[2]["parts"]) == 18
Q[2]["marks"] = 18
LOG.append("Q2 marks = 18 (the [Total: 18] line sits inside 2(c); parts sum to 18)")
for qn in Q:
    Q[qn]["content_text"] = re.sub(r"\s*\[Total: \d+\]\s*$", "", Q[qn]["content_text"])


# ---------------------------------------------------------- the asset plan
def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


def drop(qn, slot, why):
    PLAN.remove(get(qn, slot))
    LOG.append("asset plan: Q%d slot %s dropped (%s)" % (qn, slot, why))


drop(2, "bii2", "Steps 2-4 are ONE snip")
drop(2, "bii3", "Steps 2-4 are ONE snip")
drop(2, "bii4", "Steps 2-4 are ONE snip")
_x = get(2, "bii")
_x["slot"] = "bi"
_x["storage_path"] = "CJC_H2_P3_Q2_bi_2026.png"
LOG.append("asset plan: Q2 slot bii renamed bi (CJC_H2_P3_Q2_bi_2026.png, the user's combined snip)")
drop(2, "c", "no printed picture")
for k in range(2, 23):
    drop(4, "b%d" % k, "Q4(b) is ONE snip: b")

for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 17, len(PLAN)

for qn in Q:
    h = Q[qn]["content_html"]
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<td") == h.count("</td>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "[Total" not in h and "BLANK PAGE" not in h
    n_mk = len(re.findall(r'<span class="mk">', h))
    n_parts = len([p for p in Q[qn]["parts"] if p["marks"]])
    assert n_mk == n_parts, "Q%d: %d mark badges vs %d parts with marks" % (qn, n_mk, n_parts)
assert [Q[k]["marks"] for k in sorted(Q)] == [18, 18, 19, 20, 20]
for qn in Q:
    assert sum(p["marks"] or 0 for p in Q[qn]["parts"]) == Q[qn]["marks"], qn

for qn in Q:
    Q[qn]["section"] = None

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets" % (len(Q), len(PLAN)))
