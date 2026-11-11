"""Hand transcription of NJC 2026 H2 Prelim Paper 2 (9476/02, 6 structured, 75 marks) -> questions.json +
asset_plan.json. The school supplied a PDF only (its Word file was badly formatted), so there is no
extractor; same output contract as extract_parts, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_njc26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school NJC --year 2026 --paper 2 --level H2

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
SCHOOL, LEVEL, PAPER, YEAR = "NJC", "H2", "P2", 2026
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


# ---- extra helpers --------------------------------------------------------------------------
CL = "C" + L
kk = i("k")
def pK(s): return "p" + K + sub(s)
def dH(s=""): return DEL + i("H") + (sub(s) if s else "")
def long_arrow(w):
    return ('<span style="display:flex;align-items:center;width:%sem;margin:0 auto">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.55em;margin-left:-.3em;line-height:1">►</span></span>' % w)
def over(top, arrow, bottom=None, wide=False):
    pad = "padding:0 .35em;" if wide else "padding:0 .15em;"
    small = '<span style="display:block;font-size:.72em;line-height:1.15">%s</span>'
    out = ('<span style="display:inline-block;vertical-align:middle;text-align:center;'
           'line-height:1.1;%s">' % pad) + small % top
    out += '<span style="display:block;line-height:1">%s</span>' % arrow
    out += small % (bottom or "&nbsp;")
    return out + "</span>"
def ceqn(s): return '<p class="c eqn">%s</p>' % s
EM = "&emsp;"
OH = "OH" + sup(M)
HP = "H" + sup("+")
STD = sup("⦵")
H2O = "H" + sub(2) + "O"

# Parts are (label, html) or (label, html, tail). `tail` is text/figure the paper prints AFTER the part's
# mark and BEFORE the next label (it introduces the next sub-part); it is emitted as bare blocks between
# the qpart divs, the same shape render_parts gives a QLEVEL tail on the extractor path.
Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])

# ---------------------------------------------------------------- Q1
CCL4, PCL5 = "CC" + L + sub(4), "PC" + L + sub(5)
Q[1] = dict(marks=8, intro=[p("Elements in Period 3 of the Periodic Table show trends in their properties.")], parts=[
    ("(a)", p("Fig. 1.1 shows the ionic radii of the anions and cations of Period 3.") + FIG + cap("Fig. 1.1") +
            p("Explain the shape of the graph in Fig. 1.1. " + mk(2))),
    ("(b)", p("The third ionisation energies of consecutive Period 3 elements represented by letters " + b("A") + " to " + b("F") +
              " are shown in Fig. 1.2.") + FIG + cap("Fig. 1.2")),
    ("(b)(i)", p("Write an equation, including state symbols, to represent the third ionisation energy of element " + b("B") + ". " + mk(1))),
    ("(b)(ii)", p("Identify which element is phosphorus. Explain your answer. " + mk(2))),
    ("(c)", p("Carbon tetrachloride, " + CCL4 + ", and phosphorus pentachloride, " + PCL5 + ", are both non-metal chlorides.")),
    ("(c)(i)", p("When added to water, " + PCL5 + " undergoes hydrolysis while " + CCL4 + " does not. "
                 "Explain the difference in behaviour of both chlorides. " + mk(1))),
    ("(c)(ii)", p("Write a balanced equation for the hydrolysis of " + PCL5 + " with water. " + mk(1)),
     p("Phosphorus pentachloride exhibits distinct structural behaviours depending on its physical state. In the gas and liquid phases, " + PCL5 +
       " exists as discrete covalent molecules, while in the solid phase, it exists as a giant ionic lattice structure.")),
    ("(c)(iii)", p("When " + PCL5 + " solidifies, it undergoes auto-ionisation to form two distinct ions, both of which contain phosphorus and "
                   "chlorine atoms only.") +
                 p("Suggest the formulae of the two oppositely charged ions. " + mk(1))),
])

# ---------------------------------------------------------------- Q2
HI, HCL = "HI", "HC" + L
Q[2] = dict(marks=10, intro=[p("Hydrogen halides are important industrial chemicals used in processes such as etching, synthesis, and chemical manufacture.")], parts=[
    ("(a)", p("The boiling points of hydrogen iodide, HI, and hydrogen chloride, " + HCL + ", are as shown in Table 2.1.") + cap("Table 2.1") +
            table(tr(th("Species"), th("Boiling Point / °C")),
                  tr(td(HI), td(M + "35.4")),
                  tr(td(HCL), td(M + "85.1")))),
    ("(a)(i)", p("Explain the difference in the boiling points observed for HI and " + HCL + ". " + mk(1))),
    ("(a)(ii)", p("A 25.0 cm" + sup(3) + " sample of 0.2 " + MDM + " HI(aq) has a pH of 0.70 at 298 K.") +
                p("State the pH of a 25.0 cm" + sup(3) + " sample of " + HCL + "(aq) of the same concentration and temperature. Explain your answer. " + mk(1)),
     p("Hydrogen iodide can react with alcohols to form alkanes under suitable conditions.") +
     ceqn("CH" + sub(3) + "OH + 2HI → CH" + sub(4) + " + I" + sub(2) + " + " + H2O)),
    ("(a)(iii)", p("Suggest the role of HI in this reaction. " + mk(1))),
    ("(b)", p("Hydrogen fluoride, HF, has a very low acid strength. The dissociation of HF in aqueous solution involves a series of steps.") +
            ceqn("HF(aq) ⇌ " + HP + "(aq) + F" + sup(M) + "(aq)" + EM + EM + dH("dissociation")) +
            p("The " + dH("dissociation") + " can be calculated using the enthalpy change of hydration for " + HP + " and F" + sup(M) +
              " ions and other data found in Table 2.2.") + cap("Table 2.2") +
            table(tr(th(""), th(dH() + " / kJ mol" + sup(M + "1"))),
                  tr(td("first electron affinity for F(g)"), td(M + "328")),
                  tr(td("HF(g) → HF(aq)"), td(M + "48")),
                  tr(td("enthalpy change of hydration for " + HP + " ion"), td(M + "1091")),
                  tr(td("enthalpy change of hydration for F" + sup(M) + " ion"), td(M + "515")))),
    ("(b)(i)", p("Explain what is meant by enthalpy change of hydration for F" + sup(M) + " ion. " + mk(1))),
    ("(b)(ii)", p("Complete the energy level diagram in Fig. 2.3 and calculate the " + dH("dissociation") + " for HF, using data from Table 2.2 and the " +
                  i("Data Booklet") + ".") + FIG + cap("Fig. 2.3") + c(mk(3))),
    ("(b)(iii)", p("Calculate the pH for a 25.0 cm" + sup(3) + " sample of 0.20 " + MDM + " HF(aq), given that " + pK("a") + " of HF = 3.14 at 25 °C. " + mk(1))),
    ("(b)(iv)", p("Neutron diffraction studies of solid HF show that there are two different distances between hydrogen and fluorine nuclei, 0.092 nm and 0.163 nm.") +
                p("Draw a diagram containing two HF molecules and suggest a reason for the two different distances. Your diagram should show and label both distances. " + mk(2))),
])

# ---------------------------------------------------------------- Q3
TI3 = "Ti" + sup("3+")
TIH2O6 = "[Ti(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+")
Q[3] = dict(marks=16, intro=[p("The chemistry of titanium is of significant industrial importance.")], parts=[
    ("(a)(i)", p("Write the electronic configuration of the titanium atom, and hence explain why titanium exhibits a range of oxidation states in its compounds. " + mk(2))),
    ("(a)(ii)", p("Complete Fig. 3.1 to show the splitting of energy levels of the 3d orbitals of " + TI3 + " when forming " + TIH2O6 + ".") + FIG + cap("Fig. 3.1") + c(mk(1))),
    ("(a)(iii)", p("Using the axes below in Fig. 3.2, draw " + b("one") + " of the d orbitals of " + TI3 + " that is in the higher energy level when forming " +
                   TIH2O6 + ".") + FIG + cap("Fig. 3.2") + c(mk(1))),
    ("(a)(iv)", p("Explain why " + TIH2O6 + " complex is coloured. " + mk(2))),
    ("(b)", p("Titanium metal is produced industrially by the Kroll process, which involves the reduction of TiC" + L + sub(4) +
              " with magnesium metal. The electrolysis of molten MgC" + L + sub(2) + " is used to produce the magnesium required.") +
            p("An industrial electrolytic cell is used to produce magnesium from molten MgC" + L + sub(2) + " at a current of 50,000 A for 24 hours.") +
            p("Calculate the maximum mass of magnesium, in kg, that can be produced. " + mk(2))),
    ("(c)", p("Solid titanium(III) chloride, TiC" + L + sub(3) + ", is used as a component of Ziegler-Natta catalysts for the polymerisation of gaseous alkenes. "
              "Despite having the same molecular mass, the polymers produced by Ziegler-Natta catalysts have different properties compared to those produced "
              "by a radical polymerisation process.") +
            p("Table 3.3 shows the comparison of polyethenes produced via Ziegler-Natta polymerisation and radical polymerisation.") + cap("Table 3.3") +
            table(tr(th("Feature of polyethene"), th("Ziegler-Natta polymerisation"), th("radical polymerisation")),
                  tr(td("Polymer density / g cm" + sup(M + "3")), td("0.97–0.99<br>High"), td("0.82–0.84<br>Low")),
                  tr(td("Melting point / °C"), td("130 – 135"), td("105 – 110")),
                  tr(td("Physical properties"), td("rigid, high tensile strength"), td("flexible")),
                  tr(td("Common use"), td("water pipes, detergent bottles"), td("plastic bags, cling wrap")))),
    ("(c)(i)", p("Outline the mode of action of the Ziegler-Natta catalyst in the polymerisation of gaseous alkenes. " + mk(2))),
    ("(c)(ii)", p("Suggest an explanation for the difference in melting points of the polymers formed by the two processes. " + mk(2))),
    ("(d)", p("When SnC" + L + sub(4) + " reacts with potassium hydroxide in a small amount of water, potassium chloride is produced, together with an anhydrous salt, " +
              b("G") + ", having the following composition by mass: K, 23.28%; Sn, 35.34%; C" + L + ", 21.14%; O, 19.05%; H, 1.19%.")),
    ("(d)(i)", p("Calculate the empirical formula of the salt " + b("G") + ". " + mk(1))),
    ("(d)(ii)", p("Deduce the structural formula of the complex anion of salt " + b("G") + ". " + mk(1)),
     p("The anion was found to exhibit cis-trans isomerism.")),
    ("(d)(iii)", p("Suggest the shape of the anion. " + mk(1))),
    ("(d)(iv)", p("Draw the structure of the trans isomer. " + mk(1))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=17, intro=[], parts=[
    ("(a)", p("Procaine, C" + sub(13) + "H" + sub(20) + "N" + sub(2) + "O" + sub(2) + ", is a local anaesthetic widely used in dentistry and minor surgical procedures.") + FIG +
            p("Procaine is typically converted into a salt by reacting it with hydrochloric acid, " + HCL + ", forming procaine hydrochloride, C" + sub(13) + "H" + sub(21) +
              "N" + sub(2) + "O" + sub(2) + CL + ". The salt is administered by injection into the blood plasma, which comprises 90–92% water. "
              "In the blood plasma which has a pH of 7.4, a small percentage of procaine hydrochloride converts back to the original form and enters the target cells.")),
    ("(a)(i)", p("Explain the difference in " + pK("b") + " values of the two amine functional groups in procaine. " + mk(2)),
     p("The pH curve in Fig. 4.1 below shows the addition of 0.010 " + MDM + " " + HCL + " to 10.0 cm" + sup(3) + " of 0.010 " + MDM + " of procaine.") + FIG + cap("Fig. 4.1")),
    ("(a)(ii)", p("The pH at point " + b("B") + " can be calculated using the following formula:") +
                c("pH" + sub("B") + " = " + frac("pH" + sub("A") + " + pH" + sub("C"), "2")) +
                p("Using the " + pK("b") + " values of procaine, determine the pH at point " + b("B") + " in Fig. 4.1. " + mk(2))),
    ("(a)(iii)", p("With the aid of an equation, explain why the pH of the solution is less than 7 at point " + b("D") + ". " + mk(2))),
    ("(b)(i)", p("Explain why procaine hydrochloride is highly soluble in blood plasma. " + mk(2))),
    ("(b)(ii)", p("A solution of procaine hydrochloride, C" + sub(13) + "H" + sub(21) + "N" + sub(2) + "O" + sub(2) + CL +
                  ", of unknown concentration is used in a quantitative analysis. A 10.00 cm" + sup(3) + " portion of this solution is diluted with water to 100.0 cm" + sup(3) + ".") +
                p("The diluted solution contains 236 ppm of procaine hydrochloride by mass.") +
                p("(1 ppm of procaine hydrochloride = 1 mg of procaine hydrochloride in 1000 g of solvent)") +
                p("Calculate the concentration, in " + MDM + ", of procaine hydrochloride in the original solution.") +
                p("Molar mass of procaine hydrochloride = 237.3 g mol" + sup(M + "1") + ".<br>The density of the diluted solution may be assumed to be 1.00 g cm" + sup(M + "3") + ". " + mk(2))),
    ("(c)(i)", p("When procaine hydrochloride is converted into procaine in the cells, procaine is quickly degraded by esterase enzymes. In an " + i("in-vitro") +
                 " laboratory setting, this degradation can be replicated using alkaline hydrolysis.") +
               p("Draw the structural formulae of the organic products formed when procaine is heated under reflux with aqueous sodium hydroxide. " + mk(2))),
    ("(c)(ii)", p("Fig. 4.2 shows the relative rate of esterase activity at various temperatures.") + FIG + cap("Fig. 4.2") +
                p("Explain the effect of temperature on esterase activity. " + mk(2))),
    ("(d)", p("The alkaline hydrolysis of procaine, " + b("P") + " can be represented by the following rate equation:") +
            c("Rate = " + kk + " [" + b("P") + "]" + sup(i("m")) + " [" + OH + "]" + sup(i("n"))) +
            p("To determine the orders of reaction " + i("m") + " and " + i("n") + ", a large excess of sodium hydroxide, NaOH was used such that the [" + OH +
              "] remains effectively constant throughout the reaction. Under these “pseudo-order” conditions, the rate equation simplifies to:") +
            ceqn("Rate = " + kk + sub(1) + " [" + b("P") + "]" + sup(i("m")) + EM + EM + "where " + kk + sub(1) + " = " + kk + " [" + OH + "]" + sup(i("n"))) +
            p("By taking the natural logarithm of both sides, this equation can be expressed as:") +
            c("ln (Rate) = " + i("m") + " ln [" + b("P") + "] + ln (" + kk + sub(1) + ")") +
            p(b("<u>Experiment 1: Determining " + i("m") + "</u>")) +
            p("A series of experiments was conducted using varying initial concentrations of procaine with a fixed excess concentration of 0.10 " + MDM + " NaOH.") +
            p("The plot of ln (Rate) against ln [" + b("P") + "] is shown below in Fig. 4.3.") + FIG + cap("Fig. 4.3")),
    ("(d)(i)", p("Use Fig. 4.3 to show that the reaction is first-order with respect to procaine and hence calculate a value for " + kk + sub(1) + ". " + mk(2))),
    ("(d)(ii)", p(b("<u>Experiment 2: Determining " + i("n") + "</u>")) +
                p("The experiment was repeated at 298 K using the same concentration of " + b("P") + ", but different concentrations of " + OH + ".") + cap("Table 4.4") +
                table(tr(th("Run"), th("[" + b("P") + "] / " + MDM), th("[" + OH + "] / " + MDM), th("Half-life, t" + sub("1/2") + " / s")),
                      tr(td("A"), td("0.01"), td("0.10"), td("138.6")),
                      tr(td("B"), td("0.01"), td("0.20"), td("69.3"))) +
                p("Using the data provided in Table 4.4, deduce the order of reaction with respect to " + OH + ", " + i("n") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=16, intro=[], parts=[
    ("(a)", p("Epoxyethane, also known as ethylene oxide or oxirane, is industrially important as a raw material. The family of 3-membered ring compounds derived "
              "from it, epoxides, are useful in organic synthesis.") +
            p("A reaction of epoxyethane to form 2-aminoethanol is shown in Fig. 5.1.") + FIG + cap("Fig. 5.1")),
    ("(a)(i)", p("Complete the mechanism for " + b("steps 1") + " and " + b("2") + " of the reaction of epoxyethane with ammonia in Fig. 5.2.") +
               p("Include all relevant curly arrows, lone pairs of electrons, charges and dipoles.") + FIG + cap("Fig. 5.2") + c(mk(2))),
    ("(a)(ii)", p("Another epoxide, " + b("M") + ", also reacts with ammonia via the same mechanism in Fig. 5.2 to give " + b("N") + " as the major product.") + FIG +
                p("Suggest two reasons for the formation of " + b("N") + " as the major product. " + mk(2))),
    ("(b)", p("In industry, ethene is catalytically oxidised using a silver catalyst to form epoxyethane.") + FIG),
    ("(b)(i)", p("Use data from the " + i("Data Booklet") + " to calculate a theoretical value for the sum of the C–C and 2 × C–O bond energies in epoxyethane. " + mk(1))),
    ("(b)(ii)", p("The " + dH() + STD + " for the reaction between ethene and oxygen is " + M + "107 kJ mol" + sup(M + "1") + ".") +
                p("You can assume that the C–H bond energy is the same in ethene and epoxyethane.") +
                p("Use the " + dH() + STD + " value for the reaction between ethene and oxygen given above to calculate the actual value of the sum of the C–C and 2 × C–O "
                  "bond energies in epoxyethane. " + mk(2))),
    ("(b)(iii)", p("Suggest an explanation for the difference between the theoretical and actual values and comment on the high reactivity nature of epoxyethane. " + mk(2))),
    ("(c)", p("A chemical spill in a laboratory has destroyed the labels on three bottles " + b("X") + ", " + b("Y") + ", and " + b("Z") +
              ". The inventory states that the bottles contain the following three aromatic liquids, though not necessarily in this order:") + FIG +
            p("To identify them, the same amount of each liquid is placed into three separate beakers containing equal volumes of a 50:50 water/ethanol solvent mixture. "
              "The pH and the electrical conductivity of each solution are continuously monitored at 25 °C.") +
            p("The experimental data is summarised below:") +
            ul(b("Bottle X:") + " Electrical conductivity spikes to a very high value almost instantly. The pH drops from 7.0 to approximately 1.5 within seconds.",
               b("Bottle Y:") + " Electrical conductivity gradually increases over several hours. The pH slowly drops from 7.0 to around 4.5 over the same time period.",
               b("Bottle Z:") + " Electrical conductivity remains near zero. The pH remains constant at 7.0 even after 24 hours.")),
    ("(c)(i)", p("There are no changes in pH and electrical conductivity observed for the liquid in bottle " + b("Z") + ".") +
               p("What does this suggest about the identity of the liquid present in bottle " + b("Z") + "? Explain your answer. " + mk(2))),
    ("(c)(ii)", p("Suggest what causes the observed changes in pH and electrical conductivity when the liquids from bottles " + b("X") + " and " + b("Y") +
                  " are added separately to the water/ethanol solvent mixture. " + mk(2))),
    ("(c)(iii)", p("Based on your answer to (ii), and using the experimental data, identify the compounds present in bottles " + b("X") + " and " + b("Y") + ".") +
                 p("Hence, explain why they show different rates of change. " + mk(3))),
])

# ---------------------------------------------------------------- Q6
R = "R–"
Q[6] = dict(marks=8, intro=[], parts=[
    ("(a)", p("The following reaction can be achieved in a 3-step synthesis.") + FIG),
    ("(a)(i)", p("Draw the structures of the intermediates, " + b("U") + " and " + b("V") + ", in the boxes provided. " + mk(2))),
    ("(a)(ii)", p("Suggest the reagents and conditions for the above reactions. " + mk(3))),
    ("(b)", p("In 1881, the German chemist August Wilhelm von Hofmann discovered that treating primary amides with aqueous alkaline bromine produced primary amines "
              "containing one less carbon atom than the starting material.") +
            c("R–CONH" + sub(2) + " " + over("Br" + sub(2) + " + " + OH, long_arrow(4.2), wide=True) + " R–NH" + sub(2)) +
            p("The Hofmann reaction can be used in the following synthesis of compound " + b("O") + ", C" + sub(9) + "H" + sub(11) + "N.") + FIG +
            p("Suggest the structures of compounds " + b("J") + ", " + b("K") + " and " + b("O") + ". " + mk(3)) +
            table(tr(th(b("J")), th(b("K")), th(b("O"))), tr(td("<br><br><br><br><br>"), td(""), td("")))),
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
EXTRA_TEXT = {(5, "(c)"): "chlorophenylmethane, CH2Cl; chlorobenzene, Cl; benzoyl chloride, COCl"}

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
