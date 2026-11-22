"""SAJC 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: "SAJC 2026 H2 Chemistry Paper 1 answers" (25-page PDF + docx twin).  Page 1 prints the key table
(BCABCBCBCB BADCCDADDD ACAADCBBDA); every solution also carries an "Ans:" / "Answer here:" line or a stated option verdict
(STATED, asserted below).  Solutions are typed in house markup; only drawn structures are snipped.

Run:  python3 -m ingest.build_sajc26_p1_answers <answers.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

Answer snips (Claude / user, 11): Q4 ans-1 (ice lattice), Q16 ans-1 (parent acid; user redrew) and ans-2 (4-membered ester),
Q19 ans-1 (rotation about the C-C bond; user redrew), Q20 ans-1 (monomer), Q22 ans-1..4, Q23 ans-1, Q25 ans-1 (whole
handwritten solution).  The school's handwritten Q3 working is NOT used; Q3 is typed.
Files: SAJC_H2_P1_Q<n>_ans-<k>_2026.png.

Slips in the school's solutions, corrected on the user's standing ruling (fix typos/grammar, spell short forms in full, keep
state symbols and symbols) -- each is logged in CHANGES below.  Chemistry fixes the user confirmed: Q2, Q3, Q5, Q6, Q12 (>= for
the precipitation condition), Q15, Q16, Q17, Q21, Q28, Q29, Q4.  Fixes beyond that list (flagged to the user): Q5 options A/B/D
reasoning, Q8 statement 3 inequality, Q29 cathode reasoning.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

#        1-10          11-20         21-30
KEY = dict(enumerate("BCABCBCBCB" "BADCCDADDD" "ACAADCBBDA", 1))
# letters the school's own text states (the rest follow the printed key table)
STATED = {1: "B", 2: "C", 3: "A", 4: "B", 5: "C", 6: "B", 7: "C", 8: "B", 9: "C", 10: "B", 11: "B", 12: "A", 13: "D",
          14: "C", 15: "C", 17: "A", 18: "D", 19: "D", 20: "D", 21: "A", 22: "C", 23: "A", 24: "A", 27: "B", 28: "B",
          29: "D", 30: "A"}
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
    path = "SAJC_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
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
    P("Amount of gas = " + fr("1", "24000") + " mol"),
    P("Number of H~2~ molecules = " + fr("1", "24000") + " × " + LL + " = " + fr(LL, "24000")),
    P("Number of H atoms = " + fr(LL, "24000") + " × 2 = " + fr("2" + LL, "24000")),
]
SOL[2] = [
    P(O("A") + " is incorrect. Ca is from Group 2 with a valence electronic configuration of 4s^2^. To achieve Ca^2+^, both electrons "
      "are removed from the same 4s subshell."),
    P(O("B") + " is incorrect. Fe has a valence electronic configuration of 3d^6^ 4s^2^. To achieve Fe^2+^, both electrons are "
      "removed from the same 4s subshell."),
    P(O("C") + " is correct. Cu has a valence electronic configuration of 3d^10^ 4s^1^. To achieve Cu^2+^, one electron is removed "
      "from the 4s subshell and another from the 3d subshell."),
    P(O("D") + " is incorrect. P is from Group 15 with a valence electronic configuration of 3s^2^ 3p^3^. To achieve P^2+^, both "
      "electrons are removed from the same 3p subshell."),
]
SOL[3] = [
    P("Amount of Cr~2~O~7~^2-^ = " + fr("20.80", "1000") + " × 0.400 = 0.00832 mol"),
    P("Amount of L^<i>x</i>+^ = " + fr("25.0", "1000") + " × 0.500 = 0.0125 mol"),
    P("Cr~2~O~7~^2-^ : L^<i>x</i>+^ = 0.00832 : 0.0125 = 2 : 3"),
    P("1 Cr~2~O~7~^2-^ gains 6 electrons (Data Booklet): Cr~2~O~7~^2-^ + 14H^+^ + 6e^-^ → 2Cr^3+^ + 7H~2~O"),
    TBL([["Cr~2~O~7~^2-^", "e^-^ gained", "L^<i>x</i>+^"],
         ["1", "6", ""],
         ["2", "12", "3"],
         ["", "4", "1"]]),
    P("Each L^<i>x</i>+^ loses 4 electrons to become L^5+^."),
    P("<i>x</i> + 4 = +5<br><i>x</i> = +1"),
]
SOL[4] = [
    P("Structure of ice:"),
    IMG(4, 1),
    P(ST("1") + " is correct. The structure of ice involves both covalent O–H bonds and hydrogen bonds between O and H."),
    P(ST("2") + " is correct. Due to this open structure, ice floats on water and hence it is less dense."),
    P(ST("3") + " is correct. From the structure, each O is surrounded by 4 electron pairs (2 bond pairs in the O–H bonds and 2 "
      "lone pairs, which form hydrogen bonds with neighbouring water molecules). This gives a tetrahedral arrangement around O "
      "and a bond angle of 109.5°."),
    P(ST("4") + " is incorrect. Each O uses both of its 2 lone pairs to form 2 hydrogen bonds with neighbouring water molecules, so "
      "4 electrons are involved in forming hydrogen bonds, not 2."),
]
SOL[5] = [
    P(O("A") + " is incorrect. For 1 mole of an ideal gas, <i>pV</i> = <i>RT</i>, so a graph of <i>pV</i> against <i>T</i> is a "
      "straight line through the origin. This is not what is seen on the graph (a curve of the form <i>y</i> = <i>m</i>/<i>x</i>)."),
    P(O("B") + " is incorrect. At constant <i>V</i>, <i>p</i> increases linearly with <i>T</i>, giving a straight line through the "
      "origin (<i>y</i> = <i>mx</i>). This is not what is seen on the graph."),
    P(O("C") + " is correct. At constant <i>T</i>, when <i>V</i> increases, <i>p</i> decreases to keep <i>nRT</i> constant. This is "
      "what is seen on the graph (<i>y</i> = <i>m</i>/<i>x</i>)."),
    P(O("D") + " is incorrect. At constant <i>T</i>, as <i>p</i> increases, <i>V</i> decreases and hence 1/<i>V</i> will increase. "
      "<i>p</i> is directly proportional to 1/<i>V</i>, giving a straight line through the origin (<i>y</i> = <i>mx</i>), which is "
      "not what is seen on the graph."),
]
SOL[6] = [
    P(O("A") + " is incorrect. The first ionisation energy of the elements in Period 3 has a generally increasing trend."),
    P(O("B") + " is correct. The melting point of the elements increases from Na to Si before generally decreasing from P to Cl."),
    P(O("C") + " is incorrect. The pH of the oxides of the Period 3 elements in water has a general decreasing trend, from basic "
      "to acidic."),
    P(O("D") + " is incorrect. Ionic radius decreases from Na^+^ to Si^4+^, and then decreases again from P^3-^ to Cl^-^."),
]
SOL[7] = [
    P("A conjugate acid-base pair differs by only 1 proton (H^+^)."),
    P(O("C") + " is correct. H~2~O and OH^-^ differ by exactly one H^+^."),
]
SOL[8] = [
    P(ST("1") + " is correct. Ion-dipole interactions are formed during hydration (between the gaseous ions and water). Ionic bonds "
      "(between the anion and cation) are formed in lattice energy. Both are exothermic."),
    P(ST("2") + " is correct. Since the beaker felt warm when calcium chloride was dissolved in water, the enthalpy change of "
      "solution is exothermic. Since " + DH + "~soln~ = " + DH + "~hyd~ – LE, and both the enthalpy change of hydration and the "
      "lattice energy are exothermic, the magnitude of LE has to be smaller than the magnitude of the enthalpy change of hydration "
      "in order for the enthalpy change of solution to be exothermic (negative)."),
    P(ST("3") + " is incorrect. " + DG + " is negative as the reaction takes place readily. " + DS + " can be positive or "
      "negative: since " + DH + " is negative, " + DG + " is still negative with a negative " + DS + " as long as |" + DH + "| > "
      "|<i>T</i>" + DS + "|. Hence " + DS + " cannot be concluded to be negative."),
]
SOL[9] = [
    P("Rate = <i>k</i>[CH~3~CO~2~CH~2~CH~3~][H^+^]"),
    P("Since [H^+^] remains constant, rate = <i>k</i>′[CH~3~CO~2~CH~2~CH~3~], where <i>k</i>′ = <i>k</i>[H^+^]."),
    P("<i>t</i>~½~ = " + fr("ln 2", "<i>k</i>′") + " = " + fr("ln 2", "<i>k</i>[H^+^]")),
    P("When [HCl] = [H^+^] = 1.0 mol dm^-3^, <i>t</i>~½~ = 30 min.<br>"
      "When [HCl] = [H^+^] = 2.0 mol dm^-3^, <i>t</i>~½~ = 15 min."),
    P("0.2 → 0.1 → 0.05 → 0.025"),
    P("For [CH~3~CO~2~CH~2~CH~3~] to fall to 0.025 mol dm^-3^, 3 × <i>t</i>~½~ = 3 × 15 = 45 min."),
]
SOL[10] = [
    P("The forward reaction is endothermic, as energy is required to break the bond in the dimer to give its two monomers."),
    P("When <i>T</i> increases, the position of equilibrium shifts right to favour the forward endothermic reaction, so as to "
      "absorb heat and decrease <i>T</i>. As there are more gaseous species, the volume increases."),
]

# ============================================================== 11 - 20
SOL[11] = [
    P("Let the volume of COCl~2~ that decomposes be <i>x</i> cm^3^."),
    TBL([["", "COCl~2~(g)", "<->", "CO(g)", "+", "Cl~2~(g)"],
         ["equilibrium volume / cm^3^", "100 – <i>x</i>", "", "<i>x</i>", "", "<i>x</i>"]]),
    P("Total volume at equilibrium = (100 + <i>x</i>) cm^3^"),
    P(fr("<i>x</i>", "100 + <i>x</i>") + " = 0.20; hence <i>x</i> = 25"),
    P("Total volume of gases in the equilibrium mixture = 100 + 25 = 125 cm^3^"),
]
SOL[12] = [
    P("Total volume of the mixture is 140 cm^3^, [Mg^2+^] = " + fr("100", "140") + " × 0.20 = 0.143 mol dm^-3^."),
    P("In order for Mg(OH)~2~ to precipitate, the ionic product (IP) of Mg(OH)~2~ ≥ " + KSP + " of Mg(OH)~2~."),
    P("[Mg^2+^][OH^-^]^2^ ≥ 6.3 × 10^-10^<br>0.143 × [OH^-^]^2^ ≥ 6.3 × 10^-10^<br>[OH^-^] ≥ 6.6407 × 10^-5^ mol dm^-3^"),
    P("When Mg(OH)~2~ just precipitates, [OH^-^] = 6.6407 × 10^-5^ mol dm^-3^, and [Cu^2+^] is fixed by the " + KSP + " of Cu(OH)~2~:"
      "<br>[Cu^2+^][OH^-^]^2^ = 2.2 × 10^-20^<br>[Cu^2+^] = 4.99 × 10^-12^ mol dm^-3^"),
]
SOL[13] = [
    P("Reaction 1 is elimination, reaction 2 is (acidic) hydrolysis and reaction 3 is substitution. Only reaction 3 is correctly "
      "identified."),
]
SOL[14] = [
    P(ST("1") + " is incorrect. The enantiomers have identical physical properties except in the direction in which they rotate "
      "plane-polarised light."),
    P(ST("2") + " is correct. The enantiomers bond with chiral biological receptors differently."),
    P(ST("3") + " is incorrect. The enantiomers are stereoisomers, not structural isomers, and have identical chemical properties "
      "except in their interactions with another chiral molecule."),
]
SOL[15] = [
    P(O("A") + " and " + O("D") + " are incorrect as there are no H• radicals formed in free-radical substitution."),
    P(O("B") + " is incorrect as it is a propagation step, not a termination step."),
    P(O("C") + " is correct. Two radicals combine to form a stable molecule, which is a termination step."),
]
SOL[16] = [
    IMG(16, 1),
    P(ST("1") + " is incorrect. To form H~2~NCH~2~CH(OH)CH~2~COOC~6~H~5~, an acyl chloride is needed to react with phenol, as phenol "
      "is a poor nucleophile."),
    P(ST("2") + " is incorrect. The expected organic product for the nucleophilic substitution by PCl~5~ is "
      "H~2~NCH~2~CHClCH~2~COCl."),
    P(ST("3") + " is correct. The 4-membered cyclic ester " + IMGL(16, 2) + " is formed through intramolecular esterification. "
      "(3 only is correct.)"),
]
SOL[17] = [
    P("<b>W</b> is a bromobenzene. The lone pair of electrons on Br delocalises into the benzene ring, giving the C–Br bond partial "
      "double bond character. Hence, the C–Br bond is very strong and does not hydrolyse easily."),
    P("<b>X</b> is an acyl chloride. With the additional electronegative O, the C of C=O is very electron-deficient and reacts "
      "with nucleophiles/water easily. Hence, it is the most easily hydrolysed."),
    P("<b>Y</b> is more reactive than <b>Z</b>. The C–Br bond is weaker than the C–Cl bond. The larger Br atom causes the orbital "
      "overlap between C and Br to be less effective."),
    P("Order of increasing ease of hydrolysis: <b>W</b> → <b>Z</b> → <b>Y</b> → <b>X</b>"),
]
SOL[18] = [
    P(O("A") + " is incorrect. Benzene undergoes electrophilic substitution, not electrophilic addition, because addition would "
      "disrupt the stable delocalised π system."),
    P(O("B") + " is incorrect. Each carbon atom contributes one electron, not one electron pair, to the delocalised π system."),
    P(O("C") + " is incorrect. Benzene is planar, but its π electrons do not alternate between adjacent carbon atoms. They are "
      "delocalised over all six carbon atoms, which gives benzene its stability."),
    P(O("D") + " is correct."),
]
SOL[19] = [
    P("Structure <b>D</b> has an internal plane of symmetry (it is a meso compound), hence it cannot rotate plane-polarised light."),
    P("Rotating the C–C bond that contains both –OH groups shows this: structure <b>C</b> has no plane of symmetry, whereas "
      "structure <b>D</b> has one."),
    IMG(19, 1),
]
SOL[20] = [
    P(ST("1") + " is incorrect as the alcohol can form hydrogen bonds with water."),
    P(ST("2") + " is incorrect as alcohols cannot undergo neutralisation with NaOH."),
    P(ST("3") + " is correct as the polymer is formed from " + IMGL(20, 1) + ", which cannot show cis-trans isomerism."),
]

# ============================================================== 21 - 30
SOL[21] = [
    P("Step 1: nucleophilic substitution"),
    P("Step 2: nucleophilic addition"),
    P("Step 3: acid-base reaction"),
    P("Oxidation does not occur in this process, so <b>A</b> is the answer."),
]
SOL[22] = [
    TBL([[O("A"), IMGI(22, 1), "No elimination as there are no H atoms on the adjacent carbon."],
         [O("B"), IMGI(22, 2), "No elimination as there are no H atoms on the adjacent carbon."],
         [O("C"), IMGI(22, 3), "Elimination forms only 1 organic product."],
         [O("D"), IMGI(22, 4), "Elimination forms 2 possible organic products."]]),
]
SOL[23] = [
    P("A nucleophile is involved in all three reactions (boxed below)."),
    IMG(23, 1),
]
SOL[24] = [
    TBL([["", "", "molecular formula", "empirical formula", "iodoform test",
          "amount of H~2~(g) / mol<br>(½ mol of H~2~ for every –OH, including the –OH of –COOH)"],
         [O("A"), "CH~3~CH(OH)CO~2~H", "C~3~H~6~O~3~", "CH~2~O", OK, "1"],
         [O("B"), "CH~3~COCH~2~CH~2~CO~2~H", "C~5~H~8~O~3~", "C~5~H~8~O~3~", OK, "0.5"],
         [O("C"), "CH~3~CO~2~H", "C~2~H~4~O~2~", "CH~2~O", NO, "0.5"],
         [O("D"), "HO~2~CCH~2~CH(OH)CH~2~OH", "C~4~H~8~O~4~", "CH~2~O", NO, "1.5"]]),
    P("Only <b>A</b> has the empirical formula CH~2~O, gives a positive iodoform test and gives 1 mol of H~2~(g)."),
]
SOL[25] = [
    P("On heating under reflux with acidified aqueous KMnO~4~, the C=C bonds and the diol are cleaved as shown below. Only the "
      "product with a ketone or aldehyde group gives an orange precipitate with 2,4-dinitrophenylhydrazine."),
    IMG(25, 1),
]
SOL[26] = [
    P("Mn has an electronic configuration of [Ar]3d^5^4s^2^ and can have oxidation states of 0 to +7."),
    P(O("A") + ": Mn is in the +7 oxidation state."),
    P(O("B") + ": Mn is in the +2 oxidation state."),
    P(O("C") + ": Mn is in the +8 oxidation state, which is not possible. Hence, this species is unlikely to exist."),
    P(O("D") + ": Mn is in the +3 oxidation state."),
]
SOL[27] = [
    P(E_STD + "(I~2~/I^-^) = +0.54 V<br>" + E_STD + "(H~2~O~2~/H~2~O) = +1.77 V"),
    P("<i>E</i>" + STD + "~cell~ = +1.77 – (+0.54) = +1.23 V"),
    P("H~2~O~2~ + 2H^+^ + 2I^-^ → 2H~2~O + I~2~"),
    P("The solution turns brown due to iodine. No gas is evolved."),
]
SOL[28] = [
    P("<i>Q</i> = <i>It</i> = 0.44 × 25 × 60 = 660 C"),
    P("Amount of e^-^ transferred = " + fr("660", "96500") + " = 6.839 × 10^-3^ mol"),
    P("Amount of Ru deposited = " + fr("0.345", "101") + " = 3.416 × 10^-3^ mol"),
    P("Ru^<i>y</i>+^ + <i>y</i>e^-^ → Ru"),
    P("<i>y</i> = " + fr("6.839 × 10^-3^", "3.416 × 10^-3^") + " = 2"),
    P("Hence, the formula is Ru(NO~3~)~2~."),
]
SOL[29] = [
    P("At the anode, gas <b>Y</b> is produced."),
    P("Species at the anode: NO~3~^-^ and H~2~O. H~2~O is oxidised as NO~3~^-^ can only be reduced."),
    P("2H~2~O → O~2~ + 4H^+^ + 4e^-^"),
    P("Options <b>A</b> and <b>B</b> are incorrect."),
    P("At the cathode, the metal ion undergoes reduction to form metal <b>X</b>. " + E_STD + "(Zn^2+^/Zn) is less negative than "
      + E_STD + "(H~2~O/H~2~), so Zn^2+^ is preferentially reduced, whereas Mg^2+^ is not (water is reduced instead)."),
]
SOL[30] = [
    P("Cl~2~ + 2e^-^ <-> 2Cl^-^, " + E_STD + " = +1.36 V (cathode)<br>"
      "Zn^2+^ + 2e^-^ <-> Zn, " + E_STD + " = –0.76 V (anode)"),
    P(O("A") + " is correct. When the pressure of Cl~2~ decreases, the position of equilibrium shifts left, so <i>E</i>(Cl~2~/Cl^-^) "
      "becomes less positive. Since <i>E</i>~cell~ = <i>E</i>~cathode~ – <i>E</i>~anode~, <i>E</i>~cell~ will be less positive."),
    P(O("B") + " is incorrect. When AgNO~3~ is added to Tank 1, AgCl(s) forms. [Cl^-^] decreases and the position of equilibrium "
      "shifts right, so <i>E</i>(Cl~2~/Cl^-^) becomes more positive. <i>E</i>~cell~ will be more positive."),
    P(O("C") + " is incorrect. The size of the electrode does not affect the <i>E</i>~cell~ value."),
    P(O("D") + " is incorrect. Addition of ammonia forms [Zn(NH~3~)~4~]^2+^. [Zn^2+^] decreases and the position of equilibrium shifts "
      "left to favour oxidation, so <i>E</i>(Zn^2+^/Zn) becomes more negative. Overall, <i>E</i>~cell~ will be more positive."),
]

# ------------------------------------------------------------------- output
assert sorted(SOL) == list(range(1, 31))
out = {}
for q in sorted(SOL):
    out[str(q)] = '<div class="worked-solution">\n%s\n</div>' % "\n".join(SOL[q])

# ------------------------------------------------------------------- checks
assert len(KEY) == 30 and all(v in "ABCD" for v in KEY.values())
for q, a in STATED.items():
    assert KEY[q] == a, ("KEY disagrees with a letter the school states", q, KEY[q], a)
page1 = subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-layout", PDF, "-"], capture_output=True, text=True,
                       check=True).stdout
printed = re.findall(r"\b([A-D])\b", page1.split("Use of the Data Booklet")[0])
assert "".join(printed) == "".join(KEY[i] for i in range(1, 31)), ("printed key table", "".join(printed))
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
for q, tok in ((3, "0.00832"), (3, "0.0125"), (9, "45 min"), (11, "125 cm"), (12, "4.99"), (12, "0.143"), (28, "6.839"),
               (28, "3.416"), (30, "+1.36")):
    assert tok in lay, (q, tok)
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
print("key counts", counts)
assert len(ASSETS) == 11, len(ASSETS)
for q, html in out.items():
    own = len(re.findall(r'data-asset="SAJC_H2_P1_Q%s_ans-' % q, html))
    assert own == sum(1 for a in ASSETS if a["question"] == int(q)), q
    bad = re.findall(r".{15}[~^@].{15}", re.sub(r"<[^>]+>", "", html).replace("→", ""))
    assert not bad, ("unconverted notation", q, bad[:3])
    assert "%s" not in html and "%%" not in html and "\x00" not in html, q
    assert re.search("[-]", html) is None, ("private-use glyph", q)
    assert "\t" not in html, q

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key %s, %d answer snips" % ("".join(KEY[i] for i in range(1, 31)), len(ASSETS)))
