#!/usr/bin/env python3
"""Emit the guarded SQL that flags ONE structured question as Data-based /
contextual: a `question_question_types` row with part_label NULL and the type
looked up by code 'data-based' (what index.html's isDbq() reads).

Usage:
  python3 -m ingest.gen_databased_migration OUTDIR --school HCI --year 2024 \
      --paper 2 --level H2 --qn 5

Writes <OUTDIR>/<SCHOOL>_<year>_<level>_P<paper>_Q<qn>_databased_COMMIT.sql and
..._DRYRUN.sql (the Supabase editor ignores ROLLBACK, so ship both and treat
every file as live). Pre-flight refuses: not exactly one such question, no
single 'data-based' type row, or the flag already present (a rerun).
Built for HCI 2024 H2 P2 (2026-10-14) from the DHS P2 pattern; scratch-tested.
"""
import argparse, os

BODY = """DO $pre$
DECLARE n int; t int;
BEGIN
  SELECT count(*) INTO n FROM questions q JOIN papers p ON p.id=q.paper_id
   WHERE p.school='{s}' AND p.year={y} AND p.paper_number={p} AND p.level='{l}' AND q.type='structured' AND q.question_number={q};
  IF n <> 1 THEN RAISE EXCEPTION 'expected exactly 1 {s} {y} {l} P{p} Q{q}, found %', n; END IF;
  SELECT count(*) INTO t FROM question_types WHERE code='data-based';
  IF t <> 1 THEN RAISE EXCEPTION 'expected exactly 1 question_types row with code data-based, found %', t; END IF;
  SELECT count(*) INTO n FROM question_question_types x JOIN questions q ON q.id=x.question_id JOIN papers p ON p.id=q.paper_id
   WHERE p.school='{s}' AND p.year={y} AND p.paper_number={p} AND p.level='{l}' AND q.type='structured' AND q.question_number={q}
     AND x.part_label IS NULL AND x.type_id=(SELECT id FROM question_types WHERE code='data-based');
  IF n <> 0 THEN RAISE EXCEPTION 'Q{q} already has a Data-based flag'; END IF;
END $pre$;

INSERT INTO question_question_types (question_id, type_id, part_label)
SELECT q.id, (SELECT id FROM question_types WHERE code='data-based'), NULL
  FROM questions q JOIN papers p ON p.id=q.paper_id
 WHERE p.school='{s}' AND p.year={y} AND p.paper_number={p} AND p.level='{l}' AND q.type='structured' AND q.question_number={q}
RETURNING question_id, type_id, part_label;
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--school", required=True); ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--paper", type=int, required=True); ap.add_argument("--level", default="H2")
    ap.add_argument("--qn", type=int, required=True)
    a = ap.parse_args()
    body = BODY.format(s=a.school, y=a.year, p=a.paper, l=a.level, q=a.qn)
    assert "%%" not in body
    stem = f"{a.school}_{a.year}_{a.level}_P{a.paper}_Q{a.qn}_databased"
    os.makedirs(a.outdir, exist_ok=True)
    for name, end in (("COMMIT", "COMMIT;"), ("DRYRUN", "ROLLBACK;")):
        with open(os.path.join(a.outdir, f"{stem}_{name}.sql"), "w") as f:
            f.write(f"-- {a.school} {a.year} {a.level} P{a.paper}: flag Q{a.qn} as Data-based / contextual (part_label NULL). {name}.\nBEGIN;\n\n{body}\n{end}\n")
        print("wrote", f"{stem}_{name}.sql")

if __name__ == "__main__":
    main()
