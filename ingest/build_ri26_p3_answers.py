"""Hand transcription of the RI 2026 H2 Prelim Paper 3 (9476/03) suggested solutions
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's 10-page answers PDF and its docx twin (flat grid, floating drawings, OLE equations), so the text is typed.
Underlined keywords follow the docx runs. There are no mark breakdowns and no red marking notes; the one black comment
("Explanation using LCP ...", 4(c)(ii)) is kept as a span.note.

Run from the repo root:
    python3 ingest/build_ri26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_ri26_p3.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6, as build_ri26_p2_answers.py): div.worked-solution > div.part > (span.lab + div.body);
answers in span.ans with <u> on the school's underlined keywords; figures are bare img.ws-fig[data-asset] (the user snips
them: RI_H2_P3_Q<n>_ans-<slot>_2026.png); tables are table.cmp.
The school labels the Q3 evidence table "3(c)(iii)" a second time; it answers 3(c)(iv) and is filed there.
School wording is kept where the chemistry is off (see RULED_FIXES / the handoff); plain typos are fixed silently.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "RI_H2_P3", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
CLM = CL + sup(M)
HCL = "HC" + L
AGCL = "AgC" + L
AL = "A" + L
DEL = "Δ"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def rad(s): return '√<span style="text-decoration:overline">%s</span>' % s
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
def BUL(*items): return [P(A(x)) for x in items]
def NOTE(t): return P(N(t))
def eq(s): return P(A(s))
RARR = "⇌"
ARROW = " ⟶ "
H2O = "H" + sub(2) + "O"
MDM = "mol dm" + sup(M + "3")
PLS = '<span class="pl-sym">⦵</span>'
STD = "<sup>" + PLS + "</sup>"
def kJ(): return "kJ mol" + sup(M + "1")
DGS = DEL + i("G") + "<sub>r</sub>" + STD        # worked solutions never use .stk (CSS is .stem-only): sub then sup
ES = i("E") + STD
K, KSP, KB = i("K"), i("K") + sub("sp"), i("K") + sub("b")
KK = i("k")
BZ = "C" + sub(6) + "H" + sub(5) + "COO"
BZM = BZ + sup(M)
TMA_O = "(CH" + sub(3) + ")" + sub(3) + "NO"
TMA = "(CH" + sub(3) + ")" + sub(3) + "N"
DMA = "(CH" + sub(3) + ")" + sub(2) + "NH"
S8, S82, S42 = "S" + sub(8), "S" + sub(8) + sup("2" + M), "S" + sub(4) + sup("2" + M)
CO3 = "CO" + sub(3) + sup("2" + M)
def orb(x): return "3d" + sub(x)


def long_arrow(w):
    return ('<span style="display:flex;align-items:center;width:%sem;margin:0 auto">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.55em;margin-left:-.3em;line-height:1">►</span></span>' % w)
def over(top, arrow, bottom=None):
    small = '<span style="display:block;font-size:.8em;line-height:1.15">%s</span>'
    return ('<span style="display:inline-block;vertical-align:middle;text-align:center;line-height:1.1;padding:0 .2em">'
            + small % top + '<span style="display:block;line-height:1">%s</span>' % arrow + small % (bottom or "&nbsp;") + "</span>")
def under(sym, label):
    return ('<span style="display:inline-block;text-align:center;vertical-align:middle;line-height:1.25">%s'
            '<span style="display:block;font-size:.85em">%s</span></span>' % (sym, label))
def sp(letter, formula): return under(b(letter), "(" + formula + ")")
KMN = over("KMnO" + sub(4) + "<br>H" + sub(2) + "SO" + sub(4), long_arrow(3.5), "heat")
SC_AB = sp("A", "C" + sub(11) + "H" + sub(18) + "O" + sub(2)) + " " + KMN + " " + sp("B", "C" + sub(11) + "H" + sub(18) + "O" + sub(4))
SC_CDE = (sp("C", "C" + sub(11) + "H" + sub(14) + "O" + sub(2)) + " " + KMN + " " + sp("D", "C" + sub(8) + "H" + sub(10) + "O" + sub(4)) +
          " + " + sp("E", "C" + sub(3) + "H" + sub(4) + "O" + sub(3)))
SC_BC = (sp("B", "C" + sub(11) + "H" + sub(18) + "O" + sub(4)) + " " + over("conc. H" + sub(3) + "PO" + sub(4), long_arrow(3.5), "heat") + " " +
         sp("C", "C" + sub(11) + "H" + sub(14) + "O" + sub(2)))
def DED(*items): return "".join("<p>• %s</p>" % x for x in items)
CIV_TABLE = ('<table class="cmp">' + "".join("<tr><td>%s</td><td>%s</td></tr>" % r for r in [
    ("<b>Evidence</b>", "<b>Deduction</b>"),
    (b("A") + " and " + b("B") + " do not react with K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + "<br>(or " + b("A") + " and " + b("B") + ": test I)",
     DED(b("A") + " and " + b("B") + " did not undergo oxidation with K" + sub(2) + "Cr" + sub(2) + "O" + sub(7),
         b("A") + " and " + b("B") + " each contain two tertiary alcohols.")),
    (b("A") + ": reaction 1<br><br>" + b("C") + ": reaction 3",
     DED("Strong oxidation occurred.", "C=C bonds in " + b("A") + " and " + b("C") + " were cleaved.")),
    ("1 mol of " + b("A") + " reacted with 1 mol of Br" + sub(2) + "<br>(or " + b("A") + ": test III)<br><br>1 mol of " + b("C") + " reacted with 2 mol of Br" + sub(2) + "<br>(or " + b("C") + ": test III)",
     DED("Electrophilic addition occurred", b("A") + " contains 1 C=C", b("C") + " contains 2 C=C")),
    (b("B") + ": reaction 2",
     DED("Dehydration / elimination of H" + sub(2) + "O occurred.", b("C") + " contains 2 C=C")),
    ("When oxidised by I" + sub(2) + ", NaOH, 1 mol of " + b("B") + ", " + b("C") + " or " + b("D") + " gave 2 mol of CHI" + sub(3) + "<br>(or " + b("B") + ", " + b("C") + ", " + b("D") + ": test III)",
     DED(b("B") + ", " + b("C") + " and " + b("D") + " each contains 2 –COCH" + sub(3) + " groups")),
]) + "</table>")

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
RULED_FIXES = []

# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)", P(A("A transition element is a d block element whose " + u("atom has an incomplete d subshell") + ", " + b(u("or")) +
                 " which can give rise to " + u("cations with an incomplete d subshell") + "."))),
 PART("(b)(i)", eq("Fe" + sup("2+") + ": 1s" + sup(2) + "2s" + sup(2) + "2p" + sup(6) + "3s" + sup(2) + "3p" + sup(6) + "3d" + sup(6))),
 PART("(b)(ii)",
      P(A("Copper has more protons and a " + u("higher nuclear charge") + " than iron. However, the " +
          u("electrons are added to the inner 3d subshell, which provides more shielding") + " between the nucleus and the outer 4s electrons.")),
      P(A("The increase in shielding effect offsets the higher nuclear charge. Hence, the " +
          u("electrostatic attraction between the nucleus and the outer 4s electrons increases minimally") + " and the atomic radii are similar."))),
 PART("(b)(iii)",
      P(A("In the Haber process, Fe(s) provides sites on which N" + sub(2) + "(g) and H" + sub(2) + "(g) can be " + u("adsorbed") +
          ". The adsorption is possible because " + u("Fe(s) possesses a partially filled 3d subshell") + ". It provides " +
          u("3d electrons to form bonds with reactant molecules") + ".")),
      P(A("The adsorption leads to an increase in reaction rate.")),
      *BUL("It " + u("weakens the covalent bonds") + " in N" + sub(2) + " and H" + sub(2) + u(" thus reducing the activation energy") + " for the reaction.",
           "It " + u("increases the concentration of the reactant molecules") + " at the Fe surface. Hence, the reactant molecules can come into " +
           u("close contact") + ", with " + u("proper orientation") + ", for reaction."),
      P(A("Once formed, NH" + sub(3) + " molecules can easily " + u("desorb") + " from the Fe surface so that the " +
          u("active sites are exposed for further reaction") + " (" + u("regeneration of catalyst") + ")."))),
 PART("(c)(i)", eq("Oxidation number = +2")),
 PART("(c)(ii)",
      P(A("[Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + " is a complex ion with Co" + sup("2+") + " as the central metal ion with an electronic configuration of [Ar]3d" + sup(7) + ".")),
      P(A("The presence of the H" + sub(2) + "O " + u("ligands") + " causes the " + u("splitting") + " of the five 3d orbitals in the Co" + sup("2+") +
          " ion into two sets of slightly " + u("different energy levels.") + "")),
      P(A("Since the 3d subshell is " + u("partially filled") + ", the " + u("electrons from the lower energy d orbitals") + " can " + u("absorb energy") +
          " corresponding to certain wavelengths from the visible spectrum and " + u("get promoted to the higher energy d orbitals") + ".")),
      P(A("Such d-d transitions are responsible for the colour observed. " + u("The colour observed is the complement of the colour absorbed") + "."))),
 PART("(c)(iii)",
      P(A("Either")),
      P(A("the complexes contain " + u("different ligands") + ", H" + sub(2) + "O and " + CLM + ", and these ligands " + u("split the d-orbitals of Co" + sup("2+") + " to a different extent"))),
      P(A("Or")),
      P(A("the complexes have " + u("different shapes thus the d-orbitals of Co" + sup("2+") + " have different splitting patterns") + " with different energy gaps.")),
      P(A("Thus different wavelength of visible light is absorbed, showing a different complementary colour."))),
 PART("(c)(iv)",
      P(A("There is more water in a humid environment, this will cause the " + u("concentration of all ions in solution to decrease") + ".")),
      P(A("The equilibrium system will counteract this by " + u("favouring the backward reaction") + " which produces more ions, increasing the concentration of ions in solution. "
          "Thus producing more [Co(H" + sub(2) + "O)" + sub(6) + "]" + sup("2+") + ", intensifying the " + u("pink colour") + "."))),
 PART("(d)(i)", IMG(1, "di")),
 PART("(d)(ii)",
      P(A("In a square planar environment, the four ligands approach the central metal ion " + u("along the x and y axes") + " (which is on the xy plane).")),
      P(A(orb("xy") + " is at a higher energy level than " + orb("xz") + " and " + orb("yz") + " because the " + u(orb("xy") + " orbital has the greatest electron density in between the x and y axes") +
          " (which is also on the xy plane) while the " + orb("xz") + " and " + orb("yz") + " orbitals have no electron density on the xy plane. Hence the " + orb("xy") +
          " orbital " + u("experiences more repulsion") + " with the approaching ligands."))),
 PART("(e)",
      P(A(b("X") + ": Cu(OH)" + sub(2))),
      P(A(b("Y") + ": [CuC" + L + sub(4) + "]" + sup("2" + M)))),
]

# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)", P(A("Lattice energy of Li" + sub(2) + "S is the " + u("energy released when 1 mole of Li" + sub(2) + "S(s) is formed from Li" + sup("+") + "(g) and S" + sup("2" + M) + "(g) at standard conditions") +
                    " of 298 K and 1 bar."))),
 PART("(a)(ii)", IMG(2, "aii"),
      P(A("By Hess’ Law,")),
      P(A("LE = –400 – 2(+519) – 2(+159) – (+279) + (–447)")),
      P(A("= –2482 = –2480 " + kJ() + " (3 s.f.)"))),
 PART("(a)(iii)",
      P(A("| Lattice energy | ∝ | " + frac(i("q") + sub("+") + " " + i("q") + sub(M), i("r") + sub("+") + " + " + i("r") + sub(M)) + " |")),
      P(A("Since the " + u("ionic radius of S" + sub(2) + sup("2" + M) + " is larger than that of S" + sup("2" + M)) +
          " and the ionic charge of the anions is the same, the numerical value of lattice energy of Li" + sub(2) + "S" + sub(2) + " is " + u("smaller") + " than that of Li" + sub(2) + "S."))),
 PART("(b)(i)", eq("2Li(s) + 2H" + sub(2) + "O(l)" + ARROW + "2LiOH(aq) + H" + sub(2) + "(g)")),
 PART("(b)(ii)", IMG(2, "bii")),
 PART("(b)(iii)", P(A("Sulfur does not conduct electricity. Carbon in the form of graphite helps to conduct electricity."))),
 PART("(c)", P(A("After several cycles of charging and discharging, the accumulated " + u("Li" + sub(2) + "S") + " crystals " + u("occupy a larger volume") +
                 " as compared to the volume once occupied by S" + sub(8) + " molecules. This causes the cathode to “crack” after a few cycles of charging and discharging."))),
 PART("(d)(i)", eq(S8 + " + 16e" + sup(M) + ARROW + "8S" + sup("2" + M))),
 PART("(d)(ii)", eq("Q = 0.500 × 10 × 60 × 60 = 1.80 × 10" + sup(4) + " C")),
 PART("(e)(i)",
      eq(S8 + " + 2e" + sup(M) + " " + RARR + " " + S82 + "&emsp;+2.38 V"),
      eq(S82 + " + 2e" + sup(M) + " " + RARR + " 2" + S42 + "&emsp;+2.15 V"),
      eq("2" + S82 + ARROW + S8 + " + 2" + S42),
      eq(i("E") + "<sub>cell</sub> = +2.15 – (+2.38) = −0.23 V < 0"),
      P(A("Reaction is not spontaneous.")),
      P(A(S82 + " does not undergo disproportionation to " + S8 + " and " + S42 + "."))),
 PART("(e)(ii)",
      eq(i("x") + " = " + DGS + " of reaction 3 = –459 + (–415) = −874 " + kJ()),
      eq(S8 + " + 4e" + sup(M) + ARROW + "2" + S42),
      eq(DGS + " = −" + i("nFE") + STD),
      eq("−874 × 10" + sup(3) + " = −4 × 96500 × " + ES),
      eq(ES + " = +2.26 V")),
]

# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)",
      P(A("Relative basicities:")), P(A("ethylamine > phenylamine > ethanamide")),
      P(A("In ethylamine, the " + u("electron-donating CH" + sub(3) + "CH" + sub(2) + "– group increases the availability of the lone pair of electrons on nitrogen,") +
          " making it " + u("more available for coordination to a proton than in phenylamine") + ".")),
      P(A("In phenylamine, the orbital containing the lone pair of electrons on the nitrogen atom overlaps with the π electron cloud of the benzene ring, allowing the " +
          u("lone pair of electrons on the nitrogen atom to be delocalised into the benzene ring, making it less available for coordination to a proton") + " than that in ethylamine.")),
      P(A("In ethanamide, the orbital containing the lone pair of electrons on the nitrogen atom overlaps with the π electron cloud of the adjacent C=O bond and the " +
          u("lone pair of electrons is delocalised into the C=O bond") + " making it " + u("unavailable") + " for coordination to a proton."))),
 PART("(a)(ii)", IMG(3, "aii"),
      *BUL("Compared to TMPD, DMAN has the amine N groups in close proximity. Intramolecular interactions like hydrogen bonding are possible.",
           "DMAN–H" + sup("+") + " is " + u("stabilised") + " by the intramolecular hydrogen-bonding which makes it " + u("less likely") + " to take in another proton.",
           "As the " + u("lone pairs on N are involved in") + " intramolecular hydrogen-bonds, they are " + u("less available") + " to take in another proton.")),
 PART("(b)(i)",
      P(A("Polymer " + b("W") + " " + u("lacks electron-rich sites") + " for attack by electrophiles and " + u("electron-poor sites for attack") + " by nucleophiles.")),
      P(A("The " + u("relatively strong") + " C–C " + u("bonds") + " and C–H " + u("bonds") + " do not break under normal conditions."))),
 PART("(b)(ii)", IMG(3, "bii")),
 PART("(b)(iii)", P(A("The " + u("hydrogen bonding") + " between the N–H groups on one polymer chain of " + b(u("X")) + " and C=O groups of chain of " + b("X") + " is " +
                      u("stronger than the instantaneous dipole-induced dipole interactions between chains of polymer " + b("W")) + ", requiring more energy to break."))),
 PART("(c)(i)", P(A(u("Tertiary") + " alcohol"))),
 PART("(c)(ii)", P(A("CHI" + sub(3)))),
 PART("(c)(iii)", P(A("Oxidation reaction")), IMG(3, "ciii")),
 PART("(c)(iv)", CIV_TABLE, IMG(3, "civ")),
]

# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)",
      P(A("Down the group, cationic radius increases, resulting in a " + u("lower charge density") + " and " + u("weaker polarising power") + " of the cations.")),
      P(A("Consequently, there is " + u("decreasing extent of distortion of the electron cloud of the " + CO3) + " anion and hence " +
          u("decreasing extent of weakening of covalent bonds within the " + CO3) + " anion.")),
      P(A(u("More heat energy") + " is required to break the covalent bonds within the " + CO3 + " anion, causing the " + u("decomposition temperature / thermal stability to increase") + "."))),
 PART("(a)(ii)",
      P(A("From the " + i("Data Booklet") + ", ionic radius of Mg" + sup("2+") + " is " + u("0.065 nm") + " and ionic radius of Fe" + sup("2+") + " is " + u("0.061 nm") +
          ". " + b("OR") + " The cationic radius of Fe" + sup("2+") + " is smaller than that of Mg" + sup("2+") + ".")),
      P(A("The " + u("charge density of Fe" + sup("2+") + " is greater") + ". This increases extent of weakening of covalent bonds within the " + CO3 + " anion. " +
          u("FeCO" + sub(3) + " will decompose at a lower temperature than MgCO" + sub(3)) + "."))),
 PART("(b)(i)", eq(KSP + " of " + AGCL + " = [Ag" + sup("+") + "][" + CLM + "]")),
 PART("(b)(ii)",
      P(A("To achieve maximum separation, the concentration of Ag" + sup("+") + " has to be at the highest just before " + AGCL + " starts to precipitate out, i.e., [Ag" + sup("+") +
          "] in the solution is just high enough to make the ionic product of " + AGCL + " = " + KSP + " of " + AGCL + ".")),
      eq(KSP + " of " + AGCL + " = [Ag" + sup("+") + "][" + CLM + "]"),
      eq("1.77 × 10" + sup(M + "10") + " = [Ag" + sup("+") + "] (1.00 × 10" + sup(M + "2") + ")"),
      eq("[Ag" + sup("+") + "] = 1.77 × 10" + sup(M + "8") + " " + MDM)),
 PART("(b)(iii)",
      eq("When [Ag" + sup("+") + "] = 1.77 × 10" + sup(M + "7") + " " + MDM + ","),
      eq(KSP + " of " + BZ + "Ag = [Ag" + sup("+") + "] [" + BZM + "]"),
      eq("2.50 × 10" + sup(M + "13") + " = (1.77 × 10" + sup(M + "8") + ") [" + BZM + "]"),
      eq("[" + BZM + "] = 1.41 × 10" + sup(M + "5") + " " + MDM),
      P(A("Percentage of " + BZM + " remaining in the solution = " + frac("1.41 × 10" + sup(M + "5"), "8.00 × 10" + sup(M + "3")) + " × 100% = 0.176%"))),
 PART("(b)(iv)",
      P(A("Maximum concentration of benzoate ion allowed = 1.50 ppm")),
      eq("[" + BZM + "]<sub>max</sub> = 1.50 mg dm" + sup(M + "3") + " = 0.00150 g dm" + sup(M + "3")),
      P(A("= " + frac("0.00150", "121") + " = 1.24 × 10" + sup(M + "5") + " " + MDM)),
      P(A("From " + b("4(b)(iii)") + ", [" + BZM + "] remaining in the solution is 1.41 × 10" + sup(M + "5") + " " + MDM + ".")),
      P(A("Since the [" + BZM + "] remaining in the solution is greater than the allowable limit, this method is ineffective in treating wastewater."))),
 PART("(c)(i)", eq("Ag" + sup("+") + "(aq) + 2NH" + sub(3) + "(aq) " + RARR + " [Ag(NH" + sub(3) + ")" + sub(2) + "]" + sup("+") + "(aq)")),
 PART("(c)(ii)",
      P(A("Upon addition of NH" + sub(3) + ", formation of the [Ag(NH" + sub(3) + ")" + sub(2) + "]" + sup("+") + " complex will cause " + u("[Ag" + sup("+") + "] to decrease") + ".")),
      P(A("When [Ag" + sup("+") + "] decreases, the " + u("ionic product of " + AGCL + " will drop below its " + KSP) + ", allowing " + AGCL + " to dissolve. However, the " +
          u("ionic product of " + BZ + "Ag will still be more") + " than " + KSP + " of " + BZ + "Ag and thus " + BZ + "Ag does not dissolve.")),
      NOTE("Explanation using LCP is insufficient to explain why all ppt. dissolves")),
 PART("(d)(i)", eq("CH" + sub(3) + "CH" + sub(2) + "C" + L + ", A" + L + "C" + L + sub(3))),
 PART("(d)(ii)",
      P(A("If benzene were to be converted to phenylethene in one step, it requires the use of " + u("chloroethene") + " as a reagent.")),
      P(A("The p-orbital of " + CL + " " + u("overlaps") + " with the pi electron cloud of C=C, lone pair of electron in the p-orbital of " + CL + " " + u("delocalise") +
          " into C=C bond, this results in " + u("partial double bond character/strengthening of the C" + M + "C" + L + " bond") + " in chloroethene, hence more energy is required to break the C" + M + CL +
          " bond to form the electrophile."))),
 PART("(d)(iii)", eq("Na")),
 PART("(d)(iv)", P(A("Nucleophilic substitution"))),
 PART("(d)(v)", IMG(4, "dv")),
]

# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)",
      P(A("Hydrogen chloride is thermally stable (does not decompose).")),
      P(A("Hydrogen bromide and hydrogen iodide thermally decompose to give hydrogen gas and their respective halogens as shown in the following equation.")),
      eq("2HX " + RARR + " H" + sub(2) + " + X" + sub(2) + " (where X = Br and I)"),
      P(A("Since the bond energy decreases from H–" + CL + " to H–Br to H–I, the bond strength decreases in the same order.")),
      P(A("Thus, the thermal stability of the hydrogen halides decreases from " + HCL + " to HBr to HI."))),
 PART("(b)(i)", eq("NH" + sub(3) + " + H" + sub(2) + "O " + RARR + " NH" + sub(4) + sup("+") + " + OH" + sup(M))),
 PART("(b)(ii)",
      eq("NH" + sub(3) + "(aq) + H" + sub(2) + "O(l) " + RARR + " NH" + sub(4) + sup("+") + "(aq) + OH" + sup(M) + "(aq)"),
      P(A(KB + " = " + frac("[NH" + sub(4) + sup("+") + "][OH" + sup(M) + "]", "[NH" + sub(3) + "]"))),
      P(A("Since NH" + sub(3) + " is a weak base with a small " + KB + ", [NH" + sub(3) + "]<sub>eqm</sub> ≈ [NH" + sub(3) + "]<sub>initial</sub> = 0.01 ÷ 0.25 = " + u("0.0400 " + MDM))),
      P(A("[OH" + sup(M) + "] = " + rad(KB + " × [NH" + sub(3) + "]") + " = " + rad("(1.8 × 10" + sup(M + "5") + ") × 0.04") + " = " + u("8.485 × 10" + sup(M + "4")) + " " + MDM + ".")),
      P(A("pOH = –lg (8.485 × 10" + sup(M + "4") + ") = 3.071 OR 3.076")),
      P(A("pH = 14 – 3.071 = " + u("10.9")))),
 PART("(c)(i)", eq("NH" + sub(4) + sup("+") + "(aq) + H" + sub(2) + "O(l) " + RARR + " NH" + sub(3) + "(aq) + H" + sub(3) + "O" + sup("+") + "(aq)")),
 PART("(c)(ii)", eq("12.5 cm" + sup(3))),
 PART("(d)(i)",
      P(A("Cis-trans isomerism.")),
      P(A("There is restricted rotation about the C=C bond in EPA and there are also two different groups attached to each C atom of the C=C bond."))),
 PART("(d)(ii)",
      P(A("Homolytic fission of the C–H bond results in the formation of a " + u("more stable free radical intermediate " + b("Q1")) + ".")),
      P(A("The orbital containing the unpaired electron on the radical C atom can " + u("overlap with the π electron cloud of adjacent p-orbitals of C=C") +
          ", allowing the electrons to be " + u("delocalised") + " resulting in a resonance stabilised intermediate."))),
 PART("(d)(iii)", IMG(5, "diii")),
 PART("(e)(i)",
      eq("Pathway 1: rate = " + KK + sub(1) + " [" + TMA_O + "]"),
      eq("Pathway 2: rate = " + KK + sub(2) + "[" + TMA_O + "]")),
 PART("(e)(ii)",
      eq("rate = " + KK + sub(1) + " [" + TMA_O + "] + " + KK + sub(2) + "[" + TMA_O + "]"),
      P(A(b("OR"))),
      eq("rate = (" + KK + sub(1) + " + " + KK + sub(2) + ")[" + TMA_O + "]")),
 PART("(e)(iii)", IMG(5, "eiii"), eq(i("t") + sub("½") + " = 20 hours")),
 PART("(e)(iv)",
      eq(i("t") + sub("½") + " = " + frac("ln 2", KK) + " since " + KK + " = (" + KK + sub(1) + " + " + KK + sub(2) + ")"),
      eq("20 = " + frac("ln 2", "0.030 + " + KK + sub(2))),
      eq(KK + sub(2) + " = 0.00466"),
      P(A(TMA + " is formed in greater proportion than " + DMA + "."))),
 PART("(e)(v)",
      eq("Rate of production of " + TMA + " = " + KK + sub(1) + "[" + TMA_O + "]"),
      eq("Rate of production of " + DMA + " = " + KK + sub(2) + "[" + TMA_O + "]"),
      P(A("Since time taken for both reactions are the same,")),
      eq("[" + TMA + "] ∝ rate" + sub(1) + " ∝ " + KK + sub(1) + "[" + TMA_O + "]"),
      eq("[" + DMA + "] ∝ rate" + sub(2) + " ∝ " + KK + sub(2) + "[" + TMA_O + "]"),
      P(A("Ratio of products formed: " + frac("[" + TMA + "]", "[" + DMA + "]") + " = " + frac(KK + sub(1) + "[" + TMA_O + "]", KK + sub(2) + "[" + TMA_O + "]") + " = " + frac(KK + sub(1), KK + sub(2)))),
      P(A("Since " + u("rate constant is a constant at the same temperature") + ", the ratio of products formed is also a constant at the same temperature."))),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    for q, old, new, n in RULED_FIXES:
        if q == qn:
            assert h.count(old) == n, (qn, old, h.count(old)); h = h.replace(old, new)
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
