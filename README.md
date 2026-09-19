# `ingest/` — mark-scheme extraction for the H1/H2 Chemistry question bank

Drop this folder into the repo that already holds `index.html`. The point is
persistence: until now the extractor was rebuilt from prose every session, and
the handoff note records four rules being re-implemented wrongly from their own
verbatim description. Code in version control does not have that failure mode.

## Run it

```bash
mkdir -p work && unzip -q PAPER_Answers.docx -d work/unz
python3 extract_answers.py work/unz PAPER_Answers.pdf out   # HTML + asset plan + text gate
python3 make_figures.py    work/unz PAPER_Answers.pdf out   # the images
python3 build_preview.py   index.html out/worked_solutions.json out/assets out/preview.html
python3 gen_migration.py   out out/migration.sql
python3 -m pytest ingest/tests/ -q
```

## The Word-exported PDF is REQUIRED, not optional

Ask every school for the `.docx` **and** a PDF exported from Word. It is thirty
seconds of "Save As" and it is the cheapest defect-prevention step in this
pipeline. Measured on RI 2024 P2, converting the same file through LibreOffice
instead:

| | LibreOffice | Word |
|---|---|---|
| extracted text lines | 164 | 186 |
| radical dot `•` | **dropped everywhere** | present |
| `×`, `→`, `⎯` | **dropped** | present |
| OMML fractions | **dropped entirely** | present |
| chart construction lines | **mis-positioned** (wrong half-lives) | correct |
| chart axis title | `[□OH]/[□OH]0` | `[•OH]/[•OH]₀` |

On a paper whose Q4 is entirely about `•OH` radicals, that is not cosmetic. One
of the dropped fractions is the `3/2` in `3BE(B–H) + 3/2 BE(O=O)`; the paper's
own stated answer of −1019 kJ mol⁻¹ only reproduces with `3/2`.

With a Word PDF in hand, handoff §7's whole EMF chain — `soffice --convert-to
svg` → strip clip-paths → remap Symbol → crop to BoundingBox → cairosvg — is
unnecessary. All of it existed to work around LibreOffice damage.

## Files

| file | role |
|---|---|
| `symbols.py` | the extractor's Symbol/Wingdings table |
| `adobe_symbol.py` | an **independent** copy for the auditor — see below |
| `oxml.py` | Word runs/paragraphs/OMML → inline HTML |
| `answers.py` | walks the 2-column answers grid into parts |
| `render.py` | emits `worked_solution` in the bank's house style |
| `figures.py` | PNGs from the docx, EMF/shapes cropped from the Word PDF |
| `corrections.py` | recorded, reasoned departures from the source |
| `audit.py` | the acceptance gates |

## Why `adobe_symbol.py` exists separately — do not "simplify" this

The first version of the text gate **could not fail**. It decoded the reference
PDF using `symbols.py`, the extractor's own table. Deleting the radical-dot
mapping produced byte-identical output with and without the bug, because both
sides lost the character together.

That is exactly the failure handoff §9 records: *"a text diff of EMF records vs
converted SVG compared a file against its own conversion, so it could not see a
character that had no glyph to render with."* It was rebuilt, in a new file,
whose docstring quoted the warning against it.

`adobe_symbol.py` is the auditor's own encoding. `cross_check()` fails if the two
tables drift apart. `tests/test_gate_can_fail.py` deletes a mapping and asserts
the gate notices. If someone makes `audit.py` import `symbols.SYMBOL`, that test
is what catches it.

## Two gates, deliberately non-overlapping

**Text gate** — every character in the Word PDF must appear in our extraction.
Cheap, and needs no advance knowledge of which glyph to worry about. Catches
dropped or mis-mapped characters. Blind to figure placement.

**Figure gate** — walks `.fig` placeholders in DOM order and zips them to assets
in ordinal order *exactly as `index.html` does*, then checks each image against
the label it will render under. Catches rotations. Blind to dropped glyphs.

Exemptions live in `audit.FIGURE_BORNE`, each with a reason. An undocumented
exemption list is how a gate quietly stops catching things.

## Things this paper taught us

- The **answers** docx is a flat 2-column `[label | answer]` grid. §7's
  4-column SEAB description is the **question** paper and does not transfer.
- Labels carry the question number (`1(a)(i)`). Strip it: `annotateParts()`
  matches the bare `(a)(i)`, and getting this wrong silently kills LO hover.
- `mc:AlternateContent` holds `Choice` (real drawing) + `Fallback` (VML stand-in)
  for ONE figure. Counting both shifts every later ordinal.
- Some figures are **native Word shapes** with no media file at all. Crop them.
- A chart plus shapes drawn over it is one picture, not four.
- `wp:anchor` figures are stored in a different row than they render in. The
  reattachment rule fires only on an unambiguous pairing and logs every move.
- Word emits degenerate paths: RI's chart page has a stroke spanning
  `y = −6852 → 470`. Reject by size **before** clamping to the page.
- `w:jc`: only `center` is centring. `both`/`distribute` is justification.

## House style read off live WA2 rows

`div.worked-solution > div.part > (div.lab + div.body)`, answers in `span.ans`
with `<u>` on mark-bearing keywords, `img.ws-fig[data-asset]`, fractions as
`.frac > .fnum + .fden`, comparisons in `table.cmp` (no `thead`, no `th`).

RI 2024 P2 needs no `ul.marks`, `p.mark-note`, `span.note` or `span.mk` — that
mark scheme has no mark breakdown and no examiner notes. Verified, not assumed.

Two settled conventions, recorded so they are not relitigated:
- **`span.ans` is coalesced.** WA2 splits it at Word run boundaries (twelve spans
  for one electron configuration). Identical render, ~40% smaller, and §7 asks
  for coalescing anyway.
- **Answer slots follow the paper, not WA2.** `ans-cii`, matching RI P2's own
  question-side `cii`/`di`/`di2`, rather than WA2's dashed `ans-a-iii`.

## Migrations

`gen_migration.py` emits a dry run ending in `ROLLBACK`, with a `RAISE
EXCEPTION` pre-flight because `question_assets` has no unique constraint and
`ON CONFLICT` is unavailable — a re-run would silently duplicate every figure.

Validate against a scratch Postgres before going near live:

```bash
initdb -D /tmp/pgdata -A trust -U postgres && pg_ctl -D /tmp/pgdata -o '-k /tmp -p 5433' start
psql -h /tmp -p 5433 -U postgres -d scratch -f fixture.sql -f out/migration.sql
```

For RI P2 this proved the guards fire: a second run was refused and left 14
`ans-` assets rather than 28, and an ordinal clash was caught before any insert.
