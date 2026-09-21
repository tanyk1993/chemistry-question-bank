#!/usr/bin/env python3
"""Render the extracted questions the way index.html will, into one HTML file.

This is the FIGURE GATE as well as a preview. It does not lay the images out
however it likes -- it reproduces the frontend's own algorithm:

  1. resolveAssets(): set src on `img[data-asset="FILE.png"]`, matched by
     FILENAME, before anything else.
  2. split the remaining assets into stem (slot not A-E) and option (slot
     exactly A-E, isOptSlot = /^[A-E]$/).
  3. walk `.fig` placeholders in DOM order, filling them from the stem assets
     sorted by ORDINAL; the first placeholder left over receives the whole
     option grid; any placeholder after that is REMOVED.

Reproducing the consumer is the only way the check can catch a rotation: a
count of figures cannot, and neither can looking at the images on their own.
Handoff SS9 -- "a check that cannot fail is not a check".

Usage:
  python3 -m ingest.build_question_preview index.html <outdir> <preview.html>
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

IS_OPT = re.compile(r"^[A-E]$")


def _css(index_html: Path) -> str:
    txt = index_html.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", txt, re.S)
    return "\n".join(blocks)


def _data_uri(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def render_question(row: dict, assets: list, adir: Path) -> str:
    html = row["content_html"]
    by_name = {a["storage_path"]: a for a in assets}

    # 1. inline images, matched by filename
    def _inline(m):
        name = m.group(1)
        a = by_name.get(name)
        if a is None:
            return '<b style="color:red">[missing inline asset %s]</b>' % name
        f = adir / name
        if not f.exists():
            return '<b style="color:red">[no file %s]</b>' % name
        return '<img src="%s" alt="">' % _data_uri(f)

    html = re.sub(r'<img data-asset="([^"]+)" alt="">', _inline, html)

    # 2/3. placeholders, exactly as index.html fills them
    stem = sorted((a for a in assets if not IS_OPT.match(a["slot"])),
                  key=lambda a: a["ordinal"])
    opts = sorted((a for a in assets if IS_OPT.match(a["slot"])),
                  key=lambda a: a["slot"])
    # inline assets have already been placed by filename; the frontend does NOT
    # exclude them from the stem list, which is exactly why block figures must
    # hold the lower ordinals. Mirror that here rather than correcting for it.
    placed_inline = {m for m in by_name if 'data-asset="%s"' % m in row["content_html"]}
    stem = [a for a in stem if a["storage_path"] not in placed_inline]

    out, si, grid_done = [], 0, False
    for chunk in re.split(r'(<div class="fig">figure</div>)', html):
        if chunk != '<div class="fig">figure</div>':
            out.append(chunk)
            continue
        if si < len(stem):
            a = stem[si]; si += 1
            f = adir / a["storage_path"]
            out.append('<div class="figimg"><img src="%s" alt="">'
                       '<div style="font:11px monospace;color:#888">%s ord%d</div>'
                       "</div>"
                       % (_data_uri(f) if f.exists() else "", a["slot"], a["ordinal"]))
        elif opts and not grid_done:
            grid_done = True
            rows = []
            for a in opts:
                f = adir / a["storage_path"]
                # Mirror index.html's .optcap: the option's own text is printed
                # under its diagram, unless it is the "[structure A]" search
                # placeholder standing in for a figure-only option.
                cap = (row.get("options") or {}).get(a["slot"], "")
                if re.fullmatch(r"\[structure [A-E]\]", cap.strip()):
                    cap = ""
                rows.append('<div class="optrow"><b>%s</b><div class="optbody">'
                            '<img src="%s" alt="">%s</div></div>'
                            % (a["slot"], _data_uri(f) if f.exists() else "",
                               '<div class="optcap">%s</div>' % cap if cap else ""))
            out.append('<div class="optgrid">%s</div>' % "".join(rows))
        else:
            out.append('<b style="color:red">[placeholder with no asset — '
                       "the frontend would DELETE this]</b>")
    if si < len(stem):
        out.append('<b style="color:red">[%d stem assets had no placeholder — '
                   "they would never render]</b>" % (len(stem) - si))
    return "".join(out)


def main(index_html, outdir, dest):
    out = Path(outdir)
    rows = json.loads((out / "questions.json").read_text(encoding="utf-8"))
    plan = json.loads((out / "asset_plan.json").read_text(encoding="utf-8"))
    by_q: dict = {}
    for a in plan:
        by_q.setdefault(a["question"], []).append(a)

    parts = ["<!doctype html><meta charset='utf-8'><title>RI 2024 H2 P1 preview</title>",
             "<style>%s</style>" % _css(Path(index_html)),
             "<style>body{max-width:60em;margin:2em auto;font-family:system-ui;"
             "background:#fff;color:#111}"
             ".qwrap{border:1px solid #ddd;border-radius:8px;padding:1em 1.2em;"
             "margin:1.2em 0}.qn{font:700 13px monospace;color:#888}"
             ".key{float:right;font:700 13px monospace;color:#0a7}</style>"]
    for r in rows:
        qn = r["question_number"]
        parts.append("<div class='qwrap'><div class='qn'>Q%d</div>"
                     "<div class='stem'>%s</div></div>"
                     % (qn, render_question(r, by_q.get(qn, []), out / "assets")))
    Path(dest).write_text("\n".join(parts), encoding="utf-8")
    print("wrote", dest)


if __name__ == "__main__":
    main(*sys.argv[1:4])
