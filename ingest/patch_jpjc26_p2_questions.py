"""JPJC 2026 H2 P2 (9476/02) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QA.docx -d unz
  python3 -m ingest.jpjc26_p2_prep unz unz_q           # answers out, grid squared up
  python3 -m ingest.redact_inline_answers_pdf QA_word.pdf q_word.pdf \
      0xff,0x3333ff,0x33cc,0xff0000,0xee0000            # answer text out of the PDF
  python3 -m ingest.extract_parts unz_q q_word.pdf out \
      --school JPJC --level H2 --paper P2 --year 2026 --first-page 2
        (crops stubbed: the user snips every figure; PF.crop_all -> ([], []))
  python3 -m ingest.patch_jpjc26_p2_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school JPJC --year 2026 --paper 2 --level H2

Shape: table family, one irregular grid per table (JPJC 2024 P2 family), answers
in the SAME tables in blue; see `jpjc26_p2_prep`. Answers are NOT read at this
stage.

FIGURES (user snips, 9, all block figures; printed captions "Fig. 2.1", "Fig. 2.2",
"Fig. 3.1", "Fig. 4.1" and "Fig. 5.1" stay typed in the stem):
  Q2(a)     Fig 2.1 graph (the school's answer overlay is NOT part of the question)
  Q2(b)(ii) the PBT segment (Fig 2.2); the drawn monomers below it are the answer
  Q3(b)     carbonic acid / 2-chlorophenol structures (two table cells, two snips)
  Q3(e)     Fig 3.1 (PV/RT axes, CO2 and ideal gas); the SF6 / CO2 (600 K) graph is the answer
  Q4        Fig 4.1 (E against log10 [Fe3+]/[Fe2+])
  Q5        Fig 5.1 scheme; 5(b) Friedel-Crafts equation; 5(d) the two ions

TYPED, NOT SNIPPED: the equilibrium arrows of Q3(a) equations (1)-(3) and Q3(c)
(small pictures in the source; the page shows the harpoon pair), and the
[HCO3-]/[CO3 2-] fraction of Q3(a)(iii) (an equation object with no text layer).

MARKS RESTORED: 3(e)(ii) [1] sits in the school's ANSWER row (deleted with it).
4(d)(ii) prints NO mark but Q4 totals [12]: [2] added (TOGGLE_4DII; the user was
asked, 2026-11-05).

RULINGS APPLIED (user, ...): none yet beyond the generic standardisations below.
Held for the user's ruling and NOT edited: "hydratioSn" (Table 1.1), 3(e)(iii)
"on on ... the what", the lone "." before [2] in 3(b), the missing full stop after
"alkaline iodine" (6(c)), 4(b)(i) "E-theta" against the plimsoll used elsewhere,
4(b)(iii) "b(i) and b(ii)".
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
LOG = []

TOGGLE_4DII = True          # add the missing [2] to 4(d)(ii)
EQ = "⇌"
MINUS = "−"
EM3 = "   "


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, old_h, new_h, old_t, new_t, rx_h=False, rx_t=False):
    sub(qn, old_h, new_h, rx=rx_h)
    sub(qn, old_t, new_t, field="content_text", rx=rx_t)


# ======================================================================= Q1
# the blank space for the energy cycle: a tab + zero-width space + the mark badge
both(1, r'\(s\)\.</p>\n<p>\t​ <span class="mk">\[3\]</span></p></div>',
        '(s). <span class="mk">[3]</span></p></div>',
        r"\(s\)\.\n\t​ \[3\]", "(s). [3]", rx_h=True, rx_t=True)
sub(1, "<td>-80.0 </td>", "<td>" + MINUS + "80.0</td>")
sub(1, "CoCl2(s)-80.0 standard", "CoCl2(s) " + MINUS + "80.0 standard", field="content_text")
# the centred equation: the school's gap before the enthalpy label
both(1, r"\(aq\)      ∆", "(aq)" + EM3 + "∆",
        r"\(aq\)      ∆", "(aq)" + EM3 + "∆", rx_h=True, rx_t=True)

# ======================================================================= Q2
# the rate table: header cell broken by a stray <p>, and a stray </p> after the table
sub(2, "<td>initial rate\n<p>/ mol dm<sup>−3 </sup>min<sup>−1</sup></td>",
       "<td>initial rate / mol dm<sup>−3</sup> min<sup>−1</sup></td>")
sub(2, "</table></p>", "</table>")
sub(2, "initial rate\n/ mol dm−3 min−1", "initial rate / mol dm−3 min−1", field="content_text")

# ======================================================================= Q3
# equations (1)-(3): the arrows are small pictures in the source (typed here)
both(3, '<p>Equation (1): CO<sub>2</sub>(g)</p>\n<div class="fig">figure</div>\n<p>CO<sub>2</sub>(aq)</p>',
        '<p>Equation (1): CO<sub>2</sub>(g) %s CO<sub>2</sub>(aq)</p>' % EQ,
        "Equation (1): CO2(g)  CO2(aq) ", "Equation (1): CO2(g) %s CO2(aq)" % EQ)
both(3, '(<i class="el">l</i>)  H<sub>2</sub>CO<sub>3</sub>(aq)</p>',
        '(<i class="el">l</i>) %s H<sub>2</sub>CO<sub>3</sub>(aq)</p>' % EQ,
        "H2O(l)  H2CO3(aq)", "H2O(l) %s H2CO3(aq)" % EQ)
both(3, '<p>Equation (3): H<sub>2</sub>CO<sub>3</sub>(aq)</p>\n<div class="fig">figure</div>\n'
        '<p>HCO<sub>3</sub><sup>–</sup>(aq) + H<sup>+</sup>(aq)</p>',
        '<p>Equation (3): H<sub>2</sub>CO<sub>3</sub>(aq) %s HCO<sub>3</sub><sup>–</sup>(aq) + H<sup>+</sup>(aq)</p>' % EQ,
        "Equation (3): H2CO3(aq)  HCO3–(aq)", "Equation (3): H2CO3(aq) %s HCO3–(aq)" % EQ)
# (a)(iii): the fraction [HCO3-]/[CO3 2-] is an equation object (no text layer)
FRAC = ('<span class="frac"><span class="fnum">[HCO<sub>3</sub><sup>–</sup>]</span>'
        '<span class="fden">[CO<sub>3</sub><sup>2–</sup>]</span></span>')
both(3, 'calculate the</p>\n<div class="fig">figure</div>\n<p>ratio in this sample of seawater.',
        'calculate the %s ratio in this sample of seawater.</p>\n<p>' % FRAC,
        "calculate the ratio in this sample of seawater.",
        "calculate the [HCO3–]/[CO32–] ratio in this sample of seawater.")
# the paragraph split above leaves '<p>\n<span class="mk">': put the mark on the sentence
sub(3, '</p>\n<p> <span class="mk">[2]</span></p></div>', ' <span class="mk">[2]</span></p></div>')
# (b): the structures table; the extractor wrapped the figure cells in stray <p>s
sub(3, r'<table class="qt"><tr><td>Compound</td>.*?</table></p>',
    '<table class="qt"><tr><td>Compound</td><td>Structure</td><td>p<i>K</i><sub>a</sub></td></tr>'
    '<tr><td>carbonic acid</td><td><div class="fig">figure</div></td><td>6.35</td></tr>'
    '<tr><td>2-chlorophenol</td><td><div class="fig">figure</div></td><td>8.50</td></tr></table>', rx=True)
# (c): the solubility equation, arrow typed
both(3, '<p class="c">Ag<sub>2</sub>CO<sub>3</sub>(s) + aq</p>\n<div class="fig">figure</div>\n'
        '<p class="c">2Ag<sup>+</sup>(aq) + CO<sub>3</sub><sup>2–</sup>(aq)</p>',
        '<p class="c">Ag<sub>2</sub>CO<sub>3</sub>(s) + aq %s 2Ag<sup>+</sup>(aq) + CO<sub>3</sub><sup>2–</sup>(aq)</p>' % EQ,
        "Ag2CO3(s) + aq  2Ag+(aq) + CO32–(aq)", "Ag2CO3(s) + aq %s 2Ag+(aq) + CO32–(aq)" % EQ)
# (e)(ii): the [1] sat in the school's answer row
both(3, 'Your answer should include reference to intermolecular forces.</div>',
        'Your answer should include reference to intermolecular forces. <span class="mk">[1]</span></div>',
        "intermolecular forces. (e)(iii)", "intermolecular forces. [1] (e)(iii)")
for p in Q[3]["parts"]:
    if p["label"] == "(e)(ii)":
        assert p["marks"] is None
        p["marks"] = 1

# ======================================================================= Q4
both(4, r"equation 4\.1\s{5,}", "equation 4.1" + EM3, r"equation 4\.1\s{5,}", "equation 4.1" + EM3,
        rx_h=True, rx_t=True)
# standard-state sign in equation 4.1 (letter o superscript in the source)
both(4, "<i>E </i>= <i>E</i><sup>o</sup> +", '<i>E</i> = <i>E</i><sup class="pl-sym">⦵</sup> +',
        "E = Eo + ", "E = E⦵ + ")
# I2 / I-: iodine, not a Roman numeral
both(4, '<span class="sr">I</span><sub>2</sub>/<span class="sr"> I</span><sup>−</sup>',
        'I<sub>2</sub>/I<sup>−</sup>', "I2/ I−", "I2/I−")
if TOGGLE_4DII:
    both(4, "in (c). </div>", 'in (c). <span class="mk">[2]</span></div>',
            "in (c). [Total: 12]", "in (c). [2] [Total: 12]")
    for p in Q[4]["parts"]:
        if p["label"] == "(d)(ii)":
            assert p["marks"] is None
            p["marks"] = 2

# ======================================================================= Q5
# steps I, III and IV: three Roman numerals, one span had swallowed "III and IV"
sub(5, 'steps <span class="sr">I</span>,<span class="sr"> III and IV</span>.',
       'steps <span class="sr">I</span>, <span class="sr">III</span> and <span class="sr">IV</span>.')

# ======================================================================= generic
for qn in sorted(Q):
    h, t = Q[qn]["content_html"], Q[qn]["content_text"]
    # zero-width spaces and non-breaking spaces typed by the school
    n = h.count("​") + t.count("​") + h.count("\xa0") + t.count("\xa0")
    h = h.replace("​", "").replace("\xa0", " ")
    t = t.replace("​", "").replace("\xa0", " ")
    # soft line breaks inside a sentence -> space; a trailing one is dropped
    h = re.sub(r"\s*<br></p>", "</p>", h)
    h = re.sub(r"\s*<br>", " ", h)
    # whitespace inside inline tags: move it outside
    def _ws(m):
        tag, body, nxt = m.group(1), m.group(2), m.group(3)
        sp = "" if (nxt and (nxt[0] in " ,.;:)]<" or nxt == "")) else " "
        return "<%s>%s</%s>%s" % (tag, body, tag, sp) + nxt
    h = re.sub(r"<(sup|sub|i)>([^<]*?)\s+</\1>(.?)", _ws, h)
    # a dash inside a superscript is a minus sign (charges and exponents)
    h = re.sub(r"<sup>([^<]*)</sup>",
               lambda m: "<sup>" + re.sub(r"[-–‑]", MINUS, m.group(1)) + "</sup>", h)
    # runs of spaces typed to push text across the line
    h = re.sub(r"(?<=\S) {2,}(?=\S)", " ", h)
    t = re.sub(r"(?<=\S) {2,}(?=\S)", " ", t)
    t = re.sub(r"\n[ \t]+\n", "\n", t)
    # exponents typed with a dash in the search text
    t = re.sub(r"(?<=10)[–-](?=\d)", MINUS, t)
    t = re.sub(r"\b(dm|mol|min|K|g|J|cm|s)[–-](?=\d)", lambda m: m.group(1) + MINUS, t)
    Q[qn]["content_html"], Q[qn]["content_text"] = h, t
    if n:
        LOG.append("Q%d: %d zero-width / non-breaking spaces removed" % (qn, n))

# ---- typos, grammar and notation (user: "fix all typos (and grammar errors if any)", 2026-11-05) ----
# each counted in the display HTML and in the search text
def fix(qn, old_h, new_h, old_t=None, new_t=None, count=1):
    sub(qn, old_h, new_h, count=count)
    sub(qn, old_t if old_t is not None else old_h, new_t if new_t is not None else new_h,
        field="content_text", count=count)


fix(1, "hydratioSn", "hydration")
fix(1, "(s) dissolves readily", "(s), dissolves readily")
fix(1, "<sub>soln</sub>", "<sub>sol</sub>", "\u2206H\u29b5soln", "\u2206H\u29b5sol")      # sol, as in the later parts
fix(2, "in (a)(iii), calculate the value", "in (a)(iii) to calculate the value")
fix(3, "carbon sink on earth", "carbon sink on Earth")
fix(3, "difficulty to build and maintain their calcium carbonate",
       "difficulty in building and maintaining their calcium carbonate")
fix(3, "of 298K", "of 298 K")
fix(3, "at 298K", "at 298 K")
fix(3, "Illustrate on on the same axes in Fig. 3.1 the what happens",
       "Illustrate, on the same axes in Fig. 3.1, what happens")
sub(3, '<p>You may ignore the second ionisation of carbonic acid.</p>\n<p>. <span class="mk">[2]</span></p></div>',
       '<p>You may ignore the second ionisation of carbonic acid. <span class="mk">[2]</span></p></div>')
sub(3, "second ionisation of carbonic acid.\n. [2]", "second ionisation of carbonic acid. [2]", field="content_text")
fix(4, '<i>E</i><sup>\u03b8</sup>, of', '<i>E</i><sup class="pl-sym">\u29b5</sup>, of', "E\u03b8, of", "E\u29b5, of")
fix(4, "from b(i) and b(ii)", "from (b)(i) and (b)(ii)")
fix(4, "addition of SCN<sup>\u2212</sup>, on the ratio", "addition of SCN<sup>\u2212</sup> on the ratio",
       "addition of SCN\u2212, on the ratio", "addition of SCN\u2212 on the ratio")
fix(4, "where n is the number", "where <i>n</i> is the number", "where n is the number", "where n is the number")
fix(4, "the value of n in equation", "the value of <i>n</i> in equation", "the value of n in equation", "the value of n in equation")
fix(5, "3 etc)", "3 etc.)")
fix(5, "[4<i>n</i> +2]", "[4<i>n</i> + 2]", "[4n +2]", "[4n + 2]")
fix(6, "vapourised", "vaporised")
fix(6, "is produced which", "is produced, which")
fix(6, "aqueous alkaline iodine</p>", "aqueous alkaline iodine.</p>", "aqueous alkaline iodine\n", "aqueous alkaline iodine.\n")
fix(6, "plane\u2013polarised", "plane-polarised")

# ---- Q5: the school printed (a), (b), (d), (c); relabelled in reading order (user, 2026-11-05) ----
sub(5, '<span class="pl">(d)</span> In 1931', '<span class="pl">(c)</span> In 1931')
sub(5, '<span class="pl">(c)</span> Phenol', '<span class="pl">(d)</span> Phenol')
sub(5, "(d) In 1931", "(c) In 1931", field="content_text")
sub(5, "(c) Phenol", "(d) Phenol", field="content_text")
_lab = [p["label"] for p in Q[5]["parts"]]
assert _lab == ["(a)(i)", "(a)(ii)", "(b)", "(d)", "(c)"], _lab
Q[5]["parts"][3]["label"], Q[5]["parts"][4]["label"] = "(c)", "(d)"

# ---- asset plan (final) ----------------------------------------------------------------------
def A(q, slot, part):
    return {"question": q, "part": part, "slot": slot, "ordinal": 0,
            "storage_path": "JPJC_H2_P2_Q%d_%s_2026.png" % (q, slot), "n_refs": 1}


PLAN = [A(2, "a", "(a)"), A(2, "bii", "(b)(ii)"),
        A(3, "b", "(b)"), A(3, "b2", "(b)"), A(3, "e", "(e)"),
        A(4, "intro", None),
        A(5, "intro", None), A(5, "b", "(b)"), A(5, "d", "(c)")]   # file keeps slot d (the user snipped it as Q5_d); the part is now (c)
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
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    if "[Total" in h:
        bad.append("Q%d: leftover [Total] in html" % qn)
    if not r["content_text"].rstrip().endswith("[Total: %d]" % r["marks"]):
        bad.append("Q%d: content_text does not end with its [Total]" % qn)
    if h.count("<div") != h.count("</div>"):
        bad.append("Q%d: unbalanced div" % qn)
    if "​" in h or "​" in r["content_text"] or "<br>" in h:
        bad.append("Q%d: leftover zero-width space or <br>" % qn)
    if "<sup>o</sup>" in h:
        bad.append("Q%d: leftover letter-o superscript" % qn)
    got = sum(p["marks"] or 0 for p in r["parts"])
    if got != r["marks"]:
        bad.append("Q%d: parts sum %d vs total %d" % (qn, got, r["marks"]))
assert sum(r["marks"] for r in Q.values()) == 75
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d (all block)" % (len(Q), len(PLAN)))
for l in LOG:
    print("  " + l)
