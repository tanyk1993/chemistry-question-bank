"""Hand transcription of A Level (SEAB) 9729/03 Oct/Nov 2024 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as build_alevel_p2.py, i.e. what
gen_parts_migration.py reads).
Run from the repo root:  python3 ingest/build_alevel_p3.py <outdir>

Paper: 5 structured questions. Section A = Q1-Q3 (answer all), Section B = Q4-Q5 (answer one).
Totals printed on the paper: Q1 21, Q2 20, Q3 19, Q4 20, Q5 20 (100 marks in the bank, 80 as sat).

Conventions (see claude/style-guide.md and build_alevel_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder; a "Fig. n.n" / "Table n.n" caption is typed as a
    centred bold p.c; a label that is part of the drawing itself (a compound name, "product", "most basic")
    is baked into the snip, not typed;
  * answer lines and empty answer boxes are NOT reproduced;
  * asset slot = part label without brackets ('d'), 'f2'/'f3' for a second/third figure in the same part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SEAB", "H2", "P3", 2024
FIG = '<div class="fig">figure</div>'
M = "−"                                   # minus sign U+2212
NB = "&nbsp;"
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

def chem(s):
    """Compact formula notation -> house markup.
    ^...^ = superscript (a '-' inside becomes U+2212); a digit right after a letter, ')' or ']' = subscript;
    'Cl' / 'Al' get the upright-serif element l. A leading coefficient (2NH3) stays full size."""
    parts = re.split(r"(\^[^^]*\^)", s)
    out = []
    for seg in parts:
        if seg.startswith("^") and seg.endswith("^") and len(seg) >= 2:
            out.append(sup(seg[1:-1].replace("-", M)))
        else:
            seg = re.sub(r"(?<=[A-Za-z\)\]])(\d+)", lambda m: sub(m.group(1)), seg)
            seg = re.sub(r"(?<=[AC])l(?![a-z])", L, seg)
            out.append(seg)
    return "".join(out)

K = i("K")
def kk(x): return i("k") + sub(x)         # rate constant k_x
MDM = "mol dm" + sup(M + "3")
DH = "Δ" + i("H") + sup("⦵")
DS = "Δ" + i("S") + sup("⦵")
DG = "Δ" + i("G") + sup("⦵")
E0 = i("E") + sup("⦵")
TIMES = "×"
DB = i("Data Booklet")
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html)])

# ---------------------------------------------------------------- Q1
t11 = table(tr(th("experiment"), th("halide ion"), th("halogen")),
            tr(td("1"), td(chem("Br^-^(aq)")), td(chem("Cl2(aq)"))),
            tr(td("2"), td(chem("I^-^(aq)")), td(chem("Cl2(aq)"))),
            tr(td("3"), td(chem("Br^-^(aq)")), td(chem("I2(aq)"))))
Q[1] = dict(marks=21, intro=[], parts=[
    ("(a)", p("Describe the trend in volatility of the Group 17 elements from chlorine to iodine.") +
            p("Explain your answer. " + mk(2))),
    ("(b)", p("The relative reactivity of the Group 17 elements chlorine to iodine is investigated.") +
            p("The trend in reactivity of these halogens can be determined by carrying out three experiments as shown in Table 1.1. "
              "In each experiment, an aqueous halide ion is added to a solution containing a halogen.") +
            cap("Table 1.1") + t11 +
            p("For each experiment in Table 1.1, predict the colour of the final solution, and write an equation for any reaction that occurs. "
              "State clearly if no reaction occurs.") +
            p("Explain your answers, using " + E0 + " values from the " + DB + ". " + mk(5))),
    ("(c)", p("In 1931, Erich Hückel proposed a theory to help predict whether a compound or ion is aromatic.") +
            p("When a species has a conjugated, planar, cyclic structure with [4" + i("n") + " + 2]π electrons (where " + i("n") +
              " = 0 or a positive integer 1, 2, 3 etc.), it is said to be aromatic.") +
            p("A molecule with a conjugated system has multiple p orbitals interacting with each other, resulting in delocalised electrons.") +
            p("Deduce how many π electrons are present in " + b("A") + " and " + b("B") + ". Hence, state whether " + b("A") + " and " + b("B") +
              " are aromatic or non-aromatic. " + mk(2)) +
            FIG),
    ("(d)", p("Hückel’s theory can be used to classify pyrrole as aromatic. Pyrrole has six π electrons. Two representations of pyrrole are shown in Fig. 1.1.") +
            FIG + cap("Fig. 1.1") +
            p("Nitrogen atoms undergo the same type of hybridisation as carbon atoms.") +
            p("By reference to orbital overlap and the hybridisation of the nitrogen and carbon atoms, suggest how the σ and π bonds are formed in a pyrrole molecule. " + mk(3))),
    ("(e)", p("Aqueous solutions of pyrrolidine, pyrrole and γ-lactam are basic. Fig. 1.2 shows them listed in decreasing order of basicity.") +
            FIG + cap("Fig. 1.2") +
            p("Explain the relative basicities of aqueous solutions of pyrrolidine, pyrrole and γ-lactam in terms of their structures. " + mk(3))),
    ("(f)", p("The pyrrole ring is found in some medicines. An example is atorvastatin, shown in Fig. 1.3, which is used to lower cholesterol.") +
            FIG + cap("Fig. 1.3") +
            p("One step in its synthesis is the reaction that forms a carbon-carbon bond as shown in Fig. 1.4.") +
            FIG + cap("Fig. 1.4") +
            p("The steps for the mechanism for the reaction in Fig. 1.4 are shown in Fig. 1.5.") +
            FIG + cap("Fig. 1.5")),
    ("(f)(i)", p("Name all the functional groups, in addition to pyrrole, in atorvastatin. " + mk(3))),
    ("(f)(ii)", p("Suggest the type of reaction shown in Fig. 1.4. " + mk(1))),
    ("(f)(iii)", p("Draw three curly arrows on " + b("step 2") + " of Fig. 1.5 to complete the mechanism for " + b("step 2") + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q2
t21 = table(tr(th("test"), th("reagents and conditions"), th("compounds formed"), th("other information")),
            tr(td("1"), td(chem("excess H2 / Ni")), td(b("G") + ", " + chem("C11H22O")), td(b("G") + " contains three chiral centres.")),
            tr(td("2"), td(chem("excess Br2(l)") + " in absence of ultra-violet light"), td(b("H") + ", " + chem("C11H14OBr6")), td("")),
            tr(td("3"), td("2,4-DNPH"), td("orange precipitate"), td("")),
            tr(td("4"), td("Fehling’s reagent"), td("no reaction"), td("")),
            tr(td("5"), td("excess hot concentrated acidified " + chem("KMnO4")),
               td("<p>" + b("J") + ", " + chem("C2H4O2") + "</p><p>" + b("K") + ", " + chem("C4H6O3") + "</p><p>" + b("L") + ", " + chem("C5H4O6") + "</p>"),
               td("<p>" + b("J") + ", " + b("K") + " and " + b("L") + " all effervesce on addition of " + chem("Na2CO3(aq)") + ".</p>" +
                  "<p>" + b("K") + " and " + b("L") + " form an orange precipitate with 2,4-DNPH.</p>")))
Q[2] = dict(marks=20, intro=[], parts=[
    ("(a)", p("A platinum catalyst can be used for the removal of oxides of nitrogen from the exhaust gases of car engines.")),
    ("(a)(i)", p("Write an equation for the reaction that removes NO from the exhaust gases of car engines. " + mk(1))),
    ("(a)(ii)", p("State whether platinum acts as a homogeneous or heterogeneous catalyst in this reaction. Explain your answer. " + mk(1))),
    ("(b)", p("Explain, with the aid of a labelled Boltzmann distribution diagram, the effect of a catalyst on a rate constant. " + mk(3))),
    ("(c)", p("Enzymes, E, are biological catalysts that can catalyse the breakdown of a substrate, S, to a product, P. "
              "This reaction involves the formation of an intermediate enzyme–substrate complex, ES.") +
            p("Sketch a graph to show the relationship between the rate of reaction and substrate concentration, using a fixed amount of enzyme, "
              "in this reaction. Explain your reasoning. " + mk(2))),
    ("(d)", p("The kinetics of the enzyme-catalysed breakdown of a substrate are investigated. A mechanism is suggested in Fig. 2.1.") +
            FIG + cap("Fig. 2.1") +
            p("Key: E = enzyme, S = substrate, ES = enzyme–substrate complex, P = product") +
            p("The rate constants for these reactions are " + kk("f") + ", " + kk("r") + " and " + kk("2") + ".") +
            p("The rate of formation of the ES is rate = " + kk("f") + "[E][S].") +
            p("The rate of breakdown of the ES is given by the equation below.") +
            c("rate = (rate equation for the reverse reaction of step 1) + (rate equation of step 2)") +
            p("When the rate of formation of the ES is equal to the rate of breakdown of the ES, the concentration of the ES, [ES], can be determined.") +
            p("The expression in terms of [ES] can be used to deduce the Michaelis constant, " + K + sub("m") +
              ". This constant is a measure of the affinity of an enzyme for its substrate.") +
            c(K + sub("m") + " = (" + kk("r") + " + " + kk("2") + ") / " + kk("f"))),
    ("(d)(i)", p("Write the rate equation for the reverse reaction of step 1 and the rate equation of step 2. " + mk(1))),
    ("(d)(ii)", p("Use your answer to " + b("(d)(i)") + " and the information given to determine an expression for the concentration of the ES, [ES]. " + mk(1))),
    ("(d)(iii)", p("Use your answer to " + b("(d)(ii)") + " to deduce an expression for " + K + sub("m") + " in terms of [E], [S] and [ES]. " + mk(1))),
    ("(e)", p("Compound " + b("F") + ", " + chem("C11H14O") + ", contains one branched carbon chain connected to a 2-cyclopenten-1-one structure.") +
            FIG +
            p(b("F") + " has two different functional groups, displays " + i("cis-trans") + " isomerism and does " + b("not") + " contain a chiral centre.") +
            p("A series of tests are carried out on " + b("F") + ". Table 2.1 shows the compounds formed, and other information, when " + b("F") +
              " is added to different reagents under specific conditions.") +
            cap("Table 2.1") + t21 +
            p("For each of the five tests, state the type of reaction occurring, if any. For each compound, state what the information in Table 2.1 "
              "tells you about the functional groups it contains. Include your reasoning.") +
            p("Suggest possible structures for " + b("J") + ", " + b("K") + " and " + b("L") + ".") +
            p("Use these structures to deduce possible structures for " + b("F") + ", " + b("G") + " and " + b("H") + ". " + mk(10))),
])

# ---------------------------------------------------------------- Q3
t31 = table(tr(th("acid"), th("p" + K + sub("a"))),
            tr(td(chem("NH4^+^")), td("9.25")),
            tr(td(chem("H2S")), td("6.98")))
Q[3] = dict(marks=19, intro=[], parts=[
    ("(a)", p("The Haber process for the production of ammonia is an exothermic reaction which involves the equilibrium shown.") +
            eqn("equilibrium 1   " + chem("N2(g) + 3H2(g)") + " ⇌ " + chem("2NH3(g)") + "     " + DS + " = " + M + "199" + NB + "J" + NB + "K" + sup(M + "1") + NB + "mol" + sup(M + "1")) +
            p("This process is usually carried out at 2.00 " + TIMES + " 10" + sup("4") + " kPa and 450 °C.")),
    ("(a)(i)", p("Use bond energy values from the " + DB + " to calculate the standard enthalpy change of reaction, " + DH + ", for equilibrium 1. " + mk(1))),
    ("(a)(ii)", p("Calculate the standard Gibbs free energy change of reaction, " + DG + ", for equilibrium 1 at 450 °C. " + mk(2))),
    ("(a)(iii)", p("Use the information about " + DH + " and " + DS + " to predict the effect of increasing temperature on the spontaneity of the formation of ammonia. "
                   "Explain your answer. " + mk(2))),
    ("(b)", p("It has been suggested that the colour of the planet Jupiter is due to the presence of ammonium hydrosulfide, " + chem("NH4SH") + ".") +
            p(chem("NH4SH") + " can be produced by passing " + chem("H2S") + " through a concentrated solution of " + chem("NH3") +
              " to form an equilibrium mixture containing two acid-base pairs.") +
            eqn("equilibrium 2   " + chem("NH3 + H2S") + " ⇌ " + chem("NH4^+^ + HS^-^")) +
            p("The p" + K + sub("a") + " values for " + chem("NH4^+^") + " and " + chem("H2S") + " are given in Table 3.1.") +
            cap("Table 3.1") + t31),
    ("(b)(i)", p("Identify the two conjugate acid-base pairs in equilibrium 2. " + mk(1))),
    ("(b)(ii)", p("Use the p" + K + sub("a") + " values in Table 3.1 to calculate the equilibrium constant, " + K + sub("eq") + ", for equilibrium 2. " + mk(2))),
    ("(c)", p("Liquid ammonia exists in an equilibrium.") +
            c(chem("2NH3") + " ⇌ " + chem("NH4^+^ + NH2^-^")) +
            p("Draw the ‘dot-and-cross’ diagram for the " + chem("NH2^-^") + " ion.") +
            p("Use VSEPR theory to predict the H-N-H bond angle in the " + chem("NH2^-^") + " ion. Explain your answer. " + mk(3))),
    ("(d)", p("Cyclohexanone reacts with propyne, " + chem("CH3C≡CH") + ", in the presence of " + chem("NaNH2") + " as shown in Fig. 3.1.") +
            FIG + cap("Fig. 3.1") +
            p("The reaction happens in a two-step process.") +
            p("In step 1, sodium amide reacts with propyne to form " + chem("CH3C≡C^-^") + " ions.") +
            p("In step 2, the " + chem("CH3C≡C^-^") + " ions react with cyclohexanone to form the product.")),
    ("(d)(i)", p("Name the mechanism for the overall reaction shown in Fig. 3.1. " + mk(1))),
    ("(d)(ii)", p("Draw a mechanism for step 2. Include all relevant lone pairs, dipoles, curly arrows and charges. Include the structure of the organic intermediate. " + mk(4))),
    ("(e)", p("When sodium amide is dissolved in liquid ammonia, the complex " + chem("[Na(NH3)6]^+^") + " is formed.")),
    ("(e)(i)", p("Draw the three-dimensional diagram for " + chem("[Na(NH3)6]^+^") + ". " + mk(1))),
    ("(e)(ii)", p("Define the terms ligand and complex by reference to the complex " + chem("[Na(NH3)6]^+^") + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Describe the trend in the first ionisation energy of the elements down Group 1.") +
            p("Explain your answer. " + mk(2))),
    ("(b)", p("Fig. 4.1 shows the graph of the log of the successive ionisation energies for sodium.") +
            FIG + cap("Fig. 4.1")),
    ("(b)(i)", p("An atom of sodium has a total of 11 electrons present in s orbitals and p orbitals. Give the electronic configuration for an atom of sodium. " + mk(1))),
    ("(b)(ii)", p("For sodium, state all the ionisation energies (1st to 11th) that involve removing an electron from a full orbital. " + mk(1))),
    ("(b)(iii)", p("Describe the shape of the graph for the trend in the log of successive ionisation energies for sodium in Fig. 4.1. Explain your answer. " + mk(2))),
    ("(c)", p("Describe the reactions, if any, of " + chem("NaCl") + ", " + chem("AlCl3") + " and " + chem("SiCl4") + " with an excess of water.") +
            p("Write equations for any reactions that occur, and suggest the pH of the resulting mixtures. " + mk(3))),
    ("(d)", p(chem("BCl3") + ", " + chem("AlCl3") + " and " + chem("GaCl3") + " can act as Lewis acids.")),
    ("(d)(i)", p("Explain what is meant by a Lewis acid. " + mk(1))),
    ("(d)(ii)", p("Suggest the trend in the Lewis acid strength of the chlorides " + chem("BCl3") + ", " + chem("AlCl3") + " and " + chem("GaCl3") +
                  " towards ammonia, " + chem("NH3") + ". Explain your answer by reference to orbital overlap only. " + mk(2))),
    ("(e)", p(chem("Ga2Cl6") + " has a similar structure to that of " + chem("Al2Cl6(g)") + ". Draw a structure for " + chem("Ga2Cl6") +
              ", and identify the types of bond formed. " + mk(1))),
    ("(f)", p(chem("GaCl3") + " and " + chem("Ga2Cl6") + " exist in an equilibrium in the gas phase.") +
            c(chem("2GaCl3(g)") + " ⇌ " + chem("Ga2Cl6(g)")) +
            p("A sample of 0.881 g of " + chem("GaCl3") + " is left to reach equilibrium in a sealed flask. At equilibrium, it is found that 30.0% of " +
              chem("GaCl3") + " has reacted. The total pressure in the flask is 250 kPa.") +
            p("Determine the equilibrium amount of " + chem("GaCl3") + " and " + chem("Ga2Cl6") + ", and hence calculate the value of " + K + sub("p") +
              " for this equilibrium. State its units. " + mk(3))),
    ("(g)", p("Methoxybenzene reacts with " + chem("SOCl2") + " in the presence of " + chem("GaCl3") + " as shown in Fig. 4.2.") +
            FIG + cap("Fig. 4.2") +
            p("The mechanism of this reaction is similar to that of the chlorination of benzene.") +
            p("In the first step of the mechanism, " + chem("SOCl2") + " reacts with " + chem("GaCl3") + " to generate the electrophile " + chem("SOCl^+^") + ".")),
    ("(g)(i)", p("Draw the mechanism for the reaction shown in Fig. 4.2. Use the displayed formula of " + chem("SOCl^+^") +
                 ", and show relevant curly arrows, charges and the structure of the intermediate.") +
               p("Include an equation for the formation of " + chem("SOCl^+^") + ". " + mk(3))),
    ("(g)(ii)", p("The reaction shown in Fig. 4.2 forms a small amount of a byproduct " + b("M") + " with the molecular formula " + chem("C14H14O3S") +
                  ". Suggest the structure of " + b("M") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Transition elements have characteristic physical and chemical properties.")),
    ("(a)(i)", p("Explain why transition elements have variable oxidation states. " + mk(1))),
    ("(a)(ii)", p("Explain why the atomic radii of the transition elements are relatively similar. " + mk(1))),
    ("(a)(iii)", p("State how the melting point of cobalt compares to that of calcium. Explain your answer. " + mk(1))),
    ("(b)", p("Haemoglobin plays a vital role in oxygen transport. Carbon monoxide can bind to haemoglobin at the same binding site as oxygen.")),
    ("(b)(i)", p("State the type of reaction that occurs between haemoglobin and carbon monoxide. " + mk(1))),
    ("(b)(ii)", p("Suggest why carbon monoxide is poisonous. " + mk(1))),
    ("(c)", p("The concentration of dissolved oxygen in rivers and lakes can be determined by the Winkler method in a three-step process.") +
            p("A sample of river water is shaken with aqueous alkaline " + chem("Mn^2+^") + " ions, forming a precipitate of " + chem("MnO2") + ".") +
            c(chem("2Mn^2+^(aq) + 4OH^-^(aq) + O2(aq)") + " → " + chem("2MnO2(s) + 2H2O(l)")) +
            p("The " + chem("MnO2") + " precipitate is separated and reacted with an excess of " + chem("I^-^(aq)") + " in acid to liberate " + chem("I2(aq)") + ".") +
            c(chem("MnO2(s) + 2I^-^(aq) + 4H^+^(aq)") + " → " + chem("Mn^2+^(aq) + I2(aq) + 2H2O(l)")) +
            p("The resulting solution, containing " + chem("I2(aq)") + ", is titrated with " + chem("S2O3^2-^(aq)") + ".") +
            c(chem("2S2O3^2-^(aq) + I2(aq)") + " → " + chem("S4O6^2-^(aq) + 2I^-^(aq)")) +
            p("A 250.0 cm" + sup("3") + " sample of river water requires 23.80 cm" + sup("3") + " of 0.0450 " + MDM + " " + chem("S2O3^2-^") + " for this titration.") +
            p("Calculate the concentration of dissolved oxygen in the sample in g" + NB + "dm" + sup(M + "3") + ". " + mk(3))),
    ("(d)(i)", p("Define the term standard electrode potential, " + E0 + ". " + mk(1))),
    ("(d)(ii)", p("The standard electrode potential of the " + chem("Ce^4+^(aq)/Ce^3+^(aq)") + " electrode is +1.72 V.") +
                p("Draw a fully labelled diagram of the experimental set-up used to measure the standard electrode potential, " + E0 + ", of the " +
                  chem("Ce^4+^(aq)/Ce^3+^(aq)") + " electrode. Include all necessary chemicals. " + mk(3))),
    ("(d)(iii)", p("A solution containing aqueous cerium(IV) ions, " + chem("Ce^4+^(aq)") + ", reacts with bismuth metal, Bi(s), as shown.") +
                 eqn(chem("3Ce^4+^(aq) + Bi(s) + H2O(l)") + " → " + chem("3Ce^3+^(aq) + BiO^+^(aq) + 2H^+^(aq)") + "     " + DG + " = " + M + "405.3 kJ mol" + sup(M + "1")) +
                 p("Use values from the " + DB + " to calculate the standard electrode potential, " + E0 + ", of the " + chem("BiO^+^(aq)") + ", " +
                   chem("H^+^(aq)") + "/Bi(s) electrode. Show all working. " + mk(3))),
    ("(e)", p("Compound " + b("P") + " is a useful building block in organic synthesis. It can be synthesised from 3-phenylpropanoic acid in three steps as shown in Fig. 5.1.") +
            FIG + cap("Fig. 5.1")),
    ("(e)(i)", p("Suggest structures for the organic compounds " + b("N") + " and " + b("O") + ". " + mk(2))),
    ("(e)(ii)", p("Suggest reagents and conditions for each of the steps 1, 2 and 3. " + mk(3))),
])

def lead_inline(h):
    """A part's FIRST paragraph is left bare so its text continues the line the label sits on
    (render_parts._render_owner(lead_inline=True)); a <p> is a block and would drop below the label."""
    if h.startswith("<p>"):
        j = h.index("</p>")
        return h[3:j] + h[j + 4:]
    return h

def nbsp(h):
    """Bind a value to its unit (and the factors of a x 10^n) so a line never breaks between them."""
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|V\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol|kPa)\b)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

# ---------------------------------------------------------------- assemble
def strip(h):
    h = h.replace(FIG, " ").replace("<br>", " ").replace(NB, " ")
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
