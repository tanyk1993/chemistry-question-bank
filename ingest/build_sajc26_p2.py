"""Hand transcription of SAJC 2026 H2 Prelim Paper 2 (9476/02, 5 structured Q, 75 marks, 1 Sept 2026) -> questions.json +
asset_plan.json. Typed from the school's Word file and the Word-exported PDF (the two agree word for word). Same output
contract as build_rvhs26_p3.py, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_sajc26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school SAJC --year 2026 --paper 2 --level H2 --skip-assets=false

Conventions (claude/style-guide.md; same as build_rvhs26_p2.py / build_rvhs26_p3.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it (a mark printed under a figure or table goes at the
    end of the instruction sentence that asks for the work; a mark under a bullet list goes in the last bullet);
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c; Table 5.2 (structures in
    its cells) is one picture with the caption typed;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed; labelled answer
    lines such as "Advantage:" are typed);
  * asset slot = part label without brackets ('aii', 'biv'); 'intro' for the stem; 'c2' for a second figure in a part.
  * text the school prints between two sub-parts (Q1(e) FeCl3 sentence) is a tail after the part before it; lead-in text
    that the school prints before "(b)", "(c)", "(d)" of Q2/Q3 (equilibria, Fig 3.1, Table 3.1) is the text of a bare
    "(b)"/"(c)"/"(d)" part, as the other P2/P3 builders do.
Typography as the other 2026 builders: x -> multiplication sign, hyphen/en dash minus -> U+2212, "25 oC" -> "25 °C",
italic element l, the standard-state sign for the school's small raised o on delta H.
School slips corrected (listed in the handoff note; veto-able):
  Q2(a)(iii) "ligands" -> "ligand"; Q2(c) "equilibrium 2" gets its full stop; Q2(c)(ii) "What does Kc1 and Kc2 tell" -> "do";
  Q4(c) "Conjugate dienes" -> "Conjugated dienes"; Q4(e)(i) "atoms that is sp" -> "atoms that are sp";
  Q5(a)(i) "forces of attractions" -> "attraction"; Q5(b)(iii) "an advantage and disadvantage" -> "a disadvantage";
  Q5(c)(ii) full stop added after "in your answer".
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SAJC", "H2", "P2", 2026
FIG = '<div class="fig">figure</div>'
M = "−"                              # minus sign U+2212
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
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
DH_HYD = DEL + i("H") + STD + sub("hydrogenation")
DH_VAP = DEL + i("H") + sub("vap")
EM = "&emsp;"
DBK = i("Data Booklet")
CL = "C" + L
HCL = "HC" + L
MGCL2 = "MgC" + L + sub(2)
PCL5 = "PC" + L + sub(5)
FECL3 = "FeC" + L + sub(3)
FE2 = "Fe" + sup("2+")
O2 = "O" + sub(2)
def iso(a, sym, ch=""): return sup(a) + sym + (sup(ch) if ch else "")
ETHANOYL = lambda x: x                    # placeholder for readability

def eq(n, body, kc):
    return p("equilibrium %d" % n + EM + body + (EM + EM + kc if kc else ""))

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1  (17)
Q[1] = dict(marks=17, intro=[
    p("Magnesite is a mineral that is commonly found in rocks at mining sites. It is known to mainly contain isotopes of magnesium, carbon and oxygen "
      "along with their ions and compounds.")], parts=[
    ("(a)(i)", p("Define the term " + i("isotopes") + ". " + mk(1))),
    ("(a)(ii)", p("Table 1.1 shows information about the isotopes of magnesium found in a sample of magnesite.") +
                cap("Table 1.1") +
                table(tr(th("relative mass"), th("relative % abundance")),
                      tr(td("23.92"), td("66.71")), tr(td("25.08"), td("5.99")), tr(td("26.11"), td("9.31"))) +
                p("Calculate the relative atomic mass of magnesium in this sample to four significant figures. Show your working. " + mk(2))),
    ("(b)", p("Table 1.2 lists the number of protons, neutrons and electrons of five different particles found in magnesite. "
              "Each particle may be an atom, an anion or a cation.") +
            cap("Table 1.2") +
            table(tr(th("particle"), th("number of protons"), th("number of neutrons"), th("number of electrons")),
                  tr(td(""), td("6"), td("6"), td("2")),
                  tr(td(iso(13, "C")), td(""), td("7"), td("6")),
                  tr(td(iso(18, "O", "2" + M)), td("8"), td(""), td("")),
                  tr(td(iso(25, "Mg", "2+")), td("12"), td("13"), td("")),
                  tr(td(iso(26, "Mg")), td("12"), td(""), td("12"))) +
            p("Complete Table 1.2. " + mk(2))),
    ("(c)(i)", p("Write an equation for the first ionisation energy of oxygen. " + mk(1))),
    ("(c)(ii)", p("Describe and explain the change in first ionisation energy from") +
                ul("carbon to nitrogen, and", "nitrogen to oxygen. " + mk(3))),
    ("(d)", p("One of the compounds in magnesite is magnesium carbonate.")),
    ("(d)(i)", p("Draw a ‘dot-and-cross’ diagram of magnesium carbonate. " + mk(1))),
    ("(d)(ii)", p("Describe a simple chemical test to confirm the presence of carbonate in magnesite. Include any observations. " + mk(2))),
    ("(e)", p("Magnesium chloride, " + MGCL2 + ", is produced from magnesite by leaching or dissolving processed magnesite ore in " + HCL + ".")),
    ("(e)(i)", p("Explain, in terms of structure and bonding, the difference in melting point between " + MGCL2 + " and " + PCL5 + ". " + mk(2)),
     p("As there are trace amounts of iron in magnesite, " + FECL3 + " is also produced.")),
    ("(e)(ii)", p("Write an equation to show why a solution of " + MGCL2 + " has a pH of 6.5. " + mk(1))),
    ("(e)(iii)", p("Explain why the pH of a solution of " + FECL3 + " is lower than a solution of " + MGCL2 + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q2  (15)
Q[2] = dict(marks=15, intro=[
    p("Haemoglobin is an iron-containing transition metal complex, specifically a metalloprotein, which transports oxygen in red blood cells."),
    p("In oxyhaemoglobin, " + FE2 + " is surrounded by five nitrogen-containing ligands and one " + O2 + " ligand in an octahedral arrangement.")], parts=[
    ("(a)(i)", p("State the full electronic configuration of " + FE2 + ". " + mk(1))),
    ("(a)(ii)", p("There are two energy levels of d orbitals in an octahedral complex. Electrons in the d subshell may fill up the d orbitals in the lower "
                  "energy level before filling up the d orbitals in the higher energy level or occupy all the orbitals singly before pairing up.") +
                p("There are fewer unpaired electrons in " + FE2 + " of oxyhaemoglobin than there are in isolated gaseous " + FE2 + ".") +
                FIG + cap("Fig 2.1") +
                p("On Fig 2.1, label the d orbitals and show the distribution of electrons in the 3d subshell for " + FE2 + " in oxyhaemoglobin. " + mk(2))),
    ("(a)(iii)", p("Identify the type of bond formed between the nitrogen atom of each nitrogen-containing ligand and " + FE2 + ". "
                   "Explain how this bond is formed. " + mk(2))),
    ("(b)", p("One molecule of deoxyhaemoglobin, Hb, can bond with four molecules of oxygen to form oxyhaemoglobin, as shown in equilibrium 1.") +
            eq(1, "Hb(aq) + 4" + O2 + "(aq) ⇌ Hb(" + O2 + ")" + sub(4) + "(aq)", K + sub("c1") + " = 4.5 × 10" + sup(6)) +
            p("Oxyhaemoglobin is bright red, while deoxyhaemoglobin is dark purple-red.")),
    ("(b)(i)", p("Explain why oxyhaemoglobin is coloured. " + mk(3))),
    ("(b)(ii)", p("Oxyhaemoglobin and deoxyhaemoglobin have different colours. Explain why. " + mk(1))),
    ("(c)", p("The binding of carbon monoxide to haemoglobin forms carboxyhaemoglobin, as shown in equilibrium 2.") +
            eq(2, "Hb(aq) + 4CO(aq) ⇌ Hb(CO)" + sub(4) + "(aq)", K + sub("c2") + " = 2.2 × 10" + sup(29))),
    ("(c)(i)", p("Suggest why carbon monoxide binds to " + FE2 + " at the carbon atom and not at the oxygen atom. " + mk(1))),
    ("(c)(ii)", p("What do " + K + sub("c1") + " and " + K + sub("c2") + " tell you about the relative affinity of haemoglobin for oxygen and carbon monoxide? " + mk(1))),
    ("(c)(iii)", p("Write the expression for the equilibrium constant, " + K + sub("c2") + ", for this reaction. Include its units. " + mk(1))),
    ("(d)", p("The displacement of oxygen from Hb(" + O2 + ")" + sub(4) + " by carbon monoxide is shown in equilibrium 3.") +
            eq(3, "Hb(" + O2 + ")" + sub(4) + "(aq) + 4CO(aq) ⇌ Hb(CO)" + sub(4) + "(aq) + 4" + O2 + "(aq)", K + sub("c3"))),
    ("(d)(i)", p("Carbon monoxide poisoning is treated using hyperbaric oxygen therapy, which involves administering pure oxygen at pressures greater "
                 "than atmospheric level.") +
               p("Using " + i("Le Chatelier’s Principle") + ", explain how hyperbaric oxygen therapy restores oxygen transport in the blood. " + mk(1))),
    ("(d)(ii)", p("Use " + K + sub("c1") + " and " + K + sub("c2") + " to calculate a value for " + K + sub("c3") + ". " + mk(2))),
])

# ---------------------------------------------------------------- Q3  (15)
ACYL = "CH" + sub(3) + "COC" + L
BRACYL = "CH" + sub(2) + "BrCOC" + L
CLACYL = "CH" + sub(2) + "C" + L + "COC" + L
Q[3] = dict(marks=15, intro=[
    p("Compound " + b("X") + " is a sweet-smelling substance extracted from a tropical fern. Acid hydrolysis of " + b("X") +
      " yields three compounds " + b("A") + ", " + b("B") + " and " + b("D") + " only.") + FIG], parts=[
    ("(a)(i)", p("Give the systematic name for " + b("D") + ". " + mk(1))),
    ("(a)(ii)", p("Suggest why " + b("D") + " is more acidic than " + b("A") + ". " + mk(2))),
    ("(a)(iii)", p("Draw the structure of " + b("X") + ". " + mk(1))),
    ("(b)", p("When cold water is added to ethanoyl chloride, hydrolysis occurs rapidly.") +
            p("The hydrolysis of ethanoyl chloride is shown in Fig 3.1.") + FIG + cap("Fig 3.1") +
            p("The hydrolysis of substituted ethanoyl chlorides was monitored by measuring the initial rates at 25 °C. Table 3.1 shows the results. "
              "In each experiment, the initial concentration of the substituted ethanoyl chloride was 2.00 × 10" + sup(M + "2") + " " + MDM +
              " and the initial concentration of water was 0.15 " + MDM + ".") +
            cap("Table 3.1") +
            table(tr(th(""), th("Initial rate / " + MDM + " s" + sup(M + "1"))),
                  tr(td(ACYL), td("5.1 × 10" + sup(M + "6"))),
                  tr(td(BRACYL), td("1.3 × 10" + sup(M + "5"))),
                  tr(td(CLACYL), td("1.9 × 10" + sup(M + "5"))))),
    ("(b)(i)", p("Suggest the name of the mechanism for step 1. " + mk(1))),
    ("(b)(ii)", p("Step 1 is the slow step in this mechanism.") +
                p("Suggest the rate equation for the hydrolysis of ethanoyl chloride. " + mk(1))),
    ("(b)(iii)", p("Hence, calculate the value of the rate constant, " + i("k") + ", for the hydrolysis of ethanoyl chloride. Include its units. " + mk(1))),
    ("(b)(iv)", p("Based on your rate equation in " + b("(b)(ii)") + ", sketch a graph of [ethanoyl chloride] against time. "
                  "You may assume that water is in large excess.") +
                p("Use the graph to suggest how successive half-lives vary for this reaction. " + mk(2)) + FIG),
    ("(b)(v)", p("Explain how the initial rate can be determined from the graph in " + b("(b)(iv)") + ". " + mk(1))),
    ("(b)(vi)", p("Using collision theory, explain how the initial rate will change when the hydrolysis of ethanoyl chloride is carried out at 35 °C. " + mk(2))),
    ("(c)(i)", p("Using the data in Table 3.1, state the relationship between the electronic effect of the substituent and the rate of hydrolysis. " + mk(1))),
    ("(c)(ii)", p("By considering the reaction in Fig 3.1, suggest a reason for this relationship. " + mk(2))),
])

# ---------------------------------------------------------------- Q4  (14)
Q[4] = dict(marks=14, intro=[
    p("A conjugated system occurs when double and single carbon-carbon bonds alternate. This system is seen in aromatic rings like benzene and in "
      "certain alkenes, such as conjugated dienes."),
    p("Buta-1,3-diene is the simplest conjugated diene.") + FIG], parts=[
    ("(a)", p("Describe how delocalisation of electrons in buta-1,3-diene occurs. " + mk(1))),
    ("(b)", p("Buta-1,3-diene undergoes hydrogenation to form butane.")),
    ("(b)(i)", p("The standard enthalpy change of hydrogenation, " + DH_HYD + ", of an isolated C=C is approximately " + M + "112 kJ mol" + sup(M + "1") + ".") +
               p("Calculate the expected " + DH_HYD + " for buta-1,3-diene. " + mk(1))),
    ("(b)(ii)", p("The difference in the expected and actual " + DH_HYD + " in buta-1,3-diene is known as stabilisation energy.") +
                p("The actual enthalpy of hydrogenation, " + DH_HYD + ", of buta-1,3-diene is " + M + "208 kJ mol" + sup(M + "1") + ".") +
                p("Using your answer in " + b("(b)(i)") + ", construct an energy level diagram to determine the stabilisation energy in buta-1,3-diene. " + mk(2)) +
                FIG),
    ("(c)", p("Conjugated dienes can undergo addition with alkenes in a process called Diels-Alder reaction to form cyclic products.") +
            p("An example of the Diels-Alder reaction is shown below where gaseous buta-1,3-diene reacts with gaseous ethene to form liquid cyclohexene.") +
            FIG + cap("Fig 4.1")),
    ("(c)(i)", p("Using relevant data from the " + DBK + ", calculate the enthalpy change for the Diels-Alder reaction in Fig 4.1. " + mk(2))),
    ("(c)(ii)", p("The standard entropy change of the reaction is " + M + "182 J mol" + sup(M + "1") + " K" + sup(M + "1") + ".") +
                p("Explain the significance of its sign with respect to the reaction. " + mk(1))),
    ("(c)(iii)", p("Calculate the Gibbs free energy of the Diels-Alder reaction. Hence, predict the spontaneity of the reaction at 298 K. " + mk(2))),
    ("(d)", p("Polydienes, formed by polymerisation of conjugated dienes, are widely used in synthetic rubber production due to their flexible structure.") +
            p("Polybutadiene is an example of a long polymer chain formed by linking many buta-1,3-diene monomers. Polybutadiene exists in " + i("cis") +
              "-1,4 and " + i("trans") + "-1,4 forms. " + i("Cis") + "-1,4-polybutadiene is shown in Fig 4.2.") +
            FIG + cap("Fig 4.2") +
            p("Draw " + b("two") + " repeat units of " + i("trans") + "-1,4-polybutadiene. " + mk(2))),
    ("(e)", p("Buta-1,3-diene is more stable than buta-1,2-diene, which is a non-conjugated diene.") + FIG),
    ("(e)(i)", p("Complete Table 4.1 by identifying the number of carbon atoms that are sp and sp" + sup(2) + " hybridised in buta-1,2-diene. " + mk(1)) +
               cap("Table 4.1") +
               table(tr(td("sp hybridised carbon"), td("")),
                     tr(td("sp" + sup(2) + " hybridised carbon"), td("")),
                     tr(td("sp" + sup(3) + " hybridised carbon"), td("1")))),
    ("(e)(ii)", p("On Fig 4.3, draw the arrangement of p orbitals for all the carbon atoms in buta-1,2-diene. " + mk(1)) + FIG + cap("Fig 4.3")),
    ("(e)(iii)", p("Hence, suggest why buta-1,2-diene is not a conjugated diene. " + mk(1))),
])

# ---------------------------------------------------------------- Q5  (14)
C3H12 = "C" + sub(7) + "H" + sub(12) + "O" + sub(2)
Q[5] = dict(marks=14, intro=[
    p("Lignocellulose is an abundant plant material typically found in agricultural waste such as fruit peels. Through Acetone–Butanol–Ethanol (ABE) "
      "fermentation, bacteria can ferment lignocellulose to produce a mixture of propanone (acetone), butan-1-ol, and ethanol. These products are biofuels.")], parts=[
    ("(a)", p("After ABE fermentation, organic solvents are used to separate the mixture of products. Common organic solvents include unsaturated alcohols, "
             "such as oleyl alcohol, C" + sub(18) + "H" + sub(35) + "OH. Butan-1-ol concentrates in the organic phase while ethanol stays in the aqueous phase. "
             "Propanone distributes between both phases.")),
    ("(a)(i)", p("By considering the structure of propanone and the intermolecular forces of attraction it can form with both water and oleyl alcohol, "
                 "explain why propanone can be found in both aqueous and organic phase. " + mk(2))),
    ("(a)(ii)", p("Describe a simple chemical test to confirm that butan-1-ol obtained in the organic phase is not contaminated with propanone. State the observations. " + mk(2))),
    ("(b)", p("Gas stripping is a technique used to recover volatile organic compounds like propanone and ethanol from the aqueous phase.") +
            p("In this process, nitrogen gas is bubbled through the aqueous phase at the fermentation temperature of 35 °C. At 35 °C, some of the organic "
              "molecules vapourise, changing from liquid phase to gas phase. The stream of nitrogen gas carries these gaseous organic molecules and is "
              "passed through a condenser to collect the liquid products.") +
            p("Table 5.1 shows the enthalpy change of vapourisation, " + DH_VAP + ", at 35 °C and boiling points of ethanol, propanone and water.") +
            cap("Table 5.1") +
            table(tr(th(""), th(DH_VAP + " / kJ mol" + sup(M + "1")), th("Boiling Point / °C")),
                  tr(td("Ethanol"), td("+38.6"), td("78")),
                  tr(td("Propanone"), td("+29.1"), td("56")),
                  tr(td("Water"), td("+40.7"), td("100")))),
    ("(b)(i)", p("Explain the difference in boiling point between water and ethanol. " + mk(1))),
    ("(b)(ii)", p("Using the information in Table 5.1, identify the product that is first collected from gas stripping of the ABE aqueous phase at 35 °C. "
                  "Explain your answer briefly. " + mk(1))),
    ("(b)(iii)", p("Using the information provided, give an advantage and a disadvantage of gas stripping instead of distillation to obtain propanone and "
                   "ethanol from the aqueous phase.") + p("Advantage:") + p("Disadvantage: " + mk(2))),
    ("(c)", p("In the presence of a catalytic amount of NaOH(aq), propanone obtained from ABE fermentation can undergo the aldol reaction to form "
              "diacetone alcohol, an important feedstock for many industrial applications.") + FIG +
            p("The three stages of aldol reaction are described in Table 5.2.") + cap("Table 5.2") + FIG),
    ("(c)(i)", p("Complete Table 5.2 by adding the balanced equation to represent stage 3. " + mk(1))),
    ("(c)(ii)", p("Draw three curly arrows on the equation in " + b("stage 2") + " of Table 5.2 to complete the mechanism. Show all relevant dipoles in your answer. " + mk(2))),
    ("(c)(iii)", p("Compound " + b("T") + ", " + C3H12 + ", undergoes an aldol reaction to form two different compounds " + b("U") + " and " + b("V") + ".") + FIG +
                 p("Draw the structure of " + b("T") + ". " + mk(1))),
    ("(c)(iv)", p("Predict which compound, " + b("U") + " or " + b("V") + ", is the minor product formed in smaller amounts. Explain your answer. " + mk(1))),
    ("(d)", p("Suggest why the biofuels offer significant greenhouse gas reductions compared to fossil fuels, despite releasing carbon dioxide into the "
              "atmosphere when combusted. " + mk(1))),
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
EXTRA_TEXT = {(2, "(a)(ii)"): "energy",
              (3, None): "acid hydrolysis X A B D CH3COOH HO OH COOH",
              (3, "(b)"): "step 1 multiple steps CH3COCl H2O CH3COOH HCl Cl CH3 O H",
              (3, "(b)(iv)"): "[ethanoyl chloride] time",
              (4, None): "buta-1,3-diene",
              (4, "(b)(ii)"): "energy / kJ mol-1",
              (4, "(c)"): "heat",
              (4, "(d)"): "polymerisation cis-1,4-polybutadiene n",
              (4, "(e)"): "buta-1,2-diene",
              (4, "(e)(ii)"): "C C C H H H CH3",
              (5, "(c)"): "NaOH(aq) diacetone alcohol stage description of stage equation reaction of propanone with OH- to make an enolate ion, Q "
                          "addition reaction of Q with propanone to form R protonation of R with water to form diacetone alcohol O OH",
              (5, "(c)(iii)"): "T U V NaOH(aq) C7H12O2 O OH"}

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
