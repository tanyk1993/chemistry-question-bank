"""Prove the acceptance gates can actually fail.

Handoff SS9: "A check that cannot fail is not a check. Prove the check fails --
reintroduce the original bug and confirm the audit names it."

This test exists because the FIRST version of the text gate could not fail. It
decoded the reference PDF using the extractor's own symbol table, so deleting a
mapping removed the character from both sides at once and the diff stayed clean.
The bug and its own detector were the same object. If someone later "simplifies"
audit.py to import symbols.SYMBOL instead of adobe_symbol, this test is what
catches it.

Run:  python3 -m pytest ingest/tests/ -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ingest import adobe_symbol, audit          # noqa: E402
from ingest.symbols import SYMBOL, WINGDINGS    # noqa: E402

DOCX = ROOT / "work/unz"
REF = ROOT / "work/ref.pdf"

pytestmark = pytest.mark.skipif(
    not (DOCX.exists() and REF.exists()),
    reason="needs the RI 2024 P2 answers docx + Word-exported reference PDF")

IGNORE = [r"(?m)^.*Raffles Institution.*$", r"(?m)^.*Suggested Solutions.*$"]


def _extract() -> str:
    from ingest.answers import parse
    from ingest.render import question_html_grouped, slot_for, asset_filename
    parts, _figs, _anom = parse(DOCX / "word/document.xml",
                                DOCX / "word/_rels/document.xml.rels")
    names = {}
    for p in parts:
        if not p.figures:
            continue
        seen, out = {}, []
        for f in p.figures:
            key = "composite" if f.kind in ("shape", "chart") else id(f)
            if key not in seen:
                seen[key] = asset_filename("RI", "H2", "P2", p.qnum,
                                           slot_for(p.label, len(seen)), 2024)
            out.append(seen[key])
        names[p.full_label] = out
    qs = sorted({p.qnum for p in parts})
    return "\n".join(question_html_grouped([p for p in parts if p.qnum == q], names)
                     for q in qs)


def test_tables_agree():
    """Extractor table and audit reference table must not have drifted."""
    assert adobe_symbol.cross_check(SYMBOL, WINGDINGS) == []


def test_gate_passes_on_clean_extraction():
    problems = audit.charset_gate(_extract(), REF, ignore_re=IGNORE)
    # Figure-borne characters are exempt BY NAME in audit.FIGURE_BORNE, each
    # with a reason. Anything else is a defect.
    real, _expected = audit.classify(problems)
    assert real == [], real


def test_gate_catches_a_dropped_radical_dot(monkeypatch):
    """The single highest-consequence glyph in this paper.

    Q4 is entirely about .OH radicals; losing the dot changes the chemistry
    while still rendering as clean, plausible text.
    """
    monkeypatch.setitem(SYMBOL, "F0B7", "")
    problems = audit.charset_gate(_extract(), REF, ignore_re=IGNORE)
    assert any("•" in p or "F0B7" in p or "U+2022" in p for p in problems), \
        "gate did not notice the radical dot going missing: %r" % problems


def test_gate_catches_a_wrong_mapping(monkeypatch):
    """A WRONG mapping is more dangerous than a missing one: it renders."""
    monkeypatch.setitem(SYMBOL, "F0B4", "+")     # multiply -> plus
    problems = audit.charset_gate(_extract(), REF, ignore_re=IGNORE)
    assert any("×" in p or "U+00D7" in p for p in problems), \
        "gate did not notice x being mapped to +: %r" % problems


def test_cross_check_catches_table_drift(monkeypatch):
    monkeypatch.setitem(SYMBOL, "F0B7", "")
    assert adobe_symbol.cross_check(SYMBOL, WINGDINGS) != []
