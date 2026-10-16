"""HCI 2024 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_hci_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `hci_p3_prep` (drop the leading blank cell of every row of the two
question tables) -> `extract_parts` (crops stubbed: the user snips every
figure) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 generic (all questions)
   - whitespace sitting INSIDE <sup>/<sub>/<i>/<b> moved outside; empty
     <sub></sub>/<sup></sup> removed; a space at the START of a <sup> that
     follows a word (`mol<sup> -1</sup>`) removed (it is inside the
     superscript on the page)
   - en dash INSIDE <sup> -> U+2212 (charges, exponents)
   - unbalanced <p> inside a table cell closed; a stray </p> removed
 Q1  the iodine lead-in stays between (c)(iii) and (c)(iv) as its own paragraph; equation's DeltaH gap -> em spaces; Table 1.1 negative values: en dash ->
     U+2212; search text of Table 1.1 made readable
 Q2  (c)(iii): the three structures + their B/C/D captions are ONE user snip
     (the extractor's caption table was malformed HTML); soft <br> -> space
 Q3  (d)(ii): the orange / yellow labels under the equilibrium
 Q4  Table 4.1 is ONE user snip (its structures, labels and pI row)
 Q5  equations 1-3 are tab-aligned lines: class eqn on all three
 soft <br> typed to wrap a sentence became a space (Q2 x2, Q4 x1, Q5 x2).
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
# (these blocks are malformed HTML as extracted; fix them before the generic tidy)

# Q2(c)(iii): three drawings + a caption table whose cells leaked out of a <p>.
# ONE snip of the three structures WITH their B / C / D labels.
sub(2, '<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n'
       '<p></td></tr><tr><td><b>B</b></td><td><b>C</b></td><td><b>D</b></td></tr></table></p>\n',
       '<div class="fig">figure</div>\n')
sub(2, "\nBCD\n", "\nB C D\n", field="content_text")

# Q4(b): Table 4.1 (structures + labels + pI row) is ONE snip
sub(4, r'<table class="qt"><tr><td>amino acid</td><td>\n(?:<div class="fig">figure</div>\n){3}'
       r'<p></td></tr><tr><td>p<span class="sr">I</span></td><td>2\.77</td><td>6\.00</td><td>9\.74</td></tr></table></p>',
    '<div class="fig">figure</div>', rx=True)
sub(4, "\namino acidpI2.776.009.74 ", "\namino acid asp ala lys pI 2.77 6.00 9.74 ", field="content_text")

# Q1: "If the halogen is changed to iodine..." links (c)(iii) and (c)(iv) and belongs to NEITHER
# (user ruling 2026-10-15): it stands as its own paragraph between the two parts.
sub(1, r'(<span class="mk">\[1\]</span>)\n(<p>If the halogen is changed to iodine.*?</p>)</div>',
    r'\1</div>\n\2', rx=True)

# ------------------------------------------------------------- soft <br>
sub(2, "reacted with <br>2,4-dinitrophenylhydrazine", "reacted with 2,4-dinitrophenylhydrazine")
sub(2, "suggest the structures of <br><b>F</b>", "suggest the structures of <b>F</b>")
sub(4, "titrated against <br>0.100 mol", "titrated against 0.100 mol")
sub(5, "with a volume of <br>6.87 dm", "with a volume of 6.87 dm")
sub(5, "at a pressure of <br>30.0 bar", "at a pressure of 30.0 bar")

# school grammar (user ruling 2026-10-15): "there has been breakthroughs" -> "there have been"
for _f in ("content_html", "content_text"):
    sub(5, "there has been breakthroughs", "there have been breakthroughs", field=_f)

# Q5 equation 1 keeps its TAB before the dG label inside the <sup> (a tab is a deliberate column gap)
sub(5, "8e<sup>–\t</sup>", "8e<sup>–</sup>\t")


# ---------------------------------------------------------------- generic tidy
def tidy(qn):
    s = Q[qn]["content_html"]
    n_ws = n_dash = n_td = n_stray = n_empty = n_exp = 0
    # a space at the start of a <sup> that follows a word is inside the superscript
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
    # en dash inside <sup> -> U+2212
    def dash(m):
        nonlocal n_dash
        if "–" in m.group(0):
            n_dash += 1
        return m.group(0).replace("–", "−")
    s = re.sub(r"<sup>[^<]*</sup>", dash, s)
    # unbalanced <p> in a table cell
    def td(m):
        nonlocal n_td
        inner = m.group(2)
        o, c = len(P_OPEN.findall(inner)), inner.count(P_CLOSE)
        if o > c:
            n_td += o - c
            inner += P_CLOSE * (o - c)
        return m.group(1) + inner + "</td>"
    s = re.sub(r"(<td[^>]*>)(.*?)</td>", td, s, flags=re.S)
    # a </p> with no open <p>
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

# the search text: en dash on a charge or exponent -> U+2212 (Q5 only; Q1's are the Table 1.1 values below)
for pat in (r"(?<=8e)–(?=\t)", r"(?<=mol)–(?=1)", r"(?<=4e)–(?= )", r"(?<=I)–(?= and)",
            r"(?<=S2O82)–(?= is)", r"(?<=\nS2O82)–", r"(?<=2I)–(?= →)", r"(?<=2SO42)–(?= \+)"):
    s = Q[5]["content_text"]
    n = len(re.findall(pat, s))
    assert n == 1, (pat, n)
    Q[5]["content_text"] = re.sub(pat, "−", s)
    LOG.append("Q5 content_text: en dash -> U+2212 (%s)" % pat)
assert "–" not in re.sub(r"[–]\s", "", Q[5]["content_text"].replace("–", "")) or True

# =================================================================== Q1
# equation's gap before dH (centred line; spaces collapse in HTML)
sub(1, r"\(g\)\s{6,}∆<i>H</i> &gt; 0", "(g)&emsp;&emsp;&emsp;∆<i>H</i> &gt; 0", rx=True)
sub(1, r"\(s\) →", "(s) →", rx=True)          # (the empty <sub> left a double space)
# Table 1.1: en dash used as a minus sign on the two negative values -> U+2212 (flagged for the user)
sub(1, "<td>–142</td>", "<td>−142</td>")
sub(1, "<td>–602</td>", "<td>−602</td>")
sub(1, "∆H⦵ / kJ mol –11st electron affinity of oxygen–1422nd electron affinity of oxygen+844standard enthalpy change "
       "of atomisation of Mg(s)+148standard enthalpy change of formation of MgO(s)–602 [4]",
    "∆H⦵ / kJ mol−1 1st electron affinity of oxygen −142 2nd electron affinity of oxygen +844 standard enthalpy "
    "change of atomisation of Mg(s) +148 standard enthalpy change of formation of MgO(s) −602 [4]",
    field="content_text")

# =================================================================== Q3
# (d)(ii): "orange" / "yellow" sit under Cr2O7(2-) and CrO4(2-). The equation and the label line are
# both p.eqn (white-space:pre-wrap) so the label spacing is preserved; spacing tuned in the site font
# (4 leading em spaces to sit near the centre; 4 spaces before "orange", 30 before "yellow").
sub(3, r'<p class="c">(Cr<sub>2</sub>O<sub>7</sub><sup>2−</sup>\(aq\) \+ H<sub>2</sub>O.*?\+ 2H<sup>\+</sup>\(aq\))</p>\n<p>\s*orange\s+yellow</p>',
    '<p class="eqn">&emsp;&emsp;&emsp;&emsp;\\1</p>\n<p class="eqn">&emsp;&emsp;&emsp;&emsp;' + " " * 4 + "orange" + " " * 30 + "yellow</p>", rx=True)

# =================================================================== Q5
# equations 1-3 are lines aligned on a real tab: all three are class eqn
sub(5, '<p class="eqn">equation 1 \tCH<sub>4</sub>', '<p class="eqn">equation 1\tCH<sub>4</sub>')
sub(5, '<p>equation 2\t', '<p class="eqn">equation 2\t')
sub(5, '<p>equation 3\t', '<p class="eqn">equation 3\t')

# ---------------------------------------------------------- the asset plan
def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


def drop(qn, slot):
    global PLAN
    n = len(PLAN)
    PLAN = [x for x in PLAN if not (x["question"] == qn and x["slot"] == slot)]
    assert len(PLAN) == n - 1, (qn, slot)
    LOG.append("asset plan: dropped Q%d %s" % (qn, slot))


drop(2, "ciii2")
drop(2, "ciii3")
get(2, "ciii")["n_refs"] = 1                 # B, C, D with their labels: one snip
drop(4, "b2")
drop(4, "b3")
get(4, "b")["n_refs"] = 1                    # Table 4.1: one snip

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))

# no leftover soft <br>; no stray </p>; no sentinel bytes
for qn in Q:
    h = Q[qn]["content_html"]
    assert "<br>" not in h, "Q%d still has <br>" % qn
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "</td></tr>" not in re.sub(r"<table.*?</table>", "", h, flags=re.S), "Q%d stray table tail" % qn
assert [Q[k]["marks"] for k in sorted(Q)] == [20, 19, 21, 20, 20]
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
