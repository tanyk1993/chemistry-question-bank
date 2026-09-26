#!/usr/bin/env python3
"""Preview a structured-paper ingest with its REAL figures, before any SQL.

Reads what `extract_parts.py` wrote -- questions.json, asset_plan.json and the
cropped assets -- and renders it with `index.html`'s own CSS, so the review is
of the markup that will actually be stored, not an approximation of it.

It fills the `div.fig` placeholders THE WAY THE FRONTEND DOES: in DOM order,
from the question's assets sorted by ordinal. That is deliberate. Reproducing
the consumer's own pairing is what makes this able to catch a rotation, which
handoff SS7 records as this pipeline's costliest defect -- a check that
matches figures the way the extractor holds them cannot see one.

Images are embedded as data URIs and downscaled, so the file can be sent and
opened anywhere without its assets.

Usage:
  python3 -m ingest.build_parts_preview <outdir> <index.html> <preview.html>
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_W = 720


def _css(index_html: Path) -> str:
    txt = index_html.read_text(encoding="utf-8", errors="replace")
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", txt, re.S))


def _data_uri(png: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        small = Path(tmp.name)
    subprocess.run(["convert", str(png), "-resize", "%dx>" % MAX_W,
                    str(small)], check=True)
    b64 = base64.b64encode(small.read_bytes()).decode("ascii")
    small.unlink(missing_ok=True)
    return "data:image/png;base64," + b64


def render_question(row, assets, outdir: Path, problems: list) -> str:
    """One question, with its placeholders filled in DOM order by ordinal."""
    html = row["content_html"]
    mine = sorted([a for a in assets if a["question"] == row["question_number"]],
                  key=lambda a: a["ordinal"])
    n_ph = html.count('<div class="fig">')
    if n_ph != len(mine):
        problems.append("Q%s: %d placeholders but %d assets -- the frontend "
                        "would pair them wrongly from here on"
                        % (row["question_number"], n_ph, len(mine)))

    it = iter(mine)

    def _fill(_m):
        a = next(it, None)
        if a is None:
            return ('<div style="border:2px solid #c00;padding:.6em;'
                    'color:#c00;font:12px monospace">placeholder with no '
                    'asset</div>')
        png = outdir / "assets" / a["storage_path"]
        if not png.exists():
            problems.append("Q%s %s: %s missing from assets/"
                            % (row["question_number"], a["slot"],
                               a["storage_path"]))
            return ('<div style="border:2px solid #c00;padding:.6em;'
                    'color:#c00;font:12px monospace">missing %s</div>'
                    % a["storage_path"])
        return ('<figure class="fig"><img src="%s" alt="%s">'
                '<figcaption style="font:11px monospace;color:#999">'
                '%s &middot; ordinal %d</figcaption></figure>'
                % (_data_uri(png), a["slot"], a["storage_path"], a["ordinal"]))

    filled = re.sub(r'<div class="fig">figure</div>', _fill, html)

    head = ('<div class="qn">Q%s%s <span style="float:right;font:12px '
            'monospace;color:#888">[Total: %s] &middot; %d figure(s)</span>'
            '</div>'
            % (row["question_number"],
               "  &middot; Section %s" % row["section"] if row.get("section")
               else "",
               row.get("marks"), len(mine)))
    return '<div class="qwrap">%s<div class="stem">%s</div></div>' % (head,
                                                                      filled)


def main(outdir, index_html, dest):
    outdir = Path(outdir)
    rows = json.loads((outdir / "questions.json").read_text(encoding="utf-8"))
    assets = json.loads((outdir / "asset_plan.json").read_text(encoding="utf-8"))
    anomalies = (outdir / "anomalies.txt").read_text(encoding="utf-8") \
        if (outdir / "anomalies.txt").exists() else ""

    problems: list = []
    body = [render_question(r, assets, outdir, problems) for r in rows]

    out = [
        "<!doctype html><meta charset='utf-8'>"
        "<title>RI 2024 H2 P3 - ingest preview</title>",
        "<style>%s</style>" % _css(Path(index_html)),
        "<style>body{max-width:64em;margin:2em auto;font-family:system-ui;"
        "background:#fff;color:#111;padding:0 1em}"
        ".qwrap{border:1px solid #ddd;border-radius:8px;padding:1em 1.2em;"
        "margin:1.2em 0}.qn{font:700 13px monospace;color:#888;"
        "border-bottom:1px solid #eee;padding-bottom:.5em;margin-bottom:.8em}"
        "figure.fig{margin:1em 0;text-align:center}"
        "figure.fig img{max-width:100%;height:auto;border:1px solid #e6e6e6;"
        "border-radius:6px;background:#fff}"
        "#banner{background:#eaf5ea;border:1px solid #bcd9bc;border-radius:8px;"
        "padding:.8em 1em;margin-bottom:1.5em;font-size:.9rem}"
        "pre{white-space:pre-wrap;font:11px monospace;color:#666;"
        "background:#fafafa;border:1px solid #eee;padding:.8em;"
        "border-radius:6px}</style>",
        '<div id="banner"><b>Ingest preview with real figures.</b> '
        "Markup is exactly what would be stored in <code>content_html</code>. "
        "Figures are filled the way the app fills them &mdash; placeholders in "
        "DOM order, assets sorted by ordinal &mdash; so a mis-pairing would "
        "show up here. Pairing problems found: <b>%d</b>.</div>" % len(problems),
    ]
    if problems:
        out.append("<h3 style='color:#c00'>Pairing problems</h3><ul>%s</ul>"
                   % "".join("<li><code>%s</code></li>" % p for p in problems))
    out += body
    if anomalies.strip():
        out.append("<h3>Pipeline report</h3><pre>%s</pre>"
                   % anomalies.replace("&", "&amp;").replace("<", "&lt;"))

    Path(dest).write_text("\n".join(out), encoding="utf-8")
    print("wrote %s | %d questions, %d assets, %d pairing problems"
          % (dest, len(rows), len(assets), len(problems)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
