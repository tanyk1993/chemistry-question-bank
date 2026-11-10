"""NJC 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: the school's answers file exists only as a PDF (the docx formatting is off):
the question paper with each solution typed in blue under its question, MathType
fractions, a printed answer-key table on the last page.  There is no docx to parse, so
the solutions are typed here (house markup: div.worked-solution > p > span.ans, .frac,
table.cmp, img.ws-fig) and CHECKED against the PDF: the key printed on the last page,
the 30 'Ans: X' lines, and the diagrams' file names.

Run:  python3 -m ingest.build_njc26_p1_answers <answers.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

The school's wording is kept verbatim (editorial rulings are applied in TYPO_FIXES, which
is empty until the user rules).  Not typed: the 10 diagram snips (answer_assets.json).
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

KEY = dict(enumerate("CCCDDBADCB" "ACDDABCBCC" "AABBDDCABA", 1))
MINUS, TIMES, DELTA = "−", "×", "∆"

# --------------------------------------------------------------------- markup
def fx(s):
    """mini-notation -> html:  H~2~O  x^2+^  ->  ->  <->  @H  (l) Cl Al"""
    s = re.sub(r"~([^~]*)~", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([^^]*)\^", lambda m: "<sup>%s</sup>" % m.group(1).replace("-", MINUS), s)
    s = s.replace("<->", "⇌").replace("->", "→").replace("@", DELTA)
    s = s.replace("(l)", '(<i class="el">l</i>)')
    s = re.sub(r"Cl(?![a-z])", 'C<i class="el">l</i>', s)
    s = re.sub(r"(?<![A-Za-z])Al(?![a-z])", 'A<i class="el">l</i>', s)
    return s


def fr(n, d):
    return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (fx(n), fx(d))


def P(s):
    return '<p><span class="ans">%s</span></p>' % fx(s)


def PC(s):
    return '<p class="c"><span class="ans">%s</span></p>' % fx(s)


def UL(items):
    return '<ul class="stmts">%s</ul>' % "".join('<li><span class="ans">%s</span></li>' % fx(i) for i in items)


def TBL(rows):
    return '<table class="cmp">%s</table>' % "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % fx(c) for c in r) for r in rows)


def IMG(q, k):
    path = "NJC_H2_1_Q%d_ans-%d_2026.png" % (q, k)
    ASSETS.append({"question": q, "slot": "ans-%d" % k, "path": path,
                   "offset": 1 + sum(1 for a in ASSETS if a["question"] == q)})
    return '<img class="ws-fig" data-asset="%s" alt="">' % path


def over_arrow(top, width=3.2):
    """a forward arrow of chosen length with a label above it (inline styles: no CSS needed)"""
    return ('<span style="display:inline-block;vertical-align:middle;text-align:center;line-height:1.1;padding:0 .2em">'
            '<span style="display:block;font-size:.72em;line-height:1.15">%s</span>'
            '<span style="display:flex;align-items:center;width:%sem;margin:0 auto">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.55em;margin-left:-.3em;line-height:1">►</span></span>'
            '<span style="display:block;font-size:.72em;line-height:1.15">&nbsp;</span></span>' % (top, width))


# the standard-state sign: .stk is only styled inside .stem, so (as MI 2026 P3) inline styles
STD = '<span class="pl-sym">⦵</span>'
E_STD = '<i>E</i>' + STD
E_CELL = ('<i>E</i><span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;'
          'line-height:1;font-size:.72em;text-align:left;margin-left:.08em">'
          '<span style="display:block">' + STD + '</span><span style="display:block">cell</span></span>')


def kk(n):          # k with subscript
    return "<i>k</i>~%s~" % n


def KK(n):
    return "<i>K</i>~%s~" % n


ASSETS = []
SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P("Relative atomic mass = " + fr("(46 %s 11.2) + (47 %s 10.1) + (48 %s 100) + (49 %s 7.3) + (50 %s 7)" % ((TIMES,) * 5),
                                     "11.2 + 10.1 + 100 + 7.3 + 7.0")),
    P("= " + fr("515.2 + 474.7 + 4800 + 357.7 + 350", "135.6")),
    P("= " + fr("6497.3", "135.6") + " = 47.92"),
]
SOL[2] = [
    P("Given that <i>n</i> and <i>R</i> are constant (<i>n</i> is constant because the gas did not react),"),
    P(fr("<i>P</i>~1~<i>V</i>~1~", "<i>T</i>~1~") + " = " + fr("<i>P</i>~2~<i>V</i>~2~", "<i>T</i>~2~")
      + " Temperature must be in K when using this formula."),
    PC(fr("(16)<i>V</i>~1~", "300") + " = " + fr("(40)" + fr("1", "2") + "<i>V</i>~1~", "<i>T</i>~2~")),
    PC("<i>T</i>~2~ = 375 K = <b><u>102 °C</u></b>"),
]
SOL[3] = [
    P("Mol ratio of O~2~ = " + fr("150", "500") + " = 0.3<br>"
      "Hence amt of O~2~ = 0.3 %s 1.2 = 0.36 mol<br>"
      "Amt of N~2~ = " % TIMES + fr("5.76", "24") + " = 0.24 mol<br>"
      "Hence amt of Ar = 1.2 %s 0.36 %s 0.24 = 0.6 mol" % (MINUS, MINUS)),
    P("Thus <i>p</i>~Ar~ = " + fr("0.6", "1.2") + " %s 500 = <b><u>250 kPa</u></b>" % TIMES),
]
SOL[4] = [
    P("Recall that real gases would deviate from ideal behaviour at high pressures and low temperatures."),
    P("<i>Real gas tends towards ideal gas behaviour when the intermolecular forces are negligible and the volume of "
      "the gas particles is negligible to the volume of the vessel.</i>"),
    TBL([
        ["Option", "Explanation"],
        ["A", "For the same gas, it will deviate less at higher temperature since the molecules have more kinetic energy "
              "to overcome the intermolecular permanent dipole-permanent dipole (pd-pd) interactions."],
        ["B", "CH~4~ is a non-polar molecule with only weak intermolecular <i>instantaneous dipole induced dipole (id-id)</i>. "
              "CH~4~ will also deviate less at higher temperature since the molecules have more kinetic energy to overcome "
              "the intermolecular forces."],
        ["C", "O~2~ is a non-polar molecule with only weak intermolecular <i>id-id</i>, hence should deviate less from ideal "
              "behaviour than HCl."],
        ["D", "HF is a polar molecule with stronger <i>intermolecular</i> hydrogen bonding interactions than the "
              "<i>intermolecular pd-pd</i> of HCl. Hence HF deviates more from ideal behaviour than HCl at the same "
              "temperature of 300 K."],
    ]),
]
SOL[5] = [
    TBL([
        ["", "", "electron pairs", "unpaired electrons"],
        ["Be", "1s^2^ 2s^2^", "1", "0"],
        ["C", "1s^2^ 2s^2^ 2p^2^", "1", "2"],
        ["N", "1s^2^ 2s^2^ 2p^3^", "1", "3"],
        ["<b>O</b>", "<b>1s^2^ 2s^2^ 2p^4^</b>", "<b>2</b>", "<b>2</b>"],
    ]),
]
SOL[6] = [
    TBL([
        ["", "molecule", "molecular shape", "polarity"],
        ["A", "BrF~3~", "T-shaped", "polar"],
        ["B", "PCl~3~", "trigonal pyramidal", "polar"],
        ["C", "SCl~2~", "bent", "polar"],
        ["D", "CHF~3~", "tetrahedral", "polar"],
    ]),
]
SOL[7] = [
    P("Refer to diagram below (* represents sp^2^ C while • represents sp^3^ C)."),
    P("There are <b><u>one sp C</u></b>, <b><u>three sp^2^ C</u></b> and <b><u>eight sp^3^ C</u></b>."),
    "<p>%s</p>" % IMG(7, 1),
]
SOL[8] = [
    P("<b>A: different</b>"),
    UL(["Al: metallic bonds between cations and sea of delocalized electrons",
        "P: weak id-id between P~4~ molecules, strong covalent bonds between atoms within the molecule"]),
    P("<b>B: different</b>"),
    UL(["Cl: weak id-id between Cl~2~ molecules, strong covalent bonds between atoms within the molecule",
        "Ar: weak id-id between individual atoms"]),
    P("<b>C: different</b>"),
    UL(["Mg: strong metallic bonds between cations and sea of delocalized electrons",
        "Si: strong covalent bonds between Si atoms (giant covalent lattice)"]),
    P("<b>D: same</b>"),
    UL(["S: weak id-id between S~8~ molecules, strong covalent bonds between atoms within the molecule",
        "Cl: weak id-id between Cl~2~ molecules, strong covalent bonds between atoms within the molecule"]),
]
SOL[9] = [
    P("Both H~2~SO~4~ and NaOH are strong acid and strong base, fully dissociated in water to give H^+^ and OH^-^ respectively."),
    P("Reaction is between H^+^ and OH^-^ ions: H^+^ + OH^-^ -> H~2~O"),
    P("Expt 1: Amt of OH^-^ = " + fr("25", "1000") + " %s 1.0 = 0.025 mol<br>" % TIMES
      + "&emsp;&emsp;&emsp;Amt of H^+^ = " + fr("25", "1000") + " %s 0.5 %s 2 = 0.025 mol = Amt of H~2~O formed" % (TIMES, TIMES)),
    P("Expt 2: Amt of OH^-^ = " + fr("50", "1000") + " %s 0.5 = 0.025 mol<br>" % TIMES
      + "&emsp;&emsp;&emsp;Amt of H^+^ = " + fr("25", "1000") + " %s 0.25 %s 2 = 0.025 mol = Amt of H~2~O formed" % (TIMES, TIMES)),
    P("No. of moles of H~2~O formed from the neutralisation reaction of both experiments are the same (0.025 mol)."),
    P("Thus the heat evolved for both experiments are the same (same <i>q</i>)."),
    P("However, since the total volume is doubled for the 2^nd^ experiment, the @T is halved, i.e. 3.5 °C."),
    PC("<i>q</i>~1~ = <i>q</i>~2~"),
    PC("<i>m</i>~1~<i>c</i>@<i>T</i>~1~ = <i>m</i>~2~<i>c</i>@<i>T</i>~2~"),
    PC(fr("@<i>T</i>~2~", "@<i>T</i>~1~") + " = " + fr("<i>m</i>~1~", "<i>m</i>~2~")),
    PC(fr("@<i>T</i>~2~", "7") + " = " + fr("50", "100")),
    PC("@<i>T</i>~2~ = 3.5 °C"),
]
SOL[10] = [
    P("Combustion reaction is exothermic, ∴ @H < 0."),
    P("@S > 0 since there is increase in number of gas particles upon reaction."),
    P("i.e. 2 mol of gas products from ½ mol of gas reactant."),
    P("Since @G = @H %s T@S and @H < 0 and @S > 0," % MINUS),
    P("@G < 0 for all temperatures as the physical states of (COOH)~2~(l) and H~2~O(l) remain unchanged with increasing "
      "temperatures (as stated in Question “before the boiling point of water”)."),
    P("@G = @H %s T@S → @G = %s@S <i>T</i> + @H" % (MINUS, MINUS)),
    PC("<i>y</i> = <i>mx</i> + <i>c</i>"),
    P("hence gradient = %s@S = negative (since @S > 0)" % MINUS),
    P("y-intercept, <i>c</i> = @H = negative value (since @H < 0)"),
]

# ============================================================== 11 - 20
SOL[11] = [
    P("Statement 1 is correct: @H is positive for thermal decomposition reaction. So the reaction is endothermic."),
    P("Statement 2 is correct: A solid decomposes to form a solid and a gas, so the number of gaseous moles increases "
      "from 0 to 1, increasing disorder (@S > 0)."),
    P("Statement 3 is correct: Using @G = @H %s T@S, since @H > 0 and @S > 0, increasing T makes T@S larger, making @G "
      "more negative, so the reaction becomes more feasible at higher temperatures." % MINUS),
]
IS = "[IS~2~O~8~]^3-^"
S2 = "S~2~O~8~^2-^"
SOL[12] = [
    P("<b>A: Incorrect</b>"),
    UL(["Slow Step (Step 2): Rate = " + kk(2) + "[I~2~Cl~2~][H~2~]",
        "Pre-equilibrium (Step 1): " + KK(1) + " = " + fr("[I~2~Cl~2~]", "[ICl]^2^") + " ⇒ [I~2~Cl~2~] = " + KK(1) + "[ICl]^2^"]),
    PC("Rate = <i>k</i>[ICl]^2^[H~2~]"),
    P("<b>B: Incorrect</b>"),
    UL(["Slow Step (Step 2): Rate = " + kk(2) + "[N][NO]",
        "Pre-equilibrium (Step 1): " + KK(1) + " = " + fr("[N][H~2~O]", "[NO][H~2~]") + " ⇒ [N] = " + KK(1) + " "
        + fr("[NO][H~2~]", "[H~2~O]")]),
    PC("Rate = <i>k</i> " + fr("[NO]^2^[H~2~]", "[H~2~O]")),
    P("<b>C: Correct</b>"),
    UL(["Slow Step (Step 2): Rate = " + kk(2) + "[" + IS + "]",
        "Pre-Equilibrium Expression from Step 1:"]),
    PC(KK(1) + " = " + fr("[" + IS + "]", "[" + S2 + "][I^-^]") + " ⇒ [" + IS + "] = " + KK(1) + "[" + S2 + "][I^-^]"),
    UL(["Substituting into the Rate Law:"]),
    PC("<b>Rate = " + kk(2) + KK(1) + "[" + S2 + "][I^-^] = <i>k</i>[" + S2 + "][I^-^]</b>"),
    P("<b>D: Incorrect</b>"),
    UL(["Slow Step (Step 2): Rate = " + kk(2) + "[NO~2~CO][NO]"]),
    UL(["Pre-equilibrium (Step 1):"]),
    PC(KK(1) + " = " + fr("[NO~2~CO]", "[NO~2~][CO]") + " ⇒ [NO~2~CO] = " + KK(1) + "[NO~2~][CO]"),
    UL(["Substitute intermediate back into the rate law:"]),
    PC("Rate = " + kk(2) + "(" + KK(1) + "[NO~2~][CO])[NO]<br>Rate = <i>k</i>[NO~2~][CO][NO]"),
]
SOL[13] = [
    P("Option 1 is correct."),
    P("The general rate equation is given as: rate = <i>k</i>[SO~2~Cl~2~]<sup><i>m</i></sup>"),
    PC(fr("rate~2~", "rate~1~") + " = (" + fr("[SO~2~Cl~2~]~2~", "[SO~2~Cl~2~]~1~") + ")<sup><i>m</i></sup>"),
    PC(fr("4.40 %s 10^-3^" % TIMES, "2.84 %s 10^-3^" % TIMES) + " = (" + fr("0.333", "0.215") + ")<sup><i>m</i></sup>"),
    PC("1.549 = (1.549)<sup><i>m</i></sup>"),
    PC("<i>m</i> = 1 (first order wrt SO~2~Cl~2~)"),
    P("Option 2 is correct."),
    P("Since rate = <i>k</i>[SO~2~Cl~2~]"),
    P("<i>Using the data from expt 1:</i> &emsp;2.84 %s 10^-3^ = <i>k</i>(0.215)" % TIMES),
    PC("<i>k</i> = " + fr("2.84%s10^-3^" % TIMES, "0.215") + " = 1.321 %s 10^-2^ min^-1^" % TIMES),
    P("For a first-order reaction, the half-life is given by:"),
    PC("<i>t</i>~½~ = " + fr("ln 2", "<i>k</i>") + " = " + fr("0.693", "1.321%s10^-2^" % TIMES) + " = 52.5 min (3 s.f.)"),
    P("Option 3 is correct."),
    PC("number of half-life, <i>n</i> = " + fr("total time", "<i>t</i>~½~") + " = " + fr("105", "52.5") + " = 2"),
    PC("For a first-order decay, " + fr("[SO~2~Cl~2~]~<i>t</i>~", "[SO~2~Cl~2~]~0~") + " = (" + fr("1", "2") + ")<sup><i>n</i></sup>"),
    P("Note: [ ]~0~ refers to the initial concentration<br>&emsp;&emsp;&emsp;[ ]~<i>t</i>~ refers to the concentration remaining "
      "after time, <i>t</i>, has passed."),
    P("Substituting the initial concentration (0.333 mol dm^-3^) and <i>n</i> = 2:"),
    PC("[SO~2~Cl~2~]~<i>t</i>~ = 0.333 %s (" % TIMES + fr("1", "2") + ")^2^ = 0.333 %s " % TIMES + fr("1", "4")
       + " = <b>0.0833</b> mol dm^-3^ (3 s.f.)"),
    P("Or"),
    PC("0.333 " + over_arrow("1 <i>t</i>~½~".replace("~½~", "<sub>½</sub>"))
       + " 0.1665 " + over_arrow("2 <i>t</i><sub>½</sub>") + " 0.08325"),
]
SOL[14] = [
    P("<b>A:</b> True."),
    PC(KK("c").replace("<sub>c</sub>", "<sub>c</sub>") + " = 1000 = "
       + fr("[Co(SCN)~4~]^2-^", "[Co(H~2~O)~6~]^2+^[SCN^-^]^4^") + " = " + fr("10 / 0.11", "(1 / 0.11) [SCN^-^]^4^")),
    PC("∴ [SCN^-^] = 0.316 mol dm^-3^"),
    P("<b>B:</b> True. <i>K</i>~c~ >>> 1, hence formation of products is favoured. The forward reaction is spontaneous."),
    P("<b>C:</b> True. <i>K</i>~c~ = " + fr("[Co(SCN)~4~]^2-^", "[Co(H~2~O)~6~]^2+^[SCN^-^]^4^")
      + " (mol dm^-3^)^-4^ → mol^-4^ dm^12^"),
    P("<b>D:</b> False. By Le Chatelier’s Principle, dilution of the reaction mixture causes the position of equilibrium "
      "to shift to the left as there is a decrease in the concentration of aqueous ions, <b><u>NOT due</u></b> to the change in "
      "concentration of water. Concentration of water is a constant in aqueous environment. Since there is more mol of aq ions "
      "on the left, position of equilibrium will shift left to partially offset the decrease in conc of aq ions."),
]
SOL[15] = [
    P("For pure D~2~O, [D~3~O^+^] = [OD^-^] due to 1:1 stoichiometry."),
    P("<i>K</i>~d~ = [D~3~O^+^]^2^ = 1.35 %s 10^-15^" % TIMES),
    P("[D~3~O^+^] = " + '<span class="sqrt"><span class="rad">1.35 %s 10<sup>%s15</sup></span></span>' % (TIMES, MINUS)
      + " = 3.67 %s 10^-8^ mol dm^-3^" % TIMES),
    P("pD = %s lg(3.67 %s 10^-8^) = 7.435 ≈ 7.43" % (MINUS, TIMES)),
    P("<b>A is correct:</b> The pD is 7.43."),
    P("<b>B is incorrect:</b> A solution is neutral when [D~3~O^+^] = [OD^-^]. Neutrality does not require a fixed value of 7.00."),
    P("<b>C is incorrect:</b> <i>K</i>~d~ is an equilibrium constant and depends <b>only</b> on temperature."),
    P("<b>D is incorrect:</b> [H~3~O^+^] in pure H~2~O is 1.0 %s 10^-7^ mol dm^-3^, which is larger than 3.67 %s 10^-8^ mol dm^-3^."
      % (TIMES, TIMES)),
]
SOL[16] = [
    P("<b>Option 1:</b> Correct<br>As reaction is endothermic (@H > 0), by Le Chatelier’s Principle, increasing the "
      "temperature shifts the equilibrium to the right to absorb the added heat.<br>This directly increases the concentrations of "
      "the charge-carrying ions, [NH~4~^+^] and [NH~2~^-^]. More ions per unit volume means a higher capacity to carry an "
      "electric current."),
    P("<b>Option 2:</b> Correct<br>One molecule NH~3~ is acting as an acid, its conjugate base differs by 1 proton, NH~2~^-^."),
    P("<b>As a Lewis Base (Electron pair donor):</b> The second NH~3~ molecule donates its electron pair to a proton (H^+^), "
      "becoming ammonium ion, NH~4~^+^."),
    P("<b>Option 3:</b> Incorrect"),
    UL(["NH~4~^+^ has 4 bond pairs, 0 lone pairs → perfect tetrahedral angle (109.5°).",
        "NH~3~ has 3 bond pairs, 1 lone pair → trigonal pyramidal (≈ 107°).",
        "NH~2~^-^ has 2 bond pairs, 2 lone pairs → bent shape (≈ 104.5°)."]),
    P("Therefore, the bond angle order is NH~4~^+^ (109.5°) > NH~3~ (107°) > NH~2~^-^ (104.5°)."),
]
SOL[17] = [
    P("<b>Statement 1: False</b>"),
    P("<b>The high concentration of H^+^ ions (pH 1.0 ⇒ [H^+^] = 0.1 mol dm^-3^) suppresses dissociation, it does not "
      "catalyse it.</b>"),
    P("Stomach acid contains a <u>high concentration of H^+^ ions</u> (pH 1.0 ⇒ [H^+^] = 0.1 mol dm^-3^) and according to "
      "Le Chatelier\u2019s Principle, this shifts the <u>equilibrium position to the left</u>:"),
    PC("HA(aq) <-> H^+^(aq) + A^-^(aq)"),
    P("This suppresses the dissociation of aspirin, causing it to remain almost entirely in its un-ionised form (HA)."),
    P("<b>Statement 2 and 3: correct for the above reason of eqm shift.</b>"),
]
SOL[18] = [
    P("Ca(OH)~2~(s) <-> Ca^2+^(aq) + 2OH^-^(aq)<br>"
      "Statement 1 is correct: <i>K</i>~sp~ = [Ca^2+^][OH^-^]^2^ = (s)(2s)^2^ = 4s^3^ = 5.5 %s 10^-6^<br>"
      "→ s = (5.5 %s 10^-6^ / 4)<sup>⅓</sup> = 0.011 mol dm^-3^." % (TIMES, TIMES)),
    P("Statement 2 is correct: Decreasing pH means adding H^+^ ions, which react with OH^-^ ions (neutralisation), shifting "
      "the equilibrium to the right and increasing solubility."),
    P("Statement 3 is incorrect: Adding CaCl~2~ introduces a common ion (Ca^2+^), which decreases the solubility of Ca(OH)~2~ "
      "(common ion effect) but it does not change the solubility product. Solubility product is only affected by change in "
      "temperature."),
]
SOL[19] = [
    UL(["<b>Silicon (Si)</b> and <b>Germanium (Ge)</b>: SiO~2~ is acidic (it reacts with bases), but it is insoluble in water.",
        "<b>Phosphorus (P)</b> and <b>Arsenic (As)</b>: Phosphorus oxides (like P~4~O~10~) dissolve in water to form H~3~PO~4~, "
        "giving an acidic solution.",
        "<b>Sulfur (S)</b> and <b>Selenium (Se)</b>: Sulfur oxides (like SO~2~ and SO~3~) dissolve in water to form H~2~SO~3~ "
        "and H~2~SO~4~."]),
]
SOL[20] = [
    P("As the number of electrons or size of electron cloud increases, the electron cloud gets more polarised, id-id forces "
      "increase down the group. More energy required to overcome id-id forces. Boiling point increases and hence @H~vap~ "
      "increases down the group."),
    P("Halogens have simple molecular structure with weak instantaneous dipole-induced dipole forces (id-id) between "
      "molecules. Enthalpy change of vaporisation is proportional to boiling point."),
    P("Thermal stability of HX <u>decreases</u> down group 17 due to <u>decreasing</u> bond strength of H–X "
      "(<u>increasing</u> H–X bond length)"),
    TBL([
        ["<b>Electrode reaction</b>", "<b>" + E_STD + " / V</b>"],
        ["F~2~ + 2e^-^ <-> 2F^-^", "+2.87"],
        ["Cl~2~ + 2e^-^ <-> 2Cl^-^", "+1.36"],
        ["Br~2~ + 2e^-^ <-> 2Br^-^", "+1.07"],
        ["I~2~ + 2e^-^ <-> 2I^-^", "+0.54"],
    ]),
    P(E_STD + "(X~2~|X^-^) becomes less positive down the group, oxidising power of elements <u>decreases</u> down the group."),
]

# ============================================================== 21 - 30
SOL[21] = [
    P("Option 1 is correct as shown."),
    "<p>%s</p>" % IMG(21, 1),
    P("Option 2 is wrong because C=C is within a ring and therefore, the trans isomer will experience ring strain. Hence, "
      "there is no cis-trans isomerism."),
    P("Option 3 is wrong because the lone pair of electrons on O will delocalise towards C=C, resulting in C-OH to have "
      "partial double character, making it harder to break. As such, there is no nucleophilic substitution with PCl~5~."),
    P("Option 4 is wrong because one mole of OH group produces ½ mole of H~2~ only with excess Na."),
]
SOL[22] = [
    P("<b>Explanation:</b>"),
    UL(["Reacts with sodium → contains <b>alcohol</b> (OH) group.",
        "Reacts with Fehling’s → contains <b>aldehyde</b> (CHO) group.",
        "Does not decolourise bromine water → no C=C bonds.",
        "Molecular formula C~4~H~8~O~3~ (must contain 3 oxygen atoms):"]),
    P("A: CH~2~(OH)CH~2~CH(OH)CHO→ C~4~H~8~O~3~ (3 O atoms: one aldehyde, two alcohol groups) ✓"),
    P("B: HOCH~2~CH~2~COCH~2~OH → C~4~H~8~O~3~ (one ketone, two alcohol groups) ✗"),
    P("C: CH~3~CH(OH)CH~2~COOH → C~4~H~8~O~3~ but contains COOH (reacts with Na~2~CO~3~, not specifically sodium) and no "
      "aldehyde ✗"),
    P("D: CH~3~CO~2~CH~2~CH~2~OH → C~4~H~8~O~3~ ester and no aldehyde ✗"),
    P("<b>Therefore, only A is correct.</b>"),
]
SOL[23] = [
    P("It is an addition polymer so each monomer must contain a C=C bond."),
    "<p>%s</p>" % IMG(23, 1),
]
SOL[24] = [
    P("Reaction pathway shows 2 humps, hence a 2-step mechanism.<br>The first hump has a higher E~a~, i.e. first step is slow step."),
    fx('<table class="cmp">'
    '<tr><td><b>A</b></td><td><b>Nucleophilic addition</b> (2 steps mechanism)<br>%s</td></tr>'
    '<tr><td><b>B</b></td><td><b>S~N~2</b> (1 step mechanism)<br>%s</td></tr>'
    '<tr><td><b>C</b></td><td><b>S~N~1</b> (2 steps mechanism)<br>%s</td></tr>'
    '<tr><td><b>D</b></td><td><b>Electrophilic Addition</b> (2 steps mechanism)<br>%s</td></tr></table>'
    % tuple(IMG(24, k) for k in (1, 2, 3, 4))),
]
SOL[25] = [
    P("Option A: 2-chloro-2-methylbutanol, a tertiary halogenoalkane, undergoes S~N~1 nucleophilic substitution. C–Cl bond "
      "undergoes heterolytic fission forming a carbocation which is trigonal planar in shape. The nucleophile OH^-^ can attack "
      "from the top or bottom of the plane with equal probability, forming a racemic mixture"),
    P("Option B: A racemic mixture is formed as the reactive carbonyl C in propanal is trigonal planar in shape, hence the "
      "CN^-^ nucleophile can attack the C=O from the top or bottom of the plane with equal probability, forming a racemic mixture."),
    P("Option C: A racemic mixture is formed as the intermediate carbocation is trigonal planar in shape, hence the nucleophile "
      "Cl^-^ can attack from the top or bottom of the plane with equal probability, forming a racemic mixture"),
    P("Option D: 1-chloro-2-methylpropane is a primary halogenoalkane, undergoes S~N~2 nucleophilic substitution to form "
      "2-methylpropan-1-ol which will result in the inversion of configuration, only one product is formed."),
]
SOL[26] = [
    P("<b>Step 1</b> involves the attack of the electron-deficient C atom on the C=O group of the phenylethanoic acid (the "
      "electrophile) on the benzene ring of phenol. The electrophile substitutes the H atom on the benzene ring of phenol. "
      "Hence reaction 1 is an electrophilic substitution."),
    P("In <b>Step 2</b>, NaH provides the H^-^ anion, which abstracts a H^+^ from the carbon next to the C=O group. This is an "
      "acid-base reaction with the ketone acting as the acid since it donates a H^+^ ion, while the H^-^ acts as the base in "
      "receiving the H^+^."),
    "<p>%s</p>" % IMG(26, 1),
]
SOL[27] = [
    P("Apply the same pattern of reduction across the ester bonds to alcohols, bearing in mind that ketones are also reduced "
      "to secondary alcohols and amides are reduced to amines. Hence a total of three fragments are produced after the reaction."),
    "<p>%s</p>" % IMG(27, 1),
]
SOL[28] = [
    P("<b>Pattern recognition</b>"),
    "<p>%s</p>" % IMG(28, 1),
]
SOL[29] = [
    P("Step 1: redox<br>2Fe^3+^ + 2I^-^ -> 2Fe^2+^ + I~2~ " + E_CELL + " = +0.77 %s (+0.54) > 0 V" % MINUS),
    P("Step 2: ligand exchange<br>Fe(H~2~O)~6~^2+^ + 6CN^-^ -> Fe(CN)~6~^4-^ + 6H~2~O"),
    P("Step 3: redox<br>Fe(CN)~6~^4-^ + ½Cl~2~ -> Fe(CN)~6~^3-^ + Cl^-^<br>" + E_CELL + " = +1.36 %s (+0.36) > 0 V" % MINUS),
    P("For <b>A</b>, step 3 is incorrect as SO~2~ cannot be reduced by Fe(CN)~6~^4-^."),
    P("For <b>C</b>, step 2 is incorrect as Fe^2+^ is oxidised to Fe^3+^ while I^-^ cannot be reduced."),
    P("For <b>D</b>, step 1 is incorrect as reaction is not feasible since " + E_CELL + " = +0.77 %s (+0.80) < 0 V.<br>"
      "Step 2 is incorrect as Fe^2+^ is oxidised to Fe^3+^ while I^-^ cannot be reduced." % MINUS),
]
SOL[30] = [
    P("Option A:<br>The empirical formula: Cr, 15.5%; S, 38.1%; N, 29.2%, H: 2.98%, C: 14.22%"),
    TBL([["", "Cr :", "S :", "N :", "C :", "H"],
         ["Ratio =", "0.298 :", "1.186 :", "2.086 :", "1.185 :", "2.98"],
         ["=", "1 :", "4 :", "7 :", "4 :", "10"]]),
    P("Empirical formula: CrS~4~N~7~C~4~H~10~"),
    P("From <b>K</b> to <b>P</b>, there should be no change in oxidation state and merely a ligand exchange."),
    P("In <b>P</b>, the coordination number is 6 and the oxidation number of Cr = +3. Given that there is one cation NH~4~^+^, "
      "hence the overall charge is %s1. Thus, there are 4SCN^-^ ligands to make the overall charge %s1." % (MINUS, MINUS)),
    P("Option B: Conversion of <b>L</b> to <b>M</b> is an acid base reaction where <b>L</b> is CrO~4~^2-^ and <b>M</b> is "
      "Cr~2~O~7~^2-^."),
    P("Option C: <b>K</b> is Na~3~[Cr(OH)~6~] (aq). <b>K</b> is not a solid unlike the formula given in option C."),
    P("Option D: H~2~O~2~ is an oxidising agent in the conversion of <b>K</b> to <b>L</b> as the oxidation number of Cr "
      "increases from +3 to +6."),
]

# editorial fixes: empty until the user rules (the school's wording is kept verbatim)
TYPO_FIXES = []

# ------------------------------------------------------------------- output
assert sorted(SOL) == list(range(1, 31))
out = {}
for q in sorted(SOL):
    body = "\n".join(SOL[q])
    for old, new, n in TYPO_FIXES:
        pass
    out[str(q)] = '<div class="worked-solution">\n%s\n</div>' % body

# ------------------------------------------------------------------- checks
doc = pymupdf.open(PDF)
assert len(doc) == 29, len(doc)
full = "\n".join(p.get_text() for p in doc)
ans_lines = re.findall(r"Ans(?:wer)?\s*:\s*([A-D])", full)
assert len(ans_lines) == 30, ("Ans lines", len(ans_lines))
tab = doc[28].get_text()
printed = dict((int(a), b) for a, b in re.findall(r"(?m)^(\d{1,2})\s*\n([A-D])\s*$", tab))
assert printed == KEY, ("printed key table != KEY", printed)
assert ans_lines == [KEY[i] for i in range(1, 31)], "Ans: lines out of order/disagree with the key"
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
assert counts == {"A": 7, "B": 7, "C": 9, "D": 7}, counts
assert len(ASSETS) == 10, len(ASSETS)
for q, html in out.items():
    assert html.count("data-asset=") == sum(1 for a in ASSETS if a["question"] == int(q)), q
    assert "~" not in html and "^" not in html.replace("→", ""), ("unconverted notation", q)

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key verified (printed table = Ans lines = KEY; 7/7/9/7), %d answer snips" % len(ASSETS))
