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
| `^`  | (1,5) width 5 | (1,5) width 5 | **dissents** -- completely unchanged between sizes, centred on column 3 while everything around it widened |

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

### 4. The axis-lock rule -- porting a drawing between sizes

When an 8x16 drawing is ported from an existing 7x14 one, the question is
which row it goes on, and there are only two valid answers.

**Baseline-tracking is the default.** Its ink moves down with the baseline --
row 10 at 7x14, row 11 at 8x16 (`FONT_ASCENT` 11 vs 12, baseline = ascent -
1). This is what every letterform does, because a letter is drawn relative to
the baseline, and the baseline itself moved down one row when the descent
band grew from 3 rows to 4.

**Axis-locked is the exception**, and it is allowed only when both of these
hold:

* the 8x16 drawing is a **direct copy of a specific upstream glyph** (not a
  freehand redraw), and
* that upstream glyph is **confirmed unchanged-row across both upstream
  BDFs** -- measured, not eyeballed.

A glyph with no such anchor is baseline-tracking. No exceptions by feel.

**The measured evidence** (reproduced by parsing `upstream/7x14/Tamzen7x14r.bdf`
and `upstream/8x16/Tamzen8x16r.bdf` with `tools/show-glyphs.py`, not copied
from an earlier report):

| glyph | codepoint | 7x14 row(s) | 8x16 row(s) | verdict |
|---|---|---|---|---|
| `-` | U+002D | row 7 | row 7 | unchanged -> **axis-locked** |
| `*` | U+002A | rows 5-9 | rows 5-9 | unchanged -> **axis-locked** |
| `+` | U+002B | bar row 7 | bar row 7 | bar unchanged -> **axis-locked** (only its stem grew, top and bottom; the bar itself did not move) |
| `<` | U+003C | apex row 7 | apex row 7 | unchanged -> **axis-locked** |
| `>` | U+003E | apex row 7 | apex row 7 | unchanged -> **axis-locked** |
| `=` | U+003D | rows 5, 8 | rows 6, 9 | +1 row, matches the baseline shift -> **baseline-tracking** |
| `A` | U+0041 | rows 3-10 | rows 3-11 | bottom follows the baseline; the top does not move because the CAP LINE is row 3 at both sizes, which is a measured fact and not a coincidence -> **baseline-tracking** |
| `U` | U+0055 | tail touches the baseline, row 10 | tail touches the baseline, row 11 | tail is defined *by* the baseline, moves with it -> **baseline-tracking** |

These are two disjoint populations, not one spectrum. `-`, `*`, `+`, `<` and
`>` are fixed-shape symbols drawn around their own centre -- upstream redrew
each one bigger at 8x16 without sliding it down the cell. `=`, `A` and `U` are
anchored to the letter baseline, and the baseline itself moved, so their ink
moved with it.

**Read the whole glyph, not just the feature you are placing.** `<`, `>` and
`+` are in the axis-locked column above because their *apex* and *bar* stay on
row 7 -- but each glyph as a whole grew, `<` and `>` from rows 4-10 to 3-11 and
`+` from 5-9 to 4-10. Axis-locking is a claim about a FEATURE, never about a
bounding box.

#### The type lines, measured

Every port is decided by these five rows, and four of the five are the same at
both sizes. Re-derived from `upstream/7x14/Tamzen7x14r.bdf` and
`upstream/8x16/Tamzen8x16r.bdf` with `gs.Bdf().cell_bitmaps()`:

| line | measured on | 7x14 | 8x16 |
|---|---|---|---|
| ascender line | top row of `b d f h k l` | row 2 | row 2 |
| cap line | top row of `A B E H` | row 3 | row 3 |
| x-height line | top row of `a c e m n o r s u v w x z` | row 5 | row 5 |
| baseline | bottom row of `A B E H n o x` | row 10 | **row 11** |
| descender bottom | bottom row of `g j p q y` | rows 12-13 | **row 14** |

**Only the baseline and the descender move.** Everything above the baseline is
pinned where it already was, which is why a port that "gains a row at the top"
is almost always wrong: at 7x14 nothing in the font crosses row 1, so moving a
tall glyph up to it puts it above a line the font does not have. (At 7x14
upstream's own `d` and `f` sit one row *below* the ascender line, on row 3; at
8x16 all six ascenders reach row 2.)

The descender is the one place where the two sizes genuinely differ in kind:
at 7x14 upstream draws two depths, `g` and `j` at row 12 and `p q y` at row 13,
while at 8x16 all five bottom out on **row 14**. Five of five.

#### Two bands, two different centres

The cap band is rows 3-11 and the x-height band is rows 5-11, so they centre on
**row 7** and **row 8** respectively. These are different numbers and a mid-band
feature must be told which band it belongs to before it is placed.

**The flip trap.** At 7x14 a cap-band glyph can be reversed top-for-bottom by
`row -> 13 - row`, because the band is 3-10 and `3 + 10 = 13 = H - 1`. At 8x16
the band is 3-11 and `3 + 11 = 14`, while `H - 1 = 15`. A naive vertical flip
therefore lands one row low. Flip within the band, never within the cell.

#### The extra cap row is inserted ABOVE the mid feature

The cap band grows by one row from 7x14 to 8x16 (3-10 becomes 3-11). Upstream
puts that row above the waist, not below it, so a mid-height feature moves down
one row while the number of rows below it stays the same:

| glyph | 7x14 mid feature | 8x16 mid feature | rows above / below, 7x14 -> 8x16 |
|---|---|---|---|
| `H` U+0048 | row 6 | row 7 | 3/4 -> 4/4 |
| `E` U+0045 | row 6 | row 7 | 3/4 -> 4/4 |
| `Ð` U+00D0 | row 6 | row 7 | 3/4 -> 4/4 |
| `£` U+00A3 | row 6 | row 7 | 3/4 -> 4/4 |
| `¥` U+00A5 | bars 6 and 8 | bars 7 and 9 | both bars +1 |

Four of four plus `¥`, no dissent. **This is what settles any attached
mid-height feature**, and it is the reason `Ł`'s stroke moves 6-7 -> 7-8 while
`Ŀ`'s free middle dot stays on 6-7 (see rule 5).

#### Arrows keep their band; everything else moves

Measured over every committed hand port, not inferred. Of the 145 ports whose
7x14 ink band is exactly rows 4-10:

* **37 kept rows 4-10, and 36 of them are arrows.** The one that is not is
  `⏎` U+23CE RETURN SYMBOL, which is drawn *as* U+21B5 DOWNWARDS ARROW WITH
  CORNER LEFTWARDS -- so it keeps the band for the same reason the other 36 do.
* **108 moved, and not one of them is an arrow.** 104 grew downward to rows
  4-11; the remaining 4 (`±`, `≈`, `≤`, `≥`) shifted whole, to rows 5-11.

Zero arrows moved and zero non-arrows kept. **So: if the glyph is an arrow, the
band is axis-locked; if it is not, it is baseline-tracking, and rule 4's default
applies.** This rule was load-bearing long before it was written down, and it is
the reason a new arrow does not gain a row while the operator beside it does.

**The row-7 maths axis.** `-`, `+` (its bar), `<` and `>` (their apexes) all
sit on **row 7** in both sizes -- name this axis explicitly, because any new
glyph that joins a formula (comparison operators, further arrows, anything
meant to line up with `+`/`-`) belongs on it too, not on a baseline-relative
row.

**Why this must be written down, not rediscovered per glyph:** axis-locking
is the exception and it is easy to reach for out of habit ("it looked centred
in the cell, so I kept it where it was") without checking that both
conditions above actually hold. A glyph that is merely *visually* centred but
was hand-drawn fresh, or copied from a symbol upstream did not redraw
unchanged, must default to baseline-tracking -- the anchor has to be measured
evidence from both upstream BDFs, never a guess from how the 7x14 version
looked.

### 5. The two mark families -- where a small mark's columns go

Rule 4 answers which *row* a port lands on. For small marks the *column*
needs its own answer, and the two families disagree, so measure which one a
mark belongs to before placing it.

**Low marks shift right one column and down one row, and keep their ink.**
Measured over upstream's regular face, every mark that hangs off the
baseline: `,` U+002C (cols 2-3 rows 9-13 -> cols 3-4 rows 10-14), `.` U+002E,
`:` U+003A, `;` U+003B. Four of four, all ink-preserving.

**Raised marks keep their column.** The complete top-anchored population of
upstream's regular face -- every glyph present at both sizes whose 7x14 ink
ends at row 6 or above -- is `U+0007`, `"` U+0022, `'` U+0027, `^` U+005E,
`` ` `` U+0060, `~` U+007E, `°` U+00B0: **zero of seven shift right.** This
project's own hand-drawn raised marks agree: `❛` U+275B, `❜` U+275C,
`❝` U+275D, `❞` U+275E, `™` U+2122 -- zero of five. Twelve witnesses, no
dissent. A raised mark spends the extra column on *width* if its shape has
width to spend, and never on translating right; `'` U+0027 is the sharpest
case, a lone one-column tick that stays on column 3 rather than move to
column 4.

Ink follows from shape, not from family: a thin plain tick keeps its ink
(`"` 8->8, `'` 4->4, `^` 5->5), while a mark with an interior keeps growing
(`U+0007` 8->12, `°` 8->12, `~` 7->9).

> **`glyphs/8x16/regular/00B4.txt` is NOT porting evidence -- never cite it.**
> It is the only 8x16 drawing with no 7x14 counterpart. Upstream's regular
> 8x16 BDF lacks the acute accent while its bold has it, so `00B4` was drawn
> (commit 7b2692b) as the *de-bolded* form of upstream's 8x16 **bold** acute.
> Its columns therefore carry a bold-face gutter change, not a porting rule:
> upstream's **bold** shifts all nine of its top-anchored marks +1, because
> bold's 7x14 forms start at column 0 and its 8x16 forms at column 1. Reading
> `00B4`'s +1 as a porting rule placed `‘ ’ ′` one column too far right in the
> first pass at the `20xx` block; the regular-face measurement above overruled
> it 12-0.

**A free mark and an attached feature are different populations, and
connectivity tells them apart without any judgement.** `Ŀ` U+013F and `Ł`
U+0141 are both "a mid-height mark on an `L`" and they behave oppositely:

| glyph | mark | 7x14 rows | 8x16 rows |
|---|---|---|---|
| `Ŀ` U+013F | middle dot, standing free beside the stem | 6-7 | 6-7 |
| `Ł` U+0141 | stroke, crossing the stem | 6-7 | **7-8** |

The mechanical test is the **4-connectivity delta against the bare base**: add
the mark to `L` and count connected components. A free mark leaves 2 components
and keeps its rows; an attached one leaves 1 and moves with the cap band, per
rule 4's "extra row above the mid feature". Run that test before reaching for a
population.

Note also what `Ł` does horizontally: its stroke protrudes LEFT, so at 8x16 the
whole letter is drawn one column right (stem on column 2, not 1) to keep the
protrusion out of column 0. **Where a mark sticks out to the left, shift the
base right** -- that is upstream's own answer, not a preference here.

**The row-7 maths axis covers centred mid-band marks too.** Rule 4's default
("no confirmed upstream anchor -> baseline-tracking") applies to
baseline-relative *forms*; a fixed-shape mark centred on the maths axis stays
on it. Of the 26 committed ports whose 7x14 ink lies wholly in rows 4-9, **16
keep their rows** at 8x16 -- a majority, not a law, so measure the glyph rather
than cite the statistic. (This sentence read "31 of 37" until the drawing was
finished. That figure was taken with `tools/show-glyphs.py`, which has the
BBX-17 bug; every number in this file is now re-derived with
`gs.Bdf().cell_bitmaps()`, which is the only correct reader.) `•` U+2022 is placed on rows 6-8 for that reason,
matching `▴` U+25B4 and `▾` U+25BE (rows 6-8 kept, one column wider, ink
9 -> 12) rather than dropping to rows 7-9 and leaving the axis that `-`, `+`,
`<`, `>` and both triangles sit on.

### 6. Column 0 is the gutter, and no letter touches it

Rule 2 states this for the letter box; here is the census that settles it, so
nobody has to re-argue it per glyph.

**Not one letter lights column 0 at 8x16.** Measured over every letter
(Unicode general category `L*`) in `upstream/8x16/Tamzen8x16r.bdf`: **0 of
114**. The same census at 7x14 finds **2 of 114** -- `Ð` U+00D0 and `æ`
U+00E6 -- and upstream itself VACATES column 0 for both of them at 8x16 by
shifting the glyph right rather than by shrinking it. This project's own
hand-drawn 8x16 letters agree: **0 of 72**.

So where a mark or a stroke would protrude past the left edge of the letter,
the answer upstream reached for is to move the base right one column, not to
put ink in the gutter. `Ł` U+0141 and `Ħ` U+0126 are the worked examples.

**This does NOT apply to the cell-spanning population of rule 3.** Box drawing,
rules and blocks must reach column 0 or they come apart at the cell boundary.
Decide which population the glyph is in first; the plan's old mechanical test
for that ("lights column 0 AND column 7") is a box-drawing heuristic and
MISFIRES ON LETTERFORMS -- it was overturned by this census. Ask whether the
glyph must butt against its neighbour, not where its ink happens to land.

## How the numbers in this file were measured

Every count, row and band above was re-derived from the repository at the point
the 8x16 drawing was finished, with `gs.Bdf(path).cell_bitmaps()` for upstream
bitmaps and `gs.read_glyph()` for committed drawings.

**`tools/show-glyphs.py` has the BBX-17 bug and must never be used to measure
anything** -- it is for eyeballing a glyph, nothing more. Two figures in this
file were wrong for exactly that reason (rule 4's `A` row, and the "31 of 37"
mid-band statistic), and both were repeated as evidence for months before
anyone re-measured them.

**When a rule is ported from 7x14, count the witnesses at 8x16, not at 7x14.**
A construction confirmed at the source size can still be wrong: `U+00A8`
DIAERESIS was almost shipped as the top two rows of `"`, which two independent
7x14 witnesses supported, until a count at the target size found **13**
witnesses for rows 2-3, **11** for rows 0-1 and **zero** for rows 1-2. Zero is
a refutation. It is a cheap check and it is the sharpest one there is.
