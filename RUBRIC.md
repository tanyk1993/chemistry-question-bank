# LO classification rubric — v0.2

**Status: validated once, on one held-out paper.** Built from RI 2024 H2 P2's
diff, then tested blind on VJC 2026 JC1 WA2 (31 items) on 2026-09-19. Result
**22/31 = 71% as-stated, 26/31 = 84% as-agreed** (the two numbers are explained
below and BOTH matter), against a 58% cold baseline on RI P2 and a 70% decision
threshold. Rules 10–12 below are new, derived from WA2's misses.

Still one held-out paper. Topics absent from BOTH papers (see the last section)
remain untested.

Syllabus: **H2 9476** (2026). H1 is 8873. Exam papers are 9729 and map onto 9476.

---

## The held-out result — WA2, 2026-09-19

### Two numbers, and why both are reported

| | as stated | as agreed |
|---|---|---|
| MCQ | 7/10 | 9/10 |
| Q1 bonding / atomic structure | 5/7 | 6/7 (86%, was 33%) |
| Q2 inorganic / redox | 5/5 | 5/5 (100%, was 91%) |
| Q3 energetics / kinetics | 5/9 | 6/9 (67%, was 35%) |
| **total** | **22/31 = 71%** | **26/31 = 84%** |

**As stated** = agreement with the user's tags exactly as first given.
**As agreed** = after four items where discussion changed the ground truth:
two drifted codes in the user's table-of-specs doc (MCQ 6, MCQ 9), one
within-question dedup question (1(a)(ii)), one catalyst sub-LO (3(b)(ii)).

**The 84% carries a known bias**: contests were raised only where the classifier
disagreed, so an upheld contest can only move the number up. Report both.

They answer different questions:
- **71%** — agreement with existing data, unsupervised. Too low to auto-apply.
- **84%** — agreement after a knowledgeable reviewer engages. This is the Phase 2
  workflow, since the user *is* the ruling process.

The gap between them is an argument **for** the review UI, not against it.

**Zero topic-level errors.** Every miss was a wrong code within the right topic.
Both targeted failures moved, so Rules 1 and 6 are operative.

Residual error profile, all five as-agreed misses:

| miss | family |
|---|---|
| MCQ 2 `1(a)`+`1(b)` for `1(a)` | over-tag |
| 1(b)(iii) `13(c)` for `1(i)` | wrong code — recall vs apply, see Rule 10 |
| 3(b)(iv) `7(m)` for `7(k)` | wrong code — Rule 3 violated, see Rule 10 |
| 3(c)(ii) `6(g)(i)`+`6(g)(ii)` for `6(g)(ii)` | over-tag — Rule 6 mis-transferred, see Rule 11 |
| 3(c)(iv) `8(b)(ii)`+`8(c)(i)` for `8(b)(ii)` | over-tag |

**3 of 5 residual errors are over-tags.** This is the favourable direction for a
review workflow: deleting a spurious tag is cheaper than noticing an absent one.
The user's ruling, recorded: over-tagging is acceptable at proposal time because
the reviewer has final say and extra tags may catch aspects they missed.

The counter-cost, also recorded: an accepted spurious tag pollutes the app's LO
filter **silently**, whereas a missing tag shows as an untagged badge. Asymmetric
in the opposite direction *after* acceptance. Hence the primary/secondary split
in the output contract.

**Over-tagging is the dominant residual failure.** Rule 9 predicted it and
did not prevent it: naming a bias in prose does not suppress it. Rule 12's
mark-count cap is a mechanical guard, but retro-testing shows it catches only
1 of 3 — it is a cheap floor, not the fix.

### Calibration, measured

Confidence was **under**-stated, not over-stated. The part flagged "most likely
miss" (2(b)(ii)) was a hit; the single lowest-confidence call (3(c)(iii)) was a
hit; the stated expected range 60–75% undershot the as-agreed 84%; and the
"zero no-clean-LO is suspicious" alarm was false — WA2 genuinely has none, so
Rule 8's ~8% base rate is paper-dependent, not universal.

**Consequence for the tool:** a review UI that triages by confidence would route
correct answers to manual review. Do not gate on confidence until it is
recalibrated against more than one paper.

---

## The baseline this has to beat

A cold classification of RI 2024 H2 P2 — no rubric, just the LO catalogue —
scored roughly **58% exact match** against the user's tags across 48 parts. The
distribution matters far more than the average:

| question | topic | parts | exact |
|---|---|---|---|
| Q1 | boron: bonding, energetics | 12 | ~33% |
| Q2 | aquarium water: acids/bases, redox | 11 | **91%** |
| Q3 | organic: stereochem, multi-step synthesis | 14 | ~35% |
| Q4 | kinetics, radicals | 11 | **91%** |

**Physical chemistry classifies well. Organic and fine-grained sub-LO work does
not.** Rules 1 and 6 below target exactly those two failures. If a revised run
does not move Q1 and Q3, the rubric has failed regardless of what the average does.

---

## Rule 1 — Go to the most specific sub-LO that fits

*The single biggest systematic error.* The user's own words after Q1:

> "you seem to be glossing over the sub-LOs (e.g. 11.3a vii) where relevant"

Default to the **narrowest** code that genuinely covers the assessed chemistry.
Retreat to a group code only for one of the two reasons in Rule 2.

| part | cold guess | correct | why |
|---|---|---|---|
| 1(b)(i) | 2(b) | **2(b)(ii)** | "to be more specific" |
| 1(b)(iii) | 7(f) | **7(f)(iii)** | same |
| 1(d)(iii) | 11.3(a) | **11.3(a)(vii)** | addition reactions specifically |
| 3(b)(ii) | 11.3(n) | **11.3(n)(i)** | SN1 specifically |
| 3(c)(ii) | 11.1(a) | **11.1(a)(ii)** | same |

---

## Rule 2 — When a GROUP code is right, it is for one of two reasons

**(a) Method/example variants of one skill.** The sub-codes are different
routes to the same competence, and the question does not care which.

**(b) By ABSENCE — the method used is not among the coded sub-methods.**
4(a)(iii) deduces order from a pseudo-order log plot. The syllabus codes only
initial-rates and concentration-time graphs as sub-LOs, so the part lands at
group `8(b)` because nothing narrower exists — not because the sub-codes
collapse. Different reason, same outcome, and worth distinguishing: (b) is a
syllabus gap worth noticing, (a) is not.

Do **not** use a group code merely because choosing between sub-codes is hard.
That is Rule 1's failure wearing a disguise.

---

## Rule 3 — Tag what the ANSWER requires, not what the question mentions

The stem's surface topic is often not the assessed chemistry.

> 1(b)(iv): "the answer is that additional energy is released in condensing
> B₂O₃ and water; thus i parked it under 7a (endo/exo processes)"

> 1(d)(ii): "answer is that N is less able to delocalise its lone pair due to its
> higher electronegativity so i parked it under 2f"

Both sit in a question about boron compounds. Neither is tagged to bonding.
**Read the mark scheme before tagging when one is available** — it states what
the student must produce.

---

## Rule 4 — Mentioned vs assessed: "must the student SUPPLY it?"

The canonical pair, because the surface is identical and the answers are opposite:

- **3(a)(ii)** — stereochem question, electrophilic addition. The student must
  supply the planar carbocation intermediate to explain racemisation.
  → `11.2(e) + 11.3(l)`, mechanism tag **included**.
- **3(a)(iii)** — stereochem question, mechanism **given** in the figure. No EA
  knowledge is tested. → `11.2(d)` alone, mechanism tag **excluded**.

This cuts both ways, and the cold run erred in both directions. Dropping a
mechanism tag as "context" is wrong when the student must produce the mechanism;
keeping it is wrong when the paper hands it to them.

---

## Rule 5 — Predict vs explain are different LOs

> 1(b)(ii): "i parked as 2e cuz it's not explaining using VSEPR, rather just
> stating bond angle/shape"

"State the shape and bond angle" → `2(e)`. "Explain the shape using VSEPR" →
`2(d)`. Check which verb the question actually uses.

---

## Rule 6 — Walk the WHOLE synthetic route before tagging

*The largest single miss in the blind test, and the one that makes organic score
badly.* A multi-step scheme carries an LO **per step**, including steps that are
only implied by the reagents.

> 3(c)(i) — cold guess: `11.4(b) + 11.6(a)` (alkene and alcohol).
> Correct: `11.4(b) + 11.4(d)(iii) + 11.6(a)(ii)`.
> The scheme routes through an **arene**. Friedel–Crafts was missed entirely
> because the route was never traced; so was the ROH→RX conversion.

Procedure: list every intermediate the scheme passes through, name the
transformation between each pair, and tag each one. Do not tag from the
start and end materials.

Related, same question: **3(c)(vi)** is nucleophilic substitution (RX→alcohol)
*followed by* an alcohol test. Both are assessed → `11.6(b) + 11.5(a)(i)`.
The cold run tagged only the test.

---

## Rule 7 — Catalyst LOs follow the AGENT, not the concept

Settled across three parts in two questions:

| catalyst | LO |
|---|---|
| named enzyme or bacteria | `8(k)` |
| generic / unnamed catalyst | `8(i)(i)` |
| consumed then regenerated, all aqueous | `8(j)` homogeneous |

> 2(a)(ii): "considering that this is from bacteria, the enzyme LO (8k) is more
> appropriate"

The cold run chose between `8(i)(i)` and `8(k)` on *which mechanistic detail the
answer discusses*. Wrong axis. Choose on what the catalyst **is**.

---

## Rule 8 — "No clean LO" is a VALID result. Do not force-fit

Roughly **4 of 48 parts** (~8%) landed here. A calibrated classifier should
return no-confident-LO about that often. Two distinct sub-cases, worth
distinguishing because they mean different things:

**(a) Genuine syllabus gap — nothing fits.**
- `3(b)(iii)` ring strain. RI's own mark scheme reasons via bond-pair repulsion,
  which would suggest `2(d)`, but the real chemistry is ring strain and the
  syllabus does not code it.
- Curly-arrow *drawing* as a skill sits in the Organic preamble, not as an LO.
  Tag the mechanism the arrows depict (`11.3(n)(i)`, `11.3(k)`) and note the gap.

**(b) Under-constrained — too many things fit.**
- `4(c)(iii)`: "one possible way is redox-based… but given the number of possible
  answers, it seems not possible to cleanly park it anywhere"
- `2(b)(i)`, `2(b)(ii)`: pure graph reads. "force-fitting them into any LO is a
  hard stretch."

See handoff §6H — the app's untagged badge currently conflates these with
not-yet-tagged and with out-of-syllabus material.

---

## Rule 9 — Over-tagging is the default failure mode; under-tagging is the organic one

Let the chemistry decide the count. Physical parts are usually 1 LO; organic
parts 2–3. But note the asymmetry the blind test revealed:

- On **physical/inorganic** parts the error is over-tagging — adding a second LO
  for something merely mentioned.
- On **multi-step organic** parts the error is **under-tagging** — missing whole
  steps (Rule 6).

Do not apply a blanket "prefer fewer tags" instinct. It is right in one half of
the paper and wrong in the other.

---

## Rule 10 — Content vs OPERATION: tag what the student must DO

*New in v0.2. Generalises Rules 4 and 5, which are instances of it.*

Where two LOs cover the same chemistry at different cognitive levels, the code is
decided by the operation demanded, not by which LO's wording the stem resembles.

> **WA2 1(b)(iii)** — "first ionisation energies of the first row transition
> metals remain relatively invariant". `13(c)` says almost exactly that, and
> that is the trap. `13(c)` is **recall of the fact**. The question supplies the
> factors — *"by considering how nuclear charge and shielding effect change from
> Sc to Cu, suggest why"* — and asks the student to **derive** it. That is
> `1(i)`, explaining the factors influencing ionisation energies, applied to
> transition-metal data. → **`1(i)`**, and it would still be `1(i)` on a JC2
> paper where topic 13 is fully taught.

The stem's command verb is the tell: *state / recall* vs *suggest why / by
considering X, explain*.

Three instances of one principle, now grouped:
- Rule 4 — mentioned vs assessed ("must the student SUPPLY it?")
- Rule 5 — predict vs explain
- Rule 10 — recall vs apply

**Do not infer a rule from course position.** The tempting wrong reason here was
"topic 13 isn't taught in a JC1 WA2, so it's out of scope". That reaches the
right answer on this item and the wrong one on a JC2 paper asking the same thing.

### Rule 5, corrected

Rule 5's two verbs are **not mutually exclusive**. WA2 2(b)(ii) says "state
VSEPR theory **and use it to predict** the shape and suggest a value for the bond
angle" — three marks, and the answer supplies both the VSEPR explanation and the
predicted shape. → **`2(d)` + `2(e)`**, both.

Rule 5 distinguishes the verbs. It does not license choosing exactly one.

---

## Rule 11 — Rule 6 is ORGANIC-ONLY. Do not walk calculation steps

*New in v0.2, from a miss caused by Rule 6 itself.*

Rule 6 says walk every step of a synthetic route and tag each. That is right
because each transformation is separately examinable chemistry. **It does not
transfer to calculations.**

> **WA2 3(c)(ii)** — mass of NH₄NO₃ needed for 40 cm³ of N₂ at r.t.p.
> Cold-with-Rule-6 guess: `6(g)(i)` + `6(g)(ii)` — volume→mol is gas volumes,
> mol→mass is reacting masses, two steps, two tags.
> Correct: **`6(g)(ii)` alone.**

A multi-step calculation is **one** LO, named by the data the question hands you
(here, a gas volume). The mol→mass arithmetic is not a second competence.

Compare 2(a)(ii) in the same paper — titration volumes and concentrations, also
multi-step, also one LO (`6(g)(iii)`). And 1(a)(i): two marks, σ count and π
count, one LO (`2(c)`). Marks split *within* an LO all the time.

Scope boundary, stated plainly: **Rule 6 applies to `11.x` synthetic schemes.
Everywhere else, prefer the single LO naming the assessed skill.**

---

## Rule 12 — Tag count ≤ mark count

*New in v0.2. A mechanical guard, not a judgement.*

An LO cannot be assessed for less than one mark, so a part's tag count can never
exceed its mark allocation. A **1-mark part carries exactly one LO.**

The converse is false and the strict form "1 mark per LO" is wrong — verified
against WA2:

| part | marks | LOs | why the gap |
|---|---|---|---|
| 1(a)(i) | 2 | 1 | σ count + π count, same LO |
| 1(b)(i) | 2 | 1 | two orbital shapes, same LO |
| 1(b)(iii) | 3 | 1 | nuclear charge + shielding + conclusion, all `1(i)` |
| 1(a)(ii) | 2 | 2 | genuinely two LOs |

Marks routinely split within one LO. So this is a **cap**, not a target.

Value, measured honestly: on WA2 it would have vetoed **1 of 3** over-tags
(MCQ 2, 1 mark, 2 LOs). 3(c)(ii) had 2 marks for 2 LOs and 3(c)(iv) 2 marks for
2 LOs — both legal under the cap and both still wrong. Worth implementing because
it is free — mark allocations are printed in the paper and the extractor can
parse them — but it is a floor, not a solution.

**The per-tag form is the useful one.** Run the cap tag-by-tag and ask *which
mark does this LO earn?* An LO pinnable to a specific mark-scheme line is
**primary**; one merely consistent with the answer is **secondary**. On WA2 that
split is clean: all three residual over-tags fall to secondary (`1(b)` at MCQ 2
has one mark to give; `6(g)(i)` at 3(c)(ii) earns no mark of its own, the
mol→mass step being uncredited; `8(c)(i)` at 3(c)(iv) likewise), and **no correct
tag does** — 2(b)(ii)'s `2(d)` and `2(e)` both earn marks and both come up
primary.

---

## Output contract

For each part, return:

```json
{
  "part_label": "(c)(i)",
  "marks": 3,
  "primary":   ["11.4(b)", "11.4(d)(iii)", "11.6(a)(ii)"],
  "secondary": [],
  "confidence": "high | medium | low",
  "no_clean_lo": false,
  "no_clean_lo_reason": null,
  "reasoning": "one line — which step of the route each LO covers"
}
```

**`primary` vs `secondary` is set by Rule 12's per-tag test**, NOT by the
confidence score — confidence measured as miscalibrated on WA2 and must not be
load-bearing until it is revalidated on more papers. An LO goes in `primary`
only if a specific mark-scheme line can be named for it.

`len(primary) <= marks` is a hard invariant. Assert it; do not emit a proposal
that violates it.

The review UI renders the two lists distinctly, and accepting all of them stays
one click. This preserves the recall the user asked for while keeping spurious
tags visually separable — they pollute the app's LO filter silently once accepted.

`no_clean_lo_reason` is one of `syllabus_gap` | `under_constrained`, per Rule 8.

The one-line reasoning is not decoration: it is what makes review fast, and it is
what turns a rejected proposal into a usable training example.

---

## What this rubric has NOT been tested on

Two papers now — RI 2024 H2 P2 (JC2 prelim, 48 parts) and VJC 2026 JC1 WA2
(31 items). Coverage is still whatever those two happened to examine.

**Absent from both:** electrochemistry, equilibria (Kc/Kp, acid–base,
solubility), the whole of transition-metal chemistry as an *assessed* topic
(WA2 only brushes it), the Periodic Table trends topic, and the entire H1
syllabus. Expect genuinely new rules from the first paper covering those.

**Untested by construction:** Rule 8's no-clean-LO handling. RI P2 had ~8%,
WA2 had 0%, and the classifier emitted none on WA2 — so the *correct* behaviour
was observed but the *discriminating* behaviour never was. A paper with
force-fit temptations is needed before Rule 8 can be said to work.

**User rulings from the WA2 reveal, recorded as convention:**
- `3(c)(iv)` → `8(b)(ii)` alone.
- `3(b)(ii)` → **`8(i)(i)` + `8(i)(ii)`, both.** Initially tagged `8(i)(i)` alone
  on the ground that the answer "doesn't explicitly mention rate constant";
  flagged back because the mark scheme's third bullet reads "Rate constant and
  rate both increase" immediately after the Boltzmann argument. Ruling: tag both.
  General form — **a demanded Maxwell–Boltzmann sketch carries `8(i)(ii)` in its
  own right**, not as scaffolding for the lower-Ea argument.

**Settled 2026-09-19** — `7(c)(ii)` vs `7(f)(iii)`, raised by WA2 MCQ 6. The line
is **calculation vs term**, not whether a cycle is drawn:

- **`7(f)(iii)`** — any *calculation* using bond energies, cycle drawn or not.
  Includes one-line substitution into ΔH = ΣBE(reactants) − ΣBE(products).
- **`7(c)(ii)`** — defining or interpreting the *term* bond energy, or
  recognising bond breaking as endothermic, with no calculation.

Two supporting items: RI P2 1(b)(iii) and WA2 MCQ 6, both `7(f)(iii)`, and
neither draws a cycle. The rejected alternative — a "was a cycle constructed"
test — would have split MCQ 6 to `7(c)(ii)` and left `7(c)(ii)` and `7(f)(iii)`
competing on every energetics paper.

## A second use for the classifier: auditing existing tags

Two WA2 MCQ codes in the user's table-of-specs document were wrong (`7c(ii)` for
`7(f)(iii)`; `8b(ii)` for `8(b)(iv)` — the latter's LO text is explicitly limited
to zero/first order and to concentration-time graphs, and MCQ 9 is second order
with no graph). Both were caught because the classifier stated a *reason* that
could be checked against the LO wording; neither was findable from the code alone.

Design consequence: a proposal that **contradicts an existing tag** must be
surfaced for review, not silently dropped as a duplicate-or-conflict. And the
one-line reasoning is load-bearing, not decoration — see the output contract.
