"""Hand transcription of the NYJC 2026 H2 Prelim Paper 3 (9476/03) suggested answers
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's answers docx/PDF (35 pages): the question paper with each answer typed in blue,
red marking notes, underlined mark-bearing keywords (underlines read from the docx runs). Typed from the
rendered pages and the text layer.

Run from the repo root:
    python3 ingest/build_nyjc26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_nyjc26_p3.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions as build_nyjc26_p2_answers.py / build_njc26_p3_answers.py (claude/style-guide.md SS6):
div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u> on the school's
underlined keywords; figures are bare img.ws-fig[data-asset] (the user snips them:
NYJC_H2_P3_Q<n>_ans-<slot>_2026.png); tables are table.cmp; the school's red marking notes are span.note;
the school's [n] ticks, (bullet-dot) mark markers and red (1a)/(2b) numbering are dropped; the examiner
"Comments" blocks (4(a)(i), 5(b)(iv)) are NOT emitted (standing ruling).
Standard-state symbol: <sup><span class="pl-sym">⦵</span></sup> everywhere; no .stk in worked solutions.
Typo/grammar fixes follow the NYJC P1/P2 rulings; every one is listed in FIXES below for the user.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "NYJC_H2_P3", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
AL = "A" + L
DEL = "Δ"
K = i("K")
EM = "&emsp;"
PLS = '<span class="pl-sym">⦵</span>'
STD = sup(PLS)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
def sub_(s): return sub(s)
H2O, HP = "H" + sub(2) + "O", "H" + sup("+")
H3OP = "H" + sub(3) + "O" + sup("+")
MDM = "mol dm" + sup(M + "3")
Ecell = i("E") + STD + sub("cell")
def dG(): return DEL + i("G") + STD
def EST(s=""): return i("E") + STD + s
ARROW = " → "
EQ = " ⇌ "

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)
def BUL(*items): return [P(A(x)) for x in items]
def NOTE(t): return P(N(t))
def eq(s): return P(A(s))
def ion(sym, ch): return sym + sup(ch)
def pK(s): return "p" + K + sub(s)
def fm(s):
    """formula: subscript digits after a letter/')' ; Cl italic-l"""
    s = re.sub(r"(?<=[A-Za-z\)])(\d+)", lambda m: sub(m.group(1)), s)
    return s.replace("Cl", CL)
FIXES = []

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", P(A("1<i>s</i>" + sup(2) + "2<i>s</i>" + sup(2) + "2<i>p</i>" + sup(6) + "3<i>s</i>" + sup(2) + "3<i>p</i>" + sup(6) + "3<i>d</i>" + sup(5) + "4<i>s</i>" + sup(1)))),
 PART("(a)(ii)", P(A("A transition element is a d-block element whose atom has incomplete d subshell or which forms at least one stable ion with partially filled d orbital."))),
 PART("(b)",
      *BUL("In an octahedral complex ion, the presence of ligands causes the energy level of the five 3d orbitals to be split into two different levels (crystal field splitting or d-d splitting).",
           "The energy difference, " + i("E") + ", corresponds to wavelengths in the visible spectrum.",
           "When light energy is absorbed by the substance, an electron is promoted from a d orbital of lower energy to one of higher energy (d-d transition).",
           "Unabsorbed wavelengths are transmitted and the colour of the complex is complementary to the colour absorbed."),
      NOTE("4 points: 3 marks; 3 points: 2 marks; 2 points: 1 mark.")),
 PART("(c)(i)", P(A("Standard cell potential, " + Ecell + " is the maximum potential difference between two electrodes of a galvanic cell measured under standard conditions."))),
 PART("(c)(ii)", IMG(1, "cii"), NOTE("1 mark: salt bridge, standard conditions, voltmeter. 1 mark for each half-cell (2 marks).")),
 PART("(c)(iii)",
      eq(CL + sub(2) + " + 2e" + sup(M) + EQ + "2" + CL + sup(M) + EM + "+1.36 V" + EM + "(reduction)"),
      eq("Cr" + sup("3+") + " + 3e" + sup(M) + EQ + "Cr" + EM + M + "0.74 V" + EM + "(oxidation)"),
      eq("Overall: 2Cr + 3" + CL + sub(2) + ARROW + "2Cr" + sup("3+") + " + 6" + CL + sup(M)),
      eq(Ecell + " = (+1.36) " + M + " (" + M + "0.74) = +2.10 V"),
      NOTE("1 mark for both the equation and the value.")),
 PART("(c)(iv)", eq(dG() + " = " + M + "<i>nFE</i>" + STD + sub("cell") + " = " + M + "6(96 500)(+2.10) = " + M + "1215900 J mol" + sup(M + "1") + " = " + M + "1220 kJ mol" + sup(M + "1"))),
 PART("(d)",
      P(A(ion("Cr", "3+") + " ion has " + u("high charge density") + " and " + u("undergoes hydrolysis") + " to form an acidic solution:")),
      eq("[Cr(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+") + "(aq) + " + H2O + "(l)" + EQ + "[Cr(H" + sub(2) + "O)" + sub(5) + "(OH)]" + sup("2+") + "(aq) + " + H3OP + "(aq)"),
      P(A("The acidic solution will react with carbonate to form " + u("effervescence of CO" + sub(2) + "(g)") + ".")),
      eq("CO" + sub(3) + sup("2" + M) + " + 2" + H3OP + ARROW + "CO" + sub(2) + " + 3" + H2O + EM + "<b>or</b>" + EM + "CO" + sub(3) + sup("2" + M) + " + 2" + HP + ARROW + "CO" + sub(2) + " + " + H2O),
      P(A("Na" + sub(2) + "CO" + sub(3) + "(aq) is alkaline in nature and behaves like NaOH(aq). " + u("Grey-green precipitate of Cr(OH)" + sub(3)) + " is also formed via " + u("acid-base reaction") + ".")),
      eq("CO" + sub(3) + sup("2" + M) + "(aq) + " + H2O + "(l)" + EQ + "OH" + sup(M) + "(aq) + HCO" + sub(3) + sup(M) + "(aq)"),
      eq("Cr" + sup("3+") + "(aq) + 3OH" + sup(M) + "(aq)" + ARROW + "Cr(OH)" + sub(3) + "(s)"),
      eq("Overall equation: 2Cr" + sup("3+") + "(aq) + 3CO" + sub(3) + sup("2" + M) + "(aq) + 3" + H2O + "(l)" + ARROW + "2Cr(OH)" + sub(3) + "(s) + 3CO" + sub(2) + "(g)"),
      NOTE("6 or 7 points: 3 marks; 3–5 points: 2 marks; 2 points: 1 mark.")),
 PART("(e)(i)", P(A("Lattice energy is the energy change/evolved when one mole of an ionic compound is formed from its constituent gaseous ions at standard conditions."))),
 PART("(e)(ii)",
      IMG(1, "eii"),
      eq(M + "302 = +397 + (+31) + (+193) + (+653) + (+1590) + 2(" + M + "324) + LE(CrBr" + sub(2) + ")"),
      eq("LE(CrBr" + sub(2) + ") = " + M + "2518 = " + M + "2520 kJ mol" + sup(M + "1")),
      NOTE("All 5 correct levels: 2 marks; 3 or 4 correct levels: 1 mark.")),
 PART("(e)(iii)",
      P(A("Decreasing magnitude of LE: CrO, CrF" + sub(2) + ", CrBr" + sub(2))),
      P(A("| LE | ∝ " + frac("|" + i("z") + sup("+") + i("z") + sup(M) + "|", i("r") + sub("+") + " + " + i("r") + sub(M)))),
      *BUL("The ionic charge of O" + sup("2" + M) + " is double that of F" + sup(M) + " and Br" + sup(M) + ". The lattice energy of CrO will be more exothermic than CrF" + sub(2) + " and CrBr" + sub(2) + ".",
           "The ionic radius of F" + sup(M) + " is smaller than that of Br" + sup(M) + ". The lattice energy of CrF" + sub(2) + " will be more exothermic than CrBr" + sub(2) + "."),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
]
# ------------------------------------------------------------------ Q2
CLO4 = CL + "O" + sub(4)
W[2] = [
 PART("(a)(i)", IMG(2, "ai"),
      P(A("There are 4 bond pairs and 0 lone pairs around the " + CL + " atom, hence the electron pairs will arrange themselves as far apart as possible, resulting in a tetrahedral arrangement around "
          + CL + " atom and a O-" + CL + "-O bond angle of 109°.")),
      P(A("There are 2 bond pairs and 2 lone pairs around the O atom bonded to H atom. Since lone pair–lone pair repulsion is greater than lone pair–bond pair repulsion which is greater than "
          "bond pair–bond pair repulsion, the arrangement around the O atom is v-shaped with a H-O-" + CL + " bond angle of 105°.")),
      NOTE("Marking points: tetrahedral arrangement around the " + "C" + L + " atom; angle labelled to correspond to the shape drawn; numbers of bond pairs and lone pairs stated to correspond with the shape drawn; "
           "VSEPR theory quoted to correspond with the numbers of bond pairs and lone pairs stated. The same four points apply to the V-shaped arrangement around the O atom."),
      NOTE("8 points: 3 marks; 5–7 points: 2 marks; 3–4 points: 1 mark. Allow error carried forward from the second to fourth and sixth to eighth points.")),
 PART("(a)(ii)", P(A("Perchloric acid is a strong acid because its conjugate base, " + CLO4 + sup(M) + ", is very stable because the negative charge in " + CLO4 + sup(M) +
                    " is dispersed over several electronegative oxygen atoms. Therefore the extent of dissociation of H" + CLO4 + " is very large."))),
 PART("(a)(iii)", P(A(u("In perchloric acid, H" + CLO4 + ", chlorine is in the +7 oxidation state, which is its highest possible oxidation state.") +
                    " As a result, chlorine is highly oxidised and has a strong tendency to gain electrons (be reduced). " + u("Hence, perchloric acid is (highly) oxidising.")))),
 PART("(a)(iv)", P(A(u("The C-" + CL + " bond is relatively strong") + " making these compounds stable and inert under normal conditions."))),
 PART("(b)",
      P(A("Initial total n(H" + CLO4 + ") added = " + frac("10.00", "1000") + " × 0.100 = 1.000 × 10" + sup(M + "3") + " mol")),
      P(A("n(H" + CLO4 + ") left unreacted = n(CH" + sub(3) + "COONa) reacted = " + frac("5.40", "1000") + " × 0.100 = 5.400 × 10" + sup(M + "4") + " mol")),
      P(A("n(H" + CLO4 + ") reacted with basic substances in the oil = 1.000 × 10" + sup(M + "3") + " " + M + " 5.400 × 10" + sup(M + "4") + " = 4.600 × 10" + sup(M + "4") + " mol = n(KOH)")),
      P(A("m(KOH) in 2.000 g of oil = 4.600 × 10" + sup(M + "4") + " × 56.1 = 0.02580 g")),
      P(A("m(KOH) in 1.000 g of oil = 4.600 × 10" + sup(M + "4") + " × 56.1 ÷ 2 = 0.01290 g")),
      P(A("TBN = m(KOH) in 1.000 g of oil in mg = 0.01290 × 1000 = 12.9 mg KOH g" + sup(M + "1"))),
      NOTE("6 points: 2 marks; 3–5 points: 1 mark.")),
 PART("(c)(i)",
      P(A("The electron-withdrawing group withdraws electron density from the C=C double bond. As a result the terminal alkene / sp" + sup(2) + " hybridised carbon in C=C becomes electron deficient and susceptible to attack by nucleophile.")),
      P(A("<b>OR</b>")),
      P(A("The p orbitals of the three consecutive sp" + sup(2) + " hybridised C atoms overlap resulting in the delocalisation of π electrons from C=C across the carbonyl C towards electron-withdrawing group / electronegative O atom. "
          "As a result the terminal alkene / sp" + sup(2) + " hybridised carbon in C=C becomes electron deficient and susceptible to attack by nucleophile."))),
 PART("(c)(ii)", IMG(2, "cii")),
 PART("(d)",
      P(A(b("Test 1: reduction"))), P(A(b("Test 2: electrophilic addition and electrophilic substitution"))),
      P(A(b("Test 3: oxidation and acid-base reaction"))), P(A(b("Test 4: nucleophilic addition"))),
      P(A("From test 2, we know that in " + u("F") + ", there is an " + u("alkene") + " functional group which reacts with aq Br" + sub(2) + " to form " + u("bromoalkane") + " " + u("in H") +
          " and a " + u("phenol") + " functional group which undergoes multiple substitution with aq Br" + sub(2) + " to form " + u("bromoarenes") + " " + u("in H") +
          ". As only 2 H atoms in the benzene are substituted by 2 Br atoms, we know that the " + u("two side-chains are in 1,4 position") + ".")),
      P(A("From test 3, we know that there is a " + u("methyl ketone functional group in F") + " which undergoes oxidation with aqueous alkaline iodine to form the yellow precipitate, triiodomethane, CHI" + sub(3) +
          ". The phenol functional group also undergoes acid-base reaction with the alkaline present in test 3.")),
      P(A("Therefore, in test 1, the alkene and ketone functional groups in F reacts with H" + sub(2) + " to become " + u("alkane and secondary alcohol functional groups respectively in G") + ".")),
      P(A("In test 4, the alkene functional group in F reacts with CH" + sub(3) + "COCH" + sub(3) + " such that the unsaturated alkene becomes saturated alkane and an additional ketone functional group is introduced.")),
      IMG(2, "d"),
      NOTE("Each structure is 1 mark, so the total is 5 marks."),
      NOTE("6 correct types of reaction: 2 marks; 3–5 correct types of reaction: 1 mark."),
      NOTE("Reasoning: 2 marks (3 points: 2 marks; 1–2 points: 1 mark).")),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)", IMG(3, "ai"),
      P(A(i("Deduce from ideal gas equation"))),
      P(A("<i>pV</i> = <i>nRT</i>")),
      P(A("<i>V</i> = (<i>nR</i>/<i>p</i>)<i>T</i>, where the gradient of the graph = <i>nR</i>/<i>p</i>")),
      P(A("Since " + i("p") + sub(1) + " > " + i("p") + sub(2) + ", the gradient of graph for higher pressure " + i("p") + sub(1) + " will be smaller.")),
      P(A("<b>OR</b>")),
      P(A(i("Physical explanation"))),
      P(A("At a higher pressure " + i("p") + sub(1) + ", the external forces compressing the gas are stronger. Therefore, the gas particles are forced closer together, resulting in a " + u("smaller overall volume") + ".")),
      NOTE("1 mark for the graph; 1 mark for the explanation.")),
 PART("(a)(ii)",
      P(A("Hydrazine and ethylamine have simple molecular structure with hydrogen bonds between molecules. " + u("Hydrazine can form two hydrogen bonds per molecule while ethylamine can form one hydrogen bond per molecule."))),
      P(A("Hydrazine forms more extensive hydrogen bonds, hence, deviates more from ideal gas behaviour."))),
 PART("(b)(i)",
      NOTE("4 marking points: 3 marks; 3 marking points: 2 marks; 1–2 marking points: 1 mark."),
      *BUL("In order of increasing basicity: Q < phenylamine < 4-ethylphenylamine",
           "In phenylamine and 4-ethylphenylamine, the " + u("p orbital on N atom overlaps with the π electron cloud of the benzene ring") + ", " + u("resulting in the delocalisation of lone pair of electrons on N atom into the benzene ring") +
           ", hence " + u("less available") + " for dative bonding with a proton.",
           "4-ethylphenylamine is the strongest base. " + u("Electron donating ethyl group") + " " + u("increases the electron density of the nitrogen atom (of phenylamine)") + ". " +
           u("Lone pair of electrons on N atom is most available for dative bonding with a proton.") + " Hence phenylamine is a weaker base than 4-ethylphenylamine.",
           "In " + u("Q, an amide") + ", the " + u("p orbital on N atom overlaps with the π electron cloud of C=O") + " hence " + u("lone pair of electrons on N atom delocalised over the C=O group. Due to the electronegative O atom") +
           ", the lone pair of electrons on N atom is delocalised over the -CON group, thus making it " + u("not available for bonding with a proton") + ", hence Q is " + u("neutral") + ".")),
 PART("(b)(ii)", P(A(fm("AlCl3").replace("AlC", AL + "C") + " acts as a " + u("Lewis acid") + " and " + u("accepts an electron pair from CH" + sub(3) + "CH" + sub(2) + CL + " to form a stronger electrophile CH" + sub(3) + "CH" + sub(2) + sup("+")) + ".")),
      NOTE("For information: " + AL + CL + sub(3) + " + CH" + sub(3) + "CH" + sub(2) + CL + EQ + AL + CL + sub(4) + sup(M) + " + CH" + sub(3) + "CH" + sub(2) + sup("+"))),
 PART("(b)(iii)", IMG(3, "biii")),
 PART("(b)(iv)", IMG(3, "biv")),
 PART("(b)(v)", P(A("step 2: CH" + sub(3) + "CO" + CL + " (room temperature)")), P(A("step 4: NaOH(aq), heat"))),
 PART("(b)(vi)",
      *BUL("Electrophilic substitution",
           AL + CL + sub(3) + " + CH" + sub(3) + "CH" + sub(2) + CL + EQ + AL + CL + sub(4) + sup(M) + " + CH" + sub(3) + "CH" + sub(2) + sup("+") + " (reversible arrow optional)"),
      P(A("Step 2")), IMG(3, "bvi"), NOTE("Step 2: 3 points (arrow, slow, intermediate)."),
      P(A("Step 3")), IMG(3, "bvi2"), NOTE("Step 3: 3 points (arrow 1 including lone pair, arrow 2, balanced equation)."),
      NOTE("8 points: 3 marks; 6–7 points: 2 marks; 3 points: 1 mark.")),
 PART("(c)(i)", P(A("Condensation or nucleophilic acyl substitution"))),
 PART("(c)(ii)", P(A(u("Electronegativity of nitrogen is lower than oxygen") + ", N holds on to its lone pair of electrons less tightly and is " + u("more nucleophilic / a stronger nucleophile / more available to donate") +
                    " its lone pair of electrons to attack the electron deficient carbon on the acyl chloride."))),
]
# ------------------------------------------------------------------ Q4
RS = "RS•"
W[4] = [
 PART("(a)(i)", P(A("A radical is a species that has an unpaired electron."))),
 PART("(a)(ii)",
      eq(DEL + i("H") + "(reaction <b>A</b>) = [2BE(C-N) + BE(N=N) + 2BE(S-H)] " + M + " [BE(N≡N) + 2BE(C-H)]"),
      eq("= [2(305) + 410 + 2(347)] " + M + " [944 + 2(410)]"),
      eq("= " + M + "50 kJ mol" + sup(M + "1"))),
 PART("(a)(iii)", P(A(u("Propagation") + ". A " + u("radical") + " is produced and consumed in each step from <b>B</b> to <b>E</b>.")), P(A("<b>OR</b>")),
      P(A("The reactive intermediate, RS•, is being used in step <b>B</b> but regenerated in step <b>E</b>."))),
 PART("(a)(iv)", IMG(4, "aiv"), NOTE("1 mark for step D; 1 mark for step E.")),
 PART("(a)(v)", IMG(4, "av"),
      P(A("The other product is not formed as the two bulky alkyl groups sterically hinder the alkyl radical to attack the alkene carbon that they are bonded to.")), P(A("<b>OR</b>")),
      P(A("A more stable tertiary alkyl radical is formed in the production of <b>F</b> while a less stable secondary alkyl radical is formed in the production of <b>G</b> in step <b>D</b>.")),
      NOTE("1 mark for the structure of F; 1 mark for the explanation.")),
 PART("(a)(vi)", P(A("The S-H bond dissociation energy of methanethiol is lower than the O-H bond dissociation energy of methanol as the S atom has a larger atomic radius than the O atom, "
                    "the S-H bond length will be longer than that of the O-H bond. Hence, the S-H bond will be weaker than the O-H bond."))),
 PART("(b)(i)", P(A("The Mn" + sup("2+") + " catalyst is first oxidised to Mn" + sup("3+") + " to generate the radical intermediate before being reduced to regenerate Mn" + sup("2+") + " in order to form the dichloroalkanes."))),
 PART("(b)(ii)", P(A("It can exhibit variable oxidation states."))),
 PART("(b)(iii)",
      eq(Ecell + " = " + EST(sub("r")).replace(i("E") + STD, i("E") + STD, 1) + " " + M + " " + EST(sub("o"))),
      eq(M + "2.3 = " + EST("(H" + sup("+") + "/H" + sub(2) + ")") + " " + M + " " + EST("([Mn" + sup("III") + "-" + CL + "]/[Mn" + sup("II") + "-" + CL + "])")),
      eq(M + "2.3 = 0 " + M + " " + EST("([Mn" + sup("III") + "-" + CL + "]/[Mn" + sup("II") + "-" + CL + "])")),
      eq(EST("([Mn" + sup("III") + "-" + CL + "]/[Mn" + sup("II") + "-" + CL + "])") + " = +2.3 V")),
 PART("(b)(iv)",
      P(A(u("Enantiomers") + " <b>H</b> and <b>J</b> will be produced in a " + u("1:1 ratio") + ".")),
      P(A("The " + u(CL + "• radical can attack the trigonal planar radical carbon centre") + " from " + u("either above or below the plane in equal probabilities") + " yielding equal quantities of both enantiomers <b>H</b> and <b>J</b>.")),
      NOTE("4 points: 3 marks; 3 points: 2 marks; 2 points: 1 mark.")),
 PART("(c)(i)", IMG(4, "ci"), NOTE("Arrows can be clockwise (see cii ans) or anticlockwise (shown above)."), NOTE("3 arrows: 2 marks; 2 arrows: 1 mark.")),
 PART("(c)(ii)", P(A("The " + u("trans-diene has the 2 terminal C=C opposite/further away") + " from each other such that their " +
                    u("p orbitals are unable to overlap with the p orbitals of the dienophile simultaneously / will result in ring strain if a ring is formed with dienophile") + "."))),
 PART("(c)(iii)", P(A("(1)")), IMG(4, "ciii"), P(A("(2)")), IMG(4, "ciii2"), IMG(4, "ciii3")),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A("Concentrated H" + sub(3) + "PO" + sub(4) + " (catalyst), heat"))),
 PART("(a)(ii)",
      P(A("<b>X</b> is " + u("maleic acid") + ".")),
      IMG(5, "aii"),
      NOTE("1 mark for the displayed formula (error carried forward); 1 mark for the mono-anion (error carried forward)."),
      NOTE("Benefit of the doubt for the diagram if the student never shows the hydrogen bond for the cis isomer."),
      P(A("The " + u("formation of (intra-molecular) hydrogen bonding") + " " + N("(can be in diagram)") + " between the " + u("adjacent") + " " + N("(or cis)") + " -COOH and -COO" + sup(M) + " groups in the " + u("cis isomer") + " of maleic acid")),
      P(A(u("stabilises the mono-anion") + " which is the conjugate base of " + K + sub("a1") + " hence it is a " + u("stronger acid with a lower p" + K + sub("a1") + " value") + ".")),
      P(A("In addition, it is " + u("unfavourable to donate the 2" + sup("nd") + " proton") + " as the stabilising hydrogen bond is disrupted hence it has a " + u("higher p" + K + sub("a2") + " of 6.2") + " as it is a weaker acid. ")),
      NOTE("Both p" + K + sub("a") + " values should be used in the explanation."),
      NOTE("6 points: 3 marks; any 4 points: 2 marks; any 2 points: 1 mark. Similar concept in 2019 P2 Q4(c).")),
 PART("(a)(iii)", IMG(5, "aiii"), P(A("3 curly arrows (including one lone pair on " + CL + sup(M) + " for one of them).")), NOTE("All 3 arrows: 2 marks; any 2 arrows: 1 mark.")),
 PART("(b)(i)", NOTE("Aspartic acid exhibits enantiomerism."), IMG(5, "bi")),
 PART("(b)(ii)", P(A("The " + u("biochemical route") + " is more likely to produce a single enantiomer, in this case (" + M + ") aspartic acid, as it " + u("involves an enzyme which has high specificity") +
                    " and only reacts with specific substrate/" + u("forms products with a particular spatial arrangement") + " that can " + u("fit well in its 3D active site/ due to the lock-and-key model") + ".")),
      NOTE("3 points: 2 marks; biochemical route plus some mention of enzymes: 1 mark.")),
 PART("(b)(iii)",
      TBL(["conc / " + MDM, "Fumaric acid(aq)", "+ NH" + sub(3) + "(aq)", EQ.strip(), "Aspartic acid(aq)"],
          ["Initial", "0.88", "3.1", "", "0"],
          ["Change", M + "0.85(0.88) = " + M + "0.748", M + "0.748", "", "+0.748"],
          ["Eqm", "0.132", "2.352", "", "0.748"]),
      P(A(K + sub("c") + " = " + frac("[Aspartic acid]", "[Fumaric acid][NH" + sub(3) + "]") + " = " + frac("(0.748)", "(0.132)(2.352)") + " = 2.4 mol" + sup(M + "1") + " dm" + sup(3))),
      NOTE("6 points: 2 marks; 3 points: 1 mark.")),
 PART("(b)(iv)",
      P(A(u("Temperature was increased") + ". According to Le Chatelier's Principle, the " + u("backward endothermic reaction was favoured") + ". Hence " + u("position of equilibrium shifted left") + " and " + u(K + sub("c") + " decreases") + ".")),
      NOTE("4 points: 2 marks; any 2 points: 1 mark."),
      P(A("The bacteria provide the aspartase enzyme which catalyses the reaction. " + u("Adding more catalyst increases rate at which equilibrium is established/increases rate of both forward and backward reactions to the same extent") + " but " + u("does not affect " + K + sub("c") + " value") + ".")),
      NOTE("1 mark for the suggestion plus some explanation.")),
 PART("(c)(i)",
      P(A("Polymers are " + u("macromolecules built up from monomers") + ", with " + u("average molar mass of at least 1000 or at least 100 repeat units") + ".")),
      NOTE("This point is needed as the question is for 2 marks; the points can be combined below."),
      P(A("Condensation polymers form when " + u("bifunctional monomers / monomers containing 2 functional groups") + " react to form a long chain polymer / (macromolecule with average molar mass of at least 1000 or at least 100 repeat units). A " +
          u("small molecule is eliminated during the reaction") + "."))),
 PART("(c)(ii)", IMG(5, "cii"),
      P(A("The two carboxylic groups in aspartic acid should have reacted as PSI does not undergo neutralisation with Na" + sub(2) + "CO" + sub(3) + ".")),
      P(A("Working backwards from PAsp, an amide present in PSI should have undergone basic hydrolysis to form PAsp."))),
 PART("(c)(iii)",
      P(A("During condensation polymerisation of aspartic acid to form PAsp, a H" + sub(2) + "O molecule is lost (" + DEL + i("M") + sub("r") + " of 18.0) and a H is also replaced with Na (" + DEL + i("M") + sub("r") + " of 22.0).")),
      P(A("∴ mass of one repeating unit = 133.0 − 18.0 − 1 + 23.0 = 137.0")),
      P(A("∴ number of repeating units = 30,000 / 137.0 = 218.9781 ≈ 219 units."))),
 PART("(c)(iv)", P(A("PAsp contains a " + u("peptide (amide)") + " functional group which can " + u("undergo hydrolysis") + " readily to form non-toxic small molecules (like CO" + sub(2) + " and water) within the body."))),
 PART("(c)(v)", P(A("PAsp readily binds to / has a strong affinity for Ca" + sup("2+") + " in bones as the numerous " + u("COO" + sup(M) + " groups can form strong ionic bonds with Ca" + sup("2+") + " in bones") + ".")),
      NOTE("Also accept coordinate bonds that are formed between COO" + sup(M) + " of EDTA" + sup("4" + M) + " and Ca" + sup("2+") + "."),
      NOTE("For information: in fact, PAsp is able to chelate Ca" + sup("2+") + ", meaning it forms a stable ring structure as numerous bonds are formed concurrently, e.g. EDTA is a good chelating agent as it is a hexadentate ligand.")),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    assert not re.search(r"\[\d+\]", re.sub(r"<[^>]+>", "", h)), (qn, re.findall(r".{20}\[\d.{10}", h))
    for bad in ("<sup>o</sup>", "<sup>⦵</sup>", "stk"):
        assert bad not in h, (qn, bad)
    out[str(qn)] = h

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
