#!/usr/bin/env python3
"""Driver: a STRUCTURED question paper (P2/P3) docx + its Word PDF -> rows.

Usage:
  python3 -m ingest.extract_parts <unzipped-docx-dir> <word.pdf> <outdir> \
      [--school RI --level H2 --paper P3 --year 2024]

Writes into <outdir>:
  questions.json   one row per question: content_html, content_text, marks
  asset_plan.json  one row per figure: slot, ordinal, storage_path
  assets/          the cropped PNGs
  anomalies.txt    everything the parser, the cropper and the gate reported

The Word-exported PDF is REQUIRED, not optional -- see ingest/README.md. Here
it is doubly so: it is the only thing that knows how many pictures the paper
actually PRINTS, which is not the number of drawings the docx stores.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from . import audit, corrections, parts_figures as PF, render_parts as R
from .parts import parse
from .question_figures import write_crops


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--school", default="RI")
    ap.add_argument("--level", default="H2")
    ap.add_argument("--paper", default="P3")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--first-page", type=int, default=2,
                    help="first QUESTION page; the cover is not question content")
    ap.add_argument("--last-page", type=int, default=None)
    a = ap.parse_args(argv)

    unz, out = Path(a.unz), Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    scope = (a.school, a.level, a.paper, a.year)

    numbering_path = unz / "word/numbering.xml"
    questions, figures, anomalies = parse(
        unz / "word/document.xml", unz / "word/_rels/document.xml.rels",
        numbering_path if numbering_path.exists() else None)

    # --- recorded source corrections, BEFORE anything reads the figures ----
    # One of them removes placeholders (1(c)'s radical dots), so it has to run
    # before the collapse decides which placeholder is the picture.
    correction_log = []
    for q in questions:
        q.intro_html, log = corrections.apply(q.intro_html, scope)
        correction_log += ["Q%d intro: %s" % (q.qnum, x) for x in log]
        for p in q.parts:
            p.html, log = corrections.apply(p.html, scope)
            correction_log += ["Q%d%s: %s" % (p.qnum, p.label, x) for x in log]

    # --- reconcile the docx's drawing count to the page's picture count ----
    for q in questions:
        q.intro_html = R.reconcile(q.intro_html)
        for p in q.parts:
            p.html = R.reconcile(p.html)

    # --- plan the assets, then crop to those exact filenames ---------------
    doc = pymupdf.open(a.pdf)
    plan_all, owners = [], []
    for q in questions:
        plan = R.asset_plan(q, a.school, a.level, a.paper, a.year)
        for item in plan:
            label = ("%d%s" % (q.qnum, item["part"])) if item["part"] \
                else "Q%d" % q.qnum
            owners.append((label, item["storage_path"]))
        plan_all.extend(plan)

    crops, crop_anoms = PF.crop_all(doc, owners)
    anomalies += crop_anoms
    if len(crops) != len(plan_all):
        anomalies.append("%d assets planned but %d cropped -- every later "
                         "ordinal in the affected question would shift"
                         % (len(plan_all), len(crops)))
    write_crops(doc, crops, out / "assets", dpi=a.dpi)

    # --- rows --------------------------------------------------------------
    rows = []
    for q in questions:
        n_ph = R.content_html(q).count('<div class="fig">')
        n_assets = len([p for p in plan_all if p["question"] == q.qnum])
        if n_ph != n_assets:
            # handoff SS7's costliest defect class: the frontend fills
            # placeholders in DOM order from ordinal-sorted assets, so a
            # mismatch rotates every figure after it.
            anomalies.append("Q%d: %d div.fig placeholders but %d assets"
                             % (q.qnum, n_ph, n_assets))
        rows.append({
            "question_number": q.qnum,
            "type": "structured",
            "section": q.section,
            "marks": q.marks_total,
            "content_html": R.content_html(q),
            "content_text": R.content_text(q),
            "parts": [{"label": p.label, "marks": p.marks} for p in q.parts],
        })

    (out / "questions.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "asset_plan.json").write_text(
        json.dumps(plan_all, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- marks cross-check --------------------------------------------------
    for q in questions:
        got = sum(p.marks or 0 for p in q.parts)
        if q.marks_total is not None and got != q.marks_total:
            anomalies.append("Q%d: parts sum to %d but the paper prints "
                             "[Total: %d]" % (q.qnum, got, q.marks_total))

    # --- text gate: our extraction vs the Word PDF, an independent renderer -
    extracted = " ".join(R.content_text(q) for q in questions)
    last = a.last_page or (len(doc) - 1)
    problems = audit.charset_gate(
        extracted, a.pdf,
        # Page furniture, and the dotted answer rules, which are deliberately
        # not extracted -- excluded explicitly so the exclusion stays visible.
        ignore_re=[r"©\s*Raffles Institution\s*\d{4}",
                   r"9729/0\d/S/\d+", r"…+"],
        first_page=a.first_page, last_page=last)
    real, expected = audit.classify(problems)

    (out / "anomalies.txt").write_text(
        "\n".join(["== parser + cropper =="] + anomalies
                  + ["", "== corrections applied =="] + correction_log
                  + ["", "== text gate (real) =="] + real
                  + ["", "== text gate (documented exemptions) =="] + expected),
        encoding="utf-8")

    print("questions %d | assets %d | crops %d"
          % (len(rows), len(plan_all), len(crops)))
    print("anomalies %d | corrections %d | text-gate problems %d (%d expected)"
          % (len(anomalies), len(correction_log), len(real), len(expected)))
    for x in anomalies:
        print("  ANOMALY:", x)
    for x in real:
        print("  GATE:", x[:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
