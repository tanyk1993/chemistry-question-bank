"""Hand transcription of the VJC suggested answers to A Level (SEAB) 9729/03 Oct/Nov 2025
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the college answers docx + its Word PDF (8 pages); typed from the rendered pages and checked
against the docx text (see the verification at the bottom).

Run from the repo root:
    python3 ingest/build_alevel25_p3_answers.py <outdir> <questions_dir> [<answers.docx>]
(<questions_dir> = the folder holding questions.json from build_alevel25_p3.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6, build_alevel25_p2_answers.py, build_alevel_p3_answers.py):
  div.worked-solution > div.part > (span.lab + div.body); answers in span.ans (<u> on the school's
  underlined final answers); figures are bare img.ws-fig[data-asset] (the user snips them:
  SEAB_H2_P3_Q<n>_ans-<slot>_2025.png); tables are table.cmp (no thead/th).
  The school's black boxed / italic explanatory notes are kept as p.mark-note; the one red marker
  note (1(b)(i), "pH of 7 should be below the mid-point...") is dropped: the user moved the box off the
  graph before snipping (ruling 2026-11-03).
RULED_FIXES holds the wording/chemistry changes the user has ruled on; nothing is changed silently.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
DOCX = sys.argv[3] if len(sys.argv) > 3 else None
PFX = "SEAB_H2_P3"
YEAR = 2025
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
TIMES = "×"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def NOTE(t): return '<p class="mark-note">%s</p>' % t
def UL(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<li>\s*</li>", "", h)
    h = re.sub(r'<ul class="stmts">\s*</ul>', "", h)
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW, EQ = " → ", " ⇌ "
def ion(sym, ch): return sym + sup(ch)
def chem(s):
    """Compact formula notation -> house markup (same as build_alevel25_p3.py)."""
    parts = re.split(r"(\^[^^]*\^)", s)
    out = []
    for seg in parts:
        if seg.startswith("^") and seg.endswith("^") and len(seg) >= 2:
            out.append(sup(seg[1:-1].replace("-", M)))
        else:
            seg = re.sub(r"(?<=[A-Za-z\)\]])(\d+)", lambda m: sub(m.group(1)), seg)
            seg = re.sub(r"(?<=[AC])l(?![a-z])", L, seg)
            out.append(seg)
    return "".join(out)
K = i("K")
Ka, Kb, Kc, Kw = K + sub("a"), K + sub("b"), K + sub("c"), K + sub("w")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
DH = DEL + i("H")
def dh(s): return DH + sub(s)
E0 = i("E") + sup("⦵")
STDP = '<span class="pl-sym">⦵</span>'
ECELL = i("E") + '<span class="stk post"><span>%s</span><span>cell</span></span>' % STDP
def E(x): return E0 + "(" + x + ")"
DB = i("Data Booklet")
FE2 = ion("Fe", "2+")
H2O = "H" + sub(2) + "O"
O2 = "O" + sub(2)

ASSETS = []     # (question, slot) in per-question DOM order
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s_Q%d_ans-%s_%d.png" alt=""></p>' % (PFX, qn, slot, YEAR)

W = {}   # qn -> list of PART html
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", P(A("Electronegativity of an element measures the relative tendency of its atom to attract the shared pair of electrons in a covalent bond."))),
 PART("(a)(ii)",
      P(A("OCS is a polar molecule. As oxygen is more electronegative than sulfur, the C=O bond dipole is larger than the C=S bond dipole. "
          "Because the bond dipoles are unequal, they do not cancel, resulting in a net dipole moment towards the oxygen end.")),
      P(A(chem("CO2") + " is non–polar molecule. Although each C=O bond is polar, the molecule is linear and symmetrical. "
          "The two C=O bond dipoles are equal in magnitude and act in opposite directions, so they cancel out, giving no net dipole moment."))),
 PART("(b)(i)", IMG(1, "bi")),
 PART("(b)(ii)", P(A("At the equilvalence point, the rapid pH change region is higher than 7. Metacresol purple is the most suitable indicator as its "
                     "working pH range lies within the range of rapid pH change at the equivalence point of the weak acid–strong base titration."))),
 PART("(c)",
      P(A(chem("HClO + NaOH") + ARROW + chem("NaClO + H2O"))),
      P(A("Amount of NaOH added = " + frac("25.00", "1000") + " " + TIMES + " 0.500 = 0.0125 mol")),
      P(A("Amount of HClO added = " + frac("32.75", "1000") + " " + TIMES + " 0.400 = 0.0131 mol")),
      P(A("NaOH is the limiting reagent.")),
      P(A("Total volume of mixture = 25.00 + 32.75 = 57.75 cm" + sup("3"))),
      P(A("Amount of NaClO formed = 0.0125 mol")),
      P(A("Amount of HClO left = 0.0131 " + M + " 0.0125 = 6.00 " + TIMES + " 10" + sup(M + "4") + " mol")),
      P(A("A buffer is formed which is made up of the weak acid, HClO and its salt, NaClO.")),
      P(A(Ka + " = " + frac("[H" + sup("+") + "][ClO" + sup(M) + "]", "[HClO]"))),
      P(A("2.95 " + TIMES + " 10" + sup(M + "8") + " = [H" + sup("+") + "] " + TIMES + " (" + frac("0.0125", "57.75 " + TIMES + " 10" + sup(M + "3")) + ") ÷ (" +
          frac("6.00 " + TIMES + " 10" + sup(M + "4"), "57.75 " + TIMES + " 10" + sup(M + "3")) + ")")),
      P(A("[H" + sup("+") + "] = 1.41 " + TIMES + " 10" + sup(M + "9") + " " + MDM)),
      P(A("pH = " + M + "lg(1.41 " + TIMES + " 10" + sup(M + "9") + ") = " + u("8.85"))),
      NOTE("Note: A buffer made up of a weak acid and its conjugate base can have a pH that is greater than 7 if"),
      UL('<span class="note">the weak acid has a p' + K + sub("a") + ' &gt; 7, and/or</span>',
         '<span class="note">the buffer contains a much higher concentration of A' + sup(M) + ' than that of HA.</span>')),
 PART("(d)", P(A("The standard cell potential, " + ECELL + " is the potential difference between two half–cells under standard conditions at 298 K, "
                 "pressure of any gases involved at 1 bar and concentrations of any aqueous ions involved at 1 " + MDM + "."))),
 PART("(e)", IMG(1, "e")),
 PART("(f)(i)",
      P(A("From " + DB + ":")),
      TBL(["", E0],
          [FE2 + " + 2e" + sup(M) + EQ + "Fe", M + "0.44 V"],
          [O2 + " + 2" + H2O + " + 4e" + sup(M) + EQ + "4OH" + sup(M), "+0.40 V"]),
      P(A(ECELL + " = " + E0 + sub("red") + " " + M + " " + E0 + sub("oxid") + " = " + E("O" + sub(2) + " | OH" + sup(M)) + " " + M + " " +
          E(FE2 + " | Fe") + " = (+0.40) " + M + " (" + M + "0.44) = " + u("+0.84 V"))),
      P(A("Oxidation: Fe(s)" + ARROW + FE2 + "(aq) + 2e" + sup(M))),
      P(A("Reduction: " + O2 + "(g) + 2" + H2O + "(l) + 4e" + sup(M) + ARROW + "4OH" + sup(M) + "(aq)")),
      P(A("Overall equation: 2Fe(s) + " + O2 + "(g) + 2" + H2O + "(l)" + ARROW + "2Fe(OH)" + sub(2) + "(s)"))),
 PART("(f)(ii)",
      P(A("From " + DB + ":")),
      TBL(["", E0],
          [FE2 + " + 2e" + sup(M) + EQ + "Fe", M + "0.44 V"],
          ["Mg" + sup("2+") + " + 2e" + sup(M) + EQ + "Mg", M + "2.38 V"],
          ["Zn" + sup("2+") + " + 2e" + sup(M) + EQ + "Zn", M + "0.76 V"]),
      P(A("Magnesium is more effective in preventing rusting of iron because " + E("Mg" + sup("2+") + " | Mg") + " is much more negative than " +
          E("Zn" + sup("2+") + " | Zn") + ", so Mg is oxidised more readily than Zn and provides stronger sacrificial protection to iron."))),
 PART("(g)",
      P(A("Oxidation: Fe(OH)" + sub(2) + "(s) + OH" + sup(M) + "(aq)" + ARROW + "Fe(OH)" + sub(3) + "(s) + e" + sup(M))),
      P(A("Reduction: " + O2 + "(g) + 2" + H2O + "(l) + 4e" + sup(M) + ARROW + "4OH" + sup(M) + "(aq)")),
      P(A("Overall equation: 4Fe(OH)" + sub(2) + "(s) + " + O2 + "(g) + 2" + H2O + "(l)" + ARROW + "4Fe(OH)" + sub(3) + "(s)"))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)", P(A(u("Any 2 of the following assumptions:"))),
      UL(A("The gas particles occupy negligible volume compared to the volume of the container."),
         A("The gas particles have negligible intermolecular forces of attraction."),
         A("Collisions between gas particles are perfectly elastic."))),
 PART("(b)", IMG(2, "b"),
      NOTE("pV = nRT"),
      NOTE("p = nRT(" + frac("1", "V") + ")"),
      NOTE("For a fixed mass of gas at constant T, graph of p against (1/V) gives a straight line passing through the origin.")),
 PART("(c)",
      P(A("Total amount of " + O2 + " and N" + sub(2) + " = " + frac("4.00", "32.0") + " + " + frac("4.00", "28.0") + " = 0.268 mol")),
      P(A("pV = nRT")),
      P(A("V = " + frac("nRT", "P") + " = " + frac("0.268 " + TIMES + " 8.31 " + TIMES + " (40 + 273)", "750 " + TIMES + " 10" + sup("3")) +
          " = 9.29 " + TIMES + " 10" + sup(M + "4") + " m" + sup("3") + " = " + u("929 cm" + sup("3"))))),
 PART("(d)(i)", P(A("Protons are positively charged and are deflected towards the negative plate, electrons are negatively charged and are deflected "
                    "towards the positive plate. Hence, the beams are deflected in opposite directions in an electric field.")),
      P(A("Electrons are much lighter than protons. Hence electrons are deflected more than protons in an electric field."))),
 PART("(d)(ii)",
      P(A("Angle of deflection = " + i("k") + " (" + frac("charge", "mass") + ")")),
      P(A("+5.5 = " + i("k") + "(" + frac("+1", "63") + ")")),
      P(A(i("k") + " = 346.5")),
      P(A("Angle of deflection of " + sup("19") + "F" + sup(M) + " = 346.5(" + frac(M + "1", "19") + ") = " + u(M + "18.2°")))),
 PART("(d)(iii)", P(A("It is the ratio of the mass of one atom of the isotope to " + frac("1", "12") + " of the mass of an atom of " + sup("12") + "C isotope."))),
 PART("(d)(iv)", P(A(i("A") + sub("r") + " of Cu = " + frac("69.15", "100") + " " + TIMES + " 62.930 + " + frac("30.85", "100") + " " + TIMES + " 64.928 = " + u("63.55") + " (2 d.p.)"))),
 PART("(e)", P(A(u("Similarities:"))),
      P(A("Both orbitals are spherical in shape.")),
      P(A("Both orbitals can accommodate a maximum of 2 electrons with opposite spins.")),
      P(A(u("Difference (Any one):"))),
      P(A("2s orbital is larger than the 1s orbital.")),
      P(A("2s orbital is higher in energy than the 1s orbital."))),
 PART("(f)(i)", IMG(2, "fi")),
 PART("(f)(ii)", P(A("Nitrogen has a higher nuclear charge than boron, so its 1s subshell electrons are more strongly attracted to the nucleus and have a higher binding energy."))),
 PART("(g)", IMG(2, "g")),
]
# ------------------------------------------------------------------ Q3
MCO3, MO = chem("MCO3"), "MO"
W[3] = [
 PART("(a)(i)", P(A("Thermal stability of Group 2 carbonates increases down the group.")),
      P(A("Down the group, the cationic charge remains constant but the cationic radius increases. Hence, the charge density of the cation decreases, "
          "so its polarising power decreases. As a result, the cation causes less distortion of the " + chem("CO3^2-^") + " anion. The C–O bonds within the " +
          chem("CO3^2-^") + " anion are weakened to a lesser extent, making the " + chem("CO3^2-^") + " more stable to heat. "
          "Therefore, more energy is required to decompose Group 2 carbonates down the group."))),
 PART("(a)(ii)", P(A("Lattice energy is the energy released when one mole of an ionic solid is formed from its isolated gaseous ions from an infinite distance apart."))),
 PART("(a)(iii)", IMG(3, "aiii"),
      P(A("By Hess’ Law,")),
      P(A(dh("1") + " = " + M + dh("latt") + "(" + MCO3 + ") + " + dh("2") + " + " + dh("latt") + "(MO)")),
      P(A("For decomposition of " + chem("MgCO3") + ", " + dh("1") + " = " + M + "(" + M + "3450) + " + dh("2") + " + (" + M + "3790) = (" + dh("2") + " " + M + " 340) kJ mol" + sup(M + "1"))),
      P(A("For decomposition of " + chem("CaCO3") + ", " + dh("1") + " = " + M + "(" + M + "3150) + " + dh("2") + " + (" + M + "3400) = (" + dh("2") + " " + M + " 250) kJ mol" + sup(M + "1"))),
      P(A("Down the group, " + dh("1") + " for decomposition of Group 2 carbonate becomes less exothermic because the difference between the lattice energy of "
          "the Group 2 carbonate and the Group 2 oxide decreases."))),
 PART("(b)(i)", IMG(3, "bi"),
      P(A("By Hess’ Law,")),
      P(A("Bond energy (Li–Li) = 2(+50.0) " + M + " 2(" + M + "520) " + M + " 2(+519) = +102 kJ mol" + sup(M + "1")))),
 PART("(b)(ii)", P(A("The 2s orbital of one Li atom overlaps head-on with the 2s orbital of the other Li atom along the internuclear axis, forming a σ bond."))),
 PART("(c)(i)", P(A("Energy is absorbed to break bonds in the reactants and released when new bonds form in the products.")),
      P(A("If bond formation releases more energy than the energy required in bond breaking, the reaction is exothermic."))),
 PART("(c)(ii)", IMG(3, "cii"),
      P(A("By Hess’ Law,")),
      P(A(DH + " = 6BE(O–O) " + M + " 3BE(O=O)")),
      P(A("= 6(+150) " + M + " 3(496)")),
      P(A("= " + u(M + "588 kJ mol" + sup(M + "1")))),
      P(A("Since " + DH + " is negative, the decomposition of " + chem("O6") + " into " + O2 + " is exothermic.")),
      P(A("This indicates that more energy is released when strong O=O double bonds are formed in " + O2 + " molecules than the energy required to break the "
          "weaker O–O single bonds in the " + chem("O6") + " ring. Hence, oxygen is more stable as " + O2 + " rather than " + chem("O6") + "."))),
 PART("(d)", P(A("Ease of hydrolysis:")),
      P(A("acyl chlorides &gt; alkyl chlorides &gt; aryl chlorides")),
      P(A("In acyl chloride, the carbonyl C atom is highly electron deficient due to the electron-withdrawing inductive effect of both the electronegative O and " + CL +
          " atoms, making it highly susceptible to nucleophilic attack. The carbonyl carbon is also sp" + sup("2") + "– hybridised and trigonal planar, allowing "
          "easier approach of the nucleophile with less steric hindrance. In contrast, the C atom bonded to " + CL + " in an alkyl chloride is sp" + sup("3") +
          "–hybridised and tetrahedral, resulting in greater steric hindrance to nucleophilic attack.")),
      P(A("In aryl chloride, the p orbital of " + CL + " atom overlaps with the p orbitals of the C atoms in the benzene ring, causing the delocalisation of the lone pair "
          "of electrons on " + CL + " into the benzene ring. This confers partial double bond character in the C–" + CL + " bond, which makes the C–" + CL +
          " bond stronger and cleavage of the C–" + CL + " bond more difficult. The benzene ring also poses steric hindrance, making it difficult for the nucleophile "
          "to approach the electron deficient carbon."))),
 PART("(e)",
      P(A(b("A") + " is a di–substituted benzene derivative containing only one chiral C atom.")),
      P(A(b("B") + " is " + u(chem("CHI3")) + ". " + b("A") + " undergoes " + u("oxidative cleavage") + " with alkaline " + chem("I2(aq)") + ", to give " + u(b("B") + ", " + chem("CHI3")) +
          " and carboxylate, " + chem("RCO2^-^") + ", which gives " + b("C") + ", " + u(chem("RCO2H") + ", after acidification") + ".")),
      P(A(b("A") + " " + u("contains a " + chem("RCOCH3")) + " structure since molecular formula of " + b("A") + " to " + b("C") + " showed a net decrease of 2 H atoms, "
          "–" + chem("CH3CH(OH)") + " group would have caused a net decrease of 4 H atoms.")),
      P(A(b("A") + " undergoes " + u("oxidative cleavage") + " with excess of hot, concentrated, acidified " + chem("KMnO4") + " to give " + b("E") + ", " + chem("C9H10O3") + ", and " +
          b("F") + ", " + chem("C3H4O3") + ". " + b("A") + " is an " + u("alkene") + ".")),
      P(A(b("C") + ", " + b("E") + " and " + b("F") + " undergoes " + u("acid-base reaction") + " with " + chem("Na2CO3") + " to give effervescence of " + chem("CO2") +
          " gas and thus " + b("C") + ", " + b("E") + " and " + b("F") + " each contains the " + u("carboxylic acid") + " functional group.")),
      P(A(b("F") + " is " + chem("CH3COCO2H") + ".")),
      P(A("Since " + b("E") + " undergoes " + u("electrophilic substitution") + " with " + chem("HNO3") + " without conc " + chem("H2SO4") + " catalyst, " + b("E") +
          " contains a " + u("phenol") + " group. The lone pair on O delocalises into the benzene ring, increasing its reactivity towards electrophilic substitution. "
          "Hence, " + b("A") + " also contains a " + u("phenol") + " group.")),
      P(A("Given that " + b("E") + " has only 1 chiral C atom,")),
      IMG(3, "e"),
      P(A("Since " + b("A") + " (" + chem("C12H14O2") + ") contains the alkene and phenol functional groups, it undergoes " +
          u("electrophilic addition and electrophilic substitution respectively with " + chem("Br2(aq)")) + " to give " + b("B") + ", " + chem("C12H12Br4O2") + ".")),
      IMG(3, "e2"),
      NOTE("In reaction of " + b("A") + " with " + chem("Br2(aq)") + ", the minor product is formed rather than adding 1 Br and 1 OH across C=C bond as this will increase the number of O atoms."),
      NOTE("Remaining 2 Br atoms are due to electrophilic substitution of phenol (loss in 2 H atoms).The di–substitution are at 1,2– or 1,4– positions, since only 2 Br are involved, not 3."),
      NOTE("Note: " + b("A") + ", " + b("C") + ", " + b("D") + ", " + b("E") + " and " + b("G") + " must all be consistently 1,2-disubstituted or consistently 1,4-disubstituted benzene derivatives.")),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)", P(A("For constitutional isomerism, the isomers have the same molecular formula but different structural formulae (or connectivity of atoms)."))),
 PART("(a)(ii)", IMG(4, "aii")),
 PART("(a)(iii)", P(A("In alkenes, " + i("cis") + "–" + i("trans") + " isomerism arises from the restricted rotation about the C=C bond due to the presence of π bond. "
                      "Each carbon atom of the C=C bond is bonded to two different atoms / groups."))),
 PART("(b)", P(A(chem("LiAlH4") + " does not reduce alkenes because both the C=C bond and H" + sup(M) + " are electron– rich, so electrostatic repulsion occurs "
                 "and H" + sup(M) + " attack on the C=C bond does not take place."))),
 PART("(c)", P(A("Mechanisim: Electrophilic addition")), IMG(4, "c"),
      P(A("The major product is " + chem("CH3CHBrCH2I") + " because the intermediate " + chem("CH3CH^+^CH2I") + " is a secondary carbocation, which is more stable due to "
          "greater electron–donating inductive effect from two alkyl groups. There would be less of the minor product as it would be formed from the less stable "
          "primary carbocation (" + chem("CH3CHICH2^+^") + ")."))),
 PART("(d)(i)", P(A(chem("S8") + " has the highest melting point, followed by " + chem("P4") + ", and " + chem("Cl2") + " has the lowest melting point.")),
      P(A(chem("P4") + ", " + chem("S8") + " and " + chem("Cl2") + " are simple discrete molecules held by weak instantaneous dipole–induced dipole (id–id) interactions.")),
      P(A(chem("S8") + " has the highest melting point as it has the greatest number of electrons and thus the electron cloud is the most polarisable. "
          "The id–id interactions between " + chem("S8") + " molecules is the strongest and requires the greatest energy to overcome.")),
      P(A(chem("Cl2") + " has the lowest melting point as it has the least number of electrons. Hence it has the least polarisable electron cloud and its id–id "
          "interactions requires the least energy to overcome."))),
 PART("(d)(ii)", P(A(chem("CH3CH2CH2OH") + " and " + chem("CH3SCH3") + " are both simple discrete molecules. " + chem("CH3CH2CH2OH") + " molecules are held by hydrogen "
                     "bonding while the polar " + chem("CH3SCH3") + " molecules are held by permanent dipole–permanent dipole (pd–pd) forces of attraction. "
                     "Since number of electrons is the same for both molecules, the instantaneous dipole–induced dipole interactions is comparable for both " +
                     chem("CH3CH2CH2OH") + " and " + chem("CH3SCH3") + ". Hence, more energy is required to overcome the stronger hydrogen bonding between " +
                     chem("CH3CH2CH2OH") + " molecules than the weaker pd–pd forces between " + chem("CH3SCH3") + " molecules, leading to a higher boiling point for " +
                     chem("CH3CH2CH2OH") + "."))),
 PART("(e)",
      TBL(["", "4HC" + L + "(g)", "+ " + O2 + "(g)", EQ.strip(), "2C" + L + sub(2) + "(g)", "+ 2" + H2O + "(g)"],
          ["initial amt (mol)", "0.175", "0.0500", "", "0.000", "0.00"],
          ["change (mol)", M + "0.72(0.175)", M + frac("0.72(0.175)", "4"), "", "+" + frac("2(0.72)(0.175)", "4"), "+" + frac("2(0.72)(0.175)", "4")],
          ["eqm amt (mol)", "0.049", "0.0185", "", "0.063", "0.063"],
          ["eqm conc (mol dm" + sup(M + "3") + ")", frac("0.049", "3.5") + "<br>= 0.014", frac("0.0185", "3.5") + "<br>= 0.005286", "",
           frac("0.063", "3.5") + "<br>= 0.018", frac("0.063", "3.5") + "<br>= 0.018"]),
      P(A(Kc + " = " + frac("[C" + L + sub(2) + "]" + sup("2") + "[" + H2O + "]" + sup("2"), "[HC" + L + "]" + sup("4") + "[" + O2 + "]") + " = " +
          frac("0.018" + sup("2") + " " + TIMES + " 0.018" + sup("2"), "0.014" + sup("4") + " " + TIMES + " 0.005286") + " ≈ 517 mol" + sup(M + "1") + " dm" + sup("3"))),
      NOTE("Note: Although question is in the gaseous state, we are required to calculate " + Kc + ", not " + K + sub("p") + ". Expression for " + Kc +
           " uses concentrations instead of partial pressures.")),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A("2HBr(g) ⟶ " + chem("H2(g)") + " + " + chem("Br2(g)"))),
      P(A("Reddish–brown fumes of " + chem("Br2") + " is observed."))),
 PART("(a)(ii)",
      P(A("BE(H–" + CL + ") = +431 kJ mol" + sup(M + "1"))),
      P(A("BE(H–Br) = +366 kJ mol" + sup(M + "1"))),
      P(A("BE(H–I) = +299 kJ mol" + sup(M + "1"))),
      P(A("Down the group, the atomic radius of the halogen increases, leading to poorer extent of orbital overlap. H–X bond becomes longer and weaker. "
          "Less energy is required to break the H–X bond, leading to less endothermic bond energy down the group.")),
      P(A("Hence, thermal stability of HX decreases down the group."))),
 PART("(b)", P(A(chem("H2X(aq)") + " ⟶ 2H" + sup("+") + "(aq) + X" + sup("2" + M) + "(aq)")),
      P(A("[H" + sup("+") + "] = 2(0.0280) = 0.0560 " + MDM)),
      P(A("pH = " + M + "log" + sub("10") + "(0.0560) = 1.25"))),
 PART("(c)", P(A("H" + sup("+") + " comes from the auto–ionisation of water at 298K as well as dissociation of H" + CL + ". When the amount of H" + CL +
                 " is small, H" + sup("+") + " from water is not negligible and must be included.")),
      P(A("[H" + sup("+") + "] from dissociation of water and H" + CL + " = 1.00 " + TIMES + " 10" + sup(M + "7") + " + 1.00 " + TIMES + " 10" + sup(M + "7") +
          " = 2.00 " + TIMES + " 10" + sup(M + "7") + " " + MDM)),
      P(A("pH = " + M + "log" + sub("10") + "(2.00 " + TIMES + " 10" + sup(M + "7") + ") = 6.69"))),
 PART("(d)(i)", P(A("The auto-ionisation of water is an endothermic reaction.")),
      P(A("H" + sub(2) + "O(l)" + EQ + "H" + sup("+") + "(aq) + OH" + sup(M) + "(aq)")),
      P(A("As temperature increases, the position of equilibrium shifts to the right to favour the endothermic reaction by absorbing the excess heat and "
          "counteract the increase in temperature.")),
      P(A("This increases the concentrations of both H" + sup("+") + " and OH" + sup(M) + ", leading to a higher value of ionic product of water, " + Kw + "."))),
 PART("(d)(ii)", P(A("Since H" + sub(2) + "O(l)" + EQ + "H" + sup("+") + "(aq) + OH" + sup(M) + "(aq),")),
      P(A("[H" + sup("+") + "] = [OH" + sup(M) + "]")),
      P(A("[H" + sup("+") + "][OH" + sup(M) + "] = 2.93 " + TIMES + " 10" + sup(M + "15"))),
      P(A("[H" + sup("+") + "]" + sup("2") + " = 2.93 " + TIMES + " 10" + sup(M + "15"))),
      P(A("[H" + sup("+") + "] = " + '<span class="sqrt"><span class="rad">2.93 ' + TIMES + ' 10' + sup(M + "15") + '</span></span>' + " = 5.41 " + TIMES + " 10" + sup(M + "8") + " " + MDM)),
      P(A("pH = " + M + "log" + sub("10") + "(5.41 " + TIMES + " 10" + sup(M + "8") + ") = 7.27"))),
 PART("(e)(i)", P(A(chem("CN^-^(aq)") + " + " + H2O + "(l)" + EQ + "HCN(aq) + OH" + sup(M) + "(aq)")),
      NOTE("Note: For ionic equation, spectator ion like K" + sup("+") + " should not be included.")),
 PART("(e)(ii)", P(A(chem("CN^-^(aq)") + " + " + H2O + "(l)" + EQ + "HCN(aq) + OH" + sup(M) + "(aq)")),
      P(A("pOH = 14 " + M + " 10.7 = 3.3")),
      P(A(Kb + " = " + frac("[HCN][OH" + sup(M) + "]", "[CN" + sup(M) + "]"))),
      P(A("2.04 " + TIMES + " 10" + sup(M + "5") + " = " + frac("[10" + sup(M + "3.3") + "][10" + sup(M + "3.3") + "]", "[CN" + sup(M) + "]"))),
      P(A("[CN" + sup(M) + "] = " + frac("[10" + sup(M + "3.3") + "][10" + sup(M + "3.3") + "]", "[2.04 " + TIMES + " 10" + sup(M + "5") + "]") + " = 0.01231 " + MDM)),
      P(A("Amount of CN" + sup(M) + " = " + frac("50.0", "1000") + " " + TIMES + " 0.01231 = 6.157 " + TIMES + " 10" + sup(M + "4") + " mol")),
      P(A("Mass of KCN = (39.1 + 12.0 + 14.0) " + TIMES + " 6.157 " + TIMES + " 10" + sup(M + "4") + " = 0.0401 g = 40.1 mg"))),
 PART("(f)(i)", IMG(5, "fi")),
 PART("(f)(ii)", P(A("5 chiral C atoms")), IMG(5, "fii")),
 PART("(g)(i)", IMG(5, "gi")),
 PART("(g)(ii)", P(A("step 1: Reagents and conditions: limited " + chem("CH3Cl") + ", anhydrous " + chem("AlCl3") + " catalyst")),
      P(A("step 2: Reagents and conditions: " + chem("KMnO4(aq)") + ", " + chem("H2SO4(aq)") + ", heat")),
      P(A("step 3: Reagents and conditions: " + chem("PCl5")))),
]

# ------------------------------------------------------------------ rulings (user, 2026-11-02/03)
RULED_FIXES = [   # (qn, old, new, expected count) -- typo / grammar fixes approved by the user ("fix typos/grammar errors")
    (1, "equilvalence", "equivalence", 1),
    (1, "is non–polar molecule", "is a non–polar molecule", 1),
    (3, "from its isolated gaseous ions from an infinite distance apart", "from its isolated gaseous ions that are an infinite distance apart", 1),
    (3, "</b> undergoes <u>acid-base", "</b> undergo <u>acid-base", 1),
    (3, "(loss in 2 H atoms).The di–substitution are at", "(loss in 2 H atoms). The di–substitution is at", 1),
    (4, "Mechanisim", "Mechanism", 1),
    (4, "due to the presence of π bond", "due to the presence of a π bond", 1),
]
RULED_FIXES += [
    (4, "molecules is the strongest and requires", "molecules are the strongest and require", 1),
    (4, "id–id interactions requires the least energy", "id–id interactions require the least energy", 1),
    (4, "interactions is comparable for both", "interactions are comparable for both", 1),
    (5, "Reddish–brown fumes of " + chem("Br2") + " is observed", "Reddish–brown fumes of " + chem("Br2") + " are observed", 1),
    # user 2026-11-03: "The decomposition of O6 (into O2) is exothermic." (3(c)(ii))
    (3, "the decomposition of " + chem("O6") + " into " + O2 + " is exothermic", "the decomposition of " + chem("O6") + " (into " + O2 + ") is exothermic", 1),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    for q, old, new, n in RULED_FIXES:
        if q == qn:
            assert h.count(old) == n, (qn, old, h.count(old)); h = h.replace(old, new)
    assert not re.search(r"\[\d+\]", h), (qn, re.findall(r".{20}\[\d+\].{10}", h))   # a leaked mark badge like [2]
    out[str(qn)] = h

# 3(e) reads "to give B, C12H12Br4O2" in the school's text; the compound is D (user ruling 2026-11-02)
_old = "to give " + b("B") + ", " + chem("C12H12Br4O2")
assert out["3"].count(_old) == 1
out["3"] = out["3"].replace(_old, "to give " + b("D") + ", " + chem("C12H12Br4O2"))

# labels = the question parts that carry a mark badge (answerable parts)
qs = {r["question_number"]: r for r in json.loads((QDIR / "questions.json").read_text())}
for qn in sorted(W):
    want = []
    for m in re.finditer(r'<span class="pl">([^<]*)</span>(.*?)</div>(?=\n<div class="qpart">|$)', qs[qn]["content_html"], re.S):
        if 'class="mk"' in m.group(2): want.append(m.group(1))
    have = re.findall(r'<span class="lab">([^<]*)</span>', out[str(qn)])
    assert want == have, (qn, want, have)

assets, seen = [], {}
for qn, slot in ASSETS:
    seen[qn] = seen.get(qn, 0) + 1
    assets.append({"question": qn, "slot": "ans-" + slot, "path": "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR), "offset": seen[qn]})
(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "worked solutions,", sum(h.count('class="lab"') for h in out.values()), "parts,", len(assets), "answer assets")
for a in assets: print("  Q%d %-8s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))

# ------------------------------------------------------------------ verification against the school's docx text
if DOCX:
    import zipfile
    from lxml import etree
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = etree.fromstring(zipfile.ZipFile(DOCX).read("word/document.xml"))
    def norm(s):
        import unicodedata
        s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s))      # CO₂ -> CO2, H⁻ -> H-
        s = s.replace("&nbsp;", " ").replace("&gt;", ">").replace("–", "-").replace("−", "-").replace("’", "'").replace("‘", "'")
        return re.sub(r"[^A-Za-z0-9]", "", s).lower()
    src = norm(" ".join("".join(p.itertext()) for p in root.iter("{%s}p" % ns["w"])))
    miss = []
    for qn, h in out.items():
        for m in re.finditer(r'<span class="ans">(.*?)</span>', h, re.S):
            t = norm(m.group(1))
            if len(t) > 12 and t not in src: miss.append((qn, re.sub(r"<[^>]+>", "", m.group(1))[:90]))
    print("verification: %d answer run(s) not found verbatim in the docx text (expect the ruled fixes, OMML maths)" % len(miss))
    for q, t in miss: print("   Q%s: %s" % (q, t))
