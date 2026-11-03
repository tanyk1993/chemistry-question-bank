"""Hand transcription of A Level (SEAB) 9729/03 Oct/Nov 2025 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as build_alevel_p3.py, i.e. what
gen_parts_migration.py reads).
Run from the repo root:  python3 ingest/build_alevel25_p3.py <outdir>

Paper: 5 structured questions. Section A = Q1-Q3 (answer all), Section B = Q4-Q5 (answer one).
Totals printed on the paper: Q1 18, Q2 19, Q3 23, Q4 20, Q5 20 (100 marks in the bank, 80 as sat).

Conventions (see claude/style-guide.md and build_alevel_p3.py / build_alevel25_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder; a "Fig. n.n" / "Table n.n" caption is typed as a
    centred bold p.c; a label that is part of the drawing itself (a compound name, "step 1", "Z") is baked
    into the snip, not typed;
  * answer lines and empty answer boxes are NOT reproduced;
  * asset slot = part label without brackets ('f', 'fii').
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SEAB", "H2", "P3", 2025
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
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
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
Ka, Kb, Kc, Kw = K + sub("a"), K + sub("b"), K + sub("c"), K + sub("w")
MDM = "mol dm" + sup(M + "3")
DB = i("Data Booklet")
DH = "Δ" + i("H")
STD = '<span class="pl-sym">⦵</span>'
E0 = i("E") + sup("⦵")
ECELL = i("E") + '<span class="stk post"><span>%s</span><span>cell</span></span>' % STD
HALF = frac("1", "2")
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html)])

# ---------------------------------------------------------------- Q1
t11 = table(tr(th("indicator"), th("pH range")),
            tr(td("methyl violet"), td("0.0–1.6")),
            tr(td("methyl red"), td("4.4–6.2")),
            tr(td("metacresol purple"), td("7.4–9.0")),
            tr(td("indigo carmine"), td("11.6–13.0")))
Q[1] = dict(marks=18, intro=[], parts=[
    ("(a)", p("Electronegativity values can be used to predict the polarity of a covalent bond.")),
    ("(a)(i)", p("Define electronegativity. " + mk(1))),
    ("(a)(ii)", p("A molecule of carbonyl sulfide, OCS, is similar to a molecule of " + chem("CO2") +
                  ". Both have a central carbon atom and a linear shape.") +
                p("Deduce the polarity of the molecules OCS and " + chem("CO2") + ". Explain your answer. " + mk(2))),
    ("(b)(i)", p("Sketch the titration curve for the pH changes during the addition of an excess of a weak acid to a strong base. "
                 "Label the axes, and include pH 7 on the " + i("y") + "-axis. " + mk(2))),
    ("(b)(ii)", p("Table 1.1 shows information about four indicators.") + cap("Table 1.1") + t11 +
                p("State which of the four indicators in Table 1.1 is most suitable for a weak acid–strong base titration. Explain why. " + mk(1))),
    ("(c)", p("The value of the acid dissociation constant, " + Ka + ", for chloric(I) acid, HClO, is 2.95 × 10" + sup(M + "8") + " at 298 K.") +
            p("25.00 cm" + sup("3") + " of 0.500 " + MDM + " NaOH(aq) is added to a beaker.") +
            p("32.75 cm" + sup("3") + " of 0.400 " + MDM + " HClO is added to this beaker.") +
            eqn(chem("HClO + NaOH") + " → " + chem("NaClO + H2O")) +
            p("Calculate the pH of the resulting mixture in the beaker. " + mk(3))),
    ("(d)", p("Define standard cell potential, " + ECELL + ". Include a description of standard conditions in your answer. " + mk(2))),
    ("(e)", p("An electrochemical cell is set up to measure the " + ECELL + " between the " + chem("Fe^2+^(aq)") + "/Fe(s) electrode and the " +
              chem("O2(g)") + "/OH" + sup(M) + "(aq) electrode.") +
            p("Draw a labelled diagram of this electrochemical cell set-up.") +
            p("Include all necessary substances and relevant pieces of apparatus.") +
            p("It is " + b("not") + " necessary to state conditions used. " + mk(3))),
    ("(f)", p("The exposure of iron to oxygen in the presence of water leads to rusting of iron.") +
            p("Rusting can be simplified into two stages by considering the reactions taking place in droplets of water on the surface of iron.") +
            p("In stage 1, Fe atoms are converted to " + chem("Fe^2+^") + " ions in the presence of " + chem("O2") + " and " + chem("H2O") +
              " to form iron(II) hydroxide, " + chem("Fe(OH)2") + ".") +
            p("In stage 2, " + chem("Fe(OH)2") + " reacts with more oxygen to form rust, " + chem("Fe2O3") + "•" + chem("H2O") + ".") +
            p("Magnesium or zinc blocks can be attached to the bottom of iron boats to prevent rusting in sea water.")),
    ("(f)(i)", p("Use standard electrode potential, " + E0 + ", values from the " + DB + " to calculate " + ECELL + " for stage 1.") +
               p("Write an overall equation for stage 1. " + mk(2))),
    ("(f)(ii)", p("Use " + E0 + " values from the " + DB + " to evaluate which metal, magnesium or zinc, works best to prevent rusting of iron boats. "
                  "Explain your answer. " + mk(1))),
    ("(g)", p(chem("Fe(OH)2") + " is also formed as a green precipitate by the reaction of " + chem("Fe^2+^(aq)") + " with OH" + sup(M) + "(aq).") +
            p(chem("Fe(OH)2") + " slowly turns brown on standing in moist air to form iron(III) hydroxide, " + chem("Fe(OH)3") + ".") +
            p("Construct an equation for the conversion of " + chem("Fe(OH)2") + " to " + chem("Fe(OH)3") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q2
CU63, CU65 = sup("63") + "Cu", sup("65") + "Cu"
t21 = table(tr(th(""), th("relative isotopic mass"), th("percentage abundance")),
            tr(td(CU63), td("62.930"), td("69.15")),
            tr(td(CU65), td("64.928"), td("30.85")))
Q[2] = dict(marks=19, intro=[], parts=[
    ("(a)", p("State " + b("two") + " basic assumptions of the kinetic theory as applied to an ideal gas. " + mk(2))),
    ("(b)", p("A given mass of an ideal gas is compressed in a closed container at a constant temperature.") +
            p("Sketch a graph to show how the pressure of this gas varies with " + frac("1", "volume") + " at constant temperature. " + mk(1))),
    ("(c)", p("4.00 g of " + chem("O2") + " and 4.00 g of " + chem("N2") + " are mixed in a sealed container.") +
            p("Calculate the total volume of the gas mixture in cm" + sup("3") + " at 750 kPa and a temperature of 40 °C.") +
            p("Assume both " + chem("O2") + " and " + chem("N2") + " behave like ideal gases. " + mk(2))),
    ("(d)", p("A beam of charged particles is deflected by an electric field.") +
            p("The angle of deflection of a charged particle through an electric field is directly proportional to its charge / mass ratio.")),
    ("(d)(i)", p("State " + b("two") + " ways the behaviour of a beam of protons in an electric field differs from that of a beam of electrons. " + mk(2))),
    ("(d)(ii)", p("A sample of the isotope " + CU63 + " is vapourised, ionised and passed through an electric field.") +
                p("A beam of " + CU63 + sup("+") + " shows an angle of deflection of +5.5°.") +
                p("The experiment is repeated using a beam of " + sup("19") + "F" + sup(M) + " particles under the same conditions.") +
                p("Calculate the angle of deflection shown by the " + sup("19") + "F" + sup(M) + " particles. " + mk(1))),
    ("(d)(iii)", p("Define relative isotopic mass. " + mk(1))),
    ("(d)(iv)", p("Copper has two isotopes, " + CU63 + " and " + CU65 + ".") + cap("Table 2.1") + t21 +
                p("Use the data in Table 2.1 to calculate the relative atomic mass of copper to two decimal places. " + mk(1))),
    ("(e)", p("Describe " + b("two") + " similarities and " + b("one") + " difference between 1s and 2s orbitals. " + mk(3))),
    ("(f)", p("Photoelectron spectroscopy (PES) can be used to determine the relative energies of electrons in atoms.") +
            p("A typical PES spectrum shows peaks at different binding energies, which is the energy required to remove electrons from atoms. "
              "Electrons in the same subshell have the same binding energy.") +
            p("On a PES spectrum:") +
            ul("binding energy increases in magnitude from " + b("right to left") + " on the " + i("x") + "-axis",
               "each peak corresponds to electrons in a different subshell",
               "the height of each peak is proportional to the number of electrons lost.") +
            p("Fig. 2.1 shows the PES spectrum for lithium.") + FIG + cap("Fig. 2.1") +
            p("PES is also performed on a sample of nitrogen and a sample of boron.")),
    ("(f)(i)", p("Draw the PES spectrum expected for nitrogen using similar axes to that shown in Fig. 2.1.") +
               p("Clearly label the subshell and ratio of the peak heights. You do " + b("not") + " need to label the binding energy value for each peak. " + mk(2))),
    ("(f)(ii)", p("Suggest why the binding energy of the 1s subshell electrons of boron is smaller in magnitude than that of nitrogen in the PES spectrum. " + mk(1))),
    ("(g)", p("Dipeptides and proteins can be hydrolysed under certain conditions.") +
            p("Fig. 2.2 shows a dipeptide that undergoes complete hydrolysis under acidic conditions.") + FIG + cap("Fig. 2.2") +
            p("Draw the structures of the two products formed in this hydrolysis. " + mk(3))),
])

# ---------------------------------------------------------------- Q3
t31 = table(tr(th(""), th(chem("MgCO3(s)")), th(chem("MgO(s)")), th(chem("CaCO3(s)")), th(chem("CaO(s)"))),
            tr(td(DH + sub("latt") + " / kJ mol" + sup(M + "1")), td(M + "3450"), td(M + "3790"), td(M + "3150"), td(M + "3400")))
t32 = table(tr(th(""), th(DH + " / kJ mol" + sup(M + "1"))),
            tr(td("enthalpy change of reaction for " + HALF + chem("Li2(g)") + " → " + chem("Li^+^(aq)") + " + e" + sup(M)), td("+50.0")),
            tr(td("enthalpy change of hydration of " + chem("Li^+^(g)")), td(M + "520")))
t33 = table(tr(th("test"), th("reaction"), th("organic compounds formed"), th("other information")),
            tr(td("1"), td(b("A") + " with alkaline " + chem("I2(aq)")),
               td("yellow precipitate " + b("B") + "<br>" + b("C") + ", " + chem("C11H12O3")),
               td(b("C") + " effervesces with " + chem("Na2CO3(aq)") + ".")),
            tr(td("2"), td(b("A") + " with an excess of " + chem("Br2(aq)")), td(b("D") + ", " + chem("C12H12Br4O2")), td("")),
            tr(td("3"), td(b("A") + " with an excess of hot, concentrated, acidified " + chem("KMnO4")),
               td(b("E") + ", " + chem("C9H10O3") + "<br>" + b("F") + ", " + chem("C3H4O3")),
               td(b("E") + " contains only one chiral carbon atom. " + b("E") + " and " + b("F") + " effervesce with " + chem("Na2CO3(aq)") + ".")),
            tr(td("4"), td(b("E") + " with " + chem("HNO3(aq)")), td(b("G") + ", " + chem("C9H9NO5")),
               td(b("G") + " effervesces with " + chem("Na2CO3(aq)") + ".")))
Q[3] = dict(marks=23, intro=[], parts=[
    ("(a)", p("The Group 2 carbonates, " + chem("MCO3") + ", decompose on heating as shown.") +
            eqn(chem("MCO3(s)") + " → " + chem("MO(s)") + " + " + chem("CO2(g)") + "      " + DH + sub("1")) +
            p("The standard enthalpy change for this decomposition reaction, " + DH + sub("1") + ", changes down the group.") +
            p("The change in " + DH + sub("1") + " can be predicted from the lattice energies, " + DH + sub("latt") +
              ", of the corresponding metal carbonates and metal oxides.") +
            p("Table 3.1 shows some lattice energies for the metal carbonates and metal oxides of magnesium and calcium.") +
            cap("Table 3.1") + t31),
    ("(a)(i)", p("State the trend in thermal stability of the Group 2 carbonates. Explain your answer. " + mk(3))),
    ("(a)(ii)", p("Define lattice energy. " + mk(1))),
    ("(a)(iii)", p("Use the information in Table 3.1 to predict how " + DH + sub("1") + " changes down the group. Explain your reasoning. " + mk(1))),
    ("(b)", p("Dilithium, " + chem("Li2") + ", consists of two lithium atoms covalently bonded together in the gas phase.") +
            cap("Table 3.2") + t32),
    ("(b)(i)", p("Use the data in Table 3.2 and data from the " + DB + " to calculate a value for the Li–Li bond energy. " + mk(2))),
    ("(b)(ii)", p("Suggest how the two lithium atoms covalently bond together in terms of orbital overlap. " + mk(1))),
    ("(c)", p("Most chemical reactions are accompanied by energy changes associated with the breaking and forming of chemical bonds.")),
    ("(c)(i)", p("Explain in terms of bond breaking and bond forming why energy changes of some reactions are exothermic. " + mk(1))),
    ("(c)(ii)", p(chem("O6") + " has a ring structure and contains only single O–O bonds.") +
                p("Considering the formation of " + chem("O2") + " from " + chem("O6") + ", use bond energies from the " + DB +
                  " to suggest why oxygen is more stable as " + chem("O2") + " rather than " + chem("O6") + ". " + mk(1))),
    ("(d)", p("State the relative ease of hydrolysis of acyl chlorides, alkyl chlorides and aryl chlorides. Explain your answer. " + mk(3))),
    ("(e)", p("Compound " + b("A") + ", " + chem("C12H14O2") + ", is a di-substituted benzene derivative.") +
            p(b("A") + " contains only one chiral carbon atom.") +
            p("A series of tests are carried out. Table 3.3 shows some organic compounds formed in each test.") +
            cap("Table 3.3") + t33 +
            p("For each test, state the types of reactions occurring.") +
            p("Use the information in Table 3.3 to suggest possible structures for " + b("A") + ", " + b("B") + ", " + b("C") + ", " + b("D") + ", " +
              b("E") + ", " + b("F") + " and " + b("G") + ". You may find it useful to determine the structures of " + b("B") + ", " + b("E") +
              " and " + b("F") + " first. " + mk(10))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=20, intro=[], parts=[
    ("(a)(i)", p("Define constitutional (structural) isomerism. " + mk(1))),
    ("(a)(ii)", p("Draw " + b("two") + " branched alkene constitutional (structural) isomers of " + chem("C5H10") + ". " + mk(2))),
    ("(a)(iii)", p("Describe the origin of " + i("cis") + "-" + i("trans") + " isomerism in alkenes. Explain your answer. " + mk(2))),
    ("(b)", p("Alkenes readily undergo reduction with hydrogen in the presence of a nickel catalyst.") +
            p("The reducing agent " + chem("LiAlH4") + " cannot reduce alkenes to alkanes.") +
            p(chem("LiAlH4") + " acts as a source of hydride ions, H" + sup(M) + ".") +
            p("Suggest why " + chem("LiAlH4") + " does " + b("not") + " reduce alkenes. " + mk(1))),
    ("(c)", p("Propene, " + chem("CH3CH=CH2") + ", undergoes electrophilic addition with iodine monobromide, IBr, to form a mixture of two organic products.") +
            p("Identify the major organic product from the reaction of propene with IBr. Explain your reasoning.") +
            p("Draw the mechanism to show the formation of the major organic product. Include all relevant lone pairs, dipoles, curly arrows and charges. "
              "Include the structure of the organic intermediate. " + mk(5))),
    ("(d)(i)", p("State the variation in the melting points of " + chem("P4") + ", " + chem("S8") + " and " + chem("Cl2") + ". Explain your answer. " + mk(3))),
    ("(d)(ii)", p("Explain why the boiling point of propan-1-ol, " + chem("CH3CH2CH2OH") + ", is much higher than the boiling point of dimethyl sulfide, " +
                  chem("CH3SCH3") + ". " + mk(2))),
    ("(e)", p("Hydrogen chloride can be oxidised to chlorine by the Deacon process.") +
            eqn(chem("4HCl(g) + O2(g)") + " ⇌ " + chem("2Cl2(g) + 2H2O(g)")) +
            p("0.175 mol of hydrogen chloride is added to 0.0500 mol of oxygen in a container with a volume of 3.50 dm" + sup("3") + ".") +
            p("The gas mixture is pressurised and left to reach equilibrium at constant temperature.") +
            p("At equilibrium, 72.0% of the hydrogen chloride has reacted.") +
            p("Calculate the " + Kc + " for this equilibrium. Include its units. " + mk(4))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=20, intro=[], parts=[
    ("(a)", p("Hydrogen bromide gas decomposes on heating to its constituent elements.")),
    ("(a)(i)", p("Write an equation for this decomposition. Include an observation. " + mk(1))),
    ("(a)(ii)", p("State the trend in thermal stability of the Group 17 hydrides, HCl, HBr and HI. Explain your answer with reference to bond energy and orbital overlap. " + mk(2))),
    ("(b)", p(chem("H2X") + " is a strong dibasic acid.") +
            p("Calculate the pH of a 0.0280 " + MDM + " " + chem("H2X") + " solution. " + mk(1))),
    ("(c)", p("An aqueous solution of 1.00 × 10" + sup(M + "7") + " " + MDM + " HCl has a pH of 6.69 instead of a pH of 7.00 at 298 K.") +
            p("Suggest why. " + mk(1))),
    ("(d)", p("The ionic product of pure water, " + Kw + ", is 2.93 × 10" + sup(M + "15") + " at 283 K.")),
    ("(d)(i)", p("State how the " + Kw + " varies with increasing temperature. Explain your reasoning. " + mk(1))),
    ("(d)(ii)", p("Calculate the pH of pure water at 283 K. " + mk(1))),
    ("(e)", p("Potassium cyanide, KCN, is a weak base.") +
            p("The value for " + Kb + " of KCN is 2.04 × 10" + sup(M + "5") + " at 298 K.")),
    ("(e)(i)", p("When KCN is added to water, " + chem("CN^-^") + " ions are released and an acid–base equilibrium is set up.") +
               p("Write an ionic equation for the acid–base equilibrium reaction. " + mk(1))),
    ("(e)(ii)", p("Calculate the mass of KCN in mg to make 50 cm" + sup("3") + " KCN(aq) of pH 10.7 at 298 K. " + mk(4))),
    ("(f)(i)", p("Potassium cyanide is used in the chemical synthesis of lactic acid, " + chem("CH3CH(OH)CO2H") + ".") +
               p("This synthesis produces two enantiomers of lactic acid. Lactic acid contains only one chiral carbon atom.") +
               p("Draw the three-dimensional structures of the two enantiomers of lactic acid. " + mk(2))),
    ("(f)(ii)", p("Vitamin D" + sub("3") + " also contains chiral carbon atoms. The structure of vitamin D" + sub("3") + " is shown.") + FIG +
                p("State the number of chiral carbon atoms present in one molecule of vitamin D" + sub("3") + ". " + mk(1))),
    ("(g)", p("Compound " + b("Z") + " is a useful building block in organic synthesis. It can be synthesised from 1-phenylethanone in three steps as shown in Fig. 5.1.") +
            p("You may assume that the carbonyl substituent in 1-phenylethanone cannot be oxidised.") + FIG + cap("Fig. 5.1")),
    ("(g)(i)", p("Suggest structures for the organic compounds " + b("X") + " and " + b("Y") + ". " + mk(2))),
    ("(g)(ii)", p("Suggest reagents and conditions for each of the steps 1, 2 and 3. " + mk(3))),
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
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|V\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b|mg\b))", r"\1" + NB, h)
    h = re.sub(r"\b(mol|kJ|kg) (?=(?:dm|mol|kg)\b)", r"\1" + NB, h)
    h = re.sub(r"</sup> (?=(?:atm|dm|mol|kPa)\b)", "</sup>" + NB, h)
    h = re.sub(r"(\d) × (?=10)", r"\1" + NB + "×" + NB, h)
    return h

# ---------------------------------------------------------------- assemble
def strip(h):
    h = re.sub(r'<span class="frac"><span class="fnum">(.*?)</span><span class="fden">(.*?)</span></span>',
               lambda m: "%s/%s" % (re.sub(r"<[^>]+>", "", m.group(1)), re.sub(r"<[^>]+>", "", m.group(2))), h)
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
