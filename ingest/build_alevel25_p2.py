"""Hand transcription of A Level (SEAB) 9729/02 Oct/Nov 2025 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as extract_parts, i.e. what
gen_parts_migration.py reads).
Run from the repo root:  python3 ingest/build_alevel25_p2.py <outdir>

Conventions (see claude/style-guide.md; same as build_alevel_p2.py for 2024):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('cii'), 'b2' for a second figure in the same part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "SEAB", "H2", "P2", 2025
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
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
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
SN1, SN2 = "S" + sub("N") + "1", "S" + sub("N") + "2"
FE2, FE3 = ion("Fe", "2+"), ion("Fe", "3+")
HALF = frac("1", "2")

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html)])

# ---------------------------------------------------------------- Q1
ALCL3 = "A" + L + "C" + L + sub(3)
AL2CL6 = "A" + L + sub(2) + "C" + L + sub(6)
NH4CL = "NH" + sub(4) + "C" + L
PCL4P = "PC" + L + sub(4) + sup("+")
PCL6M = "PC" + L + sub(6) + sup(M)
Q[1] = dict(marks=12, intro=[p("Aluminium and phosphorus react separately with chlorine gas to form solid chlorides.")], parts=[
    ("(a)", p("A beaker containing " + ALCL3 + " is placed next to some concentrated NH" + sub(3) + ". When drops of water are added to the " + ALCL3 +
              ", white fumes containing " + NH4CL + " are observed.")),
    ("(a)(i)", p("Write an equation for the reaction of water and " + ALCL3 + ". " + mk(1))),
    ("(a)(ii)", p("Name the type of reaction that occurs when water is added to " + ALCL3 + ". " + mk(1))),
    ("(b)", p(NH4CL + " can be formed by adding the base NH" + sub(3) + "(g) to HC" + L + "(g).") +
            p("Identify the type of base present in this reaction. Explain your reasoning. " + mk(2))),
    ("(c)", p("When solid aluminium chloride, " + ALCL3 + ", is heated under pressure, it melts and " + AL2CL6 + " is produced.") +
            p("Draw a ‘dot-and-cross’ diagram of one molecule of " + AL2CL6 + " to show the arrangement of outer shell electrons.") +
            p("Represent electrons from aluminium as ×. Represent electrons from chlorine as •. " + mk(2))),
    ("(d)", p("When " + AL2CL6 + "(l) is heated, it vapourises and both " + AL2CL6 + "(g) and " + ALCL3 + "(g) are produced.") +
            p("An equilibrium between " + AL2CL6 + "(g) and " + ALCL3 + "(g) is set up in a closed system at a temperature of " + i("T") + "°C.") +
            eqn(AL2CL6 + "(g) ⇌ 2" + ALCL3 + "(g)")),
    ("(d)(i)", p("Suggest the effect, if any, on the amount of " + ALCL3 + " present in the equilibrium mixture when the temperature is increased. Explain your answer. " + mk(3))),
    ("(d)(ii)", p("Suggest the effect, if any, on the equilibrium constant, " + K + sub("p") + ", when the pressure is increased and the temperature of the mixture remains at " +
                  i("T") + "°C. " + mk(1))),
    ("(e)", p("Phosphorus(V) chloride exists as a solid that contains " + PCL4P + " and " + PCL6M + " at room temperature and pressure.")),
    ("(e)(i)", p("Predict the shape of " + PCL4P + ". " + mk(1))),
    ("(e)(ii)", p("Predict the bond angle of " + PCL6M + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q2
S2O8 = "S" + sub(2) + "O" + sub(8) + sup("2" + M)
SO4 = "SO" + sub(4) + sup("2" + M)
IM = "I" + sup(M)
Q[2] = dict(marks=9, intro=[], parts=[
    ("(a)", p("When a sample of the non-metal sulfur and the metal iron are heated together, iron sulfide is made.")),
    ("(a)(i)", p("Covalent bonds are present between the atoms in an S" + sub(8) + " molecule.") +
               p("Describe a covalent bond. " + mk(1))),
    ("(a)(ii)", p("Draw a labelled diagram to show the bonding present in solid iron. " + mk(2))),
    ("(b)", p("Greigite is a mineral of iron sulfide. It contains both " + FE2 + " and " + FE3 + ".") +
            p("A 25.00 g sample of greigite is made of 18.86% by mass of " + FE2 + " and 37.73% by mass of " + FE3 + ".") +
            p("Deduce the oxidation number of sulfur in the sample. " + mk(2))),
    ("(c)", p(FE2 + "(aq) is a catalyst for the reaction between " + S2O8 + "(aq) and " + IM + "(aq). Without the catalyst, they react together slowly "
              "because the activation energy for the reaction is very high.") +
            eqn("reaction 1   " + S2O8 + " + 2" + IM + " → 2" + SO4 + " + I" + sub(2))),
    ("(c)(i)", p("Explain why the activation energy for reaction 1 is very high. " + mk(1))),
    ("(c)(ii)", p("Identify the type of catalytic behaviour shown by " + FE2 + "(aq) in reaction 1. " + mk(1))),
    ("(c)(iii)", p("Write " + b("two") + " equations to show how " + FE2 + "(aq) acts as a catalyst for reaction 1. " + mk(2))),
])

# ---------------------------------------------------------------- Q3
FEH2O6 = "[Fe(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+")
Q[3] = dict(marks=11, intro=[p("Iron behaves as a typical transition element.")], parts=[
    ("(a)", p("Explain why iron is described as a transition element. " + mk(1))),
    ("(b)", p("Complete Fig. 3.1 to show the arrangement of electrons in " + FE3 + "(g).") + FIG + c(b("Fig. 3.1") + " " + mk(1))),
    ("(c)", p("The shapes of the five 3d orbitals are shown in Fig. 3.2.") + FIG + cap("Fig. 3.2")),
    ("(c)(i)", p("Draw labelled diagrams to show the energy levels of these five 3d orbitals, " + b("A") + " – " + b("E") + ", in:") +
               ul(FE3 + " as an isolated gaseous species",
                  FE3 + " in the octahedral complex ion " + FEH2O6 + " present in " + FE3 + "(aq).") +
               p(mk(2))),
    ("(c)(ii)", p("State and explain how the energy levels of the 3d orbitals in " + FE3 + "(g) compares with that of " + FE3 + "(aq). " + mk(3))),
    ("(d)", p("When colourless NaSCN(aq) is added to " + FEH2O6 + ", one water ligand only is replaced by one thiocyanate anion, SCN" + sup(M) +
              ", to produce a coloured complex ion.")),
    ("(d)(i)", p("Predict the formula of the complex ion made on addition of NaSCN. " + mk(1))),
    ("(d)(ii)", p("Explain why complexes containing " + FE3 + " are coloured. " + mk(3))),
])

# ---------------------------------------------------------------- Q4
t41 = table(tr(th(""), th("nicotinamide")), tr(td("σ bonds"), td("")), tr(td("π bonds"), td("")))
Q[4] = dict(marks=19, intro=[], parts=[
    ("(a)", p("Phenylamine is made from benzene in a three-step process as shown in Fig. 4.1.") + FIG + cap("Fig. 4.1")),
    ("(a)(i)", p("Describe the reagents and conditions required for step 1. " + mk(1))),
    ("(a)(ii)", p("Write an equation to describe the reaction to produce " + b("salt F") + " in step 2. Represent hydrogen from the reducing agent as [H]. " + mk(2))),
    ("(b)", p("Phenylamine reacts with H" + sub(2) + "(g) in the presence of a nickel catalyst to produce " + b("G") + ".") + FIG +
            p("Write an equation for this reaction. " + mk(1))),
    ("(c)", p("A pyridine molecule is made from a ring of 5 carbon atoms and 1 nitrogen atom joined by six covalent bonds. The bonding is similar to that in benzene. "
              "Both rings have six π electrons.") + FIG + cap("Fig. 4.2")),
    ("(c)(i)", p("Identify the hybridisation of the carbon atoms in the pyridine molecule shown in Fig. 4.2. " + mk(1))),
    ("(c)(ii)", p("The nitrogen atom in pyridine undergoes the same type of hybridisation as the carbon atoms.") +
                p("Complete Fig. 4.3 to show all the valence electrons in the orbitals of carbon and nitrogen atoms in pyridine that are " + b("not") +
                  " involved in the formation of σ bonds.") + FIG + c(b("Fig. 4.3") + " " + mk(2))),
    ("(c)(iii)", p("Describe how delocalisation of electrons in the pyridine ring occurs. " + mk(1))),
    ("(c)(iv)", p("Suggest why pyridine is less reactive than benzene in electrophilic substitution reactions. " + mk(2))),
    ("(d)", p("The pyridine ring shown in Fig. 4.2 is found in nicotinamide and niacin. Both are types of vitamin B3, which is essential in a balanced diet.")),
    ("(d)(i)", p("State the molecular formula of niacin.") + FIG + c(mk(1))),
    ("(d)(ii)", p("Complete Table 4.1 to show the number of σ bonds and π bonds present in a nicotinamide molecule.") + FIG +
                cap("Table 4.1") + t41 + c(mk(2))),
    ("(d)(iii)", p("State the reagents and conditions required to convert nicotinamide into niacin in a single-step reaction.") + FIG + c(mk(1))),
    ("(e)", p("In plants and animals, niacin is used to produce two species that are represented as NAD" + sup("+") + " and NADH.") +
            p("The mechanism for the conversion of NAD" + sup("+") + " to NADH is shown in Fig. 4.4. In the pyridine ring structure in NAD" + sup("+") +
              ", the ring is shown as alternating single and double covalent bonds.") + FIG + cap("Fig. 4.4")),
    ("(e)(i)", p("Suggest the name of the mechanism for the reaction described in Fig. 4.4. " + mk(1))),
    ("(e)(ii)", p("The kinetics for the breakdown of ethanol using NAD" + sup("+") + " and enzyme " + b("J") + " was studied using a range of concentrations of NAD" +
                  sup("+") + ", enzyme " + b("J") + " and ethanol.") +
                p("On Fig. 4.5, sketch the shapes of the graphs that show the order of reaction with respect to both NAD" + sup("+") + " and ethanol is zero.") +
                FIG + c(b("Fig. 4.5") + " " + mk(2))),
    ("(e)(iii)", p("Describe and explain the difference, if any, in the magnitude of the rate constant for the catalysed and uncatalysed reactions. " + mk(2))),
])

# ---------------------------------------------------------------- Q5
MG2 = "2Mg(s) + O" + sub(2) + "(g) → 2MgO(s)"
Q[5] = dict(marks=7, intro=[], parts=[
    ("(a)", p("The effect of increasing temperature on " + DEL + i("G") + " per mole of O" + sub(2) + " reacted for reaction 2 is shown in Fig. 5.1.") +
            eqn("reaction 2   " + MG2) + FIG + cap("Fig. 5.1")),
    ("(a)(i)", p("State the equation that relates the value of " + DEL + i("G") + " to the values of " + DEL + i("S") + " and " + DEL + i("H") + ". " + mk(1))),
    ("(a)(ii)", p("Use Fig. 5.1 to deduce the value of " + DEL + i("S") + " for reaction 2. Include relevant units in your answer. " + mk(2))),
    ("(a)(iii)", p("On Fig. 5.1, show how the value for " + DEL + i("H") + " for reaction 2 can be determined. " + mk(1))),
    ("(b)", p("The effect of increasing temperature on " + DEL + i("G") + " per mole of O" + sub(2) + " reacted for reaction 3 and reaction 4 is shown in Fig. 5.2.") +
            eqn("reaction 3   2Cu(s) + O" + sub(2) + "(g) → 2CuO(s)") +
            eqn("reaction 4   " + frac("4", "3") + "A" + L + "(s) + O" + sub(2) + "(g) → " + frac("2", "3") + "A" + L + sub(2) + "O" + sub(3) + "(s)") +
            FIG + cap("Fig. 5.2") +
            p("Hess’ Law can be used to construct simple cycles involving values for Gibbs free energy change, " + DEL + i("G") +
              ", in a similar way to cycles involving values for " + DEL + i("H") + ".") +
            p("Using the data shown about reaction 3 and reaction 4 in Fig. 5.2, calculate the value of " + DEL + i("G") +
              " for the formation of 1 mol of Cu when CuO reacts with an excess of A" + L + " at 300 K. " + mk(3))),
])

# ---------------------------------------------------------------- Q6
def eq6(lhs_hc, o2, co2, h2o):
    """C-xHy + O2 -> CO2 + H2O row; o2 is (integer, half?) """
    n, half = o2
    o2s = str(n) + (HALF if half else "") + "O" + sub(2)
    return lhs_hc + " + " + o2s + " → " + str(co2) + "CO" + sub(2) + " + " + str(h2o) + "H" + sub(2) + "O"
def hc(cn, hn, o=0): return "C" + sub(cn) + "H" + sub(hn) + ("O" + sub(o) if o else "")
t61 = table(tr(th(""), th("equation for complete combustion"), th("enthalpy change for complete combustion / kJ mol" + sup(M + "1")),
               th("energy released / kJ g" + sup(M + "1"))),
            tr(td("pentadecane"),  td(eq6(hc(15, 32), (23, 0), 15, 16)), td(M + "9942"),  td("46.90")),
            tr(td("hexadecane"),   td(eq6(hc(16, 34), (24, 1), 16, 17)), td(M + "10058"), td("44.50")),
            tr(td("heptadecane"),  td(eq6(hc(17, 36), (26, 0), 17, 18)), td(M + "10674"), td("44.48")),
            tr(td("octadecane"),   td(eq6(hc(18, 38), (27, 1), 18, 19)), td(M + "11290"), td("44.45")),
            tr(td("methyl ester " + b("L")), td(eq6(hc(17, 34, 2), (24, 1), 17, 17)), td(M + "10208"), td("37.81")),
            tr(td("methyl ester " + b("M")), td(eq6(hc(17, 32, 2), (24, 0), 17, 16)), td(M + "10096"), td("37.67")),
            tr(td("methyl ester " + b("N")), td(eq6(hc(19, 38, 2), (27, 1), 19, 19)), td(M + "11440"), td("38.39")))
Q[6] = dict(marks=8, intro=[
    p("Diesel contains a mixture of hydrocarbons that each contain between 15 and 25 carbon atoms."),
    p("Biodiesel can be used as a fuel in diesel engines instead of using diesel produced from crude oil. Biodiesel is produced from vegetable oils which are extracted from plants."),
    p("There are many advantages to using biodiesel instead of diesel produced from crude oil as a fuel, including:"),
    ul("biodiesel is a renewable resource", "a reduction in unburned fuel emissions", "a reduction in solid carbon emissions",
       "a reduction in CO emissions", "negligible SO" + sub(2) + " emissions."),
    p("To produce biodiesel, the vegetable oil is converted into methyl esters. Table 6.1 shows information on the complete combustion of four hydrocarbons "
      "that can be found in diesel produced from crude oil and three methyl esters found in biodiesel."),
    cap("Table 6.1"), t61],
  parts=[
    ("(a)", p("The methyl ester made from pentadecanoic acid and methanol is called methyl pentadecanoate.")),
    ("(a)(i)", p("Use the information in Table 6.1 to suggest the name for methyl ester " + b("L") + ". " + mk(1))),
    ("(a)(ii)", p("Draw the structure of methyl ester " + b("N") + ". " + mk(1))),
    ("(b)", p("Use information from Table 6.1 to explain why using biodiesel in diesel engines reduces the amount of unburned fuel, carbon monoxide gas and solid carbon "
              "emissions in the exhaust gases. " + mk(2))),
    ("(c)", p("Using information from Table 6.1, suggest " + b("one") + " disadvantage of using biodiesel instead of diesel as a fuel. " + mk(1))),
    ("(d)", p("Predict the effect, if any, on the amount of unburned fuel, carbon monoxide gas and solid carbon emissions with methyl esters that contain at least one "
              "carbon–carbon double bond compared to methyl esters with no carbon–carbon double bonds. Use data from Table 6.1 to support your answer. " + mk(2))),
    ("(e)", p("Suggest why scientists do " + b("not") + " describe the release of carbon dioxide into the atmosphere when biodiesel is burned as contributing to the "
              "enhanced greenhouse effect. " + mk(1))),
])

# ---------------------------------------------------------------- Q7
t71 = table(tr(th("bromoalkane"), th("relative rate of " + SN2 + " reaction")),
            tr(td("bromomethane"), td("200")), tr(td("bromoethane"), td("30")), tr(td("2-bromopropane"), td("0.03")))
CL = "C" + L
t72 = table(tr(th("chloroalkane"), th("order of rate of hydrolysis")),
            tr(td("CH" + sub(3) + "(CH" + sub(2) + ")" + sub(3) + CL), td("")),
            tr(td("(CH" + sub(3) + ")" + sub(3) + "C" + CL), td("")),
            tr(td("CH" + sub(3) + "CH" + sub(2) + "CH(CH" + sub(3) + ")" + CL), td("")))
t74 = table(tr(th("assumption"), th("predicted angle of rotation of plane-polarised light, " + i("z") + " / °"), th("reason for predicted angle")),
            tr(td("only " + SN1 + " occurs"), td(""), td("")),
            tr(td("only " + SN2 + " occurs"), td(""), td("")))
Q[7] = dict(marks=9, intro=[
    p("The nucleophilic substitution reactions of different halogenoalkanes can occur by " + SN1 + " reaction mechanisms, " + SN2 + " reaction mechanisms or both.")],
  parts=[
    ("(a)", p("Table 7.1 shows the relative rate of reaction for the " + SN2 + " reactions of three bromoalkanes with an excess of iodide ions. "
              "The same solvent and temperature are used in each reaction.") + cap("Table 7.1") + t71 +
            p("State the factor that determines why the " + SN2 + " reactions described in Table 7.1 occur at different rates. " + mk(1))),
    ("(b)", p("The relative rate of " + SN1 + " hydrolysis reactions of primary, secondary and tertiary chloroalkanes are investigated under the same reaction conditions.")),
    ("(b)(i)", p("Explain what determines the rate of hydrolysis in these " + SN1 + " reactions. " + mk(3))),
    ("(b)(ii)", p("Predict the order of the rate of hydrolysis for the " + SN1 + " reactions of the chloroalkanes shown in Table 7.2.") +
                p("Use ‘1’ to represent the fastest rate of hydrolysis, ‘2’ to represent the second fastest rate of hydrolysis and ‘3’ to represent the slowest rate of hydrolysis.") +
                cap("Table 7.2") + t72 + c(mk(1))),
    ("(c)", p("Pure samples of enantiomers are distinguishable by passing a beam of plane-polarised light through each sample. The angle that the plane is rotated is measured.") +
            p("2-bromooctane and octan-2-ol both exist as pairs of enantiomers. Table 7.3 describes the angle of rotation of plane-polarised light for pure samples of these enantiomers.") +
            cap("Table 7.3") + FIG +
            p("A sample of " + b("V") + " is added to an excess of NaOH(aq). When the hydrolysis reaction is complete, a beam of plane-polarised light is passed through the "
              "reaction mixture and the plane is rotated by " + i("z") + "°.") +
            p("Complete Table 7.4 to predict the final angle of rotation of plane-polarised light, " + i("z") + "°, after complete hydrolysis of " + b("V") +
              ". Give " + b("one") + " reason for each of the predicted angles. Assume that the reaction occurs via either " + SN1 + " or " + SN2 + ".") +
            cap("Table 7.4") + t74 + c(mk(4))),
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
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b))", r"\1" + NB, h)
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
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"\s+", " ", h).strip()

slot_for = lambda label, k: ("intro" if not label else label.replace("(", "").replace(")", "")) + ("" if k == 0 else str(k + 1))
rows, plan = [], []
for n in sorted(Q):
    d = Q[n]
    html_blocks = list(d["intro"])
    text_bits = [strip(" ".join(d["intro"]))]
    for label, h in d["parts"]:
        text_bits += [label, strip(h)]
        h = lead_inline(h)
        html_blocks.append('<div class="qpart"><span class="pl">%s</span> %s</div>' % (label, h))
    text_bits.append("[Total: %d]" % d["marks"])
    html = nbsp("\n".join(html_blocks))
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
