"""RVHS 2026 H2 P3: crop the 10 answer-side figures from the Word-exported solutions PDF (400 dpi, trimmed, 12 px border).
Two repairs are made on a scratch copy of page 1 before the Q1 energy cycle is cropped (the school's own file has both faults):
  * the standard-state sign is typed as Wingdings 0x2C, which the PDF draws as a mail-box pictogram: it is redrawn as a circle
    with a bar;
  * the cycle's arrow label reads "-417" while the question gives -4175 (the school's own working line below it uses -4175):
    the missing 5 is added.
Q3(c) is one composite: the J K L header row sits at the foot of page 5 and the structures on page 6.
usage: python3 ingest/crop_rvhs26_p3_answers.py <soln.pdf> <outdir>"""
import io, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
SRC = sys.argv[1]
out = sys.argv[2]
d = pymupdf.open(SRC)

# ---- repair page 1 (the energy cycle): redraw the standard-state sign and add the missing 5 ----
pg = d[0]
fix = []
for b in pg.get_text("dict")["blocks"]:
    for ln in b.get("lines", []):
        for s in ln["spans"]:
            x0, y0, x1, y1 = s["bbox"]
            if 380 < y0 < 470 and 290 < x0 < 420:        # inside the cycle only
                if s["text"] == "\uf02c":
                    fix.append(("std", s))
                elif s["text"] == "417":
                    fix.append(("lab", s))
assert [k for k, _ in fix].count("std") == 1 and [k for k, _ in fix].count("lab") == 1, fix
for k, s in fix:
    if k == "std":
        pg.add_redact_annot(pymupdf.Rect(s["bbox"]), fill=(1, 1, 1))
pg.apply_redactions(images=0, graphics=0)
for k, s in fix:
    x0, y0, x1, y1 = s["bbox"]
    if k == "std":
        cx, cy, r = x0 + 3.6, y0 + 3.9, 2.6
        pg.draw_circle((cx, cy), r, color=(0, 0, 0), width=0.6)
        pg.draw_line((cx - r, cy), (cx + r, cy), color=(0, 0, 0), width=0.6)
    else:

        pg.insert_text((s["bbox"][2], s["origin"][1]), "5", fontname="helv", fontsize=s["size"], color=(0, 0, 0))

def grab(pno, box):
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

BOXES = {   # file slot: (page 1-based, box pt)
    "Q1_ans-bi":   (1, (140, 385, 535, 562)),     # Hess cycle (repaired)
    "Q2_ans-dii":  (4, (140, 222, 545, 484)),     # steps 1-3 of the mechanism, with the Step labels
    "Q2_ans-diii": (4, (140, 540, 300, 612)),     # repeat-unit formula
    "Q3_ans-ai":   (5, (148, 188, 260, 240)),     # dot-and-cross of O3
    "Q4_ans-eii":  (8, (135, 68, 270, 182)),      # trans-azobenzene
    "Q4_ans-f":    (8, (108, 236, 548, 360)),     # SN2 mechanism
    "Q5_ans-bi":   (9, (140, 68, 415, 268)),      # anodising cell
    "Q5_ans-eii":  (10, (140, 116, 420, 306)),    # intermediate 1 and compound B
    "Q5_ans-eiii": (10, (140, 316, 450, 474)),    # four possible structures of C
}
imgs = {k: grab(p, b) for k, (p, b) in BOXES.items()}

# ---- Q3(c): header row (foot of page 5) + structure grid (page 6) ----
a = grab(5, (110, 620.5, 545.5, 651.5))      # J K L header row at the foot of page 5
bpage = grab(6, (110, 61.5, 545.5, 367.5))   # the structure grid on page 6 (borders are not vector lines: fixed box)
# stack: header row (J K L) over the page-6 grid; header row itself is cut above its bottom rule, page 6 supplies it
W = max(a.width, bpage.width)
comp = Image.new("RGB", (W, a.height + bpage.height), (255, 255, 255))
comp.paste(a, (0, 0)); comp.paste(bpage, (0, a.height))
imgs["Q3_ans-c"] = comp

order = ["Q1_ans-bi", "Q2_ans-dii", "Q2_ans-diii", "Q3_ans-ai", "Q3_ans-c", "Q4_ans-eii", "Q4_ans-f", "Q5_ans-bi", "Q5_ans-eii", "Q5_ans-eiii"]
for slot in order:
    im = imgs[slot]
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, slot
    edge = bb[0] <= 2 or bb[1] <= 2 or bb[2] >= im.width - 2 or bb[3] >= im.height - 2
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    qn, s = slot.split("_", 1)
    name = "%s/RVHS_H2_P3_%s_%s_2026.png" % (out, qn, s)
    o.save(name)
    print(name.split("/")[-1], o.size, "printed approx %d x %d pt" % (round(im.width * 72 / DPI), round(im.height * 72 / DPI)),
          "EDGE INK" if edge else "")
