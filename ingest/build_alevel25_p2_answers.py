"""Hand transcription of the VJC suggested answers to A Level (SEAB) 9729/02 Oct/Nov 2025
-> worked_solutions.json + answer_assets.json (feeds gen_answers_migration.py --type structured).
Source: the college answers docx + its Word PDF (5 pages); typed from the rendered pages and checked
against the docx text (see the verification at the bottom).

Run from the repo root:
    python3 ingest/build_alevel25_p2_answers.py <outdir> <questions_dir> [<answers.docx>]
(<questions_dir> = the folder holding questions.json from build_alevel25_p2.py; used to check that the
worked-solution labels are exactly the question parts that carry a mark badge.)

Conventions (claude/style-guide.md SS6, build_alevel_p2_answers.py for 2024):
  div.worked-solution > div.part > (span.lab + div.body); answers in span.ans; figures are bare
  img.ws-fig[data-asset] (the user snips them: SEAB_H2_P2_Q<n>_ans-<slot>_2025.png); tables are table.cmp
  (no thead/th). This scheme carries no marking points and no examiner comments; its only red text (the
  Q3(c)(i) note "A and B bind with ligands head-on...") sits INSIDE the energy-level diagram snip and is
  kept there (user ruling 2026-11-02).
RULED_FIXES holds the wording/chemistry changes the user has ruled on; nothing is changed silently.
"""
import json, re, sys
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
QDIR = Path(sys.argv[2])
DOCX = sys.argv[3] if len(sys.argv) > 3 else None
PFX = "SEAB_H2_P2"
YEAR = 2025
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
def ion(sym, ch): return sym + sup(ch)
FE2, FE3 = ion("Fe", "2+"), ion("Fe", "3+")
ALCL3 = "A" + L + CL + sub(3)
AL2CL6 = "A" + L + sub(2) + CL + sub(6)
HCL = "H" + CL
H2O = "H" + sub(2) + "O"
S2O8 = "S" + sub(2) + "O" + sub(8) + sup("2" + M)
SO4 = "SO" + sub(4) + sup("2" + M)
DEL = "Δ"
def dg(s=""): return DEL + i("G") + (sub(s) if s else "")
MOLK = "kJ K" + sup(M + "1") + " mol" + sup(M + "1")

ASSETS = []     # (question, slot) in per-question DOM order
def IMG(qn, slot):
    ASSETS.append((qn, slot))
    return '<p><img class="ws-fig" data-asset="%s_Q%d_ans-%s_%d.png" alt=""></p>' % (PFX, qn, slot, YEAR)

W = {}   # qn -> list of PART html
# ------------------------------------------------------------------ Q1
W[1] = [
 PART("(a)(i)", P(A(ALCL3 + " + 3" + H2O + ARROW + "A" + L + "(OH)" + sub(3) + " + 3" + HCL))),
 PART("(a)(ii)", P(A("Hydrolysis"))),
 # RULED 2026-11-02 (user): both Lewis base and Bronsted-Lowry base are acceptable; the school's answer is kept
 # and the Bronsted-Lowry wording is added as an OR alternative.
 PART("(b)", P(A("Lewis base as NH" + sub(3) + "(g) donates a lone pair to the hydrogen of " + HCL + "(g) to form NH" + sub(4) + CL + ".")),
      P(A("OR")),
      P(A("Brønsted–Lowry base as NH" + sub(3) + "(g) accepts a proton (H" + sup("+") + ") from " + HCL + "(g) to form NH" + sub(4) + CL + "."))),
 PART("(c)", IMG(1, "c")),
 PART("(d)(i)", P(A("When the " + AL2CL6 + " dimer decomposes, covalent bonds are broken which is an endothermic process. "
                    "When temperature is increased, the system will counteract the increase in temperature by favouring the forward endothermic "
                    "process to absorb the excess heat. Position of equilibrium shifts right, increasing the amount of " + ALCL3 + "."))),
 PART("(d)(ii)", P(A("No effect. (Equilibrium constant only varies with temperature.)"))),
 PART("(e)(i)", P(A("Tetrahedral"))),
 PART("(e)(ii)", P(A("90°"))),
]
# ------------------------------------------------------------------ Q2
W[2] = [
 PART("(a)(i)", P(A("Electrostatic forces of attraction between a shared pair of electrons and positively charged nuclei of two bonded atoms."))),
 PART("(a)(ii)", IMG(2, "aii")),
 PART("(b)",
      TBL(["", FE2, FE3, "S ion"],
          ["mass (g)",
           frac("18.86", "100") + " " + TIMES + " 25.00<br>= 4.715",
           frac("37.73", "100") + " " + TIMES + " 25.00<br>= 9.4325",
           "25.00 " + M + " 4.715 " + M + " 9.4325<br>= 10.8525"],
          ["molar mass (g/mol)", "55.8", "55.8", "32.1"],
          ["amount (mol)", "0.0845", "0.1690", "0.3381"],
          ["relative ratio", "1", "2", "4"]),
      P(A("Let the oxidation number of sulfur in the sample be " + i("X") + ".")),
      P(A("4" + i("X") + " + (+2) + 2(+3) = 0")),
      P(A(i("X") + " = " + M + "2"))),
 PART("(c)(i)", P(A("The reaction between " + S2O8 + " and I" + sup(M) + " is slow due to the high activation energy caused by the repulsion "
                    "between the two negatively charged ions."))),
 PART("(c)(ii)", P(A("Homogeneous catalyst"))),
 PART("(c)(iii)", P(A("2" + FE2 + " + " + S2O8 + ARROW + "2" + FE3 + " + 2" + SO4)),
      P(A("2" + FE3 + " + 2I" + sup(M) + ARROW + "2" + FE2 + " + I" + sub(2)))),
]
# ------------------------------------------------------------------ Q3
W[3] = [
 PART("(a)", P(A("Iron is a transition element as it is a d block element whose atom has an incomplete d-subshell, "
                 "or which can give rise to cations with an incomplete d-subshell."))),
 PART("(b)", IMG(3, "b")),
 PART("(c)(i)", IMG(3, "ci")),
 PART("(c)(ii)", P(A("In " + FE3 + "(aq), repulsion of 3d-orbitals by approaching " + H2O + " ligands occurs. Greater repulsion of " + b("A") + " and " + b("B") +
                     " orbitals as they lie along the axes the ligands approach from. Lesser repulsion of " + b("C") + ", " + b("D") + " and " + b("E") +
                     " orbitals as they lie in between the axes the ligands approach from. Hence, " + b("C") + ", " + b("D") + " and " + b("E") +
                     " orbitals are raised to a lower energy level than " + b("A") + " and " + b("B") + " orbitals. All the 3d-orbitals in " + FE3 +
                     "(aq) are at higher energy levels than they are in " + FE3 + "(g) which have the same energy level, i.e. degenerate, as ligands are absent."))),
 PART("(d)(i)", P(A("[Fe(" + H2O + ")" + sub(5) + "(SCN)]" + sup("2+")))),
 PART("(d)(ii)", P(A("The degenerate 3d orbitals are split into two different energy levels in the presence of ligands. 3d electrons from the lower energy "
                     "level are promoted to the upper energy level by absorbing a photon of light from the visible region of the electromagnetic spectrum "
                     "where the energy of the absorbed photon is equal to the difference in the energy levels of the orbitals. The colour seen is the "
                     "complement of those absorbed in the visible region of the spectrum."))),
]
# ------------------------------------------------------------------ Q4
W[4] = [
 PART("(a)(i)", P(A("Concentrated HNO" + sub(3) + ", concentrated H" + sub(2) + "SO" + sub(4) + " catalyst, heat at 50°C"))),
 PART("(a)(ii)", IMG(4, "aii")),
 PART("(b)", IMG(4, "b")),
 PART("(c)(i)", P(A("sp" + sup("2")))),
 PART("(c)(ii)", IMG(4, "cii")),
 PART("(c)(iii)", P(A("Each carbon atom and nitrogen atom has an unhybridised 2p orbital that is parallel to one another and contains an electron. "
                      "Each of the 2p orbitals overlap sideways with adjacent 2p orbitals continuously to form π bonds resulting in a delocalised "
                      "π electron cloud."))),
 PART("(c)(iv)", P(A("Nitrogen is more electronegative than carbon and pulls electron density away from the ring via inductive effect. "
                     "This would reduce the electron density in the pyridine ring compared to benzene so electrophiles are less attracted to it."))),
 PART("(d)(i)", P(A("C" + sub(6) + "H" + sub(5) + "NO" + sub(2)))),
 PART("(d)(ii)", TBL(["", "nicotinamide"], ["σ bonds", "15"], ["π bonds", "4"])),
 PART("(d)(iii)", P(A(HCL + "(aq), heat OR H" + sub(2) + "SO" + sub(4) + "(aq), heat"))),
 PART("(e)(i)", P(A("Nucleophilic addition"))),
 PART("(e)(ii)", IMG(4, "eii")),
 PART("(e)(iii)", P(A("The rate constant for the catalysed reaction is greater than that of the uncatalysed reaction. As the catalysed reaction has a "
                      "pathway of lower activation energy, a greater proportion of reactants possesses energy greater than this activation energy. "
                      "This increases the frequency of effective collisions."))),
]
# ------------------------------------------------------------------ Q5
W[5] = [
 PART("(a)(i)", P(A(dg() + " = " + DEL + i("H") + " " + M + " " + i("T") + DEL + i("S")))),
 PART("(a)(ii)",
      P(A("From the equation,     " + dg() + " = " + DEL + i("H") + " " + M + " " + i("T") + DEL + i("S"))),
      P(A("The gradient of the graph = " + M + DEL + i("S"))),
      P(A(M + DEL + i("S") + " = " + frac(M + "1040 " + M + " (" + M + "960)", "340 " + M + " 740") + " = 0.200 " + MOLK.replace(" mol", " mol", 1))),
      P(A(DEL + i("S") + " = " + M + "200 J K" + sup(M + "1") + " mol" + sup(M + "1")))),
 PART("(a)(iii)", P(A("y-intercept of the graph")), IMG(5, "aiii")),
 # RULED 2026-11-02 (user): "dG3" typed without its subscript in the school's text -> typed as dG<sub>3</sub>
 PART("(b)", P(A("Reaction 4 " + M + " Reaction 3:")), IMG(5, "b"),
      P(A("At 300 K,")),
      P(A("2" + dg("r") + " = (" + dg("4") + ") " + M + " " + dg("3"))),
      P(A(dg("r") + " = [" + M + "1140 " + M + " (" + M + "260)] ÷ 2")),
      P(A("= " + M + "440 kJ mol" + sup(M + "1")))),
]
# ------------------------------------------------------------------ Q6
C17H36, C17H34O2 = "C" + sub(17) + "H" + sub(36), "C" + sub(17) + "H" + sub(34) + "O" + sub(2)
W[6] = [
 PART("(a)(i)", P(A("Methyl hexadecanoate (1 + 6 + 10 = 17 carbon atoms)"))),     # user 2026-11-02: leave as is
 PART("(a)(ii)", P(A("CH" + sub(3) + "(CH" + sub(2) + ")" + sub(16) + "CO" + sub(2) + "CH" + sub(3)))),
 PART("(b)", P(A("Biodiesel contains oxygen and require less oxygen than hydrocarbons found in diesel for complete combustion so there would be less "
                 "incomplete combustion. Comparing " + C17H36 + " and " + C17H34O2 + ", heptadecane requires 26 moles of oxygen per mole of heptadecane "
                 "each while " + b("L") + " requires 24.5 moles each for complete combustion. As a result, biodiesel burns more completely, producing "
                 "less unburnt fuel, CO and solid carbon emissions."))),
 PART("(c)", P(A("Biodiesel produces less energy per gram, for example " + b("L") + " produces 37.81 kJ g" + sup(M + "1") + " while heptadecane produces 44.48 kJ g" +
                 sup(M + "1") + "."))),
 PART("(d)", P(A(b("M") + " has one carbon-carbon double bond, compared to " + b("L") + " which has no carbon-carbon double bond. " + b("M") +
                 " requires less oxygen for complete combustion than " + b("L") + " per mole of methyl ester from Table 6.1. This is because the unsaturated "
                 "methyl ester has less hydrogen atoms, thus requiring less oxygen for complete combustion. Methyl esters containing carbon-carbon double "
                 "bonds burn more completely, produce less CO and solid carbon emissions."))),
 PART("(e)", P(A("The amount of CO" + sub(2) + " released to the atmosphere is the same as the amount the plants from removed from the atmosphere when they grow, "
                 "so there is no net increase of CO" + sub(2) + " released into the atmosphere."))),
]
# ------------------------------------------------------------------ Q7
SN1, SN2 = "S" + sub("N") + "1", "S" + sub("N") + "2"
W[7] = [
 PART("(a)", P(A("Steric hindrance due to bulky alkyl groups."))),
 PART("(b)(i)", P(A("Stability of the carbocation intermediate. The halogenoalkanes undergo heterolytic fission to form a halide ion and a carbocation. "
                    "A tertiary carbocation will have more electron-donating alkyl groups to disperse the positive charge on the carbocation, leading to "
                    "greater stability, thus undergoing the " + SN1 + " mechanism more readily than primary and secondary halogenoalkanes. "
                    "Thus, 2-bromopropane undergoes the " + SN1 + " mechanism more readily than bromomethane or bromoethane."))),   # user 2026-11-02: leave as is
 PART("(b)(ii)", TBL(["chloroalkane", "order of rate of hydrolysis"],
                     ["CH" + sub(3) + "(CH" + sub(2) + ")" + sub(3) + CL, "3"],
                     ["(CH" + sub(3) + ")" + sub(3) + "C" + CL, "1"],
                     ["CH" + sub(3) + "CH" + sub(2) + "CH(CH" + sub(3) + ")" + CL, "2"])),
 PART("(c)", TBL(["assumption", "predicted angle of rotation of plane-polarised light, " + i("z") + " / °", "reason for predicted angle"],
                 ["only " + SN1 + " occurs", "0", "Racemic mixture of equal amounts of " + b("X") + " and " + b("Y") + " are formed"],
                 ["only " + SN2 + " occurs", "+9.9", b("Y") + " is produced from " + b("V") + " after inversion of configuration from " + SN2])),
]

# ------------------------------------------------------------------ rulings (user, item by item)
RULED_FIXES = [   # (qn, old, new, expected count) -- wording fixes approved by the user 2026-11-02 ("apply all wording fixes")
    (6, "Biodiesel contains oxygen and require less oxygen", "Biodiesel contains oxygen and requires less oxygen", 1),
    (6, "per mole of heptadecane each while", "per mole of heptadecane while", 1),
    (6, "requires 24.5 moles each for complete combustion", "requires 24.5 moles of oxygen per mole of " + b("L") + " for complete combustion", 1),
    (6, "has less hydrogen atoms", "has fewer hydrogen atoms", 1),
    (6, "the same as the amount the plants from removed from the atmosphere when they grow",
        "the same as the amount of CO" + sub(2) + " removed from the atmosphere by plants when they grow", 1),
]

out = {}
for qn in sorted(W):
    h = '<div class="worked-solution">' + "\n".join(W[qn]) + "</div>"
    for q, old, new, n in RULED_FIXES:
        if q == qn:
            assert h.count(old) == n, (qn, old, h.count(old)); h = h.replace(old, new)
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
    assets.append({"question": qn, "slot": "ans-" + slot, "path": "%s_Q%d_ans-%s_%d.png" % (PFX, qn, slot, YEAR), "offset": seen[qn]})
(OUT / "worked_solutions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "answer_assets.json").write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "worked solutions,", sum(h.count('class="lab"') for h in out.values()), "parts,", len(assets), "answer assets")
for a in assets: print("  Q%d %-8s offset %d  %s" % (a["question"], a["slot"], a["offset"], a["path"]))

# ------------------------------------------------------------------ verification against the school's docx text
if DOCX:
    import zipfile
    from lxml import etree
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = etree.fromstring(zipfile.ZipFile(DOCX).read("word/document.xml"))
    def norm(s):
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("&nbsp;", " ").replace("–", "-").replace("−", "-").replace("’", "'").replace("‘", "'")
        return re.sub(r"[^A-Za-z0-9]", "", s).lower()
    src = norm(" ".join("".join(p.itertext()) for p in root.iter("{%s}p" % ns["w"])))
    # every typed text run of the answers must be found in the docx text (ruled fixes are checked separately)
    miss = []
    for qn, h in out.items():
        for m in re.finditer(r'<span class="ans">(.*?)</span>', h, re.S):
            t = norm(m.group(1))
            if len(t) > 12 and t not in src: miss.append((qn, re.sub(r"<[^>]+>", "", m.group(1))[:90]))
    print("verification: %d answer run(s) not found verbatim in the docx text" % len(miss))
    for q, t in miss: print("   Q%s: %s" % (q, t))
