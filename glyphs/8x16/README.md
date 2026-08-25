# Drawing at 8x16

One file per glyph, named for its codepoint in uppercase hex, following the
same convention as [`glyphs/7x14`](../7x14/README.md):
`glyphs/8x16/regular/2192.txt` is the rightwards arrow in the regular face.
`<face>` is one of `regular`, `bold`, `italic`, `bold-italic`.

    # U+2192 '→'  RIGHTWARDS ARROW
    ........
    ........
    ........
    ........
    ........
    ...#....
    ....#...
    .######.
    ....#...
    ...#....
    ........
    ........
    ........
    ........
    ........
    ........

Exactly 16 rows of exactly 8 characters. `#` is ink, `.` is background.

**`#` is both ink and the comment marker.** A tool that scans these files must
decide "is this line a pixel row?" before it decides "is this line a
comment?" -- checking comment-first would swallow any all-ink row (a `#` row
of a filled glyph is indistinguishable from a `#`-prefixed comment line by
content alone). Pixel-row detection has to key off position (line count /
fixed width) or an explicit fence, never off the leading character.

## Vertical metrics (read from upstream, Step 1)

Quoted exactly as they appear in `upstream/8x16/Tamzen8x16r.bdf` and
`Tamzen8x16b.bdf` (both files agree):

```
FONTBOUNDINGBOX 8 16 0 -4
FONT_ASCENT 12
FONT_DESCENT 4
```

12 + 4 = 16, so the baseline sits after row 11: rows 0..11 are the ascent
(cap height and x-height both live in that band, confirmed against `A` and
`x`), rows 12..15 are the descent (confirmed against `g`).

## Horizontal placement (Step 2/3)

At 8 columns wide there is no true centre column, unlike at 7 (which has one:
index 3). This section was rewritten after a first pass asked one question
("which side does the spare column fall on?") of every symmetric glyph and
got a messy answer. The real picture is **three separate rules for three
separate kinds of glyph**, found by measuring the ink window
(leftmost/rightmost lit column, 0-indexed) of every symmetric capital, digit
and symbol in `upstream/8x16/Tamzen8x16r.bdf`, and comparing each against its
own `7x14` counterpart, with `tools/show-glyphs.py`. Use whichever rule
matches the kind of glyph being drawn -- do not average them into one number.

### 1. The stem rule -- a single centred vertical stroke

Glyphs whose ink *is* a single vertical stroke (or a stroke plus symmetric
serifs) consistently centre on **column 4**, not column 3:

| glyph | 7x14 window | 8x16 window | reading |
|---|---|---|---|
| `\|` | (3,3) | (4,4) | single-column stem, shifted right one column |
| `I`  | (1,5) width 5 | (2,6) width 5 | same width, shifted right one column (stem at col 4; serif bar cols 2-6, midpoint 4) |
| `+`  | (1,5) width 5 | (1,7) width 7, stem at col 4 | vertical stroke centres on col 4; its bar widens too (see rule 2) |
| `^`  | (2,4) width 3 | (1,5) width 5 | **dissents** -- widened but held its centre at column 3 |

**Rule: a hand-drawn centred stem goes at column 4** (4 columns of space to
the left, 3 to the right). This is what box-drawing verticals and arrow
shafts must follow, because *consistency across glyphs* is what matters
there -- a stem that wanders between column 3 and column 4 from glyph to
glyph is visibly broken in a way a single glyph's own asymmetry is not.
`^` is upstream's own drawing and is vendored as-is (nothing under
`upstream/` is edited); it is recorded as the one glyph that does not follow
this rule, not silently folded into the majority.

### 2. The letter box -- ordinary letterforms

Column 0 is a **left gutter**: no plain letter, digit or arithmetic symbol
in the sample ever puts ink there. Column 7 is the same gutter *unless* the
letterform needs the extra width, in which case the ink grows into it. Going
from 7x14 to 8x16 **added a column of width, it did not shift the glyph** --
the left edge of the ink stays at column 1 in both sizes:

| group | 7x14 window | 8x16 window | change |
|---|---|---|---|
| `A H O U V 0 8 * # = -` | (1,5) width 5 | (1,6) width 6 | +1 column, added on the right; col 0 stays clear both sizes |
| `M T W X Y` | (1,5) width 5 | (1,7) width 7 | +2 columns, added on the right; col 0 stays clear both sizes |
| `+` (its bar) | cols 1-5 | cols 1-7 | same pattern as the wide letters |
| `~` | n/a (asymmetric by design) | (1,7) | reaches col 7 like the wide letters; weak evidence since `~` isn't a symmetric shape to begin with |

**Rule: draw letter-like glyphs in columns 1..6, and draw them WIDER than the
7x14 original, not padded.** Of the 23 symmetric glyphs measured across both
sizes, 18 changed ink width going from 7x14 to 8x16 (the two groups in the
table above); only 5 kept their 7x14 width unchanged -- 3 of those (`|`, `I`,
`(`) shifted right by one column instead, and 2 (`^`, `)`) neither widened
nor moved. A hand-drawn 8x16 letter should follow the majority: **redraw it
wider to fill the extra column**, the same way upstream's own letters did.
A 7x14 drawing with a blank column stapled on the right will sit visibly
thin next to upstream's neighbours -- that is a padding mistake, not a valid
interpretation of "add one column." Extend into column 7 only if the design
genuinely needs the width; never use column 0 -- upstream never puts an
interior letterform there, so a new drawing that did would be the outlier,
not the norm.

**One upstream inconsistency, recorded rather than smoothed over:** `%`
breaks the "column 0 stays clear" pattern above -- at 7x14 it is flush
*left*, window (0,5), and at 8x16 it is flush *right*, window (1,7). That is
upstream's own glyph, drawn independently at each size, and it is vendored
as-is; it is not evidence against the column-0-gutter rule for *new*
drawings, just proof that upstream itself is not perfectly consistent across
sizes.

### 3. The cell-spanning case -- glyphs that must connect

Box-drawing, rules and blocks are a **different population from letters, not
an edge case of it**, and they use the full cell, columns 0..7, with no
gutter on either side. This isn't a stylistic choice like rules 1 and 2 --
it's a correctness requirement: a horizontal rule that stops at column 6
comes apart at every cell boundary when two cells are drawn side by side.

Measured directly against the 309 existing `glyphs/7x14/regular/*.txt`
drawings (the population this project will grow at 8x16 too): **150 of 309
span the full cell edge-to-edge**, and the rest sit inside the letter box of
rule 2 (131 touch neither edge; a further 28 touch exactly one edge --
`%`-style outliers and asymmetric marks like `«`/`»`). This is a genuine
two-(plus)-population split, not one spectrum: **decide which population a
new glyph belongs to first** -- does it need to butt against its neighbour?
-- and then apply rule 2 or rule 3, never something in between. A glyph that
"almost" spans the cell (say, columns 0..6) is not a compromise; it is a
box-drawing glyph with a seam, which is a bug.

**This rule coexists with rule 1, it does not override it.** A box-drawing
vertical still centres its stroke on column 4 exactly as rule 1 says -- it
just also runs the full 16 rows, edge to edge, rather than stopping short
top or bottom. Its horizontal partner runs the full 8 columns, edge to
edge, the same way. Centring and full-span are answers to two different
questions (where does the stroke sit vs. how far does it reach) and a
box-drawing glyph needs both answers at once.

### Mirror pairs (not evidence for any of the above)

`(`/`)`, `<`/`>`, `[`/`]`, `{`/`}` are each individually asymmetric and
symmetric only as a pair; at 8x16 each pair's two halves straddle the 3.5
axis and cancel exactly (e.g. `(` is (3,5), `)` is (2,4)). That confirms
upstream mirrors them correctly but is not a data point for rules 1 or 2 --
neither half is picking a single centre column on its own. For what it's
worth, `(` shifted right by one column between font sizes (like `|` and `I`)
while `)` did not move at all -- each curve was drawn independently by the
type designer, not as a matched pair-rule, so this is mentioned for
completeness rather than used as evidence.
