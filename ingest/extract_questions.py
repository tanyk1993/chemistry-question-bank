#!/usr/bin/env python3
"""Driver: a QUESTION paper docx + its Word-exported PDF -> rows + assets.

Usage:
  python3 -m ingest.extract_questions <unzipped-docx-dir> <word.pdf> <outdir> \
      [--school RI --level H2 --paper P1 --year 2024]

Writes into <outdir>:
  questions.json   one row per question: content_html, content_text, options
  asset_plan.json  one row per figure: slot, ordinal, storage_path
  assets/          the cropped PNGs
  anomalies.txt    everything the parser could not account for

The Word-exported PDF is REQUIRED, not optional -- see ingest/README.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from . import audit, corrections, question_figures as QF, render_questions as R
from .questions import parse


FIG_SENTINEL = "\x00FIG\x00"


def _matrix_shape(q):
    """(nrows, ncols) if this question lays its figures out in a grid."""
    rows = [r for r in q.extra_html
            if len(r) > 1 and any(FIG_SENTINEL in c for c in r)]
    if len(rows) < 2:
        return None
    ncols = max(sum(1 for c in r if FIG_SENTINEL in c) for r in rows)
    if ncols < 2:
        return None
    return len(rows), ncols


def _crop_question(doc, q, plan, spans, anomalies) -> list:
    """Crop one question's figures, banding by the paper's own landmarks.

    Cropping the whole question in one pass and merging the nearest clusters
    fails on any grid layout: on RI 2024 H2 P1 Q25 it fused a whole column of
    structures into one image and shattered four others, because two structures
    stacked in a column are closer together than one structure is to its own
    detached methyl group. Each figure is therefore cropped inside the cell the
    paper prints it in -- an option letter's cell, or a matrix cell.
    """
    out = []
    opt_cells = QF.option_cells(doc, spans)
    stem_items = [p for p in plan if p["kind"] == "block"]
    opt_items = [p for p in plan if p["kind"] == "option"]

    # Split the band at the first option letter. Cropping each letter's own
    # cell was tried and is worse: the cells have to be generous enough to
    # catch strokes whose midpoint sits outside them, and once they are, a
    # neighbouring option's structure is pulled in too (Q24 and Q26 each
    # swallowed the option below). Clustering the whole option REGION and
    # merging to the known count keeps the boundaries the page itself implies,
    # and the letters only decide which crop is which.
    first_opt = min((p, r.y0) for p, r in opt_cells.values()) if opt_cells else None
    if first_opt and q.opt_headers:
        # ONLY for a question whose options genuinely have column headings.
        # Those headings print above the first option letter, inside the
        # options table, so the stem crop must stop at the table's top rule or
        # it carries the header shell away with it (Q19, Q27).
        #
        # Gated on opt_headers deliberately: Q26's options are structures with
        # no table at all, and the nearest rule above its first letter belongs
        # to the STEM's reaction scheme -- cutting there would move 57pt of
        # stem into the options region.
        top = QF.options_table_top(doc, first_opt[0], first_opt[1])
        if top is not None:
            first_opt = (first_opt[0], top)
    opt_spans, stem_spans = [], spans
    if first_opt:
        opt_spans, stem_spans = [], []
        for pno, y0, y1 in spans:
            if pno < first_opt[0]:
                stem_spans.append((pno, y0, y1))
            elif pno == first_opt[0]:
                if y0 < first_opt[1]:
                    stem_spans.append((pno, y0, min(y1, first_opt[1] - 4)))
                opt_spans.append((pno, max(y0, first_opt[1] - 8), y1))
            else:
                opt_spans.append((pno, y0, y1))

    if opt_items:
        rects = QF.crop_plan(doc, q.qnum, opt_spans, len(opt_items))
        if len(rects) != len(opt_items):
            anomalies.append("Q%d: %d option figures but %d crops"
                             % (q.qnum, len(opt_items), len(rects)))
        # Reading order and option order agree: the letters are laid out left
        # to right then top to bottom, and so are their structures.
        for item, (pno, rect) in zip(sorted(opt_items, key=lambda i: i["slot"]),
                                     rects):
            out.append((pno, rect, item["storage_path"]))

    shape = _matrix_shape(q)
    y_limit = min((r.y0 for _p, r in opt_cells.values()), default=None)
    cells = []
    if shape and len(stem_items) == shape[0] * shape[1]:
        cells = QF.matrix_cells(doc, spans, shape[0], shape[1], y_limit=y_limit)
        if not cells:
            anomalies.append("Q%d: %dx%d grid expected but its row/column "
                             "landmarks were not all found" % (q.qnum, *shape))
    if cells:
        for item, (pno, rect) in zip(stem_items, cells):
            got = QF.crop_in(doc, pno, rect, 1)
            if not got:
                anomalies.append("Q%d: empty grid cell for %s"
                                 % (q.qnum, item["slot"]))
                continue
            out.append((got[0][0], got[0][1], item["storage_path"]))
    elif stem_items:
        rects = QF.crop_plan(doc, q.qnum, stem_spans, len(stem_items))
        if len(rects) != len(stem_items):
            anomalies.append("Q%d: wanted %d stem crops, clustering produced %d"
                             % (q.qnum, len(stem_items), len(rects)))
        for item, (pno, rect) in zip(stem_items, rects):
            out.append((pno, rect, item["storage_path"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("unz")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--school", default="RI")
    ap.add_argument("--level", default="H2")
    ap.add_argument("--paper", default="P1")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--first-page", type=int, default=2,
                    help="first QUESTION page; the cover is not question content")
    ap.add_argument("--last-page", type=int, default=None)
    ap.add_argument("--skip", default="",
                    help="comma-separated question numbers to leave out of the "
                         "bank entirely, e.g. out-of-syllabus items")
    a = ap.parse_args(argv)

    unz, out = Path(a.unz), Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    questions, figures, anomalies = parse(unz / "word/document.xml",
                                          unz / "word/_rels/document.xml.rels")
    doc = pymupdf.open(a.pdf)
    bands = QF.question_bands(doc, 1, max(q.qnum for q in questions))
    missing = [q.qnum for q in questions if q.qnum not in bands]
    if missing:
        anomalies.append("no PDF band located for Q%s" % missing)

    skip = {int(x) for x in a.skip.split(",") if x.strip()}
    if skip:
        # Skipped questions are dropped AFTER parsing, never before: the parser
        # still walks them, so their figures are still counted and their
        # placeholder/figure gate still runs. Excluding them earlier would hide
        # a defect in a question we happen not to be loading today, and the
        # decision to skip is editorial and reversible.
        anomalies.append("skipped by request (not loaded): %s" % sorted(skip))

    rows, plan_all, crops = [], [], []
    for q in questions:
        if q.qnum in skip:
            continue
        kinds = R.figure_kinds(q)
        spans = bands.get(q.qnum, [])

        # Fractions are READ from the PDF, not cropped -- see question_figures.
        fracs = []
        n_frac = kinds.count("frac")
        if n_frac:
            got = QF.read_fraction(doc, spans)
            fracs = [(g["num"], g["den"]) for g in got]
            if len(fracs) != n_frac:
                anomalies.append(
                    "Q%d: %d Equation objects but %d fractions readable from "
                    "the PDF -- NOT guessed, markup left empty"
                    % (q.qnum, n_frac, len(fracs)))
                fracs = fracs[:n_frac]

        plan = R.asset_plan(q, a.school, a.level, a.paper, a.year)
        for n, why in corrections.dropped_blocks(
                a.school, a.level, a.paper, a.year, q.qnum).items():
            # Never silent: a figure the paper prints and the bank does not is
            # exactly the kind of drift corrections.py exists to make visible.
            anomalies.append("Q%d: block figure #%d DROPPED on purpose -- %s"
                             % (q.qnum, n, why))
            if kinds.count("block") - 1 > 0:
                anomalies.append(
                    "Q%d: a drop left %d other block figure(s); crop_plan "
                    "merges the band to the PLANNED count, so check the crops"
                    % (q.qnum, kinds.count("block") - 1))
        if plan and not spans:
            anomalies.append("Q%d: %d figures but no PDF band" % (q.qnum, len(plan)))
        elif plan:
            crops += _crop_question(doc, q, plan, spans, anomalies)

        rows.append({
            "question_number": q.qnum,
            "type": "mcq",
            "marks": 1,
            "content_html": R.content_html(q, plan, fracs),
            "content_text": R.content_text(q, fracs),
            "options": R.options_json(q),
        })
        plan_all.extend(plan)

    QF.write_crops(doc, crops, out / "assets", dpi=a.dpi)

    (out / "questions.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "asset_plan.json").write_text(
        json.dumps(plan_all, ensure_ascii=False, indent=1), encoding="utf-8")

    # TEXT GATE -- our extraction against the Word PDF, an independent renderer.
    # The gate compares against the whole PDF, so it must see the whole paper
    # -- including skipped questions. Otherwise every glyph unique to a skipped
    # question reads as a dropped character and the gate cries wolf.
    extracted = " ".join(
        R.content_text(q, [(g["num"], g["den"])
                           for g in QF.read_fraction(doc, bands.get(q.qnum, []))]
                       if R.figure_kinds(q).count("frac") else None)
        for q in questions)
    last = a.last_page or (len(doc) - 1)   # trailing blank page
    problems = audit.charset_gate(
        extracted, a.pdf,
        # The running footer repeats on every page and belongs to none of them.
        ignore_re=[r"\u00a9\s*Raffles Institution\s*\d{4}", r"9729/01/S/\d+"],
        first_page=a.first_page, last_page=last)
    real, expected = audit.classify(problems)
    (out / "anomalies.txt").write_text(
        "\n".join(["== parser =="] + anomalies
                  + ["", "== text gate (real) =="] + real
                  + ["", "== text gate (figure-borne, expected) =="] + expected),
        encoding="utf-8")

    print("questions %d | assets %d | crops %d" % (len(rows), len(plan_all), len(crops)))
    print("parser anomalies %d | text-gate problems %d (%d expected)"
          % (len(anomalies), len(real), len(expected)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
