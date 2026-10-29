"""DHS 2026 H2 P2 (9476/02) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QP.docx -d unz
  python3 -m ingest.extract_parts unz QP_word.pdf out \
      --school DHS --level H2 --paper P2 --year 2026
  python3 -m ingest.patch_dhs26_p2_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school DHS --year 2026 --paper 2 --level H2          # (assets: see below)

Shape: SEAB 4-column grid ("table" shape, same family as DHS 2024 P2). The
cover page and the examiner-use box are skipped by the extractor. Answers are
NOT read at this stage.

LAYOUT: the cropper's landmark finder needed a DHS-2026 layout override in
parts_figures.LAYOUT_OVERRIDES (question number at x~58.6, past the default
55pt cutoff). The crops it writes are NOT used: the user snips every figure.
The asset plan below is the SNIP LIST.

FIGURES (user snips, 12): six block figures (Fig 2.1, Fig 3.1, P, Fig 5.1,
reagent A, Fig 6.1; the printed caption is typed in the stem, so the snip
carries the drawing only) and six INLINE structure snips filling the cells of
Table 4.1 (P, R, S) and Table 4.2 (three phenols/alcohol), which the extractor
had mangled (figure placeholders inside <p>…</p> across table cells).
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


def img(slot, alt, qn=4):
    return '<img data-asset="DHS_H2_P2_Q%d_%s_2026.png" alt="%s">' % (qn, slot, alt)


# ---- soft line breaks typed to wrap a sentence (removed) --------------------------
sub(1, "at <br>520 °C", "at 520 °C")
sub(2, "Fe, <br>to one decimal place", "Fe, to one decimal place")
sub(4, "sodium hydroxide, <br><b>P</b> undergoes", "sodium hydroxide, <b>P</b> undergoes")
sub(4, "phenol and <br>2–phenylethanol", "phenol and 2–phenylethanol")
sub(4, "by completing <br>Table 4.3.", "by completing Table 4.3.")
# Q6(b): "<br>An external voltage source ..." is a deliberate line break, kept.

# ---- Q2(b)(ii): dz2 (OMML sub(sup)) -> d with z squared in the subscript ------------
sub(2, '<i>d</i><sub>z</sub><sup><sub>2</sub></sup> orbital',
       '<i>d</i><sub>z<sup>2</sup></sub> orbital')
sub(2, r"in Fe<sup>3\+</sup>\.\s+\n<div class=\"fig\">",
       'in Fe<sup>3+</sup>.\n<div class="fig">', rx=True)
sub(2, r"in Fe3\+\.\s+\n\nFig\. 2\.1", "in Fe3+.\nFig. 2.1", field="content_text", rx=True)

# ---- Q4(a)(iii): Table 4.1 = a real table, three inline structure snips -------------
T41 = ('<table class="qt"><tr><td>compound</td><td>enantiomer</td>'
       '<td>angle of rotation of plane–polarised light / °</td></tr>'
       '<tr><td><b>P</b></td><td>%s</td><td>+33.8</td></tr>'
       '<tr><td><b>R</b></td><td>%s</td><td>–8.8</td></tr>'
       '<tr><td><b>S</b></td><td>%s</td><td>+8.8</td></tr></table>'
       % (img("aiii", "enantiomer of compound P: 1-bromoethylbenzene"),
          img("aiii2", "enantiomer R: 1-phenylethanol"),
          img("aiii3", "enantiomer S: 1-phenylethanol")))
s = Q[4]["content_html"]
m = re.search(r'<table class="qt"><tr><td>compound</td><td>enantiomer</td>.*?</table></p>\n', s, flags=re.S)
assert m, "Q4 Table 4.1 not found"
Q[4]["content_html"] = s[:m.start()] + T41 + "\n" + s[m.end():]
LOG.append("Q4(a)(iii): Table 4.1 rebuilt with 3 inline structure snips")

# ---- Q4(b)(i): Table 4.2 = three names over three inline structure snips ------------
T42 = ('<table class="qt"><tr><td>2–phenylethanol</td><td>phenol</td><td>4–nitrophenol</td></tr>'
       '<tr><td>%s</td><td>%s</td><td>%s</td></tr></table>'
       % (img("bi", "2-phenylethanol"), img("bi2", "phenol"), img("bi3", "4-nitrophenol")))
s = Q[4]["content_html"]
m = re.search(r'<table class="qt"><tr><td>2–phenylethanol</td>.*?</table> (<span class="mk">\[3\]</span>)</p></div>',
              s, flags=re.S)
assert m, "Q4 Table 4.2 not found"
Q[4]["content_html"] = s[:m.start()] + T42 + " " + m.group(1) + "</div>" + s[m.end():]
LOG.append("Q4(b)(i): Table 4.2 rebuilt with 3 inline structure snips")

# ---- Q3(a): the "reaction 1 ... equation ... dH < 0" line wrapped dH onto a 2nd line
#      (11 tabs + 24 spaces typed for alignment) -> short gaps (user, 2026-10-28)
sub(3, r"reaction 1[ \t]+CO\(g\)", "reaction 1    CO(g)", rx=True)
sub(3, r"CH<sub>3</sub>OH\(g\)[ ]{10,}∆", "CH<sub>3</sub>OH(g)      ∆", rx=True)
sub(3, r"reaction 1[ \t]+CO\(g\)", "reaction 1    CO(g)", field="content_text", rx=True)
sub(3, r"CH3OH\(g\)[ ]{10,}∆", "CH3OH(g)      ∆", field="content_text", rx=True)

# ---- Q4(c): Table 4.3's empty answer row needs room (user, 2026-10-28)
sub(4, "structure of <b>X</b></td></tr><tr><td></td><td></td></tr></table>",
       'structure of <b>X</b></td></tr><tr><td style="height:10em"></td>'
       '<td style="height:10em"></td></tr></table>')

# ---- Q6(a)(i): stray spaces in the half-equation row ------------------------------------
sub(6, "FePO<sub>4</sub><sup> </sup>+ Li", "FePO<sub>4</sub> + Li")
sub(6, "<td><i> E</i><sup>⦵</sup> = +0.60 V</td>", "<td><i>E</i><sup>⦵</sup> = +0.60 V</td>")

# ---- asset plan (final): block figures first, then inline, ordinals continue ----------
def A(q, slot, ordinal, part, inline=False, n_refs=1):
    return {"question": q, "part": part, "slot": slot, "ordinal": ordinal,
            "storage_path": "DHS_H2_P2_Q%d_%s_2026.png" % (q, slot),
            "n_refs": 0 if inline else n_refs, **({"inline": True} if inline else {})}


PLAN = [
    A(2, "bii", 1, "(b)(ii)"),
    A(3, "ai", 1, "(a)(i)"),
    A(4, "a", 1, "(a)"),
    A(4, "aiii", 2, "(a)(iii)", True), A(4, "aiii2", 3, "(a)(iii)", True),
    A(4, "aiii3", 4, "(a)(iii)", True),
    A(4, "bi", 5, "(b)(i)", True), A(4, "bi2", 6, "(b)(i)", True),
    A(4, "bi3", 7, "(b)(i)", True),
    A(5, "bii", 1, "(b)(ii)"),
    A(5, "c", 2, "(c)"),
    A(6, "a", 1, "(a)"),
]

# ---- checks ---------------------------------------------------------------------------------
bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count('<div class="fig">')
    nblock = len([p for p in PLAN if p["question"] == qn and not p.get("inline")])
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d block assets" % (qn, nph, nblock))
    for p in PLAN:
        if p["question"] == qn and p.get("inline") and 'data-asset="%s"' % p["storage_path"] not in h:
            bad.append("Q%d: inline %s not in the html" % (qn, p["storage_path"]))
    if "<br>" in h and qn != 6:
        bad.append("Q%d: leftover <br>" % qn)
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    ords = sorted(p["ordinal"] for p in PLAN if p["question"] == qn)
    if ords != list(range(1, len(ords) + 1)):
        bad.append("Q%d: ordinals not 1..n" % qn)
assert sum(r["marks"] for r in Q.values()) == 75
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d (%d block, %d inline)" % (
    len(Q), len(PLAN), len([p for p in PLAN if not p.get("inline")]),
    len([p for p in PLAN if p.get("inline")])))
for l in LOG:
    print("  " + l)
