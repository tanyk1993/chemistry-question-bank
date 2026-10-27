"""CJC 2026 H2 P3 -- worked solutions from the "WORKED SOLUTIONS" docx (9476/03).

Copied from `extract_cjc26_p2_answers.py` (same school, same document shape: the
question paper in paragraph flow, answers in floating blue text boxes). The paper-
specific tables (FIGURE_PLAN, DROP_BOX_TEXT, TRUNCATE_FROM, SPLIT_BEFORE, LEAD,
TEXT_FIXES) are the only part that differs.

Original P2 docstring follows.

Same document shape as CJC 2024 P2 (see `extract_cjc_p2_answers.py`): the
question paper itself in paragraph flow, answers in FLOATING BLUE TEXT BOXES
(`wps:txbx`, `mc:Choice` copy only). 2026 adds three things the 2024 walk did
not need:

  * some answers are BLUE PARAGRAPHS IN THE FLOW (Q2(a)(iii) working, the
    "C3H7 can be ..." line of Q3(a)(i)), and the red "[1] for graph" line of
    Q2(b)(ii) is a flow paragraph too;
  * red-only text boxes are marking notes ("[1 correct partial charges ...]"),
    carried as plain marker lines after the part's text;
  * two ANSWER TABLES: Q4(c)(ii) (structures B, C, D -> one snip) and
    Q4(c)(iii) (reagents, read cell by cell).

Colours: answer = blue (0000FF / 0432FF / 0000CC) or the purple first sentence
of Q5(a)(iii) (7030A0); marks = red (FF0000 / EE0000 / FF3300). Anything else
(figure labels, examiner comments) is ignored.

Output feeds `gen_answers_migration.py --type structured --paper 3`:
  worked_solutions.json, answer_assets.json.

Run:  python3 -m ingest.extract_cjc26_p3_answers <unz> <questions.json> <outdir>
(<unz> is the UNZIPPED mark-scheme docx; it is prepped into <outdir>/unz_prep
by `cjc26_p2_prep`.)
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

from lxml import etree

from . import cjc26_p2_prep
from .oxml import NS, Wq, paragraph_html
from .extract_cjc_p1_answers import _table_cmp, _tidy_ws
from .extract_cjc_p2_answers import (  # shared, paper-independent helpers
    _boxes, _context as _context_p2, _merge, _minus, _own_text, FIG, MC, WPS)


def _context(own, qnum, letter):
    """As the shared walk, but Q3 is typed "3." (with a full stop) in this file."""
    return _context_p2(re.sub(r"^(\s*\d)\.", r"\1", own), qnum, letter)

MR = "{http://schemas.openxmlformats.org/officeDocument/2006/math}r"
FILE_FMT = "CJC_H2_P3_Q%d_ans-%s_2026.png"

ANSWER_COLS = {"0000FF", "0432FF", "0000CC", "3333FF", "7030A0"}
MARK_COLS = {"FF0000", "EE0000", "FF3300"}

#: (qnum, label) -> (slot, where). `where`: "before" | "after" | "after:N"
#: (after the N-th carried paragraph of the part).
FIGURE_PLAN = {
    (1, "(f)"): ("f", "before"),
    (1, "(g)(iii)"): ("giii", "before"),
    (2, "(b)(ii)"): ("bii", "before"),
    (2, "(c)"): ("c", "after"),
    (3, "(e)(iii)"): ("eiii", "before"),
    (3, "(f)"): ("f", "after:1"),
    (4, "(b)"): ("b", "before"),
    (5, "(b)(ii)"): ("bii", "before"),
    (5, "(b)(iii)"): ("biii", "before"),
}

#: Answer-coloured boxes that are figure labels: dropped (they are in the snip).
#: (q, label) -> text prefixes (whitespace-squeezed).
DROP_BOX_TEXT = {}

#: Hidden overflow: the box's text after (and including) the first carried
#: paragraph starting with this string is NOT shown on the page (the next
#: part's answer repeated inside a clipped box). (q, label) -> prefix.
TRUNCATE_FROM = {
    # School slip: two lines from another question (phthalic acid, C8H6O4) are left at
    # the end of Q3(b)(ii)'s answer. Dropped; flagged to the user.
    (3, "(b)(ii)"): "Amount of KOH = 0.75",
}

#: A carried paragraph split in two before this regex: (q, label) -> rx.
SPLIT_BEFORE = {
    (4, "(g)"): r" (?=NO \+ \u00bd O)",
}

#: Typed prefixes (the question's own printed labels around the answer line),
#: one per carried paragraph in order; None = no prefix.
LEAD = {}

#: Counted text fixes on the part's carried paragraphs: (q, label) -> [(rx, rep, n)]
TEXT_FIXES = {
    # Source-paper references typed at the end of the school's answer: removed.
    (1, "(a)"): [(r" 2018/P3/Q4\(a\)$", "", 1)],
    (1, "(b)"): [(r" 2018/P3/Q4\(a\)$", "", 1)],
    (1, "(c)"): [(r" 2022/P2/5\(b\)$", "", 1)],
    (1, "(f)"): [(r" Inspired from 2021/P2/2\(c\)\(i\)$", "", 1)],
    (2, "(c)"): [(r'CH<span class="sr">I</span><sub>3</sub>', "CHI<sub>3</sub>", 1),
                 # the tick glyph in the source is Symbol F0DE (a double arrow in the PDF)
                 (r"^\u2713 ", "\u21d2 ", 8),
                 # the school's structures are lost from the text; typed as the user ruled
                 (r"Compounds G, H, J and K contain or \.", "Compounds G, H, J, K contain -COCH<sub>3</sub> or -CH(OH)CH<sub>3</sub>", 1)],
    (2, "(a)(i)"): [
        (r"<sup>(rate<sub>\d</sub>)</sup>", r"\1", 4),
        (r"<sup>=</sup>", " = ", 4),
        (r"\[Benzene<sup>\]y</sup>", "[Benzene]<sup>y</sup>", 4),
        (r"\((\d+)<sup>\)y</sup>", r"(\1)<sup>y</sup>", 4),
        (r'<span class="(fnum|fden)"><sup>(\d+)</sup></span>', r'<span class="\1">\2</span>', 8),
    ],
    (3, "(c)"): [(r'(<span class="stk post"><span>)(\d?)-(</span>)', "\\1\\2\u2212\\3", 2),
                 # Word stacks the charge over the subscript: house form is C<sub>2</sub>O<sub>4</sub><sup>2\u2212</sup>
                 (r'<span class="stk post"><span>(\d?\u2212)</span><span>4</span></span>', r'<sub>4</sub><sup>\1</sup>', 2)],
    # the school's overline radical -> the house .sqrt / .rad markup
    (3, "(b)(ii)"): [                 (r'(<span style="text-decoration:overline">)K<sub>a1</sub>', r'\1<i>K</i><sub>a1</sub>', 1),
                 (r'\u221a<span style="text-decoration:overline">((?:(?!</span></span>).)*?(?:<span class="frac">.*?</span></span>)?)\s*</span>',
                  r'<span class="sqrt"><span class="rad">\1</span></span>', 2)],
    (3, "(h)(i)"): [(r'\u221a<span style="text-decoration:overline">((?:(?!</span></span>).)*?(?:<span class="frac">.*?</span></span>)?)\s*</span>',
                  r'<span class="sqrt"><span class="rad">\1</span></span>', 1)],
    (3, "(h)(ii)"): [(r'\u221a<span style="text-decoration:overline">((?:(?!</span></span>).)*?(?:<span class="frac">.*?</span></span>)?)\s*</span>',
                  r'<span class="sqrt"><span class="rad">\1</span></span>', 1)],
    (4, "(d)"): [(r"AlCl3 undergoes", "AlCl<sub>3</sub> undergoes", 1),
                 (r"SiCl4 undergoes", "SiCl<sub>4</sub> undergoes", 1),
                 (r"SiCl4 \+ 2H2O \u2192 SiO2 \+ 4 HCl", "SiCl<sub>4</sub> + 2H<sub>2</sub>O \u2192 SiO<sub>2</sub> + 4 HCl", 1)],
    (4, "(f)(i)"): [(r" <sup>atm\u22121</sup>", " atm<sup>\u22121</sup>", 1)],
}

#: Whole carried paragraphs dropped (plain text matches rx from the start):
#: (q, label) -> [(rx, n)]. Source-paper references and stray label fragments.
DROP_PARAS = {
    (1, "(d)"): [(r"2018/P3/1\(d\)$", 1)],
    (1, "(e)"): [(r"similar 2024/P3/1\(d\)$", 1)],
    (2, "(b)(ii)"): [(r"\[1\]$", 3)],
    (5, "(b)(ii)"): [(r"\u2212$", 1), (r"write the oxidation state", 1)],
    # Q2(c): the F-L structure snip carries these label/mark lines
    (2, "(c)"): [(r"F:\s*\[1\] J:", 1), (r"G:\s*\[1\] K:", 1), (r"H:\s*\[1\] L:", 1)],
    # drawing-guidance box: ignored (user ruling)
    (3, "(e)(iii)"): [(r"write the oxidation state", 1)],
}

#: Paragraphs joined onto the previous one (a sentence the Word box wrapped):
#: (q, label) -> [(rx_on_plain_start, n)]. Joined with a space unless it starts
#: with punctuation.
JOIN_PREV = {
    (1, "(e)"): [(r", and these", 1)],
    (2, "(c)"): [(r"group\. \[1\]", 1)],
    (3, "(c)"): [(r"4\.64", 1)],
}

#: Paragraphs appended after a part's carried text: (q, label) -> [html, ...]
APPEND_PARAS = {
    (2, "(b)(ii)"): ["1 mark per correctly drawn step"],
}

#: FIG sentinels in carried paragraphs, DOM order (equation objects with no
#: text layer): (q, label) -> [html, ...]
SENTINEL_FILL = {}


def _frac(n, d):
    return ('<span class="frac"><span class="fnum">%s</span>'
            '<span class="fden">%s</span></span>' % (n, d))


def _col(r) -> str:
    c = r.find("w:rPr/w:color", NS)
    return ((c.get(Wq + "val") if c is not None else "") or "").upper()


def _run_text(r) -> str:
    return "".join(x.text or "" for x in r.iter(Wq + "t"))


def _box_kind(c) -> str | None:
    """'ans' (blue/purple text present), 'mark' (red only), or None."""
    cols = {_col(r) for r in c.iter(Wq + "r") if _run_text(r).strip()}
    if not cols:        # a box holding only an equation: read the m:r colours
        cols = {(r.find("w:rPr/w:color", NS).get(Wq + "val") or "").upper()
                for r in c.iter(MR) if r.find("w:rPr/w:color", NS) is not None}
    if cols & ANSWER_COLS:
        return "ans"
    if cols and cols <= MARK_COLS:
        return "mark"
    return None


def _plain(c) -> str:
    return re.sub(r"\s+", " ", "".join(x.text or "" for x in c.iter(Wq + "t"))).strip()


def _filtered_para(p):
    """Copy of a FLOW paragraph with drawings/boxes removed and every run that
    carries text but no answer/mark colour dropped (the question's own black
    text). Returns None when nothing answer-coloured is left."""
    q = copy.deepcopy(p)
    for el in list(q.iter("{%s}AlternateContent" % MC)):
        el.getparent().remove(el)
    for el in list(q.iter(Wq + "drawing", Wq + "pict", Wq + "object")):
        if el.getparent() is not None:
            el.getparent().remove(el)
    keep = False
    for r in list(q.iter(Wq + "r")):
        t = _run_text(r)
        if not t.strip():
            continue
        if _col(r) in ANSWER_COLS | MARK_COLS:
            keep = True
        else:
            r.getparent().remove(r)
    return q if keep else None


def _table_is_answer(tbl) -> bool:
    """A body-level table whose own text is answer-coloured (Q3(e)(i), Q5(a)(iii))."""
    return any(_col(r) in ANSWER_COLS and _run_text(r).strip() for r in tbl.iter(Wq + "r"))


def _items(content):
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


def _clean(h: str) -> str:
    h = h.replace("\x00C\x00", "")
    h = h.replace("<b>", "").replace("</b>", "")      # the author types answers in bold
    h = _merge(h)
    h = re.sub(r"\s*<br>\s*", " ", h)
    h = h.replace("\t", "   ") if re.search(r"\S\s*\t\s*\S", h) else h.replace("\t", " ")
    h = re.sub(r'<i class="el">(.*?)</i>', r"\1", h)
    return h


def _img(q, slot):
    return '<img class="ws-fig" data-asset="%s" alt="">' % (FILE_FMT % (q, slot))


def _house(h: str) -> str:
    """House symbols/dashes on an answer fragment (minus U+2212, range en
    dash, times sign, standard-state sign, degree sign, ∆ U+2206)."""
    h = h.replace("\u0394", "\u2206")
    h = re.sub(r"(?<=[A-Za-z])\u2012(?=[A-Za-z])", "\u2013", h)       # bond C‒O
    h = h.replace("\u2012", "\u2212")
    h = re.sub(r"<u>\s*(<sup>\u2212</sup>)\s*</u>", r"\1", h)
    h = re.sub(r"(?<=[(\[=])(\s*)[\u2013-]\s?(?=\d|lg|log)", "\\1\u2212", h)   # unary minus
    h = re.sub(r"(?<=<td>)[\u2013-](?=\d)", "\u2212", h)
    h = re.sub(r"(?<=[\d)>]) x (?=[\d(])", " \u00d7 ", h)
    h = re.sub(r"(?<=\S)\u00d7(?=\S)", " \u00d7 ", h)
    h = re.sub(r"\s?<sup>o</sup>C", " \u00b0C", h)
    h = h.replace("<sup>\ua74b</sup>", '<sup class="pl-sym">\u29b5</sup>')
    h = re.sub(r"<u>(\s+)", r"\1<u>", h)
    h = re.sub(r"(\s+)</u>", r"</u>\1", h)
    return h


def _join_wrapped(paras):
    """The school types an answer line by line along the dotted lines; a line
    that stops mid-sentence and continues in lower case joins the previous."""
    out = []
    for kind, h in paras:
        plain = re.sub(r"<[^>]+>", "", h).strip()
        if (out and kind in ("p", "mark") and out[-1][0] == kind
                and re.match(r"[a-z]", plain) and len(plain.split()) >= 3):
            prev = re.sub(r"<[^>]+>", "", out[-1][1]).rstrip()
            if prev and prev[-1] not in ".:!?]=)" and "=" not in prev and "=" not in plain:
                out[-1] = (kind, out[-1][1].rstrip() + " " + h.lstrip())
                continue
        out.append((kind, h))
    return out


def build(unz_prep: Path, bank):
    tree = etree.parse(str(unz_prep / "word/document.xml"))
    body = tree.getroot().find("w:body", NS)
    bank_labels = {q["question_number"]: [p["label"] for p in q["parts"]] for q in bank}
    bank_marks = {(q["question_number"], p["label"]): p["marks"] for q in bank for p in q["parts"]}

    raw = {}          # (q, label) -> [("p", html) | ("tbl", el) | ("mark", html)]
    order = []
    qnum, letter, cur = 0, None, None

    def add(key, item):
        if key not in raw:
            raw[key] = []
            order.append(key)
        raw[key].append(item)

    def take_box(cur, c):
        kind = _box_kind(c)
        if kind is None:
            return
        text = _plain(c)
        if any(text.startswith(t) for t in DROP_BOX_TEXT.get(cur, ())):
            return
        for it_kind, it in _items(c):
            add(cur, ("mark" if kind == "mark" and it_kind == "p" else it_kind, it))

    for k in body:
        ln = etree.QName(k).localname
        if ln == "tbl":
            if cur is not None and _table_is_answer(k):
                add(cur, ("tbl", k))
            if cur is not None:
                for tp in k.iter(Wq + "p"):
                    for c in _boxes(tp):
                        take_box(cur, c)
            continue
        if ln != "p":
            continue
        own = _own_text(k)
        qnum, letter, lab = _context(own, qnum, letter)
        if lab:
            cur = (qnum, lab)
        if cur is None:
            continue
        fp = _filtered_para(k)
        if fp is not None:
            h = paragraph_html(fp)
            if h.strip():
                add(cur, ("p", h))
        for c in _boxes(k):
            take_box(cur, c)
    for key in FIGURE_PLAN:
        if key not in raw:
            raw[key] = []
            order.append(key)

    worked, assets, per_q, report = {}, [], {}, []
    for key in sorted(order, key=lambda x: (x[0], bank_labels[x[0]].index(x[1])
                                            if x[1] in bank_labels.get(x[0], []) else 999)):
        q, label = key
        if label not in bank_labels.get(q, []):
            raise SystemExit("answer part %s %s has no bank part" % (q, label))
        n_fig = sum(h.count(FIG) for kind, h in raw[key] if kind in ("p", "mark"))
        fill = SENTINEL_FILL.get(key, [])
        if n_fig != len(fill):
            raise SystemExit("Q%d%s: %d FIG sentinels, %d fills" % (q, label, n_fig, len(fill)))
        fit = iter(fill)
        paras = []
        for kind, h in raw[key]:
            if kind == "tbl":
                paras.append(("tbl", _house(_minus(_table_cmp(h)))))
                continue
            h = re.sub(re.escape(FIG), lambda m: next(fit), h)
            h = _tidy_ws(_minus(_house(_clean(h))))
            plain = re.sub(r"<[^>]+>", "", h).strip()
            if not plain or re.fullmatch(r"[.\s]+", plain):
                continue
            paras.append((kind, h))
        cut = TRUNCATE_FROM.get(key)
        if cut:
            idx = [i for i, (k2, h) in enumerate(paras)
                   if k2 == "p" and re.sub(r"<[^>]+>", "", h).startswith(cut)]
            if len(idx) != 1:
                raise SystemExit("Q%d%s: TRUNCATE_FROM %r matched %d" % (q, label, cut, len(idx)))
            paras = paras[:idx[0]]
        paras = _join_wrapped(paras)
        paras = [(k2, _tidy_ws(_minus(_merge(h)))) if k2 in ("p", "mark") else (k2, h)
                 for k2, h in paras]
        for rx, rep, cnt in TEXT_FIXES.get(key, []):
            n_tot, new = 0, []
            for kind, h in paras:
                if kind in ("p", "mark"):
                    h, n = re.subn(rx, rep, h)
                    n_tot += n
                new.append((kind, h))
            if n_tot != cnt:
                raise SystemExit("Q%d%s: text fix %r matched %d, expected %d" % (q, label, rx, n_tot, cnt))
            paras = new
        for rx, cnt in DROP_PARAS.get(key, []):
            keep = [(k2, h) for k2, h in paras
                    if not (k2 in ("p", "mark") and re.match(rx, re.sub(r"<[^>]+>", "", h).strip()))]
            if len(paras) - len(keep) != cnt:
                raise SystemExit("Q%d%s: DROP_PARAS %r dropped %d, expected %d"
                                 % (q, label, rx, len(paras) - len(keep), cnt))
            paras = keep
        for rx, cnt in JOIN_PREV.get(key, []):
            out, n = [], 0
            for k2, h in paras:
                if (k2 == "p" and out and out[-1][0] == "p"
                        and re.match(rx, re.sub(r"<[^>]+>", "", h).strip())):
                    glue = "" if h.lstrip()[:1] in ",.;)" else " "
                    out[-1] = ("p", out[-1][1].rstrip() + glue + h.lstrip())
                    n += 1
                else:
                    out.append((k2, h))
            if n != cnt:
                raise SystemExit("Q%d%s: JOIN_PREV %r joined %d, expected %d" % (q, label, rx, n, cnt))
            paras = out
        paras = paras + [("mark", h) for h in APPEND_PARAS.get(key, [])]
        paras = [(k2, _tidy_ws(_minus(_merge(h)))) if k2 in ("p", "mark") else (k2, h)
                 for k2, h in paras]
        rx_split = SPLIT_BEFORE.get(key)
        if rx_split:
            new = []
            for k2, h in paras:
                parts = re.split(rx_split, h) if k2 in ("p", "mark") else [h]
                new.extend((k2, x) for x in parts)
            paras = new
        lead = LEAD.get(key)
        text_idx = [i for i, (k2, h) in enumerate(paras) if k2 == "p"]
        if lead is not None and len(lead) != len(text_idx):
            raise SystemExit("Q%d%s: LEAD has %d entries, %d answer paragraphs: %r"
                             % (q, label, len(lead), len(text_idx), [paras[i][1][:40] for i in text_idx]))
        html = []
        for idx, (kind, h) in enumerate(paras):
            if kind == "tbl":
                html.append(h)
                continue
            if kind == "mark":
                html.append('<p><span class="ans">%s</span></p>' % h)
                continue
            pre = lead[text_idx.index(idx)] if lead else None
            ind = "  " if h.lstrip().startswith("=") and not pre else ""
            html.append('<p>%s<span class="ans">%s%s</span></p>'
                        % (pre or "", ind, h.lstrip() if ind else h))
        if key in FIGURE_PLAN:
            slot, where = FIGURE_PLAN[key]
            tag = "<p>%s</p>" % _img(q, slot)
            if where == "before":
                html = [tag] + html
            elif where == "after":
                html = html + [tag]
            else:
                n = int(where.split(":")[1])
                html = html[:n] + [tag] + html[n:]
            per_q[q] = per_q.get(q, 0) + 1
            assets.append(dict(question=q, slot="ans-" + slot, path=FILE_FMT % (q, slot),
                               part=label, offset=per_q[q]))
        part = ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                % (label, "\n".join(html)))
        worked.setdefault(q, []).append(part)
    for q in bank_labels:
        have = {l for (qq, l) in order if qq == q}
        miss = [l for l in bank_labels[q] if bank_marks.get((q, l)) and l not in have]
        if miss:
            report.append("!! Q%d: bank parts with marks but no answer: %s" % (q, miss))
    out = {q: '<div class="worked-solution">\n%s\n</div>' % "\n".join(v) for q, v in worked.items()}
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
    cjc26_p2_prep.COVER_END = "Section A"
    cjc26_p2_prep.prep(a.unz, prep)
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
