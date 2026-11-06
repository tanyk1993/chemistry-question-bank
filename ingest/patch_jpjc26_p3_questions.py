"""JPJC 2026 H2 P3 (9476/03) questions: patch the extractor output (declared,
asserted) and write the final questions.json / asset_plan.json for
gen_parts_migration.

usage:
  mkdir unz && unzip -q QP.docx -d unz
  python3 -m ingest.jpjc26_p3_prep unz unz_prep
  python3 -m ingest.extract_parts unz_prep QP_word.pdf out \
      --school JPJC --level H2 --paper P3 --year 2026
        (no crops are written: the user snips every figure)
  python3 -m ingest.patch_jpjc26_p3_questions out build [--typos]
  python3 -m ingest.gen_parts_migration build dest.sql \
      --school JPJC --year 2026 --paper 3 --level H2

Shape: SEAB table family, three irregular grids (JPJC 2024/2026 P2 family); see
`jpjc26_p3_prep` (it also gives the school's bCs-only bold runs a real `w:b`).
The docx is QUESTIONS ONLY. Answers are NOT read at this stage.

Marks as ingested: Q1 23, Q2 17, Q3 15, Q4 20, Q5 20 = 95 (75 as sat: Section B
is "answer one"), the same convention as the other P3s.

FIGURES (user snips, 15, all block figures; the printed captions "Fig. x.x" stay
typed in the stem, so snips carry the drawing only -- Q4(f) included):
  Q2(c)(ii)  the whole "halogenoalkanes" table (A, B, C)       [typed table removed]
  Q2(d)      Fig 2.1 (Steps 1-3)
  Q3(a)      Fig 3.1 (pyridine, phenylamine, benzamide)          [caption typed, added]
  Q3(b)      Fig 3.2 lysine
  Q3(b)(iii) protonated lysine of solution W   } the lead-in "A 10 cm3 sample of
  Q3(b)(iii) Fig 3.3 titration graph           } Solution W ..." moved (b)(ii)->(b)(iii)
  Q3(c)      gly / his / lys structures with labels and names
  Q4(a)      Fig 4.1 scheme
  Q4(b)      propanol -> propanal equation (the "Cu" over the arrow is a floating box)
  Q4(e)      Strecker scheme
  Q4(f)      Fig 4.3 graph incl. caption
  Q5(d)(ii)  Fig 5.1
  Q5(e)      Fig 5.2 (incl. the product name label)
  Q5(e)      Fig 5.3
  Q5(f)      phenol and 3-hydroxy-3-methylcyclopentan-1-one (with name labels)
TYPED, NOT SNIPPED: Q2(d) C-Li polarity (superscript delta signs); Tables 1.1-1.3;
Q2(e) D / E / F.

DECLARED FIXES: lead-ins filed under the wrong part (Q1 "During the Contact
process ..." (c)(i)->(c)(ii); Q3 "A 10 cm3 sample of Solution W ..." (b)(ii)->(b)(iii));
Table 1.3 cell broken by a stray <p>; stray empty sup/sub; hard line breaks
mid-sentence; standard-state sign (U+A74B in the source -> house sign); minus signs
for charges / exponents; "x" -> multiplication sign; compound labels the extractor
left plain (Q3 X/Y/Z, Q4 Q/R/S/V, Q5 X/Y, equilibrium I/II) set bold as printed;
a false bold on "step 2" removed; figure / table captions bold as printed.
School typos: ruled by the user 2026-11-06 (apply all), on by default (--no-typos to skip).
Q4(f): the user's snip excludes the caption, so the typed "Fig. 4.3" stays.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
APPLY_TYPOS = "--no-typos" not in sys.argv
Q = {r["question_number"]: r for r in json.loads((SRC / "questions.json").read_text())}
LOG = []
MINUS = "−"


def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


def both(qn, h_old, h_new, t_old=None, t_new=None, rx_h=False, rx_t=False, count=1):
    sub(qn, h_old, h_new, "content_html", count=count, rx=rx_h)
    if t_old is False:               # html-only edit (bold, caption, layout)
        return
    sub(qn, h_old if t_old is None else t_old, h_new if t_new is None else t_new,
        "content_text", count=count, rx=rx_t if t_old is not None else rx_h)


def move_leadin(qn, prev, nxt, n_tail):
    """The lines printed after `prev`'s last [n] become the start of `nxt`; the
    first line is inlined after the label, the part's own text is wrapped in <p>
    (the same shape corrections.LEADIN_MOVES produces)."""
    s = Q[qn]["content_html"]
    pa = '<div class="qpart"><span class="pl">%s</span>' % prev
    na = '<div class="qpart"><span class="pl">%s</span>' % nxt
    assert s.count(pa) == 1 and s.count(na) == 1
    i = s.index(pa)
    j = s.index(na)
    assert i < j
    prev_div = s[i:j]
    assert prev_div.rstrip().endswith("</div>")
    body = prev_div.rstrip()[:-len("</div>")]
    lines = body.split("\n")
    last = max(k for k, ln in enumerate(lines) if '<span class="mk">' in ln)
    tail = lines[last + 1:]
    assert len(tail) == n_tail, (qn, prev, len(tail), tail)
    new_prev = "\n".join(lines[:last + 1]) + "</div>\n"
    k = s.index("</div>", j)
    nxt_div = s[j:k + len("</div>")]
    m = re.match(re.escape(na) + r" (.*)</div>$", nxt_div, flags=re.S)
    own = m.group(1)
    if not own.lstrip().startswith("<"):
        first, sep, rest = own.partition("\n")
        own = "<p>%s</p>%s%s" % (first.rstrip(), sep, rest)
    t0 = tail[0]
    m0 = re.match(r"^<p>(.*)</p>$", t0, flags=re.S)
    assert m0, t0
    new_nxt = na + " " + "\n".join([m0.group(1)] + tail[1:] + [own]) + "</div>"
    Q[qn]["content_html"] = s[:i] + new_prev + new_nxt + s[k + len("</div>"):]
    LOG.append("Q%d: moved %d tail line(s) of %s to the start of %s" % (qn, n_tail, prev, nxt))


# ---- zero-width spaces ---------------------------------------------------------------
for r in Q.values():
    for f in ("content_html", "content_text"):
        r[f] = r[f].replace("​", "")

# ======================================================================= Q1
# (c)(i) -> (c)(ii): "During the Contact process ..."
move_leadin(1, "(c)(i)", "(c)(ii)", 1)
# (a)(i): the full stop printed inside the subscript
both(1, "SO<sub>2. </sub>Explain", "SO<sub>2</sub>. Explain", "SO2. Explain", "SO2. Explain")
# Table 1.1 header: degree sign
both(1, "boiling point / <sup>o</sup> C", "boiling point / °C", "boiling point / o C", "boiling point / °C")
# Table 1.3: the cell broken by a stray <p> and a stray </p> after the table
sub(1, "blue\n<p>after acidification of <b>M</b>, the resulting compound effervesces on addition of "
       "Na<sub>2</sub>CO<sub>3</sub>(aq).</td>",
       "blue<p>after acidification of <b>M</b>, the resulting compound effervesces on addition of "
       "Na<sub>2</sub>CO<sub>3</sub>(aq).</p></td>")
sub(1, "</table></p>", "</table>")

# ======================================================================= Q2
both(2, "Halogens and halides ions", "Halogens and halide ions") if APPLY_TYPOS else None
both(2, "0.500A is", "0.500 A is") if APPLY_TYPOS else None
both(2, "to synthesis alcohols", "to synthesise alcohols") if APPLY_TYPOS else None
sub(2, "CaBr<sub>2 </sub>using", "CaBr<sub>2</sub> using")
sub(2, "CaBr2 using platinum electrodes  can", "CaBr2 using platinum electrodes can", "content_text")
sub(2, "C<i class=\"el\">l</i><sup>−</sup><sub> </sub>ions", "C<i class=\"el\">l</i><sup>−</sup> ions")
# (c)(ii): the A / B / C table becomes ONE snip
sub(2, r' <br>\n<table class="qt"><tr><td colspan="2">halogenoalkanes</td></tr>.*?</table></p>',
    '\n<div class="fig">figure</div>', rx=True)
sub(2, r" ?\nhalogenoalkanesA\nAB\nBC\nC", "", "content_text", rx=True)
# (d): the C-Li polarity is typed; Fig 2.1 is a block snip before its caption
both(2, 'polarised <br></p>\n<div class="fig">figure</div>\n<p>, which are useful',
        'polarised C<sup>δ−</sup>-Li<sup>δ+</sup>, which are useful',
        "polarised , which are useful", "polarised Cδ−-Liδ+, which are useful")
sub(2, '<p class="c">Fig. 2.1</p>', '<div class="fig">figure</div>\n<p class="c">Fig. 2.1</p>')

# ======================================================================= Q3
# (a): Fig 3.1 caption is inside a text box in the source (not extracted): typed
sub(3, 'in decreasing order of basicity.</p>\n<div class="fig">figure</div>\n',
       'in decreasing order of basicity.</p>\n<div class="fig">figure</div>\n<p class="c">Fig. 3.1</p>\n')
both(3, "many protein, the", "many proteins, the") if APPLY_TYPOS else None
both(3, "amino acids <span", "amino acids. <span", "amino acids [1]", "amino acids. [1]") if APPLY_TYPOS else None
# (b)(ii) -> (b)(iii): "A 10 cm3 sample of Solution W ..." + structure + Fig 3.3 (5 lines)
move_leadin(3, "(b)(ii)", "(b)(iii)", 5)
# (c): three structures + their label table = ONE snip
sub(3, r'<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n'
       r'<p></td></tr><tr><td><b>gly</b></td>.*?</table></p>|'
       r'<div class="fig">figure</div>\n<div class="fig">figure</div>\n<div class="fig">figure</div>\n'
       r'<p></td></tr><tr><td>gly</td>.*?</table></p>',
    '<div class="fig">figure</div>', rx=True)
sub(3, "glyhislysglycinehistidinelysine", "gly his lys glycine histidine lysine", "content_text")

# ======================================================================= Q4
# (a)(iii) fine. (b): the equation line is a snip (Cu over the arrow); text keeps it
sub(4, r'\n<p>CH<sub>3</sub>CH<sub>2</sub>CH<sub>2</sub>OH\s+\+\s+½ O<sub>2\s+</sub>→<sub>\s+</sub>'
       r'CH<sub>3</sub>CH<sub>2</sub>CHO \+ H<sub>2</sub>O</p>', "", rx=True)
sub(4, r"\n\s+\nCH3CH2CH2OH\s+\+\s+½ O2\s+→\s+CH3CH2CHO \+ H2O",
    "\nCH3CH2CH2OH + ½ O2 → CH3CH2CHO + H2O", "content_text", rx=True)
# (f): first placeholder + typed caption go; the snip carries the caption
sub(4, '<span class="pl">(f)</span> <div class="fig">figure</div>\n<p>At low pH',
       '<span class="pl">(f)</span> At low pH')
sub(4, "acts as a bidentate ligand.</p>", "acts as a bidentate ligand.")
both(4, "α-Aminobutyric acid (AABA), represented", "α-aminobutyric acid (AABA), represented") if APPLY_TYPOS else None
# compound labels printed bold, left plain by the extractor
sub(4, "formulae of Q, R and S.", "formulae of <b>Q</b>, <b>R</b> and <b>S</b>.")
sub(4, "structure of compound V.", "structure of compound <b>V</b>.")

# ======================================================================= Q5
sub(5, '<i><span class="sr">.</span></i>', '.')
# (c): equilibria I / II and reaction 1 are bold where printed
sub(5, "for equilibrium I.", "for equilibrium <b>I</b>.")
sub(5, "<p>equilibrium I:</p>", "<p>equilibrium <b>I</b>:</p>")
sub(5, "<p>equilibrium II:</p>", "<p>equilibrium <b>II</b>:</p>")
sub(5, "<p>reaction 1 [Ni(NH", "<p><b>reaction 1</b> [Ni(NH")
sub(5, "<p>equilibrium I:<b> </b>[Ni(H<sub>2</sub>O)", "<p>equilibrium <b>I</b>: [Ni(H<sub>2</sub>O)")
sub(5, "products X and Y as shown", "products <b>X</b> and <b>Y</b> as shown")
sub(5, "on <b>step 2</b> of Fig. 5.3 to complete the mechanism for <b>step 2.</b>", "on step 2 of Fig. 5.3 to complete the mechanism for step 2.")
# the bCs hack bolds the ketol name in the (f) prose; the PDF prints it plain
sub(5, "and <b>3-hydroxy-3-methylcyclopentan-1-one</b>. ", "and 3-hydroxy-3-methylcyclopentan-1-one. ")
# (e): Fig 5.2 snip carries the product name label; Fig 5.3 is a block snip
sub(5, r'\n<p>\s+3-hydroxy-3-methylcyclopentan-1-one</p>', "", rx=True)
sub(5, r"\n\n {20,}3-hydroxy-3-methylcyclopentan-1-one\nFig\. 5\.2", "\nFig. 5.2", "content_text", rx=True)
# (f): one snip for both structures and their name labels
sub(5, r'<div class="fig">figure</div>\n<p>and</p>\n<div class="fig">figure</div>\n<p>\s+phenol\s+'
       r'<b>3-hydroxy-3-methylcyclopentan-1-one</b> <span class="mk">\[2\]</span></p>',
    '<div class="fig">figure</div>\n<p><span class="mk">[2]</span></p>', rx=True)
sub(5, r"\n\s+and\s+\n\s+phenol\s+3-hydroxy-3-methylcyclopentan-1-one \[2\]", " [2]", "content_text", rx=True)

# ======================================================================= global clean-ups
for qn, r in Q.items():
    h, t = r["content_html"], r["content_text"]
    # bold that is only whitespace / punctuation / a line break
    h = re.sub(r"<b>((?:\s|\.|<br>)*)</b>", r"\1", h)
    # hard line breaks in the middle of a sentence
    h = re.sub(r" ?<br> (<span class=\"mk\">)", r" \1", h)
    h = re.sub(r" ?<br>", " ", h)
    # captions bold as printed
    h = re.sub(r'<p class="c">((?:Fig\.|Table) \d\.\d)</p>', r'<p class="c"><b>\1</b></p>', h)
    # standard-state sign: U+A74B in the source
    h = h.replace("<sup>ꝋ</sup>", '<sup class="pl-sym">⦵</sup>')
    t = t.replace("ꝋ", "⦵")
    # cm^3 as a superscript character
    h = h.replace("cm³", "cm<sup>3</sup>")
    t = t.replace("cm³", "cm3")
    # stray space inside sup / sub
    h = re.sub(r"<(sup|sub)>([^<]*?)\s+</\1>", lambda m: "<%s>%s</%s> " % (m.group(1), m.group(2), m.group(1)), h)
    h = re.sub(r"<(sup|sub)>\s*</\1>", "", h)
    # minus signs: charges, exponents, negative numbers
    h = re.sub(r"<sup>(\d?)-</sup>", r"<sup>\1" + MINUS + "</sup>", h)
    h = re.sub(r"<sup>-(\d)</sup>", r"<sup>" + MINUS + r"\1</sup>", h)
    h = h.replace("is -1280", "is " + MINUS + "1280")
    t = t.replace("is -1280", "is " + MINUS + "1280")
    t = re.sub(r"EDTA4-", "EDTA4" + MINUS, t)
    t = re.sub(r"\]2-\(", "]2" + MINUS + "(", t)
    # multiplication sign
    h = re.sub(r"(\d) x (10<sup>)", r"\1 × \2", h)
    t = re.sub(r"(\d) x (10)", r"\1 × \2", t)
    # degrees
    h = h.replace("−12.6<sup>o</sup>", "−12.6°")
    t = t.replace("−12.6o", "−12.6°")
    r["content_html"], r["content_text"] = h, t

# bold labels the extractor left plain (printed bold): Q3 W, X, Y, Z; Q4 U
sub(3, "identify the point X, Y and Z at which", "identify the point <b>X</b>, <b>Y</b> and <b>Z</b> at which")
sub(3, r"(?<=olution )W(?![A-Za-z0-9])", "<b>W</b>", rx=True, count=Q[3]["content_html"].count("olution W"))
sub(3, r"(?<=<p>)W(?= was titrated)", "<b>W</b>", rx=True, count=len(re.findall(r"<p>W was titrated", Q[3]["content_html"])))
assert Q[3]["content_html"].count("<b>W</b>") == 4, Q[3]["content_html"].count("<b>W</b>")
sub(4, r"(?<=complex ion )U(?![A-Za-z0-9])", "<b>U</b>", rx=True,
    count=len(re.findall(r"complex ion U(?![A-Za-z0-9])", Q[4]["content_html"])))

CONTEXT = []
for qn, r in Q.items():
    for f in ("content_html", "content_text"):
        for m in re.finditer("–", r[f]):
            CONTEXT.append("Q%d %s: %r" % (qn, f[8:], r[f][max(0, m.start() - 12): m.end() + 8]))
        r[f] = r[f].replace("–", MINUS) if "<sup>" in r[f] and False else r[f]

# ---- asset plan (final) ---------------------------------------------------------------
def A(q, slot, part):
    return {"question": q, "part": part, "slot": slot, "ordinal": 0,
            "storage_path": "JPJC_H2_P3_Q%d_%s_2026.png" % (q, slot), "n_refs": 1}


PLAN = [A(2, "cii", "(c)(ii)"), A(2, "d", "(d)"),
        A(3, "a", "(a)"), A(3, "b", "(b)"), A(3, "biii", "(b)(iii)"), A(3, "biii2", "(b)(iii)"),
        A(3, "c", "(c)"),
        A(4, "a", "(a)"), A(4, "b", "(b)"), A(4, "e", "(e)"), A(4, "f", "(f)"),
        A(5, "dii", "(d)(ii)"), A(5, "e", "(e)"), A(5, "e2", "(e)"), A(5, "f", "(f)")]
seen = {}
for p in PLAN:
    seen[p["question"]] = seen.get(p["question"], 0) + 1
    p["ordinal"] = seen[p["question"]]

# ---- checks ---------------------------------------------------------------------------
bad = []
for qn, r in sorted(Q.items()):
    h = r["content_html"]
    nph = h.count('<div class="fig">')
    nblock = len([p for p in PLAN if p["question"] == qn])
    if nph != nblock:
        bad.append("Q%d: %d placeholders for %d block assets" % (qn, nph, nblock))
    if re.search(r"<(sup|sub)>\s*</\1>", h) or "<p></td>" in h or "</table></p>" in h:
        bad.append("Q%d: leftover empty sup/sub or stray <p> around a table" % qn)
    if re.search(r"</td></tr></table></td>", h):
        bad.append("Q%d: stray table fragment" % qn)
    if "[Total:" in h:
        bad.append("Q%d: leftover [Total] in html" % qn)
    if not r["content_text"].rstrip().endswith("[Total: %d]" % r["marks"]) and r["marks"]:
        bad.append("Q%d: content_text does not end with its [Total]" % qn)
    if h.count("<div") != h.count("</div>"):
        bad.append("Q%d: unbalanced div" % qn)
    got = sum(p["marks"] or 0 for p in r["parts"])
    if got != r["marks"]:
        bad.append("Q%d: parts sum %d vs total %d" % (qn, got, r["marks"]))
    if "<br>" in h and "<br>" not in h.replace("<br>", "", 0) and False:
        pass
    if "ꝋ" in h or "ꝋ" in r["content_text"]:
        bad.append("Q%d: U+A74B left" % qn)
    if "&lt;" in r["content_text"]:
        bad.append("Q%d: html entity in content_text" % qn)
assert [Q[k]["marks"] for k in sorted(Q)] == [23, 17, 15, 20, 20], [Q[k]["marks"] for k in sorted(Q)]
assert not bad, "\n".join(bad)

(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, indent=1), encoding="utf-8")
print("questions: %d | assets: %d (all block) | typos applied: %s" % (len(Q), len(PLAN), APPLY_TYPOS))
for l in LOG:
    print("  " + l)
print("en dashes left (review):")
for c in CONTEXT:
    print("  " + c)
