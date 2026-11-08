"""MI 2026 H2 P2 (9729/02 on the cover, 4 structured, 75 marks) questions: patch the
extractor output (declared, asserted) and write the final questions.json /
asset_plan.json for gen_parts_migration.

usage:
  mkdir unz && unzip -q MI_2026_PU3_H2_P2_Student.docx -d unz
  python3 -m ingest.extract_parts unz MI_..._Student.pdf out \
      --school MI --level H2 --paper P2 --year 2026 --first-page 2
        (crops stubbed: the user snips every figure; PF.crop_all -> ([], []))
  python3 -m ingest.patch_mi26_p2_questions out build
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school MI --year 2026 --paper 2 --level H2

Shape: the plain 4-column SEAB table family; ONE body table of 87 rows with a
6-column grid (527|430|567|142|8177|977) and two row shapes ([1,1,3,1] and
[1,1,1,1,1,1]); `parts.py` reads it as is, so NO prep script is needed. The paper
is the student copy: questions only, no answers in the file.

FIGURES (7 block figures, all snipped by the user; printed captions "Graph 3.1",
"Table 4.1" ... stay typed in the stem):
  Q1(b)      the two-vessel diagram (PCl3 / PCl5 and the valve)
  Q2(b)(ii)  1,2-diaminoethane (en) structure (the paragraph that introduces
             (b)(iii) and (b)(iv) is printed after (b)(ii)'s [3]; the shared lead-in
             mover refuses a tail holding a figure, so it stays under (b)(ii))
  Q3(a)      Graph 3.1 (V_t against t)
  Q4(a)      Table 4.1: structure of procaine
  Q4(b)      Table 4.2: benzene / ethylbenzoate / benzocaine (three snips b, b2, b3)

WORDING RULINGS (user, 2026-11-08): Table 4.3 "2-position"/"3-position" with a plain
hyphen; "monobromination" throughout 4(b); "ethyl benzoate" (two words) in Table 4.2;
3(a) "The data collected are shown"; 3(a)(iii) "given that the reaction behaves as a
first-order reaction overall".
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
PLAN = json.loads((SRC / "asset_plan.json").read_text())
LOG = []

MINUS = "−"
EMSP = "&emsp;"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


# ---- figure plan (declared) ------------------------------------------------------------------
EXPECT = {1: ["b"], 2: ["bii"], 3: ["a"], 4: ["a", "b", "b2", "b3"]}
got = {}
for p in PLAN:
    got.setdefault(p["question"], []).append(p["slot"])
assert got == EXPECT, got

# ======================================================================= Q3
# (a): the equation is a tab-indented paragraph with a hand-spaced gap before the label;
# printed centred
sub(3, r"<p>\t(CH<sub>3</sub>COOCH<sub>2</sub>CH<sub>3</sub> \+ H<sub>2</sub>O → "
       r"CH<sub>3</sub>COOH \+ CH<sub>3</sub>CH<sub>2</sub>OH) {2,}----- ",
    r'<p class="c">\1' + EMSP + EMSP + "----- ", rx=True)
sub(3, r"\n\t(CH3COOCH2CH3 \+ H2O → CH3COOH \+ CH3CH2OH) {2,}-----",
    r"\n\1 -----", field="content_text", rx=True)

# ======================================================================= Q4
# Table 4.1 and Table 4.2: the figure cells came out wrapped in stray <p> ... </p> that
# straddle the cells, and each table is closed by a stray </p>. Rewritten cleanly.
FIG = '<div class="fig">figure</div>'
sub(4, r'<table class="qt"><tr><td><b>anaesthetic</b></td>.*?</table></p>',
    '<table class="qt"><tr><td><b>anaesthetic</b></td><td><b>structure of base, B</b></td>'
    '<td><b>p<i>K</i><sub>a</sub> of the conjugate acid, BH<sup>+</sup></b></td></tr>'
    '<tr><td>procaine</td><td>' + FIG + '</td><td>8.9</td></tr></table>', rx=True)
sub(4, r'<table class="qt"><tr><td><b>compound</b></td>.*?</table></p>',
    '<table class="qt"><tr><td><b>compound</b></td><td><b>structure</b></td>'
    '<td><b>relative rate of bromination</b></td></tr>'
    '<tr><td>benzene</td><td>' + FIG + '</td><td>1.0</td></tr>'
    '<tr><td>ethyl benzoate</td><td>' + FIG + '</td><td>0.0015</td></tr>'
    '<tr><td>benzocaine</td><td>' + FIG + '</td><td>4.8 × 10<sup>6</sup></td></tr></table>',
    rx=True)
# the p<i>K</i>a in the stem: the subscript a came out italic
sub(4, "p<i>K</i><i><sub>a</sub></i> value", "p<i>K</i><sub>a</sub> value")
# ---- user rulings (2026-11-08) on the held wording ----
# Table 4.3: "2-position" / "3-position" with a plain hyphen (en dash typed by the school)
sub(4, "2\u2013position", "2-position")
sub(4, "3\u2013position", "3-position")
sub(4, "2\u2013position", "2-position", field="content_text")
sub(4, "3\u2013position", "3-position", field="content_text")
# 4(b): "monobromination" everywhere (Table 4.3 lead-in had "mono-bromination")
sub(4, "mono-bromination", "monobromination")
sub(4, "mono-bromination", "monobromination", field="content_text")
# Table 4.2: "ethyl benzoate" as two words (rewritten cell above; search text here)
sub(4, "ethylbenzoate0.0015", "ethyl benzoate0.0015", field="content_text")
# 3(a): subject-verb agreement; 3(a)(iii): smoother wording
for f in ("content_html", "content_text"):
    sub(3, "The data collected is shown", "The data collected are shown", field=f)
sub(3, "given that the overall order of the reaction behaves as a first-order reaction.",
    "given that the reaction behaves as a first-order reaction overall.")
sub(3, "given that the overall order of the reaction behaves as a first-order reaction.",
    "given that the reaction behaves as a first-order reaction overall.", field="content_text")
# Table 4.4: stray leading space in the first header cell
sub(4, "<td> test</td>", "<td>test</td>")
# the search text keeps the entity of the "<" in Table 4.3
sub(4, "&lt; 1%", "< 1%", field="content_text")

# ======================================================================= generic
for qn in sorted(Q):
    h, t = Q[qn]["content_html"], Q[qn]["content_text"]
    # zero-width and non-breaking spaces typed by the school
    n = h.count("​") + t.count("​") + h.count("\xa0") + t.count("\xa0")
    h = h.replace("​", "").replace("\xa0", " ")
    t = t.replace("​", "").replace("\xa0", " ")
    # soft line breaks typed to wrap a sentence at the printed margin -> space
    h = re.sub(r"\s*<br></p>", "</p>", h)
    h = re.sub(r"[ \t]*<br>[ \t]*", " ", h)
    # a dash inside a superscript is a minus sign (charges and exponents)
    h = re.sub(r"<sup>([^<]*)</sup>",
               lambda m: "<sup>" + re.sub(r"[-–‒‑]", MINUS, m.group(1)) + "</sup>", h)
    # a negative value typed with an en dash after "=" (lattice energies)
    h = re.sub(r"(=\s*)[–-](?=\d)", "\\1" + MINUS, h)
    t = re.sub(r"(=\s*)[–-](?=\d)", "\\1" + MINUS, t)
    # runs of spaces typed to push text across the line
    h = re.sub(r"(?<=\S) {2,}(?=\S)", " ", h)
    t = re.sub(r"(?<=\S) {2,}(?=\S)", " ", t)
    t = re.sub(r"\n[ \t]+\n", "\n", t)
    # exponents typed with a dash in the search text
    t = re.sub(r"(?<=10)[–-](?=\d)", MINUS, t)
    t = re.sub(r"\b(dm|mol|min|K|g|J|cm|s)[–-](?=\d)", lambda m: m.group(1) + MINUS, t)
    Q[qn]["content_html"], Q[qn]["content_text"] = h, t
    if n:
        LOG.append("Q%d: %d zero-width / non-breaking spaces removed" % (qn, n))

# ---- checks ----------------------------------------------------------------------------------
VOID = {"br", "img", "hr"}


class Bal(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.err = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.err.append("close </%s> with stack %r" % (tag, self.stack[-3:]))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


bad = []
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
for qn, r in sorted(Q.items()):
    h, t = r["content_html"], r["content_text"]
    nph = h.count('<div class="fig">')
    if nph != len(by_q.get(qn, [])):
        bad.append("Q%d: %d placeholders for %d assets" % (qn, nph, len(by_q.get(qn, []))))
    if "<p></td>" in h or "</table></p>" in h or "<td></p>" in h or "<p></p>" in h:
        bad.append("Q%d: stray <p> around a table cell or table" % qn)
    if "[Total" in h:
        bad.append("Q%d: leftover [Total] in html" % qn)
    if not t.rstrip().endswith("[Total: %d]" % r["marks"]):
        bad.append("Q%d: content_text does not end with its [Total]" % qn)
    for ch, name in (("\t", "tab"), ("\x00", "NUL"), ("​", "zero-width space"), ("\xa0", "nbsp")):
        if ch in h or ch in t:
            bad.append("Q%d: leftover %s" % (qn, name))
    if "<br>" in h:
        bad.append("Q%d: leftover <br>" % qn)
    if "&lt;" in t:
        bad.append("Q%d: &lt; in content_text" % qn)
    if re.search(r"<sup>[^<]*[–-][^<]*</sup>", h):
        bad.append("Q%d: dash left in a superscript" % qn)
    b = Bal()
    b.feed(h)
    b.close()
    if b.stack or b.err:
        bad.append("Q%d: unbalanced tags %r %r" % (qn, b.stack, b.err[:2]))
    got_marks = sum(p["marks"] or 0 for p in r["parts"])
    if got_marks != r["marks"]:
        bad.append("Q%d: parts sum %d vs total %d" % (qn, got_marks, r["marks"]))
assert [r["marks"] for _, r in sorted(Q.items())] == [16, 16, 18, 25]
assert sum(r["marks"] for r in Q.values()) == 75
assert sorted(Q) == [1, 2, 3, 4]
assert not bad, "\n".join(bad)

PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("questions: %d | assets: %d (all block)" % (len(Q), len(PLAN)))
for l in LOG:
    print("  " + l)
