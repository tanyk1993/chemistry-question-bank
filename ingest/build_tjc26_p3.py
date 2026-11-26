"""Hand transcription of TJC 2026 H2 Prelim Paper 3 (9476/03, 15 Sept 2026; Section A Q1-Q4 = 55 marks, Section B answer ONE of
Q5/Q6 = 20 marks, 75 as sat; 95 as ingested because both Section B questions are loaded) -> questions.json + asset_plan.json.
Typed from the school's Word file ("QP and Ans": question paper with the mark scheme painted in blue/red) and its Word-exported
PDF. Same output contract as build_tjc26_p2.py, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_tjc26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school TJC --year 2026 --paper 3 --level H2 --skip-assets=false

Conventions as build_tjc26_p2.py / build_sajc26_p3.py (claude/style-guide.md): stem = intro blocks, then one div.qpart per part that
has text of its own; [n] a span.mk where the paper prints it; every figure a block <div class="fig"> placeholder with the caption
typed as a centred bold p.c; answer lines and empty answer boxes NOT reproduced; tables typed. Asset slot = part label without
brackets; text and a figure the school prints BETWEEN two sub-parts is a tail after the part before it and its figure takes that
part's slot (Q1 Fig 1.2 -> 'ci'; Q4 Fig 4.2 -> 'bi', Fig 4.3 -> 'cii', Fig 4.5 -> 'eii'; Q4(c) text after (iv) and Q6(d) are in-part).
Part marks are all printed in the question (summed per question and asserted against the printed [Total]: 10/10/14/21/20/20).
Fig 2.1 (Q2(c)) is plain text steps, typed; the empty box for step 3 is a dotted line.
Figure choices: Q4 Fig 4.2 is printed twice in the school's file; the second copy ("epoxide") is used.
School slips corrected (veto-able; listed in the chat note):
  Q1(b) "bond lengths ... is shown" -> "are shown"; "Fig 1.1" -> "Fig. 1.1"; Q1(c) "behavior" -> "behaviour", "Fig. 1.2. shows" -> "Fig. 1.2 shows";
  Q3(b)(ii) "effervesces" -> "effervesce"; Q3(c) "Triiodide are" -> "Triiodides are", "2e" -> "2e-";
  Q4(a) "towards electrophile" -> "electrophiles"; Q4(e) "long polymer chain" -> "chains"; Q5(b)(ii) "value of for" -> "value for";
  Q5(b)(iii) "has a pH 6.90" -> "has a pH of 6.90"; Q5(d) double space "M  and N" closed.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "TJC", "H2", "P3", 2026
FIG = '<div class="fig">figure</div>'
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
def ceqn(s): return '<p class="c eqn">%s</p>' % s
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)

L = '<i class="el">l</i>'
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
STD = sup('<span class="pl-sym">⦵</span>')
EM = "&emsp;"
ARR = "→"
EQ = "⇌"
DBK = i("Data Booklet")
EA = i("E") + STD
CL = "C" + L
HCL = "H" + CL
H2PO4 = "H" + sub(2) + "PO" + sub(4) + sup(M)
HPO4 = "HPO" + sub(4) + sup("2" + M)
KA = K + sub("a")
KP = K + sub("p")
KSP = K + sub("sp")
ALI3 = "A" + L + "I" + sub(3)
AL2I6 = "A" + L + sub(2) + "I" + sub(6)
PCL5 = "PC" + L + sub(5)
I3 = "I" + sub(3) + sup(M)
def eion(s): return s + "e" + sup(M)
RAD = "•"

Q = {}

# ---------------------------------------------------------------- Q1  (10)
Q[1] = dict(marks=10, intro=[], parts=[
    ("(a)", p("Sodium nitrate is frequently used in various real-world applications such as fertilisers, water treatment and food preservation due to its high solubility in water.") +
            p("Explain why sodium nitrate is highly soluble in water. " + mk(2))),
    ("(b)", p("Some information about the nitrate ion is provided in Table 1.1.") +
            cap("Table 1.1") +
            table(tr(td("Shape of nitrate ion"), td("Trigonal planar")),
                  tr(td("Bond length of nitrogen-oxygen bond"), td("0.124 nm"))) +
            p("The bond lengths between nitrogen and oxygen atoms in different molecules are shown in Table 1.2.") +
            cap("Table 1.2") +
            table(tr(th("Type of nitrogen-oxygen bond"), th("bond length/nm")),
                  tr(td("N-O in NH" + sub(2) + "OH"), td("0.145")),
                  tr(td("N=O in NO"), td("0.115"))) +
            p("Fig. 1.1 shows one possible arrangement of valence electrons and bonds in the nitrate ion, NO" + sub(3) + sup(M) + ".") +
            FIG + cap("Fig. 1.1")),
    ("(b)(i)", p("Use the information in both Table 1.1 and 1.2 to explain why Fig. 1.1 does " + b("not") + " represent an accurate model for the bonding in the nitrate ion. " + mk(1))),
    ("(b)(ii)", p("Nitrogen and oxygen atoms undergo the same type of hybridisation as carbon atoms.") +
                p("Suggest the mixing and overlap of atomic orbitals which account for the N-O bond length in the nitrate ion. " + mk(2))),
    ("(c)", p("The behaviour of real gas, CO" + sub(2) + "(g), can be compared to the behaviour of an ideal gas.")),
    ("(c)(i)", p("It is assumed that there are no intermolecular forces of attraction between gas particles in an ideal gas.") +
               p("State two other basic assumptions of kinetic theory as applied to an ideal gas. " + mk(2)),
     p("Fig. 1.2 shows a plot of " + i("pV") + "/" + i("RT") + " against " + i("p") + " for one mole of an ideal gas and one mole of carbon dioxide, where " +
       i("p") + " is the pressure and " + i("V") + " is the volume of the gas.") + FIG + cap("Fig. 1.2")),
    ("(c)(ii)", p("Explain the shape of the graph for carbon dioxide. " + mk(2))),
    ("(c)(iii)", p("On Fig. 1.2, sketch the variation of " + i("pV") + "/" + i("RT") + " against " + i("p") + " for one mole of SO" + sub(2) + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q2  (10)
Q[2] = dict(marks=10, intro=[], parts=[
    ("(a)", p("Propanone reacts with methanol under acidic conditions to form compound " + b("A") + ".") + FIG +
            p("Table 2.1 shows how the initial rate of reaction changes as [CH" + sub(3) + "OH] and [H" + sup("+") + "] are varied. In each experiment, a large excess of propanone is used.") +
            cap("Table 2.1") +
            table(tr(th("Experiment"), th("[CH" + sub(3) + "OH] / " + MDM), th("[H" + sup("+") + "] / " + MDM), th("Relative initial rate of reaction")),
                  tr(td("1"), td("0.020"), td("0.020"), td("1.00")),
                  tr(td("2"), td("0.030"), td("0.030"), td("2.25")),
                  tr(td("3"), td("0.030"), td("0.040"), td("3.00")))),
    ("(a)(i)", p("Explain why a large excess of propanone is used in each experiment. " + mk(1))),
    ("(a)(ii)", p("Use the data in Table 2.1 to determine the order with respect to [CH" + sub(3) + "OH] and [H" + sup("+") + "]. Explain your answer. " + mk(2))),
    ("(b)", p("In a separate experiment, a large excess of methanol and H" + sup("+") + " ions are added to a solution containing a known concentration of propanone. "
              "The rate equation can be expressed as") +
            ceqn("rate = " + i("k") + "′[CH" + sub(3) + "COCH" + sub(3) + "]") +
            p("The half-life of the reaction is 165 s.")),
    ("(b)(i)", p("Determine the time taken for the concentration of propanone to decrease to 12.5% of its initial concentration. " + mk(1))),
    ("(b)(ii)", p("The experiment in " + b("(b)") + " was repeated using twice the concentration of propanone under the same conditions.") +
                p("Suggest how it would affect your answer in " + b("(b)(i)") + ". " + mk(1))),
    ("(c)", p("Another experiment was carried out with propanone and iodine in the presence of an acid catalyst.") +
            ceqn("CH" + sub(3) + "COCH" + sub(3) + " + I" + sub(2) + " " + ARR + " CH" + sub(3) + "COCH" + sub(2) + "I + H" + sup("+") + " + I" + sup(M)) +
            p("The rate equation is rate = " + i("k") + "[CH" + sub(3) + "COCH" + sub(3) + "][H" + sup("+") + "] and the partial mechanism is as shown in Fig. 2.1.") +
            p("Step 1: CH" + sub(3) + "COCH" + sub(3) + " + H" + sup("+") + " " + ARR + " CH" + sub(3) + "C" + sup("+") + "(OH)CH" + sub(3)) +
            p("Step 2: CH" + sub(3) + "C" + sup("+") + "(OH)CH" + sub(3) + " " + ARR + " CH" + sub(3) + "C(OH)=CH" + sub(2) + " + H" + sup("+")) +
            p("Step 3: ………………………………………………………………") +
            p("Step 4: CH" + sub(3) + "C" + sup("+") + "(OH)CH" + sub(2) + "I " + ARR + " CH" + sub(3) + "COCH" + sub(2) + "I + H" + sup("+")) +
            cap("Fig. 2.1")),
    ("(c)(i)", p("Write an equation for step 3 in the box in Fig. 2.1. " + mk(1))),
    ("(c)(ii)", p("Suggest and explain which is the slowest step in the mechanism. " + mk(1))),
    ("(c)(iii)", p("With the aid of a labelled Boltzmann distribution diagram, explain the effect of the acid catalyst on the rate constant. " + mk(3))),
])

# ---------------------------------------------------------------- Q3  (14)
Q[3] = dict(marks=14, intro=[], parts=[
    ("(a)", p("State the trend in thermal stability of " + HCL + ", HBr and HI. Explain your answer with reference to bond energy and orbital overlap. " + mk(2))),
    ("(b)", p("Group 2 elements, also known as alkaline earth metals, react with water to form metal hydroxides and hydrogen gas.") +
            p("The table below shows the observation when various alkaline earth metals react with water.") +
            table(tr(th("alkaline earth metals"), th("observation with water")),
                  tr(td("beryllium"), td("no effervescence")),
                  tr(td("magnesium"), td("slow effervescence")),
                  tr(td("calcium"), td("steady effervescence")),
                  tr(td("strontium"), td("vigorous effervescence")))),
    ("(b)(i)", p("Using relevant " + EA + " values from the " + DBK + ", explain the observations.") +
               p("Your answer should relate to the reactivity of the alkaline earth metals. " + mk(2))),
    ("(b)(ii)", p("The standard electrode potential of Be" + sup("2+") + "/Be is " + M + "1.85 V.") +
                p("Show that beryllium should theoretically effervesce with water to produce hydrogen gas. " + mk(1))),
    ("(b)(iii)", p("Beryllium and aluminium share similar chemical reactions with each other.") +
                 p("Suggest an explanation why there is no reaction observed between beryllium and water. " + mk(1))),
    ("(c)", p("Triiodides are species with three iodine atoms in the molecular formula, such as triiodide anion, " + I3 + ", and aluminium triiodide, " + ALI3 + ".")),
    ("(c)(i)", p("In aqueous medium of iodine and iodide solution, triiodide anion, " + I3 + " is formed.") +
               p("The half-equation for the triiodide/iodide half-cell is:") +
               ceqn(I3 + "(aq) + 2" + eion("") + " " + EQ + " 3I" + sup(M) + "(aq)" + EM + EM + EA + " = +0.54 V") +
               p("Draw a fully labelled diagram of the experimental set-up used to measure the standard electrode potential of the " + I3 + "(aq)/I" + sup(M) + "(aq) half-cell. " + mk(3)),
     p(ALI3 + " has a simple molecular structure in the gaseous phase. It dimerises readily to form " + AL2I6 + ".") +
     p(AL2I6 + " is injected into an empty vessel to set up an equilibrium between " + AL2I6 + " and " + ALI3 + ", as shown in reaction 1.") +
     ceqn("reaction 1" + EM + EM + AL2I6 + "(g) " + EQ + " 2" + ALI3 + "(g)" + EM + EM + DEL + i("H") + " > 0") +
     p("The initial pressure of " + AL2I6 + " is 17 kPa.")),
    ("(c)(ii)", p("Write an expression for " + KP + " for reaction 1. State its units. " + mk(1))),
    ("(c)(iii)", p("The degree of dissociation of " + AL2I6 + " at 400 °C is 40%.") +
                 p("Calculate the value of " + KP + " for reaction 1 at 400 °C. State its units. " + mk(2))),
    ("(c)(iv)", p("State and explain the effect on the value of " + KP + " if the reaction was carried out at 500 °C. " + mk(2))),
])

# ---------------------------------------------------------------- Q4  (21)
Q[4] = dict(marks=21, intro=[
    p("Cyclohexene is a cyclic alkene that is industrially produced from benzene. It can then be converted into a range of useful products including polymers.")], parts=[
    ("(a)", p("Explain the difference between the reactivity of benzene and of cyclohexene towards electrophiles. " + mk(1))),
    ("(b)", p("Cyclohexene can be converted into an epoxide as shown in Fig. 4.1. The reaction involves the addition of oxygen across the C=C bond without breaking the sigma bond.") +
            FIG + cap("Fig. 4.1")),
    ("(b)(i)", p("Suggest and explain why the epoxide is expected to be highly reactive. " + mk(2)),
     p("The epoxide can undergo hydrolysis to form cyclohexane-1,2-diol as shown in Fig. 4.2.") + FIG + cap("Fig. 4.2")),
    ("(b)(ii)", p("The melting point of the epoxide is " + M + "40 °C and that of cyclohexane-1,2-diol is 103 °C.") +
                p("Using structure and bonding, explain the difference in the melting points of these two compounds. " + mk(2))),
    ("(c)", p("Cyclohexene can also be converted to hexanedioic acid, via the cleavage of the C=C bond.")),
    ("(c)(i)", p("Suggest the reagents and conditions for this conversion and include the expected observation. " + mk(2))),
    ("(c)(ii)", p("Write a balanced chemical equation for this conversion. " + mk(1)),
     p("Hexanedioic acid is a precursor for the manufacture of polymer " + b("O") + ". The pathway is as shown in Fig. 4.3.") + FIG + cap("Fig. 4.3")),
    ("(c)(iii)", p("Define the term " + i("polymer") + ". " + mk(1))),
    ("(c)(iv)", p("Suggest the structure of compound " + b("M") + ". " + mk(1)),
     p("Compounds " + b("M") + " and " + b("N") + " can react to form polymer " + b("O") + ". Hexanedioic acid can also be used to react with compound " + b("N") + " to form polymer " + b("O") + ".")),
    ("(c)(v)", p("Draw the structure of polymer " + b("O") + ". " + mk(1))),
    ("(c)(vi)", p("Suggest the disadvantage of using hexanedioic acid directly for the synthesis of polymer " + b("O") + " as compared to using compound " + b("M") + ". " + mk(1))),
    ("(c)(vii)", p("Explain why polymer " + b("O") + " is prone to degradation when exposed to acid rain for a prolonged period of time. " + mk(1))),
    ("(d)", p("Cyclohexene can be used to synthesise cyclohexanone oxime as shown in Fig. 4.4.") + FIG + cap("Fig. 4.4")),
    ("(d)(i)", p("Draw the structure of " + b("P") + " and state the reagent and conditions for step 1. " + mk(2))),
    ("(d)(ii)", p("Suggest the type of reaction for step 3. " + mk(1))),
    ("(e)", p("Alkoxy radicals, RO" + RAD + ", can be used as initiators in free radical addition polymerisation to react with alkene molecules to form long polymer chains.") +
            ul("The initiation step involves the formation of RO" + RAD + " radicals, from heating an organic peroxide, RO–OR.",
               "The first propagation step involves adding RO" + RAD + " to an alkene molecule to form a free radical intermediate.",
               "This free radical intermediate then reacts with another alkene molecule in the second propagation step to form a new free radical "
               "intermediate with a higher number of carbon atoms.")),
    ("(e)(i)", p("Write the equation for the formation of the free radicals from benzoyl peroxide when it is being heated. Include curly arrow notation for the equation. " + mk(1)) + FIG),
    ("(e)(ii)", p("Hence, write the equations for the first and second propagation steps for the reaction between benzoyl peroxide, (C" + sub(6) + "H" + sub(5) + "CO)" + sub(2) +
                  "O" + sub(2) + " and ethene. Include curly arrow notation for both equations. " + mk(2)),
     p("During this process, a phenomenon known as back-biting can occur in which the growing polymer chain can fold back on itself, resulting in the abstraction of "
       "a hydrogen atom from a carbon atom in the middle of the chain to form a new type of radical as shown in Fig. 4.5.") + FIG + cap("Fig. 4.5")),
    ("(e)(iii)", p("Suggest why there is a tendency for the abstraction of hydrogen atom to occur. " + mk(1))),
    ("(e)(iv)", p("By considering the branching of the various polymer chains formed, suggest why back-biting will form a polymer that has a lower density. " + mk(1))),
])

# ---------------------------------------------------------------- Q5  (20)  Section B
Q[5] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Sodium and phosphorus react with oxygen to form stable oxides in their highest oxidation states.")),
    ("(a)(i)", p("State the formula for these two oxides. " + mk(1))),
    ("(a)(ii)", p("Write balanced equations for the reaction of each oxide with water and state the expected pH of each resulting solution. " + mk(2))),
    ("(b)", p("The phosphate buffer system present in biological cells consists of " + H2PO4 + " and " + HPO4 + ".") +
            ceqn(H2PO4 + " + H" + sub(2) + "O " + EQ + " " + HPO4 + " + H" + sub(3) + "O" + sup("+") + EM + "⎯ " + KA) +
            p("A series of experiments were carried out using phosphate buffers. The pH values of different samples of phosphate buffer with varying ratios of [" + HPO4 +
              "] and [" + H2PO4 + "] were measured, as shown in Table 5.1.") +
            cap("Table 5.1") +
            table(tr(th("Sample"), th("Ratio of [" + HPO4 + "]/ [" + H2PO4 + "]"), th("Measured pH")),
                  tr(td("1"), td("0.25"), td("6.60")),
                  tr(td("2"), td("0.50"), td("6.90")),
                  tr(td("3"), td("1.00"), td("7.20")),
                  tr(td("4"), td("2.00"), td("7.50")))),
    ("(b)(i)", p("Explain what is meant by the term " + i("buffer solution") + ". " + mk(1))),
    ("(b)(ii)", p("With reference to Table 5.1, state the p" + KA + " value for " + H2PO4 + ". " + mk(1))),
    ("(b)(iii)", p("A 200 cm" + sup(3) + " buffer solution containing NaH" + sub(2) + "PO" + sub(4) + " and Na" + sub(2) + "HPO" + sub(4) + " has a pH of 6.90. The [" + H2PO4 +
                   "] was found to be 0.0600 " + MDM + ".") +
                 p("Using information from Table 5.1, calculate the pH of the buffer upon adding 0.002 mol of NaOH. " + mk(3))),
    ("(c)", p("Fumaric acid and maleic acid are cis-trans isomers with different physical properties.") + FIG),
    ("(c)(i)", p("Explain why the p" + KA + sub(2) + " of fumaric acid is higher than its p" + KA + sub(1) + ". " + mk(1))),
    ("(c)(ii)", p("With the aid of a clearly-labelled diagram, explain why p" + KA + sub(1) + " of maleic acid is lower than p" + KA + sub(1) + " of fumaric acid. " + mk(2))),
    ("(d)", p("Compound " + b("J") + ", C" + sub(11) + "H" + sub(12) + "O" + sub(2) + ", is a neutral, di-substituted benzene derivative.") +
            p("When heated with dilute " + HCL + ", " + b("J") + " gives ethanoic acid and " + b("K") + ", C" + sub(9) + "H" + sub(10) + "O.") +
            p(b("K") + " reacts with cold alkaline KMnO" + sub(4) + " to give " + b("L") + ", C" + sub(9) + "H" + sub(12) + "O" + sub(3) + ". When heated with acidified K" + sub(2) +
              "Cr" + sub(2) + "O" + sub(7) + ", " + b("L") + " forms " + b("M") + ", C" + sub(9) + "H" + sub(10) + "O" + sub(4) + ". " + b("M") +
              " does not react with 2,4-dinitrophenylhydrazine. " + b("M") + " reacts with " + PCL5 + " to give a sweet-smelling compound " + b("N") + ", C" + sub(9) + "H" + sub(7) +
              "O" + sub(2) + CL + ".") +
            p("One mole of " + b("K") + " reacts with 3 moles of aqueous bromine to give a white precipitate.") +
            p("Explain the reactions involved and deduce the structures of compounds " + b("J") + ", " + b("K") + ", " + b("L") + ", " + b("M") + " and " + b("N") + ". " + mk(9))),
])

# ---------------------------------------------------------------- Q6  (20)  Section B
Q[6] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Describe the reactions, if any, of NaC" + L + ", " + "A" + L + CL + sub(3) + " and SiC" + L + sub(4) + " with an excess of water. Write equations for any reactions "
              "that occur, and suggest the pH of the resulting mixtures. " + mk(3))),
    ("(b)", p("A mixture of two cations can be separated by selective precipitation.") +
            p("A solution contains 0.010 " + MDM + " of lead(II) nitrate and 0.020 " + MDM + " of silver nitrate. Solid sodium chromate, Na" + sub(2) + "CrO" + sub(4) +
              ", is added slowly to the solution until the precipitation of lead(II) chromate occurs. The addition of solid Na" + sub(2) + "CrO" + sub(4) +
              " to the solution is then continued until the precipitation of silver chromate occurs.")),
    ("(b)(i)", p("Write the " + KSP + " expression for the solubility product of silver chromate, Ag" + sub(2) + "CrO" + sub(4) + ", giving its units. " + mk(2))),
    ("(b)(ii)", p("Given that the numerical value for the " + KSP + " of silver chromate is 1.1 × 10" + sup(M + "12") + ", calculate the concentration of chromate ions when "
                  "the silver chromate precipitate first appeared. " + mk(1))),
    ("(b)(iii)", p("When the first trace of lead(II) chromate precipitate, PbCrO" + sub(4) + ", appeared, the concentration of chromate ions in the solution is 1.8 × 10" +
                   sup(M + "12") + " " + MDM + ".") +
                 p("Calculate the concentration of lead ions remaining in the solution when silver chromate precipitate first appears. " + mk(1))),
    ("(b)(iv)", p("The separation is considered effective if less than 1% of lead ions remain in the solution. Hence, deduce whether the separation is effective. "
                  "Show your working clearly. " + mk(1))),
    ("(c)", p("D-Threitol is primarily used as a chemical intermediate in organic synthesis. Emerging research also explores its potential in food science as a "
              "low-calorie sweetener. The total number of stereoisomers including D-Threitol is three. The three-dimensional structure of D-Threitol is shown.") + FIG),
    ("(c)(i)", p("Describe what is meant by stereoisomerism. " + mk(1))),
    ("(c)(ii)", p("Draw the three-dimensional structure of the enantiomer of D-Threitol. " + mk(1))),
    ("(c)(iii)", p("One of the stereoisomers has no effect on plane polarised light. Explain why. " + mk(1))),
    ("(d)", p(b("P") + " is a cyclic compound and has the molecular formula C" + sub(8) + "H" + sub(11) + "NO" + sub(2) + ".") +
            p("A series of tests are carried out. Table 6.1 shows some compounds formed in each test.") +
            cap("Table 6.1") +
            table(tr(th("test"), th("reaction"), th("compounds formed"), th("other information")),
                  tr(td("1"), td(b("P") + ", C" + sub(8) + "H" + sub(11) + "NO" + sub(2) + ", with cold dilute " + HCL), td("no reaction"), td("")),
                  tr(td("2"), td(b("P") + " with Fehling’s reagent, warm"), td("red-brown precipitate and other products"), td("")),
                  tr(td("3"), td(b("P") + " with an excess of hot, concentrated, acidified KMnO" + sub(4)),
                     td(b("Q") + " (C" + sub(6) + "H" + sub(8) + "O" + sub(5) + ")<br>and H" + sub(2) + "NCH" + sub(2) + "COOH"),
                     td(b("Q") + " effervesces with Na" + sub(2) + "CO" + sub(3) + "(aq).<br>" + b("Q") + " gives orange ppt with 2,4-DNPH.<br>" + b("Q") + " undergoes reduction to form " + b("R") + ".")),
                  tr(td("4"), td(b("P") + " with an excess of LiA" + L + "H" + sub(4)), td(b("S") + ", C" + sub(8) + "H" + sub(15) + "NO"), td("")),
                  tr(td("5"), td(b("S") + " with an excess of CH" + sub(3) + "I, heat"), td("salt " + b("T")), td(b("T") + " forms a yellow precipitate with AgNO" + sub(3) + "(aq)."))) +
            p("The structure of " + b("R") + " is shown.") + FIG +
            p("For each test, state the type of reaction described. For each compound, state what the information in Table 6.1 tells you about the functional groups it contains. "
              "Include your reasoning.") +
            p("Suggest possible structures for " + b("P") + ", " + b("Q") + ", " + b("S") + " and " + b("T") + ". You may find it useful to determine the structures of " +
              b("Q") + " and " + b("P") + " first. " + mk(9))),
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
    h = re.sub(r"</sup> (?=(?:K|s)<sup>)", "</sup>" + NB, h)          # mol-1 K-1, dm-3 s-1
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
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", h).strip()

# Names printed in a snipped figure that content_text should still carry (search only).
EXTRA_TEXT = {(1, "(b)"): "nitrate ion NO3- N O trigonal planar",
              (1, "(c)(i)"): "pV/RT pressure / atm ideal gas CO2 1.0",
              (2, "(a)"): "CH3COCH3 CH3OH A H3CO OCH3 H3C CH3 H2O propanone methanol",
              (4, "(b)"): "cyclohexene epoxide",
              (4, "(b)(i)"): "epoxide cyclohexane-1,2-diol OH",
              (4, "(c)(ii)"): "hexanedioic acid HOOC(CH2)4COOH PCl5 M N HOCH2(CH2)4CH2OH Polymer O",
              (4, "(d)"): "cyclohexene step 1 P step 2 cyclohexanone step 3 NH2OH cyclohexanone oxime",
              (4, "(e)(i)"): "benzoyl peroxide",
              (4, "(e)(ii)"): "back-biting radical CH CH2 CH3",
              (5, "(c)"): "fumaric acid pKa1 = 3.0 pKa2 = 4.4 maleic acid pKa1 = 1.9 pKa2 = 6.1 OH O HO",
              (6, "(c)"): "D-Threitol HO OH H",
              (6, "(d)"): "R HO OH"}

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
assert sum(r["marks"] for r in rows) == 95
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))
