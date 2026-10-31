"""Prepare EJC 2026 H2 P2 (9476/02, structured, paragraph-flow) for `parts_flow.py`.

Two things the generic `flow_parts_prep` does not cover on this paper:

1. A part label is often split over several BOLD runs: "(", "a", ")" and an
   empty bold run ("1(a)Calcium", "(d)(i)For", "5(b)Lactic"). `parts_flow`
   recognises a label only as ONE run whose text is exactly "(a)" / "(i)" / a
   bare digit, so a split label is silently lost. Here every leading group of
   bold runs "(" + token + ")" is merged into the first run.
2. Auto-numbered labels ((i)/(ii)/(iii) lists and the (a)/(b) list on Q2) are
   typed in by `flow_parts_prep.prep` first, on the same copy.

The ORIGINAL document.xml is never touched: the result is a copy of the
unzipped directory.

Run:  python3 -m ingest.ejc26_p2_prep unz unz_prep
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from lxml import etree

from . import flow_parts_prep
from .oxml import NS

W = "{%s}" % NS["w"]
_TOKEN = re.compile(r"^[a-z]{1,4}$")  # a, b, i, ii, iii, iv ...
COVER_END = "1 Carbon can form"


def _is_bold(r) -> bool:
    b = r.find("w:rPr/w:b", NS)
    return b is not None and b.get(W + "val") not in ("0", "false")


def _text(r) -> str:
    return "".join(t.text or "" for t in r.findall("w:t", NS))


def _plain_run(r) -> bool:
    """A run that is only w:rPr + w:t children (safe to merge/drop)."""
    return all(c.tag in (W + "rPr", W + "t") for c in r)


def merge_split_labels(p) -> int:
    """Merge bold '(' + token + ')' runs inside one paragraph into '(token)'.
    Only runs of the leading label zone are touched (before the first
    non-bold non-empty run). Returns the number of merges."""
    runs = [c for c in p if c.tag == W + "r"]
    n, i = 0, 0
    while i < len(runs):
        r = runs[i]
        t = _text(r)
        if not _is_bold(r) and t.strip():
            break  # leading label zone over
        if t == "(" and _is_bold(r) and _plain_run(r):
            # find the token and ")" among the next bold runs (skip empties)
            j, got = i + 1, []
            while j < len(runs) and len(got) < 2 and _is_bold(runs[j]) and _plain_run(runs[j]):
                tj = _text(runs[j])
                if tj != "":
                    got.append((j, tj))
                j += 1
            if (len(got) == 2 and _TOKEN.match(got[0][1]) and got[1][1] == ")"):
                ts = r.findall("w:t", NS)
                ts[0].text = "(" + got[0][1] + ")"
                ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                for k in range(i + 1, got[1][0] + 1):
                    runs[k].getparent().remove(runs[k])
                n += 1
                runs = [c for c in p if c.tag == W + "r"]
                i += 1
                continue
        i += 1
    return n


def drop_repeated_qnum(body) -> list:
    """The paper reprints the question number beside a part label when a
    question continues on a new page ("5(b)Lactic acid ..."). `parts_flow`
    reads a leading bold bare digit as a NEW question, so Q5 split in two.
    Blank such a run when the digit equals the question currently open."""
    cur, dropped = 0, []
    for p in body.findall("w:p", NS):
        for r in p.findall("w:r", NS):
            t = _text(r)
            if not _is_bold(r):
                if t.strip():
                    break
                continue
            if t == "":
                continue
            if re.fullmatch(r"\d{1,2}", t):
                n = int(t)
                if n == cur:
                    r.find("w:t", NS).text = ""
                    dropped.append(n)
                elif n == cur + 1:
                    cur = n
            break
    return dropped


def prep(unz_dir, out_dir):
    done = flow_parts_prep.prep(unz_dir, out_dir, COVER_END)
    doc = Path(out_dir) / "word/document.xml"
    tree = etree.parse(str(doc))
    body = tree.getroot().find("w:body", NS)
    merged = sum(merge_split_labels(p) for p in body.findall("w:p", NS))
    dropped = drop_repeated_qnum(body)
    print("repeated question numbers blanked:", dropped)
    tree.write(str(doc), xml_declaration=True, encoding="UTF-8", standalone=True)
    return done, merged


if __name__ == "__main__":
    done, merged = prep(sys.argv[1], sys.argv[2])
    print("typed auto-numbers:", len(done), "| merged split labels:", merged)
