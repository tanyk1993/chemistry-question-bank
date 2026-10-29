"""DHS 2026 H2 P3 (9476/03) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QA.docx -d unz
  python3 -m ingest.dhs26_p3_prep unz unz_q                  # strip the answer rows (copy)
  python3 -m ingest.redact_inline_answers_pdf QA_word.pdf q_word.pdf 0xff,0x3333ff,0xff0000
  python3 -m ingest.extract_parts unz_q q_word.pdf out \
      --school DHS --level H2 --paper P3 --year 2026 --first-page 1
  python3 -m ingest.patch_dhs26_p3_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql --school DHS --year 2026 --paper 3 --level H2

Shape: the school's "question paper + suggested solutions" docx (SEAB 4-column grid
with blue answer rows), same family as ACJC / ASRJC 2026 P3. Answers are NOT read at
this stage; `dhs26_p3_prep` removes them from a copy. The crops the extractor writes
are NOT used: the user snips every figure, so the asset plan below is the SNIP LIST.

symbols.py / adobe_symbol.py: Wingdings F081-F083 = circled 1-3 (Q1(b)(ii) list).

Section A is Q1-Q3 (18 + 18 + 19) and Section B is Q4 or Q5 (20 each), so the rows hold
95 marks; the cover prints 75 (the sat paper: Section A + one Section B question).

FIGURES (user snips, 10 files):
  block (placeholders, ordinal = DOM order): Q1 a, a2, b, ci, cii, d; Q2 b; Q3 c; Q5 b
  inline: Q1 bi = the "R" unit, ONE file used by BOTH Q1(b)(i) and Q1(b)(ii)
          (resolveAssets() matches every img[data-asset] by filename).
  The structure labels M (Q1(a)), X / Y (Q1(b)) and A / B (Q1(c)(ii)) are typed in the
  Word file as space-padded lines under the drawing; they are part of the snip and the
  typed lines are removed. Printed captions (succinimide, Fig. 1.1, Fig. 2.1,
  Table 3.2's W, 2-bromo-4-nitrobenzoic acid) stay typed.
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

P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"
FIG = '<div class="fig">figure</div>'


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, old, new, count=1, rx=False):
    sub(qn, old, new, count=count, rx=rx)
    sub(qn, old, new, field="content_text", count=count, rx=rx)


# ======================================================================= Q1
# (a): "M" is typed under the reactant with a run of spaces; it is part of the snip
sub(1, r'\n<p>\s+<b>M</b></p>\n', "\n", rx=True)
sub(1, r"reaction 1\. \n\n\s+M\nExplain", "reaction 1. \nExplain", field="content_text", rx=True)
# (b): "X ... Y" typed under the two structures; part of the snip
sub(1, r'\n<p>\s+<b>X</b>\s+<b>Y</b></p></div>', "</div>", rx=True)
sub(1, r"Torlon®\.\n\s+\n\s+X\s+Y \(b\)\(i\)", "Torlon®. (b)(i)", field="content_text", rx=True)
# (b)(i), (b)(ii): "You may use R to represent [picture]." -> the picture is INLINE in the
# sentence (one file, both parts)
R_IMG = ('<img data-asset="DHS_H2_P3_Q1_bi_2026.png" alt="R: the diphenylmethane unit (two benzene '
         'rings joined by CH2)" style="vertical-align:middle">')
sub(1, '<p>You may use R to represent</p>\n' + FIG + '\n<p>. <span class="mk">[1]</span></p></div>',
    '<p>You may use R to represent ' + R_IMG + '. <span class="mk">[1]</span></p></div>')
sub(1, '<p>You may use R to represent</p>\n' + FIG + '\n<p>. <span class="mk">[3]</span></p></div>',
    '<p>You may use R to represent ' + R_IMG + '. <span class="mk">[3]</span></p></div>')
sub(1, r"You may use R to represent\s+\. \[", "You may use R to represent . [", field="content_text", count=2, rx=True)
# (c)(ii): "A ... B" typed under the structures; part of the snip
sub(1, r'\n<p><b>\s+A\s+B\s+</b> <span class="mk">\[3\]</span></p></div>',
    '\n<p><span class="mk">[3]</span></p></div>', rx=True)
sub(1, r"Explain this order\.\n\n\s+A\s+B\s+ \[3\]", "Explain this order. [3]", field="content_text", rx=True)

# ======================================================================= Q2
# (a)(ii): Table 2.2's <p> were mis-nested across its cells -> rebuilt; the empty answer
# cells get room to write in
sub(2, "complete <br>Table 2.2. ", "complete Table 2.2. ")
sub(2, r'<table class="qt"><tr><td>type of hydrogen atom</td><td>number of <br>hydrogen atom\n'
    r'<p>in 2-methylbutane</td>.*?</table> <span class="mk">\[2\]</span></p></div>',
    '<table class="qt">'
    '<tr><td>type of hydrogen atom</td><td>number of hydrogen atom in 2-methylbutane</td>'
    '<td>relative ratio of monochlorinated product, C<sub>5</sub>H<sub>11</sub>C<i class="el">l</i></td></tr>'
    '<tr><td>primary (1°)</td><td style="height:2.2em"></td><td></td></tr>'
    '<tr><td>secondary (2°)</td><td style="height:2.2em"></td><td></td></tr>'
    '<tr><td>tertiary (3°)</td><td style="height:2.2em"></td><td></td></tr></table>'
    '<p><span class="mk">[2]</span></p></div>', rx=True)
sub(2, r"type of hydrogen atomrelative rate of substitutionprimary \(1°\)1secondary \(2°\)7tertiary \(3°\)21",
    "type of hydrogen atom relative rate of substitution primary (1°) 1 secondary (2°) 7 tertiary (3°) 21",
    field="content_text", rx=True)
sub(2, r"Use the data in Table 2\.1 and the structure of 2-methylbutane to complete Table 2\.2\. \n"
    r"Table 2\.2\ntype of hydrogen atomnumber of hydrogen atom\nin 2-methylbutanerelative ratio of "
    r"monochlorinated product, C5H11Clprimary \(1°\)secondary \(2°\)tertiary \(3°\) \[2\]",
    "Use the data in Table 2.1 and the structure of 2-methylbutane to complete Table 2.2. \nTable 2.2\n"
    "type of hydrogen atom number of hydrogen atom in 2-methylbutane relative ratio of monochlorinated "
    "product, C5H11Cl primary (1°) secondary (2°) tertiary (3°) [2]", field="content_text", rx=True)
# (c)(ii): typed line wrap
sub(2, "with <br>20 cm", "with 20 cm")
# the bullets of (c)(iii) run together in the search text
sub(2, "the initial pH the equivalence volume the pH and volume at maximum buffering capacity "
    "the pH of solution after 50 cm3 of HCl is added",
    "the initial pH; the equivalence volume; the pH and volume at maximum buffering capacity; "
    "the pH of solution after 50 cm3 of HCl is added", field="content_text")

# ======================================================================= Q3
sub(3, "of <br>0.050 mol", "of 0.050 mol")
sub(3, "of 0.050 mol dm−3 NaOH(aq).", "of 0.050 mol dm−3 NaOH(aq).", field="content_text")
# Table 3.1 (search text: cells glued together)
sub(3, r"Cu2\+Mg2\+Ksp for metal hydroxide at 298 K / mol3 dm−92\.20 × 10−201\.80 × 10−11",
    "Cu2+ Mg2+ Ksp for metal hydroxide at 298 K / mol3 dm−9 2.20 × 10−20 1.80 × 10−11",
    field="content_text", rx=True)
# (c): Table 3.2 rebuilt (the extractor mis-nests <p> across its cells)
sub(3, r'<table class="qt"><tr><td>test</td><td>reaction</td>.*?</table></p>\n',
    '<table class="qt">'
    '<tr><td>test</td><td>reaction</td><td>organic compounds formed</td><td>other information</td></tr>'
    '<tr><td>1</td><td><b>P</b> with 2,4-DNPH</td><td>orange ppt</td><td></td></tr>'
    '<tr><td>2</td><td><b>P</b> with Fehling’s reagent</td><td>no reaction</td><td></td></tr>'
    '<tr><td>3</td><td><b>P</b> with an excess of hot, acidified KMnO<sub>4</sub></td>'
    '<td><b>Q</b>, C<sub>9</sub>H<sub>8</sub>O<sub>3</sub><br><b>R</b>, C<sub>3</sub>H<sub>6</sub>O</td><td></td></tr>'
    '<tr><td>4</td><td><b>Q</b> with alkaline I<sub>2</sub>(aq), followed by acidification of resultant mixture</td>'
    '<td>yellow precipitate <b>S</b><br><b>T</b>, C<sub>8</sub>H<sub>6</sub>O<sub>4</sub></td>'
    '<td><b>T</b> is formed after acidification</td></tr>'
    '<tr><td>5</td><td><b>R</b> with alkaline I<sub>2</sub>(aq), followed by acidification of resultant mixture</td>'
    '<td>yellow precipitate <b>S</b><br><b>U</b>, C<sub>2</sub>H<sub>4</sub>O<sub>2</sub></td>'
    '<td><b>U</b> is formed after acidification</td></tr>'
    '<tr><td>6</td><td><b>T</b> with LiA<i class="el">l</i>H<sub>4</sub></td><td><b>V</b></td><td></td></tr>'
    '</table>\n', rx=True)
sub(3, r"testreactionorganic compounds formedother information1P with 2,4-DNPHorange ppt2P with "
    r"Fehling’s reagentno reaction3P with an excess of hot, acidified KMnO4Q, C9H8O3\nR, C3H6O4Q with "
    r"alkaline I2\(aq\), followed by acidification of resultant mixtureyellow precipitate S\nT, C8H6O4T is "
    r"formed after acidification5R with alkaline I2\(aq\), followed by acidification of resultant "
    r"mixtureyellow precipitate S\nU, C2H4O2U is formed after acidification6T with LiAlH4V\n",
    "test reaction organic compounds formed other information "
    "1 P with 2,4-DNPH orange ppt "
    "2 P with Fehling’s reagent no reaction "
    "3 P with an excess of hot, acidified KMnO4 Q, C9H8O3 R, C3H6O "
    "4 Q with alkaline I2(aq), followed by acidification of resultant mixture yellow precipitate S T, C8H6O4 "
    "T is formed after acidification "
    "5 R with alkaline I2(aq), followed by acidification of resultant mixture yellow precipitate S U, C2H4O2 "
    "U is formed after acidification "
    "6 T with LiAlH4 V\n", field="content_text", rx=True)

# ======================================================================= Q4
# (a): the equation line is hand-aligned with a run of spaces
sub(4, r'equation 1[ \t]{3,}PC', "equation 1    PC", rx=True)
sub(4, r'equation 1[ \t]{3,}PCl5', "equation 1    PCl5", field="content_text", rx=True)
# (c)(ii): the minus of HSO4- was typed bold, the arrow bold
sub(4, '2HSO<sub>4</sub><b><sup>–</sup></b> + H', '2HSO<sub>4</sub><sup>−</sup> + H')
sub(4, "2HSO4– + H3O+", "2HSO4− + H3O+", field="content_text")
sub(4, '<b>⇌ </b>NO<sub>2</sub>', '⇌ NO<sub>2</sub>')

# ======================================================================= Q5
# (a): the equilibrium line (centred) is spaced by hand; "&gt;" leaked into the search text
sub(5, r'<p class="c">2NOC<i class="el">l</i>\(g\)  ⇌ 2NO\(g\) \+ C<i class="el">l</i><sub>2</sub>\(g\)     ∆',
    '<p class="c eqn">2NOC<i class="el">l</i>(g) ⇌ 2NO(g) + C<i class="el">l</i><sub>2</sub>(g)    ∆', rx=True)
sub(5, r"2NOCl\(g\)  ⇌ 2NO\(g\) \+ Cl2\(g\)     ∆H⦵ &gt; 0", "2NOCl(g) ⇌ 2NO(g) + Cl2(g)    ∆H⦵ > 0",
    field="content_text", rx=True)
sub(5, "was <br>4.5 kPa", "was 4.5 kPa")
# (c)(iii): the two observations are ONE list
sub(5, '</li></ul>\n<ul class="stmts"><li>When an aqueous solution', '</li><li>When an aqueous solution')

# --------------------------------------------- standard-state sign: house markup sup.pl-sym
for qn in sorted(Q):
    s = Q[qn]["content_html"]
    n = s.count("<sup>⦵</sup>")
    if n:
        Q[qn]["content_html"] = s.replace("<sup>⦵</sup>", '<sup class="pl-sym">⦵</sup>')
        LOG.append("Q%d: %d standard-state sign(s) -> sup.pl-sym" % (qn, n))


# ---------------------------------------------------------------- generic tidy
def tidy(qn):
    s = Q[qn]["content_html"]
    n_ws = n_dash = n_td = n_stray = n_empty = n_exp = 0
    s, n_exp = re.subn(r"(?<=[A-Za-z0-9)])<sup>[ \t]+", "<sup>", s)
    s = re.sub(r"<(b|i)>[ \t]+</\1>", " ", s)          # a bold/italic run holding only a space

    def rep(m):
        nonlocal n_ws
        open_t, lead, body, trail, close_t = m.groups()
        if not lead and not trail:
            return m.group(0)
        n_ws += 1
        return (" " if lead else "") + open_t + body + close_t + (" " if trail else "")
    s = re.sub(r'(<(?:sup|sub|i|b|i class="el")>)([ \t]*)([^<]*?)([ \t]*)(</(?:sup|sub|i|b)>)', rep, s)
    s, n_empty = re.subn(r"<(sub|sup|i|b)></\1>", "", s)

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
        if ln.startswith('<p class="eqn">') or ln.startswith('<p class="c eqn">'):
            continue
        new = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", ln)
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
    for pat in (r"(?<=dm)[-–‒](?=\d)", r"(?<=mol)[-–‒](?=\d)", r"(?<=10)[-–‒](?=\d)"):
        t, k = re.subn(pat, "−", t)
        n += k
    t = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", t)
    t = t.replace("[Total: %d]" % Q[qn]["marks"], "").rstrip() if "[Total" in t else t
    Q[qn]["content_text"] = t
    LOG.append("Q%d text: %d minus signs normalised, [Total] line dropped" % (qn, n))


# ---------------------------------------------------------- the asset plan (= the SNIP LIST)
def A(q, slot, ordinal, part, inline=False):
    return {"question": q, "part": part, "slot": slot, "ordinal": ordinal,
            "storage_path": "DHS_H2_P3_Q%d_%s_2026.png" % (q, slot),
            "n_refs": 0 if inline else 1, **({"inline": True} if inline else {})}


PLAN[:] = [
    A(1, "a", 1, "(a)"), A(1, "a2", 2, "(a)"), A(1, "b", 3, "(b)"),
    A(1, "ci", 4, "(c)(i)"), A(1, "cii", 5, "(c)(ii)"), A(1, "d", 6, "(d)"),
    A(1, "bi", 7, "(b)(i)", inline=True),
    A(2, "b", 1, "(b)"),
    A(3, "c", 1, "(c)"),
    A(5, "b", 1, "(b)"),
]
LOG.append("asset plan rebuilt: 9 block + 1 inline = 10 snips")

# ---------------------------------------------------------------- checks
bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count(FIG)
    nblock = len([p for p in PLAN if p["question"] == qn and not p.get("inline")])
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d block assets" % (qn, nph, nblock))
    for p in PLAN:
        if p["question"] == qn and p.get("inline") and 'data-asset="%s"' % p["storage_path"] not in h:
            bad.append("Q%d: inline %s not in the html" % (qn, p["storage_path"]))
    ords = sorted(p["ordinal"] for p in PLAN if p["question"] == qn)
    if ords != list(range(1, len(ords) + 1)):
        bad.append("Q%d: ordinals not 1..n" % qn)
    if len(P_OPEN.findall(h)) != h.count(P_CLOSE):
        bad.append("Q%d: <p> unbalanced" % qn)
    for tag in ("table", "tr", "td", "div", "ul", "li"):
        if h.count("<%s" % tag) != h.count("</%s>" % tag):
            bad.append("Q%d: <%s> unbalanced" % (qn, tag))
    if "<br>" in h and "<td" not in h:
        bad.append("Q%d: leftover <br> outside a table" % qn)
    if re.search(r"<(sup|sub|b|i)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    if "[Total" in h or "[Total" in Q[qn]["content_text"]:
        bad.append("Q%d: still has a [Total] line" % qn)
    n_mk = len(re.findall(r'<span class="mk">', h))
    n_parts = len([p for p in r["parts"] if p["marks"]])
    if n_mk != n_parts:
        bad.append("Q%d: %d mark badges vs %d parts with marks" % (qn, n_mk, n_parts))
    if sum(p["marks"] or 0 for p in r["parts"]) != r["marks"]:
        bad.append("Q%d: parts do not sum to the question total" % qn)
    if "&gt;" in r["content_text"] or "\x00" in h or "\x00" in r["content_text"]:
        bad.append("Q%d: entity or NUL in the text" % qn)
    # a <br> left inside a table cell is deliberate (Table 3.2); everywhere else it is a typed wrap
assert [Q[k]["marks"] for k in sorted(Q)] == [18, 18, 19, 20, 20]
assert sum(r["marks"] for r in Q.values()) == 95
assert not bad, "\n".join(bad)

# section_label is NULL for structured papers
for qn in Q:
    Q[qn]["section"] = None

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets (%d block, %d inline)" % (
    len(Q), len(PLAN), len([p for p in PLAN if not p.get("inline")]),
    len([p for p in PLAN if p.get("inline")])))
