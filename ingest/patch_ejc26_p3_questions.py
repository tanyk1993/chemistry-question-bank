"""EJC 2026 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_ejc26_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `ejc26_p3_prep` (question-only copy of the school's question + solutions
docx: 55 answer text boxes removed, the Fig 1.2 axes kept, the second Q4 "(b)"
relabelled "(c)"; cover dropped, auto-numbers typed, split labels merged) ->
`extract_parts` (flow shape; --first-page 2; school EJC, level H2, paper P3, year
2026; run against the Word PDF with the answer-coloured text redacted) -> THIS
script -> gen_parts_migration. The user snips every printed picture: 9 images
(Q1 b, d, d2, dv; Q2 a; Q4 b, biii; Q5 b, bv). The extractor's own plan (12) is cut
to those 9.

Every `sub()` asserts its match count. What is patched, and why:
 corrections (extractor side): LEADIN_MOVES for 10 lead-in passages printed between
   a part's [n] and the next label. Two lead-ins carry a figure and the mechanism
   refuses those, so they are moved here: Q4(b)(iii) -> (b)(iv) (M and N) and
   Q5(b)(v) -> (b)(vi) (methyl orange).
 Q1 (c): the equation's arrow carries "Cu2+ / Cu+(aq)" (a MathType object, no text
      layer): typed as a label stacked over a ruled arrow (inline styles only, the
      DHS 2026 P1 Q24 pattern).  (d)(i): the school's blank gap after "the
      resonance" is filled with "structures" (user ruling).
 Q2 (b)(iii): the 5/2 and 1/2 in equations (2) and (4) are MathType objects: typed
      as span.frac.  The energy-cycle opening line 2C(s) + N2(g) -> (CN)2(g) with
      dHf over the arrow is typed the same way as Q1(c).  Marks 19.
 Q3 (d): CO3 2- in equation 4 was extracted as "CO2- 3".  (g): Table 3.2 rebuilt
      (the extractor mis-nests <p> across its cells).
 Q4 (c): "SO2- 4" -> SO4 2-; the serif I in NaIO3 is plain.  Soft <br> -> space.
 Q5: three "BLANK PAGE" lines removed.
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
PL = '<sup class="pl-sym">\u29b5</sup>'


def over_arrow(label, min_w):
    """A label stacked over a ruled arrow; inline styles only (no index.html change)."""
    return ('<span style="display:inline-flex;flex-direction:column;align-items:center;'
            'vertical-align:middle;margin:0 .35em;min-width:%s">'
            '<span style="font-size:.8em;line-height:1.2;white-space:nowrap">%s</span>'
            '<span style="display:flex;align-items:center;width:100%%">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.75em;margin-left:-.3em;line-height:1">&#9654;</span>'
            '</span></span>') % (min_w, label)


def frac(a, b):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (a, b)


# ======================================================================= Q1
sub(1, r"(\xbdO<sub>2</sub>\(aq\))   (C<sub>6</sub>H<sub>6</sub>O<sub>6</sub>\(aq\))",
    "\\1" + over_arrow("Cu<sup>2+</sup> / Cu<sup>+</sup>(aq)", "10em").replace("\\", "\\\\") + "\\2", rx=True)
sub(1, "\xbdO2(aq)   C6H6O6(aq)", "\xbdO2(aq) Cu2+ / Cu+(aq) \u2192 C6H6O6(aq)", field="content_text")

both(1, "Using the resonance \t\t of the conjugate bases", "Using the resonance structures of the conjugate bases")
LOG.append("Q1(d)(i): the school's blank gap after 'the resonance' filled with 'structures' (user ruling 2026-10-31)")

# ======================================================================= Q2
_l2 = ('<p>(2)  C<sub>2</sub>H<sub>2</sub>(g) +</p>\n<div class="fig">figure</div>\n<p>O<sub>2</sub>(g)')
sub(2, _l2, '<p>(2)  C<sub>2</sub>H<sub>2</sub>(g) + ' + frac(5, 2) + 'O<sub>2</sub>(g)')
_l4 = ('<p>(4)  H<sub>2</sub>(g) +</p>\n<div class="fig">figure</div>\n<p>O<sub>2</sub>(g)')
sub(2, _l4, '<p>(4)  H<sub>2</sub>(g) + ' + frac(1, 2) + 'O<sub>2</sub>(g)')
_cyc = ('2C(s) + N<sub>2</sub>(g)' + over_arrow('\u2206<i>H</i>' + PL.replace('<sup', '<sup') + '<sub>f</sub>', "7em")
        + '(CN)<sub>2</sub>(g)')
sub(2, r'(<span class="mk">\[3\]</span></p>)\n<div class="fig">figure</div></div>',
    '\\1\n<p class="c">' + _cyc.replace("\\", "\\\\") + '</p></div>', rx=True)
sub(2, "(2)  C2H2(g) + O2(g)", "(2)  C2H2(g) + 5/2 O2(g)", field="content_text")
sub(2, "(4)  H2(g) + O2(g)", "(4)  H2(g) + 1/2 O2(g)", field="content_text")
sub(2, "\n [3] (c) Consider", "\n [3] 2C(s) + N2(g) \u2206H\u29b5f \u2192 (CN)2(g) (c) Consider", field="content_text")

# (b)(iii): the four equations and their enthalpy changes sit in a borderless 4 x 3 table
# (label | equation | enthalpy change) so the lines read less cluttered.
_TD = "padding:.3em 1.2em .3em 0;vertical-align:middle;text-align:left"
_rows = []
_h = Q[2]["content_html"]
for _n in "1234":
    _m = re.search(r"<p>[\t ]*\(" + _n + r"\)  (.*?)[\t ]*(\u2206<i>H</i>.*?)</p>\n?", _h, flags=re.S)
    assert _m, "Q2 (b)(iii) equation %s not found" % _n
    _rows.append((_n, _m.group(1), _m.group(2), _m.group(0)))
for _n, _eq, _dh, _whole in _rows:
    assert _h.count(_whole) == 1
_first = _rows[0][3]
_table = ('<table style="border-collapse:collapse;margin:.5em 0 .5em 1em;border:0">'
          + "".join('<tr><td style="%s">(%s)</td><td style="%s">%s</td><td style="%s;white-space:nowrap">%s</td></tr>'
                    % (_TD, n, _TD, eq, _TD, dh) for n, eq, dh, _ in _rows)
          + '</table>\n')
for _n, _eq, _dh, _whole in _rows:
    _h = _h.replace(_whole, _table if _whole == _first else "")
Q[2]["content_html"] = _h
LOG.append("Q2(b)(iii): 4 equation lines -> borderless 4x3 table")

# The standard-state sign stacked over the subscript (house markup, as CJC 2026 P1 Q8; the
# live `.stem .stk.post` rule): a plain <sup>⦵</sup><sub>f</sub> renders as a cramped, offset glyph.
_n_stk = len(re.findall(r'<sup class="pl-sym">\u29b5</sup><sub>([a-z]+)</sub>', Q[2]["content_html"]))
Q[2]["content_html"] = re.sub(r'<sup class="pl-sym">\u29b5</sup><sub>([a-z]+)</sub>',
    '<span class="stk post"><span><span class="pl-sym">\u29b5</span></span><span>\\1</span></span>',
    Q[2]["content_html"])
assert _n_stk == 5, _n_stk          # (1)-(4) rows + the cycle's arrow label
LOG.append("Q2(b)(iii): %d standard-state signs -> stacked house markup" % _n_stk)

# ======================================================================= Q3
sub(3, "CO2\u2013 3 (aq)", "CO<sub>3</sub><sup>2\u2212</sup>(aq)")
_t32 = (
    '<table class="qt"><tr><td>test</td><td>reaction</td><td>organic compounds formed</td><td>other information</td></tr>'
    '<tr><td>1</td><td><b>A</b> with 2,4-DNPH</td><td>orange precipitate</td><td></td></tr>'
    '<tr><td>2</td><td><b>A</b> with Tollens\u2019 reagent</td><td>no reaction</td><td></td></tr>'
    '<tr><td>3</td><td><b>A</b> with excess H<sub>2</sub> / Ni</td><td><b>B</b>, C<sub>10</sub>H<sub>20</sub>O</td>'
    '<td><b>B</b> is symmetrical and contains two chiral centres</td></tr>'
    '<tr><td>4</td><td><b>A</b> with hot acidified KMnO<sub>4</sub></td>'
    '<td><p><b>C</b> (has 3 carbon atoms)</p><p><b>D</b>, C<sub>7</sub>H<sub>12</sub>O<sub>2</sub></p></td>'
    '<td><p><b>C</b> reacts completely with Na<sub>2</sub>CO<sub>3</sub> in a 1:1 mole ratio</p>'
    '<p><b>C</b> also reacts with 2,4-DNPH</p></td></tr>'
    '<tr><td>5</td><td><b>D</b> with alkaline I<sub>2</sub>(aq) followed by acidification</td>'
    '<td><p>yellow precipitate <b>E</b></p><p><b>F</b>, C<sub>5</sub>H<sub>8</sub>O<sub>4</sub></p></td><td></td></tr>'
    '<tr><td>6</td><td><b>F</b> with LiA<i class="el">l</i>H<sub>4</sub></td><td><b>G</b>, C<sub>5</sub>H<sub>12</sub>O<sub>2</sub></td><td></td></tr>'
    '<tr><td>7</td><td><b>G</b> with hot concentrated H<sub>3</sub>PO<sub>4</sub></td><td>no reaction</td><td></td></tr></table>')
sub(3, r'<table class="qt"><tr><td>test</td>.*?</table></p>', _t32.replace("\\", "\\\\"), rx=True)

# ======================================================================= Q4
# lead-in that carries a figure (the declared mechanism refuses these)
sub(4, r'(<span class="mk">\[2\]</span></p>)\n(<p>\t\tIn another chemical reaction[^\n]*</p>\n<div class="fig">figure</div>)</div>'
       r'\n(<div class="qpart"><span class="pl">\(b\)\(iv\)</span>) (<b>)',
    "\\1</div>\n\\3 \\2\n\\4", rx=True)
sub(4, '(b)(iv)</span> <p>\t\tIn another', '(b)(iv)</span> In another')
sub(4, '<b>N</b>.</p>\n<div class="fig">figure</div>', '<b>N</b>.\n<div class="fig">figure</div>')
sub(4, '<span class="sr">I</span>', "I")
sub(4, "SO2\u2013 4.", "SO<sub>4</sub><sup>2\u2212</sup>.")
sub(4, "SO2\u2013 4.", "SO42\u2212.", field="content_text")

# ======================================================================= Q5
sub(5, r'(<span class="mk">\[1\]</span>)\n(<p>The structure of the deprotonated form of methyl orange is as shown\.</p>\n<div class="fig">figure</div>)</div>'
       r'\n(<div class="qpart"><span class="pl">\(b\)\(vi\)</span>) ',
    "\\1</div>\n\\3 \\2\n", rx=True)
sub(5, '(b)(vi)</span> <p>The structure of the deprotonated form of methyl orange is as shown.</p>\n<div class="fig">figure</div>',
    '(b)(vi)</span> The structure of the deprotonated form of methyl orange is as shown.\n<div class="fig">figure</div>')
sub(5, '\n<p class="c"><b>BLANK PAGE</b></p>', "", count=3)
sub(5, "\nBLANK PAGE", "", field="content_text", count=3)

# generic: a soft <br> -> space
for qn in sorted(Q):
    s = Q[qn]["content_html"]
    n = s.count("<br>")
    Q[qn]["content_html"] = re.sub(r"<br>\s*", " ", s)
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


for _s in ("biii", "biii2", "biii3"):
    drop(2, _s, "typed (5/2 and 1/2 fractions; the cycle's opening line)")

for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
assert len(PLAN) == 9, len(PLAN)

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
assert [Q[k]["marks"] for k in sorted(Q)] == [19, 19, 17, 20, 20]
for qn in Q:
    assert sum(p["marks"] or 0 for p in Q[qn]["parts"]) == Q[qn]["marks"], qn

for qn in Q:
    Q[qn]["section"] = None

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets" % (len(Q), len(PLAN)))
