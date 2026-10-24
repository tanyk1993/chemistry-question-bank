"""ASRJC 2026 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_asrjc26_p3_questions <extractor_out_dir> <build_dir>

Pipeline: `asrjc26_p3_prep` (strips the blue/red answer rows out of a COPY of the
school's solutions docx) -> `extract_parts` (table shape; crops stubbed because the
user snips every figure; school ASRJC, level H2, paper P3, year 2026; run against
the redacted Word PDF) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half applied
silently. What is patched, and why:

 corrections (extractor side, not here): Q1(b) and Q1(b)(iii) equilibrium arrows and
   Q4(d) forward arrow typed; the Q1(b) Kstab fraction (a MathType object, no text
   layer) typed as span.frac; Q1(b)(iv) N-arc-N ligand symbol becomes an INLINE image;
   Q2(b) / Q2(d) / Q4(b) Fig 4.2 / Fig 4.3 borderless tables collapsed to ONE snip each.
 Q1  tabs before mark badges and inside the Fig. 1.1 caption removed; the Kstab fraction
     in the search text gets a "/" so the numerator and denominator do not run together.
 Q2  (d): soft <br> -> space.
 Q3  standard-state sign in Table 3.1 -> house markup sup.pl-sym.
 school typos fixed (user, 2026-10-24): ethylenediamine, aluminium, behaviours, in a stream,
     rate of the, with a small amount, all the reactions.
 wording rulings (user, 2026-10-24b): Q3(d) comma after NaBH4; Q5(c)(i) dipoles / lone pairs;
     Q5(d) an excess of hot, a yellow precipitate.
 generic: non-breaking spaces -> spaces (Q4(d) "decomposition of\\xa0dinitrogen", "30\\xa0\\u00b0C"; Q5).
 Q5  (c): soft <br> -> space; tab / space-run before the mark badges removed.
 generic: whitespace inside inline tags, dashes inside <sup> -> U+2212, runs of spaces,
     "[Total: n]" dropped from the search text.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
PLAN = json.loads((SRC / "asset_plan.json").read_text())
LOG = []


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"
PL = '<sup class="pl-sym">⦵</sup>'

# ======================================================================= Q1
# tabs the school typed to push the mark / the caption across the page
sub(1, "transition element.\t<span", "transition element. <span")
sub(1, "<b>A</b>, <b>B</b> and <b>C</b>.  \t<span", "<b>A</b>, <b>B</b> and <b>C</b>. <span")
sub(1, "<b>\t\t\t\t\tFig. 1.1</b>", "<b>Fig. 1.1</b>")
sub(1, r"\t\t\t\t\tFig\. 1\.1", "Fig. 1.1", field="content_text", rx=True)
# the Kstab fraction: numerator / denominator in the search text
sub(1, "= [Ni(NH3)62+][Ni(H2O)62+][NH3]6\n", "= [Ni(NH3)62+] / ([Ni(H2O)62+][NH3]6)\n", field="content_text")

# ======================================================================= Q2
sub(2, r"benzene\. <br>Six", "benzene. Six", rx=True)

# ======================================================================= Q5
sub(5, r"via a <br>3-stage", "via a 3-stage", rx=True)
sub(5, r"hydrides\.\s{10,}<span", "hydrides. <span", rx=True)
sub(5, r"for the reaction\. \t<span", "for the reaction. <span", rx=True)
sub(5, r"in your answer\.\t<span", "in your answer. <span", rx=True)
sub(5, r"aldol reaction\.\t\n<div", "aldol reaction.\n<div", rx=True)
sub(5, r"intermolecular forces\. \t\n<div", "intermolecular forces.\n<div", rx=True)

# ------------------------------------------------ school typos (user: "fix typos", 2026-10-24)
# each counted in BOTH the display HTML and the search text. Grammar the user did NOT ask to change
# ("an excess", "gives yellow precipitate", comma after NaBH4, dangling "When heated") is flagged, not edited.
for qn, old, new in (
        (1, "ethylenediammine", "ethylenediamine"),
        (3, "aluminum", "aluminium"),
        (3, "behaviors", "behaviours"),
        (3, "in stream of hydrogen gas", "in a stream of hydrogen gas"),
        (4, "The rate the decomposition", "The rate of the decomposition"),
        (5, "with small amount of NaOH", "with a small amount of NaOH"),
        (5, "all the reaction involved", "all the reactions involved")):
    sub(qn, old, new)
    sub(qn, old, new, field="content_text")

# ------------------------------------------------ wording rulings (user, 2026-10-24b), html + text
for qn, old_h, new_h, old_t, new_t in (
        (3, "NaBH<sub>4</sub> are useful", "NaBH<sub>4</sub>, are useful",
            "NaBH4 are useful", "NaBH4, are useful"),
        (5, "relevant dipole and lone pair of electrons in your answer",
            "relevant dipoles and lone pairs of electrons in your answer",
            "relevant dipole and lone pair of electrons in your answer",
            "relevant dipoles and lone pairs of electrons in your answer"),
        (5, "with an excess hot concentrated", "with an excess of hot concentrated",
            "with an excess hot concentrated", "with an excess of hot concentrated"),
        (5, "<b>W</b> gives yellow precipitate", "<b>W</b> gives a yellow precipitate",
            "W gives yellow precipitate", "W gives a yellow precipitate")):
    sub(qn, old_h, new_h)
    sub(qn, old_t, new_t, field="content_text")
# left as the school wrote them (user ruled): Q3(c)(iii) "When heated with ..." (correct: LiH is what is
# heated), Q4(c) comma run, Q5(b)(ii) "while mixing", Q5(c) "bond forming".

# ------------------------------------------------ non-breaking spaces typed by the school
for qn in sorted(Q):
    n_h, n_t = Q[qn]["content_html"].count("\xa0"), Q[qn]["content_text"].count("\xa0")
    if n_h or n_t:
        Q[qn]["content_html"] = Q[qn]["content_html"].replace("\xa0", " ")
        Q[qn]["content_text"] = Q[qn]["content_text"].replace("\xa0", " ")
        LOG.append("Q%d: %d + %d non-breaking spaces -> spaces (html + text)" % (qn, n_h, n_t))

# ------------------------------------------------ the standard-state sign, house markup
for qn in Q:
    s = Q[qn]["content_html"]
    k = s.count("<sup>⦵</sup>")
    if k:
        Q[qn]["content_html"] = s.replace("<sup>⦵</sup>", PL)
        LOG.append("Q%d: %d <sup>⦵</sup> -> sup.pl-sym" % (qn, k))


# ---------------------------------------------------------------- generic tidy
def tidy(qn):
    s = Q[qn]["content_html"]
    n_ws = n_dash = n_td = n_stray = n_empty = n_exp = 0
    s, n_exp = re.subn(r"(?<=[A-Za-z0-9)])<sup>[ \t]+", "<sup>", s)

    def rep(m):
        nonlocal n_ws
        open_t, lead, body, trail, close_t = m.groups()
        if not lead and not trail:
            return m.group(0)
        n_ws += 1
        return (" " if lead else "") + open_t + body + close_t + (" " if trail else "")
    s = re.sub(r'(<(?:sup|sub|i|b|i class="el")>)([ \t]*)([^<]*?)([ \t]*)(</(?:sup|sub|i|b)>)', rep, s)
    s, n_empty = re.subn(r"<(sub|sup|i)></\1>", "", s)

    def dash(m):
        nonlocal n_dash
        if re.search(r"[-–‒]", m.group(0)):
            n_dash += 1
        return re.sub(r"[-–‒]", "−", m.group(0))
    s = re.sub(r"<sup>[^<]*</sup>", dash, s)

    def td(m):
        nonlocal n_td
        inner = m.group(2)
        o, c = len(P_OPEN.findall(inner)), inner.count(P_CLOSE)
        if o > c:
            n_td += o - c
            inner += P_CLOSE * (o - c)
        return m.group(1) + inner + "</td>"
    s = re.sub(r"(<td[^>]*>)(.*?)</td>", td, s, flags=re.S)
    out, depth, i = [], 0, 0
    for m in re.finditer(r"<p(?:\s[^>]*)?>|</p>", s):
        out.append(s[i:m.start()])
        if m.group(0) == P_CLOSE:
            if depth == 0:
                n_stray += 1
            else:
                depth -= 1
                out.append(P_CLOSE)
        else:
            depth += 1
            out.append(m.group(0))
        i = m.end()
    out.append(s[i:])
    s = "".join(out)
    s, n_tr = re.subn(r"[ \t]+</p>", "</p>", s)
    lines = s.split("\n")
    n_run = 0
    for k, ln in enumerate(lines):
        new = re.sub(r"(?<=\S)[ \t]{3,}(?=\S)", " ", ln)
        if new != ln:
            n_run += 1
            lines[k] = new
    s = "\n".join(lines)
    Q[qn]["content_html"] = s
    LOG.append("Q%d tidy: %d exponent-leading spaces, %d spaces moved out of inline tags, %d empty sub/sup, "
               "%d dash->U+2212 in sup, %d trailing spaces before </p>, %d td <p> closed, %d stray </p>, "
               "%d lines with a space run collapsed"
               % (qn, n_exp, n_ws, n_empty, n_dash, n_tr, n_td, n_stray, n_run))


for qn in sorted(Q):
    tidy(qn)

# the same minus-sign / space-run normalisation for the search text; [Total: n] dropped
for qn in sorted(Q):
    t = Q[qn]["content_text"]
    n = 0
    for pat in (r"(?<=dm)[-–‒](?=\d)", r"(?<=mol)[-–‒](?=\d)",
                r"(?<=10)[-–‒](?=\d)", r"(?<=OH)[-–‒](?=\s|$)"):
        t, k = re.subn(pat, "−", t)
        n += k
    t, nt = re.subn(r"\s*\[Total:[^\]]*\]", "", t)
    t = re.sub(r"[ \t]*\t[ \t]*", " ", t)
    t = re.sub(r"(?<=\S)[ \t]{3,}(?=\S)", " ", t)
    Q[qn]["content_text"] = t
    LOG.append("Q%d text: %d minus signs normalised, %d [Total] dropped" % (qn, n, nt))

# ---------------------------------------------------------- the asset plan
# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule);
# an INLINE asset keeps the ordinal the extractor gave it (after every block figure)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))
    for x in PLAN:
        if x["question"] == qn and x.get("inline"):
            assert 'data-asset="%s"' % x["storage_path"] in Q[qn]["content_html"], x
            assert x["ordinal"] == len(mine) + 1, x
assert len(PLAN) == 21, len(PLAN)

# user re-snipped one figure under a new filename (2026-10-24): same slot / ordinal, new storage_path
RENAMED_ASSETS = {"ASRJC_H2_P3_Q4_b_2026.png": "ASRJC_H2_P3_Q4_b_new_2026.png"}
for old, new in RENAMED_ASSETS.items():
    hit = [x for x in PLAN if x["storage_path"] == old]
    assert len(hit) == 1, old
    hit[0]["storage_path"] = new
    LOG.append("asset renamed: %s -> %s" % (old, new))

# structural checks
for qn in Q:
    h = Q[qn]["content_html"]
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert h.count("<table") == h.count("</table>") and h.count("<tr>") == h.count("</tr>"), qn
    assert h.count("<td") == h.count("</td>"), qn
    assert h.count("<div") == h.count("</div>"), "Q%d <div> unbalanced" % qn
    assert h.count("<ul") == h.count("</ul>") and h.count("<li>") == h.count("</li>"), qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]
    assert "[Total" not in h and "[Total" not in Q[qn]["content_text"], "Q%d still has a [Total] line" % qn
    assert "<br>" not in h, "Q%d still has a <br>" % qn
    assert "\t" not in h and "\xa0" not in h, "Q%d still has a tab / NBSP" % qn
    assert "<sup>o</sup>" not in h, "Q%d still has a letter-o superscript" % qn
    n_mk = len(re.findall(r'<span class="mk">', h))
    n_parts = len([p for p in Q[qn]["parts"] if p["marks"]])
    assert n_mk == n_parts, "Q%d: %d mark badges vs %d parts with marks" % (qn, n_mk, n_parts)
assert [Q[k]["marks"] for k in sorted(Q)] == [22, 14, 19, 20, 20], [Q[k]["marks"] for k in sorted(Q)]
for qn in Q:
    assert sum(p["marks"] or 0 for p in Q[qn]["parts"]) == Q[qn]["marks"], qn

# section_label is NULL for structured papers (HANDOFF SS23)
for qn in Q:
    Q[qn]["section"] = None

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets" % (len(Q), len(PLAN)))
