"""Pick the right shape-adapter for a STRUCTURED (P2/P3) question paper docx,
one template at a time -- the same problem `parse_dispatch.py` solves for MCQ
papers ("a bespoke per-school module for every different docx layout does not
scale to 21 colleges x 3 papers each"), solved the same way here.

Two shapes exist so far, each verified against one real paper:

  table  one Word table PER QUESTION, laid out as the 4-column grid whose
         row 0, cell 0 is a bare question number (RI 2024 H2 P3)  -- parts.py
  flow   plain paragraphs, no per-question table at all; a question/part/
         sub-part label is its own leading BOLD run instead of a grid
         position (EJC 2024 H2 P2)                          -- parts_flow.py

Detection reuses parts.py's own QNUM_RE against a body-level table's row 0,
cell 0 -- the identical structural test `parse_dispatch.py` already uses on
the MCQ side. This is a fact about the document's CONTAINER, not its
formatting, so it needs no update for a new school's fonts, mark-badge
convention, or list style.

A flow-shape paper can still contain body-level `w:tbl` elements of its own
(EJC 2024 H2 P2's Hess-cycle enthalpy table, its Table 3.2 structure grid) --
those are CONTENT tables handed to whichever part is open, not a table PER
QUESTION, and neither one's row 0 / cell 0 is a bare question number, so they
do not trip this test (confirmed directly against that document below). Only
a genuinely THIRD container shape (say, numbered lists standing in for both
the question grid AND the part labels, with no bold-run or table landmark at
all) would need a new branch here -- one more adapter, same as the first two.
"""
from __future__ import annotations

from lxml import etree

from .oxml import NS
from . import parts as _table_shape
from . import parts_flow as _flow_shape


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


def parse(document_xml, rels_xml, numbering_xml=None, scope=None):
    """(questions, figures, anomalies, shape) -- dispatches by container shape.

    Same contract as `parts.parse()`/`parts_flow.parse()`, plus the detected
    shape (a driver script prints it, the same way one would want to notice
    "this paper parsed as flow but I expected table"). `scope` (school,
    level, paper, year) is forwarded to the chosen adapter unchanged -- see
    `parts_flow.parse()`'s own docstring for what it is used for.
    """
    shape = detect_shape(document_xml)
    adapter = _table_shape if shape == "table" else _flow_shape
    questions, figures, anomalies = adapter.parse(document_xml, rels_xml,
                                                  numbering_xml, scope=scope)
    return questions, figures, anomalies, shape
