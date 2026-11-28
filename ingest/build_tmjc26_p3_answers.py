"""Hand transcription of the TMJC 2026 H2 Prelim Paper 3 (9476/03) suggested solutions -> worked_solutions.json +
answer_assets.json (feeds gen_answers_migration.py --type structured).

Source: the school's "Suggested Solutions" Word file / Word-exported PDF (question paper with the mark scheme overlaid: answers in
blue, marking notes in red, a few green remarks; bold + underline marks the keywords). Text is typed from the page images (every page
was rendered and compared with the extracted text, because the drawn answers are invisible to pdftotext); the 12 answer figures are
snipped from the PDF by crop_tmjc26_p3_answers.py.

Run from the repo root:
    python3 ingest/build_tmjc26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_tmjc26_p3.py; the worked-solution labels must be exactly the question
parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u> on the
school's underlined keywords; marking notes in span.note; figures are bare img.ws-fig[data-asset]
(TMJC_H2_P3_Q<n>_ans-<slot>_2026.png); tables are table.cmp. Two adjacent parts that share ONE figure are one div.part carrying two
span.lab and a single body (Q4(c)(iv)/(v)).
Dropped from the school's pages: the [n] marks and tick marks, the "5 ticks - 3m" style tallies (the mark SCALE is kept as a plain-words
note where the school gave one), the red/green marking text inside the figures. Red MARKING notes (accept / allow ecf / "Or words to the
effect") are kept as span.note. The school's "OR" lines become P("Or").

Drawn answers (snipped, ans-* assets): Q1(a)(ii), (b)(i); Q2(b)(ii), (e); Q3(d)(i); Q4(c)(i), (iii), (iv)+(v); Q5(a)(iv), (c)(i), (c)(ii),
(d)(i).

Changes made to the school's wording (listed to the user; veto-able):
  Q4(c)(vi): "compound C" -> "compound D" (twice; the test is for D, the aldehyde);
  Q1(c)(i): the school's "Qrxn = Qsol = mcDT + CDT" is typed "Qrxn = Qsol + Qcan = mcDT + CDT";
  Q1(e): "Alternate:" -> "Alternative:";
  Q5(a)(iv): the three small inline structures in the school's sentence are typed as formulas, (CH3)2CHCH2COO-, (CH3)2CHCH2. and
  (CH3)3C. (read off the printed drawings);
  Q5(c)(ii): the heading "Mechanism: Electrophilic Addition" (above the drawing) is typed; the green labels beside the drawing are typed as a
  "marking points" note; Q5(d)(ii): the green "(electrophilic addition)" etc. are typed after "Step n";
  Q1(d)(ii): the empty arrow column of the school's table is dropped.
School ERRORS CORRECTED at the user's instruction (2026-11-28): Q1(c)(i) -562 -> -563 (26.37 / 0.04688 = 562.5); Q3(a)(iii) pOH 2.15 ->
2.16 and pH 11.85 -> 11.84; Q5(a)(ii) n 0.0467 -> 0.0466 mol (2.5 x 3600 / 193000; V = 1.21 dm3 unchanged); Q5(a)(iv) "which has" -> "which
have"; Q4(c)(vii) now opens "The mechanism is SN1."; Q3(a)(ii) gains the half-equivalence reason; grammar: Q3(b) "d subshells" -> "d subshell",
Q3(c)(ii) "gets promoted" -> "get promoted", Q3(a)(vi) "amounts of OH- is added" -> "are added", Q2(d)(ii) "they are less available" -> "it is
less available".
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "TMJC_H2_P3", 2026
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
def PART(label, *blocks):
    labs = [label] if isinstance(label, str) else list(label)
    return ('<div class="part">%s<div class="body">%s</div></div>'
            % ("".join('<span class="lab">%s</span>' % l for l in labs), _tidy("\n".join(blocks))))
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
CH3OH = "CH" + sub(3) + "OH"
CO2 = "CO" + sub(2)
H2 = "H" + sub(2)
O2 = "O" + sub(2)
HP = "H" + sup("+")
OHM = "OH" + sup(M)
NA = "Na" + sup("+")
EMINUS = "e" + sup(M)
H3PO4 = "H" + sub(3) + "PO" + sub(4)
H2PO4 = "H" + sub(2) + "PO" + sub(4) + sup(M)
HPO4 = "HPO" + sub(4) + sup("2" + M)
CL2 = "C" + L + sub(2)
DHS = DEL + i("H")
DHC = DEL + i("H") + sub("c") + STD
DHVAP = DEL + i("H") + sub("vap") + STD
SQRT = "√"

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A("Bond energy of a covalent bond is the " + u("average energy absorbed") + " to " + u("break one mole of the (covalent) bond in the gas phase") +
          " into its " + u("constituent gaseous atoms") + " under " + u("standard conditions / 298 K and 1 bar") + "."))),
 PART("(a)(ii)",
      IMG(1, "aii"),
      C(A(DHS + sub(1) + " = ΣBE (reactants) " + M + " ΣBE (products)")),
      C(A("= [2×BE(C=O) + 3×BE(H–H)] " + M + " [3×BE(C–H) + BE(C–O) + BE(O–H) + 2×BE(O–H)]")),
      C(A("= [2(805) + 3(436)] " + M + " [3(410) + 360 + 3(460)]")),
      C(A("= 2918 " + M + " 2970")),
      C(A("= " + u(M + "52 " + KJ))),
      P(N("Sign required; ignore units."))),
 PART("(a)(iii)",
      P(A("Copper forms " + u("temporary bonds") + " with the gaseous reactants to " + u("increase surface concentration") + ", speeding up reaction rate.")),
      P(N("Or words to the effect: 1. Adsorption and 2. Mechanism to speed up."))),
 PART("(b)(i)",
      IMG(1, "bi"),
      P(A("By Hess’ Law,")),
      C(A(DHS + sub(2) + " " + M + " " + DHVAP + "(" + CH3OH + ") + " + DHC + "(" + CH3OH + ") = " + DHC + "(CO) + 2" + DHC + "(" + H2 + ")")),
      C(A(DHS + sub(2) + " = " + DHC + "(CO) + 2" + DHC + "(" + H2 + ") + " + DHVAP + "(" + CH3OH + ") " + M + " " + DHC + "(" + CH3OH + ")")),
      C(A("= " + M + "283 + 2(" + M + "286) + 37 " + M + " (" + M + "726)")),
      C(A("= " + M + "92 " + KJ)),
      P(N("The O" + sub(2) + " additions on the energy cycle are ignored."))),
 PART("(b)(ii)",
      P(A(u("Bond energy values used are average values") + " and are not specific to the actual bonds of the substances involved."))),
 PART("(c)(i)",
      P(A(i("Q") + sub("sol") + " = " + i("mc") + DEL + i("T") + " (where " + i("c") + " = specific heat capacity of water)")),
      C(A("= 200 × 4.18 × (54.5 " + M + " 25.0) = 200 × 4.18 × (29.5)")),
      C(A("= 24662 J = 24.66 kJ")),
      P(A(i("Q") + sub("can") + " = " + i("C") + DEL + i("T") + " (where " + i("C") + " = heat capacity of copper can)")),
      C(A("= 57.8 × (54.5 " + M + " 25.0) = 57.8 × (29.5)")),
      C(A("= 1705.1 J = 1.705 kJ")),
      P(A(i("Q") + sub("rxn") + " = " + i("Q") + sub("sol") + " + " + i("Q") + sub("can") + " = " + i("mc") + DEL + i("T") + " + " + i("C") + DEL + i("T") +
          " = 24.66 + 1.705 = 26.37 kJ"), " ", N("(assuming 100% efficiency)")),
      P(A("Amount of methanol combusted = " + frac("1.50", "32.0") + " = 0.04688 mol")),
      P(A(DHC + "(" + CH3OH + ") = " + M + frac(i("Q") + sub("rxn"), "Amount combusted") + " = " + M + frac("26.37", "0.04688"))),
      C(A("= " + u(M + "563 " + KJ) + " (3 s.f.)")),
      P(N("Sign required; ignore units."))),
 PART("(c)(ii)",
      P(A("Heat loss to surroundings")),
      P("Or"),
      P(A("Incomplete combustion of methanol")),
      P("Or"),
      P(A("Draught effects / no wind shield that causes heat loss to surroundings")),
      P(N("Any appropriate reason in relation to the given set-up that reflects unaccounted heat transfer."))),
 PART("(d)(i)",
      P(A(i("K") + sub("c") + " = " + frac("[" + CH3OH + "]", "[CO][" + H2 + "]" + sup(2)))),
      P(A("Units: " + u("mol" + sup(M + "2") + " dm" + sup(6))))),
 PART("(d)(ii)",
      table(tr(th(""), th("CO(g)"), th("2" + H2 + "(g)"), th(CH3OH + "(g)")),
            tr(td("Initial amount / mol"), td("4.00"), td("7.00"), td("0")),
            tr(td("Change amount / mol"), td(M + "1.50"), td(M + "2(1.50)"), td("+1.50")),
            tr(td("Equilibrium amount / mol"), td("2.50"), td("4.00"), td("1.50")),
            tr(td("Equilibrium conc. / " + MDM), td(frac("2.50", "5.00") + " = 0.500"), td(frac("4.00", "5.00") + " = 0.800"), td(frac("1.50", "5.00") + " = 0.300"))),
      P(A(i("K") + sub("c") + " = " + frac("[" + CH3OH + "]", "[CO][" + H2 + "]" + sup(2)) + " = " + frac("0.300", "(0.500)(0.800)" + sup(2)) + " = " + frac("0.300", "(0.500)(0.640)"))),
      C(A("= " + frac("0.300", "0.320") + " = " + u("0.938 mol" + sup(M + "2") + " dm" + sup(6)))),
      P(N("Ignore units; allow ecf from the expression in (d)(i)."))),
 PART("(d)(iii)",
      P(A("As pressure ∝ " + frac("1", "volume") + ", " + u("decreasing volume increases total pressure") + ", " + u("equilibrium position of Reaction 2 shifts right") + " to " +
          u("fewer moles of gas") + " to reduce pressure; equilibrium yield of methanol thus " + u("increases") + "."))),
 PART("(d)(iv)",
      P(A("By Le Chatelier’s Principle, " + u("high temperature favours the endothermic to remove excess heat") + ". Since forward reaction proceeds readily under high temperature, the forward reaction is " +
          u("endothermic") + "."))),
 PART("(e)",
      P(A("Add " + u("I" + sub(2) + "(aq) with NaOH(aq)") + " to each sample separately and " + u("heat") + ".")),
      P(A("For methanol: " + u("No") + " (pale) " + u("yellow precipitate") + " formed")),
      P(A("For ethanol: (Pale) " + u("yellow precipitate formed"))),
      P(N("Alternative: KMnO" + sub(4) + " or K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ", give full descriptors including colour change."))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A("Amount of etomidate needed for the adult = " + frac("0.3 × 10" + sup(M + "3"), "244") + " × 70 = 8.61 × 10" + sup(M + "5") + " mol")),
      P(A("Volume of solution = " + frac("8.61 × 10" + sup(M + "5"), "8.2 × 10" + sup(M + "3")) + " = 0.0105 dm" + sup(3)))),
 PART("(a)(ii)",
      P(A(i("c") + sub("o") + " = " + frac("0.3 × 70", "2.5") + " = 8.40 mg dm" + sup(M + "3")))),
 PART("(a)(iii)",
      P(A("Let number of half-lives be " + i("n"))),
      C(A("8.40 × (½)" + sup(i("n")) + " = 1.0")),
      C(A(i("n") + " log(½) = log(1.0/8.40)")),
      C(A(i("n") + " = 3.07")),
      P(A("Time taken = 3.07 × 3.0 = 9.21 min")),
      P("Alternatively,"),
      C(A(i("n") + " = log " + frac("8.40", "1.0") + " ÷ log 2 = 3.07")),
      P(N("Allow ecf."))),
 PART("(b)(i)",
      P(A("ester"))),
 PART("(b)(ii)",
      IMG(2, "bii"),
      P(N("Marking scale: 11–13 points earn 3 marks, 8–10 earn 2 marks, 4–7 earn 1 mark."))),
 PART("(b)(iii)",
      P(A("Two / second"))),
 PART("(c)",
      P(A("Different stereoisomers exhibit " + u("different biological properties") + ". Only the (+) enantiomer of the drug provides the desired biological effect."))),
 PART("(d)(i)",
      P(A("sp" + sup(2)))),
 PART("(d)(ii)",
      P(A("The " + u("lone pair") + " of electrons on the nitrogen atom is " + u("delocalised into the aromatic ring") + ". Hence, it is " + u("less available to accept a proton") +
          ", making the N less basic than an amine."))),
 PART("(e)",
      P(A("1. B is less basic than 1-phenylethanamine, it is likely a " + u("phenylamine"))),
      P(A("2. B undergoes " + u("electrophilic substitution") + " with Br" + sub(2) + "(aq) to form C.")),
      P(A("&emsp;– B is a " + u("phenylamine"))),
      P(A("3. B undergoes " + u("oxidation") + " with KMnO" + sub(4) + " to give D.")),
      P(A("&emsp;– D is a " + u("dicarboxylic acid"))),
      P(A("&emsp;– Hence, B has " + u("2 methyl side chains"))),
      P(A("4. A undergoes " + u("reduction") + " with Sn in conc. HC" + L + ", to give B.")),
      P(A("&emsp;– A is a " + u("nitrobenzene"))),
      IMG(2, "e"),
      P(N("Reasoning: every 2 points earn 1 mark, maximum 3 marks. Structures: every 2 correct structures earn 1 mark."))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)",
      P(A("[" + H3PO4 + "] = 0.100 × " + frac("22.40", "25.0") + " = 0.0896 " + MDM)),
      P(A("[" + HP + "] = " + SQRT + "(0.0896 × (6.9 × 10" + sup(M + "3") + ")) = 0.02486")),
      P(A("pH = " + M + "log(0.02486) = 1.60"))),
 PART("(a)(ii)",
      P(A("At the half-equivalence point (11.20 cm" + sup(3) + "), [" + H3PO4 + "] = [" + H2PO4 + "], so [" + HP + "] = " + i("K") + sub("a1") + ".")),
      P(A("pH = " + M + "log(6.9 × 10" + sup(M + "3") + ") = 2.16"))),
 PART("(a)(iii)",
      P(A("Amount of excess NaOH = " + frac("50.00 " + M + " 2(22.40)", "1000") + " × 0.100 = 0.000520 mol")),
      P(A("[NaOH] = 0.000520 ÷ " + frac("25.0 + 50.00", "1000") + " = 0.006933 " + MDM)),
      P(A("pH = 14 " + M + " pOH = 14 " + M + " (" + M + "log 0.006933) = 14 " + M + " (2.16) = 11.84"))),
 PART("(a)(iv)",
      P(A(i("K") + sub("a2") + " = " + frac("[" + HP + "][" + HPO4 + "]", "[" + H2PO4 + "]")))),
 PART("(a)(v)",
      P(A(HPO4 + "(aq) + " + H2O + "(l)" + EQ + H2PO4 + "(aq) + " + OHM + "(aq)"))),
 PART("(a)(vi)",
      P("(When 30.00 cm" + sup(3) + " of NaOH was added, the buffer solution contains " + H2PO4 + " and " + HPO4 + ")"),
      P(A(H2PO4 + "(aq) + " + OHM + "(aq)" + ARROW + HPO4 + "(aq) + " + H2O + "(l)")),
      P(A("When small amounts of " + OHM + " are added, " + H2PO4 + " reacts with the additional " + OHM + " and forms " + HPO4 +
          ", such that the actual increase in [" + OHM + "] is minimised, hence pH remains largely constant."))),
 PART("(b)",
      P(A("A transition element is a " + u("d-block element") + " whose " + u("atom") + " has an " + u("incomplete d subshell") + ", or which can give rise to " +
          u("cations") + " with an " + u("incomplete d subshell") + "."))),
 PART("(c)(i)",
      P(A("Cr" + sup("3+") + ": 1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(6) + " 3s" + sup(2) + " 3p" + sup(6) + " 3d" + sup(3) + " or [Ar] 3d" + sup(3)))),
 PART("(c)(ii)",
      P(A("A transition metal ion has partially-filled d orbitals.")),
      P(A("In the " + u("presence of ligands") + ", the " + u("d orbitals are split into two groups") + " with an energy gap, ΔE. This effect is known as d orbital splitting.")),
      P(A("During " + u("d–d transition") + ", the d electrons " + u("from the lower energy d orbitals") + " " + u("absorb a certain wavelength of light") + " from the " +
          u("visible spectrum") + " and get " + u("promoted to") + " a higher energy d orbital.")),
      P(A("The " + u("green colour observed") + " is " + u("complementary") + " to the " + u("red colour absorbed") + ".")),
      P(N("Marking scale: 5 points earn 3 marks, 3–4 points earn 2 marks, 1–2 points earn 1 mark."))),
 PART("(d)(i)",
      IMG(3, "di")),
 PART("(d)(ii)",
      P(A("Elements with " + u("unpaired electrons") + " respond to magnetic fields whereas elements with only paired electrons do not respond to magnetic fields."))),
 PART("(d)(iii)",
      P(A("Mn" + sup("2+") + " has all the d orbitals singly filled with electrons of the same spin. The lower energy orbital electrons cannot promote to the higher energy orbitals because there is already another electron there with the same spin."))),
]
# ------------------------------------------------------------------ Q4
CH3NH2 = "CH" + sub(3) + "NH" + sub(2)
NH2OH = "NH" + sub(2) + "OH"
CH3SH = "CH" + sub(3) + "SH"
W[4] = [
 PART("(a)",
      P(A("There is " + u("more extensive hydrogen bonding between " + NH2OH + " molecules than between " + CH3NH2 + " molecules") + ". (or strength of hydrogen bond) " +
          u("More energy") + " is required to " + u("separate " + NH2OH + " molecules") + ", resulting in a " + u("higher boiling point") + ".")),
      P(A(u("Electron cloud size of " + CH3SH + " is much larger than that of " + CH3NH2) + ". Hence, there exists " + u("stronger instantaneous dipole–induced dipole attractions") +
          " between " + u(CH3SH + " molecules") + " than " + u("the hydrogen bonding") + " between " + u(CH3NH2 + " molecules") + ". " + u("More energy") + " is required to " +
          u("separate " + CH3SH + " molecules") + ", resulting in " + u("a higher boiling point") + ".")),
      P(N("(Marked once.)"))),
 PART("(b)",
      P(A("MgO and Al" + sub(2) + "O" + sub(3) + " " + u("giant ionic") + " structures.")),
      P(A(u("Large amount") + " of energy is required to overcome " + u("strong electrostatic attraction between oppositely charged ions") + ". Hence, both oxides have " + u("high melting points") + ".")),
      P(A(u("Al" + sup("3+") + " has high charge density and polarises O" + sup("2" + M)) + ". Hence " + u("Al" + sub(2) + "O" + sub(3) + " ionic bond has some covalent character") +
          " which weakens the ionic bond strength, resulting in " + u("lower melting point") + ".")),
      P(A("P" + sub(4) + "O" + sub(10) + " has " + u("simple molecular") + " structure. " + u("Small amount of energy") + " is required to overcome " +
          u("weak instantaneous dipole – induced dipole attractions between molecules") + ". Hence, P" + sub(4) + "O" + sub(10) + " has a low melting point."))),
 PART("(c)(i)",
      IMG(4, "ci")),
 PART("(c)(ii)",
      P("Step 4: ", A("condensation")),
      P("Step 5: ", A("elimination"))),
 PART("(c)(iii)",
      IMG(4, "ciii"),
      P(N("Every 2 correct points earn 1 mark."))),
 PART(["(c)(iv)", "(c)(v)"],
      IMG(4, "civ"),
      P(N("1 mark for the structure of the alkoxide intermediate; 1 mark for the mechanism."))),
 PART("(c)(vi)",
      P(A("Add " + u("2,4-DNPH") + " to the solution sample and warm.")),
      P(A("An " + u("orange precipitate") + " of hydrazone " + u("forms if compound D is present") + ".")),
      P(A(u("No orange precipitate") + " forms if compound D is absent.")),
      P(N("Can also accept Na" + sub(2) + "CO" + sub(3) + ", Tollens’ solution or Fehling’s solution."))),
 PART("(c)(vii)",
      P(A("The mechanism is " + u("S" + sub("N") + "1") + ". This is because the reaction proceeds via an " + u("S" + sub("N") + "1 mechanism") + ", in which the leaving group first departs to form a " + u("resonance-stabilised carbocation") + ".")),
      P(A("The " + u("nucleophile") + " can then attack this " + u("planar carbocation") + " " + u("from either side") + " " + u("with equal probability") + ", producing " +
          u("both enantiomers in equal amounts") + "."))),
]
# ------------------------------------------------------------------ Q5
RAD3 = "(CH" + sub(3) + ")" + sub(3) + "C•"
W[5] = [
 PART("(a)(i)",
      P("Cathode: ", A("2" + H2O + "(l) + 2" + EMINUS + ARROW + H2 + "(g) + 2" + OHM + "(aq)")),
      P("Overall: ", A("2CH" + sub(3) + "COO" + sup(M) + "(aq) + 2" + H2O + "(l)" + ARROW + "CH" + sub(3) + "CH" + sub(3) + " + 2" + CO2 + " + " + H2 + "(g) + 2" + OHM + "(aq)")),
      P(N("At the cathode, reduction occurs. Since carboxylate is present, it implies the medium is alkaline. Species present at the cathode: " + NA + "; " + H2O + "."))),
 PART("(a)(ii)",
      P(A("From the reaction at anode: CH" + sub(3) + "CH" + sub(3) + " ≡ 2" + EMINUS)),
      P(A(i("n") + "(CH" + sub(3) + "CH" + sub(3) + ") = " + frac(i("I") + " × " + i("t"), i("n") + sub("e" + sup(M)) + " × " + i("F")) + " = " + frac("2.5 × (60 × 60)", "2 × 96500") + " = 0.0466 mol")),
      P(A("Using " + i("pV") + " = " + i("nRT"))),
      P(A(i("V") + " = " + frac(i("n") + " " + i("R") + " " + i("T"), i("P")) + " = " + frac("(0.0466) × (8.31) × (313)", "1 × 10" + sup(5)) +
          " = " + u("1.21 × 10" + sup(M + "3") + " m" + sup(3)) + " OR " + u("1.21 dm" + sup(3))))),
 PART("(a)(iii)",
      P(A("Under high pressure, the ethane molecules are forced closer together, so the " + u("volume occupied by the ethane gas molecules is no longer negligible as compared to the volume of the container") +
          " and the " + u("intermolecular instantaneous dipole induced dipole attractions between ethane molecules become significant") +
          ". These attractions reduce the frequency and force of collisions with the container walls, causing ethane to deviate from ideal gas behaviour at high pressure.")),
      P(N("Can just write IMF generally.")),
      P(N("The kinetic molecular theory assumes that the volume occupied by gas particles is negligible as compared to the volume of the container and that there are negligible intermolecular forces of attraction between the gas particles."))),
 PART("(a)(iv)",
      IMG(5, "aiv"),
      C(A("2,2,3,3-tetramethylbutane")),
      P(A("The Kolbe electrolysis of (CH" + sub(3) + ")" + sub(2) + "CHCH" + sub(2) + "COO" + sup(M) + " initially forms primary (CH" + sub(3) + ")" + sub(2) + "CHCH" + sub(2) + "• radicals which can rearrange to the " +
          u("more stable tertiary") + " " + RAD3 + " " + u("radicals, which have more electron-donating alkyl groups") + ". Tertiary radicals are more stable and therefore exist in higher (effective) concentration.")),
      P(A("The probability of radical coupling depends on both radical concentration and stability, so coupling of two tertiary radicals occurs more frequently.")),
      P(A("As a result, 2,2,3,3-tetramethylbutane is formed in much greater amount than 2,5-dimethylhexane."))),
 PART("(b)",
      P(A("To deduce the relative amounts of " + b("X") + ", " + b("Y") + " and " + b("Z") + " formed, both the number of abstractable hydrogen atoms and the relative rates of abstraction at each type of carbon must be considered.")),
      table(tr(th("Product"), th("Type of C–H substituted"), th("No. of H atoms available for substitution"), th("Relative rate of abstraction"), th("Weighted value")),
            tr(td(b("X") + " (1-chloro-2,5-dimethylhexane)"), td("Primary"), td("12"), td("1"), td("12 × 1 = " + b("12"))),
            tr(td(b("Y") + " (3-chloro-2,5-dimethylhexane)"), td("Secondary"), td("4"), td("4"), td("4 × 4 = " + b("16"))),
            tr(td(b("Z") + " (2-chloro-2,5-dimethylhexane)"), td("Tertiary"), td("2"), td("5"), td("2 × 5 = " + b("10")))),
      P(A("Ratio of " + b("X") + " : " + b("Y") + " : " + b("Z") + " = 12 : 16 : 10")),
      P(A("Relative amount of the three mono-chlorinated products: " + b("X") + " : " + b("Y") + " : " + b("Z") + " = " + u("6 : 8 : 5")))),
 PART("(c)(i)",
      IMG(5, "ci"),
      P(N("1 mark for correct single-headed curly arrows shown in both equations."))),
 PART("(c)(ii)",
      P(A("Mechanism: " + u("Electrophilic Addition"))),
      IMG(5, "cii"),
      P(N("Marking points: correct dipoles; arrow pushing (each arrow); slow step; correct tertiary carbocation intermediate; C" + L + sup(M) + " to balance the equation. Mechanism: 6–8 points earn 2 marks, 3–5 points earn 1 mark. 1 mark for the correct major product."))),
 PART("(c)(iii)",
      P(A(u("IC" + L + " is polar and undergoes electrophilic addition more readily with alkene") + " under mild (dark) conditions especially at low impurity level, so the alkane remains unreacted."))),
 PART("(d)(i)",
      IMG(5, "di"),
      P(N("1 mark for each intermediate."))),
 PART("(d)(ii)",
      P("Step 1 (electrophilic addition): ", A(u(CL2 + "(aq), r.t.p. (in the dark)"))),
      P("Step 2 (nucleophilic substitution): ", A(u("ethanolic KCN, heat"))),
      P("Step 3 (acidic hydrolysis): ", A(u("HC" + L + "(aq) / H" + sub(2) + "SO" + sub(4) + "(aq), heat"))),
      P(N("3 correct earn 2 marks; 1–2 correct earn 1 mark."))),
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
