"""Hand transcription of NYJC 2026 H2 Prelim Paper 3 (9476/03, 5 structured) -> questions.json +
asset_plan.json. The school's Word file is a paragraph-flow docx full of floating answer boxes and ChemDraw/WMF
objects (same as P2), so the question text is typed here from the PDF + docx. Same output contract as
extract_parts, i.e. what gen_parts_migration.py reads.
Run from the repo root:  python3 ingest/build_nyjc26_p3.py <outdir>
Then:  python3 -m ingest.gen_parts_migration <outdir> dest.sql --school NYJC --year 2026 --paper 3 --level H2

Marks as ingested: Q1 20, Q2 19, Q3 16, Q4 20, Q5 20 = 95 (75 as sat: Section B is "answer one",
Q4 or Q5). Same convention as the other P3s. No Data-based flag (P3 rule).

Conventions as build_njc26_p3.py: [n] is a span.mk where the paper prints it; every figure is a block
<div class="fig"> placeholder with a typed bold centred caption (the snip excludes the caption); answer
lines/boxes are not reproduced (tables the candidate completes are typed); asset slot = part label without
brackets, 'c2' for a second figure in the same part. Bond hyphens are plain hyphens (ruling 2026-11-01);
minus signs U+2212.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SCHOOL, LEVEL, PAPER, YEAR = "NYJC", "H2", "P3", 2026
FIG = '<div class="fig">figure</div>'
M = "−"                                   # minus sign U+2212
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def mk(n): return '<span class="mk">[%d]</span>' % n
def p(s): return "<p>%s</p>" % s
def c(s): return '<p class="c">%s</p>' % s
def ceqn(s): return '<p class="c eqn">%s</p>' % s
def ul(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def ol(*items): return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % x for x in items)
def cap(s): return c(b(s))
def th(s): return "<th>%s</th>" % s
def td(s): return "<td>%s</td>" % s
def tr(*cells): return "<tr>%s</tr>" % "".join(cells)
def table(*rows): return '<table class="qt">%s</table>' % "".join(rows)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)

L = '<i class="el">l</i>'                  # element l
CL = "C" + L
K = i("K")
MDM = "mol dm" + sup(M + "3")
DEL = "Δ"
EM = "&emsp;"
STD = sup('<span class="pl-sym">⦵</span>')
DOT = "•"
def F(s):
    """Formula string: subscript digits after a letter or ')', element l in Cl italic."""
    s = re.sub(r"(?<=[A-Za-z\)])(\d+)", lambda m: sub(m.group(1)), s)
    return s.replace("Cl", CL)
def pK(s): return "p" + K + sub(s)
def Ka(): return K + sub("a")
def Ksp(): return K + sub("sp")
def Kp(): return K + sub("p")
def dHr(): return DEL + i("H") + sub(i("r"))
def dGstd(): return DEL + i("G") + STD
def Ecell(): return i("E") + STD + sub("cell")
AL = "A" + L
ALCL3 = AL + CL + sub(3)
OHm = "OH" + sup(M)
def x10(a, n): return "%s × 10%s" % (a, sup(M + str(n)))
def chg(sym, ch): return F(sym) + sup(ch)

Q = {}   # qn -> dict(marks, intro=[blocks], parts=[(label, html[, tail])])
SUPM = lambda n: sup(M + str(n))
def kjmol(): return "kJ mol" + SUPM(1)

# ---------------------------------------------------------------- Q1
Q[1] = dict(marks=20, intro=[], parts=[
    ("(a)(i)", p("State the full electronic configuration of a chromium atom. " + mk(1))),
    ("(a)(ii)", p("Explain why chromium is classified as a " + i("transition element") + ". " + mk(1))),
    ("(b)", p("Explain why transition element complexes are usually coloured. " + mk(3))),
    ("(c)(i)", p("Define standard cell potential, " + Ecell() + ". " + mk(1))),
    ("(c)(ii)", p("An electrochemical cell is set to measure the " + Ecell() + " between the " + chg("Cr", "3+") + "(aq)/Cr(s) electrode and the " +
                  CL + sub(2) + "(g)/" + CL + sup(M) + "(aq) electrode.") +
                p("Draw a labelled diagram of this electrochemical cell set-up.") +
                p("Include all necessary substances and relevant pieces of apparatus. " + mk(3))),
    ("(c)(iii)", p("Write the overall equation for when current flows and hence calculate the standard cell potential, " + Ecell() + " for this cell. " + mk(1))),
    ("(c)(iv)", p("Use your answer to " + b("(c)(iii)") + " to calculate the standard Gibbs free energy change, " + dGstd() + ", for this electrochemical reaction. " + mk(1))),
    ("(d)", p("A sample of chromium(III) chloride, " + F("CrCl3") + ", green solution, is added to aqueous sodium carbonate. Describe and explain what you would observe, "
              "identify the types of reaction and write equations. " + mk(3))),
    ("(e)(i)", p("Define the term " + i("lattice energy") + ". " + mk(1))),
    ("(e)(ii)", p("Use the data in Table 1.1, together with data from the " + i("Data Booklet") + ", to calculate a value for the lattice energy of chromium(II) bromide, " +
                  F("CrBr2") + "(s). Show your working.") + cap("Table 1.1") +
                table(tr(th(""), th("value / " + kjmol())),
                      tr(td("electron affinity of bromine, Br(g) + e" + sup(M) + " → Br" + sup(M) + "(g)"), td(M + "324")),
                      tr(td("enthalpy change of vaporisation of Br" + sub(2) + "(l) → Br" + sub(2) + "(g)"), td("+31")),
                      tr(td("standard enthalpy change of atomisation of Cr(s)"), td("+397")),
                      tr(td("standard enthalpy change of formation of " + F("CrBr2") + "(s)"), td(M + "302"))) + c(mk(3))),
    ("(e)(iii)", p("Deduce the order of lattice energy, in decreasing magnitude, of " + F("CrF2") + ", CrO and " + F("CrBr2") + ". Explain your answer. " + mk(2))),
])

# ---------------------------------------------------------------- Q2
Q[2] = dict(marks=19, intro=[], parts=[
    ("(a)", p("Chlorofluorocarbons (CFCs) and hydrochlorofluorocarbons (HCFCs) are organic compounds containing carbon–chlorine bonds and have been used as refrigerants "
              "because they are considered stable and inert under normal conditions.") +
            p("In the stratosphere, the breakdown of CFCs releases reactive chlorine. This stratospheric chlorine is involved in the formation of perchloric acid, " +
              F("HClO4") + ", causing it to deposit in polar ice and snow.") +
            p("Because perchloric acid is an incredibly strong, corrosive, and reactive superacid, it requires rigorous safety protocols.")),
    ("(a)(i)", p("Give the displayed formula of the " + F("HClO4") + " molecule, showing the spatial arrangement and estimated bond angles of O-" + CL + "-O and H-O-" + CL + ".") +
               p("Explain the spatial arrangement and bond angles using Valence Shell Electron Pair Repulsion Theory. " + mk(3))),
    ("(a)(ii)", p("Explain why perchloric acid is a strong acid, with reference to the stability of its conjugate base. " + mk(1))),
    ("(a)(iii)", p("Other than being corrosive and highly acidic, state another chemical property of perchloric acid. Explain your answer in terms of the oxidation state of chlorine. " + mk(1))),
    ("(a)(iv)", p("Explain why CFCs and HCFCs are considered stable and inert. " + mk(1))),
    ("(b)", p("Total Base Number (TBN) is a measure of the quantity of basic substances present in a lubricant oil. It is defined as the mass of potassium hydroxide, in milligrams, "
              "that is chemically equivalent to the basic constituents present per gram of oil.") +
            p("To determine TBN, the oil sample is treated with an excess of a strong acid. The basic constituents in the oil react completely with part of this acid. "
              "The remaining unreacted acid is then determined by back-titration with a standard base. From this, the amount of acid that reacted with the oil and hence, "
              "the TBN can be calculated.") +
            p("A 2.000 g sample of lubricant oil was analysed using this method.") +
            p("10.00 cm" + sup(3) + " of 0.100 " + MDM + " perchloric acid, " + F("HClO4") + ", was added to the oil sample. After the reaction was completed, the resulting mixture "
              "was titrated with 0.100 " + MDM + " sodium acetate solution, " + F("CH3COONa") + ". 5.40 cm" + sup(3) + " of sodium acetate solution was required to reach the end point.") +
            p("Assuming all the basic groups in the lubricant oil react completely with " + F("HClO4") + " in a 1 : 1 mole ratio, calculate the TBN of the lubricant oil, in mg KOH g" + SUPM(1) + ". " + mk(2))),
    ("(c)", p("Perchloric acid typically supported on silica gel serves as an efficient, recyclable, and mild Brønsted acid catalyst for some Michael addition reactions.") +
            p("One example of a Michael addition reaction is the addition of an enolate to an electrophilic alkene to form carbon–carbon single bond as shown in Fig. 2.1. "
              "An electrophilic alkene is an alkene where the C=C is bonded to at least one electron-withdrawing group.") + FIG + cap("Fig. 2.1") +
            p("An enolate can be formed through treatment of a ketone, ester, nitrile or similar species with a strong base as shown in Fig. 2.2. Other than enolates, other typical "
              "nucleophiles used for this addition reaction are thiols, RSH, thioacids, RCOSH and amines, RN" + F("H2") + ".") + FIG + cap("Fig. 2.2")),
    ("(c)(i)", p("Suggest why enolates can add to an alkene to form carbon–carbon single bond as shown in Fig. 2.1. Use the concepts of electronic effects or delocalisation in your answer. " + mk(1)),
     p("Michael addition reaction is widely applied in the synthesis of pharmaceuticals. An example is spironolactone, a diuretic medication used to treat fluid build-up due to liver or kidney disease.") + FIG),
    ("(c)(ii)", p("Suggest the structure of a thioacid and the electrophilic alkene that would form spironolactone by a similar reaction to that shown in Fig. 2.1. " + mk(1))),
    ("(d)", p("Compound " + b("F") + ", " + F("C10H10O2") + ", contains a benzene ring with two side-chains.") +
            p(b("F") + " does not contain a chiral carbon atom but displays cis–trans isomerism.") +
            p("A series of tests are carried out on " + b("F") + ".") +
            p("Table 2.1 shows the compounds formed, and other information, when " + b("F") + " is added to different reagents under specific conditions.") + cap("Table 2.1") +
            table(tr(th("test"), th("reagents and conditions"), th("compounds formed"), th("other information")),
                  tr(td("1"), td("excess " + F("H2") + " / Ni"), td(b("G") + ", " + F("C10H14O2")), td(b("G") + " contains one chiral centre")),
                  tr(td("2"), td("aqueous " + F("Br2")), td(b("H") + ", " + F("C10H9O3Br3")), td("white ppt observed and orange aqueous " + F("Br2") + " decolourises")),
                  tr(td("3"), td("warm with aqueous alkaline iodine"), td(b("I") + ", yellow ppt"), td("")),
                  tr(td("4"), td(F("CH3COCH3")), td(b("J") + ", " + F("C13H16O3")), td("Refer to Fig. 2.1 and 2.2"))) +
            p("For each of the four tests, state the type of reaction occurring, if any.") +
            p("For each compound, state what the information in Table 2.1 tells you about the functional groups it contains. Include your reasoning.") +
            p("Using your answers above to deduce possible structures for " + b("F") + ", " + b("G") + ", " + b("H") + ", " + b("I") + " and " + b("J") + ". " + mk(9))),
])

# ---------------------------------------------------------------- Q3
Q[3] = dict(marks=16, intro=[], parts=[
    ("(a)(i)", p("On the same axes, sketch and label the graphs showing how the volume for a given mass of an ideal gas varies with temperature at two different pressures, " +
                 i("p") + sub(1) + " and " + i("p") + sub(2) + ", where " + i("p") + sub(1) + " > " + i("p") + sub(2) + ".") +
               p("Explain your answer.") + FIG + c(mk(2))),
    ("(a)(ii)", p("Explain why hydrazine gas, " + F("N2H4") + ", deviates more from ideal gas behaviour than ethylamine, " + F("CH3CH2NH2") + ". " + mk(1))),
    ("(b)", p("A student wanted to synthesise 4-ethylphenylamine from phenylamine and wrongly proposed step 1 shown in Fig. 3.1 below. Instead of 4-ethylphenylamine, "
              "a neutral product " + b("P") + " is formed. The correct synthesis can be achieved by carrying out steps 2, 3 and 4.") + FIG + cap("Fig. 3.1")),
    ("(b)(i)", p("Describe and explain the relative basicities of phenylamine, " + b("Q") + " and 4-ethylphenylamine in aqueous medium. " + mk(3))),
    ("(b)(ii)", p("Explain the role of " + ALCL3 + " in step 3. " + mk(1))),
    ("(b)(iii)", p("Hence using your answer from " + b("(i)") + " and " + b("(ii)") + ", suggest the structure of " + b("P") + ". " + mk(1))),
    ("(b)(iv)", p("Suggest the structure of " + b("R") + ". " + mk(1))),
    ("(b)(v)", p("State the reagents and conditions for steps 2 and 4. " + mk(2))),
    ("(b)(vi)", p("Describe the mechanism for step 3. " + mk(3))),
    ("(c)", p(i("Paracetamol") + " is widely used as an analgesic. It can be synthesised as shown below.") + FIG +
            p("Compound " + b("S") + " is a possible side product of the reaction.") + FIG),
    ("(c)(i)", p("State the type of reaction that occurs in the formation of " + i("Paracetamol") + ". " + mk(1))),
    ("(c)(ii)", p("Explain why the major product formed is " + i("Paracetamol") + " and not " + b("S") + ". " + mk(1))),
])

# ---------------------------------------------------------------- Q4
Q[4] = dict(marks=20, intro=[], parts=[
    ("(a)", p("A longer chain alkane can be formed by a radical chain reaction between alkene and thiol as shown in Fig. 4.1. This reaction is conducted in the presence of "
              "azobisisobutyronitrile (AIBN) and isocyanide.") + FIG + cap("Fig. 4.1") +
            p("The radical chain reaction occurs via five separate steps, " + b("A") + " to " + b("E") + ".") + FIG + cap("Fig. 4.2")),
    ("(a)(i)", p("Explain what is meant by the term " + i("radical") + ". " + mk(1))),
    ("(a)(ii)", p("Using data from the " + i("Data Booklet") + ", calculate the standard enthalpy change of step " + b("A") + ". " + mk(2))),
    ("(a)(iii)", p("Suggest the overall process occurring in steps " + b("B") + " to " + b("E") + ".") + p("Explain your answer. " + mk(1))),
    ("(a)(iv)", p("Complete the mechanism for steps " + b("D") + " and " + b("E") + " on Fig. 4.2. Use curly arrows to show the movement of electrons. " + mk(2))),
    ("(a)(v)", p("Fig. 4.3 shows a compound undergoing the radical chain reaction to form a cyclic product " + b("F") + ".") +
               p("Suggest the structure of " + b("F") + ". Hence, explain why product " + b("G") + " is not formed.") + FIG + cap("Fig. 4.3") + c(mk(2))),
    ("(a)(vi)", p("Thiols rather than alcohols are used in the radical chain reaction due to their lower bond dissociation energy.") +
                p("Explain why the bond dissociation energy of the S-H bond in methanethiol is lower than the O-H bond in methanol. " + mk(1))),
    ("(b)", p("An electrolytic process of manganese-catalysed dichlorination of alkenes using " + F("MnCl2") + "(aq) as the chlorine source is able to produce dichloroalkanes. "
              "Fig. 4.4 shows the mechanism of this process.") + FIG + cap("Fig. 4.4")),
    ("(b)(i)", p("Use Fig. 4.4 to explain how manganese(II) ions can act as a homogenous catalyst. " + mk(1))),
    ("(b)(ii)", p("State the property, typical of a transition metal, which allows manganese(II) ions to act as a homogenous catalyst. " + mk(1))),
    ("(b)(iii)", p("The standard cell potential, " + Ecell() + ", for the electrolytic process shown in Fig. 4.4 is at " + M + "2.3 V.") +
                 p("Using data from the " + i("Data Booklet") + ", deduce the standard reduction potential, " + i("E") + STD + " ([Mn" + sup("III") + "-" + CL + "]/[Mn" + sup("II") + "-" + CL + "]). " + mk(1))),
    ("(b)(iv)", p("The radical intermediate has the unpaired electron on an sp" + sup(2) + " carbon.") +
                p("State the relationship between " + b("H") + " and " + b("J") + ". Hence, suggest and explain the ratio of " + b("H") + " and " + b("J") + " produced. " + mk(3))),
    ("(c)", p("Diels–Alder reactions occur between a diene and an alkene, usually called the dienophile, as shown in Fig. 4.5. The reaction occurs in a single step through a cyclic "
              "transition state in which two new C-C bonds form simultaneously.") + FIG + cap("Fig. 4.5")),
    ("(c)(i)", p("Complete the Diels-Alder reaction between " + F("CH2=CHCH=CH2") + " and " + F("CH2=CHCH3") + " on Fig. 4.6 by adding " + b("three") + " curly arrows.") + FIG + cap("Fig. 4.6") + c(mk(2))),
    ("(c)(ii)", p("Suggest why the trans-diene does not undergo the Diels-Alder reaction. " + mk(1)),
     p("For a Diels-Alder reaction, the position of the electron-donating group on the diene will give rise to different products with a dienophile with an "
       "electron-withdrawing group as shown in Fig. 4.7.") + FIG + cap("Fig. 4.7")),
    ("(c)(iii)", p("Predict the products when the following compounds undergo Diels-Alder reaction.") + FIG + c(mk(2))),
])

# ---------------------------------------------------------------- Q5
Q[5] = dict(marks=20, intro=[
    p("Malic acid is a naturally occurring organic acid found in green apples and grapes that contributes to the sour taste of these fruits."),
    p("It can be dehydrated to give a mixture of two isomeric alkenedioic acids with the molecular formula " + F("C4H4O4") + " as follows:"),
    FIG,
], parts=[
    ("(a)(i)", p("Suggest reagents and conditions for the dehydration reaction. " + mk(1))),
    ("(a)(ii)", p("The " + pK("a") + " values of the two acidic groups in one isomer of the alkenedioic acid, " + b("W") + ", are 3.0 and 4.4, whereas in the other isomer, " + b("X") +
                 ", they are 1.9 and 6.2.") +
               p("By considering the stability of the mono-anion produced on treatment with 1 mol of NaOH, use the " + pK("a") + " values to deduce which isomer, " + b("W") + " or " + b("X") +
                 ", is maleic acid. Include a displayed formula of the mono-anion produced in your answer. " + mk(3))),
    ("(a)(iii)", p("Interconversion of the two isomeric alkenedioic acids is typically achieved by heating in the presence of a strong acid such as HC" + L + "(aq). "
                   "Fig. 5.1 shows the mechanism for this conversion.") + FIG + cap("Fig. 5.1") +
                 p("Complete the mechanism for the reaction of maleic acid with HC" + L + " for the " + b("first") + " step on Fig. 5.1 by adding " + b("three") +
                   " curly arrows and any relevant lone pairs. " + mk(2))),
    ("(b)", p("Amino acids are the essential building blocks of proteins. Aspartic acid, one of the 20 standard amino acids, can be synthesised from malic acid or its derivatives "
              "in a reaction with ammonia via two different routes to introduce the amino group.") + FIG),
    ("(b)(i)", p("Aspartic acid exists as a mixture of stereoisomers. Draw the structure of each stereoisomer of aspartic acid. " + mk(1))),
    ("(b)(ii)", p("The two routes differ in their stereochemical outcomes. One route produces a pure form of (" + M + ") aspartic acid while the other route produces a mixture. "
                  "Suggest which route is more likely to produce the pure form of (" + M + ") aspartic acid. Explain your reasoning. " + mk(2)),
     p("Aspartase enzyme found in bacteria from a soil sample was isolated, and used in the synthesis of aspartic acid from fumaric acid. It was found that the best yield was "
       "achieved at 53 °C, using 0.88 " + MDM + " fumaric acid and 3.1 " + MDM + " ammonia, and the bacteria cells at 53 mg dry weight per cm" + sup(3) +
       ". In this case, 85 % of fumaric acid added was converted into aspartic acid.")),
    ("(b)(iii)", p("Use these data to calculate a value for the equilibrium constant, " + K + sub("c") + ", for the reaction. Ignore the involvement of bacteria cells in your "
                   "calculation. Give your answer to " + b("two") + " significant figures. " + mk(2))),
    ("(b)(iv)", p("Given the forward reaction is exothermic, suggest and explain how the value of equilibrium constant changes:") +
                ul("when the reaction was carried out at 60 °C", "when 60 mg dry weight per cm" + sup(3) + " bacteria was added.") + c(mk(3))),
    ("(c)", p("Polyaspartic acid (PAsp) is a condensation polymer made from aspartic acid via an intermediate, Polysuccinimide (PSI), followed by alkaline hydrolysis as shown in "
              "Fig. 5.2.") + FIG + cap("Fig. 5.2")),
    ("(c)(i)", p("Explain what is meant by " + i("condensation polymer") + ". " + mk(2))),
    ("(c)(ii)", p("PSI does not give effervescence with " + F("Na2CO3") + ". Draw the structure of PSI. " + mk(1))),
    ("(c)(iii)", p("Calculate the number of repeat units in a sample of PAsp with a polymer mass of 30,000 g mol" + SUPM(1) + ". " + mk(1)),
     p("PAsp is a highly biocompatible polymer primarily due to its protein backbone and its ability to completely biodegrade. These properties make PAsp a versatile and safe "
       "material for a wide range of biomedical applications, including drug delivery systems and tissue engineering.")),
    ("(c)(iv)", p("Explain why PAsp is biodegradable. " + mk(1))),
    ("(c)(v)", p("Given bone is a composite of proteins such as collagen and minerals such as calcium(II), suggest a reason why PAsp is commonly used to deliver osteoporosis drugs "
                 "directly to the bone tissue. " + mk(1))),
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
EXTRA_TEXT = {(2, "(c)"): "enolate electrophilic alkene electron-withdrawing group strong base Michael addition",
              (2, "(c)(i)"): "spironolactone",
              (3, "(b)"): "phenylamine acetanilide 4-ethylphenylamine",
              (3, "(c)"): "paracetamol 4-aminophenol ethanoyl chloride",
              (4, "(a)"): "alkene thiol AIBN isocyanide radical chain steps A B C D E initiation propagation",
              (4, "(b)"): "manganese catalysed dichlorination alkene electrolysis anode cathode",
              (4, "(c)"): "Diels-Alder diene dienophile cis-diene trans-diene",
              (5, None): "malic acid fumaric acid maleic acid",
              (5, "(a)(iii)"): "maleic acid fumaric acid HCl mechanism",
              (5, "(b)"): "malic acid fumaric acid aspartic acid aspartase",
              (5, "(c)"): "polyaspartic acid polysuccinimide PSI PAsp"}

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
