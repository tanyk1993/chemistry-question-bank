"""Hand transcription of NJC 2026 H2 Prelim Paper 3 (9476/03, 5 structured) -> questions.json +
asset_plan.json. The school supplied a PDF only, so there is no extractor; same output contract as
extract_parts / build_njc26_p2.py, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_njc26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school NJC --year 2026 --paper 3 --level H2

Marks as ingested: Q1 16, Q2 23, Q3 16, Q4 20, Q5 20 = 95 (75 as sat: Section B is "answer one",
Q4 or Q5). Same convention as the other P3s. No Data-based flag (P3 rule).

Conventions as build_njc26_p2.py: [n] is a span.mk where the paper prints it; every figure is a block
<div class="fig"> placeholder with a typed bold centred caption; answer lines/boxes are not reproduced
(tables the candidate completes are typed); asset slot = part label without brackets, 'aiii2' for a
second figure in the same part. Bond hyphens are plain hyphens (ruling 2026-11-01); minus signs U+2212.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "NJC", "H2", "P3", 2026
FIG = '<div class="fig">figure</div>'
M = "−"                                   # minus sign U+2212
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
def ceqn(s): return '<p class="c eqn">%s</p>' % s
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def ol(*items): return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)

L = '<i class="el">l</i>'                  # element l
CL = "C" + L
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
EM = "&emsp;"
STD = sup('<span class="pl-sym">⦵</span>')
DOT = "•"
def F(s):
    """Formula string: subscript digits after a letter or ')', element l in Cl italic."""
    s = re.sub(r"(?<=[A-Za-z\)])(\d+)", lambda m: sub(m.group(1)), s)
    return s.replace("Cl", CL)
def pK(s): return "p" + K + sub(s)
def Ka(): return K + sub("a")
def Ksp(): return K + sub("sp")
def Kp(): return K + sub("p")
def dHr(): return DEL + i("H") + sub(i("r"))
def dGstd(): return DEL + i("G") + STD
def dGppt(): return DEL + i("G") + '<span class="stk post"><span><span class="pl-sym">⦵</span></span><span>ppt</span></span>'
def x10(a, n): return "%s × 10%s" % (a, sup(M + str(n)))
def chg(sym, ch): return F(sym) + sup(ch)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1
Q[1] = dict(marks=16, intro=[], parts=[
    ("(a)", p("The ozone molecule, " + F("O3") + ", contains a dative covalent bond.")),
    ("(a)(i)", p("Draw a 'dot-and-cross' diagram to show the bonding in a molecule of " + F("O3") + ". Include all outer shell electrons in your diagram. " + mk(1))),
    ("(a)(ii)", p("Suggest a value for the bond angle in " + F("O3") + ". Explain your answer. " + mk(2))),
    ("(a)(iii)", p("Ozone can act as a Lewis base.") + p("Draw the structure of the product formed when " + F("BF3") + " reacts with " + F("O3") + ". " + mk(1))),
    ("(b)", p("Atmospheric sulfur species play key roles in both acid rain precursor formation and stratospheric ozone depletion.") +
            p("Sulfuryl chloride, " + F("SO2Cl2") + " is a liquid with low boiling point. When sulfuryl chloride, " + F("SO2Cl2") +
              ", vapour reaches the stratosphere, it decomposes to give sulfur dioxide and chlorine radical. Under high-frequency UV radiation, "
              "the mixture undergoes a series of reactions leading to the destruction of ozone, " + F("O3") + ", as shown in Table 1.1.") +
            cap("Table 1.1") +
            table(tr(td(b("Step 1:")), td("One of the S-" + CL + " bonds in an " + F("SO2Cl2") + " molecule undergoes homolytic fission to generate a chlorine radical, " +
                                          CL + DOT + ", and a " + DOT + F("SO2Cl") + " radical.")),
                  tr(td(b("Step 2:")), td("The highly unstable " + DOT + F("SO2Cl") + " radical undergoes further homolytic fission, breaking its remaining S-" + CL +
                                          " bond to produce a sulfur dioxide molecule, " + F("SO2") + ", and a radical, " + CL + DOT + ".")),
                  tr(td(b("Step 3:")), td("The highly reactive " + CL + DOT + " radical collides with an ozone molecule, " + F("O3") + ", forming a chlorine monoxide radical, " +
                                          "C" + L + "O" + DOT + ", and an oxygen molecule, " + F("O2") + ".")),
                  tr(td(b("Step 4:")), td("The C" + L + "O" + DOT + " radical reacts with a free oxygen atom present in the stratosphere, forming another molecule of " + F("O2") +
                                          " and the " + CL + DOT + " radical."))) +
            p("In the lower atmosphere, " + F("NO2") + " acts as a homogeneous catalyst in converting " + F("SO2") + " to " + F("SO3") + ".") +
            p("The first step of the catalytic oxidation is shown in equation 1.1.") +
            ceqn("equation 1.1" + EM + F("SO2") + "(g) + " + F("NO2") + "(g) ⇌ " + F("SO3") + "(g) + NO(g)" + EM + dHr() + " = " + M + "41.8 kJ mol" + sup(M + "1"))),
    ("(b)(i)", p("Define the term homolytic fission. " + mk(1))),
    ("(b)(ii)", p("Use curly arrows to show the movement of electrons in step 1 by completing Figure 1.1.") + p(b("Step 1:")) + FIG + cap("Figure 1.1") + c(mk(1))),
    ("(b)(iii)", p("Name the reactions for " + b("steps 1") + " and " + b("3") + ". " + mk(1))),
    ("(b)(iv)", p("State the role of the chlorine radical in the overall destruction of ozone and explain your answer by referring to Table 1.1. " + mk(2))),
    ("(b)(v)", p("Figure 1.2 shows how the temperature of the atmosphere varies with height from the ground.") + FIG + cap("Figure 1.2") +
               p("Suggest how the position of equilibrium of equation 1.1 differs at a height of " + b("20 km") + " compared with a height of " + b("50 km") + " from the ground.") +
               p("Explain your answer. " + mk(2))),
    ("(c)", p("4-acetamidomethylbenzene is formed by the three-step route shown in Figure 1.3.") + FIG + cap("Figure 1.3")),
    ("(c)(i)", p("Draw the structure of each of the organic products, " + b("T") + " and " + b("U") + " in Figure 1.3. " + mk(2))),
    ("(c)(ii)", p("Give the reagents and conditions needed for steps 1 to 3. " + mk(3))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=23, intro=[], parts=[
    ("(a)", p("A solution containing hydrazoic acid, " + F("HN3") + "(aq), and azide ion, " + chg("N3", M) + "(aq), can act as a buffer. The value of the acid dissociation constant, " +
              Ka() + ", for " + F("HN3") + "(aq) is 1.8 × 10" + sup(M + "5") + " " + MDM + " at 298 K.")),
    ("(a)(i)", p("Describe how a solution containing " + F("HN3") + "(aq) and " + chg("N3", M) + "(aq) can act as a buffer. Include relevant equations to illustrate your answer. " + mk(2))),
    ("(a)(ii)", p("A buffer solution is prepared by mixing 50.0 cm" + sup(3) + " of 0.500 " + MDM + " " + F("HN3") + " and 25.0 cm" + sup(3) + " of 0.600 " + MDM + " NaOH.") +
                p("Calculate the pH of the buffer solution formed at 298 K. Show your working. " + mk(2))),
    ("(a)(iii)", p("Ethanal reacts readily with " + F("HN3") + "(aq) to form product " + b("Q") + ".") + FIG +
                 p("The first step of this mechanism involves the reaction of ethanal with " + chg("N3", M) + ". The structure of the " + chg("N3", M) + " ion is shown.") + FIG +
                 p("Suggest the mechanism of this reaction. Include all relevant lone pairs, dipoles, curly arrows and charges. " + mk(3))),
    ("(b)", p("Burning sodium in air produces a mixture of sodium oxide, " + F("Na2O") + ", and sodium peroxide, " + F("Na2O2") +
              ". The proportion of sodium peroxide in the mixture can be determined by the following method.") +
            ul("The mixture is dissolved in water and the following reaction takes place." + ceqn(F("Na2O2") + " + 2" + F("H2O") + " → 2 NaOH + " + F("H2O2")),
               "The solution is acidified and an excess of potassium iodide solution is added. Iodine is liberated by the following reaction." +
               ceqn("2KI + " + F("H2O2") + " + 2H" + sup("+") + " → 2" + F("H2O") + " + 2K" + sup("+") + " + " + F("I2")),
               "The iodine liberated is titrated with standard sodium thiosulfate solution." + ceqn("2" + F("Na2S2O3") + " + " + F("I2") + " → " + F("Na2S4O6") + " + 2NaI")) +
            p("When a sample of the mixed oxides, of mass 0.500 g, was treated in this way, it was found that 16.70 cm" + sup(3) + " of 0.200 " + MDM + " " + F("Na2S2O3") +
              " was required to react with all the iodine released.") +
            p("Calculate the ratio " + frac("mass of " + F("Na2O"), "mass of " + F("Na2O2")) + " in the oxide mixture to five significant figures. " + mk(2))),
    ("(c)", p("The reaction between acyl chloride and hydrogen peroxide produces peroxyacid.") + FIG +
            p("The " + pK("a") + " values of four compounds are listed in Table 2.1 below.") + cap("Table 2.1") +
            table(tr(th("name"), th("formula"), th(pK("a"))),
                  tr(td("water"), td(F("H2O")), td("14.0")),
                  tr(td("hydrogen peroxide"), td(F("H2O2")), td("11.7")),
                  tr(td("ethanoic acid"), td(F("CH3CO2H")), td("4.8")),
                  tr(td("peroxyethanoic acid"), td(F("CH3CO3H")), td("8.2"))) +
            p("Suggest an explanation for why")),
    ("(c)(i)", p("the " + pK("a") + " value of " + F("H2O2") + " is less than that for water. " + mk(2))),
    ("(c)(ii)", p("the " + pK("a") + " value of " + F("CH3CO3H") + " is more than that for " + F("CH3CO2H") + ". " + mk(1))),
    ("(d)", p("Peroxyethanoic acid, " + F("CH3CO3H") + ", reacts with ketones to give esters.") +
            ceqn("RCOR’ + " + F("CH3CO3H") + " → " + F("RCO2R’") + " + " + F("CH3CO2H")) +
            p("Ketone " + b("A") + " was reacted in this way to give ester " + b("B") + ".<br>When heated with " + F("H2SO4") + "(aq), " + b("B") + " gave compound " + b("C") + ", " +
              F("C5H12O") + ", and compound " + b("D") + ", " + F("C8H8O2") + ".") +
            p("Compound " + b("D") + " could be synthesised from methylbenzene shown in Figure 2.1.") + FIG + cap("Figure 2.1")),
    ("(d)(i)", p("Suggest the structures for compounds " + b("G") + " and " + b("D") + ". " + mk(2))),
    ("(d)(ii)", p("Give the reagents and conditions for the reactions " + b("II") + " and " + b("III") + ". " + mk(2)),
     p("Compound " + b("C") + ", " + F("C5H12O") + ", gave a yellow precipitate when treated with alkaline aqueous iodine, and produced two isomeric products " + b("E") + " and " + b("F") +
       " of formula " + F("C5H10") + " when heated with concentrated phosphoric acid.") +
     p("On treatment with hot acidified " + F("KMnO4") + ", " + b("E") + " produced " + F("C3H6O") + " and " + F("C2H4O2") + ".")),
    ("(d)(iii)", p("Suggest possible structures for " + b("C") + ", " + b("E") + " and " + b("F") + ".") + p("For each reaction, state the type of reaction described. " + mk(4))),
    ("(d)(iv)", p("Using your structures for " + b("C") + " and " + b("D") + ", deduce the structures for " + b("A") + " and " + b("B") + ". " + mk(2))),
    ("(d)(v)", p("Ketene is a highly reactive organic compound used in the synthesis of pharmaceuticals. It reacts readily with water to form carboxylic acid as shown.") + FIG +
               p("Suggest a possible structure of the ketene that reacts with " + F("H2O") + " to form " + b("D") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q3
Q[3] = dict(marks=16, intro=[], parts=[
    ("(a)", p("This question is about copper.") + cap("Table 3.1") +
            table(tr(th(""), th("calcium"), th("copper")),
                  tr(td("atomic radius / nm"), td("0.197"), td("0.128")),
                  tr(td("ionic radius / nm"), td("0.099"), td("0.073")),
                  tr(td("melting point / °C"), td("843"), td("1084")),
                  tr(td("electronic configuration"), td("[Ar]4s" + sup(2)), td("[Ar]3d" + sup(10) + "4s" + sup(1))))),
    ("(a)(i)", p("Using data from Table 3.1, give " + b("two") + " reasons to explain why the melting point of copper is higher than calcium. " + mk(2)),
     p("Metal nitrates generally undergo thermal decomposition to give metal oxides, nitrogen dioxide and oxygen.")),
    ("(a)(ii)", p("Write an equation, with state symbols, for the decomposition of copper(II) nitrate. " + mk(1))),
    ("(a)(iii)", p("Predict whether copper(II) nitrate would decompose at a higher or lower temperature than calcium nitrate. Explain your answer. " + mk(2))),
    ("(b)", p("Copper is widely used to manufacture industrial plumbing networks due to its relative chemical inertness and resistance to corrosion by dilute acids.")),
    ("(b)(i)", p("Use suitable data from the " + i("Data Booklet") + " to prove that the corrosion of solid copper by dilute acid is not spontaneous. " + mk(1))),
    ("(b)(ii)", p("Use your answer to (i) to calculate the standard Gibbs free energy change, " + dGstd() + ", per mole of Cu reacted. " + mk(1))),
    ("(b)(iii)", p("However, in industrial areas where liquid waste contains a high concentration of chloride ions, copper pipes corrode spontaneously to give a yellowish-green mixture.") +
                 p("With the aid of relevant equation(s), explain the observation. " + mk(2))),
    ("(c)", p("To remove the toxic copper-containing species from the waste solution, a chelating agent called " + b("EDTA" + sup("4" + M)) + " is added. EDTA" + sup("4" + M) +
              " is a hexadentate ligand that forms a stable complex ion with Cu" + sup("2+") + ".")),
    ("(c)(i)", p("Explain what is meant by the term " + i("ligand") + ". " + mk(1))),
    ("(c)(ii)", p("Write an ionic equation for the ligand exchange reaction between the copper-containing species in " + b("(b)(iii)") + " and EDTA" + sup("4" + M) + ". " + mk(1))),
    ("(c)(iii)", p("State the sign of the entropy change, " + DEL + "S, for the ligand exchange reaction in " + b("(c)(ii)") + ". Explain your answer. " + mk(1))),
    ("(d)", p("When a particular copper ore was reduced, an impure copper with iron and silver as minor impurities was obtained. It contained no other metal.")),
    ("(d)(i)", p("Draw a labelled diagram of the electrolysis cell used to purify the piece of impure copper.") + p("Include details of the cathode, anode and electrolyte. " + mk(1))),
    ("(d)(ii)", p("Explain, with reference to relevant " + i("E") + STD + " values, what happens to the iron and silver impurities during this purification procedure. " + mk(3))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=20, intro=[
    p("Silver forms a series of halides of general formula AgX. The chloride, bromide and iodide of silver are sparingly soluble in water at room temperature."),
    p("Data about the solubilities in water and the solubility products of the chloride, bromide and iodide of silver at 298 K are given in Table 4.1."),
    cap("Table 4.1"),
    table(tr(th("salt"), th("solubility / " + MDM), th("solubility product / mol" + sup(2) + " dm" + sup(M + "6"))),
          tr(td("AgC" + L), td(x10("1.4", 5)), td(x10("2.0", 10))),
          tr(td("AgBr"), td(x10("7.1", 7)), td(x10("5.0", 13))),
          tr(td("AgI"), td(x10("8.9", 9)), td(i("y")))),
], parts=[
    ("(a)(i)", p("Write an expression for the solubility product, " + Ksp() + " of silver iodide. " + mk(1))),
    ("(a)(ii)", p("From the data above, determine the value of " + i("y") + ". " + mk(1))),
    ("(a)(iii)", p("To a 1.0 dm" + sup(3) + " of saturated solution of AgI, 0.025 g of " + F("AgNO3") + "(s) was added. Calculate [I" + sup(M) + "(aq)] in the resulting solution. " + mk(2))),
    ("(b)", p("When a precipitate is formed, " + dGppt() + " is given by the following expression.") +
            ceqn(dGppt() + " (in J mol" + sup(M + "1") + ") = 2.303 " + i("RT") + " log" + sub(10) + " " + Ksp() + EM + EM + "where " + i("R") + " = molar gas constant, " + i("T") +
                 " = temperature (in K)")),
    ("(b)(i)", p("Use the data in Table 4.1 to calculate " + dGppt() + ", for silver chloride. " + mk(1))),
    ("(b)(ii)", p("When silver nitrate is added to solution containing chloride ions,") + p("the following observations are made:") +
                ol("A white precipitate is observed.", "The white precipitate dissolves when aqueous ammonia is added.",
                   "Only a cream precipitate is obtained when aqueous sodium bromide is added to the resultant mixture.") +
                p("With the aid of suitable equations, explain the chemistry behind these three observations. " + mk(3))),
    ("(c)", p("Unlike silver halides, chromium(III) chloride is soluble in water.") +
            p("Explain, with the aid of an equation, why a solution of chromium(III) chloride is acidic. " + mk(2))),
    ("(d)", p("Caftaric acid, " + F("C13H12O9") + ", is a compound found in grapes and is responsible for the yellowish-gold colour seen in some white wines.") + FIG),
    ("(d)(i)", p("State the type(s) of stereoisomerism exhibited by caftaric acid. " + mk(1))),
    ("(d)(ii)", p("Hence, state the total number of stereoisomers of caftaric acid. " + mk(1))),
    ("(d)(iii)", p("By reference to the hybridisation of the atoms and orbital overlap, describe the covalent bonding between C" + sub(1) + " and O" + sub(1) + " in caftaric acid.") +
                 p("You may use a labelled diagram to illustrate your answer. " + mk(2))),
    ("(e)", p("On heating with dilute aqueous acid, caftaric acid produces two compounds " + b("A") + " and " + b("B") + ".") + FIG),
    ("(e)(i)", p("State the " + i("type of reaction") + " caftaric acid is undergoing when " + b("A") + " and " + b("B") + " are formed. " + mk(1))),
    ("(e)(ii)", p(b("A") + " exists as three stereoisomers, " + b("A" + sub(1)) + ", " + b("A" + sub(2)) + " and " + b("A" + sub(3)) + ".") +
                p(b("A" + sub(1)) + " has no effect on plane polarised light.") +
                p("Explain why " + b("A" + sub(1)) + " has no effect on plane polarised light. " + mk(1))),
    ("(e)(iii)", p("Compounds " + b("C") + " and " + b("D") + " are constitutional isomers of " + b("B") + ".") +
                 ul(b("C") + " reacts with both " + F("H2") + ", Ni " + b("and") + " LiA" + L + "H" + sub(4) + ".",
                    b("D") + " only reacts with LiA" + L + "H" + sub(4) + " but " + b("not") + " " + F("H2") + ", Ni.") +
                 p("Suggest the structures of " + b("C") + " and " + b("D") + ". " + mk(2)) +
                 table(tr(th(b("C")), th(b("D"))), tr(td("<br><br><br><br><br><br>"), td("")))),
    ("(f)", p("Compounds " + b("E") + " and " + b("F") + " are also constitutional isomers of each other.") + FIG +
            p("Describe a simple chemical test that distinguishes " + b("E") + " from " + b("F") + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Natural gas, consisting primarily of methane, is available in large amounts and is used as a fuel.") +
            p("In 2013, scientists discovered that they could selectively convert methane to alkenes using gaseous sulfur, " + F("S2") +
              ", over a suitable catalyst. This conversion takes place at over 1000 K, where sulfur exists as " + F("S2") + "(g), as shown in reaction 5.1.") +
            p("reaction 5.1" + EM + EM + "2" + F("CH4") + "(g) + " + F("S2") + "(g) → " + F("C2H4") + "(g) + 2" + F("H2S") + "(g)") +
            p("Calculate the enthalpy change of reaction 5.1 by drawing an energy cycle using the information in Table 5.1.") + cap("Table 5.1") +
            table(tr(th(""), th(dHr() + " / kJ mol" + sup(M + "1"))),
                  tr(td(F("CH4") + "(g) + 2" + F("S2") + "(g) → " + F("CS2") + "(g) + 2" + F("H2S") + "(g)"), td("+96.0")),
                  tr(td(F("C2H4") + "(g) + 3" + F("S2") + "(g) → 2" + F("CS2") + "(g) + 2" + F("H2S") + "(g)"), td("+91.0"))) +
            c(mk(2))),
    ("(b)", p("The key stage in the manufacture of sulfuric acid is the reaction between sulfur dioxide and oxygen over a catalyst.") +
            ceqn("2" + F("SO2") + "(g) + " + F("O2") + "(g) ⇌ 2" + F("SO3") + "(g)")),
    ("(b)(i)", p("Write the " + Kp() + " expression for the above reaction, stating the units. " + mk(1))),
    ("(b)(ii)", p("When an equimolar mixture of " + F("SO2") + " and " + F("O2") + " is placed in a sealed vessel at " + i("T") + " °C at an initial total pressure of 200 kPa, "
                  "the percentage conversion of " + F("SO2") + "(g) is 98%.") +
                p("Calculate the equilibrium partial pressure of each of the three gases. Hence, calculate the value of " + Kp() + " at temperature " + i("T") + " °C. " + mk(2))),
    ("(b)(iii)", p("Explain the effect on the percentage conversion and the value of " + Kp() + " when equimolar amounts of " + F("SO2") + " and " + F("O2") + " reacts in a larger vessel at " +
                   i("T") + " °C. " + mk(2))),
    ("(c)", p("Swift Enterprises, a chemical company, has proposed 2-methylbutane as a fuel for light airplanes.") + FIG +
            p("2-methylbutane can react with chlorine in the presence of UV light to give substitution products. Table 5.2 shows the relative reactivity of different types of "
              "hydrogen for this reaction.") + cap("Table 5.2") +
            table(tr(th("types of hydrogen"), th("relative reactivity")),
                  tr(td("primary"), td("1")), tr(td("secondary"), td("3.5")), tr(td("tertiary"), td("5")))),
    ("(c)(i)", p("Draw the structures of all the monochlorinated products for 2-methylbutane (ignoring stereoisomers), and give the relative proportions of all the products obtained "
                 "using the data in Table 5.2. " + mk(3))),
    ("(c)(ii)", p("Monochlorinated alkanes serve as precursors in the synthesis of hydrochlorofluorocarbons (HCFCs). Although initially adopted as transitional substitutes for CFCs due to "
                  "their lower Ozone Depletion Potential (ODP), HCFCs are currently being phased out worldwide.") +
                p("State " + b("one") + " other environmental hazard associated with HCFCs. " + mk(1))),
    ("(d)", p("Compound " + b("I") + " can be formed from compound " + b("G") + " via a two-step synthesis as shown in Figure 5.1.") + FIG + cap("Figure 5.1")),
    ("(d)(i)", p("Suggest the structure of intermediate " + b("H") + " in this synthesis. " + mk(1))),
    ("(d)(ii)", p("State the reagents and conditions used in step 1 and step 2. " + mk(2))),
    ("(d)(iii)", p(b("L") + " is a constitutional isomer of " + b("I") + ".") +
                 ul(b("L") + " contains two chiral centres.", b("L") + " does not give a cream precipitate when heated with ethanolic silver nitrate.") +
                 p("Suggest a structure of " + b("L") + ". " + mk(1)),
     p("In step 3, " + b("I") + " is heated with aqueous potassium hydroxide and the resulting mixture is then distilled. " + b("J") +
       " is collected as the distillate and " + b("K") + " remains in the distillation flask.")),
    ("(d)(iv)", p("Suggest the structures of compounds " + b("J") + " and " + b("K") + ". " + mk(2))),
    ("(e)", p("Concentrated potassium hydroxide is added dropwise to a mixture containing 0.200 " + MDM + " Cu" + sup("2+") + "(aq) and 0.200 " + MDM + " Pd" + sup("2+") +
              "(aq) to separate the two cations.") +
            p("The numerical values of the solubility products of " + F("Cu(OH)2") + " and " + F("Pd(OH)2") + " are given in Table 5.3 below.") + cap("Table 5.3") +
            table(tr(th("hydroxide"), th("solubility product, " + Ksp())),
                  tr(td(F("Cu(OH)2")), td(x10("2.20", 20))), tr(td(F("Pd(OH)2")), td(x10("1.00", 31))))),
    ("(e)(i)", p("Determine the hydroxide ion concentration at maximum separation, when " + F("Cu(OH)2") + " is just about to precipitate out from solution. " + mk(1))),
    ("(e)(ii)", p("The two cations are said to be effectively separated when only 0.01% of Pd" + sup("2+") + "(aq) is left in the solution.") +
                p("Calculate the concentration of Pd" + sup("2+") + "(aq) remaining in solution at maximum separation. Hence comment whether potassium hydroxide can be used to "
                  "separate the two cations effectively. " + mk(2))),
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
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b|nm\b|ppm\b|mg\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol)\b)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

# ---------------------------------------------------------------- assemble
def strip(h):
    h = re.sub(r'<span class="frac"><span class="fnum">(.*?)</span><span class="fden">(.*?)</span></span>',
               lambda m: "%s/%s" % (re.sub(r"<[^>]+>", "", m.group(1)), re.sub(r"<[^>]+>", "", m.group(2))), h)
    h = h.replace(FIG, " ").replace("<br>", " ")
    h = re.sub(r"</(p|li|tr|div)>", " ", h)
    h = re.sub(r"</(td|th)>", " | ", h)
    h = re.sub(r"<span[^>]*>\s*</span>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ").replace("\u25ba", "→")
    return re.sub(r"\s+", " ", h).strip()

# Names printed in a snipped figure that content_text should still carry (search only).
EXTRA_TEXT = {}

slot_for = lambda label, k: ("intro" if not label else label.replace("(", "").replace(")", "")) + ("" if k == 0 else str(k + 1))
rows, plan = [], []
for n in sorted(Q):
    d = Q[n]
    parts = [(x + ("",))[:3] for x in d["parts"]]
    html_blocks = list(d["intro"])
    text_bits = [strip(" ".join(d["intro"]))]
    for label, h, tail in parts:
        text_bits += [label, strip(h), EXTRA_TEXT.get((n, label), ""), strip(tail)]
        html_blocks.append('<div class="qpart"><span class="pl">%s</span> %s</div>' % (label, lead_inline(h)))
        if tail:
            html_blocks.append(tail)
    text_bits.append("[Total: %d]" % d["marks"])
    html = nbsp("\n".join(html_blocks))
    got = sum(int(x) for x in re.findall(r'class="mk">\[(\d+)\]', html))
    assert got == d["marks"], (n, got, d["marks"])
    rows.append({"question_number": n, "type": "structured", "section": None, "marks": d["marks"],
                 "content_html": html, "content_text": re.sub(r"\s+", " ", " ".join(x for x in text_bits if x)).strip(),
                 "parts": [{"label": l} for l, _, _ in parts]})
    o = 1
    for label, h in [(None, "".join(d["intro"]))] + [(l, h + t) for l, h, t in parts]:
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
