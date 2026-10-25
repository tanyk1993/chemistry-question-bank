"""CJC 2026 H2 P1 (9476/01): prepare the paragraph-flow question paper for
`questions_flow.py`.

Two things the generic `flow_numpr_prep` cannot do on this paper:

1. QUESTION NUMBERS. Most are typed digits glued to the stem ("2Which ...");
   three (Q1, Q16, Q17) are `w:numPr` list paragraphs whose number exists only
   at render time. `flow_numpr_prep` accepts a numPr paragraph when its list
   number == last + 1, and here that coincides with the THIRD item of Q2's
   statement list (3 == 2 + 1), so it typed a bogus number into a statement
   and stopped finding the real questions. This prep adds one structural test:
   a numPr paragraph is a question start only if it is NOT adjacent to another
   numPr paragraph of the same list (statement items always are; a question
   stem never is, because its options sit between it and the next question).

2. A LEAKED SOLUTION. The "for exchange" file still carries one floating text
   box of worked solution ("Concept: Energetics ... Ans: C", which is really
   Q7's solution) anchored in Q6's stem paragraph. It is answer-side content,
   so it is removed from the QUESTION copy and reported (the answers stage will
   decide what to do with it).

3. SMALL STRUCTURAL TIDY-UPS in the question copy (each reported):
   * Q21's option table has an empty spacer first column; removed.
   * Q11's option C has a stray space run between the letter and its tab,
     which defeats the "tab follows the letter" marker test; removed.
   * Q12's three graphs sit in one table of floating shapes; the table is
     replaced by ONE picture paragraph (the user snips the three graphs, with
     their numbers and captions, as one image).
   * Q22 option A is a MathType object holding "(CH3)3COH2+ and (CH3)3COH";
     typed in place (it is plain text, not a picture).
   * Typed statements ("1<tab>text", "2<tab>text") become real list items so
     they render as the house `ol.stmts` (Q14, Q20, Q24, Q28).

usage: python3 -m ingest.cjc26_p1_prep <unz_dir> <unz_q_dir>
The ORIGINAL directory is never touched; the result is a copy.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from lxml import etree

from .oxml import NS
from .questions_flow import QSTART
from .flow_numpr_prep import _starts

W = "{%s}" % NS["w"]


def _numpr(p):
    npr = p.find("w:pPr/w:numPr", NS)
    if npr is None:
        return None
    nid = npr.find("w:numId", NS)
    il = npr.find("w:ilvl", NS)
    return (nid.get(W + "val") if nid is not None else None,
            il.get(W + "val") if il is not None else "0")


def _is_text(p):
    return bool("".join(p.itertext()).strip())


def _rtext(r):
    out = []
    for c in r:
        ln = etree.QName(c).localname
        if ln == "t":
            out.append(c.text or "")
        elif ln == "tab":
            out.append("\t")
    return "".join(out)


def _mk_run(text, sub=False, sup=False, like=None):
    r = etree.Element(W + "r")
    if like is not None and like.find("w:rPr", NS) is not None:
        import copy
        rpr = copy.deepcopy(like.find("w:rPr", NS))
        for va in rpr.findall("w:vertAlign", NS):
            rpr.remove(va)
        r.append(rpr)
    if sub or sup:
        rpr = r.find("w:rPr", NS)
        if rpr is None:
            rpr = etree.SubElement(r, W + "rPr")
        va = etree.SubElement(rpr, W + "vertAlign")
        va.set(W + "val", "subscript" if sub else "superscript")
    t = etree.SubElement(r, W + "t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def _untype_statement(p, n):
    """Strip the typed number (and its tab) off statement paragraph `p`, then
    mark it as a list item (numPr), so questions_flow wraps it in ol.stmts.
    Returns False (and leaves `p` untouched) if the paragraph does not have the
    typed-number shape."""
    runs = p.findall("w:r", NS)
    k = None
    for i, r in enumerate(runs):
        tx = _rtext(r)
        if tx.strip() == str(n):
            k = i
            break
        if tx.strip():                  # some other text came first
            return False
    if k is None:
        return False
    for r in runs[:k + 1]:
        p.remove(r)
    rest = runs[k + 1:]
    # the tab that separates the number from the text: either its own run or
    # the first child of the next text run
    for r in rest:
        if not _rtext(r).strip() and _rtext(r) != "":
            p.remove(r)                 # whitespace/tab-only run
            continue
        kids = [c for c in r if etree.QName(c).localname != "rPr"]
        if kids and etree.QName(kids[0]).localname == "tab":
            r.remove(kids[0])
        break
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        ppr = etree.Element(W + "pPr")
        p.insert(0, ppr)
    npr = etree.Element(W + "numPr")
    il = etree.SubElement(npr, W + "ilvl")
    il.set(W + "val", "0")
    nid = etree.SubElement(npr, W + "numId")
    nid.set(W + "val", "16")
    ppr.insert(0, npr)
    return True


def prep(unz_dir, out_dir):
    unz_dir, out_dir = Path(unz_dir), Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(unz_dir, out_dir)
    starts = _starts(out_dir / "word/numbering.xml")
    doc = out_dir / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    paras = body.findall("w:p", NS)

    # ---- 2. leaked solution text boxes (in the question copy only)
    removed = []
    for p in paras:
        for ac in list(p.iter("{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent")) + \
                list(p.iter(W + "drawing")):
            txt = " ".join("".join(tb.itertext())
                           for tb in ac.iter(W + "txbxContent"))
            if "Ans:" in txt and "Concept:" in txt:
                run = ac
                while run is not None and run.tag != W + "r":
                    run = run.getparent()
                if run is not None and run.getparent() is not None:
                    run.getparent().remove(run)
                    removed.append(txt.strip()[:60])
                break

    # ---- 3. Symbol-font "o" (U+F06F), used in two senses on this paper.
    # Symbol 0x6F is a Greek omicron in the shared table, so it is resolved
    # here from context instead of being added to `symbols.SYMBOL` (the
    # auditor's independent encoding would then disagree):
    #   after "/ " and before "C"  -> degree sign (Q4/Q30 "boiling point / °C")
    #   after "ΔH"                 -> the standard-state sign U+29B5 (Q8)
    # The Symbol-font spaces (U+F020) that pad the Q8 ΔH⦵f runs are removed.
    fixed = {"degree": 0, "plimsoll": 0}
    for p in list(body.iter(W + "p")):         # includes paragraphs inside tables
        runs = p.findall("w:r", NS)
        for i, r in enumerate(runs):
            f = r.find("w:rPr/w:rFonts", NS)
            if f is None or "ymbol" not in (f.get(W + "ascii") or ""):
                continue
            ts = r.findall("w:t", NS)
            raw = "".join(t.text or "" for t in ts)
            if raw == "\uf020":                      # Symbol-font space
                nb = "".join("".join(x.itertext()) for x in runs[max(0, i - 2):i])
                na = "".join("".join(x.itertext()) for x in runs[i + 1:i + 3])
                if nb.endswith("\u0394H") or nb.endswith("\u0394H\uf020") \
                        or na.startswith("\uf06f") or na.startswith("\uf020f") \
                        or nb.endswith("\uf06f"):
                    # leave real spacing alone; only the plimsoll's padding goes
                    if ("\u0394H" in nb[-4:]) or na.startswith("\uf06f") \
                            or na.startswith("\uf020f") or nb.endswith("\uf06f"):
                        p.remove(r)
                continue
            if raw.strip("\uf020 ") != "\uf06f":
                continue
            before = "".join("".join(x.itertext()) for x in runs[max(0, i - 3):i])
            after = "".join("".join(x.itertext()) for x in runs[i + 1:i + 3])
            if before.rstrip().endswith("/") and after.lstrip().startswith("C"):
                new_txt, kind = "\u00b0", "degree"
            elif "\u0394H" in before[-6:]:
                new_txt, kind = "\u29b5", "plimsoll"
            else:
                raise SystemExit("cjc26_p1_prep: unclassified Symbol-font o "
                                 "after %r" % before[-20:])
            f.getparent().remove(f)                  # drop the Symbol font
            ts[0].text = new_txt
            for extra in ts[1:]:
                r.remove(extra)
            fixed[kind] += 1

    # ---- 4. structural tidy-ups (see module docstring, item 3)
    tidy = []
    import copy
    # (a) Q21: drop the empty spacer first column of the option table
    for tbl in body.findall("w:tbl", NS):
        grid = [g.get(W + "w") for g in tbl.findall("w:tblGrid/w:gridCol", NS)]
        rows = tbl.findall("w:tr", NS)
        if len(grid) == 5 and len(rows) == 5 and all(
                not "".join(r.findall("w:tc", NS)[0].itertext()).strip()
                for r in rows) and "".join(rows[1].itertext()).startswith("A"):
            tbl.find("w:tblGrid", NS).remove(
                tbl.find("w:tblGrid", NS).findall("w:gridCol", NS)[0])
            for r in rows:
                r.remove(r.findall("w:tc", NS)[0])
            tidy.append("Q21: spacer column removed from the option table")
    # (b) Q11: a space-only run between a bare option letter and its tab run
    for p in body.iter(W + "p"):
        runs = p.findall("w:r", NS)
        for i in range(1, len(runs) - 1):
            if _rtext(runs[i]) == " " and _rtext(runs[i - 1]) in "ABCD" \
                    and _rtext(runs[i - 1]) and _rtext(runs[i + 1]).startswith("\t"):
                p.remove(runs[i])
                tidy.append("stray space run after option letter %s removed"
                            % _rtext(runs[i - 1]))
    # (c) Q12: replace the table of three graphs by one picture paragraph
    for tbl in body.findall("w:tbl", NS):
        txt = "".join(tbl.itertext())
        if "no Mn2+ added" in txt.replace("\u00b2\u207a", "2+") or \
                ("MnO4" in txt and "time" in txt and "rate" in txt):
            pic = None
            for r in tbl.iter(W + "r"):
                if r.find(W + "drawing") is not None and \
                        r.find(".//{http://schemas.openxmlformats.org/drawingml/2006/picture}pic") is not None:
                    pic = r
                    break
            if pic is None:
                raise SystemExit("cjc26_p1_prep: Q12 table has no picture run")
            newp = etree.Element(W + "p")
            newp.append(copy.deepcopy(pic))
            tbl.getparent().replace(tbl, newp)
            tidy.append("Q12: table of three graphs replaced by one picture paragraph")
    # (d) Q22: option A object -> typed text
    for p in body.iter(W + "p"):
        if "".join(p.itertext()).startswith("Aare conjugate"):
            runs = p.findall("w:r", NS)
            obj = [r for r in runs if r.find(W + "object") is not None]
            if len(obj) != 1:
                raise SystemExit("cjc26_p1_prep: Q22 option A object not found")
            like = [r for r in runs if _rtext(r).startswith("are ")][0]
            new = [_mk_run("(CH", like=like), _mk_run("3", sub=True, like=like),
                   _mk_run(")", like=like), _mk_run("3", sub=True, like=like),
                   _mk_run("COH", like=like), _mk_run("2", sub=True, like=like),
                   _mk_run("+", sup=True, like=like),
                   _mk_run(" and (CH", like=like), _mk_run("3", sub=True, like=like),
                   _mk_run(")", like=like), _mk_run("3", sub=True, like=like),
                   _mk_run("COH ", like=like)]
            at = list(p).index(obj[0])
            p.remove(obj[0])
            for j, r in enumerate(new):
                p.insert(at + j, r)
            tidy.append("Q22: option A object typed as text")

    # ---- 1. question numbers
    last, seen, accepted = 0, {}, []
    qstarts = set()
    for i, p in enumerate(paras):
        text = "".join(p.itertext())
        np_ = _numpr(p)
        if np_ is not None:
            nid, ilvl = np_
            if nid is None or ilvl != "0" or not text.strip():
                continue
            n = starts.get(nid, 1) + seen.get(nid, 0)
            seen[nid] = seen.get(nid, 0) + 1
            adj = False
            for j in (i - 1, i + 1):
                if 0 <= j < len(paras):
                    q = _numpr(paras[j])
                    if q is not None and q[0] == nid and _is_text(paras[j]):
                        adj = True
            if n == last + 1 and not adj:
                p.find("w:pPr/w:numPr", NS).getparent().remove(
                    p.find("w:pPr/w:numPr", NS))
                run = etree.Element(W + "r")
                t = etree.SubElement(run, W + "t")
                t.text = str(n)
                ppr = p.find("w:pPr", NS)
                p.insert(list(p).index(ppr) + 1 if ppr is not None else 0, run)
                last = n
                qstarts.add(id(p))
                accepted.append((n, "auto-numbered"))
            continue
        m = QSTART.match(text)
        if m and int(m.group(1)) == last + 1:
            last = int(m.group(1))
            qstarts.add(id(p))
            accepted.append((last, "typed"))

    # (e) typed statements -> list items (after the question numbers are
    # settled, so a question start is never mistaken for statement 1/2/3)
    run_items, converted = [], 0

    def _flush():
        nonlocal run_items, converted
        if len(run_items) >= 2:
            for n, para in run_items:
                if _untype_statement(para, n):
                    converted += 1
                    tidy.append("  statement %d: %s"
                                % (n, "".join(para.itertext())[:40]))
        run_items = []
    for el in list(body):
        if etree.QName(el).localname != "p":
            _flush()
            continue
        text = "".join(el.itertext())
        if not text.strip():
            continue
        if id(el) in qstarts or _numpr(el) is not None:
            _flush()
            continue
        want = len(run_items) + 1
        first = [r for r in el.findall("w:r", NS) if _rtext(r).strip()][:1]
        if first and _rtext(first[0]).strip() == str(want):
            run_items.append((want, el))
        else:
            _flush()
    _flush()
    if converted:
        tidy.append("typed statements converted to list items: %d" % converted)

    nums = [n for n, _k in accepted]
    if nums != list(range(1, 31)):
        raise SystemExit("cjc26_p1_prep: question numbers %s are not exactly "
                         "1..30" % nums)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8",
               standalone=True)
    return accepted, removed, fixed, tidy


if __name__ == "__main__":
    acc, rem, fixed, tidy = prep(sys.argv[1], sys.argv[2])
    for t in tidy:
        print("tidy: %s" % t)
    print("Symbol-font o resolved: %s" % fixed)
    print("questions: %d; auto-numbered (typed in): %s"
          % (len(acc), [n for n, k in acc if k == "auto-numbered"]))
    for r in rem:
        print("removed leaked solution text box: %s ..." % r)
