"""Extract worked solutions + answer key for CJC 2026 H2 P1 (9476/01, 30 MCQ).

Document shape: the "Worked Solutions" docx is the question paper itself with
each solution typed in BLUE (0000FF / 0432FF) either as ordinary paragraphs
under the question or inside a FLOATING TEXT BOX (dashed border `wps:txbx`)
anchored in the question flow. Word stores each box twice (`mc:Choice`
DrawingML + `mc:Fallback` VML); only the `mc:Choice` copy is read.

A solution is found by SEGMENT: the body children from one question's first
paragraph up to the next question's (`START_TEXT`, each verified to occur once
and in order). Inside a segment the solution is every blue top-level paragraph
plus every blue text box, in document order. Question-side boxes (Q9's graph
labels, Q18's equation, Q3's option numerals) are not blue-text solutions and
are skipped by rule or by `SKIP_BOXES`.

Dropped from the worked solution, kept for the tags stage in
`school_lo_lines.json`: the school's bold "Concept: ..." / "Topic: ..." line
(user, 2026-10-25: "remove the bolded lines that say concept") -- plus the
green "Nitrogen Compounds - ..." line that plays the same role on Q25 and the
indented run-on line under Q21's "Concept:".

Key: read two independent ways and both must agree -- the "Ans/Answer: X" line
in each solution (XML) and the answer-key table on the cover page (PDF).
Q29 is declared in `KEY_DISAGREES` (school error, user to rule).

Every counted fix must match its expected count or the run raises.

Output (to <outdir>): worked_solutions.json, answer_assets.json,
answer_key.json, school_lo_lines.json, anomalies.txt.

Run (from the repo root):
  python3 -m ingest.extract_cjc26_p1_answers <unz_sol_dir> <solutions.pdf> <outdir>
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS, Wq, paragraph_html, paragraph_numid, load_bullet_numids
from . import extract_cjc_p1_answers as base
from .extract_cjc_p1_answers import (
    _items, _text, _plain, _merge_runs, _tidy_ws, _bold_ratio, _keep_bold,
    _unbold, CENTRE, FIG, MC, WPS)

W = "{%s}" % NS["w"]
BLUE = ("0000FF", "0432FF")
GREEN = ("00B050",)
ASSET_FMT = "CJC_H2_P1_Q%d_%s_2026.png"

# first words of each question's stem, in order; each must be found exactly
# once as the start of a top-level paragraph (the stem text is the anchor,
# because Q16/Q17 carry automatic numbers)
START_TEXT = {
    1: "Which statement correctly explains the trends in ionisation",
    2: "Which of the following statements explains why graphite",
    3: "Which of the following species is planar",
    4: "The table shows the boiling points of three alkanes",
    5: "The successive ionisation energies",
    6: "Use of the Data Booklet is relevant to this question.",   # 1st of 3
    7: "Use of the Data Booklet is relevant to this question.",   # 2nd
    8: "The standard enthalpy change of formation of sulfur dioxide",
    9: "The Boltzmann distributions and activation energies",
    10: "Nitrogen monoxide, NO, reacts with chlorine",
    11: "The sulfur at hydrothermal vents",
    12: "Manganate(VII) ions",
    13: "Haber process is the process",
    14: "Magnesium, aluminium, silicon and phosphorus",
    15: "The compounds listed are formed from their elements",
    16: "Which of the following reactions does NH3",
    17: "Ethanoic acid is a weak acid",
    18: "Metal sulfides are generally insoluble",
    19: "Which statement about the chemical reactions involving but-2-ene",
    20: "20 cm3 of a gaseous hydrocarbon",
    21: "(3-nitrophenyl)methanol can be produced",
    22: "The mechanism for a certain reaction",
    23: "Which statement regarding acidity",
    24: "Which of the following can be used to distinguish",
    25: "What are the product(s) when CH3NHCH2CONH2",
    26: "Which molecules may be used in protein formation",
    27: "Use of the Data Booklet is relevant to this question.",   # 3rd
    28: "Use of the Data Booklet is relevant to this question.",   # 4th
    29: "When solid Cr(NO3)3 is added to water",
    30: "Use of the Data Booklet is relevant to this question.",   # 5th
}
# the Data Booklet line is shared by five questions; its stem is the NEXT
# paragraph, which identifies the question
DATA_BOOKLET_STEM = {
    6: "Which contains the greatest number of molecules",
    7: "When 0.006 mol of Br",
    27: "A current of 0.85 A",
    28: "Which statements about an H",
    30: "The table shows some physical properties of metals",
}

# ---- figures --------------------------------------------------------------
# qnum -> ordered replacement for each FIG sentinel in that question's
# solution (after the concept line is dropped), in DOCUMENT ORDER:
#   ("img", slot)  a snip the user makes   ("inline", slot)  same, but set in a line
#   ("html", text) typed                   None             dropped
# The run raises if a question's FIG count differs from its plan.
_O_R = ("O: 2H<sub>2</sub>O \u2192 O<sub>2</sub> + 4H<sup>+</sup> + 4e<sup>\u2013</sup>",
        "R: Ag<sup>+</sup> + e<sup>\u2013</sup> \u2192 Ag")
FIG_PLAN = {
    2: [("img", "ans-1")],                       # graphite layers
    3: [("img", "ans-1"), None, None, None],     # four structure pairs: ONE snip
    # Q6: methyl ethanoate typed as a formula (user, 2026-10-25: "no snip")
    6: [("html", "CH<sub>3</sub>OCOCH<sub>3</sub>")],
    8: [("img", "ans-1")],                       # energy level diagram
    24: [("img", "ans-1")],                      # R-CO-CH3
    25: [("img", "ans-1")],                      # hydrolysis scheme
    26: [("img", "ans-1"), ("img", "ans-2")],    # general alpha-amino acid; the four acids
    # Q27: the two half-equations are small PICTURES of typed text; they are typed
    # here (the school's own PDF reads "O: 2H2O -> O2 + 4H+ + 4e-" / "R: Ag+ + e- -> Ag")
    27: [("html", _O_R[0] + "&emsp;"), ("html", _O_R[1]), ("img", "ans-1")],
}
ASSET_ORDER = {2: ["ans-1"], 3: ["ans-1"], 8: ["ans-1"],
               24: ["ans-1"], 25: ["ans-1"], 26: ["ans-1", "ans-2"], 27: ["ans-1"]}
INLINE_STYLE = "display:inline;vertical-align:middle;margin:0 .15em;border:0"

# The school's concept line ("Concept:", "Topic:", Q25's green heading) is not
# part of the worked solution (user, 2026-10-25): dropped, kept in lo_lines.
CONCEPT_RX = re.compile(r"^\s*(Concept\s*:|Topic\s*:)")
Q25_HEADING = "Nitrogen Compounds"
# Q21's "Concept:" line runs on into an indented second line ("Reduction of ...")
CONCEPT_CONT = {21}
# Q6: a leaked, invisible text box holding an earlier copy of Q7's working
LEAKED_BOX = {6: "Concept: Energetics"}
# Q20: two typed rows aligned with spaces under the equation -> one table
Q20_ROWS = ("Volume reacted", "Simplified ratio")
# Q27: text that is in the file but not on the school's page (white/hidden stray)
STRAY = {27: [("are in s", "")]}

# Text boxes (document-order index within the segment) that are figure parts or
# question-side, not solution text: {qnum: set(box texts)} matched by startswith.
SKIP_BOX_TEXT = {
    3: ("1", "2", "3", "4"),       # numerals of the four structure pairs
}
SKIPPED = []

# Wholly dropped paragraphs (qnum, startswith of PLAIN text)
DROP_PARAS: list = []


# ---------------------------------------------------------------------------
def _col(r):
    c = r.find(Wq + "rPr/" + Wq + "color")
    return c.get(Wq + "val") if c is not None else None


def _own_runs(el):
    """Runs of `el` that are not inside a Fallback copy and not inside a text box."""
    for r in el.iter(Wq + "r"):
        a = r.getparent()
        skip = False
        while a is not None and a is not el:
            if a.tag in ("{%s}Fallback" % MC, Wq + "txbxContent"):
                skip = True
                break
            a = a.getparent()
        if not skip:
            yield r


def _is_blue_para(p):
    n_blue = n_all = 0
    for r in _own_runs(p):
        t = "".join(x.text or "" for x in r.findall(Wq + "t")).strip()
        if not t:
            continue
        n_all += 1
        if _col(r) in BLUE + GREEN:
            n_blue += 1
    return n_all > 0 and n_blue / n_all >= 0.5


def _box_contents(child):
    """[txbxContent] of every mc:Choice text box anchored in `child`."""
    out = []
    for ac in child.iter("{%s}AlternateContent" % MC):
        ch = ac.find("{%s}Choice" % MC)
        tb = ch.find(".//{%s}txbx" % WPS) if ch is not None else None
        if tb is None:
            continue
        c = tb.find(Wq + "txbxContent")
        if c is not None:
            out.append(c)
    return out


def _box_is_blue(c):
    n_blue = n_all = 0
    for r in c.iter(Wq + "r"):
        t = "".join(x.text or "" for x in r.findall(Wq + "t")).strip()
        if not t:
            continue
        n_all += 1
        if _col(r) in BLUE + GREEN:
            n_blue += 1
    return n_all > 0 and n_blue / n_all >= 0.5


def _resolve_symbols(body):
    """Symbol-font F06F in this document: degree after '/ ' (before C), the
    standard-state sign after 'ΔH'. Same ruling as cjc26_p1_prep.py."""
    fixed = {"degree": 0, "plimsoll": 0}
    for p in list(body.iter(W + "p")):
        runs = p.findall("w:r", NS)
        for i, r in enumerate(runs):
            f = r.find("w:rPr/w:rFonts", NS)
            if f is None or "ymbol" not in (f.get(W + "ascii") or ""):
                continue
            ts = r.findall("w:t", NS)
            raw = "".join(t.text or "" for t in ts)
            if raw == "":
                nb = "".join("".join(x.itertext()) for x in runs[max(0, i - 2):i])
                na = "".join("".join(x.itertext()) for x in runs[i + 1:i + 3])
                if nb.endswith("ΔH") or nb.endswith("ΔH") \
                        or na.startswith("") or na.startswith("f") \
                        or nb.endswith(""):
                    p.remove(r)
                continue
            if raw.strip(" ") != "":
                continue
            before = "".join("".join(x.itertext()) for x in runs[max(0, i - 3):i])
            after = "".join("".join(x.itertext()) for x in runs[i + 1:i + 3])
            if before.rstrip().endswith("/") and after.lstrip().startswith("C"):
                new_txt, kind = "°", "degree"
            elif "ΔH" in before[-6:]:
                new_txt, kind = "⦵", "plimsoll"
            else:
                raise SystemExit("unclassified Symbol-font o after %r" % before[-20:])
            f.getparent().remove(f)
            ts[0].text = new_txt
            for extra in ts[1:]:
                r.remove(extra)
            fixed[kind] += 1
    # Wingdings F0E8 (a right arrow, typed in Q6 and Q7 workings) -> U+2192, as
    # the question paper's own arrows are
    for sym in list(body.iter(W + "sym")):
        if (sym.get(W + "font") or "").lower() == "wingdings" \
                and (sym.get(W + "char") or "").upper() == "F0E8":
            t = etree.Element(W + "t")
            t.text = "\u2192"
            sym.getparent().replace(sym, t)
            fixed["arrow"] = fixed.get("arrow", 0) + 1
    return fixed


def _own_text(k):
    return "".join("".join(x.text or "" for x in r.findall(Wq + "t"))
                   for r in _own_runs(k))


def _starts(kids):
    """{qnum: child index of the question's first paragraph}."""
    paras = [(i, _own_text(k).strip()) for i, k in enumerate(kids)
             if etree.QName(k).localname == "p"]
    starts = {}
    booklet = [i for i, t in paras
               if re.sub(r"^\s*\d{1,2}[.\s]*", "", t).startswith(START_TEXT[6])
               and i > 40]
    # the question's number is typed in a separate run: the start paragraph text
    # begins with it (e.g. "1Which statement..."), or not at all (Q16/Q17)
    for q, stem in START_TEXT.items():
        if stem == START_TEXT[6]:
            continue
        hit = [i for i, t in paras
               if re.sub(r"^\s*\d{1,2}[.\s]*", "", t).startswith(stem)
               or t.startswith(stem)]
        # skip the first occurrence for stems also present in the cover page
        if len(hit) != 1:
            raise ValueError("Q%d: stem found %d times" % (q, len(hit)))
        starts[q] = hit[0]
    # Data Booklet questions: the stem is the next non-empty paragraph
    for q, nxt in DATA_BOOKLET_STEM.items():
        cands = []
        for i in booklet:
            j = i + 1
            while j < len(kids) and not _own_text(kids[j]).strip():
                j += 1
            if _own_text(kids[j]).strip().startswith(nxt):
                cands.append(i)
        if len(cands) != 1:
            raise ValueError("Q%d: Data Booklet start found %d times" % (q, len(cands)))
        starts[q] = cands[0]
    order = [starts[q] for q in range(1, 31)]
    if order != sorted(order):
        raise ValueError("question starts not in order: %r" % order)
    return starts


def segment_items(kids, lo, hi, q):
    """Solution items of one question: [(kind, html|el, numid, source)]."""
    items = []
    for i in range(lo, hi):
        k = kids[i]
        ln = etree.QName(k).localname
        if ln != "p":
            continue
        if _is_blue_para(k):
            h = paragraph_html(k)
            if h.strip():
                items.append(("p", h, paragraph_numid(k), "para"))
        for c in _box_contents(k):
            txt = _text(c).strip()
            if any(txt == s for s in SKIP_BOX_TEXT.get(q, ())):
                continue
            if q in LEAKED_BOX and txt.startswith(LEAKED_BOX[q]):
                SKIPPED.append((q, txt[:40]))
                continue
            if not _box_is_blue(c):
                continue
            for kind, h, nid in _items(c):
                items.append((kind, h, nid, "box%d" % i))
    return items




def parse(unz_dir):
    unz = Path(unz_dir)
    tree = etree.parse(str(unz / "word" / "document.xml"))
    body = tree.getroot().find(Wq + "body")
    fixed = _resolve_symbols(body)
    kids = list(body)
    starts = _starts(kids)
    return tree, body, kids, starts, fixed


# ---- counted text fixes (applied to each question's final body HTML) --------
# (qnum, old, new, expected_count)
from .corrections import _PLS as _PLIMSOLL_STACK       # same markup as the question side

TEXT_FIXES = [
    # Q7: the school aligns "6 O / 3 O / 3 O" under the species with spaces
    (7, "6 O 3 O 3 O", "6 O&emsp;&emsp;3 O&emsp;&emsp;3 O", 1),
    # user rulings 2026-10-25: Q29 answer line D -> B; Q17 "propanoic" -> "ethanoic";
    # Q9 "Both decrease in temperature" -> "Both increase in temperature"
    (29, "<b>Answer: D</b>", "<b>Answer: B</b>", 1),
    (17, "propanoic acid", "ethanoic acid", 1),
    (9, "Both decrease in temperature", "Both increase in temperature", 1),
    # Q8: standard-state sign stacked over its subscript (as the question side);
    # the sentence-ending full stop typed inside the subscript; "kJmol"
    (8, "<i><sup>\u29b5</sup> </i><sub>f</sub>", _PLIMSOLL_STACK % "f", 2),
    (8, "<i><sup>\u29b5</sup> </i><sub>c</sub>", _PLIMSOLL_STACK % "c", 1),
    (8, "SO<sub>3.</sub>", "SO<sub>3</sub>.", 1),
    (8, "kJmol", "kJ mol", 1),
    # Q14: stray italic + underline on one subscript
    (14, "<i><u><sub>3</sub></u></i>", "<sub>3</sub>", 1),
    # Q16: a space before the full stop
    (16, "<sup>+</sup> .", "<sup>+</sup>.", 1),
    # Q22: one sentence split over two paragraphs by the school
    (22, 'substitution with</p>\n<p>-C<i class="el">l</i>.',
         'substitution with -C<i class="el">l</i>.', 1),
    # Q27: stray text that is in the file but not on the school's page; a space
    (27, "are in s", "", 1),
    (27, '=<span class="frac">', '= <span class="frac">', 1),
    # Q29: the school typed an overline (U+203E) for the minus of an anion charge
    (29, "OH\u203e", "OH<sup>\u2212</sup>", 4),
    (29, "<sup>3</sup>\u203e", "<sup>3\u2212</sup>", 1),
    (29, "<u><sup>3</sup></u><u>\u203e.</u>", "<u><sup>3\u2212</sup></u><u>.</u>", 1),
]
# ASCII hyphen standing in for a minus inside a superscript (charges, exponents):
# declared document-wide normalisation to U+2212 (as CJC 2024).


def _plain_html(h):
    return re.sub(r"<[^>]+>", "", re.sub(r"\x00[A-Z]+\x00", "", h)).replace("&nbsp;", " ")


def _lo_text(h):
    t = html.unescape(_plain_html(h)).replace("\t", " ")
    return re.sub(r"\s+", " ", t).strip()


def _table_rows(rows):
    return '<table class="cmp">%s</table>' % "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)


def build(q, items, lo_lines, log):
    """items -> (worked-solution html, [asset slots in order], key letter)."""
    # ---- 1. concept line(s) out
    kept, dropped = [], []
    drop_next = False
    for kind, h, nid, src in items:
        if kind == "p":
            pl = _lo_text(h)
            if CONCEPT_RX.match(pl) or (q == 25 and pl.startswith(Q25_HEADING)):
                dropped.append(pl)
                drop_next = q in CONCEPT_CONT
                continue
            if drop_next:
                drop_next = False
                if re.match(r"^(<b>)?\s{4,}", h):
                    dropped.append(pl)
                    continue
        kept.append((kind, h, nid, src))
    if len(dropped) != (2 if q in CONCEPT_CONT else 1):
        raise ValueError("Q%d: %d concept line(s) dropped: %r" % (q, len(dropped), dropped))
    lo_lines[q] = dropped

    # ---- 2. figures, document order
    plan = list(FIG_PLAN.get(q, []))
    slots = []
    out = []                                    # [(kind, html)]
    for kind, h, nid, src in kept:
        if kind == "tbl":
            raise ValueError("Q%d: unexpected table in a solution" % q)
        if nid not in (None, 0):
            raise ValueError("Q%d: unexpected list numbering %r" % (q, nid))
        h = h.replace(CENTRE, "")
        if FIG in h:
            segs = h.split(FIG)
            buf = segs[0]
            for nxt in segs[1:]:
                if not plan:
                    raise ValueError("Q%d: FIG without a plan entry" % q)
                rep = plan.pop(0)
                if rep is None:
                    buf += nxt
                elif rep[0] == "html":
                    buf += rep[1] + nxt
                else:
                    slot = rep[1]
                    slots.append(slot)
                    path = ASSET_FMT % (q, slot)
                    if rep[0] == "inline":
                        buf += ('<img class="ws-fig" data-asset="%s" alt="" style="%s">'
                                % (path, INLINE_STYLE)) + nxt
                    else:
                        # a block picture: the text so far, the picture, the rest
                        if _plain_html(buf).strip():
                            out.append(("p", buf))
                        out.append(("raw", '<p><img class="ws-fig" data-asset="%s" alt=""></p>'
                                    % path))
                        buf = nxt
            h = buf
            if not _plain_html(h).strip() and "<img" not in h:
                continue
        out.append(("p", h))
    if plan:
        raise ValueError("Q%d: %d FIG plan entries unused" % (q, len(plan)))
    if slots != ASSET_ORDER.get(q, []):
        raise ValueError("Q%d: assets %r != %r" % (q, slots, ASSET_ORDER.get(q, [])))

    # ---- 3. normalise paragraph html
    paras = []
    for kind, h in out:
        if kind == "raw":
            paras.append(("raw", h))
            continue
        h = _merge_runs(h)
        h = re.sub(r"^(<br>)+", "", h)
        paras.append(("p", h))
    # Q20: the two space-aligned rows become one table
    if q == 20:
        rows, rest, ins = [], [], None
        for kind, h in paras:
            pl = _lo_text(h)
            if kind == "p" and pl.startswith(Q20_ROWS):
                if ins is None:
                    ins = len(rest)
                cells = [c.strip() for c in re.split(r"\s{2,}|\t", _plain_html(h).strip())
                         if c.strip()]
                if len(cells) != 4:
                    raise ValueError("Q20 row not 4 cells: %r" % cells)
                rows.append(cells)
            else:
                rest.append((kind, h))
        if len(rows) != 2:
            raise ValueError("Q20: expected 2 aligned rows, found %d" % len(rows))
        rest.insert(ins, ("raw", _table_rows(rows)))
        paras = rest
    # bold: a solution typed >= 70% in bold is the author's habit, not emphasis
    body_p = [h for k, h in paras if k == "p" and not _keep_bold(h)
              and not re.match(r"\s*(<b>)?\s*Ans", _plain_html(h))]
    ratio = _bold_ratio(body_p)
    strip = ratio >= 0.70
    if strip:
        log.append("Q%d: bold-dominant (%.0f%%), bold dropped except the answer line"
                   % (q, 100 * ratio))
    blocks = []
    for kind, h in paras:
        if kind == "raw":
            blocks.append(h)
            continue
        is_ans = bool(re.match(r"\s*(<b>)?\s*Ans", _plain_html(h)))
        if strip and not is_ans:
            h = _unbold(h)
        h = _merge_runs(h)
        h = _tidy_ws(h)
        if not (_plain_html(h).strip() or "<img" in h):
            continue
        blocks.append("<p>%s</p>" % h)
    body = "\n".join(blocks)
    body = re.sub(r"(?<=\S) {2,}(?=\S)", " ", body)
    body = re.sub(
        r"<sup>([^<]*)</sup>",
        lambda m: "<sup>%s</sup>" % m.group(1).replace("-", "−"), body)
    for fq, old, new, exp in TEXT_FIXES:
        if fq != q:
            continue
        n = body.count(old)
        if n != exp:
            raise ValueError("Q%d text fix %r: expected %d, found %d" % (q, old, exp, n))
        body = body.replace(old, new)

    # ---- 4. key letter from the solution's own answer line
    ans = None
    for kind, h, _n, _s in kept:
        m = re.match(r"\s*Ans(?:wer)?\s*:?\s*([A-D])\b", _lo_text(h))
        if m:
            ans = m.group(1)
            break
    if not ans and q not in NO_ANS_LINE:
        raise ValueError("Q%d: no 'Ans/Answer: X' line" % q)
    return '<div class="worked-solution">\n%s\n</div>' % body, slots, ans


def pdf_key(pdf):
    """The 30 letters of the answer-key table on the cover page of the Word PDF."""
    import pymupdf
    page = pymupdf.open(str(pdf))[0]
    words = [w[4] for w in page.get_text("words")]
    i = words.index("SOLUTIONS")
    seq = [w for w in words[i + 1:] if re.fullmatch(r"\d{1,2}|[A-D]", w)][:60]
    nums = [int(w) for w in seq if w.isdigit()]
    letters = [w for w in seq if not w.isdigit()]
    if nums != list(range(1, 31)) or len(letters) != 30:
        raise ValueError("cover key table not read: %r" % seq)
    return {q: letters[q - 1] for q in range(1, 31)}


# Q29: the solution box ends "Answer: D" but the key table and the highlighted
# option are B (redox): a school error, to be ruled on by the user.
KEY_DISAGREES = {29}
# Q22 has no "Ans:" line ("Option B is not true (the answer)"): key from the cover table
NO_ANS_LINE = {22}


def extract(unz_dir, pdf):
    tree, body, kids, starts, fixed = parse(unz_dir)
    ws, key, assets, lo_lines, log = {}, {}, [], {}, []
    for q in range(1, 31):
        lo = starts[q]
        hi = starts[q + 1] if q < 30 else len(kids)
        items = segment_items(kids, lo, hi, q)
        html, slots, ans = build(q, items, lo_lines, log)
        ws[q], key[q] = html, ans
        for off, slot in enumerate(slots, start=1):
            assets.append({"question": q, "slot": slot,
                           "path": ASSET_FMT % (q, slot), "offset": off})
    if SKIPPED != [(6, "Concept: Energetics" + SKIPPED[0][1][19:])] and len(SKIPPED) != 1:
        raise ValueError("leaked-box skip count %r" % SKIPPED)
    pk = pdf_key(pdf)
    bad = {q: (key[q], pk[q]) for q in key if key[q] and key[q] != pk[q]}
    if {q for q in key if not key[q]} != NO_ANS_LINE:
        raise ValueError("unexpected missing answer lines")
    if set(bad) != KEY_DISAGREES:
        raise ValueError("answer key disagrees (solution line, cover table): %r" % bad)
    log.append("KEY DISAGREES (school error): %r" % bad)
    key = dict(pk)                  # the cover table (and the highlighted option) rule
    return ws, key, assets, lo_lines, fixed, log, bad


def main(unz_dir, pdf, outdir):
    ws, key, assets, lo_lines, fixed, log, bad = extract(unz_dir, pdf)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "worked_solutions.json").write_text(
        json.dumps({str(q): h for q, h in ws.items()}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    (out / "answer_key.json").write_text(
        json.dumps({str(q): k for q, k in key.items()}, indent=1), encoding="utf-8")
    (out / "answer_assets.json").write_text(json.dumps(assets, indent=1), encoding="utf-8")
    (out / "school_lo_lines.json").write_text(
        json.dumps({str(q): v for q, v in sorted(lo_lines.items())}, indent=1,
                   ensure_ascii=False), encoding="utf-8")
    (out / "anomalies.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("questions:", len(ws), " assets:", len(assets), " symbols:", fixed)
    print("key:", "".join(key[q] for q in sorted(key)))
    for l in log:
        print("  ", l)


if __name__ == "__main__":      # pragma: no cover
    main(sys.argv[1], sys.argv[2], sys.argv[3])
