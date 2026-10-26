#!/usr/bin/env python3
"""Image display-width SQL (HANDOFF 33.4), with the printed widths FILLED IN.

From CJC 2026 H2 P2 on, the size file is generated with each figure's printed
width already set (measured by `measure_fig.py` on the Word PDF) instead of a
NULL template to fill in by hand. One file per side of the paper: the
question-side file after the questions SQL, the answer-side file after the
answers SQL. `display_width_pt` is applied by `sizeFig()` -- no deploy.

Spec JSON: a list of
  {"path": "CJC_H2_P2_Q1_aii_2026.png", "w": 390, "h": 209, "desc": "Fig. 1.1 ..."}
  (`w` = printed width in pt, rounded; `h` is for the comment only)

  python3 -m ingest.gen_image_sizes spec.json dest.sql \\
      --school CJC --year 2026 --paper 2 --level H2 --side question|answer

The join is on storage_path plus the paper's identity (school, year, paper,
level), so a filename shared by two papers can never be touched by mistake.
Safe to re-run: it only sets display_width_pt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(spec, school, year, paper, level, side):
    if not spec:
        raise SystemExit("empty spec")
    paths = [s["path"] for s in spec]
    if len(set(paths)) != len(paths):
        raise SystemExit("duplicate path in spec")
    for s in spec:
        if not (s["w"] > 0):
            raise SystemExit("width must be > 0: %r" % s)
    pw = max(len(s["path"]) for s in spec) + 3          # "'path',"
    dw = max(len(str(round(s["w"]))) for s in spec)
    lines = []
    for i, s in enumerate(spec):
        sep = "," if i < len(spec) - 1 else " "
        val = ("'%s'," % s["path"]).ljust(pw) + (" %s::numeric)%s" % (str(round(s["w"])).rjust(dw), sep))
        size = "%d x %d pt (w x h)" % (round(s["w"]), round(s["h"])) if s.get("h") else "%d pt wide" % round(s["w"])
        lines.append("    (%s  -- printed approx %s  %s" % (val, size, s.get("desc", "")))
    label = "question-side" if side == "question" else "answer-side"
    return "\n".join([
        "-- %s %d H%s P%d : %s image display widths" % (school, year, level[1:], paper, label),
        "-- NULL = leave on the shared caps (the default). A number sets the displayed",
        "-- MAX WIDTH of that image in pt (the height follows, aspect kept). Here each",
        "-- value equals the PRINTED width of the figure in the paper (measured on the",
        "-- Word PDF; \"approx\" because the snips were hand-cropped).",
        "-- Run after the images are uploaded AND after the %s SQL. Safe to re-run" % (
            "questions" if side == "question" else "answers"),
        "-- (it only sets display_width_pt). No deploy needed.",
        "",
        "update question_assets a",
        "   set display_width_pt = v.w",
        "  from (values",
        *lines,
        "  ) as v(path, w),",
        "  questions q, papers p",
        " where a.storage_path = v.path",
        "   and a.question_id  = q.id",
        "   and q.paper_id     = p.id",
        "   and p.school = '%s' and p.year = %d and p.paper_number = %d and p.level = '%s'" % (
            school, year, paper, level),
        "returning q.question_number, a.slot, a.storage_path, a.display_width_pt;",
        "-- Expect %d rows." % len(spec),
        ""])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("dest")
    ap.add_argument("--school", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--paper", type=int, required=True)
    ap.add_argument("--level", default="H2")
    ap.add_argument("--side", choices=["question", "answer"], required=True)
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    Path(a.dest).write_text(render(spec, a.school, a.year, a.paper, a.level, a.side),
                            encoding="utf-8")
    print("wrote", a.dest, "-", len(spec), "row(s)")


if __name__ == "__main__":
    main()
