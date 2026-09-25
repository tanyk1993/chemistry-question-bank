"""Pick the right shape-adapter for a QUESTION paper docx, one template at a
time (see HANDOFF and the project's own working notes on why this exists: a
bespoke per-school module for every different docx layout does not scale to
21 colleges x 3 papers each).

Two shapes exist so far, each verified against one real paper:

  table  one Word table per question (RI 2024 H2 P1)      -- questions.py
  flow   plain paragraphs, no per-question table (EJC 2024 H2 P1)
                                                            -- questions_flow.py

Detection reads the document ONCE, cheaply: a table-shape paper's questions
are always `w:tbl` elements whose row 0, cell 0 is a bare question number
(questions.py's own QNUM_RE). If body-level tables opening on a bare number
exist at all, this is the table shape; otherwise it is the flow shape. This is
a STRUCTURAL fact about the container, not a guess from formatting, so it does
not need updating for each new paper's fonts or layout quirks -- only a
genuinely THIRD container shape (say, numbered lists instead of either) would
need a new branch here, one adapter, same as the first two.
"""
from __future__ import annotations

from lxml import etree

from .oxml import NS
from . import questions as _table_shape
from . import questions_flow as _flow_shape


def detect_shape(document_xml) -> str:
    """'table' or 'flow', from the document's own container structure."""
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        if not rows:
            continue
        c0 = rows[0].findall("w:tc", NS)
        if not c0:
            continue
        if _table_shape.QNUM_RE.match(_table_shape._cell_text(c0[0])):
            return "table"
    return "flow"


def parse(document_xml, rels_xml):
    """(questions, figures, anomalies, shape) -- dispatches by container shape."""
    shape = detect_shape(document_xml)
    adapter = _table_shape if shape == "table" else _flow_shape
    questions, figures, anomalies = adapter.parse(document_xml, rels_xml)
    return questions, figures, anomalies, shape
