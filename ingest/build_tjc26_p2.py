"""Hand transcription of TJC 2026 H2 Prelim Paper 2 (9476/02, 6 structured Q, 75 marks) -> questions.json +
asset_plan.json. Typed from the school's Word file ("H2 P2 Review": question paper with the mark scheme inline in
blue/red) and its Word-exported PDF (the two agree word for word). Same output contract as build_sajc26_p2.py, i.e. what
gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_tjc26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school TJC --year 2026 --paper 2 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_sajc26_p2.py / build_rvhs26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced;
  * asset slot = part label without brackets ('a', 'c'), 'intro' for the stem, 'intro2' / 'd2' for a second figure.
  * Q2(b)(ii): the "|lattice energy| proportional to q+q-/(r+ + r-)" line is part of the school's SOLUTION (different font
    colour in the Word file), not the question, so it is not typed here (user ruling, 2026-11-25);
  * text the school prints between two sub-parts (Q1(b)(i) Li+ sentence, Q1(b)(ii) Table 1.1, Q1(b)(iv) battery data,
    Q3(b)(i) cis-trans sentence, Q6(c)(i) bidentate-ligand paragraphs) is a tail after the part before it; lead-in text
    printed before a "(b)"/"(c)" that has sub-parts is the text of a bare "(b)"/"(c)" part.

MARKS. The school's file has no part marks printed in the question for Q1-Q3, Q5, Q6 (the right-margin "[n]" was
replaced by the mark scheme's own red [n] / tick marks); Q4 does print them. Marks for the other five questions are
therefore taken from the mark scheme (ticks counted as the school states, e.g. "2 [tick] = 1 mark") and each question
is asserted to sum to its printed [Total: n]: Q1 12, Q2 13, Q3 14, Q4 16, Q5 5, Q6 15 = 75. A mark that the school
prints under a formula/figure is placed at the end of the instruction sentence.

Typography as the other 2026 builders: x -> multiplication sign, hyphen/en dash minus -> U+2212 (a "+ 0.38" / "- 1.22"
sign spaced from its number is closed up), italic element l, the standard-state sign for the school's small raised o.
School slips corrected (veto-able; listed in the chat note):
  Q1(b)(v) "Using Avogadro constant" -> "Using the Avogadro constant"; Q2(a)(iv) "gibbs" -> "Gibbs";
  Q3(b)(i) "a pair of cis-trans isomer" -> "isomers"; Q4(c) "shown in Fig. 4.1 on page 13" -> "shown in Fig. 4.1"
  (the page number belongs to the printed paper, not the site); Q6 "electrochemically-mediated" en dash -> hyphen.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "TJC", "H2", "P2", 2026
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
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def ion(sym, ch): return sym + sup(ch)

L = '<i class="el">l</i>'                  # element l
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
STD = sup('<span class="pl-sym">⦵</span>')
def dG(): return DEL + i("G") + STD
def iso(a, sym): return sup(a) + sym
DBK = i("Data Booklet")
EM = "&emsp;"
ARR = "→"
CO2 = "CO" + sub(2)
H2O = "H" + sub(2) + "O"
CUEN2 = "[Cu(en)" + sub(2) + "]" + sup("2+")
PCL3 = "PC" + L + sub(3)
H3PO3 = "H" + sub(3) + "PO" + sub(3)
CACO3 = "CaCO" + sub(3)
CO3 = "CO" + sub(3) + sup("2" + M)
O2M = "O" + sup("2" + M)
ALPHA = "α"
def kj(): return "kJ mol" + sup(M + "1")

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (12)
Q[1] = dict(marks=12, intro=[
    p("Modern spacecrafts require both efficient rocket fuels and lightweight rechargeable batteries."),
    p("Liquid hydrogen is commonly used as rocket fuel and burns according to the equation below."),
    c("2H" + sub(2) + "(l) + O" + sub(2) + "(l) " + ARR + " 2H" + sub(2) + "O(g)"),
    p("A spacecraft carries 500 kg of liquid hydrogen fuel. During the mission, water produced from the combustion of hydrogen is collected "
      "for onboard use. The mission requires at least 4000 kg of water.")], parts=[
    ("(a)(i)", p("Calculate the mass of water, in kg, that can be produced from 500 kg of hydrogen fuel given that only 90% of the hydrogen "
                 "undergoes complete combustion. " + mk(2))),
    ("(a)(ii)", p("Hence, justify whether the hydrogen fuel carried is sufficient to meet the water requirement for this mission. " + mk(1))),
    ("(b)", p("The spacecraft is powered by rechargeable lithium batteries. Lithium is chosen because of its low density and its ability to form "
              "Li" + sup("+") + " ions readily. Naturally occurring lithium consists of two stable isotopes, " + iso(6, "Li") + " and " + iso(7, "Li") + ".")),
    ("(b)(i)", p("The relative atomic mass of a sample of lithium which contains only these two isotopes is 6.94. Calculate the relative abundance "
                 "of each of the two stable isotopes. Show your working. " + mk(2)),
     p("Lithium atoms undergo ionisation in the battery to form lithium ions, Li" + sup("+") + ".")),
    ("(b)(ii)", p("Define the term " + i("first ionisation energy") + ". " + mk(1)),
     p("The first three ionisation energies of lithium are shown in Table 1.1.") +
     cap("Table 1.1") +
     table(tr(th(""), th("first ionisation energy"), th("second ionisation energy"), th("third ionisation energy")),
           tr(td("lithium"), td("519"), td("7300"), td("11800")))),
    ("(b)(iii)", p("Explain why the second ionisation energy of lithium is much higher than its first ionisation energy. " + mk(2))),
    ("(b)(iv)", p("Explain why the first ionisation energy of boron is higher than that of lithium but lower than that of beryllium. " + mk(2)),
     p("A lithium-ion battery contains 64.9 g of lithium atoms.") +
     p("The unit of charge is the coulomb, C. The charge on an electron is 1.60 × 10" + sup(M + "19") + " coulombs.")),
    ("(b)(v)", p("Using the Avogadro constant, " + i("L") + ", calculate the charge, in coulombs, if all the lithium atoms in this battery are "
                 "converted to lithium ions. Show your working. " + mk(2)) +
               p("Use of the " + DBK + " is required.")),
])

# ---------------------------------------------------------------- Q2  (13)
Q[2] = dict(marks=13, intro=[], parts=[
    ("(a)", p("Hydrogen peroxide is moderately stable but decomposes to form water and oxygen when a catalyst is added.") +
            c("2H" + sub(2) + "O" + sub(2) + "(l) " + ARR + " 2H" + sub(2) + "O(l) + O" + sub(2) + "(g)")),
    ("(a)(i)", p("Predict the sign of the standard entropy change of the reaction and explain your answer. " + mk(1))),
    ("(a)(ii)", p("Using data from the " + DBK + ", calculate the standard enthalpy change of the reaction. " + mk(2))),
    ("(a)(iii)", p("The literature value of the standard enthalpy change of reaction is different from the value calculated in " + b("(a)(ii)") + ".") +
                 p("Other than bond energy values being average, suggest another reason for this difference. " + mk(1))),
    ("(a)(iv)", p("The standard Gibbs free energy change of the reaction is " + M + "238 " + kj() + ".") +
                p("Using the answer from " + b("(a)(ii)") + ", calculate the standard entropy change of the reaction. " + mk(1))),
    ("(b)", p("Group 2 carbonates such as " + CACO3 + " decompose on heating. The enthalpy change for the decomposition can be estimated using "
              "lattice energies. Table 2.1 shows some enthalpy changes.") +
            cap("Table 2.1") +
            table(tr(td(CO3 + "(g) " + ARR + " " + CO2 + "(g) + " + O2M + "(g)"), td("+914 " + kj())),
                  tr(td("Lattice energy of " + CACO3 + "(s)"), td(M + "2800 " + kj())),
                  tr(td("Lattice energy of CaO(s)"), td(M + "3460 " + kj())))),
    ("(b)(i)", p("Define lattice energy. " + mk(1))),
    ("(b)(ii)", p("Explain why the lattice energy of CaO is more exothermic than " + CACO3 + ". " + mk(1))),
    ("(b)(iii)", p("Using the data in Table 2.1, construct an energy cycle to calculate the enthalpy change of decomposition of calcium carbonate. " + mk(3))),
    ("(b)(iv)", p("Suggest and explain whether " + CACO3 + " or SrCO" + sub(3) + " is thermally less stable. " + mk(3))),
])

# ---------------------------------------------------------------- Q3  (14)
RCL = "RC" + L
Q[3] = dict(marks=14, intro=[], parts=[
    ("(a)", p("Phosphorus trichloride, " + PCL3 + ", is widely used in industrial chemistry to synthesise pesticides and flame retardants. "
              "It can react with alcohol to give chloroalkane and phosphorous acid, " + H3PO3 + ".") +
            c("3 ROH + " + PCL3 + " " + ARR + " 3 " + RCL + " + " + H3PO3)),
    ("(a)(i)", p("Draw the shape of " + PCL3 + ". State its shape and bond angle. " + mk(2))),
    ("(a)(ii)", p("Deduce and explain the polarity of " + PCL3 + ". " + mk(1))),
    ("(a)(iii)", p(H3PO3 + " is a diprotic acid which contains two O–H bonds in the molecule.") +
                 p("Draw the dot and cross diagram of " + H3PO3 + ". " + mk(1))),
    ("(a)(iv)", p("Using the Valence Shell Electron Pair Repulsion (VSEPR) theory, state and explain the difference in bond angles about the P atom in " +
                  PCL3 + " and in " + H3PO3 + ". " + mk(1))),
    ("(b)", p("Compound " + b("D") + " has the molecular formula C" + sub(7) + "H" + sub(14) + "O. " + b("D") + " effervesces with sodium metal and gives a "
              "yellow precipitate with alkaline aqueous iodine. Heating " + b("D") + " with acidified KMnO" + sub(4) + " produces CH" + sub(3) + "CH" + sub(2) +
              "COCH" + sub(3) + " and CH" + sub(3) + "COCO" + sub(2) + "H.")),
    ("(b)(i)", p("For each test, state the type of reaction occurring and deduce the functional groups present in " + b("D") + ".") +
               p("Hence, determine the structure of " + b("D") + ". " + mk(4)),
     p(b("D") + " exists as a pair of cis-trans isomers.")),
    ("(b)(ii)", p("Explain how cis-trans isomerism arises. " + mk(2))),
    ("(b)(iii)", p("Draw the skeletal formula of the cis and trans isomers of " + b("D") + ". " + mk(1))),
    ("(b)(iv)", p("Write a balanced equation for the reaction of CH" + sub(3) + "CH" + sub(2) + "COCH" + sub(3) + " with alkaline aqueous iodine. " + mk(2))),
])

# ---------------------------------------------------------------- Q4  (16)
EPLUS = b("E") + sup("+")
Q[4] = dict(marks=16, intro=[
    p("Aldehydes and ketones react with primary amines in slightly acidic solutions to form imines, which contain the C=N group. "
      "For example, propanal can react with methylamine to form an imine as shown.") + FIG], parts=[
    ("(a)", p("Fig. 4.1 shows the mechanism for the reaction between propanal and methylamine to form an imine.") + FIG + cap("Fig. 4.1")),
    ("(a)(i)", p("State the role of CH" + sub(3) + "NH" + sub(2) + " in step 1. " + mk(1))),
    ("(a)(ii)", p("Step 4 is an elimination reaction.") +
                p("Suggest the structure of " + EPLUS + ". The positive charge is " + b("not") + " on a carbon atom. " + mk(1))),
    ("(a)(iii)", p("Use Fig. 4.1 to suggest one role of the H" + sup("+") + " ion. Explain your answer with reference to the steps shown in the mechanism. " + mk(1))),
    ("(b)", p("The Maillard reaction is responsible for the rich brown colours, aromas and flavours in foods. When starchy foods undergo the Maillard "
              "reaction, a potential carcinogen, acrylamide, is formed as a by-product. Its formation is due to the reaction between glucose and the " +
              ALPHA + "-amino acid, asparagine, to form imine " + b("G") + " at high cooking temperatures as shown in Fig. 4.2.") + FIG + cap("Fig. 4.2")),
    ("(b)(i)", p("State and explain the difference in basicity of N" + sub("a") + " and N" + sub("b") + " in asparagine. " + mk(2))),
    ("(b)(ii)", p(b("G") + " undergoes decarboxylation to produce carbon dioxide gas, followed by a series of reactions to form acrylamide as shown in Fig. 4.2.") +
                p("On the structure of " + b("G") + " given in Fig. 4.2, draw three curly arrows to show the movement of electrons for the decarboxylation of " +
                  b("G") + " to form carbon dioxide gas in step II. " + mk(1))),
    ("(b)(iii)", p("Another " + ALPHA + "-amino acid reacts with glucose via the same reaction scheme in Fig. 4.2 to form (CH" + sub(3) + ")" + sub(2) +
                   "C=CH" + sub(2) + " and NH" + sub(3) + " as the final products.") +
                 p("Suggest the structure of the " + ALPHA + "-amino acid. " + mk(1))),
    ("(c)", p("Fig. 4.3 shows the synthesis of imine " + b("R") + " from compound " + b("J") + ".") +
            p("The reaction of " + b("Q") + " in step 5 proceeds by a similar mechanism shown in Fig. 4.1.") + FIG + cap("Fig. 4.3")),
    ("(c)(i)", p("In step 1 of the synthesis, " + b("J") + " reacts with water to form " + b("K") + ".") +
               p("Give two reasons for the difference in the relative ease of hydrolysis of the two chlorine-containing functional groups in " + b("J") + ". " + mk(2))),
    ("(c)(ii)", p("Draw the structures of organic compounds " + b("L") + " and " + b("R") + " in the spaces provided in Fig. 4.3. " + mk(2))),
    ("(c)(iii)", p("State the reagents and conditions for steps 3 and 4. " + mk(2))),
    ("(d)", p("The reaction in step 4 results in an inversion of configuration.") +
            p("Describe the mechanism for the reaction to form compound " + b("Q") + " and any other products. Show relevant lone pairs and dipoles and "
              "use curly arrows to indicate the movement of electron pairs. " + mk(3))),
])

# ---------------------------------------------------------------- Q5  (5)
Q[5] = dict(marks=5, intro=[
    p("The modern alkaline battery uses the zinc/manganese dioxide chemistry. Aqueous potassium hydroxide provides the alkaline medium."),
    p("When the battery discharges, solid manganese(IV) dioxide, MnO" + sub(2) + ", is converted to solid manganese(III) oxyhydroxide, MnOOH, "
      "at the cathode. The reaction is as follows."),
    ceqn("MnO" + sub(2) + "(s) + H" + sub(2) + "O(l) + e" + sup(M) + " " + ARR + " MnOOH(s) + OH" + sup(M) + "(aq)" + EM + EM + EM +
         i("E") + STD + "(MnO" + sub(2) + "/MnOOH) = +0.38 V")], parts=[
    ("(a)", p("Zinc is converted to solid zinc hydroxide at the anode.") +
            p("Construct a half-equation, with state symbols, for the reaction at the anode when the battery discharges. " + mk(1))),
    ("(b)", p("Write an overall equation for the zinc/manganese dioxide alkaline battery when the battery discharges. " + mk(1))),
    ("(c)", p("The standard electrode potential for Zn(OH)" + sub(2) + "/Zn is " + M + "1.22 V.")),
    ("(c)(i)", p("Calculate the standard cell potential for the zinc/manganese dioxide alkaline battery. " + mk(1))),
    ("(c)(ii)", p("Hence, calculate the standard Gibbs free energy change, " + dG() + ", for the zinc/manganese dioxide alkaline battery. " + mk(1))),
    ("(d)", p("The standard Gibbs free energy change is related to the equilibrium constant, " + K + sub("eq") + ", by the equation:") +
            c(dG() + " = " + M + " RT ln " + K + sub("eq")) +
            p("where " + dG() + " is in J mol" + sup(M + "1") + ".") +
            p("Using your answer in " + b("(c)(ii)") + ", calculate the equilibrium constant, " + K + sub("eq") + ", for the zinc/manganese dioxide alkaline battery. " + mk(1))),
])

# ---------------------------------------------------------------- Q6  (15)
Q[6] = dict(marks=15, intro=[
    p("Carbon capture and storage (CCS) is a critical climate mitigation process that captures carbon dioxide, " + CO2 + ", emissions directly at "
      "industrial sources, such as power plants, before they enter the atmosphere."),
    p("One method of CCS is the electrochemically-mediated amine regeneration (EMAR). This electrolysis method uses amine-based absorbents and "
      "copper electrodes to capture and store " + CO2 + " for future uses. A typical setup for the EMAR process is shown in Fig. 6.1.") + FIG + cap("Fig. 6.1"),
    p("Flue gas is a mixture of industrial gaseous byproducts. It is first passed through the absorber tank which contains ethane-1,2-diamine (en). "
      "Carbon dioxide in the flue gas mixture reacts with ethane-1,2-diamine to form carbamate ion, as shown in Fig. 6.2.") + FIG + cap("Fig. 6.2"),
    p("The carbamate is passed through the electrolytic cell near the positive terminal, where copper(II) ions produced react with the carbamates to "
      "form " + CUEN2 + " complex ions. Carbon dioxide gas is released in the process and directed to storage tanks for future uses."),
    p("The " + CUEN2 + " complex ions migrate through a semi-permeable membrane, to the negative terminal, where copper(II) ions are converted back "
      "to copper metal. Ethane-1,2-diamine molecules are released and recycled back to the absorber tank for subsequent reactions.")], parts=[
    ("(a)", p("Construct a half-equation at the positive terminal of the EMAR process, showing the reaction of copper electrode and carbamates to form " +
              CUEN2 + " and " + CO2 + ". " + mk(1))),
    ("(b)", p("In one laboratory process, the current used for the EMAR process is 176 A.")),
    ("(b)(i)", p("Calculate the time, " + i("t") + ", for 17.0 g copper to be electrodeposited at the negative terminal, assuming an efficiency of 100%. " + mk(3))),
    ("(b)(ii)", p("With reference to your answer in " + b("(a)") + ", calculate the volume of " + CO2 + " released at the positive terminal in the storage "
                  "tank after time " + i("t") + ", at room temperature and pressure. " + mk(1))),
    ("(c)", p("During the electrolysis process, the region of the semi-permeable membrane changes colour from colourless to deep blue, due to the "
              "copper(II) complex ion, " + CUEN2 + ".")),
    ("(c)(i)", p("Explain the origin of the deep blue colour of the " + CUEN2 + " ion. " + mk(3)),
     p("Ethane-1,2-diamine is a " + i("bidentate ligand") + ".") +
     p(CUEN2 + " can also be formed when ethane-1,2-diamine is added to aqueous copper(II) sulfate solution. An immediate colour change of the solution is observed.")),
    ("(c)(ii)", p("Explain the term " + i("bidentate ligand") + ". " + mk(1))),
    ("(c)(iii)", p("State the type of reaction that occurs and construct an equation for this reaction. You may use en to represent "
                   "ethane-1,2-diamine in the equation. " + mk(2))),
    ("(c)(iv)", p("With reference to your answer in " + b("(c)(iii)") + " and the thermodynamics aspect of the reaction, explain why the colour change "
                  "happens readily. " + mk(1))),
    ("(d)", p("The formation of carbamates in the absorber tank involves a nucleophilic addition reaction between the nitrogen atom of "
              "ethane-1,2-diamine and carbon dioxide.") + FIG +
            p("One reaction uses amine " + b("X") + ", instead of ethane-1,2-diamine, to capture " + CO2 + ".") + FIG +
            p("Compare the effectiveness of amine " + b("X") + " to capture " + CO2 + " in the absorber tank. " + mk(2))),
    ("(e)", p("The electrolyte used in Fig. 6.1 is an ionic liquid that does not contain any water. High voltage is applied across the terminals.") +
            p("With reference to the reaction at the positive electrode, or otherwise, suggest one reason why water is not used as a medium for the "
              "EMAR process to capture and store " + CO2 + ". " + mk(1))),
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
EXTRA_TEXT = {(4, None): "propanal methylamine imine H+ NCH3 H2O CH3NH2",
              (4, "(a)"): "step 1 step 2 step 3 step 4 step 5 CH3NH2 H+ E+ propanal imine",
              (4, "(b)"): "asparagine glucose imine G step I step II multiple steps acrylamide NH2 CO2 NH3 Na Nb",
              (4, "(c)"): "J K L P Q imine R C6H10N2 step 1 step 2 step 3 step 4 step 5 H2O LiAlH4 H+ Cl",
              (6, None): "Pure CO2 to storage tank + terminal - terminal Cu absorber tank CO2 in flue gas en carbamates [Cu(en)2]2+ "
                         "semi permeable membrane electrolyte ethane-1,2-diamine CO2 carbamate",
              (6, "(d)"): "ethane-1,2-diamine CO2 carbamate amine X"}

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
assert sum(r["marks"] for r in rows) == 75
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))
