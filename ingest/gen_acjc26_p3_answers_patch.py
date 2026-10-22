#!/usr/bin/env python3
"""ACJC 2026 H2 P3: targeted worked_solution patch (user report 2026-10-21):
 1(d)(i) radical dot; 1(c)(ii) two captions; Q3(b) F structure on the formula's line;
 Q4 italic K and sub/superscripts on the CrO4 / Cr2O7 ions.
Each fragment pair is applied with replace() (not a whole-column overwrite) so a
later hand edit elsewhere survives; the pre-flight refuses an admin-edited row.
usage: python3 -m ingest.gen_acjc26_p3_answers_patch <old_ws.json> <new_ws.json> <dest.sql>
"""
import json
import sys
from pathlib import Path

OR = '<p><span class="ans"><b>OR</b></span></p>'
PAIRS = []   # (qnum, old, new)


def derive(old_ws, new_ws):
    cap1 = ('<p><span class="ans">(showing all three hybrid orbitals and unhybridised p orbital '
            'around N<sub>x</sub> and N<sub>y</sub>)</span></p>')
    cap2 = ('<p><span class="ans">(showing only one hybridised orbital each on N<sub>x</sub> and '
            'N<sub>y</sub>, along with unhybridised p orbital)</span></p>')
    a1 = 'Q1_ans-cii_2026.png" alt=""></p>\n' + OR
    p = [
        (1, a1, 'Q1_ans-cii_2026.png" alt=""></p>\n' + cap1 + "\n" + OR),
        (1, 'Q1_ans-cii2_2026.png" alt=""></p></div>',
            'Q1_ans-cii2_2026.png" alt=""></p>\n' + cap2 + "</div>"),
        (1, '(g) → N<sub>3</sub>(g)', '(g) → •N<sub>3</sub>(g)'),
        (3, 'Q3_ans-bF_2026.png" alt="">',
            'Q3_ans-bF_2026.png" alt="" style="display:inline;vertical-align:middle;'
            'margin:0 .15em;border:0">'),
        (4, 'K<sub>c</sub>', '<i>K</i><sub>c</sub>'),
        (4, 'K<sub>sp</sub>', '<i>K</i><sub>sp</sub>'),
        (4, '<span class="stk post"><span>2−</span><span>7</span></span>',
            '<sub>7</sub><sup>2−</sup>'),
        (4, '<span class="stk post"><span>2−</span><span>4</span></span>',
            '<sub>4</sub><sup>2−</sup>'),
    ]
    # prove the pairs turn the live (old) text into the freshly generated (new) text
    for q in "1345":
        t = old_ws[q]
        for qq, o, n in p:
            if str(qq) == q:
                assert o in t, (q, o[:50])
                t = t.replace(o, n)
        assert t == new_ws[q], "Q%s: pairs do not reproduce the regenerated text" % q
    assert old_ws["2"] == new_ws["2"]
    return p


def derive_spacing(old_ws, new_ws):
    """follow-up patch: a space between mol and dm in units (user, 2026-10-21)"""
    p = [(4, 'moldm<sup>', 'mol dm<sup>'),
         (4, 'mol<sup>\u22123</sup>dm<sup>9</sup>', 'mol<sup>\u22123</sup> dm<sup>9</sup>'),
         (5, 'moldm<sup>', 'mol dm<sup>')]
    for q in "45":
        t = old_ws[q]
        for qq, o, n in p:
            if str(qq) == q:
                assert o in t
                t = t.replace(o, n)
        assert t == new_ws[q]
    assert all(old_ws[q] == new_ws[q] for q in "123")
    return p


def lit(s):
    assert "$ws$" not in s
    return "$ws$" + s + "$ws$"


def main(old_json, new_json, dest, spacing=False):
    old = json.loads(Path(old_json).read_text(encoding="utf-8"))
    new = json.loads(Path(new_json).read_text(encoding="utf-8"))
    pairs = derive_spacing(old, new) if spacing else derive(old, new)
    qs = sorted({q for q, _, _ in pairs})
    W = "p.school = 'ACJC' AND p.year = 2026 AND p.paper_number = 3 AND p.level = 'H2'"
    L = (["-- ACJC 2026 H2 P3 : worked-solution patch 2 (a space between mol and dm in units).",
          "-- COMMIT copy, no dry run.", ""] if spacing else
         ["-- ACJC 2026 H2 P3 : worked-solution patch (radical dot, 1(c)(ii) captions,",
         "-- Q3(b) F inline, Q4 italic K and ion scripts). COMMIT copy, no dry run.",
         "-- Targeted replace() only; run AFTER the answers SQL. A rerun is a safe no-op refusal.",
         ]) + ["", "BEGIN;", "", "DO $preflight$", "DECLARE n int; r record; ws text;", "BEGIN"]
    for q in qs:
        L += ["  SELECT q.worked_solution, q.edited_at IS NOT NULL AS edited INTO r",
              "    FROM questions q JOIN papers p ON p.id = q.paper_id",
              "   WHERE %s AND q.type = 'structured' AND q.question_number = %d;" % (W, q),
              "  IF NOT FOUND OR r.worked_solution IS NULL THEN",
              "    RAISE EXCEPTION 'Q%d: no worked_solution to patch (run the answers SQL first)';" % q,
              "  END IF;",
              "  IF r.edited THEN",
              "    RAISE EXCEPTION 'Q%d was hand-edited in the admin; patch it by hand';" % q,
              "  END IF;"]
        for qq, o, nw in pairs:
            if qq == q:
                L += ["  IF strpos(r.worked_solution, %s) = 0 THEN" % lit(o),
                      "    RAISE EXCEPTION 'Q%d: expected fragment not found (already patched or changed): %%', left(%s, 60);" % (q, lit(o)),
                      "  END IF;"]
    L += ["END", "$preflight$;", ""]
    for q in qs:
        expr = "q.worked_solution"
        for qq, o, nw in pairs:
            if qq == q:
                expr = "replace(%s,\n         %s,\n         %s)" % (expr, lit(o), lit(nw))
        L += ["UPDATE questions q SET worked_solution =", "       " + expr,
              "  FROM papers p", " WHERE p.id = q.paper_id AND %s" % W,
              "   AND q.type = 'structured' AND q.question_number = %d" % q,
              "   AND q.edited_at IS NULL",
              " RETURNING q.question_number, length(q.worked_solution) AS html_chars;", ""]
    L += ["DO $post$", "DECLARE bad int;", "BEGIN"]
    for q in qs:
        for qq, o, nw in pairs:
            if qq == q:
                L += ["  SELECT count(*) INTO bad FROM questions q JOIN papers p ON p.id = q.paper_id",
                      "   WHERE %s AND q.type = 'structured' AND q.question_number = %d" % (W, q),
                      "     AND (strpos(q.worked_solution, %s) > 0 OR strpos(q.worked_solution, %s) = 0);" % (lit(o), lit(nw)),
                      "  IF bad <> 0 THEN RAISE EXCEPTION 'Q%d: patch did not apply cleanly'; END IF;" % q]
    L += ["END", "$post$;", "", "COMMIT;", "",
          "-- VERIFICATION -- run SEPARATELY, after COMMIT:",
          "-- select q.question_number, length(q.worked_solution) from questions q join papers p on p.id=q.paper_id",
          "--  where %s and q.question_number in (%s) order by 1;" % (W, ", ".join(map(str, qs)))]
    Path(dest).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", dest, "-", len(pairs), "fragment pairs over Q", qs)


if __name__ == "__main__":
    main(*sys.argv[1:4], spacing=len(sys.argv) > 4 and sys.argv[4] == "--spacing")
