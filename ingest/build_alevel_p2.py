"""Hand transcription of A Level (SEAB) 9729/02 Oct/Nov 2024 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as extract_parts, i.e. what
gen_parts_migration.py reads).
Run from the repo root:  python3 ingest/build_alevel_p2.py <outdir>

Conventions (see claude/style-guide.md):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced;
  * asset slot = part label without brackets ('bii'), 'b2' for a second figure in the same part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SEAB", "H2", "P2", 2024
FIG = '<div class="fig">figure</div>'
M = "−"                                   # minus sign U+2212
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
def eqn(s): return '<p class="eqn">%s</p>' % s
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
L = '<i class="el">l</i>'                  # element l
K = i("K")
MDM = "mol dm" + sup(M + "3")
def ion(sym, ch): return sym + sup(ch)
SR2, CL_ = ion("Sr", "2+"), "C" + L + sup(M)
SRCL2 = "SrC" + L + sub(2)
CO3 = "CO" + sub(3)
CO32 = "CO" + sub(3) + sup("2" + M)
HCO3_ = "HCO" + sub(3) + sup(M)
DH = "Δ" + i("H") + sup("⦵")
TIMES = "×"
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html)])

# ---------------------------------------------------------------- Q1
t11 = table(tr(th("metal carbonate"), th("decomposition temperature / °C")),
            tr(td("CaCO" + sub(3)), td("832")), tr(td("SrCO" + sub(3)), td("1340")))
t12 = table(tr(th("process"), th(DH + " / kJ mol" + sup(M + "1"))),
            tr(td("standard enthalpy change of formation of " + SRCL2 + "(s)"), td(M + "828")),
            tr(td("standard enthalpy change of atomisation of strontium"), td("+164")),
            tr(td("standard enthalpy change of atomisation of chlorine"), td("+122")),
            tr(td("first electron affinity of chlorine"), td(M + "349")),
            tr(td("standard enthalpy change of hydration of strontium ions"), td(M + "1480")),
            tr(td("standard enthalpy change of hydration of chloride ions"), td(M + "364")))
Q[1] = dict(marks=16, intro=[], parts=[
    ("(a)", p("Table 1.1 shows the decomposition temperatures of two metal carbonates.") + cap("Table 1.1") + t11),
    ("(a)(i)", p("Write an equation for the thermal decomposition of SrCO" + sub(3) + ". " + mk(1))),
    ("(a)(ii)", p("Explain why the decomposition temperature of CaCO" + sub(3) + " is lower than that of SrCO" + sub(3) + ". " + mk(3))),
    ("(b)", p("Strontium chloride, " + SRCL2 + ", is an ionic compound.") +
            p("When " + SRCL2 + "(s) is added to water, a colourless solution is made, and the temperature of this solution increases.")),
    ("(b)(i)", p("Name the force of attraction between the particles in " + SRCL2 + "(s) and the force of attraction between water molecules. " + mk(1))),
    ("(b)(ii)", p("Fig. 1.1 shows the ions present in " + SRCL2 + ".") + p("Complete Fig. 1.1 to show:") +
                ul("the arrangement of two water molecules around one " + SR2 + "(aq) ion",
                   "the arrangement of two water molecules around one " + CL_ + "(aq) ion.") +
                p("The ions are " + b("not") + " drawn to scale.") + FIG +
                c(b("Fig. 1.1") + " " + mk(1))),
    ("(c)", p("The net effect of the individual processes that occur when " + SRCL2 + "(s) dissolves in water produces an overall positive entropy change.")),
    ("(c)(i)", p("Explain what is meant by entropy. " + mk(1))),
    ("(c)(ii)", p("Describe " + b("two") + " processes that have a positive entropy change when " + SRCL2 + "(s) dissolves in water. " + mk(2))),
    ("(c)(iii)", p("Describe " + b("one") + " process that has a negative entropy change when " + SRCL2 + "(s) dissolves in water. " + mk(1))),
    ("(d)", p("Explain what is meant by enthalpy change of hydration. " + mk(1))),
    ("(e)", p("Table 1.2 gives data relevant to this question.") + cap("Table 1.2") + t12),
    ("(e)(i)", p("Use data from Table 1.2 and the " + i("Data Booklet") + " to calculate the lattice energy of " + SRCL2 + "(s). " + mk(2))),
    ("(e)(ii)", p("Use your answer to " + b("(e)(i)") + " and relevant data from Table 1.2 to calculate the enthalpy change of solution in kJ mol" + sup(M + "1") + " for " + SRCL2 + "(s).") +
                p("If you were unable to calculate a value for the lattice energy of " + SRCL2 + "(s) in " + b("(e)(i)") + ", you should use " + M + "2048 kJ mol" + sup(M + "1") + ". This is " + b("not") + " the correct answer. " + mk(2))),
    ("(f)", p("CaF" + sub(2) + " is insoluble in water even though the theoretical value of Δ" + i("G") + " of solution is negative at 298 K.") +
            p("Suggest why CaF" + sub(2) + " is insoluble in water. " + mk(1))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=8, intro=[], parts=[
    ("(a)", p("An ideal gas consists of particles in constant motion at high velocities.") +
            p("It is assumed that there are no intermolecular forces of attraction between gas particles in an ideal gas.") +
            p("State " + b("two") + " other basic assumptions of kinetic theory as applied to an ideal gas. " + mk(2)) +
            p("The behaviour of a real gas, N" + sub(2) + "(g), can be compared to the behaviour of an ideal gas. Fig. 2.1 shows the values of " + i("pV / RT") +
              " produced when the volume of 1 mole of N" + sub(2) + "(g) is measured at specific pressures at a constant temperature.") + FIG + cap("Fig. 2.1")),
    ("(b)", p("On Fig. 2.1, sketch the relationship between " + i("pV / RT") + " and pressure for 1 mole of an ideal gas. " + mk(1))),
    ("(c)", p("Explain the non-ideal behaviour of N" + sub(2) + "(g) at the very high pressure Z. Your answer should " + b("not") +
              " refer to intermolecular forces. You may find it helpful to refer to Fig. 2.1 in your answer. " + mk(2))),
    ("(d)", p("N" + sub(2) + "(g) behaves as a non-ideal gas at the moderate pressure W because at this pressure the intermolecular forces are " + b("not") + " negligible.") +
            p("A molecule of N" + sub(2) + "(g) and a molecule of CO(g) have approximately the same volume.") +
            p("A sample of 1 mole of CO(g) is at the same temperature as N" + sub(2) + "(g).") +
            p("At pressure W, the approximate value for " + i("pV / RT") + " for CO(g) is lower than the value for N" + sub(2) + "(g).") +
            p("Explain why with reference to all types of intermolecular forces present in N" + sub(2) + "(g) and CO(g) and their relative strengths. " + mk(3))),
])

# ---------------------------------------------------------------- Q3
t31 = table(tr(th("test"), th("reagents and conditions"), th("observations with " + b("B")), th("observations with " + b("C"))),
            tr(td("1"), td("heat with acidified potassium dichromate(VI)"),
               td("<p>mixture changes from orange to green</p><p>single organic product made that</p>" +
                  ul("reacts with 2,4-dinitrophenylhydrazine to form an orange precipitate",
                     "does " + b("not") + " react with Fehling’s reagent")),
               td("no change")),
            tr(td("2"), td("warm with alkaline aqueous iodine"), td("pale yellow precipitate forms"), td("no change")))
Q[3] = dict(marks=10, intro=[
    p(b("A") + ", " + b("B") + " and " + b("C") + " are different organic compounds each of which contains only carbon, hydrogen and oxygen atoms. Each compound contains one hydroxy functional group only.")],
  parts=[
    ("(a)", p("When a sample of 0.500 g of " + b("A") + " is vapourised, it occupies a volume of 250 cm" + sup("3") + " at 101.325 kPa and 93 °C.") +
            p("Use the general gas equation to determine the molecular formula of " + b("A") + ". " + mk(3))),
    ("(b)", p("Compounds " + b("B") + " and " + b("C") + " both have molecular mass of 74.") +
            p("Table 3.1 shows the observations that occur when separate samples of " + b("B") + " and " + b("C") +
              " are added to different reagents under specific conditions in two separate tests.") + cap("Table 3.1") + t31),
    ("(b)(i)", p("Draw a structure for " + b("B") + " and for " + b("C") + ". " + mk(2))),
    ("(b)(ii)", p("Write a half-equation that describes the reaction of the species that is reduced when " + b("B") + " is heated with acidified potassium dichromate(VI). " + mk(1))),
    ("(b)(iii)", p("Name and state the formula of the pale yellow precipitate made when " + b("B") + " reacts with alkaline aqueous iodine. " + mk(1))),
    ("(c)", p("Explain why chromium ions are coloured. " + mk(3))),
])

# ---------------------------------------------------------------- Q4
t41 = table(tr(th("halogenoalkane sample"), th("time for precipitate to appear / s"), th("identity of halogen"), th("colour of precipitate")),
            tr(td(b("L")), td("38"), td(""), td("")),
            tr(td(b("M")), td("76"), td(""), td("")),
            tr(td(b("N")), td("512"), td(""), td("")))
Q[4] = dict(marks=18, intro=[], parts=[
    ("(a)", p("Stereoisomers are two or more molecules with the same molecular formula that differ only in the spatial arrangement of their atoms.") +
            p("Fig. 4.1 shows the structural formula of a molecule of vitamin E.") + FIG + cap("Fig. 4.1") +
            p("Vitamin E exists as 8 different stereoisomers.") +
            p("Use an asterisk (*) to mark each chiral centre present on the molecule of vitamin E shown in Fig. 4.1. " + mk(1))),
    ("(b)", p(b("F") + " and " + b("G") + " are a pair of isomers. Fig. 4.2 shows the structural formula for the pair of isomers " + b("F") + " and " + b("G") + ".") +
            FIG + cap("Fig. 4.2") +
            p(b("H") + " is a compound extracted from bacteria.") +
            p(b("H") + " is added to separate samples of " + b("F") + " and " + b("G") + ".") +
            p("When " + b("H") + " is added to " + b("F") + ", reaction 4.1 occurs.") + FIG +
            p("When " + b("H") + " is added to " + b("G") + ", no reaction occurs.")),
    ("(b)(i)", p("Identify the role of " + b("H") + " when it is added to " + b("F") + ". " + mk(1))),
    ("(b)(ii)", p("Explain why " + b("H") + " reacts with " + b("F") + " but does " + b("not") + " react with " + b("G") + ". " + mk(1))),
    ("(c)", p(b("J") + " and " + b("K") + " are a pair of stereoisomers with molecular formula C" + sub(4) + "H" + sub(8) + "O that share the following properties:") +
            ul("one secondary alcohol functional group", "two sp" + sup("2") + "-hybridised carbon atoms", "boils at 100 °C.")),
    ("(c)(i)", p("Draw the structural formula for " + b("J") + ". " + mk(2))),
    ("(c)(ii)", p("Suggest how separate samples of " + b("J") + " and " + b("K") + " can be distinguished from each other. " + mk(1))),
    ("(d)", p("Halogenoalkanes can react with aqueous sodium hydroxide to produce alcohols.") +
            p("A sample that contains one enantiomer of 2-bromooctane reacts completely with NaOH(aq) to produce one enantiomer of octan-2-ol.")),
    ("(d)(i)", p("Complete Fig. 4.3 to show the mechanism for this reaction. Use curly arrows to show the movement of electrons, and include relevant dipoles.") +
               FIG + c(b("Fig. 4.3") + " " + mk(3))),
    ("(d)(ii)", p("Identify the type of mechanism for this reaction. " + mk(1))),
    ("(e)", p(b("L") + ", " + b("M") + " and " + b("N") + " are three separate samples. Each sample contains a different halogenoalkane. "
              "One sample contains a chloroalkane, another sample contains a bromoalkane and the other sample contains an iodoalkane.") +
            p("Ethanolic AgNO" + sub(3) + "(aq) is added to equal amounts of each sample, heated to a constant temperature, and a stopwatch is started. "
              "The time for a precipitate to appear is recorded. The results are shown in Table 4.1.") + cap("Table 4.1") + t41),
    ("(e)(i)", p("Complete Table 4.1. " + mk(2))),
    ("(e)(ii)", p("Using relevant data from the " + i("Data Booklet") + ", explain why the times for precipitates to appear for " + b("L") + ", " + b("M") + " and " + b("N") + " are different. " + mk(2))),
    ("(f)", p("The reactions of chloroethane, chlorobenzene and ethanoyl chloride with water are investigated.") +
            p("Chlorobenzene does " + b("not") + " react with cold water. When cold water is added to ethanoyl chloride, a rapid reaction occurs.")),
    ("(f)(i)", p("Write an equation for the reaction of ethanoyl chloride with water. " + mk(1))),
    ("(f)(ii)", p("Give " + b("two") + " reasons why chlorobenzene does " + b("not") + " react with cold water. " + mk(2))),
    ("(f)(iii)", p("Explain the difference in reactivity of ethanoyl chloride compared to chloroethane when added to cold water. " + mk(1))),
])

# ---------------------------------------------------------------- Q5
EDTA = "EDTA" + sup("4" + M)
Y2 = "Y" + sup("2+")
XY = "X-Y" + sup("2+")
t51 = table(tr(th("ion"), th("concentration / " + MDM)),
            tr(td(CL_ + "(aq)"), td("0.016")), tr(td(ion("Na", "+") + "(aq)"), td("0.020")),
            tr(td(ion("Mg", "2+") + "(aq)"), td(b("U"))), tr(td("SO" + sub(4) + sup("2" + M) + "(aq)"), td("0.00029")),
            tr(td(ion("Ca", "2+") + "(aq)"), td(b("V"))), tr(td(ion("K", "+") + "(aq)"), td("0.00026")))
t52 = table(tr(th(""), th("volume of 0.00375 " + MDM + " " + EDTA + " added / cm" + sup("3"))),
            tr(td("titration 1"), td("16.80")), tr(td("titration 2"), td("8.00")))
t53 = table(tr(th(""), th(ion("Ca", "2+")), th(ion("Mg", "2+"))),
            tr(td(K + sub("sp") + " for metal hydroxide at 298 K / mol" + sup("3") + " dm" + sup(M + "9")),
               td("5.5 " + TIMES + " 10" + sup(M + "6")), td("1.1 " + TIMES + " 10" + sup(M + "11"))))
Q[5] = dict(marks=11, intro=[
    p("Different oceans contain slightly different concentrations of dissolved ions. The amount of ions present can be found by analysis of sea water samples taken from the oceans."),
    p("Table 5.1 shows the six most abundant ions present in a sample of sea water taken from an ocean, ocean 1."),
    cap("Table 5.1"), t51,
    p("The amounts of " + ion("Ca", "2+") + "(aq) and " + ion("Mg", "2+") + "(aq) present in a sample of sea water can be found by titration with " + EDTA +
      " using indicator X in alkaline conditions. (" + ion("Ca", "2+") + "(aq) and " + ion("Mg", "2+") + "(aq) will be represented as " + Y2 + " in this question.)"),
    p("When indicator X is added to sea water, it forms a complex ion with " + Y2 + "; the complex ion is pink and its formula is " + XY + ". This is shown in reaction 5.1."),
    eqn("reaction 5.1   X (blue)  +  " + Y2 + "  →  " + XY + " (pink)"),
    p("When alkaline " + EDTA + " is added to a solution containing " + XY + ", the complex ion (EDTA-Y)" + sup("2" + M) + " is formed. This is shown in reaction 5.2."),
    eqn("reaction 5.2   " + EDTA + "  +  " + XY + "  →  (EDTA-Y)" + sup("2" + M) + "  +  X"),
    p("When reaction 5.2 occurs at pH 10 and sufficient " + EDTA + " is added so that all " + Y2 + " ions are removed from the " + XY + " complex ion, X remains and the solution turns blue."),
    p(b("Description of method")),
    p("Titration 1"),
    ul("1 cm" + sup("3") + " of sea water is added to 50 cm" + sup("3") + " of deionised water in a conical flask followed by a few drops of X dissolved in a buffer at pH 10.",
       "0.00375 " + MDM + " " + EDTA + " is added until a permanent colour change appears.",
       "The total volume of " + EDTA + " added is recorded."),
    p("Titration 2"),
    ul("3 cm" + sup("3") + " of sea water is added to 50 cm" + sup("3") + " of deionised water in a conical flask followed by a few drops of X.",
       "NaOH(aq) is then added until the mixture has a pH of 12. Under these conditions, it is assumed that all the " + ion("Mg", "2+") +
       "(aq) has been removed from the solution and only the " + ion("Ca", "2+") + "(aq) ions are available to react with the " + EDTA + ".",
       "0.00375 " + MDM + " " + EDTA + " is added until a permanent colour change appears.",
       "The total volume of " + EDTA + " added is recorded."),
    p("Table 5.2 shows the results from these two titrations using sea water from ocean 1."),
    cap("Table 5.2"), t52],
  parts=[
    ("(a)(i)", p("At pH 10, the indicator species X may be represented as HIn" + sup("2" + M) + ".") +
               p("Complete the equation to show how X behaves as an acid at pH 10 when " + ion("Ca", "2+") + "(aq) is added.") +
               p("HIn" + sup("2" + M) + " + " + ion("Ca", "2+") + " → " + mk(1))),
    ("(a)(ii)", p("State the colour of the sea water sample with X before the addition of " + EDTA + " and the permanent colour that appears at the end-point of this titration. " + mk(1))),
    ("(b)", p("Use the information in Table 5.2 to calculate the values of " + b("U") + ", the concentration of " + ion("Mg", "2+") + "(aq), and " + b("V") +
              ", the concentration of " + ion("Ca", "2+") + "(aq), present in ocean 1 in " + MDM + ". " + mk(3))),
    ("(c)", p("Ocean 2 contains different concentrations of the ions listed in Table 5.1. The concentration of one of these ions, " + b("Q") +
              ", is calculated by adding an excess of BaC" + L + sub(2) + "(aq) to a 100 cm" + sup("3") + " sample of the sea water. "
              "The mixture is filtered to isolate the insoluble solid. The solid is then dried to constant mass.") +
            p("The mass of the dried white solid is 0.658 g.")),
    ("(c)(i)", p("Identify the ion " + b("Q") + ". " + mk(1))),
    ("(c)(ii)", p("Calculate the concentration in " + MDM + " of " + b("Q") + " in ocean 2. " + mk(1))),
    ("(d)", p("A sample of sea water from ocean 2 contains 0.0050 " + MDM + " of " + ion("Ca", "2+") + "(aq) and 0.0480 " + MDM + " of " + ion("Mg", "2+") +
              "(aq). The " + K + sub("sp") + " for the metal hydroxides of these ions is shown in Table 5.3.") + cap("Table 5.3") + t53),
    ("(d)(i)", p("Use your knowledge of solubility products and the information in Table 5.3 to explain why the " + ion("Ca", "2+") +
                 " ions in this sample remain in solution at pH 12 but the " + ion("Mg", "2+") + " ions do " + b("not") + ". Calculations are " + b("not") + " required. " + mk(2))),
    ("(d)(ii)", p("Show by relevant calculation that almost all the " + ion("Mg", "2+") + "(aq) present in this sample forms a precipitate at pH 12. " + mk(2))),
])

# ---------------------------------------------------------------- Q6
KSOL = K + sub("(solubility CO" + sub(2) + ")")
t61 = table(tr(td("temperature / °C"), td("25"), td("40"), td("80")),
            tr(td("p" + K + sub(2) + " for reaction 6.2<br>" + HCO3_ + " ⇌ " + CO32.replace("</sup>", "</sup>") + " + H" + sup("+")),
               td("9.00"), td("8.68"), td("8.16")))
Q[6] = dict(marks=12, intro=[
    p("Atmospheric carbon dioxide can dissolve in sea water."),
    p("The three inorganic carbon-containing species present in sea water are:"),
    ul("dissolved CO" + sub(2) + "(g)", CO32 + "(aq)", HCO3_ + "(aq)."),
    p("Increasing levels of CO" + sub(2) + "(g) in the atmosphere can change the proportions of these inorganic carbon-containing species present in sea water. This can lead to ocean acidification."),
    p("The relationship between the solubility of CO" + sub(2) + "(g) in water, " + KSOL + ", and the amount of CO" + sub(2) +
      "(g) present in air at equilibrium is described in expression 6.1."),
    eqn("expression 6.1   " + KSOL + " = " + frac("[CO" + sub(2) + "(g) present in water]", "partial pressure of CO" + sub(2) + "(g) in air")),
    c(KSOL + " = 0.034 mol kg" + sup(M + "1") + " atm" + sup(M + "1") + " at 298 K"),
    p("Reactions 6.1 and 6.2 show the two equilibria that regulate the concentration of the three inorganic carbon-containing species present in sea water "
      "and the values for their equilibrium constants. In reaction 6.1, the value for " + K + sub(1) + " assumes that the concentration of water is constant."),
    eqn("reaction 6.1   CO" + sub(2) + " + H" + sub(2) + "O ⇌ " + HCO3_ + " + H" + sup("+") + "     " + K + sub(1) + " = 1.45 " + TIMES + " 10" + sup(M + "6") + " " + MDM + " at 298 K"),
    eqn("reaction 6.2   " + HCO3_ + " ⇌ " + CO32 + " + H" + sup("+") + "     " + K + sub(2) + " = 1.10 " + TIMES + " 10" + sup(M + "9") + " " + MDM + " at 298 K"),
    p("When changes to the amount of dissolved carbon dioxide in the ocean occur, the pH of sea water remains approximately constant between pH 7.5 and 8.5. "
      "This is due to " + CO32 + "(aq) and " + HCO3_ + "(aq) acting as a buffer.")],
  parts=[
    ("(a)", p("Approximately 200 years ago, the average pH of sea water taken from the ocean surface was 8.2. At present, this is 8.1.") +
            p("Calculate the percentage increase in hydrogen ion concentration of the sea water taken from the ocean surface at present compared with 200 years ago. " + mk(3))),
    ("(b)", p("Pure water is exposed to air that contains CO" + sub(2) + "(g) at equilibrium at 298 K and a pressure of 1.009 bar, where 1 atm = 1.013 bar. "
              "The mole fraction of CO" + sub(2) + " in air is 4.2 " + TIMES + " 10" + sup(M + "4") + ".") +
            p("The density of water is 1.00 kg dm" + sup(M + "3") + ".") +
            p("Calculate the concentration of CO" + sub(2) + "(g) dissolved in this sample of water in " + MDM + ". Give your answer to " + b("three") + " significant figures. " + mk(2))),
    ("(c)(i)", p("Using information from reactions 6.1 and 6.2, suggest how the " + CO32 + "(aq) and " + HCO3_ + "(aq) buffer maintains the pH in sea water "
                 "as the amount of carbon dioxide gas in the atmosphere increases. " + mk(2))),
    ("(c)(ii)", p("Reaction 6.3 describes the overall reaction that occurs when more CO" + sub(2) + "(g) is dissolved in sea water with no overall change in pH.") +
                eqn("reaction 6.3   CO" + sub(2) + " + H" + sub(2) + "O + " + CO32 + " ⇌ 2" + HCO3_) +
                p("Deduce an expression for the equilibrium constant for reaction 6.3, " + K + sub(3) + ", using the relationship between " + K + sub(1) + " and " + K + sub(2) +
                  ". Hence, calculate a value and unit for " + K + sub(3) + " at 298 K, assuming that the concentration of water is constant. " + mk(3))),
    ("(c)(iii)", p("Deduce the most abundant inorganic carbon-containing species present in sea water at pH 8.1. Explain your answer. " + mk(1))),
    ("(d)", p("Table 6.1 shows the effect of temperature on p" + K + sub(2) + " for reaction 6.2 for a sample of sea water collected at a constant depth from one ocean.") +
            cap("Table 6.1") + t61 +
            p("By considering the p" + K + sub(2) + " values in Table 6.1, deduce the nature of reaction 6.2 as either endothermic or exothermic. " + mk(1))),
])

def lead_inline(h):
    """A part's FIRST paragraph is left bare so its text continues the line the label sits on
    (render_parts._render_owner(lead_inline=True)); a <p> is a block and would drop below the label."""
    if h.startswith("<p>"):
        j = h.index("</p>")
        return h[3:j] + h[j + 4:]
    return h

NB = "&nbsp;"
def nbsp(h):
    """Bind a value to its unit (and the factors of a x 10^n) so a line never breaks between them."""
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol)\b)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

# ---------------------------------------------------------------- assemble
def strip(h):
    h = re.sub(r'<span class="frac"><span class="fnum">(.*?)</span><span class="fden">(.*?)</span></span>',
               lambda m: "(%s)/(%s)" % (re.sub(r"<[^>]+>", "", m.group(1)), re.sub(r"<[^>]+>", "", m.group(2))), h)
    h = h.replace(FIG, " ").replace("<br>", " ")
    h = re.sub(r"</(p|li|tr|div)>", " ", h)
    h = re.sub(r"</(td|th)>", " | ", h)
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"\s+", " ", h).strip()

# figure slots (hand-snipped); owner label -> list of slots in DOM order
slot_for = lambda label, k: ("intro" if not label else label.replace("(", "").replace(")", "")) + ("" if k == 0 else str(k + 1))
rows, plan = [], []
for n in sorted(Q):
    d = Q[n]
    html_blocks = list(d["intro"])
    text_bits = [strip(" ".join(d["intro"]))]
    for label, h in d["parts"]:
        text_bits += [label, strip(h)]           # search text from the un-transformed blocks
        h = lead_inline(h)
        html_blocks.append('<div class="qpart"><span class="pl">%s</span> %s</div>' % (label, h))
    text_bits.append("[Total: %d]" % d["marks"])
    html = nbsp("\n".join(html_blocks))
    # marks cross-check: the part badges must sum to the printed question total
    got = sum(int(x) for x in re.findall(r'class="mk">\[(\d+)\]', html))
    assert got == d["marks"], (n, got, d["marks"])
    rows.append({"question_number": n, "type": "structured", "section": None, "marks": d["marks"],
                 "content_html": html, "content_text": re.sub(r"\s+", " ", " ".join(x for x in text_bits if x)).strip(),
                 "parts": [{"label": l} for l, _ in d["parts"]]})
    o = 1
    for label, h in [(None, "".join(d["intro"]))] + list(d["parts"]):
        for k in range(h.count(FIG)):
            slot = slot_for(label, k)
            plan.append({"question": n, "part": label, "slot": slot, "ordinal": o, "kind": "block",
                         "storage_path": "%s_%s_%s_Q%d_%s_%d.png" % (SCHOOL, LEVEL, PAPER, n, slot, YEAR)})
            o += 1
    nph = html.count('class="fig"'); nas = sum(1 for a in plan if a["question"] == n)
    assert nph == nas, (n, nph, nas)
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))
