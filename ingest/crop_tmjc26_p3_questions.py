"""TMJC 2026 H2 P3: crop the question-side diagram assets from the Word PDF (Claude's snips, at the user's request).

The school's PDF is the plain question paper (no mark scheme overlaid), so no colour stripping is needed.
  Q1  Fig. 1.1 calorimetry apparatus (labels included)
  Q2  (+)-etomidate; enzymatic hydrolysis scheme (b); alkaline hydrolysis mechanism with the EMPTY tetrahedral-intermediate
      box (b)(ii); 1-phenylethanamine -> etomidate scheme (d)
  Q3  H3PO4 / NaOH titration curve (a); Mn2+ d-orbital template (d)(i); blank Cr3+ and Cu+ templates (d)(i)
  Q4  Fig. 4.1 ibuprofen synthesis; (c)(iii) ethene -> F -> ethyl 2-chloroethanoate; stage 1 scheme; stage 2 scheme with the
      EMPTY alkoxide-intermediate box; Fig. 4.2 W -> E
  Q5  2 radicals -> 2,5-dimethylhexane; table of X, Y, Z; (c)(i) acyloxy-radical equations; (d) scheme with the EMPTY boxes
Not cropped (typed instead): Table 1.1, Table 4.1, Table 4.2, all equations. Captions ("Fig. 1.1", "Fig. 4.1", "Fig. 4.2")
are typed in the question, not in the snips. A structure's own name label IS in the snip.
Each region is in PDF points (page number 1-based). Each crop is rendered at 400 dpi, trimmed to its ink and given a 12 px
white border. A crop whose ink touches the region edge is refused (the box cut through something).

usage: python3 crop_tmjc26_p3_questions.py <word.pdf> <outdir>
Writes the PNGs plus sizes.json (printed widths, for gen_image_sizes).
"""
import io, json, os, sys
import pymupdf
from PIL import Image, ImageChops

DPI = 400
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = pymupdf.open(src)

# file stem -> (page number, (x0, y0, x1, y1) in pt, description)
FIGS = {
    "Q1_c":     (4,  (150.0, 100.0, 510.0, 243.0), "Q1(c) Fig. 1.1 calorimetry apparatus"),
    "Q2_intro": (7,  (190.0, 125.0, 380.0, 258.0), "Q2 (+)-etomidate"),
    "Q2_b":     (8,  (95.0, 590.0, 530.0, 692.0),  "Q2(b) enzymatic hydrolysis of etomidate"),
    "Q2_bii":   (9,  (105.0, 283.0, 545.0, 552.0), "Q2(b)(ii) alkaline hydrolysis mechanism (empty box)"),
    "Q2_d":     (10, (150.0, 100.0, 500.0, 224.0), "Q2(d) 1-phenylethanamine to etomidate"),
    "Q3_a":     (12, (115.0, 230.0, 510.0, 470.0), "Q3(a) titration curve of H3PO4 with NaOH"),
    "Q3_di":    (14, (225.0, 308.0, 380.0, 386.0), "Q3(d)(i) Mn2+ d-orbital template"),
    "Q3_di2":   (14, (150.0, 418.0, 500.0, 489.0), "Q3(d)(i) blank Cr3+ and Cu+ templates"),
    "Q4_c":     (17, (88.0, 100.0, 525.0, 633.5),  "Q4(c) Fig. 4.1 ibuprofen synthesis"),
    "Q4_ciii":  (18, (130.0, 205.0, 490.0, 405.0), "Q4(c)(iii) ethene to F to ethyl 2-chloroethanoate"),
    "Q4_ciii2": (19, (95.0, 138.0, 562.0, 238.0),  "Q4(c)(iii) stage 1 of step 2"),
    "Q4_ciii3": (19, (95.0, 297.0, 545.0, 672.0),  "Q4(c)(iii) stage 2 of step 2 (empty alkoxide box)"),
    "Q4_cvii":  (20, (110.0, 320.0, 530.0, 412.0), "Q4(c)(vii) Fig. 4.2 W to E"),
    "Q5_aiii":  (22, (185.0, 262.0, 475.0, 340.0), "Q5(a) coupling to 2,5-dimethylhexane"),
    "Q5_b":     (23, (95.0, 108.0, 530.0, 232.0),  "Q5(b) structures of X, Y and Z"),
    "Q5_ci":    (24, (95.0, 176.0, 506.8, 326.5),  "Q5(c)(i) acyloxy radical equations"),
    "Q5_d":     (25, (88.0, 300.0, 530.0, 556.0),  "Q5(d) three-step scheme (empty boxes)"),
}
sizes = []
for key, (pno, box, desc) in FIGS.items():
    pix = d[pno - 1].get_pixmap(clip=pymupdf.Rect(*box), dpi=DPI)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    assert bb, key
    edges = [bb[0] <= 2, bb[1] <= 2, bb[2] >= im.width - 2, bb[3] >= im.height - 2]
    if any(edges):
        print("!! %s: ink touches region edge (L,T,R,B) %s" % (key, edges))
    im = im.crop(bb)
    o = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
    o.paste(im, (12, 12))
    name = "TMJC_H2_P3_%s_2026.png" % key
    o.save("%s/%s" % (out, name))
    w, h = round(im.width * 72 / DPI), round(im.height * 72 / DPI)
    sizes.append({"path": name, "w": w, "h": h, "desc": desc})
    print(name, o.size, "printed approx %d x %d pt" % (w, h))
with open("%s/sizes.json" % out, "w") as f:
    json.dump(sizes, f, indent=1)
