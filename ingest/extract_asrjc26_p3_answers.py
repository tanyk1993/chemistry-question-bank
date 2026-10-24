"""ASRJC 2026 H2 P3 (9476/03) -- worked solutions from the combined QP + suggested-solutions docx.

Same family as ASRJC 2026 H2 P2 (extract_asrjc26_p2_answers.py): the solutions docx IS the
question paper (one 4-column SEAB table per question, Q1..Q3 = tables 2..4, Q4 = tables 5 AND 6,
Q5 = table 7) with each answer typed into a following ROW in blue (0000CC; a few in 0000FF),
red (FF0000) marker notes, no examiner "Comments" rows.

ANSWER ROWS are exactly the rows the questions stage deleted (`asrjc26_p3_prep`: every row with
coloured text, plus the FORCE_DELETE picture-only rows). Reusing those decisions keeps the two
stages from disagreeing about where a question ends and its answer begins. There are no MIXED
rows in P3 (STRIP_COLOURED is empty).

Usage:
  python3 -m ingest.extract_asrjc26_p3_answers <unz> <questions.json> <outdir>
Output feeds `gen_answers_migration.py --type structured --paper 3`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from . import parts_dispatch
from . import inline_answers_prep_parts as P
from .parts import _strip_answer_dots
from .oxml import NS, Wq
from .asrjc26_p3_prep import COLOURS, SKIP_TABLES, FORCE_DELETE

STRIP_COLOURED = set()      # no mixed question/answer rows in this paper

SCOPE = ("ASRJC", "H2", "P3", 2026)
FIG = "\x00FIG\x00"
MR1, MR2 = "⁣R⁣", "⁣r⁣"      # red criteria text inside an answer line
MA, MC, MN = "⁣A⁣", "⁣C⁣", "⁣N⁣"
INCLUDE_COMMENTS = False
PLAIN_LISTS = True
ANSWER_BLUES = ("0000CC", "0000FF")
RED = "FF0000"
MQ = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
LABEL_MAP = {}
AR, EQ = " → ", " ⇌ "


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


#: Answer figures the user SNIPS: (qnum, label) -> dict(slots, n_fig, mode[, fill]).
#: file = ASRJC_H2_P3_Q<n>_ans-<slot>_2026.png.  Filled after the DISCOVER run.
#: mode "each": each FIG sentinel becomes one picture on its own line (slots in DOM order).
#: mode "marked": `fill` gives one replacement per sentinel: "@slot" = inline picture,
#:   "@!slot" = the whole block holding it IS that picture (consecutive same-slot blocks merge).
FIGURE_PLAN = {
    (1, "(b)(iv)"): dict(slots=["biv-1", "biv-2"], n_fig=4, mode="marked",      # the two alternative answers, one snip each
                         fill=["@!biv-1", "@!biv-1", "@!biv-2", "@!biv-2"]),
    (2, "(a)(ii)"): dict(slots=["aii"], n_fig=1, mode="each"),                # the whole equation drawing
    (2, "(a)(iii)"): dict(slots=["aiii-1", "aiii-2"], n_fig=2, mode="marked",  # L, M structures (labels stay typed)
                          fill=["@aiii-1", "@aiii-2"]),
    (2, "(c)"):     dict(slots=["c"], n_fig=1, mode="each"),                  # intramolecular H-bond drawing
    (3, "(c)(ii)"): dict(slots=["cii"], n_fig=3, mode="marked",               # Born-Haber cycle (one drawing, 3 objects)
                         fill=["@!cii", "@!cii", "@!cii"]),
    (3, "(d)(i)"):  dict(slots=["di"], n_fig=1, mode="each"),                 # dot-and-cross LiAlH4
    (3, "(d)(iii)"): dict(slots=["diii"], n_fig=1, mode="each"),              # scheme with J, K, L drawn in
    (3, "(e)(i)"):  dict(slots=["ei"], n_fig=1, mode="each"),                 # anodising set-up
    (4, "(b)(ii)"): dict(slots=["bii"], n_fig=1, mode="marked", fill=["@!bii"]),    # step 3 row incl. its label
    (4, "(b)(iii)"): dict(slots=["biii"], n_fig=1, mode="marked", fill=["@!biii"]),  # step 5 row incl. its label
    (4, "(b)(iv)"): dict(slots=["biv"], n_fig=1, mode="each"),                # scheme with the alkene drawn in
    (4, "(c)"):     dict(slots=["c"], n_fig=4, mode="marked",                 # L, M, N, P table (labels in the snip)
                         fill=["@!c", "@!c", "@!c", "@!c"]),
    (4, "(d)(ii)"): dict(slots=["dii"], n_fig=2, mode="marked",               # the annotated graph (2 objects)
                         fill=["@!dii", "@!dii"]),
    (5, "(c)(i)"):  dict(slots=["ci"], n_fig=1, mode="each"),                 # Fig 5.1 with curly arrows
    (5, "(c)(ii)"): dict(slots=["cii"], n_fig=1, mode="each"),                # the dicarbonyl structure
    (5, "(d)"):     dict(slots=["d"], n_fig=5, mode="marked",                 # whole V / W / X structures table, labels in the snip
                         fill=["@!d"] * 5),
    (5, "(e)(ii)"): dict(slots=["eii"], n_fig=1, mode="each"),                # rate against [Z] graph
}
#: FIG sentinels that are NOT snipped (typed arrows etc.), in DOM order per part.
SENTINEL_FILL = {
    (1, "(b)(i)"): [EQ],
    (1, "(b)(ii)"): [EQ],
    (1, "(b)(iii)"): [EQ],
    (1, "(e)(i)"): [EQ],
    (3, "(b)(i)"): [AR],
    (3, "(c)(iii)"): [AR],
    (3, "(e)(ii)"): [AR, AR],
    (4, "(a)"): [AR],
}
#: (qnum, label) -> [(regex, replacement)], each must match.
TEXT_FIXES = {
    # the two mark notes beside the L and M structures
    (2, "(a)(iii)"): [(r"((?:<b>)?<img[^>]*>(?:</b>)?)\[1\]", r'\1<span class="note">[1]</span>')],
    # school typo, user ruled 2026-10-24: the question says 16.5 mol, so 16.5 / 2 = 8.25
    (4, "(d)(i)"): [(r"16\.2 \u00f7 2", "16.5 \u00f7 2")],
}
NOTE_LINES = {}
NOTE_TEXT = {}
#: Post-assembly fixes on a question's whole worked-solution html:
#: qnum -> [(regex, replacement-or-callable, expected_count)]. Each is a declared, counted rewrite.
POST_FIXES = {
    # 1(e)(ii): the cube root of a fraction typed as a Word overline -> the house .sqrt / .rad markup
    1: [(r'\u221a<span style="text-decoration:overline">((?:(?!</span></span>).)*?(?:<span class="frac">.*?</span></span>)?)\s*</span>',
         lambda m: '<span class="sqrt"><span class="rad">%s</span></span>' % m.group(1).strip(), 1),
        # spaces the school typed inside the brackets of the Kstab / Kc fractions
        (r"\[ (?=N)", "[", 10),
        (r"(?<=\d|>|\)) \]", "]", 10)],
}
OL_PARTS = set()
FORCE_Q = set()
ANS_FIG = set()
MARK_START = re.compile(r"\s*(?:<b>)?\s*\[\s*(?:[–−\-]?\d+(?:\.\d+)?|\d/\d)\b")
META = re.compile(r"^(LO\s*\d|AO[AB]\b|AO[AB]\s*[–-]|M\s*\(\d\)$)")


#: Superscript signs: the paper types en dashes and hyphens; the minus sign is
#: U+2212 (the question side uses both, so one rule is applied here).
def _sup_minus(t):
    return re.sub(r"<sup>([^<]*)</sup>",
                  lambda m: "<sup>%s</sup>" % re.sub(r"[–\-](?=\d|$|\s)", "−", m.group(1)), t)


def _txt(el):
    return "".join(el.itertext(Wq + "t"))


def _run_colour(rr):
    c = rr.find("w:rPr/w:color", NS)
    return (c.get(Wq + "val") or "").upper() if c is not None else ""


def answer_rows(src_document_xml: Path):
    """Rows the questions stage deleted (original indices) -> answer rows."""
    tmp = Path(str(src_document_xml) + ".prep.tmp")
    log = P.prep(src_document_xml, tmp, force_delete=FORCE_DELETE,
                 colours=COLOURS, skip_tables=SKIP_TABLES)
    tmp.unlink()
    rows = {(l[0], l[1]) for l in log
            if len(l) == 4 and str(l[2]).startswith("delete")}
    return rows - set(STRIP_COLOURED)


def _own_runs(p):
    out = []
    for rr in p.iter(Wq + "r"):
        q = rr.getparent()
        while q is not None and q.tag != Wq + "p":
            q = q.getparent()
        if q is p:
            out.append(rr)
    return out


def _wrap_red(p):
    """Red marker text that says something ("correct sign", "with units") sits inline in the
    blue answer line: bracket each such group so `_clean` can emit it as span.note. A bare
    red "[1]" is left alone (the mark logic reads it as a plain mark)."""
    groups, cur = [], []
    for rr in _own_runs(p):
        tx = _txt(rr)
        if not tx.strip():
            continue
        if _run_colour(rr) == RED:
            cur.append(rr)
        else:
            if cur:
                groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    for g in groups:
        if not re.search(r"[A-Za-z]", "".join(_txt(r) for r in g)):
            continue
        for rr, mk, add in ((g[0], MR1, "addprevious"), (g[-1], MR2, "addnext")):
            r = etree.Element(Wq + "r")
            etree.SubElement(r, Wq + "t").text = mk
            getattr(rr, add)(r)


def _mark(p, mk):
    r = etree.Element(Wq + "r")
    etree.SubElement(r, Wq + "t").text = mk
    ppr = p.find("w:pPr", NS)
    p.insert(0 if ppr is None else 1, r)


def mark_zones(src_document_xml: Path, dst_document_xml: Path):
    arows = answer_rows(src_document_xml)
    tree = etree.parse(str(src_document_xml))
    body = tree.getroot().find("w:body", NS)
    tables = body.findall("w:tbl", NS)
    assert len(tables) == 8, len(tables)
    log = []
    for ti, tbl in enumerate(tables):
        if ti < SKIP_TABLES:
            continue
        for ri, tr in enumerate(tbl.findall("w:tr", NS)):
            key = (ti, ri)
            mixed = key in STRIP_COLOURED
            if key not in arows and not mixed:
                continue
            for p in tr.iter(Wq + "p"):
                tot = red = blue = 0
                for rr in p.iter(Wq + "r"):
                    tx = _txt(rr).strip()
                    if not tx:
                        continue
                    v = _run_colour(rr)
                    tot += len(tx)
                    red += len(tx) if v == RED else 0
                    blue += len(tx) if v in ANSWER_BLUES else 0
                # OMML (MathType-free equations) carry no w:r colour: they are answer text
                mt = sum(len((t.text or "").strip()) for t in p.iter(MQ + "t"))
                tot += mt
                blue += mt
                if mixed and not (blue or red):
                    continue
                if not tot and not mixed:
                    # empty / picture-only paragraph of an answer row
                    if not any(etree.QName(x).localname in P.FIG_TAGS for x in p.iter()):
                        continue
                mk = MN if (tot and red == tot) else MA
                if mk == MA and red:
                    _wrap_red(p)
                _mark(p, mk)
                log.append((ti, ri, mk[1], _txt(p).strip()[:50]))
    tree.write(str(dst_document_xml), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return log


def _clean(line: str) -> str:
    line = re.sub("[⁣]?[ANC][⁣]", "", line)
    line = line.replace(MR1, '<span class="note">').replace(MR2, "</span>")
    line = line.replace("\x00C\x00", " ").replace("\t", " ")
    line = re.sub(r"\s*<br>\s*", " ", line).strip()
    line = _strip_answer_dots(line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    return line


NL = "\x02NL\x02"


def split_part(html: str):
    """-> (answer_blocks, comment_items).

    `answer_blocks` is a list of ('p'|'ul', html, is_note) in DOM order.
    A `<ul>` group holds its own <li> items, each with a zone marker.
    A Word table is ONE block: its cell paragraphs arrive as separate lines, so
    the lines from `<table` to `</table>` are joined (NL tokens become <br>).
    """
    blocks, comments = [], []
    lines, buf = [], None
    for line in html.split("\n"):
        if buf is not None:
            buf.append(line)
            if "</table>" in line:
                lines.append(NL.join(buf))
                buf = None
            continue
        if line.lstrip().startswith("<table") and "</table>" not in line:
            buf = [line]
            continue
        lines.append(line)
    if buf is not None:
        lines.append(NL.join(buf))
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("<ul"):
            items = re.findall(r"<li>(.*?)</li>", s, flags=re.S)
            marked = [i for i in items if MA in i or MN in i]
            a_items = [_clean(i) for i in marked]
            c_items = [_clean(i) for i in items if MC in i]
            if a_items:
                blocks.append(("ul", a_items, all(MN in i and MA not in i for i in marked)))
            comments.extend(c_items)
            continue
        if s.startswith("<table"):
            if MA in s or MN in s:
                # a cell holding a marked paragraph is an ANSWER cell (given cells stay plain)
                s = re.sub(r"<td([^>]*)>((?:(?!</td>).)*?%s(?:(?!</td>).)*?)</td>" % re.escape(MA),
                           lambda m: '<td%s><span class="ans">%s</span></td>' % (m.group(1), m.group(2)),
                           s, flags=re.S)
                body = _clean(s).replace(NL, "<br>")
                body = re.sub(r"(<br>\s*){2,}", "<br>", body)
                body = re.sub(r"(<td[^>]*>)\s*<br>|<br>\s*(</td>)", r"\1\2", body)
                blocks.append(("p", body, False))
            continue
        if MC in s:
            body = _clean(s)
            if re.fullmatch(r"(<[^>]+>)*Comments(</[^>]+>)*", body):
                continue
            if body:
                comments.append(body)
        elif MN in s:
            blocks.append(("p", _clean(s), True))
        elif MA in s:
            blocks.append(("p", _clean(s), False))
    return blocks, comments


def _img(path):
    return '<img class="ws-fig" data-asset="%s" alt="">' % path


def build(unz: Path, outdir: Path, bank_questions: list, first_ordinals: dict,
          workdir: Path):
    """-> (worked: {qnum: html}, assets: [...], report: [str])"""
    report = []
    marked = workdir / "marked"
    if marked.exists():
        shutil.rmtree(marked)
    shutil.copytree(unz, marked)
    zlog = mark_zones(unz / "word/document.xml", marked / "word/document.xml")

    numbering = marked / "word/numbering.xml"
    questions, _figs, anomalies, shape = parts_dispatch.parse(
        marked / "word/document.xml", marked / "word/_rels/document.xml.rels",
        numbering if numbering.exists() else None, scope=SCOPE)
    report.append("container shape: %s; %d questions parsed" % (shape, len(questions)))

    bank_labels = {q["question_number"]: [p["label"] for p in q["parts"]]
                   for q in bank_questions}
    bank_marks = {(q["question_number"], p["label"]): p["marks"]
                  for q in bank_questions for p in q["parts"]}

    worked, assets = {}, []
    used_plan = set()
    for q in questions:
        blocks_out = []
        seen_labels = set()
        for p in q.parts:
            label = LABEL_MAP.get((q.qnum, p.label), p.label)
            blocks, comments = split_part(p.html)
            key = (q.qnum, label)
            plan = FIGURE_PLAN.get(key)
            if not blocks and not comments and not plan:
                continue
            if label not in bank_labels.get(q.qnum, []):
                report.append("!! Q%d %s: answer part has no bank part" % (q.qnum, label))
                continue
            if label in seen_labels:
                report.append("!! Q%d %s: duplicate answer part" % (q.qnum, label))
            seen_labels.add(label)

            fn = lambda s, qn=q.qnum: "ASRJC_H2_P3_Q%d_ans-%s_2026.png" % (qn, s)
            # ---- figure handling ----
            n_sent = sum(b[1].count(FIG) if b[0] == "p"
                         else sum(i.count(FIG) for i in b[1]) for b in blocks)
            fill_list = (plan["fill"] if plan and plan["mode"] == "marked"
                         else SENTINEL_FILL.get(key))
            if plan:
                used_plan.add(key)
                if n_sent != plan["n_fig"]:
                    raise SystemExit("Q%d%s: expected %d FIG sentinels in the "
                                     "answer, parser found %d"
                                     % (q.qnum, label, plan["n_fig"], n_sent))
                if plan["mode"] == "marked" and len(fill_list) != n_sent:
                    raise SystemExit("Q%d%s: fill has %d entries for %d sentinels"
                                     % (q.qnum, label, len(fill_list), n_sent))
            elif key in SENTINEL_FILL:
                if n_sent != len(SENTINEL_FILL[key]):
                    raise SystemExit("Q%d%s: SENTINEL_FILL has %d entries, parser "
                                     "found %d sentinels" % (q.qnum, label,
                                     len(SENTINEL_FILL[key]), n_sent))
            elif n_sent:
                if os.environ.get("DISCOVER"):
                    report.append("?? Q%d%s: %d FIG sentinel(s): %s" % (q.qnum, label, n_sent,
                        " | ".join(re.sub(r"<[^>]+>", "", b[1] if b[0] == "p" else " ".join(b[1])).replace(FIG, "<FIG>")[:90] for b in blocks)))
                else:
                    raise SystemExit("Q%d%s: %d undeclared FIG sentinel(s) in the "
                                     "answer" % (q.qnum, label, n_sent))

            if fill_list is not None:
                reps = iter(fill_list)
                def sub(_m, reps=reps):
                    return next(reps)
                new = []
                for kind, body, note in blocks:
                    if kind == "p":
                        body = re.sub(re.escape(FIG), sub, body)
                    else:
                        body = [re.sub(re.escape(FIG), sub, i) for i in body]
                    new.append((kind, body, note))
                blocks = new
                if list(reps):
                    raise SystemExit("Q%d%s: unused SENTINEL_FILL entries" % (q.qnum, label))
                # "@!slot" -> the whole block that holds it is the image;
                # "@slot" -> an inline image
                new, last = [], None
                for kind, body, note in blocks:
                    if kind == "p" and not body.strip():
                        new.append((kind, body, note))   # empty spacer: transparent to the collapse
                        continue
                    if kind == "p" and re.search(r"@!([\w-]+)", body):
                        slot = re.search(r"@!([\w-]+)", body).group(1)
                        if slot != last:
                            new.append(("p", "<p>%s</p>" % _img(fn(slot)), False))
                        last = slot
                        continue
                    last = None
                    if kind == "p":
                        body = re.sub(r"@([\w-]+)", lambda m: _img(fn(m.group(1))), body)
                    new.append((kind, body, note))
                blocks = new

            if os.environ.get("DUMP") == "%d%s" % (q.qnum, label):
                for _b in blocks:
                    print("DUMP", repr(_b))
            for rx, rep in TEXT_FIXES.get(key, []):
                hit = False
                new = []
                for kind, body, note in blocks:
                    if kind == "p":
                        nb, n = re.subn(rx, rep, body)
                        hit |= bool(n)
                        body = nb
                    new.append((kind, body, note))
                if not hit:
                    if os.environ.get("SOFTFIX"):
                        report.append("?? Q%d%s: TEXT_FIXES pattern did not match: %s" % (q.qnum, label, rx))
                        continue
                    raise SystemExit("Q%d%s: TEXT_FIXES pattern did not match: %s"
                                     % (q.qnum, label, rx))
                blocks = new

            # fills may carry several lines ("\n"): one block each
            exp = []
            for kind, body, note in blocks:
                if kind == "p" and "\n" in body:
                    exp += [("p", ln, note) for ln in body.split("\n")]
                else:
                    exp.append((kind, body, note))
            blocks = exp
            # house sign conventions
            def _fx(t):
                t = t.replace("", "")     # a Symbol minus typed after a hyphen minus (shows as a box in Word)
                t = _sup_minus(t)
                t = "".join(pc if pc.startswith("<") else re.sub(r" {2,}", " ", pc)
                            for pc in re.split(r"(<[^>]+>)", t))
                return t.replace("<sup>⦵</sup>", '<sup class="pl-sym">⦵</sup>')
            blocks = [(k, _fx(b) if k == "p" else [_fx(i) for i in b], n)
                      for k, b, n in blocks]

            # ---- plain "[n]" marks join the styled ones (the source types both) ----
            _plain = lambda t: re.sub(
                r'(<span class="mk">\[\d\]</span>)|(?<![\w\[])\[([1-9])\](?![\w\]])',
                lambda m: m.group(1) or '<span class="mk">[%s]</span>' % m.group(2), t)
            blocks = [(k, (_plain(b) if not n else b) if k == "p"
                       else [_plain(i) for i in b], n)
                      for k, b, n in blocks]
            # ---- trailing redundant part-mark ----
            marks = bank_marks.get(key)
            mk_all = []
            for kind, body, note in blocks:
                if kind == "p" and not note:
                    mk_all += re.findall(r'<span class="mk">\[(\d+)\]</span>', body)
            if mk_all and marks is not None and sum(int(x) for x in mk_all) != marks and len(mk_all) > 1:
                report.append("!! Q%d %s: the answer shows mark(s) %s, the question part is [%s]"
                              % (q.qnum, label, mk_all, marks))
            if len(mk_all) == 1 and marks is not None and int(mk_all[0]) == marks:
                blocks = [(k, re.sub(r'\s*<span class="mk">\[\d+\]</span>', "", b)
                           if k == "p" and not n else b, n) for k, b, n in blocks]
            blocks = [(k, re.sub(r'<span class="mk">(\[\d+\])</span>', r"\1", b)
                       if k == "p" else b, n) for k, b, n in blocks]
            blocks = [(k, b, n) for k, b, n in blocks
                      if (k == "ul" and b) or (k == "p" and b.strip())]

            # ---- render ----
            body_html = []
            mode = plan["mode"] if plan else None
            if mode == "bare":
                body_html.append("<p>%s</p>" % _img(fn(plan["slots"][0])))
                blocks = []
            elif mode in ("lead_text", "lead_notes"):
                labs = plan.get("labels") or [None] * len(plan["slots"])
                for sl, lb in zip(plan["slots"], labs):
                    if lb:
                        body_html.append("<p><b>%s</b></p>" % lb)
                    body_html.append("<p>%s</p>" % _img(fn(sl)))
                # HCI: a lead_text part keeps its <ul> mark-scheme bullets too
                blocks = [(k, b, n) for k, b, n in blocks
                          if (k == "ul" and mode == "lead_text") or
                          (k == "p" and FIG not in b
                           and (mode == "lead_text" or n)
                           and not re.fullmatch(r"\s*or\s*", b, flags=re.I))]
            elif mode == "each":
                slots = iter(plan["slots"])
                new = []
                for kind, body, note in blocks:
                    if kind == "p" and FIG in body:
                        # the picture on its own line, the text around it after/before
                        pieces = re.split("(%s)" % re.escape(FIG), body)
                        for pc in pieces:
                            if pc == FIG:
                                new.append(("p", _img(fn(next(slots))), note))
                            elif pc.strip():
                                new.append(("p", pc.strip(), note))
                        continue
                    new.append((kind, body, note))
                blocks = new
            # ---- marking-criteria lines -> red notes (see MARK_START / NOTE_LINES) ----
            def _txt_of(k, b):
                return b if k == "p" else " | ".join(b)
            blocks = [(k, b, True if (k == "p" and not n and not b.lstrip().startswith("<table")
                                      and MARK_START.match(b)) else n) for k, b, n in blocks]
            for rx in NOTE_LINES.get(key, []):
                hit = False
                nb = []
                for k, b, n in blocks:
                    first = b if k == "p" else (b[0] if b else "")
                    if not n and re.search(rx, first) and not first.lstrip().startswith("<table"):
                        n, hit = True, True
                    nb.append((k, b, n))
                if not hit:
                    raise SystemExit("Q%d%s: NOTE_LINES pattern matched no block: %s" % (q.qnum, label, rx))
                blocks = nb
            # a lone red "[n]" note equal to a one-mark part is the part mark again
            if marks == 1 and not mk_all:
                lone = [b for b in blocks if b[0] == "p" and b[2]
                        and re.fullmatch(r"\s*\[1\]\s*", b[1])]
                others = [b for b in blocks if b[0] == "p" and b[2] and b not in lone
                          and re.search(r"\[\d\]", b[1])]
                if len(lone) == 1 and not others and not any(
                        b[0] == "p" and not b[2] and re.search(r"\[\d\]", b[1])
                        for b in blocks):
                    blocks = [b for b in blocks if b not in lone]

            if key in NOTE_TEXT:
                hit = [i for i, b in enumerate(blocks)
                       if b[0] == "p" and b[2] and re.fullmatch(r"\s*\[\d\]\s*", b[1])]
                if len(hit) != 1:
                    raise SystemExit("Q%d%s: NOTE_TEXT needs exactly one lone red mark"
                                     % (q.qnum, label))
                blocks[hit[0]] = ("p", NOTE_TEXT[key], True)
            # tables: a comparison table, values in answer spans
            def _table(t):
                t = t.replace('class="qt"', 'class="cmp"')
                t = re.sub(r"</?b>", "", t)
                t = re.sub(r"(<br>\s*)+(</td>)", r"\2", t)
                t = re.sub(r"(</ul>)(\s*<br>)+|(<br>\s*)+(<ul)", lambda m: m.group(1) or m.group(4), t)
                t = re.sub(r"<td>(?=[^<]*\w)(.*?)</td>",
                           lambda m: "<td>%s</td>" % m.group(1), t)
                # answer cells (carry a [0.5] mark, or the "-" fill-ins) -> blue; given cells stay plain
                t = re.sub(r"<td([^>]*)>((?:(?!</td>).)*?\[0\.5\](?:(?!</td>).)*?)</td>",
                           r'<td\1><span class="ans">\2</span></td>', t, flags=re.S)
                t = re.sub(r"<td([^>]*)>-</td>", r'<td\1><span class="ans">-</span></td>', t)
                return t
            for kind, body, note in blocks:
                def wrap(t, note=note):
                    if re.fullmatch(r"\s*(<p>)?\s*<img[^>]*>\s*(</p>)?\s*", t):
                        return re.sub(r"</?p>", "", t).strip()
                    return '<span class="%s">%s</span>' % ("note" if note else "ans", t)
                if kind == "p" and body.lstrip().startswith("<table"):
                    body_html.append(_table(body.strip()))
                elif kind == "p":
                    body_html.append("<p>%s</p>" % wrap(body))
                else:
                    body_html.append('<ul class="stmts">%s</ul>'
                                     % "".join("<li>%s</li>" % wrap(i) for i in body))
            if comments and INCLUDE_COMMENTS:
                body_html.append('<p class="mark-note"><b>Comments</b></p>')
                body_html.append('<ul class="marks mark-note">%s</ul>'
                                 % "".join("<li>%s</li>" % c for c in comments))
            if key in OL_PARTS:
                items = re.findall(r'<p><span class="ans">(.*?)</span></p>', "\n".join(body_html), flags=re.S)
                assert len(items) == len(body_html), (key, len(items), len(body_html))
                body_html = ['<ol class="stmts">%s</ol>' % "".join("<li><span class=\"ans\">%s</span></li>" % i for i in items)]
            blocks_out.append(
                '<div class="part"><span class="lab">%s</span>'
                '<div class="body">%s</div></div>' % (label, "\n".join(body_html)))

            if plan:
                for k, s in enumerate(plan["slots"]):
                    assets.append(dict(question=q.qnum, slot="ans-" + s,
                                       path=fn(s), part=label))
        # every bank part that carries marks must have an answer
        missing = [l for l in bank_labels.get(q.qnum, [])
                   if l not in seen_labels and bank_marks.get((q.qnum, l))]
        if missing:
            report.append("!! Q%d: bank parts with marks but no answer: %s" % (q.qnum, missing))
        html_q = "\n".join(blocks_out)
        html_q = re.sub(r"<(sup|sub)> </\1>", "", html_q)           # empty spacer scripts
        html_q = re.sub(r'<p><span class="ans"><b> </b></span></p>\n?', "", html_q)
        html_q = re.sub(r"<b></b>", "", html_q)                       # empty bold runs
        html_q = re.sub(r"(<(sup|sub)>[^<]*?)\s+(</\2>)", r"\1\3 ", html_q)   # space inside a script -> after it
        html_q = re.sub(r"(\d) x (10<sup>)", "\\1 × \\2", html_q)      # typed "x" -> multiplication sign
        html_q = re.sub(r" {2,}", " ", html_q)
        # the source sets "C3H8" / "H2O" / "H2" as ONE subscript on P (digits not lowered
        # again): nest the digits so P<sub>C<sub>3</sub>H<sub>8</sub></sub> reads correctly
        html_q = re.sub(r"<sub>((?:[A-Z][a-z]?\d*)+)</sub>",
                        lambda m: "<sub>%s</sub>" % re.sub(r"(\d+)", r"<sub>\1</sub>", m.group(1))
                        if re.search(r"\d", m.group(1)) else m.group(0), html_q)
        html_q = html_q.replace("‒", "−")                      # figure dash typed as minus
        html_q = re.sub(r"\s*<sup>o</sup>C", " °C", html_q)           # superscript o -> degree sign
        html_q = re.sub(r"([\d)]|</sup>) x (?=[\d(])", "\\1 × ", html_q)
        html_q = re.sub(r"(?<=\d) – (?=\d)", " − ", html_q)      # en dash used as minus
        html_q = re.sub(r"(?<= = )-(?=lg)", "−", html_q)
        # ---- generic tidy of Word run noise (each rule is a plain, reversible rewrite) ----
        html_q = html_q.replace("</u><u></u><u>", " ")            # a space lost between two underlined runs
        html_q = html_q.replace("<i> </i>", " ")
        html_q = re.sub(r"<(sub|sup)></\1>", "", html_q)
        html_q = re.sub(r"<i><sub>([^<]*)</sub></i>", r"<sub>\1</sub>", html_q)   # descriptors are upright
        for _ in range(2):
            html_q = (html_q.replace("</b><b>", "").replace("</u><u>", "")
                      .replace("</i><i>", ""))
        html_q = re.sub(r"<i>\s+([A-Za-z])</i>", r" <i>\1</i>", html_q)          # "<i> K</i>" -> " <i>K</i>"
        html_q = re.sub(r'(<span class="note">)(\s+)', r"\2\1", html_q)         # space belongs outside the note
        html_q = html_q.replace('<span class="ans"> ', '<span class="ans">')
        html_q = re.sub(r"(?<=\S) {2,}", " ", html_q)
        html_q = re.sub(r'<span class="mk">(\[\d+\])</span>', r"\1", html_q)   # marks inside lists stay plain text
        if PLAIN_LISTS:
            # house ruling (ASRJC 2026 P2, 2026-10-23): bullets in answer lists render flush right,
            # so each bullet becomes a plain paragraph
            html_q = re.sub(r'<ul class="stmts">(.*?)</ul>',
                            lambda m: "\n".join("<p>%s</p>" % i for i in re.findall(r"<li>(.*?)</li>", m.group(1))),
                            html_q, flags=re.S)
        for rx, rep, cnt in POST_FIXES.get(q.qnum, []):
            html_q, n = re.subn(rx, rep, html_q)
            if n != cnt:
                raise SystemExit("Q%d POST_FIXES %r matched %d, expected %d" % (q.qnum, rx, n, cnt))
        worked[q.qnum] = '<div class="worked-solution">\n%s\n</div>' % html_q
    unused = set(FIGURE_PLAN) - used_plan
    if unused:
        raise SystemExit("FIGURE_PLAN entries never matched a part: %s" % sorted(unused))

    # ordinals: offsets after the question side, DOM order per question
    per_q = {}
    for a in assets:
        per_q[a["question"]] = per_q.get(a["question"], 0) + 1
        a["offset"] = per_q[a["question"]]
    # DOM order must equal plan order: verify by position in the html
    for qn, html in worked.items():
        pos = [(html.find(a["path"]), a["path"]) for a in assets if a["question"] == qn]
        if [p for p, _ in pos] != sorted(p for p, _ in pos) or any(p < 0 for p, _ in pos):
            raise SystemExit("Q%d: asset order does not follow DOM order: %s" % (qn, pos))
    return worked, assets, report, anomalies, zlog


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("questions_json")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    bank = json.loads(Path(a.questions_json).read_text(encoding="utf-8"))
    worked, assets, report, anomalies, zlog = build(Path(a.unz), out, bank, {}, out)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in worked.items()}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "answer_assets.json").write_text(
        json.dumps([{k: v for k, v in x.items() if k != "part"} for x in assets],
                   indent=1), encoding="utf-8")
    (out / "zones.txt").write_text("\n".join(map(str, zlog)), encoding="utf-8")
    print("\n".join(report))
    print("answer figures:", len(assets))
    for x in assets:
        print("  Q%d %-10s %-8s %s" % (x["question"], x["part"], x["slot"], x["path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
