"""HCI 2026 H2 P2 (9476/02) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QP.docx -d unz
  python3 -m ingest.hci26_p2_prep unz unz_prep
  python3 -m ingest.extract_parts unz_prep QP_word.pdf out \
      --school HCI --level H2 --paper P2 --year 2026
  python3 -m ingest.patch_hci26_p2_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school HCI --year 2026 --paper 2 --level H2

Shape: SEAB 4-column grid ("table" shape) with ONE blank leading cell per row
(HCI 2024 family); `hci26_p2_prep` squares the tables up first. Answers are NOT
read at this stage.

FIGURES (user snips, 7, all block figures; printed captions "Figure 2.1/2.2"
and "peroxyethanoic acid" stay typed in the stem, so each snip carries the
drawing only, except where the labels are part of the drawing):
  Q2(d)      Figure 2.2: the three bracketed structures A, B, C (the extractor
             saw 3 ChemDraw objects + a label row; ONE snip with A/B/C labels)
  Q3(b)(iii) the empty [O2(g)] / time axes
  Q4(a)      structure of peroxyethanoic acid (label typed under it)
  Q4(b)      propene + HOCl -> A (ticked) / B (crossed arrow)
  Q4(c)      oxirane + Nu- ring-opening scheme (labels oxirane, nucleophile)
  Q4(c)(i)   phenoxide + epichlorohydrin -> [box D] -> E + Cl-
  Q5(b)(ii)  ethanal -> CH3CH2- -> alkoxide -> dilute acid -> butan-2-ol

LEAD-INS filed under the wrong part by the extractor (text printed AFTER a
part's last [n] but belonging to the next part): Q5 (b)(i)->(b)(ii),
(b)(iv)->(c), (h)->(i). Moved here (corrections.LEADIN_MOVES is not used so no
shared file is touched).
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
LOG = []


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


# ---- stray empty / space-only sub/sup/span runs ---------------------------------------
sub(2, "2+ </sup>is yellow", "2+</sup> is yellow")
sub(2, 'solid.<span class="sr"> </span>The compound', "solid. The compound")
sub(2, '<sup class="pl-sym">⦵</sup><sup> </sup>values', '<sup class="pl-sym">⦵</sup> values')
sub(3, "O<sub>3</sub>(g)<sub> </sub>→", "O<sub>3</sub>(g) →")
sub(4, "p<i>K</i><sub>a </sub>values", "p<i>K</i><sub>a</sub> values")

# ---- Q2(d): Figure 2.2 = ONE snip (three ChemDraw objects + the A/B/C label row) -------
sub(2, '<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n'
       '<p></td></tr><tr><td><b>A</b></td><td><b>B</b></td><td><b>C</b></td></tr></table></p>',
       '<div class="fig">figure</div>')
sub(2, "[Co(en)2Cl2].\nABC\nFigure 2.2", "[Co(en)2Cl2].\nFigure 2.2", field="content_text")

# ---- hand-aligned lines: keep the typed gaps (p.eqn is pre-wrap) -----------------------
sub(3, "<p>step 1         C", '<p class="eqn">step 1         C')
sub(3, "<p>step 2         C", '<p class="eqn">step 2         C')
sub(5, '<p class="c">                                Grignard reagent</p>',
       '<p class="c eqn">                                Grignard reagent</p>')

# ---- Q4(a): the name under the structure is a centred caption --------------------------
sub(4, "<p>peroxyethanoic acid</p>", '<p class="c">peroxyethanoic acid</p>')

# ---- Q5: lead-in text filed under the wrong part --------------------------------------
def move_leadin(qn, frm, to, start_marker_html, start_marker_text, to_first_html, to_first_text):
    """Move everything after `start_marker` in part `frm` (html and text) to the
    start of part `to`, ahead of its own question text."""
    h = Q[qn]["content_html"]
    a = h.index('<span class="pl">%s</span>' % frm)
    b = h.index('<span class="pl">%s</span>' % to)
    seg = h[a:b]
    k = seg.index(start_marker_html)
    tail_html = seg[k:]
    assert tail_html.endswith("</div>\n<div class=\"qpart\">"), tail_html[-60:]
    tail_html = tail_html[: -len("</div>\n<div class=\"qpart\">")]
    new_frm = seg[:k] + "</div>\n<div class=\"qpart\">"
    after = h[b:]
    lab = '<span class="pl">%s</span>' % to
    assert after.startswith(lab + " " + to_first_html), after[:80]
    new_to = lab + tail_html.rstrip() + "\n<p>" + to_first_html
    # close the <p> that now wraps the part's own first sentence: it ends at the
    # first "</p>" if the part already wraps the rest in <p>, else at the part end
    h2 = h[:a] + new_frm + new_to + after[len(lab) + 1 + len(to_first_html):]
    Q[qn]["content_html"] = h2
    LOG.append("Q%d: moved lead-in from %s to %s (%d chars html)" % (qn, frm, to, len(tail_html)))

    t = Q[qn]["content_text"]
    ta = t.index("%s " % frm)
    tb = t.index("%s %s" % (to, to_first_text), ta)
    tseg = t[ta:tb]
    tk = tseg.index(start_marker_text)
    ttail = tseg[tk:].strip()
    rest = t[tb + len(to) + 1 + len(to_first_text):]
    Q[qn]["content_text"] = (t[:ta] + tseg[:tk].rstrip() + " %s %s\n%s" % (to, ttail, to_first_text) + rest)


# (b)(i) -> (b)(ii): the Grignard background + scheme (the figure) precede "Draw the mechanism"
move_leadin(5, "(b)(i)", "(b)(ii)",
            "\n<p>Since magnesium is less electronegative",
            "\nSince magnesium is less electronegative",
            "Draw the mechanism for the reaction between ethanal",
            "Draw the mechanism for the reaction between ethanal")
# (b)(iv) -> (c): the Table 5.2 passage + the preparation steps precede "Draw the displayed formula"
move_leadin(5, "(b)(iv)", "(c)",
            "\n<p>Pentan-2-one can be converted",
            "\nPentan-2-one can be converted",
            "Draw the displayed formula of the tertiary alcohol",
            "Draw the displayed formula of the tertiary alcohol")
# (h) -> (i): the purification passage + steps 6-11 precede "Using the data in Table 5.2"
move_leadin(5, "(h)", "(i)",
            "\n<p>The preparation of organic compounds usually produces",
            "\nThe preparation of organic compounds usually produces",
            "Using the data in Table 5.2",
            "Using the data in Table 5.2")

# the moved-into parts' own first sentence was inline; it now sits in a <p>: close it
h = Q[5]["content_html"]
for first in ("Draw the mechanism for the reaction between ethanal and CH<sub>3</sub>CH<sub>2</sub>MgBr to form     butan-2-ol. \n",
              "Draw the displayed formula of the tertiary alcohol produced in this synthesis. <span class=\"mk\">[1]</span></div>",
              "Using the data in Table 5.2, explain why the ethoxyethane forms a layer above the aqueous layer. <span class=\"mk\">[1]</span></div>"):
    assert h.count("<p>" + first) == 1, first[:50]
# (b)(ii): "<p>Draw ... butan-2-ol. \n<p>Show relevant..." -> close the first <p>
sub(5, "<p>Draw the mechanism for the reaction between ethanal and CH<sub>3</sub>CH<sub>2</sub>MgBr to form     butan-2-ol. \n<p>Show",
       "<p>Draw the mechanism for the reaction between ethanal and CH<sub>3</sub>CH<sub>2</sub>MgBr to form butan-2-ol.</p>\n<p>Show")
sub(5, "<p>Draw the displayed formula of the tertiary alcohol produced in this synthesis. <span class=\"mk\">[1]</span></div>",
       "<p>Draw the displayed formula of the tertiary alcohol produced in this synthesis. <span class=\"mk\">[1]</span></p></div>")
sub(5, "<p>Using the data in Table 5.2, explain why the ethoxyethane forms a layer above the aqueous layer. <span class=\"mk\">[1]</span></div>",
       "<p>Using the data in Table 5.2, explain why the ethoxyethane forms a layer above the aqueous layer. <span class=\"mk\">[1]</span></p></div>")

# ---- Q5(l): fill-in blanks (user: keep for (l), none for (d)) (the extractor drops answer-dot runs) ----------------------
# 5(d): the "volume = cm3" answer line is left dangling once the blanks are removed
# (ruling 2026-11-01): drop it and keep the [2] on the question line.
sub(5, 'significant figures.\n<p>volume = cm<sup>3</sup> <span class="mk">[2]</span></p></div>',
    'significant figures. <span class="mk">[2]</span></div>')
sub(5, "significant figures.\nvolume = cm3 [2]", "significant figures. [2]", field="content_text")

DOTS = "…………………………"
sub(5, r"<p>From <sup>o</sup>C to <sup>o</sup>C\s+\[1\]</p>\n<p>\[Total: 25\]</p></div>",
       "<p>From %s <sup>o</sup>C to %s <sup>o</sup>C <span class=\"mk\">[1]</span></p></div>" % (DOTS, DOTS), rx=True)
sub(5, r"From oC to oC\s+\[1\]\n\[Total: 25\]",
       "From %s oC to %s oC [1]\n[Total: 25]" % (DOTS, DOTS), field="content_text", rx=True)
assert Q[5]["marks"] is None
Q[5]["marks"] = 25
for p in Q[5]["parts"]:
    if p["label"] == "(l)":
        assert p["marks"] is None
        p["marks"] = 1

# ---- asset plan (final) ----------------------------------------------------------------------
def A(q, slot, part):
    return {"question": q, "part": part, "slot": slot, "ordinal": 0,
            "storage_path": "HCI_H2_P2_Q%d_%s_2026.png" % (q, slot), "n_refs": 1}


PLAN = [A(2, "d", "(d)"), A(3, "biii", "(b)(iii)"),
        A(4, "a", "(a)"), A(4, "b", "(b)"), A(4, "c", "(c)"), A(4, "ci", "(c)(i)"),
        A(5, "bii", "(b)(ii)")]
seen = {}
for p in PLAN:
    seen[p["question"]] = seen.get(p["question"], 0) + 1
    p["ordinal"] = seen[p["question"]]

# ---- checks ----------------------------------------------------------------------------------
bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count('<div class="fig">')
    nblock = len([p for p in PLAN if p["question"] == qn])
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d block assets" % (qn, nph, nblock))
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    if "[Total" in h:
        bad.append("Q%d: leftover [Total] in html" % qn)
    if not r["content_text"].rstrip().endswith("[Total: %d]" % r["marks"]):
        bad.append("Q%d: content_text does not end with its [Total]" % qn)
    if h.count("<div") != h.count("</div>"):
        bad.append("Q%d: unbalanced div" % qn)
    if h.count("<p") - h.count("<pl") != h.count("</p>"):
        pass
    got = sum(p["marks"] or 0 for p in r["parts"])
    if got != r["marks"]:
        bad.append("Q%d: parts sum %d vs total %d" % (qn, got, r["marks"]))
def _dash(o):
    if isinstance(o, str):
        o = re.sub(r"mol dm<sup>[-\u2212]3</sup>", "mol\u00a0dm<sup>\u22123</sup>", o)   # unit never wraps
        o = re.sub(r"<tr><td></td><td></td></tr>", "", o)      # empty spacer rows (Q5 step table)
        return re.sub(r"dm<sup>-3</sup>", "dm<sup>\u22123</sup>", re.sub(r"dm-3\b", "dm\u22123", o))
    if isinstance(o, list):
        return [_dash(x) for x in o]
    if isinstance(o, dict):
        return {k: _dash(v) for k, v in o.items()}
    return o


Q = {k: _dash(v) for k, v in Q.items()}   # rulings 2026-11-01: dm-3 hyphen -> minus sign
assert sum(r["marks"] for r in Q.values()) == 75
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d (all block)" % (len(Q), len(PLAN)))
for l in LOG:
    print("  " + l)
