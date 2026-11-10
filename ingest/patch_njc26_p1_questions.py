"""NJC 2026 H2 P1 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_question_migration.

usage:
  python3 -m ingest.extract_questions <unz> <word.pdf> <out> \
      --school NJC --level H2 --paper 1 --year 2026 --no-crops
  python3 -m ingest.patch_njc26_p1_questions <out> <build_dir>

Every edit asserts its match count: a silent miss is how a fix ships unapplied.
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
    assert n == count, "Q%d %s: expected %d got %d for %r" % (
        qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))


# ---- over-arrow labels (rate constants / reagents), inline-styled like corrections.py's
# stacked glyphs, so no index.html change (= no deploy).  top / arrow / optional bottom.
def long_arrow(w):
    """a forward arrow of chosen length (em): the U+27F6 glyph falls back to a short
    arrow in the site font, so draw it (line + head)."""
    return ('<span style="display:flex;align-items:center;width:%sem;margin:0 auto">'
            '<span style="flex:1;border-top:1.3px solid currentColor"></span>'
            '<span style="font-size:.55em;margin-left:-.3em;line-height:1">\u25ba</span></span>' % w)


def over(top, arrow, bottom=None, wide=False):
    pad = "padding:0 .35em;" if wide else "padding:0 .15em;"
    small = '<span style="display:block;font-size:.72em;line-height:1.15">%s</span>'
    out = ('<span style="display:inline-block;vertical-align:middle;text-align:center;'
           'line-height:1.1;%s">' % pad) + small % top
    out += '<span style="display:block;line-height:1">%s</span>' % arrow
    # forward arrows get an invisible bottom line so the arrow sits on the text midline
    out += small % (bottom or "&nbsp;")
    return out + "</span>"


def stack_label(species, label):
    """species with its colour label centred underneath (Q14)."""
    return ('<span style="display:inline-block;vertical-align:top;text-align:center">'
            '%s<span style="display:block;font-size:.72em;line-height:1.3">%s</span></span>'
            % (species, label))

# ---- Q3: the docx holds one stray drawing object but the page has no figure
# (text-only question); the extractor planned a stem1 for it. Drop it.
# ---- Q14, Q15, Q16: the only "figure" is the drawn equilibrium arrow; typed as "⇌"
# (user ruling 2026-11-10), so no snip is needed.
# Q28: the extractor counted 4 stem drawing objects (8 for 6 placeholders); the page
# has two figures -- stem1 = the aldol scheme, stem2 = diketone reactant + its scheme
# (user ruling 2026-11-10: snipped as 2). Options A-D stay.
DROP = {3: ["stem1"], 14: ["stem1"], 15: ["stem1"], 16: ["stem1"],
        28: ["stem3", "stem4"]}
for qn, slots in DROP.items():
    gone = [p for p in PLAN if p["question"] == qn and p["slot"] in slots]
    assert len(gone) == len(slots), (qn, gone)
    PLAN = [p for p in PLAN if p not in gone]
    LOG.append("Q%d asset plan: dropped %s" % (qn, slots))

FIG_JOIN = r'\s*</p>\n<div class="fig">figure</div>\n<p class="c">\s*'
for qn in (14, 15, 16):
    sub(qn, FIG_JOIN, " ⇌ ", rx=True)
# content_text has no arrow (the drawing contributes nothing): insert it
sub(14, r"4SCN‒ \(aq\) \[Co", "4SCN‒ (aq) ⇌ [Co", field="content_text", rx=True)
sub(15, r"2D2O\(l\) D3O", "2D2O(l) ⇌ D3O", field="content_text", rx=True)
sub(16, r"2NH3 NH4", "2NH3 ⇌ NH4", field="content_text", rx=True)


# ---- Q14: "pale pink / bright blue" labels sit under the two complexes, aligned by hand-typed spaces

# ---- Q22: the three clue bullets are a list (house style: ul.stmts), not paragraphs
sub(22, r'(<p class="qstem">Compound <b>X</b> (?:reacts with sodium|reacts with Fehling|does <b>not</b>)[^\n]*?</p>\n?){3}',
    "@@UL@@", rx=True)
_m = re.findall(r'<p class="qstem">(Compound <b>X</b> [^\n]*?)</p>', "".join(
    ['<p class="qstem">Compound <b>X</b> reacts with sodium metal to produce hydrogen gas.</p>',
     '<p class="qstem">Compound <b>X</b> reacts with Fehling\u2019s solution to produce a brick red precipitate. </p>',
     '<p class="qstem">Compound <b>X</b> does <b>not</b> decolourise bromine water.</p>']))
sub(22, "@@UL@@", '<ul class="stmts">' + "".join("<li>%s</li>" % t.strip() for t in _m) + "</ul>\n")

# ---- Q24: reagent above the arrow was aligned with runs of spaces
sub(24, "HCN      NaCN     →  CH", "HCN " + over("NaCN", long_arrow(4.2), wide=True) + " CH")
sub(24, "NaOH                    → ", "NaOH → ", count=2)
# the site builds the option cards from this table, so it must stay in the DOM,
# but it would show a second (D-blank) copy of the options: hide it
sub(24, '<table class="opts-table">', '<table class="opts-table" style="display:none">')


# ---- Q14: colour labels belong UNDER their own complex (pale pink: [Co(H2O)6]2+,
# bright blue: [Co(SCN)4]2-), smaller font (user ruling 2026-11-10)
_cr = '[Co(H<sub>2</sub>O)<sub>6</sub>]<sup>2+</sup>(aq)'
_cb = '[Co(SCN)<sub>4</sub>]<sup>2\u2212</sup>(aq)'
sub(14, r'\n<p class="qstem">\s+pale pink\s+bright blue</p>', "", rx=True)
sub(14, '<p class="c">[Co(H<sub>2</sub>O)<sub>6</sub>]<sup>2+</sup>(aq)  +  4SCN<sup>\u2012</sup> (aq) \u21cc '
        '[Co(SCN)<sub>4</sub>]<sup>2\u2012</sup> (aq)  +  6H<sub>2</sub>O(<i class="el">l</i>)</p>',
    '<p class="c">' + stack_label(_cr, "pale pink") + ' + 4SCN<sup>\u2212</sup>(aq) \u21cc '
    + stack_label(_cb, "bright blue") + ' + 6H<sub>2</sub>O(<i class="el">l</i>)</p>')

# ---- Q12: the rate-constant arrows were drawn pictures; rebuilt as typed steps, one per line
S2O8 = 'S<sub>2</sub>O<span class="stk post"><span>2\u2212</span><span>8</span></span>'
SO4 = 'SO<span class="stk post"><span>2\u2212</span><span>4</span></span>'
K = lambda n: "<i>k</i><sub>%s</sub>" % n
FWD = lambda n: over(K(n), long_arrow(2.6))
EQM = lambda n: over(K(n), '<span style="font-size:1.25em;line-height:.9">\u21cc</span>', "<i>k</i><sub>\u2212%s</sub>" % n)
def step(n, body, speed):
    return '<b>Step %d:</b> %s&emsp;(%s)' % (n, body, speed)
Q12 = {
 "A": ('rate = <i>k</i> [ICl] [H<sub>2</sub>]',
       [step(1, '2 ICl ' + EQM(1) + ' I<sub>2</sub>Cl<sub>2</sub>', 'fast'),
        step(2, 'I<sub>2</sub>Cl<sub>2</sub> + H<sub>2</sub> ' + FWD(2) + ' I<sub>2</sub> + 2HCl', 'slow')]),
 "B": ('rate = <i>k</i> [NO]<sup>2</sup> [H<sub>2</sub>]',
       [step(1, 'NO + H<sub>2</sub> ' + EQM(1) + ' N + H<sub>2</sub>O', 'fast'),
        step(2, 'N + NO ' + FWD(2) + ' N<sub>2</sub>O', 'slow'),
        step(3, 'N<sub>2</sub>O + H<sub>2</sub> ' + FWD(3) + ' N<sub>2</sub> + H<sub>2</sub>O', 'fast')]),
 "C": ('rate = <i>k</i> [' + S2O8 + '] [I<sup>\u2212</sup>]',
       [step(1, S2O8 + ' + I<sup>\u2212</sup> ' + EQM(1) + ' [IS<sub>2</sub>O<sub>8</sub>]<sup>3\u2212</sup>', 'fast'),
        step(2, '[IS<sub>2</sub>O<sub>8</sub>]<sup>3\u2212</sup> ' + FWD(2) + ' 2' + SO4 + ' + I<sup>+</sup>', 'slow'),
        step(3, 'I<sup>+</sup> + I<sup>\u2212</sup> ' + FWD(3) + ' I<sub>2</sub>', 'fast')]),
 "D": ('rate = <i>k</i> [NO<sub>2</sub>]<sup>2</sup>',
       [step(1, 'NO<sub>2</sub> + CO ' + EQM(1) + ' NO<sub>2</sub>CO', 'fast'),
        step(2, 'NO<sub>2</sub>CO + NO ' + FWD(2) + ' 2NO + CO<sub>2</sub>', 'slow')]),
}
_t = Q[12]["content_html"]
_i = _t.index('<table class="opts-table">')
_rows = ('<tr><td class="ol"></td><td><b>rate equation</b></td><td><b>suggested mechanism</b></td></tr>'
         + "".join('<tr><td class="ol">%s</td><td>%s</td><td>%s</td></tr>' % (k, r, "<br>".join(st))
                   for k, (r, st) in Q12.items()))
Q[12]["content_html"] = _t[:_i] + '<table class="opts-table">' + _rows + "</table>\n"
LOG.append("Q12 content_html: mechanism table rebuilt (typed steps, one per line)")
# search text / options: same wording as the table, with the rate constants spelled out
_txt = {
 "A": ("rate = k [ICl] [H2]", ["Step 1: 2 ICl k1 ⇌ k−1 I2Cl2 (fast)", "Step 2: I2Cl2 + H2 k2 → I2 + 2HCl (slow)"]),
 "B": ("rate = k [NO]2 [H2]", ["Step 1: NO + H2 k1 ⇌ k−1 N + H2O (fast)", "Step 2: N + NO k2 → N2O (slow)", "Step 3: N2O + H2 k3 → N2 + H2O (fast)"]),
 "C": ("rate = k [S2O82−] [I−]", ["Step 1: S2O82− + I− k1 ⇌ k−1 [IS2O8]3− (fast)", "Step 2: [IS2O8]3− k2 → 2SO42− + I+ (slow)", "Step 3: I+ + I− k3 → I2 (fast)"]),
 "D": ("rate = k [NO2]2", ["Step 1: NO2 + CO k1 ⇌ k−1 NO2CO (fast)", "Step 2: NO2CO + NO k2 → 2NO + CO2 (slow)"]),
}
for k, (r, st) in _txt.items():
    Q[12]["options"][k] = r + " | " + " ".join(st)
_ct = Q[12]["content_text"]
_j = _ct.index("rate equation | suggested mechanism")
Q[12]["content_text"] = (_ct[:_j] + "rate equation | suggested mechanism | "
    + " | ".join("%s %s" % (k, Q[12]["options"][k]) for k in "ABCD") + " |")
LOG.append("Q12 content_text/options rewritten")

# ---- Q27: statements 1-3 are figures; a content-sized layout grid (table.qt.center) puts
# each structure next to its number instead of centred on the page
sub(27, '<ol class="stmts"><li><div class="fig">figure</div></li><li><div class="fig">figure</div></li>'
        '<li><div class="fig">figure</div></li></ol>',
    '<table class="qt center">' + "".join(
        '<tr><td>%d</td><td><div class="fig">figure</div></td></tr>' % i for i in (1, 2, 3)) + '</table>')


# ---- Q15: nuclide notation was flattened to "12D" / "11H"; stacked mass-over-proton number
# (.stk, the site's nuclide markup), and the figure-dash exponents -> U+2212
_nuc = lambda a, z, sym: '<span class="stk"><span>%s</span><span>%s</span></span>%s' % (a, z, sym)
sub(15, "Deuterium, 12D is an isotope of hydrogen, 11H.",
    "Deuterium, %s is an isotope of hydrogen, %s." % (_nuc(2, 1, "D"), _nuc(1, 1, "H")))
sub(15, "Deuterium, 12D is an isotope of hydrogen, 11H.",
    "Deuterium, 21D is an isotope of hydrogen, 11H.", field="content_text")
sub(15, "10<sup>\u201215</sup> mol<sup>2 </sup>dm<sup>\u20126</sup>",
    "10<sup>\u221215</sup> mol<sup>2</sup> dm<sup>\u22126</sup>")
sub(15, "OD<sup>\u2012</sup> (aq)", "OD<sup>\u2212</sup>(aq)")

# hand-spaced gaps inside the same equation lines
sub(15, "(aq)        <i>K</i><i><sub>d</sub></i> =", "(aq)&emsp;<i>K</i><i><sub>d</sub></i> =")
sub(16, "</span></span>             ∆<i>H</i>", "</span></span>&emsp;∆<i>H</i>")

# ---------------------------------------------------------------- GATE -----
by_q = {}
for p in PLAN:
    by_q.setdefault(p["question"], []).append(p)
bad = []
for qn, r in sorted(Q.items()):
    ph = r["content_html"].count('<div class="fig">')
    ps = by_q.get(qn, [])
    want = sum(1 for p in ps if p["kind"] == "block") + (
        1 if any(p["kind"] == "option" for p in ps) else 0)
    if ph != want:
        bad.append("Q%d: %d placeholders, plan wants %d" % (qn, ph, want))
    for key in ("content_html", "content_text"):
        if "\x00" in r[key]:
            bad.append("Q%d: NUL in %s" % (qn, key))
    if sorted(r["options"]) != list("ABCD"):
        bad.append("Q%d: options %r" % (qn, sorted(r["options"])))
if bad:
    print("GATE (open items, not yet resolved):\n" + "\n".join(bad))
assert sorted(Q) == list(range(1, 31))

for p in PLAN:                      # re-number ordinals after the drops
    pass
_seen = {}
for p in sorted(PLAN, key=lambda p: (p["question"], p["ordinal"])):
    _seen[p["question"]] = _seen.get(p["question"], 0) + 1
    p["ordinal"] = _seen[p["question"]]
PLAN.sort(key=lambda p: (p["question"], p["ordinal"]))
(DST / "questions.json").write_text(
    json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(
    json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("patched %d questions; %d assets" % (len(Q), len(PLAN)))
