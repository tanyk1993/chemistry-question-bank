"""DHS 2024 H2 P2 questions: patch the extractor output (declared, asserted)
and write the final questions.json / asset_plan.json for gen_parts_migration."""
import json, re
from pathlib import Path
import sys
# usage: python3 -m ingest.patch_dhs_p2_questions <extractor_out_dir> <build_dir>
SRC = Path(sys.argv[1]); DST = Path(sys.argv[2]); DST.mkdir(parents=True, exist_ok=True)
Q = {r["question_number"]: r for r in json.loads((SRC/"questions.json").read_text())}
LOG = []

def sub(qn, old, new, field="content_html", count=1, rx=False):
    s = Q[qn][field]
    n = len(re.findall(old, s, flags=re.S)) if rx else s.count(old)
    assert n == count, "Q%d %s: expected %d got %d for %r" % (qn, field, count, n, old[:70])
    Q[qn][field] = re.sub(old, new, s, flags=re.S) if rx else s.replace(old, new)
    LOG.append("Q%d %s x%d: %s" % (qn, field, n, old[:60].replace("\n", " ")))

def img(slot, alt):
    return '<img data-asset="DHS_H2_P2_Q%s_2024.png" alt="%s">' % (slot, alt)

# ---- soft line breaks typed to wrap a sentence (Q1-Q4); Q5's header <br> are genuine
for qn, n in ((1, 2), (2, 1), (3, 2), (4, 1)):
    sub(qn, r"[ \t]*<br>[ \t]*", " ", count=n, rx=True)
# ---- empty superscript / subscript spacers
sub(1, "(aq) <sup> </sup>→", "(aq) →")
sub(5, "propane<sub> </sub>at", "propane at")

# ---- Q2(b): Table 2.1 is ONE user snip (replaces the broken per-cell figures)
sub(2, r'<table class="qt"><tr><td>name</td>.*?</table></p></div>',
    '<div class="fig">figure</div></div>', rx=True)
# lead-in printed between (a)'s [3] and (b): move to the start of (b)
LEAD2 = ("Carboxylic acids, esters and ketones are examples of organic compounds "
         "containing carbon and oxygen atoms.")
sub(2, '<span class="mk">[3]</span>\n<p>%s</p></div>' % LEAD2, '<span class="mk">[3]</span></div>')
sub(2, '<span class="pl">(b)</span> Table 2.1', '<span class="pl">(b)</span> %s\n<p>Table 2.1' % LEAD2)
sub(2, 'carboxylic acid group.\n<p class="c"><b>Table 2.1</b></p>',
       'carboxylic acid group.</p>\n<p class="c"><b>Table 2.1</b></p>')
sub(2, "\nCarboxylic acids, esters and ketones are examples of organic compounds containing carbon and oxygen atoms. (b) ",
       " (b) Carboxylic acids, esters and ketones are examples of organic compounds containing carbon and oxygen atoms.\n",
    field="content_text")
# ---- Q2(c): W sits in a one-cell layout table; type the caption
sub(2, '<div class="fig">figure</div>\n<p></td></tr><tr><td><b>W</b></td></tr></table></p>',
       '<div class="fig">figure</div>\n<p class="c"><b>W</b></p>')

# ---- Q2(c): the empty X/Y/Z answer grid is removed (user, 2026-10-11)
sub(2, '<p>Draw the structures of <b>X</b>, <b>Y</b> and <b>Z</b>.</p>\n<table class="qt"><tr><td><b>X</b></td><td><b>Y</b></td><td><b>Z</b></td></tr><tr><td></td><td></td><td></td></tr></table> <span class="mk">[2]</span></div>',
       '<p>Draw the structures of <b>X</b>, <b>Y</b> and <b>Z</b>. <span class="mk">[2]</span></p></div>')
sub(2, 'Z.\nXYZ [2]', 'Z. [2]', field="content_text")
# ---- Q3(a): asparagine + threonine = ONE user snip (captions inside the snip)
sub(3, '<div class="fig">figure</div>\n<div class="fig">figure</div>\n<p></td></tr><tr><td>asparagine</td><td></td><td>threonine</td></tr></table></p></div>',
       '<div class="fig">figure</div></div>')
# ---- Q3(b): Table 3.1 rows = inline snips; lead-in moves from (b)(i) to (b)(ii)
T31 = ('<table class="qt"><tr><td>%s</td><td>p<i>K</i><sub>b1</sub> = 3.45</td></tr>'
       '<tr><td>%s</td><td>p<i>K</i><sub>b2</sub> = 5.12</td></tr></table>'
       % (img("3_bi", "M + H+ to give the monoprotonated ion"),
          img("3_bi2", "monoprotonated M + H+ to give the diprotonated ion")))
sub(3, r'<span class="mk">\[1\]</span>\n<p><b>M</b> is a weak diacidic base\. Table 3\.1 shows the p<i>K</i><sub>b</sub> values of <b>M</b>\.</p>\n'
       r'<p class="c"><b>Table 3\.1</b></p>\n<div class="fig">figure</div>\n<p></td><td>p<i>K</i><sub>b1</sub> = 3\.45</td></tr><tr><td></p>\n'
       r'<div class="fig">figure</div>\n<p></td><td>p<i>K</i><sub>b2</sub> = 5\.12</td></tr></table></p>\n'
       r'<p>(A 25 cm<sup>3</sup> sample.*?pH meter\.)</p></div>\n'
       r'<div class="qpart"><span class="pl">\(b\)\(ii\)</span> (Calculate the initial pH)',
    ('<span class="mk">[1]</span></div>\n'
     '<div class="qpart"><span class="pl">(b)(ii)</span> <b>M</b> is a weak diacidic base. Table 3.1 shows the p<i>K</i><sub>b</sub> values of <b>M</b>.\n'
     '<p class="c"><b>Table 3.1</b></p>\n' + T31 + '\n<p>\\1</p>\n<p>\\2'), rx=True)
sub(3, 'on the pH. <span class="mk">[2]</span></div>', 'on the pH. <span class="mk">[2]</span></p></div>')
sub(3, 'M is a weak diacidic base. Table 3.1 shows the pKb values of M.\nTable 3.1\npKb1 = 3.45pKb2 = 5.12\nA 25',
       'A 25', field="content_text") if False else None

# ---- Q4(c)(i): Table 4.3 step 1 = inline snip; rate-determining-step line -> (c)(ii)
sub(4, '<td>\n<div class="fig">figure</div>\n<p></td></tr><tr><td>2</td>',
       '<td>%s</td></tr><tr><td>2</td>' % img("4_ci", "step 1: protonation of Y to give Z"))
sub(4, '</table> <span class="mk">[3]</span></p>\n<p>Step 2 is the rate-determining step of the mechanism described in Table 4.3.</p></div>',
       '</table> <span class="mk">[3]</span></div>')
sub(4, '<span class="pl">(c)(ii)</span> Suggest the rate equation',
       '<span class="pl">(c)(ii)</span> Step 2 is the rate-determining step of the mechanism described in Table 4.3.\n<p>Suggest the rate equation')
sub(4, 'with hydrobromic acid. <span class="mk">[1]</span></div>',
       'with hydrobromic acid. <span class="mk">[1]</span></p></div>')

# ---- Q5(a): Table 5.1 header cells (a <p> opened in one <td> and closed in the next)
sub(5, 'energy per gram\n<p>/ kJ g<sup>−1</sup></td><td>energy per dm<sup>3</sup> at 25 °C and 1 bar</p>\n<p>/ MJ dm<sup>−3</sup></td>',
       'energy per gram<br>/ kJ g<sup>−1</sup></td><td>energy per dm<sup>3</sup> at 25 °C and 1 bar<br>/ MJ dm<sup>−3</sup></td>')
sub(5, '</table></p></div>', '</table></div>')
# Q5(b)(i): equation with a trailing dH label aligned by spaces -> p.c.eqn (pre-wrap)
sub(5, '<p class="c">4CH<sub>3</sub>CH<sub>2</sub>COOH', '<p class="c eqn">4CH<sub>3</sub>CH<sub>2</sub>COOH')

# ---- asset plan (final, per the user's two merged snips)
def A(q, slot, ordinal, inline=False, n_refs=1, part=None):
    return {"question": q, "part": part, "slot": slot, "ordinal": ordinal,
            "storage_path": "DHS_H2_P2_Q%d_%s_2024.png" % (q, slot), "n_refs": n_refs,
            **({"inline": True} if inline else {})}
PLAN = [A(1,"cii",1,part="(c)(ii)"),
        A(2,"b",1,part="(b)"), A(2,"c",2,part="(c)"), A(2,"d",3,part="(d)"),
        A(3,"a",1,part="(a)"), A(3,"b",2,part="(b)"), A(3,"biv",3,part="(b)(iv)"),
        A(3,"bi",4,True,0,"(b)(i)"), A(3,"bi2",5,True,0,"(b)(i)"),
        A(4,"c",1,part="(c)"), A(4,"ciii",2,part="(c)(iii)"), A(4,"civ",3,part="(c)(iv)"),
        A(4,"ci",4,True,0,"(c)(i)"),
        A(5,"ciii",1,part="(c)(iii)")]
# placeholder / asset agreement (the frontend rotates figures on a mismatch)
for qn, r in Q.items():
    nph = r["content_html"].count('<div class="fig">')
    nas = len([p for p in PLAN if p["question"] == qn and not p.get("inline")])
    assert nph == nas, (qn, nph, nas)
    for p in PLAN:
        if p["question"] == qn and p.get("inline"):
            assert 'data-asset="%s"' % p["storage_path"] in r["content_html"], p
assert sum(r["marks"] for r in Q.values()) == 75
DST.mkdir(exist_ok=True)
(DST/"questions.json").write_text(json.dumps([Q[k] for k in sorted(Q)], ensure_ascii=False, indent=1))
(DST/"asset_plan.json").write_text(json.dumps(PLAN, ensure_ascii=False, indent=1))
print("\n".join(LOG)); print(len(PLAN), "assets")
