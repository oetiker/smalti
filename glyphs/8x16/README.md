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

## Horizontal bias rule (Step 2/3)

At 8 columns wide there is no true centre column: a stem at column 3 leaves
3 columns to its left and 4 to its right; a stem at column 4 leaves 4 to its
left and 3 to its right.

The first pass at this rule (see git history) read a "stem column" off 8
hand-picked glyphs. That sample was too thin -- 2 glyphs agreeing against 1
dissenting is not enough basis for a rule ~292 hand-drawn glyphs inherit. The
measurement below replaces it with the **ink window** (leftmost/rightmost lit
column, 0-indexed) of every left-right-symmetric glyph in a much larger,
representative set: 11 symmetric capitals, 2 symmetric digits, and 18
symbols, all read from `upstream/8x16/Tamzen8x16r.bdf` with
`tools/show-glyphs.py`.

In an 8-wide cell a symmetric glyph of *even* ink-width sits dead centre (the
blank columns split evenly, e.g. width 6 leaves 1 blank on each side) and
carries no bias information. A symmetric glyph of *odd* ink-width forces the
one extra blank column onto one side or the other -- *that* is the bias
signal, and it is far more reliable than picking out a "stem" by eye.

Four of the 18 symbols are mirror **pairs** (`(`/`)`, `<`/`>`, `[`/`]`,
`{`/`}`) -- individually asymmetric, symmetric only as a pair. Each pair's
two halves straddle the 3.5 axis and cancel exactly, which confirms upstream
mirrors them correctly but contributes no net bias evidence; they are
recorded separately below rather than mixed into the vote.

| glyph | ink window (min,max col) | width | verdict |
|---|---|---|---|
| A | (1,6) | 6 | tie |
| H | (1,6) | 6 | tie |
| I | (2,6) | 5 | **right** (extra blank on the left) |
| M | (1,7) | 7 | **right** |
| O | (1,6) | 6 | tie |
| T | (1,7) | 7 | **right** |
| U | (1,6) | 6 | tie |
| V | (1,6) | 6 | tie |
| W | (1,7) | 7 | **right** |
| X | (1,7) | 7 | **right** |
| Y | (1,7) | 7 | **right** |
| 0 | (1,6) | 6 | tie |
| 8 | (1,6) | 6 | tie |
| `*` | (1,6) | 6 | tie |
| `#` | (1,6) | 6 | tie (crossbars run cols 1-6) |
| `%` | (1,7) | 7 | **right** |
| `+` | (1,7) | 7 | **right** (vertical stem col 4; horizontal bar cols 1-7, midpoint 4) |
| `=` | (1,6) | 6 | tie |
| `_` | (0,7) | 8 | tie (fills the full cell by design, joins across cells) |
| `-` | (1,6) | 6 | tie |
| `^` | (1,5) | 5 | **left** (extra blank on the right) -- dissents |
| `~` | (1,7) | 7 | **right**, but `~` is an asymmetric wave by design, not a true symmetry test -- weak evidence |
| `\|` | (4,4) | 1 | **right** (col 4 alone: 4 blank left, 3 blank right) |

Mirror pairs, recorded separately (cancel, no net vote):

| pair | halves (min,max) | 
|---|---|
| `(` / `)` | (3,5) / (2,4) -- straddle 3.5, correctly mirrored |
| `<` / `>` | (1,5) / (2,6) -- straddle 3.5, correctly mirrored |
| `[` / `]` | (3,6) / (1,4) -- straddle 3.5, correctly mirrored |
| `{` / `}` | (0,6) / (1,7) -- straddle 3.5, correctly mirrored |

**Rule: bias right -- column 4.** Of the 23 non-paired symmetric glyphs
above, 12 are ties (even width, no signal) and 11 carry a directional
signal. **10 of those 11 (91%) put the extra blank column on the left**,
i.e. their own ink sits centred on column 4 rather than column 3: `I` `M`
`T` `W` `X` `Y` `%` `+` `~` `|`. Only **`^` dissents** (1 of 11), landing on
column 3 instead. This is a strong majority, not a coin flip, and it
confirms and strengthens the original `|`/`+` reading rather than changing
it: when a hand-drawn glyph needs a single centred vertical stem in the
8-wide cell, put it at **column 4** (4 columns of space to the left, 3 to
the right).

**Dissent, recorded rather than smoothed over:** `^` is upstream's own
drawing and is vendored as-is (see house rule: nothing under `upstream/` is
edited), so it is not "fixed" to column 4. The column-4 rule above governs
*new, hand-drawn* glyphs under `glyphs/8x16/`; it does not retroactively
re-centre `^` or any other upstream bitmap that disagrees with it. The four
mirror pairs are not evidence either way -- each pair's two halves straddle
the 3.5 axis by design rather than either half picking a single centre
column, and `~` is included for completeness but is weak evidence since a
tilde is not vertically symmetric by design in the first place.
