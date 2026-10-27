"""Hand transcription of the NYJC solutions to A Level (SEAB) 9729/03 Oct/Nov 2024
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source is a PDF only; typed from the rendered pages.

Run from the repo root:
    python3 ingest/build_alevel_p3_answers.py <outdir> <questions_dir>

Rulings (user, 2026-10-27; see project doc claude/alevel-2024-h2-p3-answer-rulings-2026-10-27.md):
  4(d)(ii) and 1(e): scheme kept ("answer to the qn"); 3(e)(ii): complex definition ADDED;
  typo/presentation fixes applied (1(b) expt 3, 4(d)(ii) grammar, 5(c) g dm-3, 2(e) H2/Ni);
  red marker notes and green examiner comments dropped (incl. the green 'mechanism for M');
  Q2(b) Boltzmann image has no key; Q4(g)(i) types only 'Electrophilic substitution' (equation lives in the image).
Figures are bare img.ws-fig[data-asset] (user snips: SEAB_H2_P3_Q<n>_ans-<slot>_2024.png).
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX = "SEAB_H2_P3"
M = "−"
NB = " "
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
L = '<i class="el">l</i>'
CL = "C" + L
TIMES = "×"
STD = "⦵"
def frac(n, d): return '<span class="frac"><span class="fnum">%s</span><span class="fden">%s</span></span>' % (n, d)
def A(t): return '<span class="ans">%s</span>' % t
def P(*parts): return "<p>%s</p>" % "".join(parts)
def UL(*items): return '<ul class="stmts">%s</ul>' % "".join("<li>%s</li>" % x for x in items)
def TBL(*rows): return '<table class="cmp">%s</table>' % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
def _tidy(h):
    h = re.sub(r"<li>\s*</li>", "", h)
    h = re.sub(r'<ul class="stmts">\s*</ul>', "", h)
    h = re.sub(r"<p>\s*</p>", "", h)
    return "\n".join(l for l in h.split("\n") if l.strip())
def PART(label, *blocks): return ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                                  % (label, _tidy("\n".join(blocks))))
ARROW, EQ = " → ", " ⇌ "
MDM = "mol dm" + sup(M + "3")
MOL1 = "kJ mol" + sup(M + "1")
def ion(sym, ch): return sym + sup(ch)
def E(x): return i("E") + sup(STD) + x
def D(x, s=""): return "Δ" + i(x) + (sup(STD) if s == "" else s)
Hp = "H" + sup("+")
H2O, CO2 = "H" + sub(2) + "O", "CO" + sub(2)
def e(x, n): return "%s %s 10%s" % (x, TIMES, sup(M + str(n) if n >= 0 else "+" + str(-n)))

ASSETS = []
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s_Q%d_ans-%s_2024.png" alt=""></p>' % (PFX, qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)", P(A("Volatility decreases down the group from " + "Cl" + sub(2) + " to I" + sub(2) + ".")),
      P(A("The halogens are simple molecules with instantaneous dipole–induced dipole (id–id) interactions between molecules. "
          "Down the group the number of electrons, and so the size of the electron cloud, increases and it is more easily polarised, so the id–id interactions are stronger. "
          "More energy is required to overcome them, so the boiling point increases and volatility decreases."))),
 PART("(b)", TBL(
      ["experiment", "colour of final solution", "equation / explanation"],
      ["1", A("orange (Br" + sub(2) + "(aq))"),
       A("2Br" + sup(M) + " + Cl" + sub(2) + ARROW + "Br" + sub(2) + " + 2Cl" + sup(M)) + "<br>" +
       A(E("(Cl" + sub(2) + "/Cl" + sup(M) + ") = +1.36 V; " ) + E("(Br" + sub(2) + "/Br" + sup(M) + ") = +1.07 V") + "<br>" +
         E("cell") + " = +1.36 " + M + " 1.07 = +0.29 V &gt; 0, reaction occurs")],
      ["2", A("brown (I" + sub(2) + "(aq))"),
       A("2I" + sup(M) + " + Cl" + sub(2) + ARROW + "I" + sub(2) + " + 2Cl" + sup(M)) + "<br>" +
       A(E("(Cl" + sub(2) + "/Cl" + sup(M) + ") = +1.36 V; " ) + E("(I" + sub(2) + "/I" + sup(M) + ") = +0.54 V") + "<br>" +
         E("cell") + " = +1.36 " + M + " 0.54 = +0.82 V &gt; 0, reaction occurs")],
      ["3", A("brown (I" + sub(2) + "(aq))"),
       A("no reaction") + "<br>" +
       A(E("(I" + sub(2) + "/I" + sup(M) + ") = +0.54 V; " ) + E("(Br" + sub(2) + "/Br" + sup(M) + ") = +1.07 V") + "<br>" +
         E("cell") + " = +0.54 " + M + " 1.07 = " + M + "0.53 V &lt; 0, reaction is not feasible")])),
 PART("(c)", P(A(b("A") + " has 8 π electrons, which does not follow the 4" + i("n") + " + 2 rule: it is non-aromatic.")),
      P(A(b("B") + " has 10 π electrons, which follows the 4" + i("n") + " + 2 rule (" + i("n") + " = 2): it is aromatic."))),
 PART("(d)", UL(
      A("All the carbon atoms and the nitrogen atom in the ring are sp" + sup("2") + " hybridised."),
      A("The σ bonds are formed by head-on overlap of sp" + sup("2") + " orbitals."),
      A("The π bonds are formed by side-on overlap of the unhybridised p orbitals."),
      A("The lone pair on N is delocalised into the ring, giving a delocalised π system of 6 π electrons."))),
 PART("(e)", UL(
      A("Pyrrolidine is the most basic: the lone pair on N is localised and available to accept H" + sup("+") + ", and the two electron-donating alkyl groups increase the electron density on N."),
      A("In pyrrole the lone pair on N is delocalised into the aromatic ring, so it is less available to accept H" + sup("+") + "; it is less basic."),
      A("In the γ-lactam the lone pair on N is delocalised into the C=O group; the more electronegative O withdraws electron density more strongly than the ring does in pyrrole, so it is the least basic."))),
 PART("(f)(i)", P(A("secondary amide, secondary alcohol, carboxylic acid, aryl fluoride (halogenoarene), benzene ring (arene)"))),
 PART("(f)(ii)", P(A("Nucleophilic addition"))),
 PART("(f)(iii)", IMG(1, "fiii")),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)", P(A("CO + NO " + ARROW + " ½N" + sub(2) + " + CO" + sub(2)))),
 PART("(a)(ii)", P(A("Heterogeneous catalysis: the catalyst is a solid while the reactants are gases (different phases)."))),
 PART("(b)", UL(
      A("The catalyst provides an alternative reaction pathway with a lower activation energy, " + i("E") + sub("a") + "."),
      A("A greater proportion of reactant particles have energy ≥ " + i("E") + sub("a") + ", so the frequency of effective collisions increases."),
      A("The rate constant, " + i("k") + " = " + i("A") + "e" + sup(M + i("E") + sub("a") + "/" + i("RT")) + ", increases, so the rate of reaction increases.")),
      IMG(2, "b")),
 PART("(c)", P(A("At low [S] the reaction is first order with respect to [S]: the rate is proportional to [S].")),
      P(A("At high [S] the reaction is zero order with respect to [S]: all the active sites on the enzyme are saturated, so the rate is at its maximum and independent of [S].")),
      IMG(2, "c")),
 PART("(d)(i)", P(A("rate of formation of P = " + i("k") + sub("r") + "[ES]; rate = " + i("k") + sub("2") + "[ES]"))),
 PART("(d)(ii)", P(A("At steady state: rate of formation of ES = rate of removal of ES")),
      P(A(i("k") + sub("f") + "[E][S] = (" + i("k") + sub("r") + " + " + i("k") + sub("2") + ")[ES]")),
      P(A("[ES] = " + frac(i("k") + sub("f") + "[E][S]", i("k") + sub("r") + " + " + i("k") + sub("2"))))),
 PART("(d)(iii)", P(A(i("K") + sub("m") + " = " + frac(i("k") + sub("r") + " + " + i("k") + sub("2"), i("k") + sub("f")) + " = " + frac("[E][S]", "[ES]")))),
 PART("(e)", TBL(
      ["test", "type of reaction / observation", "deduction"],
      ["1", A("reduction (hydrogenation)"), A("F has 3 C=C and 1 carbonyl (C=O) group")],
      ["2", A("electrophilic addition with Br" + sub(2)), A("F has 3 C=C")],
      ["3", A("condensation with 2,4-DNPH"), A("F has a carbonyl group (aldehyde or ketone)")],
      ["4", A("no reaction with Fehling’s reagent"), A("the carbonyl group is a ketone, not an aldehyde")],
      ["5", A("oxidative cleavage with KMnO" + sub(4)), A("F has 3 C=C; J, K and L effervesce with Na" + sub(2) + "CO" + sub(3) + ", so they are carboxylic acids; K and L give an orange precipitate with 2,4-DNPH, so they contain a ketone")]),
      IMG(2, "e")),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)", P(A(D("H") + " = " + "944 + 3(436) " + M + " 6(390) = " + M + "88.0 " + MOL1))),
 PART("(a)(ii)", P(A(D("G") + " = " + D("H") + " " + M + " " + i("T") + D("S") + " = " + M + "88 " + M + " (273 + 450)(" + M + "0.199) = +55.9 " + MOL1))),
 PART("(a)(iii)", P(A(D("S") + " is negative, so " + M + i("T") + D("S") + " becomes more positive at higher temperature. " + D("G") + " becomes more positive and the reaction is less spontaneous."))),
 PART("(b)(i)", P(A("NH" + sub(3) + "/NH" + sub(4) + sup("+") + " and H" + sub(2) + "S/HS" + sup(M)))),
 PART("(b)(ii)", P(A(i("K") + sub("eq") + " = " + frac(i("K") + sub("a") + "(H" + sub(2) + "S)", i("K") + sub("a") + "(NH" + sub(4) + sup("+") + ")") + " = " +
                    frac("10" + sup(M + "6.98"), "10" + sup(M + "9.25")) + " = 186"))),
 PART("(c)", IMG(3, "c"),
      P(A("There are 4 electron pairs around N, with 2 bond pairs and 2 lone pairs. Lone pair–lone pair repulsion &gt; lone pair–bond pair repulsion &gt; bond pair–bond pair repulsion, "
          "so the bond angle is reduced below 109.5° to about 105°; the shape is bent (V-shaped)."))),
 PART("(d)(i)", P(A("Nucleophilic addition"))),
 PART("(d)(ii)", IMG(3, "dii")),
 PART("(e)(i)", IMG(3, "ei")),
 PART("(e)(ii)", UL(
      A("A ligand is a species with a lone pair of electrons which forms a dative bond with the central metal atom or ion."),
      A("A complex is a species which consists of a central metal atom or ion surrounded by ligands which are bonded to it by dative bonds."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)", UL(
      A("Nuclear charge increases down the group."),
      A("Shielding effect increases significantly as the number of inner shells increases."),
      A("The outermost electron is further from the nucleus, so the attraction is weaker and less energy is needed to remove it; first ionisation energy decreases."))),
 PART("(b)(i)", P(A("1s" + sup("2") + "2s" + sup("2") + "2p" + sup("6") + "3s" + sup("1")))),
 PART("(b)(ii)", TBL(
      ["ionisation", "ionisation energy / " + "kJ mol" + sup(M + "1")],
      ["2nd", A("4560 or 10" + sup("3.65") + " = 4467")],
      ["3rd", A("6940 or 10" + sup("3.85") + " = 7079")],
      ["4th", A("9540 or 10" + sup("4") + " = 10000")],
      ["8th", A("10" + sup("4.4") + " = 25119")],
      ["10th", A("10" + sup("5.15") + " = 141254")])),
 PART("(b)(iii)", UL(
      A("In general, ionisation energy increases as successive electrons are removed from an increasingly positive ion: the same nuclear charge attracts fewer electrons, which are held more strongly."),
      A("There is a large jump between the 1st and 2nd ionisation energies, as the 2nd electron is removed from the inner (2nd) quantum shell, which is closer to the nucleus and less shielded."),
      A("There is a large jump between the 9th and 10th ionisation energies, as the 10th electron is removed from the innermost (1st) quantum shell, which is closest to the nucleus and experiences the least shielding."))),
 PART("(c)", UL(
      A("NaC" + L + " dissolves in water without hydrolysis: NaC" + L + "(s) + aq " + ARROW + " Na" + sup("+") + "(aq) + C" + L + sup(M) + "(aq); pH 7."),
      A("AlC" + L + sub(3) + " hydrolyses: AlC" + L + sub(3) + "(s) + 6H" + sub(2) + "O(" + L + ")" + ARROW + "[Al(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+") + "(aq) + 3C" + L + sup(M) + "(aq); "
        "[Al(H" + sub(2) + "O)" + sub(6) + "]" + sup("3+") + EQ + "[Al(H" + sub(2) + "O)" + sub(5) + "(OH)]" + sup("2+") + " + H" + sup("+") + "; pH 3."),
      A("SiC" + L + sub(4) + " hydrolyses: SiC" + L + sub(4) + "(" + L + ") + 2H" + sub(2) + "O(" + L + ")" + ARROW + "SiO" + sub(2) + "(s) + 4HC" + L + "(aq); pH 2."))),
 PART("(d)(i)", P(A("An electron-pair acceptor."))),
 # RULED: scheme kept; grammar fixed ("are electron deficient and are able to act as")
 PART("(d)(ii)", P(A("The Lewis acidity decreases in the order BCl" + sub(3) + " &gt; AlC" + L + sub(3) + " &gt; GaC" + L + sub(3) + ".")),
      P(A("BC" + L + sub(3) + ", AlC" + L + sub(3) + " and GaC" + L + sub(3) + " are electron deficient and are able to act as Lewis acids. "
          "The atomic radius increases from B to Al to Ga, so the overlap of the orbital on the central atom with the lone pair on the incoming species becomes less effective down the group, "
          "and the Lewis acidity decreases."))),
 PART("(e)", IMG(4, "e"),
      P(A("Two Cl atoms each donate a lone pair to a Ga atom, forming two Cl→Ga dative bonds; there are also six Ga–Cl covalent bonds."))),
 PART("(f)", UL(
      A("n(GaC" + L + sub(3) + ") initially = " + frac("0.881", "69.7 + 3(35.5)") + " = 0.00500 mol"),
      A("n(GaC" + L + sub(3) + ") reacted = 0.300 " + TIMES + " 0.00500 = 0.00150 mol"),
      A("Equilibrium n(GaC" + L + sub(3) + ") = 0.00350 mol; equilibrium n(Ga" + sub(2) + "C" + L + sub(6) + ") = 7.50 " + TIMES + " 10" + sup(M + "4") + " mol"),
      A("Total n = 0.00425 mol; " + i("p") + "(GaC" + L + sub(3) + ") = " + frac("0.00350", "0.00425") + " " + TIMES + " 250 = 205.88 kPa; " + i("p") + "(Ga" + sub(2) + "C" + L + sub(6) + ") = " + frac("7.50 " + TIMES + " 10" + sup(M + "4"), "0.00425") + " " + TIMES + " 250 = 44.12 kPa"),
      A(i("K") + sub("p") + " = " + frac("44.12", "205.88" + sup("2")) + " = 1.04 " + TIMES + " 10" + sup(M + "3") + " kPa" + sup(M + "1")))),
 PART("(g)(i)", P(A("Electrophilic substitution")), IMG(4, "gi")),
 PART("(g)(ii)", IMG(4, "gii")),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A("The 3d and 4s subshells are close in energy, so electrons can be removed from both."))),
 PART("(a)(ii)", P(A("Across the period the nuclear charge increases, but the shielding by the added 3d electrons also increases, so the effective nuclear charge is approximately constant."))),
 PART("(a)(iii)", P(A("Co has both 3d and 4s electrons delocalised, giving stronger metallic bonding, whereas Ca has only two valence electrons per atom delocalised.")) ),
 PART("(b)(i)", P(A("Ligand exchange"))),
 PART("(b)(ii)", P(A("CO binds strongly and irreversibly to Fe" + sup("2+") + " in haemoglobin, so haemoglobin is not available to carry O" + sub(2) + "."))),
 PART("(c)", UL(
      A("n(S" + sub(2) + "O" + sub(3) + sup("2" + M) + ") = " + frac("23.80", "1000") + " " + TIMES + " 0.0450 = 1.071 " + TIMES + " 10" + sup(M + "3") + " mol"),
      A("n(I" + sub(2) + ") = 5.355 " + TIMES + " 10" + sup(M + "4") + " mol = n(MnO" + sub(2) + ")"),
      A("n(O" + sub(2) + ") = 2.677 " + TIMES + " 10" + sup(M + "4") + " mol"),
      A("concentration of O" + sub(2) + " = " + frac("2.677 " + TIMES + " 10" + sup(M + "4") + " " + TIMES + " 32.0 " + TIMES + " 1000", "250") + " = 3.43 " + TIMES + " 10" + sup(M + "2") + " g" + NB + "dm" + sup(M + "3")))),
 PART("(d)(i)", P(A("The standard electrode potential is the potential difference between the half-cell and the standard hydrogen electrode (0.00 V) under standard conditions."))),
 PART("(d)(ii)", IMG(5, "dii")),
 PART("(d)(iii)", UL(
      A(D("G") + " = " + M + i("n") + i("F") + E("cell")),
      A(M + "405.3 " + TIMES + " 10" + sup("3") + " = " + M + "(3)(96500)" + E("cell") + "; " + E("cell") + " = +1.4 V"),
      A("+1.4 = +1.72 " + M + " " + E(""), ) + A("; " + E("") + " = +0.32 V"))),
 PART("(e)(i)", IMG(5, "ei"),
      P(A(b("N") + " is 3-phenylpropan-1-ol; " + b("O") + " is 1-chloro-3-phenylpropane."))),
 PART("(e)(ii)", UL(
      A("Step 1: LiAl" + "H" + sub(4) + " in dry ether"),
      A("Step 2: PC" + L + sub(5) + " (or SOC" + L + sub(2) + ") at room temperature"),
      A("Step 3: anhydrous FeC" + L + sub(3) + " (or AlC" + L + sub(3) + ") at room temperature"))),
]

RULED_FIXES = []
out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    assert not re.search(r"\[\d", h), (qn, re.findall(r".{20}\[\d.{10}", h))
    out[str(qn)] = h

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
