#!/usr/bin/env python3
"""Driver: RI 2024 H2 P2 Answers docx -> worked_solution HTML + asset plan.

Usage:  python3 extract_answers.py <unzipped-docx-dir> <reference.pdf> <outdir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest.answers import parse
from ingest.render import question_html_grouped, slot_for, asset_filename
from ingest import audit, corrections

SCHOOL, LEVEL, PAPER, YEAR = "RI", "H2", "P2", 2024

# Highest existing question_asset ordinal per question, read from the live DB.
# Answer-side assets continue the sequence (WA2's pattern).
NEXT_ORDINAL = {1: 5, 2: 4, 3: 10, 4: 3}

QUESTION_IDS = {
    1: "8dafc8c0-7446-4027-80d2-c7d4a1149efd",
    2: "599e83cc-ad19-4637-9df4-cb09cf36388f",
    3: "46e0560d-2531-4e28-a73e-16fc8116f909",
    4: "fcc49f25-f5eb-46f8-b09f-eb0847865458",
}


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


def main(unz: str, ref_pdf: str, outdir: str):
    unz_p, out_p = Path(unz), Path(outdir)
    out_p.mkdir(parents=True, exist_ok=True)

    parts, figures, anomalies = parse(unz_p / "word/document.xml",
                                      unz_p / "word/_rels/document.xml.rels")

    # --- plan the assets -------------------------------------------------
    plan = []
    files_by_part: dict[str, list[str]] = {}
    ordinal = dict(NEXT_ORDINAL)
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
        html_by_q[q], log = corrections.apply(html_by_q[q])
        correction_log += ["Q%d: %s" % (q, x) for x in log]

    # --- text gate -------------------------------------------------------
    combined = "\n".join(html_by_q[q] for q in sorted(html_by_q))
    # The running header/footer is page furniture, not answer content, and we
    # deliberately do not extract it. Excluded explicitly rather than by a
    # blanket character allowlist, so the exclusion stays visible.
    IGNORE = [r"(?m)^.*Raffles Institution.*$",
              r"(?m)^.*Suggested Solutions.*$"]
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
    main(*sys.argv[1:4])
