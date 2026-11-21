"""Hand transcription of RVHS 2026 H2 Prelim Paper 3 (9476/03, 5 structured Q, 95 marks as ingested, 75 as sat:
Section A Q1-Q3, Section B answer ONE of Q4/Q5) -> questions.json + asset_plan.json. Typed from the school's .doc
(converted with LibreOffice) and the Word-exported PDF (the two agree). Same output contract as build_ri26_p3.py, i.e.
what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_rvhs26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school RVHS --year 2026 --paper 3 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_rvhs26_p2.py / build_ri26_p3.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('diii'); a figure the paper prints AFTER a part's mark (a tail)
    takes that part's slot (2(a) Fig. 2.1 -> 'a'; 5(d) Table 5.1 -> 'd').
School typos corrected on user ruling (2026-11-21): Nafion, polytetrafluoroethylene, "forms halides", "repeat units",
"the more stable form", two stray commas in 2(c)(iv)/2(c).
Source glyph notes: the school's 'Chemical' font f023 = single bond, f024 = double bond, f02e = radical dot;
the stray dash before 'R group' (2(d)(iii)) is dropped, as the stray dash before OCH3 was on RVHS P2.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "RVHS", "H2", "P3", 2026
FIG = '<div class="fig">figure</div>'
M = "−"                              # minus sign U+2212
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
def ceqn(s): return '<p class="c eqn">%s</p>' % s
def ol(*items): return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def nuc(a, z, sym): return '<span class="stk"><span>%s</span><span>%s</span></span>%s' % (a, z, sym)

L = '<i class="el">l</i>'                  # element l
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
STD = sup('<span class="pl-sym">⦵</span>')
DH_STD = DEL + i("H") + STD
EM = "&emsp;"
BOND = "–"                            # single bond dash as printed (R-O-O-R)
DOT = "•"                             # radical dot
DB = "="
DBK = i("Data Booklet")

CL = "C" + L
HCL = "HC" + L
NCL3 = "NC" + L + sub(3)
ALCL3 = "A" + L + "C" + L + sub(3)
PCL5 = "PC" + L + sub(5)
NACL = "NaC" + L
AL = "A" + L
ALOH3 = AL + "(OH)" + sub(3)
AL2O3 = AL + sub(2) + "O" + sub(3)
CF2 = "CF" + sub(2)
ROOR = "R" + BOND + "O" + BOND + "O" + BOND + "R"
RO_RAD = "R" + BOND + "O" + DOT
TFE = CF2 + DB + CF2
CO2 = "CO" + sub(2)
N2O = "N" + sub(2) + "O"
O3 = "O" + sub(3)
NO2 = "NO" + sub(2)
CA3PO42 = "Ca" + sub(3) + "(PO" + sub(4) + ")" + sub(2)
PO4 = "PO" + sub(4) + sup("3" + M)
def cmp_(x): return b(x)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (16)
Q[1] = dict(marks=16, intro=[], parts=[
    ("(a)", p("The nitrates, carbonates and hydroxides of Group 2 elements can undergo thermal decomposition.")),
    ("(a)(i)", p("During the thermal decomposition of Group 2 nitrates, a metal oxide, oxygen and a brown gas are produced.") +
               p("Write a balanced equation, with state symbols, for the decomposition of calcium nitrate. " + mk(1))),
    ("(a)(ii)", p("The nitrates of lead and zinc can undergo thermal decomposition similar to calcium nitrate. The decomposition temperatures of the three nitrates are given in Table 1.1.") +
                cap("Table 1.1") +
                table(tr(th("compound"), th("decomposition temperature / °C")),
                      tr(td("lead(II) nitrate, Pb(NO" + sub(3) + ")" + sub(2)), td("290")),
                      tr(td("calcium nitrate, Ca(NO" + sub(3) + ")" + sub(2)), td("132")),
                      tr(td("zinc nitrate, Zn(NO" + sub(3) + ")" + sub(2)), td("105"))) +
                p("Explain, with reference to the " + DBK + ", the trend in the decomposition temperatures of the metal nitrates in Table 1.1. " + mk(3))),
    ("(b)", p("Calcium phosphate, " + CA3PO42 + ", is a mineral found in our bones.") +
            p("Table 1.2 gives data relevant to the question.") +
            cap("Table 1.2") +
            table(tr(th(""), th("value / kJ mol" + sup(M + "1"))),
                  tr(td("standard enthalpy change of atomisation of Ca(s)"), td("+178")),
                  tr(td("standard enthalpy change of formation of " + CA3PO42 + "(s)"), td(M + "4175")),
                  tr(td("lattice energy of " + CA3PO42 + "(s)"), td(M + "10520")),
                  tr(td("standard enthalpy change of hydration of Ca" + sup("2+") + "(g)"), td(M + "1562")),
                  tr(td("standard enthalpy change of hydration of " + PO4 + "(g)"), td(M + "2876")))),
    ("(b)(i)", p("Use the data from Table 1.2 and the " + DBK + " to calculate the standard enthalpy change of formation of " + PO4 + "(g). " + mk(2))),
    ("(b)(ii)", p("Define the term " + i("standard enthalpy change of solution") + ". " + mk(1))),
    ("(b)(iii)", p("The standard enthalpy change of solution of " + CA3PO42 + " can also be calculated using the data in Table 1.2. Calculate the standard enthalpy change of solution of " + CA3PO42 + ". " + mk(1))),
    ("(b)(iv)", p("Deduce the order of lattice energy, in decreasing magnitude, of " + CA3PO42 + ", Ca" + sub(3) + "N" + sub(2) + " and CaSO" + sub(4) + ". Explain your answer. " + mk(2))),
    ("(c)", p("The distinctive smell of swimming pool water is attributed to various types of chloramines, such as NH" + sub(2) + CL + ", NH" + CL + sub(2) + " and " + NCL3 + ".") +
            p("These chloramines are formed from the reaction between ammonia and hypochlorous acid, H" + CL + "O.")),
    ("(c)(i)", p("At a temperature of 70.0 °C and a pressure of 1.20 atm, 0.400 g of a gaseous mixture containing NH" + sub(2) + CL + ", NH" + CL + sub(2) + " and " + NCL3 +
                 " takes up a volume of 150 cm" + sup("3") + ". Calculate the average molar mass of the sample. " + mk(2))),
    ("(c)(ii)", p("Explain why " + NCL3 + " gas behaves less ideally than NH" + sub(3) + " gas. " + mk(1))),
    ("(c)(iii)", p(NCL3 + " can be removed by channelling swimming pool water through an ultraviolet (UV) disinfection system, producing chlorine gas as shown by the equation below.") +
                 ceqn("2" + NCL3 + "(l) → N" + sub(2) + "(g) + 3" + CL + sub(2) + "(g)" + EM + EM + DH_STD + " = +184 kJ mol" + sup(M + "1")) +
                 p("Explain why the standard entropy change of this reaction is positive. " + mk(1))),
    ("(c)(iv)", p("Using the information in " + b("(c)(iii)") + ", explain whether a lower or higher temperature will favour the removal of " + NCL3 + " in swimming pool. " + mk(2))),
])

# ---------------------------------------------------------------- Q2  (24)
Q[2] = dict(marks=24, intro=[
    p("Use of the " + DBK + " is relevant to this question."),
    p("The hydrogen fuel cell presents a solution to generate clean and sustainable energy for static based application. It also boasts a very high energy efficiency, where up to 75% of energy used could be put to useful work."),
    p("Storage and transport of hydrogen gas, however, is challenging, and it presents a significant barrier in the development and adoption of hydrogen fuel cell for practical applications.")], parts=[
    ("(a)", p("Suggest why hydrogen gas is challenging to store and transport. " + mk(1)),
     p("The Direct Methanol Fuel Cell (DMFC) addresses the hydrogen fuel portability issue by feeding liquid methanol directly into an acidic proton-exchange membrane cell.") + FIG + cap("Fig. 2.1")),
    ("(b)(i)", p("State the direction of electron flow in the external circuit. " + mk(1))),
    ("(b)(ii)", p("Construct the balanced half-equation at electrode " + b("X") + " and deduce the overall balanced cell equation for the DMFC. " + mk(2))),
    ("(b)(iii)", p("Given that the standard cell potential for this cell is +1.21 V, calculate the standard electrode potential for the half-cell containing methanol. " + mk(1))),
    ("(b)(iv)", p("A DMFC produced an average of 4.34 A of current during its operation.") +
                p("Calculate the volume of " + CO2 + "(g) produced in one hour at room temperature and pressure. " + mk(2))),
    ("(b)(v)", p("Predict and explain the effect on the electromotive force generated if pure oxygen is used at electrode " + b("Y") + ". " + mk(2))),
    ("(c)", p("The overall reaction taking place inside the fuel cell is similar to the complete combustion of liquid methanol.") +
            p("The standard enthalpy change of combustion of liquid methanol is " + M + "726 kJ mol" + sup(M + "1") + ".")),
    ("(c)(i)", p("Define the term " + i("standard enthalpy change of combustion") + ". " + mk(1))),
    ("(c)(ii)", p("Using the " + DBK + ", calculate a value for the enthalpy change of combustion for methanol. " + mk(2))),
    ("(c)(iii)", p("Some bond energies in the " + DBK + " are average values. Using them in calculations can result in discrepancies when compared to actual enthalpy change values.") +
                 p("Suggest another reason why the value calculated in " + b("(c)(ii)") + " is different from the actual value of " + M + "726 kJ mol" + sup(M + "1") + ". " + mk(1))),
    ("(c)(iv)", p("Calculate the standard Gibbs free energy change for the oxidation of " + b("one mole") + " of liquid methanol in the fuel cell at standard conditions. " + mk(1))),
    ("(c)(v)", p("Hence, determine the standard entropy change for the combustion of methanol. " + mk(1))),
    ("(d)", p("The membrane of the fuel cell is made up of Nafion polymer. The manufacture of Nafion involves the initial production of a polytetrafluoroethylene (PTFE) polymer, which is shown in the figure below.") +
            FIG + cap("Fig. 2.2") +
            p("The production of PTFE involves the reaction of tetrafluoroethene, " + TFE + ", with a small amount of a peroxide initiator, " + ROOR + ".") +
            p("The mechanism is known to take place in the following steps:") +
            ol("The initiator molecule undergoes homolytic fission of the O" + BOND + "O bond at elevated temperature, forming reactive " + RO_RAD + " species.",
               RO_RAD + " then reacts with " + TFE + " to form a free radical.",
               "The free radical formed in step 2 then reacts with " + TFE + " to produce a longer free radical chain.",
               "Step 3 repeats itself multiple times, eventually producing a linear chain.",
               "Over time, two separate radical chains come together in a termination reaction to produce a long-chain PTFE polymer.")),
    ("(d)(i)", p("State the type of polymerisation that occurs. " + mk(1))),
    ("(d)(ii)", p("Describe the mechanism for the first three steps in the reaction between " + TFE + " and " + ROOR + ". Use curly arrows to indicate the movement of electrons. " + mk(3))),
    ("(d)(iii)", p("A sample polymer strand has a relative molecular mass of about 13426.") +
                 p("Deduce the number of repeat units of this polymer strand, given that the R group has the following structure:") + FIG + cap("Fig. 2.3") + c(mk(2))),
    ("(d)(iv)", p("Explain why the PTFE produced has a range of " + i("M") + sub("r") + " value. " + mk(1))),
    ("(d)(v)", p("Suggest how the average " + i("M") + sub("r") + " of PTFE can be increased. " + mk(1))),
    ("(d)(vi)", p("Suggest why PTFE is chemically inert. " + mk(1))),
])

# ---------------------------------------------------------------- Q3  (15)
Q[3] = dict(marks=15, intro=[], parts=[
    ("(a)(i)", p("The ozone molecule, " + O3 + ", contains a dative covalent bond.") +
               p("Draw a ‘dot-and-cross’ diagram to show the bonding in a molecule of " + O3 + ". " + mk(1))),
    ("(a)(ii)", p("Hence, suggest a value for the bond angle in " + O3 + ". " + mk(1))),
    ("(b)", p("In terms of structure and bonding, explain the difference in boiling points of hex-1-ene and 3,3-dimethylbut-1-ene.") +
            table(tr(th("substance"), th("boiling point / °C")),
                  tr(td("hex-1-ene"), td("63")),
                  tr(td("3,3-dimethylbut-1-ene"), td("41"))) +
            c(mk(2))),
    ("(c)", p("Ozonolysis is a reaction where ozone is used to cleave a C" + DB + "C bond into two C" + DB + "O bonds. Under suitable reaction conditions, ketones and carboxylic acids can be formed, as shown in Fig. 3.1. However, benzene rings remain unreactive to ozone.") +
            FIG + cap("Fig. 3.1") +
            p("Compound " + b("J") + ", C" + sub(12) + "H" + sub(16) + "O, is a di-substituted benzene. It reacts with an excess of ozone under similar conditions to form two organic compounds, " +
              b("K") + ", C" + sub(3) + "H" + sub(6) + "O" + sub(3) + ", and " + b("L") + ", C" + sub(9) + "H" + sub(10) + "O.") +
            p("A series of tests are carried out, and the results are recorded in Table 3.1.") +
            cap("Table 3.1") +
            table(tr(th("test"), th("reagents and conditions"), th("observations / results")),
                  tr(td("1"), td("alkaline aqueous iodine"), td(b("J") + ", " + b("K") + " and " + b("L") + " form a yellow precipitate.")),
                  tr(td("2"), td("2,4-DNPH"), td("Only " + b("L") + " forms an orange precipitate.")),
                  tr(td("3"), td("concentrated nitric acid and concentrated sulfuric acid catalyst"), td(b("L") + " forms " + b("M") + ", C" + sub(9) + "H" + sub(9) + "NO" + sub(3) + ", as the major product.")),
                  tr(td("4"), td("aqueous sodium carbonate"), td(b("K") + " effervesces.<br>" + b("K") + " has a chiral centre.")),
                  tr(td("5"), td("concentrated sulfuric acid catalyst, warm"), td(b("K") + " forms " + b("P") + ", C" + sub(6) + "H" + sub(8) + "O" + sub(4) + "."))) +
            p("For each test, state the type of reaction occurring. For each compound, state what the information tells you about the functional groups it contains. Include your reasoning.") +
            p("Suggest possible structures of " + b("J") + ", " + b("K") + ", " + b("L") + ", " + b("M") + " and " + b("P") + ". " + mk(9))),
    ("(d)", p("Compounds " + b("U") + " and " + b("V") + " are possible products of ozonolysis.") +
            p("Suggest a simple chemical test to distinguish between these two compounds.") + FIG + c(mk(2))),
])

# ---------------------------------------------------------------- Q4  (20)  Section B
ION_O = nuc(16, 8, "O") + sup("2" + M)
ION_N = nuc(14, 7, "N") + sup("2+")
ION_MG = nuc(24, 12, "Mg") + sup("2+")
Q[4] = dict(marks=20, intro=[p("This question is about the element nitrogen and its compounds.")], parts=[
    ("(a)", p("Nitrogen is a main building block for DNA and RNA, and amino acids, which make up proteins.")),
    ("(a)(i)", p("Define, by means of an equation, what is meant by the second ionisation energy of nitrogen. " + mk(1))),
    ("(a)(ii)", p("Explain why the second ionisation energy of carbon is lower than that of nitrogen. " + mk(2))),
    ("(a)(iii)", p("A gaseous mixture containing the ions, " + ION_O + ", " + ION_N + " and " + ION_MG + " was passed between two plates carrying an electric charge.") +
                 p("Given that " + ION_MG + " is deflected towards the negatively-charged plate at an angle of " + M + "5.00°, calculate the angle of deflection for the other two ions. " + mk(2))),
    ("(b)", p("Nitrous oxide, " + N2O + ", is a colourless air pollutant with a sweet scent.")),
    ("(b)(i)", p(N2O + " can be represented by two resonance structures.") + FIG +
               p("Given that nitrogen atoms undergo the same type of hybridisation as carbon atoms, describe how the σ and π bonds are formed between nitrogen atoms in structure II using orbital overlap and hybridisation of atoms. " + mk(2))),
    ("(b)(ii)", p("Suggest why " + N2O + " exists predominantly as structure II. " + mk(1))),
    ("(c)", p("Like " + N2O + ", an air pollutant, chlorofluorocarbons (CFCs) deplete the ozone layer via a 3-step mechanism. A description of the process is shown below using CF" + CL + sub(3) + ".") +
            table(tr(td("Step 1"), td("CF" + CL + sub(3) + " releases a chlorine radical in the presence of UV light.")),
                  tr(td("Step 2"), td("The chlorine radical collides with an ozone molecule, " + O3 + ", to form chlorine monoxide radical and oxygen gas.")),
                  tr(td("Step 3"), td("Chlorine monoxide collides with another ozone molecule to produce chlorine radical and oxygen gas.")))),
    ("(c)(i)", p("Write balanced equations for steps 2 and 3 of the mechanism. " + mk(1))),
    ("(c)(ii)", p("Explain why one chlorine radical, once formed, is said to destroy tens of thousands of ozone molecules. " + mk(1))),
    ("(d)", p("Describe and explain the relative basicities of ammonia, ethylamine and phenylamine. " + mk(3))),
    ("(e)", p("Azo compounds are a class of synthetic organic compounds featuring the characteristic diazenyl functional group (R" + BOND + "N" + DB + "N" + BOND + "R').") +
            p("Azobenzene is a light-sensitive compound with the chemical formula of (C" + sub(6) + "H" + sub(5) + "N)" + sub(2) + ".") +
            p("Using specific wavelengths of light, azobenzene can be switched back and forth between two forms: " + i("cis") + " form and " + i("trans") + " form.")),
    ("(e)(i)", p("Explain why azobenzene exhibits " + i("cis-trans") + " isomerism. " + mk(2))),
    ("(e)(ii)", p("Draw the structure of the more stable form and explain your answer. " + mk(2))),
    ("(f)", p("Noradrenaline and adrenaline are hormones that are produced by the body during times of stress.") + FIG +
            p("Adrenaline is formed by a reaction between the amine group of noradrenaline and a suitable halogen derivative molecule, with the following rate equation:") +
            ceqn("rate = " + i("k") + " [noradrenaline] [halogen derivative]") +
            p("Draw a mechanism for this reaction between noradrenaline and a suitable halogen derivative molecule to produce adrenaline. Show relevant lone pairs and dipoles, and use curly arrows to indicate the movement of electron pairs.") +
            p("You can represent noradrenaline using R" + BOND + "NH" + sub(2) + ". " + mk(3))),
])

# ---------------------------------------------------------------- Q5  (20)  Section B
Q[5] = dict(marks=20, intro=[
    p("Aluminium and its adjacent Period 3 elements are widely utilised in aerospace and automotive engineering due to their structural properties. "
      "However, their production, surface treatment, and operational emissions present key chemical and environmental challenges.")], parts=[
    ("(a)", p("Aluminium forms halides and oxides that behave differently from those of Period 3 elements when exposed to air and water.")),
    ("(a)(i)", p("Describe the reactions, if any, of the chlorides, " + NACL + ", " + ALCL3 + " and " + PCL5 + " with excess water.") +
               p("Write equations for all reactions that occur and suggest the pH of the resulting solutions. " + mk(4))),
    ("(a)(ii)", p("Describe simple chemical tests to distinguish " + AL2O3 + " from MgO and P" + sub(4) + "O" + sub(10) + ". Explain the observations. " + mk(2))),
    ("(b)", p("Although aluminium is a reactive metal, structural aircraft components made from aluminium alloys resist atmospheric corrosion. "
              "To enhance durability and dye absorption, an electrolytic process called anodising is used to treat the surface of the aluminium alloys.")),
    ("(b)(i)", p("Draw a labelled diagram of the electrolytic cell used to anodise the structural aircraft components made of aluminium alloys.") +
               p("Include details of the cathode, anode and electrolyte. " + mk(1))),
    ("(b)(ii)", p("With the aid of chemical equations, explain how anodising enhances the durability of the aircraft components. " + mk(2))),
    ("(c)", p("The treatment of anodising waste involves neutralising acids and precipitating dissolved aluminium ions as aluminium hydroxide.") +
            p("The solubility product of aluminium hydroxide is 3.00 × 10" + sup(M + "34") + " mol" + sup("4") + " dm" + sup(M + "12") + " at 298 K.")),
    ("(c)(i)", p("Calculate the solubility of " + ALOH3 + " in pure water at 298 K. " + mk(1))),
    ("(c)(ii)", p("When 52.0 cm" + sup("3") + " of NaOH solution was added to 20.0 cm" + sup("3") + " of wastewater, a white precipitate started to appear. At this point, the resultant wastewater was found to have a pH of 6.0.") +
                p("Given that the white precipitate is " + ALOH3 + ", calculate the concentration of " + AL + sup("3+") + " in the wastewater. " + mk(2))),
    ("(d)", p("Combustion at high temperature in aircraft jet engines causes atmospheric nitrogen and oxygen to react, producing oxides of nitrogen.") +
            p("With the aid of suitable equations, explain how " + NO2 + " acts as a catalyst in the oxidation of atmospheric sulfur dioxide. " + mk(2)),
     p("Organic chemists often employ named reactions to selectively modify molecular structures during the synthesis of pharmaceuticals and fine chemicals. Two such reactions are shown in Table 5.1.") +
     cap("Table 5.1") + FIG +
     p("Both Hofmann elimination and the Hofmann rearrangement are highly pH-dependent processes that proceed exclusively under strongly basic conditions.")),
    ("(e)(i)", p("Name the compound " + b("A") + " used in Hofmann elimination. " + mk(1))),
    ("(e)(ii)", p("Compound " + b("B") + ", C" + sub(6) + "H" + sub(10) + "O" + sub(2) + ", can be produced from a cyclic amide in a three-step synthesis as shown below.") + FIG +
                p("Suggest the reagents and conditions required for Step 1 and Step 3, and the structures of intermediate 1 and compound " + b("B") + ". " + mk(4)) +
                p("Step 1:") + p("Step 3:") +
                table(tr(td("<br><br><br><br><br><br>"), td("")), tr(th("intermediate 1"), th("compound " + b("B"))))),
    ("(e)(iii)", p("After carrying out both Hofmann reactions, compound " + b("C") + ", C" + sub(7) + "H" + sub(16) + "N" + sub(2) + "O, was converted into the following diene.") + FIG +
                 p("Suggest the structure of compound " + b("C") + ". " + mk(1))),
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
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b|nm\b|ppm\b|mg\b|V\b|A\b|h\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol)\b)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

# ---------------------------------------------------------------- assemble
def strip(h):
    h = h.replace(FIG, " ").replace("<br>", " ")
    h = re.sub(r"</(p|li|tr|div)>", " ", h)
    h = re.sub(r"</(td|th)>", " | ", h)
    h = re.sub(r"<span[^>]*>\s*</span>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", h).strip()

# Names printed in a snipped figure that content_text should still carry (search only).
EXTRA_TEXT = {(2, "(a)"): "Fig. 2.1 Electrode X Electrode Y CO2 H2O Methanol Air Membrane",
              (2, "(d)"): "Fig. 2.2 CF2 CF2 n",
              (2, "(d)(iii)"): "Fig. 2.3 S OH O O",
              (3, "(c)"): "Fig. 3.1 R1 R2 R3 O3 H HO",
              (3, "(d)"): "U V HCOOH HO OH O",
              (4, "(b)(i)"): "structure I structure II N N O",
              (4, "(f)"): "noradrenaline adrenaline HO OH NH2 N H CH3",
              (5, "(d)"): "Table 5.1 Hofmann rearrangement NaOH Br2 H2O NH2 CO2 In this reaction, there is a loss of one molecule of CO2 as a primary amide is converted into a primary amine. "
                          "Hofmann elimination excess compound A N(CH3)3I Ag2O H2O heat Hofmann elimination involves two reactions. It converts a primary amine to alkene(s), with the major product being a less substituted alkene.",
              (5, "(e)(ii)"): "Step 1 intermediate 1 Step 2 one of the Hofmann reactions intermediate 2 Step 3 C6H10O2 Compound B NH O",
              (5, "(e)(iii)"): "diene"}

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
