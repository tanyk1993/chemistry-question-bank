"""Hand transcription of the RVHS 2026 H2 Prelim Paper 2 (9476/02) suggested answers (7-page PDF + docx twin; the docx keeps
the equations as MathType objects and the figures as ChemDraw pictures, so the text is typed and the five figures are
snipped from the Word PDF) -> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Underlined keywords follow the docx runs. There are no mark breakdowns and no red marking notes.

Run from the repo root:
    python3 ingest/build_rvhs26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_rvhs26_p2.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u>
on the school's underlined keywords; figures are bare img.ws-fig[data-asset] (RVHS_H2_P2_Q<n>_ans-<slot>_2026.png);
tables are table.cmp. Editorial defaults (standing rulings): typos and grammar fixed, short forms spelled in full; see FIXES.

FIXES made to the school's answers (listed to the user):
  3(c)(i)  "250 atm" -> "200 atm" (the question says 200 atm);
  3(d)(iii) stray asterisk after "effective collision" dropped;
  2(d)(iii) "poses" -> "pose"; 5(c)(ii) "Water form ionic dipole interaction" -> "Water forms ion-dipole interactions";
  1(b) "sideway" -> "sideways"; "IMF" -> "intermolecular forces"; "id-id" -> "instantaneous dipole-induced dipole";
  4(c)(ii) a closing sentence is ADDED (pV constant, hence ideal): the school gives the two products but no conclusion;
  4(a)(i) the school's bracketed note is kept.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "RVHS_H2_P2", 2026
M = "\u2212"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
CL = "C" + L
DEL = "\u0394"
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
def BUL(*items): return [P(A(x)) for x in items]
def eq(s): return P(A(s))
ARROW = " \u2192 "
RARR = "\u21cc"
EM = "&emsp;"
H2O = "H" + sub(2) + "O"
MDM = "mol dm" + sup(M + "3")
STD = sup('<span class="pl-sym">\u29b5</span>')
CO2 = "CO" + sub(2)
HCO3 = "HCO" + sub(3) + sup(M)
CO3 = "CO" + sub(3) + sup("2" + M)
K = i("K")
def NUC(a, z, sym):   # .stk is only styled inside .stem, so inline styles here
    return ('<span style="display:inline-block;vertical-align:middle;position:relative;top:-.06em;line-height:1;font-size:.72em;'
            'text-align:right"><span style="display:block">%s</span><span style="display:block">%s</span></span>%s' % (a, z, sym))
def conc(s): return "[" + s + "]"

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
RULED_FIXES = []

# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A(u("White ppt") + " of AgCl " + u("dissolves") + " in aqueous ammonia to give a " + u("colourless solution") + ".")),
      eq("AgCl(s) + 2NH" + sub(3) + "(aq)" + ARROW + "[Ag(NH" + sub(3) + ")" + sub(2) + "]" + sup("+") + "(aq) + " + CL + sup(M) + "(aq)")),
 PART("(a)(ii)",
      P(A("The thermal stability of hydrogen halides " + u("decreases down the Group") + ". As the " + u("size of the halogen atoms increases") +
          " from " + CL + " to I, their " + u("valence orbitals become more diffuse") + ". This results in " + u("less effective overlap of the orbitals") +
          " between the small H atom and the larger halogen atom and " + u("less energy is required to break the weaker H" + M + "X bond") + "."))),
 PART("(b)",
      P(A("In decreasing relative rate of hydrolysis: " + u("R > P > Q"))),
      P(A(b("R") + " is the most reactive as the " + u("acyl carbon atom is highly electron deficient as it is bonded to two electronegative atoms") +
          ", O and " + CL + ", and hence is most susceptible to nucleophilic attack.")),
      P(A(b("P") + " is less reactive than " + b("R") + " because the " + u("electron deficient carbon is bonded to only one electronegative (" + CL + ") atom") + ".")),
      P(A(b("Q") + " does not undergo hydrolysis. Due to sideways overlap of p-orbital of " + CL + " with the π electron cloud of benzene ring, the " +
          u("lone pair of electrons on " + CL + " atom delocalises into the benzene ring") + ". This results in " +
          u("C" + M + CL + " bond having partial double bond character") + ", which makes the bond stronger."))),
 PART("(c)",
      P(A("Since the " + u(M + "OH group") + " is highly activating, it " + u("increases electron density") + " on the benzene ring as well as " +
          u("stabilises the arenium ion") + ", making the ring " + u("more susceptible to electrophilic attack") + "."))),
 PART("(d)", IMG(1, "d")),
 PART("(e)(i)", P(A("Free radical substitution")), P(A("Limited Br" + sub(2) + ", UV light at room temperature"))),
 PART("(e)(ii)", IMG(1, "eii")),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)", P(A("Circle N")), P(A("Tetrahedral"))),
 PART("(b)",
      P(A(u("Energy released") + " by " + u("ion-dipole interactions between (protonated dextromethorphan and Br" + sup(M) + ") ions and (polar) water molecules ") +
          "is " + u("sufficient") + " to " + u("compensate for the energy required") + " to overcome the " +
          u("electrostatic attraction between oppositely-charged ions/ ionic bonds and hydrogen bonds between water molecules") + "."))),
 PART("(c)(i)", IMG(2, "ci")),
 PART("(c)(ii)", P(A("PC" + L + sub(5)))),
 PART("(d)(i)",
      P(A("Anion " + b("X") + " is resonance-stabilised as the " + u("negative charge on C can delocalise into " + M + "CN and C=O") + "."))),
 PART("(d)(ii)", IMG(2, "dii")),
 PART("(d)(iii)",
      P(A(u("Carbonyl C atom in cyclohexanone is less electron-deficient") + " as it is attached to " + u("2 electron-donating alkyl groups") +
          " while the carbonyl C atom in hexanal is attached to " + u("1 electron-donating alkyl group") + ".")),
      P(A("The " + u("2 alkyl groups bonded to carbonyl C atom in cyclohexanone") + " pose " + u("greater steric hindrance") +
          " to the incoming nucleophile compared to 1 alkyl group bonded to carbonyl C atom in hexanal.")),
      P(A("Cyclohexanone is less susceptible to attack by nucleophiles and rate of reaction is slower."))),
 PART("(d)(iv)",
      P(A(u(M + "CN is electron-withdrawing/ N atom in " + M + "CN is electronegative.") + " " + u("Negative charge on " + M + "COO" + sup(M) + " is dispersed by") +
          " the " + M + "CN in cyanoacetate anion, which makes it a " + u("more stable anion") + " than CH" + sub(3) + "CH" + sub(2) + "CH" + sub(2) + "COO" + sup(M) + "."))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)",
      P(A("Let " + i("x") + " be the initial amount of N" + sub(2) + ".")),
      TBL(["", "3H" + sub(2) + "(g)", "+", "N" + sub(2) + "(g)", RARR, "2NH" + sub(3) + "(g)"],
          ["Initial amount / mol", "3" + i("x"), "", i("x"), "", "0"],
          ["Change in amount / mol", M + "0.9" + i("x"), "", M + "0.3" + i("x"), "", "+0.6" + i("x")],
          ["Equilibrium amount / mol", "2.1" + i("x"), "", "0.7" + i("x"), "", "0.6" + i("x")]),
      P(A(frac("0.6" + i("x"), "5") + " = 0.320")),
      P(A(i("x") + " = 2.667 mol")),
      P(A("Equilibrium concentration of H" + sub(2) + " = " + frac("2.1 × 2.667", "5") + " = 1.12 " + MDM)),
      P(A("Equilibrium concentration of N" + sub(2) + " = " + frac("0.7 × 2.667", "5") + " = 0.373 " + MDM))),
 PART("(a)(ii)",
      P(A(K + sub("c") + " = " + frac("0.320" + sup("2"), "(1.12)" + sup("3") + "(0.373)") + " = 0.195 mol" + sup(M + "2") + " dm" + sup("6")))),
 PART("(b)(i)",
      P(A("Since there is " + u("no change in the concentration/ partial pressure of N" + sub(2) + ", H" + sub(2) + " and NH" + sub(3) +
          ", the position of equilibrium remains unchanged") + ".")),
      P(A("Therefore, the " + u("composition") + " of the reaction mixture " + u("remains unchanged") + "."))),
 PART("(b)(ii)", P(A(K + sub("c") + " " + u("remains unchanged") + "."))),
 PART("(c)(i)",
      P(A("The forward exothermic reaction is favoured by " + u("low temperature") + " to absorb some heat. However, at low temperature, the " +
          u("reaction would be slow") + ". Hence, an optimal moderately high temperature of 450 °C is used so that a " +
          u("reasonable yield can be obtained at a fairly high rate") + ".")),
      P(A("A " + u("high pressure would shift the position of equilibrium to the right") + " increasing the yield of NH" + sub(3) + ". It also " +
          u("increases the rate") + " at which equilibrium is established. However, the " +
          u("cost of equipment to produce and maintain high pressure would be greater/costly to maintain high pressure") +
          ". Hence, a relatively high pressure of 200 atm is used as a " + u("compromise between yield and cost/ optimal pressure") + "."))),
 PART("(c)(ii)", P(A("A large amount of energy is required to " + u("break the (very) strong N≡N bond") + "."))),
 PART("(d)(i)", P(A(sub("26") + "Fe: 1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(6) + " 3s" + sup(2) + " 3p" + sup(6) + " 3d" + sup(6) + " 4s" + sup(2)))),
 PART("(d)(ii)",
      P(A("Iron has " + u("energetically accessible/low-lying partially filled 3d subshells/ 3d and 4s electrons") + " which allow the " +
          u("N" + sub(2) + " and H" + sub(2) + " molecules to adsorb onto the surface of the catalyst/ form weak temporary bonds with the surface of the catalyst") + "."))),
 PART("(d)(iii)",
      IMG(3, "diii"),
      P(A("A catalyst provides an " + u("alternative reaction pathway with a lower activation energy") + ".")),
      P(A("As a result, " + u("more reactant particles possess the energy required for an effective collision") + " and the " +
          u("frequency of effective collisions increases") + ".")),
      P(A("The rate of reaction is thus increased and " + u("the rate constant increases") + "."))),
 PART("(e)",
      P(A(u("NH" + sub(3)) + " is a stronger ligand than N" + sub(2) + ".")),
      P(A("In NH" + sub(3) + ", the N atom is " + u("sp" + sup(3) + " hybridised") + ", whereas in N" + sub(2) + ", the N atom is " + u("sp hybridised") + ".")),
      P(A("The lone pair of electrons in N" + sub(2) + " is in a " + u("sp hybrid orbital") + " which has " +
          u("greater s-character/ smaller in size/ closer to the nucleus") + " (50%) compared to the sp" + sup(3) + " hybrid orbital (25%) in NH" + sub(3) + ".")),
      P(A("Consequently, the " + u("lone pair of electrons in N" + sub(2) + " experience greater nuclear attraction") +
          ", making it less available to form a coordinate/ dative bond."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)",
      P(A(NUC(222, 86, "Rn"))),
      P(A("(Mass must balance: 226 " + M + " 4 = 222; atomic number must balance: 88 " + M + " 2 = 86. Element 86 corresponds to Rn on the periodic table)."))),
 PART("(a)(ii)",
      P(A("The beam will deflect towards the " + u("negatively charged plate") + " because α-particles are helium nuclei (" + NUC(4, 2, "He") + sup("2+") +
          ") which carry a positive charge."))),
 PART("(b)",
      P(A("The successive half-lives (" + i("t") + sub("1/2") + ") can be calculated directly from Table 4.1:")),
      P(A("Time to drop from 5.12 × 10" + sup("20") + " to 2.56 × 10" + sup("20") + " atoms (100% to 50%): 1600 " + M + " 0 = 1600 years")),
      P(A("Time to drop from 2.56 × 10" + sup("20") + " to 1.28 × 10" + sup("20") + " atoms (50% to 25%): 3200 " + M + " 1600 = 1600 years")),
      P(A("Since the " + u("half-life is constant at 1600 years") + ", the order of reaction is " + u("first-order") + "."))),
 PART("(c)(i)",
      P(A("Helium atoms occupy negligible volume compared to volume of the container.")),
      P(A("There is negligible intermolecular forces of attraction between the helium atoms."))),
 PART("(c)(ii)",
      P(A("For an ideal gas, the product of " + i("pV") + " must remain constant at a constant temperature (" + i("pV") + " = constant).")),
      P(A(b("Experiment 1:") + " " + i("pV") + " = (2.026 × 10" + sup("5") + ") × (3.274 × 10" + sup(M + "9") + ") = 6.6 × 10" + sup(M + "4") + " J")),
      P(A(b("Experiment 2:") + " " + i("pV") + " = (4.052 × 10" + sup("5") + ") × (1.623 × 10" + sup(M + "9") + ") = 6.6 × 10" + sup(M + "4") + " J")),
      P(A("Since " + i("pV") + " is the same in both experiments, helium exhibits ideal behaviour at 0 °C."))),
 PART("(d)(i)",
      P(A(i("n") + " = " + frac(i("pV"), i("RT")) + " = " + frac("(2.026 × 10" + sup(5) + ")(3.274 × 10" + sup(M + "9") + ")", "(8.31)(273)") + " = 2.924 × 10" + sup(M + "7") + " mol")),
      P(A(i("N") + sub("A") + " = " + frac("1.88 × 10" + sup(17), "2.924 × 10" + sup(M + "7")) + " = 6.43 × 10" + sup(23) + " mol" + sup(M + "1")))),
 PART("(d)(ii)",
      P(A("% error = " + frac("6.43 × 10" + sup(23) + " " + M + " 6.02 × 10" + sup(23), "6.02 × 10" + sup(23)) + " × 100% = 6.81%"))),
 PART("(d)(iii)",
      P(A("Each decaying radium atom produces four α-particles.")),
      P(A("Total number of " + sup("226") + "Ra atoms decayed = " + frac("1.88 × 10" + sup(17), "4") + " = 4.70 × 10" + sup(16) + " atoms")),
      P(A("Initial number of " + sup("226") + "Ra atoms = " + frac("192 / 1000", "226") + " × 6.02 × 10" + sup(23) + " = 5.114 × 10" + sup(20) + " atoms")),
      P(A("Percentage converted = " + frac("4.70 × 10" + sup(16), "5.114 × 10" + sup(20)) + " × 100% = 0.00919%"))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)",
      P(A(conc(CO2) + " = 0.01 × 2.10 × 10" + sup(M + "3") + " = 2.10 × 10" + sup(M + "5") + " " + MDM)),
      P(A(conc(CO3) + " = 0.04 × 2.10 × 10" + sup(M + "3") + " = 8.40 × 10" + sup(M + "5") + " " + MDM)),
      P(A(conc(HCO3) + " = 0.95 × 2.10 × 10" + sup(M + "3") + " = 2.00 × 10" + sup(M + "3") + " " + MDM))),
 PART("(a)(ii)",
      P(A("The small amount of acid added is " + u("neutralised by the large amount of " + CO3) + " in seawater. Hence, " +
          u("[H" + sup("+") + "] does not increase appreciably,") + " and the pH is kept approximately constant."))),
 PART("(b)(i)",
      P(A("When " + conc(HCO3) + " = " + conc(CO3) + ", pH = 9.5")),
      P(A(K + sub("a2") + " = 10" + sup(M + "9.5") + " = 3.16 × 10" + sup(M + "10") + " " + MDM))),
 PART("(b)(ii)",
      P(A(K + sub("a1") + " × " + K + sub("a2") + " = " + frac(conc(HCO3) + "[H" + sup("+") + "]", conc(CO2)) + " × " + frac(conc(CO3) + "[H" + sup("+") + "]", conc(HCO3)))),
      P(A("= " + frac(conc(CO3) + "[H" + sup("+") + "]" + sup("2"), conc(CO2))))),
 PART("(b)(iii)",
      P(A("[H" + sup("+") + "] = 10" + sup(M + "8.10") + " = 7.94 × 10" + sup(M + "9") + " " + MDM)),
      P(A(conc(CO2) + " = " + frac(conc(CO3) + "[H" + sup("+") + "]" + sup("2"), K + sub("a1") + " × " + K + sub("a2")))),
      P(A("= " + frac("(8.40 × 10" + sup(M + "5") + ")(10" + sup(M + "8.10") + ")" + sup("2"), "(1.42 × 10" + sup(M + "6") + ")(1.08 × 10" + sup(M + "9") + ")"))),
      P(A("= 3.46 × 10" + sup(M + "6") + " " + MDM)),
      P(N("Marking note: award the mark whichever " + K + sub("a2") + " is used, the value from (b)(i) (3.16 × 10" + sup(M + "10") + ", giving 1.18 × 10" + sup(M + "5") +
          " " + MDM + ") or the value given in the question (1.08 × 10" + sup(M + "9") + ", giving the answer above)."))),
 PART("(c)(i)",
      P(A(i("p") + sub("CO\u2082") + " = " + frac(i("n") + sub("CO\u2082"), i("n") + sub("total")) + " × " + i("p") + sub("total"))),
      P(A("= " + frac("430 × 10" + sup(M + "6"), "1") + " × 1.00")),
      P(A("= 4.30 × 10" + sup(M + "4") + " atm")),
      P(A(conc(CO2) + " = 0.0340 × 4.30 × 10" + sup(M + "4"))),
      P(A("= 1.46 × 10" + sup(M + "5") + " " + MDM))),
 PART("(c)(ii)",
      P(A("The concentration of dissolved " + CO2 + " in seawater sample, S1, will be lower.")),
      P(A("Seawater has " + u("higher salinity") + " compared to pure water. " + u("Non-polar " + CO2) + " gas is less soluble in seawater as the " + CO2 +
          " molecules are " + u("unable to form favourable interaction with seawater") + " containing " + u("highly polar dissolved ions") + ".")),
      P(A("Water forms ion-dipole interactions with dissolved ions rather than forming interaction with " + CO2 + ".")),
      P(A("Or")),
      P(A("The (surface) temperature of seawater at " + u("29.7 °C is higher") + " than that of pure water (at 25 °C). At higher temperature, " + CO2 +
          " molecules have " + u("more energy to overcome the weak instantaneous dipole-induced dipole interaction with water molecules") + ".")),
      P(A("Or")),
      P(A("The (surface) temperature of seawater at " + u("29.7 °C is higher") + " than that of pure water (at 25 °C). Equilibrium 1 is " + u("exothermic") +
          ". Higher temperature " + u("favours the backward endothermic reaction") + " to release more gas."))),
 PART("(d)(i)",
      P(A("There is a " + u("decrease in disorder") + " when " + u("mobile aqueous ions") + " are arranged to form a " +
          u("lattice structure/ held in fixed positions in solid") + " calcium carbonate."))),
 PART("(d)(ii)",
      P(A("The " + u("increase in disorder") + " is more significant when the " + u("water molecules bonded to the hydrated ions are released") +
          " as the ions get extracted for calcification."))),
 PART("(d)(iii)",
      P(A(DEL + i("G") + STD + " = " + DEL + i("H") + STD + " " + M + " " + i("T") + DEL + i("S") + STD)),
      P(A("= +12.1 " + M + " 298 (+199 × 10" + sup(M + "3") + ")")),
      P(A("= " + M + "47.2 kJ mol" + sup(M + "1")))),
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
