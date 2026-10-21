"""ACJC 2026 H2 P2 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_acjc26_p2_questions <extractor_out_dir> <build_dir>

Pipeline: `extract_parts` (table shape, no prep needed; crops stubbed because the
user snips every figure; school ACJC, level H2, paper P2, year 2026) -> THIS
script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 corrections.GLYPH_PICTURES (extractor side, not here): the equilibrium arrows of
   equations 1.1, 1.2 and 4.2 are drawn pictures; they are typed as "⇌".
 Q1  equations 1.1/1.2 (a borderless 2-cell table in the docx) -> two p.eqn lines;
     the soft <br> after Table 1.2
 Q2  Table 2.1's header cells (the extractor mis-nests <p> across cells) rebuilt;
     (b)(ii)'s mark sits in its own <p> with a blank italic run -> mk badge
 Q3  (b)(i)'s mark was typed after a <br> and a run of spaces (not parsed: 3 marks
     lost, so the paper "summed to 11"); the lead-in before (b)(iii) (the coupling
     paragraph + Fig. 3.3) stands as its own unlabelled block (the user's HCI P3
     ruling), asset slot bii -> biii
 Q4  "equation N.N" lines get class eqn (EQN_LINE_RE only matches an INTEGER N);
     (b)(iii)'s and (c)'s marks, and the question total, were not parsed
 Q5  Table 5.1 rebuilt as a clean table; Fig. 5.1 and Fig. 5.2 are two pictures
     (one placeholder was extracted) -> a second placeholder, asset slot b2;
     (d)(vi)'s mark and the question total were not parsed
 generic: whitespace inside inline tags, runs of spaces, en/figure dash and hyphen
     inside <sup> and as a minus -> U+2212, a soft <br> -> space
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
# Q1: equations 1.1 / 1.2 are a borderless label|equation table in the docx; the
# paper prints them as two aligned lines, so emit p.eqn (pre-wrap keeps the gap).
sub(1, r'<table class="qt"><tr><td>equation 1\.1</td><td> (.*?)</td></tr><tr><td>equation 1\.2</td><td> (.*?)</td></tr></table>',
    r'<p class="eqn">equation 1.1      \1</p>\n<p class="eqn">equation 1.2      \2</p>', rx=True)
sub(1, "H3O+equation 1.2", "H3O+ equation 1.2", field="content_text")
sub(1, "equation 1.1 HOOCCH", "equation 1.1 HOOCCH", field="content_text")

# Q1(a)(i): "acid:" and "conjugate base:" sat on one line; the user wants two lines
sub(1, '<p>acid: conjugate base: <span class="mk">[1]</span></p>',
    '<p>acid:</p>\n<p>conjugate base: <span class="mk">[1]</span></p>')

# Q1(c)(iv): a soft <br> opens the paragraph that follows Table 1.2
sub(1, "</table>\n<p><br>Identify", "</table>\n<p>Identify")

# Q2: Table 2.1's header row. The extractor mis-nests <p> across cells; rebuild it.
sub(2, r'<tr><td>experiment</td>.*?</td></tr><tr><td>1</td>',
    '<tr><td>experiment</td>'
    '<td>initial [CH<sub>3</sub>CH<sub>2</sub>CBr(CH<sub>3</sub>)<sub>2</sub>] /<br>mol dm<sup>–3</sup></td>'
    '<td>initial [NaOH] /<br>mol dm<sup>–3</sup></td>'
    '<td>initial rate /<br>mol dm<sup>–3</sup> s<sup>–1</sup></td></tr><tr><td>1</td>', rx=True)
# Q2(b)(ii): the mark is in its own <p> with a blank italic run
sub(2, r'state the type of mechanism for this reaction\. \n<p>\[1\]<i>\s*</i></p></div>',
    'state the type of mechanism for this reaction. <span class="mk">[1]</span></div>', rx=True)
sub(2, "for this reaction. \n[1] (b)(iii)", "for this reaction. [1] (b)(iii)", field="content_text")

# Q3(b)(i): the mark follows a soft <br> and a run of spaces
sub(3, r'compound <b>W</b>\.\s+<br>\s+\[3\]</p>',
    'compound <b>W</b>. <span class="mk">[3]</span></p>', rx=True)

# Q3: the coupling paragraph and Fig. 3.3 follow (b)(ii)'s last mark but belong to
# (b)(iii): close (b)(ii), then they stand as their own unlabelled block.
def eject(qn, nxt):
    s = Q[qn]["content_html"]
    pat = (r'(<span class="mk">\[\d\]</span>(?:</p>)?)\n((?:(?!<div class="qpart">).)+?)</div>\n'
           r'(<div class="qpart"><span class="pl">%s</span>)' % re.escape(nxt))
    ms = list(re.finditer(pat, s, flags=re.S))
    assert len(ms) == 1, "Q%d eject before %s: %d matches" % (qn, nxt, len(ms))
    Q[qn]["content_html"] = re.sub(pat, r"\1</div>\n\2\n\3", s, flags=re.S)
    LOG.append("Q%d: lead-in passage moved out of the previous part, before %s" % (qn, nxt))


eject(3, "(b)(iii)")

# Q4: "equation 4.1/4.2" lines are hand-aligned with runs of spaces; EQN_LINE_RE only
# matches an integer ("equation 4"), so tag them here.
sub(4, '<p>equation 4.1 ', '<p class="eqn">equation 4.1 ')
sub(4, '<p>equation 4.2 ', '<p class="eqn">equation 4.2 ')
# the dehydrogenation equation's own line break: the sentinel replacement leaves it intact
# Q4(b)(iii): mark typed after a run of spaces
sub(4, r'was re-established\.\s+\[2\]</p>', 'was re-established. <span class="mk">[2]</span></p>', rx=True)
# Q4(c): the mark and the question total are separate paragraphs
sub(4, r'O<sup>−</sup>\.\s+</p>\n<p>\[1\]</p>\n<p>\[Total: 10\]</p></div>',
    'O<sup>−</sup>. <span class="mk">[1]</span></p></div>', rx=True)

# Q5: Table 5.1 rebuilt (the extractor mis-nests <p> across the header cells and
# around the figure cells). Placeholders stay in DOM order: nylon-6,6, -4,6, -4.
sub(5, r'<table class="qt"><tr><td>name</td>.*?</table></p>',
    '<table class="qt"><tr><td>name</td><td>polymer</td>'
    '<td>degree of crystallinity<br>/ %</td><td>maximum tensile strength<br>/ MPa</td></tr>'
    '<tr><td>nylon-6,6</td><td><div class="fig">figure</div></td><td>45</td><td>95</td></tr>'
    '<tr><td>nylon-4,6</td><td><div class="fig">figure</div></td><td>70</td><td>85</td></tr>'
    '<tr><td>nylon-2,6</td><td></td><td>40</td><td>90</td></tr>'
    '<tr><td>nylon-4</td><td><div class="fig">figure</div></td><td>55</td><td>40</td></tr></table>', rx=True)
sub(5, "degree of crystallisation\n/ %maximum tensile strength\n/ MPanylon-6,64595nylon-4,67085nylon-2,64090nylon-45540",
    "degree of crystallinity / % maximum tensile strength / MPa nylon-6,6 45 95 nylon-4,6 70 85 nylon-2,6 40 90 nylon-4 55 40",
    field="content_text")
# Q5(b): Fig. 5.1 and Fig. 5.2 are two pictures; one placeholder was extracted
sub(5, '<p class="c"><b>Fig. 5.1</b></p>\n<p class="c"><b>Fig. 5.2</b></p>',
    '<p class="c"><b>Fig. 5.1</b></p>\n<div class="fig">figure</div>\n<p class="c"><b>Fig. 5.2</b></p>')
# Q5(d)(vi): the mark and the question total are separate paragraphs
sub(5, r'discarded nylon-6,6 nets\.\n<p>\[2\]</p>\n<p>\[Total: 20\]</p></div>',
    'discarded nylon-6,6 nets. <span class="mk">[2]</span></div>', rx=True)

# Q5 Table 5.2: the minus sign is typed as a figure dash (U+2012)
sub(5, r"<td>‒(\d)", r"<td>−\1", count=3, rx=True)
sub(5, "‒", "−", field="content_text", count=4)

# ------------------------------------------------ user rulings (2026-10-20)
def both(qn, old, new, count=1, rx=False):
    """Apply one change to content_html AND content_text, each asserted."""
    sub(qn, old, new, count=count, rx=rx)
    sub(qn, old, new, field="content_text", count=count, rx=rx)


# user ruling 2026-10-21: the two small answer tables in Q3 become plain labelled lines
sub(3, '<table class="qt"><tr><td>observations for phenylalanine</td><td>observations for tyrosine</td></tr><tr><td></td><td></td></tr></table>',
    '<p>observations for phenylalanine:</p>\n<p>observations for tyrosine:</p>')
sub(3, '<table class="qt"><tr><td>step 1</td><td></td></tr><tr><td>step 2</td><td></td></tr></table>',
    '<p>step 1:</p>\n<p>step 2:</p>')
sub(3, "observations for phenylalanineobservations for tyrosine", "observations for phenylalanine:\nobservations for tyrosine:", field="content_text")
sub(3, "step 1step 2", "step 1:\nstep 2:", field="content_text")
both(2, "to synthesis pentanoic acid", "to synthesise pentanoic acid")
both(3, "can be synthesized from", "can be synthesised from")
both(3, "azodyes", "azo dyes")
both(4, "for decomposition temperature", "for the decomposition temperature")
both(4, "injected to an evacuated", "injected into an evacuated")
both(5, "Using Fig 5.3", "Using Fig. 5.3")
both(5, "such highly ordered", "such a highly ordered")
both(5, "a 2.26 g of", "2.26 g of", count=2)
both(5, "repeating unit", "repeat unit")
# the pressure conversion line is not used by the question: removed
sub(5, r"\n<p>\(1 MPa = 10<sup>6</sup> Pa\)</p>", "", rx=True)
sub(5, r"\n\(1 MPa = 106 Pa\)", "", field="content_text", rx=True)

# ------------------------------------------------------------- soft <br>
# the only <br> left outside a table cell is a typed line wrap inside a sentence (Q5(b))
sub(5, "Among the nylon variants, <br>nylon-6,6", "Among the nylon variants, nylon-6,6")


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
    # a run of spaces typed to separate words (outside the hand-aligned eqn lines)
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
                r"(?<=OH)[-–‒](?=\s|$)", r"(?<=\d)[-–‒](?=\d{3,})", r"(?<=\s)‒(?=\d)"):
        t, k = re.subn(pat, "−", t)
        n += k
    t = re.sub(r"(?<=\S)[ \t]{3,}(?=\S)", " ", t)
    Q[qn]["content_text"] = t
    LOG.append("Q%d text: %d minus signs normalised" % (qn, n))


# ------------------------------------------------ marks the extractor missed
def set_marks(qn, label, n):
    hits = [p for p in Q[qn]["parts"] if p["label"] == label]
    assert len(hits) == 1, (qn, label)
    assert hits[0]["marks"] in (None, n), (qn, label, hits[0]["marks"])
    hits[0]["marks"] = n
    LOG.append("Q%d %s marks = %d" % (qn, label, n))


set_marks(3, "(b)(i)", 3)
set_marks(4, "(b)(iii)", 2)
set_marks(4, "(c)", 1)
set_marks(5, "(d)(vi)", 2)
for qn, tot in ((3, 14), (4, 10), (5, 20)):
    assert Q[qn]["marks"] in (None, tot), (qn, Q[qn]["marks"])
    Q[qn]["marks"] = tot


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


# Fig. 3.3 now sits between (b)(ii) and (b)(iii): its slot is the part it is shown before
rename(3, "bii", "biii", "(b)(iii)")

# Q5(b): Fig. 5.2 is its own picture
b = get(5, "b")
b2 = dict(b)
b2.update({"slot": "b2", "storage_path": b["storage_path"].replace("_b_", "_b2_")})
PLAN.insert(PLAN.index(b) + 1, b2)
LOG.append("asset plan: Q5 added slot b2 (%s)" % b2["storage_path"])

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 17, len(PLAN)

# structural checks
for qn in Q:
    h = Q[qn]["content_html"]
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<td") == h.count("</td>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "[Total" not in h, "Q%d still has a [Total] line" % qn
    # every part prints its mark as a badge exactly where marks > 0
    for p in Q[qn]["parts"]:
        pass
    n_mk = len(re.findall(r'<span class="mk">', h))
    n_parts = len([p for p in Q[qn]["parts"] if p["marks"]])
    assert n_mk == n_parts, "Q%d: %d mark badges vs %d parts with marks" % (qn, n_mk, n_parts)
assert [Q[k]["marks"] for k in sorted(Q)] == [16, 15, 14, 10, 20]
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
