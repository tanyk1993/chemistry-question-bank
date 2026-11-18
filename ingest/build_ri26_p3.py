"""Hand transcription of RI 2026 H2 Prelim Paper 3 (9476/03, 5 structured Q, 95 marks as ingested, 75 as sat:
Section A Q1-Q3, Section B answer ONE of Q4/Q5) -> questions.json + asset_plan.json. Typed from the school's Word
file and the Word-exported PDF (the two agree). Same output contract as extract_parts / build_ri26_p2.py, i.e. what
gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_ri26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school RI --year 2026 --paper 3 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_ri26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('aii'), 'd2' for a second figure in the same part; a figure the
    paper prints AFTER a part's mark (a tail) takes that part's slot.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "RI", "H2", "P3", 2026
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
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)

L = '<i class="el">l</i>'                  # element l
K = i("K")
kk = i("k")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
EM = "&emsp;"
RARR = "⇌"
STD = sup('<span class="pl-sym">⦵</span>')   # standard-state sign: ALWAYS this form (NJC 2026 P3 lesson)
def stkr(bottom):
    """a standard-state sign stacked over a subscript (dG_r), as build_ri26_p2 / NJC 2026 P3"""
    return '<span class="stk post"><span><span class="pl-sym">⦵</span></span><span>%s</span></span>' % bottom
DG_R = DEL + i("G") + stkr("r")
DH_STD = DEL + i("H") + STD
E_STD = i("E") + STD
KSP = K + sub("sp")
KB = K + sub("b")
PKA = "p" + K + sub("a")

# ---- layout helpers (copied from build_ri26_p2.py) --------------------------------------------
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
def arrow(w=3.5): return over("&nbsp;", long_arrow(w))
def under(sym, label):
    """a species with its label printed directly underneath ('pink' / 'blue')"""
    return ('<span style="display:inline-block;text-align:center;vertical-align:top;line-height:1.25">%s'
            '<span style="display:block;font-size:.95em">%s</span></span>' % (sym, label))

# ---- chemistry shorthands ----------------------------------------------------------------------
CL = "C" + L
HCL = "HC" + L
AGCL = "AgC" + L
CLM = CL + sup(M)
LI = "Li" + sup("+")
BZ = "C" + sub(6) + "H" + sub(5) + "COO"            # benzoate stem
BZM = BZ + sup(M)
ETHER = "CH" + sub(3) + "OCH" + sub(2) + "CH" + sub(2) + "OCH" + sub(3)
NH3 = "NH" + sub(3)
TMA_O = "(CH" + sub(3) + ")" + sub(3) + "NO"          # (CH3)3NO
TMA = "(CH" + sub(3) + ")" + sub(3) + "N"
DMA = "(CH" + sub(3) + ")" + sub(2) + "NH"
S8 = "S" + sub(8)
S82 = "S" + sub(8) + sup("2" + M)
S42 = "S" + sub(4) + sup("2" + M)
def orb(x): return "d" + sub(x)
DX2Y2 = "d" + sub("x" + sup("2") + M + "y" + sup("2"))
DZ2 = "d" + sub("z" + sup("2"))

# Parts are (label, html) or (label, html, tail). `tail` is text/figure the paper prints AFTER the part's
# mark and BEFORE the next label (it introduces the next sub-part); it is emitted as bare blocks between
# the qpart divs.
Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (19)
CO_EQ = ("[Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + "(aq) + 4" + CLM + "(aq) " + RARR + " [CoC" + L + sub(4) + "]" + sup("2" + M) + "(aq) + 6H" + sub(2) + "O(l)")
CO_EQ_LBL = (under("[Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + "(aq)", "pink").replace("vertical-align:top", "vertical-align:top") +
             " + 4" + CLM + "(aq) " + RARR + " " + under("[CoC" + L + sub(4) + "]" + sup("2" + M) + "(aq)", "blue") + " + 6H" + sub(2) + "O(l)")
Q[1] = dict(marks=19, intro=[], parts=[
    ("(a)", p("Explain what is meant by the term " + i("transition element") + ". " + mk(1))),
    ("(b)(i)", p("State the full electronic configuration of Fe" + sup("2+") + ". " + mk(1))),
    ("(b)(ii)", p("Suggest why the atomic radii of iron atoms and copper atoms are similar. " + mk(2))),
    ("(b)(iii)", p("Iron is commonly used as a heterogenous catalyst in the Haber process.") +
                 p("Describe the role of iron in the Haber process. " + mk(3))),
    ("(c)", p("An equilibrium involving some cobalt complexes is shown below.") + ceqn(CO_EQ_LBL)),
    ("(c)(i)", p("State the oxidation number of Co in [CoC" + L + sub(4) + "]" + sup("2" + M) + ". " + mk(1))),
    ("(c)(ii)", p("Explain why [Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + " is coloured. " + mk(3))),
    ("(c)(iii)", p("Suggest a reason why [Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + " and [CoC" + L + sub(4) + "]" + sup("2" + M) + " have different colours. " + mk(1))),
    ("(c)(iv)", p("Humidity indicator cards used in enclosed containers rely on cobalt(II) chloride systems.") +
                p("With reference to the equilibrium shown above, explain how these cards indicate that the containers are humid. " + mk(2))),
    ("(d)", p("Copper is a transition metal that forms complexes with different shapes.") +
            p("Figure 1.1 shows the 3-dimensional structure of [Cu(NH" + sub(3) + ")" + sub(4) + "]" + sup("2+") + " with a square planar geometry.") +
            FIG + cap("Figure 1.1")),
    ("(d)(i)", p("On Figure 1.1, draw the " + DX2Y2 + " orbital. " + mk(1)),
     p("Figure 1.2 shows the relative energy levels of d" + M + "orbitals in a square planar complex.") + FIG + cap("Figure 1.2")),
    ("(d)(ii)", p("By considering the shape and orientation of the d" + M + "orbitals of the metal ion in a square planar complex, explain why the " +
                  orb("xy") + " orbital has a higher energy level than the " + orb("yz") + " and " + orb("xz") + " orbitals, as shown in Figure 1.2. " + mk(2))),
    ("(e)", p("When concentrated " + HCL + " is added to a solution containing [Cu(NH" + sub(3) + ")" + sub(4) + "]" + sup("2+") +
              ", a pale blue precipitate, " + b("X") + ", is first formed. " + b("X") + " dissolves in excess concentrated " + HCL +
              " to form a yellow-green solution, " + b("Y") + ".") +
            p("Identify " + b("X") + " and " + b("Y") + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q2  (16)
Q[2] = dict(marks=16, intro=[p("Lithium and sulfur are abundant elements used in energy storage systems such as lithium−sulfur batteries.")], parts=[
    ("(a)(i)", p("Define the " + i("lattice energy") + " of lithium sulfide, Li" + sub(2) + "S. " + mk(1))),
    ("(a)(ii)", p("By using suitable data from the " + i("Data Booklet") + " and those in Table 2.1, construct a fully labelled energy cycle to determine the lattice energy of Li" + sub(2) + "S.") +
                cap("Table 2.1") +
                table(tr(td("standard enthalpy change of formation of lithium sulfide / kJ mol" + sup(M + "1")), td(M + "447")),
                      tr(td("standard enthalpy change of atomisation of lithium / kJ mol" + sup(M + "1")), td("+159")),
                      tr(td("standard enthalpy change of atomisation of sulfur / kJ mol" + sup(M + "1")), td("+279")),
                      tr(td("sum of first and second electron affinity of sulfur / kJ mol" + sup(M + "1")), td("+400"))) +
                c(mk(3))),
    ("(a)(iii)", p("Li" + sub(2) + "S" + sub(2) + " contains an S−S bond.") +
                 p("Predict whether the magnitude of lattice energy of Li" + sub(2) + "S" + sub(2) + " is higher or lower than that of Li" + sub(2) + "S. Explain your answer. " + mk(2))),
    ("(b)", p("In a lithium−sulfur battery, the anode contains lithium metal while the cathode contains sulfur, " + S8 + ". A common electrolyte used is " + ETHER + ".")),
    ("(b)(i)", p("Write an equation to show why water should not be present in the electrolyte. " + mk(1))),
    ("(b)(ii)", p("One " + LI + " forms an octahedral complex ion with three " + ETHER + " molecules.") +
                p("Draw the structure of the complex ion.") +
                p("You may represent " + ETHER + " as") + FIG + c(mk(1))),
    ("(b)(iii)", p("The sulfur cathode must be mixed with graphite for the battery to work. Explain why this is necessary. " + mk(1))),
    ("(c)", p("During discharge, some " + S8 + " molecules on the surface of the graphite cathode leave and solid Li" + sub(2) + "S gradually accumulates within the vacant sites previously occupied by " + S8 +
              ". After several rounds of charging and discharging, there are cracks in the structure of the cathode.") +
            p("Suggest how this process results in these cracks. " + mk(1))),
    ("(d)", p("The overall reaction for a lithium–sulfur battery during discharge is shown below.") +
            ceqn(S8 + " + 16Li " + arrow(3.5) + " 8Li" + sub(2) + "S")),
    ("(d)(i)", p("Write an equation for the reaction that occurs at the cathode. " + mk(1))),
    ("(d)(ii)", p("A lithium–sulfur battery is required to provide constant current of 0.500 A for 10 h. Calculate the amount of charge that is produced. " + mk(1))),
    ("(e)", p("The electrode potential values of the reduction processes involving some sulfur containing species are shown in Figure 2.1.") + FIG + cap("Figure 2.1")),
    ("(e)(i)", p("Use information from Figure 2.1 to explain whether the disproportionation of " + S82 + " into " + S8 + " and " + S42 + " is spontaneous. Show your working. " + mk(2))),
    ("(e)(ii)", p("The " + DG_R + " values of reactions 1 to 3 are shown in the table below.") +
                table(tr(th("reaction"), th("equation"), th(DG_R + " / kJ mol" + sup(M + "1"))),
                      tr(td("1"), td(S8 + " + 2e" + sup(M) + " ⟶ " + S82), td("–459")),
                      tr(td("2"), td(S82 + " + 2e" + sup(M) + " ⟶ 2" + S42), td("–415")),
                      tr(td("3"), td(S8 + " + 4e" + sup(M) + " ⟶ 2" + S42), td(i("x")))) +
                p("Determine the value of " + i("x") + " and hence, the electrode potential value of reaction 3. " +
                  DG_R + " can be used in the same manner as " + DH_STD + " in a Hess’ law cycle but " + E_STD + " cannot. " + mk(2))),
])

# ---------------------------------------------------------------- Q3  (20)
CCl4 = "CC" + L + sub(4)
def cpd(x): return "compound " + b(x)
Q[3] = dict(marks=20, intro=[], parts=[
    ("(a)(i)", p("Explain the relative basicities of ethanamide, CH" + sub(3) + "CONH" + sub(2) + ", ethylamine, CH" + sub(3) + "CH" + sub(2) + "NH" + sub(2) +
                 " and phenylamine, C" + sub(6) + "H" + sub(5) + "NH" + sub(2) + ", in aqueous medium. " + mk(3))),
    ("(a)(ii)", p("The structures of two bases, TMPD and DMAN, are shown below.") + FIG +
                p("While TMPD is a di-acidic base, DMAN functions as a mono-acidic base.") +
                p("Draw the displayed formula for DMAN–H" + sup("+") + ", the conjugate acid of DMAN, and use it to explain why DMAN functions as a mono-acidic base.") +
                p("On your structure, draw and label relevant interactions to support your explanation. " + mk(3))),
    ("(b)", p("Table 3.1 shows some properties of two polymers.") + cap("Table 3.1") + FIG +
            p("Tensile strength is the maximum force that is applied to a material before it breaks.")),
    ("(b)(i)", p("Polymer " + b("W") + " is chemically inert which makes it more difficult to biodegrade.") +
               p("Suggest a reason why polymer " + b("W") + " is chemically inert. " + mk(1))),
    ("(b)(ii)", p("Draw the structure of the monomer used to produce polymer " + b("X") + ". " + mk(1))),
    ("(b)(iii)", p("By considering the intermolecular forces of attraction between polymer chains, explain the relative tensile strengths of polymers " + b("W") + " and " + b("X") + ". " + mk(1))),
    ("(c)", p("To determine its structure, compound " + b("A") + " was subjected to a series of reactions as shown in Figure 3.1.") + FIG + cap("Figure 3.1") +
            p("Compounds " + b("A") + " and " + b("B") + " each contains two hydroxy groups. Compound " + b("D") + " contains a linear 8-carbon chain where carbon-4 and carbon-5 are each connected to 2 hydrogen atoms.") +
            p("A series of tests are carried out. Table 3.2 shows some information in each test.") + cap("Table 3.2") +
            table(tr(th("test"), th("I"), th("II"), th("III")),
                  tr(td("reagents &amp; conditions"), td("K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ", H" + sub(2) + "SO" + sub(4) + ", heat"), td("Br" + sub(2) + " in " + CCl4), td("I" + sub(2) + ", NaOH, heat")),
                  tr(td(cpd("A")), td("NR"), td("1 mol of " + b("A") + " reacted with 1 mol of Br" + sub(2)), td("NR")),
                  tr(td(cpd("B")), td("NR"), td("NR"), td("1 mol of " + b("B") + " gave 2 mol of yellow precipitate, " + b("F") + ".")),
                  tr(td(cpd("C")), td("NR"), td("1 mol of " + b("C") + " reacted with 2 mol of Br" + sub(2)), td("1 mol of " + b("C") + " gave 2 mol of yellow precipitate, " + b("F") + ".")),
                  tr(td(cpd("D")), td("NR"), td("NR"), td("1 mol of " + b("D") + " gave 2 mol of yellow precipitate, " + b("F") + ".")),
                  tr(td(cpd("E")), td("NR"), td("NR"), td("1 mol of " + b("E") + " gave 1 mol of yellow precipitate, " + b("F") + "."))) +
            p("(NR = no reaction)")),
    ("(c)(i)", p("Compounds " + b("A") + " and " + b("B") + " each contains two hydroxy groups but do not react with acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) +
                 ". State the type of hydroxy group present in " + b("A") + " and " + b("B") + ". " + mk(1))),
    ("(c)(ii)", p("State the identity of yellow precipitate, " + b("F") + ". " + mk(1))),
    ("(c)(iii)", p("With reference to test " + b("III") + ", state the type of reaction and structural feature present when " + b("F") + " is formed. " + mk(2))),
    ("(c)(iv)", p("For each compound, state what the information from reactions 2 and 3 and tests " + b("II") + "–" + b("III") +
                  " tells you about the functional groups it contains. You should state the types of reaction which occurred and include your reasoning.") +
                p("Suggest possible structures for " + b("D") + " and " + b("E") + ".") +
                p("Use these structures to deduce possible structures for " + b("A") + ", " + b("B") + " and " + b("C") + ". " + mk(7))),
])

# ---------------------------------------------------------------- Q4  (20)  Section B
Q[4] = dict(marks=20, intro=[], parts=[
    ("(a)(i)", p("Describe and explain the trend in the thermal stability of the carbonates of Group 2 elements. " + mk(3))),
    ("(a)(ii)", p("Using data from the " + i("Data Booklet") + ", predict if FeCO" + sub(3) + " will decompose at a higher or lower temperature than MgCO" + sub(3) + ". " + mk(2)),
     p("Wastewater from a chemical processing plant contains chloride ions, " + CLM + ", benzoate ions, " + BZM + ", and trace amounts of dissolved organic compounds.")),
    ("(b)", p("One method to treat wastewater is precipitation. In an experiment, a wastewater sample containing 1.00 × 10" + sup(M + "2") + " " + MDM + " of " + CLM +
              " and 8.00 × 10" + sup(M + "3") + " " + MDM + " of " + BZM + " is analysed.") +
            p("To separate the two ions, solid AgNO" + sub(3) + " was added to precipitate the maximum amount of " + BZ + "Ag from the mixture, without precipitating " + AGCL + ".") +
            p("Numerical values of two solubility products are given in the table below.") +
            table(tr(th("compound"), th("numerical values of " + KSP)),
                  tr(td(AGCL), td("1.77 × 10" + sup(M + "10"))),
                  tr(td(BZ + "Ag"), td("2.50 × 10" + sup(M + "13"))))),
    ("(b)(i)", p("Write an expression for the solubility product, " + KSP + ", for " + AGCL + ". " + mk(1))),
    ("(b)(ii)", p("Calculate the concentration of Ag" + sup("+") + " in the solution at the end of the separation. " + mk(1))),
    ("(b)(iii)", p("Calculate the percentage of " + BZM + " remaining in the solution. " + mk(2))),
    ("(b)(iv)", p("In some countries, the maximum concentration of " + BZM + " allowed in treated wastewater is 1.50 ppm.") +
                p("Comment on the effectiveness of the method used in " + b("(b)") + " in wastewater treatment.") +
                p("(1 ppm of " + BZM + " ions = 1 mg of " + BZM + " ions in 1000 cm" + sup("3") + " of solvent.) " + mk(2))),
    ("(c)", p("A mixture of " + AGCL + " and " + BZ + "Ag can be separated by adding aqueous ammonia. This allows " + AGCL + " to dissolve and separation can be achieved by filtration.")),
    ("(c)(i)", p("Write an equation for the reaction between aqueous ammonia and silver ion. " + mk(1))),
    ("(c)(ii)", p("Suggest why " + AGCL + " dissolves while " + BZ + "Ag does not. " + mk(2))),
    ("(d)", p("The following scheme shows the conversion of benzene into an epoxide, which contains the functional group shown below.") + FIG + FIG + cap("Figure 4.1")),
    ("(d)(i)", p("Suggest the reagent and condition for step 1. " + mk(1))),
    ("(d)(ii)", p("Benzene does not undergo a one-step electrophilic substitution to form phenylethene.") + FIG +
                p("Suggest why. " + mk(2))),
    ("(d)(iii)", p("Suggest the reagent and condition for step 4. " + mk(1))),
    ("(d)(iv)", p("State the " + i("type of reaction") + " that occurs in step 5. " + mk(1))),
    ("(d)(v)", p("Complete the mechanism for step 5 on Figure 4.1 by adding a lone pair, curly arrows and a dipole. " + mk(1))),
])

# ---------------------------------------------------------------- Q5  (20)  Section B
Q[5] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Describe and explain the trend in the thermal stability of the hydrogen halides " + HCL + ", HBr and HI. Include an equation for the thermal decomposition reaction in your answer. " + mk(3))),
    ("(b)(i)", p("Write a balanced equation for the equilibrium between " + NH3 + " and water. " + mk(1))),
    ("(b)(ii)", p("A solution containing 0.0100 mol of " + NH3 + " was dissolved in a total volume of 250 cm" + sup("3") + " of water.") +
               p("Calculate the pH of this solution.") +
               p("For " + NH3 + ", " + KB + " = 1.80 × 10" + sup(M + "5") + " " + MDM + " at 25 °C. " + mk(3))),
    ("(c)", p("Figure 5.1 shows the change in pH when 25.0 cm" + sup("3") + " of 0.100 " + MDM + " of aqueous ammonia, " + NH3 + "(aq), is titrated with 0.100 " + MDM + " of " + HCL + "(aq).") +
            FIG + cap("Figure 5.1")),
    ("(c)(i)", p("Write an equation to explain why the pH at the equivalence point is less than 7. " + mk(1))),
    ("(c)(ii)", p("State the volume of " + HCL + " required for pH = " + PKA + " of NH" + sub(4) + sup("+") + ". " + mk(1))),
    ("(d)", p("Eicosapentaenoic acid (EPA) is found in fish fats.") + p("The structure of EPA is shown below.") + FIG),
    ("(d)(i)", p("State the type of stereoisomerism EPA exhibits. Explain your answer. " + mk(2)),
     p("EPA can undergo auto-oxidation via a free radical mechanism.") +
     p("The initiation step involves the homolytic cleavage of a C–H bond to form a radical intermediate " + b("Q") + ".") +
     p("Two different radicals, " + b("Q1") + " and " + b("Q2") + ", can be formed as shown in Figure 5.2.") + FIG +
     p("R = side chain") + cap("Figure 5.2")),
    ("(d)(ii)", p("Suggest whether " + b("Q1") + " or " + b("Q2") + " would be the major species formed during the initiation step. Explain your answer. " + mk(2)),
     p("The first propagation step involving radical intermediate Q• is shown.") +
     p("step 1:" + EM + "Q•" + EM + "+" + EM + "O=O" + EM + arrow(3.5) + EM + "Q−O−O•")),
    ("(d)(iii)", p("Draw curly arrows for step 1 to show the mechanism of the reaction. " + mk(1))),
    ("(e)", p(TMA_O + " is present in fish muscle. It can be broken down simultaneously via two competing pathways.") +
            p("pathway 1: " + TMA_O + " " + over(kk + sub(1), long_arrow(3.5)) + " " + TMA + " + by-products") +
            p("pathway 2: " + TMA_O + " " + over(kk + sub(2), long_arrow(3.5)) + " " + DMA + " + HCHO") +
            p("For the above reactions, " + kk + sub(1) + " and " + kk + sub(2) + " are rate constants.") +
            p("In both pathways, the reaction is first order with respect to " + TMA_O + ".")),
    ("(e)(i)", p("Write the rate equations for pathway 1 and pathway 2. " + mk(1))),
    ("(e)(ii)", p("Using your answer in " + b("(e)(i)") + ", write the overall rate equation for the decomposition of " + TMA_O + ". " + mk(1)),
     p("At a given temperature, the half-life for the overall decomposition of " + TMA_O + " is 20 hours.")),
    ("(e)(iii)", p("Sketch the graph of [" + TMA_O + "] against time. Label two half-lives in your graph.") + FIG + c(mk(1))),
    ("(e)(iv)", p("Given that " + kk + sub(1) + " is 0.030 h" + sup(M + "1") + ", calculate the value of " + kk + sub(2) + ".") +
                p("Hence comment on the relative amount of " + TMA + " and " + DMA + " formed. " + mk(2))),
    ("(e)(v)", p("By considering the rate of production of the products, show that the ratio " + frac("[" + TMA + "]", "[" + DMA + "]") +
                 " is a constant at the same temperature for the same amount of time. " + mk(1))),
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
EXTRA_TEXT = {(1, "(d)"): "Figure 1.1 [Cu(NH3)4]2+ H3N NH3 Cu z x y axes square planar",
              (1, "(d)(i)"): "Figure 1.2 energy dx2-y2 dz2 dxy dyz dxz d-orbitals of metal ion in square planar complex",
              (2, "(b)(ii)"): "CH3OCH2CH2OCH3 O O",
              (2, "(e)"): "Figure 2.1 S8 S82- S42- reaction 1 reaction 2 reaction 3 +2.38 V +2.15 V",
              (3, "(a)(ii)"): "TMPD DMAN N CH3 CH3 benzene naphthalene",
              (3, "(b)"): "polymer W repeat unit CH2CH2 polymer X NH(CH2)5CO tensile strength 15 65 MPa",
              (3, "(c)"): "Figure 3.1 A C11H18O2 B C11H18O4 C C11H14O2 D C8H10O4 E C3H4O3 KMnO4 H2SO4 heat conc. H3PO4 reaction 1 reaction 2 reaction 3",
              (4, "(d)"): "epoxide Figure 4.1 benzene step 1 step 2 step 3 step 4 step 5 OH Br Na+ O-",
              (4, "(d)(ii)"): "benzene phenylethene",
              (5, "(c)"): "Figure 5.1 pH 14 7 25.0 Vol of HCl added cm3 titration curve",
              (5, "(d)"): "EPA structure HO O",
              (5, "(d)(i)"): "Figure 5.2 free radical Q1 free radical Q2 R HO O",
              (5, "(e)(iii)"): "[(CH3)3NO] / mol dm-3 time / hour axes"}

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

