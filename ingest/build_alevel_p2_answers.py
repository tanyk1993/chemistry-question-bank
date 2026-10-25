"""Hand transcription of the NYJC solutions to A Level (SEAB) 9729/02 Oct/Nov 2024
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
The source is a PDF only (no docx), so everything is typed from the rendered pages.

Run from the repo root:
    python3 ingest/build_alevel_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_alevel_p2.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6, extract_acjc_p2_answers.py):
  div.worked-solution > div.part > (span.lab + div.body); answers in span.ans; red marker notes in
  span.note; a part's trailing [n] is dropped when it only repeats the part mark, inline [n] kept where a
  part carries several; examiner "Comments" are NOT emitted (standing ruling); figures are bare
  img.ws-fig[data-asset] (the user snips them: SEAB_H2_P2_Q<n>_ans-<slot>_2024.png).
RULED_FIXES holds the wording/chemistry changes the user has ruled on; nothing is changed silently.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX = "SEAB_H2_P2"
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
L = '<i class="el">l</i>'
CL = "C" + L
TIMES = "×"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return ""   # red marker notes are NOT emitted (user ruling 2026-10-24: "don't put in any of the red comments")
def P(*parts): return "<p>%s</p>" % "".join(parts)
def UL(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<li>\s*</li>", "", h)
    h = re.sub(r'<ul class="stmts">\s*</ul>', "", h)
    h = re.sub(r"<p>\s*</p>", "", h)
    h = re.sub(r"\s+(</span>)(</p>|</li>)", r"\1\2", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW, EQ = " → ", " ⇌ "
MDM = "mol dm" + sup(M + "3")
def ion(sym, ch): return sym + sup(ch)
SRCL2 = "SrC" + L + sub(2)
CO2, H2O = "CO" + sub(2), "H" + sub(2) + "O"
CO32, HCO3 = "CO" + sub(3) + sup("2" + M), "HCO" + sub(3) + sup(M)
Hp = "H" + sup("+")
def mol(x): return "mol" + sup(M + "1") if x else ""

ASSETS = []     # (question, slot) in per-question DOM order
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s_Q%d_ans-%s_2024.png" alt=""></p>' % (PFX, qn, slot)

W = {}   # qn -> list of PART html
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", P(A("SrCO" + sub(3) + "(s)" + ARROW + "SrO(s) + " + CO2 + "(g)"))),
 PART("(a)(ii)",
      P(N("[pt 1]"), " ", A(ion("Ca", "2+") + " has same charge but smaller ionic radius than " + ion("Sr", "2+") + ".")),
      P(N("[pt 2]"), " ", A("Hence the charge density and polarising power of " + ion("Ca", "2+") + " is higher than that of " + ion("Sr", "2+") + ".")),
      P(N("[pt 3]"), " ", A("The electron cloud of " + CO32 + " is polarised to a greater extent by " + ion("Ca", "2+") +
                           " and the C–O bond is more weakened, less energy is required to break the C–O bond, decomposition temperature is lower.")),
      P(N("1 mark for each point."))),
 PART("(b)(i)", P(A("Ionic bonds between " + ion("Sr", "2+") + " and " + CL + sup(M) + " ions. Hydrogen bonds between water molecules."))),
 PART("(b)(ii)", IMG(1, "bii"),
      P(N("1 mark for showing that the O is oriented towards " + ion("Sr", "2+") + " and both H are oriented towards " + CL + sup(M)))),
 PART("(c)(i)", P(A("Entropy is the measure of the disorder of a system."))),
 # RULED 2026-10-24 (user): school's answer kept; the energy-quanta argument added as an ALTERNATIVE answer
 PART("(c)(ii)",
      P(A("The breaking of ionic bonds between " + ion("Sr", "2+") + " and " + CL + sup(M) + " [1] and the breaking of hydrogen bonds between water molecules [1]. "
          "This resulted in an increase in the number of particles in the system and an increase in disorderness.")),
      P(A("OR")),
      P(A("Water temperature increases when solid " + SRCL2 + " dissolves in water. Water molecules gain kinetic energy, "
          "and there are more ways to arrange the energy quanta, hence Δ" + i("S") + " &gt; 0."))),
 PART("(c)(iii)", P(A("The forming of ion-dipole interactions between water molecules and " + ion("Sr", "2+") + " and " + CL + sup(M) + " ions respectively."))),
 PART("(d)", P(A("The enthalpy change of hydration is the energy change when one mole of gaseous ions is surrounded by water molecules, "
                 "forming a solution at infinite dilution (under standard conditions)."))),
 PART("(e)(i)", IMG(1, "ei"),
      P(A("By Hess’s Law")),
      P(A(M + "828 = (+164) + 2(+122) + (+548) + (+1060) + 2(" + M + "349) + LE")),
      P(A("LE = " + M + "2146 ≈ " + M + "2150 kJ mol" + sup(M + "1"))),
      P(N("1 mark for using " + M + "848, 164, +122, " + M + "349, 548 &amp; 1060")),
      P(N("1 mark for getting " + M + "2146 kJ mol" + sup(M + "1") + " (no need to check for this if 1st mark is not fulfilled)"))),
 PART("(e)(ii)",
      P(A("enthalpy change of solution for " + SRCL2 + "(s)")),
      P(A("= Δ" + i("H") + sub("hyd") + "(" + ion("Sr", "2+") + ") + 2Δ" + i("H") + sub("hyd") + "(" + CL + sup(M) + ") " + M + " LE(" + SRCL2 + ")")),
      P(A("= " + M + "1480 + 2(" + M + "364) " + M + " (" + M + "2146)")),
      P(A("= " + M + "62 kJ mol" + sup(M + "1"))),
      P(A("OR")),
      P(A("Using " + M + "2048 (provided by qn)")),
      P(A("enthalpy change of solution for " + SRCL2 + "(s)")),
      P(A("= Δ" + i("H") + sub("hyd") + "(" + ion("Sr", "2+") + ") + 2Δ" + i("H") + sub("hyd") + "(" + CL + sup(M) + ") " + M + " LE(" + SRCL2 + ")")),
      P(A("= " + M + "1480 + 2(" + M + "364) " + M + " (" + M + "2048)")),
      P(A("= " + M + "160 kJ mol" + sup(M + "1"))),
      UL(N("Multiply 2 to " + M + "364"), N("Apply formula correctly"),
         N("Press calculator correctly to obtain either " + M + "62 or " + M + "160; ignore units as given in qns")),
      P(N("3 pts – 2 marks, 2 points – 1 mark"))),
 PART("(f)", P(A("High activation energy due to strong ionic bonds between " + ion("Ca", "2+") + " and " + ion("F", M) + " ions."))),
]
# ------------------------------------------------------------------ Q2
PVRT = frac(i("pV"), i("RT"))
W[2] = [
 PART("(a)", P(A("The volume of the ideal gas particles is negligible compared to the volume of the container. [1]")),
      P(A("Collisions between particles of an ideal gas are perfectly elastic, i.e. there is no loss of kinetic energy during collision. [1]"))),
 PART("(b)", IMG(2, "b"), P(N("1 mark for drawing the horizontal line at PV/RT = 1"))),
 PART("(c)",
      P(A("As pressure increases even further, gaseous particles are more compressed and have no volume left to move. [1]")),
      P(A("Strong " + i("repulsive force") + " arises as the particles are so close to each other that their atoms’ positive nuclei will repel. "
          "This causes the volume of the gas occupies to increase.")),
      P(A("(as " + i("p") + " factor ↑, " + i("V") + " factor ↑, " + i("pV") + " factor ↑, hence " + PVRT + " ↑). [1]")),
      P(A("OR")),
      P(A("As pressure increases even further, volume of the particles becomes significant to the volume of the container. [1] "
          "This causes the volume of the gas occupies to increase.")),
      P(A("(as " + i("p") + " factor ↑, " + i("V") + " factor ↑, " + i("pV") + " factor ↑, hence " + PVRT + " ↑). [1]"))),
 PART("(d)", UL(
      A("Both N" + sub(2) + " and CO have simple molecular structures with instantaneous dipoles-induced dipoles (id-id) forces of attraction between the molecules."),
      A("Both N" + sub(2) + " and CO have similar electron cloud size which are therefore polarised to the same extent."),
      A("Hence the strength of both their id-id forces of attraction between molecules are similar."),
      A("However, CO is polar while N" + sub(2) + " is non-polar. Hence there is additional permanent dipole-permanent dipole forces of attraction between CO molecules."),
      A("As such the intermolecular forces of attraction between CO molecules are stronger and more significant than that between N" + sub(2) + " molecules.")),
      P(N("5 pts – 3 marks, 3-4 pts – 2 marks, 2 pts – 1 mark"))),
]
# ------------------------------------------------------------------ Q3
MR, AR = i("M") + sub("r"), i("A") + sub("r")
W[3] = [
 PART("(a)",
      P(A("pV = nRT")),
      P(A("101.325 " + TIMES + " 10" + sup("3") + " " + TIMES + " 250 " + TIMES + " 10" + sup(M + "6") + " = " + frac("0.500", MR) + " " + TIMES + " 8.31 " + TIMES + " (93+273)")),
      P(A(MR + " = 60.0")),
      P(A(MR + " (OH) = 17.0")),
      P(A("Sum of " + AR + " of C and " + AR + " of H = 60.0 " + M + " 17.0 = 43.0, giving rise to 3 C and 7 H")),
      P(A("∴ The molecular formula of " + b("A") + " is C" + sub(3) + "H" + sub(8) + "O")),
      P(N("1 mark for units conversion from cm" + sup("3") + " to m" + sup("3") + " &amp; °C to K")),
      P(N("1 mark for applying PV=nRT correctly")),
      P(N("1 mark for deducing the molecular formula correctly"))),
 PART("(b)(i)", IMG(3, "bi")),
 PART("(b)(ii)", P(A("Cr" + sub(2) + "O" + sub(7) + sup("2" + M) + " + 14" + Hp + " + 6e" + sup(M) + ARROW + "2Cr" + sup("3+") + " + 7" + H2O))),
 PART("(b)(iii)", P(A("triiodomethane, CHI" + sub(3)))),
 PART("(c)", UL(
      A("In the presence of ligands, the partially filled 3d orbitals split into two energy levels, with a small energy gap, ΔE."),
      A("An electron in the lower energy d orbital absorbs energy in the visible spectrum corresponding to ΔE and becomes excited to a vacant d orbital at the higher energy level (d-d transition)."),
      A("Unabsorbed wavelengths are transmitted and the colour observed is complementary to the colour absorbed.")),
      P(N("3 pts – 3 marks, 2 pts – 2 marks, 1 pt – 1 mark"))),
]
# ------------------------------------------------------------------ Q4
SN2 = "S" + sub("N") + "2"
W[4] = [
 PART("(a)", IMG(4, "a"), P(N("1 mark for identifying 3 chiral centres correctly"))),
 PART("(b)(i)", P(A("Catalyst"))),
 PART("(b)(ii)", P(A(b("F") + " and " + b("G") + " are a pair of enantiomers where the four different groups are arranged around the chiral carbon in a particular 3-dimensional spatial arrangement. "
                     + b("H") + " is likely an enzyme, hence it is highly specific, so only " + b("F") + " whose four different groups around the chiral carbon with a particular spatial arrangement can fit into the active site of " + b("H") + "."))),
 PART("(c)(i)", IMG(4, "ci"),
      UL(N("One secondary alcohol functional group"), N("Two sp" + sup("2") + " hybridised carbons"),
         N("A chiral carbon to give enantiomers that boil at the same temperature")),
      P(N("3 pts – 2 marks, 2 pts – 1 mark"))),
 PART("(c)(ii)",
      P(A("They can be distinguished by passing separate samples of J and K through a plane-polarised light.")),
      P(A("One of the enantiomer will rotate the plane-polarised light clockwise while the other enantiomer will rotate the plane-polarised light anticlockwise but with the same magnitude of angle of rotation.")),
      P(N("1 mark for the above"))),
 PART("(d)(i)", IMG(4, "di"),
      UL(N("2 correctly drawn arrows"), N("Correct partial charges"), N("Correct pentavalent state")),
      P(N("1 mark per point"))),
 PART("(d)(ii)", P(A("nucleophilic substitution (" + SN2 + ")"))),
 PART("(e)(i)", TBL(["halogenoalkane sample", "time for precipitate to appear / s", "identity of halogen", "colour of precipitate"],
                    [b("L"), "38", A("iodine"), A("yellow")],
                    [b("M"), "76", A("bromine"), A("cream")],
                    [b("N"), "512", A("chlorine"), A("white")]),
      P(N("6 correct – 2 marks, 3 correct – 1 mark"))),
 PART("(e)(ii)",
      P(A("From the Data Booklet:")),
      TBL(["Bond", "Bond Energy / kJ mol" + sup(M + "1")], ["C–I", "240"], ["C–Br", "280"], ["C–" + CL, "340"]),
      P(A("Bond strength decreases in the order: (strongest) C–" + CL + " &gt; C–Br &gt; C–I (weakest)")),
      P(A("More energy required to break the stronger C–" + CL + " bond, followed by C–Br and C–I.")),
      P(A("Hence time taken for precipitates to appear decreases: (longest) R–" + CL + " &gt; R–Br &gt; R–I (shortest) (optional)")),
      P(N("3 pts – 2 marks and 2 pts – 1 mark"))),
 PART("(f)(i)", P(A("CH" + sub(3) + "CO" + CL + " + " + H2O + ARROW + "CH" + sub(3) + "CO" + sub(2) + "H + H" + CL))),
 PART("(f)(ii)",
      P(N("1" + sup("st") + " reason [1]")),
      P(A("p orbital of " + CL + " atom overlaps with π electron cloud of benzene ring resulting in the delocalisation of lone pair of electrons on the " + CL +
          " atom into the benzene ring. This introduces a partial double bond between C and " + CL + ", strengthening the C–" + CL +
          " bond and cannot be broken easily. Hence chlorobenzene cannot undergo hydrolysis with cold water.")),
      P(N("2" + sup("nd") + " reason [1]")),
      P(A("The bulky benzene increases steric hindrance for the nucleophile to attack electron deficient carbon from the rear side. OR")),
      P(A("The π electron cloud of the benzene ring will repel the lone pair of electrons of an incoming nucleophile, " + H2O + "."))),
 PART("(f)(iii)",
      P(A("C atom in –" + b("C") + "O" + CL + " is attached to two highly electronegative O and " + CL + ". It is more electron deficient and more susceptible to nucleophilic attack by " + H2O +
          ". Therefore ethanoyl chloride undergoes hydrolysis more readily and a rapid reaction occurs when cold water is added to ethanoyl chloride.")),
      P(A("C atom in " + b("C") + "–" + CL + " is attached to only one electronegative " + CL + ". It is less electron deficient than the carbon atom in –CO" + CL +
          ". Therefore, chloroethane undergoes hydrolysis slowly.")),
      P(N("1 mark for the above"))),
]
# ------------------------------------------------------------------ Q5
EDTA = "EDTA" + sup("4" + M)
def e(x, n): return "%s " % x + TIMES + " 10" + sup(M + str(n))
W[5] = [
 # RULED 2026-10-24: school printed "[H+][CaIn]-"; the equation is completed as X acting as an acid
 PART("(a)(i)", P(A("HIn" + sup("2" + M) + " + " + ion("Ca", "2+") + ARROW + "[CaIn]" + sup(M) + " + " + Hp))),
 PART("(a)(ii)", P(A("Colour of sea water sample with X: Pink")), P(A("Permanent colour at end-point: Blue"))),
 PART("(b)",
      P(A("From 2" + sup("nd") + " titration,")),
      UL(A("n(" + EDTA + ") = " + frac("8.00", "1000") + " " + TIMES + " 0.00375 = " + e("3.00", 5) + " mol = n(" + ion("Ca", "2+") + ") in 3 cm" + sup("3") + " sea water"),
         A("n(" + ion("Ca", "2+") + ") in 1 cm" + sup("3") + " sea water = " + frac(e("3.00", 5), "3") + " = " + e("1.00", 5) + " mol")),
      P(A("From 1" + sup("st") + " titration,")),
      UL(A("n(" + EDTA + ") = " + frac("16.80", "1000") + " " + TIMES + " 0.00375 = " + e("6.30", 5) + " mol = [n(" + ion("Mg", "2+") + ") + n(" + ion("Ca", "2+") + ")] in 1 cm" + sup("3") + " sea water"),
         A("n(" + ion("Mg", "2+") + ") in 1 cm" + sup("3") + " sea water = " + e("6.30", 5) + " " + M + " " + e("1.00", 5) + " = " + e("5.30", 5) + " mol"),
         A(b("U") + " = [" + ion("Mg", "2+") + "] = " + frac(e("5.30", 5), "1/1000") + " = 0.0530 " + MDM),
         A(b("V") + " = [" + ion("Ca", "2+") + "] = " + frac(e("1.00", 5), "1/1000") + " = 0.0100 " + MDM)),
      P(N("6 pts – 3 marks, 3-5 pts – 2 marks, 2 pts, 1 mark"))),
 PART("(c)(i)", P(A("SO" + sub(4) + sup("2" + M)))),
 PART("(c)(ii)",
      P(A("n(BaSO" + sub(4) + ") = " + frac("0.658", "137.3 + 32.1 + 4(16.0)") + " = " + e("2.819", 3) + " mol")),
      P(A("= n(SO" + sub(4) + sup("2" + M) + ") in 100 cm" + sup("3"))),
      P(A("[SO" + sub(4) + sup("2" + M) + "] = " + frac(e("2.819", 3), "100/1000") + " = 0.02819 ≈ 0.0282 " + MDM))),
 PART("(d)(i)", P(A(i("K") + sub("sp") + " of Mg(OH)" + sub(2) + " is much smaller than " + i("K") + sub("sp") + " of Ca(OH)" + sub(2) + ". [1] Hence at pH 12, ionic product of Ca(OH)" + sub(2) +
                   " is likely to be smaller than its " + i("K") + sub("sp") + " while ionic product of Mg(OH)" + sub(2) + " is likely to be larger than its " + i("K") + sub("sp") +
                   ", resulting in precipitation of Mg(OH)" + sub(2) + ". [1]"))),
 PART("(d)(ii)", UL(
      A("At pH 12, [OH" + sup(M) + "] = 10" + sup(M + "(14" + M + "12)") + " = 0.01 " + MDM),
      A("[" + ion("Mg", "2+") + "](0.01)" + sup("2") + " = 1.1 " + TIMES + " 10" + sup(M + "11") + "<br>[" + ion("Mg", "2+") + "] = 1.1 " + TIMES + " 10" + sup(M + "7") + " " + MDM),
      # RULED 2026-10-24: user's working (% remaining) replaces the school's last line
      A("Percentage of " + ion("Mg", "2+") + " remaining = " + frac("1.1 " + TIMES + " 10" + sup(M + "7"), "0.0480") + " " + TIMES + " 100 = 2.3 " + TIMES + " 10" + sup(M + "4") + " %, i.e. almost all the " + ion("Mg", "2+") + " has precipitated")),
      P(N("3 pts – 2 marks, 2 pts – 1 mark"))),
]
# ------------------------------------------------------------------ Q6
KK = lambda n: i("K") + sub(n)
ph = lambda x: "10" + sup(M + x)
W[6] = [
 PART("(a)",
      P(A("200 years ago, [" + Hp + "] = " + ph("8.2"))),
      P(A("At present, [" + Hp + "] = " + ph("8.1"))),
      P(A("Percentage increase = " + frac(ph("8.1") + " " + M + " " + ph("8.2"), ph("8.2")) + " " + TIMES + " 100 = 25.89 ≈ 25.9 %")),
      UL(N("Marking pt 1: applying pH = " + M + "lg[" + Hp + "]"), N("Marking pt 2: calculating the increase"),
         N("Marking pt 3: calculating the percentage"), N("1 mark for each pt"))),
 PART("(b)", UL(
      A("Partial pressure of " + CO2 + " in the air = 4.2 " + TIMES + " 10" + sup(M + "4") + " " + TIMES + " " + frac("1.009", "1.013") + " = 4.183 " + TIMES + " 10" + sup(M + "4") + " atm"),
      A("Using expression 6.1,<br>0.034 = " + frac("[" + CO2 + "(g)]", "4.183 " + TIMES + " 10" + sup(M + "4")) + "<br>[" + CO2 + "(g)] = 1.422 " + TIMES + " 10" + sup(M + "5") + " mol kg" + sup(M + "1")),
      A("[" + CO2 + "(g)] in " + MDM + " = 1.422 " + TIMES + " 10" + sup(M + "5") + " mol kg" + sup(M + "1") + " " + TIMES + " 1.00 kg dm" + sup(M + "3") +
        "<br>= 1.422 " + TIMES + " 10" + sup(M + "5") + "<br>≈ 1.42 " + TIMES + " 10" + sup(M + "5") + " " + MDM + " (3 s.f)")),
      P(N("3 pts – 2 marks, 2 pts – 1 mark"))),
 PART("(c)(i)",
      P(A("reaction 6.1   " + CO2 + " + " + H2O + EQ + HCO3 + " + " + Hp)),
      P(A("As the amount of " + CO2 + " gas in the atmosphere increases, position of equilibria for reaction 6.1 shifts to the right to reduce the increase in " + CO2 +
          " gas, hence resulting in increase in amount of " + Hp + ". "), N("[1" + sup("st") + " mark]")),
      P(A("reaction 6.2   " + HCO3 + EQ + CO32 + " + " + Hp)),
      P(A("The large reservoir of " + CO32 + " in the buffer reacts with " + Hp + " as shown in reaction 6.2, shifting the position of equilibria for reaction 6.2 to the left, "
          "removing " + Hp + " and therefore keeping the pH approximately constant. "), N("[2" + sup("nd") + " mark]"))),
 PART("(c)(ii)",
      P(A(KK(1) + " = " + frac("[" + HCO3 + "][" + Hp + "]", "[" + CO2 + "]") + " and " + KK(2) + " = " + frac("[" + CO32 + "][" + Hp + "]", "[" + HCO3 + "]"))),
      P(A(KK(3) + " = " + frac("[" + HCO3 + "]" + sup("2"), "[" + CO2 + "][" + CO32 + "]") + " = " + frac(KK(1), KK(2)) + " = " +
          frac("1.45 " + TIMES + " 10" + sup(M + "6"), "1.10 " + TIMES + " 10" + sup(M + "9")) + " = 1318 ≈ 1320 no units")),
      UL(N("1 mark for writing the expression of " + KK(1) + " and " + KK(2) + " correctly"),
         N("1 mark for writing the expression of " + KK(3) + " in terms of " + KK(1) + " and " + KK(2) + " and calculating the value of " + KK(3) + " correctly (allow ECF)"),
         N("1 mark for units (allow ECF)"))),
 # RULED 2026-10-24: school key said CO3(2-); user's answer HCO3-, reasoned from the large K3 of 6(c)(ii)
 PART("(c)(iii)",
      P(A(HCO3 + ". " + KK(3) + " ≈ 1320 is large, so the position of equilibrium of reaction 6.3 lies far to the right, favouring " + HCO3 + " over " + CO2 + " and " + CO32 + "."))),
 PART("(d)", UL(
      A("As temperature increases, p" + KK(2) + " decreases, hence " + KK(2) + " increases which tells us that"),
      A("the forward reaction of reaction 6.2 is favored. This means that position of equilibrium shifts right as"),
      A("temperature increases to favor the endothermic reaction to remove the added heat."),
      A("Hence the nature of reaction 6.2 is endothermic reaction.")),
      P(N("4 pts – 2 marks, 2 pts – 1 mark"))),
]

# ------------------------------------------------------------------ rulings (user, item by item) -- none yet
RULED_FIXES = [   # (qn, old, new, expected count) -- wording fixes approved by the user 2026-10-24
    (1, "an increase in disorderness.", "an increase in disorder.", 1),
    (2, "the volume of the gas occupies to increase", "the volume the gas occupies to increase", 2),
    (4, "through a plane-polarised light", "through plane-polarised light", 1),
    (4, "One of the enantiomer will rotate", "One enantiomer will rotate", 1),
    (6, "is favored.", "is favoured.", 1),
    (6, "to favor the endothermic", "to favour the endothermic", 1),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    for q, old, new, n in RULED_FIXES:
        if q == qn:
            assert h.count(old) == n, (qn, old, h.count(old)); h = h.replace(old, new)
    h = h.replace(" [1]", "")      # inline mark allocations are red text: not emitted
    assert not re.search(r"\[\d", h), (qn, re.findall(r".{20}\[\d.{10}", h))
    out[str(qn)] = h

# labels = the question parts that carry a mark badge (answerable parts)
qs = {r["question_number"]: r for r in json.loads((QDIR / "questions.json").read_text())}
for qn in sorted(W):
    want = []
    for m in re.finditer(r'<span class="pl">([^<]*)</span>(.*?)</div>(?=\n<div class="qpart">|$)', qs[qn]["content_html"], re.S):
        if 'class="mk"' in m.group(2): want.append(m.group(1))
    have = re.findall(r'<span class="lab">([^<]*)</span>', out[str(qn)])
    assert want == have, (qn, want, have)

assets, seen = [], {}
for qn, slot in ASSETS:
    seen[qn] = seen.get(qn, 0) + 1
    assets.append({"question": qn, "slot": "ans-" + slot, "path": "%s_Q%d_ans-%s_2024.png" % (PFX, qn, slot), "offset": seen[qn]})
(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "worked solutions,", sum(h.count('class="lab"') for h in out.values()), "parts,", len(assets), "answer assets")
for a in assets: print("  Q%d %-8s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))
