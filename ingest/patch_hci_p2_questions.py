"""HCI 2024 H2 P2 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_hci_p2_questions <extractor_out_dir> <build_dir>

Pipeline: `hci_p2_prep` (square up the tables) -> `extract_parts` (crops
stubbed: the user snips every figure) -> THIS script -> gen_parts_migration.

Every `sub()` asserts its match count, so a changed extractor cannot be half
applied silently. What is patched, and why:

 generic (all questions)
   - whitespace sitting INSIDE <sup>/<sub>/<i>/<b> moved outside
   - whitespace-only `span.sr` runs removed
   - en dash INSIDE <sup> -> U+2212 (charges, exponents); en dashes elsewhere
     are bond dashes (RO-OR, CF2-CF2) and stay
   - unbalanced <p> inside a table cell closed; a stray </p> with no open <p>
     removed (the extractor's multi-paragraph-cell quirk)
 Q1  [3] and [Total: 6] were plain paragraphs, so the part had no marks
 Q2  stage letters A-D laid out with &emsp; instead of runs of spaces; Fig. 2.3
     is ONE user snip (the three Type 1/2/3 structures with their labels)
 Q4  the school typed (d)(i) and (d)(ii) in the LETTER column, so the parser
     filed them as one part "(i)": split them, rename the Fig. 4.2 asset slot
 Q5  Word auto-numbered lists (Outline A/B, the procedure) lost their numbers:
     rebuilt as ol.stmts; (vii) was swallowed into (vi) because its label cell
     also holds the y-axis label text box ("current / A"): split, Fig. 5.3 is
     ONE user snip owned by (c)(vii)
 soft <br> typed to wrap a sentence became a space (Q1(b)(ii), Q3(b)(ii),
 Q4(c)(ii), Q5(b)(i)); the two <br> that stay are Q2(d)'s A/B/C stage list.
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


# ---------------------------------------------------------------- generic tidy
P_OPEN = re.compile(r"<p(?:\s[^>]*)?>")
P_CLOSE = "</p>"


def tidy(qn):
    s = Q[qn]["content_html"]
    n_ws = n_sr = n_dash = n_td = n_stray = 0
    # 1. whitespace inside inline tags -> outside
    def rep(m):
        nonlocal n_ws
        open_t, lead, body, trail, close_t = m.groups()
        if not lead and not trail:
            return m.group(0)
        n_ws += 1
        return (" " if lead else "") + open_t + body + close_t + (" " if trail else "")
    s = re.sub(r'(<(?:sup|sub|i|b|i class="el")>)(\s*)([^<]*?)(\s*)(</(?:sup|sub|i|b)>)', rep, s)
    # 2. whitespace-only span.sr (optionally inside <i>)
    s, n = re.subn(r'(?:<i>)?<span class="sr">(\s*)</span>(?:</i>)?', r"\1", s)
    n_sr += n
    # 3. en dash inside <sup> -> U+2212
    def dash(m):
        nonlocal n_dash
        if "–" in m.group(0):
            n_dash += 1
        return m.group(0).replace("–", "−")
    s = re.sub(r"<sup>[^<]*</sup>", dash, s)
    # 4. unbalanced <p> in a table cell
    def td(m):
        nonlocal n_td
        inner = m.group(2)
        o, c = len(P_OPEN.findall(inner)), inner.count(P_CLOSE)
        if o > c:
            n_td += o - c
            inner += P_CLOSE * (o - c)
        return m.group(1) + inner + "</td>"
    s = re.sub(r"(<td[^>]*>)(.*?)</td>", td, s, flags=re.S)
    # 5. a </p> with no open <p>
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
    s, n_tr = re.subn(r"[ \t]+</p>", "</p>", s)      # the half-equation lines
    Q[qn]["content_html"] = s
    LOG.append("Q%d tidy (%d trailing spaces before </p>): %d spaces moved out of inline tags, %d sr runs, %d en dash->U+2212 in sup, "
               "%d td <p> closed, %d stray </p> removed" % (qn, n_tr, n_ws, n_sr, n_dash, n_td, n_stray))


for qn in sorted(Q):
    tidy(qn)

# the text field: en dash on a charge or exponent -> U+2212 (the same places)
for qn, pat, cnt in (
    (4, r"(?<=[2O])–(?=[ .,])", None),          # CO2-  /  O2CCHCHCO2-
    (4, r"(?<=\s)–(?=O2C)", None),              # -O2CCHCHCO2-
    (4, r"(?<=10)–(?=3)", None),                # 10-3
    (4, r"(?<=dm)–(?=3)", None),                # dm-3
):
    s = Q[qn]["content_text"]
    n = len(re.findall(pat, s))
    Q[qn]["content_text"] = re.sub(pat, "−", s)
    LOG.append("Q%d content_text: %d x en dash -> U+2212 (%s)" % (qn, n, pat))

# ------------------------------------------------------------- soft <br>
sub(1, "elements <br>(Na to Ar)", "elements (Na to Ar)")
sub(3, "concentration of <br>2-bromopropane", "concentration of 2-bromopropane")
sub(4, ". <br>Calculate the concentration of C", ". Calculate the concentration of C")
sub(5, "given that its density is <br>1.2 g cm", "given that its density is 1.2 g cm")

# ------------------------------------------------------------------ Q1
sub(1, '<p>[3]</p>\n<p>[Total: 6]</p></div>', '<p><span class="mk">[3]</span></p></div>')
sub(1, "[3]\n[Total: 6]", "[3]", field="content_text")
Q[1]["marks"] = 6
for p in Q[1]["parts"]:
    if p["label"] == "(b)(ii)":
        assert p["marks"] is None
        p["marks"] = 3
assert sum(p["marks"] or 0 for p in Q[1]["parts"]) == 6

# ------------------------------------------------------------------ Q2
# stage letters: runs of spaces -> em space; A, B, C one tight block
sub(2, r"(<b>[A-D]</b>)\s{3,}", r"\1&emsp;", rx=True, count=4)
sub(2, "</p>\n<p><b>C</b>&emsp;", "<br><b>C</b>&emsp;")
# school grammar (user ruling 2026-10-14): PFAS is plural
for _f in ("content_html", "content_text"):
    sub(2, "(PFAS) is a group of compounds", "(PFAS) are a group of compounds", field=_f)
    sub(2, "Due to its persistence in the environment, it has been dubbed",
        "Due to their persistence in the environment, they have been dubbed", field=_f)
# Fig. 2.3 = ONE snip with its Type 1/2/3 labels; drop the three placeholders
# and the typed labels
sub(2, '<div class="fig">figure</div>\n<p>Type 1</p>\n<div class="fig">figure</div>\n<p>Type 2</p>\n'
       '<div class="fig">figure</div>\n<p>Type 3</p>\n<p class="c"><b>Fig. 2.3</b>',
       '<div class="fig">figure</div>\n<p class="c"><b>Fig. 2.3</b>')

# ------------------------------------------------------------------ Q4
for old, new in ((r"(\s{3,})(p<i>K</i><sub>a,[12]</sub>)", r"&emsp;&emsp;\2"),):
    sub(4, old, new, rx=True, count=2)
# (d)(i) / (d)(ii): the school's labels sit in the letter column
sub(4, '<div class="qpart"><span class="pl">(i)</span> Give the reagents',
       '<div class="qpart"><span class="pl">(d)(i)</span> Give the reagents')
sub(4, '<p>step 3: <span class="mk">[3]</span></p>\n<p>The Heck reaction is the palladium-catalysed',
       '<p>step 3: <span class="mk">[3]</span></p></div>\n<div class="qpart"><span class="pl">(d)(ii)</span> '
       'The Heck reaction is the palladium-catalysed')
sub(4, "alkene as the major product.</p>", "alkene as the major product.")  # its <p> became the label's inline text
sub(4, "(i) Give the reagents and conditions for steps 1 to 3.", "(d)(i) Give the reagents and conditions for steps 1 to 3.",
    field="content_text")
sub(4, "[3]\nThe Heck reaction is", "[3] (d)(ii) The Heck reaction is", field="content_text")
parts4 = Q[4]["parts"]
assert parts4[-1] == {"label": "(i)", "marks": 1}, parts4[-1]
parts4[-1:] = [{"label": "(d)(i)", "marks": 3}, {"label": "(d)(ii)", "marks": 1}]
assert sum(p["marks"] or 0 for p in parts4) == Q[4]["marks"] == 15

# ------------------------------------------------------------------ Q5
def ol(items):
    return '<ol class="stmts">' + "".join("<li>%s</li>" % t for t in items) + "</ol>"


def listify(qn, texts, label):
    """Turn consecutive <p>text</p> lines (each exactly one of `texts`) into
    one ol.stmts, in the same position."""
    block = "\n".join("<p>%s</p>" % t for t in texts)
    sub(qn, block, ol(texts))
    LOG.append("Q%d: %s -> ol.stmts (%d items)" % (qn, label, len(texts)))


listify(5, ["Transfer v cm<sup>3</sup> of 37% w/w HC<i class=\"el\">l</i> into a 250 cm<sup>3</sup> volumetric flask. "
            "(volume v was calculated in <b>(b)(ii)</b>)",
            "Slowly add deionised water into the volumetric flask and top up to the mark."], "Outline A")
listify(5, ["Transfer 150 cm<sup>3</sup> of deionised water into a 250 cm<sup>3</sup> volumetric flask.",
            "Slowly add v cm<sup>3</sup> of 37% w/w HC<i class=\"el\">l</i> into the volumetric flask.",
            "Top up to the mark with deionised water."], "Outline B")
listify(5, ["Transfer 2.50 cm<sup>3</sup> of 0.100 mol dm<sup>−3</sup> HC<i class=\"el\">l</i>(aq) into a 250 cm<sup>3</sup> beaker.",
            "Add 97.5 cm<sup>3</sup> of 0.2 mol dm<sup>−3</sup> NaC<i class=\"el\">l</i>(aq) into the beaker. "
            "(NaC<i class=\"el\">l</i>(aq) is added, instead of deionised water, to maintain sufficient electrical "
            "conductivity of the electrolyte.)",
            "Construct the electrolytic setup in Fig. 5.1.",
            "Close the switch and start a stopwatch at the same time. Record the pH of the electrolyte indicated by "
            "the pH meter and the current indicated by the ammeter at regular time intervals.",
            "Open the switch at time t = 240 s, which is beyond the equivalence point of the titration."], "procedure")

# (c)(vi) / (c)(vii): split at "Student Z"; Fig. 5.3 is ONE snip owned by (c)(vii)
sub(5, '<span class="mk">[1]</span></p>\n<p>Student Z also carried out',
       '<span class="mk">[1]</span></p></div>\n<div class="qpart"><span class="pl">(c)(vii)</span> '
       'Student Z also carried out')
# (the y-axis label "current / A" sits beside the graph in the revised export: part of the snip)
sub(5, 'on the same axes.</p>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n',
       'on the same axes.\n<div class="fig">figure</div>\n')
# the user snipped BOTH axes of Figs 5.2 / 5.3 (a half-typed axis would look odd): drop the typed "time / s"
sub(5, '<p class="c">time / s</p>\n', '', count=2)
sub(5, "\ntime / s\nFig. 5.2", "\nFig. 5.2", field="content_text")
sub(5, "\ntime / s\nFig. 5.3", "\nFig. 5.3", field="content_text")
# Fig. 5.2 is drawn as two pieces (grid + curve): ONE snip
sub(5, '<div class="fig">figure</div>\n<div class="fig">figure</div>\n<p class="c"><b>Fig. 5.2</b>',
       '<div class="fig">figure</div>\n<p class="c"><b>Fig. 5.2</b>')
sub(5, "Student Z also carried out student X’s experiment", "(c)(vii) Student Z also carried out student X’s experiment",
    field="content_text")
parts5 = Q[5]["parts"]
assert parts5[-1] == {"label": "(c)(vi)", "marks": 2}, parts5[-1]
parts5[-1:] = [{"label": "(c)(vi)", "marks": 1}, {"label": "(c)(vii)", "marks": 2}]
assert sum(p["marks"] or 0 for p in parts5) == Q[5]["marks"] == 23

# ---------------------------------------------------------- the asset plan
def drop(qn, slot):
    global PLAN
    n = len(PLAN)
    PLAN = [x for x in PLAN if not (x["question"] == qn and x["slot"] == slot)]
    assert len(PLAN) == n - 1, (qn, slot)
    LOG.append("asset plan: dropped Q%d %s" % (qn, slot))


def get(qn, slot):
    hits = [x for x in PLAN if x["question"] == qn and x["slot"] == slot]
    assert len(hits) == 1, (qn, slot)
    return hits[0]


drop(2, "diii3")
drop(2, "diii4")
for slot in ("diii", "diii2"):
    get(2, slot)["n_refs"] = 1                      # one snip each (Fig. 2.2, Fig. 2.3)
a = get(4, "i")                                      # Fig. 4.2 belongs to (d)(ii)
a.update(part="(d)(ii)", slot="dii", storage_path="HCI_H2_P2_Q4_dii_2024.png")
drop(5, "c3")
drop(5, "cvi2")
drop(5, "cvi3")
a = get(5, "cvi")                                    # Fig. 5.3, owned by (c)(vii)
a.update(part="(c)(vii)", slot="cvii", n_refs=1, storage_path="HCI_H2_P2_Q5_cvii_2024.png")

# ordinals: 1-based per question, in DOM order (HANDOFF SS7: the highest-consequence rule)
for qn in sorted(Q):
    mine = [x for x in PLAN if x["question"] == qn and not x.get("inline")]
    for k, x in enumerate(mine, 1):
        x["ordinal"] = k
    n_ph = Q[qn]["content_html"].count('<div class="fig">')
    assert n_ph == len(mine), "Q%d: %d placeholders vs %d assets" % (qn, n_ph, len(mine))

# no leftover soft <br> except Q2(d)'s stage list (two); no stray </p>
assert sum(Q[qn]["content_html"].count("<br>") for qn in Q) == 2, \
    {qn: Q[qn]["content_html"].count("<br>") for qn in Q}
for qn in Q:
    h = Q[qn]["content_html"]
    assert len(P_OPEN.findall(h)) == h.count(P_CLOSE), "Q%d <p> unbalanced" % qn
    assert "\x00" not in h and "\x00" not in Q[qn]["content_text"]

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
print("OK: %d questions, %d assets" % (len(Q), len(PLAN)))
