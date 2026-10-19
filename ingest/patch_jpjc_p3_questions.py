"""JPJC 2024 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_jpjc_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `jpjc_p3_prep` (re-emit the four question tables as
[qnum|letter|roman|content|marks]) -> `extract_parts` (crops stubbed: the user
snips every figure) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 hidden text   Q1(a): white, struck-through "210 kJ mol-1" after the delta-H (the
               school's deleted value) is removed from the stem and the search text
 lead-ins      three passages printed after a part's last mark belong to the NEXT
               part: Q3(d)(ii)->(d)(iii) ("Solution N"), Q4(a)(i)->(a)(ii) ("Nickel
               carbonate..."), Q5(a)(i)->(a)(ii) ("Cadmium ions are toxic...")
               (the user's HCI P3 ruling: they stand as their own unlabelled block)
 figures       Q2(b) two start-of-part anchors folded into Fig. 2.1 and put after the
               sentence that introduces it; Q2(e) Table 2.1 is ONE picture (the
               typed grid and three per-stage anchors removed); Q2(d) the two Nernst
               fractions are typed (.frac), not snipped; Q5(a)(ii) 1/1000 typed;
               Q3(a)/(b) typed captions under the structures dropped (the snip carries
               the names); Q4(a)(i) the figure moves BELOW its instruction
 marks         Q2(a)(ii) the [1] typed in its own paragraph becomes the mark badge
 bold          style-inherited bold restored as printed (compound letters, x, I/II)
 captions      every Fig./Table caption bold
 symbols       the Chemical-font plimsoll gets class="pl-sym" (as everywhere else)

NOT patched here (awaiting the user's rulings, see the stage report): school
typos and grammar, "x" vs "×", hyphen-minus superscripts, the Chemical-font glyph.
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
KEEP_BR = "@@KEEPBR@@"


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

# ============================================================ hidden text
# Q1(a): "∆H" is followed by white, struck-through text ("210 kJ mol-1").
sub(1, r"∆<i>H</i>210 kJ mol<sup>-1</sup>", "∆<i>H</i>", rx=False)
sub(1, "∆H210 kJ mol-1", "∆H", field="content_text")

# ============================================================ structural first
# Q1(e): "alkoxide    ether" is typed under the equation with runs of spaces
# The labels are set UNDER the species they name: each term is an inline-block, the two labelled terms two
# lines (formula / label), all top-aligned so the formulae stay on one line (user, 2026-10-19: the typed
# spaces left "alkoxide"/"ether" off their species).
_S = lambda t: '<sup style="line-height:0">%s</sup>' % t   # a raised charge must not grow its line box
_T = '<span style="display:inline-block;vertical-align:top;text-align:center;line-height:1.5">%s</span>'
sub(1, r'<p class="c">RBr<sup> </sup> \+ R’O<sup>−</sup>\s+→ ROR<sup>’</sup> \+ Br<sup>−</sup> </p>\s*<p>\s+alkoxide\s+ether</p>',
    '<p class="c">' + " ".join([_T % "RBr", _T % "+", _T % ("R’O" + _S("−") + KEEP_BR + "alkoxide"), _T % "→",
                                 _T % ("ROR" + _S("’") + KEEP_BR + "ether"), _T % "+", _T % ("Br" + _S("−"))]) + '</p>', rx=True)
sub(1, r"RBr  \+ R’O−  → ROR’ \+ Br− \n\s+alkoxide\s+ether",
    "RBr + R’O− → ROR’ + Br−\nalkoxide ether", field="content_text", rx=True)

# Q2(a)(ii): the mark [1] was typed in its own paragraph (with trailing spaces)
sub(2, r'\s*<i>\s*</i></p>\n<p>\[1\]\s*<i>\s*</i></p></div>',
    ' <span class="mk">[1]</span></p></div>', rx=True)
sub(2, r"like benzene does\.\s+\n\[1\]", "like benzene does. [1]", field="content_text", rx=True)

# Q2(b): the two start-of-part anchors are the pieces of Fig. 2.1. The printed order is
# sentence -> Fig. 2.1 -> caption -> sentence -> Fig. 2.2 -> caption.
sub(2, r'(<span class="pl">\(b\)</span>) <div class="fig">figure</div>\n<div class="fig">figure</div>\n'
       r'<p>(The standard reduction potential for 1,4-benzoquinone /benzene-1,4-diol is shown in Fig\. 2\.1\.)</p>\n',
    r'\1 \2\n<div class="fig">figure</div>\n', rx=True)
# Q2(b): the standard reduction potential is printed BESIDE Fig. 2.1 in a text box, at a
# different scale from the structure, so it is typed (not snipped) under the figure.
sub(2, r'(<div class="fig">figure</div>\n)(<p class="c">Fig\. 2\.1)',
    r'\1<p class="c"><i>E</i><sup class="pl-sym">⦵</sup> = +0.70&nbsp;V</p>\n\2', rx=True)
sub(2, r"\nFig\. 2\.1\nFig\. 2\.2 below", "\nE⦵ = +0.70 V\nFig. 2.1\nFig. 2.2 below",
    field="content_text", rx=True)

# Q4(c)(ii): the printed equation has a wide gap before the enthalpy change (runs of spaces
# collapse in HTML), so the gap is typed as em spaces to push the delta-H to the right.
sub(4, r"(\+  H<sub>2</sub>\(g\))\s+(∆<i>H</i><sup>⦵</sup> = x kJ)",
    r"\1&emsp;&emsp;&emsp;&emsp;\2", rx=True)

# Q2(d): the Nernst equation. Two fractions were pictures; typed as house .frac markup.
FR = '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>'
sub(2, r'<p class="c"><i>E</i> = <i>E</i><sup class="pl-sym">⦵</sup> \+</p>\n<div class="fig">figure</div>\n'
       r'<p class="c">log</p>\n<div class="fig">figure</div>\n',
    '<p class="c"><i>E</i> = <i>E</i><sup class="pl-sym">⦵</sup> + ' + FR % ("0.059", "n")
    + ' log ' + FR % ("[oxidised species]", "[reduced species]") + '</p>\n', rx=True)
sub(2, r"E = E⦵ \+  log\n", "E = E⦵ + 0.059/n log [oxidised species]/[reduced species]\n",
    field="content_text", rx=True)
sub(2, "<p>\tn = number of electrons transferred</p>", "<p>&emsp;n = number of electrons transferred</p>")

# Q2(e): Table 2.1 is ONE picture (Stage/Equation grid with its three structure rows)
sub(2, r'<table class="qt"><tr><td><b>Stage</b></td>.*?(?=<p class="c"><b>Table 2\.1</b></p>)',
    '<div class="fig">figure</div>\n', rx=True)
sub(2, r"StageEquation1\s+23\nTable 2\.1", "Table 2.1", field="content_text", rx=True)
# Q2(e)(ii): the name under the 1,4-cyclohexanedione structure
sub(2, r"<p>\s+1,4-cyclohexanedione</p>", '<p class="c">1,4-cyclohexanedione</p>', rx=True)

# Q3(a): the typed names under Fig. 3.1's structures are dropped (the snip carries them)
sub(3, r'<p>\s+oxirane\s+2-aminoethanol</p>\n', "", rx=True)
sub(3, r"\(a\) oxirane\s+2-aminoethanol\nFig\. 3\.1", "(a)\nFig. 3.1", field="content_text", rx=True)
# Q3(b): same for "J   K   2-aminoethanol"; the mark follows the figure as its own paragraph
sub(3, r'(<div class="fig">figure</div>)\n<p>\s+J\s+K\s+2-aminoethanol (<span class="mk">\[3\]</span>)</p>',
    r'\1\n<p>\2</p>', rx=True)
sub(3, r"\n\s+J\s+K\s+2-aminoethanol \[3\]", "\n[3]", field="content_text", rx=True)

# Q4(a)(i): the figure sits BELOW its instruction, above its own caption
sub(4, r'(<span class="pl">\(a\)\(i\)</span>) <div class="fig">figure</div>\n'
       r'<p>(Suggest a mechanism for the decomposition of the carbonate ion by adding two curly arrows on Fig\. 4\.1\.)</p>\n',
    r'\1 \2\n<div class="fig">figure</div>\n', rx=True)

# Q5(a): equilibrium I / II on their own lines; K_stab and its value on the NEXT line (user, 2026-10-19:
# the value wrapped, leaving only 10^10 alone on a line)
sub(5, r"equilibrium I:<br>", "equilibrium <b>I</b>:" + KEEP_BR)
sub(5, r"equilibrium II: <br>", "equilibrium <b>II</b>:" + KEEP_BR)
sub(5, r"\(l\)\s+<sub>\s*</sub><i>K</i><sub>stab</sub> = 3\.6", "(l)" + KEEP_BR + "<i>K</i><sub>stab</sub> = 3.6", rx=True)
sub(5, r"\(l\)\s+<i>K</i><sub>stab</sub> = 4\.2", "(l)" + KEEP_BR + "<i>K</i><sub>stab</sub> = 4.2", rx=True)
# Q5(a)(ii): 1/1000 was a picture, wrapped in a malformed underline
sub(5, r'to <u></p>\n<div class="fig">figure</div>\n<p></u> of its original concentration\.',
    'to ' + FR % ("1", "1000") + ' of its original concentration.', rx=True)
sub(5, "to  of its original concentration", "to 1/1000 of its original concentration", field="content_text")

# ------------------------------------------------ lead-ins between two parts
def eject(qn, nxt):
    s = Q[qn]["content_html"]
    pat = (r'(<span class="mk">\[\d\]</span>(?:</p>)?)\n((?:(?!<div class="qpart">).)+?)</div>\n'
           r'(<div class="qpart"><span class="pl">%s</span>)' % re.escape(nxt))
    ms = list(re.finditer(pat, s, flags=re.S))
    assert len(ms) == 1, "Q%d eject before %s: %d matches" % (qn, nxt, len(ms))
    Q[qn]["content_html"] = re.sub(pat, r"\1</div>\n\2\n\3", s, flags=re.S)
    LOG.append("Q%d: lead-in passage moved out of the previous part, before %s" % (qn, nxt))


eject(3, "(d)(iii)")
eject(4, "(a)(ii)")
eject(5, "(a)(ii)")

# ------------------------------------------------------------- soft <br>
BR_EXPECT = {1: 3, 2: 5, 3: 8, 4: 0, 5: 1 + 0}   # Q5: the two label breaks are KEPT (sentinel)
for qn in sorted(Q):
    h = Q[qn]["content_html"]
    n = len(re.findall(r"<br>", h))
    assert n == BR_EXPECT[qn], "Q%d <br> count %d, expected %d" % (qn, n, BR_EXPECT[qn])
    h = re.sub(r"[ \t]*<br>[ \t]*\n?", " ", h)
    h = h.replace("  <span class=\"mk\">", " <span class=\"mk\">")
    Q[qn]["content_html"] = h
    LOG.append("Q%d: %d soft <br> -> space" % (qn, n))


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
    Q[qn]["content_html"] = Q[qn]["content_html"].replace(KEEP_BR, "<br>")

# the Chemical-font plimsoll sign (U+29B5) in a bare <sup>: the same class every paper uses
n_pl = 0
for qn in sorted(Q):
    h = Q[qn]["content_html"]
    k = h.count("<sup>⦵</sup>")
    n_pl += k
    Q[qn]["content_html"] = h.replace("<sup>⦵</sup>", '<sup class="pl-sym">⦵</sup>')
assert n_pl == 3, n_pl      # Table 4.1 header, Q4(c)(ii), Q5(d)(i)
LOG.append("plimsoll: %d bare <sup>⦵</sup> -> class pl-sym" % n_pl)


# ---------------------------------------------------------------- bold (as printed)
def bold(qn, old, new, count=1):
    sub(qn, old, new, count=count)


# captions: every Fig./Table caption on its own line
_n_cap = 0
for qn in sorted(Q):
    h = Q[qn]["content_html"]
    h, k1 = re.subn(r'<p class="c">((?:Table|Fig\.) \d\.\d)</p>', r'<p class="c"><b>\1</b></p>', h)
    h, k2 = re.subn(r'<p class="c">((?:Table|Fig\.) \d\.\d) (<span class="mk">)', r'<p class="c"><b>\1</b> \2', h)
    Q[qn]["content_html"] = h
    _n_cap += k1 + k2
LOG.append("captions: %d Fig./Table captions bold" % _n_cap)

# Q2(e): aldol A; (g): E F G H
bold(2, "The aldol A is made", "The aldol <b>A</b> is made")
bold(2, "Compound E, C<sub>10</sub>H<sub>18</sub>O", "Compound <b>E</b>, C<sub>10</sub>H<sub>18</sub>O")
bold(2, " E reacts with sodium", " <b>E</b> reacts with sodium")
bold(2, "<p>E reacts with an excess", "<p><b>E</b> reacts with an excess")
bold(2, "molecules, F, C<sub>3</sub>H<sub>6</sub>O, H, (CO<sub>2</sub>H)<sub>2</sub>, and G, C<sub>5</sub>H<sub>8</sub>O<sub>3</sub>.",
     "molecules, <b>F</b>, C<sub>3</sub>H<sub>6</sub>O, <b>H</b>, (CO<sub>2</sub>H)<sub>2</sub>, and <b>G</b>, C<sub>5</sub>H<sub>8</sub>O<sub>3</sub>.")
bold(2, "<p>F and G both react with 2,4-dinitrophenylhydrazine. E, F and G react with aqueous alkaline iodine forming a yellow precipitate. G reacts",
     "<p><b>F</b> and <b>G</b> both react with 2,4-dinitrophenylhydrazine. <b>E</b>, <b>F</b> and <b>G</b> react with aqueous alkaline iodine forming a yellow precipitate. <b>G</b> reacts")
bold(2, "Suggest the structures of E, F and G.", "Suggest the structures of <b>E</b>, <b>F</b> and <b>G</b>.")

# Q3
bold(3, "structure of each compound J, K and 2-aminoethanol", "structure of <b>each</b> compound <b>J</b>, <b>K</b> and 2-aminoethanol")
bold(3, "an unknown gas, M, are formed", "an unknown gas, <b>M</b>, are formed")
bold(3, "primary amide, L, was reacted", "primary amide, <b>L</b>, was reacted")
bold(3, "primary amine and gas M were produced", "primary amine and gas <b>M</b> were produced")
bold(3, "primary amide L.", "primary amide <b>L</b>.")
bold(3, "<p>Solution N, a 10 cm", "<p>Solution <b>N</b>, a 10 cm")
bold(3, "a fully protonated lysine", "a <b>fully protonated</b> lysine")
bold(3, "initial pH of solution N?", "initial pH of solution <b>N</b>?")

# Q4
bold(4, "alkyne, Q, and a carbonyl compound, R, react together to form compound P as shown",
     "alkyne, <b>Q</b>, and a carbonyl compound, <b>R</b>, react together to form compound <b>P</b> as shown")
bold(4, "structures of alkyne Q and carbonyl compound R.", "structures of alkyne <b>Q</b> and carbonyl compound <b>R</b>.")
bold(4, "Identify compounds S and T.", "Identify compounds <b>S</b> and <b>T</b>.")
bold(4, "Compound U reacts with", "Compound <b>U</b> reacts with")
bold(4, "= x kJ mol", "= <b>x</b> kJ mol")
bold(4, "calculate a value for x.", "calculate a value for <b>x</b>.")
bold(4, "is less negative than x.", "is less negative than <b>x</b>.")

# Q5
bold(5, "for equilibrium I, and state", "for equilibrium <b>I</b>, and state")
bold(5, "a bidentate ligand, V, is formed", "a bidentate ligand, <b>V</b>, is formed")
bold(5, "Draw the structure of V and on", "Draw the structure of <b>V</b> and on")
bold(5, "(b)(ii)</span> V reacts with aqueous", "(b)(ii)</span> <b>V</b> reacts with aqueous")
bold(5, "a colourless solution W, which", "a colourless solution <b>W</b>, which")
bold(5, "a white solid X, containing", "a white solid <b>X</b>, containing")
bold(5, "copper in W and X are the same", "copper in <b>W</b> and <b>X</b> are the same")
bold(5, "complex ion in W and the solid compound X.", "complex ion in <b>W</b> and the solid compound <b>X</b>.")
bold(5, "An organic compound Y, a selective", "An organic compound <b>Y</b>, a selective")
bold(5, "structure of compound Y.", "structure of compound <b>Y</b>.")
bold(5, "added to compound Z in stage II", "added to compound <b>Z</b> in stage II")

# ------------------------------------------------ user rulings (2026-10-18)
both(5, "relevent", "relevant")
both(3, r"1\.00 x 10", "1.00 × 10", rx=True)
sub(5, "]<sup>2+</sup>complex ion", "]<sup>2+</sup> complex ion")
sub(5, "]2+complex ion", "]2+ complex ion", field="content_text")
sub(1, "<sub>3,</sub>", "<sub>3</sub>,", count=2)
sub(4, "HC<i class=\"el\">l</i> acid", "hydrochloric acid")
sub(4, "HCl acid", "hydrochloric acid", field="content_text")
both(4, "Fig.4.2", "Fig. 4.2")
both(5, "A 0.155 g of impure sample", "A 0.155 g impure sample")
sub(5, "copper in <b>W</b> and <b>X</b> are the same", "copper in <b>W</b> and <b>X</b> is the same")
sub(5, "copper in W and X are the same", "copper in W and X is the same", field="content_text")
both(5, "precursors or synthetic intermediate to", "precursors or synthetic intermediates to")
both(2, "reacts with the presence of NaOH", "reacts with NaOH")
both(3, "structure formula", "structural formula")
# hyphen-minus -> U+2212 (the P2 ruling): exponents and the sign of -42
sub(2, "<sup>-3</sup>", "<sup>−3</sup>")
sub(3, "<sup>-3</sup>", "<sup>−3</sup>")
sub(2, "mol dm-3.", "mol dm−3.", field="content_text")
sub(3, "mol dm-3 N", "mol dm−3 N", field="content_text")
sub(1, "<td>-42</td>", "<td>−42</td>")
sub(1, "CH3CH2CH3-42", "CH3CH2CH3−42", field="content_text")

# ---------------------------------------------------------- the asset plan
def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


def drop(qn, slot, why):
    x = get(qn, slot)
    PLAN.remove(x)
    LOG.append("asset plan: Q%d slot %s dropped (%s)" % (qn, slot, why))


drop(2, "b3", "Fig. 2.1 is ONE snip (b); Fig. 2.2 is b2")
drop(2, "d", "Nernst fraction typed")
drop(2, "d2", "Nernst fraction typed")
drop(2, "e2", "Table 2.1 is ONE snip (e)")
drop(2, "e3", "Table 2.1 is ONE snip (e)")
drop(5, "aii", "1/1000 typed")

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
        x["n_refs"] = 1
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 21, len(PLAN)

# no leftover soft <br> other than the two intended label breaks; balanced markup
for qn in Q:
    h = Q[qn]["content_html"]
    assert h.count("<br>") == {1: 2, 5: 4}.get(qn, 0), "Q%d <br>: %d" % (qn, h.count("<br>"))
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "<u>" not in h and KEEP_BR not in h
assert [Q[k]["marks"] for k in sorted(Q)] == [19, 21, 20, 20, 20]
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
