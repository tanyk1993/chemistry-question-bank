"""Hand transcription of the NJC 2026 H2 Prelim Paper 3 (9476/03) suggested answers
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's answers PDF only (26 pages): the question paper with each answer typed in blue inside a
box, red notes, bold/underlined mark-bearing keywords. Typed from the rendered pages and the text layer.

Run from the repo root:
    python3 ingest/build_njc26_p3_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_njc26_p3.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions as build_njc26_p2_answers.py (claude/style-guide.md SS6): div.worked-solution > div.part >
(span.lab + div.body); answers in span.ans with <u> on the mark-bearing keywords (the school's bold/underlined
blue text); figures are bare img.ws-fig[data-asset] (the user snips them: NJC_H2_P3_Q<n>_ans-<slot>_2026.png);
tables are table.cmp; the school's red text is span.note.
Per-point mark brackets the school typed inside an answer (2(a)(i) "[1]", 5(e)(i) "[1m]") are kept as printed;
the part-total "[2]" at the end of 4(c) is dropped.
PROPOSED_FIXES holds wording changes to the school text that wait for the user's ruling (APPLY_PROPOSED).
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "NJC_H2_P3", 2026
APPLY_PROPOSED = True
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
DEL = "Δ"
K = i("K")
EM = "&emsp;"
PLS = '<span class="pl-sym">⦵</span>'
STD = sup(PLS)
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def sqrt(s): return '<span class="sqrt"><span class="rad">%s</span></span>' % s
def A(t): return '<span class="ans">%s</span>' % t
def N(t): return '<span class="note">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
def F(s):
    s = re.sub(r"(?<=[A-Za-z\)\]])(\d+)", lambda m: sub(m.group(1)), s)
    return s.replace("Cl", CL)
def chg(sym, ch): return F(sym) + sup(ch)
def pK(s): return "p" + K + sub(s)
def Ka(): return K + sub("a")
def Ksp(): return K + sub("sp")
def Kp(): return K + sub("p")
def Esub(s): return i("E") + STD + sub(s)
def x10(a, n): return "%s × 10%s" % (a, sup(M + str(n)))
MDM = "mol dm" + sup(M + "3")
H2O, HP, OHM = F("H2O"), "H" + sup("+"), "OH" + sup(M)
ARROW = " → "

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", IMG(1, "ai")),
 PART("(a)(ii)",
      P(A(F("O3") + ": 110° ≤ bond angle < 120°<br>[actual 117°]")),
      P(A("Central oxygen atom has 3 regions of electron density: " + u("2 bonding pairs") + " (one single bond, one double bond) and " + u("1 lone pair") + ".")),
      P(A(u("The lone pair-bond pair repulsion is greater than the bond-bond pair repulsion, compressing the bond angle") +
          " from the ideal 120° / electron geometry as trigonal planar to approximately 117°."))),
 PART("(a)(iii)",
      P(A(u("A dative covalent (co-ordinate) bond") + " is formed.")),
      IMG(1, "aiii"),
      P(A("Note: Ozone acts as a " + u("Lewis base") + " by donating a lone pair of electrons to the electron-deficient boron atom in " + F("BF3") + " (Lewis acid)).")) ),
 PART("(b)(i)", P(A("The even breaking of a covalent bond where the " + u("shared pair of electrons is divided equally") + ", with each atom taking one electron to " + u("form radicals") + "."))),
 PART("(b)(ii)", IMG(1, "bii")),
 PART("(b)(iii)", P(A("Step 1: " + u("Initiation") + EM + EM + "Step 3: " + u("Propagation")))),
 PART("(b)(iv)",
      P(A("The chlorine radical acts as a " + u("catalyst") + " in the overall destruction of ozone.")),
      P(A("C" + L + "• is " + u("consumed in Step 3") + " when C" + L + "• reacts with " + F("O3") + " to form C" + L + "O• and " + F("O2") + ", C" + L + "• is " +
          u("regenerated in Step 4") + " when C" + L + "O• reacts with a free oxygen atom to form " + F("O2") + " and C" + L + "•."))),
 PART("(b)(v)",
      P(A("Since temperature at 20 km from ground is " + u("colder/lower") + " compared to 50 km, position of equilibrium at 20 km " + u("lies more/ farther to right") +
          " to favour the " + u("forward exothermic reaction") + " as to produce some heat/ increase the temperature.")),
      P(A("OR")),
      P(A("Since temperature at 50 km from ground is " + u("higher/hotter") + " compared to 20 km, position of equilibrium at 50 km " + u("lies more/ farther to left") +
          " to favour the " + u("backward endothermic reaction") + " as to absorb some heat/ decrease the temperature."))),
 PART("(c)(i)", IMG(1, "ci")),
 PART("(c)(ii)",
      P(A("Step 1 " + u("conc. " + F("HNO3") + ", conc. " + F("H2SO4") + ", " + b("30 °C")))),
      P(A("Step 2 " + u("1. Sn, conc. H" + CL + ", heat") + EM + u("2. NaOH(aq)"))),
      P(A("Step 3 " + u("anhydrous " + F("CH3COCl"))))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A("A " + u("buffer solution") + " contains a large reservoir of weak acid, " + F("HN3") + " and its conjugate base, " + chg("N3", M) + ". A " + u("buffer solution") +
          " can " + u("resist a change in pH when a small amount of " + HP + " or " + OHM + " is added to it") + ". [1]")),
      P(A("When a small amount of " + HP + " is added, " + chg("N3", M) + " + " + HP + ARROW + F("HN3") + "<br>When a small amount of " + OHM + " is added, " + F("HN3") + " + " + OHM +
          ARROW + chg("N3", M) + " + " + H2O + "<br>[1 for both equations]")),
      P(A("Note: In this buffer, " + F("HN3") + " is the weak acid, " + chg("N3", M) + " is the conjugate base<br>Use " + u("full arrow") + " for acid-base reaction."))),
 PART("(a)(ii)",
      P(A("When NaOH is added to " + F("HN3") + ", acid base reaction takes place. Use ICF table to determine the composition of the final mixture.")),
      P(A("Amount of " + OHM + " = 0.025 dm" + sup(3) + " × 0.600<br>&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;= 0.015 mol")),
      P(A("Amount of " + F("HN3") + " = 0.05 dm" + sup(3) + " × 0.500<br>&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;= 0.025 mol")),
      TBL(["", OHM, "+ " + F("HN3"), "→", chg("N3", M), "+ " + H2O],
          ["Initial / mol", "0.015 (L.R.)", "0.025", "", "0", "–"],
          ["Change / mol", M + "0.015", M + "0.015", "", "+0.015", "–"],
          ["Final / mol", "0", N("0.010"), "", N("0.015"), "–"]),
      P(A("pH = p" + Ka() + " + lg " + frac("[<i>salt</i>]", "[<i>weak acid</i>]") + "&emsp;or pH = p" + Ka() + " + lg " + frac("[<i>conj. base</i>]", "[<i>weak acid</i>]"))),
      P(A("pH = p" + Ka() + " + lg " + frac("[" + chg("N3", M) + "]", "[" + F("HN3") + "]"))),
      P(A("&emsp;&nbsp;= " + M + " lg 1.8 × 10" + sup(M + "5") + " + lg " + frac(frac("0.015", "<i>V</i>"), frac("0.010", "<i>V</i>")))),
      P(A("&emsp;&nbsp;= 4.92"))),
 PART("(a)(iii)", P(A("Nucleophilic addition")), IMG(2, "aiii")),
 PART("(b)",
      P(A("From the given question: " + F("Na2O2") + " ≡ " + F("H2O2") + " ≡ " + F("I2") + " ≡ 2" + chg("S2O3", "2" + M))),
      P(A("Moles of " + F("Na2O2") + " = ½ × moles of " + chg("S2O3", "2" + M) + " = ½ × 0.0167 × 0.200 = 1.67 × 10" + sup(M + "3"))),
      P(A("Mass of " + F("Na2O2") + " = 1.67 × 10" + sup(M + "3") + " × 78 = 0.1303 g<br>Mass of " + F("Na2O") + " = 0.5 " + M + " 0.1303 = 0.3697 g")),
      P(A(frac("mass of " + F("Na2O"), "mass of " + F("Na2O2")) + " = " + frac("0.3697", "0.1303") + " = 2.837 = 2.84"))),
 PART("(c)(i)",
      P(A("HOO" + sup(M) + " (conjugate base of " + F("H2O2") + ") " + u("has 1 additional electronegative O than " + OHM) + " (conjugate base of " + H2O + "). Hence the " +
          u("negative charge of HOO" + sup(M) + " is more dispersed and the anion is more stabilised") + " than " + OHM + ".")),
      P(A("Thus " + F("H2O2") + " can dissociate into " + HP + " and HOO" + sup(M) + " ion to a greater extent; is more acidic than " + H2O + " and higher " + Ka() + ", lower p" + Ka() + "."))),
 PART("(c)(ii)",
      P(A("Due to " + u("intramolecular hydrogen bonding") + " in " + F("CH3CO3H") + " (hydrogen bonding forms a 5 atoms cyclic arrangement), more energy is required to release " + HP +
          " / " + F("CH3CO3H") + " to dissociate a proton.<br>Hence " + F("CH3CO3H") + " is less acidic than " + F("CH3CO2H") + " and has a higher p" + Ka() + " value.")),
      IMG(2, "cii"),
      P(A("OR")),
      IMG(2, "cii2"),
      P(A(chg("CH3CO2", M) + " (conjugate base of " + F("CH3CO2H") + ") is " + u("resonance-stabilised as the negative charge on " + chg("CH3CO2", M) +
          " can delocalise over 2 electronegative oxygen atoms") + "; while " + chg("CH3CO3", M) + " (conjugate base of " + F("CH3CO3H") + ") is not stabilised by resonance.")),
      P(A("Hence " + F("CH3CO2H") + " is more acidic with a lower p" + Ka() + " as it can dissociate to a greater extent into " + HP + " and " + chg("CH3CO2", M) + "."))),
 PART("(d)(i)", IMG(2, "di")),
 PART("(d)(ii)",
      P(A("Reaction " + b("II") + ": NaCN, ethanol, heat")),
      P(A("Reaction " + b("III") + ": " + F("H2SO4") + "(aq) heat"))),
 PART("(d)(iii)",
      P(A(b("C") + " → yellow ppt: " + u("tri-iodomethane " + F("CHI3")) + " formed.")),
      P(A(b("C") + " → " + b("E") + " and " + b("F") + ": " + u("Elimination") + " of " + H2O + " to give C=C bond in " + b("E") + " and " + b("F"))),
      P(A(b("E") + " → " + F("C3H6O") + " + " + F("C2H4O2") + " : " + u("vigorous oxidation"))),
      P(A(b("E") + " has a structure of")),
      IMG(2, "diii"),
      P(A("(deduced from the structures of oxidised products, this tells us that the hydrocarbon chain is " + u("NOT a straight chain") + ")")),
      P(A(b("C") + " must have a methyl carbinol structure,")),
      IMG(2, "diii2"),
      P(A(b("C") + " can also give " + b("F") + ",")),
      IMG(2, "diii3"),
      P(A("as product upon elimination of " + H2O + " across adjacent carbons."))),
 PART("(d)(iv)",
      P(A(b("Ester B") + ": (" + F("CH3") + ")" + sub(2) + "CHCH(" + F("CH3") + ")OCOCH" + sub(2) + "C" + sub(6) + "H" + sub(5))),
      IMG(2, "div"),
      P(A(b("Ketone A") + ": (" + F("CH3") + ")" + sub(2) + "CHCH(" + F("CH3") + ")COCH" + sub(2) + "C" + sub(6) + "H" + sub(5))),
      IMG(2, "div2")),
 PART("(d)(v)", P(A(F("C6H5") + "CH=C=O"))),
]
# ------------------------------------------------------------------ Q3
CU2 = "Cu" + sup("2+")
W[3] = [
 PART("(a)(i)",
      P(A("Copper has a higher melting point than calcium because its " + u("metallic bonds are much stronger") + ". ") + N("“Metallic bond” is the electrostatic attraction between the cations and the sea of delocalised electrons.")),
      P(A("1. " + u("Cu" + sup("2+") + " is much smaller (ionic radius) than Ca" + sup("2+")) + ", so Cu" + sup("2+") + " has a higher charge density and exerts a stronger electrostatic attraction on the sea of delocalised electrons.")),
      P(A("2. " + u("Small energy difference") + " between the 3d and 4s subshells allows Cu to contribute " + u("3d and 4s electrons") + " to the sea of delocalised electrons for metallic bonding. Whereas " +
          u("calcium only contributes its two 4s electrons") + " for metallic bonding.")),
      P(A("3. " + u("Packing efficiency is higher for Cu") + " compared to Ca due to smaller " + u("cationic radius in Cu") + ", resulting in " + u("more number of Cu" + sup("2+") + " ions per unit volume") + ".")),
      P(A("More energy is required to overcome the stronger metallic bonding in Cu than Ca."))),
 PART("(a)(ii)", P(A(F("Cu(NO3)2") + "(s)" + ARROW + "CuO(s) + 2" + F("NO2") + "(g) + ½" + F("O2") + "(g)"))),
 PART("(a)(iii)",
      P(A(CU2 + " has a smaller radius than Ca" + sup("2+") + ", and thus has a higher charge/ size.<br>Hence, " + CU2 + " polarises and weakens the N–O bonds in the anion to a greater extent.<br>"
          "Less thermal energy is required to break the N–O bond in " + F("Cu(NO3)2") + " and " + F("Cu(NO3)2") + " can decompose at a lower temperature."))),
 PART("(b)(i)",
      P(A(b("Cu(s) + 2" + HP + "(aq) → " + CU2 + "(aq) + " + F("H2") + "(g)"))),
      P(A(Esub("cell") + " = " + Esub("reduction") + " " + M + " " + Esub("oxidation"))),
      P(A(b(Esub("cell") + " = 0.00 " + M + " 0.34 = " + M + "0.34 V")))),
 PART("(b)(ii)",
      P(A(DEL + i("G") + STD + " = " + M + i("nF") + Esub("cell"))),
      P(A("(Where " + i("n") + " = 2 moles of electrons)")),
      P(A(DEL + i("G") + STD + " = " + M + "(2)(96500)(" + M + "0.34)")),
      P(A(u(DEL + i("G") + STD + " = +65,620 J mol" + sup(M + "1") + " or +65.6 kJ mol" + sup(M + "1"))))),
 PART("(b)(iii)",
      P(A("In high conc of C" + L + sup(M) + ", " + u("complex ion [CuC" + L + sub(4) + "]" + sup("2" + M)) + " is formed, " + u("which decreases the concentration of " + CU2 + "(aq) ions") + " in the solution.")),
      P(A("According to Le Chatelier’s Principle, the " + u("position of equilibrium") + " for the " + CU2 + "/Cu half-equation " + u("shifts to the left") + " (favoring oxidation) to " +
          u("partially increase [" + CU2 + "]") + ".")),
      P(A("&emsp;" + CU2 + " + 2e" + sup(M) + " ⇌ Cu" + EM + i("E") + STD + " = +0.34 V")),
      P(A("This causes the " + u("(" + i("E") + "(" + CU2 + "/Cu)) to decrease until it becomes negative") + ", such that the overall " + i("E") + sub("cell") + " (in b(i)) " +
          u("becomes positive") + ". Thus, the corrosion reaction becomes spontaneous."))),
 PART("(c)(i)",
      P(A("A ligand is a " + u("molecule, atom or anion") + " that has at least " + u("a lone pair of electrons to form dative covalent (coordinate) bonds with a central metal atom/ion") + "."))),
 PART("(c)(ii)", P(A("[CuC" + L + sub(4) + "]" + sup("2" + M) + " + EDTA" + sup("4" + M) + " ⇌ [Cu(EDTA)]" + sup("2" + M) + " + 4C" + L + sup(M)))),
 PART("(c)(iii)",
      P(A("There is an " + u("increase in number of moles of ions from reactants to products") + " (from 2 to 5), thus an increase in the " +
          u("disorder/number of ways in which the particles and their energies can be distributed") + ", creating a " + u("positive entropy change") + " (" + DEL + "S > 0)."))),
 PART("(d)(i)", IMG(3, "di")),
 PART("(d)(ii)",
      TBL(["Ag" + sup("+") + " + e" + sup(M) + " ⇌ " + u("Ag"), i("E") + STD + " = +0.80 V"],
          [CU2 + " + 2e" + sup(M) + " ⇌ " + u("Cu"), i("E") + STD + " = +0.34 V"],
          ["Fe" + sup("2+") + " + 2e" + sup(M) + " ⇌ " + u("Fe"), i("E") + STD + " = " + M + "0.44 V"]),
      P(A(u("At the anode,"))),
      P(A("The " + i("E") + STD + sub("(Fe" + sup("2+") + "/Fe)") + " is the most negative, hence Fe oxidises to Fe" + sup("2+") + "(aq) first followed by Cu to " + CU2 + "(aq). Once Cu anode dissolves into the electrolyte, " +
          "Ag impurities are deposited underneath the anode as sludge.")),
      P(A(u("At the cathode,"))),
      P(A("Since only Fe" + sup("2+") + " and " + CU2 + " cations in the electrolyte, they will migrate to the cathode. " + CU2 + " is preferentially reduced since " + i("E") + STD + sub("(Cu" + sup("2+") + "/Cu)") +
          " is more positive than " + i("E") + STD + sub("(Fe" + sup("2+") + "/Fe)") + ". Hence, it will deposit on the cathode as pure Cu(s) while Fe" + sup("2+") + " remained in the electrolyte."))),
]
# ------------------------------------------------------------------ Q4
AG, IM = "[Ag" + sup("+") + "]", "[I" + sup(M) + "]"
GPPT = DEL + i("G") + '<span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;line-height:1;font-size:.72em;text-align:left;margin:0 0 0 .08em"><span style="display:block">' + PLS + '</span><span style="display:block">ppt</span></span>'
W[4] = [
 PART("(a)(i)", P(A(Ksp() + " = " + AG + " " + IM))),
 PART("(a)(ii)",
      P(A(AG + " = " + IM + " = [AgI(aq)]")),
      P(A(Ksp() + " = (8.9 × 10" + sup(M + "9") + ")" + sup(2) + "<br>&emsp;&nbsp;= " + u("7.9 × 10" + sup(M + "17") + " mol" + sup(2) + " dm" + sup(M + "6"))))),
 PART("(a)(iii)",
      P(A(AG + " = " + frac("0.025", "107.9 + 14.0 + 16.0 × 3") + "<br>&emsp;&nbsp;= " + u("1.47 × 10" + sup(M + "4") + " mol dm" + sup(M + "3")))),
      P(A("Let the solubility of AgI, after addition of " + F("AgNO3") + ", be " + i("s") + ".")),
      P(A(Ksp() + " = " + AG + " " + IM)),
      P(A("7.92 × 10" + sup(M + "17") + " = " + u("(1.47 × 10" + sup(M + "4") + " + " + i("s") + ")(" + i("s") + ")"))),
      P(A("Since solubility of AgI in water is &lt;&lt; 10" + sup(M + "4") + ", (1.47 × 10" + sup(M + "4") + " + " + i("s") + ") ≈ 1.47 × 10" + sup(M + "4"))),
      P(A("7.92 × 10" + sup(M + "17") + " = " + u("(1.47 × 10" + sup(M + "4") + ")(" + i("s") + ")"))),
      P(A("&emsp;&emsp;" + i("s") + " = 5.39 × 10" + sup(M + "13") + " mol dm" + sup(M + "3")))),
 PART("(b)(i)",
      P(A(GPPT + " = 2.303 " + i("RT") + " log" + sub(10) + " " + Ksp() + "<br>&emsp;&nbsp;&nbsp;= 2.303 × 8.31 × 298 × log" + sub(10) + " (2.0 × 10" + sup(M + "10") + ")<br>&emsp;&nbsp;&nbsp;= " +
          u(M + "5.53 × 10" + sup(4) + " J mol" + sup(M + "1"))))),
 PART("(b)(ii)",
      P(A("Ag" + sup("+") + " (aq) + C" + L + sup(M) + " (aq) ⇌ AgC" + L + "(s)&emsp;eqm (1)<br>White ppt is formed due to the " + u("formation of insoluble AgC" + L) + ".")),
      P(A("Ag" + sup("+") + " + 2" + F("NH3") + " ⇌ [Ag(" + F("NH3") + ")" + sub(2) + "]" + sup("+") + "&emsp;&emsp;eqm (2)<br>Ag" + sup("+") + " is used for the " + u("formation of a complex ion") + ", [Ag" + sup("+") +
          "] decreases,<br>Ionic product(AgC" + L + ") &lt; " + Ksp() + "(AgC" + L + ") =&gt; White ppt dissolves<br>or<br>hence POE of eqm (1) shift left, resulting in dissolution of AgC" + L + " (white ppt)")),
      P(A("Ag" + sup("+") + " + Br" + sup(M) + " ⇌ AgBr(s)&emsp;&emsp;&emsp;eqm (3)<br>Despite low conc of Ag" + sup("+") + "(aq) due to eqm 2, ionic product of AgBr still exceeds the " + Ksp() +
          " (AgBr), therefore precipitation takes place."))),
 PART("(c)",
      P(A("[Cr(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) ⇌ [Cr(" + H2O + ")" + sub(5) + "(OH)]" + sup("2+") + "(aq) + " + HP + "(aq)")),
      P(A("Due to " + u("high " + frac("charge", "size") + " ratio") + " of Cr" + sup("3+") + " cation, " + u("significant hydrolysis") + " occurs and produces more " + HP + "(aq), an acidic solution."))),
 PART("(d)(i)", P(A("Cis-trans and optical isomerism/enantiomerism"))),
 PART("(d)(ii)",
      P(A("2" + sup("2+1") + " = 8<br>(2 chiral centre + 1 double bond that can give cis-trans)")),
      P(N("(refer to diagram)")),
      IMG(4, "dii")),
 PART("(d)(iii)",
      P(A(u("σ bond") + ": Head-on overlap between sp orbital of C" + sub(1) + " and p (or sp" + sup(2) + ") orbital of O<br>" + u("π bond") + ": Side-on overlap between p orbital of C" + sub(1) + " and p orbital of O.<br>(accept diagram as well)")),
      IMG(4, "diii")),
 PART("(e)(i)", P(A("(Acidic) " + u("Hydrolysis")))),
 PART("(e)(ii)",
      IMG(4, "eii"),
      P(A(b("A") + sub(1) + " is a " + u("meso compound") + " or there is a " + u("plane of symmetry within " + b("A") + sub(1)) + " so the rotation of the plane polarised light by the two chiral centres will cancel each other out."))),
 PART("(e)(iii)", P(A("Multiple possible answers for " + b("C") + " and " + b("D") + ": Below are two possible answers:")), IMG(4, "eiii")),
 PART("(f)",
      P(A("Reagent and conditions: Fehling’s solution, warm.")),
      P(A("Observations for " + b("E") + ": no brick red precipitate formed.<br>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;" + b("F") + ": Brick red precipitate formed."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)", IMG(5, "a"), P(A(DEL + i("H") + " for reaction 1 = +2(96.0) " + M + " 91.0 = " + u("+101 kJ mol" + sup(M + "1"))))),
 PART("(b)(i)", P(A(Kp() + " = " + frac("(P" + sub(F("SO3")) + ")" + sup(2), "(P" + sub(F("SO2")) + ")" + sup(2) + "(P" + sub(F("O2")) + ")") + " Pa" + sup(M + "1")))),
 PART("(b)(ii)",
      TBL(["", "2" + F("SO2") + "(g)", "+ " + F("O2") + "(g)", "⇌", "2" + F("SO3") + "(g)"],
          ["initial partial pressure /kPa", "100", "100", "", "0"],
          ["Change partial pressure /kPa", M + "0.98(100)", M + "0.98(100) ½", "", "+0.98(100)"],
          ["eqm partial pressure /kPa", "2", "51", "", "98"]),
      P(A(Kp() + " = " + frac("(P" + sub(F("SO3")) + ")" + sup(2), "(P" + sub(F("SO2")) + ")" + sup(2) + "(P" + sub(F("O2")) + ")") + " = " + frac("(98)" + sup(2), "(2)" + sup(2) + "(51)") + " = " + u("47.1") + " " + b("kPa" + sup(M + "1")))),
      P(A(Kp() + " = " + frac("(98000)" + sup(2), "(2000)" + sup(2) + "(51000)") + " = 0.0471 " + b("Pa" + sup(M + "1"))))),
 PART("(b)(iii)",
      P(A("As volume of the vessel increased, total pressure decreases. Based on LCP, POE shift left to favour the side with more mole of gaseous particles. Hence % conversion will decrease.")),
      P(A(Kp() + " remains the same as temperature is kept constant."))),
 PART("(c)(i)", IMG(5, "ci")),
 PART("(c)(ii)",
      P(A("HCFCs are greenhouse gases which trap heat leading to global warming.")),
      P(N(b("<u>Unacceptable Answer</u>") + ":")),
      P(N("• Destroys the ozone layer (This is incorrect because the question asks for " + b("one other effect") + " besides the ODP mentioned in the text)."))),
 PART("(d)(i)", IMG(5, "di")),
 PART("(d)(ii)", P(A("Step 1: Ethanolic NaOH, heat")), P(A("Step 2: aq " + F("Br2")))),
 PART("(d)(iii)", IMG(5, "diii"), P(A("Accept other structures of " + b("L") + " with Br attached to C=C and no gem diol/triol."))),
 PART("(d)(iv)", IMG(5, "div")),
 PART("(e)(i)",
      P(A("When " + F("Cu(OH)2") + " is about to precipitate out,&emsp;IP(" + F("Cu(OH)2") + ") = " + Ksp() + "(" + F("Cu(OH)2") + ")<br>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;[" + CU2 + "][" + OHM + "]" + sup(2) + " = 2.20 × 10" + sup(M + "20"))),
      P(A("[" + OHM + "] at maximum separation = " + sqrt(frac("2.20 × 10" + sup(M + "20"), "0.200")) + " = " + b(u("3.32 × 10" + sup(M + "10") + " mol dm" + sup(M + "3"))) + " [1m]"))),
 PART("(e)(ii)",
      P(A("at maximum separation, [" + OHM + "] = 3.32 × 10" + sup(M + "20") + " mol dm" + sup(M + "3"))),
      P(A("[Pd" + sup("2+") + "] remaining in solution = " + frac("1.00 × 10" + sup(M + "31"), "(3.32 × 10" + sup(M + "10") + ")" + sup(2)) + " = " + b(u("9.07 × 10" + sup(M + "13") + " mol dm" + sup(M + "3"))))),
      P(A("%[Pd" + sup("2+") + "] remaining = " + frac("9.07 × 10" + sup(M + "13"), "0.200") + " × 100% = 4.54 × 10" + sup(M + "10") + "% &lt; 0.01%")),
      P(A("Therefore KOH can be used to effectively separate Pd" + sup("2+") + " (by precipitation) from " + CU2 + "."))),
]

# ------------------------------------------------------------------ proposed wording fixes (wait for the user's ruling)
PROPOSED_FIXES = [   # (qn, old, new, expected count)
    (1, "(Lewis acid)).", "(Lewis acid).", 1),                                   # stray closing bracket
    (4, "sp orbital of C", "sp" + sup(2) + " orbital of C", 1),                    # carbonyl C is sp2 (the school's own diagram says sp2)
    (5, "for reaction 1 =", "for reaction 5.1 =", 1),                              # label
    (5, "0.98(100) ½", "0.98(100) × ½", 1),                                        # missing multiplication sign
    (5, "[" + OHM + "] = 3.32 × 10" + sup(M + "20"), "[" + OHM + "] = 3.32 × 10" + sup(M + "10"), 1),   # exponent typo
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    if APPLY_PROPOSED:
        for q, old, new, n in PROPOSED_FIXES:
            if q == qn:
                assert h.count(old) == n, (qn, old, h.count(old)); h = h.replace(old, new)
    brackets = re.findall(r"\[\d+[^\]]*\]", re.sub(r"<[^>]+>", "", h))
    assert all(x in ("[1]", "[1 for both equations]", "[1m]") for x in brackets), (qn, brackets)
    out[str(qn)] = h

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
