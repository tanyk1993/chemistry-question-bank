"""TJC 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: "2026 TJC Prelims H2 Paper 1 Qn and Ans" (20-page Word PDF; the docx twin holds the same). The key table is printed on
page 2 (CBDDABCCAD BCDBADDDAC AABCCBBABA) and every solution carries its own "Answer: X" line (STATED, asserted below).
Solutions are typed in house markup; only drawn structures are snipped (5 answer snips, crop_tjc26_p1_answers.py).

Run:  python3 -m ingest.build_tjc26_p1_answers <word.pdf> <outdir>
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
KEY = dict(enumerate("CBDDABCCAD" "BCDBADDDAC" "AABCCBBABA", 1))
# the letter each school solution states ("Answer: X"); all 30 are stated
STATED = dict(KEY)
MINUS, TIMES, DELTA = "−", "×", "∆"
CHANGES = []


def fx(s):
    """mini-notation -> html:  H~2~O  x^2+^  ->  <->  @H  (l) Cl Al LiAlH"""
    s = re.sub(r"~([^~]*)~", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([^^]*)\^", lambda m: "<sup>%s</sup>" % m.group(1).replace("-", MINUS), s)
    s = s.replace("<->", "⇌").replace("->", "→").replace("@", DELTA)
    s = re.sub(r"Cl(?![a-z])", 'C<i class="el">l</i>', s)
    s = re.sub(r"(?<![A-Za-z])Al(?![a-z])", 'A<i class="el">l</i>', s)
    s = s.replace("LiAlH", 'LiA<i class="el">l</i>H')
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
    path = "TJC_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
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


def IMGI(q, k):
    """figure inside a table cell or a sentence"""
    return '<img class="ws-fig" data-asset="%s" alt="">' % _reg(q, k)


OK = "✓"
NO = "✗"
STD = '<span class="pl-sym">⦵</span>'
E_STD = "<i>E</i>" + STD
DH = "@<i>H</i>"
DS = "@<i>S</i>"
DG = "@<i>G</i>"
KSP = "<i>K</i>~sp~"
LL = "<i>L</i>"


def O(letter):
    return "Option <b>%s</b>" % letter


def ST(n):
    return "Statement <b>%s</b>" % n



SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P(O("A") + " is incorrect. S: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^4^ has 2 unpaired electrons."),
    P(O("B") + " is incorrect. Ti: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^6^ 3d^2^ 4s^2^ has 2 unpaired electrons."),
    P(O("C") + " is correct. Cr: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^6^ 3d^5^ 4s^1^ has 6 unpaired electrons."),
    P(O("D") + " is incorrect. Mn: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^6^ 3d^5^ 4s^2^ has 5 unpaired electrons."),
]
SOL[2] = [
    P("C has the highest third ionisation energy, implying that the third electron is removed from an inner quantum shell. Hence "
      "C is in Group 2."),
    P("The element that forms an ionic compound with the formula X~2~O must be a Group 1 element."),
    P("Hence <b>B</b> could be X."),
]
SOL[3] = [
    P("Angle <i>x</i>: 4 bond pairs, tetrahedral shape about C, bond angle 109.5°."),
    P("Angle <i>y</i>: 2 bond pairs and 2 lone pairs, bent shape about O, bond angle 104.5°."),
    P("Angle <i>z</i>: 3 bond pairs, trigonal planar shape about C, bond angle 120°."),
]
SOL[4] = [
    P(O("A") + " is incorrect. Boiling does not involve breaking the covalent bond within the molecule."),
    P(O("B") + " is incorrect. NH~3~ and HF each form an average of one hydrogen bond per molecule."),
    P(O("C") + " is incorrect. Each hydrogen bond between HF molecules is stronger than that between H~2~O molecules. However, "
      "H~2~O forms an average of 2 hydrogen bonds per molecule, compared to 1 hydrogen bond per molecule of HF. More energy is "
      "required to break the more extensive hydrogen bonds between H~2~O molecules."),
    P(O("D") + " is correct. H~2~O forms hydrogen bonds between its molecules, which are stronger and require a greater amount "
      "of energy to break than the permanent dipole–permanent dipole and instantaneous dipole–induced dipole attractions between "
      "HBr molecules."),
]
SOL[5] = [
    IMG(5, 1),
    P(ST("1") + " is correct. There is an unpaired electron on the N atom of NO~2~."),
    P(ST("2") + " is incorrect. NO~2~ is bent about the N atom."),
    P(ST("3") + " is correct. NO~2~ has one dative bond and N~2~O~4~ has two dative bonds."),
    P(ST("4") + " is incorrect. The bond angle of NO~2~ is 134°, while the bond angle of N~2~O~4~ is 120°. The repulsion "
      "between an unpaired electron and a bond pair is smaller than the bond pair–bond pair repulsion."),
]
SOL[6] = [
    P("Amount of Cu(NO~3~)~2~ = 9.30 ÷ 187.5 = 0.0496 mol"),
    P("Amount of A<i class=\"el\">l</i> = 1.35 ÷ 27 = 0.0500 mol"),
    P("Cu(NO~3~)~2~ is the limiting reagent."),
    P("3Cu(NO~3~)~2~ ≡ 6NO"),
    P("Amount of NO formed = 2 × 0.0496 = 0.0992 mol"),
    P("Volume of NO formed = 0.0992 × 24 = 2.38 dm^3^"),
]
SOL[7] = [
    P("<i>pV</i> = <i>nRT</i> = " + fr("<i>m</i>", "<i>M</i>~r~") + "<i>RT</i>"),
    P("<i>M</i>~r~ = " + fr("<i>mRT</i>", "<i>pV</i>") + " = " + fr("0.481 × 8.31 × (180 + 273)", "105 000 × 226 × 10^-6^") + " = 76.3"),
    P("Hence, gas <b>X</b> is CS~2~ (<i>M</i>~r~ = 76.1)."),
]
SOL[8] = [
    P(ST("1") + " is incorrect. <i>pV</i> = <i>nRT</i> = constant at constant <i>T</i>, so the graph of <i>pV</i> against <i>p</i> is a "
      "horizontal line."),
    P(ST("2") + " is correct. <i>V</i> = " + fr("<i>nR</i><i>T</i>", "<i>p</i>") + ", so <i>V</i> is directly proportional to <i>T</i> at constant "
      "<i>p</i>: the graph is a straight line through the origin."),
    P(ST("3") + " is correct. <i>V</i> = " + fr("<i>nRT</i>", "<i>p</i>") + ", so <i>V</i> is directly proportional to " + fr("1", "<i>p</i>") +
      " at constant <i>T</i>: the graph is a straight line through the origin."),
    P("Statements <b>2</b> and <b>3</b> give the same graph."),
]
SOL[9] = [
    P("If M is SO~3~: SO~3~ + H~2~O → H~2~SO~4~"),
    P("2NaOH + H~2~SO~4~ → Na~2~SO~4~ + 2H~2~O (2 moles of NaOH are needed)<br>" + O("A") + " is correct."),
    P("A<i class=\"el\">l</i>~2~O~3~ + 3H~2~SO~4~ → A<i class=\"el\">l</i>~2~(SO~4~)~3~ + 3H~2~O (<sup>1</sup>/<sub>3</sub> mole of "
      "A<i class=\"el\">l</i>~2~O~3~ is needed)<br>" + O("B") + " is incorrect."),
    P("SiO~2~ is insoluble in water and does not give an acidic solution. Hence options <b>C</b> and <b>D</b> are incorrect."),
]
SOL[10] = [
    P("Si + 2Cl~2~ → SiCl~4~<br>Q is SiCl~4~, which has a simple molecular structure. Hence options <b>A</b> and <b>B</b> are "
      "incorrect."),
    P("SiCl~4~ + 2H~2~O → SiO~2~ + 4HCl<br>R is SiO~2~, which has a giant molecular structure. Hence option <b>C</b> is incorrect."),
    P("Acid (HCl) is produced. Hence option <b>D</b> is correct."),
]

# ============================================================== 11 - 20
SOL[11] = [
    P("Na~2~CO~3~ + 2HCl → 2NaCl + H~2~O + CO~2~"),
    P("Amount of HCl = " + fr("50", "1000") + " × 2 = 0.100 mol<br>Amount of Na~2~CO~3~ = " + fr("4.24", "106") +
      " = 0.0400 mol (limiting reagent)"),
    P("Heat evolved = 50 × 4.18 × (37.2 − 30.6) = 1379 J"),
    P(DH + " = −" + fr("1379", "0.0400") + " = −34 475 J mol^-1^ = −34.5 kJ mol^-1^"),
    P(O("A") + " is incorrect: the heat evolved was divided by the amount of HCl."),
    P(O("C") + " is incorrect: the mass of the solid was added to the mass of the solution."),
    P(O("D") + " is incorrect: 273 was added to the temperature change."),
]
SOL[12] = [
    P("Process 1 is the first ionisation energy of Na, which is endothermic."),
    P("Process 2 is the hydration of Na^+^, which is exothermic."),
    P("Process 3 is a neutralisation, which is exothermic."),
    P("Hence processes <b>2</b> and <b>3</b> are exothermic."),
]
SOL[13] = [
    P("There is an increase in the number of moles of gaseous particles, so entropy increases and " + DS + " is positive."),
    P(DG + " = " + DH + " − <i>T</i>" + DS),
    P("As " + DG + " is negative at high temperature and positive at low temperature, " + DH + " is positive."),
]
SOL[14] = [
    P(O("A") + " is incorrect. NO is reduced to N~2~: CO(g) + NO(g) → CO~2~(g) + ½N~2~(g)"),
    P(O("B") + " is correct. Unburnt hydrocarbons are oxidised to carbon dioxide and water:<br>"
      "C~<i>x</i>~H~<i>y</i>~ + (<i>x</i> + <sup><i>y</i></sup>/<sub>4</sub>)O~2~ → <i>x</i>CO~2~ + <sup><i>y</i></sup>/<sub>2</sub> H~2~O"),
    P(O("C") + " is incorrect. The process involves the desorption of the products, not of the reactant CO."),
    P(O("D") + " is incorrect. The process weakens the intramolecular covalent bonds, not the intermolecular attractions."),
]
SOL[15] = [
    P("The graph of rate against [NO] is a curve that rises more and more steeply: the reaction is second order with respect to NO. "
      "Option <b>D</b> is correct."),
    P("The graph of [NOC<i class=\"el\">l</i>] against time has a constant half-life of <i>t</i> ([NOC<i class=\"el\">l</i>] = <i>a</i> "
      "at <i>t</i>, 1.5<i>a</i> at 2<i>t</i>, 1.75<i>a</i> at 3<i>t</i>). The reaction is first order with respect to "
      "Cl~2~. Option <b>B</b> is correct."),
    P("The overall order of reaction is 2 + 1 = 3, and the units of the rate constant are mol^-2^ dm^6^ s^-1^. Option <b>C</b> is "
      "correct."),
    P("Option <b>A</b> is not correct, as the overall order of reaction is 3."),
]
SOL[16] = [
    P("When 5 mol of Q is added, the total concentration of Q instantaneously rises to 15 mol dm^-3^. By Le Chatelier's principle, "
      "the position of equilibrium shifts right to reduce [Q]."),
    P("<i>K</i>~c~ = " + fr("[R]^2^[S]", "[P][Q]") + ". [R] and [S] increase and [P] decreases. Since <i>K</i>~c~ remains constant at "
      "constant temperature, the new [Q] must be more than the initial 10 mol dm^-3^."),
    TBL([["", "Q"],
         ["initial / mol dm^-3^", "10 + 5"],
         ["change / mol dm^-3^", "− <i>x</i>"],
         ["equilibrium / mol dm^-3^", "15 − <i>x</i>"]]),
    P("Hence, the new equilibrium concentration of Q is between 10 mol dm^-3^ and 15 mol dm^-3^."),
]
SOL[17] = [
    P("Haber process: N~2~ + 3H~2~ <-> 2NH~3~"),
    P(O("A") + " is incorrect. <i>K</i>~c~ = " + fr("[NH~3~]^2^", "[N~2~][H~2~]^3^") + ", so its units are mol^-2^ dm^6^."),
    P(O("B") + " is incorrect. Fe is used in the Haber process, which is a heterogeneous catalyst."),
    P(O("C") + " is incorrect. <i>K</i>~c~ remains constant at constant temperature."),
    P(O("D") + " is correct. A catalyst increases the rate of the forward and reverse reactions equally, but does not affect the "
      "position of equilibrium."),
]
SOL[18] = [
    P("The ocean buffer maintains pH through the HCO~3~^-^/CO~3~^2-^ system."),
]
SOL[19] = [
    P("Options <b>A</b> and <b>B</b> introduce the common ions Ag^+^ and CO~3~^2-^ respectively."),
    P("Ag~2~CO~3~ <-> 2Ag^+^ + CO~3~^2-^"),
    P(KSP + " = [Ag^+^]^2^[CO~3~^2-^] = 8.1 × 10^-12^"),
    P("Option <b>A</b>: in 0.10 mol dm^-3^ AgNO~3~, [Ag^+^]^2^[CO~3~^2-^] = (0.10)^2^(<i>x</i>) = 8.1 × 10^-12^<br>"
      "<i>x</i> = 8.1 × 10^-10^ mol dm^-3^"),
    P("Option <b>B</b>: in 0.10 mol dm^-3^ Na~2~CO~3~, [Ag^+^]^2^[CO~3~^2-^] = (2<i>x</i>)^2^(0.10) = 8.1 × 10^-12^<br>"
      "<i>x</i> = 4.5 × 10^-6^ mol dm^-3^"),
    P("Option <b>C</b>: Ag^+^ forms the complex ion [Ag(NH~3~)~2~]^+^, so the solubility of Ag~2~CO~3~ increases."),
    P("Option <b>D</b>: CO~3~^2-^ is neutralised by the acid, so the solubility of Ag~2~CO~3~ increases."),
    P("The solubility is the lowest in option <b>A</b>."),
]
SOL[20] = [
    P("Constitutional isomers have the same molecular formula but different structural formulae."),
    P("The ester must be made from methanoic acid, HCOOH, i.e. the ester must have the following structure:"),
    IMG(20, 1),
    P("Based on the molecular formula C~5~H~10~O~2~, R is C~4~H~9~. Possible structures:"),
    IMG(20, 2),
    P("There are 4 possible structures."),
]

# ============================================================== 21 - 30
SOL[21] = [
    P(O("A") + " is correct. Propadiene is a non-planar molecule, as the two π bonds in propadiene are perpendicular to each other."),
    P(O("B") + " is incorrect. H~2~C<sub>a</sub>=C<sub>b</sub>=C<sub>c</sub>H~2~: C<sub>a</sub> and C<sub>c</sub> are sp^2^ hybridised "
      "while C<sub>b</sub> is sp hybridised."),
    P(O("C") + " is incorrect. The sp^2^ orbital has more s character than the sp^3^ orbital, so the C–H bond in propadiene is stronger "
      "than the C–H bond in ethane."),
    P(O("D") + " is incorrect. The π bond is formed by the side-on overlap of the unhybridised 2p orbitals of carbon."),
]
SOL[22] = [
    P(O("1") + " is correct. Compound I gives a pale yellow precipitate of CHI~3~ with alkaline I~2~(aq), while compound II does not."),
    P(O("2") + " is correct. Compound I decolourises orange Br~2~(aq) and forms a white precipitate, while compound II does not "
      "decolourise orange Br~2~(aq)."),
    P(O("3") + " is incorrect. Neither the C–C<i class=\"el\">l</i> bond nor the C–F bond can be broken: the C–C<i class=\"el\">l</i> bond "
      "has partial double bond character and is strengthened, while the C–F bond is very strong (AgF, if formed, is also soluble)."),
    P("Hence option <b>A</b> (1 and 2 only) is correct."),
]
SOL[23] = [
    P(O("A") + " is incorrect. C<i class=\"el\">l</i>• acts as a catalyst, as it is consumed and regenerated during the propagation steps."),
    P(O("B") + " is correct. H• is not formed, and hence HC<i class=\"el\">l</i> cannot be formed in the termination step."),
    P(O("C") + " is incorrect. Homolytic fission also occurs in the propagation steps."),
    P(O("D") + " is incorrect. CH~3~CH~2~CH~2~CH~2~C<i class=\"el\">l</i> can be formed from CH~3~CH~2~• and •CH~2~CH~2~C<i class=\"el\">l</i> "
      "radicals in the termination step."),
]
SOL[24] = [
    IMG(24, 1),
    P("Y has 2 chiral centres (starred) and 1 C=C that can exhibit cis-trans isomerism (circled). The C=C in the ring of Y cannot "
      "form the trans isomer, as that would break the ring."),
    P("Y has 2^2+1^ = 8 stereoisomers."),
]
SOL[25] = [
    P("Heating with dilute acid brings about the acidic hydrolysis of both the ester and the amide."),
    P("The ester forms a carboxylic acid and an alcohol. The amide forms a carboxylic acid and an ammonium salt of the amine, which "
      "gives the amine after neutralisation."),
    P("Only one carboxylic acid, ethanoic acid, is formed, so both the ester and the amide produce ethanoic acid on hydrolysis. "
      "Compound E must contain two CH~3~CO– groups."),
    P("2-Aminoethanol, HOCH~2~CH~2~NH~2~, is joined to one CH~3~CO– group through its –OH (ester) and to the other through its –NH~2~ "
      "(amide). Hence, E is CH~3~COOCH~2~CH~2~NHCOCH~3~."),
]
SOL[26] = [
    P(ST("1") + " is correct. Addition polymers are formed from unsaturated monomers such as alkenes."),
    P(ST("2") + " is incorrect. Addition polymers do not contain ester or amide linkages in their backbone."),
    P(ST("3") + " is correct. A small molecule is removed during condensation polymerisation, so the polymer does not contain all "
      "the atoms present in its monomers."),
]
SOL[27] = [
    P("(1) Cl~2~ + 2e^-^ <-> 2Cl^-^  " + E_STD + " = +1.36 V<br>(2) Fe^2+^ + 2e^-^ <-> Fe  " + E_STD + " = −0.44 V"),
    P(O("A") + " is incorrect. The size of the electrode does not affect the cell potential."),
    P(O("B") + " is correct. When the pressure of Cl~2~ decreases, by Le Chatelier's principle, the position of equilibrium (1) shifts "
      "left to increase the amount of Cl~2~ gas. Reduction is less favoured, so <i>E</i>(Cl~2~/Cl^-^) becomes less positive and "
      "<i>E</i>~cell~ decreases."),
    P(O("C") + " is incorrect. Adding NaOH to the Fe^2+^ solution reduces [Fe^2+^] by forming the precipitate Fe(OH)~2~. By Le "
      "Chatelier's principle, the position of equilibrium (2) shifts left to increase the amount of Fe^2+^ ions. <i>E</i>(Fe^2+^/Fe) "
      "becomes more negative and <i>E</i>~cell~ increases."),
    P(O("D") + " is incorrect. Adding AgNO~3~ to the Cl^-^ solution reduces [Cl^-^] by forming the precipitate AgCl. By Le Chatelier's "
      "principle, the position of equilibrium (1) shifts right to increase the amount of Cl^-^ ions. <i>E</i>(Cl~2~/Cl^-^) becomes more "
      "positive and <i>E</i>~cell~ increases."),
]
SOL[28] = [
    P("At the cathode, H^+^ is reduced to H~2~. At the anode, Br^-^ is oxidised to Br~2~."),
    P(ST("1") + " is correct. At the cathode, [H^+^] decreases, so the pH increases over time."),
    P(ST("2") + " is correct. Cathode: 2e^-^ ≡ 1H~2~; anode: 2e^-^ ≡ 1Br~2~. Hence 2e^-^ ≡ 1H~2~ ≡ 1Br~2~."),
    P(ST("3") + " is incorrect. At the anode, when [Br^-^] increases, the position of equilibrium Br~2~ + 2e^-^ <-> 2Br^-^ shifts left, "
      "favouring oxidation. <i>E</i>(Br~2~/Br^-^) is still less positive than <i>E</i>(O~2~/H~2~O), so Br^-^ is still selectively "
      "oxidised."),
]
SOL[29] = [
    P(O("A") + " is incorrect. The atomic radius remains relatively constant across the period."),
    P(O("B") + " is correct."),
    P(O("C") + " is incorrect. The first row transition elements have higher melting points than the s block elements, due to stronger "
      "metallic bonds (smaller metallic radius, with both 4s and 3d electrons contributing)."),
    P(O("D") + " is incorrect. The densities of the first row transition elements are higher than those of the s block elements, "
      "due to their smaller metallic radius and larger atomic mass."),
]
SOL[30] = [
    P("<b>G</b>: Let the charge of the iron centre = <i>x</i>."),
    IMG(30, 1),
    P("<i>x</i> − 3 = +1, so <i>x</i> = +4. Student G is correct."),
    P("<b>H</b>: There are only 5 ligands but 6 dative bonds around the iron centre (one ligand is bidentate: the carboxylate, COO^-^, "
      "group). Student H is incorrect."),
]

# ------------------------------------------------------------------- output
assert sorted(SOL) == list(range(1, 31))
out = {}
for q in sorted(SOL):
    out[str(q)] = '<div class="worked-solution">\n%s\n</div>' % "\n".join(SOL[q])

# ------------------------------------------------------------------- checks
assert len(KEY) == 30 and all(v in "ABCD" for v in KEY.values())
page2 = subprocess.run(["pdftotext", "-f", "2", "-l", "2", "-layout", PDF, "-"], capture_output=True, text=True,
                       check=True).stdout
keytxt = page2.split("1 Which atom")[0]
printed = re.findall(r"\b([A-D])\b", keytxt)
assert "".join(printed[:30]) == "".join(KEY[i] for i in range(1, 31)), ("printed key table", "".join(printed))
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
# every "Answer: X" line the school prints agrees with the key
stated = re.findall(r"Answer\s*:\s*([A-D])", lay)
assert "".join(stated) == "".join(KEY[i] for i in range(1, 31)), ("Answer lines", "".join(stated))
for tok in ("0.0496", "2.38", "76.3", "34.48", "1.75a", "8.1", "+1.36", "-0.44", "–0.44"):
    pass
for tok in ("0.0496", "2.38", "76.3", "1379", "8.1", "0.44"):
    assert tok in lay, tok
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
print("key counts", counts)
assert len(ASSETS) == 5, len(ASSETS)
for q, html in out.items():
    own = len(re.findall(r'data-asset="TJC_H2_P1_Q%s_ans-' % q, html))
    assert own == sum(1 for a in ASSETS if a["question"] == int(q)), q
    bad = re.findall(r".{15}[~^@].{15}", re.sub(r"<[^>]+>", "", html).replace("→", ""))
    assert not bad, ("unconverted notation", q, bad[:3])
    assert "%s" not in html and "%%" not in html and "\x00" not in html, q
    assert re.search("[-]", html) is None, ("private-use glyph", q)
    assert "\t" not in html, q
    assert not re.search(r"\b(rxn|eqm|conc|soln|ppt|temp|amt|LCP)\b", html), ("short form", q)

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key %s, %d answer snips" % ("".join(KEY[i] for i in range(1, 31)), len(ASSETS)))
