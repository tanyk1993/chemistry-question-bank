"""Hand transcription of NYJC 2026 H2 Prelim Paper 2 (9476/02, 7 structured Q, 75 marks) -> questions.json +
asset_plan.json. The school's Word file is a paragraph-flow docx full of floating answer boxes, stray tabs and
OLE equations, so the question text is typed here (typo/grammar fixes applied on the user's ruling, 2026-11-14). Same output contract as extract_parts, i.e. what
gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_nyjc26_p2.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school NYJC --year 2026 --paper 2 --level H2

Conventions (see claude/style-guide.md; same as build_njc26_p2.py):
  * stem = intro blocks, then one div.qpart per part that has text of its own; a bare label that only
    introduces sub-parts is dropped;
  * [n] is a span.mk written in place where the paper prints it;
  * every figure is a block <div class="fig"> placeholder, caption typed as a centred p.c;
  * answer lines and empty answer boxes are NOT reproduced (tables the candidate completes ARE typed);
  * asset slot = part label without brackets ('aii'), 'b2' for a second figure in the same part.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "NYJC", "H2", "P2", 2026
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

# ---- NYJC-specific helpers -------------------------------------------------------------------
CL = "C" + L
ARm = i("A") + sub("r")
MRm = i("M") + sub("r")
KSP = i("K") + sub("sp")
KA = i("K") + sub("a")
DEG = "°C"
def tdc(s, n=2): return '<td colspan="%d">%s</td>' % (n, s)
def unit_minus(n): return sup(M + str(n))
NH3OH = "NH" + sub(3) + "OH"
NH3OHP = NH3OH + sup("+")
def under(sym, label):
    """a species with its label printed directly underneath (Q7(c) 'red' / 'colourless')"""
    return ('<span style="display:inline-block;text-align:center;vertical-align:top;line-height:1.25">%s'
            '<span style="display:block;font-size:.95em">%s</span></span>' % (sym, label))
RARR = "⇌"

# ---------------------------------------------------------------- Q1
Q[1] = dict(marks=5, intro=[], parts=[
    ("(a)", p("A sample of iron contains three different isotopes and has a relative atomic mass, " + ARm + ", of 55.8.")),
    ("(a)(i)", p("Define relative atomic mass. " + mk(1))),
    ("(a)(ii)", p("Table 1.1 shows the abundances of two of the isotopes present in the sample of iron.") + cap("Table 1.1") +
                table(tr(th("isotope"), th("relative isotopic mass"), th("relative % abundance")),
                      tr(td(sup(54) + "Fe"), td("53.9"), td("6.0")),
                      tr(td(sup(56) + "Fe"), td("55.9"), td("91.9"))) +
                p("Use Table 1.1 to calculate the relative isotopic mass of the third isotope of iron in the sample. Show your working. " + mk(2))),
    ("(b)", p("Deduce the number of pairs of electrons in an iron(II) ion. " + mk(1))),
    ("(c)", p("The atomic radius of iron is 1.26 × 10" + sup("–10") + " m.") +
            p("Suggest the change to the radius, if any, after an iron atom reacts to produce an Fe" + sup("3+") + " ion. Explain your answer. " + mk(1))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=12, intro=[
    p("Hydroxylammonium chloride, NH" + sub(3) + "OHC" + L + ", is a toxic contaminant found in industrial wastewater. Environmental engineers must remove "
      "heavy metal contaminants like iron and hydroxylammonium ions, " + NH3OHP + ", from the water, and manage halogenated by-products before "
      "environmental discharge."),
    p("An engineer analyses a 1.00 dm" + sup(3) + " wastewater sample containing an unknown concentration of " + NH3OHP + " ions and 0.0150 " + MDM +
      " of iron(II) ions, Fe" + sup("2+") + "."),
], parts=[
    ("(a)", p("To remove the iron contaminants, the engineer slowly adds solid sodium hydroxide, NaOH to a 1.00 dm" + sup(3) + " portion of the wastewater "
             "sample until the pH reaches 7.50.") +
            p("Determine whether a precipitate of Fe(OH)" + sub(2) + " forms at this pH.<br>[The solubility product, " + KSP + " (Fe(OH)" + sub(2) +
              ") is 4.80 × 10" + sup(M + "17") + "] " + mk(2))),
    ("(b)", p("The treated wastewater from " + b("(a)") + " is filtered to remove all other impurities, leaving only the " + NH3OHP + " ions.") +
            p("To determine the concentration and chemical behaviour of the " + NH3OHP + " contaminant, the engineer performs a gravimetric analysis and a "
              "redox titration.") +
            p("In the gravimetric analysis, it was found that 10.0 cm" + sup(3) + " wastewater sample contained exactly 1.04 g of hydroxylammonium chloride, "
              "NH" + sub(3) + "OHC" + L + " (" + MRm + " = 69.5).") +
            p("In the redox titration, a 25.0 cm" + sup(3) + " sample of the wastewater is acidified and titrated against 2.00 " + MDM +
              " acidified potassium dichromate. During this reaction, " + NH3OHP + " is oxidised to a gaseous nitrogen oxide product.") +
            p("12.50 cm" + sup(3) + " of the acidified potassium dichromate solution is required for complete reaction with all the " + NH3OHP + " ions present.")),
    ("(b)(i)", p("Using data from the gravimetric analysis, calculate the initial concentration of " + NH3OHP + " ions in the wastewater sample in " + MDM + ". " + mk(1))),
    ("(b)(ii)", p("The possible gaseous nitrogen oxides are NO, NO" + sub(2) + ", N" + sub(2) + "O" + sub(3) + ".") +
                p("Using your answer in " + b("(i)") + ", calculate the number of moles of electrons transferred per mole of " + NH3OHP + ". Deduce the final "
                  "oxidation state of nitrogen in the gaseous nitrogen oxide product and suggest the identity of the nitrogen oxide. " + mk(3))),
    ("(c)", p("The volatile halogens generated during industrial water treatment must be recaptured.")),
    ("(c)(i)", p("Describe and explain the trend in volatility down Group 17 from chlorine to iodine in terms of their structures and bonding. " + mk(2))),
    ("(c)(ii)", p("During high temperature decomposition treatments, small concentrations of hydrogen halides, HX may form as gaseous byproducts. "
                  "Explain the trend in the thermal stability of the hydrogen halides. " + mk(2))),
    ("(d)", p("After the wastewater has been treated, an engineer tests for residual chloride ions by adding aqueous silver nitrate. 1 cm" + sup(3) +
              " of water is added to 1 cm" + sup(3) + " of 1 " + MDM + " silver nitrate solution. If no precipitate is formed, the water is considered "
              "to be safe for reuse in the manufacturing plant.") +
            p("What is the maximum allowed concentration of chloride ions that can be present in the water?") +
            p(KSP + " of AgC" + L + " = 1.8 × 10" + sup(M + "10") + " mol" + sup(2) + " dm" + sup(M + "6") + " " + mk(2))),
])

# ---------------------------------------------------------------- Q3
Q[3] = dict(marks=10, intro=[], parts=[
    ("(a)", p("W, X, Y and Z are Group 2 elements, barium, calcium, magnesium and strontium, but may not be in that order. "
              "Below is some information about them and their compounds.") +
            ul("W reacts faster with dilute hydrochloric acid than Y.",
               "The hydroxide of X is less soluble in water than the hydroxide of W.",
               "The sulfate of Y is the most soluble of the sulfates of W, X, Y and Z.",
               "The carbonate of Z decomposes at a higher temperature than the carbonate of W.")),
    ("(a)(i)", p("Explain why the carbonate of Z decomposes at a higher temperature than the carbonate of W. " + mk(2))),
    ("(a)(ii)", p("Using the above information, suggest the identities of W, X, Y and Z.") +
                p("W:") + p("X:") + p("Y:") + p("Z: " + mk(1))),
    ("(b)", p("Table 3.1 gives some information about MgC" + L + sub(2) + " and SiC" + L + sub(4) + ".") + cap("Table 3.1") +
            table(tr(th(""), th("MgC" + L + sub(2)), th("SiC" + L + sub(4))),
                  tr(td("electrical conductivity in liquid state"), td("conducts"), td("does not conduct")),
                  tr(td("observation when added to water"), td("dissolves"), td("vigorous reaction")))),
    ("(b)(i)", p("Explain the difference between the electrical conductivity of MgC" + L + sub(2) + " and SiC" + L + sub(4) + " in the liquid state. "
                 "Refer to structure, bonding and relevant particles in your answer. " + mk(2))),
    ("(b)(ii)", p("Suggest the pH of the solutions that form when each chloride is added to water.") +
                p("MgC" + L + sub(2) + EM + EM + "SiC" + L + sub(4) + " " + mk(1))),
    ("(b)(iii)", p("Complete Table 3.2 by writing equations to show the reactions, if any, of oxides of aluminium and sulfur with aqueous alkali and with "
                   "aqueous acid.") + cap("Table 3.2") +
                 table(tr(tdc("With aqueous sodium hydroxide")),
                       tr(td("aluminium oxide"), td("")),
                       tr(td("one of the sulfur oxides"), td("")),
                       tr(tdc("With aqueous hydrochloric acid")),
                       tr(td("aluminium oxide"), td("")),
                       tr(td("one of the sulfur oxides"), td(""))) + c(mk(4))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=8, intro=[
    p("Acetate ester is often used as a fragrance stabiliser in cosmetic products. One example of acetate ester can be synthesised using phenylpropene."),
    FIG,
], parts=[
    ("(a)", p("When phenylpropene reacts with HBr in step 1, there are two possible carbocation intermediates that can be formed.")),
    ("(a)(i)", p("Suggest a mechanism for step 1. Show the intermediate formed and use curly arrows to indicate the movement of electron pairs. " + mk(3))),
    ("(a)(ii)", p("Suggest the structure of the other carbocation intermediate in step 1. " + mk(1))),
    ("(a)(iii)", p("During the preparation of organic compounds, by-products may be formed because reactants or reaction intermediates can undergo "
                   "alternative reaction pathways.") +
                 p("Compound " + b("A") + ", with molecular formula C" + sub(9) + "H" + sub(10) + " is one such by-product. It is formed from the carbocation "
                   "intermediate generated in " + b("(ii)") + ".") +
                 p("Suggest the structure of compound " + b("A") + ". " + mk(1))),
    ("(b)", p("In step 2, the halogenoalkane is hydrolysed to form an alcohol.") +
            p("Explain fully why this reaction proceeds mainly via " + SN1 + " mechanism rather than " + SN2 + " mechanism. " + mk(2))),
    ("(c)", p("Suggest reagents and conditions for step 3. " + mk(1))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=8, intro=[
    p("Mandelic acid is a chemical exfoliant used in cosmetics."),
    p("It can be produced in three steps as shown in Fig. 5.1."),
    FIG, cap("Fig. 5.1"),
], parts=[
    ("(a)", p("State the reagents and conditions needed for step 1. " + mk(1))),
    ("(b)", p("Hydrogen cyanide, HCN is the reagent used in step 2.")),
    ("(b)(i)", p("Hydrogen cyanide, HCN contains a C≡N bond.") +
               p("Nitrogen atoms undergo the same type of hybridisation as carbon atoms.") +
               p("By reference to orbital overlap and the hybridisation of the nitrogen and carbon atoms, suggest how the σ and π bonds are formed in a "
                 "hydrogen cyanide molecule. " + mk(2))),
    ("(b)(ii)", p("Suggest the order of reactivity of benzene, methylbenzene and benzaldehyde with a mixture of concentrated nitric acid and concentrated "
                  "sulfuric acid under suitable conditions. Explain your answer. " + mk(2))),
    ("(c)", p("Benzaldehyde reacts with 2,4-DNPH forming an orange precipitate.")),
    ("(c)(i)", p("State the type of reaction that occurs. " + mk(1))),
    ("(c)(ii)", p("Draw the structure of the orange precipitate. " + mk(1))),
    ("(d)", p("In step 3, mandelic acid is made by reacting the cyanohydrin intermediate with H" + sub(2) + "SO" + sub(4) + "(aq).") +
            p("Write an equation to show the reaction which occurs in step 3. " + mk(1))),
])

# ---------------------------------------------------------------- Q6
Q[6] = dict(marks=9, intro=[
    p("Asparagine and aspartic acid are two naturally occurring amino acids. Their structures are shown in the following table."),
    table(tr(th("amino acid"), th("structure")),
          tr(td("asparagine"), td("HOOCCH(NH" + sub(2) + ")CH" + sub(2) + "CONH" + sub(2))),
          tr(td("aspartic acid"), td("HOOCCH(NH" + sub(2) + ")CH" + sub(2) + "COOH"))),
], parts=[
    ("(a)(i)", p("Draw the structure of asparagine at pH 2. " + mk(1))),
    ("(a)(ii)", p("Asparagine is treated separately with an excess of LiA" + L + "H" + sub(4) + ". Draw the structure of the organic product of this reaction. " + mk(1))),
    ("(a)(iii)", p("Aspartic acid exists in two optically active forms.") +
                 p("Describe two similarities and one difference in their optical activity.") +
                 p("Similarities:") + p("Difference: " + mk(2))),
    ("(b)", p("Propanedioic acid, HOOCCH" + sub(2) + "COOH, is treated with an excess of phosphorus(" + '<span class="sr">V</span>' + ") chloride. "
              "Propanedioyl chloride, C" + L + "OCCH" + sub(2) + "COC" + L + ", is formed.")),
    ("(b)(i)", p("Write an equation for this reaction. " + mk(1))),
    ("(b)(ii)", p("Propanedioyl chloride reacts with an excess of asparagine to form compound " + b("G") + " with molecular formula C" + sub(11) + "H" + sub(16) +
                  "N" + sub(4) + "O" + sub(8) + ".") +
                p("Draw the skeletal structure of compound " + b("G") + ". " + mk(2))),
    ("(b)(iii)", p("State and explain the difference in reactivity of propanedioyl chloride, C" + L + "OCCH" + sub(2) + "COC" + L + ", compared to "
                   "1,3-dichloropropane, CH" + sub(2) + "C" + L + "CH" + sub(2) + "CH" + sub(2) + "C" + L + ", when added to cold water. " + mk(2))),
])

# ---------------------------------------------------------------- Q7
ARRH = ("ln " + i("k") + " = " + M + frac(i("E") + sub("a"), i("R")) + " (" + frac("1", i("T")) + ") + ln " + i("A"))
LNQ = "ln(" + frac(i("q") + sub("o"), i("q") + sub("t")) + ") = " + i("kt")
Q[7] = dict(marks=23, intro=[
    p("Anthocyanins are natural pigments responsible for the red and purple colours in fruits. These pigments are unstable and degrade over time, "
      "especially at high temperatures. In a laboratory, this degradation can be monitored using a spectrophotometer, which measures absorbance."),
    p("Absorbance is a measure of how much light is blocked by the pigment in a sample. According to the Beer-Lambert Law, the absorbance of a solution "
      "is directly proportional to the concentration of the coloured pigment"),
    c("Absorbance ∝ [Pigment]"),
], parts=[
    ("(a)", p("An experiment was conducted to monitor the absorbance of a sample of blackberry juice with time. Given that the degradation of pigments "
             "follows overall first-order kinetics, sketch the graph of absorbance against time at 60 " + DEG + ", and how the graph can be used to "
             "determine the rate constant, " + kk + ", at this temperature.") + FIG + c(mk(2)),
     p("During storage, these pigments undergo degradation, leading to a loss of colour and nutritional value. Food scientists use Accelerated Shelf-Life "
       "Testing (ASLT) to predict how long a product will remain acceptable to consumers. ASLT is conducted when the food is stored under elevated stress "
       "conditions, e.g. at high temperature to speed up their rate of degradation. In this way, ASLT greatly shortens the time needed for food "
       "shelf-life testing.") +
     p("The manufacturer determined the rate constant, " + kk + ", at four elevated temperatures.") + cap("Table 7.1") +
     table(tr(th("temperature / " + DEG), th(kk + " / s" + sup(M + "1"))),
           tr(td("40"), td("3.33 × 10" + sup(M + "6"))),
           tr(td("50"), td("7.78 × 10" + sup(M + "6"))),
           tr(td("60"), td("1.69 × 10" + sup(M + "5"))),
           tr(td("70"), td("3.50 × 10" + sup(M + "5")))) +
     p("The Arrhenius equation that relates the rate constant, " + kk + ", in s" + sup(M + "1") + ", to temperature, " + i("T") + ", in Kelvin, is then used "
       "to predict how long the product will last at regular storage temperatures.") +
     ceqn(ARRH) +
     p("where " + i("R") + " = 8.31 J K" + sup(M + "1") + " mol" + sup(M + "1") + ", " + i("E") + sub("a") + " is the activation energy and " + i("A") +
       " is the Arrhenius constant")),
    ("(a)(i)", p("With reference to the Collision Theory, explain why the increase in temperature leads to an increase in the value of the rate constant, " +
                 kk + ", as shown in Table 7.1. " + mk(2))),
    ("(a)(ii)", p("Using the values in Table 7.1 and the Arrhenius equation, plot a straight line graph to find the rate constant, " + kk + ", at 25 " + DEG + ".") +
                FIG + c(mk(3))),
    ("(a)(iii)", p("Use the graph to calculate the activation energy, " + i("E") + sub("a") + ", including the units of the degradation reaction. " + mk(2))),
    ("(b)", p("Manufacturer considers the juice “unsellable” once 30% of the anthocyanins have degraded.") +
            p("Given " + LNQ) +
            p("where " + i("q") + sub("o") + " is the quantity of anthocyanins of a freshly prepared juice") +
            p(i("q") + sub("t") + " is the quantity of anthocyanins at time, " + i("t")) +
            p(kk + " is the rate constant") +
            p(i("t") + " is the time taken") +
            p("Using values from Table 7.1, calculate how many " + b("days") + " the juice can be stored at 40 " + DEG + " before it becomes unsellable. " + mk(2))),
    ("(c)", p("The red colour of berry juice is due to the flavylium cation, BH" + sup("+") + ". In aqueous solution, this cation behaves as a weak "
              "Brønsted-Lowry acid, establishing an equilibrium with the colourless conjugate base, B.") +
            ceqn(under("BH" + sup("+"), "red") + " + " + H2O + " " + RARR + " " + under("B", "colourless") + " + H" + sub(3) + "O" + sup("+") + EM + EM +
                 KA + " = 1.26 × 10" + sup(M + "3") + " " + MDM)),
    ("(c)(i)", p("A typical sample of berry juice has a pH of 3.4. Calculate the ratio of the colourless to the red form in the berry juice " + mk(1))),
    ("(c)(ii)", p("Explain how the colour of the juice would change if the pH is increased. " + mk(2)),
     p("To maintain a consistent colour, manufacturers often use a buffer system consisting of citric acid, C" + sub(6) + "H" + sub(8) + "O" + sub(7) +
       ", and sodium citrate, C" + sub(6) + "H" + sub(7) + "O" + sub(7) + "Na")),
    ("(c)(iii)", p("Define the term " + i("buffer") + ". " + mk(1))),
    ("(c)(iv)", p("Using relevant equation, explain how this buffer system maintains a constant pH when small amounts of OH" + sup(M) + " is introduced "
                  "during processing. " + mk(2))),
    ("(c)(v)", p("Determine the amount of solid sodium hydroxide that needs to be added to 500 cm" + sup(3) + " of 0.02 " + MDM + " of citric acid so as "
                 "to prepare a buffer solution of pH 3.4.") +
               p("(" + KA + " of citric acid = 7.4 × 10" + sup(M + "4") + " " + MDM + ") " + mk(3))),
    ("(d)", p("In addition to its role as a pH regulator, the citrate ion acts as a chelating agent to bind to the metal ion, forming a stable complex ion. "
              "This prevents the metal ion from catalysing the degradation of the berry pigments. The structure of a possible complex ion formed from "
              "aqueous solution of iron(III) ions is given below.") + FIG),
    ("(d)(i)", p("State the number of bonds formed by each citrate ion in the complex above. " + mk(1))),
    ("(d)(ii)", p("Explain the change in entropy, when citrate ion is added to an aqueous solution of iron(III) ions. " + mk(2))),
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
EXTRA_TEXT = {(4, None): "phenylpropene HBr step 1 step 2 step 3 acetate ester",
              (5, None): "step 1 step 2 step 3 benzaldehyde mandelic acid",
              (7, "(d)"): "iron(III) citrate complex"}

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
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", sum(r["marks"] for r in rows), "marks,", len(plan), "assets")
for a in plan: print("  Q%d %-6s ord %d  %s" % (a["question"], a["slot"], a["ordinal"], a["storage_path"]))

