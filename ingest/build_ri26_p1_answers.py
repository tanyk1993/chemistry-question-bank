"""RI 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: the school's "2026 H2 Chemistry RI Preliminary Exams Paper 1 - Suggested Solutions" (14-page PDF, docx twin):
a printed key table, then "Qn (Ans: X)" blocks.  Hand-typed here in house markup (div.worked-solution > p > span.ans,
.frac, table.cmp, img.ws-fig) and CHECKED against the PDF: the key table, the 30 block headings and the question
paper's own answer letters agree.  The docx is a flat table grid with floating figures and OLE equations, so the
text is typed (same approach as NYJC 2026 P1), not extracted.

Run:  python3 -m ingest.build_ri26_p1_answers <answers.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

Figures: the user snips 28 answer images (answer_assets.json); the four Q25 COMPOUND structures re-use the question-side
snips (RI_H2_P1_Q25_stem1-4_2026.png: resolveAssets() matches by filename over all of the question's assets).
Files: RI_H2_P1_Q<n>_ans-<k>_2026.png.

Editorial rulings go in TYPO_FIXES / SHORT_FORMS.  User rulings applied: Q16 pi count 8 -> 5 (structure has 5); Q26 opening reworded (*O ends up in the ester,
not "with CH3OH which left during hydrolysis"); Q7 B locant but-2-ene.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

KEY = dict(enumerate("CBDBBDBBBBCDABD" "CBDCCDBADBBCADA", 1))
MINUS, TIMES, DELTA = "−", "×", "∆"


def fx(s):
    """mini-notation -> html:  H~2~O  x^2+^  ->  <->  @H  (l) Cl Al"""
    s = re.sub(r"~([^~]*)~", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([^^]*)\^", lambda m: "<sup>%s</sup>" % m.group(1).replace("-", MINUS), s)
    s = s.replace("<->", "⇌").replace("->", "→").replace("@", DELTA)
    s = re.sub(r"Cl(?![a-z])", 'C<i class="el">l</i>', s)
    s = re.sub(r"(?<![A-Za-z])Al(?![a-z])", 'A<i class="el">l</i>', s)
    return s


def fr(n, d):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (fx(n), fx(d))


def P(s):
    return '<p><span class="ans">%s</span></p>' % fx(s)


def PC(s):
    return '<p class="c"><span class="ans">%s</span></p>' % fx(s)


def TBL(rows):
    return '<table class="cmp">%s</table>' % "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % fx(c) for c in r) for r in rows)


ASSETS = []


def _reg(q, k):
    path = "RI_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
    ASSETS.append({"question": q, "slot": "ans-%d" % k, "path": path,
                   "offset": 1 + sum(1 for a in ASSETS if a["question"] == q)})
    return path


def IMG(q, k):
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _reg(q, k)


def IMGI(q, k):
    """figure inside a table cell"""
    return '<img class="ws-fig" data-asset="%s" alt="">' % _reg(q, k)


def IMGQ(name):
    """re-use of a QUESTION-side snip (not an answer asset)"""
    return '<img class="ws-fig" data-asset="%s" alt="">' % name


STD = '<span class="pl-sym">⦵</span>'
E_STD = "<i>E</i>" + STD
DH = "@<i>H</i>" + STD
DS = "@<i>S</i>" + STD
DG = "@<i>G</i>" + STD
OK = "✓"


def opt(letter, ok=False):
    return "<b>%s%s</b>" % (letter, OK if ok else "")


SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P("Let <i>x</i> be the percentage abundance of ^12^C and (100 %s <i>x</i>) be the percentage abundance of ^13^C." % MINUS),
    P("<i>A</i>~r~ of C = " + fr("(<i>x</i>)(12) + (100 %s <i>x</i>)(13)" % MINUS, "100") + " = 12.2"),
    P("Percentage abundance of ^12^C = <i>x</i> = 80 %%<br>Percentage abundance of ^13^C = 100 %s <i>x</i> = 20 %%" % MINUS),
    P("Ratio of ^12^C to ^13^C is 4:1"),
]
SOL[2] = [
    TBL([["element", "<b>C</b>", "<b>N</b>"],
         ["mass in 3.3 g of carbon nitride / g",
          fr("4.4", "12.0 + (2)(16.0)") + " %s 12.0<br>= 1.2" % TIMES,
          fr("6.9", "14.0 + (2)(16.0)") + " %s 14.0<br>= 2.1" % TIMES],
         ["amount / mol", fr("1.2", "12.0") + " = 0.1", fr("2.1", "14.0") + " = 0.15"],
         ["molar ratio", "1", "1.5"],
         ["", "2", "3"]]),
]
SOL[3] = [
    TBL([["", "atom", "electronic configuration", "number of electrons in p orbitals"],
         [opt("A"), "Cl", "1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^5^", "11"],
         [opt("B"), "N", "1s^2^ 2s^2^ 2p^3^", "3"],
         [opt("C"), "P", "1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^3^", "9"],
         [opt("D", True), "F", "1s^2^ 2s^2^ 2p^5^", "5"]]),
]
SOL[4] = [
    TBL([[opt("A"), "Al^3+^: 1s^2^ 2s^2^ 2p^6^<br>S^2-^: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^6^<br><br>"
                    "Al^3+^ has a smaller ionic radius than S^2-^ as it has one less electron shell."],
         [opt("B", True), "Aluminium: giant metallic structure with strong metallic bonds between Al^3+^ and delocalised electrons."
                          "<br><br>Sulfur: simple molecular structure with weak intermolecular forces of attraction between S~8~ molecules."
                          "<br><br>More energy is required to overcome the stronger metallic bonds in aluminium, resulting in a higher "
                          "melting point."],
         [opt("C"), "Aluminium is less electronegative than sulfur as electronegativity increases across the Period."],
         [opt("D"), "Aluminium has a lower first ionisation energy than sulfur.<br><br>The 1^st^ ionisation energy of the elements "
                    "generally increases across a period. Note the irregularity from Group 2 to 13, and Group 15 to 16."]]),
]
SOL[5] = [
    P("A large jump in the 3^rd^ and 4^th^ ionisation energies is observed. Significantly more energy is required to remove the "
      "4^th^ electron as it is located in an inner electron shell."),
    P("Hence, there are 3 electrons in the valence shell. <b>J</b> is likely to be in Group 13. However <b>J</b> cannot be boron as "
      "it has only 5 electrons."),
]
SOL[6] = [
    TBL([[opt("A"), IMGI(6, 1), "bent"],
         [opt("B"), IMGI(6, 2), "T-shaped"],
         [opt("C"), IMGI(6, 3), "square planar"],
         [opt("D", True), IMGI(6, 4), "trigonal pyramidal"]]),
]
SOL[7] = [
    TBL([[opt("A"), "Incorrect. Both fluoroethane and ethanol have simple molecular structures with pd-pd interactions between "
                    "fluoroethane molecules and H-bonding between ethanol molecules. As their electron cloud sizes are the same, their "
                    "id-id interactions are similar. Since H-bonding is stronger than pd-pd interactions, fluoroethane has a lower "
                    "boiling point than ethanol."],
         [opt("B", True), "Correct. <i>Cis</i>-but-2-ene is slightly polar while <i>trans</i>-but-2-ene is non-polar. The permanent "
                          "dipole-permanent dipole (pd-pd) interactions and instantaneous dipole-induced dipole (id-id) interactions "
                          "between <i>cis</i>-but-2-ene molecules are stronger than the id-id interactions between "
                          "<i>trans</i>-but-2-ene molecules so that <i>cis</i>-but-2-ene has a higher boiling point than "
                          "<i>trans</i>-but-2-ene."],
         [opt("C"), "Incorrect. Aluminium chloride has a simple molecular structure while aluminium fluoride has a giant ionic "
                    "lattice structure. Less energy is needed to overcome weak intermolecular forces of attraction between aluminium "
                    "chloride molecules than strong ionic bonds between aluminium and fluoride ions in aluminium fluoride. Hence, "
                    "aluminium chloride has a lower boiling point than aluminium fluoride."],
         [opt("D"), "Incorrect. -OH and -COOH groups in 2-hydroxybenzoic acid are in close proximity resulting in intra-molecular H "
                    "bonding being formed. Hence, fewer sites are available to form inter-molecular H bonding, compared to "
                    "4-hydroxybenzoic acid. This results in 2-hydroxybenzoic acid having lower boiling point as less energy is needed "
                    "to overcome the weaker intermolecular forces of attraction between its molecules."]]),
]
SOL[8] = [
    P("From the <i>Data Booklet</i>,<br>"
      "MnO~4~^-^ + 8H^+^ + 5e^-^ <-> Mn^2+^ + 4H~2~O &emsp;&emsp;&emsp; " + E_STD + " = +1.52 V<br>"
      "Cl~2~ + 2e^-^ <-> 2Cl^-^ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; " + E_STD + " = +1.36 V<br>"
      "I~2~ + 2e^-^ <-> 2I^-^ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; " + E_STD + " = +0.54 V<br>"
      "S~4~O~6~^2-^ + 2e^-^ <-> 2S~2~O~3~^2-^ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; " + E_STD + " = +0.09 V"),
    TBL([["substances mixed", "I~2~ + S~2~O~3~^2-^", "I~2~ + Mn^2+^", "I~2~ + Cl^-^"],
         [E_STD + "~cell~", "0.54 %s 0.09 = +0.45 V" % MINUS, "0.54 %s 1.52 = %s0.98 V" % (MINUS, MINUS),
          "0.54 %s 1.36 = %s0.82 V" % (MINUS, MINUS)],
         ["spontaneity of reaction", "Spontaneous. Brown iodine is decolourised.",
          "Non-spontaneous. Mn^2+^ is not oxidised to purple MnO~4~^-^ and I~2~ is not reduced to I^-^.",
          "Non-spontaneous. Cl^-^ is not oxidised and I~2~ is not reduced to I^-^."],
         ["colour of resultant solution", "Colourless", "Brown (due to colour of unreacted iodine).",
          "Brown (due to colour of unreacted iodine)."]]),
    P("Only rows 1 and 3 are correct."),
]
SOL[9] = [
    P("In the given experiment in question:<br>2 mol of H~2~O is formed.<br>Let heat evolved = <i>q</i> kJ, and @<i>T</i> = <i>x</i> °C "
      "in a 100 cm^3^ solution."),
    P("For neutralisation, " + DH + "~neut~ = %s " % MINUS + fr("<i>q</i>", "amount of H~2~O") + ", <i>q</i> ∝ amount of H~2~O as "
      + DH + "~neut~ is constant for strong acid and strong base reaction."),
    P("As <i>q</i> = <i>mC</i>@<i>T</i>, @<i>T</i> = " + fr("<i>q</i>", "<i>mC</i>") + " = <i>x</i>, where <i>m</i> is the mass of "
      "the solution."),
    TBL([[opt("A"), "As NaOH is limiting, 1 mol H~2~O is formed.<br>Heat evolved is 0.5<i>q</i>, and is @<i>T</i> = "
                    + fr("0.5<i>q</i>", "0.5<i>mC</i>") + " = <i>x</i> for 50 cm^3^ solution."],
         [opt("B", True), "As Ca(OH)~2~ is limiting, 2 mol H~2~O is formed.<br>Heat evolved is <i>q</i>, and @<i>T</i> = "
                          + fr("<i>q</i>", "<i>mC</i>") + " = <i>x</i> for the same 100 cm^3^ solution."],
         [opt("C"), "As HCl is limiting, 2 mol H~2~O is formed.<br>Heat evolved is <i>q</i>, and is @<i>T</i> = "
                    + fr("<i>q</i>", "2<i>mC</i>") + " = 0.5<i>x</i> for 200 cm^3^ solution."],
         [opt("D"), "As NaOH is limiting, 4 mol H~2~O is formed.<br>Heat evolved is 2<i>q</i>, and is @<i>T</i> = "
                    + fr("2<i>q</i>", "2<i>mC</i>") + " = <i>x</i> for 200 cm^3^ solution."]]),
]
SOL[10] = [
    TBL([[opt("1", True), "Correct. " + DS + " &gt; 0 as there is an increase in the number of moles of gaseous particles."],
         [opt("2", True), "Correct. This reaction is endothermic. Vaporisation of water from liquid to gaseous state is endothermic as "
                          "energy is taken in to provide kinetic energy for water molecules to break free from these attractive forces "
                          "and move far apart into the air.<br><br>Changing H~2~O(g) to O~2~(g) and H~2~(g),<br>"
                          + DH + " = 2BE(O%sH) %s [0.5 BE(O=O) + BE(H%sH)]<br>&emsp;&emsp;= 2(460) %s [0.5(496) + 436]<br>"
                          "&emsp;&emsp;= +236 kJ mol^-1^" % (MINUS, MINUS, MINUS, MINUS)],
         [opt("3"), "Incorrect. Using " + DG + "~r~ = " + DH + " %s <i>T</i>" % MINUS + DS + "<br><br>" + DH + " &gt; 0 and "
                    "%s<i>T</i>@<i>S</i> = %s(+) &lt; 0.<br><br>At low temperature, " % (MINUS, MINUS) + DG + "~r~ &gt; 0 and reaction "
                    "is non-spontaneous.<br>At high temperature, " + DG + "~r~ &lt; 0 and reaction is spontaneous."]]),
]
# ============================================================== 11 - 20
SOL[11] = [
    P("As the decomposition of H~2~O~2~ is first order with respect to H~2~O~2~, rate = <i>k</i>[H~2~O~2~]"),
    TBL([[opt("A"), "Incorrect. Graph of [H~2~O~2~] against time should be a curve with constant half-life."],
         [opt("B"), "Incorrect. Graph of [H~2~O~2~] against rate should be a straight line that passes through the origin."],
         [opt("C", True), "Correct. Graph of rate against [H~2~O~2~] is a straight line that passes through the origin."],
         [opt("D"), "Incorrect. Graph of volume of O~2~ against time should be a positive slope curve with decreasing gradient, "
                    "plateauing when maximum volume of O~2~ (<i>V</i>~max~) has been reached. Graph should be showing “constant "
                    "half-life”, that is, constant <i>t</i> from <i>V</i> = 0 to <i>V</i> = 0.5<i>V</i>~max~, and 0.5<i>V</i>~max~ to "
                    "0.75<i>V</i>~max~."]]),
]
SOL[12] = [
    IMG(12, 1),
    TBL([[opt("1"), "Incorrect. The number of particles at E~1~ decreases at 350 K."],
         [opt("2", True), "Correct. The number of particles at energy higher than E~A~ increases at 350 K."],
         [opt("3"), "Incorrect. Increasing the temperature does not affect the activation energy of the reaction."]]),
]
SOL[13] = [
    P("As the yield is 20%%, the amount of NH~3~ formed is 0.20 %s 2 = 0.40 atm" % TIMES),
    TBL([["", "3H~2~(g)", "+", "N~2~(g)", "<->", "2NH~3~(g)"],
         ["Initial pressure / atm", "3", "", "1", "", "0"],
         ["Change in pressure / atm", "%s0.6" % MINUS, "", "%s0.2" % MINUS, "", "+0.4"],
         ["Equilibrium pressure / atm", "2.4", "", "0.8", "", "0.4"]]),
    PC("<i>K</i>~p~ = " + fr("<i>P</i>(NH~3~)^2^", "<i>P</i>(H~2~)^3^<i>P</i>(N~2~)") + " = " + fr("(0.4)^2^", "(2.4)^3^(0.8)")
       + " = 0.0145 atm^-2^"),
]
SOL[14] = [
    TBL([["<b>solution</b>", "<b>concentration</b>", "<b>pH</b>", "<b>[H^+^]</b>", "<b>[OH^-^]</b>", "<b>type</b>"],
         ["<b>I</b>", "1.0 %s 10^-4^" % TIMES, "4", "1.0 %s 10^-4^" % TIMES, MINUS, "strong acid"],
         ["<b>II</b>", "1.0 %s 10^-1^" % TIMES, "4", "1.0 %s 10^-4^" % TIMES, MINUS, "weak acid"],
         ["<b>III</b>", "1.0 %s 10^-4^" % TIMES, "10", MINUS, "1.0 %s 10^-4^" % TIMES, "strong base"],
         ["<b>IV</b>", "1.0 %s 10^-1^" % TIMES, "10", MINUS, "1.0 %s 10^-4^" % TIMES, "weak base"]]),
    P("We can deduce that <b>I</b> and <b>III</b> are strong acid and strong base respectively as their concentrations are the same "
      "as the corresponding H^+^/OH^-^ concentration in the table. For <b>II</b> and <b>IV</b>, as the concentrations of H^+^/OH^-^ are "
      "much lower than that of the reagents, they are weak acid and weak base respectively."),
    TBL([[opt("1"), "Incorrect. All 3 indicators can be used for strong acid-strong base titration."],
         [opt("2", True), "Correct. The pH change range of methyl red falls within the pH change range at equivalence point of a strong "
                          "acid-weak base titration (around pH 3 %s 6)." % MINUS],
         [opt("3"), "Incorrect. No indicators will work for weak acid-weak base titration as the end point is not distinct."]]),
]
SOL[15] = [
    TBL([[opt("A"), "Incorrect. The blue precipitate Cu(OH)~2~ is formed by a precipitation/acid-base reaction and not by ligand "
                    "exchange."],
         [opt("B"), "Incorrect. The dark blue solution contains [Cu(NH~3~)~4~]^2+^. The reaction is not a redox reaction as there is no "
                    "change in oxidation number."],
         [opt("C"), "Incorrect. High chloride concentration is needed to convert blue [Cu(H~2~O)~6~]^2+^ to yellow [CuCl~4~]^2-^. "
                    "Concentration of chloride ions in dilute HCl is not high enough for ligand exchange to take place so a yellow "
                    "solution is not formed."],
         [opt("D", True), "Correct. Addition of excess dilute H~2~SO~4~ to the dark blue solution causes Cu^2+^ to be formed. Cu^2+^ "
                          "reacts with iodide ions to form CuI (cream precipitate) and I~2~ (brown solution)."]]),
]
SOL[16] = [
    P("It has 9 sp^2^ hybridised C (6 on benzene, 3 on each doubly bonded C), 12 hydrogen atoms, 25 σ bonds and 5 π bonds."),
    IMG(16, 1),
]
SOL[17] = [
    IMG(17, 1),
    P("3 chiral carbons, number of enantiomers = 2^3^<br>1 set of cis-trans isomers = 2<br>Total stereoisomers = 2^3^ %s 2 = 16" % TIMES),
    P("Note: - the alkene with 2 %sCH~3~ groups cannot have cis-trans isomerism as they are the same<br>"
      "&emsp;&emsp;&emsp;- C atoms of the benzene ring are sp^2^ with only 3 other atoms attached, they are not chiral" % MINUS),
]
SOL[18] = [
    IMG(18, 1),
    P("The correct reagent for halogenation is PCl~5~."),
    P("Since the C atom with the hydroxyl group is electron deficient, it must be susceptible to nucleophilic attack, not "
      "electrophilic attack."),
]
SOL[19] = [
    IMG(19, 1),
    P("These are the possible radicals formed during propagation."),
    P("Hence possible termination steps can combine these 2 radicals to give the following possible outcomes:"),
    IMG(19, 2),
    P("Formed by combining R1 with R1, no corresponding option"),
    IMG(19, 3),
    P("Formed by combining R1 with R2, no corresponding option"),
    IMG(19, 4),
    P("Formed by combining R2 with R2, hence option C is correct."),
    P("Bonds that are newly formed are indicated in bold above."),
    P("Options A and B are incorrect, as they have 9 and 7 carbon atoms in total. New compound must have 2 %s 4 = 8 carbon atoms." % TIMES),
    P("Option D is incorrect as its starting radical would be straight-chain rather than branched."),
]
SOL[20] = [IMG(20, 1)]
# ============================================================== 21 - 30
SOL[21] = [
    IMG(21, 1),
    P("Options A, B and C do not direct the incoming groups to the correct positions and will not produce molecule <b>T</b>."),
]
SOL[22] = [
    P("If hydrolysis only takes place 100% by S~N~2:"),
    IMG(22, 1),
    P("product enantiomer shows inversion of configuration,<br>rotates plane-polarised light by <b>%s20°</b>, since it is the "
      "<b>mirror image</b> of enantiomer <b>W1</b>" % MINUS),
    P("If hydrolysis only takes place by 100% S~N~1, then the product will be a racemic mixture of <b>W1</b> and its <b>mirror image "
      "enantiomer</b> in equal proportions and will have a net rotation of plane-polarised light by 0°."),
    P("If hydrolysis takes place by both S~N~2 and S~N~1 with equal rates, the net rotation must be exactly halfway between %s20° and "
      "0°, that is %s10°.<br>Since the observed rotation is %s15°, S~N~2 must be faster than S~N~1." % (MINUS, MINUS, MINUS)),
    P("Option 1 is incorrect since a combination of S~N~2 and S~N~1 will not give second order kinetics.<br>"
      "Options 2 and 3 are correct."),
]
SOL[23] = [
    P("There are three chlorine-containing functional groups in compound <b>Y</b>."),
    IMG(23, 1),
    P("The acyl chloride is more easily hydrolysed than the chloroalkane. This is because of the more electron-deficient carboxyl "
      "carbon (as it is attached to 2 highly electronegative atoms) and less steric hindrance (as the carboxyl carbon is sp^2^ "
      "hybridised). The acyl chloride readily hydrolyses in the absence of heat at room temperature, while the chloroalkane requires "
      "the presence of heat for hydrolysis."),
    P("The chlorobenzene does not undergo hydrolysis under both conditions due to the partial double bond character in the C%sCl "
      "bond which strengthens the bond." % "–"),
    P("Under condition I, only the chloride from the acyl chloride will be released, that is, 1 mol of chloride.<br>"
      "Under condition II, the chlorides from both the acyl chloride and chloroalkane will be released, that is, 2 mol of chloride."),
]
SOL[24] = [
    P("Two factors determine the rate of nucleophilic addition reactions of carbonyls.<br>"
      "&emsp;1. Steric effects (presence of bulky groups which hinder the approach of nucleophile to carbonyl carbon)<br>"
      "&emsp;2. Electronic effects (electron-donating groups which reduce <b>OR</b> electron-withdrawing groups which increase the "
      "electron-deficiency of carbonyl carbon)"),
    TBL([[opt("A"), "Incorrect. The 2 bulky %sCH~3~ in propanone hinders the approach of a nucleophile to a greater extent than the 1 "
                    "bulky %sCH~3~ in ethanal. With one more electron-donating %sCH~3~ in propanone, the electron-deficiency of the "
                    "carbonyl carbon is reduced to a greater extent in propanone. Hence, propanone undergoes nucleophilic addition at a "
                    "<u>slower</u> rate." % (MINUS, MINUS, MINUS)],
         [opt("B"), "Incorrect. The electron-withdrawing %sOH group in HOCH~2~CHO increases the electron-deficiency of the carbonyl "
                    "carbon in HOCH~2~CHO compared to ethanal. Hence, ethanal undergoes nucleophilic addition at a <u>slower</u> rate "
                    "than HOCH~2~CHO." % MINUS],
         [opt("C"), "Incorrect. The rate-determining step of the nucleophilic addition involves one carbonyl compound and one KCN. "
                    "Hence, increasing the concentration of KCN increases the reaction rate."],
         [opt("D", True), "Correct. When heated with hot aqueous HCl, the %sCN group is converted to %sCOOH. The nitrogen is lost as "
                          "NH~4~^+^ and is no longer part of the organic compound." % (MINUS, MINUS)]]),
]
SOL[25] = [
    P("Reducing abilities of H~2~ / Ni and LiAlH~4~."),
    TBL([["", "H~2~ / Ni", "LiAlH~4~"],
         ["alkene", OK, "✗"], ["aldehyde", OK, OK], ["ketone", OK, OK], ["nitrile", OK, OK],
         ["carboxylic acid", "✗", OK], ["amide", "✗", OK]]),
    TBL([["", "reducing agent", "compound", "product"],
         ["<b>1</b>", "H~2~", IMGQ("RI_H2_P1_Q25_stem1_2026.png") + "<br>Functional groups present:<br>alkene, amide, aldehyde",
          IMGI(25, 1)],
         ["<b>2</b>", "H~2~", IMGQ("RI_H2_P1_Q25_stem2_2026.png") + "<br>Functional groups present:<br>amine, aldehyde, alkene",
          IMGI(25, 2)],
         ["<b>3</b>", "LiAlH~4~", IMGQ("RI_H2_P1_Q25_stem3_2026.png") + "<br>Functional groups present:<br>alkene, amide, aldehyde",
          IMGI(25, 3)],
         ["<b>4</b>", "LiAlH~4~", IMGQ("RI_H2_P1_Q25_stem4_2026.png") + "<br>Functional groups present:<br>amide, 1° alcohol",
          IMGI(25, 4)]]),
]
SOL[26] = [
    P("An important observation from the results is the species in which *O resides in the products. Here, *O from CH~3~O*H is "
      "found in the ester product, not in the water lost."),
    P("The species formed from the options are shown below. Students should select options in which the O from OH^-^ forms a bond with "
      "the carboxyl carbon."),
    TBL([[opt("1"), "Not possible since *O is not attached to the carboxyl carbon.<br>" + IMGI(26, 1)],
         [opt("2", True), "Possible since *O from CH~3~O*H forms a bond with carboxyl carbon.<br>" + IMGI(26, 2)],
         [opt("3", True), "Possible since *O from CH~3~O*H forms a bond with carboxyl carbon.<br>" + IMGI(26, 3)]]),
]
SOL[27] = [
    P("Under these conditions, alkaline hydrolysis of the amide bonds and acid-base reaction with %sCOOH take place." % "–"),
    IMG(27, 1),
]
SOL[28] = [
    TBL([["<b>Evidence</b>", "<b>Deduction</b>"],
         ["<b>R</b> does not react with sodium metal",
          "No redox reaction<br><b>R</b> does not contain alcohol, phenol or carboxylic acid groups."],
         ["<b>R</b> gives an orange precipitate with 2,4-dinitrophenylhydrazine",
          "Condensation reaction.<br><b>R</b> contains at least 1 aldehyde/ketone"],
         ["When <b>R</b> (C~4~H~6~O~2~) is treated with <b>S</b>, it forms an organic product with formula C~4~H~6~O~3~.",
          "<b>R</b> gained 1 O to form C~4~H~6~O~3~.<br>"
          "• Concentrated H~3~PO~4~, steam adds H~2~O across C=C, which would result in the gain of 2H and 1O.<br>"
          "• Strong oxidation using KMnO~4~ results in the gain of 1O when an aldehyde is oxidised to form a carboxylic acid, that is, "
          "%sCHO → %sCOOH.<br>Since <b>R</b> gained 1 O, <b>R</b> contains 1 aldehyde group." % ("–", "–")]]),
    P("Since <b>R</b> contains an aldehyde, it would react with Fehling’s solution."),
]
SOL[29] = [
    IMG(29, 1),
    P("By observing the example reaction, the changes are:<br>C1C2 π bond broken, C1C6 forms new σ bond<br>"
      "C5C6 π bond broken, C4C5 forms new π bond<br>C3C4 σ bond broken, C2C3 forms new π bond<br>"
      "possible mechanism shown by curly arrows"),
    P("Applying the same pattern of bonds broken and formed, or by mechanism:"),
    IMG(29, 2),
]
_m = _reg(30, 2)
SOL[30] = [
    IMG(30, 1),
    '<p><span class="ans">This polymer is made of 2 types of monomers through addition polymerisation. Hence, there are 2 types of '
    'alkenes, ethene and <img class="ws-fig" data-asset="%s" alt="" style="vertical-align:middle">.</span></p>' % _m,
]

# ------------------------------------------------------------------- user rulings (declared, asserted)
TYPO_FIXES = [     # (qn, old, new, expected count) -- none of the pending items (Q16 pi, Q26 wording) are applied
]

SHORT_FORMS = [
]

# ------------------------------------------------------------------- output
assert sorted(SOL) == list(range(1, 31))
out = {}
for q in sorted(SOL):
    html = '<div class="worked-solution">\n%s\n</div>' % "\n".join(SOL[q])
    for qn, old, new, n in TYPO_FIXES:
        if qn == q:
            assert html.count(old) == n, (qn, old, html.count(old))
            html = html.replace(old, new)
    for pat, rep in SHORT_FORMS:
        html = re.sub(pat, rep, html)
    out[str(q)] = html

# ------------------------------------------------------------------- checks
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
heads = dict((int(a), b) for a, b in re.findall(r"\bQ\s*(\d{1,2})\s+\(Ans:\s*([A-D])\)", lay))
assert heads == KEY, ("block headings != KEY", {k: (heads.get(k), KEY[k]) for k in KEY if heads.get(k) != KEY[k]})
top = lay.split("MCQ worked solutions")[0]
rows = re.findall(r"Answer\s+((?:[A-D]\s+)+[A-D])", top)
printed = "".join(re.sub(r"\s+", "", r) for r in rows)
assert printed == "".join(KEY[i] for i in range(1, 31)), ("printed table != KEY", printed)
# the question paper's own typed table (not present for RI): the key is cross-checked against the two printed sources above
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
print("key counts", counts)
assert len(ASSETS) == 28, len(ASSETS)
for q, html in out.items():
    own = len(re.findall(r'data-asset="RI_H2_P1_Q%s_ans-' % q, html))
    assert own == sum(1 for a in ASSETS if a["question"] == int(q)), q
    assert "~" not in html and "^" not in html.replace("→", ""), ("unconverted notation", q, re.findall(r".{15}[~^].{15}", html)[:3])
    assert "%s" not in html and "%%" not in html, q

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key verified (table = headings = KEY), %d answer snips" % len(ASSETS))
