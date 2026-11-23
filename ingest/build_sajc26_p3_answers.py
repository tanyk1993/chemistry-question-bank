"""Hand transcription of the SAJC 2026 H2 Prelim Paper 3 (9476/03) suggested solutions (26-page PDF + docx twin; the text is typed
from the docx, which carries the underlines, and the sixteen answer figures are snipped from the Word PDF by
crop_sajc26_p3_answers.py) -> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).

Run from the repo root:
    python3 -I ingest/build_sajc26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_sajc26_p3.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6, same as build_sajc26_p2_answers.py): div.worked-solution > div.part > (span.lab + div.body);
answers in span.ans with <u> on the school's underlined keywords (bold + underline kept where the school has both); figures are bare
img.ws-fig[data-asset] (SAJC_H2_P3_Q<n>_ans-<slot>_2026.png); tables are table.cmp.
Dropped from the school's pages: the L/M/H and A/B/... labels in the right margin (and "2H / 4M" at Q4(b), "2M / 2A" at Q5(d)), the
[n] mark ticks inside the answers, the "[2]: 4 - 8 ticks / [1]: 2 - 3 ticks" conversion line under the Q4(b) table, and the "(wef)"
marking abbreviations. The school's "OR" lines become P("Or").
The answer key repeats the questions with a few wording differences from the question paper (Q4(a) "Complete the equation ...",
Q6(b)/(c) stem sentences); the QP wording stays in the question rows.

FIXES made to the school's answers (listed to the user; veto-able):
  1(b)(ii)   "overlaps side ways" -> "overlaps sideways" (as on P2);
  1(c)(iii)  "Hence, ClF3 to behaves less ideally" -> "Hence, ClF3 behaves less ideally";
  2(d)(vi)   "As the alcohol become" -> "becomes"; "the alkyl groups blocks" -> "the alkyl groups block";
  5(c)(iii)  "the remaining thiophenolate ions is less than" -> "are less than";
  5(d)       the school's superscript slip "2OH- + 3H2O" is read as "2OH- + 3H2O" (a plus sign, not a charge);
  6(a)(v)    "shows a lower the tendency" -> "shows a lower tendency";
  6(b)(i)    electron written "e" -> "e-" in both half-equations;
  Q4(a) the school's "9[O]" and "2CO2 + 2H2O" are underlined as printed (balanced: C10, H18, O10 both sides).
  1(a)(ii)   the school's stacked fraction (4/35) over (2/16) is typed as a fraction of the two ratios.
  The school's own drawings (1(b)(ii), 1(b)(iii), 1(c)(v), 2(a), 2(c)(iv), 2(d)(i), 2(d)(v), 3(b)(ii), 3(b)(iii), 4(b) structures,
  5(a)(ii), 5(b)(i), 5(b)(ii), 6(c)(ii), 6(c)(iv), 6(d)(i)) are snipped as printed; the 4(b) reasoning table is typed, its structures
  (F, G and the three geraniol / E pairs) are one snip.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "SAJC_H2_P3", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
DEL = "Δ"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW = " → "
RARR = " ⇌ "
MDM = "mol dm" + sup(M + "3")
KJ = "kJ mol" + sup(M + "1")
STD = sup('<span class="pl-sym">⦵</span>')
H2O = "H" + sub(2) + "O"
EMINUS = "e" + sup(M)
H3BO3 = "H" + sub(3) + "BO" + sub(3)
H2BO3M = "H" + sub(2) + "BO" + sub(3) + sup(M)
SAG = "C" + sub(6) + "H" + sub(5) + "SAg"
THIO = "C" + sub(6) + "H" + sub(5) + "S" + sup(M)
EA = i("E") + STD
KSP = i("K") + sub("sp")
CLF3 = CL + "F" + sub(3)
CL2 = CL + sub(2)
MR = i("M") + sub("r")
def x10(a, n): return a + " × 10" + sup(M + str(n) if not str(n).startswith(M) else str(n))

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A("There is a " + u("significant/large increase from the 3rd to the 4th electron removed") + " from " + CL + sup("n+") + ", indicating that " +
          u(CL + sup("n+") + " has 3 valence electrons") + ". Since " + CL + " has 7 valence electrons, " + u("4 electrons were removed from " + CL + " to form " + CL + sup("4+")) +
          ". Hence, n = 4."))),
 PART("(a)(ii)",
      P(A("angle of deflection for X" + sup("n+") + " ions = " + frac("4/35", "2/16") + " × 0.50 = " + u("+0.46°")))),
 PART("(b)(i)",
      P(A("C has " + u("3 bond pairs and no lone pairs of electrons") + ". Based on VSEPR theory, the 3 " +
          u("bond pairs of electrons are arranged as far apart as possible to minimise") + " electronic " + u("repulsion") + ". Hence, its shape is " + u("trigonal planar") + "."))),
 PART("(b)(ii)",
      IMG(1, "bii"),
      P(A("Diagram shows the following:")),
      P(A(u("sp" + sup("2")) + " (label) hybrid orbital of C and O " + u("overlaps head on") + " to form " + u("σ") + " (label) bond.")),
      P(A(u("p") + " (label) orbital of C and O " + u("overlaps sideways") + " to form " + u("π") + " (label) bond."))),
 PART("(b)(iii)", IMG(1, "biii")),
 PART("(c)(i)",
      P(A("Amt of " + CL2 + " = " + frac(i("PV"), i("RT")) + " = " + frac("(50 × 1000)(2.00 × 10" + sup(M + "3") + ")", "8.31 × (250 + 273)") + " = " + u("0.0230") + " mol"))),
 PART("(c)(ii)",
      TBL(["", CL2 + " +", i("y") + "F" + sub(2) + " →", "2" + CL + "F" + "<sub><i>y</i></sub>".replace("<sub><i>y</i></sub>", sub(3))],
          ["initial / kPa", "50", "200", "0"],
          ["change / kPa", M + "50", M + "50" + i("y"), "+100"],
          ["final / kPa", "0", "200 " + M + " 50" + i("y"), "100"]),
      P(A("200 " + M + " 50" + i("y") + " + 100 = 150")),
      P(A(i("y") + " = 3")),
      P(A("Molecular formula of the product is " + CLF3)),
      P(A("Or")),
      P(A("When " + i("y") + " = 3")),
      TBL(["", CL2 + " +", "3F" + sub(2) + " →", "2" + CLF3],
          ["initial / kPa", "50", "200", "0"],
          ["change / kPa", M + "50", M + "150", "+100"],
          ["final / kPa", "0", "50", "100"]),
      P(A("Total pressure = 50 + 100 = 150 kPa")),
      P(A("Molecular formula of the product is " + CLF3))),
 PART("(c)(iii)",
      P(A(CLF3 + " has " + u("significant intermolecular forces of attraction") + " between molecules.")),
      P(A("Or")),
      P(A(CLF3 + " has a " + u("large/significant molecular size/volume with respect to the volume of the container") + ".")),
      P(A("Hence, " + CLF3 + " " + u("behaves less ideally/ " + CLF3 + " is not an ideal gas") + "."))),
 PART("(c)(iv)",
      P(A("Ability of an " + u("atom") + " to " + u("attract shared/bonding electrons") + " towards itself in a " + u("covalent bond") + "."))),
 PART("(c)(v)", IMG(1, "cv")),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)", IMG(2, "a")),
 PART("(b)(i)", P(A("Zn + 2OH" + sup(M) + ARROW + "ZnO + " + H2O + " + 2" + EMINUS))),
 PART("(b)(ii)",
      P(A("(+1.47) = " + EA + " " + M + " (" + M + "1.28)")),
      P(A(EA + " = " + u("+0.19") + " V"))),
 PART("(b)(iii)",
      P(A(DEL + i("G") + STD + " = " + M + "2(96500)(+1.47) = " + u(M + "284000 J mol" + sup(M + "1")) + " = " + u(M + "284 " + KJ) + " (3sf)"))),
 PART("(c)(i)",
      P(A("H" + sub(2) + " / hydrogen gas")),
      P(A(u("2H" + sup("+") + " + 2" + EMINUS + ARROW + "H" + sub(2))))),
 PART("(c)(ii)", P(A("From " + u(M + "1") + " to " + u(M + "3")))),
 PART("(c)(iii)", P(A("CH" + sub(3) + "COC" + L))),
 PART("(c)(iv)",
      IMG(2, "civ"),
      P(A("Condensation reaction of acyl chloride and phenol can also take place to form esters, giving a mixture of products."))),
 PART("(d)(i)",
      IMG(2, "di"),
      P(A("Phenylhydroxylamine is the least basic. The " + u("electronegative O/electron withdrawing " + M + "OH group decreases the availability of the lone pair of electrons on N for donation/protonation") + ".")),
      P(A(i("N") + "-methyl-4-aminophenol is the most basic. The " + u("electron donating " + M + "CH" + sub(3)) + " group " + u("increases the availability of the lone pair of electrons on N for donation/protonation") + "."))),
 PART("(d)(ii)",
      P(A(u("Energy released/change") + " when " + u("one mole of substance is completely burnt in excess oxygen") + " at " + u("standard conditions") + " of 298 K and 1 bar."))),
 PART("(d)(iii)",
      P(A(DEL + i("H") + STD + sub("r") + " = [(" + M + "3090) + (" + M + "726)] " + M + " (" + M + "3650) = " + u(M + "166") + " " + KJ))),
 PART("(d)(iv)",
      P(A(u("BE") + " requires reactants and products to be in " + u("gaseous state") + ", but in step 2, the reactants and products are " + u("not in gaseous state") + ". Hence, BE gives the poorer estimate."))),
 PART("(d)(v)", IMG(2, "dv")),
 PART("(d)(vi)",
      P(A("As the alcohol becomes " + u("bulkier/more branched/substituted") + ", the alkyl groups block " + u("the approach of phenylhydroxylamine/alcohol/nucleophile/electrophile") +
          ". Hence, the " + u("relative rate decreases/slower") + "."))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)",
      P(A(u(H3BO3 + " did not lose H") + sup("+"))),
      P(A("Or")),
      P(A(u(H3BO3 + " gains OH" + sup(M)))),
      P(A("Or")),
      P(A(u(H3BO3 + " and H" + sub(4) + "BO" + sub(4) + sup(M) + " do not differ by a H" + sup("+")) + "/ are " + u("not conjugate acid-base pair") + "."))),
 PART("(b)(i)", P(A("A Lewis acid is an " + b(u("electron/lone pair acceptor")) + "."))),
 PART("(b)(ii)", IMG(3, "bii")),
 PART("(b)(iii)", IMG(3, "biii")),
 PART("(b)(iv)",
      P(A("Boroxine has a high " + MR + "/molecular mass with " + u("large number of electrons/large electron cloud") + " and forms " + u("strong ") + b(u("intermolecular")) + " " +
          u("instantaneous dipole induced dipole interactions") + "."))),
 PART("(c)(i)",
      P(A(H2BO3M + " + " + H2O + RARR.strip() + " " + H3BO3 + " + OH" + sup(M))),
      P(A("Sodium borate reacts with water to give OH" + sup(M) + "."))),
 PART("(c)(ii)",
      P(A("5.4 × 10" + sup(M + "10") + " = " + frac("[H" + sup("+") + "]" + sup("2"), "0.06"))),
      P(A("[H" + sup("+") + "] = 5.69 × 10" + sup(M + "6") + " " + MDM + ".")),
      P(A("pH = " + M + "lg(5.69 × 10" + sup(M + "6") + ") = " + u("5.24")))),
 PART("(c)(iii)",
      P(A("5.4 × 10" + sup(M + "10") + " = " + frac("10" + sup(M + "8.8") + "[" + H2BO3M + "]", "[" + H3BO3 + "]"))),
      P(A("Or")),
      P(A("8.8 = " + M + "lg(5.4 × 10" + sup(M + "10") + ") + lg([" + H2BO3M + "]/[" + H3BO3 + "])")),
      P(A(frac("[" + H2BO3M + "]", "[" + H3BO3 + "]") + " = 0.34071")),
      P(A(frac("0.09" + i("x"), "0.06 × 0.025 " + M + " 0.09" + i("x")) + " = 0.34071")),
      P(A(i("x") + " = " + u("4.24 cm" + sup("3"))))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)",
      P(A("C" + sub(10) + "H" + sub(18) + "O + " + u("9[O]") + ARROW.rstrip() + " C" + sub(3) + "H" + sub(6) + "O + C" + sub(5) + "H" + sub(8) + "O" + sub(3) + " + " +
          u("2CO" + sub(2) + " + 2" + H2O)))),
 PART("(b)",
      TBL(["C" + sub(10) + "H" + sub(18) + "O + acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ARROW + b("E") + "<br>C" + sub(10) + "H" + sub(16) + "O" + sub(2),
           A(u("Primary alcohol") + " in geraniol<br>" + b("E") + " is a " + u("carboxylic acid"))],
          ["C" + sub(10) + "H" + sub(18) + "O + hot acidified KMnO" + sub(4) + ARROW + b("F") + " + " + b("G") + "<br>C" + sub(3) + "H" + sub(6) + "O and C" + sub(5) + "H" + sub(8) + "O" + sub(3),
           A(u("Two C=C") + "<br>" + b("F") + " has " + u("ketone"))],
          ["C" + sub(10) + "H" + sub(18) + "O + H" + sub(2) + "/Ni" + ARROW + "C" + sub(10) + "H" + sub(22) + "O.",
           A(u("Reduction") + "<br>" + u("Two C=C"))],
          [b("F") + " and " + b("G") + " + iodoform test" + ARROW + "yellow ppt",
           A(u("Oxidation") + "<br>" + b("F") + " and " + b("G") + " are " + u("methyl ketones"))]),
      IMG(4, "b"),
      P(A(b("E") + " and Geraniol must correspond"))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A("To generate the " + b(u("stronger/better nucleophile")) + " thiophenolate."))),
 PART("(a)(ii)", IMG(5, "aii")),
 PART("(b)(i)", IMG(5, "bi")),
 PART("(b)(ii)",
      IMG(5, "bii"),
      P(A("Step 1: KMnO" + sub(4) + "(aq), H" + sub(2) + "SO" + sub(4) + "(aq), heat")),
      P(A("Step 2: PC" + L + sub(5)))),
 PART("(b)(iii)",
      P(A("Polymers are " + u("macromolecules") + " built from" + u(" monomers") + " with " + u("average molar mass of at least 1000") + " or " + u("at least 100 repeat units") + "."))),
 PART("(b)(iv)", P(A("PET: condensation")), P(A("PIB: addition"))),
 PART("(c)(i)", P(A(u(KSP + " = [Ag" + sup("+") + "][" + THIO + "] mol" + sup("2") + " dm" + sup(M + "6"))))),
 PART("(c)(ii)",
      P(A(KSP + " = [Ag" + sup("+") + "][" + THIO + "]")),
      P(A("At the point when precipitation just begins,")),
      P(A("[Ag" + sup("+") + "] = (1.2 × 10" + sup(M + "16") + ") / 0.03 = " + u("4.0 × 10" + sup(M + "15")) + " " + MDM)),
      P(A("Mole of Ag" + sup("+") + " in 500 cm" + sup("3") + " = 2.0 × 10" + sup(M + "15"))),
      P(A("Mass of AgNO" + sub(3) + " needed = 2.0 × 10" + sup(M + "15") + " × 170 = " + u("3.4 × 10" + sup(M + "13") + " g")))),
 PART("(c)(iii)",
      P(A("[" + THIO + "] = (1.2 × 10" + sup(M + "16") + ") / (1.0 × 10" + sup(M + "4") + ") = " + u("1.2 × 10" + sup(M + "12")) + " " + MDM)),
      P(A("As the remaining thiophenolate ions are " + u("less than 1.0 × 10" + sup(M + "6") + " " + MDM) + ", the treated wastewater " + u("meets the requirement") + "."))),
 PART("(c)(iv)",
      P(A("Ag" + sup("+") + " + 2NH" + sub(3) + ARROW + "[Ag(NH" + sub(3) + ")" + sub(2) + "]" + sup("+"))),
      P(A("Formation of the complex ion [Ag(NH" + sub(3) + ")" + sub(2) + "]" + sup("+") + " decreases the [Ag" + sup("+") + "]. Hence, the " + u("position of equilibrium") + " 5.1 " +
          u("shifts right ") + "to increase [Ag" + sup("+") + "], which " + u("increases the solubility of AgC" + L) + "."))),
 PART("(d)",
      P(A(b(u("Al" + sub(2) + "O" + sub(3) + " + 6H" + sup("+") + ARROW + "2Al" + sup("3+") + " + 3" + H2O)))),
      P(A(b(u("Al" + sub(2) + "O" + sub(3) + " + 2OH" + sup(M) + " + 3" + H2O + ARROW + "2Al(OH)" + sub(4) + sup(M))))),
      P(A("Aluminium oxide is " + b(u("amphoteric")) + " and " + b(u("would not be present to capture heavy metals when the wastewater is too acidic or basic")) + ".")),
      P(A("Or")),
      P(A("Aluminium oxide is " + b(u("insoluble/still present at pH 7")) + " and " + b(u("can capture heavy metals")) + "."))),
]
# ------------------------------------------------------------------ Q6
W[6] = [
 PART("(a)(i)", P(A("+5"))),
 PART("(a)(ii)",
      P(A(u(KSP + " = [Ca" + sup("2+") + "]" + sup("5") + " [PO" + sub(4) + sup("3" + M) + "]" + sup("3") + " [OH" + sup(M) + "]")))),
 PART("(a)(iii)",
      P(A(u("H" + sup("+") + " reacts with OH" + sup(M) + ",") + " decreasing the [OH" + sup(M) + "]. Hence, the " + u("position of equilibrium shifts to the right") +
          " to increase [OH" + sup(M) + "], which also " + u("increases the solubility of hydroxyapatite") + "."))),
 PART("(a)(iv)",
      P(A(u(CL + sup(M) + ": 0.181") + " nm; " + u("F" + sup(M) + ": 0.136 ") + "nm " + i("Accept either radius"))),
      P(A("The " + u("ionic radius of the other group 17 halides are larger than OH" + sup(M) + "/F" + sup(M)) + " and are unable to replace OH" + sup(M) + "."))),
 PART("(a)(v)",
      P(A(u("Oxidising power of halogen decreases down the group") + ".")),
      TBL(["From " + i("Data Booklet"), EA + " / V"],
          ["F" + sub(2) + " + 2" + EMINUS + RARR + "2F" + sup(M), "+2.87"],
          [CL2 + " + 2" + EMINUS + RARR + "2" + CL + sup(M), "+1.36"],
          ["Br" + sub(2) + " + 2" + EMINUS + RARR + "2Br" + sup(M), "+1.07"],
          ["I" + sub(2) + " + 2" + EMINUS + RARR + "2I" + sup(M), "+0.54"]),
      P(A("This is evident in the " + u("less positive " + EA + " value down the group") + ", which shows a lower tendency of halogen to accept electron/be reduced."))),
 PART("(b)(i)",
      TBL([b("cathode or anode"), b("half-equation(s)")],
          ["titanium implant: cathode", "Ag" + sup("+") + " + " + EMINUS + ARROW + "Ag"],
          ["silver electrode: anode", "Ag" + ARROW + "Ag" + sup("+") + " + " + EMINUS])),
 PART("(b)(ii)",
      P(A("Amt of Ag = (5 × 10" + sup(M + "3") + ") / 107.9 = 4.6339 × 10" + sup(M + "5") + " mol")),
      P(A("Amt of " + EMINUS + " = " + u("4.6339 × 10" + sup(M + "5")) + " mol")),
      P(A("4.6339 × 10" + sup(M + "5") + " mol × 96500 = 0.02 × " + i("t"))),
      P(A(i("t") + " = " + u("224 s") + " = 3.73 min"))),
 PART("(c)(i)", P(A("10"))),
 PART("(c)(ii)", IMG(6, "cii")),
 PART("(c)(iii)", P(A("It is bonded to 4 different (groups of) atoms."))),
 PART("(c)(iv)", IMG(6, "civ")),
 PART("(c)(v)", P(A("Bacteria in the mouth produce acids which can " + u("hydrolyse/break peptide bonds") + " in collagen."))),
 PART("(d)(i)", IMG(6, "di")),
 PART("(d)(ii)", P(A("KMnO" + sub(4) + "(aq), H" + sub(2) + "SO" + sub(4) + "(aq) or NaOH(aq), cold"))),
 PART("(d)(iii)",
      P(A("Reaction in " + b("(ii)") + " requires " + b(u("more reagents")) + ", compared to a single peroxide-based agent.")),
      P(A("Or")),
      P(A("Reaction in " + b("(ii)") + " involves " + b(u("coloured KMnO" + sub(4) + " or brown MnO" + sub(2))) + " (only when alkaline condition is suggested), compared to a colourless peroxide-based agent."))),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    assert not re.search(r"\[\d+\]", re.sub(r"<[^>]+>", "", h)), (qn, re.findall(r".{20}\[\d.{10}", h))
    out[str(qn)] = h

# labels = the question parts that carry a mark badge (answerable parts)
qs = {r["question_number"]: r for r in json.loads((QDIR / "questions.json").read_text())}
for qn in sorted(W):
    want = []
    for blk in qs[qn]["content_html"].split('<div class="qpart">')[1:]:
        m = re.match(r'<span class="pl">([^<]*)</span>', blk)
        body = blk[:blk.index('</div>\n') if '</div>\n' in blk else len(blk)]
        if 'class="mk"' in body: want.append(m.group(1))
    have = re.findall(r'<span class="lab">([^<]*)</span>', out[str(qn)])
    assert want == have, (qn, want, have)

assets, seen = [], {}
for qn, slot in ASSETS:
    seen[qn] = seen.get(qn, 0) + 1
    assets.append({"question": qn, "slot": "ans-" + slot, "path": _path(qn, slot), "offset": seen[qn]})
(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "worked solutions,", sum(h.count('class="lab"') for h in out.values()), "parts,", len(assets), "answer assets")
for a in assets: print("  Q%d %-8s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))
