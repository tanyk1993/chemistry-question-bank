"""ACJC 2026 H2 P1 (9476/01) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_question_migration.

usage:
  python3 -m ingest.extract_questions <unz> <word.pdf> <out> \
      --school ACJC --level H2 --paper P1 --year 2026 --no-crops
  python3 -m ingest.patch_acjc26_p1_questions <out> <build_dir>

Shape: table family (one Word table per question, 30 clean tables, so NO prep
script was needed). Every edit asserts its match count: a silent miss is how a
fix ships unapplied.

FIGURES. The asset plan here is the SNIP LIST (HANDOFF SS7: slots follow DOM
order, ordinal = DOM order of the placeholders). The user snips every figure
by hand, EXCEPT Q26's four option structures, which were cut from the Word PDF
at the user's request (the one exception to the "never crop" rule).

NOT APPLIED (held for the user's rulings, see the report): theta vs plimsoll
in Q12/Q27, every wording / chemistry point in the report, Q10's table shape.
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


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def set_plan(qn, entries):
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...] in DOM
    order (block stem figures first, then the ONE option grid)."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "ACJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- Q1: a stacked exponent with an empty subscript is just a superscript ----------
sub(1, '<span class="stk post"><span>‒3</span><span> </span></span>FeC',
    '<sup>‒3</sup> FeC')

# ---- Q2: zero-width spaces typed between the letters of every option formula -------
for qn in Q:
    for f in ("content_html", "content_text"):
        n = Q[qn][f].count("​")
        if n:
            Q[qn][f] = Q[qn][f].replace("​", "")
            LOG.append("Q%d %s: %d zero-width spaces removed" % (qn, f, n))
    for k, v in list(Q[qn]["options"].items()):
        if "​" in v:
            Q[qn]["options"][k] = v.replace("​", "")
            LOG.append("Q%d option %s: zero-width spaces removed" % (qn, k))

# ---- Q3: the minus of each ion is a bold run in its own <sup>: one <sup> -----------
sub(3, r"<sup>(\d)</sup><b><sup>−</sup></b>", r"<sup>\1−</sup>", count=2, rx=True)
sub(3, r"<b><sup>−</sup></b>", "<sup>−</sup>", count=2, rx=True)

# ---- Q4 / Q10 / Q27 / Q30: table cells run together in content_text ---------------
sub(4, "IE / kJ mol–11st2nd3rd4th5th6th7th8th M550106541385500691087601023011800 "
       "N114021033470456057608550994018600",
    "IE / kJ mol−1 1st 2nd 3rd 4th 5th 6th 7th 8th M 550 1065 4138 5500 6910 8760 "
    "10230 11800 N 1140 2103 3470 4560 5760 8550 9940 18600", field="content_text")
sub(10, "bondbond energy /kJ mol–1bond length / nm C – F4850.138 C – Cl3400.177 "
        "C – Br2800.193 C – I2400.214",
    "bond | bond energy / kJ mol−1 | bond length / nm C – F 485 0.138 "
    "C – Cl 340 0.177 C – Br 280 0.193 C – I 240 0.214", field="content_text")

# ---- Q8: three charts = ONE snip (user's call; the extractor counted 5 placeholders) -
sub(8, "(?:" + re.escape(FIG) + r"\n){4}" + re.escape(FIG), FIG, rx=True)
set_plan(8, [("block", "stem1")])   # the user snipped the 3 charts as ONE image

# ---- Q11: one flowchart (Word shapes) ------------------------------------------------
set_plan(11, [("block", "stem1")])

# ---- Q12: option A's 1/2 is a MathType object: typed as house .frac, not snipped ---
FR_HALF = '<span class="frac"><span class="fnum">1</span><span class="fden">2</span></span>'
sub(12, '</p>\n' + FIG + '\n<table class="opts-table">', '</p>\n<table class="opts-table">')
sub(12, "2C(s) + 3H<sub>2</sub>(g) +O<sub>2</sub>(g) → CH<sub>3</sub>CH<sub>2</sub>OH(l)",
    "2C(s) + 3H<sub>2</sub>(g) + " + FR_HALF + "O<sub>2</sub>(g) → CH<sub>3</sub>CH<sub>2</sub>OH(l)")
sub(12, "2C(s) + 3H2(g) +O2(g) → CH3CH2OH(l)", "2C(s) + 3H2(g) + ½O2(g) → CH3CH2OH(l)",
    field="content_text", count=1)
Q[12]["options"]["A"] = Q[12]["options"]["A"].replace("+O2(g)", "+ ½O2(g)")
assert "½" in Q[12]["options"]["A"]
set_plan(12, [])

# ---- Q14: runs of spaces typed to line the rate labels up ---------------------------
sub(14, '<p class="qstem">Equation 1:     2NO', '<p class="qstem">Equation 1:&emsp;2NO')
sub(14, r'<sub>2\s+</sub><i> \(fast\)</i>', "<sub>2</sub>" + GAP + "<i>(fast)</i>", rx=True)
sub(14, r"H<sub>2</sub>O<i>\s+\(slow\)</i>", "H<sub>2</sub>O" + GAP + "<i>(slow)</i>", rx=True)
sub(14, r"H<sub>2</sub>O <i>\s+\(fast\)</i>", "H<sub>2</sub>O" + GAP + "<i>(fast)</i>", rx=True)

# ---- Q15: the ∆H label typed 12 spaces after the equilibrium ------------------
sub(15, r"2NH<sub>3</sub>\(g\)\s{6,}∆H &lt; 0", "2NH<sub>3</sub>(g)" + GAP + "∆<i>H</i> &lt; 0", rx=True)

# ---- Q16: the Ka labels typed 6-7 spaces after their equilibria --------------------
sub(16, r"HCO<span class=\"stk post\"><span>‒</span><span>3</span></span> \(aq\)\s{4,}<i>K</i>",
    'HCO<span class="stk post"><span>‒</span><span>3</span></span> (aq)' + GAP + "<i>K</i>", rx=True)
sub(16, r"CO<span class=\"stk post\"><span>2‒</span><span>3</span></span> \(aq\)\s{4,}<i>K</i>",
    'CO<span class="stk post"><span>2‒</span><span>3</span></span> (aq)' + GAP + "<i>K</i>", rx=True)
# statement 1's ratio: hyphens for minus, and the text version was garbled
sub(16, "The ratio of ([CO2-3])/([HCO-3)] in seawater is 54.1.",
    "The ratio of [CO3" + "2" + MINUS + "] / [HCO3" + MINUS + "] in seawater is 54.1.",
    field="content_text")
sub(16, "The ratio of  <span", "The ratio of <span")

# ---- Q17/19/22/23: one structure each (nothing to patch, plan only) ------------------
for qn in (17, 19, 22, 23):
    set_plan(qn, [("block", "stem1")])

# ---- Q21: ONE scheme, drawn as two stacked fragments -------------------------------
sub(21, FIG + "\n" + FIG, FIG)
set_plan(21, [("block", "stem1")])

# ---- Q24: the option table is figures. stem1 = the scheme (block placeholder); the
# S / T structures of each row are 8 INLINE images in a columnar opts-table (cut at ONE
# size from the Word PDF, user request 2026-10-19); U is typed. Inline images are matched
# by filename; the block figure keeps ordinal 1 (frontend does not exclude inline assets).
def _q24_row(L, u):
    return ('<tr><td class="ol">%s</td><td><img data-asset="ACJC_H2_P1_Q24_%s_S_2026.png" alt=""></td>'
            '<td><img data-asset="ACJC_H2_P1_Q24_%s_T_2026.png" alt=""></td><td>%s</td></tr>' % (L, L, L, u))
_U = {"A": "dilute H<sub>2</sub>SO<sub>4</sub>", "B": "concentrated H<sub>3</sub>PO<sub>4</sub>",
      "C": "dilute H<sub>2</sub>SO<sub>4</sub>", "D": "concentrated H<sub>3</sub>PO<sub>4</sub>"}
sub(24, FIG + "\n" + FIG + '\n<p class="c">What are the products <b>S</b> and <b>T</b>, '
        'and the reagent <b>U</b>?</p>\n' + FIG,
    FIG + '\n<p class="qstem">What are the products <b>S</b> and <b>T</b>, '
          'and the reagent <b>U</b>?</p>\n'
          '<table class="opts-table"><tr><td class="ol"></td><td><b>S</b></td><td><b>T</b></td><td><b>U</b></td></tr>'
          + "".join(_q24_row(L, _U[L]) for L in "ABCD") + "</table>")
sub(24, "S | T | U A | | dilute H2SO4 B | | concentrated H3PO4 C | | dilute H2SO4 "
        "D | | concentrated H3PO4",
    "S T U A dilute H2SO4 B concentrated H3PO4 C dilute H2SO4 D concentrated H3PO4",
    field="content_text")
set_plan(24, [("block", "stem1")] + [("inline", "%s_%s" % (L, X)) for L in "ABCD" for X in "ST"])

# ---- Q26: three fragments = ONE stem snip; options A-D (cut from the Word PDF) --------
sub(26, FIG + '\n<p class="c">What is the formula of the tetrapeptide?</p>\n' + FIG,
    FIG + '\n<p class="qstem">What is the formula of the tetrapeptide?</p>\n' + FIG)
assert Q[26]["options"] == {L: "[structure %s]" % L for L in "ABCD"}
set_plan(26, [("block", "stem1")] + [("option", L) for L in "ABCD"])

# ---- Q27: stacked charge with a blank subscript; one minus for the E value ---------
sub(27, r'2e<span class="stk post"><span>‒</span><span>\s*</span></span>⇌\s+2C<i class="el">l</i><sup>‒</sup>',
    '2e<sup>‒</sup> ⇌ 2C<i class="el">l</i><sup>‒</sup>', rx=True)
sub(27, "half-equationEθ / V C", "half-equation Eθ / V C", field="content_text")
sub(27, "2Cl‒+1.36 Zn(OH)42− + 2e− ⇌ Zn(s) + 4OH−‒1.29",
    "2Cl− +1.36 Zn(OH)42− + 2e− ⇌ Zn(s) + 4OH− −1.29", field="content_text")
sub(27, "2e‒ ⇌", "2e− ⇌", field="content_text")

# ---- Q27: trailing spaces after the stem's full stop ---------------------------------
sub(27, '<sub>2</sub>.  </p>', '<sub>2</sub>.</p>')

# ---- Q29: the scheme belongs AFTER the sentence that introduces Y and Z; the typed
#      copy of the scheme's labels is the figure's own text ---------------------------
sub(29, r'<div class="fig">figure</div>\n(<p class="qstem">A reaction scheme[^\n]*?</p>)\n'
        r'<p class="c">CuSO<sub>4</sub>\(aq\)[^\n]*?</p>\n',
    r"\1\n" + FIG + "\n", rx=True)
set_plan(29, [("block", "stem1")])

# ---- Q30: the minus is the scan-line glyph in 3 places; the equation / table text ----
sub(30, "L⎺", "L<sup>−</sup>", count=1)
sub(30, "SCN⎺", "SCN<sup>−</sup>", count=1)
sub(30, "F⎺", "F<sup>−</sup>", count=1)
sub(30, "<i>K</i><sub>stab</sub>=<span", "<i>K</i><sub>stab</sub> = <span")
# user ruling 2026-10-19: centre the Kstab expression (matches the paper)
sub(30, '<p class="qstem"><i>K</i><sub>stab</sub> = <span', '<p class="c"><i>K</i><sub>stab</sub> = <span')
sub(30, "solution of  iron(", "solution of iron(")
sub(30, "L⎺ ⇌ Fe(L)", "L− ⇌ Fe(L)", field="content_text")
sub(30, "Kstab=([Fe(L)(H2O)52+])/([Fe(H2O)63+][L–])",
    "Kstab = [Fe(L)(H2O)52+] / [Fe(H2O)63+][L−]", field="content_text")
sub(30, "ligand, LKstabcolour of Fe(L)(H2O)52+ SCN⎺126blood red F⎺251000colourless",
    "ligand, L Kstab colour of Fe(L)(H2O)52+ SCN− 126 blood red F− 251000 colourless",
    field="content_text")

# ---- user rulings (2026-10-19) ---------------------------------------------------------
# Q14: mechanism steps indented slightly right (user ruling 2026-10-19); html only
for n in (1, 2, 3):
    sub(14, '<p class="qstem">step %d:' % n, '<p class="qstem">&emsp;step %d:' % n)
# Q16 statement 1 (54.1) and Q22 statement 1 (C10H11O5): deliberately wrong, NO change.
# grammar (both fields)
for f in ("content_html", "content_text"):
    sub(14, "NO and H", "NO and H", field=f)            # presence check
sub(14, "reacts as shown in equation 1.", "react as shown in equation 1.", field="content_html")
sub(14, "reacts as shown in equation 1.", "react as shown in equation 1.", field="content_text")
for f in ("content_html", "content_text"):
    sub(16, "The following equilibria shows how", "The following equilibria show how", field=f)
    sub(16, "Increasing effects of deforestation have", "The increasing effects of deforestation have", field=f)
    sub(20, "overlaps with the", "overlap with the", field=f)
    sub(26, "What is the formula of the tetrapeptide?", "What is the structure of the tetrapeptide?", field=f)
# units / spacing: "0.177 nm"; bond notation C-X with no spaces (the source mixes both in Q10)
for f in ("content_html", "content_text"):
    sub(10, "0.177nm", "0.177 nm", field=f)
sub(10, "C \u2013 ", "C\u2013", count=7, field="content_html")
sub(10, "C \u2013 ", "C\u2013", count=7, field="content_text")
# state symbols: no space before (g)/(l)/(aq) (Q16 typed one); Zn(s) upright
sub(16, r"(?<=\S) \((g|l|aq)\)", r"(\1)", count=9, rx=True)
sub(16, r"(?<=\S) \((g|l|aq)\)", r"(\1)", count=9, rx=True, field="content_text")
sub(27, "Zn(<i>s</i>)", "Zn(s)")
# standard-state sign: the plimsoll every other paper uses, not Greek theta
sub(12, '<span class="stk post"><span>\u03b8</span><span>f</span></span>',
    '<span class="stk post"><span><span class="pl-sym">\u29b5</span></span><span>f</span></span>')
sub(12, "\u2206Hf\u03b8", "\u2206Hf\u29b5", field="content_text")
sub(27, "<sup>\u03b8 </sup>", '<sup class="pl-sym">\u29b5</sup> ')
sub(27, "E\u03b8 / V", "E\u29b5 / V", field="content_text")

# ---- minus: ONE convention, U+2212, for charges / exponents / signs (style-guide) -----
for qn, r in Q.items():
    h = r["content_html"]
    n0 = h.count("‒")
    h = h.replace("‒", MINUS)
    h = re.sub(r"<sup>([^<]*)</sup>",
               lambda m: "<sup>" + m.group(1).replace("–", MINUS) + "</sup>", h)
    h = re.sub(r'(<span class="stk post"><span>)(\d?)[-–](</span>)',
               lambda m: m.group(1) + m.group(2) + MINUS + m.group(3), h)
    h = re.sub(r"(<span class=\"stk post\"><span>)(\d?)−(</span>)", r"\1\2−\3", h)
    r["content_html"] = h
    t = r["content_text"]
    t = t.replace("‒", MINUS)
    t = t.replace("mol–1", "mol" + MINUS + "1")
    t = t.replace("2–(aq)", "2" + MINUS + "(aq)")
    r["content_text"] = t
    if n0:
        LOG.append("Q%d: %d U+2012 -> U+2212" % (qn, n0))
# the ASCII hyphen charges Q16 statement 1 typed (inside .stk) are now minus too
for qn, r in Q.items():
    for f in ("content_html", "content_text"):
        assert "‒" not in r[f], "Q%d still has U+2012 in %s" % (qn, f)
    for m in re.finditer(r"<sup>([^<]*)</sup>", r["content_html"]):
        assert not re.search(r"[-–]", m.group(1)), "Q%d sup %r" % (qn, m.group(1))
    for m in re.finditer(r'<span class="stk post"><span>([^<]*)</span>', r["content_html"]):
        assert not re.search(r"[-–]", m.group(1)), "Q%d stk %r" % (qn, m.group(1))
# en dashes that remain are prose / bond dashes: Q10's "C – F" bonds, Q16 "carbonate–hydrogencarbonate"
left = sorted(qn for qn, r in Q.items() if "–" in r["content_html"])
assert left == [10, 16], left

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
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
    if re.search(r"[ \u00a0]{3,}", re.sub(r"<[^>]+>", "", r["content_html"])):
        bad.append("Q%d: a run of 3+ spaces is left in content_html" % qn)
assert not bad, "\n".join(bad)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1),
    encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
print("\n".join(LOG))
