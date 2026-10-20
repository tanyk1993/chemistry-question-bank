"""Extract worked solutions + answer key for ACJC 2026 H2 P1 (9476/01, MCQ).

Document shape (same family as ASRJC 2024 P1, HANDOFF section 21): the school's
solutions file is the question paper itself -- ONE Word table per question --
with one extra ROW per table whose first paragraph reads "Answer: X" and which
runs on into the worked explanation, all in blue. A separate key table sits on
page 2 (table 1) and the cover page is table 0; both are skipped (no
"Answer:" row). Run on the ORIGINAL solutions document.xml.

Key: read THREE independent ways and all must agree -- the letter in each
"Answer:" row (XML), the printed key table on page 2 (XML table 1) and the
"Answer: X" letters printed in the Word PDF.

Figures (the user hand-snips everything; `FIG_PLAN`): every drawing / OLE
object / ink stroke is a FIG sentinel, resolved by an explicit per-question
plan consumed in DOCUMENT ORDER; the run raises on a shortfall or leftover.

Declared, asserted steps (nothing silent):
  * `DROP_BLOCKS`   typed labels that live inside a user snip (Q24 S / T)
  * `BLOCK_PREFIX`  text Word supplies as an auto-number label (Q1 "0.01")
  * `ALIGN_RULES`   whitespace-aligned lines rebuilt (Q16, Q27)
  * `norm()`        mechanical typography only (zero-width spaces, minus signs,
                    spaces inside sup/sub, adjacent bold/italic runs, the
                    standard-state sign, state-symbol italics). Wording and
                    chemistry are NEVER changed here: those go to the user and
                    are applied through `RULED_FIXES` once ruled.

Usage:
  python3 -m ingest.extract_acjc26_p1_answers <solutions document.xml> <solutions.pdf> <outdir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import corrections
from .oxml import NS, Wq, paragraph_html

SCOPE = ("ACJC", "H2", "P1", 2026)

FIG = "\x00FIG\x00"
CENTRE = "\x00C\x00"
W = "{%s}" % NS["w"]

ARROW = ("html", " \u2192 ")
EQUIL = ("html", " \u21cc ")


def IMG(slot):
    return ("img", slot)


# Per-question plan for FIG sentinels, in DOCUMENT ORDER after the collapsing
# rule (consecutive figure-only paragraphs become one). A question absent here
# must have no FIG sentinel. Real pictures are the user's hand snips.
FIG_PLAN = {
    17: [IMG("ans-1")],     # cholesterol with the 8 chiral carbons circled
    18: [IMG("ans-1")],     # hand-drawn F and G with the H environments coloured
    24: [IMG("ans-a"),      # R -> S scheme (KMnO4), S label inside the snip
         IMG("ans-b"),      # R -> T scheme (I2, NaOH), T label inside the snip
         IMG("ans-c"),      # the R-CH(OH)-CH3 fragment, IN the sentence
         IMG("ans-d")],     # R -> divinyl scheme, "+ 2H2O" inside the snip
    26: [IMG("ans-1")],     # the three fragments with R1-R4 circled
    29: [EQUIL, EQUIL],     # two drawn equilibrium arrows, typed
}
# A picture that sits IN a line of text (img.ws-fig is display:block in
# index.html, so these carry an inline style; sizeFig only sets max-width/height).
INLINE_FIGS = {(24, "ans-c")}

# Typed labels that live INSIDE a user snip (so are not typed again). Each rule
# must match exactly one paragraph.
DROP_BLOCKS = {
    24: [("p", r"^\s*<b>S</b>\s*$", "S label is inside the ans-a snip"),
         ("p", r"^\s*<b>T</b>\s*$", "T label is inside the ans-b snip")],
}

# Text Word supplies as an AUTO-NUMBER label (numId 27, level 1 = "%1.%2" =
# "0.01"): absent from the XML text, present in the Word PDF.
BLOCK_PREFIX = {
    1: [(r'^\u00d7 <span class="frac"><span class="fnum">V</span>', "0.01 ")],
}

# Paragraphs whose `<br>` are real line breaks (kept) rather than layout wraps.
BR_KEEP = {11, 19}

# Answer-figure files: SCHOOL_H2_P1_Q<n>_<slot>_2026.png (the bank's own
# convention: ACJC 2024 P1 used ..._ans-a_2024.png; a lone figure is "ans-1").
def asset_name(q, slot):
    return "ACJC_H2_P1_Q%d_%s_2026.png" % (q, slot)


# ---------------------------------------------------------------------------
def direct(el, tag):
    return [c for c in el if c.tag == W + tag]


def plain(el):
    return "".join(el.itertext())


_QNUM = re.compile(r"^\s*(\d{1,2})\s*$")
_ANS_P = re.compile(r"Answer\s*:\s*<b>\s*([A-D])\s*</b>")


def cell_colspan(tc):
    tcPr = tc.find(Wq + "tcPr")
    if tcPr is None:
        return None
    gs = tcPr.find(Wq + "gridSpan")
    if gs is None:
        return None
    v = gs.get(Wq + "val")
    return int(v) if v else None


def _indent_gap(match_text):
    width = sum(4 if c == "\t" else 1 for c in match_text)
    return width


SPACE_EM = 0.28      # one Arial space, in em: the source aligns with typed spaces


def spacer(em):
    return '<span style="display:inline-block;width:%.1fem"></span>' % em


def tidy(html: str, qn=None) -> str:
    """Layout line-wrap <br> -> space (kept where BR_KEEP says they are real
    line breaks); leading typed spaces -> a spacer of the same width; a run of
    spaces or a tab inside a line -> a gap."""
    html = html.rstrip(" \t\u00a0")   # trailing alignment padding is not content
    html = re.sub(r"^(?:[ \t\u00a0]|&nbsp;)*<br>", "", html)
    # typed spaces INSIDE a leading <b>/<i> are indentation, not content
    html = re.sub(r"^((?:<[bi]>)+)([ \t\u00a0]+)", r"\2\1", html)
    if qn in BR_KEEP:
        lines = [tidy(x) for x in re.split(r"[ \t\u00a0]*<br>", html)
                 if re.sub(r"<[^>]+>|[ \t\u00a0]", "", x)]
        return "<br>".join(lines)
    html = re.sub(r"\s*<br>\s*", " ", html)
    m = re.match(r"^([ \t\u00a0]+)", html)
    lead = ""
    if m:
        w = _indent_gap(m.group(1))
        html = html[m.end():]
        if w >= 4:
            lead = spacer(w * SPACE_EM)

    def gap(mm):
        w = _indent_gap(mm.group(0))
        return spacer(max(1.0, w * SPACE_EM))

    html = re.sub(r"[ \u00a0]*\t[ \t\u00a0]*|[ \u00a0]{4,}", gap, html)
    return lead + html.rstrip()


def read_blocks(ans_row):
    """[("p", html) | ("table", rows)] for one answer row, empties dropped."""
    blocks = []
    for tc in direct(ans_row, "tc"):
        for child in tc:
            if child.tag == W + "p":
                h = paragraph_html(child)
                if h and h.replace(CENTRE, "").strip():
                    blocks.append(("p", h))
            elif child.tag == W + "tbl":
                rows = []
                for tr in direct(child, "tr"):
                    row = []
                    for cell in direct(tr, "tc"):
                        paras = []
                        for p in direct(cell, "p"):
                            h = paragraph_html(p).replace(CENTRE, "")
                            if h.strip():
                                paras.append(clean(h, None))
                        row.append(("<br>".join(paras), cell_colspan(cell)))
                    rows.append(row)
                blocks.append(("table", rows))
    return blocks


def question_groups(document_xml):
    """{qnum: answer_row} -- the one row per question holding 'Ans:'."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    out = {}
    for tbl in direct(body, "tbl"):
        if not re.search(r"Answer\s*:", plain(tbl)):
            continue                      # cover-page and answer-key tables
        rows = direct(tbl, "tr")
        starts = [i for i, r in enumerate(rows)
                  if direct(r, "tc") and _QNUM.match(plain(direct(r, "tc")[0]))]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(rows)
            grp = rows[s:e]
            qn = int(_QNUM.match(plain(direct(grp[0], "tc")[0])).group(1))
            ans = [r for r in grp if re.search(r"Answer\s*:", plain(r))]
            if len(ans) != 1:
                raise RuntimeError("Q%d: expected exactly one answer row, "
                                   "found %d" % (qn, len(ans)))
            if qn in out:
                raise RuntimeError("Q%d appears twice" % qn)
            out[qn] = ans[0]
    return out


def fig_only(html):
    s = html.replace(CENTRE, "").replace(FIG, "").strip()
    return html.count(FIG) > 0 and not s


def _sc(m):
    """Spaces inside a sup/sub move outside it (leading ones are dropped)."""
    tag, lead, core, trail, nxt = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    if not core.strip():
        return " " if (lead or core or trail) else ""
    out = "<%s>%s</%s>" % (tag, core, tag)
    if trail:
        out += " " if nxt.isalnum() else trail
    return out


def norm_pre(html):
    """Before tidy(): zero-width / non-breaking spaces, spaces inside sup/sub."""
    html = html.replace("\u200b", "")
    html = html.replace("\u00a0,", ",").replace("\u00a0", " ")
    return re.sub(r"<(sup|sub)>(\s*)([^<]*?)(\s*)</\1>(?=(.?))", _sc, html)


def clean(html, qn):
    return norm(tidy(norm_pre(html), qn))


def norm(html):
    """MECHANICAL typography only; wording and chemistry are never touched."""
    # the scan-line / macron glyph standing in for a charge sign
    html = re.sub(r"(?<=[A-Za-z)\]])[\u00af\u23ba]", "<sup>\u2212</sup>", html)
    # minus signs inside charges / exponents
    html = re.sub(r"<sup>([^<]*)</sup>",
                  lambda m: "<sup>%s</sup>" % re.sub("[\u2012\u2013\u2010-]", "\u2212", m.group(1)),
                  html)
    html = html.replace("\u2012", "\u2212")
    html = re.sub(r"(?<=\d) \u2013 (?=\d)", " \u2212 ", html)       # subtraction
    html = re.sub(r"(?<![\w)\]])-(?=lg\b)", "\u2212", html)           # -lg(...)
    html = re.sub(r"<(sub)>(\d)([.,;:])</sub>", r"<sub>\2</sub>\3", html)
    html = html.replace("</b><b>", "").replace("</i><i>", "")
    html = re.sub(r"<b>[ ]+", "<b>", html)
    html = html.replace("<i> </i>", " ")
    html = re.sub(r"<i>([A-Za-z])<sub>([^<]*)</sub>( ?)</i>", r"<i>\1</i><sub>\2</sub>\3", html)
    html = html.replace("<sup>\u03b8</sup>", '<sup class="pl-sym">\u29b5</sup>')   # standard-state sign
    html = html.replace("\u2206", "\u0394")
    html = html.replace("(<i>s</i>)", "(s)")                               # state symbols are upright
    html = html.replace("<i>e</i><sup>", "e<sup>")
    html = re.sub(r'<span class="sr">([IVX]+)([.,;]?) </span>', r'<span class="sr">\1</span>\2 ', html)
    html = re.sub(r"\u00d7(?=\d|<span class=\"frac\")", "\u00d7 ", html)
    return html


def _right(w, txt):
    return ('<span style="display:inline-block;min-width:%.1fem;text-align:right">%s</span>'
            % (w, txt))


# Lines the source aligns with runs of spaces: rebuilt so they align in any
# font. (regex on the block AFTER norm()/tidy, replacement, why). Each rule must
# match exactly one paragraph.
ALIGN_RULES = {
    16: [(r"^(?:<span[^>]*></span>)?8\.1 = (.*)$",
          lambda m: spacer(3) + _right(8.5, "8.1") + " = " + m.group(1)),
         (r"^(?:<span[^>]*></span>)?(\[CO<sub>3</sub>.*?\]) = (0\.00705)$",
          lambda m: spacer(3) + _right(8.5, m.group(1)) + " = " + m.group(2))],
}
ALIGN_MANY = {27: (re.compile(r"^(.+?)<span[^>]*></span>([\u2212+]\d\.\d\d V)$"), 4)}


def _apply_align(qn, out):
    for pat, fn in ALIGN_RULES.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(pat, p)]
        if len(hit) != 1:
            raise RuntimeError("Q%d: align rule %r matched %d block(s)" % (qn, pat, len(hit)))
        out[hit[0]] = ("p", re.sub(pat, fn, out[hit[0]][1]))
    if qn in ALIGN_MANY:
        rx, want = ALIGN_MANY[qn]
        n = 0
        for i, (k, p) in enumerate(out):
            if k == "p" and rx.match(p):
                m = rx.match(p)
                out[i] = ("p", '<span style="display:inline-block;min-width:21em">%s</span>%s'
                          % (m.group(1), m.group(2)))
                n += 1
        if n != want:
            raise RuntimeError("Q%d: align-many matched %d line(s), expected %d" % (qn, n, want))
    return out


def prepare(qn, blocks):
    """Pull the key, drop the 'Ans' paragraph, apply the collapsing rules."""
    key = None
    out = []
    for kind, payload in blocks:
        if kind == "p" and key is None and re.search(r"Answer\s*:", payload):
            m = _ANS_P.search(payload)
            if not m:
                raise RuntimeError("Q%d: cannot read the answer letter from %r"
                                   % (qn, payload))
            key = m.group(1)
            rest = _ANS_P.sub("", payload, count=1).replace(CENTRE, "")
            if rest.strip():
                if fig_only(rest):
                    out.append(("p", rest.strip()))
                else:
                    out.append(("p", rest))
            continue
        out.append((kind, payload))
    if key is None:
        raise RuntimeError("Q%d: no 'Ans:' paragraph found" % qn)

    for kind, pat, _why in DROP_BLOCKS.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out)
               if k == kind and (pat is None or re.search(pat, p))]
        if len(hit) != 1:
            raise RuntimeError("Q%d: drop rule %r/%r matched %d block(s), "
                               "expected 1" % (qn, kind, pat, len(hit)))
        del out[hit[0]]

    # tidy (layout) then norm (typography), then the declared rebuilds
    out = [(k, clean(p, qn) if k == "p" and FIG not in p else p)
           for k, p in out]
    for pat, prefix in BLOCK_PREFIX.get(qn, []):
        hit = [i for i, (k, p) in enumerate(out) if k == "p" and re.search(pat, p)]
        if len(hit) != 1:
            raise RuntimeError("Q%d: prefix rule %r matched %d block(s)" % (qn, pat, len(hit)))
        out[hit[0]] = ("p", prefix + out[hit[0]][1])
    out = _apply_align(qn, out)

    merged = []
    for kind, payload in out:
        if (kind == "p" and fig_only(payload) and merged
                and merged[-1][0] == "p" and fig_only(merged[-1][1])):
            continue                      # collapse into the previous figure
        if kind == "p" and fig_only(payload):
            payload = FIG                 # one figure, however many objects
        merged.append((kind, payload))
    return key, merged


def wrap_answer(html):
    html = html.strip()
    if not html:
        return ""
    return '<span class="ans">%s</span>' % html


# Pictures that sit IN a line of text rather than in a block of their own.
# index.html forces img.ws-fig to display:block, so these carry an inline style
# (inline styles beat the stylesheet; sizeFig only touches max-width/height).
INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"


def render(qn, blocks):
    plan = iter(FIG_PLAN.get(qn, []))
    assets = []

    def take():
        try:
            return next(plan)
        except StopIteration:
            raise RuntimeError("Q%d: more FIG placeholders than FIG_PLAN "
                               "entries" % qn)

    def img_html(slot):
        path = asset_name(qn, slot)
        assets.append((slot, path))
        return '<img class="ws-fig" data-asset="%s" alt="">' % path

    out = []
    skip = 0
    for idx, (kind, payload) in enumerate(blocks):
        if skip:
            skip -= 1
            continue
        if kind == "table":
            rows_html = []
            for row in payload:
                cells = []
                for text, span in row:
                    parts = text.split(FIG)
                    buf = parts[0]
                    for nxt in parts[1:]:
                        item = take()
                        if item[0] != "html":
                            raise RuntimeError("Q%d: an image planned inside "
                                               "a table cell" % qn)
                        buf += item[1] + nxt
                    attr = ' colspan="%d"' % span if span else ""
                    cells.append("<td%s>%s</td>" % (attr, buf.strip()))
                rows_html.append("<tr>%s</tr>" % "".join(cells))
            out.append('<table class="cmp">%s</table>' % "".join(rows_html))
            continue

        centred = payload.startswith(CENTRE)
        text = payload.replace(CENTRE, "")
        if FIG in text:
            text = clean(text, qn)
        if FIG not in text:
            inner = wrap_answer(text)
            if inner:
                out.append('<p class="c">%s</p>' % inner if centred
                           else "<p>%s</p>" % inner)
            continue

        # a paragraph carrying figures: typed ones stay inline, a real picture
        # gets its own paragraph (img.ws-fig is display:block in index.html, so
        # mid-sentence placement splits the sentence regardless).
        segs = text.split(FIG)
        pending = segs[0]
        prefix = ""
        for i, nxt in enumerate(segs[1:], start=1):
            item = take()
            if item[0] == "html":
                pending += item[1] + nxt
                continue
            if (qn, item[1]) in INLINE_FIGS:
                im = img_html(item[1]).replace(
                    'alt=""', 'alt="" style="%s"' % INLINE_STYLE)
                prefix += wrap_answer(pending) + im
                pending = nxt
                continue
            if pending.strip() or prefix:
                out.append("<p>%s</p>" % (prefix + wrap_answer(pending)))
                prefix = ""
            tail = nxt
            im = img_html(item[1])
            # a punctuation mark right after the picture belongs to it, not
            # to a line of its own (", yellow ppt is observed.")
            m = re.match(r"^\s*([,.;:])", tail)
            if m:
                im += '<span class="ans">%s</span>' % m.group(1)
                tail = tail[m.end():]
            out.append("<p>%s</p>" % im)
            pending = tail
        if pending.strip() or prefix:
            out.append("<p>%s</p>" % (prefix + wrap_answer(pending)))

    left = list(plan)
    if left:
        raise RuntimeError("Q%d: %d FIG_PLAN entries unused: %r"
                           % (qn, len(left), left))
    body = "\n".join(out)
    body, log = corrections.apply(body, SCOPE)
    if log:
        print("Q%d corrections applied: %s" % (qn, log))
    return '<div class="worked-solution">\n%s\n</div>' % body, assets


def key_table(document_xml):
    """{n: letter} from the printed answer-key table (body table 1)."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    tbl = direct(body, "tbl")[1]
    cells = [plain(tc).strip() for tr in direct(tbl, "tr") for tc in direct(tr, "tc")]
    out = {}
    for a, b in zip(cells[0::2], cells[1::2]):
        if a.isdigit() and b in "ABCD" and len(b) == 1:
            out[int(a)] = b
    return out


def pdf_keys(pdf):
    """The 'Answer: X' letters printed in the Word PDF, in page order."""
    import pymupdf
    doc = pymupdf.open(str(pdf))
    text = "\n".join(pg.get_text() for pg in doc)
    return re.findall(r"Answer:\s*([A-D])\b", text)


def extract(document_xml, pdf):
    groups = question_groups(document_xml)
    if sorted(groups) != list(range(1, 31)):
        raise RuntimeError("expected questions 1-30, got %s" % sorted(groups))
    keys, ws, assets = {}, {}, []
    for qn in sorted(groups):
        key, blocks = prepare(qn, read_blocks(groups[qn]))
        keys[qn] = key
        html, a = render(qn, blocks)
        ws[qn] = html
        for off, (slot, path) in enumerate(a, start=1):
            assets.append({"question": qn, "slot": slot, "path": path,
                           "offset": off})
    kt = key_table(document_xml)
    pk = pdf_keys(pdf)
    if sorted(kt) != list(range(1, 31)):
        raise RuntimeError("key table has %d entries, expected 30" % len(kt))
    if len(pk) != 30:
        raise RuntimeError("the Word PDF prints %d 'Answer:' letters, expected 30"
                           % len(pk))
    bad = {q: (keys[q], kt[q], pk[q - 1]) for q in keys
           if not (keys[q] == kt[q] == pk[q - 1])}
    if bad:
        raise RuntimeError("answer key disagrees (row, key table, PDF): %r" % bad)
    return ws, assets, keys


if __name__ == "__main__":      # pragma: no cover
    doc, pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    ws, assets, keys = extract(doc, pdf)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    (outdir / "answer_assets.json").write_text(
        json.dumps(assets, indent=2), encoding="utf-8")
    (outdir / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in keys.items()}, indent=2),
        encoding="utf-8")
    print("worked solutions: %d" % len(ws))
    print("answer figures:   %d" % len(assets))
    print("answer keys:      %d, row = key table = Word PDF" % len(keys))
