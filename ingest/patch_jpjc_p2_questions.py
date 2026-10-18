"""JPJC 2024 H2 P2 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_jpjc_p2_questions <extractor_out_dir> <build_dir>

Pipeline: `jpjc_p2_prep` (re-emit the one question table as
[qnum|letter|roman|content|marks]) -> `extract_parts` (crops stubbed: the user
snips every figure) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 generic (all questions)
   - whitespace sitting INSIDE <sup>/<sub>/<i>/<b> moved outside; empty
     <sub></sub>/<sup></sup> removed; a space at the START of a <sup> that
     follows a word removed; en dash INSIDE <sup> -> U+2212
   - every soft <br> typed to wrap a sentence becomes a space (12, asserted)
 lead-ins: five passages sit after a part's last mark but belong to the NEXT
   part(s) (the user's HCI P3 ruling: they stand as their own unlabelled block
   between the two parts): Q2(a)->(b), Q4(a)(ii)->(a)(iii), Q4(b)(i)->(b)(ii),
   Q5(a)(iii)->(a)(iv), Q6(a)(ii)->(a)(iii). Q2 and Q6's carry Fig. 2.1 and
   Fig. 6.1: their asset slots are renamed to the part they now sit before.
 Q1  particle column of Table 1.1 bold (as printed)
 Q2  mechanism boxes rebuilt as a well-formed table; "(c)(ii)" bold; Table 2.1
     header bold
 Q3  the Equation 1 scheme moves BELOW the paragraph that introduces it; bold
     compound letters / step numbers (the extractor ignores style-inherited bold);
     the typed "J   K" caption line is dropped (the user's snip carries the labels)
 Q4  bold D/E/F/S/x, "(a)(i), (a)(ii) and (a)(iii)", experiments 3 and 4
 Q5  bold cross-references; "&amp;" in the search text
 Q6  bold T, U, V; Table 6.1/6.2 headers and X, Y of Table 6.3 bold
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


P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"

# ============================================================ structural first
# (malformed or misplaced HTML as extracted; fix before the generic tidy)

# Q2(d): the two mechanism boxes. The extracted table is malformed (the <p> opened
# in cell 1 closes in cell 3, an empty spacer cell between, the mark and a stray
# </p> after it). Rebuilt as a clean two-cell table; the spacing runs become em spaces.
sub(2, r'<table class="qt"><tr><td>Mechanism 1\n.*?</table> <span class="mk">\[1\]</span></p></div>',
    '<table class="qt"><tr>'
    '<td><p class="c">Mechanism <b>1</b></p>'
    '<p>2NO ⇌ N<sub>2</sub>O<sub>2</sub>&emsp;&emsp;(fast)</p>'
    '<p>N<sub>2</sub>O<sub>2</sub> + O<sub>2</sub> → 2NO<sub>2</sub>&emsp;&emsp;(slow)</p></td>'
    '<td><p class="c">Mechanism <b>2</b></p>'
    '<p>NO + O<sub>2</sub> → NO<sub>2</sub> + O&emsp;&emsp;(slow)</p>'
    '<p>O + NO → NO<sub>2</sub>&emsp;&emsp;(fast)</p></td>'
    '</tr></table> <span class="mk">[1]</span></div>', rx=True)
sub(2, r"Mechanism 1\n2NO .*?\(fast\) \[1\]",
    "Mechanism 1\n2NO ⇌ N2O2 (fast)\nN2O2 + O2 → 2NO2 (slow)\nMechanism 2\nNO + O2 → NO2 + O (slow)\nO + NO → NO2 (fast) [1]",
    field="content_text", rx=True)

# Q3: Equation 1's scheme is printed BELOW its introducing paragraph; the extractor put it first
sub(3, r'^<div class="fig">figure</div>\n(<p>The Wolff-Kishner.*?</p>)\n',
    r'\1\n<div class="fig">figure</div>\n', rx=True)

# ------------------------------------------------ lead-ins between two parts
# A passage printed after a part's last mark that belongs to the NEXT part(s) closes the
# part first, then stands as its own unlabelled block (the user's HCI P3 ruling).
def eject(qn, nxt):
    s = Q[qn]["content_html"]
    pat = (r'(<span class="mk">\[\d\]</span>(?:</p>)?)\n((?:(?!<div class="qpart">).)+?)</div>\n'
           r'(<div class="qpart"><span class="pl">%s</span>)' % re.escape(nxt))
    ms = list(re.finditer(pat, s, flags=re.S))
    assert len(ms) == 1, "Q%d eject before %s: %d matches" % (qn, nxt, len(ms))
    Q[qn]["content_html"] = re.sub(pat, r"\1</div>\n\2\n\3", s, flags=re.S)
    LOG.append("Q%d: lead-in passage moved out of the previous part, before %s" % (qn, nxt))


eject(2, "(b)(i)")
eject(4, "(a)(iii)")
eject(4, "(b)(ii)")
eject(5, "(a)(iv)")
eject(6, "(a)(iii)")

# ------------------------------------------------------------- soft <br>
# every <br> in this paper is a typed line wrap inside a sentence
BR_EXPECT = {2: 2, 3: 1, 4: 2, 5: 1, 6: 6}
for qn in sorted(Q):
    n = len(re.findall(r"<br>", Q[qn]["content_html"]))
    assert n == BR_EXPECT.get(qn, 0), "Q%d <br> count %d" % (qn, n)
    Q[qn]["content_html"] = re.sub(r"[ \t]*<br>[ \t]*", " ", Q[qn]["content_html"])
    # a <br> that followed a mark/empty line leaves a double space or a space before the mark
    Q[qn]["content_html"] = Q[qn]["content_html"].replace("  <span class=\"mk\">", " <span class=\"mk\">")
    LOG.append("Q%d: %d soft <br> -> space" % (qn, n))
sub(2, "onFig. 2.1", "on Fig. 2.1", field="content_text")
sub(4, "answer,giving", "answer, giving", field="content_text")


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
        if "–" in m.group(0):
            n_dash += 1
        return m.group(0).replace("–", "−")
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
    Q[qn]["content_html"] = s
    LOG.append("Q%d tidy: %d exponent-leading spaces, %d spaces moved out of inline tags, %d empty sub/sup, "
               "%d en dash->U+2212 in sup, %d trailing spaces before </p>, %d td <p> closed, %d stray </p>"
               % (qn, n_exp, n_ws, n_empty, n_dash, n_tr, n_td, n_stray))


for qn in sorted(Q):
    tidy(qn)

# a run of spaces typed to separate words (Q5 stem, Q6(c)(i), Q6 Table 6.1 lead-in): one space
for old, new, qn in (("bicarbonate              (", "bicarbonate (", 5),
                     ("molar mass of                   267", "molar mass of 267", 6)):
    sub(qn, old, new)
    sub(qn, old, new, field="content_text")
# (the trailing spaces after "wavelength." are already gone from the html by the tidy above)
sub(6, "shorter wavelength.                                  \n", "shorter wavelength.\n", field="content_text")


# ---------------------------------------------------------------- bold (as printed)
def bold(qn, old, new, count=1, field="content_html"):
    sub(qn, old, new, count=count, field=field)


def bold_header_row(qn, first_text):
    """Bold every non-empty cell of the table row that opens with `first_text`."""
    s = Q[qn]["content_html"]
    pat = r'(<table class="qt"><tr>)((?:<td>%s).*?)(</tr>)' % re.escape(first_text)
    ms = list(re.finditer(pat, s, flags=re.S))
    assert len(ms) == 1, (qn, first_text, len(ms))

    def wrap(m):
        inner = re.sub(r"<td>(.+?)</td>", r"<td><b>\1</b></td>", m.group(2))
        return m.group(1) + inner + m.group(3)
    Q[qn]["content_html"] = re.sub(pat, wrap, s, flags=re.S)
    LOG.append("Q%d: header row %r bold" % (qn, first_text))


def bold_tokens(qn, region_end, letters, expect):
    """Bold single capital letters standing alone as a word, in the text before
    `region_end` (a unique string), never inside a tag."""
    s = Q[qn]["content_html"]
    cut = s.index(region_end)
    head, tail = s[:cut], s[cut:]
    counts = {k: 0 for k in letters}
    parts = re.split(r"(<[^>]+>)", head)
    for i, part in enumerate(parts):
        if part.startswith("<"):
            continue

        def one(m):
            counts[m.group(1)] += 1
            return "<b>%s</b>" % m.group(1)
        parts[i] = re.sub(r"(?<![A-Za-z0-9<>/])([%s])(?![A-Za-z0-9])" % letters, one, part)
    assert counts == expect, "Q%d bold tokens %r, expected %r" % (qn, counts, expect)
    Q[qn]["content_html"] = "".join(parts) + tail
    LOG.append("Q%d: bold %r in the region before %r: %r" % (qn, letters, region_end[:30], counts))


# Q1: the particle column of Table 1.1
for cell in ("Nh", "Mc<sup>3−</sup>", "Ts<sup>−</sup>", "Og"):
    sub(1, "<td>%s</td>" % cell, "<td><b>%s</b></td>" % cell)

# Q2
bold(2, "written in (c)(ii) and", "written in <b>(c)(ii)</b> and")
bold_header_row(2, "Experiment")

# Q3
bold(3, "Draw the structures of A and B.", "Draw the structures of <b>A</b> and <b>B</b>.")
bold(3, "for steps 1, 2 and 3.", "for steps <b>1</b>, <b>2</b> and <b>3</b>.")
bold(3, "distinguish compounds J and K.", "distinguish compounds <b>J</b> and <b>K</b>.")
bold(3, "Compound J can be used", "Compound <b>J</b> can be used")
bold(3, "Draw the structure of C.", "Draw the structure of <b>C</b>.")
bold(3, "for step 7.", "for step <b>7</b>.")
# (b)(iii): the typed "J   K" caption line is dropped; the user's snip carries both labels
sub(3, r'(<div class="fig">figure</div>)\n<p>\s+J\s+K (<span class="mk">\[2\]</span>)</p>', r'\1\n<p>\2</p>', rx=True)
sub(3, r"\n \n\s+J\s+K \[2\]", "\nJ K [2]", field="content_text", rx=True)

# Q4 (a): D, E, F as printed; the experiment numbers and the cross-references
bold_tokens(4, '<span class="pl">(b)</span>', "DEF", {"D": 8, "E": 6, "F": 6})
bold(4, "experiments 3 and 4,", "experiments <b>3</b> and <b>4</b>,")
bold(4, "answers in (a)(i), (a)(ii) and (a)(iii), draw", "answers in <b>(a)(i)</b>, <b>(a)(ii) and (a)(iii)</b>, draw")
# Q4 (b)
bold(4, "<i>x</i>", "<b><i>x</i></b>", count=2)
bold(4, "final product, S.", "final product, <b>S</b>.")
bold(4, "<p>S reacts", "<p><b>S</b> reacts")
bold(4, "organic compound S.", "organic compound <b>S</b>.")

# Q5
bold(5, "(a)(iii) &amp; (a)(iv)", "<b>(a)(iii) &amp; (a)(iv)</b>")
sub(5, "(a)(iii) &amp; (a)(iv)", "(a)(iii) & (a)(iv)", field="content_text")
bold(5, "answer in (a)(v) and (b)(ii),", "answer in <b>(a)(v)</b> and <b>(b)(ii)</b>,")

# Q6
bold(6, "namely T, U and V,", "namely <b>T</b>, <b>U</b> and <b>V</b>,")
bold_header_row(6, "colour of visible")
bold_header_row(6, "Element")
sub(6, "<td>X</td>", "<td><b>X</b></td>")
sub(6, "<td>Y</td>", "<td><b>Y</b></td>")

# ------------------------------------------------ user rulings (2026-10-17)
def both(qn, old, new, count=1, rx=False):
    """Apply one change to content_html AND content_text, each asserted."""
    sub(qn, old, new, count=count, rx=rx)
    sub(qn, old, new, count=count, field="content_text", rx=rx)


# 1. Table 2.1: the rate unit is s^-1 (Fig. 2.1 is in seconds; k = 3.75 reproduces it)
sub(2, "mol dm<sup>-3</sup> min<sup>-1</sup>", "mol dm<sup>-3</sup> s<sup>-1</sup>")
sub(2, "mol dm-3 min-1", "mol dm-3 s-1", field="content_text")
# 2. stray comma
both(4, "a gem-triol, is formed", "a gem-triol is formed")
# 3. spelling
both(6, "hemocyanin", "haemocyanin", count=2)
# 4. typography: "x" -> "×" in a number written in standard form
for qn, n in ((2, 2), (5, 4)):
    sub(qn, r"(?<=\d) x (?=10<sup>)", " × ", count=n, rx=True)
    sub(qn, r"(?<=\d) x (?=10)", " × ", count=n, field="content_text", rx=True)
# 4. hyphen-minus inside a superscript -> U+2212 (charges and exponents); the search text too
for qn in sorted(Q):
    h = Q[qn]["content_html"]
    sups = [x for x in re.findall(r"<sup>[^<]*</sup>", h) if "-" in x]
    for x in sups:
        assert re.fullmatch(r"<sup>(?:\d-|-\d?)</sup>", x), (qn, x)
    n_text = 0
    t = Q[qn]["content_text"]
    for pat in (r"(?<=dm)-(?=\d)", r"(?<=min)-(?=\d)", r"(?<= s)-(?=1)", r"(?<=mol)-(?=\d)", r"(?<=10)-(?=\d)",
                r"(?<=CO32)-", r"(?<=HCO3)-", r"(?<=Mc3)-", r"(?<=OH)-(?=\s)"):
        t, k = re.subn(pat, "−", t)
        n_text += k
    assert n_text == len(sups), "Q%d: %d hyphen superscripts in the html, %d in the text" % (qn, len(sups), n_text)
    Q[qn]["content_html"] = re.sub(r"<sup>[^<]*</sup>", lambda m: m.group(0).replace("-", "−"), h)
    Q[qn]["content_text"] = t
    if sups:
        LOG.append("Q%d: %d hyphen-minus superscripts -> U+2212 (html and search text)" % (qn, len(sups)))
# 4. en dash used as a minus sign (Q6(c)(iv)); the wavelength ranges "620 – 750" are real ranges and stay
both(6, "is –2582 kJ", "is −2582 kJ")
both(6, "–1980", "−1980")
both(6, "–381", "−381")
# 4. "2977 <sup>o</sup>C" -> degree sign
sub(6, "2977 <sup>o</sup>C and 180 <sup>o</sup>C", "2977 °C and 180 °C")
sub(6, "2977 oC and 180 oC", "2977 °C and 180 °C", field="content_text")
# 5. grammar
both(3, "can achieved by", "can be achieved by")
both(3, "incorporating Wolff-Kishner reaction", "incorporating the Wolff-Kishner reaction")
both(4, "is an constitutional isomer", "is a constitutional isomer")
both(5, "by ocean acidification has been a concern", "by ocean acidification have been a concern")
both(5, "Changes in the pH alters", "Changes in the pH alter")
both(5, "form their shells in the seawater in 2020?", "form their shells in the seawater in 2020.")
both(6, "some of elements from", "some of the elements from")
# 6. "x and y" -> bold X and Y (as Table 6.3 labels them)
sub(6, "State the values of x and y in Table 6.3", "State the values of <b>X</b> and <b>Y</b> in Table 6.3")
sub(6, "State the values of x and y in Table 6.3", "State the values of X and Y in Table 6.3", field="content_text")

# 7. Fig./Table captions are bold (user ruling, 2026-10-17)
_n_cap = 0
for qn in sorted(Q):
    h = Q[qn]["content_html"]
    h, k1 = re.subn(r'<p class="c">((?:Table|Fig\.) \d\.\d)</p>', r'<p class="c"><b>\1</b></p>', h)
    h, k2 = re.subn(r'<p class="c"><i>(Fig\. \d\.\d:[^<]*)</i></p>', r'<p class="c"><i><b>\1</b></i></p>', h)
    Q[qn]["content_html"] = h
    _n_cap += k1 + k2
assert _n_cap == 13, _n_cap
LOG.append("captions: %d Fig./Table captions bold" % _n_cap)

# ---------------------------------------------------------- the asset plan
def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


def rename(qn, old, new, part):
    x = get(qn, old)
    x["slot"], x["part"] = new, part
    x["storage_path"] = x["storage_path"].replace("_%s_" % old, "_%s_" % new)
    LOG.append("asset plan: Q%d slot %s -> %s (%s)" % (qn, old, new, x["storage_path"]))


# the figure now sits between two parts, before the part named here
rename(2, "a", "b", "(b)(i)")
rename(6, "aii", "aiii", "(a)(iii)")

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 11

# no leftover soft <br>; no stray </p>; no sentinel bytes
for qn in Q:
    h = Q[qn]["content_html"]
    assert "<br>" not in h, "Q%d still has <br>" % qn
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
assert [Q[k]["marks"] for k in sorted(Q)] == [7, 11, 13, 14, 12, 18]
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
