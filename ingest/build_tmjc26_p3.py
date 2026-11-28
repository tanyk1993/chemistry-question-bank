"""Hand transcription of TMJC 2026 H2 Prelim Paper 3 (9476/03, 22 Sept 2026; Section A Q1-Q3 = 55 marks, Section B answer ONE of
Q4/Q5 = 20 marks, 75 as sat; 95 as ingested because both Section B questions are loaded) -> questions.json + asset_plan.json.
Typed from the school's Word file (sub/superscripts) checked against the Word-exported PDF. Same output contract as
build_sajc26_p3.py, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_tmjc26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school TMJC --year 2026 --paper 3 --level H2 --skip-assets=false

Conventions as build_sajc26_p3.py (claude/style-guide.md): block <div class="fig"> placeholders with captions typed; tables
(Table 1.1, 4.1, 4.2) typed as table.qt; answer lines NOT reproduced (fill-in lines "Step 4:", "Cathode:" are kept); marks are
span.mk placed where the paper prints [n]. Text the school prints between two sub-parts is a tail after the part before it.
Asset slots are set explicitly in SLOTS (the user's snip filenames, TMJC_H2_P3_Q{n}_{slot}_2026.png), in DOM order.
Typography: minus U+2212, element l italic, standard-state sign, "230 C" -> "230 °C", radical dot U+2022.
School slips corrected (veto-able): Q2(b)(ii) missing full stop after "where necessary"; Q5(b) "is the dependent on" -> "is dependent on".
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "TMJC", "H2", "P3", 2026
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
DBK = i("Data Booklet")
def dH(n): return DEL + i("H") + sub(n)
DHC = DEL + i("H") + sup('<span class="pl-sym">⦵</span>') + sub("c")
def dHc(x): return DEL + i("H") + STD + sub("c") + "(" + x + ")"
H2 = "H" + sub(2); CO2 = "CO" + sub(2); CH3OH = "CH" + sub(3) + "OH"; H2O = "H" + sub(2) + "O"
ICL = "IC" + L
RAD = "•"
def r_(t): return t

Q = {}

# ---------------------------------------------------------------- Q1 (19)
Q[1] = dict(marks=19, intro=[
    p("Methanol, " + CH3OH + ", is produced industrially by reacting synthesis gas (a mixture of carbon dioxide, " + CO2 + ", carbon monoxide, CO, and hydrogen, " + H2 +
      ", gases) over a copper catalyst at high temperatures and pressures to produce a reasonable yield of methanol."),
    p("Reaction 1" + EM + CO2 + "(g) + 3" + H2 + "(g) → " + CH3OH + "(g) + " + H2O + "(g)" + EM + dH(1)),
    p("Reaction 2" + EM + "CO(g) + 2" + H2 + "(g) → " + CH3OH + "(g)" + EM + EM + EM + dH(2))], parts=[
    ("(a)(i)", p("Define the term " + i("bond energy") + " of a covalent bond. " + mk(1))),
    ("(a)(ii)", p("Using relevant data from the " + DBK + ", determine a value for the enthalpy change of reaction 1, " + dH(1) + ". " + mk(2))),
    ("(a)(iii)", p("Briefly explain how copper functions as a heterogeneous catalyst in this process. " + mk(1))),
    ("(b)", p("Table 1.1 shows standard enthalpy changes related to CO, " + H2 + ", and " + CH3OH + ".") + cap("Table 1.1") +
            table(tr(th("reaction"), th("standard enthalpy change"), th("value / kJ mol" + sup(M + "1"))),
                  tr(td("combustion of CO(g)"), td(dHc("CO")), td(M + "283")),
                  tr(td("combustion of " + H2 + "(g)"), td(dHc(H2)), td(M + "286")),
                  tr(td("combustion of " + CH3OH + "(l)"), td(dHc(CH3OH)), td(M + "726")),
                  tr(td("vapourisation of " + CH3OH + "(l)<br>" + CH3OH + "(l) → " + CH3OH + "(g)"), td(DEL + i("H") + STD + sub("vap") + "(" + CH3OH + ")"), td("+37")))),
    ("(b)(i)", p("Using the data in Table 1.1, construct a labelled energy cycle to determine a value for the enthalpy change of reaction 2, " + dH(2) + ". " + mk(3))),
    ("(b)(ii)", p("The enthalpy change for reaction 2, " + dH(2) + ", was separately determined using bond energies from the " + DBK + ", and was found to be " + M + "101 kJ mol" + sup(M + "1") + ".") +
                p("Suggest a reason why the " + dH(2) + " value determined using bond energies differs from that calculated in <b>(b)(i)</b>. " + mk(1))),
    ("(c)", p("Fig 1.1 shows an experimental set-up of a calorimetry experiment carried out to evaluate the energy efficiency of the combustion of methanol.") + FIG + cap("Fig. 1.1") +
            ul("1.5 g of liquid methanol is burned", "200.0 g of water in copper can", "Initial temperature of water = 25.0 °C", "Final temperature of water = 54.5 °C",
               "Heat capacity of copper can = 57.8 J K" + sup(M + "1"), "Specific heat capacity of water = 4.18 J g" + sup(M + "1") + " K" + sup(M + "1")) +
            p("In your calculations, assume that the copper can and water are at the same temperature.")),
    ("(c)(i)", p("Determine the experimental standard enthalpy change of combustion of methanol, " + dHc(CH3OH) + ", in kJ mol" + sup(M + "1") + ". " + mk(3))),
    ("(c)(ii)", p("The theoretical value of " + dHc(CH3OH) + " given in <b>(b)</b> is " + M + "726 kJ mol" + sup(M + "1") + ". Suggest a reason for the difference between the value calculated in <b>(c)(i)</b> and that of the theoretical value. " + mk(1))),
    ("(d)", p("In the manufacture of methanol in a pilot reactor, 4.00 mol of CO(g) and 7.00 mol of " + H2 + "(g) are introduced into a 5.00 dm" + sup(3) + " vessel at 230 °C.") +
            ceqn("CO(g) + 2" + H2 + "(g) ⇌ " + CH3OH + "(g)") +
            p("When equilibrium is established, 1.50 mol of " + CH3OH + "(g) is formed.")),
    ("(d)(i)", p("State the equilibrium constant, " + K + sub("c") + ", expression for the reaction, including its units. " + mk(1))),
    ("(d)(ii)", p("Calculate the value of " + K + sub("c") + ". " + mk(2))),
    ("(d)(iii)", p("Predict and explain the effect on the equilibrium yield of methanol if the volume of the reactor vessel is decreased while keeping the reaction at constant temperature. " + mk(1))),
    ("(d)(iv)", p("Residual gases in the synthesis gas mixture may react in a manner that produces water instead of methanol according to the reversible reaction:") +
                p("Reaction 3" + EM + CO2 + "(g) + " + H2 + "(g) ⇌ CO(g) + " + H2O + "(g)") +
                p("The forward reaction proceeds to a larger extent at higher temperature.") +
                p("Using Le Chatelier’s Principle, deduce whether the forward direction of Reaction 3 is exothermic or endothermic. " + mk(1))),
    ("(e)", p("Methanol is commonly added to ethanol meant for industrial use to denature it. This prevents the denatured ethanol from being consumed as liquor.") +
            p("Describe a simple chemical test to distinguish between methanol and ethanol. " + mk(2))),
])

# ---------------------------------------------------------------- Q2 (18)
Q[2] = dict(marks=18, intro=[
    p("Etomidate has been classified as a controlled drug in Singapore following reports of its misuse in vape pods known as “Kpods”. Despite this, it remains a highly effective and valuable anaesthetic widely used in medical practice for short procedures and rapid induction."),
    FIG], parts=[
    ("(a)", p("Etomidate is administered for general sedation.") + p("The recommended dosage is 0.30 mg per kg of body mass.")),
    ("(a)(i)", p("A typical etomidate solution has a concentration of 8.2 × 10" + sup(M + "3") + " " + MDM + ". Calculate the volume, in dm" + sup(3) +
                 ", of this solution required to sedate an adult of body mass 70 kg. (" + i("M") + sub("r") + " of etomidate = 244.0) " + mk(2))),
    ("(a)(ii)", p("Calculate the initial etomidate plasma concentration, " + i("c") + sub("o") + ", in mg dm" + sup(M + "3") +
                  ", for the 70 kg adult, based on the recommended dosage. The total volume of blood plasma in the body is assumed to be 2.5 dm" + sup(3) + ". " + mk(1)),
     p("After administration, the blood plasma concentration of etomidate decreases in two phases:") +
     ul("distribution phase half-life = 3.0 min (0 – 12 min)", "elimination phase half-life = 3.0 h (after 12 min)") +
     p("Immediately after injection, the plasma concentration is denoted as " + i("c") + sub("o") + ".") +
     p("The patient regains consciousness when the plasma concentration falls below 1.0 mg dm" + sup(M + "3") + ".")),
    ("(a)(iii)", p("Assuming that the distribution phase follows first-order kinetics, use the distribution phase half-life and your answer in <b>(a)(ii)</b> to calculate the time taken for the patient to regain consciousness. " + mk(1))),
    ("(b)", p("During the elimination phase in the human body, etomidate undergoes enzymatic hydrolysis in the liver to form an inactive carboxylic acid and an alcohol.") + FIG),
    ("(b)(i)", p("Identify the functional group in etomidate that undergoes hydrolysis. " + mk(1)),
     p("In the laboratory, the hydrolysis of etomidate can be carried out under alkaline conditions.") +
     p("The reaction proceeds via a nucleophilic acyl substitution mechanism involving the following stages:") +
     p("<b>I</b>: An OH" + sup(M) + " ion acts as a nucleophile and attacks the C=O carbon, forming a tetrahedral intermediate. This is the slow step.") +
     p("<b>II</b>: The C=O is re-formed and the alkoxide ion is eliminated.") +
     p("<b>III</b>: The alkoxide ion abstracts a proton from the carboxylic acid formed, producing an alcohol and a carboxylate ion.")),
    ("(b)(ii)", p("Complete the three-stage mechanism below by drawing the tetrahedral intermediate and showing the movement of electron pairs using curly arrows. Include lone pairs and dipoles where necessary. " + mk(3)) + FIG),
    ("(b)(iii)", p("Suggest the overall order of this reaction. " + mk(1))),
    ("(c)", p("Suggest why only the (+) enantiomer of etomidate is used as an anaesthetic drug. " + mk(1)),
     p("1-phenylethanamine is used as a starting material in the synthesis of etomidate.") + FIG),
    ("(d)", p("In etomidate, the five-membered ring containing two nitrogen atoms is aromatic. Both nitrogen atoms undergo the same type of hybridisation as the carbon atoms in the benzene ring.")),
    ("(d)(i)", p("Suggest the hybridisation of the nitrogen atoms in the five-membered ring of etomidate. " + mk(1))),
    ("(d)(ii)", p("By considering the hybridisation of the N" + sub(1) + " atom in etomidate and in 1-phenylethanamine, explain why etomidate is less basic. " + mk(1))),
    ("(e)", p("Compound <b>B</b> is an isomer of 1-phenylethanamine with molecular formula C" + sub(8) + "H" + sub(11) + "N.") +
            p("<b>B</b> has a higher p" + K + sub("b") + " value than 1-phenylethanamine.") +
            p("<b>B</b> decolourises aqueous Br" + sub(2) + " to form compound <b>C</b>, with molecular formula C" + sub(8) + "H" + sub(8) + "NBr" + sub(3) + ".") +
            p("When <b>B</b> is heated with acidified KMnO" + sub(4) + ", a cation <b>D</b> is formed with molecular formula C" + sub(8) + "H" + sub(8) + "O" + sub(4) + "N" + sup("+") + ".") +
            p("<b>B</b> can be synthesised from compound <b>A</b> by heating with Sn in concentrated HCl, followed by addition of aqueous NaOH.") +
            p("Deduce the structures of <b>A</b>, <b>B</b>, <b>C</b> and <b>D</b>. Show your reasoning clearly. " + mk(6))),
])

# ---------------------------------------------------------------- Q3 (18)
H3PO4 = "H" + sub(3) + "PO" + sub(4)
Q[3] = dict(marks=18, intro=[
    p("Titrations are a well-established laboratory method to analyse quantitative content of samples. One such application is in the use of acid-base titrations.")], parts=[
    ("(a)", p(H3PO4 + " dissociates in two stages as an acid, as shown in the equation below.") +
            ceqn(H3PO4 + " ⇌ H" + sub(2) + "PO" + sub(4) + sup(M) + " + H" + sup("+") + EM + EM + K + sub("a1") + " = 6.9 × 10" + sup(M + "3")) +
            ceqn("H" + sub(2) + "PO" + sub(4) + sup(M) + " ⇌ HPO" + sub(4) + sup("2" + M) + " + H" + sup("+") + EM + EM + K + sub("a2") + " = 6.2 × 10" + sup(M + "8")) +
            p("A 25.0 cm" + sup(3) + " solution of " + H3PO4 + " is titrated using 0.100 " + MDM + " NaOH. Using phenolphthalein as the indicator, the titration is shown below.") + FIG),
    ("(a)(i)", p("Given that the first equivalence point was detected at 22.40 cm" + sup(3) + ", calculate the initial concentration of the " + H3PO4 + " solution before NaOH was added, and hence find the initial pH. " + mk(2))),
    ("(a)(ii)", p("Calculate the pH when 11.20 cm" + sup(3) + " of NaOH was added. " + mk(1))),
    ("(a)(iii)", p("Calculate the pH when 50.00 cm" + sup(3) + " of NaOH was added. " + mk(2))),
    ("(a)(iv)", p("Write the expression for " + K + sub("a2") + ". " + mk(1))),
    ("(a)(v)", p("Write a chemical equation to explain why the pH at the second equivalence point is higher than 7. " + mk(1))),
    ("(a)(vi)", p("When 30.00 cm" + sup(3) + " of NaOH solution was added, the mixture is considered a buffer solution. With the aid of a chemical equation, explain how this solution functions as a buffer when more NaOH is added. " + mk(2)),
     p("Redox titrations often make use of various transition elements and their compounds due to their distinct colour changes.")),
    ("(b)", p("Define what is a transition element. " + mk(1))),
    ("(c)(i)", p("Write the electronic configuration of the Cr" + sup("3+") + " ion. " + mk(1))),
    ("(c)(ii)", p("Explain why aqueous Cr" + sup("3+") + " ions are green in colour. " + mk(3))),
    ("(d)(i)", p("Manganese is also a transition element, just like chromium. The electronic configuration of aqueous Mn" + sup("2+") + " is shown below.") + FIG +
               p("By using the same template, draw the electronic configurations of aqueous Cr" + sup("3+") + " and Cu" + sup("+") + ". " + mk(2)) + FIG),
    ("(d)(ii)", p("Mn" + sup("2+") + " is known to respond to magnetic fields whereas Cu" + sup("+") + " does not. Using the electronic configurations, suggest why they behave differently. " + mk(1))),
    ("(d)(iii)", p("Suggest why aqueous Mn" + sup("2+") + " appears colourless, unlike Cr" + sup("3+") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q4 (20)  Section B
def tbl2(h1, h2, rows):
    return table(tr(th(h1), th(h2)), *[tr(td(a), td(bb)) for a, bb in rows])
Q[4] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Table 4.1 lists the boiling points of some compounds.") + cap("Table 4.1") +
            tbl2("compound", "boiling point / °C", [("NH" + sub(2) + "OH", "58"), ("CH" + sub(3) + "NH" + sub(2), M + "6"), ("CH" + sub(3) + "SH", "6")]) +
            p("Suggest reasons for the differences in boiling points between:") +
            ul("NH" + sub(2) + "OH and CH" + sub(3) + "NH" + sub(2), "CH" + sub(3) + "SH and CH" + sub(3) + "NH" + sub(2)) + p(mk(3))),
    ("(b)", p("The melting points of the oxides of Period 3 elements vary significantly, as shown in Table 4.2") + cap("Table 4.2") +
            tbl2("compound", "melting point / °C", [("MgO", "2850"), ("Al" + sub(2) + "O" + sub(3), "2070"), ("P" + sub(4) + "O" + sub(10), "340")]) +
            p("State and explain the differences in melting points of MgO, Al" + sub(2) + "O" + sub(3) + " and P" + sub(4) + "O" + sub(10) + " in terms of their structure and bonding. " + mk(3))),
    ("(c)", p("Ibuprofen is an important anti-inflammatory drug. It can be synthesised from isobutylbenzene in six steps as shown in Fig. 4.1.") + FIG + cap("Fig. 4.1")),
    ("(c)(i)", p("Suggest the reagent and conditions for step 1. " + mk(1))),
    ("(c)(ii)", p("Suggest the types of reaction in steps 4 and 5.") + p("Step 4:") + p("Step 5: " + mk(2))),
    ("(c)(iii)", p("Ethyl 2-chloroethanoate, which is used in step 2, can be synthesised from ethene via compound <b>F</b>.") + FIG +
                 p("Propose a feasible synthetic route for the preparation of compound <b>F</b> from ethene.") +
                 p("You should state the reagents and conditions needed for each step and show clearly the structure of any intermediate compounds. " + mk(4)),
     p("The reaction in step 2 occurs in two stages.") +
     p("In <b>stage 1</b>, sodium ethoxide acts as a base and removes the α-hydrogen from ethyl 2-chloroethanoate, forming a carbanion at the carbon adjacent to the carbonyl group.") + FIG +
     p("In <b>stage 2</b>, the nucleophilic carbanion attacks the carbonyl carbon of <b>compound A</b>, forming a tetrahedral alkoxide intermediate. The negatively charged oxygen then attacks the carbon atom bearing the chlorine atom in an intramolecular nucleophilic substitution reaction forming <b>compound B</b>.") + FIG),
    ("(c)(iv)", p("Draw the structure of the alkoxide intermediate in the space provided. " + mk(1))),
    ("(c)(v)", p("The first part of the mechanism for <b>stage 2</b> has been drawn for you. Using the alkoxide intermediate structure drawn, complete the mechanism for <b>stage 2</b>. Include all relevant lone pairs, dipoles, curly arrows and charges. " + mk(1))),
    ("(c)(vi)", p("Describe a suitable chemical test to distinguish compound <b>D</b> from ibuprofen. Refer to Fig. 4.1 on page 17. " + mk(2))),
    ("(c)(vii)", p("In a separate experiment, compound <b>E</b> is synthesised by reacting compound <b>W</b> with ethanolic potassium cyanide as shown in Fig. 4.2.") + FIG + cap("Fig. 4.2") +
                 p("This reaction proceeds via S" + sub("N") + "1 or S" + sub("N") + "2 mechanism and forms a racemic mixture of compound <b>E</b>. Identify the mechanism and explain why it is preferred. Hence, explain why a racemic mixture is formed. " + mk(3))),
])

# ---------------------------------------------------------------- Q5 (20)  Section B
CH3_2CHCH2 = "(CH" + sub(3) + ")" + sub(2) + "CHCH" + sub(2)
Q[5] = dict(marks=20, intro=[
    p("To reduce reliance on fossil fuels, an integrated process employing Kolbe electrolysis for converting biomass-derived carboxylates into useful hydrocarbons is investigated.")], parts=[
    ("(a)", p("The Kolbe electrolysis reaction involves the electrolysis of aqueous solutions of sodium salts of carboxylic acids, using inert platinum electrodes. The reaction occurring at the anode is described by the equation shown below.") +
            ceqn("2RCOO" + sup(M) + " → R–R + 2" + CO2 + " + 2e" + sup(M)) +
            p("R = −CH" + sub(3) + ", −CH" + sub(2) + "CH" + sub(3) + ", etc.") +
            p("For example, the electrolysis of an aqueous solution of sodium ethanoate, CH" + sub(3) + "COO" + sup(M) + "Na" + sup("+") + " solution produces ethane, CH" + sub(3) + "CH" + sub(3) + ", at the anode.")),
    ("(a)(i)", p("Write the half-equation for the reaction occurring at the cathode. Hence, write the overall equation for the electrolysis of aqueous sodium ethanoate.") + p("Cathode:") + p("Overall: " + mk(2))),
    ("(a)(ii)", p("Using data from the " + DBK + ", calculate the volume of ethane produced at the anode maintained at 40 °C and 1 bar when a constant current of 2.5 A is passed through a solution of sodium ethanoate for 60 minutes. " + mk(3))),
    ("(a)(iii)", p("The ethane gas produced is pressurised before being used in a downstream reactor. Using the kinetic molecular theory, explain fully why ethane gas is expected to deviate from ideal gas behaviour. " + mk(2)),
     p(CH3_2CHCH2 + "COO" + sup(M) + "Na" + sup("+") + "(aq) undergoes Kolbe electrolysis at inert platinum electrodes. At the anode, the " + CH3_2CHCH2 + "COO" + sup(M) + " ions are oxidised to form radicals. Each carboxylate ion first loses one electron to form an acyloxy radical.") +
     ceqn(CH3_2CHCH2 + "COO" + sup(M) + " → " + CH3_2CHCH2 + "COO" + RAD + " + e" + sup(M)) +
     p("The acyloxy radical is unstable and decomposes rapidly, releasing carbon dioxide to form a " + CH3_2CHCH2 + RAD + " radical.") +
     ceqn(CH3_2CHCH2 + "–COO" + RAD + " → " + CH3_2CHCH2 + RAD + " + " + CO2) +
     p("Direct coupling of two " + CH3_2CHCH2 + RAD + " radicals produces 2,5-dimethylhexane, which is obtained in small yield at the anode.") + FIG +
     p("Another alkane is formed in much greater amount because some of the initially formed " + CH3_2CHCH2 + RAD + " radicals rearrange to a more stable radical before coupling occurs. The relative stabilities of radicals is similar to the relative stabilities of carbocations.")),
    ("(a)(iv)", p("Deduce the major organic product formed at the anode. Your answer should include the skeletal structural formula of the product. Explain why this is the major product in terms of relative radical stability and likelihood of coupling. " + mk(2))),
    ("(b)", p("2,5-dimethylhexane undergoes free-radical chlorination under ultraviolet light to give three different mono-chlorinated products, <b>X</b>, <b>Y</b> and <b>Z</b>.") + FIG +
            p("The relative amounts of the products is dependent on both the number of hydrogen available for substitution and the relative rates of hydrogen abstraction.") +
            p("Given that the relative rates of hydrogen abstraction at primary, secondary and tertiary carbon atoms are 1 : 4 : 5 respectively, deduce the relative amounts of the three mono-chlorinated products formed. Show your working clearly. " + mk(2))),
    ("(c)", p("Kolbe electrolysis of the sodium salt of 3-methylbutanoic acid produces a small amount of 2-methylpropene as an impurity via a side reaction of the alkyl radical formed at the anode.")),
    ("(c)(i)", p("The equations below outline the formation of 2-methylpropene from the acyloxy radical. Complete both equations using <b>single-headed curly arrows</b> to show the movement of electrons in each step.") + FIG + p(mk(1)),
     p("To remove the 2-methylpropene impurity, the gas mixture is treated with iodine monochloride, " + ICL + ".")),
    ("(c)(ii)", p("Deduce the major product formed when 2-methylpropene reacts with " + ICL + ". Explain your answer using a mechanism that shows curly arrows, the carbocation intermediate, and any relevant charges or dipoles. " + mk(3))),
    ("(c)(iii)", p("In this purification step, iodine monochloride solvent is preferred over liquid bromine. Suggest one reason, other than reagent cost or safety, for this choice. " + mk(1))),
    ("(d)", p("2-methylpropene can be converted into 3-hydroxy-3-methylbutanoic acid in three steps, as shown below.") + FIG),
    ("(d)(i)", p("Draw the structural formula of the intermediates <b>I</b> and <b>II</b> in the spaces above. " + mk(2))),
    ("(d)(ii)", p("For each step, state the suitable reagents and conditions for the conversion.") + p("Step 1:") + p("Step 2:") + p("Step 3: " + mk(2))),
])

SLOTS = {1: ["c"], 2: ["intro", "b", "bii", "d"], 3: ["a", "di", "di2"], 4: ["c", "ciii", "ciii2", "ciii3", "cvii"], 5: ["aiii", "b", "ci", "d"]}

def lead_inline(h):
    if h.startswith("<p>"):
        j = h.index("</p>")
        return h[3:j] + h[j + 4:]
    return h
NB = "&nbsp;"
def nbsp(h):
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b|nm\b|mg\b|V\b|A\b|h\b|min\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol)\b)", "</sup>" + NB, h)
    h = re.sub(r"</sup> (?=(?:K|s)<sup>)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

def strip(h):
    h = h.replace(FIG, " ").replace("<br>", " ")
    h = re.sub(r"</(p|li|tr|div)>", " ", h)
    h = re.sub(r"</(td|th)>", " | ", h)
    h = re.sub(r"<span[^>]*>\s*</span>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", h).strip()

EXTRA_TEXT = {(1, "(c)"): "thermometer copper can containing water wire gauze tripod spirit lamp containing liquid methanol",
              (2, None): "(+)-etomidate N O",
              (2, "(b)"): "etomidate H2O enzyme CH3CH2OH carboxylic acid",
              (2, "(b)(ii)"): "OH- I II III tetrahedral intermediate carboxylate ethanol ethoxide",
              (2, "(c)"): "1-phenylethanamine NH2 multiple steps etomidate",
              (3, "(a)"): "pH volume of NaOH added 22.40 44.80 50.00 > 7",
              (3, "(d)(i)"): "energy Mn2+ Cr3+ Cu+",
              (4, "(c)"): "isobutylbenzene step 1 A step 2 NaOCH2CH3 B step 3 H+ heat D step 4 NH2OH step 5 E step 6 H+ heat ibuprofen",
              (4, "(c)(iii)"): "H2C=CH2 1 step C2H5OCl 2 steps F CH3CH2OH ethyl 2-chloroethanoate stage 1 stage 2 A alkoxide intermediate B",
              (4, "(c)(vii)"): "compound W KCN (alc) compound E",
              (5, "(a)(iii)"): "2,5-dimethylhexane",
              (5, "(b)"): "X Y Z",
              (5, "(c)(i)"): "2-methylpropene",
              (5, "(d)"): "2-methylpropene step 1 Intermediate I step 2 Intermediate II step 3 3-hydroxy-3-methylbutanoic acid"}

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
    nph = html.count('class="fig"')
    assert nph == len(SLOTS[n]), (n, nph, SLOTS[n])
    for o, slot in enumerate(SLOTS[n], 1):
        plan.append({"question": n, "part": slot, "slot": slot, "ordinal": o, "kind": "block",
                     "storage_path": "%s_%s_%s_Q%d_%s_%d.png" % (SCHOOL, LEVEL, PAPER, n, slot, YEAR)})
assert sum(r["marks"] for r in rows) == 95
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))
