"""Strip the school's coloured ANSWER layer (blue / red / green / teal) out of a Word-exported PDF at the
content-stream level, leaving only the black / grey question content, so question figures can be cropped clean.

The stream is walked operator by operator with a graphics-state stack (q / Q) that tracks the current fill and stroke
colour (g G rg RG k K). A painting operator (S s f F f* B B* b b* for paths; Tj TJ ' " for text) issued while the
relevant colour is CHROMATIC is removed (a path is ended with `n` instead, so nothing is painted). The object is deleted,
not painted over, so black / grey content it used to overlap (grid lines under a drawn curve) is intact.
Images / Do / sh are kept. Inline images are refused (Word does not write them).

usage: python3 -m ingest.strip_answer_colours in.pdf out.pdf
or import `clean(src, dst, drop_rects={page_no: [(x, y, w, h), ...]})`; drop_rects removes a WHITE-FILLED `re` box (stream
coordinates) that is itself an answer label (TMJC 2026 P2 Fig. 2.1 "Run B" box).
First used for TMJC 2026 H2 P2, whose Word file is the question paper with the mark scheme overlaid in blue/red/green:
a plain crop of the Word PDF would carry the answers, and a colour mask would punch holes in the black grid beneath them.
"""
import re
import sys

import pymupdf

WS = b" \t\r\n\f\x00"
DELIM = b"()<>[]{}/%"
PAINT_STROKE = {b"S", b"s"}
PAINT_FILL = {b"f", b"F", b"f*"}
PAINT_BOTH = {b"B", b"B*", b"b", b"b*"}
SHOW = {b"Tj", b"TJ", b"'", b'"'}


def tokens(c):
    """yield (kind, bytes): kind in 'op' (operator) or 'arg' (operand source text, incl. strings/arrays/names/numbers)"""
    i, n = 0, len(c)
    while i < n:
        ch = c[i:i + 1]
        if ch in WS:
            i += 1
        elif ch == b"%":
            while i < n and c[i:i + 1] not in b"\r\n":
                i += 1
        elif ch == b"(":
            depth, j = 1, i + 1
            while j < n and depth:
                cj = c[j:j + 1]
                if cj == b"\\":
                    j += 2
                    continue
                if cj == b"(":
                    depth += 1
                elif cj == b")":
                    depth -= 1
                j += 1
            yield "arg", c[i:j]
            i = j
        elif ch == b"[":
            depth, j = 1, i + 1
            while j < n and depth:
                cj = c[j:j + 1]
                if cj == b"(":
                    k = j + 1
                    d2 = 1
                    while k < n and d2:
                        ck = c[k:k + 1]
                        if ck == b"\\":
                            k += 2
                            continue
                        if ck == b"(":
                            d2 += 1
                        elif ck == b")":
                            d2 -= 1
                        k += 1
                    j = k
                    continue
                if cj == b"[":
                    depth += 1
                elif cj == b"]":
                    depth -= 1
                j += 1
            yield "arg", c[i:j]
            i = j
        elif ch == b"<":
            if c[i:i + 2] == b"<<":
                depth, j = 1, i + 2
                while j < n and depth:
                    if c[j:j + 2] == b"<<":
                        depth += 1
                        j += 2
                    elif c[j:j + 2] == b">>":
                        depth -= 1
                        j += 2
                    else:
                        j += 1
                yield "arg", c[i:j]
                i = j
            else:
                j = c.index(b">", i) + 1
                yield "arg", c[i:j]
                i = j
        elif ch == b"/":
            j = i + 1
            while j < n and c[j:j + 1] not in WS and c[j:j + 1] not in DELIM:
                j += 1
            yield "arg", c[i:j]
            i = j
        else:
            j = i
            while j < n and c[j:j + 1] not in WS and c[j:j + 1] not in DELIM:
                j += 1
            w = c[i:j]
            if re.fullmatch(rb"[-+]?(\d+\.?\d*|\.\d+)", w):
                yield "arg", w
            else:
                yield "op", w
            i = j


def chromatic(vals):
    return max(vals) - min(vals) > 0.05


def clean_stream(c, drop_rects=()):
    """drop_rects: (x, y, w, h) of `re` boxes (PDF coordinates, as written in the stream) whose fill is to be removed"""
    out, args = [], []
    last_re = None
    stack = []
    fill, stroke = (0, 0, 0), (0, 0, 0)
    dropped = {"path": 0, "text": 0}
    in_path = False
    for kind, t in tokens(c):
        if kind == "arg":
            args.append(t)
            continue
        op = t
        if op == b"BI":
            raise SystemExit("inline image not supported")
        emit = True
        if op == b"re" and len(args) == 4:
            last_re = [float(a) for a in args]
        if op == b"q":
            stack.append((fill, stroke))
        elif op == b"Q":
            if stack:
                fill, stroke = stack.pop()
        elif op in (b"rg", b"RG", b"g", b"G", b"k", b"K"):
            v = [float(a) for a in args]
            if op in (b"g", b"G"):
                rgb = (v[0],) * 3
            elif op in (b"k", b"K"):
                rgb = (1 - min(1, v[0] + v[3]), 1 - min(1, v[1] + v[3]), 1 - min(1, v[2] + v[3]))
            else:
                rgb = tuple(v)
            if op in (b"rg", b"g", b"k"):
                fill = rgb
            else:
                stroke = rgb
        elif op in (b"sc", b"scn", b"SC", b"SCN", b"cs", b"CS"):
            raise SystemExit("unsupported colour operator %r" % op)
        elif op in PAINT_STROKE or op in PAINT_FILL or op in PAINT_BOTH:
            bad = (op in PAINT_STROKE and chromatic(stroke)) or (op in PAINT_FILL and chromatic(fill)) or \
                  (op in PAINT_BOTH and (chromatic(stroke) or chromatic(fill)))
            if not bad and last_re and op in (PAINT_FILL | PAINT_BOTH) and any(
                    all(abs(a - b) < 0.2 for a, b in zip(last_re, r)) for r in drop_rects):
                bad = True
            if bad:
                op = b"n"
                dropped["path"] += 1
        elif op in SHOW:
            if chromatic(fill):
                emit = False
                dropped["text"] += 1
        if emit:
            out.append(b" ".join(args + [op]))
        args = []
    return b"\n".join(out), dropped


def clean(src, dst, drop_rects=None):
    drop_rects = drop_rects or {}
    d = pymupdf.open(src)
    report = []
    for pg in d:
        new, dr = clean_stream(pg.read_contents(), drop_rects.get(pg.number + 1, ()))
        xrefs = pg.get_contents()
        d.update_stream(xrefs[0], new)
        for x in xrefs[1:]:
            d.update_stream(x, b" ")
        report.append((pg.number + 1, dr))
    # Form XObjects (ChemDraw / EMF drawings come through as Forms): same treatment, in place
    nforms = 0
    for xref in range(1, d.xref_length()):
        try:
            if d.xref_get_key(xref, "Subtype")[1] != "/Form":
                continue
            raw = d.xref_stream(xref)
        except Exception:
            continue
        if not raw:
            continue
        new, dr = clean_stream(raw)
        if new != raw:
            d.update_stream(xref, new)
            nforms += 1
    report.append(("forms changed", {"path": nforms, "text": 0}))
    d.save(dst, garbage=0)
    return report


if __name__ == "__main__":
    for pn, dr in clean(sys.argv[1], sys.argv[2]):
        print(("p%-2d" % pn if isinstance(pn, int) else pn), "dropped paths %4d  text %4d" % (dr["path"], dr["text"]))
