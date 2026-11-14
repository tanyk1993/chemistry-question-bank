"""NYJC 2026 H2 P1 (9476/01, 30 MCQ): typed worked solutions + answer key.

SOURCE: the school's "Answers and Comments" (8-page PDF, docx twin): a printed key table, then one block per
question (answer letter + comments).  Hand-typed here in house markup (div.worked-solution > p > span.ans, .frac,
table.cmp, img.ws-fig) and CHECKED against the PDF: the key table, the 30 block headings, the 7/7/... counts and
the question paper's own typed table (same key).  Q19 is headed "B (VOID)" by the school -- see VOID_NOTE.

Run:  python3 -m ingest.build_nyjc26_p1_answers <answers.pdf> <outdir>
Writes worked_solutions.json, answer_assets.json, answer_key.json.

The school's wording is kept verbatim; editorial rulings go in TYPO_FIXES (empty until the user rules).
Not typed: the 11 diagram snips (answer_assets.json); the user snips them: NYJC_H2_P1_Q<n>_ans-<k>_2026.png.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PDF, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

KEY = dict(enumerate("CBDCADACCDBBDDAAADBDCBDCACBAB" "B", 1))
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


def IMG(q, k):
    path = "NYJC_H2_P1_Q%d_ans-%d_2026.png" % (q, k)
    ASSETS.append({"question": q, "slot": "ans-%d" % k, "path": path,
                   "offset": 1 + sum(1 for a in ASSETS if a["question"] == q)})
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % path


STD = '<span class="pl-sym">⦵</span>'
E_STD = '<i>E</i>' + STD
X10 = lambda m, e: "%s %s 10^%s^" % (m, TIMES, str(e).replace("-", MINUS))

ASSETS = []
SOL = {}

# ============================================================== 1 - 10
SOL[1] = [
    P("I.E. generally increase across the period. Looking at the 10^th^ I.E., there is an unusual smaller increase from "
      "element Y to Z."),
    P("This indicates that there is a possibility of Y^9+^ and Z^9+^ having electron configuration ns^2^ and ns^2^np^1^ or "
      "ns^2^np^3^ and ns^2^np^4^ ⇒ Adding back 9 electrons, element Y and element Z will have the electron configuration of "
      "group 3 to group 14 or group 16 to group 17 (option C)."),
    P("OR Based on the electron configuration of Y^9+^ and Z^9+^ (as we are checking their 10^th^ I.E.) stated below, we can see "
      "that only option C has electron configuration of Y^9+^ and Z^9+^ accounting for an exception across the period."),
    TBL([["", "element X", "element Y", "element Z"],
         ["<b>A</b>", "Na<br>X^9+^: 1s^2^", "Mg<br>Y^9+^:1s^2^2s^1^", "Al<br>Z^9+^:1s^2^2s^2^"],
         ["<b>B</b>", "Al<br>X^9+^: 1s^2^2s^2^", "Si<br>Y^9+^:1s^2^2s^2^2p^1^", "P<br>Z^9+^:1s^2^2s^2^2p^2^"],
         ["<b>C</b>", "P<br>X^9+^: 1s^2^2s^2^2p^2^", "S<br><b>Y^9+^:1s^2^2s^2^2p^3^</b>", "Cl<br><b>Z^9+^:1s^2^2s^2^2p^4^</b>"],
         ["<b>D</b>", "S<br>X^9+^:1s^2^2s^2^2p^3^", "Cl<br>Y^9+^:1s^2^2s^2^2p^4^", "Ar<br>Z^9+^:1s^2^2s^2^2p^5^"]]),
]
SOL[2] = [
    P("V(CO~2~) = 40 cm^3^<br>V(O~2~ unreacted) = 75 %s 40 = 35 cm^3^<br>V(O~2~ reacted) = 100 %s 35 = 65 cm^3^" % (MINUS, MINUS)),
    TBL([["C~<i>x</i>~H~<i>y</i>~", "+ (<i>x</i>+<i>y</i>/4) O~2~", "->", "<i>x</i>CO~2~", "+ <i>y</i>/2 H~2~O"],
         ["10", "65", "", "40", ""]]),
    P("1/<i>x</i> = 10/40 ⇒ <i>x</i> = 4<br><i>x</i>+<i>y</i>/4 = 65/10 ⇒ <i>y</i> = 10<br>∴ M.F is C~4~H~10~"),
]
SOL[3] = [
    P("1 is incorrect since the relative isotopic mass, of an isotope is the <u>mass of <b>an atom</b> of the isotope</u> compared "
      "to " + fr("1", "12") + " the mass of a ^12^C atom e.g. for O, it’s either 18 for ^18^O or 16 for ^16^O. It need not take into "
      "account the different isotopes."),
    P("2 is correct since the relative atomic mass, <i>A</i>~r~, of an element, is the <u>weighted average</u> mass of the isotopes "
      "of the element compared to " + fr("1", "12") + " the mass of a ^12^C atom.<br>"
      "1 mole of hydrogen will include all isotopes of hydrogen (and their relative abundances)."),
    P("3 is correct as this is how <i>M</i>~r~ is worked out e.g. <i>M</i>~r~ of H~2~O = 1.0 + 1.0 +16.0 = 18.0. Note while this is a "
      "correct statement, this is NOT the definition of <i>M</i>~r~ ⇒ answer would be different if question was not true/fasle "
      "but which is a correct definition."),
]
SOL[4] = [
    P("Instantaneous dipole-induced dipole (id-id) interaction arises as the electrons in a molecule are constantly moving. At any "
      "moment, there can be an asymmetrical electron density around a molecule, resulting in an instantaneous dipole. This "
      "instantaneous dipole will induce another dipole on its neighbouring molecule. The electrostatic attraction between these "
      "fluctuating dipoles results in instantaneous dipole – induced dipole interactions."),
    P("Option C is false because the electron-poor end of a bromine molecule <u>attracts</u> electrons in a neighbouring bromine "
      "molecule."),
]
SOL[5] = [
    P("W is characteristic of an ionic compound as it has high mp/bp and electrical conductivity in liquid and solid state "
      "(Ans is A or B)."),
    P("X is characteristic of a compound with simple molecular structure. It has low mp/bp and poor electrical conductivity in "
      "solid and liquid states. CH~3~CO~2~H is very soluble in water while C~5~H~12~ is not soluble in water (Ans is A or D)."),
    P("Y is characteristic of a metal as it has high mp/bp and electrical conductivity in solid state. K is an extremely reactive "
      "Group 1 metal and explodes in water to form a souble salt. Fe does not react (can calculate <i>E</i>~cell~) and remains "
      "insoluble in water as the energy released from the relatively weaker ion-dipole interactions between Fe cations and water "
      "molecules is insufficient to overcome the strong metallic bonds between cations and sea of delocalised valence electrons."
      "(Ans is A or C)."),
    P("Z is characteristic of a compound with giant molecular structure (with structure similar to diamond). It has high mp/bp and "
      "poor conductor in solid and liquid state. Al~2~O~3~ would be a conductor in liquid state. (Ans is A or C)."),
]
SOL[6] = [
    P("Statement 1: False<br>Refer to <i>V</i>~m~ at rtp from DB, when <i>V</i> is 24 dm^3^ at temp <i>T</i> = 20 °C, pressure is 1 atm, "
      "<u>not 1 bar.</u>"),
    P("Statement 2: False<br>from p<i>V</i> = <i>nRT</i>, at constant <i>V</i> and <i>n</i>, p ∝ <i>T</i>(K)<br>Doubling p doubles "
      "temperature, <u><i>only if</i></u> T is in Kelvin, not in degree Celsius."),
    P("Statement 3: True<br>NH~3~ molecules experience significant hydrogen bonding, so intermolecular attractive forces reduce the "
      "frequency and force of collisions with the container walls compared to an ideal gas. Under the same <i>n</i>, <i>V</i>, "
      "<i>T</i>, <u>real NH~3~ exerts a pressure <b><i>lower</i></b> than the ideal gas</u> prediction of 1 bar."),
    P("Answer: Only statement 3 is true."),
]
SOL[7] = [
    P("For reaction to be spontaneous/energetically feasible at all temperature, @G is negative at all temperature."),
    P("Since @G = @H %s T@S,<br>this means <u>@H should be negative (exothermic reaction)</u> and %s T@S is also negative "
      "(and hence @S is positive) ⇒ Ans is A." % (MINUS, MINUS)),
    TBL([["", "@H", "@S", "%s T@S" % MINUS, "@G &lt;0 and rxn is spontaneous at"],
         ["A", "%sve" % MINUS, "+ve", "%sve" % MINUS, "All temp" ],
         ["B", "%sve" % MINUS, "%sve" % MINUS, "+ve", "At low temp when |%s T@S|&lt;|@H|" % MINUS],
         ["C", "+ve", "+ve", "%sve" % MINUS, "At high temp when |T@S|&gt;|@H|"],
         ["D", "+ve", "%sve" % MINUS, "+ve", "Never spont at any temp"]]),
]
SOL[8] = [
    P("Activation energy is the minimum energy required for a reaction to happen. In an energy profile diagram, it is the energy of "
      "the starting species of reaction/step to the peak energy of the transition state (@E~1~ for stage Y and @E~6~ for stage Z)"),
    P("Enthalpy change of reaction is the net change in energy during a reaction/step. It equals energy of final species %s initial "
      "species (+@E~3~ for stage Y (endo) %s@E~7~ for stage Z (exo) and overall %s@E~5~ for reaction X (exo))." % (MINUS, MINUS, MINUS)),
    P("Reaction X is a 2-step reaction. Hence it’s first E~a~ is @E~1~ for stage Y and @E~6~ for stage Z. It’s E~a~ is not equal to "
      "@E~3~ (option 1 is wrong)."),
]
SOL[9] = [
    P("Rate of production of Cl~2~ = @[Cl~2~] / @time<br>Either work out an additional column of [Cl~2~] / 30 to find rate in "
      "mol dm^-3^ s^-1^ OR<br>observe <u>relative</u> rate ∝ [Cl~2~] detected at 30s"),
    P("Comparing expt 1 and 2, when [HCl] is ↑ by 1.5 times (0.15/0.10), rate ↑ by approx. 1.5 times "
      "(%s/%s=1.47), <b>hence rate is proportional to [HCl] and rate is 1^st^ order wrt HCl.</b>" % (X10("1.0", -3), X10("6.8", -4))),
    P("Let relative rate = k’[HCl][O~2~]^<i>a</i>^<br>Comparing expt 2 and 3 (or 1 and 3),"),
    PC(fr(X10("6.0", -4), X10("1.0", -3)) + " = " + fr("<i>k</i>’(0.20)(0.10)^<i>a</i>^", "<i>k</i>’(0.15)(0.15)^<i>a</i>^")),
    PC("0.450 = (" + fr("2", "3") + ")^<i>a</i>^"),
    P("<b><i>a</i>= ln (0.450) / ln (2/3) = 1.969 ≈ 2</b><br>(<i>a</i> = for expt 1 and 3 = 2.01)"),
    P("OR Comparing expt 1 and 3, [HCl] is ↑ by 2 times (0.20/0.10), rate is expected to ↑ by 2 times "
      "(%s×2=%s). Hence, rate ↓ by approx. 0.45 times (%s/%s=0.45) when [O~2~] ↓ by 0.67 times (0.10/0.15) and 0.67^2^ = 0.45. "
      "(OR rate ↑ by approximately 2.25=1.5^2^ times (%s/%s=2.27) when [O~2~] ↑by 1.5 times (0.15/0.10).) "
      "<b>Hence rate is proportional to [O~2~]^2^ and rate is 2^nd^ order wrt O~2~</b>"
      % (X10("6.8", -4), X10("1.36", -3), X10("6.0", -4), X10("1.36", -3), X10("1.36", -3), X10("6.0", -4))),
    P("<b>rate = <i>k</i> [HCl][O~2~]^2^</b>"),
    P("Comparing expt 2 and 4, when both [HCl] and [O~2~] are ↑ by 2 times (0.30/0.15), rate is expected to ↑ by 2 x 2^2^ = 8 times "
      "i.e. becomes 8 x %s = 8 ×10^%s^" % ("1.0×10^%s3^" % MINUS, MINUS + "3")),
    P("Alternatively, find a proportionality constant<br>Let relative rate = k’[HCl][O~2~]^2^.<br>Substitute data from expt 1-3 to find "
      "k’.<br>e.g. 6.8 x 10^%s4^ = k’ (0.10)(0.15)^2^<br>k’=0.30<br>For expt 4: x = (0.30)(0.30)(0.30)^2^=8.1x10^%s3^" % (MINUS, MINUS)),
]
SOL[10] = [
    P("Option D will give downward sloping straight line graph instead."),
    IMG(10, 1),
    P("During reaction, as T is used up, [T] decreases. Gradient of [T]-time graph equals rate which is constant. This is because "
      "rate remains constant (with time as reaction progresses) as it is zero order wrt [T] hence option A is correct."),
    P("Option C is correct as rate constant is only affected by temperature and catalyst. It remains constant during reaction (even "
      "when [T] is decreasing)."),
    P("Option B is correct. Recall the following graphs that can be plotted for non-continuous method (when comparing many expt):"),
    IMG(10, 2),
]
# ============================================================== 11 - 20
SOL[11] = [
    P("When temperature is decreased, it favours the forward exothermic reaction. Hence position of equilibrium shifts to the right.<br>"
      "Less amount of I~2~ will be present (&lt; 0.23 mol)."),
    P("When temperature is decreased, the rate of reaction will be slower. Hence the slope will be less steep."),
]
SOL[12] = [
    P("n(SO~2~) reacted = 0.800(0.60) = 0.480 mol"),
    TBL([["amount/mol", "2SO~2~(g)", "+", "O~2~(g)", "<->", "2SO~3~(g)"],
         ["Initial", "0.800", "", "0.400", "", "0"],
         ["Change", "%s0.480" % MINUS, "", "%s0.480/2" % MINUS, "", "+0.480"],
         ["Eqm", "0.320", "", "0.160", "", "0.480"]]),
    PC("<i>P</i> = " + fr("<i>nRT</i>", "<i>V</i>")),
    P("Either substitute n~x~ to find eqm p~x~ of each gas or find a common factor first:"),
    PC(fr("<i>RT</i>", "<i>V</i>") + " = " + fr("8.31 %s 700" % TIMES, "5.00 %s 10^%s3^" % (TIMES, MINUS)) + " = 1.163 %s 10^6^" % TIMES),
    PC("<i>P</i>(SO~2~) = (0.320)(1.163 %s 10^6^) = 3.722 %s 10^5^ <i>Pa</i><br>"
       "<i>P</i>(O~2~) = (0.160)(1.163 %s 10^6^) = 1.861 %s 10^5^ <i>Pa</i><br>"
       "<i>P</i>(SO~3~) = (0.480)(1.163 %s 10^6^) = 5.584 %s 10^5^ <i>Pa</i>" % ((TIMES,) * 6)),
    PC("<i>K</i>~p~ = " + fr("(<i>P</i>(SO~3~))^2^", "(<i>P</i>(SO~2~))^2^(<i>P</i>(O~2~))")),
    PC("= " + fr("(5.584 %s 10^5^)^2^" % TIMES, "(3.722 %s 10^5^)^2^(1.861 %s 10^5^)" % (TIMES, TIMES))),
    PC("= 1.208 %s 10^%s5^ <i>Pa</i>^%s1^ = 1.21 %s 10^%s5^ <i>Pa</i>^%s1^" % (TIMES, MINUS, MINUS, TIMES, MINUS, MINUS)),
    P("<b>OR using p~x~ ICE table</b>"),
    PC("<i>P</i> = " + fr("<i>nRT</i>", "<i>V</i>")),
    P("Either substitute n~x~ to find initial p~x~ of SO~2~ and O~2~ or find a common factor first:"),
    PC(fr("<i>RT</i>", "<i>V</i>") + " = " + fr("8.31 %s 700" % TIMES, "5.00 %s 10^%s3^" % (TIMES, MINUS)) + " = 1.163 %s 10^6^" % TIMES),
    P("P(O~2~)=(0.400)(1.163 %s10^6^)=4.652%s10^5^Pa<br>P(SO~2~)=(0.800)(1.163 %s10^6^)=9.304%s10^5^Pa" % ((TIMES,) * 4)),
    P("P(SO~2~) reacted = (9.304%s10^5^)(0.60)<br>= 5.582%s10^5^ Pa" % (TIMES, TIMES)),
    TBL([["p~x~/Pa", "2SO~2~(g)", "+", "O~2~(g)", "<->", "2SO~3~(g)"],
         ["Initial", "9.304%s10^5^" % TIMES, "", "4.652%s10^5^" % TIMES, "", "0"],
         ["Change", "%s5.582%s10^5^" % (MINUS, TIMES), "", "%s1/2<br>(5.582%s10^5^)" % (MINUS, TIMES), "", "+5.582%s10^5^" % TIMES],
         ["Eqm", "3.722%s10^5^" % TIMES, "", "1.8608%s10^5^" % TIMES, "", "5.582%s10^5^" % TIMES]]),
    P("Note regarding distractors:<br>A: Did not convert to m^3^.<br>C: use 0.480 mol instead of 0.240 mol of O~2~"),
]
SOL[13] = [
    P("Graph I — <u>weak acid</u>-strong base titration. Initial pH starts around pH 4, has a gradual rise (<u>buffer region</u>), "
      "then a sharp jump up to pH 14."),
    P("Graph II — <u>strong acid</u>/strong base titration. Initial pH starts around pH 1, followed by a sharp jump in pH at "
      "equivalence point, and <u>no buffer region</u>."),
    P("Hence,<br>A (true): ethanoic acid is a weak acid.<br>B (true): The gentle sloping region before the equivalence point is the "
      "buffer region (mixture of CH~3~COOH/CH~3~COO^-^)."),
    P("C (true): nitric acid is a strong acid.<br>D (untrue — this is the answer): There is no buffer region in Graph II at all, either "
      "before or after the neutralisation point. A buffer requires a weak acid/conjugate base (or weak base/conjugate acid) pair in "
      "significant amounts."),
]
SOL[14] = [
    P("Answer: D (1, 2, 3 and 4)"),
    P("Statement 1: True<br>ZnF~2~(s) <-> Zn^2+^(aq) + 2F^-^(aq)<br>Let solubility = x mol dm^-3^, so [Zn^2+^] = s, [F^-^] = 2x<br>"
      "Ksp(ZnF~2~) = x(2x)^2^ = 4x^3^ = 3.2 %s 10^%s2^<br>x^3^ = 8.0 %s 10^%s3^ ⇒ x = 0.20 mol dm^-3^<br>So in solution X: [F^-^] = 2x = "
      "0.40 mol dm^-3^<br>Diluting with an equal volume of water simply halves the concentration instantly:<br>"
      "[F^-^]new = 0.40 / 2 = 0.20 mol dm^-3^" % (TIMES, MINUS, TIMES, MINUS)),
    P("Statement 2: True. <i>K</i>~sp~ is an equilibrium constant and depends only on temperature."),
    P("Statement 3: True. Solution X is saturated with respect to ZnF~2~.<br>Adding NaF increases [F^-^] via the common ion effect hence "
      "POE of ZnF~2~(s) <-> Zn^2+^(aq) + 2F^-^(aq) shifts left to use up F^-^ and more solid ZnF~2~ is precipitated."),
    P("Statement 4: True. Since solution X is saturated with respect to ZnF~2~, which has a <u>much larger</u> <i>K</i>~sp~ value than "
      "BaF~2~, [F^-^] is at a <u>high</u> equilibrium value (4.0%s10^%s1^ mol dm^%s3^). Adding even a small amount of Ba^2+^ will make "
      "the ionic product [Ba^2+^][F^-^]^2^ exceed the <u>very small</u> <i>K</i>~sp~(BaF~2~) = 1.6%s10^%s7^ almost immediately, since "
      "[F^-^] is comparatively larger." % (TIMES, MINUS, MINUS, TIMES, MINUS)),
]
SOL[15] = [
    P("The stable ion formed by Y is an anion which has one more electron shell and hence a greater radius than the stable ion formed "
      "by X which is a cation. So Y is a non-metal while X is a metal in Period 3."),
    P("The anion formed by Y will have 18 electrons, after gaining electrons to form a configuration similar to Ar while the cation "
      "formed by X will have 10 electrons after losing electrons to form a stable configuration similar to Ne (Ans is A or B)."),
    P("Since atomic radius generally decreases across the period (due to increasing nuclear charge while shielding effect remains "
      "constant hence ENC increases), Y has a smaller atomic radius than X / X has a larger atomic radius than Y (Ans is A or C)."),
]
SOL[16] = [
    TBL([["", "statement", "explanation"],
         ["<b>1✓</b>", "The p<i>K</i>~a~ of hydrogen iodide is lower than that of hydrogen chloride.",
          "The H−Cl bond strength is high<br><br>The smaller the p<i>K</i>a, the stronger the acid. HI is a stronger acid than HCl because "
          "the shorter <u>H−Cl bond is stronger and requires more energy to break to donate H^+^.</u> Hence the extent of dissociation of "
          "HCl is smaller than HI."],
         ["<b>2✓</b>", "Silver chloride dissolves more readily in aqueous ammonia than silver bromide",
          "The solubility product of AgCl is larger<br><br>It’s easier for ionic product to be less than the larger <i>K</i>~sp~ value "
          "of AgCl."],
         ["<b>3✗</b>", "When chlorine is bubbled into aqueous potassium iodide, a <s>purple</s> <b>brown</b> solution is seen."
          "<br><br>A brown solution of I~2~ (aq) is formed. Purple I~2~ is formed only if organic solvent was added.",
          "<i>E</i>" + STD + "(I~2~/I^-^) is less positive than <i>E</i>" + STD + "(Cl~2~/Cl^-^)<br><br>This will result in a positive "
          "<i>E</i>cell for the reaction Cl~2~ + 2I^-^ -> I~2~ + 2Cl^-^ where Cl~2~ is reduced and I^-^ is oxidised"]]),
]
SOL[17] = [
    P("Statement 1 is incorrect.<br>Meso compound contains two or more chiral centres but they have an internal plane of symmetry that "
      "makes half of the molecule a mirror image of the other half. Hence, meso compounds are achiral molecules that has chiral centres."),
    P("Statement 2 is incorrect.<br>Racemic mixture is an equimolar mixture of two enantiomers (that are chiral molecules). Rotating "
      "powers of the enantiomers cancel out hence racemic mixture will not rotate plane-polarised light."),
]
SOL[18] = [
    P("Statement A is incorrect.<br>Only two <u>monochlorinated</u> products are formed. However, there is possibility of "
      "multi-substituted products."),
    P("Statement B is incorrect.<br>Alkyl radicals are formed during propagation, hence, formation of hydrocarbons is possible during "
      "termination where two alkyl radicals combine."),
    P("Statement C<br>Hydrogen radicals are not formed in the propagation step of free radical substitution, hence hydrogen gas will "
      "not be formed during termination."),
    P("Statement D<br>Hexane (six carbon atoms) can be produced during termination from two propyl radicals formed in the propagation "
      "step."),
]
SOL[19] = [
    IMG(19, 1),
    P("6-methylhept-5-en-2-one"),
    P("Option A: Since there is no terminal alkene, there will not be formation of CO~2~. No ethanedioic acid or methanoic acid (which "
      "can be oxidised to CO~2~ by KMnO~4~) are formed as well. The products are CH~3~COCH~3~ and HOOCCH~2~CH~2~COCH~3~."),
    P("Option B: The product formed after reduction with H~2~ has the molecular formula of C~8~H~18~O. It is a fully saturated alcohol "
      "hence it has the formula C~<i>n</i>~H~2<i>n</i>+2~O"),
    IMG(19, 2),
    P("Option C: The product formed (check M’rule) after electrophilic addition with HBr does not have a chiral centre. Hence, the "
      "product is not optically active. Anyway, step 1 and step 2 of Electrophilic Addition will also form racemic mixtures."),
    IMG(19, 3),
    P("Option D: C atoms in 6-methylhept-5-en-2-one are either sp or sp^2^ hybridised. Hence, there is no s-p overlap in the structure "
      "given."),
]
SOL[20] = [
    P("Option A and B: Aluminium chloride acts as a Lewis acid because it accepts an electron <b>pair</b> from BrCl."),
    P("Option C: The formation of the product depends on several factors such as the stability of the <b>carbocation</b>, not the "
      "product."),
]
# ============================================================== 21 - 30
SOL[21] = [
    IMG(21, 1),
    P("3-bromo-2,3-dimethylpentane"),
    P("There are four alkenes, which include only one cis-trans pair."),
    IMG(21, 2),
]
SOL[22] = [
    P("2-methylpropan-2-ol is a tertiary alcohol which cannot be oxidised by K~2~Cr~2~O~7~."),
    P("Butan-1-ol and 2-methylpropan-1-ol are primary alcohols which are oxidised to carboxylic acids."),
    P("In carboxylic acids, the presence of electron withdrawing group &gt;C=O withdraws electrons away from the hydrogen atom of the "
      "%sOH group. Hence the O%sH bond is more polarised.<br>Hydrogen bonds in carboxylic acids are stronger than hydrogen bonds in "
      "alcohols. Hence more energy is needed to break the stronger intermolecular hydrogen bonding in carboxylic acids, resulting in "
      "higher boiling point." % ("–", "–")),
    P("Butan-2-ol is a secondary alcohol which is oxidised to a ketone."),
    P("Carbonyl compounds (aldehydes and ketones) have lower boiling points when compared to alcohols and carboxylic acids of "
      "comparable <i>M</i>~r~. This is due to the absence of hydrogen bonds between the carbonyl compounds."),
]
SOL[23] = [
    P("The compound contains a benzaldehyde (aromatic aldehyde) and an ester."),
    P("Ester does <b>not</b> react with 2,4-DNPH and Tollens' reagent."),
    P("Statement 1 is incorrect as one mole of the benzaldehyde in the compound reacts with one mole of 2,4-DNPH via condensation."),
    P("Statement 2 is correct as one mole of the benzaldehyde in the compound gives two moles of Ag(s) with Tollens' reagent on "
      "warming. See equation below."),
    P("<b>1RCHO</b> + 2Ag^+^ + 3OH^-^ -> RCO~2~^-^ + <b>2Ag</b> + 2H~2~O<br>[Note benaldehyde do not react with Fehling’s Rgt "
      "(Cu^2+^ + OH^-^)]"),
    P("Statement 3 is correct. On warming with aqueous alkaline iodine, one mole of the compound undergoes hydrolysis to give one mole "
      "of CH~3~CH~2~OH, a methyl alcohol which is oxidised to give one mole of CHI~3~(s) (and one mole of HCO~2~^-^ )."),
]
SOL[24] = [
    P("For reaction W, 2 moles of carboxylic acids will form 2(1/2) = 1 mole of H~2~ gas with Na.<br>Equation: (CH~2~COOH)~2~ + 2Na -> "
      "H~2~ + (CH~2~COO^-^Na^+^)~2~"),
    P("For reaction X, 1 mole of carboxylic acid will form 1/2 mole of CO~2~ gas with Na~2~CO~3~.<br>Equation: CH~3~CH(OH)CH~2~COOH + "
      "½Na~2~CO~3~ -> ½CO~2~ + ½H~2~O + CH~3~CH(OH)CH~2~COO^-^Na^+^"),
    P("For reaction Y, CH~3~CH(OH)CH~2~COOH with NaOH does not produce any gas.<br>Equation: CH~3~CH(OH)CH~2~COOH + NaOH -> "
      "CH~3~CH(OH)CH~2~COO^-^Na^+^ + H~2~O"),
    P("For reaction Z, 1 mole of alcohol and 2 moles of carboxylic acids will form 3(1/2) =1.5 mole of H~2~ gas with Na.<br>"
      "Equation: CH(OH)(COOH)CH~2~COOH + 3Na -> 1½ H~2~ + CH(ONa)(COONa)CH~2~COONa"),
    P("Hence, order in decreasing volume is<br>Z (1.5 moles), W(1mole), X(0.5moles), Y(0)."),
]
SOL[25] = [
    IMG(25, 1),
    P("A. For the addition polymer, it can be seen that the repeating monomer is CH~2~=CHCl"),
    P("B. Using CHCl=CHCl, it will result in a polymer"),
    IMG(25, 2),
    P("C. Using CH~3~CCl=CHCl, it will result in a polymer"),
    IMG(25, 3),
    P("D. Using CH~2~=CClCCl=CH~2~, it will result in a polymer"),
    IMG(25, 4),
]
SOL[26] = [
    P("1: Correct. It can be hydrolysed to form benzoic acid and NH~2~CH~2~COOH.<br>NH~2~CH~2~COOH is an amino acid."),
    P("2: Incorrect. It can be made using benzoyl chloride with aminoethanoic acid in the laboratory. Benzoic acid will undergo "
      "acid-base reaction with aminoethanoic acid."),
    P("3: Correct. The carboxylic acid can neutralised by sodium hydroxide."),
]
SOL[27] = [
    P(E_STD + "(Ag^+^/Ag) = +0.80 V<br>" + E_STD + "(Cu^2+^/Cu) = +0.34 V<br>" + E_STD + "(Zn^2+^/Zn) = %s0.76 V" % MINUS),
    P("Both Zn and Cu are oxidised and both are in the solution as Zn^2+^ and Cu^2+^ respectively."),
    P("Ag is less readily oxidised than Cu, so it does not gets oxidised and becomes anode sludge."),
]
SOL[28] = [
    P("<i>Q</i> = <i>It</i> = 9.65 %s 1000 = 9650 C" % TIMES),
    P("n(e) = " + fr("9650", "96500") + " = 0.100 mol<br>During anodising,<br>2H~2~O -> O~2~ + 4H^+^ + 4e<br>4Al + 3 O~2~ -> 2Al~2~O~3~"),
    P("n(O~2~) = 0.100 / 4 = 0.025 mol<br>n(Al~2~O~3~)=0.025 x 2 / 3 = 0.01666 mol<br><b>OR</b> combining the 2 equations:<br>"
      "2Al~2~O~3~ ≡ 3O~2~ ≡ 12 e -> 1Al~2~O~3~ ≡ 6 e"),
    PC("n(Al~2~O~3~) = " + fr("0.100", "6") + " = 0.01666 mol"),
    P("m(Al~2~O~3~) formed = 0.01666 %s 102.0 = 1.70 g<br>n(Al) consumed = 0.01666 %s 2 = 0.03333 mol<br>m(Al) consumed = 0.03333 %s 27.0 "
      "= 0.90 g<br>max increase in mass of sheet = 1.70 %s 0.90<br>= 0.80 g" % (TIMES, TIMES, TIMES, MINUS)),
]
SOL[29] = [
    P("HCuCl~2~ is made up of H^+^ and [CuCl~2~]^-^<br>Hence o.s of Cu is +1 and its electronic configuration is [Ar]3d^10^ which "
      "contains 0 unpaired d electron"),
    P("NaMn(CO)~5~ is made up of Na^+^ and [Mn(CO)~5~]^-^<br>Hence o.s of Mn is %s1 and its electronic configuration is "
      "[Ar]3d^6^4s^2^ which contains 4 unpaired d electrons" % MINUS),
    P("[Ni(NH~3~)~6~]Cl~2~ is made up of [Ni(NH~3~)~6~]^2-^ and Cl^-^<br>Hence o.s of Ni is +2 and its electronic configuration is "
      "[Ar]3d^8^ which contains 2 unpaired d electrons"),
    P("VOBr~2~: o.s of V is +4 and its electronic configuration is [Ar]3d^1^ which contains 1 unpaired d electron"),
]
SOL[30] = [
    P("Definition of a transition element: It is a <b>d-block element</b> whose <b>atom</b> has <b>partially filled d subshell/d "
      "orbitals</b> or which forms at least one stable ion with partially filled d subshell/d orbitals.<br>Therefore statement 1 is "
      "incorrect and statement 2 is correct."),
    P("Iron has variable oxidation state because of the <b>close similarity in energies of the 3d and 4s orbitals</b> so that "
      "electrons in both orbitals can be used for bonding.<br>Therefore statement 3 is incorrect."),
    P("Iron function well as heterogenous catalysts because they <b>possess partially filled 3d subshells which can be used to form "
      "weak temporary bonds with reactant molecules</b>.<br>Therefore statement 4 is correct"),
]

# editorial fixes: empty until the user rules (the school's wording is kept verbatim)
# RULED by the user 2026-11-13: fix all typo/grammar slips ("methyl alcohol" in Q23 is intended: R-CH(OH)-CH3, left as is)
TYPO_FIXES = [     # (qn, old, new, expected count)
    (3, "true/fasle", "true/false", 1),
    (5, "souble", "soluble", 1),
    (14, "[Zn<sup>2+</sup>] = s,", "[Zn<sup>2+</sup>] = x,", 1),
    (17, "that has chiral centres", "that have chiral centres", 1),
    (19, "either sp or sp<sup>2</sup> hybridised", "either sp<sup>3</sup> or sp<sup>2</sup> hybridised", 1),
    (19, "no s-p overlap", "no s-sp overlap", 1),
    (23, "benaldehyde", "benzaldehyde", 1),
    (26, "can neutralised", "can be neutralised", 1),
    (27, "does not gets oxidised", "does not get oxidised", 1),
    (29, "[Ni(NH<sub>3</sub>)<sub>6</sub>]<sup>2−</sup> and", "[Ni(NH<sub>3</sub>)<sub>6</sub>]<sup>2+</sup> and", 1),
    (30, "Iron function well", "Iron functions well", 1),
    (30, "heterogenous", "heterogeneous", 1),
]

# RULED by the user 2026-11-13: spell every short form in full (regex, applied to the finished html)
SHORT_FORMS = [
    (r"I\.E\. generally increase", "Ionisation energies generally increase"),
    (r"(10<sup>th</sup>) I\.E\.", r"\1 ionisation energy"),
    (r"M\.F is", "Molecular formula is"),
    (r"mp/bp", "melting point/boiling point"),
    (r"Ans is", "Answer is"),
    (r"at rtp from DB", "at room temperature and pressure from the Data Booklet"),
    (r"at temp <i>T</i>", "at temperature <i>T</i>"),
    (r"at all temperature\b", "at all temperatures"),
    (r"rxn is", "reaction is"),
    (r">All temp<", ">All temperatures<"),
    (r"At low temp ", "At low temperature "),
    (r"At high temp ", "At high temperature "),
    (r"Never spont at any temp", "Never spontaneous at any temperature"),
    (r"\(endo\)", "(endothermic)"),
    (r"\(exo\)", "(exothermic)"),
    (r"\bexpt (\d+) and", r"experiments \1 and"),
    (r"\bexpt (\d+)-(\d+)", r"experiments \1-\2"),
    (r"many expt", "many experiments"),
    (r"\bexpt (\d+)", r"experiment \1"),
    (r"approx\. ", "approximately "),
    (r"\bwrt\b", "with respect to"),
    (r"<td>Eqm</td>", "<td>Equilibrium</td>"),
    (r"\beqm\b", "equilibrium"),
    (r"\bENC\b", "effective nuclear charge"),
    (r"\bPOE\b", "position of equilibrium"),
    (r"M’rule", "Markovnikov’s rule"),
    (r"Rgt\b", "reagent"),
    (r"\bo\.s of", "oxidation state of"),
    (r"<br>e\.g\. ", "<br>For example, "),
    (r" e\.g\. ", ", for example "),
    (r" i\.e\. becomes", ", that is, it becomes"),
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
import pymupdf
doc = pymupdf.open(PDF)
lay = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
heads, void = {}, []
for pg in doc:
    ws = pg.get_text("words")
    for i, w in enumerate(ws):
        if re.fullmatch(r"\d{1,2}", w[4]) and (55 < w[0] < 60 or 303 < w[0] < 308):
            nxt = [v for v in ws[i + 1:i + 4] if abs(v[1] - w[1]) < 3 and re.fullmatch(r"[A-D]", v[4])]
            if nxt:
                heads[int(w[4])] = nxt[0][4]
                if any(abs(v[1] - w[1]) < 3 and v[4] == "(VOID)" for v in ws[i + 1:i + 6]):
                    void.append(int(w[4]))
assert heads == KEY, ("block headings != KEY", {k: (heads.get(k), KEY[k]) for k in KEY if heads.get(k) != KEY[k]})
assert void == [19], void
tw = doc[0].get_text("words")
tw = [w for w in tw if w[1] < 200]
cells = [w[4] for w in sorted(tw, key=lambda w: (round(w[1] / 5), w[0]))]
tab = {}
row = []
for w in sorted(tw, key=lambda w: (round(w[1] / 5), w[0])):
    row.append(w[4])
tab = dict((int(a), b) for a, b in re.findall(r"(\d{1,2}) ([A-D])\b", " ".join(row)))
assert tab == KEY, ("printed table != KEY", {k: (tab.get(k), KEY[k]) for k in KEY if tab.get(k) != KEY[k]})
counts = {c: sum(1 for v in KEY.values() if v == c) for c in "ABCD"}
print("key counts", counts)
assert len(ASSETS) == 11, len(ASSETS)
for q, html in out.items():
    assert html.count("data-asset=") == sum(1 for a in ASSETS if a["question"] == int(q)), q
    assert "~" not in html and "^" not in html.replace("→", ""), ("unconverted notation", q, re.findall(r".{15}[~^].{15}", html)[:3])

(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(ASSETS, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_key.json").write_text(json.dumps({str(k): v for k, v in KEY.items()}, indent=1), encoding="utf-8")
print("OK: 30 solutions, key verified (table = headings = KEY), %d answer snips" % len(ASSETS))
