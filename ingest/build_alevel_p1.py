"""Hand transcription of A Level (SEAB) 9729/01 Oct/Nov 2024 -> questions.json + asset_plan.json
(scan-only paper: no docx, so no extractor; same output contract as extract_questions).
Run from the repo root:  python3 <this file> <outdir>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, ".")
from ingest.render_questions import _strip_tags

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
FIG = '<div class="fig">figure</div>'
M = "−"                       # minus
DB = '<p class="qstem">Use of the data booklet is relevant to this question.</p>'
def p(s): return '<p class="qstem">%s</p>' % s
def c(s): return '<p class="c">%s</p>' % s
def ol(*items): return '<ol class="stmts">%s</ol>' % "".join("<li>%s</li>" % i for i in items)
def sub(s): return "<sub>%s</sub>" % s
def sup(s): return "<sup>%s</sup>" % s
CL = '<i class="el">l</i>'
K = "<i>K</i>"
MDM = "mol dm" + sup(M + "3")

Q = {}   # qn -> dict(stem=[blocks], opts={L: html or [cells]}, hdr=None|[cells], fig_opts=False)
def q(n, stem, opts=None, hdr=None, fig_opts=False):
    Q[n] = dict(stem=stem, opts=opts or {}, hdr=hdr, fig_opts=fig_opts)

q(1, [p("Cation X has the same number of neutrons as protons."),
      p("Cation X and an atom of neon have the same number of electrons."),
      p("What is cation X?")],
  {"A": sup("16")+"O"+sup("2"+M), "B": sup("19")+"F"+sup(M),
   "C": sup("23")+"Na"+sup("+"), "D": sup("24")+"Mg"+sup("2+")})
q(2, [p("Which statements about the bond energy of single covalent bonds are always correct?"),
      ol("A longer covalent bond results in a greater bond energy.",
         "A larger nuclear charge on the bonded atoms results in a greater bond energy.",
         "A greater attraction between the shared pair of electrons and the nuclei of the bonded atoms results in a greater bond energy.")],
  {"A": "1 and 3", "B": "1 only", "C": "2 and 3", "D": "3 only"})
q(3, [p("The boiling points of H"+sub(2)+"O, H"+sub(2)+"S and H"+sub(2)+"Se are different. H"+sub(2)+"S has the lowest boiling point."),
      p("Which statements are correct?"),
      ol("H"+sub(2)+"S has a lower boiling point than H"+sub(2)+"Se because H"+sub(2)+"S molecules have weaker permanent dipole-permanent dipole forces of attraction.",
         "H"+sub(2)+"O molecules experience weaker temporary dipole-induced dipole forces of attraction than H"+sub(2)+"Se molecules.",
         "H"+sub(2)+"O molecules experience stronger permanent dipole-permanent dipole forces of attraction than H"+sub(2)+"S molecules.")],
  {"A": "1, 2 and 3", "B": "1 and 2 only", "C": "2 and 3 only", "D": "3 only"})
q(4, [p("The zwitterion of aminoethanoic acid is shown."), FIG,
      p("What are the bond angles x, y and z in this structure?")],
  {"A": ["90°", "90°", "120°"], "B": ["104°", "90°", "117°"],
   "C": ["104°", "109°", "120°"], "D": ["109°", "109°", "120°"]},
  hdr=["x", "y", "z"])
q(5, [p("Consider the atoms of the Period 3 elements from Na to Ar."),
      p("What is the total number of single unpaired electrons in the valence shells of these eight elements?")],
  {"A": "8", "B": "10", "C": "12", "D": "14"})
q(6, [DB, p("The percentage composition by mass of some compounds is given."),
      p("In which compound does silicon, phosphorus or sulfur show its highest possible oxidation state?")],
  {"A": "A chloride of phosphorus contains 77.5% by mass of chlorine.",
   "B": "An oxide of silicon contains 53.2% by mass of oxygen.",
   "C": "An oxide of phosphorus contains 43.6% by mass of oxygen.",
   "D": "An oxide of sulfur contains 49.9% by mass of oxygen."})
q(7, [p("The relative abundances of all the isotopes present in a sample of nickel are shown."), FIG,
      p("What is the relative atomic mass of nickel calculated from these data?")],
  {"A": "58.8", "B": "59.8", "C": "59.9", "D": "61.0"})
q(8, [p("Many metallic elements form peroxides, containing the O"+sub(2)+sup("2"+M)+" ion, as well as oxides."),
      p("Which compound has the least negative value for lattice energy?")],
  {"A": "calcium oxide", "B": "calcium peroxide", "C": "potassium oxide", "D": "potassium peroxide"})
q(9, [p("The decomposition of SOC"+"<i class=\"el\">l</i>"+sub(2)+" is a first-order reaction. After 24 hours at a certain temperature, the concentration of SOC"+CL+sub(2)+" decreases from 0.016 "+MDM+" to 0.002 "+MDM+"."),
      p("At this temperature, how long would it take for the concentration of SOC"+CL+sub(2)+" to decrease from 0.016 "+MDM+" to 0.001 "+MDM+"?")],
  {"A": "8 hours", "B": "25.7 hours", "C": "32 hours", "D": "48 hours"})
q(10, [p("Reactants P and Q are involved in a chemical reaction."),
       p("In an experiment involving a large excess of Q, the graph of [P] against time has a constant half-life."),
       p("In further experiments, the rate of reaction is measured using different initial concentrations of Q. The results are shown."),
       '<table class="qt"><tr><td>[P] / %s</td><td>[Q] / %s</td><td>initial rate / mol dm%s s%s</td></tr>'
       '<tr><td>0.0200</td><td>0.0250</td><td>4.76 × 10%s</td></tr>'
       '<tr><td>0.0200</td><td>0.0600</td><td>2.74 × 10%s</td></tr></table>'
       % (MDM, MDM, sup(M+"3"), sup(M+"1"), sup(M+"4"), sup(M+"3")),
       p("What is the numerical value of the rate constant?")],
  {"A": "0.762", "B": "0.952", "C": "38.1", "D": "47.6"})
q(11, [p("A Boltzmann distribution for a sample of a reacting gas at a constant temperature, <i>T</i> °C, is shown."),
       p("The activation energy, <i>E</i>"+sub("A")+", for the reaction is marked."),
       p("The temperature of the sample of gas is decreased to (<i>T</i>"+M+"50) °C."),
       p("Which point could show the intercept of the new Boltzmann distribution curve with the value of the activation energy of the reaction at <i>T</i>"+M+"50 °C?"),
       FIG], {"A": "", "B": "", "C": "", "D": ""})
q(12, [p("Iron is a suitable catalyst for the industrial synthesis of ammonia."),
       p("Consider the two statements."),
       ol("Iron is a good catalyst for this reaction because it donates its 3d electrons to form stronger bonds with the reacting molecules compared to those bonds within the reacting molecules.",
          "Iron is a good catalyst for this reaction because it forms more than one stable oxidation state."),
       p("Which statements are correct?")],
  {"A": "Neither statement is correct.", "B": "Statement 1 only is correct.",
   "C": "Statement 2 only is correct.", "D": "Both statements are correct."})
q(13, [p("0.010 mol H"+sub(2)+"(g) and 0.010 mol CO"+sub(2)+"(g) are mixed in a 1.00 dm"+sup(3)+" vessel at 700 K."),
       c("H"+sub(2)+"(g) + CO"+sub(2)+"(g) ⇌ H"+sub(2)+"O(g) + CO(g)"),
       p("At 700 K, "+K+sub("c")+" = 0.123."),
       p("What is the concentration of H"+sub(2)+"(g) at equilibrium?")],
  {"A": "0.0011 "+MDM, "B": "0.0026 "+MDM, "C": "0.0074 "+MDM, "D": "0.0089 "+MDM})
q(14, [DB, p("Which graph shows the correct trends when the electronegativity of each of the elements Mg, A"+CL+", Si and P is plotted against its atomic radius?"), FIG],
  {"A": "", "B": "", "C": "", "D": ""}, fig_opts=True)
q(15, [p("The compounds listed are formed from their elements."),
       p("For the formation of which compound does the reducing agent undergo a greater change in the magnitude of the oxidation number than the oxidising agent?")],
  {"A": "magnesium chloride", "B": "magnesium sulfide", "C": "sodium bromide", "D": "sodium oxide"})
q(16, [DB, p("In a titration experiment, 50.0 cm"+sup(3)+" of 0.100 "+MDM+" aqueous sodium hydroxide is slowly added to 25.0 cm"+sup(3)+" of 0.150 "+MDM+" aqueous ethanoic acid."),
       p("The pH of the reaction mixture is measured throughout the experiment and a graph of pH against volume of aqueous sodium hydroxide added is plotted."),
       p("Part of the titration curve is shown."), FIG,
       p("Consider the two statements."),
       ol("The pH at the end of the experiment will be 13.0.",
          "The pH when half of the acid has been neutralised will be the p"+K+sub("a")+" of the acid.")],
  {"A": "Both statements are correct.", "B": "Neither statement is correct.",
   "C": "Statement 1 only is correct.", "D": "Statement 2 only is correct."})
q(17, [p("A buffer solution is made by adding 25.0 cm"+sup(3)+" of 0.15 "+MDM+" C"+sub(2)+"H"+sub(5)+"CO"+sub(2)+"H to 10.0 cm"+sup(3)+" of 0.20 "+MDM+" KOH."),
       p(K+sub("a")+" of C"+sub(2)+"H"+sub(5)+"CO"+sub(2)+"H = 1.35 × 10"+sup(M+"5")+" "+MDM),
       p("What is the pH of the buffer solution?")],
  {"A": "4.60", "B": "4.81", "C": "4.93", "D": "5.14"})
q(18, [p("C"+sub(2)+"H"+sub(5)+"MgBr is an example of a Grignard reagent. It behaves as if it contains the C"+sub(2)+"H"+sub(5)+sup(M)+" ion."),
       p("3-ethylpentan-3-ol is produced when C"+sub(2)+"H"+sub(5)+"MgBr is added to pentan-3-one, followed by the addition of aqueous acid."),
       p("Which statement about the behaviour of C"+sub(2)+"H"+sub(5)+sup(M)+" ions in this reaction is correct?")],
  {"A": "C"+sub(2)+"H"+sub(5)+sup(M)+" ions behave as electrophiles.",
   "B": "C"+sub(2)+"H"+sub(5)+sup(M)+" ions behave as Arrhenius bases.",
   "C": "C"+sub(2)+"H"+sub(5)+sup(M)+" ions behave as Brønsted–Lowry bases.",
   "D": "C"+sub(2)+"H"+sub(5)+sup(M)+" ions behave as Lewis bases."})
q(19, [p("β-selinene, C"+sub(15)+"H"+sub(24)+", can be isolated from plant material."), FIG, c("β-selinene"),
       p("When β-selinene reacts completely with HBr, the product mixture contains different compounds, all with the same molecular formula."),
       p("Optical isomers should <b>not</b> be considered when answering this question."),
       p("Which row identifies the molecular formula of the products and the number of these products that are tertiary bromoalkanes?")],
  {"A": ["C"+sub(15)+"H"+sub(24)+"Br"+sub(2), "2"], "B": ["C"+sub(15)+"H"+sub(24)+"Br"+sub(2), "3"],
   "C": ["C"+sub(15)+"H"+sub(26)+"Br"+sub(2), "2"], "D": ["C"+sub(15)+"H"+sub(26)+"Br"+sub(2), "3"]},
  hdr=["molecular formula of the products", "number of products that are tertiary bromoalkanes"])
q(20, [p("When propene, CH"+sub(3)+"CH=CH"+sub(2)+", reacts with hydrogen bromide, the main product is 2-bromopropane."),
       p("Very little 1-bromopropane is produced."),
       p("Which factors contribute to this result?"),
       ol("The methyl group has an electron-donating effect.", "The methyl group has a steric effect.",
          "The methyl group has an electron-withdrawing effect.")],
  {"A": "1 and 2", "B": "1 only", "C": "2 and 3", "D": "3 only"})
q(21, [DB, p("Compound Y, C"+sub(7)+"H"+sub(7)+"NO"+sub(2)+", reacts with Br"+sub(2)+"(aq) at room temperature to produce C"+sub(7)+"H"+sub(4)+"NO"+sub(2)+"Br"+sub(3)+"."),
       p("What is the structural formula of Y?"), FIG],
  {"A": "", "B": "", "C": "", "D": ""}, fig_opts=True)
q(22, [p("Which reaction will form (CH"+sub(3)+")"+sub(2)+"CHCH"+sub(2)+"CO"+sub(2)+"H?")],
  {"A": "2-methylbutan-1-ol with concentrated sulfuric acid",
   "B": "3-methylbutan-2-ol with acidified MnO"+sub(4)+sup(M),
   "C": "2-methylpropanenitrile with dilute sodium hydroxide",
   "D": "3-methylbutan-1-ol with acidified Cr"+sub(2)+"O"+sub(7)+sup("2"+M)})
q(23, [p("Which statement is correct?")],
  {"A": "Ethanol has a larger p"+K+sub("a")+" value than phenol because the ethoxide ion is more stable than the phenoxide ion.",
   "B": "Ethanol has a smaller p"+K+sub("a")+" value than water because of the electron-donating effect of the ethyl group in the ethoxide ion.",
   "C": "Phenol has a larger "+K+sub("a")+" value than water because a lone pair of electrons on the oxygen atom is drawn into the delocalised electron ring system.",
   "D": "Phenol has a smaller "+K+sub("a")+" value than ethanol because it is a stronger acid than ethanol."})
q(24, [p("Propanone reacts with lithium aluminium hydride."),
       p("Propene does <b>not</b> react with lithium aluminium hydride."),
       p("Which statements are correct?"),
       ol("In propanone, the C=O bond has a permanent dipole which allows the carbon atom to be attacked by a nucleophile.",
          "When propene undergoes addition reactions, it reacts with a nucleophile in the first step.",
          "Lithium aluminium hydride reduces propanone to propanoic acid.")],
  {"A": "1 and 2", "B": "1 only", "C": "2 and 3", "D": "3 only"})
q(25, [p("Dimethyl formamide is a colourless liquid that is hydrolysed by aqueous sodium hydroxide."), FIG, c("dimethyl formamide"),
       p("What are the products of this hydrolysis reaction?")],
  {"A": "CH"+sub(3)+"CO"+sub(2)+"H and CH"+sub(3)+"NH"+sub(2),
   "B": "CH"+sub(3)+"CO"+sub(2)+sup(M)+"Na"+sup("+")+" and CH"+sub(3)+"NH"+sub(2),
   "C": "HCO"+sub(2)+"H and (CH"+sub(3)+")"+sub(2)+"NH",
   "D": "HCO"+sub(2)+sup(M)+"Na"+sup("+")+" and (CH"+sub(3)+")"+sub(2)+"NH"})
q(26, [p("A sample of H"+sub(2)+"NCH"+sub(2)+"COOH is dissolved in water. The pH of the solution is increased by adding an excess of hydroxide ions."),
       p("Which type of organic species increases in concentration as a result?")],
  {"A": "anion", "B": "cation", "C": "molecule", "D": "zwitterion"})
q(27, [DB, p("Copper plating is one application of electrolysis."),
       p("A current of 5.00 A was passed through CuSO"+sub(4)+"(aq) for 20.0 minutes."),
       p("What is the maximum mass of copper that could be produced at the cathode?")],
  {"A": "0.0329 g", "B": "0.902 g", "C": "1.97 g", "D": "3.95 g"})
q(28, [DB, p("A student noted the relevant standard electrode potentials and correctly deduced that bubbling O"+sub(2)+"(g) through an acidic solution of HBr(aq) should oxidise it to Br"+sub(2)+"(aq)."),
       p("On bubbling air through an acidic solution of HBr(aq) in a test-tube, the student observed no effect."),
       p("What could be reasons for this?"),
       ol("The oxygen pressure was smaller than 1.0 atmospheres.", "The activation energy for the reaction is high.",
          "The Br"+sup(M)+"(aq) concentration is much larger than 1.0 "+MDM+".")],
  {"A": "1, 2 and 3", "B": "1 and 2 only", "C": "2 only", "D": "3 only"})
q(29, [DB, p("The 3d orbitals of the transition metal ions shown are split into two different energy levels in their octahedral complexes."),
       p("Assume the electrons occupy <b>all</b> the 3d orbitals singly before pairing up."),
       p("Which row shows the number of electrons in the higher energy 3d orbitals when this splitting occurs?")],
  {"A": ["manganese(II)", "1"], "B": ["iron(III)", "3"], "C": ["nickel(II)", "2"], "D": ["copper(I)", "0"]},
  hdr=["ion", "number of electrons"])
q(30, [DB, p("An excess of sulfur dioxide, SO"+sub(2)+", is bubbled into a warm solution containing VO"+sub(2)+sup("+")+" ions in acid conditions."),
       p("What will be the final oxidation state of vanadium?")],
  {"A": "+2", "B": "+3", "C": "+4", "D": "+5"})

def strip(h): return _strip_tags(h.replace(FIG, " "))
rows, plan = [], []
STEM_FIG = {4, 7, 11, 16, 19, 25}
for n in sorted(Q):
    d = Q[n]; parts = list(d["stem"])
    if d["fig_opts"]:
        pass                                   # stem already ends in the ONE option-grid placeholder
    elif d["opts"] and not all(v == "" for v in d["opts"].values()):
        trs = []
        if d["hdr"]:
            trs.append('<tr><td class="ol"></td>%s</tr>' % "".join("<td>%s</td>" % h for h in d["hdr"]))
        for L in "ABCD":
            v = d["opts"][L]; cells = v if isinstance(v, list) else [v]
            trs.append('<tr><td class="ol">%s</td>%s</tr>' % (L, "".join("<td>%s</td>" % x for x in cells)))
        parts.append('<table class="opts-table">%s</table>' % "".join(trs))
    html = "\n".join(parts)
    bits = [strip("\n".join(d["stem"]))]
    if d["hdr"]: bits.append(" | ".join(strip(h) for h in d["hdr"]))
    for L in "ABCD":
        v = d["opts"][L]; val = " | ".join(strip(x) for x in (v if isinstance(v, list) else [v]) if strip(x))
        bits.append("%s %s" % (L, val) if val else L)
    txt = re.sub(r"\s+", " ", " ".join(b for b in bits if b)).strip()
    ojs = {}
    for L in "ABCD":
        v = d["opts"][L]; t = " | ".join(strip(x) for x in (v if isinstance(v, list) else [v]) if strip(x))
        if not t and d["fig_opts"]: t = "[structure %s]" % L
        ojs[L] = t
    rows.append({"question_number": n, "content_html": html, "content_text": txt, "options": ojs})
    # asset plan: stem figures first (slot stem1), then ONE option grid (slots A-D)
    o = 1
    if n in STEM_FIG:
        plan.append({"question": n, "kind": "block", "slot": "stem1", "ordinal": o,
                     "storage_path": "SEAB_H2_P1_Q%d_stem1_2024.png" % n}); o += 1
    if d["fig_opts"]:
        for L in "ABCD":
            plan.append({"question": n, "kind": "option", "slot": L, "ordinal": o,
                         "storage_path": "SEAB_H2_P1_Q%d_%s_2024.png" % (n, L)}); o += 1
(OUT / "questions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "asset_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "questions,", len(plan), "assets")
# sanity: placeholder counts must equal block+grid assets per question
for r in rows:
    nfig = r["content_html"].count('class="fig"')
    nblk = sum(1 for a in plan if a["question"] == r["question_number"] and a["kind"] == "block")
    ngrid = 1 if any(a["question"] == r["question_number"] and a["kind"] == "option" for a in plan) else 0
    assert nfig == nblk + ngrid, (r["question_number"], nfig, nblk, ngrid)
print("placeholder/asset counts agree")
