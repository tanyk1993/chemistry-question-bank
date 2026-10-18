#!/usr/bin/env python3
"""Question-type tag loader (structured papers, part level), generic.

Reads one or more review-sheet CSVs (columns: school, year, paper, qn, part,
proposed_type, second_type, ...), validates every row, and writes two SQL files:

    question_type_tags_DRYRUN.sql   (ends in ROLLBACK)
    question_type_tags_COMMIT.sql   (identical, ends in COMMIT)

Rows: one `primary` per part, plus one `second` row where second_type is set, plus
one more `second` row (type code data_analysis_novel, "Data analysis & novel contexts")
where the OPTIONAL column data_analysis_novel is Y. Blank or N = no row; anything else
(e.g. "?") is refused, so every part must be decided before loading. Sheets without the
column behave exactly as before. The whole-question Data-based flag is NOT loaded here
(see gen_databased_migration.py).

The SQL is ONE DO block plus a final summary SELECT: no temp tables, because the
Supabase SQL editor commits per statement. Questions are found by
(school, year, paper, question number); types by code. No ids are hard-coded.
All counts are computed from the CSVs; nothing is hard-coded to a batch.

Usage:
    python3 -I gen_question_type_tags.py OUTDIR SHEET.csv [SHEET2.csv ...]
        [--school HCI --year 2024 --paper 3]   # filter rows (all given must match)
        [--level H2]                           # papers.level, default H2
        [--lo-match N]                         # require exactly N parts whose label
                                               # exists in question_los (omit to skip)
        [--bare-labels RI:2024:2]              # papers whose DB labels drop the
                                               # question number, "(a)(i)" not "1(a)(i)"
                                               # (repeatable; default RI:2024:2)

Run AFTER the paper's LO-tags SQL and after the question-types step-2 migration
(type codes + question_question_types.role). Refuses a second run.
"""
import argparse, csv, os, re, sys, collections

TYPE_CODES = {
    "Reaction mechanisms": "mechanisms",
    "Reagents & conditions": "reagents_conditions",
    "Synthesis / synthetic route": "synthesis_and_functional_group_transformations",
    "Distinguishing tests": "distinguishing_tests",
    "Structure elucidation / deduction": "structure_elucidation",
    "Reactivity (organic)": "reactivity",
    "Trends & properties: explain (inorganic)": "inorganic_trends",
    "Reactions & observations (inorganic)": "inorganic_reactions_observations",
    "Identify or deduce a species (inorganic)": "inorganic_identify",
    "Explain / predict": "explain_predict",
    "Calculations": "calculation",
    "State / define / terminology": "state_define",
    "Equations & expressions": "equations_expressions",
    "Draw structure, diagram or product": "draw_structure",
    "Sketch graph + data processing": "sketch_graph",
}
DAN_CODE = "data_analysis_novel"   # written from the optional CSV column data_analysis_novel (Y)


def die(title, items):
    print(f"REFUSING TO GENERATE: {title} ({len(items)})")
    for i in items[:60]:
        print("   ", i)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("sheets", nargs="+")
    ap.add_argument("--school"); ap.add_argument("--year", type=int); ap.add_argument("--paper", type=int)
    ap.add_argument("--level", default="H2")
    ap.add_argument("--lo-match", type=int)
    ap.add_argument("--bare-labels", action="append", default=["RI:2024:2"])
    a = ap.parse_args()
    bare = {tuple(x.split(":")) for x in a.bare_labels}

    rows = []
    for p in a.sheets:
        with open(p, newline="", encoding="utf-8-sig") as f:
            rows += list(csv.DictReader(f))

    bad, loads, seen = [], [], collections.Counter()
    for r in rows:
        school, year, paper, qn = r["school"].strip(), int(r["year"]), int(r["paper"]), int(r["qn"])
        if a.school and school != a.school: continue
        if a.year and year != a.year: continue
        if a.paper and paper != a.paper: continue
        part = r["part"].strip()
        desc = f"{school} {year} P{paper} {part}"
        if not part.startswith(str(qn)):
            bad.append(f"{desc}: part label does not start with its qn column {qn}"); continue
        label = re.sub(r"^\d+", "", part) if (school, str(year), str(paper)) in bare else part
        if "'" in label or "%" in label:
            bad.append(f"{desc}: label has a quote or percent sign"); continue
        prim, sec = r["proposed_type"].strip(), r["second_type"].strip()
        if prim not in TYPE_CODES: bad.append(f"{desc}: unknown proposed_type {prim!r}"); continue
        if sec and sec not in TYPE_CODES: bad.append(f"{desc}: unknown second_type {sec!r}"); continue
        if sec == prim: bad.append(f"{desc}: second_type equals the primary"); continue
        dan = (r.get("data_analysis_novel") or "").strip().upper()
        if dan not in ("", "Y", "N"): bad.append(f"{desc}: data_analysis_novel must be Y, N or blank, got {dan!r}"); continue
        seen[(school, year, paper, qn, label)] += 1
        loads.append((school, year, paper, qn, label, TYPE_CODES[prim], "primary"))
        if sec: loads.append((school, year, paper, qn, label, TYPE_CODES[sec], "second"))
        if dan == "Y": loads.append((school, year, paper, qn, label, DAN_CODE, "second"))
    if bad: die("rows that do not validate", bad)
    if not loads: die("no rows selected", [])
    dups = [f"{k} x{n}" for k, n in seen.items() if n > 1]
    if dups: die("the same (question, part) appears twice", dups)

    n_p = sum(1 for x in loads if x[6] == "primary"); n_s = len(loads) - n_p
    n_q = len({x[:4] for x in loads}); n_parts = len(seen)
    codes = sorted({x[5] for x in loads})
    print(f"rows: primary={n_p} second={n_s} total={len(loads)} | questions={n_q} | parts={n_parts} | type codes={len(codes)}")

    values = ",\n".join("      ('%s',%d,%d,%d,'%s','%s','%s')" % x for x in loads)
    qvalues = ",\n".join("      ('%s',%d,%d,%d)" % k for k in sorted({x[:4] for x in loads}))
    lo_check = ""
    if a.lo_match is not None:
        lo_check = f"""
  SELECT count(*) INTO n FROM (SELECT DISTINCT q.id, l.part_label FROM _L l
    JOIN public.papers p ON p.school=l.school AND p.year=l.year AND p.paper_number=l.paper AND p.level='{a.level}'
    JOIN public.questions q ON q.paper_id=p.id AND q.question_number::text=l.qn::text AND q.type='structured'
    JOIN public.question_los ql ON ql.question_id=q.id AND ql.part_label=l.part_label) m;
  IF n <> {a.lo_match} THEN
    RAISE EXCEPTION 'pre-flight: % part labels match question_los, expected {a.lo_match}', n;
  END IF;"""

    # _L is a CTE-free inline relation: each statement below re-embeds the VALUES via a
    # DO-local approach: we materialise it once inside the DO block as a temp table
    # that lives and dies inside the same statement? Not possible; so embed as a view-like
    # subquery text.
    L = f"(VALUES\n{values}\n    ) AS _L(school,year,paper,qn,part_label,type_code,role)"
    body = TEMPLATE
    subs = {"@@L@@": L, "@@N_P@@": str(n_p), "@@N_S@@": str(n_s), "@@N_TOTAL@@": str(len(loads)),
            "@@N_Q@@": str(n_q), "@@N_PARTS@@": str(n_parts), "@@N_CODES@@": str(len(codes)),
            "@@CODES@@": ", ".join("'%s'" % c for c in codes), "@@LEVEL@@": a.level,
            "@@LO_CHECK@@": lo_check.replace("_L l", "@@L@@ l")}
    # expand twice (LO_CHECK contains @@L@@)
    for _ in range(2):
        for k, v in subs.items(): body = body.replace(k, v)
    # the VALUES alias syntax needs the table alias after the list: normalise "_L l" usages
    body = body.replace(") AS _L(school,year,paper,qn,part_label,type_code,role) l",
                        ") AS l(school,year,paper,qn,part_label,type_code,role)")
    os.makedirs(a.outdir, exist_ok=True)
    for name, hdr, end in (("DRYRUN", HDR_DRY, "ROLLBACK;"), ("COMMIT", HDR_COM, "COMMIT;")):
        t = body.replace("@@HEADER@@", hdr).replace("@@END@@", end)
        assert "@@" not in t and "%%" not in t
        path = os.path.join(a.outdir, f"question_type_tags_{name}.sql")
        open(path, "w", encoding="utf-8", newline="\n").write(t)
        print("wrote", path)


HDR_DRY = "-- DRY RUN: ends in ROLLBACK. The Supabase editor may not honour ROLLBACK: treat as live. Use the _COMMIT copy to load."
HDR_COM = "-- COMMIT COPY: ends in COMMIT. WRITES to the database. Run once only; the pre-flight refuses a second run."

TEMPLATE = """-- Question-type tags, structured papers, part level: @@N_P@@ primary + @@N_S@@ second = @@N_TOTAL@@ rows, @@N_Q@@ questions.
@@HEADER@@
-- One DO block, no temp tables (the Supabase editor commits per statement).
-- Needs the question-type step 2 (type codes + question_question_types.role) and the
-- paper's LO tags. Pre-flight refuses unless: role column exists; all @@N_CODES@@ type codes
-- exist; every question resolves to exactly one structured question; none already has a
-- part-level type tag (a second run is refused); and any --lo-match count agrees.
-- The whole-question Data-based flag is NOT written here.

BEGIN;

DO $qt$
DECLARE n int; pre int;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public'
      AND table_name='question_question_types' AND column_name='role') THEN
    RAISE EXCEPTION 'pre-flight: question_question_types.role is missing (run step 2 first)';
  END IF;

  SELECT count(*) INTO n FROM public.question_types WHERE code IN (@@CODES@@);
  IF n <> @@N_CODES@@ THEN RAISE EXCEPTION 'pre-flight: found % of @@N_CODES@@ type codes', n; END IF;

  SELECT count(*) INTO n FROM (SELECT DISTINCT q.id FROM @@L@@ l
    JOIN public.papers p ON p.school=l.school AND p.year=l.year AND p.paper_number=l.paper AND p.level='@@LEVEL@@'
    JOIN public.questions q ON q.paper_id=p.id AND q.question_number::text=l.qn::text AND q.type='structured') k;
  IF n <> @@N_Q@@ THEN RAISE EXCEPTION 'pre-flight: only % of @@N_Q@@ questions resolve to a structured question', n; END IF;

  SELECT count(*) INTO n FROM public.question_question_types t WHERE t.part_label IS NOT NULL
    AND t.question_id IN (SELECT q.id FROM @@L@@ l
      JOIN public.papers p ON p.school=l.school AND p.year=l.year AND p.paper_number=l.paper AND p.level='@@LEVEL@@'
      JOIN public.questions q ON q.paper_id=p.id AND q.question_number::text=l.qn::text AND q.type='structured');
  IF n <> 0 THEN RAISE EXCEPTION 'pre-flight: already has % part-level type tag(s); refusing a second run', n; END IF;
@@LO_CHECK@@

  SELECT count(*) INTO pre FROM public.question_question_types;

  INSERT INTO public.question_question_types (question_id, type_id, part_label, role)
  SELECT q.id, ty.id, l.part_label, l.role FROM @@L@@ l
    JOIN public.papers p ON p.school=l.school AND p.year=l.year AND p.paper_number=l.paper AND p.level='@@LEVEL@@'
    JOIN public.questions q ON q.paper_id=p.id AND q.question_number::text=l.qn::text AND q.type='structured'
    JOIN public.question_types ty ON ty.code=l.type_code;

  SELECT count(*) INTO n FROM public.question_question_types;
  IF n <> pre + @@N_TOTAL@@ THEN RAISE EXCEPTION 'post-check: inserted % rows, expected @@N_TOTAL@@', n - pre; END IF;

  SELECT count(*) INTO n FROM public.question_question_types s WHERE s.role='second'
     AND s.part_label IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.question_question_types p
       WHERE p.question_id=s.question_id AND p.part_label=s.part_label AND p.role='primary');
  IF n <> 0 THEN RAISE EXCEPTION 'post-check: % second row(s) with no primary on the same part', n; END IF;

  SELECT count(*) INTO n FROM (SELECT question_id, part_label FROM public.question_question_types
     WHERE role='primary' AND part_label IS NOT NULL GROUP BY 1,2 HAVING count(*)>1) d;
  IF n <> 0 THEN RAISE EXCEPTION 'post-check: % part(s) with more than one primary', n; END IF;
END
$qt$;

SELECT ty.name, t.role, count(*) AS parts
  FROM public.question_question_types t JOIN public.question_types ty ON ty.id=t.type_id
 WHERE t.part_label IS NOT NULL
 GROUP BY ty.name, t.role ORDER BY t.role, count(*) DESC;

@@END@@
"""

if __name__ == "__main__":
    main()
