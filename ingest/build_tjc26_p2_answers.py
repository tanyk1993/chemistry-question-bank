"""Hand transcription of the TJC 2026 H2 Prelim Paper 2 (9476/02) suggested solutions -> worked_solutions.json +
answer_assets.json (feeds gen_answers_migration.py --type structured).

Source: the school's "H2 P2 Review" Word file (question paper with the mark scheme inline: answers in blue, marking notes in
red, underlines on the mark-bearing keywords) and its Word-exported PDF. Text is typed from the docx (which carries the
underlines); the 16 answer figures are snipped from the PDF by crop_tjc26_p2_answers.py.

Run from the repo root:
    python3 ingest/build_tjc26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_tjc26_p2.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u> on the
school's underlined keywords; marking notes in span.note; figures are bare img.ws-fig[data-asset]
(TJC_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp.
Dropped from the school's pages: the [n] marks and tick marks, the "2 [tick] = 1 mark" tallies, and the red pedagogy line
"Learn the precise phrasing!" at Q3(b)(ii). Red MARKING notes (accept / do not accept / penalise / ecf / no marks / "Note: ...")
are kept as span.note. The school's "OR" lines become P("Or").
Q2(b)(ii): the |lattice energy| proportional-to q+q-/(r+ + r-) line is part of the solution (user ruling 2026-11-25) and is typed
here, centred, ahead of the answer sentence.

FIXES made to the school's answers (listed to the user; veto-able):
  1(a)(ii)  "Since the mass ... required." (fragment) -> "The mass of water produced is higher than the mass required.";
  1(b)(iv)  "requires lesser energy" -> "requires less energy";
  2(b)(iv)  "decompse CaCO3 and CaCO3 is less thermally stable" -> "decompose CaCO3. Hence, CaCO3 is less thermally stable";
  4(c)(ii)  "rxn" -> "reaction";
  6(b)(i)   "Cu2+ + 2e -> Cu" -> "2e-";   6(c)(ii) "metal center" -> "metal centre";
  6(d)      "F atoms decreases" -> "decrease";   6(e) "will be also oxidised" -> "will also be oxidised";
  the school's "ppt"-style shorthand is not present; "Amt" (6(b)) is kept as the school wrote it.
Q3(a)(i): the school's stock ball-and-stick picture beside its own PCl3 drawing is NOT used (four-ligand molecule, watermarked);
only the school's drawing is snipped.
Q4(a)(ii), (b)(iii), (c)(ii): the school's red "Note:" pictures are kept as extra figures after a typed "Note:" line.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "TJC_H2_P2", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
DEL = "Δ"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def C(*parts): return '<p class="c">%s</p>' % "".join(parts)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW = " → "
BOND = "–"
MDM = "mol dm" + sup(M + "3")
KJ = "kJ mol" + sup(M + "1")
STD = sup('<span class="pl-sym">⦵</span>')
H2O = "H" + sub(2) + "O"
CO2 = "CO" + sub(2)
EMINUS = "e" + sup(M)
EM = "&emsp;"
NB = "&nbsp;"
PCL3 = "PC" + L + sub(3)
H3PO3 = "H" + sub(3) + "PO" + sub(3)
CACO3 = "CaCO" + sub(3)
def iso(a, sym): return sup(a) + sym
DHS = DEL + i("H") + STD
DGS = DEL + i("G") + STD
DSS = DEL + i("S") + STD
ESTD = i("E") + STD
KEQ = i("K") + sub("eq")
CUEN2 = "[Cu(en)" + sub(2) + "]" + sup("2+")
SN2 = "S" + sub("N") + "2"
SN1 = "S" + sub("N") + "1"

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A("H" + sub(2) + " ≡ " + H2O)),
      P(A("actual amount of H" + sub(2) + " burnt = (500 × 1" + NB + "000 ÷ 2) × 0.90 = " + u("2.25 × 10" + sup(5) + " mol"))),
      P(A("maximum mass of " + H2O + " = 2.25 × 10" + sup(5) + " × 18.0 = 4.05 × 10" + sup(6) + " g = " + u("4050 kg")))),
 PART("(a)(ii)",
      P(A("The " + u("mass of water produced is higher than") + " the mass required. The hydrogen fuel carried is " + u("sufficient") +
          " to meet the mission water requirement.")),
      P(N("With reasoning; allow ecf."))),
 PART("(b)(i)",
      P(A("Let the relative abundance of " + iso(6, "Li") + " be " + i("y") + " % and that of " + iso(7, "Li") + " be (100 " + M + " " + i("y") + ")%.")),
      P(A(frac(i("y"), "100") + " × 6 + " + frac("100 " + M + " " + i("y"), "100") + " × 7 = 6.94")),
      P(A(i("y") + " = 6.0 %")),
      P(A("Relative abundance of " + iso(6, "Li") + " = " + u("6.0 %"))),
      P(A("Relative abundance of " + iso(7, "Li") + " = " + u("94.0 %"))),
      P(N("Accept 0.06 and 0.94."))),
 PART("(b)(ii)",
      P(A(u("Minimum energy") + " required to " + u("completely remove") + " " + u("one mole of valence electrons") + " from " +
          u("one mole of ground state gaseous atom") + " to form " + u("one mole of singly positively charged gaseous ion") + "."))),
 PART("(b)(iii)",
      P(A("There is a large increase in ionisation energy when the 2" + sup("nd") + " electron is removed as the " + u("2" + sup("nd") + " electron removed") +
          " comes from the " + u("inner electron shell") + " which is " + u("nearer to the nucleus") + " and " + u("experiences a stronger attraction") +
          " to the nucleus."))),
 PART("(b)(iv)",
      P(A("Li: 1s" + sup(2) + " 2s" + sup(1) + EM + "Be: 1s" + sup(2) + " 2s" + sup(2) + EM + "B: 1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(1))),
      P(A("Across the period, " + u("nuclear charge increases") + " " + u("but screening effect remains approximately constant.") + " The " +
          u("2p valence electron of boron is held more strongly by the nucleus than the 2s electron of Li") + ".")),
      P(A("However, the " + u("2p electron of B is slightly further") + " from the nucleus " + u("than the 2s electron of Be") +
          " hence it requires less energy for removal compared to 2s electron of Be."))),
 PART("(b)(v)",
      P(A("Li ≡ Li" + sup("+") + " ≡ " + EMINUS)),
      P(A("One mole of electrons transferred for every mole of Li" + sup("+") + " formed.")),
      P(A("Amount of " + EMINUS + " = 64.9 ÷ 6.9")),
      P(A("= 9.406 mol")),
      P(A("Flow of charge = 9.406 × 6.02 × 10" + sup(23) + " × 1.60 × 10" + sup(M + "19"))),
      P(A("= " + u("9.06 × 10" + sup(5) + " C")))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A(DSS + " has a " + u("positive") + " sign as there is an " + u("increase in the number of moles of gaseous") + " particles.")),
      P(N("Do not accept " + DSS + " > 0 instead of stating the sign."))),
 PART("(a)(ii)",
      P(A("Bond energy of O–H: 460, O–O: 150, O=O: 496")),
      P(A(DHS + " = 2(+150) " + M + " 496")),
      P(A("= " + M + "196 " + KJ))),
 PART("(a)(iii)",
      P(A("The value calculated in (a)(ii) uses " + u("bond energy") + " values from the " + u(i("Data Booklet")) + " which are applicable for reactants and products in the " +
          u("gaseous phase") + ".")),
      P(A(u("As " + H2O + " and H" + sub(2) + "O" + sub(2) + " are in liquid states instead of gaseous state") + ", the value is different."))),
 PART("(a)(iv)",
      P(A(DGS + " = " + DHS + " " + M + " " + i("T") + DSS)),
      P(A(DSS + " = " + frac(M + "196 + 238", "298"))),
      P(A("= +0.141 " + KJ.replace("mol", "mol") + " K" + sup(M + "1") + " or +141 J mol" + sup(M + "1") + " K" + sup(M + "1")))),
 PART("(b)(i)",
      P(A("Lattice energy is the heat energy " + u("evolved") + " when " + u("one mole") + " of " + u("solid ionic compound") + " is " +
          u("formed from its constituent gaseous ions") + " at 298 K and 1 bar."))),
 PART("(b)(ii)",
      C(A("|Lattice energy| ∝ |" + frac("q" + sub("+") + "q" + sub(M), "r" + sub("+") + " + r" + sub(M)) + "|")),
      P(A(u("The O" + sup("2" + M) + " ion has a smaller ionic radius than CO" + sub(3) + sup("2" + M) + " ion") +
          ". Hence, the interionic distance in CaO is smaller and hence the lattice energy is more exothermic."))),
 PART("(b)(iii)",
      IMG(2, "biii"),
      P(A("By Hess’ law,")),
      P(A(M + "2800 + " + DEL + "H" + sub("decom") + " = " + M + "3460 + 914")),
      P(A(DEL + "H" + sub("decom") + " = +254 " + KJ)),
      P(N("1 mark for the energy cycle with balanced equations and state symbols."))),
 PART("(b)(iv)",
      P(A("As " + u("Ca" + sup("2+")) + " has a " + u("smaller ionic radius") + " than " + u("Sr" + sup("2+")) + ", " + u("Ca" + sup("2+")) + " has a " +
          u("higher charge density and polarising power") + ".")),
      P(A("Hence, resulting in " + u("greater distortion/ polarisation of the electron cloud of CO" + sub(3) + sup("2" + M) + " ion") + " " +
          u("and greater weakening of the C" + BOND + "O covalent bond"))),
      P(A(u("Less energy") + " needed to decompose " + CACO3 + ". Hence, " + u(CACO3) + " is " + u("less") + " thermally " + u("stable") + "."))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)",
      IMG(3, "ai"),
      P(N("Need to draw the plane, or use wedge and dash to show 3D.")),
      P(A("Trigonal pyramidal")),
      P(A("107°"))),
 PART("(a)(ii)",
      P(A(PCL3 + " is " + u("polar") + ". There is a " + u("difference in electronegativity of P and C" + L) + " or the " + u("P" + BOND + "C" + L + " bond is") +
          " polar. Due to the shape, the " + u("dipole moments do not cancel out") + " and there is a " + u("net dipole moment") + " in the molecule."))),
 PART("(a)(iii)", IMG(3, "aiii")),
 PART("(a)(iv)",
      P(A(PCL3 + " has one lone pair around P while " + H3PO3 + " has no lone pair around P.")),
      P(A("Since " + u("bond pair " + BOND + " lone pair repulsion") + " is " + u("greater than bond pair " + BOND + " bond pair repulsion") +
          ", the bond pairs in " + PCL3 + " will be pushed closer, hence the bond angle is " + u("smaller") + " than that in " + H3PO3 + "."))),
 PART("(b)(i)",
      P(A(b("D") + " has molecular formula of C" + sub(7) + "H" + sub(14) + "O and undergoes " + u("redox") + " reaction with Na to give effervescence, " + b("D") +
          " contains an " + u(BOND + "OH group") + " / " + b("D") + " contains an " + u("alcohol") + ".")),
      P(N("Penalise for suggesting incorrect functional group of carboxylic acid and phenol as they are not possible from the molecular formula of D; "
          "only one O atom and C:H ratio is not close to 1:1.")),
      P(A(b("D") + " " + u("undergoes oxidation") + " with alkaline aqueous iodine, so it contains " + u("CH" + sub(3) + "CH(OH)" + BOND) + " group.")),
      P(A(b("D") + " " + u("undergoes strong oxidation") + " with acidified KMnO" + sub(4) + ", " + b("D") + " is an " + u("alkene/ has (one) C=C") +
          " since two products are formed.")),
      P(A("Structure of " + b("D") + ":")),
      IMG(3, "bi")),
 PART("(b)(ii)",
      P(A("Cis-trans isomerism occurs due to " + u("restricted rotation") + " about the " + u("C=C double bond") + " and " +
          u("each carbon atom of the C=C double bond") + " is bonded to " + u("two different groups") + "."))),
 PART("(b)(iii)",
      IMG(3, "biii"),
      P(A("skeletal formula"), " ", N("no H atoms shown apart from " + BOND + "OH")),
      P(A("cis-trans structures, showing the trigonal planar shape about each C of C=C")),
      P(N("Note: these are E-Z isomers."))),
 PART("(b)(iv)",
      IMG(3, "biv"),
      P(N("1 mark for organic products, 1 mark for balanced equation."))),
]
# ------------------------------------------------------------------ Q4
NA = "N" + sub("a")
NBB = "N" + sub("b")
W[4] = [
 PART("(a)(i)", P(A("Nucleophile / Lewis base"))),
 PART("(a)(ii)",
      IMG(4, "aii"),
      P(N("Note:")),
      IMG(4, "aii2")),
 PART("(a)(iii)",
      P(A("Catalyst as it is consumed in step 3 and regenerated in step 5")),
      P(A("Or")),
      P(A("protonate the OH group " + u("to form H" + sub(2) + "O") + ", a good leaving group"))),
 PART("(b)(i)",
      P(A(NA + " is a stronger base")),
      P(A("Lone pair of electrons on " + NBB + " is delocalised over the O" + BOND + "C" + BOND + NBB + " bond and is not / less available for donation to a proton"))),
 PART("(b)(ii)",
      IMG(4, "bii"),
      P(N("Accept arrows in opposite direction."))),
 PART("(b)(iii)",
      IMG(4, "biii"),
      P(N("Note: pattern recognition")),
      IMG(4, "biii2")),
 PART("(c)(i)",
      P(N("Note: difference means must COMPARE reactivity between acyl chloride and alkyl chloride (electronic and steric) → using comparative words.")),
      P(A("Acyl chloride is more reactive towards hydrolysis as")),
      P(A("(Electronic reason) the " + u("carbonyl carbon has two electron-withdrawing atoms O and C" + L) + " while the " +
          u("C" + BOND + "C" + L + " in chloroalkane has only one electron withdrawing chlorine") + " atom. Hence the " + u("carbonyl C more electron deficient") + ".")),
      P(A("(Steric reason) " + u("groups around carbonyl carbon are arranged in a trigonal planar") + " manner while " +
          u("groups around C" + BOND + "C" + L + " in chloroalkane are arranged in tetrahedral manner") + ". Hence there is " +
          u("less steric hindrance around carbonyl carbon") + "."))),
 PART("(c)(ii)",
      P(b("L") + ":"),
      IMG(4, "cii"),
      P(N("Note: reduction of COOH to " + BOND + "CH" + sub(2) + "OH, NOT " + BOND + "CH(OH)" + sub(2))),
      P(b("R") + ":"),
      IMG(4, "cii2"),
      P(N("Note: double number of C atoms → condensation reaction between two " + b("Q") + " molecules")),
      IMG(4, "cii3")),
 PART("(c)(iii)",
      P(A("step 3: acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + " "), N("(NOT KMnO" + sub(4) + ")"), A(", heat with distillation")),
      P(A("step 4: NH" + sub(3) + " in ethanol "), N("(NOT aq NH" + sub(3) + ")"), A(", heated under pressure "), N("(NOT just heat)"))),
 PART("(d)",
      P(A(SN2)),
      IMG(4, "d"),
      P(N("reactants in 3D i.e. correct RC" + L + " (given), two curly arrows, lone pair on NH" + sub(3) + " and partial charges on C" + BOND + "C" + L + " bond")),
      P(N("neutral transition state")),
      P(N("products i.e. inversion of configuration (3D) + C" + L + sup(M))),
      P(N("arrow for deprotonation step (accept if use C" + L + sup(M) + " or just lose H" + sup("+") + ")")),
      P(N("No marks if drew " + SN1 + "."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)", P(A("Zn(s) + 2OH" + sup(M) + "(aq)" + ARROW + "Zn(OH)" + sub(2) + "(s) + 2" + EMINUS))),
 PART("(b)", P(A("2MnO" + sub(2) + " + 2" + H2O + " + Zn" + ARROW + "Zn(OH)" + sub(2) + " + 2MnOOH"))),
 PART("(c)(i)", P(A(ESTD + sub("cell") + " = 0.38 " + M + " (" + M + "1.22) = +1.60 V"))),
 PART("(c)(ii)",
      P(A(DGS + " = " + M + " nF" + ESTD + sub("cell") + " = " + M + "(2)(96500)(1.60) = " + M + "308" + NB + "800 J mol" + sup(M + "1") + " = " + M + "309 " + KJ))),
 PART("(d)",
      P(A(M + "308" + NB + "800 J mol" + sup(M + "1") + " = " + M + " RT ln " + KEQ + " = " + M + " (8.31)(298) ln " + KEQ)),
      P(A(KEQ + " = 1.43 × 10" + sup(54)), " ", N("(ecf from (c)(ii))")),
      P(N("Ignore units for final answer."))),
]
# ------------------------------------------------------------------ Q6
W[6] = [
 PART("(a)", IMG(6, "a")),
 PART("(b)(i)",
      P(A("Cu" + sup("2+") + " + 2" + EMINUS + ARROW + "Cu")),
      P(A("Amt of copper deposited = 17/63.5 = 0.268 mol")),
      P(A("Amt of electrons needed = 0.268 × 2 = 0.535 mol")),
      P(A("Using Faraday’s Law, Q = It = nF")),
      P(A("176 A (" + i("t") + ") = 0.535 mol (96500)")),
      P(A("Time, " + i("t") + " = " + u("293 s") + " OR " + u("4.89 min")))),
 PART("(b)(ii)",
      P(A("From " + b("(a)") + ", 2" + CO2 + " ≡ 2" + EMINUS)),
      P(A("Amt of " + CO2 + " = 0.535 mol")),
      P(A("Volume of " + CO2 + " = 0.535 × 24 dm" + sup(3) + " = " + u("12.8 dm" + sup(3))))),
 PART("(c)(i)",
      P(A("In " + u("presence of en ligands") + ", the five d orbitals are " + u("split into two energy levels") + " (with an energy gap " + DEL + "E) due to repulsion between Cu" +
          sup("2+") + " ion and the ligands.")),
      P(A("For Cu" + sup("2+") + " ion with " + u("partially filled d-subshells") + ", when a " + u("d-electron from lower energy group is promoted to the higher energy group") +
          " (d-d transition), " + u("wavelength of orange light corresponding to " + DEL + "E is absorbed") + ".")),
      P(A("Light energy that is " + u("not absorbed") + " (blue) is seen as the colour of the complex."))),
 PART("(c)(ii)", P(A("A ligand which forms " + u("2 dative bonds / coordinate bonds") + " with the metal centre."))),
 PART("(c)(iii)",
      P(A("Ligand exchange.")),
      P(A("[Cu(" + H2O + ")" + sub(6) + "]" + sup("2+") + " + 2en" + ARROW + CUEN2 + " + 6" + H2O)),
      P(N("Accept reversible arrow."))),
 PART("(c)(iv)",
      P(A("Ligand exchange for this reaction leads to a " + u("large increase in entropy due to increase in number of particles in the products") + "."))),
 PART("(d)",
      P(A("Less effective.")),
      P(A("The " + u("electron withdrawing F atoms decrease the electron density") + " on the N atoms, " + u("making the lone pair electrons less available") +
          " to attack the electron deficient carbon of " + CO2 + "."))),
 PART("(e)",
      P(N("Either one reason below")),
      P(A("Reason 1: " + CO2 + " produced at the positive terminal will " + u("dissolve in water") + ", resulting in the loss of " + CO2 + " gas collected in the storage tank.")),
      P(A("Reason 2: when water is present, " + u("water will also be oxidised to O" + sub(2) + " gas") +
          " at the anode / positive terminal, which will decrease the purity of the " + CO2 + " in the storage tank."))),
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
for a in assets: print("  Q%d %-10s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))
