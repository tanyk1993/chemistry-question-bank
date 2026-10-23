"""ASRJC 2026 H2 P1 (9476/01): question-only copy of the "QP + suggested
solutions in one docx" file. Same family as ASRJC 2024 P1
(`inline_answers_prep`), with ONE difference: Q27-Q30 label the key
"Answer: X" instead of "Ans: X", so the answer-row pattern is widened.

usage: python3 -m ingest.asrjc26_p1_prep <unz_dir> <unz_q_dir>
(copies <unz_dir> to <unz_q_dir>, then rewrites word/document.xml there)
"""
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

from . import inline_answers_prep as P
from .oxml import NS

P._ANS = re.compile(r"Ans(?:wer)?\s*:")


def _trim_after_answer(src_xml, tmp_xml):
    """Q4 and Q16 carry their worked explanation in rows AFTER the "Ans:" row.
    Drop every row below the (single) answer row first, so it cannot leak
    into the stem as extra_html. Reports each trim."""
    tree = etree.parse(str(src_xml))
    body = tree.getroot().find("w:body", NS)
    for tbl in body.findall("w:tbl", NS):
        rows = tbl.findall("w:tr", NS)
        idx = [i for i, r in enumerate(rows) if P._ANS.search("".join(r.itertext()))]
        if len(idx) == 1 and idx[0] < len(rows) - 1:
            q = "".join(rows[0].findall("w:tc", NS)[0].itertext()).strip()
            for r in rows[idx[0] + 1:]:
                tbl.remove(r)
            print("Q%s: trimmed %d row(s) below the answer row" % (q, len(rows) - idx[0] - 1))
    tree.write(str(tmp_xml), xml_declaration=True, encoding="UTF-8", standalone=True)


def main(src, dst):
    src, dst = Path(src), Path(dst)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    tmp = dst / "word/document_trimmed.xml"
    _trim_after_answer(src / "word/document.xml", tmp)
    for line in P.prepare(tmp, dst / "word/document.xml"):
        print(line)
    tmp.unlink()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
