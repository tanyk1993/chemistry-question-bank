#!/usr/bin/env python3
"""Render the extracted worked solutions using the LIVE frontend's own CSS.

Handoff SS9: "Preview with the real CSS. Lift the display-layer rules out of
index.html and render the questions with the actual figure-placement logic, so
the preview is faithful rather than an approximation."

So: the <style> block is taken verbatim from the deployed index.html, and each
worked solution is placed inside a <div class="ws">, which is the element the
frontend builds around `worked_solution` at reveal time. Figures are resolved
the way resolveAssets() does -- by FILENAME from data-asset -- not by position.
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def live_css(index_html: Path) -> str:
    m = re.search(r"<style>(.*?)</style>", index_html.read_text(encoding="utf-8"),
                  re.S)
    if not m:
        raise SystemExit("no <style> block found in index.html")
    return m.group(1)


def inline_assets(html: str, assets: Path) -> str:
    """Mirror resolveAssets(): match img[data-asset] by filename."""
    def sub(m):
        name = m.group(1)
        f = assets / name
        if not f.exists():
            return ('<div class="figbroken">[figure not available: %s]</div>'
                    % name)
        b64 = base64.b64encode(f.read_bytes()).decode()
        return ('<img class="ws-fig" src="data:image/png;base64,%s" alt="">'
                % b64)
    return re.sub(r'<img class="ws-fig" data-asset="([^"]+)"[^>]*>', sub, html)


def main(index_html: str, solutions_json: str, assets_dir: str, out: str):
    css = live_css(Path(index_html))
    sols = json.loads(Path(solutions_json).read_text(encoding="utf-8"))
    assets = Path(assets_dir)

    blocks = []
    for q in sorted(sols, key=int):
        body = inline_assets(sols[q], assets)
        blocks.append(
            '<article class="qcard">'
            '<div class="source"><div>RI 2024</div>'
            '<div class="source-sub">H2 P2 Q%s &mdash; worked solution</div></div>'
            '<div class="ws">%s</div></article>' % (q, body))

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RI 2024 H2 P2 &mdash; worked solutions preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{css}
/* preview chrome only -- not part of the bank */
main.preview {{ max-width: 900px; margin: 0 auto; padding: 1.5rem 1.25rem 4rem;
                display: block; }}
.previewnote {{ background:#fff8e6; border:1px solid #e8d9a8; border-radius:10px;
                padding:.8rem 1rem; margin-bottom:1.2rem; font-size:.9rem; }}
.qcard {{ margin-bottom: 1.2rem; }}
</style></head>
<body>
<main class="preview">
<div class="previewnote"><b>Preview only.</b> Rendered with the display-layer CSS
lifted verbatim from the live <code>index.html</code>, inside the same
<code>div.ws</code> the app builds at reveal time. Figures are resolved by
filename exactly as <code>resolveAssets()</code> does. Nothing here is in the
database yet.</div>
{"".join(blocks)}
</main></body></html>"""
    Path(out).write_text(html, encoding="utf-8")
    print("wrote", out, "(%.1f KB)" % (len(html) / 1024))


if __name__ == "__main__":
    main(*sys.argv[1:5])
