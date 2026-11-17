"""Hand transcription of RI 2026 H2 Prelim Paper 2 (9476/02, 5 structured Q, 75 marks) -> questions.json +
asset_plan.json. The question text is typed here from the school's Word file and the Word-exported PDF (the two agree);
light typo/grammar fixes follow the standing NYJC defaults and are listed in the handoff note. Same output contract as
extract_parts, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_ri26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school RI --year 2026 --paper 2 --level H2

Conventions (see claude/style-guide.md; same as build_nyjc26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('aii'), 'b2' for a second figure in the same part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "RI", "H2", "P2", 2026
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
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def ion(sym, ch): return sym + sup(ch)

L = '<i class="el">l</i>'                  # element l
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
SN1, SN2 = "S" + sub("N") + "1", "S" + sub("N") + "2"
FE2, FE3 = ion("Fe", "2+"), ion("Fe", "3+")
HALF = frac("1", "2")


# ---- extra helpers --------------------------------------------------------------------------
CL = "C" + L
kk = i("k")
def pK(s): return "p" + K + sub(s)
def dH(s=""): return DEL + i("H") + (sub(s) if s else "")
def long_arrow(w):
    return ('<span style="display:flex;align-items:center;width:%sem;margin:0 auto">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.55em;margin-left:-.3em;line-height:1">►</span></span>' % w)
def over(top, arrow, bottom=None, wide=False):
    pad = "padding:0 .35em;" if wide else "padding:0 .15em;"
    small = '<span style="display:block;font-size:.72em;line-height:1.15">%s</span>'
    out = ('<span style="display:inline-block;vertical-align:middle;text-align:center;'
           'line-height:1.1;%s">' % pad) + small % top
    out += '<span style="display:block;line-height:1">%s</span>' % arrow
    out += small % (bottom or "&nbsp;")
    return out + "</span>"
def ceqn(s): return '<p class="c eqn">%s</p>' % s
EM = "&emsp;"
OH = "OH" + sup(M)
HP = "H" + sup("+")
STD = sup("⦵")
H2O = "H" + sub(2) + "O"

# Parts are (label, html) or (label, html, tail). `tail` is text/figure the paper prints AFTER the part's
# mark and BEFORE the next label (it introduces the next sub-part); it is emitted as bare blocks between
# the qpart divs, the same shape render_parts gives a QLEVEL tail on the extractor path.
Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---- NYJC-specific helpers -------------------------------------------------------------------
CL = "C" + L
ARm = i("A") + sub("r")
MRm = i("M") + sub("r")
KSP = i("K") + sub("sp")
KA = i("K") + sub("a")
DEG = "°C"
def tdc(s, n=2): return '<td colspan="%d">%s</td>' % (n, s)
def unit_minus(n): return sup(M + str(n))
NH3OH = "NH" + sub(3) + "OH"
NH3OHP = NH3OH + sup("+")
def under(sym, label):
    """a species with its label printed directly underneath (Q7(c) 'red' / 'colourless')"""
    return ('<span style="display:inline-block;text-align:center;vertical-align:top;line-height:1.25">%s'
            '<span style="display:block;font-size:.95em">%s</span></span>' % (sym, label))
RARR = "⇌"

# ---- RI-specific helpers ---------------------------------------------------------------------
AL = "A" + L
AL2O3 = AL + sub(2) + "O" + sub(3)
FE2O3 = "Fe" + sub(2) + "O" + sub(3)
ALOH3 = AL + "(OH)" + sub(3)
def stkr(bottom):
    """a standard-state sign stacked over a subscript (dG_r, dH_c), as NJC 2026 P3"""
    return '<span class="stk post"><span><span class="pl-sym">⦵</span></span><span>%s</span></span>' % bottom
DG_R, DH_C = DEL + i("G") + stkr("r"), DEL + i("H") + stkr("c")
DS_R = DEL + i("S") + sub("r")
ECELL = i("E") + '<span class="stk post"><span><span class="pl-sym">⦵</span></span><span>cell</span></span>'
KP = i("K") + sub("p")
PKA = "p" + i("K") + sub("a")
LI = "Li" + sup("+")
HCO3 = "HCO" + sub(3) + sup(M)
CO3 = "CO" + sub(3) + sup("2" + M)
H2CO3 = "H" + sub(2) + "CO" + sub(3)
HAQ = "H" + sup("+") + "(aq)"
DOTS = "………………"
def arrow(w=3.5): return over("&nbsp;", long_arrow(w))
def dp(s): return p(s)

# ---------------------------------------------------------------- Q1
Q[1] = dict(marks=13, intro=[], parts=[
    ("(a)", p("In terms of structure and bonding, explain the variation of melting points between Na" + sub(2) + "O, SiO" + sub(2) + " and SO" + sub(3) + ". " + mk(4))),
    ("(b)", p("Table 1.1 shows the melting points of MgO and " + AL2O3 + ".") + cap("Table 1.1") +
            table(tr(th("compound"), th("melting point / °C")),
                  tr(td("MgO"), td("2830")),
                  tr(td(AL2O3), td("2054"))) +
            p("Explain the difference in the melting points of MgO and " + AL2O3 + ". " + mk(2))),
    ("(c)", p(AL2O3 + " is produced commercially from bauxite ore via the Bayer process. Bauxite consists mainly of hydrated " + AL2O3 + ", with " + FE2O3 +
              " as an impurity.") +
            p("Impure " + AL2O3 + " is first treated with NaOH(aq) at an elevated temperature, where " + FE2O3 + " does not react with NaOH(aq).")),
    ("(c)(i)", p("Write an equation for this step. " + mk(1))),
    ("(c)(ii)", p("Suggest how " + FE2O3 + " is removed in this step. " + mk(1)),
     p("The second step involves cooling the resultant solution, which results in the precipitation of " + ALOH3 + ".") +
     p("The final step involves the thermal decomposition of " + ALOH3 + " to form " + AL2O3 + ", carried out at 1000 °C in a reaction vessel of fixed volume.") +
     ceqn("2" + ALOH3 + "(s) " + RARR + " " + AL2O3 + "(s) + 3" + H2O + "(g)" + EM + EM + DEL + i("H") + " > 0") +
     p("Table 1.2 shows the percentage yield of " + AL2O3 + "(s) under different pressures.") + cap("Table 1.2") +
     table(tr(th("pressure / atm"), th("% yield")),
           tr(td("1.0"), td("82.0")),
           tr(td("5.0"), td("60.0")),
           tr(td("10.0"), td("45.0")))),
    ("(c)(iii)", p("Suggest a cost-effective way of increasing the yield of " + AL2O3 + " in this final step of the Bayer process. " + mk(1)),
     p("Table 1.3 shows some thermodynamic data for the decomposition of " + ALOH3 + ".") + cap("Table 1.3") +
     table(tr(th("temperature / °C"), th(DG_R + " / kJ mol" + sup(M + "1"))),
           tr(td("1000"), td(M + "422.17")),
           tr(td("1500"), td(M + "660.78")))),
    ("(c)(iv)", p("State the equation that relates " + DEL + i("G") + sub("r") + " to " + DEL + i("H") + sub("r") + " and " + DS_R + ". " + mk(1))),
    ("(c)(v)", p("Use Table 1.3 to calculate " + DS_R + " in J K" + sup(M + "1") + " mol" + sup(M + "1") + ". " + mk(2))),
    ("(c)(vi)", p("Suggest how the " + DS_R + " might change if the temperature was below 100 °C. " + mk(1))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=15, intro=[], parts=[
    ("(a)", p("State " + b("two") + " basic assumptions of kinetic theory as applied to an ideal gas. " + mk(2)),
     p("Ethanol, hydrogen, octane and pentane are examples of fuels used in automobiles.") +
     p("Table 2.1 shows some properties of ethanol, pentane and octane.") + cap("Table 2.1") +
     table(tr(th("compound"), th("boiling point / °C"), th(MRm), th(DH_C + " / kJ mol" + sup(M + "1"))),
           tr(td("ethanol"), td("78"), td("46.0"), td(M + "1367")),
           tr(td("pentane"), td("36"), td("72.0"), td(M + "3509")),
           tr(td("octane"), td("125"), td("114.0"), td(M + "5471")))),
    ("(b)(i)", p("State the general gas equation. " + mk(1))),
    ("(b)(ii)", p("Hence, calculate the volume occupied by 5.0 g of gaseous octane at 250 °C and 1.0 atm. " + mk(1))),
    ("(b)(iii)", p("Use data from Table 2.1 to arrange the three gases in order of increasing relative deviation from ideal gas behaviour at moderately "
                   "high pressure. Explain your answer. " + mk(2))),
    ("(c)", p("Hydrogen is mainly produced by the steam-methane reforming reaction in the industry.") +
            ceqn(H2O + "(g) + CH" + sub(4) + "(g) " + RARR + " CO(g) + 3H" + sub(2) + "(g)" + EM + EM + DEL + i("H") + " = +193 kJ mol" + sup(M + "1"))),
    ("(c)(i)", p("Explain what is meant by dynamic equilibrium. " + mk(1))),
    ("(c)(ii)", p("Equimolar amounts of steam and methane are added to a sealed vessel and heated to 1000 K. At equilibrium, 40.7% of the methane has "
                  "reacted. The total pressure in the vessel is 10.0 atm at equilibrium.") +
                p("Calculate the value of " + KP + " for this reaction, giving its units. " + mk(3))),
    ("(c)(iii)", p("In another steam-methane equilibrium mixture, the volume of the container is halved at constant temperature.") +
                 p("Explain how the partial pressure of methane changes with time until the system reaches a new equilibrium. " + mk(2))),
    ("(c)(iv)", p("At time = " + i("t") + sub(0) + ", another steam-methane mixture is at equilibrium. The temperature of this mixture is decreased "
                  "instantaneously at constant volume at time = " + i("t") + sub(1) + " and a new equilibrium is established at time = " + i("t") + sub(2) + ".") +
                p("Complete Figure 2.1 below to show how the forward rate changes from " + i("t") + sub(0) + " onwards.") + FIG + cap("Figure 2.1") + c(mk(3))),
])

# ---------------------------------------------------------------- Q3
Q[3] = dict(marks=16, intro=[
    p("Polar functional groups in organic compounds that contain an electron-deficient carbon atom are prone to reacting with nucleophiles."),
], parts=[
    ("(a)", p("The compounds in Table 3.1 react with KCN. Complete Table 3.1 by stating the reagents and conditions required and identifying the type "
              "of reaction which occurs.") + cap("Table 3.1") +
            table(tr(th("compound"), th("reagents and conditions required for reaction"), th("type of reaction")),
                  tr(td("CH" + sub(3) + "CH" + sub(2) + CL), td(""), td("")),
                  tr(td("(CH" + sub(3) + ")" + sub(2) + "CO"), td(""), td(""))) + c(mk(2))),
    ("(b)", p("The " + PKA + " data for some common compounds are given in Table 3.2.") + cap("Table 3.2") +
            table(tr(th("compound"), th(PKA), th("conjugate base")),
                  tr(td("HBr"), td(M + "9"), td("Br" + sup(M))),
                  tr(td("CH" + sub(3) + "COOH"), td("4.8"), td("CH" + sub(3) + "COO" + sup(M))),
                  tr(td(H2O), td("15.7"), td(OH)),
                  tr(td("CH" + sub(3) + "CH" + sub(2) + "OH"), td("16"), td("CH" + sub(3) + "CH" + sub(2) + "O" + sup(M))),
                  tr(td("CH" + sub(4)), td("50"), td("CH" + sub(3) + sup(M))))),
    ("(b)(i)", p("State the relationship between the " + PKA + " of the compounds and the stability of their conjugate bases. " + mk(1))),
    ("(b)(ii)", p("Explain the relative acidities of HBr, CH" + sub(3) + "COOH and CH" + sub(3) + "CH" + sub(2) + "OH by identifying the factors influencing the "
                  "stability of their conjugate bases, or otherwise. " + mk(3))),
    ("(c)", p("Under alkaline conditions, ethyl ethanoate undergoes hydrolysis via a mechanism shown in Figure 3.1.") + FIG + cap("Figure 3.1")),
    ("(c)(i)", p("Complete the mechanism for steps 1 and 2 given in Figure 3.1. Include all relevant lone pairs, dipoles and curly arrows. " + mk(2))),
    ("(c)(ii)", p("In step 2 of the mechanism, the ethoxide anion is eliminated instead of the methide ion, CH" + sub(3) + sup(M) + ", as shown in Figure 3.2.") +
                p("Use information from part " + b("(b)") + " to explain Figure 3.2.") + FIG + cap("Figure 3.2") + c(mk(1))),
    ("(d)", p("Describe two simple chemical tests to distinguish these compounds, stating the expected observations.") + FIG + c(mk(3))),
    ("(e)", p("Organic bromine compounds are used to prepare Grignard reagents, which act as a source of highly nucleophilic carbon.") +
            p("In the preparation of a Grignard reagent, magnesium is inserted into the C–Br bond of the organic bromine compound.") +
            ceqn("R–Br" + EM + "+" + EM + "Mg" + EM + arrow(4) + EM + under("R–Mg–Br", "Grignard reagent")) +
            p("(where R can be an alkyl, alkenyl or aryl group)") +
            p("When the Grignard reagent CH" + sub(3) + "CH" + sub(2) + "MgBr is reacted with propanone, product " + b("K") + " is obtained. The Grignard reagent "
              "provides a CH" + sub(3) + "CH" + sub(2) + sup(M) + " nucleophile to add to propanone.") + FIG),
    ("(e)(i)", p("Complete the boxes in Figure 3.3 by suggesting two compounds which can be reacted to form product " + b("M") + ". One of the two reactants "
                 "must be a Grignard reagent.") + FIG + cap("Figure 3.3") + c(mk(2))),
    ("(e)(ii)", p("Using the symbol [O] to represent the oxidising agent, write the balanced equation for the reaction between " + b("M") +
                  " and excess hot, acidified KMnO" + sub(4) + ". " + mk(1))),
    ("(e)(iii)", p("When the Grignard reagent CH" + sub(3) + "CH" + sub(2) + "MgBr was added to ethanoic acid, gas " + b("L") + " was formed instead of product " +
                   b("N") + ".") + FIG + p("State the identity of gas " + b("L") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=16, intro=[
    p("The H" + sub(2) + "CO" + sub(3) + "/HCO" + sub(3) + sup(M) + " buffer system and the HCO" + sub(3) + sup(M) + "/CO" + sub(3) + sup("2" + M) +
      " buffer system are important in maintaining pH in oceans."),
    p("The two buffer systems established involve reactions 4.1 and 4.2."),
    p("reaction 4.1" + EM + H2CO3 + "(aq) " + RARR + " " + HCO3 + "(aq) + " + HAQ + EM + PKA + sub(1) + " = 6.35"),
    p("reaction 4.2" + EM + HCO3 + "(aq) " + RARR + " " + CO3 + "(aq) + " + HAQ + EM + PKA + sub(2) + " = 10.3"),
], parts=[
    ("(a)", p("Explain what is meant by a " + i("buffer") + " solution. " + mk(1)),
     p("The Bjerrum plot relates the equilibrium composition of buffer solutions to the pH.") +
     p("Figure 4.1 shows the Bjerrum plot for 1 m" + sup(3) + " of seawater containing dissolved " + H2CO3 + ", " + HCO3 + " and " + CO3 + ".") +
     FIG + cap("Figure 4.1") +
     p("Two samples of seawater were prepared, sample " + b("I") + " and sample " + b("II") + ".") +
     p("sample " + b("I") + ": seawater at pH = 8.1") +
     p("sample " + b("II") + ": seawater at composition of point " + b("A"))),
    ("(b)(i)", p("Using the Bjerrum plot in Figure 4.1, state the value of the concentration of " + HCO3 + " in sample " + b("I") + " where pH = 8.1 in the "
                 "space given below.") +
               p("[" + HCO3 + "] = " + DOTS + " " + MDM + " " + mk(1)),
     p("To simulate the effects of ocean acidification, 0.05 mol of H" + sup("+") + " ions were added to 1 m" + sup(3) + " of sample " + b("I") + " at pH = 8.1.")),
    ("(b)(ii)", p("With reference to reaction 4.1, explain how the " + H2CO3 + "/" + HCO3 + " buffer system maintains pH when a small amount of H" + sup("+") +
                  " is added. " + mk(1))),
    ("(b)(iii)", p("With reference to your answer in " + b("(b)(ii)") + ", write the equation to show how the " + H2CO3 + "/" + HCO3 + " buffer reacted with H" + sup("+") + ".") +
                 p("Hence, calculate the change in concentration of " + HCO3 + " in 1 m" + sup(3) + " of sample " + b("I") + " when 0.05 mol of H" + sup("+") + " ions were added.") +
                 p("change in [" + HCO3 + "] = " + DOTS + " " + MDM + " " + mk(3))),
    ("(b)(iv)", p("Hence, using the Bjerrum plot in Figure 4.1 or otherwise, determine the change in pH of 1 m" + sup(3) + " of sample " + b("I") + " when 0.05 mol of H" + sup("+") +
                  " ions were added.") + p("change in pH = " + DOTS + " " + mk(1))),
    ("(c)(i)", p("By comparing the relative concentrations of " + H2CO3 + " and " + HCO3 + ", comment on the significance of point " + b("A") + " on Figure 4.1 and of its "
                 "pH value with respect to the " + H2CO3 + "/" + HCO3 + " buffer system. " + mk(2))),
    ("(c)(ii)", p("0.05 mol of H" + sup("+") + " ions were added to 1 m" + sup(3) + " of sample " + b("II") + " with a composition which is that of point " + b("A") + ".") +
                p("The resultant pH change was " + M + "0.1.") +
                p("With reference to your answer in part " + b("(b)(iv)") + ", compare and comment on the effectiveness of the " + H2CO3 + "/" + HCO3 +
                  " buffer system in seawater samples " + b("I") + " and " + b("II") + " in terms of resistance to pH change. " + mk(2))),
    ("(d)", p("Ocean Alkalinity Enhancement (OAE) treatment of seawater makes use of compounds such as MgO, which can be added to seawater to increase "
              "buffering capacity against ocean acidification due to higher atmospheric CO" + sub(2) + ".")),
    ("(d)(i)", p("Write equation(s) to show the acid-base property of MgO in its reaction with CO" + sub(2) + ". " + mk(1)),
     p("However, a drawback of OAE treatment is that over-enhancement of alkalinity will cause precipitation of " + CO3 + " as MCO" + sub(3) +
       " where M" + sup("2+") + " is a metal cation.")),
    ("(d)(ii)", p("Suggest one reason to explain how the precipitation of " + CO3 + " is undesirable for marine organisms with shells. " + mk(1))),
    ("(e)", p("Other than atmospheric CO" + sub(2) + ", some aqueous metal ions also cause increased acidity. With the aid of a relevant equation, explain why "
              "aqueous Fe" + sup("3+") + " causes an increase in acidity. " + mk(3))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=15, intro=[
    p("The 2026 Singapore Motor Show showcased state-of-the-art advancements for electric vehicles (EV), such as the shift from traditional lithium-ion "
      "(NMC) batteries to newer lithium iron phosphate (LFP) battery technology."),
], parts=[
    ("(a)", p("Figure 5.1 shows the discharging process when a LFP battery is connected to an electric motor of an EV.") + FIG + cap("Figure 5.1") +
            p("The electrolyte used is lithium hexafluorophosphate (LiPF" + sub(6) + "), dissolved in an organic solvent mixture.") +
            p("When the LFP battery is charged, electrode " + b("A") + " consists of Li atoms coordinated to carbon on a graphite electrode, LiC" + sub(6) + ". "
              "During discharge, LiC" + sub(6) + " on electrode " + b("A") + " is oxidised to " + LI + " ions.") +
            p("The " + LI + " ions migrate through the electrolyte to electrode " + b("B") + ", forming LiFePO" + sub(4) + " from FePO" + sub(4) + ".") +
            p("The released electrons from electrode " + b("A") + " flow through the external circuit to the EV’s motor, which powers the vehicle before "
              "returning to electrode " + b("B") + " to complete the circuit.")),
    ("(a)(i)", p("LiPF" + sub(6) + " consists of a " + LI + " ion and one anion.") + p("Draw the ‘dot-and-cross’ diagram for LiPF" + sub(6) + ". " + mk(1))),
    ("(a)(ii)", p("Complete the half-equations for the discharge process of the LFP battery at both electrodes.") +
                p("anode" + EM + EM + "LiC" + sub(6) + " " + arrow(3) + " " + DOTS) +
                p("cathode" + EM + EM + DOTS + " " + arrow(3) + " LiFePO" + sub(4) + " " + mk(2))),
    ("(a)(iii)", p("Identify the element that is reduced during discharge and state the change in its oxidation state.") +
                 p("element: ............") + p("oxidation state changes from ……… to ……… " + mk(2))),
    ("(a)(iv)", p("Calculate the " + ECELL + " for the LFP battery, given the following data.") +
                p(i("E") + STD + "(electrode " + b("A") + ") = " + M + "3.00 V") +
                p(i("E") + STD + "(electrode " + b("B") + ") = +0.45 V " + mk(1))),
    ("(a)(v)", p("A 400 V battery pack is required to power an EV. LFP cells are connected in series and grouped into modules of 24 cells. These modules "
                 "are then connected in series to form the complete battery pack.") +
               p("Use your answer to " + b("(a)(iv)") + " to calculate the minimum number of modules required for each battery pack. " + mk(1))),
    ("(b)", p("Some considerations in the design of EV batteries are shown in Table 5.1.") + cap("Table 5.1") +
            table(tr(th(""), th("LFP battery"), th("NMC battery")),
                  tr(td("raw materials used"), td("iron, lithium, phosphate"), td("cobalt, lithium, manganese, nickel")),
                  tr(td("maximum number of charging cycles"), td("~7000"), td("~2000")),
                  tr(td("cost (per km)"), td("lower"), td("higher")),
                  tr(td("energy density" + "^"), td("lower"), td("higher")),
                  tr(td("safety concerns (thermal runaway" + sup("#") + ")"), td("low risk"), td("higher risk"))) +
            p("^Energy density is the quantity of electrical energy a battery can store per unit mass or volume.") +
            p(sup("#") + "Thermal runaway is an uncontrollable chain reaction in batteries where heat builds up causing rapid temperature rise, fire, or explosion.")),
    ("(b)(i)", p("Suggest " + b("two") + " reasons why LFP batteries are more sustainable than NMC batteries. Explain your answer in terms of cost and "
                 "environmental issues. You should make reference to the properties listed in Table 5.1. " + mk(2))),
    ("(b)(ii)", p(i("Use of Data Booklet is relevant for this question.")) +
                p("In the LFP battery shown in Figure 5.1, parts of the copper connector may be oxidised to Cu" + sup("2+") + " with misuse.") +
                p("During the recharging of LFP battery, both " + LI + " and Cu" + sup("2+") + " are present at electrode " + b("A") + ".") +
                p("Determine which ion is preferentially reduced at electrode " + b("A") + " and hence explain why there is a loss of capacity in the LFP "
                  "battery after recharging. " + mk(2))),
    ("(c)", p("A new EV brand, " + i("DF Box") + ", uses an advanced LFP battery, with quicker charging time and longer driving distance.") +
            p("Table 5.2 shows some technical specifications of the " + i("DF Box") + ".") + cap("Table 5.2") +
            table(tr(td("battery type"), td("LFP")),
                  tr(td("battery capacity"), td("42.5 kWh (1.53 × 10" + sup("5") + " kJ)")),
                  tr(td("battery voltage"), td("400 V (400 J C" + sup(M + "1") + ")")),
                  tr(td("estimated driving distance"), td("430 km")),
                  tr(td("discharge power"), td("70 kW (70 kJ s" + sup(M + "1") + ")")),
                  tr(td("recharge power"), td("70 kW (70 kJ s" + sup(M + "1") + ")"))) +
            p("Battery capacity is measured in kWh, with a higher kWh rating generally translating to longer driving distance for EVs.")),
    ("(c)(i)", p("With reference to Table 5.2, calculate the theoretical time, in minutes, required to recharge the LFP battery from 30% to 80%. " + mk(1))),
    ("(c)(ii)", p("The time taken to recharge the battery from 30% to 80% was stated by the manufacturer to be 30 minutes.") +
                p("Account for any discrepancy between your answer in " + b("(c)(i)") + " and the manufacturer’s stated charge time. " + mk(1))),
    ("(c)(iii)", p("Battery capacity is the total electrical energy the battery can store and release.") +
                 p("The electrical energy of the battery is given by the equation below.") + ceqn("electrical energy = charge × voltage") +
                 p("Using data from Table 5.2, calculate the total charge stored in the LFP battery. " + mk(1))),
    ("(c)(iv)", p("Calculate the maximum amount of electrons transferred when the LFP battery is fully discharged. " + mk(1))),
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
EXTRA_TEXT = {(2, "(c)(iv)"): "forward rate time t0 t1 t2",
              (3, "(c)"): "ethyl ethanoate hydroxide step 1 step 2 step 3",
              (3, "(c)(ii)"): "step 2 ethoxide methide",
              (3, "(d)"): "bromoethane bromoethene bromobenzene",
              (3, "(e)"): "propanone CH3CH2MgBr product K",
              (3, "(e)(i)"): "Grignard reagent product M",
              (3, "(e)(iii)"): "ethanoic acid CH3CH2MgBr product N gas L",
              (4, "(a)"): "Bjerrum plot H2CO3 HCO3 CO3 concentration pH point A",
              (5, "(a)"): "Electrode A Li+ LiC6 Electrode B FePO4 LiFePO4 electrolyte Cu connector Al connector electric motor"}

slot_for = lambda label, k: ("intro" if not label else label.replace("(", "").replace(")", "")) + ("" if k == 0 else str(k + 1))
rows, plan = [], []
for n in sorted(Q):
    d = Q[n]
    parts = [(x + ("",))[:3] for x in d["parts"]]
    html_blocks = list(d["intro"])
    text_bits = [strip(" ".join(d["intro"])), EXTRA_TEXT.get((n, None), "")]
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

