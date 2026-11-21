"""Hand transcription of the RVHS 2026 H2 Prelim Paper 3 (9476/03) suggested solutions (10-page PDF + docx twin; the docx keeps the
equations as MathType objects and the figures as ChemDraw pictures, and the school's Chemical/Wingdings glyphs print wrongly in the PDF,
so the text is typed from the docx and the ten answer figures are snipped from the Word PDF) -> worked_solutions.json +
answer_assets.json (feeds gen_answers_migration.py --type structured).
Underlined keywords follow the docx runs. There are no mark breakdowns and no red marking notes.

Run from the repo root:
    python3 ingest/build_rvhs26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_rvhs26_p3.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u>
on the school's underlined keywords; figures are bare img.ws-fig[data-asset] (RVHS_H2_P3_Q<n>_ans-<slot>_2026.png);
tables are table.cmp. Editorial defaults (standing rulings): typos and grammar fixed, short forms spelled in full; see FIXES.

FIXES made to the school's answers (listed to the user):
  1(b)(i)  the energy-cycle arrow label printed "-417" in the school's PDF; the question gives -4175 and the school's own working
           below the cycle uses -4175, so the cycle snip carries -4175 (the missing 5 is added on a scratch copy of the page);
  2(d)(iii) "226.2 + 100n = 13426" -> "194.2 + 100n = 13426": the school's own line, 2[1.0 + 32.1 + 3(16.0)] + 2(16.0), is 194.2, not
           226.2 (R is -SO3H). n = 132.3, so the school's n = 132 stands;
  2(c)(iii) "assumes that the all species" -> "assumes that all species"; 2(d)(iii) "repeat unit" -> "repeat units";
  2(a) "liquify" -> "liquefy"; 2(b)(v) "in turns" -> "in turn";
  4(b)(i)  "side-way" -> "sideways", "each N atoms" -> "each N atom"; 4(d) "is overlaps" -> "overlaps", "(2)p" -> "2p";
  1(a)(ii) the school's copy of the cation/ionic-radius table (it repeats the question's table) is not reproduced;
  4(a)(iii) the school's working is kept as printed: the O2- row uses (2/16) with no sign while the N2+ row uses (-2/14); the angles are right;
  3(c)     the school's "1,2 / 1,4-disubstituted benzene" is kept as printed.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "RVHS_H2_P3", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
AL = "A" + L
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
def eq(s): return P(A(s))
ARROW = " → "
RARR = "⇌"
IMPL = "⇒ "
BOND = "–"
DB = "="
DOT = "•"
H2O = "H" + sub(2) + "O"
MDM = "mol dm" + sup(M + "3")
KJ = "kJ mol" + sup(M + "1")
STD = sup('<span class="pl-sym">⦵</span>')
def NUC(a, z, sym):   # .stk is only styled inside .stem, so inline styles here
    return ('<span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;line-height:1;font-size:.72em;'
            'text-align:right"><span style="display:block">%s</span><span style="display:block">%s</span></span>%s' % (a, z, sym))

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

NCL3 = "NC" + L + sub(3)
NH3 = "NH" + sub(3)
NO3M = "NO" + sub(3) + sup(M)
H = lambda s: i("H") + s       # unused helper kept simple
DHS = DEL + i("H") + STD
DSS = DEL + i("S") + STD
DGS = DEL + i("G") + STD
ES = i("E") + STD
E = i("E")
TDS = M + i("T") + DEL + i("S")
TDSS = M + i("T") + DEL + i("S") + STD

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      eq("Ca(NO" + sub(3) + ")" + sub(2) + "(s)" + ARROW + "CaO(s) + 2NO" + sub(2) + "(g) + ½O" + sub(2) + "(g)")),
 PART("(a)(ii)",
      P(A("When " + u("ionic radius of the metal cation decreases") + " from Pb" + sup("2+") + " to Ca" + sup("2+") + " to Zn" + sup("2+") +
          ", its " + u("charge density increases") + ". As a result, " +
          u("the ability of the metal cation to polarise the electron cloud of the (large " + NO3M + ") anion increases") + " and the " +
          u("N" + BOND + "O bonds are weakened to a bigger extent") + ". " + u("Less energy") + " is required to decompose the metal nitrate.")),
      P(A("Hence Zn(NO" + sub(3) + ")" + sub(2) + " is least thermally stable and decomposes at the lowest temperature followed by Ca(NO" + sub(3) + ")" + sub(2) +
          " and lastly Pb(NO" + sub(3) + ")" + sub(2) + "."))),
 PART("(b)(i)",
      IMG(1, "bi"),
      P(A(M + "4175 = 3(+178) + 3(590 + 1150) + 2" + DEL + i("H") + sub("f") + STD + "(PO" + sub(4) + sup("3" + M) + "(g)) + (" + M + "10520)")),
      P(A(DEL + i("H") + sub("f") + STD + "(PO" + sub(4) + sup("3" + M) + "(g)) = +295.5 " + KJ + " = " + u("+296 " + KJ)))),
 PART("(b)(ii)",
      P(A("The standard enthalpy change of solution of a substance is the enthalpy change when " +
          u("one mole of the substance is completely dissolved to give an infinitely dilute solution") + " " + u("under standard conditions,") +
          " so that no further enthalpy change takes place on adding more solvent.")),
      P(A("Or")),
      P(A("The standard enthalpy change of solution of a substance is the enthalpy change when " +
          u("one mole of the substance is completely dissolved in enough solvent under standard conditions") + ", so that " +
          u("no further enthalpy change takes place on adding more solvent") + "."))),
 PART("(b)(iii)",
      P(A(DEL + i("H") + sub("soln") + STD + " = " + M + "(" + M + "10520) + 3(" + M + "1562) + 2(" + M + "2876) = " + u("+82.0 " + KJ)))),
 PART("(b)(iv)",
      P(A("Magnitude of lattice energy (LE) ∝ |" + frac("Z" + sup("+") + " × Z" + sup(M), "r" + sup("+") + " + r" + sup(M)) + "|")),
      P(A("Ca" + sub(3) + "N" + sub(2) + " > Ca" + sub(3) + "(PO" + sub(4) + ")" + sub(2) + " > CaSO" + sub(4))),
      P(A("The charge and size of Ca" + sup("2+") + " are the same for all 3 compounds.")),
      P(A("Since N" + sup("3" + M) + " and PO" + sub(4) + sup("3" + M) + " have the same charge, and " + u("N" + sup("3" + M) + " has a smaller ionic radius/smaller anion") +
          " than PO" + sub(4) + sup("3" + M) + ", the magnitude of lattice energy is larger for Ca" + sub(3) + "N" + sub(2) + ".")),
      P(A(u("SO" + sub(4) + sup("2" + M) + " has the smallest charge") + ", so CaSO" + sub(4) + " has the smallest magnitude of lattice energy."))),
 PART("(c)(i)",
      P(A(i("pV") + " = (" + frac(i("m"), i("M")) + ")" + i("RT"))),
      P(A(i("M") + " = " + frac(i("mRT"), i("pV")))),
      P(A("= " + frac("0.400 × 8.31 × (273 + 70)", "1.2 × 1.01325 × 10" + sup(5) + " × (150 × 10" + sup(M + "6") + ")"))),
      P(A("= 62.5 g mol" + sup(M + "1")))),
 PART("(c)(ii)",
      P(A(NCL3 + " has a " + u("larger electron cloud size/more electrons") + " than " + NH3 + " and hence " +
          u("stronger instantaneous dipole-induced dipole interactions between molecules") + ".")),
      P(A("Or")),
      P(A(NCL3 + " has a " + u("bigger molecular size") + " than " + NH3 + ". The " + u("volume of " + NCL3 + " molecules is more significant") +
          " than " + NH3 + " when " + u("compared to the volume of the container") + "."))),
 PART("(c)(iii)",
      P(A("Standard entropy change is positive as there is an " + u("increase in amount/number of gaseous molecules from 0 to 4 mol") +
          " and hence an " + u("increase in disorder") + " of the system."))),
 PART("(c)(iv)",
      P(A("A " + u("higher temperature") + " will favour the removal of " + NCL3 + ".")),
      P(A(DEL + i("S") + " > 0, " + u(TDS + " < 0"))),
      P(A("Since " + DHS + " > 0, at higher temperatures, the " + u(TDSS + " term becomes more negative/ |" + TDSS + "| > |" + DHS + "|") +
          " and hence " + u(DGS + " becomes more negative") + ". Reaction becomes more " + u("spontaneous") + " at a higher temperature."))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)",
      P(A("H" + sub(2) + "(g) molecules are very small and can more easily diffuse/leak through gaps in gas tanks.")),
      P(A("H" + sub(2) + "(g) is flammable/ explosive and requires specific safety precautions to store.")),
      P(A("Very high pressure storage requirement results in high costs.")),
      P(A("Expensive and difficult to liquefy due to very low boiling point of H" + sub(2) + "(g) for storage and transport."))),
 PART("(b)(i)", P(A("Electrons flow from electrode " + b("X") + " to " + b("Y") + "."))),
 PART("(b)(ii)",
      P(A("Anode/oxidation half: CH" + sub(3) + "OH(l) + " + H2O + "(l)" + ARROW + "CO" + sub(2) + "(g) + 6H" + sup("+") + " + 6e" + sup(M))),
      P(A("Cathode/ reduction half: O" + sub(2) + "(g) + 4H" + sup("+") + " + 4e" + sup(M) + ARROW + "2" + H2O + "(l)")),
      P(A("Overall: CH" + sub(3) + "OH + " + frac("3", "2") + "O" + sub(2) + "(g)" + ARROW + "CO" + sub(2) + "(g) + 2" + H2O + "(l)"))),
 PART("(b)(iii)",
      P(A(ES + sub("cell") + " = " + ES + "(O" + sub(2) + "/" + H2O + ") " + M + " " + ES + "(CO" + sub(2) + "/CH" + sub(3) + "OH)")),
      P(A("(+1.21) = (+1.23) " + M + " " + ES + "(CO" + sub(2) + "/CH" + sub(3) + "OH)")),
      P(A(ES + "(CO" + sub(2) + "/CH" + sub(3) + "OH) = " + u("+0.02 V")))),
 PART("(b)(iv)",
      P(A(i("It") + " = " + i("nF"))),
      P(A(i("n") + " = " + frac("(4.34)(60 × 60)", "96500") + " = " + u("0.1619 mol"))),
      P(A("Volume of CO" + sub(2) + " produced = 0.1619 ÷ 6 × 24 = " + u("0.648 dm" + sup(3))))),
 PART("(b)(v)",
      P(A("The " + u("concentration of oxygen is higher") + ".")),
      P(A("This will " + u("shift the position of equilibrium of O" + sub(2) + "(g) + 4H" + sup("+") + " + 4e" + sup(M) + " " + RARR + " 2" + H2O + "(l) to the left") +
          ", causing its " + u("electrode potential value to become more positive") + ".")),
      P(A("This in turn causes the " + u("increased/more positive electromotive force") + " generated."))),
 PART("(c)(i)",
      P(A("The enthalpy change when one mole of a substance is completely burnt in oxygen under standard conditions."))),
 PART("(c)(ii)",
      P(A("Bonds broken = 3 × " + E + "(C" + BOND + "H) + " + E + "(C" + BOND + "O) + " + E + "(O" + BOND + "H) + " + frac("3", "2") + " × " + E + "(O" + DB + "O)")),
      P(A("= 3(410) + 360 + 460 + " + frac("3", "2") + "(496) = 2794 " + KJ)),
      P(A("Bonds formed = 2 × " + E + "(C" + DB + "O) + 4 × " + E + "(O" + BOND + "H)")),
      P(A("= 2(805) + 4(460) = 3450 " + KJ)),
      P(A("Enthalpy change = 2794 " + M + " 3450 = " + u(M + "656 " + KJ)))),
 PART("(c)(iii)",
      P(A("The enthalpy change calculated from bond energies assumes that all species exist in gaseous state, but the standard states of methanol and water are liquid."))),
 PART("(c)(iv)",
      P(A("CH" + sub(3) + "OH(l) + " + frac("3", "2") + "O" + sub(2) + "(g)" + ARROW + "CO" + sub(2) + "(g) + 2" + H2O + "(l)")),
      P(A(ES + sub("cell") + " = +1.21 V")),
      P(A(DGS + " = " + M + i("nF") + ES + sub("cell"))),
      P(A("= " + M + "(6)(96500)(1.21)")),
      P(A("= " + u(M + "701 " + KJ)))),
 PART("(c)(v)",
      P(A(DGS + " = " + DEL + i("H") + " " + M + " " + i("T") + DSS)),
      P(A(M + "701 = (" + M + "726) " + M + " (298)(" + DSS + ")")),
      P(A(DSS + " = " + u(M + "0.0839 kJ mol" + sup(M + "1") + " K" + sup(M + "1"))))),
 PART("(d)(i)", P(A("Addition polymerisation"))),
 PART("(d)(ii)", IMG(2, "dii")),
 PART("(d)(iii)",
      P(A("Let the number of repeat units be " + i("n") + ".")),
      P(A("Formula:")),
      IMG(2, "diii"),
      P(A(i("M") + sub("r") + " = (2)[(1.0) + (32.1) + (3)(16.0)] + 2(16.0) + " + i("n") + "[(2)(12.0) + 4(19.0)] = 13426")),
      P(A("194.2 + 100" + i("n") + " = 13426")),
      P(A(i("n") + " = 132"))),
 PART("(d)(iv)",
      P(A("The " + u("termination of the polymer chain happens randomly") + " when any two free radicals collide. Therefore, the resulting polymer chains have varying lengths and hence a range of " +
          i("M") + sub("r") + " values."))),
 PART("(d)(v)",
      P(A("Increase reaction time with higher concentration/ amounts of monomers.")),
      P(A("Reduce/ Limit " + u("amount") + " of initiator."))),
 PART("(d)(vi)",
      P(A("The " + u("C" + BOND + "F and C" + BOND + "C bond energy is strong") + " and requires a significant amount of energy to overcome."))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)", IMG(3, "ai")),
 PART("(a)(ii)", P(A("Bond angle: 117°"))),
 PART("(b)",
      P(A("Both hex-1-ene and 3,3-dimethylbut-1-ene have " + u("simple covalent structures") + ".")),
      P(A("Hex-1-ene is a " + u("straight chain isomer") + " while 3,3-dimethylbut-1-ene is a " + u("branched isomer") + ". Since hex-1-ene has a " +
          u("larger surface area") + ", " + u("more energy") + " is needed to overcome the " +
          u("more extensive instantaneous dipole-induced dipole interactions between its molecules") + ", giving rise to its higher boiling point."))),
 PART("(c)",
      P(A(b("J") + " undergoes " + u("oxidation") + " with ozone to form " + b("K") + " and " + b("L") + ".")),
      P(A(IMPL + b("J") + " is an " + u("alkene/ has C" + DB + "C bond") + ".")),
      P(A(b("J") + ", " + b("K") + " and " + b("L") + " undergo " + u("oxidation") + " with alkaline I" + sub(2) + "(aq).")),
      P(A(IMPL + "They have " + u(BOND + "COCH" + sub(3) + " or " + BOND + "CH(OH)CH" + sub(3)) + " groups.")),
      P(A(b("L") + " undergoes " + u("condensation") + " with 2,4-DNPH.")),
      P(A(IMPL + b("L") + " is a " + u("ketone") + " with " + BOND + "COCH" + sub(3) + " structure since " + b("R") + " has only one O atom.")),
      P(A(b("L") + " undergoes " + u("electrophilic substitution") + " with conc HNO" + sub(3) + " and conc H" + sub(2) + "SO" + sub(4) + " catalyst.")),
      P(A(IMPL + b("M") + " has a " + u(BOND + "NO" + sub(2) + " group") + ".")),
      P(A(IMPL + b("L") + " is a " + u("1,2 / 1,4-disubstituted benzene") + ".")),
      P(A(b("K") + " undergoes " + u("acid-base reaction") + " with Na" + sub(2) + "CO" + sub(3) + "(aq).")),
      P(A(IMPL + b("K") + " is a " + u("carboxylic acid") + ".")),
      P(A(b("K") + " undergoes " + u("condensation") + " with itself when warmed with conc H" + sub(2) + "SO" + sub(4) + " catalyst to form " + b("P") + ", a " + u("di-ester") + ".")),
      P(A(IMPL + b("K") + " has both " + u("alcohol") + " and " + u("carboxylic acid") + " functional groups.")),
      IMG(3, "c")),
 PART("(d)",
      P(A("Test: Heat with acidified KMnO" + sub(4) + "(aq)")),
      P(A("Observations: Purple KMnO" + sub(4) + "(aq) decolourises/ turns colourless with " + b("U") + ", but KMnO" + sub(4) + "(aq) remains purple with " + b("V") + ".")),
      P(A("Or")),
      P(A("Test: Warm with Tollens’ reagent")),
      P(A("Observations: Silver mirror/ grey ppt observed with " + b("U") + ", but no silver mirror/ grey ppt observed with " + b("V") + ".")),
      P(A("Or")),
      P(A("Test: Warm with Fehling’s solution")),
      P(A("Observations: Brick-red ppt observed with " + b("U") + ", but no ppt observed with " + b("V") + "."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)", P(A("N" + sup("+") + "(g)" + ARROW + "N" + sup("2+") + "(g) + e" + sup(M)))),
 PART("(a)(ii)",
      P(A(u("Nuclear charge of N" + sup("+") + " is higher than that of C") + " while " + u("shielding effect by inner shells of electrons remains relatively constant") +
          ". Thus, effective nuclear charge of N" + sup("+") + " is higher than that of C" + sup("+") + ". " +
          u("Ionic radius of N" + sup("+") + " is also smaller/valence electron is closer to the nucleus") + " than that of C" + sup("+") + ". The " +
          u("valence electron is more strongly attracted to the nucleus") + ". Hence more energy is needed to remove an electron from N" + sup("+") + " than from C" + sup("+") + "."))),
 PART("(a)(iii)",
      TBL([b("Ion"), b("Charge/mass ratio"), b("Angle of deflection")],
          [NUC(16, 8, "O") + sup("2" + M), "2/16", frac("2/16", "2/24") + " × 5.00 = +7.50°"],
          [NUC(14, 7, "N") + sup("2+"), "2/14", frac(M + "2/14", "2/24") + " × 5.00 = " + M + "8.57°"],
          [NUC(24, 12, "Mg") + sup("2+"), "2/24", M + "5.00°"])),
 PART("(b)(i)",
      P(A("In structure II, there is 1 σ bond and 2 π bonds between N atoms.")),
      P(A("The σ bond is formed via " + u("head-on overlap") + " of " + u("sp hybridised orbitals") + " from each N atom.")),
      P(A("Each π bond is formed via " + u("sideways overlap") + " of " + u("(unhybridised) p orbital") + " from each N atom."))),
 PART("(b)(ii)",
      P(A(u("Structure II is more stable") + " as the " + u("negative charge rests on the more electronegative O atom") + "."))),
 PART("(c)(i)",
      P(A(CL + DOT + " + O" + sub(3) + ARROW + CL + "O" + DOT + " + O" + sub(2))),
      P(A(CL + "O" + DOT + " + O" + sub(3) + ARROW + CL + DOT + " + 2O" + sub(2)))),
 PART("(c)(ii)",
      P(A("Chlorine radical is unstable/ highly reactive and is " + u("regenerated in step 3/ acts as a catalyst.") + " This will lead to a " + u("chain reaction") + "."))),
 PART("(d)",
      P(A("Ethylamine is most basic followed by ammonia and the least basic compound is phenylamine.")),
      P(A("Ethylamine is more basic than ammonia because " + u("electron-donating ethyl/alkyl group") + " makes the " + u("lone pair of electrons on N atom") +
          " of ethylamine " + u("more available for protonation/donation") + " as compared to ammonia.")),
      P(A("Comparing phenylamine and ammonia, the " + u("2p orbital on N atom") + " of phenylamine " + u("overlaps with the π electron cloud") + " and the " +
          u("lone pair of electrons (on the N atom) can delocalise into the benzene ring") + ", making it " + u("less available for protonation/donation") +
          ". Hence, phenylamine is less basic than ammonia."))),
 PART("(e)(i)",
      P(A("There is " + u("restricted rotation about the (rigid) N" + DB + "N") + " in azobenzene.")),
      P(A(u("Each N") + " in the N" + DB + "N is " + u("bonded to (2 different groups): benzene ring and lone pair of electrons on N.")))),
 PART("(e)(ii)",
      IMG(4, "eii"),
      P(A("The bulky benzene rings are on " + u("opposite sides of the N" + DB + "N double bond") + ", " +
          u("less steric strain/minimise electronic repulsion between the electron-rich benzene rings") + ". Hence, the trans form is more stable."))),
 PART("(f)", IMG(4, "f")),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)",
      P(A("NaC" + L + " " + u("dissolves readily in water") + " to give a neutral " + u("solution of pH 7") + ".")),
      P(A(AL + CL + sub(3) + " " + u("dissolves readily in water") + " to form an acidic " + u("solution of pH 3") + ".")),
      P(A(AL + CL + sub(3) + "(s) + 6" + H2O + "(l)" + ARROW + "[" + AL + "(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) + 3" + CL + sup(M) + "(aq)")),
      P(A("[" + AL + "(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) + " + H2O + "(l) " + RARR + " [" + AL + "(" + H2O + ")" + sub(5) + "OH]" + sup("2+") + "(aq) + H" + sub(3) + "O" + sup("+") + "(aq)")),
      P(A("PC" + L + sub(5) + " " + u("dissolves readily in (excess) water") + " to give an acidic " + u("solution of pH 2") + ".")),
      P(A("PC" + L + sub(5) + "(s) + 4" + H2O + "(l)" + ARROW + "H" + sub(3) + "PO" + sub(4) + "(aq) + 5HC" + L + "(aq)"))),
 PART("(a)(ii)",
      P(A("To each compound, add " + u("dilute acid and dilute alkali separately") + " in a test tube.")),
      P(A("Only solid " + AL + sub(2) + "O" + sub(3) + " will " + u("react/ dissolve in both acid and alkali/base") + " because " + AL + sub(2) + "O" + sub(3) + " is " + u("amphoteric") + "."))),
 PART("(b)(i)", IMG(5, "bi")),
 PART("(b)(ii)",
      P(A("At anode (oxidation):")),
      P(A("2" + H2O + "(l)" + ARROW + "O" + sub(2) + "(g) + 4H" + sup("+") + "(aq) + 4e" + sup(M))),
      P(A("followed by: 2" + AL + "(s) + " + frac("3", "2") + "O" + sub(2) + "(g)" + ARROW + AL + sub(2) + "O" + sub(3) + "(s)")),
      P(A("O" + sub(2) + " gas oxidises the aircraft components made of aluminium alloy to " + u("form a (thick) layer of " + AL + sub(2) + "O" + sub(3)) + " which " +
          u("resist oxidation/ corrosion") + "."))),
 PART("(c)(i)",
      P(A("Let the solubility of " + AL + "(OH)" + sub(3) + " in pure water be " + i("x") + " " + MDM + ".")),
      P(A(AL + "(OH)" + sub(3) + "(s) " + RARR + " " + AL + sup("3+") + "(aq) + 3OH" + sup(M) + "(aq)")),
      P(A("Eqm conc/ " + MDM + ": &emsp;[" + AL + sup("3+") + "] = " + i("x") + ", &emsp;[OH" + sup(M) + "] = 3" + i("x"))),
      P(A("3.0 × 10" + sup(M + "34") + " = 27" + i("x") + sup("4"))),
      P(A(i("x") + " = " + u("1.83 × 10" + sup(M + "9") + " " + MDM)))),
 PART("(c)(ii)",
      P(A(AL + "(OH)" + sub(3) + "(s) " + RARR + " " + AL + sup("3+") + "(aq) + 3OH" + sup(M) + "(aq)")),
      P(A("Eqm conc/ " + MDM + ": &emsp;[" + AL + sup("3+") + "] = " + i("x") + ", &emsp;[OH" + sup(M) + "] = 10" + sup(M + "8.0"))),
      P(A("3.0 × 10" + sup(M + "34") + " = " + i("x") + "(10" + sup(M + "8.0") + ")" + sup("3"))),
      P(A(i("x") + " = " + u("3.00 × 10" + sup(M + "10") + " " + MDM))),
      P(A("[" + AL + sup("3+") + "] in the wastewater = 3.00 × 10" + sup(M + "10") + " × " + frac("72.0", "20.0") + " = " + u("1.08 × 10" + sup(M + "9") + " " + MDM)))),
 PART("(d)",
      P(A("NO" + sub(2) + " acts as a catalyst to " + u("speed up") + " the oxidation of atmospheric SO" + sub(2) + " to SO" + sub(3) + " and is " + u("regenerated") + ".")),
      P(A("Step 1: NO" + sub(2) + " + SO" + sub(2) + ARROW + "NO + SO" + sub(3))),
      P(A("Step 2: NO + ½O" + sub(2) + ARROW + "NO" + sub(2)))),
 PART("(e)(i)", P(A("Iodomethane"))),
 PART("(e)(ii)",
      P(A("Step 1: dilute NaOH(aq), heat")),
      P(A("Step 3: H" + sub(2) + "SO" + sub(4) + "(aq)/ any dilute acids")),
      IMG(5, "eii")),
 PART("(e)(iii)", IMG(5, "eiii")),
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
