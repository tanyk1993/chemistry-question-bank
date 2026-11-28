"""Hand transcription of the TMJC 2026 H2 Prelim Paper 2 (9476/02) suggested solutions -> worked_solutions.json +
answer_assets.json (feeds gen_answers_migration.py --type structured).

Source: the school's "Suggested Solutions" Word file / Word-exported PDF (question paper with the mark scheme overlaid: answers in
blue, marking notes in red, a few green examiner remarks, teal for the Fig. 2.2 curve; bold + underline marks the keywords). Text is
typed from the page images; the 11 answer figures are snipped from the PDF by crop_tmjc26_p2_answers.py.

Run from the repo root:
    python3 ingest/build_tmjc26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_tmjc26_p2.py; the worked-solution labels must be exactly the question
parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u> on the
school's underlined keywords; marking notes in span.note; figures are bare img.ws-fig[data-asset]
(TMJC_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp; bullets are plain paragraphs (bullets render flush right in answers).
Dropped from the school's pages: the [n] marks and tick marks, the "2 [tick] [1], 3-4 [tick] [2]" tallies (the mark SCALE is kept
as a plain-words note where the school gave one), the green "Marking points" boxes beside Q4(c)(ii) (typed as notes instead).
Red MARKING notes (accept / ecf / "Note: ...") are kept as span.note. The school's "OR" lines become P("Or").

Drawn answers (snipped, ans-* assets): Q1(d); Q2(a)(iii), (b)(iv), (b)(v); Q3(d)(ii); Q4(a), (c)(ii), (d); Q5(a)(i), (b), (c)(i).

Changes made to the school's wording (listed to the user; veto-able):
  short forms: "w.r.t" -> "with respect to", "Expt" -> "Experiment", "half-live" -> "half-lives" (red note at 2(a)(iii)), "rxn" none;
  Q1(c)(i): the configurations are written in full (1s2 added to the school's "2s2 2p6 3s2 3p5");
  Q2(a)(ii): "Since t1/2 is relatively constant at 0.18 unit interval" kept; the construction-lines note is kept and points to the figure
  that sits under (a)(iii);
  Q3(e): "blue" / "yellow" typed after the two complex ions (the school typed them under the equation);
  Q6(e)(i): the school's nested-fraction derivation is typed as equal-rate lines with simple fractions (same steps, same result 0.631);
  Q5(a)(ii): "OR vice versa explanation." -> "Or vice versa explanation.".
Left exactly as the school wrote (NOT changed): Q4(b) "The C-O sigma bond ... C-O pi bond" (means the sigma and pi components of C=O);
Q2(c)(i) "reduces the oxidation number of oxygen"; Q5(c)(ii) answers instantaneous dipole-induced dipole (or permanent dipole-permanent
dipole); Q3(c) uses E(oxidation) for the Li+/Li potential.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "TMJC_H2_P2", 2026
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
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*c): return "<tr>%s</tr>" % "".join(c)
def table(*rows): return '<table class="cmp">%s</table>' % "".join(rows)
ARROW = " → "
EQ = " ⇌ "
MDM = "mol dm" + sup(M + "3")
KJ = "kJ mol" + sup(M + "1")
STD = sup('<span class="pl-sym">⦵</span>')
H2O = "H" + sub(2) + "O"
CO2 = "CO" + sub(2)
CO3 = "CO" + sub(3) + sup("2" + M)
HCO3 = "HCO" + sub(3) + sup(M)
CACO3 = "CaCO" + sub(3)
EMINUS = "e" + sup(M)
EM = "&emsp;"
NB = "&nbsp;"
CLM = "C" + L + sup(M)
PCL5 = "PC" + L + sub(5)
OCLM = "OC" + L + sup(M)
IM = "I" + sup(M)
OHM = "OH" + sup(M)
LIP = "Li" + sup("+")
def iso(a, sym): return sup(a) + sym
DHS = DEL + i("H") + STD
DGS = DEL + i("G") + STD
DSS = DEL + i("S") + STD
ESTD = i("E") + STD
OMEGA = "Ω"
def conf(*terms): return " ".join(t[0] + sup(t[1]) if len(t) == 2 else t for t in terms)

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A("MgC" + L + sub(2) + " has " + u("giant ionic lattice structure") + " and SiC" + L + sub(4) + " and " + PCL5 + " have " + u("simple molecular structure") + ".")),
      P(A(u("Larger amount of energy") + " is required to overcome the " + u("stronger electrostatic force of attraction") + " between " +
          u("oppositely charged ions, Mg" + sup("2+") + " and C" + L + sup(M) + " ions") + ".")),
      P(A("However, a " + u("smaller amount of energy") + " is required to overcome " + u("weak intermolecular instantaneous dipole-induced dipole attraction") +
          ". MgC" + L + sub(2) + " has a higher melting point than SiC" + L + sub(4) + " and " + PCL5 + ".")),
      P(A("Since the " + u("size of electron cloud of " + PCL5 + " is greater than SiC" + L + sub(4)) + ", larger amount of energy is required to overcome " +
          u("stronger / more extensive intermolecular instantaneous dipole " + M + " induced dipole attraction of " + PCL5 + " than SiC" + L + sub(4)) +
          ". Hence, the melting point of " + PCL5 + " is higher than SiC" + L + sub(4) + ".")),
      P(N("Marking scale: 1–2 points earn 1 mark, 3–4 points earn 2 marks, 5–6 points earn 3 marks."))),
 PART("(a)(ii)",
      P(A("Mg" + sup("2+") + " has " + u("high charge density") + " (as compared to Na" + sup("+") + ") and " + u("polarises C" + L + sup(M) + " anion electron cloud") +
          " to some extent, resulting in some " + u("covalent character") + " in the " + u("ionic bonding") + ", weakening the electrostatic forces of attraction between Mg" +
          sup("2+") + " and C" + L + sup(M) + " ions, requiring " + u("less energy") + "."))),
 PART("(b)(i)",
      table(tr(th(""), th("equation(s)"), th("pH")),
            tr(td("A" + L + "C" + L + sub(3)),
               td(A("A" + L + "C" + L + sub(3) + "(s) + 6" + H2O + "(" + L + ")" + ARROW + "[A" + L + "(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) + 3C" + L + sup(M) + "(aq)") + "<br>" +
                  A("[A" + L + "(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq)" + EQ + "[A" + L + "(" + H2O + ")" + sub(5) + "(OH)]" + sup("2+") + "(aq) + H" + sup("+") + "(aq)")),
               td(A("3"))),
            tr(td(PCL5),
               td(A(PCL5 + "(s) + 4" + H2O + "(" + L + ")" + ARROW + "H" + sub(3) + "PO" + sub(4) + "(aq) + 5HC" + L + "(aq)")),
               td(A("1–2")))),
      P(N("Marking scale: 2 correct entries earn 1 mark, 3–4 earn 2 marks, all 5 earn 3 marks."))),
 PART("(b)(ii)",
      P(A("Number of protons: 83")),
      P(A("Number of electrons: 82"))),
 PART("(c)(i)",
      P(A("C" + L + ": 1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(6) + " 3s" + sup(2) + " 3p" + sup(5))),
      P(A("C" + L + sup("+") + ": 1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(6) + " 3s" + sup(2) + " 3p" + sup(4)))),
 PART("(c)(ii)",
      P(A("Despite the " + u("increase in nuclear charge") + " down Group 17, there is an " + u("increase in the number of occupied electron shells") + " and hence " +
          u("shielding effect") + ".")),
      P(A("The " + u("valence electrons are less strongly attracted to the nucleus") + " and " + u("further away from nucleus") + ", resulting in an " +
          u("increase in anionic radii") + " down Group 17."))),
 PART("(d)", IMG(1, "d")),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A("Half-life is " + u("the time taken") + " for the " + u("concentration of a reactant") + " to " + u("decrease to half") + " its original value."))),
 PART("(a)(ii)",
      P(A("Since " + u(i("t") + sub("½") + " is relatively constant at 0.18 unit interval") + ", the order of reaction with respect to OC" + L + sup(M) + " is " + u("1") + ".")),
      P(N("1 mark for clear construction lines with labelling showing 2 half-lives on Fig. 2.1 (see the graph under (a)(iii)).")),),
 PART("(a)(iii)",
      IMG(2, "aiii"),
      P(N("1 mark for clear construction lines with labelling showing 2 half-lives (0.18) on Fig. 2.1."))),
 PART("(b)(i)",
      P(A("Comparing Experiments 1 and 2,")),
      P(A("When [" + IM + "] × 2.5 and [" + OCLM + "] × 0.5, while keeping [" + OHM + "] constant, the initial rate of reaction × 1.25.")),
      P(A("Since the order of reaction with respect to OC" + L + sup(M) + " is 1, the order of reaction with respect to " + IM + " is " + u("1") + ".")),
      P(A("Let rate = " + i("k") + "[OC" + L + sup(M) + "][" + IM + "][" + OHM + "]" + sup(i("y")) + ".")),
      P(A("Comparing Experiments 2 and 3,")),
      C(A(frac("6.05 × 10" + sup(M + "4"), "2.42 × 10" + sup(M + "4")) + " = " +
          frac(i("k") + "(5.00 × 10" + sup(M + "3") + ")(1)" + sup(i("y")) + "(2.00 × 10" + sup(M + "3") + ")", i("k") + "(8.00 × 10" + sup(M + "3") + ")(2)" + sup(i("y")) + "(1.00 × 10" + sup(M + "3") + ")"))),
      C(A("2 = (1/2)" + sup(i("y")))),
      C(A(i("y") + " = " + M + "1")),
      P(A("Order of reaction with respect to " + OHM + " is " + u(M + "1") + "."))),
 PART("(b)(ii)",
      P(A("Rate = " + i("k") + "[OC" + L + sup(M) + "][" + IM + "][" + OHM + "]" + sup(M + "1")))),
 PART("(b)(iii)",
      P(A("Inhibitor / Rate-retarding species / Reaction suppressant / Negative-order species"))),
 PART("(b)(iv)",
      IMG(2, "biv"),
      P(N("Allow ecf."))),
 PART("(b)(v)",
      IMG(2, "bv"),
      P(A("A catalyst " + u("provides an alternative reaction pathway of LOWER activation energy") + ".")),
      P(A("When a " + u("catalyst is used") + ", " + u("number of reactant particles with energy ≥ " + i("E") + sub("a") + " increases") + ",")),
      P(A("the " + u("frequency of effective collisions increases") + ", resulting in a " + u("larger rate constant") + ", and hence " + u("rate") + " of reaction " + u("increases") + ".")),
      P(A("Diagram")),
      P(N("4 points earn 2 marks; 2–3 points earn 1 mark."))),
 PART("(c)(i)",
      P(A("Chloride ion is acting " + u("as a reducing agent") + " as it reduces " + u("the oxidation number of oxygen from 0 in O" + sub(3) + " to " + M + "2 in C" + L + "O" + sub(3) + sup(M)) + "."))),
 PART("(c)(ii)",
      P(A("Chloride ion is acting as a " + u("Lewis base") + " as it " + u("donates a lone pair of electrons") + " to the central metal ion through " + u("dative / coordinate bonds") + "."))),
]
# ------------------------------------------------------------------ Q3
NI4, CO4, NI2, CO3P = "Ni" + sup("4+"), "Co" + sup("4+"), "Ni" + sup("2+"), "Co" + sup("3+")
ECAT = ESTD + sub("cathode")
ECELL = ESTD + sub("cell")
EAN = ESTD + sub("anode")
W[3] = [
 PART("(a)",
      P(A("Anode: Li" + ARROW + "Li" + sup("+") + " + " + EMINUS)),
      P(A("Cathode: " + NI4 + " + " + CO4 + " + 3" + EMINUS + ARROW + NI2 + " + " + CO3P)),
      P(N("1 mark for correct half-equations (anode and cathode, electron-balanced).")),
      P(A("Overall: 3Li + " + NI4 + " + " + CO4 + ARROW + "3Li" + sup("+") + " + " + NI2 + " + " + CO3P))),
 PART("(b)(i)",
      P(A(DGS + " for reduction of " + NI4 + " = " + M + i("nFE") + STD + " = " + M + "2(96" + NB + "500)(+1.23) = " + u(M + "237 " + KJ))),
      P(A(DGS + " for reduction of " + CO4 + " = " + M + i("nFE") + STD + " = " + M + "1(96" + NB + "500)(+1.48) = " + u(M + "143 " + KJ) + " (3 s.f.)")),
      P(N("1 mark for the two values.")),
      P(A(DGS + sub("cathode reaction") + " = " + M + "237.4 + (" + M + "142.8) = " + u(M + "380 " + KJ) + " (3 s.f.)"))),
 PART("(b)(ii)",
      P(A(M + "380.2 × 10" + sup(3) + " = " + M + "3(96" + NB + "500)" + ECAT)),
      P(A(ECAT + " = " + u("+1.31 V") + " (3 s.f.)"), " ", N("(allow ecf)")),
      P(A(ECELL + " = " + ECAT + " " + M + " " + EAN)),
      P(A(EM + "= +1.31 " + M + " (" + M + "3.04)")),
      P(A(EM + "= " + u("+4.35 V") + " (3 s.f.)"), " ", N("(allow ecf)")),
      P("Or"),
      P(A(M + "162 × 10" + sup(3) + " = " + M + "3(96" + NB + "500)" + ECAT)),
      P(A(ECAT + " = +0.560 V (3 s.f.)")),
      P(A(ECELL + " = " + ECAT + " " + M + " " + EAN)),
      P(A(EM + "= +0.560 " + M + " (" + M + "3.04)")),
      P(A(EM + "= " + u("+3.60 V") + " (3 s.f.)"))),
 PART("(c)",
      P(A(LIP + " + " + EMINUS + EQ + "Li" + EM + "------- (1)")),
      P(A("By Le Chatelier’s Principle, the increase in " + LIP + " concentration causes the " + u("equilibrium position of (1)") + " to shift to " + u("right") +
          " to " + u("reduce the " + LIP + " concentration") + ".")),
      P(A("This causes the " + u("oxidation of Li to " + LIP + " to be less favourable") + " / " + u(i("E") + sub("oxidation") + " to become more positive") + ". Since " +
          i("E") + sub("cell") + " = " + i("E") + sub("reduction") + " " + M + " " + i("E") + sub("oxidation") + ", " + u(i("E") + sub("cell") + " becomes less positive") + "."))),
 PART("(d)(i)",
      P(A(b("A") + ": Ni(OH)" + sub(2))),
      P(A(b("B") + ": Mn(OH)" + sub(2)))),
 PART("(d)(ii)", IMG(3, "dii")),
 PART("(e)",
      P(A("[Cu(" + H2O + ")" + sub(6) + "]" + sup("2+") + " (blue) + 4" + CLM + EQ + "[CuC" + L + sub(4) + "]" + sup("2" + M) + " (yellow) + 6" + H2O)),
      P(A("Upon the addition of concentrated HC" + L + ", a " + u("ligand exchange") + " reaction occurs where the C" + L + sup(M) + " ligands " + u("replace") + " the " + H2O +
          " ligands in the blue " + u("[Cu(" + H2O + ")" + sub(6) + "]" + sup("2+")) + " complex to form the " + u("yellow [CuC" + L + sub(4) + "]" + sup("2" + M)) + " complex."))),
]
# ------------------------------------------------------------------ Q4
NA = "N" + sub("a")
W[4] = [
 PART("(a)",
      P(A("cis-trans isomerism")),
      IMG(4, "a"),
      P(N("Structures of cis and trans isomers with the amine neutralised."))),
 PART("(b)",
      P(A("The hybridisation of C in C=O is " + u("sp" + sup(2)) + ".")),
      P(A("The C–O " + u("σ bond") + " is formed by " + u("2sp" + sup(2) + "–2sp" + sup(2) + " head-on orbital overlap") + ".")),
      P(A("The C–O " + u("π bond") + " is formed by " + u("2p–2p side-on orbital overlap") + ".")),
      P(A("The shape is " + u("trigonal planar") + ".")),
      P(N("4 points earn 2 marks; 2–3 points earn 1 mark."))),
 PART("(c)(i)",
      P(A("HCN with trace NaOH (or NaCN) as catalyst, cold"))),
 PART("(c)(ii)",
      P(A(u("Nucleophilic addition"))),
      IMG(4, "cii"),
      P(N("Marking points for step 1: slow step; lone pair and dipoles; correct arrow pushing from lone pair on C atom to C atom (bond forming) and correct "
          "arrow pushing from bond to O atom; correct intermediate.")),
      P(N("Marking points for step 2: correct arrow pushing from lone pair on O atom to H atom (bond forming) and correct arrow pushing from bond to C atom "
          "(bond breaking); balanced equation with CN" + sup(M) + ".")),
      P(N("6–7 points earn 2 marks; 3–5 points earn 1 mark."))),
 PART("(c)(iii)",
      P(A("There is " + u("equal probability of the CN" + sup(M) + " nucleophile attacking the sp" + sup(2) + " hybridised trigonal planar electron-deficient carbonyl C atom from top and bottom of the plane") + ".")),
      P(A("This leads to the " + u("formation of equal amounts of the (+) and (" + M + ") enantiomers") + " resulting in the formation of a racemic mixture."))),
 PART("(d)",
      IMG(4, "d"),
      P(A("Step 1: LiAl" + "H" + sub(4) + " in dry ether / NaBH" + sub(4) + " in ethanol / H" + sub(2) + "(g), Ni / Pd / Pt")),
      P(A("Step 2: anhydrous PC" + L + sub(5) + " / HC" + L)),
      P(A("Step 3: ethanolic KCN, heat")),
      P(A("Step 4: LiAlH" + sub(4) + " in dry ether / H" + sub(2) + "(g), Ni / Pd / Pt")),
      P(N("1 mark for each correct blank (7 in total): 7 earn 4 marks; 5–6 earn 3 marks; 3–4 earn 2 marks; 2 earn 1 mark."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", IMG(5, "ai")),
 PART("(a)(ii)",
      P(A("The amino group in the ε-amino acid is more basic than the amino group in leucine.")),
      P(A("In leucine, the " + u(M + "NH" + sub(2) + " group is closer to the electron withdrawing " + M + "COOH group") + ", which makes the " + u("lone pair on nitrogen less available to accept a proton") +
          ", hence it is a weaker base. Or vice versa explanation."))),
 PART("(b)",
      IMG(5, "b"),
      P(N("1 mark for the monomer of nylon-6; 1 mark for the repeat unit of Terylene; 1 mark for both types of polymerisation correct."))),
 PART("(c)(i)",
      IMG(5, "ci"),
      P(N("1 mark for all of: lone pair on N or O; dipole labelled correctly; hydrogen bonding shown and labelled."))),
 PART("(c)(ii)",
      P(A(u("Instantaneous dipole–induced dipole") + " (or permanent dipole–permanent dipole) interaction.")),
      P(A("Polyester " + u("does not have hydrogen bonding") + " between chains, hence " + u("disruption to their alignment is minimised") + "."))),
 PART("(c)(iii)",
      P(A("Any of these reasons:")),
      P(A(u("Crease resistance") + " (as in polyester), " + u("durability") + " (or not easily torn), " + u("lower cost of production") + "."))),
 PART("(d)",
      P(A("Polyester is a synthetic polymer, hence it is " + u("not easily biodegradable") + " or it takes up " + u("limited landfill space") + "."))),
]
# ------------------------------------------------------------------ Q6
KSP = i("K") + sub("sp")
W[6] = [
 PART("(a)(i)",
      P(A("solution of " + CACO3 + ": " + CACO3 + "(s)" + ARROW + "Ca" + sup("2+") + "(aq) + " + CO3 + "(aq)")),
      P(A(DHS + sub("(sol)") + " = ΣΔ" + i("H") + sub("f") + STD + "(products) " + M + " ΣΔ" + i("H") + sub("f") + STD + "(reactants)")),
      P(A(EM + "= [Δ" + i("H") + sub("f") + STD + "(Ca" + sup("2+") + "(aq)) + Δ" + i("H") + sub("f") + STD + "(" + CO3 + "(aq))] " + M + " [Δ" + i("H") + sub("f") + STD + "(" + CACO3 + "(s))]")),
      P(A(EM + "= (" + M + "543) + (" + M + "675) " + M + " (" + M + "1207)")),
      P(A(EM + "= " + u(M + "11.0 " + KJ)))),
 PART("(a)(ii)",
      P(A(CACO3 + "(s)" + ARROW + "Ca" + sup("2+") + "(aq) + " + CO3 + "(aq)")),
      P(A(DGS + sub("(sol), 298 K") + " = " + DHS + sub("(sol)") + " " + M + " " + i("T") + "(" + DSS + sub("(sol)") + ")")),
      P(A(EM + "= (" + M + "11.0) " + M + " (298)" + frac(M + "199", "1000"))),
      P(A(EM + "= " + u("+48 " + KJ) + " > 0"), " ", N("(allow ecf from (a)(i) from wrong calculation of " + DHS + ")")),
      P(A("The dissolving of " + CACO3 + " is " + u("not spontaneous at standard conditions") + "."), " ",
        N("(allow ecf for the spontaneity conclusion if consistent with the candidate’s " + DGS + ")"))),
 PART("(a)(iii)",
      P(A("Since " + u(DHS + " is negative and " + DSS + " is negative") + ", the " + u("term " + M + i("T") + DSS + " is positive") + ".")),
      P(A("Hence, " + u(DGS + " becomes increasingly positive at high temperatures") + ", so " + u("dissolving of " + CACO3 + " becomes less feasible at higher temperatures") + ".")),
      P(N("ECF in (a)(iii) only when the candidate correctly applies the sign of " + DHS + " calculated in (a)(i).")),
      P(A("Assumption is that " + u(DHS + " and " + DSS + " are temperature independent") + "."))),
 PART("(b)(i)",
      P(A(OMEGA + " (calcite) = " + frac("[Ca" + sup("2+") + "][" + CO3 + "]", KSP + "(calcite)") + " = " +
          frac("(1.0 × 10" + sup(M + "2") + ")(2.0 × 10" + sup(M + "4") + ")", "3.3 × 10" + sup(M + "9")) + " = 606")),
      P(A(u("Aragonite is the least thermodynamically favoured") + " to precipitate from seawater because it has the " + u("smallest saturation state, " + OMEGA) + ".")),
      P(N("1 mark for the correct " + OMEGA + " calculation, with all three values correct; 1 mark for the correct conclusion with correct " + OMEGA + " use."))),
 PART("(b)(ii)",
      P(A(OMEGA + " does not account for the " + u("kinetic feasibility of the precipitation reaction") + ", which may have " + u("large activation energy, " + i("E") + sub("a") +
          ", and hence the reaction may be too slow") + "."))),
 PART("(c)",
      P(A(CACO3 + "(s)" + EQ + "Ca" + sup("2+") + "(aq) + " + CO3 + "(aq) " + M + " (1)  Due to the presence of a common ion, Ca" + sup("2+") + ", " +
          u("[Ca" + sup("2+") + "] increases") + ". Hence, " + u("equilibrium position of (1) will shift left to decrease [Ca" + sup("2+") + "]") + ". This will " +
          u("decrease the solubility of " + CACO3) + "."), " ", N("(Common ion effect.)"))),
 PART("(d)",
      P(A("Mg" + sup("2+") + " is " + u("more strongly hydrated in aqueous solution") + " / forms stronger ion-dipole interactions with water molecules due to " + u("higher charge density") +
          ". " + u("More energy is required to remove the stronger hydration shell of Mg" + sup("2+")) + ", " + u("slowing lattice assembly and magnesite nucleation") + "."))),
 PART("(e)(i)",
      P(A("When pH decreases from 8.1 to 7.9, [H" + sup("+") + "] increases from 10" + sup(M + "8.1") + " to 10" + sup(M + "7.9") + ".")),
      P(A("Given " + i("K") + sub("a2") + " = " + frac("[H" + sup("+") + "][" + CO3 + "]", "[" + HCO3 + "]") + " is " + u("constant at a fixed temperature") + " and that " +
          u("[" + HCO3 + "] remains approximately constant") + ",")),
      C(A("[H" + sup("+") + "]" + sub("pH 7.9") + "[" + CO3 + "]" + sub("pH 7.9") + " = [H" + sup("+") + "]" + sub("pH 8.1") + "[" + CO3 + "]" + sub("pH 8.1"))),
      C(A("10" + sup(M + "7.9") + " × [" + CO3 + "]" + sub("pH 7.9") + " = 10" + sup(M + "8.1") + " × [" + CO3 + "]" + sub("pH 8.1"))),
      C(A(frac("[" + CO3 + "]" + sub("pH 7.9"), "[" + CO3 + "]" + sub("pH 8.1")) + " = " + frac("10" + sup(M + "8.1"), "10" + sup(M + "7.9")) + " = " + u("0.631")))),
 PART("(e)(ii)",
      P(A("An increase in atmospheric " + CO2 + " corresponds to a decrease in pH of seawater, which " + u("reduces [" + CO3 + "], thus lowering " + OMEGA + " and reduces the tendency for calcite to precipitate") +
          ", reducing coral calcification or skeletal growth."))),
 PART("(f)",
      P(A("Corals can " + u("locally increase the saturation state, " + OMEGA) + ", by locally increasing the " + u("[Ca" + sup("2+") + "] and [" + CO3 + "] at the site of calcification") + ".")),
      P("Or"),
      P(A("By " + u("increasing pH") + ", [H" + sup("+") + "] decreases, " + u("shifting the equilibrium position") + " of " + HCO3 + "(aq)" + EQ + "H" + sup("+") + "(aq) + " + CO3 +
          "(aq) " + u("right and increasing [" + CO3 + "]") + ", thereby increasing " + OMEGA + " above 1 and favouring " + CACO3 + " precipitation."))),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    assert not re.search(r"\[\d+\]", re.sub(r"<[^>]+>", "", h)), (qn, re.findall(r".{20}\[\d.{10}", re.sub(r"<[^>]+>", "", h)))
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
