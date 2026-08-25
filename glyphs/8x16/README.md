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
left and 3 to its right. Measured with:

```
python3 tools/show-glyphs.py upstream/8x16/Tamzen8x16r.bdf \
    U+007C U+002B U+005E U+007E U+003C U+003E U+0028 U+0029
```

| glyph | codepoint | shape read                                             | stem / centre column |
|-------|-----------|---------------------------------------------------------|-----------------------|
| `\|`  | U+007C    | single vertical stroke, all 16 rows                      | **4**                 |
| `+`   | U+002B    | vertical stroke col 4, rows 4-9; horizontal bar cols 1-7, row 7 (bar midpoint = 4) | **4** |
| `^`   | U+005E    | chevron: apex col 3 (row 2), shoulders at cols 2/4 (row 3), then 1/5 (row 4) -- symmetric about col 3 | **3** (dissents) |
| `~`   | U+007E    | wave, not vertically symmetric by design -- no single centre column to read | n/a |
| `<` `>` | U+003C / U+003E | mirror pair around the 3.5 axis (tip/outer columns sum to 7 for both) -- confirms upstream mirrors correctly, doesn't pick between 3 and 4 | n/a |
| `(` `)` | U+0028 / U+0029 | mirror pair: `(` main stroke at col 3, `)` main stroke at col 4, again summing to 7 | n/a |

**Rule: bias to column 4.** When a hand-drawn glyph needs a single centred
vertical stem in the 8-wide cell, put it at column 4 (4 columns of space to
the left, 3 to the right). `|` and `+` are the two glyphs that actually test
a single self-symmetric stem, and both of them, independently, land on
column 4 -- `+`'s horizontal bar even cross-checks its own vertical stroke,
by having a midpoint of 4.

**Dissent, recorded rather than smoothed over:** `^` is upstream's one
self-symmetric glyph in this set that does *not* follow that rule -- its own
point of symmetry is column 3, one column left of where `|` and `+` sit. This
is upstream's own drawing and is vendored as-is (see house rule: nothing
under `upstream/` is edited), so it is not "fixed" to column 4. The column-4
rule above governs *new, hand-drawn* glyphs under `glyphs/8x16/`; it does not
retroactively re-centre `^` or any other upstream bitmap that disagrees with
it. `~`, `<`/`>` and `(`/`)` are not evidence either way -- they are either
not self-symmetric by design (`~`) or are mirror pairs whose two halves
straddle the 3.5 axis rather than each picking a single centre column.
