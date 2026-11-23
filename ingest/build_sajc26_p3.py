"""Hand transcription of SAJC 2026 H2 Prelim Paper 3 (9476/03, 15 Sept 2026; Section A Q1-Q4 = 55 marks, Section B answer ONE of
Q5/Q6 = 20 marks, 75 as sat; 95 as ingested because both Section B questions are loaded) -> questions.json + asset_plan.json.
Typed from the school's Word file and the Word-exported PDF (the two agree word for word; only sub/superscript formatting
differs in a plain-text diff). Same output contract as build_rvhs26_p3.py / build_sajc26_p2.py, i.e. what
gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_sajc26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school SAJC --year 2026 --paper 3 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_sajc26_p2.py / build_rvhs26_p3.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped (Q2 "(c)");
  * [n] is a span.mk written in place where the paper prints it (a mark printed under an answer space goes at the end of the
    last instruction paragraph; a mark under a figure or table the candidate completes goes at the end of the instruction);
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c; a structure's own name label
    (chloroformyl fluoride, phenylboronic acid, benzoyl chloride ...) is inside the snip; Table 5.1 (structures in its cells)
    is one picture with the caption typed; the bleaching scheme at Q6(d) (a two-row table of structures) is one picture;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed: Table 6.1; fill-in
    blanks inside a sentence or an equation are kept: Q2(c)(ii) "from ... to ...", Q4(a));
  * asset slot = part label without brackets ('biii', 'div'); 'intro' for the stem. Text and a figure the school prints
    BETWEEN two sub-parts is a tail after the part before it; a figure in a tail takes that part's slot
    (Q2 4-aminophenol scheme -> 'biii'; Q2 N-substituted scheme -> 'div'; Q5 Table 5.1 -> 'bii').
  * Q3 equation labels printed under an equation (boric acid / sodium borate; boroxine) are typed as a second centred line:
    the school aligns each name under its species by spacing, which a centred line cannot reproduce.
Typography as the other 2026 builders: x -> multiplication sign, hyphen/en dash/figure dash minus -> U+2212, "250 oC" ->
"250 °C", italic element l, the standard-state sign (also for the school's U+A74A at Q6(a)(v)) for the small raised o,
"+1.47V" -> "+1.47 V".
School slips corrected (listed in the handoff note; veto-able):
  Q3 stem "according to the following equation" gets its full stop;
  Q6(c)(ii) "One of these amino acid residues are present" -> "is present";
  Q6(c) tail "residues ... contains more than 1 chiral carbon" -> "contain".
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SAJC", "H2", "P3", 2026
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
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)

L = '<i class="el">l</i>'                  # element l
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
STD = sup('<span class="pl-sym">⦵</span>')
EM = "&emsp;"
DBK = i("Data Booklet")
DOTS = "………………"
CL = "C" + L
CL2 = CL + sub(2)
F2 = "F" + sub(2)
CLF = CL + "F"
CLF3 = CLF + sub(3)
CLFY = CLF + sub("<i>y</i>")
H3BO3 = "H" + sub(3) + "BO" + sub(3)
BORATE = "NaH" + sub(2) + "BO" + sub(3)
PHB = "C" + sub(6) + "H" + sub(5) + "B(OH)" + sub(2)
SAG = "C" + sub(6) + "H" + sub(5) + "SAg"
THIO = "C" + sub(6) + "H" + sub(5) + "S" + sup(M)
AGNO3 = "AgNO" + sub(3)
HAP = "Ca" + sub(5) + "(PO" + sub(4) + ")" + sub(3) + "OH"
FAP = "Ca" + sub(5) + "(PO" + sub(4) + ")" + sub(3) + "F"
PO4 = "PO" + sub(4) + sup("3" + M)
MNO2 = "MnO" + sub(2)
MN2O3 = "Mn" + sub(2) + "O" + sub(3)
def iso(a, sym, ch=""): return sup(a) + sym + (sup(ch) if ch else "")
def ion(sym, ch): return sym + sup(ch)
EA = i("E") + STD
DG = DEL + i("G") + STD
DH_C = DEL + i("H") + STD + sub("c")
DH_R = DEL + i("H") + STD + sub("r")
KSP = K + sub("sp")
KA = K + sub("a")
def eq(n, body): return p("equilibrium %s" % n + EM + body)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (18)
Q[1] = dict(marks=18, intro=[
    p("Interhalogen compounds are molecules that contain two or more different halogen atoms and no atoms of other elements. "
      "An example of an interhalogen compound is " + CLF + ".")], parts=[
    ("(a)", p(CL + " is an atom found in several interhalogen compounds. n electrons are removed from the valence shell of " + CL +
             " to form " + CL + sup("n+") + ". Successive electrons can be further removed from " + CL + sup("n+") + " according to the equation:") +
            ceqn(CL + sup("n+") + "(g) → " + CL + sup("(n+1)+") + "(g) + e" + sup(M)) +
            p("Fig 1.1 shows the graph of the log of the successive ionisation energies for " + CL + sup("n+") + ".") +
            FIG + cap("Fig 1.1")),
    ("(a)(i)", p("With reference to Fig 1.1, show that the value of n is 4. Explain your reasoning. " + mk(2))),
    ("(a)(ii)", p("In an electric field, a beam of " + iso(16, "O", "2+") + " ions is deflected by an angle of +0.50°.") +
                p("Calculate the angle of deflection for a beam of " + iso(35, CL, "4+") + " ions under identical conditions. " + mk(1))),
    ("(b)", p(CLF + " reacts with carbon monoxide to form chloroformyl fluoride.") + FIG),
    ("(b)(i)", p("State and explain, with reference to the Valence Shell Electron Pair Repulsion theory, the shape of a chloroformyl fluoride molecule. " + mk(2)),
     p("The carbon and oxygen atoms in chloroformyl fluoride are sp" + sup(2) + " hybridised.")),
    ("(b)(ii)", p("With the aid of a labelled diagram, explain how the orbitals overlap to form the C=O bond in chloroformyl fluoride. " + mk(2))),
    ("(b)(iii)", p("Suggest how the electrons are arranged in the second shell of the oxygen atom so that the C=O bond in chloroformyl fluoride can occur. " + mk(2))),
    ("(c)", p("Interhalogen compounds may be synthesised by reacting their constituent halogens under controlled temperatures and pressures.") +
            p("A 2.00 dm" + sup(3) + " vessel was filled with " + CL2 + "(g) and " + F2 + "(g) at 250 °C. The initial partial pressures of " + CL2 +
              " and " + F2 + " in the vessel were 50 kPa and 200 kPa respectively.") +
            p("The mixture was allowed to react completely to form a single gaseous product, " + CLFY + ", according to the following equation:") +
            ceqn(CL2 + "(g) + " + i("y") + F2 + "(g) → 2" + CLFY + "(g)") +
            p("Upon completion, the total pressure in the vessel was 150 kPa at constant temperature.")),
    ("(c)(i)", p("Calculate the initial amount of " + CL2 + "(g), in moles, in the vessel. " + mk(2))),
    ("(c)(ii)", p("Show that the molecular formula of the product is " + CLF3 + ". " + mk(2))),
    ("(c)(iii)", p("The actual partial pressure of " + CLF3 + " formed in the sealed vessel is found to be lower than the partial pressure predicted by the "
                   "general gas equation. Explain this observation. " + mk(1))),
    ("(c)(iv)", p("Explain what is meant by the term " + i("electronegativity") + ". " + mk(2))),
    ("(c)(v)", p("Draw the molecular arrangement of " + CLF3 + ", showing its shape clearly.") +
               p("On the same diagram, indicate the polarity of each of the bonds it contains and the overall polarity of the molecule. " + mk(2))),
])

# ---------------------------------------------------------------- Q2  (18)
Q[2] = dict(marks=18, intro=[
    p("Daniell cell, invented by the British chemist John Frederic Daniell in 1836, is popularly known as a zinc-copper battery.")], parts=[
    ("(a)", p("The Daniell cell is an electrochemical cell consisting of Cu" + sup("2+") + "(aq)/Cu(s) electrode and a Zn" + sup("2+") + "(aq)/Zn(s) electrode.") +
            p("Draw a labelled diagram of the Daniell cell set-up.") +
            p("Include all necessary substances and relevant pieces of apparatus.") +
            p("It is " + b("not") + " necessary to state conditions used. " + mk(3)),
     p("The Daniell cell has a fixed, low voltage and is not rechargeable. Hence, better and more efficient cells have been researched. One such cell is the "
       "Zinc-Manganese Dioxide battery, which consists of a ZnO/Zn electrode and a " + MNO2 + "/" + MN2O3 + " electrode in an alkaline electrolyte.")),
    ("(b)", p("The standard cell potential, " + EA + sub("cell") + ", for the Zinc-Manganese Dioxide cell is +1.47 V.") +
            p("The half-equation at the cathode when the cell is discharging is shown.") +
            ceqn("2" + MNO2 + " + H" + sub(2) + "O + 2e" + sup(M) + " → " + MN2O3 + " + 2OH" + sup(M))),
    ("(b)(i)", p("Write the half-equation at the anode when the cell is discharging. " + mk(1))),
    ("(b)(ii)", p("The " + EA + " for the ZnO/Zn electrode is " + M + "1.28 V.") +
                p("Calculate the standard electrode potential, " + EA + ", for the " + MNO2 + "/" + MN2O3 + " electrode. " + mk(1))),
    ("(b)(iii)", p("Calculate the standard Gibbs free energy change, " + DG + ", for the reaction in the Zinc-Manganese Dioxide cell. " + mk(1)),
     p("4-aminophenol is a key ingredient in paracetamol. Instead of using traditional chemical reagents, researchers are exploring the use of electrolysis "
       "to produce 4-aminophenol from nitrobenzene.") + FIG),
    ("(c)(i)", p("Step 1 involves reduction of nitrobenzene to phenylhydroxylamine using an acidic electrolyte.") +
               p("During the reduction of nitrobenzene, bubbles were observed at the cathode. Identify this gas and write an ionic half-equation to explain its formation. " + mk(1))),
    ("(c)(ii)", p("State the change in oxidation state of nitrogen in step 2.") +
                p("from ……………… to ……………… " + mk(1))),
    ("(c)(iii)", p("State the reagent(s) for step 3. " + mk(1))),
    ("(c)(iv)", p("The yield of paracetamol from step 3 is low because a mixture of products is formed. Draw the side-product formed from step 3. " + mk(1))),
    ("(d)", p("Phenylhydroxylamine reacts with methanol to form " + i("N") + "-methyl-4-aminophenol.") + FIG),
    ("(d)(i)", p("The following nitrogen containing compounds are shown in order of increasing basicity.") +
               c("phenylhydroxylamine < 4-aminophenol < " + i("N") + "-methyl-4-aminophenol") +
               p("Explain this order. " + mk(2)),
     p("The standard enthalpy change of combustion of " + i("N") + "-methyl-4-aminophenol, phenylhydroxylamine and methanol are shown in Table 2.1.") +
     cap("Table 2.1") +
     table(tr(th("compound"), th("formula"), th(DH_C + " / kJ mol" + sup(M + "1"))),
           tr(td(i("N") + "-methyl-4-aminophenol"), td("CH" + sub(3) + "NHC" + sub(6) + "H" + sub(4) + "OH(s)"), td(M + "3650")),
           tr(td("phenylhydroxylamine"), td("C" + sub(6) + "H" + sub(5) + "NHOH(l)"), td(M + "3090")),
           tr(td("methanol"), td("CH" + sub(3) + "OH(l)"), td(M + "726")))),
    ("(d)(ii)", p("Define the term " + i("standard enthalpy change of combustion") + ". " + mk(1))),
    ("(d)(iii)", p("Use the data in Table 2.1 to calculate the standard enthalpy change for the reaction forming " + i("N") +
                   "-methyl-4-aminophenol from phenylhydroxylamine and methanol.") +
                 p("The standard enthalpy change of combustion of water is zero.") +
                 p(DH_R + " = ……………………… " + mk(1))),
    ("(d)(iv)", p("A student suggests using bond energy values to calculate " + DH_R + ". Suggest which method will give a poorer estimate of " + DH_R +
                  ". Explain your answer. " + mk(1)),
     p("Phenylhydroxylamine can react with different alcohols to form different " + i("N") + "-substituted-4-aminophenol.") + FIG +
     p("The relative rates are shown in Table 2.2.") +
     cap("Table 2.2") +
     table(tr(th("alcohol"), th("formula"), th("relative rate")),
           tr(td("methanol"), td("CH" + sub(3) + "OH"), td("1.00")),
           tr(td("ethanol"), td("CH" + sub(3) + "CH" + sub(2) + "OH"), td("0.65")),
           tr(td("isopropanol"), td("(CH" + sub(3) + ")" + sub(2) + "CHOH"), td("0.12")),
           tr(td("tert-butanol"), td("(CH" + sub(3) + ")" + sub(3) + "COH"), td("0.01")))),
    ("(d)(v)", p("Draw the structure of the " + i("N") + "-substituted-4-aminophenol formed when phenylhydroxylamine reacts with isopropanol. " + mk(1))),
    ("(d)(vi)", p("Using Table 2.2, describe and explain how the structure of the alcohol affects the relative rate of the reaction. " + mk(2))),
])

# ---------------------------------------------------------------- Q3  (12)
Q[3] = dict(marks=12, intro=[
    p("Boric acid, " + H3BO3 + ", is a weak monobasic (monoprotic) acid. It reacts with water according to the following equation."),
    ceqn(H3BO3 + " + H" + sub(2) + "O ⇌ H" + sub(4) + "BO" + sub(4) + sup(M) + " + H" + sup("+"))], parts=[
    ("(a)", p("Using the equation above, explain why boric acid does not behave like a typical Brønsted-Lowry acid. " + mk(1))),
    ("(b)", p("Phenylboronic acid, " + PHB + ", is a Lewis acid. It has a high melting point of 218 °C.") + FIG),
    ("(b)(i)", p("Explain what is meant by a Lewis acid. " + mk(1))),
    ("(b)(ii)", p("Draw the structure of the product formed when " + PHB + " reacts with NH" + sub(3) + ". Show the bonding between the two compounds clearly. " + mk(1)),
     p("In the presence of a dehydrating agent and heat, phenylboronic acid reacts with itself to form boroxine.") +
     ceqn("3" + PHB + " → C" + sub(18) + "H" + sub(15) + "B" + sub(3) + "O" + sub(3) + " + 3H" + sub(2) + "O") +
     c("boroxine")),
    ("(b)(iii)", p("Boroxine molecules have no overall dipole moment. Suggest a possible structure of boroxine. " + mk(1))),
    ("(b)(iv)", p("Suggest why the melting point of boroxine is similar to the melting point of phenylboronic acid. " + mk(1))),
    ("(c)", p("Boric acid reacts with NaOH(aq) to form sodium borate.") +
            ceqn(H3BO3 + " + NaOH → " + BORATE + " + H" + sub(2) + "O") +
            c("boric acid" + EM + EM + "sodium borate") +
            p("The " + KA + " of boric acid is 5.4 × 10" + sup(M + "10") + " " + MDM + " at 298 K.")),
    ("(c)(i)", p("Suggest, with the aid of an equation, why the pH of sodium borate solution is more than 7. " + mk(1))),
    ("(c)(ii)", p("Calculate the pH of 0.0600 " + MDM + " " + H3BO3 + "(aq) at 298 K. Show your working. " + mk(2))),
    ("(c)(iii)", p("Boric acid and sodium borates are used as an alkaline pH buffer in eye drops and contact lens.") +
                 p("A buffer solution of pH 8.8 is prepared using 25.0 cm" + sup(3) + " of 0.0600 " + MDM + " " + H3BO3 + " and " + i("x") +
                   " cm" + sup(3) + " of 0.0900 " + MDM + " NaOH.") +
                 p("Calculate the volume, " + i("x") + " cm" + sup(3) + ", of 0.0900 " + MDM + " NaOH required to make a buffer solution of pH 8.8. " + mk(4))),
])

# ---------------------------------------------------------------- Q4  (7)
Q[4] = dict(marks=7, intro=[
    p("Geraniol, C" + sub(10) + "H" + sub(18) + "O, is widely used in fragrance and cosmetic industries due to its pleasant rose-like scent. "
      "It has two different functional groups."),
    p("Geraniol undergoes the following oxidation reactions."),
    ul("With hot acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ", it forms compound " + b("E") + ", C" + sub(10) + "H" + sub(16) + "O" + sub(2) + ".",
       "With hot acidified KMnO" + sub(4) + ", it forms compounds " + b("F") + ", C" + sub(3) + "H" + sub(6) + "O, and " + b("G") + ", C" + sub(5) + "H" + sub(8) + "O" + sub(3) + ".")], parts=[
    ("(a)", p("Construct a balanced equation for the oxidation of geraniol to form " + b("F") + " and " + b("G") + ".") +
            p("You should use [O] to represent the oxidising agent.") +
            ceqn("C" + sub(10) + "H" + sub(18) + "O + …………………………. → C" + sub(3) + "H" + sub(6) + "O + C" + sub(5) + "H" + sub(8) + "O" + sub(3) + " + …………………………. " + mk(1)),
     p("Geraniol reacts with excess hydrogen in the presence of nickel to give C" + sub(10) + "H" + sub(22) + "O.") +
     p("Both " + b("F") + " and " + b("G") + " react with alkaline aqueous iodine forming a yellow precipitate.") +
     p("Geraniol, " + b("E") + ", " + b("F") + " and " + b("G") + " do not contain any chiral carbons.")),
    ("(b)", p("Suggest possible structures of geraniol, " + b("E") + ", " + b("F") + " and " + b("G") + ". You may find it useful to determine the structures of " +
             b("F") + " and " + b("G") + " first.") +
            p("For each reaction, state the " + i("type of reaction") + " described and explain what the information tells you about the functional groups present "
              "in each compound. " + mk(6))),
])

# ---------------------------------------------------------------- Q5  (20)  Section B
Q[5] = dict(marks=20, intro=[
    p("2-phenylthioethanol is an important building block in the synthesis of various organic molecules."),
    p("A chemical manufacturing plant produces 2-phenylthioethanol through the process below.") + FIG], parts=[
    ("(a)", p("The first step of the synthesis involves the deprotonation of thiophenol to form thiophenolate. Thiophenolate then reacts with 2-chloroethanol by an S" +
             sub("N") + "2 reaction to form 2-phenylthioethanol.")),
    ("(a)(i)", p("Suggest why the deprotonation of thiophenol was necessary in the first step of the synthesis. " + mk(1))),
    ("(a)(ii)", p("Draw a mechanism for the reaction between thiophenolate and 2-chloroethanol to form 2-phenylthioethanol. Show relevant lone pairs of electrons, "
                  "dipoles and curly arrows.") +
                p("You may represent thiophenolate as RS" + sup(M) + ". " + mk(3))),
    ("(b)", p("Benzoyl chloride reacts with 2-phenylthioethanol to form compound " + b("X") + ".") + FIG),
    ("(b)(i)", p("Draw the structure of compound " + b("X") + ". " + mk(1))),
    ("(b)(ii)", p("Benzoyl chloride is synthesised from methylbenzene in two steps.") +
                p("Draw the structure of the intermediate and suggest reagents and conditions for each of the steps. " + mk(3)),
     p("Polyethylene terephthalate (PET) and polyisobutylene (PIB) are two common polymers used in the packaging and storage of organic compounds, such as "
       "2-phenylthioethanol.") + cap("Table 5.1") + FIG),
    ("(b)(iii)", p("Define polymer. " + mk(1))),
    ("(b)(iv)", p("Suggest the type of reaction used to form PET and PIB.") + p("PET:") + p("PIB: " + mk(1))),
    ("(c)", p("In the synthesis of 2-phenylthioethanol, some thiophenolate ions, " + THIO + ", remain unreacted. As thiophenolate ions are toxic, they must be "
              "removed before the wastewater can be discharged. One treatment method involves adding silver nitrate, which precipitates silver thiophenolate, " + SAG + ".") +
            p(SAG + " is sparingly soluble in water.") +
            ceqn(SAG + "(s) ⇌ " + THIO + "(aq) + Ag" + sup("+") + "(aq)") +
            p("The numerical value of the solubility product of " + SAG + ", " + KSP + ", is 1.2 × 10" + sup(M + "16") + ".")),
    ("(c)(i)", p("Write the expression for the " + KSP + " of " + SAG + " stating its units. " + mk(1))),
    ("(c)(ii)", p("A 500 cm" + sup(3) + " sample of wastewater contains 0.030 " + MDM + " of thiophenolate ions.") +
                p("Calculate the minimum mass of solid " + AGNO3 + " that must be added to the sample for precipitation of silver thiophenolate to occur. " + mk(2))),
    ("(c)(iii)", p("After sufficient aqueous silver nitrate has been added, the concentration of aqueous silver nitrate remaining in the treated wastewater is "
                   "1.0 × 10" + sup(M + "4") + " " + MDM + ".") +
                 p("Environmental regulations require that the concentration of thiophenolate ions remaining in the wastewater must not exceed 1.0 × 10" + sup(M + "6") +
                   " " + MDM + ".") +
                 p("By showing relevant calculations, deduce whether the treated wastewater meets this requirement. " + mk(2))),
    ("(c)(iv)", p("In the synthesis of 2-phenylthioethanol, chloride ions are produced. " + AGNO3 + " that is added to remove thiophenolate can also remove chloride "
                  "as silver chloride. Silver chloride is sparingly soluble in water, as shown in equilibrium 5.1.") +
                eq("5.1", "AgC" + L + "(s) ⇌ Ag" + sup("+") + "(aq) + C" + L + sup(M) + "(aq)") +
                p("With the aid of relevant equations, describe and explain how the solubility of silver chloride is affected by adding aqueous ammonia. " + mk(2))),
    ("(d)", p("Wastewater containing heavy metals such as silver are treated with aluminium oxide. Aluminium oxide is a powerful adsorbent that can capture heavy "
              "metals and be separated through filtration.") +
            p("By considering the acid-base behaviour of aluminium oxide, explain why the pH of the wastewater must be maintained at pH 7 before treatment with "
              "aluminium oxide. Write equations for all the reactions described. " + mk(3))),
])

# ---------------------------------------------------------------- Q6  (20)  Section B
Q[6] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Tooth enamel contains hydroxyapatite, " + HAP + ".") +
            p("The solubility equilibrium is represented as") +
            ceqn(HAP + "(s) ⇌ 5Ca" + sup("2+") + "(aq) + 3" + PO4 + "(aq) + OH" + sup(M) + "(aq)")),
    ("(a)(i)", p("State the oxidation state of phosphorus in " + HAP + ". " + mk(1))),
    ("(a)(ii)", p("Write the expression for " + KSP + " " + HAP + ". " + mk(1))),
    ("(a)(iii)", p("Explain how the solubility of " + HAP + " is affected by acids from food. " + mk(2)),
     p("When fluoride containing dental products are applied to the teeth, fluoride ions replace hydroxide ions in " + HAP + " to form fluorapatite, " + FAP +
       ". Fluorapatite is more acid resistant, which decreases tooth decay.") +
     p("The ionic radius of OH" + sup(M) + " in hydroxyapatite is 0.137 nm.")),
    ("(a)(iv)", p("Using the " + DBK + ", suggest why other Group 17 halides, such as " + CL + sup(M) + ", are unable to provide similar acid-resistance as F" + sup(M) + ". " + mk(1))),
    ("(a)(v)", p("State how the reactivity of the halogens as oxidising agents varies down the group, and relate this variation to relevant " + EA + " values. " + mk(2))),
    ("(b)", p("Titanium is widely used in dental implants. To improve antimicrobial properties, a titanium implant is electroplated with silver using aqueous silver nitrate. "
              "The titanium implant and a silver electrode are connected to a power supply.")),
    ("(b)(i)", p("Complete Table 6.1 to show which is the cathode and anode, with the relevant half equations, during the electroplating of titanium implant. " + mk(2)) +
               cap("Table 6.1") +
               table(tr(th(""), th("cathode or anode"), th("half-equation(s)")),
                     tr(td("titanium implant"), td(""), td("")),
                     tr(td("silver electrode"), td(""), td("")))),
    ("(b)(ii)", p("A titanium dental implant is coated with 5 mg of silver. Calculate the time taken to form this coating when a current of 0.02 A is used. " + mk(2)) +
                p("[1000 mg = 1 g]")),
    ("(c)", p("Protein collagen is widely used in dental implant procedures. The structure of a portion of the collagen is shown below.") + FIG),
    ("(c)(i)", p("How many " + b("different") + " amino acids are present in this portion of collagen? " + mk(1))),
    ("(c)(ii)", p("One of these amino acid residues is present more than once in this portion of collagen.") +
                p("Draw a displayed formula for this amino acid. " + mk(1)),
     p("Two of the amino acid residues present in this portion of collagen contain more than 1 chiral carbon.")),
    ("(c)(iii)", p("Explain what is meant by chiral carbon. " + mk(1))),
    ("(c)(iv)", p("Draw the structural formulae of these two amino acids and indicate each chiral atom with an asterisk (*). " + mk(2))),
    ("(c)(v)", p("Poor dental hygiene creates a breeding ground for bacteria that feed on leftover food and produce mouth-acid.") +
               p("Suggest a reason why poor dental hygiene can cause collagen in dental implants to breakdown quickly. " + mk(1))),
    ("(d)", p("Tooth bleaching relies on redox reactions where small amounts of peroxide-based agents break down into highly reactive free radicals. These radicals target the "
              "pigmented organic molecules, chromophores, trapped within the enamel, converting them into decolourised molecules. The process of tooth bleaching is shown below.") + FIG),
    ("(d)(i)", p("Draw four more curly arrows to show how the peroxide-based agent reacts with the chromophore to form the epoxide in step 1 of the bleaching process. " + mk(1))),
    ("(d)(ii)", p("The decolourised molecule in step 2 can be directly synthesised from the chromophore in one step.") +
                p("Suggest the reagents and conditions for this one step synthesis. " + mk(1))),
    ("(d)(iii)", p("Suggest the disadvantage of using the reaction in " + b("(d)(ii)") + " compared to the peroxide-based agent in forming the decolourised molecule from chromophore. " + mk(1))),
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
    h = h.replace(FIG, " ").replace("<br>", " ")
    h = re.sub(r"</(p|li|tr|div)>", " ", h)
    h = re.sub(r"</(td|th)>", " | ", h)
    h = re.sub(r"<span[^>]*>\s*</span>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", h).strip()

# Names printed in a snipped figure that content_text should still carry (search only).
EXTRA_TEXT = {(1, "(a)"): "log(ionisation energy) electrons removed",
              (1, "(b)"): "chloroformyl fluoride C O F Cl",
              (2, "(b)(iii)"): "NO2 step 1 reduction phenylhydroxylamine step 2 4-aminophenol step 3 paracetamol HN OH NH2 O",
              (2, "(d)"): "phenylhydroxylamine N-methyl-4-aminophenol CH3OH H2O HN OH N H CH3",
              (2, "(d)(iv)"): "phenylhydroxylamine N-substituted-4-aminophenol ROH H2O HN OH N H R",
              (3, "(b)"): "phenylboronic acid B OH",
              (5, None): "thiophenol thiophenolate 2-phenylthioethanol base ClCH2CH2OH SH S OH",
              (5, "(b)"): "benzoyl chloride O Cl",
              (5, "(b)(ii)"): "PET PIB O",
              (6, "(c)"): "NH2 OH O NH",
              (6, "(d)"): "step 1 step 2 peroxide-based agent chromophore epoxide decolourised molecule R R1 R2 O H HO OH"}

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
