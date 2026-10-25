"""A Level 2024 H2 P2: content patch for the live questions (layout fix).
  * each part's first paragraph is bare, so its text shares the label's line (was <p>, a block);
  * values bound to their units with &nbsp; (e.g. 93&nbsp;°C).
Guarded (handoff SS33.5): per question, the live content_html (CR stripped: the SQL editor turns LF into CRLF)
must hash to the OLD build (patch it) or the NEW build (skip it); anything else = hand-edited, refuse.
usage: python3 -m ingest.patch_alevel_p2_layout <old_dir> <new_dir> <dest.sql>"""
import hashlib, json, sys
from pathlib import Path
TAG = "$ap$"
def lit(s):
    assert TAG not in s; return TAG + s + TAG
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
old = {r["question_number"]: r for r in json.loads((Path(sys.argv[1]) / "questions.json").read_text())}
new = {r["question_number"]: r for r in json.loads((Path(sys.argv[2]) / "questions.json").read_text())}
assert old.keys() == new.keys()
L = ["-- A Level 2024 H2 P2: layout patch (part text on the label's line; value + unit kept together)",
     "-- Guarded, safe to re-run (an already-patched question is skipped). Updates content_html (+ content_text) only.",
     "DO $patch$", "DECLARE pid uuid; qid uuid; cur text; n int; done int := 0; skipped int := 0;",
     "        v record;", "BEGIN",
     "  SELECT count(*) INTO n FROM papers WHERE school = 'A Level' AND year = 2024 AND paper_number = 2 AND level = 'H2';",
     "  IF n <> 1 THEN RAISE EXCEPTION 'A Level 2024 H2 P2: expected 1 paper row, found %', n; END IF;",
     "  SELECT id INTO pid FROM papers WHERE school = 'A Level' AND year = 2024 AND paper_number = 2 AND level = 'H2';",
     "  FOR v IN SELECT * FROM (VALUES"]
vals = []
for qn in sorted(new):
    vals.append("    (%d, '%s', '%s', %s, %s)" % (qn, md5(old[qn]["content_html"]), md5(new[qn]["content_html"]),
                                                 lit(new[qn]["content_html"]), lit(new[qn]["content_text"])))
L.append(",\n".join(vals))
L += ["  ) AS t(qn, old_md5, new_md5, html, txt) LOOP",
      "    SELECT count(*) INTO n FROM questions WHERE paper_id = pid AND question_number = v.qn AND type = 'structured';",
      "    IF n <> 1 THEN RAISE EXCEPTION 'Q%: expected 1 row, found %', v.qn, n; END IF;",
      "    SELECT id, content_html INTO qid, cur FROM questions WHERE paper_id = pid AND question_number = v.qn AND type = 'structured';",
      "    IF md5(replace(cur, E'\\r', '')) = v.new_md5 THEN skipped := skipped + 1;",
      "    ELSIF md5(replace(cur, E'\\r', '')) = v.old_md5 THEN",
      "      UPDATE questions SET content_html = v.html, content_text = v.txt WHERE id = qid;",
      "      done := done + 1;",
      "    ELSE RAISE EXCEPTION 'Q%: live content_html is neither the original nor the patched text (edited by hand?) -- refusing', v.qn;",
      "    END IF;",
      "  END LOOP;",
      "  IF done + skipped <> " + str(len(new)) + " THEN RAISE EXCEPTION 'patched %, skipped %, expected " + str(len(new)) + "', done, skipped; END IF;",
      "  RAISE NOTICE 'A Level 2024 H2 P2 layout patch: % patched, % already new', done, skipped;",
      "END", "$patch$;", "",
      "-- verification: expect 6 rows, every lead_inline = true, every has_nbsp = true except Q2 (no units)",
      "select q.question_number, q.content_html !~ 'class=\"pl\">[^<]*</span> <p' as lead_inline,",
      "       q.content_html like '%&nbsp;%' as has_nbsp, length(q.content_html) as html_chars",
      "  from questions q join papers p on p.id = q.paper_id",
      " where p.school = 'A Level' and p.year = 2024 and p.paper_number = 2 and p.level = 'H2'",
      " order by q.question_number;"]
sql = "\n".join(L) + "\n"
assert "%%" not in sql
Path(sys.argv[3]).write_text(sql, encoding="utf-8"); print("wrote", sys.argv[3])
