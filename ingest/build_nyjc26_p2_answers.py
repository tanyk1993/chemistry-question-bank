"""Hand transcription of the NYJC 2026 H2 Prelim Paper 2 (9476/02) suggested answers
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's answers docx/PDF (24 pages): the question paper with each answer typed in blue,
red marking notes, underlined/bold mark-bearing keywords. Typed from the rendered pages and the text layer.

Run from the repo root:
    python3 ingest/build_nyjc26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_nyjc26_p2.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in
span.ans with <u> on the mark-bearing keywords; figures are bare img.ws-fig[data-asset] (the user snips them:
NYJC_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp; the school's red marking notes are span.note;
the school's [n] mark ticks are dropped. Wording rulings follow the NYJC 2026 P1 rulings (typos/grammar fixed,
short forms spelled in full); see RULED_FIXES and the list given to the user.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "NYJC_H2_P2", 2026
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
SN1, SN2 = "S" + sub("N") + "1", "S" + sub("N") + "2"

ASSETS = []     # (question, slot) in per-question DOM order
# 2026-11-11: Q2 ans-bii was re-uploaded as _v2 (a deleted-and-replaced object kept serving its cached copy on Supabase)
PATH_OVERRIDE = {}
def _path(qn, slot): return PATH_OVERRIDE.get((qn, slot), "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR))
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
RULED_FIXES = []
KSP = i("K") + sub("sp")
KA = i("K") + sub("a")
ARm = i("A") + sub("r")
NH3OHP = "NH" + sub(3) + "OH" + sup("+")
CR2O7 = "Cr" + sub(2) + "O" + sub(7) + sup("2" + M)
def BUL(*items):   # the school's bullets are typed as separate answer paragraphs (no ul in worked solutions)
    return [P(A(x)) for x in items]
def NOTE(t): return P(N(t))
def eq(s): return P(A(s))

# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", P(A("The relative atomic mass, " + ARm + ", of an element is the " + u("weighted average mass of the isotopes") + " of the element compared to " +
                    frac("1", "12") + " the mass of a <sup>12</sup>C atom."))),
 PART("(a)(ii)",
      P(A("relative % abundance of unknown isotope = (100 " + M + " 91.9 " + M + " 6.0) = 2.1%")),
      P(A("Let the isotopic mass of the third isotope be <b>a</b>.")),
      P(A("55.8 = " + frac("53.9 × 6.0 + 55.9 × 91.9 + <b>a</b> × 2.1".replace("<b>a</b>", "<i>a</i>"), "100"))),
      P(A("119.39 = 2.1<i>a</i>")),
      P(A("<i>a</i> = 56.85 ≈ 56.9"))),
 PART("(b)", P(A("Fe" + sup("2+") + ": 1<i>s</i>" + sup(2) + "2<i>s</i>" + sup(2) + "2<i>p</i>" + sup(6) + "3<i>s</i>" + sup(2) + "3<i>p</i>" + sup(6) + "3<i>d</i>" + sup(6))),
         P(A("10 electron pairs"))),
 PART("(c)", P(A("The " + u("radius decreases") + ". Since nuclear charge remains the same but there is " + u("one less shell of electrons") +
                 ", the valence electrons will experience significantly less shielding effect. As the outermost shell is now closer to the nucleus, they "
                 "experience stronger net attraction to the nucleus, hence radius decreases."))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)",
      P(A("pOH = 14.00 " + M + " 7.50 = 6.50")),
      P(A("[OH" + sup(M) + "] = 10" + sup(M + "6.50") + " = 3.162 × 10" + sup(M + "7") + " " + MDM)),
      NOTE("Calculate [OH" + sup(M) + "] from pH."),
      P(A("Ionic product of Fe(OH)" + sub(2) + " = (0.0150)(3.162 × 10" + sup(M + "7") + ")" + sup(2) + " = 1.50 × 10" + sup(M + "15"))),
      P(A("Since ionic product > " + KSP + ", a precipitate of Fe(OH)" + sub(2) + " will form.")),
      NOTE("Allow error carried forward.")),
 PART("(b)(i)",
      P(A("Amount of " + NH3OHP + " in 10.0 cm" + sup(3) + " = " + frac("1.04", "69.5") + " = 0.01496 mol")),
      P(A("Concentration = " + frac("0.01496", "10.0") + " × 1000 = 1.50 " + MDM))),
 PART("(b)(ii)",
      P(A(u("Step 1: find the amount of e" + sup(M) + " transferred"))),
      P(A(CR2O7 + " + 14H" + sup("+") + " + 6e" + sup(M) + " ⇌ 2Cr" + sup("3+") + " + 7" + H2O)),
      P(A("Amount of " + CR2O7 + " reacted = 2.00 × " + frac("12.50", "1000") + " = 0.0250 mol")),
      P(A("Total amount of e" + sup(M) + " gained by " + CR2O7 + " = 0.0250 × 6 = 0.150 mol")),
      P(A(u("Step 2: find the amount of e" + sup(M) + " lost " + b("per mol") + " of " + NH3OHP))),
      P(A("Amount of " + NH3OHP + " that reacted with " + CR2O7 + " = 1.50 × " + frac("25.0", "1000") + " = 0.0374 mol")),
      NOTE("Allow error carried forward for the concentration value from (i)."),
      P(A("Hence, " + b("0.0374 mol " + NH3OHP + " loses 0.150 mol of e" + sup(M)) + ".")),
      P(A("Amount of e" + sup(M) + " lost per mol of " + NH3OHP + " = " + frac("0.150", "0.0374") + " = 4 (nearest whole number)")),
      P(A(u("Step 3: deduce the product based on the new oxidation state of N"))),
      P(A("Let <i>x</i> be the initial oxidation state of N in " + NH3OHP + ":")),
      P(A("<i>x</i> + 3(+1) + (" + M + "2) + 1 = +1, so <i>x</i> = " + M + "1")),
      P(A("Final oxidation state of N in the product = " + M + "1 + 4 = " + u("+3"))),
      P(A("The product is " + u("N" + sub(2) + "O" + sub(3)) + ".")),
      NOTE("Not required in the answer:"),
      TBL(["", "NO", "NO" + sub(2), "N" + sub(2) + "O" + sub(3)], ["Oxidation state of N", "+2", "+4", "+3"])),
 PART("(c)(i)",
      *BUL("The halogens have " + b("simple molecular structure") + " with weak " + b("instantaneous dipole–induced dipole forces between molecules") + ".",
           "Down the group, the number of electrons per molecule increases. The " + b("electron cloud of the molecule increases and becomes more polarisable") +
           " and the " + b("strength of the instantaneous dipole–induced dipole forces increases") + ". More energy is required to overcome these stronger forces, "
           "so " + b("boiling point increases and volatility decreases") + ".")),
 PART("(c)(ii)",
      *BUL("As the " + b("atomic radius of the halogen atom increases") + ", the " + b("H–X bond length") + " becomes " + b("longer") + " and hence the strength becomes " + b("weaker") + ".",
           "The strength of the H–X bond " + b("decreases") + " in the order: HF > H" + CL + " > HBr > HI due to the increase in atomic radius of the halogen atom.",
           "Hence, thermal stability of HX " + b("decreases") + " down the group.")),
 PART("(d)",
      P(A("[Ag" + sup("+") + "][C" + L + sup(M) + "] = " + KSP)),
      P(A(frac("1.00", "2") + " × " + frac("[C" + L + sup(M) + "]", "2") + " = 1.8 × 10" + sup(M + "10"))),
      P(A("0.25 [C" + L + sup(M) + "] = 1.8 × 10" + sup(M + "10"))),
      P(A("[C" + L + sup(M) + "] = 7.2 × 10" + sup(M + "10") + " " + MDM))),
]
# ------------------------------------------------------------------ Q3
MG, SR = "Mg", "Sr"
W[3] = [
 PART("(a)(i)",
      *BUL("Both Z" + sup("2+") + " and W" + sup("2+") + " have the same ionic charge but the ionic radius of Z" + sup("2+") + " is larger than that of W" + sup("2+") + ".",
           "Charge density (thus polarising power) of Z" + sup("2+") + " is smaller than that of W" + sup("2+") + ".",
           "Electron cloud of CO" + sub(3) + sup("2" + M) + " becomes less polarised by Z" + sup("2+") + ". C–O bond in ZCO" + sub(3) + " is less weakened / weakened to a smaller extent.",
           "More energy is needed to break the C–O bond."),
      P(A("Thus, ZCO" + sub(3) + " decomposes at a higher temperature than the carbonate of W.")),
      NOTE("4 bullets: 2 marks; 2 bullets: 1 mark.")),
 PART("(a)(ii)", P(A("W is Sr, X is Ca, Y is Mg, Z is Ba"))),
 PART("(b)(i)",
      P(A("MgC" + L + sub(2) + " has a " + u("giant ionic structure") + " (point 1).")),
      P(A("When in liquid state, the " + u("ionic bonds between the oppositely charged ions, Mg" + sup("2+") + " and C" + L + sup(M) + ", are broken") + " (point 2), "
          "resulting in the " + u("ions being mobile to carry charges") + " (point 3) and conduct electricity.")),
      P(A("SiC" + L + sub(4) + " has a " + u("simple molecular structure") + " (point 4).")),
      P(A("When in liquid state, the instantaneous dipole–induced dipole forces between SiC" + L + sub(4) + " are broken.")),
      P(A("The covalent bonds between Si and C" + L + " atoms are not broken, hence the " + u("electrons are still localised in covalent bonds between the Si and C" + L + " atoms") +
          " (point 5). There is " + u("no free mobile charge carrier") + " (point 6), hence SiC" + L + sub(4) + " is not able to carry charges and conduct electricity.")),
      NOTE("6 points: 2 marks; 2–3 points: 1 mark.")),
 PART("(b)(ii)", P(A("MgC" + L + sub(2) + " 6.5 and SiC" + L + sub(4) + " 1 or 2"))),
 PART("(b)(iii)",
      TBL(["<b>With aqueous sodium hydroxide</b>", ""],
          ["aluminium oxide", "Al" + sub(2) + "O" + sub(3) + "(s) + 2NaOH(aq) + 3" + H2O + "(l) → 2NaAl(OH)" + sub(4) + "(aq)"],
          ["one of the sulfur oxides", "SO" + sub(2) + "(g) + 2NaOH(aq) → Na" + sub(2) + "SO" + sub(3) + "(aq) + " + H2O + "(l)<br><b>OR</b><br>SO" + sub(3) +
           "(g) + 2NaOH(aq) → Na" + sub(2) + "SO" + sub(4) + "(aq) + " + H2O + "(l)"],
          ["<b>With aqueous hydrochloric acid</b>", ""],
          ["aluminium oxide", "Al" + sub(2) + "O" + sub(3) + "(s) + 6H" + CL + "(aq) → 2A" + L + "C" + L + sub(3) + "(aq) + 3" + H2O + "(l)"],
          ["one of the sulfur oxides", "SO" + sub(2) + " + " + H2O + " → H" + sub(2) + "SO" + sub(3) + "<br><b>OR</b><br>SO" + sub(3) + " + " + H2O + " → H" + sub(2) + "SO" + sub(4)])),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)", P(A("Electrophilic addition")), IMG(4, "ai")),
 PART("(a)(ii)", IMG(4, "aii")),
 PART("(a)(iii)", IMG(4, "aiii")),
 PART("(b)",
      P(A("In the benzylic carbocation formed, the " + b("p orbital") + " of the positively charged C atom " + b("overlaps with the pi electron cloud") +
          " of the benzene ring (resonance-stabilised). This allows the " + b("positive charge") + " to be " + b("dispersed over the ring") + ", " +
          b("stabilising the carbocation") + " intermediate, thus " + SN1 + " mechanism is favoured.")),
      P(A("The " + b("presence of the bulky benzene ring") + " directly bonded to the C atom of the C–Br bond " + b("sterically hinders the backside approach of the nucleophile") +
          ", thus " + SN2 + " mechanism is less favoured."))),
 PART("(c)", P(A("(anhydrous) CH" + sub(3) + "COC" + L + ", room temperature"))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)", P(A("acidified K" + sub(2) + "Cr" + sub(2) + "O" + sub(7) + "(aq), heat with distillation"))),
 PART("(b)(i)",
      *BUL("One " + u("sp hybrid orbital") + " on the C atom " + u("overlaps head-on") + " with the " + u("1s orbital") + " of the H atom to form a " + u("σ C–H bond") + ".",
           "One " + u("sp hybrid orbital") + " on the C atom " + u("overlaps head-on") + " with one " + u("sp hybrid orbital") + " of the N atom to form " + u("one C–N σ bond") + ".",
           u("Two 2p orbitals") + " on the C atom " + u("overlap side-on") + " with the " + u("two 2p orbitals") + " of the N atom to form " + u("two C–N π bonds") + "."),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
 PART("(b)(ii)",
      P(A("In order of increasing reactivity: benzaldehyde, benzene, methylbenzene")),
      P(A(u("Electron-donating") + " –CH" + sub(3) + " group " + u("increases the electron density") + " and activates the aromatic ring, causing it to be more reactive than benzene itself. "
          "Hence methylbenzene is " + u("more susceptible to electrophilic attack") + " than benzene.")),
      P(A(u("Electron-withdrawing") + " –CHO group " + u("decreases the electron density") + " and deactivates the aromatic ring, causing it to be less reactive than benzene itself. "
          "Hence benzaldehyde is " + u("less susceptible to electrophilic attack") + " than benzene.")),
      NOTE("Explanation: 1 mark.")),
 PART("(c)(i)", P(A("condensation")), NOTE("(or nucleophilic addition-elimination)")),
 PART("(c)(ii)", IMG(5, "cii")),
 PART("(d)", IMG(5, "d")),
]
# ------------------------------------------------------------------ Q6
W[6] = [
 PART("(a)(i)", IMG(6, "ai")),
 PART("(a)(ii)", IMG(6, "aii")),
 PART("(a)(iii)",
      P("Similarities:"),
      P(A("Each enantiomer will " + u("rotate the plane of plane-polarised light") + " by the " + u("same angle") + ".")),
      P("Difference:"),
      P(A("Each enantiomer will rotate the plane of plane-polarised light in the " + u("opposite direction") + ".")),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
 PART("(b)(i)", P(A("HOOCCH" + sub(2) + "COOH + 2PC" + L + sub(5) + " → C" + L + "OCCH" + sub(2) + "COC" + L + " + 2POC" + L + sub(3) + " + 2H" + CL))),
 PART("(b)(ii)", IMG(6, "bii"), NOTE("1 mark for the correct structure; 1 mark for the skeletal structure.")),
 PART("(b)(iii)",
      *BUL(u("Propanedioyl chloride undergoes hydrolysis more readily") + " and a rapid reaction occurs when cold water is added to propanedioyl chloride.",
           "1,3-dichloropropane " + u("undergoes hydrolysis slowly") + ".") + 
      BUL("The C atom in COC" + L + " of propanedioyl chloride is " + u("attached to two highly electronegative O and C" + L) + ". It is " + u("more electron deficient") +
          " and more susceptible to nucleophilic attack by " + H2O + ".",
          "The C atom in C–C" + L + " of 1,3-dichloropropane is " + u("attached to only one electronegative C" + L) + ". It is " + u("less electron deficient") +
          " than the carbon atom in COC" + L + "."),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
]
# ------------------------------------------------------------------ Q7
W[7] = [
 PART("(a)", IMG(7, "a"), NOTE("1 mark for the graph."),
      P(A("The graph is a decreasing curve with constant half-life.")),
      P(A("Using half-life, " + i("k") + " can be determined using " + i("k") + " = " + frac("ln 2", i("t") + sub("½"))))),
 PART("(a)(i)",
      NOTE("(Students are not expected to use the Arrhenius equation to explain.)"),
      P(A("With an increase in temperature, the " + u("kinetic energy of the particles increases") + " and there will be more particles with " +
          u("energy more than or equal to the " + i("E") + sub("a") + " of the reaction") + ". The " + u("frequency of effective collisions increases") + ".")),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
 PART("(a)(ii)",
      TBL(["1/<i>T</i> / K" + sup(M + "1"), "ln <i>k</i>"], ["0.00319", M + "12.6"], ["0.00310", M + "11.8"], ["0.00300", M + "11.0"], ["0.00292", M + "10.3"]),
      NOTE("1 mark for the calculation of ln <i>k</i> and 1/<i>T</i> (no penalty for wrong units, since the calculated <i>k</i> will be wrong)."),
      NOTE("1 mark for correct axes and a linear graph."),
      IMG(7, "aii"),
      P(A("At 25 °C, 1/<i>T</i> = 0.00336, ln <i>k</i> = " + M + "14, <i>k</i> = 8.32 × 10" + sup(M + "7") + " s" + sup(M + "1"))),
      NOTE("Allow error carried forward.")),
 PART("(a)(iii)",
      P(A("From the graph, the line passes through (0.00290, " + M + "10.2) and (0.00348, " + M + "15.0).")),
      P(A("gradient = " + frac("(" + M + "15.0) " + M + " (" + M + "10.2)", "0.00348 " + M + " 0.00290") + " = " + M + frac("4.8", "0.00058") + " = " + M + frac(i("E") + sub("a"), i("R")) + " = " + M + "8.28 × 10" + sup(3) + " K")),
      P(A(i("E") + sub("a") + " = 8.28 × 10" + sup(3) + " × 8.31 = 6.88 × 10" + sup(4) + " J mol" + sup(M + "1")))),
 PART("(b)",
      P(A("ln" + "(" + frac("1", "0.7") + ") = 3.33 × 10" + sup(M + "6") + "(" + i("t") + ")")),
      P(A(i("t") + " = 1.071 × 10" + sup(5) + " s = 1.24 days"))),
 PART("(c)(i)",
      P(A(KA + " = " + frac("[B][" + H2O.replace(H2O, "H" + sub(3) + "O") + sup("+") + "]", "[BH" + sup("+") + "]"))),
      P(A("1.26 × 10" + sup(M + "3") + " = " + frac("[B] × 10" + sup(M + "3.4"), "[BH" + sup("+") + "]"))),
      P(A(frac("[B]", "[BH" + sup("+") + "]") + " = 3.165"))),
 PART("(c)(ii)",
      P(A("When pH is increased, [H" + sub(3) + "O" + sup("+") + "] decreases. By Le Chatelier's principle, the " + u("position of equilibrium will shift to the right to increase the [H" +
          sub(3) + "O" + sup("+") + "]") + ". [B]:[BH" + sup("+") + "] increases. " + u("Colour of the juice fades") + "."))),
 PART("(c)(iii)",
      P(A("A buffer is a solution that is able to " + b("resist large changes") + " in pH when " + b("small") + " amounts of acid or base are added."))),
 PART("(c)(iv)",
      P(A("When small amounts of OH" + sup(M) + " are added,")),
      P(A(u("OH" + sup(M) + " + HA → A" + sup(M) + " + " + H2O))),
      P(A(u("Most") + " of the added OH" + sup(M) + " is removed by reacting with the " + u("large reservoir of HA") + " (acid), keeping the pH of the solution fairly constant."))),
 PART("(c)(v)",
      P(A("pH = p" + KA + " + lg " + frac("[A" + sup(M) + "]", "[HA]"))),
      P(A("3.4 = " + M + " lg (7.4 × 10" + sup(M + "4") + ") + lg " + frac("[A" + sup(M) + "]", "[HA]"))),
      P(A(frac("[A" + sup(M) + "]", "[HA]") + " = 1.858")),
      P(A("Initial amount of HA = 500 × 0.02 / 1000 = 0.01 mol")),
      P(A("Let the amount of NaOH be <i>x</i> mol.")),
      P(A("OH" + sup(M) + " + HA → A" + sup(M) + " + " + H2O)),
      TBL(["", "OH" + sup(M), "HA", "A" + sup(M)], ["Initial amount / mol", "<i>x</i>", "0.01", "0"], ["Final amount / mol", "0", "0.01 " + M + " <i>x</i>", "<i>x</i>"]),
      P(A(frac("<i>x</i> / <i>V</i>", "(0.01 " + M + " <i>x</i>) / <i>V</i>") + " = 1.858")),
      P(A("<i>x</i> = 0.01858 " + M + " 1.858<i>x</i>")),
      P(A("<i>x</i> = 0.00650 mol"))),
 PART("(d)(i)", P(A("3"))),
 PART("(d)(ii)",
      P(A("The formation is accompanied by an " + u("increase in entropy") + u(" as there is an increase in number of particles in the product (from 3 mol of reactants to 7 mol of products)") +
          ". There is an " + u("increase in disorder") + " of the system as there are " + u("more ways of arranging these particles") + ".")),
      NOTE("3 points: 2 marks; 2 points: 1 mark.")),
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

