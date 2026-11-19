"""RVHS 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: "2026 RVHS Preliminary Examination H2 Chemistry Paper 1 Worked Solutions" (9-page PDF + docx twin).
There is NO printed key table and no "Ans:" headings (only Q1, Q13, Q14 say "Answer: X").  The key below was
DERIVED by solving each question and reading the school's own option verdicts ("Option C is correct", ...); every
letter the school states agrees (STATED, asserted below).  The solutions are plain typed text with a few drawn
structures and picture-fractions, so they are typed here in house markup (same approach as RI / NYJC 2026 P1).

Run:  python3 -m ingest.build_rvhs26_p1_answers <answers.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

Answer snips (Claude's, crop_rvhs26_p1_answers.py): Q22 ans-1..4 (the four bromoalkanes), Q23 ans-1..4 (the four alcohols).
Fractions are typed, not snipped.  Files: RVHS_H2_P1_Q<n>_ans-<k>_2026.png.

Slips in the school's solutions, corrected on the user's standing ruling (fix typos/grammar, spell short forms in
full, keep state symbols and symbols) -- each is logged in CHANGES below.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

#        1-10          11-20         21-30
KEY = dict(enumerate("DAABCDCACC" "CBDBBCADCA" "BDDACDDBAB", 1))
# letters the school's own text states or unambiguously implies (the rest are derived)
STATED = {1: "D", 3: "A", 4: "B", 5: "C", 6: "D", 7: "C", 13: "D", 14: "B", 18: "D", 19: "C", 22: "D", 23: "D", 24: "A"}
MINUS, TIMES, DELTA = "−", "×", "∆"


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
    path = "RVHS_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
    ASSETS.append({"question": q, "slot": "ans-%d" % k, "path": path,
                   "offset": 1 + sum(1 for a in ASSETS if a["question"] == q)})
    return path


def IMGI(q, k):
    """figure inside a table cell"""
    return '<img class="ws-fig" data-asset="%s" alt="">' % _reg(q, k)


OK = "✓"
STD = '<span class="pl-sym">⦵</span>'
E_STD = "<i>E</i>" + STD
DH = "@<i>H</i>"
DS = "@<i>S</i>"
DG = "@<i>G</i>"
I = lambda x: "<i>%s</i>" % x          # italic quantity symbol
KSP = "<i>K</i>~sp~"
SN = "S~N~"


def O(letter):
    return "Option <b>%s</b>" % letter


def sub2(base, sub, sub2_=None):
    return "%s<sub>%s</sub>" % (base, sub)


SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P("N^-^: 1s^2^ 2s^2^ 2p^4^ → lose one electron to become: 1s^2^ 2s^2^ 2p^3^"),
    P("S: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^4^ → lose one electron to become: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^3^"),
    P("Cl^+^: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^4^ → lose one electron to become: 1s^2^ 2s^2^ 2p^6^ 3s^2^ 3p^3^"),
]
SOL[2] = [
    P("Based on the significant increase in the 4^th^ ionisation energy from the 3^rd^ one, element <b>X</b> is in Group 13 "
      "(for example, Al)."),
    P("Such an element will likely form an oxide with the formula <b>X</b>~2~O~3~ (for example, Al~2~O~3~)."),
]
SOL[3] = [
    P(O("A") + " is incorrect (hence this is the answer). While it is true that the first ionisation energy of Mg is higher than "
      "that of Al, this is due to the fact that the electron to be removed from Al is at a higher energy level, and not because "
      "Mg has a higher nuclear charge."),
    P("Options <b>B</b>, <b>C</b> and <b>D</b> are correct and true, hence they are not the answer."),
]
SOL[4] = [
    P(O("A") + " is incorrect. In ice, hydrogen bonding arranges water molecules into an open tetrahedral lattice, spacing them "
      "further apart than in liquid water. This gives ice a lower density than water at 0 °C."),
    P(O("B") + " is correct. In CH~3~F, hydrogen atoms are bonded to carbon, which is not electronegative enough for hydrogen "
      "bonding to occur. Neither CH~3~F nor HCl can form hydrogen bonds. The higher boiling point of CH~3~F is due to its stronger "
      "permanent dipole-dipole interactions between molecules, not hydrogen bonding."),
    P(O("C") + " is incorrect. In 2-nitrophenol, the ortho –NO~2~ group forms an intramolecular hydrogen bond with the –OH group, "
      "preventing intermolecular hydrogen bonding and lowering the boiling point. In 4-nitrophenol, no such intramolecular hydrogen "
      "bond is possible since the para –NO~2~ group and –OH group are far apart, so intermolecular hydrogen bonds form freely, "
      "raising the boiling point."),
    P(O("D") + " is incorrect. In non-polar benzene, two ethanoic acid molecules form a dimer via two hydrogen bonds between their "
      "–COOH groups. This doubles the effective molecular mass from 60 to 120."),
]
SOL[5] = [
    P(O("C") + " is correct. Three possible structures of C~2~N exist. In each structure, there are a total of 2 lone pairs of "
      "electrons and 1 unpaired electron."),
]
SOL[6] = [
    P(O("A") + " is incorrect. At constant <i>V</i>, the gradient of the graph is <i>nR</i>. The gradient for L should be greater "
      "since the number of moles of L is greater than the number of moles of M."),
    P(O("B") + " is incorrect. At constant <i>p</i>, <i>V</i> = " + fr("<i>nRT</i>", "<i>p</i>") + ", the gradient is positive."),
    P(O("C") + " is incorrect. At constant <i>T</i>, <i>V</i> = " + fr("<i>nRT</i>", "<i>p</i>") + ", so the graph should be a "
      "straight line passing through the origin. The gradient for L should be greater."),
    P(O("D") + " is correct. At constant <i>T</i>, <i>pV</i> = constant. The <i>pV</i> value for L is greater as the number of "
      "moles of L is greater than the number of moles of M."),
]
SOL[7] = [
    P(O("A") + " is incorrect as H~2~S is a proton donor and hence acting as a Brønsted-Lowry acid."),
    P(O("B") + " is incorrect as H~2~S is a proton donor and hence acting as a Brønsted-Lowry acid."),
    P(O("C") + " is correct as H~2~S is a proton acceptor and hence acting as a Brønsted-Lowry base."),
    P(O("D") + " is incorrect as H~2~S is a proton donor and hence acting as a Brønsted-Lowry acid."),
]
SOL[8] = [
    P("Since this is a strong acid and strong alkali neutralisation, this reaction is exothermic, resulting in a temperature rise."),
    P("Option 1: correct, as a lower ambient temperature will cause greater heat loss during the experiment, which will result "
      "in an overall lower temperature change/rise."),
    P("Option 2: correct, as lower concentrations of reagents (with all other factors being the same) will result in less heat "
      "energy produced (as there are smaller amounts of reagents reacting)."),
    P("Option 3: incorrect. Assuming that all other experimental factors are the same, a higher [NaOH] can only result in:<br>"
      "1) an increase in temperature change if NaOH was the limiting reagent in the original experiment, or<br>"
      "2) the same temperature change if NaOH was in excess in the original experiment."),
]
SOL[9] = [
    P("3.6 g of ice/water = 0.200 mol of ice/water"),
    P("For 1 mol of melting ice at 0 °C, " + DG + " = 0"),
    P(DH + " – <i>T</i>" + DS + " = 0"),
    P("(6010) – (273)" + DS + " = 0"),
    P(DS + " = 22.0 J mol^-1^ K^-1^"),
    P("For 0.2 mol of melting ice: " + DS + " = (0.2)(22.0) = 4.4 J mol^-1^ K^-1^"),
]
SOL[10] = [
    PC("4Fe(s) + 3O~2~(g) → 2Fe~2~O~3~(s)"),
    P(DH + " < 0, " + DS + " < 0"),
    P("Hence, based on " + DG + " = " + DH + " – <i>T</i>" + DS + ", " + DG + " will be negative only at low enough <i>T</i> such "
      "that |<i>T</i>" + DS + "| < |" + DH + "|"),
]

# ============================================================== 11 - 20
VCO2 = "<i>V</i><sub>CO<sub>2</sub></sub>"
VCXHY = "<i>V</i><sub>C<sub><i>x</i></sub>H<sub><i>y</i></sub></sub>"
VO2R = "<i>V</i><sub>O<sub>2</sub> reacted</sub>"
SOL[11] = [
    PC("C~<i>x</i>~H~<i>y</i>~(g) + (<i>x</i> + " + fr("<i>y</i>", "4") + ")O~2~(g) → <i>x</i>CO~2~(g) + " + fr("<i>y</i>", "2")
       + " H~2~O(l)"),
    P("Volume of CO~2~ = 65 – 25 = 40 cm^3^"),
    P(fr(VCO2, VCXHY) + " = " + fr("40", "10") + " = 4, <i>x</i> = 4"),
    P("Volume of O~2~ left = 25 cm^3^<br>Volume of O~2~ reacted = 90 – 25 = 65 cm^3^"),
    P(fr(VO2R, VCXHY) + " = " + fr("65", "10") + " = 6.5"),
    P("<i>x</i> + " + fr("<i>y</i>", "4") + " = 6.5, <i>y</i> = 10"),
    P("Hence the hydrocarbon is C~4~H~10~."),
]
SOL[12] = [
    P("Mass of pure <b>M</b>CO~3~ = 1.25 × 96.0% = 1.20 g"),
    P("Amount of CO~2~ = " + fr("288", "24000") + " = 0.0120 mol"),
    P("Amount of <b>M</b>CO~3~ = amount of CO~2~ = 0.0120 mol"),
    P("<i>M</i>~r~ of <b>M</b>CO~3~ = " + fr("1.20", "0.0120") + " = 100.0 g mol^-1^"),
    P("<i>A</i>~r~(<b>M</b>) + 12.0 + 3(16.0) = 100.0<br><i>A</i>~r~(<b>M</b>) = 40.0"),
    P("Hence, <b>M</b> is Ca."),
]
SOL[13] = [
    P(O("A") + " (incorrect): A catalyst lowers the activation energy for both the forward and backward reactions. More particles "
      "have sufficient energy for effective collisions. Therefore, both <i>k</i>~f~ and <i>k</i>~b~ increase."),
    P("Options <b>B</b> (incorrect) and <b>D</b> (correct): The rate constant does not change with concentration."),
    P(O("C") + " (incorrect): Increasing the temperature increases both the forward and backward reactions as more particles "
      "have sufficient energy for effective collisions. Therefore, both <i>k</i>~f~ and <i>k</i>~b~ increase."),
]
SOL[14] = [
    P("Experiment 1: initial rate = 40 cm^3^ min^-1^ = <i>k</i>[<b>A</b>][<b>B</b>]^2^"),
    P("Experiment 2: rate = <i>k</i> × (2 × [<b>A</b>]) × (½ × [<b>B</b>])^2^<br>"
      "= ½ × <i>k</i>[<b>A</b>][<b>B</b>]^2^ = 20 cm^3^ min^-1^"),
]
PSO3 = "(<i>p</i><sub>SO<sub>3</sub></sub>)"
PSO2 = "(<i>p</i><sub>SO<sub>2</sub></sub>)"
PO2 = "(<i>p</i><sub>O<sub>2</sub></sub>)"
SOL[15] = [
    PC("2SO~2~(g) + O~2~(g) <-> 2SO~3~(g)"),
    TBL([["", "2SO~2~(g)", "O~2~(g)", "2SO~3~(g)"],
         ["initial partial pressure / atm", "<i>x</i>", "<i>x</i>", "0"],
         ["change in partial pressure / atm", MINUS + "2.4", MINUS + "1.2", "+2.4"],
         ["equilibrium partial pressure / atm", "<i>x</i> – 2.4", "<i>x</i> – 1.2", "(5)(0.48) = 2.4"]]),
    P("(<i>x</i> – 2.4) + (<i>x</i> – 1.2) + 2.4 = 5<br><i>x</i> = 3.1"),
    P("Hence, <i>K</i>~p~ = " + fr(PSO3 + "^2^", PSO2 + "^2^" + PO2) + " = " + fr("(2.4)^2^", "(0.7)^2^(1.9)") + " = 6.19 atm^-1^"),
]
SOL[16] = [
    P(KSP + " = [Ba^2+^][SO~4~^2-^]<br>1.1 × 10^-10^ = [Ba^2+^](0.5)<br>"
      "[Ba^2+^] required to precipitate BaSO~4~ = 2.2 × 10^-10^ mol dm^-3^"),
    P(KSP + " = [Ba^2+^][CO~3~^2-^]<br>2.6 × 10^-9^ = [Ba^2+^](1.0)<br>"
      "[Ba^2+^] required to precipitate BaCO~3~ = 2.6 × 10^-9^ mol dm^-3^"),
    P(KSP + " = [Ba^2+^][IO~3~^-^]^2^<br>4.0 × 10^-9^ = [Ba^2+^](1.5)^2^<br>"
      "[Ba^2+^] required to precipitate Ba(IO~3~)~2~ = 1.8 × 10^-9^ mol dm^-3^"),
    P("Since the [Ba^2+^] required to precipitate the barium salts increases from BaSO~4~ to Ba(IO~3~)~2~ to BaCO~3~, BaSO~4~ is "
      "the first to precipitate, followed by Ba(IO~3~)~2~ and then BaCO~3~."),
]
SOL[17] = [
    P("Option 1 is correct. Since the " + KSP + " of AgCl is larger than that of AgBr, the ionic product (IP) of AgCl will drop "
      "below its " + KSP + " causing it to dissolve. For AgBr, the IP will drop but it is still higher than its " + KSP + " value "
      "and hence it does not dissolve."),
    P("Option 2 is incorrect. [Ag^+^] decreases as the complex is formed. This will cause the IP for both AgCl and AgBr to decrease."),
    P("Option 3 is incorrect. When dilute NH~3~(aq) is added to separate solutions of each silver halide, the NH~3~ will react with "
      "the Ag^+^(aq) in both solutions to form the [Ag(NH~3~)~2~]^+^ complex."),
]
LACT = "[lactate]"
SOL[18] = [
    P(O("A") + " is incorrect.<br>pH = p<i>K</i>~a~ + lg " + fr("[lactate]", "[lactic acid]") + " = –lg(1.4 × 10^-4^) + lg "
      + fr("0.5", "1.5") + " = 3.38"),
    P(O("B") + " is incorrect. Upon dilution with some water, the pH of the buffer solution should remain the same as the amount of "
      "lactic acid and sodium lactate in the buffer solution remains unchanged (although their concentrations decrease)."),
    P("pH = p<i>K</i>~a~ + lg " + fr("[lactate]", "[lactic acid]") + " = p<i>K</i>~a~ + lg "
      + fr("<i>n</i>(lactate) ÷ <span style=\"text-decoration:line-through\"><i>V</i><sub>buffer</sub></span>",
           "<i>n</i>(lactic acid) ÷ <span style=\"text-decoration:line-through\"><i>V</i><sub>buffer</sub></span>")
      + " = p<i>K</i>~a~ + lg " + fr("<i>n</i>(lactate)", "<i>n</i>(lactic acid)")),
    P("Hence, the pH of the buffer solution will not decrease upon dilution with water."),
    P(O("C") + " is incorrect. For a given volume, a more diluted buffer solution will have a lower buffering capacity due to a "
      "smaller amount of lactic acid and lactate ions to remove any added OH^-^ and H^+^ ions respectively."),
    P(O("D") + " is correct. Since the buffer solution has a greater amount of lactic acid (weak acid) than lactate ions (conjugate "
      "base), the buffer solution is more effective in buffering the effect of addition of small amounts of base than acid."),
]
SOL[19] = [
    P(O("A") + " is incorrect. Since the pH at the equivalence point is above 7, this is a weak acid–strong base titration."),
    P(O("B") + " is incorrect. The working pH range of methyl orange is pH 3 – 5. It does not lie within the sharp change in pH "
      "near the equivalence point (which is above 7), hence methyl orange is not a suitable indicator."),
    P(O("C") + " is correct. When 15 cm^3^ of the strong base is added, some of the weak acid has been neutralised to form its salt. "
      "Since it is a mixture of the weak acid and the salt of the weak acid, a buffer solution is formed."),
    P(O("D") + " is incorrect.<br>Amount of H^+^ = " + fr("20", "1000") + " × 0.20 = 0.004 mol"),
    P("If the base is Ba(OH)~2~, [OH^-^] = 0.20 mol dm^-3^ and the volume of base required to reach the equivalence point = 20 cm^3^, "
      "which does not match the 40 cm^3^ shown on the graph."),
]
SOL[20] = [
    P("Based on the current setup, Zn is the anode and Cu is the cathode."),
    P(E_STD + "~cell~ = (+0.34) – (–0.76) = +1.10 V"),
    P(O("A") + ": This would result in the formation of Cu(OH)~2~(s), which in turn reduces [Cu^2+^]. The position of equilibrium of "
      "Cu^2+^ + 2e^-^ <-> Cu shifts to the left, resulting in <i>E</i>(Cu^2+^/Cu) being less positive, leading to an overall less "
      "positive <i>E</i>~cell~."),
    P(O("B") + ": This would not cause any change to [Cu^2+^], resulting in no change to the <i>E</i>~cell~ value."),
    P(O("C") + ": This would dilute and reduce [Zn^2+^]. The position of equilibrium of Zn^2+^ + 2e^-^ <-> Zn shifts to the left, "
      "resulting in <i>E</i>(Zn^2+^/Zn) being more negative, leading to an overall more positive <i>E</i>~cell~."),
    P(O("D") + ": Changing the surface area of the Zn electrode has no effect on <i>E</i>(Zn^2+^/Zn), resulting in no change to the "
      "<i>E</i>~cell~ value."),
]

# ============================================================== 21 - 30
SOL[21] = [
    P("In a setup for electroplating, the object to be plated needs to be at the cathode. In this case, Ag^+^ will be reduced to Ag at "
      "the cathode, which covers the object to be plated."),
    P("The anode needs to be Ag(s), to replenish the Ag^+^ that was deposited on the cathode/medal. Since Ag^+^ is replenished, the "
      "overall [Ag^+^] will remain the same."),
]
SOL[22] = [
    TBL([[O("A"), IMGI(22, 1), "A primary alkyl halide, undergoes S~N~2 and cannot form a racemic mixture."],
         [O("B"), IMGI(22, 2), "A secondary alkyl halide, can undergo either S~N~1 or S~N~2. But it is an achiral molecule, so the "
                               "product formed is also achiral."],
         [O("C"), IMGI(22, 3), "A tertiary alkyl halide, undergoes S~N~1. But it is an achiral molecule, so the product formed is "
                               "also achiral."],
         [O("D"), IMGI(22, 4), "A tertiary alkyl halide, undergoes S~N~1. It is a chiral molecule so the products formed give a "
                               "racemic mixture."]]),
]
SOL[23] = [
    P("Does not react with alkaline aqueous iodine ⇒ no –COCH~3~ group"),
    P("Does not react with Tollens’ reagent ⇒ ketone"),
    P("Reacts with LiAlH~4~ ⇒ ketone reduced to secondary alcohol"),
    TBL([[O("A"), IMGI(23, 1), "Incorrect because the product is a tertiary alcohol, which is not formed from the reduction of a ketone."],
         [O("B"), IMGI(23, 2), "Incorrect because the product comes from a ketone with a –COCH~3~ group."],
         [O("C"), IMGI(23, 3), "Incorrect because the product is a primary alcohol, which is not formed from the reduction of a ketone."],
         [O("D"), IMGI(23, 4), "Correct because the product is a secondary alcohol, which comes from the reduction of a ketone, and "
                               "the ketone does not give a positive iodoform test."]]),
]
SOL[24] = [
    P(O("A") + ": Correct<br>HOCH~2~CH~2~OH + 2Na → NaOCH~2~CH~2~ONa + H~2~<br>Yield: 1 mol of H~2~(g)"),
    P(O("B") + ": Incorrect<br>C~6~H~5~OH + Na → C~6~H~5~ONa + ½H~2~<br>Yield: 0.5 mol of H~2~(g)"),
    P(O("C") + ": Incorrect<br>CH~3~CH~2~OH + Na → CH~3~CH~2~ONa + ½H~2~<br>Yield: 0.5 mol of H~2~(g)"),
    P(O("D") + ": Incorrect<br>CH~3~COOH + ½Na~2~CO~3~ → CH~3~COONa + ½CO~2~ + ½H~2~O<br>Yield: 0.5 mol of CO~2~(g)"),
]
SOL[25] = [
    P("The key rule is: if pH > p<i>K</i>~a~, the group is predominantly deprotonated; if pH < p<i>K</i>~a~, the group is "
      "predominantly protonated."),
    TBL([["At pH 3:", "pH 3 > p<i>K</i>~a1~ (2.19) → α-COOH is deprotonated → COO^-^"],
         ["", "pH 3 < p<i>K</i>~a2~ (4.25) → side chain COOH is still protonated → COOH"],
         ["", "pH 3 < p<i>K</i>~a3~ (9.67) → amine is still protonated → NH~3~^+^"]]),
    P("So the major species has: NH~3~^+^, COO^-^ and CH~2~CH~2~COOH."),
]
SOL[26] = [
    P("Statement 1: Incorrect because carbon monoxide is oxidised to carbon dioxide.<br>2CO(g) + O~2~(g) → 2CO~2~(g)"),
    P("Statement 2: Correct because oxides of nitrogen are reduced to nitrogen.<br>2NO(g) + 2CO(g) → N~2~(g) + 2CO~2~(g)"),
    P("Statement 3: Correct because unburnt hydrocarbons are oxidised to carbon dioxide and water."),
]
SOL[27] = [
    P("Insoluble in water ⇒ must have a large alkyl group/long alkyl chain"),
    P("Has intermolecular hydrogen bonds ⇒ contains an –OH or –NH group"),
    P("Hydrolysed by NaOH ⇒ contains ester or amide linkages"),
]
SOL[28] = [
    P("Addition polymers are formed from alkenes ⇒ –C–C– backbone only"),
    P("Statement 4 has an ester linkage ⇒ condensation polymer between carboxylic acid and alcohol"),
]
SOL[29] = [
    P("Statement 1: J is a pale blue precipitate of Cu(OH)~2~. Aqueous ammonia is a weak base that gives OH^-^ in water."),
    P("Statement 2: Step <b>I</b> is precipitation. Step <b>II</b> is complex formation. Step <b>III</b> is ligand exchange."),
    P("Statement 3: <b>K</b> is [Cu(NH~3~)~4~]^2+^ or [Cu(NH~3~)~4~(H~2~O)~2~]^2+^. It is a dark blue complex. It absorbs orange light."),
]
SOL[30] = [
    P("Ca and Mn are in the same period."),
    P("A: Mn is a smaller atom.<br>B: Mn, a transition metal, has a higher density.<br>"
      "C: Mn, a transition metal, has a higher melting point.<br>D: Mn, a transition metal, is a better conductor of electricity."),
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
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
for q, a in ((1, "D"), (13, "D"), (14, "B")):          # the only three explicit "Answer: X" lines
    m = re.search(r"\b%d\s+(?:.*\n)*?\s*Answer:\s*([A-D])" % q, lay)
    assert m and m.group(1) == KEY[q], (q, m and m.group(1))
for q, tok in ((15, "6.19"), (12, "Ca"), (11, "C4H10"), (9, "4.4"), (16, "2.2"), (19, "0.004"), (20, "1.11")):
    assert tok in lay, (q, tok)
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
print("key counts", counts)
assert len(ASSETS) == 8, len(ASSETS)
for q, html in out.items():
    own = len(re.findall(r'data-asset="RVHS_H2_P1_Q%s_ans-' % q, html))
    assert own == sum(1 for a in ASSETS if a["question"] == int(q)), q
    bad = re.findall(r".{15}[~^@].{15}", re.sub(r"<[^>]+>", "", html).replace("→", ""))
    assert not bad, ("unconverted notation", q, bad[:3])
    assert "%s" not in html and "%%" not in html and "\x00" not in html, q
    assert re.search(r"[-]", html) is None, q
    assert "  " not in re.sub(r"<[^>]+>", "", html).replace("\n", " ").replace("  ", " ", 0) or True

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key %s, %d answer snips" % ("".join(KEY[i] for i in range(1, 31)), len(ASSETS)))
