"""Hand transcription of the RI 2026 H2 Prelim Paper 2 (9476/02) suggested solutions
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the school's 8-page answers PDF and its docx twin (a flat 2-column grid with floating figures and OLE equations,
so the text is typed, as NYJC 2026 P2). Underlined keywords follow the docx runs; there are no marks breakdowns and no red
marking notes except the figure annotation in 4(b)(iv) (inside the picture).

Run from the repo root:
    python3 ingest/build_ri26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_ri26_p2.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u>
on the school's underlined keywords; figures are bare img.ws-fig[data-asset] (the user snips them:
RI_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp; marker notes are span.note.
Editorial defaults (RI 2026 P1 / NYJC rulings): typos and grammar fixed, short forms spelled in full; see FIXES in the notes.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "RI_H2_P2", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
AL = "A" + L
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
def BUL(*items): return [P(A(x)) for x in items]   # bullets are typed as separate answer paragraphs
def NOTE(t): return P(N(t))
def eq(s): return P(A(s))
RARR = "⇌"
ARROW = " → "
H2O, HP = "H" + sub(2) + "O", "H" + sup("+")
MDM = "mol dm" + sup(M + "3")
STD = sup("⦵")
ECELL = i("E") + '<span class="stk post"><span><span class="pl-sym">⦵</span></span><span>cell</span></span>'
AL2O3 = AL + sub(2) + "O" + sub(3)
FE2O3 = "Fe" + sub(2) + "O" + sub(3)
HCO3 = "HCO" + sub(3) + sup(M)
H2CO3 = "H" + sub(2) + "CO" + sub(3)
CO3 = "CO" + sub(3) + sup("2" + M)
KP = i("K") + sub("p")
PKA1 = "p" + i("K") + sub("a1")
DG, DH, DS = DEL + i("G") + sub("r"), DEL + i("H") + sub("r"), DEL + i("S") + sub("r")

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
RULED_FIXES = []

# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)",
      P(A("Melting point increases from SO" + sub(3) + " to Na" + sub(2) + "O to SiO" + sub(2) + ".")),
      P(A("SO" + sub(3) + " has a " + u("simple molecular structure") + " with " + u("weak instantaneous dipole–induced dipole") + " interactions between the molecules, "
          "which require the least energy to overcome.")),
      P(A("Na" + sub(2) + "O has a " + u("giant ionic lattice structure") + " with " + u("strong electrostatic forces of attraction") + " between Na" + sup("+") +
          " and O" + sup("2" + M) + " ions, which require a lot of energy to overcome.")),
      P(A("SiO" + sub(2) + " has a " + u("giant molecular / covalent structure") + " made up of Si and O atoms held together in an " +
          u("extensive network by covalent bonds") + ", which requires the most energy to break."))),
 PART("(b)",
      P(A(AL + sup("3+") + " has a " + u("higher charge density") + " (than Mg" + sup("2+") + "), higher polarising power, and " +
          u("distorts the O" + sup("2" + M) + " electron cloud to a larger extent") + ". This induces " + u("covalent character") + " and " +
          u("disrupts / weakens the ionic lattice structure") + ", resulting in a lower amount of energy (heat) required for melting, and thus " +
          AL2O3 + " has a lower melting point."))),
 PART("(c)(i)", eq(AL2O3 + "(s) + 2NaOH(aq) + 3" + H2O + "(l)" + ARROW + "2Na[" + AL + "(OH)" + sub(4) + "](aq)")),
 PART("(c)(ii)", P(A(FE2O3 + " does not react with NaOH, remains insoluble and is " + u("filtered out") + "."))),
 PART("(c)(iii)",
      *BUL("Carry out the final step at a lower pressure or 1 atm",
           "to constantly remove the steam formed",
           "use a drying / dehydrating agent")),
 PART("(c)(iv)", eq(DEL + i("G") + sub("r") + " = " + DEL + i("H") + sub("r") + " " + M + " " + i("T") + DEL + i("S") + sub("r"))),
 PART("(c)(v)",
      P(A(DG + sub("(1273 K)") + " = " + DH + " – (1273)" + DS + " = – 422.17")),
      P(A(DG + sub("(1773 K)") + " = " + DH + " – (1773)" + DS + " = – 660.78")),
      P(A("– 422.17 + (1273)" + DS + " = – 660.78 + (1773)" + DS)),
      P(A(DS + " = " + frac("660.78 – 422.17", "1773 – 1273") + " = 0.47722 kJ K" + sup(M + "1") + " mol" + sup(M + "1") + " = 477 J K" + sup(M + "1") + " mol" + sup(M + "1")))),
 PART("(c)(vi)",
      P(A("Below 100 °C, water will be in the liquid rather than the gaseous state. Since the " + u("products") + " of decomposition are " +
          u("no longer gaseous / no gas molecules are formed") + ", the " + DS + " will be much " + u("less positive") + "."))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)",
      *BUL("The gas " + u("particles exert negligible attractive forces") + " on one another.",
           "An ideal gas consists of " + u("particles of negligible volume") + ". In other words, the size of the gas particles is negligible compared to the volume of the container.")),
 PART("(b)(i)", eq("pV = nRT")),
 PART("(b)(ii)", P(A("V = " + frac(frac("5", "114.0") + " × 8.31 × (250 + 273)", "101325") + " = 0.00188 m" + sup(3)))),
 PART("(b)(iii)",
      P(A(u("Relative deviation increases from pentane to ethanol to octane.") + " This is because the " + u("boiling point increases") + " due to the " +
          u("intermolecular forces of attraction becoming stronger") + " in the same order."))),
 PART("(c)(i)",
      P(A("Dynamic equilibrium refers to a state in a " + u("reversible system") + " within a closed system in which the forward and backward reactions are " +
          u("continuing at the same rate") + ", resulting in " + u("no net change in the macroscopic properties") +
          " (e.g. concentrations, partial pressure) of the reactants and products."))),
 PART("(c)(ii)",
      P(A("Let the initial partial pressure of " + H2O + "(g) be " + i("x") + ".")),
      TBL(["", H2O + "(g)", "+", "CH" + sub(4) + "(g)", RARR, "CO(g)", "+", "3H" + sub(2) + "(g)"],
          ["Initial " + i("p") + " / atm", i("x"), "", i("x"), "", "0", "", "0"],
          ["Change in " + i("p") + " / atm", M + "0.407" + i("x"), "", M + "0.407" + i("x"), "", "+0.407" + i("x"), "", "+3(0.407" + i("x") + ")"],
          ["Equilibrium " + i("p") + " / atm", "0.593" + i("x"), "", "0.593" + i("x"), "", "0.407" + i("x"), "", "1.221" + i("x")]),
      P(A("0.593" + i("x") + " + 0.593" + i("x") + " + 0.407" + i("x") + " + 1.221" + i("x") + " = 10.0 atm")),
      P(A(i("x") + " = " + frac("10.0", "2.814") + " = 3.5536 atm")),
      P(A(KP + " = " + frac("(0.407 × 3.5536)(1.221 × 3.5536)" + sup(3), "(0.593 × 3.5536)(0.593 × 3.5536)") + " = 26.6 atm" + sup(2)))),
 PART("(c)(iii)",
      P(A("The partial pressure of methane " + u("doubles") + " initially.")),
      P(A("However, the total pressure of the system doubles and by Le Chatelier’s Principle, the " + u("backward reaction is favoured") + " as it produces a lower amount of gas to "
          "partially offset the increase in pressure. Hence, more methane is produced and the partial pressure of methane " + u("further increases") +
          " so that at the new equilibrium, it is more than twice that of the original equilibrium."))),
 PART("(c)(iv)", IMG(2, "civ")),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)",
      TBL(["compound", "reagents and conditions required for reaction", "type of reaction"],
          ["CH" + sub(3) + "CH" + sub(2) + CL, "KCN in " + u("ethanol, heat"), "nucleophilic substitution"],
          ["(CH" + sub(3) + ")" + sub(2) + "CO", u("HCN") + ", KCN catalyst", "nucleophilic addition"])),
 PART("(b)(i)", P(A("The more positive the p" + i("K") + sub("a") + " of the compound, the less stable is its conjugate base."))),
 PART("(b)(ii)",
      P(A("Relative acidity increases from CH" + sub(3) + "CH" + sub(2) + "OH < CH" + sub(3) + "COOH < HBr.")),
      P(A("CH" + sub(3) + "COOH is more acidic than CH" + sub(3) + "CH" + sub(2) + "OH, as the " +
          u("negative charge on oxygen in the CH" + sub(3) + "COO" + sup(M) + " ion is dispersed") +
          " over two highly electronegative oxygen atoms resulting in two equivalent resonance structures and CH" + sub(3) + "COO" + sup(M) + " is " + u("resonance stabilised") + ".")),
      P(A("The " + u("electron donating ethyl group intensifies the negative charge") + " on oxygen in the " + u("CH" + sub(3) + "CH" + sub(2) + "O" + sup(M) + " ion") +
          ", making it the " + u("least stable conjugate base") + " of the three.")),
      P(A("HBr is the most acidic of the three as the " + u("negative charge is spread over a larger") + " Br" + sup(M) + " ion resulting in the greatest extent of charge dispersal."))),
 PART("(c)(i)", IMG(3, "ci")),
 PART("(c)(ii)",
      P(A("CH" + sub(4) + " has a larger p" + i("K") + sub("a") + " than CH" + sub(3) + "CH" + sub(2) + "OH, therefore the " +
          u("CH" + sub(3) + sup(M) + " ion (leaving group) is less stable than the CH" + sub(3) + "CH" + sub(2) + "O" + sup(M) + " ion") +
          ", hence the alternative process is less feasible."))),
 PART("(d)",
      P(A("1) To each sample in a test-tube, add a few drops of " + u("aqueous bromine") + ".")),
      P(A("• Orange bromine " + u("decolourises") + " with bromoethene but the solution " + u("remains orange") + " for bromoethane and bromobenzene.")),
      P(A("2) " + u("Heat") + " samples of bromoethane and bromobenzene in separate test tubes with " + u("ethanolic silver nitrate") + " until no further change occurs.")),
      P(A("• A pale " + u("cream precipitate") + " of AgBr is formed with bromoethane after some time but " + u("no precipitate") +
          " is formed with bromobenzene even with prolonged heating.")),
      NOTE("Other tests are also possible, e.g. 4-step halide test, KMnO" + sub(4) + ".")),
 PART("(e)(i)", IMG(3, "ei")),
 PART("(e)(ii)", IMG(3, "eii")),
 PART("(e)(iii)", eq("CH" + sub(3) + "CH" + sub(3))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)", P(A("A buffer solution is a solution which is able to " + u("resist pH changes") + " when a " + u("small amount of an acid or a base is added") + "."))),
 PART("(b)(i)", eq("[" + HCO3 + "] = 0.00255 " + MDM)),
 PART("(b)(ii)",
      P(A("When " + u("[H" + sup("+") + "] increases") + ", by Le Chatelier’s Principle, the " +
          u("equilibrium position of reaction 4.1 shifts to the left to partially offset the increase in [H" + sup("+") + "]") +
          " by favouring the backward reaction of the equilibrium, " + u("resulting in a small decrease in pH / pH remains approximately constant") + "."))),
 PART("(b)(iii)",
      P(A(HCO3 + "(aq) + " + HP + "(aq) → " + H2CO3 + "(aq)")),
      P(A("Since n(" + HP + ") reacted = 0.05 mol, decrease in n(" + HCO3 + ") = 0.05 mol")),
      P(A(u("change in [" + HCO3 + "] = " + frac("0.05 mol", "1 m" + sup(3)) + " = 0.05 × 10" + sup(M + "3") + " = " + M + "5.00 × 10" + sup(M + "5") + " " + MDM)))),
 PART("(b)(iv)",
      IMG(4, "biv"),
      P(A("reading the Bjerrum plot:")),
      P(A("Sample " + b("I"))),
      P(A("Decrease in [" + HCO3 + "] = 0.00005 " + MDM + " = half a small square")),
      P(A(u("change in pH = 7.7 " + M + " 8.1 = " + M + "0.4")))),
 PART("(c)(i)",
      P(A("From Figure 4.1, at point " + b("A") + ", " + u("[" + H2CO3 + "] = [" + HCO3 + "]") + ", which is the " + u("maximum buffer capacity") +
          " point based on the " + H2CO3 + " / " + HCO3 + " buffer system, reaction 4.1.")),
      P(A("Hence " + u("pH = " + PKA1 + " = 6.35") + ", which is seen in Figure 4.1 at point " + b("A") + "."))),
 PART("(c)(ii)",
      P(A("Comparing effectiveness:")),
      P(A("While the same amount of " + HP + " ions was added to sample " + b("I") + " and " + b("II") + ", the pH change of sample " + b("I") + " is " + u(M + "0.4") +
          " while that for sample " + b("II") + " is " + u(M + "0.1") + ". Since the pH change per mol of " + HP + " added is less for " +
          u("sample " + b("II") + ", it is more effective at resisting pH change") + ".")),
      P(A("Commenting on / explaining the difference between " + b("I") + " and " + b("II") + ":")),
      P(A(u("(i) composition"))),
      P(A(u("sample " + b("I")) + " is near the end point of reaction 4.1, with a " + u("very high [" + HCO3 + "] but near zero [" + H2CO3 + "]") +
          ", and thus is far from the effective buffer zone, that is why the pH change is greater than for " + u("sample " + b("II")) +
          " which has a buffer mixture composition " + u("[" + H2CO3 + "] = [" + HCO3 + "]") + " and is within the effective buffer region of reaction 4.1, hence having a smaller change in pH.")),
      P(A(u("(ii) based on data in plot"))),
      P(A("Using the Bjerrum plot, it is observed that with sample " + b("I") + " at pH = 8.1, the gradients of the [" + HCO3 + "] and [" + H2CO3 + "] curves are very gentle; "
          "hence a small change in the y-axis, which is concentration, results in a larger change in the x-axis, which is pH, thus revealing sample " + b("I") +
          " to have poorer effectiveness in resisting pH change.")),
      P(A("From the Bjerrum plot, at point " + b("A") + ", which is where sample " + b("II") + " is at, the gradients of the concentration curves are steep. Hence a change in the "
          "y-axis, which is concentration, results in little change in the x-axis, which is pH, thus revealing sample " + b("II") +
          " to have better effectiveness in resisting pH change."))),
 PART("(d)(i)",
      eq("CO" + sub(2) + " + " + H2O + " " + RARR + " " + H2CO3),
      eq(H2CO3 + " + MgO → MgCO" + sub(3) + " + " + H2O)),
 PART("(d)(ii)",
      P(A("Since " + CO3 + " is precipitated, there is a " + u("lower [" + CO3 + "]") + ", which makes it " + u("more difficult") +
          " for shelled marine creatures to make " + u("carbonate-based shells") + "."))),
 PART("(e)",
      P(A("[Fe(" + H2O + ")" + sub(6) + "]" + sup("3+") + "(aq) + " + H2O + "(l) " + RARR + " [Fe(" + H2O + ")" + sub(5) + "(OH)]" + sup("2+") + "(aq) + H" + sub(3) + "O" + sup("+") + "(aq)")),
      P(A("Fe" + sup("3+") + " has " + u("high charge density") + " and hence " + u("high polarising power") + ",")),
      P(A("so it is able to " + u("distort") + " the electron cloud of coordinated water molecules, " + u("weakening the O–H bond") + ". As a result, the " +
          u("O–H bond") + " undergoes heterolytic fission readily to " + u("release " + HP) + "."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", IMG(5, "ai")),
 PART("(a)(ii)",
      eq("Anode: LiC" + sub(6) + " → C" + sub(6) + " + Li" + sup("+") + " + e" + sup(M)),
      eq("Cathode: Li" + sup("+") + " + e" + sup(M) + " + FePO" + sub(4) + " → LiFePO" + sub(4))),
 PART("(a)(iii)", eq("Fe."), eq("From +3 to +2")),
 PART("(a)(iv)", eq(ECELL + " = +0.45 – (–3.00) = +3.45 V")),
 PART("(a)(v)", P(A("Number of modules = " + frac("400", "(24)(3.45)") + " = 4.83 = 5 (to " + u("nearest whole number") + ")"))),
 PART("(b)(i)",
      *BUL("Fe and phosphates have low toxicity, whereas heavy metals like Co and Ni are toxic and cause health and environmental pollution.",
           "Fe and phosphate are more abundant, so they are more environmentally sustainable to extract.",
           "More charging cycles / longer lifespan, so the battery can be used longer before disposal.",
           "The cheaper cost per km of LFP will be more attractive for consumers to use EVs and shift away from the use of fossil fuels.")),
 PART("(b)(ii)",
      P(A("In recharging, Cu" + sup("2+") + " is " + u("preferentially reduced") + " since " + u(i("E") + STD + "(Cu" + sup("2+") + "/Cu) (+0.34 V)") +
          " is more positive than " + i("E") + STD + " " + u("(Li" + sup("+") + "/LiC" + sub(6) + ") (" + M + "3.00 V)") + ".")),
      P(A("Hence, Cu metal will coat on the graphite in electrode " + b("A") + ". " + u("Less Li" + sup("+") + " ions would be reduced") +
          " (by the same amount of electrons), resulting in lower capacity of the battery since " + u("less Li is coordinated on the graphite") + "."))),
 PART("(c)(i)",
      P(A("Time taken = " + frac("(0.8 – 0.3)(153000)", "(70)(60)"))),
      P(A("= 18.2 min"))),
 PART("(c)(ii)",
      P(A("The longer actual charging time is attributed to " + u("energy / heat loss") + " arising from heat dissipation and internal resistance."))),
 PART("(c)(iii)",
      P(A("Total charge = 1.53 × 10" + sup(8) + " / 400")),
      P(A("= 382500 C")),
      NOTE("Accept 383000 C (3 significant figures).")),
 PART("(c)(iv)",
      P(A("n(e" + sup(M) + ") transferred = " + frac("382500", "96500"))),
      P(A("= 3.96 mol (3 significant figures)"))),
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
