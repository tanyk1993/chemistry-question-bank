"""DHS 2024 H2 P3 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration.

usage: python3 -m ingest.patch_dhs_p3_questions <extractor_out_dir> <build_dir>

The extractor itself (extract_parts) already applies, through corrections.py,
the soft-<br> fix and the three lead-in moves that carry no figure
(Q2(b)(iii)->(b)(iv), Q2(d)(i)->(d)(ii), Q5(d)(i)->(d)(ii)). A move that
carries a figure is REFUSED by the extractor (the asset owner would change),
so those three are done here, and their asset slots are renamed to the part
they are displayed under (ci->cii, di->dii, bii->biii).
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


# ---------------------------------------------------------------- lead-in moves
def move_leadin(qn, prev, nxt, n_tail):
    """Same shape the extractor's own LEADIN_MOVES produces: the lines printed
    after `prev`'s last [n] become the start of `nxt`; the first line is
    inlined after the label, the part's own text is wrapped in <p>."""
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
    # the part's own first block becomes a <p> unless it already is one
    if not own.lstrip().startswith("<"):
        first, sep, rest = own.partition("\n")
        own = "<p>%s</p>%s%s" % (first.rstrip(), sep, rest)
    # first tail line is inlined after the label (a bare paragraph)
    t0 = tail[0]
    m0 = re.match(r"^<p>(.*)</p>$", t0, flags=re.S)
    assert m0, t0
    new_nxt = na + " " + "\n".join([m0.group(1)] + tail[1:] + [own]) + "</div>"
    Q[qn]["content_html"] = s[:i] + new_prev + new_nxt + s[k + len("</div>"):]
    LOG.append("Q%d: moved %d tail line(s) of %s to the start of %s" % (qn, n_tail, prev, nxt))
    return tail


# Q1(c)(i) -> (c)(ii): Table 1.1 + Fig. 1.2
move_leadin(1, "(c)(i)", "(c)(ii)", 6)
# Q1(d)(i) -> (d)(ii): Fig. 1.4
move_leadin(1, "(d)(i)", "(d)(ii)", 3)
# Q2(b)(ii) -> (b)(iii): 3,4-dimethylhexane
move_leadin(2, "(b)(ii)", "(b)(iii)", 3)

# content_text for the same three moves
Q1T = Q[1]["content_text"]
a = ("[1]\nTable 1.1 shows the melting points of two metal nitrites which have different structure and bonding.\n"
     "Table 1.1\nmetal nitritemelting point/ °CAgNO2140KNO2441\nFig. 1.2 shows a general structure of AgNO2.\n\n"
     "Fig. 1.2 (c)(ii) ")
assert Q1T.count(a) == 1
Q[1]["content_text"] = Q1T.replace(a, "[1] (c)(ii) Table 1.1 shows the melting points of two metal nitrites which have "
                                      "different structure and bonding.\nTable 1.1\nmetal nitritemelting point/ °CAgNO2140KNO2441\n"
                                      "Fig. 1.2 shows a general structure of AgNO2.\n\nFig. 1.2\n")
a = ("[1]\nFig. 1.4 shows a reaction scheme which includes the carbonylation reactions shown in Fig. 1.3.\n\n"
     "Fig. 1.4 (d)(ii) ")
sub(1, a, "[1] (d)(ii) Fig. 1.4 shows a reaction scheme which includes the carbonylation reactions shown in Fig. 1.3.\n\n"
          "Fig. 1.4\n", field="content_text")
a = ("[2]\n3,4-dimethylhexane is produced from the Kolbe electrolysis of the aqueous solution of the sodium salt of a "
     "carboxylic acid.\n\n3,4-dimethylhexane (b)(iii) ")
sub(2, a, "[2] (b)(iii) 3,4-dimethylhexane is produced from the Kolbe electrolysis of the aqueous solution of the sodium "
          "salt of a carboxylic acid.\n\n3,4-dimethylhexane\n", field="content_text")

# ---- Q2 Fig. 2.1: t(1/2) typed as a stacked subscript in the source
sub(2, r'<p><i>t</i><sub><span class="frac"><span class="fnum"></sub><sub>1</sub><sub></span><span class="fden"></sub>'
       r'<sub>2</sub><sub></span></span></sub> = ',
    '<p class="c"><i>t</i><sub>½</sub> = ', rx=False)
sub(2, "\nt12 = 1k[A]t\n", "\nt½ = 1 / k[A]t\n", field="content_text")

# ---- Q3(b): equation with its own delta-H label on the same line
sub(3, "<p>\t\t\tN<sub>2</sub>O<sub>4</sub>(g) + 2NO(g) ⇌ 2N<sub>2</sub>O<sub>3</sub>(g)\t ∆<i>H</i>",
       '<p class="c eqn">N<sub>2</sub>O<sub>4</sub>(g) + 2NO(g) ⇌ 2N<sub>2</sub>O<sub>3</sub>(g)    ∆<i>H</i>')
sub(3, "\n\t\t\tN2O4(g) + 2NO(g) ⇌ 2N2O3(g)\t ∆H", "\nN2O4(g) + 2NO(g) ⇌ 2N2O3(g)    ∆H", field="content_text")

# ---- Q4(a): Fig. 4.1 -- the user's snip carries the names under the structures
sub(4, '<div class="fig">figure</div>\n<table class="qt"><tr><td>  propanal</td><td><b>  X</b></td>'
       '<td>butan-2-ol</td></tr></table>\n<p class="c"><b>Fig. 4.1</b></p>',
       '<div class="fig">figure</div>\n<p class="c"><b>Fig. 4.1</b></p>')
sub(4, "\n  propanal  Xbutan-2-ol\nFig. 4.1", "\nFig. 4.1", field="content_text")

# ---- Q4(a)(ii): the two bullets, with the CH3(-) carbanion as an INLINE snip
sub(4, r'<table class="qt"><tr><td><ul class="stmts"><li>In the slow step, the nucleophile</li></ul></td><td>\n'
       r'<div class="fig">figure</div>\n<p></td><td>attacks the electrophilic </td></tr></table></p>\n'
       r'<p>carbon in propanal, forming a reactive intermediate\.</p>\n'
       r'<ul class="stmts"><li>This reactive intermediate then reacts with <sup>\+</sup>MgBr to form <b>X</b>\.</li></ul>',
    '<ul class="stmts"><li>In the slow step, the nucleophile '
    '<img data-asset="DHS_H2_P3_Q4_aii_2024.png" alt="methyl carbanion with a lone pair" '
    'style="display:inline;vertical-align:middle;margin:0 .15em;border:0;padding:0"> '
    'attacks the electrophilic carbon in propanal, forming a reactive intermediate.</li>'
    '<li>This reactive intermediate then reacts with <sup>+</sup>MgBr to form <b>X</b>.</li></ul>', rx=True)
sub(4, "In the slow step, the nucleophileattacks the electrophilic \ncarbon in propanal, forming a reactive intermediate.",
       "In the slow step, the nucleophile attacks the electrophilic carbon in propanal, forming a reactive intermediate.",
    field="content_text")

# ---- Q4(a)(iv): the printed [1] sits under the scheme
sub(4, 'of the following reaction. <span class="mk">[1]</span></p>\n<div class="fig">figure</div></div>',
       'of the following reaction.</p>\n<div class="fig">figure</div> <span class="mk">[1]</span></div>')

# ---- wording fixes approved by the user (2026-10-12); every other query kept as printed
for f in ("content_html", "content_text"):
    sub(4, "Nitrous oxide, NO", "Nitrogen monoxide, NO", field=f)
    sub(1, "a fuel which the heat change is known", "a fuel for which the heat change is known", field=f)
    sub(5, "The electron deficient boron and partial negative hydrogen",
           "The electron-deficient boron and partially negative hydrogen", field=f)
sub(5, "forms solid Ni(OH)<sub>2</sub> respectively.", "forms solid Ni(OH)<sub>2</sub>.")
sub(5, "forms solid Ni(OH)2 respectively.", "forms solid Ni(OH)2.", field="content_text")

# ---- a minus sign / en dash used as a hyphen inside a WORD becomes a hyphen
# (bond notation R-X, C-H, R-R and ion charges are left alone)
for f in ("content_html", "content_text"):
    sub(2, "carbon–oxygen", "carbon-oxygen", field=f)
    sub(5, "nickel−iron", "nickel-iron", field=f)
    sub(5, "half–equations", "half-equations", field=f)
    sub(5, "half−cell", "half-cell", field=f, count=3)
    sub(5, "carbon−carbon", "carbon-carbon", field=f, count=2)

# ---------------------------------------------------------------- asset plan
RENAME ={(1, "ci"): ("(c)(ii)", "cii"), (1, "di"): ("(d)(ii)", "dii"), (2, "bii"): ("(b)(iii)", "biii")}
for it in PLAN:
    k = (it["question"], it["slot"])
    if k in RENAME:
        it["part"], it["slot"] = RENAME[k]
        it["storage_path"] = "DHS_H2_P3_Q%d_%s_2024.png" % (it["question"], it["slot"])
        LOG.append("asset Q%d slot -> %s" % (k[0], it["slot"]))
# Q4(a)(ii) becomes an inline picture: planned AFTER the block figures
blocks = [x for x in PLAN if x["question"] == 4 and x["slot"] != "aii"]
inl = [x for x in PLAN if x["question"] == 4 and x["slot"] == "aii"]
assert len(inl) == 1
PLAN = [x for x in PLAN if not (x["question"] == 4)]
for n, x in enumerate(blocks, 1):
    x["ordinal"] = n
inl[0].update({"ordinal": len(blocks) + 1, "inline": True, "n_refs": 0})
PLAN += blocks + inl

# every .fig placeholder must still equal the block-asset count, per question
for qn, r in Q.items():
    n_ph = r["content_html"].count('<div class="fig">')
    n_as = len([x for x in PLAN if x["question"] == qn and not x.get("inline")])
    assert n_ph == n_as, (qn, n_ph, n_as)

(DST / "questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1), encoding="utf-8")
(DST / "patch_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("\n".join(LOG))
