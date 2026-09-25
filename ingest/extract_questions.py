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
from .parse_dispatch import parse


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


def _opt_grid_shape(opt_cells: dict):
    """(nrows, ncols) if the printed option letters form a genuine grid.

    EJC 2024 H2 P1's Q13, Q14 and Q28 print their four options as a 2x2
    grid, and whole-region clustering fuses each COLUMN into one image --
    the same column-fusion bug `matrix_cells` exists to fix for a stem grid
    (RI 2024 H2 P1 Q25), for the same reason: `merge_to` only ever merges,
    it can never split a blob the raw clustering already fused. A single
    row or single column is not this bug (`ncols`, from the first row's own
    letter count, comes back 1 for a column and is rejected below), and
    those layouts keep the whole-region approach in `_crop_question`.
    """
    if len(opt_cells) < 4:
        return None
    items = sorted(opt_cells.items(), key=lambda kv: (kv[1][0], kv[1][1].y0))
    rows: list = []
    for _letter, (pno, r) in items:
        if rows and rows[-1][0] == pno and abs(rows[-1][1] - r.y0) < 6:
            rows[-1][2] += 1
        else:
            rows.append([pno, r.y0, 1])
    ncols = max(n for _p, _y, n in rows)
    if len(rows) < 2 or ncols < 2:
        return None
    return len(rows), ncols


#: A crop this short is not a structure or an equation, it is a bare fraction
#: rule that slipped past crop_in's own size filter (the filter tests the
#: PADDED box, not the tight one -- see figure_clusters). EJC 2024 H2 P1
#: Q13's option C/D measured 0.1pt tall this way.
MIN_OPT_H = 4.0


def _crop_options_percell(doc, opt_cells: dict, opt_items: list):
    """{slot: (page, Rect)}, cropping each option's own printed cell.

    Used only for a genuine grid (column-fusion, above) or as RECOVERY when
    whole-region clustering already returned the wrong count -- never as a
    silent default, because it was tried and rejected for RI 2024 H2 P1's
    single-column Q24/Q26 (a cell generous enough to catch a stroke whose
    midpoint sits outside it also pulled in the option below). Confirmed
    safe here on EJC 2024 H2 P1 Q23 (single column, 3 structures the
    whole-region pass fuses into 1): its three cells came back as three
    distinct, non-overlapping crops.

    `crop_in`'s vector-only clustering is tried first; a cell whose crop
    comes back missing or a sliver (Q13's Ka expressions, typeset almost
    entirely in glyphs rather than paths) falls back to `crop_in_text`.
    Returns None -- never a partial dict -- if any cell fails both, so the
    caller can fall back to the whole-region approach instead of emitting a
    wrong-shaped or degenerate crop.
    """
    out = {}
    for item in opt_items:
        letter = item["slot"]
        cell = opt_cells.get(letter)
        if cell is None:
            return None
        pno, rect = cell
        got = QF.crop_in(doc, pno, rect, 1)
        if len(got) == 1 and got[0][1].height >= MIN_OPT_H:
            out[letter] = got[0]
            continue
        textrect = QF.crop_in_text(doc, pno, rect, letter=letter)
        if textrect is None or textrect.height < MIN_OPT_H:
            return None
        out[letter] = (pno, textrect)
    return out


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
        grid = _opt_grid_shape(opt_cells)
        rects = QF.crop_plan(doc, q.qnum, opt_spans, len(opt_items))
        # A genuine grid is ALWAYS wrong under whole-region clustering (each
        # column fuses into one blob), so it never gets a chance to look
        # right by count alone -- go straight to per-cell. A single row or
        # column is only rebanded when the whole-region count already came
        # back wrong, since that layout's default is otherwise correct
        # (RI 2024 H2 P1 Q24/Q26) and per-cell was rejected there before.
        percell = None
        if grid or len(rects) != len(opt_items):
            percell = _crop_options_percell(doc, opt_cells, opt_items)
        if percell:
            for item in opt_items:
                pno, rect = percell[item["slot"]]
                out.append((pno, rect, item["storage_path"]))
        else:
            if len(rects) != len(opt_items):
                anomalies.append("Q%d: %d option figures but %d crops"
                                 % (q.qnum, len(opt_items), len(rects)))
            # Reading order and option order agree: the letters are laid out
            # left to right then top to bottom, and so are their structures.
            for item, (pno, rect) in zip(
                    sorted(opt_items, key=lambda i: i["slot"]), rects):
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

    questions, figures, anomalies, shape = parse(
        unz / "word/document.xml", unz / "word/_rels/document.xml.rels")
    print("detected document shape: %s" % shape)
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
        frac_letters = corrections.frac_option_letters(
            a.school, a.level, a.paper, a.year, q.qnum)
        eqtext_map = corrections.eqtext_options(
            a.school, a.level, a.paper, a.year, q.qnum)
        kinds = R.figure_kinds(q, frac_letters, eqtext_map)
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
            "content_html": R.content_html(q, plan, fracs, frac_letters, eqtext_map),
            "content_text": R.content_text(q, fracs, frac_letters, eqtext_map),
            "options": R.options_json(q, fracs, frac_letters, eqtext_map),
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
    def _gate_text(q):
        fl = corrections.frac_option_letters(a.school, a.level, a.paper, a.year, q.qnum)
        eq = corrections.eqtext_options(a.school, a.level, a.paper, a.year, q.qnum)
        kinds = R.figure_kinds(q, fl, eq)
        fracs = ([(g["num"], g["den"])
                 for g in QF.read_fraction(doc, bands.get(q.qnum, []))]
                if kinds.count("frac") else None)
        return R.content_text(q, fracs, fl, eq)
    extracted = " ".join(_gate_text(q) for q in questions)
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
