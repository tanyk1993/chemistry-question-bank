"""Walk a mark-scheme ("Answers") docx into per-part worked solutions.

SHAPE OF THIS DOCUMENT FAMILY -- verified against RI 2024 H2 P2, do not assume
it matches the QUESTION paper:

  The question paper is the 4-column SEAB grid described in handoff SS7
  (qnum | letter | roman | content). The ANSWERS document is NOT. It is a flat
  two-column grid, [label | answer], spread over several top-level tables, with
  blank spacer rows between content rows. Labels carry the question number
  ("1(a)(i)"), which must be stripped for div.lab and part_label because
  annotateParts() in the frontend matches on the bare "(a)(i)" form.

  Rows whose label cell is empty are CONTINUATIONS of the preceding part -- this
  is how full-width figures and overflow paragraphs are attached. A single-cell
  table is also a continuation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

from .oxml import NS, Wq, paragraph_html

WPD = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
VML = "urn:schemas-microsoft-com:vml"

#: "1(a)(i)", "12(b)", "3(c)(vi)" -- question number then any number of
#: (letter) / (roman) groups. Anchored: a cell that merely *starts* with a digit
#: is not a label.
FIG_SENTINEL = "\x00FIG\x00"

LABEL_RE = re.compile(r"^\s*(\d+)((?:\([a-z]+\))+)\s*$", re.I)


@dataclass
class Figure:
    """One figure reference, in document order."""
    index: int                 # 0-based position in document order
    kind: str                  # 'emf' | 'png' | 'chart' | 'shape'
    target: str | None         # media/imageN.emf, charts/chart1.xml, or None
    part: str | None = None    # owning part label, e.g. '(d)(i)'
    qnum: int | None = None
    anchored: bool = False     # wp:anchor -> XML position != visual position


@dataclass
class Part:
    qnum: int
    label: str                 # '(a)(i)' -- no question number
    html: str = ""
    figures: list[Figure] = field(default_factory=list)

    @property
    def full_label(self) -> str:
        return f"{self.qnum}{self.label}"


def _load_rels(rels_path) -> dict:
    out = {}
    for e in etree.parse(str(rels_path)).getroot():
        out[e.get("Id")] = e.get("Target")
    return out


def _cell_paragraphs(tc):
    """Direct-child paragraphs of a table cell, skipping nested-table ones."""
    return tc.findall(Wq + "p")


def _classify_drawing(node, rels) -> Figure:
    """Decide what a w:drawing / w:object / w:pict actually contains.

    Three outcomes, all present in RI 2024 P2:
      - a picture  -> a:blip -> media file (emf or png)
      - a chart    -> c:chart -> charts/chartN.xml
      - neither    -> native Word shapes, which have NO media file at all and
                      must be cropped from the Word-exported PDF.
    """
    blip = node.find(".//{%s}blip" % A)
    if blip is not None:
        tgt = rels.get(blip.get("{%s}embed" % R), "")
        return Figure(index=-1, kind="png" if tgt.lower().endswith(".png") else "emf",
                      target=tgt)
    chart = node.find(".//{%s}chart" % C)
    if chart is not None:
        return Figure(index=-1, kind="chart",
                      target=rels.get(chart.get("{%s}id" % R), ""))
    imgdata = node.find(".//{%s}imagedata" % VML)
    if imgdata is not None:
        tgt = rels.get(imgdata.get("{%s}id" % R), "")
        return Figure(index=-1, kind="png" if tgt.lower().endswith(".png") else "emf",
                      target=tgt)
    return Figure(index=-1, kind="shape", target=None)


def parse(document_xml, rels_xml):
    """Return (parts, figures) for a mark-scheme docx.

    `parts` is in document order. `figures` is in document order, which is the
    order that matters for asset ordinals (handoff SS7: ordinal MUST follow DOM
    order of the placeholders, because the frontend zips them positionally).
    """
    rels = _load_rels(rels_xml)
    tree = etree.parse(str(document_xml))
    body = tree.getroot().find("w:body", NS)

    parts: list[Part] = []
    figures: list[Figure] = []
    current: Part | None = None
    anomalies: list[str] = []

    for tbl in body.findall("w:tbl", NS):
        for tr in tbl.findall("w:tr", NS):
            cells = tr.findall("w:tc", NS)
            if not cells:
                continue

            label_text = "".join(cells[0].itertext(Wq + "t")).strip()
            m = LABEL_RE.match(label_text)

            if m and len(cells) >= 2:
                qnum = int(m.group(1))
                current = Part(qnum=qnum, label=m.group(2).lower())
                parts.append(current)
                content_cells = cells[1:]
            else:
                # Continuation row (blank label, or a single merged cell).
                if current is None:
                    if label_text:
                        anomalies.append("content before first label: %r"
                                         % label_text[:60])
                    continue
                content_cells = cells if len(cells) == 1 else cells[1:]
                # A continuation whose FIRST cell carries content is a merged
                # full-width row; include it.
                if len(cells) >= 2 and "".join(cells[0].itertext(Wq + "t")).strip():
                    content_cells = cells

            chunks = []
            for tc in content_cells:
                for p in _cell_paragraphs(tc):
                    html = paragraph_html(p)
                    # Attach figures found in this paragraph, in order.
                    n_fig = html.count("\x00FIG\x00")
                    for _ in range(n_fig):
                        pass  # placeholders resolved below, after DOM walk
                    if html.strip():
                        chunks.append(html)
            if chunks:
                current.html = (current.html + "\n" + "\n".join(chunks)).strip() \
                    if current.html else "\n".join(chunks)

    # --- second pass: figures in true document order, mapped to owning part ---
    # Done separately so figure order is the document's, not the cell-walk's.
    order = 0
    cur_lab = None
    cur_q = None
    for el in body.iter():
        ln = etree.QName(el).localname
        if ln == "tr":
            cells = el.findall("w:tc", NS)
            if cells:
                t = "".join(cells[0].itertext(Wq + "t")).strip()
                m = LABEL_RE.match(t)
                if m:
                    cur_q, cur_lab = int(m.group(1)), m.group(2).lower()
        elif ln in ("drawing", "object", "pict"):
            # Skip the mc:Fallback half of an AlternateContent pair: it is a
            # VML restatement of the same figure, and counting it would offset
            # every later ordinal.
            if any(etree.QName(a).localname == "Fallback"
                   for a in el.iterancestors()):
                continue
            fig = _classify_drawing(el, rels)
            fig.index = order
            fig.part = cur_lab
            fig.qnum = cur_q
            fig.anchored = el.find(".//{%s}anchor" % WPD) is not None
            figures.append(fig)
            order += 1

    by_part = {}
    for f in figures:
        by_part.setdefault((f.qnum, f.part), []).append(f)
    for p in parts:
        p.figures = by_part.get((p.qnum, p.label), [])

    _reattach_anchored(parts, anomalies)
    return parts, figures, anomalies


def _has_text(p: Part) -> bool:
    return bool(p.html.replace("\x00FIG\x00", "").strip())


def _reattach_anchored(parts: list[Part], anomalies: list[str]) -> None:
    """Move floating figures onto the part they visually belong to.

    Handoff SS7: "Floating-anchor images: XML position != visual position."
    A wp:anchor drawing is positioned by the layout engine, so it is commonly
    stored in the row BEFORE the part it renders beside. Left uncorrected, the
    figure is attributed to the wrong part -- and because assets are zipped to
    placeholders positionally, one wrong attribution rotates every figure after
    it. That is exactly the defect that cost the most last time.

    The rule is deliberately narrow, and only fires on an unambiguous pairing:
      a part with NO text and NO figures, adjacent to a part that has text of
      its own AND carries a trailing anchored figure.
    Anything less clear-cut is reported rather than guessed at, because a
    plausible wrong guess here is invisible in the rendered output.
    """
    for i, orphan in enumerate(parts):
        if _has_text(orphan) or orphan.figures:
            continue
        moved = False
        # Prefer the preceding part: Word anchors typically float downward.
        for j in (i - 1, i + 1):
            if not (0 <= j < len(parts)):
                continue
            donor = parts[j]
            if donor.qnum != orphan.qnum or not _has_text(donor):
                continue
            floats = [f for f in donor.figures if f.anchored]
            if len(floats) != 1:
                continue
            fig = floats[0]
            donor.figures.remove(fig)
            fig.part = orphan.label
            orphan.figures.append(fig)
            # The placeholder must travel with the figure. Leaving it behind
            # would put an <img> under the wrong label -- the same class of
            # mis-pairing as the ordinal rotation, just arrived at differently.
            if FIG_SENTINEL in donor.html:
                donor.html = donor.html.replace(FIG_SENTINEL, "", 1)
                donor.html = "\n".join(ln for ln in donor.html.split("\n")
                                       if ln.strip())
                orphan.html = (orphan.html + "\n" + FIG_SENTINEL).strip()
            anomalies.append(
                "floating figure #%d moved %s%s -> %s%s (anchored; owner had no "
                "content of its own)" % (fig.index, donor.qnum, donor.label,
                                         orphan.qnum, orphan.label))
            moved = True
            break
        if not moved:
            anomalies.append("part %s has neither text nor figures" % orphan.full_label)
