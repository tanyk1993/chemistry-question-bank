"""CJC 2024 H2 P3 -- worked solutions from the "WORKED SOLUTIONS" docx.

Same container as CJC 2024 H2 P2 (extract_cjc_p2_answers.py): the question paper's
paragraph flow with every answer in a FLOATING BLUE TEXT BOX (`wps:txbx`, only
the `mc:Choice` copy is read). Two differences, both handled here:

1. The answer boxes are NOT anchored to the paragraph of their own part. The
   school put each question's answers after the whole question block, so a box
   can hold the answers of several parts ("(i) ...", "(ii) ...", "(iii) ...").
   The part is therefore read from the TYPED LABEL at the start of each box
   paragraph ("(i)", "(c) (i)", "(a)"), resolved against the bank's own part
   labels, and the label is stripped (the frontend draws its own `.lab`).
   A box paragraph with no label belongs to the part before it.
2. Question 4 starts with the digit glued to the text ("41,4-dibromobutane").

Answer drawings are NOT cropped here: the user snips them (HANDOFF §17). Each is
declared either as a FIG sentinel fill "@slot" (the drawing sits at that spot in
a box) or in FIGURE_PLAN (free drawings in the flow, placed before/after the
part's typed text). Every declaration is checked: a sentinel without a fill, or a
fill without a sentinel, raises.

Output feeds `gen_answers_migration.py --type structured --paper 3`:
  worked_solutions.json, answer_assets.json.

Run:  python3 -m ingest.extract_cjc_p3_answers <unz> <questions.json> <outdir>
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
from .extract_cjc_p2_answers import (_boxes, _clean, _merge, _minus, _own_text,
                                     _frac, ROMAN, _LAB)

FIG = "\x00FIG\x00"
FILE_FMT = "CJC_H2_P3_Q%d_ans-%s_2024.png"
ANSWER_BLUE = {"0000FF"}


def _sqrt(x):
    return '<span class="sqrt"><span class="rad">%s</span></span>' % x


AR, EQ = " → ", " ⇌ "

#: (qnum, label) -> [fill per FIG sentinel, in DOM order]. "@slot" = the user's
#: snip goes here (the sentinel's paragraph holds nothing else); anything else
#: is typed markup (MathType working has no text layer; arrows are glyph pictures).
SENTINEL_FILL = {
    (1, "(a)(iii)"): ["@aiii"],
    (1, "(a)(iv)"): ["@aiv"],
    (1, "(c)(i)"): ["@ci"],
    (1, "(c)(ii)"): ["@cii"],
    (2, "(c)(iii)"): ["@ciii"],
    (3, "(b)"): [_frac("39.96 x 96.93 + 41.96 x 0.65 + 42.96 x 0.14 + 43.96 x 2.09 + 47.96 x 0.19", "100")],
    (3, "(e)(iii)"): ["@eiii"],
    (3, "(f)(i)"): ["@fi", "@fi2", "@fi3", "@fi4"],
    (3, "(f)(ii)"): ["@fii"],
    (4, "(b)(i)"): ["@bi", ""],
    (4, "(c)"): [AR],
    (4, "(d)(ii)"): ["@dii"],
    (4, "(d)(iii)"): ["@diii"],
    (4, "(e)(i)"): [_sqrt("<i>K</i><sub>b</sub> × [B]"),
                    _sqrt("10<sup>−6.1</sup> × 0.025")],
    (4, "(e)(ii)"): [_frac("[BH<sup>+</sup>]", "[B]"),
                     "[" + _frac("<i>x</i>", "<i>v</i>") + " ÷ "
                     + _frac("0.025 − <i>x</i>", "<i>v</i>") + "]",
                     _frac("<i>x</i>", "0.025 − <i>x</i>"),
                     _frac("2.23 × 10<sup>−2</sup>", "0.5")],
    (5, "(b)(iv)"): [EQ],
    (5, "(c)(ii)"): ["@cii"],
    (5, "(d)(i)"): [_frac("12.20", "1000"), _frac("0.7747", "0.800")],
}

#: Free answer drawings (no sentinel in a carried box): (q, label) -> (slot, where)
FIGURE_PLAN = {
    (2, "(a)(ii)"): ("aii", "before"),
    (3, "(d)(ii)"): ("dii", "after"),
    # the school's solutions omit 3(e)(i)/(ii); the user supplies them as snips
    (3, "(e)(i)"): ("ei", "after"),
    (3, "(e)(ii)"): ("eii", "after"),
    (4, "(a)"): ("a", "after"),
    (5, "(b)(ii)"): ("bii", "after"),
    (5, "(c)(i)"): ("ci", "after"),
}

#: Box paragraphs that are LABELS of a snipped drawing (their text is in the snip).
#: Matched on the paragraph's plain text AFTER the part label is stripped.
DROP_PARAS = {
    (3, "(d)(ii)"): [r"0"],
    (4, "(a)"): [r"transition state"],
    (4, "(d)(ii)"): [r"\+", r"[–−\-]", r"e\s*(?:>|&gt;)", r"(?:>|&gt;)\s*e"],
    (5, "(b)(ii)"): [r"Buffer region"],
    (4, "(b)(i)"): [r"A", r"B"],     # the A / B labels sit inside the one snip
}

#: Typed prefixes (the question's own printed labels around the answer line), one
#: per carried answer paragraph in order.
LEAD = {}

#: A box whose typed "(i)" label is missing from the docx text: (qnum, plain-text prefix)
#: -> the part it opens.
START_AS = {(4, "Ion-dipole attractions"): "(d)(i)"}

STD = (r"<sup>\s*o\s*</sup>(?!\s*C\b)", '<sup class="pl-sym">⦵</sup>')

#: Counted text fixes on a part's carried paragraphs: (q, label) -> [(rx, rep, n)]
#: n = None accepts any count >= 1 (reported).
TEXT_FIXES = {
    # the plain superscript "o" is the standard-state sign (the user's ruling on the
    # question side, 2026-10-09); the degree sign "315 <sup>o</sup>C" has no spaces
    (2, "(b)(i)"): [(STD[0], STD[1], None)],
    (5, "(a)(ii)"): [(STD[0], STD[1], None)],
}

SIMILAR_RX = re.compile(r"[–‒\-]\s*[Ss]imilar to 20\d\d/P\d/Q\d")


def _context(own: str, qnum: int, letter: str | None):
    """Question number / part letter from a QUESTION paragraph's own text."""
    m = re.match(r"^\s*(\d)", own)
    if m and int(m.group(1)) == qnum + 1:
        rest = own[m.end():]
        if re.match(r"\s*[A-Z(]", rest) or own.lstrip().startswith("41,4"):
            qnum, letter = int(m.group(1)), None
            own = rest
    m = _LAB.match(own)
    if m:
        toks = re.findall(r"\(([a-z]{1,3})\)", m.group(1))
        if toks[0] not in ROMAN:
            letter = toks[0]
    return qnum, letter


_SUBD = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _flatsub(h: str) -> str:
    """A subscript that holds a formula (<sub>CH4</sub>, <sub>H2O</sub>) keeps its digits as
    Unicode subscripts, so it does not render as bare digits."""
    return re.sub(r"<sub>([A-Za-z]+\d[A-Za-z\d]*)</sub>",
                  lambda m: "<sub>%s</sub>" % m.group(1).translate(_SUBD), h)


def _plain(h: str) -> str:
    return re.sub(r"<[^>]+>", "", h).replace("\x00C\x00", "").strip()


def _strip_label(h: str, n: int) -> str:
    rx = r"^((?:<[^>]*>|\x00C\x00)*)\s*(?:\([a-z]{1,3}\)\s*){%d}" % n
    new, k = re.subn(rx, r"\1", h, count=1)
    if not k:
        raise SystemExit("could not strip the %d-token label from %r" % (n, h[:80]))
    return new


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


def _img(q, slot):
    return '<img class="ws-fig" data-asset="%s" alt="">' % (FILE_FMT % (q, slot))


def build(unz_prep: Path, bank):
    body = etree.parse(str(unz_prep / "word/document.xml")).getroot().find("w:body", NS)
    bank_labels = {q["question_number"]: [p["label"] for p in q["parts"]] for q in bank}
    bank_marks = {(q["question_number"], p["label"]): p["marks"] for q in bank for p in q["parts"]}

    raw, order = {}, []
    qnum, letter, cur = 0, None, None
    log = []

    def add(key, item):
        if key not in raw:
            raw[key] = []
            order.append(key)
        raw[key].append(item)

    for k in body:
        if etree.QName(k).localname != "p":
            continue
        qnum, letter = _context(_own_text(k), qnum, letter)
        for c in _boxes(k):
            if not _is_answer_box(c):
                continue
            for kind, it in _items(c):
                if kind == "tbl":
                    if cur is None:
                        raise SystemExit("answer table before any part label")
                    add(cur, ("tbl", it))
                    continue
                h = it
                m = _LAB.match(_plain(h))
                if m:
                    toks = re.findall(r"\(([a-z]{1,3})\)", m.group(1))
                    lab = None
                    if toks[0] in ROMAN and letter and "(%s)(%s)" % (letter, toks[0]) in bank_labels.get(qnum, []):
                        lab = "(%s)(%s)" % (letter, toks[0])
                    elif toks[0] not in ROMAN or letter is None:
                        letter = toks[0]
                        if len(toks) == 2 and toks[1] in ROMAN and "(%s)(%s)" % (letter, toks[1]) in bank_labels.get(qnum, []):
                            lab = "(%s)(%s)" % (letter, toks[1])
                        elif "(%s)" % letter in bank_labels.get(qnum, []):
                            lab = "(%s)" % letter
                    if lab is None:
                        raise SystemExit("Q%d: label %r (letter %r) matches no bank part: %r"
                                         % (qnum, m.group(1), letter, _plain(h)[:60]))
                    cur = (qnum, lab)
                    h = _strip_label(h, len(toks) if lab.count("(") == 1 or len(toks) == 2 else 1)
                    if lab.count("(") == 2 and len(toks) == 2:
                        letter = toks[0]
                for (sq, pre), lab in START_AS.items():
                    if qnum == sq and _plain(h).startswith(pre):
                        cur = (qnum, lab)
                if cur is None:
                    raise SystemExit("answer paragraph before any part label: %r" % _plain(h)[:60])
                plain = _plain(h)
                if any(re.fullmatch(rx, plain) for rx in DROP_PARAS.get(cur, [])):
                    if cur not in raw:
                        raw[cur] = []
                        order.append(cur)
                    log.append("dropped label paragraph %r in Q%d%s" % (plain, *cur))
                    continue
                add(cur, ("p", h))
    for key in FIGURE_PLAN:
        if key not in raw:
            raw[key] = []
            order.append(key)

    report = list(log)
    worked, assets, per_q = {}, [], {}
    for key in sorted(order, key=lambda x: (x[0], bank_labels[x[0]].index(x[1])
                                            if x[1] in bank_labels.get(x[0], []) else 999)):
        q, label = key
        if label not in bank_labels.get(q, []):
            raise SystemExit("answer part %s %s has no bank part" % (q, label))
        n_fig = sum(h.count(FIG) for kind, h in raw[key] if kind == "p")
        fill = SENTINEL_FILL.get(key, [])
        if n_fig != len(fill):
            raise SystemExit("Q%d%s: %d FIG sentinels, %d fills" % (q, label, n_fig, len(fill)))
        fit = iter(fill)
        items = []
        for kind, h in raw[key]:
            if kind == "p":
                def _sub(mm):
                    f = next(fit)
                    return _img(q, f[1:]) if f.startswith("@") else f
                h = re.sub(re.escape(FIG), _sub, h)
            items.append((kind, h))
        paras = []
        for kind, h in items:
            if kind == "tbl":
                paras.append(("tbl", _table_cmp(h).replace(FIG, "⇌")))   # drawn equilibrium arrow in the ICE table
                continue
            h = _minus(_clean(h))
            if key == (4, "(b)(i)"):          # A / B labels are inside the one snip
                h = re.sub(r"^\s*[AB]\s*(?=<img|$)", "", h)
            h = SIMILAR_RX.sub("", h)
            h = _tidy_ws(h)
            plain = re.sub(r"<[^>]+>", "", h).strip()
            if "<img" not in h and (not plain or re.fullmatch(r"[.\s]+", plain)):
                continue
            paras.append(("p", h))
        for rx, rep, cnt in TEXT_FIXES.get(key, []):
            n_tot, new = 0, []
            for kind, h in paras:
                if kind == "p":
                    h, n = re.subn(rx, rep, h)
                    n_tot += n
                new.append((kind, h))
            if (cnt is None and n_tot < 1) or (cnt is not None and n_tot != cnt):
                raise SystemExit("Q%d%s: text fix %r matched %d, expected %s" % (q, label, rx, n_tot, cnt))
            report.append("Q%d%s: text fix matched %d" % (q, label, n_tot))
            paras = new
        paras = [(k2, _flatsub(_tidy_ws(_minus(_merge(h))))) if k2 == "p" else (k2, h) for k2, h in paras]
        lead = LEAD.get(key)
        pidx = [i for i, (k2, h) in enumerate(paras) if k2 == "p"]
        if lead is not None and len(lead) != len(pidx):
            raise SystemExit("Q%d%s: LEAD has %d entries, %d answer paragraphs" % (q, label, len(lead), len(pidx)))
        html = []
        for idx, (kind, h) in enumerate(paras):
            if kind == "tbl":
                html.append(h)
                continue
            if "<img" in h:
                if re.sub(r"<img[^>]*>", "", re.sub(r"<(?!img)[^>]+>", "", h)).strip():
                    raise SystemExit("Q%d%s: an image paragraph also carries text: %r" % (q, label, h[:80]))
                html.append("<p>%s</p>" % re.search(r"<img[^>]*>", h).group(0))
                continue
            plain = re.sub(r"<[^>]+>", "", h).strip()
            if re.fullmatch(r"\[.*\]", plain) and 'class="sqrt"' not in h and 'class="frac"' not in h:
                html.append('<p class="mark-note">%s</p>' % plain)
                continue
            pre = lead[pidx.index(idx)] if lead else None
            ind = "  " if h.lstrip().startswith("=") and not pre else ""
            html.append('<p>%s<span class="ans">%s%s</span></p>' % (pre or "", ind, h.lstrip() if ind else h))
        if key in FIGURE_PLAN:
            slot, where = FIGURE_PLAN[key]
            tag = "<p>%s</p>" % _img(q, slot)
            html = [tag] + html if where == "before" else html + [tag]
        part = ('<div class="part"><span class="lab">%s</span><div class="body">%s</div></div>'
                % (label, "\n".join(html)))
        worked.setdefault(q, []).append(part)

    out = {q: '<div class="worked-solution">\n%s\n</div>' % "\n".join(v) for q, v in worked.items()}
    # every declared snip must have landed exactly once, and the asset list follows DOM order
    declared = {}
    for key, fills in SENTINEL_FILL.items():
        for f in fills:
            if f.startswith("@"):
                declared.setdefault(key[0], []).append(f[1:])
    for key, (slot, _w) in FIGURE_PLAN.items():
        declared.setdefault(key[0], []).append(slot)
    for q, slots in sorted(declared.items()):
        html = out.get(q, "")
        found = [(html.find(FILE_FMT % (q, s)), s) for s in slots]
        for pos, s in found:
            if pos < 0 or html.count(FILE_FMT % (q, s)) != 1:
                raise SystemExit("Q%d: snip slot %s did not land exactly once" % (q, s))
        for n, (pos, s) in enumerate(sorted(found), 1):
            assets.append(dict(question=q, slot="ans-" + s, path=FILE_FMT % (q, s), offset=n))
    for q in bank_labels:
        have = {l for (qq, l) in order if qq == q}
        miss = [l for l in bank_labels[q] if bank_marks.get((q, l)) and l not in have]
        if miss:
            report.append("!! Q%d: bank parts with marks but NO answer in the solutions: %s" % (q, miss))
    return out, assets, report


def _is_answer_box(c) -> bool:
    for r in c.iter(Wq + "r"):
        if "".join(x.text or "" for x in r.iter(Wq + "t")).strip():
            col = r.find("w:rPr/w:color", NS)
            if col is not None and (col.get(Wq + "val") or "").upper() in ANSWER_BLUE:
                return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("questions_json")
    ap.add_argument("outdir")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    prep = out / "unz_prep"
    flow_parts_prep.prep(a.unz, prep, "Answer all the questions in this section")
    bank = json.loads(Path(a.questions_json).read_text(encoding="utf-8"))
    worked, assets, report = build(prep, bank)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(k): v for k, v in sorted(worked.items())}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "answer_assets.json").write_text(
        json.dumps([{k: v for k, v in x.items()} for x in assets], indent=1), encoding="utf-8")
    print("\n".join(report))
    print("questions:", sorted(worked), "| answer figures:", len(assets))
    for x in assets:
        print("  Q%d %-8s %s" % (x["question"], x["slot"], x["path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
