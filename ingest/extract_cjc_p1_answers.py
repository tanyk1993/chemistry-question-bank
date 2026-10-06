"""Extract worked solutions + answer key for CJC 2024 H2 P1 (MCQ, 30 questions).

Document shape (a FIFTH container shape, 2026-10-06): the "Worked Solutions"
docx is the question paper itself with each solution in a FLOATING TEXT BOX
(a dashed-border `wps:txbx`) anchored to an otherwise empty paragraph after the
question. Every solution box opens with a bold "Topic: ..." line and carries its
own "Answer: X" line. Word stores each box twice (`mc:Choice` DrawingML +
`mc:Fallback` VML); only the `mc:Choice` copy is read, so nothing is doubled.

What is read per question
  * the "Topic:" box (exactly 30 of them, in question order);
  * Q21 only: three extra boxes (Option A / C / D mechanisms);
  * Q5 only: the body-level table that follows the box (four graphs A-D, each
    with an explanation) -- the explanation text is typed, the graph is a snip;
  * Q8's annotated Figure 2 sits OUTSIDE its box (a free drawing), so its snip
    is placed by plan, not by a FIG sentinel.

Editorial choices (all declared below, none silent)
  * `BOLD_DOMINANT`: a solution whose text is >= 70% bold is the author's habit
    of typing the whole box in bold, not emphasis. Its bold is dropped, except on
    the "Topic:/Concept:/Answer:" lines.
  * Duplicate stray "Answer:" paragraphs (Q8's "Answer: C", Q10's second
    "Answer: D") are layout leftovers of overlapping boxes: dropped.
  * Hand-wrapped continuation paragraphs (4+ leading spaces) are merged back into
    the paragraph above; a `<br>` followed by spaces is a typed line wrap.
  * Q9's "arrow" is Symbol F0DE = a double arrow here (symbols.py reads F0DE as a
    tick for EJC); it is corrected for THIS paper only, by a counted text fix.
  * Q16's radicals use the same inline-SVG markup as the question's options
    (the user's own acceptance of it, 2026-10-05; a nicer cube root is a known
    open item).
  * Q13's tab-typed ICE rows become a `table.cmp`.

Every TEXT_FIX must match its expected count or the run raises.

Output (to <outdir>): worked_solutions.json, answer_assets.json (offsets for
`gen_answers_migration.py`) and answer_key.json.

Run (from the repo root):
  python3 -m ingest.extract_cjc_p1_answers <unz_sol_dir> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from .oxml import (Wq, paragraph_html, paragraph_numid, load_bullet_numids)
from .questions import _table_html
from .corrections import cube_root

MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
WPS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
CENTRE = "\x00C\x00"
FIG = "\x00FIG\x00"
ASSET_FMT = "CJC_H2_P1_Q%d_%s_2024.png"

FRAC = lambda n, d: ('<span class="frac"><span class="fnum">%s</span>'
                     '<span class="fden">%s</span></span>' % (n, d))

# ---- figures ---------------------------------------------------------------
# qnum -> ordered replacement for each FIG sentinel found in that question's
# boxes: ("img", slot) | ("html", text) | None (drop).
FIG_PLAN = {
    1: [("img", "ans-1")],
    2: [("img", "ans-1"), None],              # four shapes + captions: ONE snip
    5: [None],                                # repeated stem graph: not snipped
    7: [("html", FRAC("50 mg", "1 kg") + " "),
        ("html", FRAC("50 x 10<sup>‒3</sup> g", "1 kg"))],
    17: [("img", "ans-1")],
    18: [("img", "ans-1"), ("img", "ans-2")],
    20: [("img", "ans-1")],
    22: [("img", "ans-1")],
    25: [("img", "ans-1")],
}
# Paragraphs dropped outright: (qnum, startswith of the PLAIN text)
DROP_PARAS = [
    (2, "bent"),                              # captions are baked into the snip
    # Q24: the (e)/(f)/(g) syllabus learning outcomes are from the OLD syllabus
    # (user, 2026-10-06); the sentence that points at them is reworded below.
    (24, "(e) recognise"), (24, "(f) recognise"), (24, "(g) recognise"),
]
# Figure that is not inside the box: placed before the Answer line.
EXTRA_IMG_BEFORE_ANSWER = {8: "ans-1"}
# Q5's four graphs: slot -> (cell (row, col) holding the explanation)
Q5_GRAPHS = [("A", (0, 0)), ("B", (1, 1)), ("C", (2, 0)), ("D", (2, 1))]
# Q21's extra boxes: heading text -> slot
Q21_OPTIONS = {"Option A": "ans-A", "Option C": "ans-C", "Option D": "ans-D"}

# answer-asset ordering (offset within the question), in DOM order
ASSET_ORDER = {
    1: ["ans-1"], 2: ["ans-1"], 5: ["ans-A", "ans-B", "ans-C", "ans-D"],
    8: ["ans-1"], 17: ["ans-1"], 18: ["ans-1", "ans-2"], 20: ["ans-1"],
    21: ["ans-A", "ans-C", "ans-D"], 22: ["ans-1"], 25: ["ans-1"],
}


# ---- counted text fixes (applied to each question's final body HTML) --------
# (qnum, old, new, expected_count)
TEXT_FIXES = [
    (9, "✓", "⇒", 2),
    (26, "CO2H", "CO<sub>2</sub>H", 19),    # None = count printed, pinned below
    (26, "CH2F", "CH<sub>2</sub>F", 7),
    (26, "CH2Br", "CH<sub>2</sub>Br", 5),
    (26, "<i>K</i>a", "<i>K</i><sub>a</sub>", 6),
    (26, "accept H+", "accept H<sup>+</sup>", 1),
    (26, "<sub>.</sub>", ".", 1),
    (29, "<i>E</i><sup>O</sup>", "<i>E</i><sup>⦵</sup>", 2),
    (16, "4 <i>x</i>", "4<i>x</i>", 1),
    (16, "2 <i>x</i>", "2<i>x</i>", 2),
    (16, "</i> <sup>3</sup>", "</i><sup>3</sup>", 1),
    (28, "CN–. A small", "CN<sup>–</sup>. A small", 1),
    (24, "As per syllabus learning outcomes (e) and (f) below, the resultant "
         "differences in physical properties in only on rotation of "
         "plane-polarised lights",
     "The resultant difference in physical properties is only in the rotation "
     "of plane-polarised light", 1),
]
SIMILAR_COUNT = [0]   # must end at 8 (Q3, 13, 18, 19, 20, 23, 24, 26)
PINNED = {}   # filled from a first run; see _pin()

RAD_OLD = ('<sup>3</sup>√<span style="text-decoration:overline">'
           + FRAC("q", "4") + "</span>")


def _rad(inner: str) -> str:
    """Cube-root markup, identical to Q16's live option markup (patch 3).

    One definition, shared with the question side: corrections.cube_root."""
    return cube_root(inner)


# ---- helpers -----------------------------------------------------------------
def _plain(h: str) -> str:
    h = re.sub(r"\x00[A-Z]+\x00", "", h)
    return re.sub(r"<[^>]+>", "", h).replace("&nbsp;", " ")


def _boxes(body):
    """[(kid_index, txbxContent)] for every mc:Choice text box, document order."""
    out = []
    for i, k in enumerate(body):
        for ac in k.iter("{%s}AlternateContent" % MC):
            ch = ac.find("{%s}Choice" % MC)
            tb = ch.find(".//{%s}txbx" % WPS) if ch is not None else None
            if tb is None:
                continue
            c = tb.find(Wq + "txbxContent")
            if c is not None:
                out.append((i, c))
    return out


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(Wq + "t"))


def _items(content):
    """Direct children of a text box as [(kind, html, numid)]."""
    out = []
    for el in content:
        ln = etree.QName(el).localname
        if ln == "p":
            h = paragraph_html(el)
            if h.strip():
                out.append(("p", h, paragraph_numid(el)))
        elif ln == "tbl":
            out.append(("tbl", el, None))
    return out


def _merge_runs(h: str) -> str:
    for _ in range(3):
        h = h.replace("</b><b>", "").replace("</sup><sup>", "").replace("</sub><sub>", "")
        h = re.sub(r"<b>\s*</b>", "", h)
    return h


def _tidy_ws(h: str) -> str:
    h = h.replace("\t", " ")
    h = re.sub(r"<br>\s{2,}", " ", h)
    h = re.sub(r"<(i|b|sup|sub)>(\s+)", r"\2<\1>", h)
    h = re.sub(r"(\s+)</(i|b|sup|sub)>", r"</\2>\1", h)
    h = re.sub(r"<(i|b|sup|sub)></\1>", "", h)
    h = re.sub(r"(?<=[^<>\s]) {2,}(?=[^<>\s])", " ", h)
    h = re.sub(r"\s{2,}", " ", h)
    return h.strip()


def _bold_ratio(htmls) -> float:
    inside = outside = 0
    for h in htmls:
        h = re.sub(r'<span class="frac">.*?</span></span>', "", h)
        depth = 0
        for tok in re.split(r"(<[^>]+>)", h):
            if tok == "<b>":
                depth += 1
            elif tok == "</b>":
                depth -= 1
            elif not tok.startswith("<"):
                n = len(re.sub(r"[\s\x00A-Z]", "", tok)) if tok else 0
                if depth > 0:
                    inside += n
                else:
                    outside += n
    return inside / max(1, inside + outside)


def _keep_bold(h: str) -> bool:
    p = _plain(h).lstrip()
    return p.startswith(("Topic:", "Concept:", "Answer:"))


def _unbold(h: str) -> str:
    return h.replace("<b>", "").replace("</b>", "")


def _table_cmp(tbl) -> str:
    """Word table -> table.cmp (no th/thead), cells bold-stripped except the
    header row and first column, which keep their bold."""
    rows = []
    for r, tr in enumerate(tbl.findall(Wq + "tr")):
        cells = []
        for c, tc in enumerate(tr.findall(Wq + "tc")):
            inner = []
            for p in tc.findall(Wq + "p"):
                h = paragraph_html(p).replace(CENTRE, "")
                if h.strip():
                    inner.append(_tidy_ws(_merge_runs(h)))
            h = "<br>".join(inner)
            if r > 0 and c > 0:
                h = _unbold(h)
            cells.append("<td>%s</td>" % h)
        rows.append("<tr>%s</tr>" % "".join(cells))
    return '<table class="cmp">%s</table>' % "".join(rows)


def _img(q, slot) -> str:
    return '<img class="ws-fig" data-asset="%s" alt="">' % (ASSET_FMT % (q, slot))


def _ice_table(rows):
    """Q13's four tab-typed rows -> table.cmp."""
    out = []
    head = ["", "N<sub>2</sub>(g) +", "3H<sub>2</sub>(g) ⇌", "2NH<sub>3</sub>(g)"]
    out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in head))
    for h in rows[1:]:
        cells = _plain_keep(h).split()   # label + three values ("Initial 6.00 6.00 0.00")
        if len(cells) != 4:
            raise ValueError("Q13 ICE row not 4 cells: %r" % cells)
        out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c.strip() for c in cells))
    return '<table class="cmp">%s</table>' % "".join(out)


def _plain_keep(h):
    return h.replace(CENTRE, "")


# ---- per-question assembly ---------------------------------------------------
def _fill_figs(q, htmls, queue_state):
    """Substitute FIG sentinels in `htmls` (list of html strings) from FIG_PLAN."""
    plan = FIG_PLAN.get(q, [])
    out = []
    for h in htmls:
        n = h.count(FIG)
        if not n:
            out.append(h)
            continue
        parts = h.split(FIG)
        buf = parts[0]
        for nxt in parts[1:]:
            i = queue_state[0]
            queue_state[0] += 1
            if i >= len(plan):
                raise ValueError("Q%d: FIG #%d has no plan" % (q, i + 1))
            rep = plan[i]
            if rep is None:
                buf += nxt
            elif rep[0] == "img":
                buf += "\x01IMG:%s\x01" % rep[1] + nxt
            else:
                buf += rep[1] + nxt
        out.append(buf)
    return out


def _flatten_imgs(q, htmls):
    """A paragraph holding an image token becomes [text p][image p]."""
    blocks = []
    for h in htmls:
        m = re.search(r"\x01IMG:([^\x01]+)\x01", h)
        if not m:
            blocks.append(("p", h))
            continue
        before = h[:m.start()]
        after = h[m.end():]
        if _plain(before).strip():
            blocks.append(("p", before))
        blocks.append(("raw", '<p>%s</p>' % _img(q, m.group(1))))
        if _plain(after).strip():
            blocks.append(("p", after))
    return blocks


def build_question(q, items, extra_html_blocks=None, table_override=None):
    """items: [(kind, html|element, numid)] -> body html string."""
    # keep only the FIRST "Answer:" paragraph; later ones are stray leftovers of
    # overlapping boxes (Q8 "Answer: C", Q10 a repeated "Answer: D"); then the
    # declared drops
    seen_answer = False
    kept = []
    for kind, h, nid in items:
        if kind == "p":
            pl = _plain(h).strip()
            if pl.startswith("Answer:"):
                if seen_answer:
                    continue
                seen_answer = True
            if any(q == dq and pl.startswith(ds) for dq, ds in DROP_PARAS):
                continue
        kept.append((kind, h, nid))
    # figure substitution (paragraph items only, document order)
    state = [0]
    p_idx = [i for i, it in enumerate(kept) if it[0] == "p"]
    filled = _fill_figs(q, [kept[i][1] for i in p_idx], state)
    for i, h in zip(p_idx, filled):
        kept[i] = ("p", h, kept[i][2])
    if state[0] != len(FIG_PLAN.get(q, [])):
        raise ValueError("Q%d: %d FIG placeholder(s) planned, %d found"
                         % (q, len(FIG_PLAN.get(q, [])), state[0]))
    return kept


def render(q, kept, bullets):
    """kept -> list of html blocks (strings)."""
    # normalise paragraph html
    norm = []
    for kind, h, nid in kept:
        if kind == "tbl":
            norm.append(("tbl", h, nid))
            continue
        centred = h.startswith(CENTRE)
        h = h.replace(CENTRE, "")
        h = _merge_runs(h)
        raw_has_lead = bool(re.match(r"^(<b>)?\s{4,}", h))
        h = _tidy_ws(h)
        norm.append(("p", (centred, raw_has_lead, h), nid))
    # merge hand-wrapped continuation paragraphs
    merged = []
    for kind, v, nid in norm:
        if (kind == "p" and v[1] and merged and merged[-1][0] == "p"
                and q != 13 and nid is None):
            c, l, prev = merged[-1][1]
            merged[-1] = ("p", (c, l, prev + " " + v[2]), merged[-1][2])
        else:
            merged.append((kind, v, nid))
    # bold handling
    htmls = [v[2] for k, v, n in merged if k == "p"]
    body_h = [h for h in htmls if not _keep_bold(h)]
    ratio = _bold_ratio(body_h)
    strip = ratio >= 0.70
    out_blocks = []
    cur_list = None  # (tag, [li html])
    def close_list():
        nonlocal cur_list
        if cur_list:
            tag, lis = cur_list
            out_blocks.append('<%s class="stmts">%s</%s>' % (
                tag, "".join("<li>%s</li>" % x for x in lis), tag))
            cur_list = None
    ice_rows = []
    for kind, v, nid in merged:
        if kind == "tbl":
            close_list()
            out_blocks.append(_table_cmp(v))
            continue
        centred, _l, h = v
        if strip and not _keep_bold(h):
            h = _unbold(h)
        h = _merge_runs(h)
        # arrow bullets (Wingdings F0F0) are typed as an arrow prefix
        if nid in (43, 44):
            close_list()
            out_blocks.append("<p>⇒ %s</p>" % h)
            continue
        if nid is not None:
            tag = "ul" if nid in bullets else "ol"
            if cur_list and cur_list[0] != tag:
                close_list()
            if not cur_list:
                cur_list = (tag, [])
            cur_list[1].append(h)
            continue
        close_list()
        if q == 13 and (h.startswith(("N<sub>2</sub>(g)", "Initial", "Change",
                                      "Equilibrium")) or ice_rows):
            ice_rows.append(h)
            if len(ice_rows) == 4:
                out_blocks.append(_ice_table(ice_rows))
                ice_rows = []
            continue
        out_blocks.append(('<p class="c">%s</p>' if centred else "<p>%s</p>") % h)
    close_list()
    return out_blocks


def _expand_imgs(blocks, q):
    """Turn \x01IMG:slot\x01 tokens (inside <p>) into image paragraphs."""
    out = []
    for b in blocks:
        m = re.search(r"\x01IMG:([^\x01]+)\x01", b)
        if not m:
            out.append(b)
            continue
        pre = b[:m.start()]
        post = b[m.end():]
        pre_txt = _plain(re.sub(r"</?p[^>]*>", "", pre)).strip()
        post_txt = _plain(re.sub(r"</?p[^>]*>", "", post)).strip()
        if pre_txt:
            out.append(pre + "</p>")
        out.append("<p>%s</p>" % _img(q, m.group(1)))
        if post_txt:
            out.append("<p>" + post.lstrip("<p>") if not post.startswith("<p") else post)
    return out


def apply_text_fixes(q, body):
    for fq, old, new, exp in TEXT_FIXES:
        if fq != q:
            continue
        n = body.count(old)
        want = PINNED.get((fq, old), exp)
        if want is None:
            print("  [pin?] Q%d %r x%d" % (q, old, n))
            want = n
        if n != want:
            raise ValueError("Q%d text fix %r: expected %d, found %d" % (q, old, want, n))
        body = body.replace(old, new)
    return body


def apply_q16(body):
    n = body.count(RAD_OLD)
    if n != 2:
        raise ValueError("Q16: expected 2 radicals, found %d" % n)
    return body.replace(RAD_OLD, _rad(FRAC("q", "4")))


# ---- main ----------------------------------------------------------------------
def parse(unz_dir):
    unz = Path(unz_dir)
    tree = etree.parse(str(unz / "word" / "document.xml"))
    body = tree.getroot().find(Wq + "body")
    kids = list(body)
    bullets = load_bullet_numids(str(unz / "word" / "numbering.xml"))

    boxes = _boxes(body)
    topic = [(i, c) for i, c in boxes if _text(c).lstrip().startswith("Topic")]
    if len(topic) != 30:
        raise ValueError("expected 30 Topic boxes, found %d" % len(topic))
    topic_kids = [i for i, _ in topic]

    results, key, assets = {}, {}, []
    for q, (ki, content) in enumerate(topic, start=1):
        items = _items(content)

        # ---- per-question extras --------------------------------------
        extra_after = []
        if q == 5:
            # the table after the box: four graphs + explanations
            tbl = next(k for k in kids[ki + 1: topic_kids[5]]
                       if etree.QName(k).localname == "tbl")
            hence = next(paragraph_html(k) for k in kids[ki + 1: topic_kids[5]]
                         if etree.QName(k).localname == "p"
                         and _text(k).startswith("Hence, the graphs"))
            extra_after.append(("p", hence, None))
            rows = tbl.findall(Wq + "tr")
            for slot, (r, c) in Q5_GRAPHS:
                tc = rows[r].findall(Wq + "tc")[c]
                texts = []
                for p in tc.findall(Wq + "p"):
                    h = paragraph_html(p).replace(CENTRE, "")
                    if len(_plain(h).strip()) > 60:
                        texts.append(h)
                for ac in tc.iter("{%s}AlternateContent" % MC):
                    ch = ac.find("{%s}Choice" % MC)
                    tb = ch.find(".//{%s}txbx" % WPS) if ch is not None else None
                    if tb is None:
                        continue
                    cc = tb.find(Wq + "txbxContent")
                    if len(_text(cc)) > 60:
                        texts += [paragraph_html(p) for p in cc.findall(Wq + "p")
                                  if paragraph_html(p).strip()]
                extra_after.append(("p", "<b>%s</b>" % slot, None))
                extra_after.append(("p", "\x01IMG:ans-%s\x01" % slot, None))
                for t in texts:
                    extra_after.append(("p", t, None))
        if q == 21:
            for ki2, c2 in boxes:
                t2 = _text(c2).lstrip()
                for head, slot in Q21_OPTIONS.items():
                    if t2.startswith(head) and ki2 > ki:
                        m = re.search(r"\((Product can be formed)\)", t2)
                        extra_after.append(
                            ("p", "<i>%s (%s)</i>" % (head, m.group(1)), None))
                        extra_after.append(("p", "\x01IMG:%s\x01" % slot, None))
        # Q21's Topic box items come first; option boxes after; for Q5 the
        # table follows the box. Q8's figure goes before the Answer line.
        kept = build_question(q, items)
        if q in EXTRA_IMG_BEFORE_ANSWER:
            pos = next(i for i, it in enumerate(kept)
                       if it[0] == "p" and _plain(it[1]).strip().startswith("Answer:"))
            kept.insert(pos, ("p", "\x01IMG:%s\x01" % EXTRA_IMG_BEFORE_ANSWER[q], None))
        kept = kept + extra_after

        blocks = render(q, kept, bullets)
        # image tokens: a block that is ONLY the token becomes an image paragraph
        fixed = []
        for b in blocks:
            m = re.search(r"\x01IMG:([^\x01]+)\x01", b)
            if not m:
                fixed.append(b)
                continue
            pre = b[:m.start()]
            post = b[m.end():]
            pre_t = _plain(re.sub(r"</?p[^>]*>", "", pre)).strip()
            post_t = _plain(re.sub(r"</?p[^>]*>", "", post)).strip()
            open_tag = '<p class="c">' if b.startswith('<p class="c">') else "<p>"
            if pre_t:
                fixed.append(pre.rstrip() + "</p>" if not pre.endswith("</p>") else pre)
            fixed.append("<p>%s</p>" % _img(q, m.group(1)))
            if post_t:
                fixed.append(open_tag + re.sub(r"^</?p[^>]*>", "", post))
        fixed = [b for b in fixed if _plain(b).strip() or "<img" in b or "<table" in b]
        body_html = "\n".join(fixed)
        body_html = re.sub(r"(?<=\S) {2,}(?=\S)", " ", body_html)
        # ASCII hyphen standing in for a minus inside a superscript (charges,
        # exponents): a document-wide declared normalisation to U+2212
        body_html, n_minus = re.subn(
            r"<sup>([^<]*)</sup>",
            lambda m: "<sup>%s</sup>" % m.group(1).replace("-", "\u2212"), body_html)
        if q == 16:
            body_html = apply_q16(body_html)
        # "Answer: X - similar to 2022/P1/Q3 ..." cross-references to the
        # college's own past papers are removed (user, 2026-10-06)
        body_html, n_sim = re.subn(r"\s*[–-]\s*similar to [^<]*", "", body_html)
        SIMILAR_COUNT[0] += n_sim
        body_html = apply_text_fixes(q, body_html)
        results[q] = '<div class="worked-solution">\n%s\n</div>' % body_html

        # ---- answer key ------------------------------------------------
        ans = None
        for kind, h, _n in items:
            if kind == "p":
                m = re.match(r"\s*Answer:\s*([A-D])\b", _plain(h))
                if m:
                    ans = m.group(1)
                    break
        if not ans:
            raise ValueError("Q%d: no 'Answer: X' line" % q)
        key[q] = ans

        # ---- assets ----------------------------------------------------
        found = re.findall(r'data-asset="CJC_H2_P1_Q%d_([^"]+)_2024\.png"' % q, body_html)
        if found != ASSET_ORDER.get(q, []):
            raise ValueError("Q%d asset order %r != plan %r" % (q, found, ASSET_ORDER.get(q, [])))
        for off, slot in enumerate(found, start=1):
            assets.append({"question": q, "slot": slot,
                           "path": ASSET_FMT % (q, slot), "offset": off})
    if SIMILAR_COUNT[0] != 8:
        raise ValueError("expected 8 'similar to' remarks, removed %d" % SIMILAR_COUNT[0])
    return results, key, assets


def main(unz_dir, outdir):
    results, key, assets = parse(unz_dir)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in results.items()}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    (out / "answer_key.json").write_text(
        json.dumps({str(k): v for k, v in key.items()}, indent=1), encoding="utf-8")
    (out / "answer_assets.json").write_text(
        json.dumps(assets, indent=1), encoding="utf-8")
    print("questions:", len(results), " assets:", len(assets))
    print("key:", "".join(key[q] for q in sorted(key)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
