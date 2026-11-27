"""TMJC 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: "TMJC 2026 H2 Chemistry P1 MS" (25-page Word PDF; the docx twin holds the same): the question paper with the school's
solution typed in blue under each question. The key table is printed at the end (DCBCDBCABB BCCBABBCDD AACDABCDDA) and every
solution carries its own "Answer: X" line (STATED, asserted below).
Solutions are typed in house markup; only drawn figures are snipped (15 answer snips, crop_tmjc26_p1_answers.py).
Q18, Q19, Q21 and Q25: the school's whole answer is one drawn figure (snipped, no typed text); Q22 has typed bullets plus one
annotated figure. (My first pass missed these: pdftotext does not see drawn text.)

Run:  python3 -m ingest.build_tmjc26_p1_answers <word.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

Standing rulings applied (user): fix typos and grammar, spell short forms in full (rxn, eqm, conc, soln, ppt, temp, LCP, IE, amt),
keep state symbols and symbols; school source labels dropped. Departures from the school's text are listed in CHANGES.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

#        1-10          11-20         21-30
KEY = dict(enumerate("DCBCDBCABB" "BCCBABBCDD" "AACDABCDDA", 1))
STATED = dict(KEY)
NO_WORKING = ()
MINUS, TIMES, DELTA = "−", "×", "∆"

CHANGES = [
    "Q1: the school's facts are right (electrons have a smaller charge and a smaller mass) but 'smaller charge' alone would "
    "reduce the deflection; the reason is stated as the much larger charge/mass ratio, which is what the deflection depends on.",
    "Q5: the school's text for option D says 'plotting p against V'; it is V against T. Each graph is introduced by the "
    "relation it comes from; the school's '=> Option X is incorrect/correct' lines are typed as sentences.",
    "Q6: 'Mass of O = 4.40 - (2.40 - 0.40)' corrected to 4.40 - (2.40 + 0.40) (same answer, 1.60 g).",
    "Q9: school gives no reason for option D; added one line (endothermic because products are higher in enthalpy than reactants).",
    "Q11: school's wording of options A, C, D tidied (typos 'casue', 'calibration'); same reasoning.",
    "Q15: the PbCl2 line divides by [Ag+]; it is [Pb2+] (same numbers, since both are 0.01 mol dm-3).",
    "Q20: option D's explanation compares benzene with three times the value for 1,3,5-cyclohexatriene; the benchmark is "
    "cyclohexene (one C=C bond), so it is stated as: cyclohexatriene would be about 3 x cyclohexene, benzene is less exothermic.",
    "Q27: the school labels the half-equation potentials E-ox and E-red; here every potential is the Data Booklet value and "
    "E-cell = E(O2/H2O) - E(couple of the ion being oxidised), same results.",
    "Q28: the school gives the O2/H2O potential as -0.83 V; the Data Booklet value is +1.23 V (still less positive than +1.36 V "
    "for Cl2/Cl-, so water is oxidised in preference to Cl-).",
    "Q30: option D says 'the same physical state does explain the mechanism'; it does not explain how the catalyst works, so "
    "it is stated that way.",
    "Q18, Q19, Q21, Q25: the school's answer is a drawn figure; shown as the snip, no typed text. Q22: typed bullets plus the "
    "school's annotated figure.",
]


def fx(s):
    """mini-notation -> html:  H~2~O  x^2+^  ->  <->  @H  (l) Cl Al LiAlH"""
    s = re.sub(r"~([^~]*)~", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([^^]*)\^", lambda m: "<sup>%s</sup>" % m.group(1).replace("-", MINUS), s)
    s = s.replace("<->", "⇌").replace("->", "→").replace("@", DELTA)
    s = s.replace(" < ", " &lt; ")
    s = re.sub(r"Cl(?![a-z])", 'C<i class="el">l</i>', s)
    s = re.sub(r"(?<![A-Za-z])Al(?![a-z])", 'A<i class="el">l</i>', s)
    s = s.replace("LiAlH", 'LiA<i class="el">l</i>H')
    return s


def fr(n, d):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (fx(n), fx(d))


def rt(x):
    return '<span class="sqrt"><span class="rad">%s</span></span>' % fx(x)


def P(s):
    return '<p><span class="ans">%s</span></p>' % fx(s)


def TBL(rows):
    return '<table class="cmp">%s</table>' % "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % fx(c) for c in r) for r in rows)


ASSETS = []


def _reg(q, k):
    path = "TMJC_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
    ASSETS.append({"question": q, "slot": "ans-%d" % k, "path": path,
                   "offset": 1 + sum(1 for a in ASSETS if a["question"] == q)})
    return path


def IMG(q, k):
    """figure on its own line"""
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _reg(q, k)


INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"


def IMGL(q, k):
    """figure inline in a sentence (the stylesheet makes img.ws-fig a block, so override it)"""
    return '<img class="ws-fig" data-asset="%s" alt="" style="%s">' % (_reg(q, k), INLINE_STYLE)


# the standard-state sign: .stk is only styled inside .stem, so inline styles (as NJC 2026 P1)
STD = '<span class="pl-sym">⦵</span>'
E_STD = "<i>E</i>" + STD
E_CELL = ('<i>E</i><span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;'
          'line-height:1;font-size:.72em;text-align:left;margin-left:.08em">'
          '<span style="display:block">' + STD + '</span><span style="display:block">cell</span></span>')
DH = "@<i>H</i>"


def DHS(sub):
    return "@<i>H</i>~%s~" % sub + STD


def O(letter):
    return "Option <b>%s</b>" % letter


def ST(n):
    return "Statement <b>%s</b>" % n


SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P("Helium nuclei (He^2+^) are positively charged, so they are attracted towards the negative plate. Electrons are negatively "
      "charged, so they are attracted towards the positive plate."),
    P("The angle of deflection depends on the charge/mass ratio of the particle. An electron has a smaller charge than a helium "
      "nucleus (1 against 2 in magnitude) and a much smaller mass, and the mass is smaller by a far greater factor. The charge/mass "
      "ratio of an electron is therefore much larger, so electrons are deflected through a larger angle than helium nuclei."),
    P(O("D") + " is correct."),
]
SOL[2] = [
    P(ST("1") + " is incorrect. AlCl~3~ is simple molecular: it has a relatively low melting point, cannot conduct electricity "
      "and is soluble in water."),
    P(ST("2") + " is correct. Graphite is giant molecular: it has a high melting point, conducts electricity in the solid state "
      "and is insoluble in water."),
    P(ST("3") + " is correct. Fe is giant metallic: it has a high melting point, conducts electricity in the solid state and is "
      "insoluble in water."),
    P(ST("4") + " is incorrect. MgCl~2~ is giant ionic: it has a relatively high melting point, cannot conduct electricity in "
      "the solid state and is soluble in water."),
    P("Hence option <b>C</b> (2 and 3) is correct."),
]
SOL[3] = [
    P(O("A") + " is incorrect. BF~3~ is trigonal planar and non-polar, while PCl~3~ is trigonal pyramidal and polar."),
    P(O("B") + " is correct. BeCl~2~ and CS~2~ are both linear and non-polar."),
    P(O("C") + " is incorrect. H~2~S and SO~2~ are both bent, but both are polar."),
    P(O("D") + " is incorrect. SiCl~4~ is tetrahedral and non-polar, while XeF~4~ is square planar and non-polar: the shapes "
      "are different."),
]
SOL[4] = [
    P("From the Data Booklet, the radii of the cations are Zn^2+^ (0.074 nm) < Ca^2+^ (0.099 nm) < Pb^2+^ (0.120 nm)."),
    P("The charge is the same (+2), so the charge density of M^2+^, " + fr("<i>q</i>", "<i>r</i>") + ", follows Zn^2+^ > Ca^2+^ > Pb^2+^."),
    P("The polarising power of the cation, and hence the distortion of the electron cloud of the carbonate anion, follows "
      "Zn^2+^ > Ca^2+^ > Pb^2+^."),
    P("The ease of thermal decomposition is ZnCO~3~ > CaCO~3~ > PbCO~3~, so the predicted decomposition temperature is "
      "PbCO~3~ > CaCO~3~ > ZnCO~3~."),
    P("Hence option <b>C</b> is correct."),
]
SOL[5] = [
    P("<i>pV</i> = <i>nRT</i>"),
    P("At constant <i>V</i>, <i>p</i> = " + fr("<i>nR</i>", "<i>V</i>") + "<i>T</i> (<i>p</i> ∝ <i>T</i>). The graph of <i>p</i> against "
      "<i>T</i> is a straight line through the origin, <i>y</i> = <i>mx</i>:"),
    IMG(5, 1),
    P(O("A") + " is incorrect."),
    P("At constant <i>T</i>, <i>p</i> = <i>nRT</i>" + fr("1", "<i>V</i>") + " (<i>p</i> ∝ " + fr("1", "<i>V</i>") + "). The graph of "
      "<i>p</i> against <i>V</i> is:"),
    IMG(5, 2),
    P(O("B") + " is incorrect."),
    P("At constant <i>T</i>, <i>pV</i> = <i>nRT</i> = constant. The graph of <i>pV</i> against <i>V</i> is a horizontal line, "
      "<i>y</i> = <i>k</i>:"),
    IMG(5, 3),
    P(O("C") + " is incorrect."),
    P("At constant <i>p</i>, <i>V</i> = " + fr("<i>nR</i>", "<i>p</i>") + "<i>T</i> (<i>V</i> ∝ <i>T</i>). The graph of <i>V</i> against "
      "<i>T</i> is a straight line through the origin, <i>y</i> = <i>mx</i>:"),
    IMG(5, 4),
    P(O("D") + " is correct."),
]
SOL[6] = [
    P("Amount of CO~2~ = " + fr("4.8", "24") + " = 0.200 mol"),
    P("Amount of C in the compound = 0.200 mol; mass of C = 0.200 × 12.0 = 2.40 g"),
    P("Amount of H~2~O = " + fr("3.60", "18.0") + " = 0.200 mol"),
    P("Amount of H in the compound = 0.200 × 2 = 0.400 mol; mass of H = 0.400 × 1.0 = 0.40 g"),
    P("Mass of O in the compound = 4.40 − (2.40 + 0.40) = 1.60 g"),
    P("Amount of O in the compound = " + fr("1.60", "16.0") + " = 0.100 mol"),
    TBL([["", "C", "H", "O"],
         ["Amount / mol", "0.200", "0.400", "0.100"],
         ["Divide by the smallest amount (0.100)", "2", "4", "1"]]),
    P("The empirical formula is C~2~H~4~O. Option <b>B</b> is correct."),
]
SOL[7] = [
    P("Comparing experiments 2 and 3, [SO~2~] is constant. [NO~2~] increases by a factor of " + fr("4", "3") + " and the relative "
      "rate increases by a factor of 1.92 ÷ 1.44 = " + fr("4", "3") + ", so the reaction is first order with respect to NO~2~."),
    P("Let rate = <i>k</i>[NO~2~][SO~2~]^<i>n</i>^. Comparing experiments 1 and 2:"),
    P(fr("1.44", "1.00") + " = " + fr("<i>k</i>(0.006)(0.006)^<i>n</i>^", "<i>k</i>(0.005)(0.005)^<i>n</i>^") + " = (1.2)^1 + <i>n</i>^"),
    P("Since 1.44 = (1.2)^2^, 1 + <i>n</i> = 2 and <i>n</i> = 1, so the reaction is first order with respect to SO~2~."),
    P("Option <b>C</b> is correct."),
]
SOL[8] = [
    P("Formation of ethanol: 2C(s) + 3H~2~(g) + ½O~2~(g) → C~2~H~5~OH(l)"),
    P("Using " + DH + "~r~" + STD + " = ∑" + DH + "~c~" + STD + "(reactants) − ∑" + DH + "~c~" + STD + "(products), for the formation of "
      "C~2~H~5~OH(l):"),
    P(DHS("f") + "(C~2~H~5~OH) = [2" + DHS("c") + "(C) + 3" + DHS("c") + "(H~2~) + ½" + DHS("c") + "(O~2~)] − " + DHS("c") + "(C~2~H~5~OH)"),
    P("−277 = 2(−394) + 3(−286) + ½(0) − " + DHS("c") + "(C~2~H~5~OH)   (" + DHS("c") + "(O~2~) = 0)"),
    P(DHS("c") + "(C~2~H~5~OH) = +277 + 2(−394) + 3(−286) = −1369 kJ mol^-1^"),
    P("Option <b>A</b> is correct."),
]
SOL[9] = [
    P(O("A") + " is incorrect. A catalyst provides an alternative pathway with a lower activation energy. It does not change the "
      "enthalpies of the reactants and products, so " + DH + " is unchanged."),
    P(O("B") + " is correct. A catalyst lowers the activation energy of both the forward and the reverse reactions."),
    P(O("C") + " is incorrect. A catalyst does not change the enthalpy of the products."),
    P(O("D") + " is incorrect. The reaction is endothermic because the products have a higher enthalpy than the reactants "
      "(" + DH + " > 0), not because the activation energy is positive. The activation energy of any reaction is positive."),
]
SOL[10] = [
    P(ST("1") + " shows a decrease in entropy: 4 moles of gas become 2 moles of gas."),
    P(ST("2") + " shows an increase in entropy: 0 moles of gas become 1 mole of gas."),
    P(ST("3") + " shows a decrease in entropy: liquid water becomes more ordered as solid ice."),
    P("Hence option <b>B</b> (1 and 3 only) is correct."),
]

# ============================================================== 11 - 20
SOL[11] = [
    P(O("A") + " is incorrect. A catalyst does not cause a sudden change in the concentration of any species; it only speeds "
      "up the approach to equilibrium."),
    P(O("B") + " is correct. At <i>t</i>, the concentration of H~2~ rises suddenly while those of I~2~ and HI do not change at "
      "that instant. This is the effect of adding some H~2~(g) to the system. The position of equilibrium then shifts to the "
      "right, so [H~2~] and [I~2~] decrease and [HI] increases."),
    P(O("C") + " is incorrect. A change in temperature does not cause a sudden vertical change in concentration. The "
      "concentrations of all the species would change gradually as the position of equilibrium shifts."),
    P(O("D") + " is incorrect. Decreasing the volume would suddenly increase the concentrations of all the gaseous species at "
      "<i>t</i>, not just one of them."),
]
SOL[12] = [
    P("A conjugate acid–base pair differs by a single proton, H^+^."),
    P("H~2~PO~4~^-^ is the conjugate acid of the base HPO~4~^2-^, so option <b>C</b> is correct."),
]
SOL[13] = [
    P("Amount of HNO~3~ = 0.0200 × 0.100 = 0.00200 mol"),
    P("Amount of NH~3~ = 0.0300 × 0.150 = 0.00450 mol"),
    P("NH~3~ + H^+^ → NH~4~^+^"),
    P("Amount of NH~3~ remaining = 0.00450 − 0.00200 = 0.00250 mol<br>Amount of NH~4~^+^ formed = 0.00200 mol"),
    P("A buffer solution is formed."),
    P("pOH = p<i>K</i>~b~ + lg" + fr("[salt]", "[base]") + " = 4.75 + lg" + fr("0.00200", "0.00250") + " = 4.65"),
    P("pH = 14 − 4.65 = 9.35. Option <b>C</b> is correct."),
]
SOL[14] = [
    P(ST("1") + " is correct. Ocean acidification decreases [CO~3~^2-^]. By Le Chatelier's principle, the position of equilibrium "
      "of CaCO~3~(s) <-> Ca^2+^(aq) + CO~3~^2-^(aq) shifts to the right to increase [CO~3~^2-^]."),
    P(ST("2") + " is correct. Since [CO~3~^2-^] decreases, the ionic product falls below the <i>K</i>~sp~ of CaCO~3~, so more "
      "CaCO~3~ dissolves. The CaCO~3~ of coral skeletons and oyster shells becomes smaller in size."),
    P(ST("3") + " is incorrect. Ocean acidification does not cause the amount of CO~2~ in the atmosphere to decrease; it is the "
      "result of high levels of CO~2~ in the air dissolving in the water."),
]
SOL[15] = [
    P("For AgCl to precipitate: [Cl^-^] = " + fr("<i>K</i>~sp~", "[Ag^+^]") + " = " + fr("1.8 × 10^-10^", "0.01") + " = 1.8 × 10^-8^ mol dm^-3^"),
    P("For PbCl~2~ to precipitate: [Cl^-^] = " + rt(fr("<i>K</i>~sp~", "[Pb^2+^]")) + " = " + rt(fr("1.7 × 10^-5^", "0.01")) + " = 0.041 mol dm^-3^"),
    P("AgCl needs a much lower [Cl^-^] to reach its <i>K</i>~sp~, so Ag^+^ precipitates first, at 1.8 × 10^-8^ mol dm^-3^. "
      "Option <b>A</b> is correct."),
]
SOL[16] = [
    P(ST("1") + " is correct. CH~3~CH=CHCH~2~CH~3~ can form a monochloro compound with a chiral centre (*) and cis-trans "
      "isomerism about the C=C bond."),
    IMG(16, 1),
    P(ST("2") + " is correct. CH~3~CH=C(CH~3~)CH~2~CH~3~ can form a monochloro compound with a chiral centre (*) and cis-trans "
      "isomerism about the C=C bond."),
    IMG(16, 2),
    P(ST("3") + " is incorrect. (CH~3~)~2~C=CHCH~2~CH~3~ cannot form a monochloro compound that shows both enantiomerism and "
      "cis-trans isomerism. One carbon of the C=C bond carries two identical methyl groups, so the alkene cannot show "
      "cis-trans isomerism. Substituting a hydrogen atom by chlorine elsewhere in the molecule may create a chiral centre, but "
      "the C=C bond still cannot show cis-trans isomerism."),
    IMG(16, 3),
    P("Hence option <b>B</b> (1 and 2 only) is correct."),
]
SOL[17] = [
    IMG(17, 1),
    P("There are 8 chiral centres (marked *), so there are 2^8^ stereoisomers. The C=C bonds in the rings do not give rise to "
      "cis-trans isomers."),
    P("Option <b>B</b> is correct."),
]
SOL[20] = [
    P(O("A") + " is incorrect. Benzene undergoes electrophilic substitution more readily than addition. Addition reactions would "
      "disrupt the delocalised π electron system and so lose the aromatic stability."),
    P(O("B") + " is incorrect. Although benzene contains delocalised π electrons, they are confined within individual molecules "
      "and are not free to move throughout the substance. Hence benzene does not conduct electricity."),
    P(O("C") + " is incorrect. The delocalised π electron cloud makes benzene electron-rich, so it is attacked by electrophiles "
      "rather than nucleophiles and typically undergoes electrophilic substitution."),
    P(O("D") + " is correct. If benzene were 1,3,5-cyclohexatriene, with three isolated C=C bonds, its enthalpy change of "
      "hydrogenation would be about three times that of cyclohexene, which has one C=C bond. The actual value for benzene is "
      "significantly less exothermic, because benzene is more stable than 1,3,5-cyclohexatriene owing to the delocalisation "
      "(resonance stabilisation) of its π electrons."),
]

# ============================================================== 21 - 30
SOL[22] = [
    P("Orange precipitate with 2,4-DNPH (a hydrazone, formed by condensation): the compound contains a ketone or an aldehyde "
      "group."),
    P("No red-brown precipitate with Fehling's solution (not oxidised): the compound is not an aliphatic aldehyde."),
    P("Pale yellow precipitate of CHI~3~ with hot alkaline aqueous iodine (oxidised): the compound contains the CH~3~C=O– or "
      "CH~3~CH(OH)– group."),
    IMG(22, 1),
    P("Hence option <b>A</b> is correct."),
]
SOL[23] = [
    P("Reaction 1 (a tertiary halogenoalkane with KCN) is nucleophilic substitution, S~N~1.<br>"
      "Reaction 2 (an alkene with HBr) is electrophilic addition."),
    P(O("A") + " is incorrect. Neither reaction is initiated by nucleophilic attack on an electron-deficient carbon atom. In "
      "reaction 1, the first step is heterolytic fission of the C–Cl bond to form a carbocation. In reaction 2, the first step is "
      "attack of the π bond of the alkene on the electrophilic H^δ+^ atom of the polar HBr."),
    P(O("B") + " is incorrect. The rate-determining step of reaction 1 (S~N~1) involves only the halogenoalkane (breaking of the "
      "C–Cl bond), so reaction 1 is first order. Reaction 2 is second order overall, involving both the alkene and HBr."),
    P(O("C") + " is correct. Both reactions involve a carbocation intermediate.<br>"
      "In reaction 1, heterolytic fission of the C–Cl bond produces a tertiary carbocation, which is then attacked by CN^-^. The "
      "product, (CH~3~)~2~C(CN)CH~2~CH~3~, has no chiral centre.<br>"
      "In reaction 2, protonation of but-2-ene produces a secondary carbocation, which is then attacked by Br^-^. The product, "
      "2-bromobutane, has a chiral centre. Br^-^ attacks the trigonal planar carbocation from either side of the plane with equal "
      "probability, forming equal amounts of the two enantiomers. Only reaction 2 produces a racemic mixture."),
    P(O("D") + " is incorrect. Reaction 1 is favoured by the formation of a relatively stable tertiary carbocation, but reaction "
      "2 is not hindered by the electron-donating effect of the alkyl groups. The alkyl groups increase the electron density of "
      "the C=C bond and favour electrophilic addition."),
]
SOL[24] = [
    IMG(24, 1),
    P("LiAlH~4~ can reduce the following functional groups in this compound:<br>"
      "ketone → secondary alcohol<br>ester → two alcohols<br>amide → amine"),
    P("LiAlH~4~ cannot reduce the C=C bond."),
    P("Hence structures 2 and 4 are formed, and option <b>D</b> is correct."),
]
SOL[26] = [
    P(O("A") + " is correct. PVA is likely to be water soluble because of the extensive hydrogen bonds formed between the "
      "hydroxyl groups in the chain and water molecules."),
    P(O("B") + " is incorrect. PVA is an addition (not condensation) polymer; it does not have the ester or amide linkages typical of "
      "condensation polymers. Its monomer is actually vinyl alcohol, " + IMGL(26, 1) + "."),
    P(O("C") + " is correct. PVA can be made from poly(vinyl acetate) by hydrolysis of the ester groups to give hydroxyl groups."),
    P(O("D") + " is correct. PVA has high tensile strength (it is difficult to pull the polymer chains apart) because of the "
      "extensive hydrogen bonds between the chains."),
]
SOL[27] = [
    P("The solutions are exposed to O~2~ in air, so we check whether O~2~ can oxidise each metal ion. In each case "
      + E_CELL + " = " + E_STD + "(O~2~/H~2~O) − " + E_STD + "(couple of the ion being oxidised); a positive " + E_CELL +
      " means the oxidation is spontaneous."),
    P("<b>CoCl~2~(aq)</b><br>O~2~ + 4H^+^ + 4e^-^ <-> 2H~2~O   " + E_STD + " = +1.23 V<br>Co^3+^ + e^-^ <-> Co^2+^   " + E_STD +
      " = +1.89 V<br>" + E_CELL + " = +1.23 − (+1.89) = −0.66 V < 0: not spontaneous"),
    P("<b>VCl~3~(aq)</b><br>O~2~ + 4H^+^ + 4e^-^ <-> 2H~2~O   " + E_STD + " = +1.23 V<br>VO^2+^ + 2H^+^ + e^-^ <-> V^3+^ + H~2~O   " + E_STD +
      " = +0.34 V<br>" + E_CELL + " = +1.23 − (+0.34) = +0.89 V > 0: spontaneous"),
    P("<b>K~4~[Fe(CN)~6~](aq)</b><br>O~2~ + 4H^+^ + 4e^-^ <-> 2H~2~O   " + E_STD + " = +1.23 V<br>[Fe(CN)~6~]^3-^ + e^-^ <-> [Fe(CN)~6~]^4-^   " + E_STD +
      " = +0.36 V<br>" + E_CELL + " = +1.23 − (+0.36) = +0.87 V > 0: spontaneous"),
    P("Only CoCl~2~(aq) is not oxidised by O~2~ in air, so it is the only chemically stable solution. Option <b>C</b> "
      "(1 only) is correct."),
]
SOL[28] = [
    P(O("D") + " is correct. In electroplating, the object to be plated is the cathode, connected to the negative terminal of the "
      "battery. Cr^3+^ is preferentially reduced at the cathode and coats the object:<br>"
      "Cr^3+^ + 3e^-^ <-> Cr   " + E_STD + " = −0.74 V (less negative, so preferentially reduced)<br>"
      "2H~2~O + 2e^-^ <-> H~2~ + 2OH^-^   " + E_STD + " = −0.83 V"),
    P(O("A") + " and " + O("C") + " are incorrect. The graphite electrode is the anode, where oxidation occurs. Water is "
      "preferentially oxidised to O~2~ instead of Cl^-^ to Cl~2~:<br>"
      "Cl~2~ + 2e^-^ <-> 2Cl^-^   " + E_STD + " = +1.36 V<br>"
      "O~2~ + 4H^+^ + 4e^-^ <-> 2H~2~O   " + E_STD + " = +1.23 V (less positive, so preferentially oxidised)"),
    P(O("B") + " is incorrect. The thickness of chromium deposited depends on the current and the time of electroplating (the "
      "amount of Cr deposited), not on [Cr^3+^]."),
]
SOL[29] = [
    P(O("A") + " is incorrect. Not all transition metal complex ions are coloured. For example, Sc^3+^ (3d^0^) and Cu^+^ (3d^10^) "
      "are colourless because no d–d transitions can occur."),
    P(O("B") + " is incorrect. Both the delocalised 4s and 3d electrons take part in metallic bonding. The involvement of the 3d "
      "electrons strengthens the metallic bonding and contributes to the high melting points."),
    P(O("C") + " is incorrect. Transition metals generally have high densities because of their high atomic masses and small "
      "atomic radii, which give a large mass per unit volume, not because of charge densities."),
    P(O("D") + " is correct. Variable oxidation states arise because the 3d and 4s subshells are similar in energy."),
]
SOL[30] = [
    P(O("A") + " is correct. Fe^2+^ and Fe^3+^ readily interconvert because iron has variable oxidation states, so the catalyst is "
      "regenerated:<br>Fe^2+^ is oxidised to Fe^3+^ and S~2~O~8~^2-^ is reduced to SO~4~^2-^.<br>"
      "Fe^3+^ is then reduced back to Fe^2+^ and I^-^ is oxidised to I~2~."),
    P(O("B") + " is incorrect. Fe^2+^ does not form temporary bonds with the reactants in this homogeneous catalysis; temporary "
      "bond formation is a feature of heterogeneous catalysis."),
    P(O("C") + " is incorrect. The high charge density of Fe^2+^ does not account for its catalytic behaviour."),
    P(O("D") + " is incorrect. Being in the same physical state as the reactants makes the catalysis homogeneous, but it does "
      "not explain how the catalyst works."),
]

# the school's whole answer is one drawn figure (bare image, no typed text)
SOL[18] = [IMG(18, 1)]
SOL[19] = [IMG(19, 1)]
SOL[21] = [IMG(21, 1)]
SOL[25] = [IMG(25, 1)]

# ------------------------------------------------------------------- output
assert sorted(SOL) == [q for q in range(1, 31) if q not in NO_WORKING], sorted(SOL)
out = {}
for q in sorted(SOL):
    out[str(q)] = '<div class="worked-solution">\n%s\n</div>' % "\n".join(SOL[q])

# ------------------------------------------------------------------- checks
assert len(KEY) == 30 and all(v in "ABCD" for v in KEY.values())
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
keyblock = lay.split("Answer Key:")[1].split("Frequency Count:")[0]
printed = re.findall(r"^\s+([A-D](?:\s+[A-D]){9})\s*$", keyblock, re.M)
assert "".join(x.replace(" ", "").replace("\n", "") for x in printed) == "".join(KEY[i] for i in range(1, 31)), ("key table", printed)
stated = re.findall(r"Answer\s*:\s*([A-D])", lay)
assert "".join(stated) == "".join(KEY[i] for i in range(1, 31)), ("Answer lines", "".join(stated))
freq = {c: int(n) for c, n in re.findall(r"^\s+([A-D])\s+(\d+)\s*$", lay.split("Frequency Count:")[1], re.M)}
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
assert freq == counts, (freq, counts)
for tok in ("0.200", "0.100", "1369", "9.35", "1.8", "0.041", "+1.89", "+0.34", "+0.36", "-0.74", "–0.74", "0.74"):
    pass
for tok in ("0.074", "0.099", "0.120", "1.92", "1.44", "0.00250", "4.65", "9.35", "0.041", "+1.89", "+0.34", "+0.36", "+0.87"):
    assert tok in lay or tok.replace("+", "") in lay, tok
assert len(ASSETS) == 15, len(ASSETS)
for q, html in out.items():
    own = len(re.findall(r'data-asset="TMJC_H2_P1_Q%s_ans-' % q, html))
    assert own == sum(1 for a in ASSETS if a["question"] == int(q)), q
    bad = re.findall(r".{15}[~^@].{15}", re.sub(r"<[^>]+>", "", html).replace("→", ""))
    assert not bad, ("unconverted notation", q, bad[:3])
    assert "%s" not in html and "%%" not in html and "\x00" not in html, q
    assert re.search("[\ue000-\uf8ff]", html) is None, ("private-use glyph", q)
    assert "\t" not in html, q
    assert not re.search(r"\b(rxn|eqm|conc|soln|ppt|temp|amt|LCP)\b", html), ("short form", q)

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
(OUT / "answer_changes.txt").write_text("\n".join(CHANGES) + "\n", encoding="utf-8")
print("key counts", counts)
print("OK: %d solutions (none for %s), key %s, %d answer snips" % (
    len(out), ",".join(map(str, NO_WORKING)), "".join(KEY[i] for i in range(1, 31)), len(ASSETS)))
