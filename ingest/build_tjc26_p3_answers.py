"""Hand transcription of the TJC 2026 H2 Prelim Paper 3 (9476/03) suggested solutions -> worked_solutions.json +
answer_assets.json (feeds gen_answers_migration.py --type structured).

Source: the school's "QP and Ans" Word file (question paper with the mark scheme painted in: answers blue, marking notes red,
underlines on the mark-bearing keywords) and its Word-exported PDF. Text is typed from the docx (which carries the underlines);
the 20 answer figures are snipped by crop_tjc26_p3_answers.py.

Run from the repo root:
    python3 ingest/build_tjc26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_tjc26_p3.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions as build_tjc26_p2_answers.py (claude/style-guide.md SS6). Dropped: [n] marks, ticks, the "2 ticks = 1 mark" tallies.
Red MARKING notes (quote both values / ecf / max / ECF structure notes / mark allocations) are kept as span.note.
Q5(d) and Q6(d): the school's reasoning tables are typed as table.cmp; structures are snipped figures (typed bold labels P:, Q: ...).
Q6(c)(ii) and Q6(d): the school's "or" alternatives are kept (typed "Or"), each with its own figure.

FIXES made to the school's answers (listed to the user; veto-able):
  1(c)(ii)  "volume of the CO2 gas molecules are significant" -> "is significant";
  2(a)(ii)  "wrt" -> "with respect to";
  3(b)(ii)  the school labels E(Be2+/Be) = -1.85 V as "E_ox"; it is the reduction potential, labelled E_red (the E_cell working is unchanged);
  4(b)(i)   "ring to opened up" -> "ring to open up";
  5(b)(ii)  "[HPO4 2]" -> "[HPO4 2-]";   5(b)(iii) "ECF of pKa value from (b)(i)" -> "(b)(ii)";
  5(d)      "ethanoic aicd" -> "ethanoic acid";  "N is not carbonyl compound" -> "M is not a carbonyl compound" (M is what is being deduced);
  6(d)      "Q contains primary alcohol and amine" (row for test 4) -> "S contains ...";
  Q4(c)(ii) the school's "OR" equation C6H10 + 4[O] -> C6H10O4 is typed under the structure equation.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "TJC_H2_P3", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
DEL = "Δ"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def C(*parts): return '<p class="c">%s</p>' % "".join(parts)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW = " → "
EQ = " ⇌ "
BOND = "–"
MDM = "mol dm" + sup(M + "3")
STD = sup('<span class="pl-sym">⦵</span>')
ESTD = i("E") + STD
H2O = "H" + sub(2) + "O"
CO2 = "CO" + sub(2)
EMINUS = "e" + sup(M)
EM = "&emsp;"
NB = "&nbsp;"
CL = "C" + L
HCL = "H" + CL
PKA = "p" + i("K") + sub("a")
KP = i("K") + sub("p")
KSP = i("K") + sub("sp")
T12 = i("t") + sub("1/2")
CH3COCH3 = "CH" + sub(3) + "COCH" + sub(3)
HPO4 = "HPO" + sub(4) + sup("2" + M)
H2PO4 = "H" + sub(2) + "PO" + sub(4) + sup(M)

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)",
      P(A(u("Ionic-dipole interactions") + " formed between water and ions in sodium nitrate " +
          u("release sufficient energy to overcome the ionic bonds") + " between ions in " +
          u("sodium nitrate and hydrogen bonds between water molecules") + "."))),
 PART("(b)(i)",
      P(A("Fig. 1.1 shows two different types of nitrogen–oxygen bonds whereas Table 1.1 only shows one value for the nitrogen–oxygen bond length.")),
      P(A("If Fig. 1.1 is true, there should be two different values for bond length with one for the N–O bond and another for N=O."))),
 PART("(b)(ii)",
      P(A(u("Both the nitrogen and oxygen atoms are sp" + sup(2) + " hybridised") + ", where one 2s and two 2p atomic orbitals hybridise to form degenerate sp" +
          sup(2) + " hybrid orbitals, with an unhybridised 2p orbital.")),
      P(A("Each N–O bond has " + u("1 σ bond") + " formed from " + u("head-on overlap between each sp" + sup(2) + " hybrid orbital of adjacent N and O atoms") + ".")),
      P(A(u("π bond / π electron cloud") + " is formed from " + u("side-way overlap between the unhybridised 2p orbital of N and unhybridised 2p orbital of adjacent O atoms") + ".")),
      P(A("Electrons in the unhybridised 2p orbitals can " + u("delocalise") + ", hence the N–O bond in the nitrate ion has the " + u("same") + " bond length.")),
      IMG(1, "bii")),
 PART("(c)(i)",
      P(A("Volume of gas " + u("particles") + " is negligible compared to volume of container.")),
      P(A("Perfectly elastic collision between gas " + u("particles") + "."))),
 PART("(c)(ii)",
      P(A("At lower pressures, " + CO2 + " shows " + u("negative deviation") + " as there are " +
          u("significant instantaneous dipole–induced dipole (id–id) attractions between " + CO2 + " molecules") + ". As a result, its molecules " +
          u("collide with the walls of the container with lower frequency and with lesser force") + ". Thus " +
          u(i("p") + sub("real") + " < " + i("p") + sub("ideal") + " and " + i("pV") + "/" + i("nRT") + " < 1") + ".")),
      P(A("At high pressure, the " + u("total volume occupied by the gas is reduced") + ". The " +
          u("volume of the " + CO2 + " gas molecules is significant when compared to the total volume of the gas") + " i.e. " +
          u(i("V") + sub("real") + " > " + i("V") + sub("ideal") + " and " + i("pV") + "/" + i("nRT") + " > 1") + ". Hence, there is " + u("positive deviation") + "."))),
 PART("(c)(iii)",
      P(A("Graph showing both greater positive and negative deviation for SO" + sub(2) + ".")),
      IMG(1, "ciii")),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A("This is to ensure that the " + u("concentration") + " of propanone stays almost " + u("constant / does not change") + " and hence " +
          u("does not affect the rate") + "."))),
 PART("(a)(ii)",
      P(A("Comparing expt 2 and 3,")),
      P(A("when [H" + sup("+") + "] increases 1.33 times, rate increases 1.33 times i.e. directly proportional and the order of reaction is first order with respect to [H" + sup("+") + "].")),
      P(A("Or")),
      P(A("Let the rate equation be rate = " + i("k") + "[H" + sup("+") + "]" + sup(i("x")) + "[CH" + sub(3) + "OH]" + sup(i("y")))),
      C(A(frac(u("2.25"), "3.00") + " = " + frac(u(i("k") + "(0.030)" + sup(i("x"))), i("k") + "(0.040)" + sup(i("x"))) + EM + "⇒" + EM + i("x") + " = 1")),
      P(A("reaction is first order with respect to [H" + sup("+") + "]")),
      P(A("Comparing expt 1 and 2,")),
      C(A(frac("1.00", "2.25") + " = " + frac(u(i("k") + "(0.020)(0.020)" + sup(i("y"))), i("k") + "(0.030)(0.030)" + sup(i("y"))) + EM + "⇒" + EM + i("y") + " = 1")),
      P(A("reaction is first order with respect to CH" + sub(3) + "OH")),
      P(A("or Comparing expt 1 and 3,")),
      C(A(frac("1.00", "3.00") + " = " + frac(u(i("k") + "(0.020)(0.020)" + sup(i("y"))), i("k") + "(0.040)(0.030)" + sup(i("y"))) + EM + "⇒" + EM + i("y") + " = 1")),
      P(A("reaction is first order with respect to CH" + sub(3) + "OH")),
      P(N("1 mark for the correct order of reaction and reasoning."))),
 PART("(b)(i)",
      P(A("For the concentration of propanone to decrease to 12.5% of its initial concentration, 3 " + T12 + " have passed.")),
      P(A("Time taken = 3 × 165 = 495 s"))),
 PART("(b)(ii)",
      P(A(T12 + " " + u("would not change as it is independent of the initial concentration of propanone") + ". Hence, the time taken for it to decrease to 12.5% of its initial concentration " +
          u("remained unchanged") + "."))),
 PART("(c)(i)",
      P(A("CH" + sub(3) + "C(OH)=CH" + sub(2) + " + I" + sub(2) + ARROW + "CH" + sub(3) + "C" + sup("+") + "(OH)CH" + sub(2) + "I + I" + sup(M)))),
 PART("(c)(ii)",
      P(A(u("Step 1") + " is the slowest step (rate determining step) as the " + u("rate equation indicates 1 molecule of " + CH3COCH3 + " reacts with 1 H" + sup("+") + " ion") +
          " in the slowest step."))),
 PART("(c)(iii)",
      P(A("The H" + sup("+") + " ions " + u("provide an alternative pathway") + ", with a " + u("lower " + i("E") + sub("a")) + " than that of an uncatalysed reaction.")),
      P(A("The " + u("number of molecules having energy greater than or equal to " + i("E") + sub("a") + "’ increases significantly") + ". The " +
          u("frequency of effective collisions increases") + ", " + u("rate constant, " + i("k") + " increases") + " and thus rate increases.")),
      P(N("Boltzmann distribution sketch with labelling and legend.")),
      IMG(2, "ciii")),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)",
      P(A(u("Thermal stability decreases") + " down the group. " + u("Atomic radius/size increases") + " from " + CL + " to I, " + u("less effective overlap") +
          " of atomic orbitals of H and X. " + u("Bond strength decreases") + " from H" + BOND + CL + " to H" + BOND + "I and " + u("less energy") +
          " needed to break the H" + BOND + "X bond."))),
 PART("(b)(i)",
      P(A(ESTD + "(Mg" + sup("2+") + "/Mg) = " + M + "2.38 V")),
      P(A(ESTD + "(Ca" + sup("2+") + "/Ca) = " + M + "2.87 V")),
      P(N("Quote both values.")),
      P(A(u("Reactivity increases") + " down the Group. Down the Group, " + u(ESTD + "(M" + sup("2+") + "/M) becomes more negative") + ", implying the metals are " +
          u("more easily oxidised") + " / " + u("valence electrons are more easily lost") + "."))),
 PART("(b)(ii)",
      P(A("2" + H2O + " + 2e" + EQ + "H" + sub(2) + " + 2OH" + sup(M) + EM + ESTD + sub("red") + " = " + M + "0.83 V")),
      P(A("Be" + sup("2+") + " + 2e" + EQ + "Be" + EM + ESTD + sub("red") + " = " + M + "1.85 V")),
      P(A(ESTD + sub("cell") + " = " + M + "0.83 − (" + M + "1.85) = " + u("+1.02 V > 0") + ", so reaction is spontaneous"))),
 PART("(b)(iii)",
      P(A("Beryllium is a reactive metal (similar to aluminium) and " + u("reacts readily with oxygen") + " in the air to form a protective layer of " + u("BeO") +
          " which " + u("protects the metal from reaction with water") + "."))),
 PART("(c)(i)",
      IMG(3, "ci"),
      P(N("Voltmeter and salt bridge.")),
      P(N("Fully labelled components of the SHE half-cell with standard conditions.")),
      P(N("Fully labelled components of the I" + sub(3) + sup(M) + "(aq)/I" + sup(M) + "(aq) half-cell with standard conditions."))),
 PART("(c)(ii)",
      C(A(KP + " = " + frac("(" + i("P") + sub("AlI₃") + ")" + sup(2), i("P") + sub("Al₂I₆")) + EM + "kPa / Pa / atm"))),
 PART("(c)(iii)",
      TBL(["", "Al" + sub(2) + "I" + sub(6) + "(g)", "⇌", "2AlI" + sub(3) + "(g)"],
          ["Initial " + i("P") + " / kPa", "17", "", "0"],
          ["Change in " + i("P") + " / kPa", M + "0.4(17) = " + M + "6.8", "", "+2(6.8)"],
          ["Eqm " + i("P") + " / kPa", "10.2", "", "13.6"]),
      P(N("1 mark for working; 1 mark for the answer.")),
      C(A(KP + " = " + frac("(13.6)" + sup(2), "10.2") + " = 18.1 kPa"))),
 PART("(c)(iv)",
      P(A(u(KP + " increases"))),
      P(A("Position of equilibrium shifts " + u("right") + " to " + u("absorb heat") + "."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)",
      P(A(u("Resonance stabilisation") + " causes the π electron cloud in benzene to be " + u("less reactive") + " compared to C=C."))),
 PART("(b)(i)",
      P(A(u("Ring strain") + " (or discuss bond angle) resulting in " + u("weaker (C–O and C–C) bonds / ring to open up") + "."))),
 PART("(b)(ii)",
      P(A("Both have " + u("simple molecular structures") + ".")),
      P(A(u("More energy") + " is needed to overcome the " + u("stronger hydrogen bonding between cyclohexane-1,2-diol molecules") + " compared to " +
          u("weaker permanent dipole–permanent dipole attractions") + " between cyclohexene oxide molecules."))),
 PART("(c)(i)",
      P(A("Acidified KMnO" + sub(4) + ", heat")),
      P(A("Decolourisation of purple KMnO" + sub(4)))),
 PART("(c)(ii)",
      IMG(4, "cii"),
      P(A("Or")),
      P(A("C" + sub(6) + "H" + sub(10) + " + 4[O]" + ARROW + "C" + sub(6) + "H" + sub(10) + "O" + sub(4)))),
 PART("(c)(iii)",
      P(A("Polymers are " + u("macromolecules") + " built up from " + u("monomers") + ", with " +
          u("average relative molecular mass of at least 1000 or at least 100 repeat units") + "."))),
 PART("(c)(iv)",
      P(A(CL + "OC(CH" + sub(2) + ")" + sub(4) + "CO" + CL))),
 PART("(c)(v)", IMG(4, "cv")),
 PART("(c)(vi)",
      P(N("Any one of the following.")),
      P(A("Reaction is " + u("reversible") + " hence " + u("low yield") + " of polymer.")),
      P(A("Or")),
      P(A("Reaction " + u("requires catalyst and heat") + ".")),
      P(A("Or")),
      P(A("Hexanedioic acid is " + u("less reactive") + " than compound " + b("M") + "."))),
 PART("(c)(vii)",
      P(A("Polymer " + b("O") + " is a " + u("polyester") + " (or contains " + u("ester bonds") + ") that can undergo " + u("acidic hydrolysis") + "."))),
 PART("(d)(i)",
      P(A(u("H" + sub(2) + "O(g) (or steam) with H" + sub(3) + "PO" + sub(4) + " catalyst"))),
      P(b("P") + ":"),
      IMG(4, "di")),
 PART("(d)(ii)", P(A(u("Condensation")))),
 PART("(e)(i)", IMG(4, "ei")),
 PART("(e)(ii)",
      IMG(4, "eii"),
      P(N("Deduct 1 mark if curly arrows are missing or incorrect."))),
 PART("(e)(iii)",
      P(A("The new radical formed is a " + u("secondary") + " radical that is " + u("more stable") + " due to " + u("more electron-donating alkyl") + " groups."))),
 PART("(e)(iv)",
      P(A("Back-biting results in a " + u("higher number") + " of " + u("branched chains") + ", the polymer chains are " + u("packed less closely") +
          " together resulting in a lower density."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A("Na" + sub(2) + "O" + EM + "P" + sub(4) + "O" + sub(10)))),
 PART("(a)(ii)",
      P(A("Na" + sub(2) + "O + " + H2O + ARROW + "2NaOH" + EM + "pH = 13 or 14")),
      P(A("P" + sub(4) + "O" + sub(10) + " + 6" + H2O + ARROW + "4H" + sub(3) + "PO" + sub(4) + EM + "pH = 1 or 2"))),
 PART("(b)(i)",
      P(A("A " + u("buffer solution") + " is a solution that " + u("resists changes in pH") + " upon addition of a " + u("small amount of an acid") + " or base."))),
 PART("(b)(ii)",
      P(A("When [" + HPO4 + "] = [" + H2PO4 + "], solution is at maximum buffering capacity")),
      P(A("pH = " + PKA + " = 7.20"))),
 PART("(b)(iii)",
      P(A("At pH 6.90, [" + HPO4 + "] / [" + H2PO4 + "] = 0.50")),
      P(A("[" + HPO4 + "] = 0.50 × 0.06 = 0.03 " + MDM)),
      P(A("[NaOH] added = 0.002 ÷ (200/1000) = 0.01 " + MDM)),
      P(A(H2PO4 + " + OH" + sup(M) + ARROW + HPO4 + " + " + H2O)),
      TBL(["", H2PO4, "OH" + sup(M), HPO4],
          ["Initial conc / " + MDM, "0.06", "0.01", "0.03"],
          ["Change in conc / " + MDM, M + "0.01", M + "0.01", "+0.01"],
          ["Final conc / " + MDM, "0.05", "0", "0.04"]),
      C(A("pH = " + PKA + " + lg" + frac("[" + HPO4 + "]", "[" + H2PO4 + "]"))),
      C(A("= 7.20 + lg" + frac("0.04", "0.05"))),
      C(A("= 7.10")),
      P(N("Allow ecf of the " + PKA + " value from (b)(ii)."))),
 PART("(c)(i)",
      P(A("Due to the electrostatic " + u("attraction") + " between the " + u("positively charged proton") + " and " + u("anion") + ", " + u("more energy") +
          " is required to remove the second proton."))),
 PART("(c)(ii)",
      IMG(5, "cii"),
      P(N("Lone pair and partial charges, dotted lines for H-bonds.")),
      P(A("In maleic acid, the monoanion is " + u("stabilised") + " by " + u("internal hydrogen bonding") + ", which makes it easier for deprotonation to occur."))),
 PART("(d)",
      TBL([b("Information"), b("Type of reaction"), b("Deduction")],
          ["When heated with dilute HCl, J gives ethanoic acid and K, C" + sub(9) + "H" + sub(10) + "O",
           "Acid hydrolysis", "J is an ester.<br>From the molecular formula, K is an alcohol / phenol."],
          ["K reacts with cold alkaline KMnO" + sub(4) + " to give L, C" + sub(9) + "H" + sub(12) + "O" + sub(3) + ".",
           "(Mild) oxidation", "K has a C=C or K is an alkene.<br>L is a diol."],
          ["When heated with acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ", L forms M, C" + sub(9) + "H" + sub(10) + "O" + sub(4) + ".",
           "Oxidation", "From the molecular formula, L has a " + u("primary alcohol") + " or M is a " + u("carboxylic acid") + "."],
          ["M does not react with 2,4-dinitrophenylhydrazine.",
           "", "M does not undergo condensation.<br>M is " + u("not a carbonyl compound") + ".<br>One of the alcohol groups in M did not undergo oxidation. M has a " + u("tertiary alcohol") + "."],
          ["M reacts with PCl" + sub(5) + " to give a sweet-smelling compound N, C" + sub(9) + "H" + sub(7) + "O" + sub(2) + "Cl.",
           "Nucleophilic substitution and condensation", "Phenol and substituent are in 1,2 positions for intramolecular condensation to take place."],
          ["One mole of K reacts with 3 moles of aqueous bromine to give a white precipitate.",
           "Electrophilic substitution and electrophilic addition",
           "C=C present in K.<br>One position of the 2,4,6 positions with respect to phenol is unavailable for electrophilic substitution."]),
      P(N("Maximum 6 marks for the deductions; 3 marks for the structures.")),
      IMG(5, "d")),
]
# ------------------------------------------------------------------ Q6
W[6] = [
 PART("(a)",
      P(A("NaCl: " + u("hydration") + " occurs but not hydrolysis, so neutral solution formed. " + u("pH = 7"))),
      P(A(u("Hydration: NaCl(s) + aq → Na" + sup("+") + "(aq) + Cl" + sup(M) + "(aq)"))),
      P(A("AlCl" + sub(3) + ": both " + u("hydration and hydrolysis") + " occur.")),
      P(A(u("Hydration: AlCl" + sub(3) + "(s) + 6" + H2O + "(l) → [Al(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) + 3Cl" + sup(M) + "(aq)"))),
      P(A(u("Hydrolysis: [Al(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) ⇌ [Al(" + H2O + ")" + sub(5) + "OH]" + sup("2+") + "(aq) + H" + sup("+") + "(aq)"))),
      P(A(u("pH = 3"))),
      P(A("SiCl" + sub(4) + ": " + u("hydrolysis") + " takes place and HCl is produced.")),
      P(A(u("Hydrolysis: SiCl" + sub(4) + " + 2" + H2O + " → SiO" + sub(2) + " + 4HCl"))),
      P(A(u("pH = 1") + " (or 2)")),
      P(N("1 mark for the equations with mention of hydration/hydrolysis; 1 mark for all correct pH values."))),
 PART("(b)(i)",
      P(A(KSP + " = [Ag" + sup("+") + "]" + sup(2) + "[CrO" + sub(4) + sup("2" + M) + "]")),
      P(A("Unit: mol" + sup(3) + " dm" + sup(M + "9"))),
      P(N("Ecf from the expression."))),
 PART("(b)(ii)",
      P(A(KSP + " = [Ag" + sup("+") + "]" + sup(2) + "[CrO" + sub(4) + sup("2" + M) + "]")),
      P(A("1.1 × 10" + sup(M + "12") + " = (0.02)" + sup(2) + " × [CrO" + sub(4) + sup("2" + M) + "]")),
      P(A("[CrO" + sub(4) + sup("2" + M) + "] = 2.75 × 10" + sup(M + "9") + " " + MDM)),
      P(N("Ecf from the " + KSP + " expression in (i)."))),
 PART("(b)(iii)",
      P(A(KSP + " of PbCrO" + sub(4) + " = 1.8 × 10" + sup(M + "12") + " × 0.010 = 1.8 × 10" + sup(M + "14"))),
      P(A("When [CrO" + sub(4) + sup("2" + M) + "] in the solution = 2.75 × 10" + sup(M + "9") + " " + MDM + ",")),
      P(A("[Pb" + sup("2+") + "] in the solution = 1.8 × 10" + sup(M + "14") + " / 2.75 × 10" + sup(M + "9") + " = 6.55 × 10" + sup(M + "6") + " " + MDM)),
      P(N("Ecf from (ii)."))),
 PART("(b)(iv)",
      P(A("Percentage of Pb" + sup("2+") + " in the solution = " + frac("0.00000655", "0.010") + " × 100% = 0.0655% < 1%")),
      P(A("Thus, the separation is effective.")),
      P(N("Conclusion that the percentage is < 1% needed; ecf."))),
 PART("(c)(i)",
      P(A("A compound exhibits stereoisomerism if its molecules have the same molecular formula, " + u("same structural formula") + ", but " + u("different arrangement") +
          " of atoms " + u("in space") + " / " + u("different spatial arrangement") + "."))),
 PART("(c)(ii)",
      P(N("Mirror image of D-threitol.")),
      IMG(6, "cii"),
      P(A("Or")),
      IMG(6, "cii2")),
 PART("(c)(iii)",
      P(A("One of the stereoisomers has a " + u("plane of symmetry") + " in the molecule and is a meso compound. Hence, its mirror image is superimposable / is the same stereoisomer."))),
 PART("(d)",
      TBL([b("test"), b("reaction"), b("type of reaction"), b("deductions")],
          ["1", "P, C" + sub(8) + "H" + sub(11) + "NO" + sub(2) + ", with cold dilute HCl", u("no") + " acid–base reaction", "P contains amide"],
          ["2", "P with Fehling’s reagent, warm", "oxidation", "P contains aliphatic aldehyde"],
          ["3", "P with an excess of hot, concentrated, acidified KMnO" + sub(4) + " to give Q, C" + sub(6) + "H" + sub(8) + "O" + sub(5),
           "acidic " + u("hydrolysis") + " of amide<br>oxidation", "P contains alkene"],
          ["3", "Q effervesces with Na" + sub(2) + "CO" + sub(3) + "(aq)", "acid–base reaction / neutralisation", "Q contains carboxylic acid"],
          ["3", "Q gives orange ppt with 2,4-DNPH", "condensation", "Q contains ketone"],
          ["4", "P with an excess of LiAlH" + sub(4) + " to give S", "reduction", "S contains " + u("primary") + " alcohol and amine<br>Alkene in P is not reduced"],
          ["5", "S with an excess of CH" + sub(3) + "I, heat, to give T<br>T forms a yellow ppt with AgNO" + sub(3) + "(aq)",
           "S undergoes nucleophilic substitution", "T contains free I" + sup(M)]),
      P(N("Maximum 6 marks for the reasoning.")),
      P(b("P") + ":"),
      IMG(6, "d"),
      P(A("Or")),
      IMG(6, "d2"),
      P(b("Q") + ":"),
      IMG(6, "d3"),
      P(b("S") + ":"),
      IMG(6, "d4"),
      P(A("Or")),
      IMG(6, "d6"),
      P(N("Ecf for an incorrect structure of P (with 8 carbons, aldehyde and amide groups) undergoing reduction to form the corresponding primary alcohol and amine.")),
      P(b("T") + ":"),
      IMG(6, "d5"),
      P(A("Or")),
      IMG(6, "d7"),
      P(N("Ecf for an incorrect structure of S (with amine) undergoing nucleophilic substitution to form the corresponding quaternary alkyl ammonium salt."))),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    assert not re.search(r"\[\d+\]", re.sub(r"<[^>]+>", "", h)), (qn, re.findall(r".{20}\[\d.{10}", h))
    out[str(qn)] = h

# labels = the question parts that carry a mark badge (answerable parts)
qs = {r["question_number"]: r for r in json.loads((QDIR / "questions.json").read_text())}
for qn in sorted(W):
    want = []
    for blk in qs[qn]["content_html"].split('<div class="qpart">')[1:]:
        m = re.match(r'<span class="pl">([^<]*)</span>', blk)
        body = blk[:blk.index('</div>\n') if '</div>\n' in blk else len(blk)]
        if 'class="mk"' in body: want.append(m.group(1))
    have = re.findall(r'<span class="lab">([^<]*)</span>', out[str(qn)])
    assert want == have, (qn, want, have)

assets, seen = [], {}
for qn, slot in ASSETS:
    seen[qn] = seen.get(qn, 0) + 1
    assets.append({"question": qn, "slot": "ans-" + slot, "path": _path(qn, slot), "offset": seen[qn]})
(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "worked solutions,", sum(h.count('class="lab"') for h in out.values()), "parts,", len(assets), "answer assets")
for a in assets: print("  Q%d %-10s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))
