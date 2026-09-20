#!/usr/bin/env python3
"""Produce every answer-side figure named in asset_plan.json.

Usage: python3 make_figures.py <unzipped-docx-dir> <reference.pdf> <outdir>
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest import figures as F   # noqa: E402

MAX_WIDTH = 1600     # bank assets are viewed at ~34em; beyond this is waste


def main(unz: str, ref_pdf: str, outdir: str):
    unz_p, out_p = Path(unz), Path(outdir)
    assets = out_p / "assets"
    plan = json.loads((out_p / "asset_plan.json").read_text())
    doc = pymupdf.open(ref_pdf)

    labs = F.label_positions(doc)
    order = sorted(labs.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    nxt = {lab: (order[i + 1][1] if i + 1 < len(order)
                 else (len(doc) - 1, doc[-1].rect.y1))
           for i, (lab, _v) in enumerate(order)}

    by_part = defaultdict(list)
    for item in plan:
        by_part[f"{item['question']}{item['part']}"].append(item)

    made = []
    for lab, items in by_part.items():
        for item in [i for i in items if i["kind"] == "png"]:
            F.copy_media_png(unz_p, item["source"][0], assets / item["storage_path"])
            made.append((lab, item["storage_path"], "docx original"))

        crops = [i for i in items if i["kind"] != "png"]
        if not crops:
            continue
        if lab not in labs:
            raise SystemExit("label %s not found in the reference PDF" % lab)
        pno, y = labs[lab]
        npno, ny = nxt[lab]
        page = doc[pno]
        y1 = ny - 6 if npno == pno else page.rect.y1 - 60
        band = pymupdf.Rect(60, y - 6, page.rect.x1 - 40, y1)
        clusters = F.merge_to(F.figure_clusters(page, band), len(crops))
        if len(clusters) != len(crops):
            raise SystemExit("%s: wanted %d figure(s), located %d"
                             % (lab, len(crops), len(clusters)))
        for item, rect in zip(crops, clusters):
            F.render(page, rect, assets / item["storage_path"])
            made.append((lab, item["storage_path"],
                         "cropped %.0fx%.0fpt" % (rect.width, rect.height)))

    # Cap resolution, then palette-encode: these are line art, and full RGB
    # roughly doubles the bytes for no visible gain.
    import subprocess
    for f in sorted(assets.glob("*.png")):
        w = int(subprocess.run(["identify", "-format", "%w", str(f)],
                               capture_output=True, text=True).stdout)
        cmd = ["convert", str(f)]
        if w > MAX_WIDTH:
            cmd += ["-resize", "%dx" % MAX_WIDTH]
        cmd += ["-strip", "-colors", "48", "-define",
                "png:compression-level=9", "PNG8:%s" % f]
        subprocess.run(cmd, check=True)

    total = sum(f.stat().st_size for f in assets.glob("*.png"))
    for lab, name, how in sorted(made):
        print("  %-12s %-34s %s" % (lab, name, how))
    print("\n%d images, %.0f KB total" % (len(made), total / 1024))


if __name__ == "__main__":
    main(*sys.argv[1:4])
