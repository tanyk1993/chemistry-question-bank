"""Hand transcription of the NJC 2026 H2 Prelim Paper 2 (9476/02) suggested answers
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's answers PDF only (21 pages): the question paper with each answer typed in blue inside a
box, red notes, bold/underlined mark-bearing keywords. Typed from the rendered pages and the text layer.

Run from the repo root:
    python3 ingest/build_njc26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_njc26_p2.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in
span.ans with <u> on the mark-bearing keywords (the school's bold/underlined blue text); figures are bare
img.ws-fig[data-asset] (the user snips them: NJC_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp (no
thead/th); the school's red text is span.note.
RULED_FIXES holds the wording changes made to the school text; nothing is changed silently.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "NJC_H2_P2", 2026
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
ARROW = " → "
def ion(sym, ch): return sym + sup(ch)
HCL, H2O, HP = "H" + CL, "H" + sub(2) + "O", "H" + sup("+")
def dH(s=""): return DEL + i("H") + (sub(s) if s else "")
MDM = "mol dm" + sup(M + "3")

ASSETS = []     # (question, slot) in per-question DOM order
# 2026-11-11: Q2 ans-bii was re-uploaded as _v2 (a deleted-and-replaced object kept serving its cached copy on Supabase)
PATH_OVERRIDE = {(2, "bii"): "NJC_H2_P2_Q2_ans-bii_2026_v2.png"}
def _path(qn, slot): return PATH_OVERRIDE.get((qn, slot), "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR))
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
PCL4 = "[PC" + L + sub(4) + "]" + sup("+")
PCL6 = "[PC" + L + sub(6) + "]" + sup(M)
W[1] = [
 PART("(a)",
      P(A("Ionic radius " + u("decreases") + " across isoelectronic series. " + u("Nuclear charge") + " across isoelectronic series " + u("increases") +
          " while " + u("number of electrons remains the same") + ". " + u("Nuclear attraction for the valence electrons") + " increases.")),
      P(A("Anions have " + u("bigger") + " ionic radius than the cations. Anions have " + u("one additional filled electron shell") +
          " than cations in the same period. the " + u("valence electrons are further away") + " from nucleus and have greater " + u("shielding effect") +
          " which outweighs the " + u("higher nuclear charge") + " in " + u("anions") + "."))),
 PART("(b)(i)", P(A("B" + sup("2+") + "(g) → B" + sup("3+") + "(g) + e" + sup(M)))),
 PART("(b)(ii)",
      P(A("There is a significant decrease for 3" + sup("rd") + " IE for " + b("C") + " compared to " + b("B") + ", implying that the 3" + sup("rd") +
          " electron removed for " + b("B") + " is from an electron shell that is closer to the nucleus/ 2" + sup("nd") + " electron shell.")),
      P(A("OR 3" + sup("rd") + " electron removed for " + b("C") + " is from an electron shell that is further from the nucleus/ 3" + sup("rd") + " electron shell.")),
      P(A("Hence " + b("B") + " is Mg (Group 2)/ " + b("C") + " is element A" + L + " (Group 13) and phosphorus will be " + b("E") + "./ " + b("E") +
          " will be group 15, phosphorus."))),
 PART("(c)(i)", P(A("P atom (from Period 3) in PC" + L + sub(5) + " possesses " + u("vacant orbitals in the valence shell/ vacant 3d orbital") +
                    ", but " + u("not for C atom (from Period 2) in CC" + L + sub(4)) + ", " + u("to accept a lone pair of electrons from a water molecule") +
                    " for hydrolysis."))),
 PART("(c)(ii)", P(A("PC" + L + sub(5) + " + 4" + H2O + ARROW + "H" + sub(3) + "PO" + sub(4) + " + 5" + HCL))),
 PART("(c)(iii)", P(A("cation: " + PCL4)), P(A("anion: " + PCL6))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A("HI has a " + u("larger electron cloud size") + " and is more easily distorted compared to " + HCL + ", resulting in a " +
          u("stronger instantaneous dipole–induced dipole interaction (id–id)") + " between HI molecules.")),
      P(A(u("More energy is required to break") + " the stronger id-id and permanent dipole–permanent dipole (pd–pd) between HI molecules compared to the "
          "id-id and permanent dipole–permanent dipole (pd–pd) interactions between " + HCL + " molecules, resulting in higher boiling point of HI."))),
 PART("(a)(ii)",
      P(A(u("pH of " + HCL + " = 0.70"))),
      P(A("Both HI and " + HCL + " are strong acids and are taken to " + u("dissociate completely in water") + ". Since the two solutions " +
          u("have the same concentration") + ", they " + u("produce the same concentration of " + HP + " ions") + " and hence have the same pH."))),
 PART("(a)(iii)",
      P(A("Reducing agent.")),
      P(A("Oxidation state of I is increased from " + M + "1 in HI to 0 in I" + sub(2) + ".")),
      P(A("or")),
      P(A("Oxidation state of C has changed from " + M + "2 to " + M + "4"))),
 PART("(b)(i)", P(A("Enthalpy change of hydration is the " + u("heat released") + " when " + u("1 mol") + " of " + u("gaseous") + " F" + sup(M) + " is " +
                    u("dissolved in water") + " to form " + u("an infinitely diluted solution") + "."))),
 PART("(b)(ii)", IMG(2, "bii"),
      P(A(dH("dissociation") + " = +48 + 562 + 1310 " + M + " 328 " + M + " 1606 = " + M + "14 kJ mol" + sup(M + "1")))),
 PART("(b)(iii)",
      P(A(K + sub("a") + " = 10" + sup(M + "3.14") + " = 7.24 × 10" + sup(M + "4"))),
      P(A(K + sub("a") + " = " + frac("[" + HP + "] [F" + sup(M) + "]", "[HF]") + " = " + frac("<i>x</i>" + sup(2), "0.20 " + M + " <i>x</i>") +
          " = 7.24 × 10" + sup(M + "4"))),
      P(A("Since HF is a weak acid, <i>x</i> &lt;&lt; 0.20, 0.20 " + M + " <i>x</i> ≈ 0.20,")),
      P(A("[" + HP + "] = " + sqrt(K + sub("a") + " × [weak acid]"))),
      P(A("[" + HP + "] = " + sqrt("7.24 × 10" + sup(M + "4") + " × 0.2") + " = 0.012 " + MDM)),
      P(A("pH = " + M + " lg [" + HP + "] = " + u("1.92 (2 d.p.)")))),
 PART("(b)(iv)", IMG(2, "biv"),
      P(A("In solid HF, the molecules are held in a lattice state by hydrogen bonding, which is weaker than the covalent bond existing within the molecule. "
          "Hence, the longer bond distance is due to the hydrogen bond."))),
]
# ------------------------------------------------------------------ Q3
TIH2O6 = "[Ti(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+")
TI3 = "Ti" + sup("3+")
W[3] = [
 PART("(a)(i)",
      P(A("electronic configuration 1<i>s</i>" + sup(2) + "2<i>s</i>" + sup(2) + "2<i>p</i>" + sup(6) + "3<i>s</i>" + sup(2) + "3<i>p</i>" + sup(6) +
          "3<i>d</i>" + sup(2) + "4<i>s</i>" + sup(2))),
      P(A("The 4s and 3d electrons have " + u("very similar energies") + ".")),
      P(A("Titanium can therefore " + u("lose/use") + " different numbers of these electrons to form ions with different oxidation states."))),
 PART("(a)(ii)", IMG(3, "aii")),
 PART("(a)(iii)", IMG(3, "aiii")),
 PART("(a)(iv)",
      P(A("In the " + u("presence of ligands, electronic repulsion") + " between lone pair electrons of ligands and the electrons in d orbitals of " + TI3 +
          " causes the " + u("degenerate d-orbitals") + " of " + TI3 + " " + u("to split into two different energy levels with a small energy gap") +
          ", ∆<i>E</i> (d splitting). " + N("[No credit for this answer as part (ii) of the question has addressed this concept.]"))),
      P(A("As the " + u("3d subshell is partially filled") + ", electrons in the " + u("lower energy d-orbitals") + " can " +
          u("absorb light of a certain wavelength in the visible light spectrum") + " with energy corresponding to the energy gap, ∆<i>E</i>, and be " +
          u("promoted to the higher energy d-orbitals") + " (d−d transition).")),
      P(A("The colour observed is the " + u("complement of the colour absorbed") + "."))),
 PART("(b)",
      P(A("Mg" + sup("2+") + " + 2e → Mg --------(1)")),
      P(A("<i>Q</i> = <i>It</i> = 50,000 × (24 × 60 × 60) = 4.32 × 10" + sup(9) + " C")),
      P(A("Moles of electrons = <i>Q</i> / <i>F</i> = 4.32 × 10" + sup(9) + " / 96500<br>= 4.477 × 10" + sup(4) + " mol")),
      P(A("Moles of Mg = 4.477 × 10" + sup(4) + " × ½ = 2.238 × 10" + sup(4) + " mol")),
      P(A("Mass of Mg = 2.238 × 10" + sup(4) + " × 24.3 = 5.44 × 10" + sup(5) + " g = " + u("544 kg")))),
 PART("(c)(i)",
      P(A("The catalyst acts as a " + u("heterogeneous catalyst") + ", providing " + u("a surface on which reactant molecules") + " (ethene) to " + u("adsorb") + ".")),
      P(A("The adsorption " + u("weakens the bonds in the reactant molecules and/or brings them into close proximity") + " in the correct orientation for reaction, " +
          u("lowering activation energy") + ".")),
      P(A("Reaction occurs, forming products which " + u("desorb") + " from the surface of the catalyst, " + u("leaving the active sites") + " of the catalyst available " +
          u("for next reactants") + "."))),
 PART("(c)(ii)",
      P(A("The Ziegler-Natta catalyst produces " + u("linear poly(ethene)") + " with a highly ordered structure. This " + u("allows") + " the " + u("polymer chains") +
          " to " + u("pack closely together") + ", " + u("increasing") + " the strength of " + u("intermolecular forces") +
          " (instantaneous dipole-induced dipole forces) between chains, hence a higher melting point.")),
      P(A("The radical process produces a " + u("more branched, less ordered polymer") + ", polymer chains are " + u("not so closely packed") +
          ", intermolecular forces are weaker, hence a lower melting point."))),
 PART("(d)(i)",
      TBL(["", "K", "Sn", "C" + L, "O", "H"],
          ["Mass/<i>A</i>" + sub("r"),
           frac("23.28", "39.1") + "<br>= 0.5954", frac("35.34", "118.7") + "<br>= 0.2977", frac("21.14", "35.5") + "<br>= 0.5955",
           frac("19.05", "16") + "<br>= 1.1906", frac("1.19", "1") + "<br>= 1.19"],
          ["", frac("0.5954", "0.2977") + " = 2", frac("0.2977", "0.2977") + " = 1", frac("0.5955", "0.2977") + " = 2.000",
           frac("1.1906", "0.2977") + " = 3.999", frac("1.19", "0.2977") + " = 3.997"],
          ["Mole ratio", "2", "1", "2", "4", "4"]),
      P(A("empirical formula is K" + sub(2) + "SnC" + L + sub(2) + "O" + sub(4) + "H" + sub(4) + "."))),
 PART("(d)(ii)", P(A("[SnC" + L + sub(2) + "(OH)" + sub(4) + "]" + sup("2" + M))),
      P(A("Since formula has 2 K" + sup("+") + ", polyatomic (complex) anion has " + M + "2 charge."))),
 PART("(d)(iii)", P(A("Octahedral"))),
 PART("(d)(iv)", IMG(3, "div")),
]
# ------------------------------------------------------------------ Q4
PKB = "p" + K + sub("b")
W[4] = [
 PART("(a)(i)",
      P(A("The " + u("lone pair of electrons") + " on the aromatic " + u("amine nitrogen (N" + sup("b") + ")") + " is " +
          u("delocalised into the π-electron system/cloud of the benzene ring") + ", making it " + u("less available to accept a proton") + ", thus a " +
          u("weaker base") + " and hence a higher " + PKB + " value.")),
      P(A("The " + u("electron density of lone pair") + " on the " + u("aliphatic amine (N" + sup("a") + ")") + " is " + u("enhanced/more available") +
          " due to " + u("electron-donating alkyl groups") + ", making it " + u("more basic") + "/more likely to accept proton, thus a " + u("stronger base") +
          " and hence a lower " + PKB + " value."))),
 PART("(a)(ii)",
      P(A("Maximum buffer capacities occur at points " + b("A") + " and " + b("C") + " where:")),
      P(A("pOH = p" + K + sub("b") + " and hence pH = 14 " + M + " p" + K + sub("b"))),
      P(A("At " + b("A") + ": (p" + K + sub("b") + " = 5.00 corresponds to stronger base)<br>pH = 14 " + M + " 5.00 = 9.00")),
      P(A("At " + b("C") + ": (p" + K + sub("b") + " = 11.5 corresponds to weaker base)<br>pH = 14 " + M + " 11.5 = 2.5")),
      P(A("pH at point " + b("B") + " = " + frac("1", "2") + " × (9.00 + 2.5) = " + u("5.75")))),
 PART("(a)(iii)", IMG(4, "aiii"),
      P(A("Salt " + b("D") + " is the " + u("conjugate acid of a weak base") + ", thus it is a " + u("stronger acid than water") + ". So it will undergo " +
          u("salt/acid hydrolysis") + " to produce an acidic solution with pH less than 7."))),
 PART("(b)(i)", P(A(u("Energy released") + " from the " + u("ion-dipole interactions") + " of procaine hydrochloride with the " + u("polar water molecules") +
                    " is " + u("sufficient to overcome") + " the " + u("strong hydrogen bonds") + " between water molecules and the " + u("ionic bonds") +
                    " between the oppositely charged ions in procaine hydrochloride."))),
 PART("(b)(ii)",
      P(A("1 ppm = 1 mg in 1000 g of solvent<br>236 ppm = 236 mg per 1000 g or 1000 cm" + sup(3) + " of water<br>since density of solution is 1 g cm" + sup(M + "3") + ".")),
      P(A("in <b>100.0 cm" + sup(3) + "</b> of diluted solution = 100 g of diluted solution,")),
      P(A("Mass = " + frac("236 mg", "1000 g") + " × 100 g = 23.6 mg")),
      P(A("Amount in 100.0 cm" + sup(3) + " diluted solution<br>= " + frac("0.0236 g", "237.3 g mol" + sup(M + "1")) + " = 9.945 × 10" + sup(M + "5") + " mol")),
      P(A("Concentration (diluted) = " + frac("9.945 × 10" + sup(M + "5"), "0.1000") + " = 9.945 × 10" + sup(M + "4") + " " + MDM)),
      P(A("Concentration (original) = 9.945 × 10" + sup(M + "4") + " × 10<br>= 9.945 × 10" + sup(M + "3") + " " + MDM))),
 PART("(c)(i)", IMG(4, "ci"),
      P(A("(Must show carboxylate salt, not the carboxylic acid, due to alkaline conditions.)"))),
 PART("(c)(ii)",
      P(A(u("From 10 °C to 35 °C") + " (or before peak) the activity " + u("increases") + " due to " + u("more particles with energy greater than activation energy") +
          ", hence " + u("increase in frequency of effective collisions") + ".")),
      P(A(u("From 35 °C to 55 °C") + " (after peak) The activity " + u("decreases") + " (or drops significantly). As esterase " +
          u("denature/lose its function/becomes deactivated/the 3D shape of the active site changes/lost/destroyed") +
          ", preventing the substrate from binding."))),
 PART("(d)(i)",
      P(A("This is the equation of a straight line (<i>y</i> = <i>mx</i> + <i>c</i>).")),
      P(A("Point 1: (ln([<b>P</b>]" + sub(1) + "), ln(Rate)" + sub(1) + ") = (" + M + "4.0, " + M + "11.0)<br>Point 2: (ln([<b>P</b>]" + sub(2) +
          "), ln(Rate)" + sub(2) + ") = (0, " + M + "7.0)")),
      P(A("<i>m</i> = " + frac(M + "7.0 " + M + " (" + M + "11.0)", "0 " + M + " (" + M + "4.0)") + " = 1.0")),
      P(A("Since the " + u("gradient is 1") + ", <i>m</i> = 1 (the reaction is " + u("first-order") + " with respect to procaine)")),
      P(A("Calculate the value for " + i("k") + sub(1) + ".")),
      P(A("y-intercept = ln(" + i("k") + sub(1) + ") = " + M + "7.0")),
      P(A(i("k") + sub(1) + " = e" + sup(M + "7.0"))),
      P(A(i("k") + sub(1) + " = 9.12 × 10" + sup(M + "4") + " s" + sup(M + "1")))),
 PART("(d)(ii)",
      P(A("Reaction is " + u("first-order") + " with respect to procaine:")),
      P(A(frac("<i>t</i>" + sub("1/2") + "(B)", "<i>t</i>" + sub("1/2") + "(A)") + " = " + frac("69.3", "138.6") + " = " + frac("1", "2"))),
      P(A("As conc. OH" + sup(M) + " " + u("doubled") + ", <i>t</i>" + sub("1/2") + " " + u("is halved") + " implying that " + u("rate is doubled") + ".")),
      P(N("OR:")),
      P(A("<i>t</i>" + sub("1/2") + " = " + frac("ln 2", "<i>k</i>" + sub("obs")) + " = " + frac("ln 2", "<i>k</i>[OH" + sup(M) + "]" + sup("<i>n</i>")))),
      P(A(frac("<i>t</i>" + sub("1/2") + "(A)", "<i>t</i>" + sub("1/2") + "(B)") + " = " + "(" + frac("[OH" + sup(M) + "]" + sub("B"), "[OH" + sup(M) + "]" + sub("A")) + ")" + sup("<i>n</i>"))),
      P(A(frac("138.6", "69.3") + " = (" + frac("0.20", "0.10") + ")" + sup("<i>n</i>"))),
      P(A("2 = (2)" + sup("<i>n</i>") + "<br><i>n</i> = 1"))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", IMG(5, "ai")),
 PART("(a)(ii)",
      P(A("NH" + sub(3) + " nucleophile will " + u("preferentially attack") + " the " + u("C atom bonded to 2 small H atoms") + " as there is " +
          u("less steric hindrance") + " around this C atom compared to the C bonded to bulky methyl groups. AND")),
      P(A("this C atom is " + u("more electron deficient") + " compared to the " + u("C atom bonded to 2 electron-donating methyl groups") +
          " which reduces the partial positive charge on carbon."))),
 PART("(b)(i)", P(A("Theoretical value = BE(C–C) + 2 BE(C–O) = 350 + 2(360) = " + u("1070 kJ mol" + sup(M + "1"))))),
 PART("(b)(ii)",
      P(A("Let actual value of BE(C–C) + 2BE(C–O) = <i>y</i>")),
      P(A(dH("rxn") + " = ∑BE(bonds broken) " + M + " ∑BE(bonds formed)<br>= [BE(C=C) + ½ BE(O=O)] " + M + " [BE(C–C) + 2BE(C–O)]")),
      P(A(M + "107 = [610 + ½ (496)] " + M + " <i>y</i><br><i>y</i> = " + u("965 kJ mol" + sup(M + "1"))))),
 PART("(b)(iii)",
      P(A(u("Bond angles around C in epoxyethane is 60°") + " instead of the usual 109.5° for C with 4 single bonds (" + u("angle/ring strain") + " in the 3-membered ring).")),
      P(A("This bond angle creates " + u("increased repulsion between the bonding pairs of electrons around C") + ", leading to " + u("weaker C−C and C−O bonds") +
          ", " + u("hence lower bond energies") + " as compared to theoretical value.<br>Hence " + u("bonds in epoxyethane break very easily/ ring open very easily") +
          ", making epoxyethane very reactive."))),
 PART("(c)(i)", P(A("This suggests bottle " + b("Z") + " contains chlorobenzene. In chlorobenzene, the chlorine p-orbital overlaps with the benzene p-system, "
                    "giving the C–C" + L + " bond partial double-bond character. This makes the " + u("bond too strong to be broken") + " by water, so no hydrolysis occurs " +
                    u("and no ions are released") + "."))),
 PART("(c)(ii)", P(A("The changes are caused by hydrolysis of the C–C" + L + " bond when each compound reacts with water, producing H" + sup("+") + " and C" + L +
                     sup(M) + " ions. The release of H" + sup("+") + " causes the pH to drop. The release of free mobile ions increases electrical conductivity."))),
 PART("(c)(iii)",
      P(A("Bottle " + b("X") + " is benzoyl chloride; Bottle " + b("Y") + " is chlorophenylmethane.")),
      P(A("In benzoyl chloride, the carbon is bonded to two highly electronegative atoms (oxygen and chlorine), making it highly electron-deficient. "
          "Benzoyl chloride is very susceptible to nucleophilic attack by water, undergoing rapid hydrolysis, giving rise to an almost instant electrical "
          "conductivity spike and pH drop to 1.5.")),
      P(A("In chlorophenylmethane, the carbon is bonded to only one electronegative atom (chlorine), hence the carbon is less electron-deficient than the carbon in "
          "benzoyl chloride. So hydrolysis is much slower, resulting in a gradual increase in electrical conductivity and a slower pH drop to 4.5."))),
]
# ------------------------------------------------------------------ Q6
W[6] = [
 PART("(a)(i)", IMG(6, "ai")),
 PART("(a)(ii)",
      P(A("Step I: K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + ", dil H" + sub(2) + "SO" + sub(4) + ", heat with immediate distillation")),
      P(A("Step II: HCN, trace NaCN, cold")),
      P(A("Step III: dil H" + sub(2) + "SO" + sub(4) + ", heat"))),
 PART("(b)", IMG(6, "b"),
      P(N("After Hofmann reaction, there is intra-molecular nucleophilic substitution.")), IMG(6, "b2")),
]

# ------------------------------------------------------------------ rulings / wording fixes made to the school text
# Other wording changes made while typing (listed to the user): 5(b)(iii) "increased in repulsion" -> "increased repulsion";
# 4(d)(i) "y = -mx + c" -> "y = mx + c"; the duplicated "(or 9.12 x 10^-4 s^-1)" dropped; 5(c)(i) stray space before the full stop.
RULED_FIXES = [   # (qn, old, new, expected count)  PROPOSED to the user with the snip list; nothing silent
    (1, "in the same period. the ", "in the same period. The ", 1),            # lower-case sentence start
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
