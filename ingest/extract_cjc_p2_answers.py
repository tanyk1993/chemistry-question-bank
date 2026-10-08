"""CJC 2024 H2 P2 -- worked solutions from the "WORKED SOLUTIONS" docx.

Document shape (2026-10-08): the question paper itself (paragraph flow, NOT
tables) with every answer in a FLOATING BLUE TEXT BOX (`wps:txbx`, only the
`mc:Choice` copy is read) anchored to the paragraph of the dotted answer line.
Answer drawings (structures, the orbital diagram, the mechanism) are free
OLE/WMF objects or native shapes sitting in the flow, not in boxes.

How it is read (a plain linear walk, no parts_flow):
  1. `flow_parts_prep.prep` types the Word auto-numbered part labels in, so every
     part paragraph starts with its label as visible text.
  2. Walk the body: a paragraph whose own text (text-box text excluded) starts
     with a question number / "(a)" / "(i)" sets the current (question, part).
  3. A text box whose runs are answer-blue belongs to the current part; boxes in
     any other colour (examiner's comments, figure labels, red marker dots) are
     ignored. The part's answer = its boxes' paragraphs, in document order.
  4. Answer figures the user SNIPPED are declared in FIGURE_PLAN.

User decisions (2026-10-08): the "- similar to 2022/P2/..." remarks and the
"EXAMINER'S COMMENTS" box are omitted.

Output feeds `gen_answers_migration.py --type structured --paper 2`:
  worked_solutions.json, answer_assets.json.

Run:  python3 -m ingest.extract_cjc_p2_answers <unz> <questions.json> <outdir>
(<unz> is the UNZIPPED answers docx; it is prepped into <outdir>/unz_prep.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import flow_parts_prep
from .oxml import NS, Wq, paragraph_html
from .extract_cjc_p1_answers import _table_cmp, _tidy_ws

MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
WPS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
FIG = "\x00FIG\x00"
FILE_FMT = "CJC_H2_P2_Q%d_ans-%s_2024.png"

ANSWER_BLUE = {"0000FF", "0432FF", "0000CC"}
ROMAN = {"i", "ii", "iii", "iv", "v", "vi"}

#: (qnum, label) -> (slot, where): the snipped answer figure and whether it sits
#: BEFORE or AFTER the part's typed text.
FIGURE_PLAN = {
    (1, "(a)"): ("a", "after"),
    (2, "(e)(iii)"): ("eiii", "after"),
    (3, "(a)(iii)"): ("aiii", "after"),
    (3, "(b)(ii)"): ("bii", "after"),
    (3, "(b)(iii)"): ("biii", "after"),
    (5, "(e)"): ("e", "after"),
    (5, "(f)(i)"): ("fi", "before"),
    (5, "(f)(iv)"): ("fiv", "after"),
}

#: Answer boxes NOT carried (their content is the snip).
DROP_BOXES = {(3, "(a)(iii)"), (2, "(e)(iii)")}

AR, EQ = " → ", " ⇌ "


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


#: FIG sentinels in carried boxes, in DOM order (MathType working has no text
#: layer; the equilibrium arrow is a glyph picture).
SENTINEL_FILL = {
    (1, "(d)(i)"): [_frac("1", "28") + " \u00f7 " + _frac("1", "<i>m</i>"),
                    _frac("5.6", "2.0")],
    (4, "(e)(iv)"): [EQ],
}

#: Typed prefixes (the question's own printed labels around the answer line),
#: one per answer paragraph in order; None = no prefix.
LEAD = {
    (2, "(e)(ii)"): ["Anion: "],
    (4, "(c)"): ["Observations in step I: ", "Equation: ",
                 "Observations in step II: ", "Equation: ", None],
    (5, "(c)"): ["Number of σ bonds: ", "Number of π bonds: "],
    (5, "(d)"): ["Step 1: ", "Step 2: "],
    (5, "(f)(iii)"): ["Fig. 5.1: ", "Fig. 5.2: "],
    (6, "(a)(i)"): ["Anode: ", "Cathode: ", "Overall: "],
    (6, "(a)(iii)"): ["Anode: ", "Cathode: "],
    (6, "(c)"): ["Name of mechanism: ", "Reagent(s) and conditions: "],
}

#: Counted text fixes on the part's carried paragraphs: (q, label) -> [(rx, rep, n)]
TEXT_FIXES = {
    # "10-10" typed entirely as a superscript after a times sign (exponent lost its base)
    (4, "(e)(ii)"): [(r"\u00d7 <sup>10\u2212(\d+)</sup>", "\u00d7 10<sup>\u2212\\1</sup>", 1),
                     # the school types CuCrO4 for CuC2O4 (chromate for ethanedioate)
                     (r"CuCrO<sub>4</sub>", "CuC<sub>2</sub>O<sub>4</sub>", 1),
                     # house square-root markup (.sqrt/.rad), no inline style
                     (r'\u221a<span style="text-decoration:overline">(.*?)</span>',
                      r'<span class="sqrt"><span class="rad">\1</span></span>', 1)],
    (3, "(a)(iv)"): [(r"CO<sub>2,</sub>", "CO<sub>2</sub>,", 1)],
    (4, "(e)(v)"): [(r'(2H<sup>\+</sup>) (E<sup class="pl-sym">\u29b5</sup><sub>cell</sub>)', r"\1<br>\2", 1)],
    (4, "(e)(iii)"): [(r"\u00d7 <sup>10\u2212(\d+)</sup>", "\u00d7 10<sup>\u2212\\1</sup>", 2)],
    # authoring slip in the source: the arrow alone is underlined in each half-equation
    (6, "(a)(i)"): [(r"<u>\u2192</u>", "\u2192", 3)],
}

SIMILAR_RX = re.compile(
    r"(?:<b>\s*</b>)?\s*[–‒\-]\s*[Ss]imilar to 2022/P2/Q\d\([a-z]\)(?:\([a-z]+\))?")
SIMILAR_EXPECTED = 3   # Q3(a)(iv), Q5(b), Q5(c)


def _own_text(p) -> str:
    out = []
    for t in p.iter(Wq + "t"):
        if any(etree.QName(a).localname == "txbxContent" for a in t.iterancestors()):
            continue
        out.append(t.text or "")
    return "".join(out)


def _boxes(p):
    """txbxContent elements of the mc:Choice copy of every text box in p."""
    out = []
    for ac in p.iter("{%s}AlternateContent" % MC):
        ch = ac.find("{%s}Choice" % MC)
        tb = ch.find(".//{%s}txbx" % WPS) if ch is not None else None
        if tb is not None:
            c = tb.find(Wq + "txbxContent")
            if c is not None:
                out.append(c)
    return out


def _is_answer_box(c) -> bool:
    for r in c.iter(Wq + "r"):
        if "".join(x.text or "" for x in r.iter(Wq + "t")).strip():
            col = r.find("w:rPr/w:color", NS)
            if col is not None and (col.get(Wq + "val") or "").upper() in ANSWER_BLUE:
                return True
    return False


_LAB = re.compile(r"^\s*((?:\([a-z]{1,3}\)\s*){1,2})")


def _context(own: str, qnum: int, letter: str | None):
    """-> (qnum, letter, label_or_None) after reading a paragraph's own text."""
    m = re.match(r"^\s*(\d)\s*(?=[A-Z(])", own)
    if m and int(m.group(1)) == qnum + 1:
        qnum, letter = int(m.group(1)), None
        own = own[m.end():]
    m = _LAB.match(own)
    if not m:
        return qnum, letter, None
    toks = re.findall(r"\(([a-z]{1,3})\)", m.group(1))
    if toks[0] in ROMAN and not (toks[0] == "i" and False):
        if letter is None:
            return qnum, letter, None
        return qnum, letter, "(%s)(%s)" % (letter, toks[0])
    letter = toks[0]
    if len(toks) == 2 and toks[1] in ROMAN:
        return qnum, letter, "(%s)(%s)" % (letter, toks[1])
    return qnum, letter, "(%s)" % letter


def _merge(h: str) -> str:
    """Join adjacent same-tag runs; a whitespace-only run keeps its space."""
    for _ in range(4):
        h = re.sub(r"<(b|u|i|sup|sub)>(\s+)</\1>", r"\2", h)
        for t in ("b", "u", "sup", "sub"):
            h = h.replace("</%s><%s>" % (t, t), "")
        h = re.sub(r"<(b|u|i|sup|sub)></\1>", "", h)
    return h


def _clean(h: str) -> str:
    h = h.replace("\x00C\x00", "")
    h = h.replace("<b>", "").replace("</b>", "")      # the author types answers in bold
    h = _merge(h)
    h = re.sub(r"\s*<br>\s*", " ", h)
    h = h.replace("\t", "   ") if re.search(r"\S\s*\t\s*\S", h) else h.replace("\t", " ")
    h = re.sub(r'<i class="el">(.*?)</i>', r"\1", h)
    return h


def _minus(h: str) -> str:
    h = re.sub(r"<sup>([^<]*)</sup>",
               lambda m: "<sup>%s</sup>" % re.sub(r"[─‒–‐\-](?=\d|$|\s)|(?<=\d)[─‒–]",
                                                  "−", m.group(1)), h)
    h = h.replace("e‾", "e<sup>−</sup>")
    h = re.sub(r"\]‾", "]<sup>−</sup>", h)
    h = re.sub(r"\[BH<sub>4</sub>\]‾", "[BH<sub>4</sub>]<sup>−</sup>", h)
    h = h.replace("<sup>−</sup><sup>", "<sup>−")
    return h


def _items(content, tag):
    out = []
    for el in content:
        ln = etree.QName(el).localname
        if ln == "p":
            h = paragraph_html(el)
            if h.strip():
                out.append(("p", h))
        elif ln == "tbl":
            out.append(("tbl", el))
    return out


def _img(q, slot):
    return '<img class="ws-fig" data-asset="%s" alt="">' % (FILE_FMT % (q, slot))


def build(unz_prep: Path, bank):
    tree = etree.parse(str(unz_prep / "word/document.xml"))
    body = tree.getroot().find("w:body", NS)
    bank_labels = {q["question_number"]: [p["label"] for p in q["parts"]] for q in bank}
    bank_marks = {(q["question_number"], p["label"]): p["marks"] for q in bank for p in q["parts"]}

    raw = {}          # (q, label) -> [("p", html) | ("tbl", el)]
    order = []        # (q, label) in first-seen order
    qnum, letter, cur = 0, None, None
    for k in body:
        if etree.QName(k).localname != "p":
            continue
        own = _own_text(k)
        qnum, letter, lab = _context(own, qnum, letter)
        if lab:
            cur = (qnum, lab)
        for c in _boxes(k):
            if cur is None or not _is_answer_box(c):
                continue
            if cur in DROP_BOXES:
                continue
            if cur not in raw:
                raw[cur] = []
                order.append(cur)
            raw[cur].extend(_items(c, cur))
    for key in FIGURE_PLAN:
        if key not in raw:
            raw[key] = []
            order.append(key)

    report, similar_hits = [], 0
    worked, assets = {}, []
    per_q = {}
    for key in sorted(order, key=lambda x: (x[0], bank_labels[x[0]].index(x[1])
                                            if x[1] in bank_labels.get(x[0], []) else 999)):
        q, label = key
        if label not in bank_labels.get(q, []):
            raise SystemExit("answer part %s %s has no bank part" % (q, label))
        # --- sentinels ---
        n_fig = sum(h.count(FIG) for kind, h in raw[key] if kind == "p")
        fill = SENTINEL_FILL.get(key, [])
        if n_fig != len(fill):
            raise SystemExit("Q%d%s: %d FIG sentinels, %d fills" % (q, label, n_fig, len(fill)))
        fit = iter(fill)
        items = []
        for kind, h in raw[key]:
            if kind == "p":
                h = re.sub(re.escape(FIG), lambda m: next(fit), h)
            items.append((kind, h))
        # --- clean paragraphs ---
        paras = []
        for kind, h in items:
            if kind == "tbl":
                paras.append(("tbl", _table_cmp(h)))
                continue
            h = _minus(_clean(h))
            h, n = SIMILAR_RX.subn("", h)
            similar_hits += n
            h = _tidy_ws(h)
            plain = re.sub(r"<[^>]+>", "", h).strip()
            if not plain or re.fullmatch(r"[.\s]+", plain):
                continue
            paras.append(("p", h))
        for rx, rep, cnt in TEXT_FIXES.get(key, []):
            n_tot = 0
            new = []
            for kind, h in paras:
                if kind == "p":
                    h, n = re.subn(rx, rep, h)
                    n_tot += n
                new.append((kind, h))
            if n_tot != cnt:
                raise SystemExit("Q%d%s: text fix %r matched %d, expected %d" % (q, label, rx, n_tot, cnt))
            paras = new
        # --- part-specific joins / splits ---
        if key == (4, "(e)(iv)"):
            new = []
            for kind, h in paras:
                if kind == "p" and "Hence, the presence of" in h and not h.startswith("Hence"):
                    a, b = h.split("Hence, the presence of", 1)
                    new.append(("p", a.strip()))
                    new.append(("p", "Hence, the presence of" + b))
                elif kind == "p" and new and new[-1][1].endswith("the presence of "):
                    new[-1] = ("p", new[-1][1] + h)
                elif kind == "p" and new and new[-1][1].rstrip().endswith("the presence of"):
                    new[-1] = ("p", new[-1][1].rstrip() + " " + h)
                else:
                    new.append((kind, h))
            paras = new
        paras = [(k2, _tidy_ws(_minus(_merge(h)))) if k2 == "p" else (k2, h) for k2, h in paras]
        # --- prefixes ---
        lead = LEAD.get(key)
        nonlocal_p = [i for i, (k2, h) in enumerate(paras) if k2 == "p"]
        if lead is not None and len(lead) != len(nonlocal_p):
            raise SystemExit("Q%d%s: LEAD has %d entries, %d answer paragraphs: %r"
                             % (q, label, len(lead), len(nonlocal_p), [paras[i][1][:40] for i in nonlocal_p]))
        html = []
        for idx, (kind, h) in enumerate(paras):
            if kind == "tbl":
                html.append(h)
                continue
            pi = nonlocal_p.index(idx)
            pre = lead[pi] if lead else None
            # em-space indent for working lines that continue with "="
            ind = "  " if h.lstrip().startswith("=") and not pre else ""
            html.append("<p>%s<span class=\"ans\">%s%s</span></p>"
                        % (pre or "", ind, h.lstrip() if ind else h))
        if key in FIGURE_PLAN:
            slot, where = FIGURE_PLAN[key]
            tag = "<p>%s</p>" % _img(q, slot)
            html = [tag] + html if where == "before" else html + [tag]
            per_q[q] = per_q.get(q, 0) + 1
            assets.append(dict(question=q, slot="ans-" + slot, path=FILE_FMT % (q, slot),
                               part=label, offset=per_q[q]))
        part = ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                % (label, "\n".join(html)))
        worked.setdefault(q, []).append(part)
    if similar_hits != SIMILAR_EXPECTED:
        raise SystemExit("'similar to' remarks removed: %d, expected %d" % (similar_hits, SIMILAR_EXPECTED))
    # every bank part with marks must have an answer
    for q in bank_labels:
        have = {l for (qq, l) in order if qq == q}
        miss = [l for l in bank_labels[q] if bank_marks.get((q, l)) and l not in have]
        if miss:
            report.append("!! Q%d: bank parts with marks but no answer: %s" % (q, miss))
    out = {q: '<div class="worked-solution">\n%s\n</div>' % "\n".join(v) for q, v in worked.items()}
    # asset order must follow DOM order
    for q, html in out.items():
        pos = [html.find(a["path"]) for a in assets if a["question"] == q]
        if pos != sorted(pos) or any(p < 0 for p in pos):
            raise SystemExit("Q%d: asset order does not follow DOM order" % q)
    return out, assets, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("questions_json")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    prep = out / "unz_prep"
    flow_parts_prep.prep(a.unz, prep, "Answer all the questions in the space")
    bank = json.loads(Path(a.questions_json).read_text(encoding="utf-8"))
    worked, assets, report = build(prep, bank)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in sorted(worked.items())}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "answer_assets.json").write_text(
        json.dumps([{k: v for k, v in x.items() if k != "part"} for x in assets], indent=1),
        encoding="utf-8")
    print("\n".join(report))
    print("questions:", sorted(worked), "| answer figures:", len(assets))
    for x in assets:
        print("  Q%d %-10s %-8s %s" % (x["question"], x["part"], x["slot"], x["path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
