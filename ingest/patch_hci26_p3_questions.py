"""HCI 2026 H2 P3 (9476/03) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QP.docx -d unz
  python3 -m ingest.hci26_p3_prep unz unz_prep
  python3 -m ingest.extract_parts unz_prep QP_word.pdf out \
      --school HCI --level H2 --paper P3 --year 2026 --last-page 21
  python3 -m ingest.patch_hci26_p3_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school HCI --year 2026 --paper 3 --level H2

Shape: SEAB table shape with ONE blank leading cell per row (HCI 2026 P2 family)
and, in two tables, a trailing hairline column; `hci26_p3_prep` squares them up.
Answers are NOT read at this stage.

Marks as ingested: Q1 21, Q2 14, Q3 20, Q4 20, Q5 20 = 95 (75 as sat: Section B
is "answer one"), the same convention as the other P3s.

FIGURES (user snips, 10, all block figures; the printed captions "Figure 1.1 /
2.1" stay typed in the stem, so those snips carry the drawing only; Figure 3.1's
caption sits between the energy diagram and the two axes boxes, so that snip
carries the whole band including the caption):
  Q1(c)      Figure 1.1: epoxide + organocuprate -> alcohol A (labels in the snip)
  Q1(c)(ii)  structure of alcohol B (label "alcohol B" in the snip)
  Q2 intro   structure of cholamine halide (with X-)
  Q2(e)      Figure 2.1: methods A and B (labels in the snip)
  Q3(a)(ii)  Figure 3.1: energy-level diagram + the two blank axes boxes
  Q3(b)      HEA + dashed arrow + empty "polyHEA" box
  Q3(c)      RAFT equilibria for step D (X. + RAFT agent <=> ... <=> ... + Y.)
  Q3(c)(iii) radicals J and K (labels in the snip)
  Q3(c)(v)   the same equilibria replicated (no RAFT-agent label)
  Q4(b)(iv)  urea -> compound Q + 3 NH3 scheme

DECLARED FIXES: lead-ins filed under the wrong part (Q3 Figure 3.1 passage
(a)(i)->(a)(ii); Q4 "Chlorine can react with ..." (b)(iii)->(b)(iv)); step
labels A-D of Q3(c) (the extractor put them in the roman slot and dropped
them); stray table fragments around Figure 3.1; [n]/[Total] lines left as
paragraphs on Q2/Q4/Q5; marks of Q2 (e)(iii), Q4 (d), Q5 (d)(iv); minus signs /
bond hyphens (ruling 2026-11-01); d-orbital names set with subscripts.
School typos: ruled by the user 2026-11-03, applied by default (--no-typos to skip).
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
APPLY_TYPOS = "--no-typos" not in sys.argv
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
LOG = []
MINUS = "−"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, h_old, h_new, t_old=None, t_new=None, **kw):
    sub(qn, h_old, h_new, "content_html", **kw)
    sub(qn, h_old if t_old is None else t_old, h_new if t_new is None else t_new,
        "content_text", **kw)


# ---- zero-width spaces (Q4 equations) --------------------------------------------------
for r in Q.values():
    for f in ("content_html", "content_text"):
        r[f] = r[f].replace("​", "")

# ---- Q1 -------------------------------------------------------------------------------
# Ksp table: stray empty subscripts
sub(1, "10<sub> </sub><sup>–19</sup>", "10<sup>–19</sup>")
sub(1, "10<sub> </sub><sup>–39</sup>", "10<sup>–39</sup>")
sub(1, "× 10 –19", "× 10–19", "content_text")
sub(1, "× 10 –39", "× 10–39", "content_text")
# Figure 1.1 lead-in / caption
sub(1, "An example is shown in <br>Figure 1.1.  \n", "An example is shown in Figure 1.1.\n")
sub(1, '<p class="c"><b>                                          Figure 1.1</b></p>',
    '<p class="c"><b>Figure 1.1</b></p>')
sub(1, "An example is shown in Figure 1.1.  \n\n                                          Figure 1.1 (c)(i)",
    "An example is shown in Figure 1.1.\nFigure 1.1 (c)(i)", "content_text")
# (d)(i): hand-aligned gap before the mark
sub(1, r"in <b>F</b>\.\s+\t<span", "in <b>F</b>. <span", rx=True)
sub(1, r"present in F\.\s+\t\[2\]", "present in F. [2]", "content_text", rx=True)

# ---- Q2 -------------------------------------------------------------------------------
sub(2, "<p>cholamine halide, C<sub>5</sub>H<sub>15</sub>N<sub>2</sub>X\t(X is a Group 17 element)</p>",
    '<p class="eqn">cholamine halide, C<sub>5</sub>H<sub>15</sub>N<sub>2</sub>X\t(X is a Group 17 element)</p>')
sub(2, "<i><span class=\"sr\">x</span></i>", "<i>x</i>", count=2)
sub(2, "<i><span class=\"sr\">y</span></i>", "<i>y</i>", count=2)
sub(2, "chloride and<br>1 mole of compound", "chloride and 1 mole of compound")
sub(2, "chloride and1 mole of compound", "chloride and 1 mole of compound", "content_text")
sub(2, "<p>Suggest the structure of <b>Z</b>.</p>\n<p>[1]</p>\n<p>[Total: 14]</p></div>",
    '<p>Suggest the structure of <b>Z</b>. <span class="mk">[1]</span></p></div>')
sub(2, "Suggest the structure of Z.\n[1]\n[Total: 14]", "Suggest the structure of Z. [1]\n[Total: 14]",
    "content_text")
Q[2]["marks"] = 14
for p in Q[2]["parts"]:
    if p["label"] == "(e)(iii)":
        assert p["marks"] is None
        p["marks"] = 1

# ---- Q3 -------------------------------------------------------------------------------
# Figure 3.1 passage: filed under (a)(i), belongs to (a)(ii); the extractor also left
# the closing tags of the two axes boxes (and the caption) as stray HTML.
A_OLD = ('<span class="mk">[2]</span>\n<p>The splitting of degenerate d-orbitals due to a <b>linear</b> ligand field is shown in Figure 3.1.</p>\n'
         '<div class="fig">figure</div>\n'
         '<p><b>Figure 3.1</b></td><td><table class="qt"><tr><td></p>\n<p>dz<sup>2</sup></td></tr></table></td>'
         '<td><table class="qt"><tr><td></p>\n<p>dyz</td></tr></table></td></tr></table></p></div>\n'
         '<div class="qpart"><span class="pl">(a)(ii)</span> Sketch the shape of a dz<sup>2</sup> and a dyz orbital '
         'on the axes to the right of Figure 3.1.\t<span class="mk">[2]</span></div>')
A_NEW = ('<span class="mk">[2]</span></div>\n'
         '<div class="qpart"><span class="pl">(a)(ii)</span> The splitting of degenerate d-orbitals due to a <b>linear</b> ligand field is shown in Figure 3.1.\n'
         '<div class="fig">figure</div>\n'
         '<p>Sketch the shape of a dz<sup>2</sup> and a dyz orbital on the axes to the right of Figure 3.1. '
         '<span class="mk">[2]</span></p></div>')
sub(3, A_OLD, A_NEW)
sub(3, "[2]\nThe splitting of degenerate d-orbitals due to a linear ligand field is shown in Figure 3.1.\n\n"
       "Figure 3.1\ndz2\ndyz (a)(ii) Sketch the shape of a dz2 and a dyz orbital on the axes to the right of "
       "Figure 3.1.\t[2] (a)(iii)",
    "[2] (a)(ii) The splitting of degenerate d-orbitals due to a linear ligand field is shown in Figure 3.1.\n"
    "Sketch the shape of a dz2 and a dyz orbital on the axes to the right of Figure 3.1. [2] (a)(iii)",
    "content_text")
# d-orbital names with subscripts (html only; text stays plain)
h = Q[3]["content_html"]
h = h.replace("dz<sup>2</sup>", "d<sub>z²</sub>")
h = h.replace("dx<sup>2</sup>–y<sup>2</sup>", "d<sub>x²" + MINUS + "y²</sub>")
for o in ("xz", "yz", "xy"):
    h = re.sub(r"\bd%s\b" % o, "d<sub>%s</sub>" % o, h)
Q[3]["content_html"] = h
LOG.append("Q3: d-orbital names subscripted")
# Q3(c): step labels A-D (roman-slot cells the parser dropped)
for lab, start in (("A", "RO–OH reacts with Fe<sup>2+</sup>"),
                   ("B", "RO● reacts with HEA to produce"),
                   ("C", "The polymer radical <b>X</b>● is produced"),
                   ("D", "<b>X</b>● reacts with a RAFT agent")):
    sub(3, "<p>" + start, '<p><b>%s</b>&emsp;%s' % (lab, start))
for lab, start in (("A", "RO–OH reacts with Fe2+"), ("B", "RO● reacts with HEA to produce"),
                   ("C", "The polymer radical X● is produced"), ("D", "X● reacts with a RAFT agent")):
    sub(3, "\n" + start, "\n%s %s" % (lab, start), "content_text")
# bond hyphen in RO-OH (ruling 2026-11-01: plain hyphen in bonds)
sub(3, "RO–OH", "RO-OH", count=1)
sub(3, "RO–OH", "RO-OH", "content_text", count=1)
sub(3, "dx2–y2", "dx2" + MINUS + "y2", "content_text")

# ---- Q4 -------------------------------------------------------------------------------
sub(4, "∆<i>H</i> &lt; 0", "∆<i>H</i> &lt; 0")      # html entity stays
sub(4, "∆H &lt; 0", "∆H < 0", "content_text")
sub(4, '<p class="c">N<sub>2</sub>(g)', '<p class="c eqn">N<sub>2</sub>(g)')
# lead-in "Chlorine can react ..." printed after (b)(iii)'s [1], before (b)(iv)
sub(4, '<span class="mk">[1]</span>\n<p>Chlorine can react with other nitrogen-containing compounds.</p></div>\n'
       '<div class="qpart"><span class="pl">(b)(iv)</span> In the initial stages when chlorine gas was deployed, '
       'soldiers often used urine-soaked cloths to minimise the effects of chlorine.\n',
    '<span class="mk">[1]</span></div>\n<div class="qpart"><span class="pl">(b)(iv)</span> '
    'Chlorine can react with other nitrogen-containing compounds.\n'
    '<p>In the initial stages when chlorine gas was deployed, soldiers often used urine-soaked cloths to '
    'minimise the effects of chlorine.</p>\n')
sub(4, "trench warfare. [1]\nChlorine can react with other nitrogen-containing compounds. (b)(iv) In the initial "
       "stages when chlorine gas was deployed, soldiers often used urine-soaked cloths to minimise the effects of "
       "chlorine.\n",
    "trench warfare. [1] (b)(iv) Chlorine can react with other nitrogen-containing compounds.\nIn the initial "
    "stages when chlorine gas was deployed, soldiers often used urine-soaked cloths to minimise the effects of "
    "chlorine.\n", "content_text")
# (c)(i): O-Cl bond, stray spaces
sub(4, 'O–C<i class="el">l  </i>in<i><span class="sr"> </span></i>HOC<i class="el">l </i>is',
    'O-C<i class="el">l</i> in HOC<i class="el">l</i> is')
sub(4, "O–Cl  in HOCl is", "O-Cl in HOCl is", "content_text")
# hand-aligned equation lines (keep the typed gap before the label)
sub(4, '<p>NH<sub>3</sub> + HOC<i class="el">l</i>', '<p class="eqn">NH<sub>3</sub> + HOC<i class="el">l</i>')
sub(4, '<p>NH<sub>3</sub>(g) + 2C<i class="el">l</i><sub>2</sub>(g)', '<p class="eqn">NH<sub>3</sub>(g) + 2C<i class="el">l</i><sub>2</sub>(g)')
# the trailing [3] / [Total: 20] paragraphs
sub(4, 'in your answer.\n<p>[3]</p>\n<p>[Total: 20]</p></div>',
    'in your answer. <span class="mk">[3]</span></div>')
sub(4, "in your answer.\n[3]\n[Total: 20]", "in your answer. [3]\n[Total: 20]", "content_text")
Q[4]["marks"] = 20
for p in Q[4]["parts"]:
    if p["label"] == "(d)":
        assert p["marks"] is None
        p["marks"] = 3

# ---- Q5 -------------------------------------------------------------------------------
sub(5, '<sub>3.</sub> <span class="mk">[2]</span>', '<sub>3</sub>. <span class="mk">[2]</span>')
sub(5, '<sub>3 </sub>with water.', '<sub>3</sub> with water.')
sub(5, "up to       2500 K", "up to 2500 K")
sub(5, "up to       2500 K", "up to 2500 K", "content_text")
sub(5, "<p>Fe<sub>2</sub>O<sub>3</sub>(s) + 2A", '<p class="eqn">Fe<sub>2</sub>O<sub>3</sub>(s) + 2A')
sub(5, 'copper<span class="sr">(</span>II) oxide.', 'copper(<span class="sr">II</span>) oxide.')
sub(5, "replacing iron(III) oxide in reaction 5.1", 'replacing iron(<span class="sr">III</span>) oxide in reaction 5.1')
sub(5, "you might make.</p>\n<p>[3]</p>\n<p>[Total: 20]</p></div>",
    'you might make. <span class="mk">[3]</span></p></div>')
sub(5, "you might make.\n[3]\n[Total: 20]", "you might make. [3]\n[Total: 20]", "content_text")
Q[5]["marks"] = 20
for p in Q[5]["parts"]:
    if p["label"] == "(d)(iv)":
        assert p["marks"] is None
        p["marks"] = 3

# ---- held: school typos (apply with --typos after the user rules) ---------------------------
if APPLY_TYPOS:
    both(3, "polymersiation", "polymerisation")
    both(4, "industralised", "industrialised", count=2)
    both(4, "introduced into in a sealed vessel", "introduced into a sealed vessel")

# ---- dashes (ruling 2026-11-01): minus sign for charges / exponents / negative numbers ----------------------
def _dash(s):
    s = re.sub(r"<(sup|sub)>([^<]*?)\s+</\1>", lambda m: "<%s>%s</%s> " % (m.group(1), m.group(2), m.group(1)), s)
    return s.replace("–", MINUS)


CONTEXT = []
for qn, r in Q.items():
    for f in ("content_html", "content_text"):
        for m in re.finditer("–", r[f]):
            CONTEXT.append("Q%d %s: %r" % (qn, f[8:], r[f][max(0, m.start() - 12): m.end() + 8]))
        r[f] = _dash(r[f])
    r["content_html"] = re.sub(r"mol dm<sup>[-−]3</sup>", "mol dm<sup>−3</sup>", r["content_html"])

# ---- asset plan (final) ----------------------------------------------------------------------
def A(q, slot, part):
    return {"question": q, "part": part, "slot": slot, "ordinal": 0,
            "storage_path": "HCI_H2_P3_Q%d_%s_2026.png" % (q, slot), "n_refs": 1}


PLAN = [A(1, "c", "(c)"), A(1, "cii", "(c)(ii)"),
        A(2, "intro", None), A(2, "e", "(e)"),
        A(3, "aii", "(a)(ii)"), A(3, "b", "(b)"), A(3, "c", "(c)"), A(3, "ciii", "(c)(iii)"), A(3, "cv", "(c)(v)"),
        A(4, "biv", "(b)(iv)")]
seen = {}
for p in PLAN:
    seen[p["question"]] = seen.get(p["question"], 0) + 1
    p["ordinal"] = seen[p["question"]]

# ---- checks ----------------------------------------------------------------------------------
bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count('<div class="fig">')
    nblock = len([p for p in PLAN if p["question"] == qn])
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d block assets" % (qn, nph, nblock))
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h or "</td><td>" in h.replace("</td><td>", "", 0) and False:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    if re.search(r"</td></tr></table></td>", h):
        bad.append("Q%d: stray table fragment" % qn)
    if "[Total:" in h:
        bad.append("Q%d: leftover [Total] in html" % qn)
    if not r["content_text"].rstrip().endswith("[Total: %d]" % r["marks"]) and r["marks"]:
        bad.append("Q%d: content_text does not end with its [Total]" % qn)
    if h.count("<div") != h.count("</div>"):
        bad.append("Q%d: unbalanced div" % qn)
    if h.count("<p") - h.count("<pl") != h.count("</p>"):
        pass
    got = sum(p["marks"] or 0 for p in r["parts"])
    if got != r["marks"]:
        bad.append("Q%d: parts sum %d vs total %d" % (qn, got, r["marks"]))
    if "–" in h or "​" in h:
        bad.append("Q%d: en dash / zero-width space left" % qn)
    if "&lt;" in r["content_text"]:
        bad.append("Q%d: html entity in content_text" % qn)
assert [Q[k]["marks"] for k in sorted(Q)] == [21, 14, 20, 20, 20], [Q[k]["marks"] for k in sorted(Q)]
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d (all block) | typos applied: %s" % (len(Q), len(PLAN), APPLY_TYPOS))
for l in LOG:
    print("  " + l)
print("en dashes converted to minus (review):")
for c in CONTEXT:
    print("  " + c)
