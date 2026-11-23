"""Hand transcription of the SAJC 2026 H2 Prelim Paper 2 (9476/02) suggested solutions (21-page PDF + docx twin; the text is typed
from the docx, which carries the underlines, and the ten answer figures are snipped from the Word PDF by
crop_sajc26_p2_answers.py) -> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).

Run from the repo root:
    python3 -I ingest/build_sajc26_p2_answers.py <outdir> <questions_dir>
(<questions_dir> = the folder holding questions.json from build_sajc26_p2.py; the worked-solution labels must be exactly the
question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6): div.worked-solution > div.part > (span.lab + div.body); answers in span.ans with <u> on the
school's underlined keywords; figures are bare img.ws-fig[data-asset] (SAJC_H2_P2_Q<n>_ans-<slot>_2026.png); tables are table.cmp.
Dropped from the school's pages: the L/M/H and A/B/... labels in the right margin, the [n] mark ticks, the cyan highlights, the
purple "1|1|1 accept this" scribble at Q1(c)(ii) and the "(wef)" marking abbreviations. The school's "OR" lines become P("Or").

FIXES made to the school's answers (listed to the user; veto-able):
  1(c)(ii)  "requires more energy is to remove the e-" -> "requires more energy to remove the e-" (twice); "increase in shielding" -> "the increase in shielding";
  1(e)(iii) "distorts/polarise" -> "distorts/polarises";
  4(a)      "overlap side ways" -> "overlap sideways";
  5(a)(i)   "dipole induced dipole interaction with" -> "interactions with";
  5(b)(i)   "hydrogen-bonds" -> "hydrogen bonds";
  figure numbers in the school's text follow the question paper's numbering (Fig 4.1-4.3), and the school's "Table 4.1" caption that
  sits over Table 5.1 is not reproduced;
  3(b)(iv), 5(c)(i-iii), 1(d)(i), 2(a)(ii), 4(b)(ii), 4(d), 4(e)(ii) are the school's own drawings, snipped as printed (the school's
  doubled labels / numbering on the T, U, V structures at 5(c)(iii) are kept).
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
PFX, YEAR = "SAJC_H2_P2", 2026
M = "−"
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
def i(s): return "<i>%s</i>" % s
def b(s): return "<b>%s</b>" % s
def u(s): return "<u>%s</u>" % s
L = '<i class="el">l</i>'
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
ARROW = " → "
RARR = "⇌"
BOND = "–"
DB = "="
MDM = "mol dm" + sup(M + "3")
KJ = "kJ mol" + sup(M + "1")
STD = sup('<span class="pl-sym">⦵</span>')
H2O = "H" + sub(2) + "O"
EMINUS = "e" + sup(M)
def iso(a, sym, ch=""): return sup(a) + sym + (sup(ch) if ch else "")
DHS = DEL + i("H") + STD
DH_HYD = DEL + i("H") + STD + sub("hydrogenation")
DGS = DEL + i("G") + STD
KC = lambda n: i("K") + sub("c" + str(n))
THALF = i("t") + sub("½")

ASSETS = []     # (question, slot) in per-question DOM order
def _path(qn, slot): return "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR)
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s" alt=""></p>' % _path(qn, slot)

W = {}
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)",
      P(A("Isotopes are " + u("atoms") + " with the " + u("same number of protons") + " but " + u("different number of neutrons") + "."))),
 PART("(a)(ii)",
      P(A(frac("(23.92 × 66.71) + (25.08 × 5.99) + (26.11 × 9.31)", "66.71 + 5.99 + 9.31"))),
      P(A("= " + u("24.25") + " (4 s.f.)"))),
 PART("(b)",
      TBL([b("particle"), b("number of protons"), b("number of neutrons"), b("number of electrons")],
          [iso(12, "C", "4+"), "6", "6", "2"],
          [iso(13, "C"), "6", "7", "6"],
          [iso(18, "O", "2" + M), "8", "10", "10"],
          [iso(25, "Mg", "2+"), "12", "13", "10"],
          [iso(26, "Mg"), "12", "14", "12"])),
 PART("(c)(i)", P(A("O(g)" + ARROW + "O" + sup("+") + "(g) + " + EMINUS))),
 PART("(c)(ii)",
      P(A("N has a " + u("higher nuclear charge") + " than C, while " + u("the increase in shielding effect is negligible") + ". Thus, there is " +
          u("stronger attraction between the nucleus and the valence electrons in N") + ", which requires more energy to remove the " + EMINUS + ". " +
          u("N has a higher first IE than C") + ".")),
      P(A("The " + u("paired " + EMINUS + " removed from O experience inter-electronic repulsion") + ", which " + u("outweighs the increase in nuclear charge") +
          ". Thus, there is " + u("weaker attraction between the nucleus and the valence electrons in O") + ", which requires less energy to remove the " +
          EMINUS + ". " + u("O has a lower first IE than N") + "."))),
 PART("(d)(i)", IMG(1, "di")),
 PART("(d)(ii)",
      P(A("Add a sample of magnesite into " + u("HC" + L + "(aq)") + " (any dilute acid). Effervescence is observed and the " + u("gas") + " evolved " +
          u("forms a white ppt in lime water") + "."))),
 PART("(e)(i)",
      P(A("MgC" + L + sub(2) + " has a " + u("giant ionic lattice") + " structure with strong " + u("ionic bonds between Mg" + sup("2+") + " and C" + L + sup(M)) + ". " +
          "PC" + L + sub(5) + " is a " + u("simple covalent molecule") + " with weak " + u("instantaneous dipole – induced dipole interactions between molecules") + ". " +
          u("MgC" + L + sub(2) + " has a higher melting point") + " because more energy is required to break the " + u("stronger ionic bonds") + "."))),
 PART("(e)(ii)",
      P(A("[Mg(" + H2O + ")" + sub(6) + "]" + sup("2+") + "(aq) + " + H2O + "(l) " + RARR + " [Mg(OH)(" + H2O + ")" + sub(5) + "]" + sup("+") + "(aq) + H" + sub(3) + "O" + sup("+") + "(aq)")),
      P(A("Or")),
      P(A("[Mg(" + H2O + ")" + sub(6) + "]" + sup("2+") + "(aq) " + RARR + " [Mg(OH)(" + H2O + ")" + sub(5) + "]" + sup("+") + "(aq) + H" + sup("+") + "(aq)"))),
 PART("(e)(iii)",
      P(A(u("Fe" + sup("3+")) + " has a higher charge and " + u("higher charge density") + " than Mg" + sup("2+") + ". Fe" + sup("3+") +
          " has a higher polarising power, which " + u("distorts/polarises the electron cloud of water more") + ". As the " +
          u("O" + BOND + "H bond is weakened to a greater extent") + ", " + u("more H" + sup("+")) + " is released in FeC" + L + sub(3) + "(aq).")))
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)",
      P(A(u("1s" + sup(2) + " 2s" + sup(2) + " 2p" + sup(6) + " 3s" + sup(2) + " 3p" + sup(6) + " 3d" + sup(6))))),
 PART("(a)(ii)", IMG(2, "aii")),
 PART("(a)(iii)",
      P(A(u("Dative bond") + ". The " + u("N atom donates a lone pair of electrons") + " to the " + u("vacant/empty orbital of Fe" + sup("2+")) + "."))),
 PART("(b)(i)",
      P(A(u("In the presence") + " of the nitrogen-containing and O" + sub(2) + " " + u("ligands") + ", the partially filled " + u("d orbitals") + " of Fe" + sup("2+") + " " +
          u("split into 2 energy levels") + ". " + u("Energy from visible light is absorbed") + " when an " + u("electron") + " from the lower energy d orbital is " +
          u("promoted to a higher energy") + " d orbital. The " + u("red/observed colour is not absorbed / reflected") + "."))),
 PART("(b)(ii)",
      P(A("In HbO" + sub(2) + ", the " + u("O" + sub(2) + " ligand") + " causes a " + u("different energy gap") + " when the d orbitals split into two groups."))),
 PART("(c)(i)",
      P(A(u("C is less electronegative than O") + " and its " + u("lone pair of electrons on C is more available") + " to form dative bond with Fe" + sup("2+") + "."))),
 PART("(c)(ii)",
      P(A("Haemoglobin has a " + u("greater/stronger affinity for CO") + " than for O" + sub(2) + ", as " + u(KC(2) + " is much larger than " + KC(1)) + "."))),
 PART("(c)(iii)",
      P(A(KC(2) + " = " + frac("[Hb(CO)" + sub(4) + "]", "[Hb][CO]" + sup(4)))),
      P(A("Units: mol" + sup(M + "4") + " dm" + sup(12)))),
 PART("(d)(i)",
      P(A("At high [O" + sub(2) + "], the " + u("position of equilibrium 3 shifts left") + " to decrease the [O" + sub(2) + "]. This causes the " +
          u("O" + sub(2) + " to displace/replace CO") + "."))),
 PART("(d)(ii)",
      P(A(u(KC(3) + " = " + KC(2) + " / " + KC(1)))),
      P(A(KC(3) + " = " + frac("2.2 × 10" + sup(29), "4.5 × 10" + sup(6)) + " = " + u("4.9 × 10" + sup(22))))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)(i)", P(A("4-methylbenzoic acid"))),
 PART("(a)(ii)",
      P(A(b("D") + " forms a " + u("more stable conjugate base/anion") + " because the " + u("negative charge on O can further delocalise into the benzene ring") +
          ". Hence, the negative charge is more dispersed. " + b(u("D")) + " will dissociate to " + u("give more H" + sup("+")) + " and is more acidic."))),
 PART("(a)(iii)", IMG(3, "aiii")),
 PART("(b)(i)", P(A("Nucleophilic addition"))),
 PART("(b)(ii)", P(A("rate = " + i("k") + "[CH" + sub(3) + "COC" + L + "][" + H2O + "]"))),
 PART("(b)(iii)",
      P(A("5.1 × 10" + sup(M + "6") + " = " + i("k") + " (2.00 × 10" + sup(M + "2") + ")(0.15)")),
      P(A(i("k") + " = " + u("1.7 × 10" + sup(M + "3") + " mol" + sup(M + "1") + " dm" + sup(3) + " s" + sup(M + "1"))))),
 PART("(b)(iv)",
      IMG(3, "biv"),
      P(A(THALF + " is constant."))),
 PART("(b)(v)",
      P(A("Calculate/Determine the " + u("gradient of the tangent") + " (to the curve) " + u("at " + i("t") + " = 0") + "."))),
 PART("(b)(vi)",
      P(A("At higher T, the particles " + u("gain kinetic energy") + ". The amount of " + u("reacting particles with energy greater than or equal to " + i("E") + sub("a") + " increases") +
          ". Hence, the " + u("frequency of effective collision") + " increases, " + u("rate increases") + "."))),
 PART("(c)(i)",
      P(A("As the substituent is " + u("more electronegative/electron withdrawing") + ", the " + u("rate of hydrolysis increases") + "."))),
 PART("(c)(ii)",
      P(A("The " + u("C of C=O is more electron deficient") + " due to the more electron-withdrawing/electronegative atom. Hence, " +
          u("water/nucleophile can attack the C more easily") + "."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)",
      P(A(u("Each C has a p orbital with 1 electron") + ". The p orbitals " + u("overlap sideways") + " for the π electrons to delocalise."))),
 PART("(b)(i)",
      P(A(DH_HYD + " = " + M + "112 × 2 = " + u(M + "224") + " " + KJ))),
 PART("(b)(ii)", IMG(4, "bii")),
 PART("(c)(i)",
      P(A(DEL + i("H") + " = [10 C" + BOND + "H + 3 C" + DB + "C + 1 C" + BOND + "C] " + M + " [10 C" + BOND + "H + 1 C" + DB + "C + 5 C" + BOND + "C]")),
      P(A("= [2 C" + DB + "C] " + M + " [4 C" + BOND + "C]")),
      P(A("= 2(+610) " + M + " 4(350)")),
      P(A("= " + u(M + "180") + " " + KJ))),
 PART("(c)(ii)",
      P(A("Entropy is negative as there is a " + u("decrease in the amount of gaseous species") + " from 2 to 0 and the " + u("system is less disordered") + "."))),
 PART("(c)(iii)",
      P(A(DEL + i("G") + " = " + DEL + i("H") + " " + M + " " + i("T") + DEL + i("S") + " = " + M + "180 " + M + " (298)(" + M + "182/1000) = " + u(M + "126 " + KJ))),
      P(A("Since " + DEL + i("G") + " < 0, " + u("reaction is spontaneous") + " at 298 K."))),
 PART("(d)", IMG(4, "d")),
 PART("(e)(i)",
      TBL(["sp hybridised carbon", "1"],
          ["sp" + sup(2) + " hybridised carbon", "2"],
          ["sp" + sup(3) + " hybridised carbon", "1"]),
      P(A("C1 and C3 are sp" + sup(2) + " hybridised and C2 is sp hybridised. C4 is sp" + sup(3) + " hybridised."))),
 PART("(e)(ii)", IMG(4, "eii")),
 PART("(e)(iii)",
      P(A("The " + u("four p orbitals") + " of the 2 π bonds " + u("are perpendicular / 90° / not parallel to each other/cannot overlap sideways") +
          ". Hence, the π electrons cannot delocalise."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)",
      P(A("Propanone can form intermolecular " + u("instantaneous dipole–induced dipole interactions") + " with the " + u("non-polar alkyl chain of oleyl alcohol") +
          ", while the " + u("polar C=O or electronegative O") + " can form " + u("intermolecular hydrogen bonding with water") + "."))),
 PART("(a)(ii)",
      P(A("Test: " + u("I" + sub(2) + "(aq), NaOH(aq), warm"))),
      P(A("Observations if not contaminated: " + u("no yellow ppt"))),
      P(A("Observations if contaminated: yellow ppt")),
      P(A("Or")),
      P(A("Test: " + u("2,4-DNPH"))),
      P(A("Observations if not contaminated: " + u("no orange ppt"))),
      P(A("Observations if contaminated: orange ppt")),
      P(N("Note – This is not a test to prove the presence of butan-1-ol, but rather, the absence of propanone and ethanol."))),
 PART("(b)(i)",
      P(A("Water has a higher boiling point. Water can form an average of two intermolecular hydrogen bonds per molecule, while ethanol can only form one. Hence, " +
          u("water forms more/extensive intermolecular hydrogen bonds") + " than ethanol, which requires more energy to overcome."))),
 PART("(b)(ii)", P(A(u("Propanone") + ". It has the " + u("lowest enthalpy change of vapourisation") + "."))),
 PART("(b)(iii)",
      P(A("Advantage: Gas stripping is carried out at a lower temperature of 35 °C compared to the higher boiling points of propanone and ethanol. Hence less energy is required / more energy efficient / lower cost / safer.")),
      P(A("Disadvantage: Gas stripping requires the use of gas, which is more difficult / dangerous to store / transport.")),
      P(A("Or")),
      P(A("Gas stripping has a low yield / is slow as only some of the organic molecules vapourise at 35 °C, while all the organic molecules boil at the boiling point.")),
      P(A("Or")),
      P(A("Further separation is still required after gas stripping due to the close " + DEL + i("H") + sub("vapourisation") + " of propanone and ethanol."))),
 PART("(c)(i)", IMG(5, "ci")),
 PART("(c)(ii)", IMG(5, "cii")),
 PART("(c)(iii)", IMG(5, "ciii")),
 PART("(c)(iv)",
      P(A(b(u("V")) + " is formed in smaller amount. The 4-membered ring is not stable due to " + b(u("ring strain")) + "."))),
 PART("(d)",
      P(A("Biofuels come from plants which capture/remove/take in CO" + sub(2) + " from the atmosphere when they grow / during photosynthesis."))),
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
