#!/usr/bin/env python3
"""Driver: a structured paper's Answers docx -> worked_solution HTML + asset plan.

Generalised (2026-09-27, for EJC 2024 H2 P3) from the RI 2024 H2 P2 one-off
script into a reusable, CLI-parameterised driver, matching the house pattern
`gen_answers_migration.py` and every other `gen_*_migration.py` already
follow -- see HANDOFF.md's own note on why a script meant to be reused across
papers should never stay hardcoded to the one paper it was first built for.
Two things previously hardcoded module-level (SCHOOL/LEVEL/PAPER/YEAR and the
per-question NEXT_ORDINAL seed) are now threaded through as parameters; a
dead `QUESTION_IDS` dict (never referenced -- superseded by the
paper-identity-JOIN convention `gen_parts_assets_migration.py`/
`gen_answers_migration.py` already use) has been dropped.

This driver NEVER crops figures -- it only plans filenames/slots and renders
text. Cropping is `make_figures.py`, a deliberately separate step (HANDOFF's
"hand-crop" convention: the user snips and names each figure themselves to
conserve their own usage; this script's asset_plan.json is a SUGGESTION of
what to name each file, not a commitment -- the user's own chosen filenames,
once they tell us, are what actually goes into gen_answers_migration.py's
answer_assets.json).

Usage:
  python3 -m ingest.extract_answers <unzipped-docx-dir> <reference.pdf> <outdir> \\
      --school EJC --year 2024 --paper P3 --level H2 \\
      --next-ordinal 1:8,2:4,3:3,4:2,5:5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest.answers import parse
from ingest.render import question_html_grouped, slot_for, asset_filename
from ingest import audit, corrections

# Running header/footer text seen across schools so far -- page furniture,
# not answer content, deliberately excluded from the text gate rather than
# folded into a blanket character allowlist (so the exclusion stays visible).
# Extend this list, don't replace it, when a new school's running footer
# doesn't match either pattern -- keeps every prior paper's exemption honest.
DEFAULT_IGNORE = [
    r"(?m)^.*Raffles Institution.*$",
    r"(?m)^.*Suggested Solutions.*$",
    r"(?m)^.*\xa9\s*EJC.*$",
    r"(?m)^.*Eunoia Junior College.*$",
]


def group_visual_figures(part):
    """Collapse a part's figure REFERENCES into the images we will actually make.

    A chart with shapes drawn over it (RI Q4(a)(ii): chart1.xml plus three red
    half-life construction lines) is ONE picture, not four. Likewise a cluster of
    native shapes forming a single diagram. Getting this wrong would mint extra
    asset rows and shift every later ordinal.
    """
    groups: list[list] = []
    composite: list = []
    for f in part.figures:
        if f.kind in ("shape", "chart"):
            composite.append(f)
        else:
            groups.append([f])
    if composite:
        groups.append(composite)
    return groups


def _parse_next_ordinal(spec: str) -> dict:
    """'1:8,2:4,3:3' -> {1: 8, 2: 4, 3: 3}. Missing questions default to 0."""
    out: dict = {}
    if not spec:
        return out
    for pair in spec.split(","):
        pair = pair.strip()
        if not pair:
            continue
        k, v = pair.split(":")
        out[int(k)] = int(v)
    return out


def main(unz: str, ref_pdf: str, outdir: str, *, school: str = "RI",
        year: int = 2024, paper: str = "P2", level: str = "H2",
        next_ordinal: dict | None = None, extra_ignore: list[str] | None = None):
    SCHOOL, LEVEL, PAPER, YEAR = school, level, paper, year
    NEXT_ORDINAL = next_ordinal or {}
    unz_p, out_p = Path(unz), Path(outdir)
    out_p.mkdir(parents=True, exist_ok=True)

    parts, figures, anomalies = parse(unz_p / "word/document.xml",
                                      unz_p / "word/_rels/document.xml.rels")

    # --- plan the assets (NAMES/SLOTS ONLY -- nothing is cropped here) ----
    plan = []
    files_by_part: dict[str, list[str]] = {}
    ordinal = {q: NEXT_ORDINAL.get(q, 0) for q in {p.qnum for p in parts}}
    for p in parts:
        groups = group_visual_figures(p)
        name_of = {}
        for i, grp in enumerate(groups):
            slot = slot_for(p.label, i)
            fn = asset_filename(SCHOOL, LEVEL, PAPER, p.qnum, slot, YEAR)
            for f in grp:
                name_of[id(f)] = fn
            plan.append({
                "question": p.qnum, "part": p.label, "slot": slot,
                "storage_path": fn, "ordinal": ordinal[p.qnum],
                "source": [f.target or "word-shapes" for f in grp],
                "kind": "composite" if len(grp) > 1 or grp[0].kind in ("shape", "chart")
                        else grp[0].kind,
            })
            ordinal[p.qnum] += 1
        # One entry per figure REFERENCE, in the document order the sentinels
        # appear in, with composite members repeating their shared filename.
        if p.figures:
            files_by_part[p.full_label] = [name_of[id(f)] for f in p.figures]

    # --- render ----------------------------------------------------------
    html_by_q = {}
    for q in sorted({p.qnum for p in parts}):
        qparts = [p for p in parts if p.qnum == q]
        html_by_q[q] = question_html_grouped(qparts, files_by_part)

    # --- recorded source corrections -------------------------------------
    correction_log = []
    for q in list(html_by_q):
        html_by_q[q], log = corrections.apply(html_by_q[q],
                                              (SCHOOL, LEVEL, PAPER, YEAR))
        correction_log += ["Q%d: %s" % (q, x) for x in log]

    # --- text gate -------------------------------------------------------
    combined = "\n".join(html_by_q[q] for q in sorted(html_by_q))
    IGNORE = DEFAULT_IGNORE + (extra_ignore or [])
    problems = audit.charset_gate(combined, ref_pdf, ignore_re=IGNORE)

    (out_p / "worked_solutions.json").write_text(
        json.dumps({str(q): html_by_q[q] for q in html_by_q}, indent=1),
        encoding="utf-8")
    (out_p / "asset_plan.json").write_text(json.dumps(plan, indent=1),
                                           encoding="utf-8")

    print(f"parts={len(parts)}  figure refs={len(figures)}  "
          f"images planned={len(plan)}")
    for a in anomalies:
        print("  ANOMALY:", a)
    for c in correction_log:
        print("  CORRECTION:", c)
    print()
    real, expected = audit.classify(problems)
    if real:
        print("TEXT GATE FAILURES (%d):" % len(real))
        for x in real:
            print("  !", x)
    else:
        print("TEXT GATE: pass -- every character in the reference PDF's body "
              "text is present in our extraction")
    for x in expected:
        print("  (figure-borne, expected)", x.split("|")[0].strip())
    print()
    for q in sorted(html_by_q):
        n = len([p for p in plan if p["question"] == q])
        print(f"  Q{q}: {len(html_by_q[q]):>6} chars of worked_solution, "
              f"{n} answer figure(s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("ref_pdf")
    ap.add_argument("outdir")
    ap.add_argument("--school", default="RI")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--paper", default="P2")
    ap.add_argument("--level", default="H2")
    ap.add_argument("--next-ordinal", default="",
                    help="'1:8,2:4,3:3' -- highest existing question_asset "
                         "ordinal per question (continue the stem-figure "
                         "sequence); questions not listed default to 0. "
                         "Informational only -- the actual migration "
                         "(gen_answers_migration.py) recomputes this live "
                         "from the DB at run time via MAX(ordinal)+offset.")
    a = ap.parse_args()
    main(a.unz, a.ref_pdf, a.outdir, school=a.school, year=a.year,
        paper=a.paper, level=a.level,
        next_ordinal=_parse_next_ordinal(a.next_ordinal))
