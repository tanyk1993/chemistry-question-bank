"""Hand transcription of RVHS 2026 H2 Prelim Paper 2 (9476/02, 5 structured, 75 marks) -> questions.json +
asset_plan.json. The school sent a binary .doc (converted with LibreOffice) plus a Word-exported PDF; the question text
is typed here from the two (they agree). Light typo/grammar fixes follow the standing defaults and are listed in the
handoff note. Same output contract as extract_parts, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_rvhs26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school RVHS --year 2026 --paper 2 --level H2

Conventions (claude/style-guide.md; same as build_njc26_p2.py / build_ri26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('cii'), 'intro' for the stem, 'b2' for a second figure in a part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "RVHS", "H2", "P2", 2026
FIG = '<div class="fig">figure</div>'
M = "\u2212"                              # minus sign U+2212
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
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def ion(sym, ch): return sym + sup(ch)
L = '<i class="el">l</i>'                  # element l
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "\u0394"
STD = sup('<span class="pl-sym">\u29b5</span>')
def dS(): return DEL + i("S") + STD
def dG(): return DEL + i("G") + STD
def dH(): return DEL + i("H")
def nuc(a, z, sym): return '<span class="stk"><span>%s</span><span>%s</span></span>%s' % (a, z, sym)
def conc(s): return "[" + s + "]"
H2O = "H" + sub(2) + "O"
CO2 = "CO" + sub(2)
HCO3 = "HCO" + sub(3) + sup(M)
CO3 = "CO" + sub(3) + sup("2" + M)
EM = "&emsp;"
ALPHA = "\u03b1"

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])
# ---------------------------------------------------------------- Q1
CL = "C" + L
HCL = "HC" + L
Q[1] = dict(marks=17, intro=[
    p("In coastal cities, volatile organic compounds (VOCs) released from industrial solvents mix with salty sea spray aerosols. "
      "Researchers have isolated a key chlorinated intermediate, compound " + b("P") + ", which acts as a precursor to hazardous photochemical smog.") + FIG], parts=[
    ("(a)", p("To track the decomposition of pollutants like compound " + b("P") + ", aerosol samples are subjected to intense heat to liberate their constituent halogen atoms as halide ions.")),
    ("(a)(i)", p("A liquid aerosol sample containing chloride ions is treated with excess aqueous silver nitrate, followed by dilute aqueous ammonia.") +
               p("State the observations and write a balanced ionic equation, with state symbols, for the reaction that occurs upon adding aqueous ammonia. " + mk(2))),
    ("(a)(ii)", p("Sea spray aerosols also carry traces of bromide and iodide ions. When hydrogen halides are regenerated in acidic upper atmospheric clouds, their stabilities vary.") +
                p("Describe and explain the trend in thermal stability of Group 17 hydrides from " + HCL + " to HI. Explain your answer with reference to orbital overlap. " + mk(2))),
    ("(b)", p("In humid environments, trapped halogenoalkanes undergo hydrolysis within the aqueous phase of the aerosol.") +
            p("Compound " + b("P") + " and two of its structural derivatives, " + b("Q") + " and " + b("R") + ", are monitored for their relative rates of hydrolysis.") + FIG +
            p("Arrange " + b("P") + ", " + b("Q") + " and " + b("R") + " in order of decreasing relative rate of hydrolysis.") +
            p("Explain your answer. " + mk(3))),
    ("(c)", p("Following a degradation sequence, compound " + b("P") + " forms an asymmetrical arene intermediate, compound " + b("S") + ".") + FIG +
            p("Compound " + b("S") + " is treated with a dilute solution of chlorine dissolved in an inert solvent at room temperature. "
              "Explain why monochlorination occurs selectively on one of the rings. " + mk(2))),
    ("(d)", p("In a laboratory setting, compound " + b("P") + " can be synthesised from methoxybenzene. This reaction requires a catalyst and a suitable reagent. "
              "You may assume that the OCH" + sub(3) + " group is inert.") + FIG +
            p("Draw the mechanism for the formation of compound " + b("P") + " from methoxybenzene, showing:") +
            ul("the generation of the electrophile", "the attack on the aromatic ring", "the formation of the substituted product") +
            p("Include all relevant lone pairs, curly arrows and charges. " + mk(3))),
    ("(e)", p("Unlike aromatic rings, an isolated alkane or aliphatic side chain undergoes a completely different type of halogenation.") +
            p("Compound " + b("T") + " reacts with bromine to yield three different mono-bromoalkanes.") + FIG),
    ("(e)(i)", p("Name the type of mechanism, and state the reagents and conditions required for this reaction to take place.") +
               p("Type of mechanism:") + p("Reagents and conditions: " + mk(2))),
    ("(e)(ii)", p("Experiments show that during such reactions, hydrogen atoms of the primary, secondary and tertiary carbons are replaced by bromine atoms at different rates, as shown in Table 1.1.") +
                cap("Table 1.1") +
                table(tr(th("reaction"), th("relative rate")), tr(td("primary"), td("1")), tr(td("secondary"), td("7")), tr(td("tertiary"), td("21"))) +
                p("Using the information in Table 1.1, draw the structures of the three mono-bromoalkanes and predict the relative ratio in which they are formed. " + mk(3))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=16, intro=[
    p("Dextromethorphan is a common over-the-counter cough medicine.") + FIG + cap("Fig. 2.1") +
    p("When a dextromethorphan molecule reacts with an acid like hydrobromic acid, HBr, a salt is formed. "
      "This salt is known as dextromethorphan hydrobromide monohydrate.")], parts=[
    ("(a)", p("In Fig. 2.1, circle the atom that reacts with HBr and name the shape about this atom in the salt produced. " + mk(2))),
    ("(b)", p("Explain why, in terms of forces of attraction between particles, the salt product dissolves easily in water. " + mk(2))),
    ("(c)", p(b("F") + " is a precursor in the synthesis of dextromethorphan. A reaction pathway to produce " + b("F") + " is shown in Fig. 2.2.") + FIG + cap("Fig. 2.2") +
            p("The conversion of " + b("A") + " to " + b("B") + " involves the use of Grignard reagent which has extensive uses in organic synthesis. An example is shown in Fig. 2.3.") + FIG + cap("Fig. 2.3")),
    ("(c)(i)", p("Draw the structures of " + b("A") + ", " + b("B") + ", " + b("C") + " and " + b("D") + ". " + mk(4)) +
               table(tr(td("<br><br><br><br><br><br>"), td("")), tr(th("A"), th("B")), tr(td("<br><br><br><br><br><br>"), td("")), tr(th("C"), th("D")))),
    ("(c)(ii)", p("State the reagent and condition for step 3. " + mk(1))),
    ("(d)", p("Compound " + b("D") + " is produced from cyanoacetic acid.") + FIG),
    ("(d)(i)", p("In step I, KOH(aq) acts as a strong base to deprotonate cyanoacetic acid and produces anion " + b("X") + ".") + FIG +
               p("Suggest why anion " + b("X") + " is stable. " + mk(1))),
    ("(d)(ii)", p("Draw a mechanism to show the reaction between anion " + b("X") + " and cyclohexanone in step I to form " + b("Y") + ", C" + sub(9) + "H" + sub(13) + "O" + sub(3) + "N. "
                  "Include all relevant lone pairs, dipoles, curly arrows and charges. " + mk(3))),
    ("(d)(iii)", p("In a separate experiment, when cyclohexanone is replaced with hexanal, the rate of step I increases.") + p("Explain this phenomenon. " + mk(2))),
    ("(d)(iv)", p("Explain why cyanoacetic acid is more acidic than butanoic acid in water. " + mk(1))),
])

# ---------------------------------------------------------------- Q3
Q[3] = dict(marks=18, intro=[
    p("Ammonia is an important inorganic substance used in the fertiliser and explosives industries."),
    p("Ammonia is mainly produced via the Haber Process:"),
    ceqn("3H" + sub(2) + "(g) + N" + sub(2) + "(g) ⇌ 2NH" + sub(3) + "(g)" + EM + EM + dH() + " = " + M + "92 kJ mol" + sup(M + "1"))], parts=[
    ("(a)", p("A mixture of H" + sub(2) + " and N" + sub(2) + " in a 3:1 molar ratio was introduced into a vessel with a volume of 5.00 dm" + sup(3) + ". The gas mixture was left to reach equilibrium at a constant temperature.") +
            p("At equilibrium, 30.0% of the nitrogen had reacted and the concentration of NH" + sub(3) + " was 0.320 " + MDM + ".")),
    ("(a)(i)", p("Calculate the equilibrium concentrations of H" + sub(2) + " and N" + sub(2) + ". " + mk(2))),
    ("(a)(ii)", p("Hence calculate the " + i("K") + sub("c") + " for this equilibrium. Include its units. " + mk(2))),
    ("(b)", p("Helium gas is added to the system at constant temperature and volume.")),
    ("(b)(i)", p("Explain the effect this will have on the composition of the reaction mixture. " + mk(2))),
    ("(b)(ii)", p("Predict how the value of " + i("K") + sub("c") + " will change. " + mk(1))),
    ("(c)(i)", p("The Haber process is typically carried out at 450 °C and 200 atm. Explain the conditions used for manufacturing ammonia. " + mk(2))),
    ("(c)(ii)", p("Explain why the activation energy of the process is high. " + mk(1))),
    ("(d)", p("The Haber Process is often catalysed using finely divided iron catalyst to achieve an economically viable rate of reaction.")),
    ("(d)(i)", p("State the electronic configuration of an iron atom. " + mk(1))),
    ("(d)(ii)", p("State and explain the characteristic of iron which allows it to function effectively as a catalyst in the Haber Process. " + mk(2))),
    ("(d)(iii)", p("Explain, with the aid of a labelled Boltzmann distribution diagram, the effect of a catalyst on a rate constant. " + mk(3))),
    ("(e)", p("Nitrogen atoms undergo the same type of hybridisation as carbon atoms.") +
            p("With reference to the hybridisation of the nitrogen atoms, explain if NH" + sub(3) + " or N" + sub(2) + " is a stronger ligand. " + mk(2))),
])

# ---------------------------------------------------------------- Q4
RA = "<sup>226</sup>Ra"
HE = nuc(4, 2, "He") + sup("2+")
Q[4] = dict(marks=11, intro=[
    p("The primary decay of radium-226 (" + RA + ") is an alpha decay process. It involves the emission of high-energy subatomic " + ALPHA + "-particles, " + HE +
      ", together with a new daughter element, nuclide " + b("J") + ". The " + ALPHA + "-particles gradually gain electrons from the environment to form stable helium gas."),
    ceqn(RA + " → nuclide " + b("J") + " + " + HE),
    ceqn(HE + " + 2e" + sup(M) + " → He"),
    p("The nuclide " + b("J") + " is highly unstable. Within 83 days, the nuclide " + b("J") + " undergoes a series of radioactive decays which include three other " + ALPHA + "-decays."),
    p("To investigate the decay of radium-226, scientists projected the remaining number of radium-226 atoms over several millennia, shown in Table 4.1."),
    cap("Table 4.1"),
    table(tr(th("Projected time / years"), th("Calculated number of " + RA + " atoms / × 10" + sup("20"))),
          tr(td("0"), td("5.12")), tr(td("800"), td("3.62")), tr(td("1600"), td("2.56")), tr(td("2400"), td("1.81")), tr(td("3200"), td("1.28"))),
    p("In 1911, Ernest Rutherford and Bertram Boltwood conducted a quantitative study on the radioactive decay of pure radium-226 (" + RA + "). "
      "A 192 mg sample of radium-226 was put into a device and the volume of the helium gas collected was measured."),
    p("Using modern day equipment, similar experiments using the same initial mass of radium-226 were conducted at 0 °C. Table 4.2 shows the measurements collected at 83 days."),
    cap("Table 4.2"),
    table(tr(th("Experiment"), th("Pressure, " + i("p") + " / × 10" + sup("5") + " Pa"), th("Volume, " + i("V") + " / × 10" + sup(M + "9") + " m" + sup("3"))),
          tr(td("1"), td("2.026"), td("3.274")), tr(td("2"), td("4.052"), td("1.623")))], parts=[
    ("(a)", ""),
    ("(a)(i)", p("Identify nuclide " + b("J") + ". Express your answer using standard isotopic notation (" + nuc("A", "Z", "X") + ", where A represents the nucleon number). " + mk(1))),
    ("(a)(ii)", p("If a beam containing these emitted " + ALPHA + "-particles is directed horizontally into an electric field generated between two oppositely charged vertical plates, state the path deflection observed. " + mk(1))),
    ("(b)", p("Using Table 4.1, deduce the order of reaction with respect to the decay of radium-226. " + mk(1))),
    ("(c)", ""),
    ("(c)(i)", p("State a property of helium gas necessary for it to approach ideal behaviour. " + mk(1))),
    ("(c)(ii)", p("Using Table 4.2, deduce whether the gas collected at 0 °C exhibits ideal behaviour. Explain your reasoning using relevant calculations, giving your answer to 1 decimal place. " + mk(2))),
    ("(d)", ""),
    ("(d)(i)", p("The total number of " + ALPHA + "-particles emitted from the 192 mg sample of radium-226 at 83 days is 1.88 × 10" + sup("17") + ".") +
               p("Using the data from experiment 1 in Table 4.2, calculate an experimental value for Avogadro’s constant. " + mk(2))),
    ("(d)(ii)", p("Comparing with the Avogadro’s constant in the Data Booklet, calculate the percentage error for your answer in (d)(i). " + mk(1))),
    ("(d)(iii)", p("Calculate the percentage of the 192 mg sample of radium-226 that has successfully undergone primary decay. " + mk(2))),
])
Q[4]["parts"] = [x for x in Q[4]["parts"] if x[1]]   # bare labels (a), (c), (d) only introduce sub-parts: dropped

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=13, intro=[
    p("The world’s oceans absorb approximately one-quarter of the carbon dioxide released into the atmosphere each year. Dissolved carbon dioxide participates in a series of "
      "acid–base equilibria known as the marine carbonate system, which plays an important role in regulating the pH of seawater."),
    p("The simplified equilibria are given below:"),
    p("Equilibrium 1" + EM + CO2 + "(g) ⇌ " + CO2 + "(aq)"),
    p("Equilibrium 2" + EM + CO2 + "(aq) + " + H2O + "(l) ⇌ " + HCO3 + "(aq) + H" + sup("+") + "(aq)" + EM + EM + K + sub("a1")),
    p("Equilibrium 3" + EM + HCO3 + "(aq) ⇌ " + CO3 + "(aq) + H" + sup("+") + "(aq)" + EM + EM + EM + K + sub("a2")),
    p("The pH of the sea water is impacted by the relative concentration of the dissolved inorganic carbon (DIC) species present. Fig. 5.1 shows the relative proportion of "
      + CO2 + "(aq), " + HCO3 + "(aq) and " + CO3 + "(aq) at different pH, at 25.0 °C.") + FIG + cap("Fig. 5.1"),
    p("Oceanographers routinely measure atmospheric carbon dioxide concentration, DIC concentrations, ocean surface pH and temperature to investigate changes to the marine carbonate system."),
    p("Table 5.1 shows some measurements for a seawater sample, S1, compared to the global mean. For atmospheric gases, 1 ppm = 10" + sup(M + "6") + " mol of " + CO2 + " per mol of dry air. "
      "Salinity is the concentration of dissolved salts."),
    cap("Table 5.1"),
    table(tr(th(""), th("annual mean 1985"), th("annual mean 2024"), th("seawater sample, S1")),
          tr(td("Ocean surface pH"), td("8.11"), td("8.04"), td("8.10")),
          tr(td("Atmospheric " + CO2 + " concentration / ppm"), td("346"), td("425"), td("430")),
          tr(td("Salinity / " + MDM), td("0.60"), td("0.60"), td("0.61")),
          tr(td("Surface temperature of water / °C"), td("–"), td("–"), td("29.7")))], parts=[
    ("(a)", ""),
    ("(a)(i)", p("The total concentration of the DIC species is 2.10 × 10" + sup(M + "3") + " " + MDM + ".") +
               p("Using Fig. 5.1, estimate the concentration of " + CO2 + "(aq), " + HCO3 + "(aq) and " + CO3 + "(aq) in sample S1. " + mk(1))),
    ("(a)(ii)", p("Explain how seawater resists pH change when a small amount of acid is added. " + mk(1))),
    ("(b)", p("The standard " + K + sub("a") + " values widely accepted by the NOAA Ocean Carbon Data System for standard surface seawater at 25.0 °C are given below.") +
            p(K + sub("a1") + " = 1.42 × 10" + sup(M + "6") + " " + MDM) + p(K + sub("a2") + " = 1.08 × 10" + sup(M + "9") + " " + MDM)),
    ("(b)(i)", p("Using Fig. 5.1, show how a value of " + K + sub("a2") + " may be obtained. " + mk(1))),
    ("(b)(ii)", p("Show that " + K + sub("a1") + " and " + K + sub("a2") + " are related by the following equation.") +
                ceqn(K + sub("a1") + K + sub("a2") + " = " + frac(conc(CO3) + conc("H" + sup("+")) + sup("2"), conc(CO2))) + p(mk(1))),
    ("(b)(iii)", p("Hence, calculate the concentration of " + CO2 + "(aq) in the seawater sample, S1. " + mk(2))),
    ("(c)", p("Henry’s Law states that the concentration of a dissolved gas is directly proportional to its atmospheric partial pressure.") +
            ceqn(conc(CO2) + " = " + i("k") + sub("H") + " × " + i("P") + sub("CO₂")) +
            p("where Henry’s law constant, " + i("k") + sub("H") + " = 0.0340 " + MDM + " atm" + sup(M + "1") + " at 25.0 °C.")),
    ("(c)(i)", p("A sample of pure water was subjected to the same atmospheric pressure as seawater sample, S1, for several days at 25.0 °C. "
                 "Calculate the concentration of dissolved " + CO2 + " in this sample of pure water. " + mk(2))),
    ("(c)(ii)", p("Considering the information provided in Table 5.1, predict how the concentration of dissolved " + CO2 + " in seawater sample, S1, will differ from the one calculated in (c)(i). "
                  "Explain your prediction. " + mk(2))),
    ("(d)", p("Calcification is the biological process where marine organisms extract dissolved ions from seawater to construct hard calcium carbonate shells, skeletons and structures. "
              "Calcification has a standard entropy change of +199 J mol" + sup(M + "1") + " K" + sup(M + "1") + " and standard enthalpy change of +12.1 kJ mol" + sup(M + "1") + " at 298 K.")),
    ("(d)(i)", p("The sign of " + dS() + " was initially thought to be negative. Explain why. " + mk(1))),
    ("(d)(ii)", p("Suggest why the sign of " + dS() + " for calcification is actually positive. " + mk(1))),
    ("(d)(iii)", p("Calculate " + dG() + " for calcification. " + mk(1))),
])
Q[5]["parts"] = [x for x in Q[5]["parts"] if x[1]]


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
    h = re.sub(r"(\d) (?=(?:°C|K\b|g\b|kg\b|kPa\b|bar\b|atm\b|cm<sup>|dm<sup>|mol\b|kJ\b|J\b|nm\b|ppm\b|mg\b))", r"\1" + NB, h)
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
    h = re.sub(r"<span[^>]*>\s*</span>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&emsp;", " ").replace("&nbsp;", " ").replace("\u25ba", "→")
    return re.sub(r"\s+", " ", h).strip()

# Names printed in a snipped figure that content_text should still carry (search only).
EXTRA_TEXT = {(1, None): "compound P", (1, "(b)"): "Q R", (2, "(c)"): "A B C D F HCl(g) Mg CO2 LiAlH4 step 3", (2, "(d)"): "cyanoacetic acid step I Y a few steps D cyclohexanone"}

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
