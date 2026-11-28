"""Hand transcription of TMJC 2026 H2 Prelim Paper 2 (9476/02, 6 structured Q, 75 marks) -> questions.json +
asset_plan.json. Typed from the school's Word file ("Suggested Solutions": the question paper with the mark scheme overlaid in
blue / red / green) and its Word-exported PDF. Same output contract as build_tjc26_p2.py, i.e. what
gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_tmjc26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school TMJC --year 2026 --paper 2 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_tjc26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only introduces sub-parts
    is dropped (1(b), 2(b)'s lead-in is kept because it has text);
  * [n] is a span.mk written at the end of the instruction sentence (the paper prints it at the right margin of the last
    answer line, so for a part with a table or a figure it sits under the figure);
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred bold p.c; Table 1.1, 2.1, 3.1, 6.1,
    6.2 and the blank Table 1.2 are typed; Table 5.1 is a figure (it carries structures);
  * answer lines and empty answer boxes are NOT reproduced; printed answer LABELS are (Q1(b)(ii) "Number of protons:",
    Q1(c)(i) "Cl 1s2", Q3(a) "Anode:", Q3(d)(i) "A:");
  * asset slot = part label without brackets ('a', 'biv'), 'intro' for the stem.

MARKS. The paper prints every part mark at the right margin: Q1 13, Q2 13, Q3 13, Q4 13, Q5 10, Q6 13 = 75 (the cover sheet
agrees), asserted per question below.

NOT a question figure: Q2(b)(v) Boltzmann diagram (axes, curve, shaded areas, Ea labels) is the school's answer drawn in black;
the paper prints only blank space and answer lines there. The two black paragraphs at the top of p19 ("During washing ... creases
are locked into the fabric.") ARE question text (plain body paragraphs in the docx, indent of part (c), directly before (c)(ii)); they are
typed as the tail of (c)(i). The first delivery left them out by mistake; TMJC_2026_H2_P2_patch_Q5_washing_COMMIT.sql puts them back.

School slips corrected (veto-able; listed in the chat note):
  Q2(a) "The concentration of I- and OH- were used" -> "The concentrations of I- and OH- were used";
  Q5(c)(i) "Fig 5.1" -> "Fig. 5.1"; Q6 "The solubility product of some carbonate minerals ... are shown" -> "The solubility products of some carbonate minerals ... are shown";
  hyphen / en dash minus signs -> U+2212 ("-70", "-1207" ...); "Br?nsted-Lowry" kept as printed with the o-umlaut.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "TMJC", "H2", "P2", 2026
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
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s, style=""): return ("<td%s>%s</td>" % (' style="%s"' % style if style else "", s))
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def ion(sym, ch): return sym + sup(ch)

L = '<i class="el">l</i>'                  # element l
CL = "C" + L
AL = "A" + L
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
STD = sup('<span class="pl-sym">⦵</span>')
DBK = i("Data Booklet")
EM = "&emsp;"
ARR = "→"
EQ = "⇌"
OH = "OH" + sup(M)
HP = "H" + sup("+")
CO2 = "CO" + sub(2)
H2O = "H" + sub(2) + "O"
CO3 = "CO" + sub(3) + sup("2" + M)
HCO3 = "HCO" + sub(3) + sup(M)
OCL = "OC" + L + sup(M)
CLM = CL + sup(M)
CACO3 = "CaCO" + sub(3)
OMEGA = "Ω"
def dG(s=""): return DEL + i("G") + STD + (s or "")
def dH(s=""): return DEL + i("H") + STD + (s or "")
def dS(s=""): return DEL + i("S") + STD + (s or "")
def kj(): return "kJ mol" + sup(M + "1")
def over(top, arrow):
    """label above a reaction arrow (inline styles: no CSS needed)"""
    return ('<span style="display:inline-block;vertical-align:middle;text-align:center;line-height:1.1;padding:0 .15em">'
            '<span style="display:block;font-size:.72em;line-height:1.15">%s</span>'
            '<span style="display:block;line-height:1">%s</span></span>' % (top, arrow))

# Q2(b)(iv): the first snip lost the "[OH-]" axis label; re-snipped under a new name (Supabase CDN caches a replaced name)
PATH_OVERRIDE = {(2, "biv"): "TMJC_H2_P2_Q2_biv_v2_2026.png"}
Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (13)
PCL5 = "PC" + L + sub(5)
ALCL3 = AL + CL + sub(3)
Q[1] = dict(marks=13, intro=[
    p("Period 3 chlorides, NaC" + L + " to " + PCL5 + ", have a large variation in their chemistry shown by the changing nature of their "
      "bonding and structures.")], parts=[
    ("(a)", p("Table 1.1 gives the melting points, in °C, of the chlorides of some elements in Period 3.") +
            cap("Table 1.1") +
            table(tr(td(""), td("NaC" + L), td("MgC" + L + sub(2)), td("SiC" + L + sub(4)), td(PCL5)),
                  tr(td("melting points / °C"), td("801"), td("715"), td(M + "70"), td("161")))),
    ("(a)(i)", p("Explain, in terms of structure and bonding, the differences in melting points between MgC" + L + sub(2) + ", SiC" + L + sub(4) +
                 ", and " + PCL5 + ". " + mk(3))),
    ("(a)(ii)", p("Suggest an explanation for the lower than expected melting point of MgC" + L + sub(2) + " compared to that of NaC" + L + ". " + mk(2))),
    ("(b)(i)", p("Different reactions occur when " + ALCL3 + " and " + PCL5 + " are added separately to an excess of water. Write all relevant "
                 "equations and state the expected pH of each resultant solution in Table 1.2. " + mk(3)) +
               cap("Table 1.2") +
               table(tr(th(""), th("equation(s)"), th("pH")),
                     tr(td(ALCL3, "height:5em"), td(""), td("")),
                     tr(td(PCL5, "height:5em"), td(""), td(""))),
     ""),
    ("(b)(ii)", p("In solutions of polar solvents, " + PCL5 + " undergoes self-ionisation") +
                ceqn(PCL5 + " " + EQ + " [PC" + L + sub(4) + "]" + sup("+") + " + " + CLM) +
                p("State the number of protons and electrons present in [PC" + L + sub(4) + "]" + sup("+") + ". " + mk(1)) +
                p("Number of protons:") + p("Number of electrons:")),
    ("(c)(i)", p("State the electronic configuration of a chlorine atom and its cation. " + mk(1)) +
               p(CL + " 1s" + sup(2)) + p(CL + sup("+") + " 1s" + sup(2))),
    ("(c)(ii)", p("Describe and explain the trend in anionic radii down Group 17. " + mk(2))),
    ("(d)", p("Draw a labelled diagram to show the significant force of attraction between a water molecule and a " + CLM + " ion. Include the "
              "name of the attraction in your diagram. " + mk(1))),
])

# ---------------------------------------------------------------- Q2  (13)
IM = "I" + sup(M)
Q[2] = dict(marks=13, intro=[
    p("Hypochlorite ions, " + OCL + ", are commonly used as disinfectants in water treatment due to their strong oxidising properties.")], parts=[
    ("(a)", p("The reaction between hypochlorite and iodide ions in a basic solution is studied to determine its kinetics.") +
            ceqn(IM + " + " + OCL + " " + over(OH, "⟶") + " OI" + sup(M) + " + " + CLM) +
            p("The concentration of " + OCL + " was monitored over time and the following graph (Run " + b("A") + ") was obtained in Fig. 2.1. "
              "The concentrations of " + IM + " and " + OH + " were used in large excess at 1.0 " + MDM + ".") + FIG + cap("Fig. 2.1")),
    ("(a)(i)", p("Define the term " + i("half-life") + ". " + mk(1))),
    ("(a)(ii)", p("Using Fig. 2.1, determine the order of reaction with respect to " + OCL + ". " + mk(2))),
    ("(a)(iii)", p("The experiment was repeated using 8.0 × 10" + sup(M + "4") + " " + MDM + " of " + OCL + ", while the concentrations of " + IM +
                   " and " + OH + " were kept at 1.0 " + MDM + ".") +
                 p("On the axes in Fig. 2.1, draw the concentration-time graph of " + OCL + " for this new experiment and label it ‘Run B’. "
                   "On your graph, clearly label and state the half-life of " + OCL + "(aq) in Run B. " + mk(1))),
    ("(b)", p("A series of experiments was carried out to investigate the order of reaction with respect to " + IM + " and " + OH + ". The results "
              "obtained are shown in Table 2.1 below.") +
            cap("Table 2.1") +
            table(tr(th("experiment"), th("[" + IM + "]<br>/ " + MDM), th("[" + OH + "]<br>/ " + MDM), th("[" + OCL + "]<br>/ " + MDM),
                     th("initial rate<br>/ mol dm" + sup(M + "3") + " s" + sup(M + "1"))),
                  tr(td("1"), td("2.00 × 10" + sup(M + "3")), td("1.00"), td("4.00 × 10" + sup(M + "3")), td("4.84 × 10" + sup(M + "4"))),
                  tr(td("2"), td("5.00 × 10" + sup(M + "3")), td("1.00"), td("2.00 × 10" + sup(M + "3")), td("6.05 × 10" + sup(M + "4"))),
                  tr(td("3"), td("8.00 × 10" + sup(M + "3")), td("2.00"), td("1.00 × 10" + sup(M + "3")), td("2.42 × 10" + sup(M + "4"))))),
    ("(b)(i)", p("Using the information in Table 2.1 and " + b("(a)(ii)") + ", determine the order of reaction with respect to " + IM + " and " + OH + ". " + mk(2))),
    ("(b)(ii)", p("Hence, write the rate equation for the reaction. " + mk(1))),
    ("(b)(iii)", p("Suggest the role of " + OH + ". " + mk(1))),
    ("(b)(iv)", p("The rate of reaction was measured using different initial [" + OH + "], while keeping [" + OCL + "] and [" + IM + "] constant. "
                  "On Fig. 2.2, sketch the graph of rate against initial [" + OH + "]. " + mk(1)) + FIG + cap("Fig. 2.2")),
    ("(b)(v)", p("Transition metal ions can catalyse reactions involving hypochlorite ions, " + OCL + ".") +
               p("Using a labelled Boltzmann distribution diagram, explain how the addition of a transition metal ion catalyst increases the rate "
                 "of reaction. " + mk(2))),
    ("(c)", p("Chloride ion, " + CLM + ", can behave as a Brønsted-Lowry base, Lewis base or a reducing agent in different reactions. For each of the "
              "following reactions, identify the role of " + CLM + " and explain your answer.")),
    ("(c)(i)", p(CLM + " + 3O" + sub(3) + " " + ARR + " " + "C" + L + "O" + sub(3) + sup(M) + " + 3O" + sub(2) + " " + mk(1))),
    ("(c)(ii)", p("[Cu(" + H2O + ")" + sub(6) + "]" + sup("2+") + " + 4" + CLM + " " + ARR + " [CuC" + L + sub(4) + "]" + sup("2" + M) + " + 6" + H2O + " " + mk(1))),
])

# ---------------------------------------------------------------- Q3  (13)
LIP = "Li" + sup("+")
NI4, CO4, NI2, CO3P = "Ni" + sup("4+"), "Co" + sup("4+"), "Ni" + sup("2+"), "Co" + sup("3+")
Q[3] = dict(marks=13, intro=[
    p("Lithium nickel manganese cobalt oxide (NMC) batteries are widely used in electric vehicles due to their high energy density and "
      "thermal stability.") + FIG + cap("Fig. 3.1"),
    p("During discharge, lithium atoms in the graphite anode are oxidised to " + LIP + " ions, while transition metal ions in the NMC cathode "
      "are reduced. In a simplified model, " + NI4 + " and " + CO4 + " ions undergo a single combined cathode reaction, reducing simultaneously "
      "in a 1 : 1 mole ratio. " + NI4 + " ions are reduced to " + NI2 + " ions, and " + CO4 + " ions are reduced to " + CO3P +
      " ions, while manganese ions remain unchanged.")], parts=[
    ("(a)", p("Write the half-equations for the reactions at the anode and cathode during discharge. Hence, write the overall balanced cell "
              "equation. " + mk(2)) + p("Anode:") + p("Cathode:") + p("Overall:")),
    ("(b)", p("Table 3.1 lists the standard electrode potentials, " + i("E") + STD + ", of the redox couples at the electrodes in the NMC battery.") +
            cap("Table 3.1") +
            table(tr(th("redox couple"), th(i("E") + STD + " / V")),
                  tr(td(LIP + " / Li"), td(M + "3.04")),
                  tr(td(NI4 + " / " + NI2), td("+1.23")),
                  tr(td(CO4 + " / " + CO3P), td("+1.48"))) +
            p("The overall cathode reaction consists of two reduction processes of " + NI4 + " and " + CO4 + ", each involving a different number of "
              "electrons transferred.") +
            p("The standard Gibbs free energy change, " + dG() + ", for a reaction is related to the standard electrode potential by:") +
            ceqn(dG() + " = " + M + i("nFE") + STD) +
            p("The standard Gibbs free energy change of the overall reaction is equal to the sum of the standard Gibbs free energy changes of the "
              "individual steps.")),
    ("(b)(i)", p("Using the data in Table 3.1, calculate values of " + dG() + " for the reductions of " + NI4 + " and " + CO4 + ".") +
               p("Hence, determine " + dG() + " for the overall cathode reaction. " + mk(2))),
    ("(b)(ii)", p("Using your answer to " + b("(b)(i)") + ", calculate the standard electrode potential, " + i("E") + STD + sub("cathode") +
                  ", for the overall cathode reaction.") +
                p("Hence, calculate the standard cell potential, " + i("E") + STD + sub("cell") + ", for the battery. " + mk(2)) +
                p("If you were unable to obtain a value for " + dG() + " for the cathode reaction in " + b("(b)(i)") + ", you may use the value " +
                  M + "162 " + kj() + ".")),
    ("(c)", p("During discharge, the concentration of " + LIP + " in the electrolyte increases. Explain how this affects the cell potential, " +
              i("E") + sub("cell") + ". " + mk(2))),
    ("(d)", p("At the end of its service life, an NMC battery still contains valuable transition metals such as manganese and nickel. To recover "
              "these metals, the NMC cathode is crushed and treated with dilute sulfuric acid. After filtration, the aqueous solution contains "
              "Ni" + sup("2+") + "(aq) and Mn" + sup("2+") + "(aq).") +
            p("To separate these ions, the following procedure is carried out:") + FIG),
    ("(d)(i)", p("Using relevant data from the " + DBK + ", state the identities of precipitate " + b("A") + " and residue " + b("B") + ". " + mk(2)) +
               p(b("A:")) + p(b("B:"))),
    ("(d)(ii)", p("Draw the structure of the octahedral complex ion present in the blue filtrate " + b("C") + ", in which NH" + sub(3) +
                  " is the only ligand. " + mk(1))),
    ("(e)", p("During recycling of NMC batteries, copper impurities may also be present.") +
            p("An aqueous solution of copper(II) sulfate contains the complex ion, [Cu(" + H2O + ")" + sub(6) + "]" + sup("2+") + ", which is blue in "
              "colour. When concentrated HC" + L + " is added, the solution eventually turns yellow.") +
            p("Explain, with the aid of an equation, the colour change observed. " + mk(2))),
])

# ---------------------------------------------------------------- Q4  (13)
Q[4] = dict(marks=13, intro=[
    p("Noradrenaline and dopamine are body hormones crucial for brain function and stress response. They act in tandem to regulate mood and "
      "cognitive function, helping to maintain optimal mental states.") + FIG], parts=[
    ("(a)", p("Noradrenaline can be heated with concentrated H" + sub(3) + "PO" + sub(4) + " to give a mixture of two isomers. Draw the structures of "
              "the isomers and state the type of isomerism they show. " + mk(2)),
     p("These hormones are widely used for clinical treatment and can be synthesised by drug companies from simpler compounds such as "
       "3,4-dihydroxybenzaldehyde.") + FIG),
    ("(b)", p("The O" + sub(1) + " atom undergoes the same type of hybridisation as the carbonyl carbon atom. With reference to the hybridisation of the "
              "carbon and oxygen atoms in 3,4-dihydroxybenzaldehyde, describe the orbital overlap in the C=O covalent bond as well as the shape "
              "around the carbonyl carbon. " + mk(2))),
    ("(c)", p("Noradrenaline can be synthesised from 3,4-dihydroxybenzaldehyde as shown.") + FIG),
    ("(c)(i)", p("State the reagents and conditions used in step I. " + mk(1))),
    ("(c)(ii)", p("Name and outline the mechanism of the reaction in step I. In your answer you should show all relevant charges and lone pairs, "
                  "and indicate the movement of electrons with curly arrows. " + mk(2))),
    ("(c)(iii)", p("Explain why a racemic mixture is formed by the mechanism above. " + mk(2))),
    ("(d)", p("Dopamine can also be synthesised from 3,4-dihydroxybenzaldehyde using the following reaction scheme.") +
            p("Suggest the reagents and conditions you would use in this four-step synthesis, identifying the intermediate compounds " + b("P") +
              ", " + b("Q") + " and " + b("R") + ". " + mk(4)) + FIG),
])

# ---------------------------------------------------------------- Q5  (10)
Q[5] = dict(marks=10, intro=[
    p("6-aminohexanoic acid is an amino acid used in the synthesis of nylon-6.") + FIG], parts=[
    ("(a)", p("The two p" + K + sub("a") + " values associated with this amino acid are 4.43 and 10.75.")),
    ("(a)(i)", p("Draw the structure of the predominant species present when 6-aminohexanoic acid is placed in an aqueous solution at pH 3.0. " + mk(1))),
    ("(a)(ii)", p("Explain why 6-aminohexanoic acid is more basic than the amino acid, leucine. " + mk(1)) + FIG,
     p("Nylon-6 (a polyamide) and Terylene (a polyester) are common synthetic fabrics.")),
    ("(b)", p("Complete Table 5.1. " + mk(3)) + cap("Table 5.1") + FIG),
    ("(c)", p("Polyamide fabrics are prone to creasing whereas polyesters tend to be wrinkle-free.")),
    ("(c)(i)", p("Draw and label the hydrogen bonding between two chains of the polyamide, nylon-6. Include any relevant lone pairs and dipoles in "
                 "Fig. 5.1. " + mk(1)) + FIG + cap("Fig. 5.1"),
     p("During washing, water forms extensive hydrogen bonds with polyamide chains, disrupting the hydrogen bonds between the chains and "
       "allowing the polymer chains to slide past one another.") +
     p("As water evaporates, hydrogen bonds re-form between the shifted chains. As the chains are no longer neatly aligned, creases are "
       "locked into the fabric.")),
    ("(c)(ii)", p("State the type of interaction between the polyester chains. Hence, suggest why polyester is wrinkle-free. " + mk(2))),
    ("(c)(iii)", p("Suggest an advantage of using synthetic polymers as fabric materials compared to natural fibres, such as wool and cotton. " + mk(1))),
    ("(d)", p("Waste materials can be incinerated or disposed of in landfill sites.") +
            p("Suggest one environmental problem that may arise from disposal of polyester-containing waste in landfill sites. " + mk(1))),
])

# ---------------------------------------------------------------- Q6  (13)
KSP = K + sub("sp")
def sym2(t): return "[" + t + "]"
M2 = "M" + sup("2+")
Q[6] = dict(marks=13, intro=[
    p("Many marine organisms form shells or skeletons composed mainly of calcium carbonate, " + CACO3 + ", occurring as different crystalline "
      "forms such as calcite and aragonite."),
    p("Standard enthalpies of formation at 298 K are given in Table 6.1."),
    cap("Table 6.1") +
    table(tr(td(""), td(DEL + i("H") + sub("f") + STD + " / " + kj())),
          tr(td(CACO3 + " (s, calcite)"), td(M + "1207")),
          tr(td("Ca" + sup("2+") + " (aq)"), td(M + "543")),
          tr(td(CO3 + " (aq)"), td(M + "675"))),
    p("The tendency of a carbonate mineral to precipitate or dissolve in seawater is described by the saturation state, " + OMEGA + ":"),
    ceqn(OMEGA + " = " + frac("[" + M2 + "][" + CO3 + "]", KSP)),
    p("where " + OMEGA + " > 1 indicates conditions favouring precipitation and " + OMEGA + " < 1 indicates conditions favouring dissolving "
      "carbonate mineral."),
    p("In warm tropical oceans, " + OMEGA + " (calcite) is typically much greater than 1. However, in some regions, seawater is only weakly "
      "supersaturated with respect to " + CACO3 + ". Marine organisms can precipitate " + CACO3 + " under these conditions by modifying the "
      "local chemical environment at the site of calcification."),
    p("Dissolving of atmospheric " + CO2 + " in seawater alters the carbonate equilibria and contributes to ocean acidification."),
    p("The following equilibria are relevant:"),
    ceqn(CO2 + " (g) " + EQ + " " + CO2 + " (aq)"),
    ceqn(CO2 + " (aq) + " + H2O + " (" + L + ") " + EQ + " H" + sub(2) + "CO" + sub(3) + " (aq)"),
    ceqn("H" + sub(2) + "CO" + sub(3) + " (aq) " + EQ + " " + HP + " (aq) + " + HCO3 + " (aq)" + EM + EM + K + sub("a1") + " = 4.3 × 10" + sup(M + "7")),
    ceqn(HCO3 + " (aq) " + EQ + " " + HP + " (aq) + " + CO3 + " (aq)" + EM + EM + K + sub("a2") + " = 4.7 × 10" + sup(M + "11")),
    ceqn(CACO3 + " (s) " + EQ + " Ca" + sup("2+") + " (aq) + " + CO3 + " (aq)"),
    p("Typical surface seawater at 25 °C and pH ≈ 8.1 has the following composition:"),
    ceqn("[Ca" + sup("2+") + "] = 1.0 × 10" + sup(M + "2") + " " + MDM),
    ceqn("[Mg" + sup("2+") + "] = 5.0 × 10" + sup(M + "2") + " " + MDM),
    ceqn("[" + CO3 + "] = 2.0 × 10" + sup(M + "4") + " " + MDM),
    p("The solubility products of some carbonate minerals at 25 °C are shown in Table 6.2."),
    cap("Table 6.2") +
    table(tr(th("mineral"), th("value of solubility product")),
          tr(td("calcite (" + CACO3 + ")"), td("3.3 × 10" + sup(M + "9"))),
          tr(td("aragonite (" + CACO3 + ")"), td("4.6 × 10" + sup(M + "9"))),
          tr(td("magnesite (MgCO" + sub(3) + ")"), td("5.0 × 10" + sup(M + "9"))))], parts=[
    ("(a)(i)", p("Using Table 6.1, calculate the standard enthalpy change of solution, " + dH("(sol)") + ", for " + CACO3 + "(s). " + mk(1))),
    ("(a)(ii)", p("The standard entropy change, " + dS("(sol)") + ", for dissolving " + CACO3 + "(s) is determined to be " + M + "199 J K" + sup(M + "1") +
                  " mol" + sup(M + "1") + ". Calculate " + dG("(sol)") + " at 298 K and hence determine whether dissolving of " + CACO3 +
                  "(s) is spontaneous under standard conditions. " + mk(2))),
    ("(a)(iii)", p("Seawater temperature varies significantly between warm tropical oceans and colder high-latitude regions.") +
                 p("Using the values in " + b("(a)(i)") + " and in " + b("(a)(ii)") + ", explain how an increase in temperature affects the "
                   "thermodynamic feasibility of dissolving " + CACO3 + "(s).") +
                 p("State the assumption made. " + mk(2))),
    ("(b)(i)", p("Using data in the question and Table 6.2, calculate the saturation state, " + OMEGA + ", for calcite in surface seawater.") +
               p("Given that " + OMEGA + " for aragonite and magnesite is 435 and 2000 respectively, identify which of these three minerals is the "
                 "least thermodynamically favoured to precipitate under the stated conditions. " + mk(2))),
    ("(b)(ii)", p("In warm tropical oceans, " + OMEGA + " (calcite) is typically much higher than 1. Explain why this does not result in immediate "
                  "and widespread precipitation of calcite in warm tropical seawater. " + mk(1))),
    ("(c)", p("If an area of seawater receives additional Ca" + sup("2+") + " from river input, predict and explain the impact on the solubility of " +
              CACO3 + ". " + mk(1))),
    ("(d)", p("Seawater contains a higher concentration of Mg" + sup("2+") + " ions, about five times that of Ca" + sup("2+") + " ions.") +
            p("The formation of a crystalline solid begins with nucleation, in which hydrated ions lose part of their hydration shells before "
              "assembling into a stable crystal lattice. Hence, the strength of hydration influences the ease of nucleation.") + FIG +
            p("Although Mg" + sup("2+") + " ions are present at a much higher concentration than Ca" + sup("2+") + " ions, magnesite (MgCO" + sub(3) +
              ") does not readily precipitate from seawater.") +
            p("Suggest a reason, based on ionic properties and hydration, why magnesite does not precipitate from seawater. " + mk(1))),
    ("(e)", p("An increase in atmospheric " + CO2 + " increases the amount of " + CO2 + " dissolved in seawater, causing seawater pH to decrease.")),
    ("(e)(i)", p("The following equilibrium controls the relative concentrations of " + HCO3 + " and " + CO3 + " in seawater.") +
               ceqn(HCO3 + " (aq) " + EQ + " " + HP + " (aq) + " + CO3 + " (aq)") +
               p("Assuming that the concentration of " + HCO3 + " remains approximately constant, calculate the ratio of carbonate ion "
                 "concentrations, " + frac("[" + CO3 + "]" + sub("pH 7.9"), "[" + CO3 + "]" + sub("pH 8.1")) + " when seawater pH decreases from 8.1 to 7.9. " + mk(1))),
    ("(e)(ii)", p("Hence, using your calculated ratio in " + b("(e)(i)") + ", deduce the effect of increasing atmospheric " + CO2 + " on the saturation "
                  "state, " + OMEGA + ", of " + CACO3 + " and on marine organism calcification. " + mk(1))),
    ("(f)", p("Ambient seawater in some regions has a saturation state, " + OMEGA + ", close to 1, yet marine organisms are still able to precipitate " +
              CACO3 + " by modifying the local chemical environment. Using the expression for saturation state, " + OMEGA +
              ", suggest how this precipitation can occur. " + mk(1))),
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
EXTRA_TEXT = {(2, "(a)"): "Fig. 2.1 [OCl-(aq)] x 10-4 mol dm-3 relative time A",
              (2, "(b)(iv)"): "Fig. 2.2 rate [OH-]",
              (3, None): "Fig. 3.1 cathode separator electrolyte anode electron flow car LiMO2 layer structure where M = Ni, Mn and Co LixC6 graphite with Li atoms",
              (3, "(d)"): "mixture of Mn2+(aq) and Ni2+(aq) add NaOH(aq) dropwise mixture of precipitates A and B add excess NH3(aq) and filter blue filtrate C residue B",
              (4, None): "noradrenaline dopamine",
              (4, "(a)"): "3,4-dihydroxybenzaldehyde O1",
              (4, "(c)"): "3,4-dihydroxybenzaldehyde step I step II noradrenaline",
              (4, "(d)"): "3,4-dihydroxybenzaldehyde step 1 step 2 step 3 step 4 reagent and condition P (C7H8O3) Q R (C8H7NO2) dopamine",
              (5, None): "6-aminohexanoic acid H2N COOH",
              (5, "(a)(ii)"): "leucine COOH NH2",
              (5, "(b)"): "polymer structural formula of monomer(s) structure of repeat unit of polymer type of polymerisation Nylon-6 polyamide Terylene polyester "
                          "HOCH2CH2OH COOH N(CH2)5C",
              (5, "(c)(i)"): "nylon-6 N(CH2)5C n",
              (6, "(d)"): "hydrated ions partial removal of hydration shells nucleation forming a stable cluster of ions"}

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
                         "storage_path": PATH_OVERRIDE.get((n, slot), "%s_%s_%s_Q%d_%s_%d.png" % (SCHOOL, LEVEL, PAPER, n, slot, YEAR))})
            o += 1
    nph = html.count('class="fig"'); nas = sum(1 for a in plan if a["question"] == n)
    assert nph == nas, (n, nph, nas)
assert sum(r["marks"] for r in rows) == 75
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))
