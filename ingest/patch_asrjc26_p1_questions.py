"""ASRJC 2026 H2 P1 (9476/01) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_question_migration.

usage:
  python3 -m ingest.asrjc26_p1_prep <unz> <unz_q>          # question-only copy
  python3 -m ingest.redact_inline_answers_pdf <word.pdf> q_redacted.pdf \
      0xcc,0x33cc,0x7030a0,0xa0,0xff,0x3333cc
  python3 -m ingest.extract_questions <unz_q> q_redacted.pdf <out> \
      --school ASRJC --level H2 --paper P1 --year 2026 --no-crops --first-page 1
  python3 -m ingest.patch_asrjc26_p1_questions <out> <build_dir>

Shape: table family, one Word table per question (30 tables), solutions typed
into the SAME tables (ASRJC 2024 P1 family). Every edit asserts its match
count: a silent miss is how a fix ships unapplied.

FIGURES. The asset plan is the SNIP LIST. The user snips every figure by hand,
EXCEPT the three questions whose four options are all diagrams (Q7, Q8, Q10),
which were cut for the user at their request (Q7/Q8 from the docx's own PNGs,
Q10 from the Word PDF). Reaction arrows that the docx holds as little pictures
(Q10, Q11, Q13, Q19, Q30) are typed (-> / equilibrium sign), as on ACJC 2026 P3.
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
PL = '<sup class="pl-sym">⦵</sup>'


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def set_plan(qn, entries):
    """Replace question `qn`'s asset plan: entries = [(kind, slot), ...]. Block
    figures first in DOM order, then option-grid assets, then inline ones (the
    ordinal rule of render_questions): ordinal = position in `entries`."""
    global PLAN
    PLAN = [p for p in PLAN if p["question"] != qn]
    for i, (kind, slot) in enumerate(entries):
        PLAN.append({"question": qn, "index": i, "kind": kind, "slot": slot,
                     "n_parts": 1, "ordinal": i + 1,
                     "storage_path": "ASRJC_H2_P1_Q%d_%s_2026.png" % (qn, slot)})
    LOG.append("Q%d plan -> %s" % (qn, [s for _k, s in entries]))


# ---- every question: a space typed INSIDE a <sup>/<sub> (min<sup>−1 </sup>) -------
for qn, r in Q.items():
    h = r["content_html"]
    h2 = re.sub(r"<(sup|sub)>([^<]*?)[  ]+</\1>", r"<\1>\2</\1> ", h)
    if h2 != h:
        r["content_html"] = h2
        LOG.append("Q%d: space moved out of a sup/sub x%d"
                   % (qn, len(re.findall(r"<(sup|sub)>([^<]*?)[  ]+</\1>", h))))

# ---- the Data Booklet note: LEFT AS THE SCHOOL SET IT (user ruling 2026-10-22: the upright form
# is the new-syllabus form; no italic, no re-wording) -------------------------------

# ---- Q3: table cells run together in content_text ---------------------------------
sub(3, "grey tinwhite tin boiling point / K25432533 electrical conductivitynone in solid "
       "or liquidgood in solid and liquid malleabilitybrittlemalleable",
    "grey tin | white tin | boiling point / K 2543 2533 electrical conductivity none in "
    "solid or liquid good in solid and liquid malleability brittle malleable",
    field="content_text")

# ---- Q5: option rows B-D are structure pairs (I and II): ONE inline image per molecule
# (user ruling 2026-10-23: a single row image cannot sit under the I / II columns once it is
# resized, so 6 snips: B_I, B_II, C_I, C_II, D_I, D_II, structure only), one per cell of the
# columnar table, so the I/II columns, the row letters and the Show-answer highlight survive.
# A is typed.
sub(5, FIG + "\n", "")
for L in "BCD":
    sub(5, '<tr><td class="ol">%s</td><td></td><td></td></tr>' % L,
        '<tr><td class="ol">%s</td>' % L
        + "".join('<td><img data-asset="ASRJC_H2_P1_Q5_%s_%s_2026.png" alt=""></td>' % (L, c)
                  for c in ("I", "II")) + '</tr>')
set_plan(5, [("inline", "%s_%s" % (L, c)) for L in "BCD" for c in ("I", "II")])

# ---- wording fixes (user rulings 2026-10-23) --------------------------------------------
for f, a_, b_ in (("content_html", "occupy the volume 0.5<i>V</i>", "occupy a volume 0.5<i>V</i>"),
                  ("content_text", "occupy the volume 0.5V", "occupy a volume 0.5V")):
    sub(6, a_, b_, field=f)
for f in ("content_html", "content_text"):
    sub(11, "nitrogen monoxide, NO is oxidised", "nitrogen monoxide, NO, is oxidised", field=f)
    sub(12, "in which molar ratio", "in which the molar ratio", field=f)
    sub(17, "3-ethynylcyclopentene. ", "3-ethynylcyclopentene? ", field=f)
    sub(22, "An enantiomeric pure sample", "An enantiomerically pure sample", count=2, field=f)
    sub(22, "undergoes hydrolysis reaction via", "undergoes hydrolysis via", field=f)
    sub(28, "Which of following gives", "Which of the following gives", field=f)
    sub(28, "during electrolysis. Assume", "during electrolysis? Assume", field=f)
sub(26, "treated with reducing agent, LiA<i class=\"el\">l</i>H", "treated with LiA<i class=\"el\">l</i>H")
sub(26, "treated with reducing agent, LiAlH", "treated with LiAlH", field="content_text")

# ---- Q7 / Q8: four graphs A-D = option grid (cut for the user) ----------------------
for qn in (7, 8):
    assert [p["slot"] for p in PLAN if p["question"] == qn] == list("ABCD")

# ---- Q9: a stray italic space in option A -----------------------------------------
sub(9, "<i> </i>&gt;", " &gt;")

# ---- Q10: the reaction arrow is a little picture: typed; options A-D = option grid --
sub(10, "½O<sub>2</sub>(g) " + FIG + " SO<sub>3</sub>(g)",
    "½O<sub>2</sub>(g) → SO<sub>3</sub>(g)")
sub(10, "SO2(g) + ½O2(g) SO3(g)∆H < 0", "SO2(g) + ½O2(g) → SO3(g) ∆H < 0", field="content_text")
sub(10, "corresponds to  the reaction", "corresponds to the reaction")
set_plan(10, [("option", L) for L in "ABCD"])

# ---- Q11: arrow typed, one centred equation; table cells run together in text -------
sub(11, '<p class="c">2NO(g) + O<sub>2</sub>(g) </p>\n' + FIG + '\n<p class="c">2NO<sub>2</sub>(g)</p>',
    '<p class="c">2NO(g) + O<sub>2</sub>(g) → 2NO<sub>2</sub>(g)</p>')
sub(11, "2NO(g) + O2(g) 2NO2(g)", "2NO(g) + O2(g) → 2NO2(g)", field="content_text")
sub(11, "experimentinitial [NO] / mol dm−3initial [O2] / mol dm−3initial rate / mol dm−3 min−1 "
        "10.800.800.020 20.800.320.0080 31.60.960.096",
    "experiment | initial [NO] / mol dm−3 | initial [O2] / mol dm−3 | initial rate / "
    "mol dm−3 min−1 1 0.80 0.80 0.020 2 0.80 0.32 0.0080 3 1.6 0.96 0.096",
    field="content_text")
set_plan(11, [])

# ---- Q13: equilibrium sign typed; the ∆H label sits after a gap ---------------------
sub(13, r'<p class="c">CO\(g\)\s+\+\s+3H<sub>2</sub>\(g\)\s*</p>\n' + re.escape(FIG) +
        r'\n<p class="c">\s*CH<sub>4</sub>\(g\)\s+\+\s+H<sub>2</sub>O\(g\)\s+∆H &lt; 0</p>',
    '<p class="c">CO(g) + 3H<sub>2</sub>(g) ⇌ CH<sub>4</sub>(g) + H<sub>2</sub>O(g)' + GAP +
    '∆H &lt; 0</p>', rx=True)
sub(13, r"CO\(g\)\s+\+\s+3H2\(g\)\s+CH4\(g\)\s+\+\s+H2O\(g\)\s+∆H < 0",
    "CO(g) + 3H2(g) ⇌ CH4(g) + H2O(g) ∆H < 0", field="content_text", rx=True)
set_plan(13, [])

# ---- Q15: the two titration curves X and Y = ONE snip --------------------------------
set_plan(15, [("block", "stem1")])

# ---- Q16: reactions 1-4, one snip each (the typed numbers stay as the <ol>) ----------
# user ruling 2026-10-23: the four reactions WITH their numbers are ONE snip (stem1), flush left
# like the paper: an inline <img> in a paragraph is left-aligned and unboxed, a block figure
# would be centred and boxed by .figimg. The typed <ol> numbers are dropped (they are in the snip).
sub(16, r'<ol class="stmts">.*?</ol>',
    '<p class="qstem"><img data-asset="ASRJC_H2_P1_Q16_stem1a_2026.png" alt=""></p>', rx=True)
set_plan(16, [("inline", "stem1a")])

# ---- Q17 / Q23: one structure each ----------------------------------------------------
for qn in (17, 23):
    set_plan(qn, [("block", "stem1")])

# ---- Q18: molecules 1-3, one snip each -------------------------------------------------
# Q18: the school prints each molecule flush left beside its number (a block .fig would
# centre and box it): inline images, middle-aligned so the numeral sits level with the molecule.
sub(18, r'<ol class="stmts">.*?</ol>',
    '<ol class="stmts">' + "".join(
        '<li><img data-asset="ASRJC_H2_P1_Q18_stem%d_2026.png" alt="" '
        'style="vertical-align:middle"></li>' % i for i in (1, 2, 3)) + '</ol>', rx=True)
set_plan(18, [("inline", "stem%d" % i) for i in (1, 2, 3)])

# ---- Q19: arrow typed; the ion's charge is a minus; one centred equation --------------
sub(19, '<p class="c">CH<sub>3</sub>CH<sub>2</sub>CH<sub>3</sub> + X<sub>2</sub> </p>\n' + FIG +
        '\n<p class="c"> CH<sub>3</sub>CH<sub>2</sub>CH<sub>2</sub>X + HX</p>',
    '<p class="c">CH<sub>3</sub>CH<sub>2</sub>CH<sub>3</sub> + X<sub>2</sub> → '
    'CH<sub>3</sub>CH<sub>2</sub>CH<sub>2</sub>X + HX</p>')
sub(19, "CH3CH2CH3 + X2 CH3CH2CH2X + HX", "CH3CH2CH3 + X2 → CH3CH2CH2X + HX", field="content_text")
sub(19, "X<sup>–</sup> ion", "X<sup>" + MINUS + "</sup> ion")
sub(19, "reactive X– ion.", "reactive X" + MINUS + " ion.", field="content_text")
Q[19]["options"]["D"] = Q[19]["options"]["D"].replace("X– ion", "X" + MINUS + " ion")
assert MINUS in Q[19]["options"]["D"]
set_plan(19, [])

# ---- Q20: the option row was read as a staggered grid: rebuild; 4 snips ----------------
sub(20, r'<table class="opts-table">.*?</table>',
    '<table class="opts-table"><tr><td class="ol">A</td><td>1, 2 and 3</td></tr>'
    '<tr><td class="ol">B</td><td>1 and 2</td></tr>'
    '<tr><td class="ol">C</td><td>2 and 3</td></tr>'
    '<tr><td class="ol">D</td><td>1 only</td></tr></table>', rx=True)
sub(20, "A | 1, 2 and 3 B 1 and 2 C 2 and 3 D 1 only", "A 1, 2 and 3 B 1 and 2 C 2 and 3 D 1 only",
    field="content_text")
# user ruling 2026-10-23: the 1/2/3 rows must not be three columns. "P is" and its structure
# are ONE item of a numbered list (columns 2 and 3 merged, the number is the <ol> marker),
# flush left, the structure an inline image (no box, like the paper).
sub(20, r'<table class="qt center">.*?</table>',
    '<ol class="stmts">' + "".join(
        '<li>%s is <img data-asset="ASRJC_H2_P1_Q20_stem%d_2026.png" alt=""></li>' % (t, i)
        for t, i in (("P", 2), ("Q", 3), ("R", 4))) + '</ol>', rx=True)
set_plan(20, [("block", "stem1"), ("inline", "stem2"), ("inline", "stem3"), ("inline", "stem4")])

# ---- Q22: angles are SIGNED: U+2212; table cells run together in text ------------------
for f in ("content_html", "content_text"):
    n = len(re.findall(r"–(?=\d)", Q[22][f]))
    assert n == (4 if f == "content_html" else 3) or n >= 2, (f, n)
    Q[22][f] = re.sub(r"–(?=\d)", MINUS, Q[22][f])
    LOG.append("Q22 %s: %d en-dash signs -> U+2212" % (f, n))
Q[22]["options"] = {k: re.sub(r"–(?=\d)", MINUS, v) for k, v in Q[22]["options"].items()}
sub(22, "enantiomerangle of rotation of plane-polarised light V 23.1° W −23.1° X 13.5° Y −13.5°",
    "enantiomer | angle of rotation of plane-polarised light V 23.1° W −23.1° X 13.5° Y −13.5°",
    field="content_text")
sub(22, "23.1°.  An enantiomeric", "23.1°. An enantiomeric")
set_plan(22, [("block", "stem%d" % i) for i in (1, 2, 3, 4)])

# ---- Q24: the three structures are ONE snip (user, 2026-10-22): the 3-cell figure table
# becomes a single block figure; the captions are inside the snip? (asked) -> typed captions dropped
sub(24, r'<table class="qt"><tr><td><div class="fig">figure</div></td><td><div class="fig">figure</div></td>'
        r'<td><div class="fig">figure</div></td></tr><tr><td>phenol</td><td>2-chlorophenol</td>'
        r'<td>2-methylphenol</td></tr></table>', FIG, rx=True)
sub(24, "phenol2-chlorophenol2-methylphenol", "phenol 2-chlorophenol 2-methylphenol",
    field="content_text")
set_plan(24, [("block", "stem1")])

# ---- Q25: L = block figure; the small ring is INLINE in the sentence -------------------
sub(25, '<p class="qstem">The </p>\n' + FIG + '\n<p class="qstem">ring remains unaltered in most reactions.</p>',
    '<p class="qstem">The <img data-asset="ASRJC_H2_P1_Q25_ring_2026.png" alt=""> ring remains '
    'unaltered in most reactions.</p>')
set_plan(25, [("block", "stem1"), ("inline", "ring")])

# ---- Q26: the four test results are a BULLET list (numPr) ------------------------------
_s = Q[26]["content_html"]
_m = re.search(r'((?:<p class="qstem">(?:When <b>T</b> is treated|<b>T</b> can form|<b>T</b> gives an orange|'
               r'<b>T</b> does not react)[^\n]*?</p>\n?){4})', _s)
assert _m, "Q26 bullet block not found"
_items = re.findall(r'<p class="qstem">(.*?)</p>', _m.group(1), flags=re.S)
assert len(_items) == 4
Q[26]["content_html"] = _s.replace(
    _m.group(1), '<ul class="stmts">' + "".join("<li>%s</li>" % i for i in _items) + "</ul>\n")
LOG.append("Q26: four result paragraphs -> ul.stmts")

# ---- Q27: table cells run together in text ---------------------------------------------
sub(27, "Amino acidMr Val117 Lys146 Phe165 Arg174", "Amino acid | Mr Val 117 Lys 146 Phe 165 Arg 174",
    field="content_text")

# ---- Q29: the ticks are bold, the crosses are not: make them one weight -----------------
sub(29, "<b>✓</b>", "✓", count=8)

# ---- Q30: equilibrium sign typed; plimsoll; one centred equation with the E label -------
sub(30, "<i>E</i><sup>⦵</sup>(NO", "<i>E</i>" + PL + "(NO")
sub(30, r'(<p class="c">NO<span class="stk post"><span>−</span><span>3</span></span> \+ 4H<sup>\+</sup> \+ 3e) </p>\n'
        + re.escape(FIG) + r'\n<p class="c">NO \+ 2H<sub>2</sub>O\s+<i>E</i><sup>⦵</sup> = \+0\.96 V</p>',
    lambda m: m.group(1) + " ⇌ NO + 2H<sub>2</sub>O" + GAP + "<i>E</i>" + PL + " = +0.96 V</p>",
    rx=True)
sub(30, "NO3− + 4H+ + 3e NO + 2H2O E⦵ = +0.96 V", "NO3− + 4H+ + 3e ⇌ NO + 2H2O E⦵ = +0.96 V",
    field="content_text")
set_plan(30, [])

# ---- every other figure question keeps the extractor's plan -----------------------------
# (nothing to do for 1-4, 6, 9, 12, 14, 21, 26-29)

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
    # block, then option, then inline (render_questions' ordinal rule)
    rank = {"block": 0, "option": 1, "inline": 2}
    ks = [rank[p["kind"]] for p in sorted(ps, key=lambda p: p["ordinal"])]
    if ks != sorted(ks):
        bad.append("Q%d: plan order breaks block<option<inline" % qn)
    for p in ps:
        if p["kind"] == "inline":
            if 'data-asset="%s"' % p["storage_path"] not in r["content_html"]:
                bad.append("Q%d: inline %s is not in the html" % (qn, p["storage_path"]))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
    if re.search(r"[  ]{3,}", re.sub(r"<[^>]+>", "", r["content_html"])):
        bad.append("Q%d: a run of 3+ spaces is left in content_html" % qn)
    if re.search(r"<(sup|sub)>[^<]*[  ]</\1>", r["content_html"]):
        bad.append("Q%d: a space is left inside a sup/sub" % qn)
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
