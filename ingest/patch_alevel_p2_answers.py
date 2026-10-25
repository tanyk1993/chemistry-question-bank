"""A Level 2024 H2 P2: guarded content patch for worked_solution (answers stage, after the answers SQL).
Only the questions whose worked solution differs between the OLD and NEW builds are patched.
Guard (handoff SS33.5): per question, the live worked_solution (CR stripped: the SQL editor turns LF into CRLF)
must hash to the OLD build (patch it) or the NEW build (skip it); anything else = hand-edited / not loaded, refuse.
usage: python3 -m ingest.patch_alevel_p2_answers <old_dir[,old_dir2,...]> <new_dir> <dest.sql>
(several OLD builds = the question may be live in any earlier delivered state; all are patched)"""
import hashlib, json, sys
from pathlib import Path
TAG = "$ap$"
def lit(s):
    assert TAG not in s; return TAG + s + TAG
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
olds = [json.loads((Path(d) / "worked_solutions.json").read_text(encoding="utf-8")) for d in sys.argv[1].split(",")]
new = json.loads((Path(sys.argv[2]) / "worked_solutions.json").read_text(encoding="utf-8"))
assert all(o.keys() == new.keys() for o in olds)
chg = sorted((int(k) for k in new if any(o[k] != new[k] for o in olds)))
assert chg, "nothing changed"
L = ["-- A Level 2024 H2 P2: answers patch (worked_solution of Q%s)" % ", Q".join(map(str, chg)),
     "-- Guarded, safe to re-run (an already-patched question is skipped). Updates worked_solution only.",
     "DO $patch$", "DECLARE pid uuid; qid uuid; cur text; n int; done int := 0; skipped int := 0;",
     "        v record;", "BEGIN",
     "  SELECT count(*) INTO n FROM papers WHERE school = 'A Level' AND year = 2024 AND paper_number = 2 AND level = 'H2';",
     "  IF n <> 1 THEN RAISE EXCEPTION 'A Level 2024 H2 P2: expected 1 paper row, found %', n; END IF;",
     "  SELECT id INTO pid FROM papers WHERE school = 'A Level' AND year = 2024 AND paper_number = 2 AND level = 'H2';",
     "  FOR v IN SELECT * FROM (VALUES"]
L.append(",\n".join("    (%d, ARRAY[%s], '%s', %s)" % (q, ", ".join("'%s'" % md5(o[str(q)]) for o in olds), md5(new[str(q)]), lit(new[str(q)])) for q in chg))
L += ["  ) AS t(qn, old_md5s, new_md5, ws) LOOP",
      "    SELECT count(*) INTO n FROM questions WHERE paper_id = pid AND question_number = v.qn AND type = 'structured';",
      "    IF n <> 1 THEN RAISE EXCEPTION 'Q%: expected 1 row, found %', v.qn, n; END IF;",
      "    SELECT id, worked_solution INTO qid, cur FROM questions WHERE paper_id = pid AND question_number = v.qn AND type = 'structured';",
      "    IF cur IS NULL THEN RAISE EXCEPTION 'Q%: worked_solution is empty -- run the answers SQL first', v.qn; END IF;",
      "    IF md5(replace(cur, E'\\r', '')) = v.new_md5 THEN skipped := skipped + 1;",
      "    ELSIF md5(replace(cur, E'\\r', '')) = ANY (v.old_md5s) THEN",
      "      UPDATE questions SET worked_solution = v.ws WHERE id = qid;",
      "      done := done + 1;",
      "    ELSE RAISE EXCEPTION 'Q%: live worked_solution is neither the original nor the patched text (edited by hand?) -- refusing', v.qn;",
      "    END IF;",
      "  END LOOP;",
      "  IF done + skipped <> %d THEN RAISE EXCEPTION 'patched %%, skipped %%, expected %d', done, skipped; END IF;" % (len(chg), len(chg)),
      "  RAISE NOTICE 'patched %, skipped %', done, skipped;",
      "END",
      "$patch$;", "",
      "-- Verification (run separately): select question_number, length(worked_solution) from questions q join papers p on p.id = q.paper_id",
      "--  where p.school = 'A Level' and p.year = 2024 and p.paper_number = 2 and p.level = 'H2' and q.question_number in (%s) order by 1;" % ", ".join(map(str, chg))]
sql = "\n".join(L) + "\n"
assert "%%" not in sql
Path(sys.argv[3]).write_text(sql, encoding="utf-8"); print("wrote", sys.argv[3], "- questions", chg)
