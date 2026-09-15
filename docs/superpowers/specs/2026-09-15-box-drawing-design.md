# Box Drawing and Block Elements — design

Date: 2026-09-15
Status: design, approved in outline; not yet implemented
Scope: U+2500..U+257F (128 codepoints) and U+2580..U+259F (32), at 7x14 and 8x16

## 1. The gap

Smalti covers neither block at all. Not one codepoint between U+2500 and
U+259F is in the target set: no `─`, no `│`, no `┌`, no `█`, no `░`. Upstream
Tamzen has none of them either, at either size, so there is nothing to inherit.
A terminal drawing a box with Smalti falls back to another font for every
character of the box.

The request that started this was for `╭` and `╮` alone. Two arcs with no `─`
or `│` to attach to would be useless, and this project has refused to
cherry-pick a block every time it has been asked; so the whole of both blocks
is in scope.

The target set grows from 1006 codepoints to **1166**.

## 2. Generated, not drawn

160 codepoints at two sizes would be 320 hand drawings, and there is no
judgement in almost any of them: a `┼` is where the axes cross, not a design.
Hand-drawing them would also be unsafe — a `┼` one row off is a bug that
`make check` cannot see, because `check-outlines` proves the outline matches
the bitmap and has no opinion about whether the bitmap is a cross.

So this follows `gen-braille.py`: one generator, `tools/gen-box.py`, writing
`build/gen/<size>/regular/`. The precedent is exact. Braille is generated
because "the codepoint's low byte IS the dot bitmask"; box drawing is
generated because **the Unicode name IS the drawing instruction**.

### 2.1 The name is the instruction — measured, not assumed

`BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY` says: a light arm pointing down, a
heavy arm pointing right. Every one of the 128 names is of this form, over a
closed vocabulary of 20 words.

A prototype grammar was run over the block before this document was written:

* **128 of 128 names parse.**
* They yield **128 distinct arm specifications — zero collisions.** This is
  the load-bearing check: a parser that returned garbage uniformly would also
  "parse 128", and the collision count is what rules that out.
* Spot checks against the real characters are correct, including the awkward
  ones: `╬` (all four double), `┞` (up heavy, right and down light), `╇`
  (down light, the other three heavy), `╼` (light left, heavy right).

The grammar is: strip a `(DOUBLE|TRIPLE|QUADRUPLE) DASH` modifier and an `ARC`
modifier, split the rest on ` AND `, and read each group as a set of arm words
plus at most one weight word. **A group with no weight of its own inherits the
nearest stated one** — that single rule is what makes `LIGHT DOWN AND RIGHT`
and `DOWN LIGHT AND RIGHT HEAVY` fall out of the same code. `SINGLE` is a
spelling of `LIGHT`, used only opposite `DOUBLE`.

The three diagonals (U+2571..2573) are named differently and are handled apart.

Block elements parse the same way: `<EDGE> <FRACTION> BLOCK`, `FULL BLOCK`,
`<LEVEL> SHADE`, `QUADRANT <corner> AND ...`. Every fraction word maps to
eighths (`ONE QUARTER` is 2/8, `THREE QUARTERS` is 6/8).

**There is no hand-kept table of 160 rows, and that is the point.** The table
is Unicode's. `gen-braille.py`'s own docstring records the bug this avoids: a
hand-kept bit convention that agreed with the truth at width 7 and disagreed
silently at width 8, which would have made all 256 glyphs wrong with no error
anywhere.

## 3. Geometry

Drawn per size, never scaled — `gen-braille.py`'s `GEOMETRY` dict is the
model. One table, and every glyph in both blocks derives from it.

| | 7x14 | 8x16 |
|---|---|---|
| cell | 7 x 14 | 8 x 16 |
| axis column (light vertical) | 3 | 4 |
| axis row (light horizontal) | 7 | 7 |
| heavy vertical | columns 2,3 | columns 3,4 |
| heavy horizontal | rows 6,7 | rows 7,8 |
| double vertical | columns 2 and 4 | columns 3 and 5 |
| double horizontal | rows 6 and 8 | rows 6 and 8 |

Every glyph spans the full cell, columns 0..W-1 and rows 0..H-1. This is
`glyphs/8x16/README.md` rule 3, and it is a correctness requirement, not a
style: a rule that stops one column short comes apart at every cell boundary.

**The axis positions are not new.** Column 3 / column 4 is rule 1 of
`glyphs/8x16/README.md`, which already names box-drawing verticals as the
thing that rule exists for, and it is where upstream puts `|` at each size.
Row 7 is where upstream puts `-` at *both* sizes, and where the bar of `+`
sits at both. So `┼` will line up with `+` and `─` with `-`.

**Heavy takes its second pixel on the side that centres the pair in the
cell; ties go up and left.** Worked through, that single rule gives all four
entries above: at 7x14 the cell centre is row 6.5, so heavy grows *up* from
row 7; at 8x16 it is row 7.5, so heavy grows *down*. Vertically at 8x16 the
centre is column 3.5 so heavy grows *left* from column 4; at 7x14 column 3 is
already the exact centre, the tie, so heavy grows left there too.

**Doubles are clean at both sizes** — one blank line between two strokes,
symmetric about the axis, no rounding anywhere.

## 4. The junction rule

An arm is a rectangle from its cell edge to the junction. The only difficulty
is where each arm stops, and it took three iterations against rendered strips
to get right. All three rules below were validated by rendering and reading
the result, not by reasoning alone.

**A light or heavy arm reaches the FAR edge of the perpendicular band.** Heavy
is one thick line, not two strokes, so this is what makes heavy corners come
out solid. Capping heavy arms individually produced a visibly stepped `┏`.

**Exception: it stops at the NEAR edge when a double runs past it.** Precisely:
when the perpendicular band is double, *and* both perpendicular arms are
present, *and* its own axis does not run through. This keeps the inside of a
double open. It is what makes `╤` hang its stem below the lower line rather
than bridging the gap, while `╪` — whose vertical does run through — passes
straight through the middle.

**A double's two strokes cap individually: outer turns at outer, inner at
inner.** A stroke is "outer" when the perpendicular arm on its side is absent.
This is the whole of the double-corner behaviour: in `╔` the left stroke turns
at the top line and the right stroke at the bottom, so the corner is clean
with no stub. The same rule, with no special case, gives `╠` a continuous
outer line with the inner one broken across the junction, and opens `╬` into
four corner pieces with a hole in the middle — which is what `╬` is.

Getting this orientation backwards is easy and was the prototype's second bug;
it renders `╔` as a bottom-right corner. The fault-injection suite must cover
it.

### 4.1 The other families

* **Arcs** (`╭╮╯╰`): the light corner with the turn pulled back one pixel on
  each arm, so the two runs meet diagonally. At this size a one-pixel chamfer
  is the whole of the curve. Diagonal-only contact is already normal here —
  `❯` is nothing but diagonal steps — and `trace-outline.py`'s corner-touch
  rule handles it.
* **Diagonals** (`╱╲╳`): a straight run, two rows per column at both sizes.
* **Dashes**: interior gap lines clear an otherwise straight line. **Dashes
  merge across the cell boundary** — a cell cannot both start and end with a
  gap and still look evenly dashed — so a repeated `┄` shows one longer run at
  each seam. This is true of bitmap fonts generally at this width; the gap
  positions get chosen by eye per size and the seam is documented, not hidden.

## 5. Block elements, and the two things that cannot be exact

`▀`/`▄` split 14 and 16 rows exactly in half. `█` is the full cell. Quadrants
use the same two splits. `░▒▓` are dither patterns. The eighth-blocks are
fractions of the cell, rounded.

Two compromises are forced at 7x14. Both were put to the user before this
document was written, and both belong in `README.md` alongside the dingbats
compromises.

**The left eighth-blocks must collapse one pair at 7x14.** Seven steps
(`▏▎▍▌▋▊▉`) need seven distinct widths below "full", and a 7-column cell has
six. This is pigeonhole; no rounding rule escapes it. The ladder rounds half
**down**, giving widths 1,2,3,3,4,5,6 — so **`▍` and `▌` are the same glyph**.
Rounding down is what makes 4/8 agree with the half-block split, which puts
the axis column 3 in the *right* half, matching the way the axis row 7 falls
in the lower half. `▌`+`▐` therefore tile the cell exactly with no overlap.

At 8x16 all seven are exact, one column per eighth.

The *vertical* eighths are fine at both sizes: 14 rows rounds half up to
2,4,5,7,9,11,12 — seven distinct steps — and 16 rows gives 2,4,6,8,10,12,14.

**The shades `░▒▓` cannot tile at width 7.** Their dither has an even period
and 7 is odd, so the pattern phase-shifts at every cell boundary and a seam
shows where two same-phase columns meet. At 8x16 it tiles perfectly. The
7-wide patterns get chosen for least-bad appearance and the seam is named in
the README.

## 6. What needs no work

Both of these were checked in the code, not assumed:

* **Bold.** `embolden.py`'s `KEEP` is already `set(range(0x2500, 0x2900))`,
  and its comment already says box drawing "must keep their exact pitch to
  line up with their neighbours". Bold is identical to regular, for free.
* **Italic and bold italic.** `is_slanted()` returns True only for `PUNCT` and
  for letter categories; box drawing and block elements are category `So`, so
  they stay upright. `slant-bdf.py`'s docstring already names "box drawing,
  block elements" as things a shear would break.

So the generator writes the **regular** face only, exactly as
`gen-braille.py` does, and all four faces come out right.

## 7. Files

| file | change |
|---|---|
| `tools/gen-box.py` | new — the generator |
| `tools/test-gen-box.py` | new — fault injection, wired into `check-sources` |
| `Makefile` | add `gen-box.py` to `GENTOOL`; add one line to the `$(GEN)` recipe |
| `glyphs/7x14/README.md`, `glyphs/8x16/README.md` | record the axis, heavy and double positions where a future drawer will look |
| `README.md` | a "Box drawing and block elements" section; the two 7x14 compromises; remove both blocks from "Known gaps" |
| `CHANGES.md` | a `### New` entry under `[Unreleased]` |
| `docs/coverage.md` | regenerated by `make index` (1006 -> 1166) |

Nothing under `build/` is hand-edited. No packaging, site or release file is
touched.

## 8. Checks

`make check` must stay the umbrella it is; this adds to `check-sources` via a
new fault-injection suite, in the shape of `test-check-glyphs.py`'s 12 cases
and `test-check-packages.py`'s 7.

Each case must be confirmed to trip **its own** rule — remove the rule,
confirm only that case flips. The cases that matter, because each is a bug the
prototype actually had or nearly had:

1. Every name in both blocks parses.
2. The 128 box specs are **distinct** — the check that catches a uniformly
   broken parser.
3. `DOUBLE DASH` is read as a dash count, never as a weight.
4. A group with no weight inherits the stated one.
5. Double corner orientation: `╔`'s outer turn is top-left, not bottom-right.
6. Heavy corners are solid, not stepped.
7. `╪` passes through; `╤` does not bridge the double's gap.
8. `▌` and `▐` tile the cell exactly — no overlap, no hole — at both sizes.
9. The 7x14 left-eighth ladder collapses **exactly one** pair; the 8x16 ladder
   collapses none.
10. Every generated glyph spans the full cell where it should, so nothing
    comes apart at a cell boundary.

Beyond the suite, the blocks get read as a rendered strip at both sizes before
the branch is proposed — `make preview` and `make compare`. The project's rule
is to draw a batch, render it, then judge; a generator does not exempt it.

## 9. Risks

1. **The arc chamfer may look wrong at 8x16**, where the cell is larger and a
   one-pixel cut is proportionally smaller. Resolved by looking at the strip;
   if it needs two pixels at 8x16, that is a per-size geometry entry, which is
   what the table is for.
2. **The shade patterns are a judgement call at width 7** and may need a
   second pass by eye.
3. **Dash gap placement** is likewise by eye; the first formula tried produced
   an uneven `┈` with a doubled gap.
4. **The target set grows by 16%**, so `make check` and the site get slower.
   Not expected to matter, but it is the first change of this size since 8x16.
5. **Anything that looks wrong can be corrected by hand with no code change** —
   a file in `glyphs/<size>/regular/` outranks any generator. That is the
   escape hatch, and it needs no design.

## 10. Not in scope

* **U+F0219 and the rest of the Nerd Font private use area.** `README.md`
  excludes those ~3,600 icons deliberately: they are drawn for a double-width
  cell and a Nerd Font fallback already renders them properly. U+E0A0..E0BF
  stays the only PUA range Smalti draws.
* **U+2039 and U+203A** (`‹` `›`). Also missing, also asked for, but they are
  ordinary punctuation with `«`/`»` already present as models — two hand
  drawings per size, no design needed and nothing generated. They are done on
  this branch as their own commit, before the generator work, so that a small
  hand change is not buried in a 160-glyph diff. They are not part of this
  design.
* Symbols for Legacy Computing, and the sextant/octant blocks. Not asked for.
