"""Hand transcription of A Level (SEAB) 9729/01 Oct/Nov 2025 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as build_alevel_p1.py / extract_questions).
Run from the repo root:  python3 ingest/build_alevel25_p1.py <outdir>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, ".")
from ingest.render_questions import _strip_tags

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2025
FIG = '<div class="fig">figure</div>'
M = "−"                       # minus
DB = '<p class="qstem">Use of the Data Booklet is relevant to this question.</p>'
def p(s): return '<p class="qstem">%s</p>' % s
def c(s): return '<p class="c">%s</p>' % s
def ol(*items): return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % i for i in items)
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % i for i in items)
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def qt(*rows):
    return '<table class="qt">%s</table>' % "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % x for x in r) for r in rows)
CL = '<i class="el">l</i>'
K = "<i>K</i>"
MDM = "mol dm" + sup(M + "3")
TIMES = "×"
DH = "Δ" + i("H"); DS = "Δ" + i("S"); DG = "Δ" + i("G")
DGs = DG + sup("⦵"); E0 = i("E") + sup("⦵")
EM = " "                 # em space (equation + E value on one line)
CHECK, CROSS = "✓", "✗"

Q = {}   # qn -> dict(stem=[blocks], opts={L: html or [cells]}, hdr=None|[cells], tail=[blocks])
def q(n, stem, opts=None, hdr=None, tail=None):
    Q[n] = dict(stem=stem, opts=opts or {}, hdr=hdr, tail=tail or [])

# ---- Q1 -------------------------------------------------------------------
q(1, [p("The table shows the nucleon number, the number of neutrons and the number of electrons in four different particles, W, X, Y and Z."),
      qt(["", "nucleon number", "number of neutrons", "number of electrons"],
         ["W", "207", "122", "84"], ["X", "208", "126", "82"],
         ["Y", "209", "125", "86"], ["Z", "210", "127", "83"]),
      p("Which pair represents atoms of two different elements?")],
  {"A": "W and Y", "B": "W and Z", "C": "X and Y", "D": "X and Z"})
# ---- Q2 -------------------------------------------------------------------
q(2, [DB, p("The charge on one mole of particle Q is +96 500 C."),
      p("One mole of particle R has a mass of less than 0.500 g."),
      p("Which statement is correct?")],
  {"A": "Q could be a proton only; R could be a proton, a neutron or an electron.",
   "B": "Q could be a proton only; R could be an electron only.",
   "C": "Q could be a proton or an electron; R could be a proton, a neutron or an electron.",
   "D": "Q could be a proton or an electron; R could be an electron only."})
# ---- Q3 -------------------------------------------------------------------
q(3, [p("Uranium hexafluoride, UF" + sub(6) + ", has a boiling point of 330 K."),
      p("Thallium(I) iodide, T" + CL + "I, has a melting point of 715 K. It conducts electricity when molten."),
      p("What are the lattice structures of these two substances in the solid state?")],
  {"A": ["ionic", "giant molecular"], "B": ["ionic", "ionic"],
   "C": ["simple molecular", "giant molecular"], "D": ["simple molecular", "ionic"]},
  hdr=["lattice structure of solid UF" + sub(6), "lattice structure of solid T" + CL + "I"])
# ---- Q4 -------------------------------------------------------------------
q(4, [p("What is a correct statement with a correct reason about the trends in ionisation energies in the Periodic Table?")],
  {"A": "Boron has a lower first ionisation energy than beryllium because a 2p electron is more shielded from the nuclear charge than a 2s electron.",
   "B": "Copper and nickel have first ionisation energies that only differ by 9 kJ mol" + sup(M + "1") + " because they both lose an electron from a 3d orbital.",
   "C": "The first ionisation energies increase from oxygen to neon across Period 2 because each successive element has one more electron in the outer energy level.",
   "D": "The second ionisation energy of phosphorus is greater than the first ionisation energy of sulfur because the ions formed have the same electronic configuration but sulfur has the greater nuclear charge."})
# ---- Q5 -------------------------------------------------------------------
q(5, [p("L and M are chlorides of elements from the third period. Both L and M produce a colourless solution when added to water and stirred. The table shows more information about L and M."),
      qt(["", "melting point / K", "electrical conductivity of molten chloride"],
         ["L", "1074", "high"], ["M", "203", "negligible"]),
      p("Which statement best describes the nature of the aqueous solutions of L and M?")],
  {"A": "Both solutions are neutral.", "B": "Both solutions are alkaline.",
   "C": "The solution of L is neutral; the solution of M is acidic.",
   "D": "The solution of L is alkaline; the solution of M is neutral."})
# ---- Q6 -------------------------------------------------------------------
q(6, [DB, p("Iron(III) oxide can be reduced to iron using the sequence of reactions shown."),
      c("C(s) + O" + sub(2) + "(g) → CO" + sub(2) + "(g)"),
      c("CO" + sub(2) + "(g) + C(s) → 2CO(g)"),
      c("Fe" + sub(2) + "O" + sub(3) + "(s) + 3CO(g) → 2Fe(l) + 3CO" + sub(2) + "(g)"),
      p("What is the minimum volume of oxygen, measured at s.t.p., required to produce 0.422 g of iron?")],
  {"A": "129 cm" + sup(3), "B": "229 cm" + sup(3), "C": "258 cm" + sup(3), "D": "386 cm" + sup(3)})
# ---- Q7 -------------------------------------------------------------------
q(7, [p("Which pair is <b>not</b> a Brønsted–Lowry conjugate acid–base pair?")],
  {"A": "BH" + sub(3) + " and BH" + sub(4) + sup(M),
   "B": "H" + sub(2) + "PO" + sub(4) + sup(M) + " and HPO" + sub(4) + sup("2" + M),
   "C": "HCO" + sub(2) + "H" + sub(2) + sup("+") + " and HCO" + sub(2) + "H",
   "D": "NH" + sub(4) + sup("+") + " and NH" + sub(3)})
# ---- Q8 -------------------------------------------------------------------
q(8, [p("A hydrogen–oxygen fuel cell releases energy by oxidising hydrogen at one electrode and reducing oxygen at the other electrode. The ions produced then combine to form water."),
      p("The overall process is summarised by the following equation."),
      c("2H" + sub(2) + "(g) + O" + sub(2) + "(g) → 2H" + sub(2) + "O(l)"),
      p("Which row correctly shows the signs for " + DH + ", " + DS + " and " + DG + " for this process in the hydrogen–oxygen fuel cell at room temperature?")],
  {"A": [M, M, M], "B": [M, M, "+"], "C": ["+", M, M], "D": [M, "+", M]},
  hdr=[DH, DS, DG])
# ---- Q9 -------------------------------------------------------------------
q(9, [p("The Boltzmann distributions and activation energies, " + i("E") + sub("a") + ", for a homogeneous gaseous reaction under different conditions, J and K, are shown."),
      FIG,
      p("Which change in conditions would result in the changes from J to K?")],
  {"A": "an increase in temperature only", "B": "a decrease in temperature only",
   "C": "adding a catalyst and decreasing the temperature",
   "D": "adding a catalyst and increasing the temperature"})
# ---- Q10 ------------------------------------------------------------------
q(10, [p("Nickel reacts with carbon monoxide on heating."),
       c("Ni(s) + 4CO(g) ⇌ Ni(CO)" + sub(4) + "(g)"),
       p("An excess of Ni(s) is placed in a flask containing CO(g) at 1 atm and 350 K. After no further change occurs, the pressure in the flask is 0.37 atm at a temperature of 350 K."),
       p("What is the partial pressure of CO(g) in this equilibrium mixture?")],
  {"A": "0.16 atm", "B": "0.21 atm", "C": "0.37 atm", "D": "0.63 atm"})
# ---- Q11 ------------------------------------------------------------------
q(11, [p("The graph shows how " + DGs + " changes with temperature for the reaction shown."),
       c("H" + sub(2) + "O(g) + CO(g) ⇌ H" + sub(2) + "(g) + CO" + sub(2) + "(g)"),
       FIG,
       p("Equimolar amounts of H" + sub(2) + "O and CO were introduced into a sealed container and allowed to reach equilibrium."),
       p("At which points will the concentration of H" + sub(2) + " be <b>greater</b> than the concentration of H" + sub(2) + "O at equilibrium?")],
  {"A": "1 and 2", "B": "1 only", "C": "2, 3 and 4", "D": "3 and 4 only"})
# ---- Q12 ------------------------------------------------------------------
q(12, [p("The diagram shows compound X."), FIG, c("X"),
       p("Which molecules have the same empirical formula as compound X?"),
       FIG],     # molecules 1-3 are ONE snip WITH the printed numbers (a figure inside an <li> floated far from its number)
  {"A": "1, 2 and 3", "B": "1 and 2 only", "C": "1 only", "D": "2 only"})
# ---- Q13 ------------------------------------------------------------------
q(13, [p("A saturated solution of zinc(II) hydroxide has a " + K + sub("sp") + " value of 2.3 " + TIMES + " 10" + sup(M + "14") + "."),
       p("What is the concentration of this solution?")],
  {"A": "1.1 " + TIMES + " 10" + sup(M + "5") + " " + MDM,
   "B": "1.8 " + TIMES + " 10" + sup(M + "5") + " " + MDM,
   "C": "2.3 " + TIMES + " 10" + sup(M + "5") + " " + MDM,
   "D": "2.8 " + TIMES + " 10" + sup(M + "5") + " " + MDM})
# ---- Q14 ------------------------------------------------------------------
q(14, [p("Which types of reaction occur in the two-stage conversion of 1-bromopropane to 2-bromopropane?")],
  {"A": "substitution followed by elimination", "B": "addition followed by elimination",
   "C": "elimination followed by addition", "D": "elimination followed by substitution"})
# ---- Q15 ------------------------------------------------------------------
q(15, [p("Compound P has a molecular formula of C" + sub(4) + "H" + sub(8) + "O" + sub(2) + "."),
       p("Compound P contains only one functional group, which can be a carboxylic acid or an ester."),
       p("How many constitutional (structural) isomers are possible for compound P?")],
  {"A": "2", "B": "4", "C": "5", "D": "6"})
# ---- Q16 ------------------------------------------------------------------
q(16, [p("Which gas takes part in the production of both photochemical smog and the formation of acid rain?")],
  {"A": "CO", "B": "CO" + sub(2), "C": "NO" + sub(2), "D": "SO" + sub(2)})
# ---- Q17 ------------------------------------------------------------------
q(17, [p("An unknown organic compound is tested with warm silver nitrate solution. No visible result is seen after one hour. Two students see the experiment and each make a comment."),
       p("student 1" + EM + "This compound is definitely a halogenoarene, but it is <b>not</b> possible to state which halogen is present."),
       p("student 2" + EM + "This compound is definitely <b>not</b> a halogenoalkane."),
       p("Which students are correct?")],
  {"A": [CHECK, CROSS], "B": [CROSS, CHECK], "C": [CHECK, CHECK], "D": [CROSS, CROSS]},
  hdr=["student 1", "student 2"],
  tail=[p("key: " + CHECK + " = correct; " + CROSS + " = <b>not</b> correct")])
# ---- Q18 ------------------------------------------------------------------
q(18, [p("In which reaction does the organic reactant behave as a nucleophile?")],
  {"A": "CH" + sub(4) + " + C" + CL + sub(2) + " → CH" + sub(3) + "C" + CL + " + HC" + CL,
   "B": "CH" + sub(3) + "I + OH" + sup(M) + " → CH" + sub(3) + "OH + I" + sup(M),
   "C": "CH" + sub(2) + "=CH" + sub(2) + " + Br" + sub(2) + " → CH" + sub(2) + "BrCH" + sub(2) + "Br",
   "D": "CH" + sub(3) + "COCH" + sub(3) + " + HCN → CH" + sub(3) + "C(OH)(CN)CH" + sub(3)})
# ---- Q19 ------------------------------------------------------------------
q(19, [p("Chlorine gas, " + sup("35") + "C" + CL + sub(2) + ", and ethane react together by a free-radical substitution mechanism that occurs via a series of reactions."),
       ul("In reaction K, one species produces two species with exactly half the mass of the original species.",
          "In reaction L, two species of identical mass interact to produce one species of twice the mass."),
       p("Which types of reaction are reaction K and reaction L?")],
  {"A": ["initiation", "propagation"], "B": ["initiation", "termination"],
   "C": ["propagation", "propagation"], "D": ["propagation", "termination"]},
  hdr=["reaction K", "reaction L"])
# ---- Q20 ------------------------------------------------------------------
q(20, [p("Which reagent and catalyst convert benzene into G?"), FIG, c("G")],
  {"A": ["CH" + sub(3) + "CHC" + CL + sub(2), "A" + CL + "C" + CL + sub(3)],
   "B": ["CH" + sub(3) + "CHC" + CL + sub(2), "PC" + CL + sub(3)],
   "C": ["CH" + sub(3) + "CH(CH" + sub(2) + "C" + CL + ")" + sub(2), "A" + CL + "C" + CL + sub(3)],
   "D": ["CH" + sub(3) + "CH(CH" + sub(2) + "C" + CL + ")" + sub(2), "PC" + CL + sub(3)]},
  hdr=["reagent", "catalyst"])
# ---- Q21 ------------------------------------------------------------------
q(21, [p("An ester, J, is hydrolysed by heating with aqueous sulfuric acid. The resulting reaction mixture is heated under reflux with acidified potassium dichromate(VI) solution. The final mixture of products contains only one organic compound."),
       p("What could ester J be?"),
       ol("CH" + sub(3) + "CO" + sub(2) + "C" + sub(2) + "H" + sub(5),
          "CH" + sub(3) + "CH" + sub(2) + "CO" + sub(2) + "CH(CH" + sub(3) + ")" + sub(2),
          "CH" + sub(3) + "CH" + sub(2) + "CH" + sub(2) + "CO" + sub(2) + "CH" + sub(2) + "CH" + sub(3))],
  {"A": "1 and 2", "B": "1 only", "C": "2 and 3", "D": "3 only"})
# ---- Q22 ------------------------------------------------------------------
q(22, [p("Which molecules may be used in protein formation?"),
       ol("2,6-diaminohexanoic acid", "2-aminobenzoic acid", "3-aminopropanoic acid")],
  {"A": "1, 2 and 3", "B": "1 only", "C": "2 and 3 only", "D": "3 only"})
# ---- Q23 ------------------------------------------------------------------
q(23, [p("Which statement about ethanoyl chloride is correct?")],
  {"A": "It reacts with aminoethane to produce C" + sub(2) + "H" + sub(5) + "NHCOCH" + sub(3) + ".",
   "B": "It reacts with phenol to produce CH" + sub(3) + "COC" + sub(6) + "H" + sub(5) + ".",
   "C": "It reacts with propan-2-ol to produce C" + sub(2) + "H" + sub(5) + "CO" + sub(2) + "CH(CH" + sub(3) + ")" + sub(2) + ".",
   "D": "It reacts with water to produce CH" + sub(3) + "CHO."})
# ---- Q24 ------------------------------------------------------------------
q(24, [p("In the gaseous state, molecules X, Y and Z behave as Lewis bases."), FIG,
       p("In which order do the base strengths of X, Y and Z increase?")],
  {"A": "Y → X → Z", "B": "Y → Z → X", "C": "Z → X → Y", "D": "Z → Y → X"})
# ---- Q25 ------------------------------------------------------------------
q(25, [p("A student plans to prepare a sample of C" + sub(6) + "H" + sub(5) + "CH" + sub(2) + "CO" + sub(2) + "CH" + sub(3) + " in a three-step process."),
       p("Three routes are proposed. The intermediates P and Q are not necessarily the same in each route."),
       ol(FIG, FIG, FIG),
       p("Which routes will be successful?")],
  {"A": "1, 2 and 3", "B": "1 and 2 only", "C": "1 only", "D": "2 and 3 only"})
# ---- Q26 ------------------------------------------------------------------
q(26, [DB, p("The following cell was set up under standard conditions. The cell contains a silver half-cell, Ag" + sup("+") + "(aq) / Ag(s), and a chlorine half-cell, C" + CL + sub(2) + "(g) / C" + CL + sup(M) + "(aq)."),
       p("A 0.1 " + MDM + " solution of sodium chloride was then added to the silver half-cell."),
       p("What are the effects on the standard electrode potential of the silver half-cell and the standard cell potential?")],
  {"A": ["+0.8", "+0.56"], "B": ["less than +0.8", "less than +0.56"],
   "C": ["less than +0.8", "greater than +0.56"], "D": ["greater than +0.8", "less than +0.56"]},
  hdr=["standard electrode potential of silver half-cell / V", "standard cell potential / V"])
# ---- Q27 ------------------------------------------------------------------
q(27, [DB, p("What is the value of " + DGs + " for the reaction shown?"),
       c("2Cr(s) + 3Cu" + sup("2+") + "(aq) ⇌ 2Cr" + sup("3+") + "(aq) + 3Cu(s)" + EM + E0 + " = +1.08 V")],
  {"A": M + "625 kJ " + "mol" + sup(M + "1"), "B": M + "313 kJ " + "mol" + sup(M + "1"),
   "C": M + "208 kJ " + "mol" + sup(M + "1"), "D": M + "104 kJ " + "mol" + sup(M + "1")})
# ---- Q28 ------------------------------------------------------------------
q(28, [DB, p("Which metal ion is reduced to its metal by reaction with nickel under standard conditions?")],
  {"A": "Cr" + sup("2+"), "B": "Mn" + sup("2+"), "C": "Sn" + sup("2+"), "D": "V" + sup("2+")})
# ---- Q29 ------------------------------------------------------------------
q(29, [DB, p("A current of X amperes is passed through an aqueous solution of copper ions for 2 hours. Y g of copper is deposited on the cathode."),
       p("Which expression gives the charge on the copper ion?")],
  {"A": frac("X " + TIMES + " 2 " + TIMES + " 60 " + TIMES + " 63.5", "96500 " + TIMES + " Y"),
   "B": frac("X " + TIMES + " 2 " + TIMES + " 60 " + TIMES + " 60 " + TIMES + " 63.5", "96500 " + TIMES + " Y"),
   "C": frac("X " + TIMES + " Y " + TIMES + " 2 " + TIMES + " 60 " + TIMES + " 60", "96500 " + TIMES + " 63.5"),
   "D": frac("96500 " + TIMES + " Y", "X " + TIMES + " 2 " + TIMES + " 60 " + TIMES + " 60 " + TIMES + " 63.5")})
# ---- Q30 ------------------------------------------------------------------
q(30, [DB, p("Element M has a proton number between 22 and 29."), p("Which row is correct?")],
  {"A": ["greater", "less exothermic"], "B": ["greater", "more exothermic"],
   "C": ["smaller", "less exothermic"], "D": ["smaller", "more exothermic"]},
  hdr=["density of one mole of M compared to one mole of Ca",
       "value of lattice energy of MC" + CL + sub(2) + " compared to CaC" + CL + sub(2)])

# ---------------------------------------------------------------------------
def strip(h):
    # _strip_tags separates </li|p|tr|div> but not </td>: stem data tables (Q1, Q5) would glue their cells
    return _strip_tags(h.replace(FIG, " ").replace("</td>", "</td> "))
rows, plan = [], []
#: stem-figure slots per question, in DOM order of the placeholders (stem1, stem2, ...)
STEM_FIG = {9: 1, 12: 2, 20: 1, 24: 1, 25: 3}
#: storage-path overrides (a re-saved snip under a new name to dodge browser caching)
FILE_OVERRIDE = {(12, 2): "SEAB_H2_P1_Q12_stem2b_2025.png"}
#: removed from the bank (user ruling 2026-10-29): Q11 needs the dG-K relationship, out of 9476.
#: Question numbers are NOT renumbered (HCI 2024 P1 Q15 precedent): 29 questions, Q11 absent.
REMOVED = {11}
for n in sorted(Q):
    if n in REMOVED: continue
    d = Q[n]; parts = list(d["stem"])
    trs = []
    if d["hdr"]:
        trs.append('<tr><td class="ol"></td>%s</tr>' % "".join("<td>%s</td>" % h for h in d["hdr"]))
    for L in "ABCD":
        v = d["opts"][L]; cells = v if isinstance(v, list) else [v]
        trs.append('<tr><td class="ol">%s</td>%s</tr>' % (L, "".join("<td>%s</td>" % x for x in cells)))
    parts.append('<table class="opts-table">%s</table>' % "".join(trs))
    parts.extend(d["tail"])
    html = "\n".join(parts)
    bits = [strip("\n".join(d["stem"]))]
    if d["hdr"]: bits.append(" | ".join(strip(h) for h in d["hdr"]))
    ojs = {}
    for L in "ABCD":
        v = d["opts"][L]
        t = " | ".join(strip(x) for x in (v if isinstance(v, list) else [v]) if strip(x))
        ojs[L] = t
        bits.append("%s %s" % (L, t))
    if d["tail"]: bits.append(strip("\n".join(d["tail"])))
    txt = re.sub(r"\s+", " ", " ".join(b for b in bits if b)).strip()
    rows.append({"question_number": n, "content_html": html, "content_text": txt, "options": ojs})
    for k in range(1, STEM_FIG.get(n, 0) + 1):
        plan.append({"question": n, "kind": "block", "slot": "stem%d" % k, "ordinal": k,
                     "storage_path": FILE_OVERRIDE.get((n, k), "SEAB_H2_P1_Q%d_stem%d_%d.png" % (n, k, YEAR))})
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", len(plan), "assets")
# sanity: placeholder counts must equal block assets per question; all four options present
for r in rows:
    nfig = r["content_html"].count('class="fig"')
    nblk = sum(1 for a in plan if a["question"] == r["question_number"] and a["kind"] == "block")
    assert nfig == nblk, (r["question_number"], nfig, nblk)
    assert set(r["options"]) == set("ABCD") and all(r["options"].values()), r["question_number"]
print("placeholder/asset counts agree; every question has options A-D")
