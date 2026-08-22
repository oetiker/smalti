# Drawing at 7x14

One file per glyph, named for its codepoint in uppercase hex:
`glyphs/7x14/regular/2192.txt` is the rightwards arrow in the regular face.
`<face>` is one of `regular`, `bold`, `italic`, `bold-italic`.

    # U+2192 '→'  RIGHTWARDS ARROW
    .......
    .......
    .......
    .......
    .......
    ...#...
    ....#..
    .#####.
    ....#..
    ...#...
    .......
    .......
    .......
    .......

Exactly 14 rows of exactly 7 characters.  `#` is ink, `.` is background.  The
builder refuses anything else, so a miscounted row is a build error and not a
silently wrong glyph.  The header line names the codepoint, the character and
its Unicode name; leave it off if you like and `make headers` will fill it in.

**A file here always wins.**  It outranks upstream Tamzen and it outranks every
generator, in every face.  Drawing `glyphs/7x14/bold/00A8.txt` is how you
overrule the bold diaeresis; drawing `glyphs/7x14/italic/0066.txt` is how you
overrule the sheared `f`.  Nothing else is needed -- no markers, no flags, no
code change.  Delete the file and the layer underneath comes back.

`make preview` renders what is there; `make check` validates it.

## Geometry, read off the existing glyphs

| what        | where                                                |
|-------------|------------------------------------------------------|
| cell        | 7 wide, 14 tall                                      |
| body        | columns 1..5 for most glyphs; 0 and 6 are the side bearings |
| wider       | 0 and 6 are allowed -- 20 upstream glyphs use them; see below |
| rows        | 0..10 above the baseline, 11..13 below it            |
| baseline    | row 10 is the last row *on* the baseline (last row of `x`, `A`, `o`) |
| cap height  | rows 3..10 (see `A`)                                 |
| x-height    | rows 5..10 (see `x`)                                 |
| math axis   | row 7 (see `-`, `+`; `=` uses rows 5 and 8)          |
| descender   | rows 11..12 (see `g`); `$` spans rows 2..12          |

### When to use columns 0 and 6

Staying inside columns 1..5 keeps one pixel of air against the neighbouring
cell, which is why most glyphs do it.  Upstream breaks out for three reasons,
and so may you:

* **Must join across cells.**  `_` uses all 7 columns so that underscores form
  one unbroken line.  Same for the VT100 line-drawing set upstream keeps in the
  control-code slots, and for the Powerline separators, which must butt against
  their neighbours with no seam.
* **Needs the width.**  `%` `&` `©` `Ð` `Æ` `æ` are dense; five columns is not
  enough detail.
* **Deliberate asymmetry.**  `«` sits in columns 3..6 and `»` in columns 1..4,
  so each is pushed toward the text it quotes and `«wort»` hugs.

The only cost is that the glyph touches its neighbour.

### The three geometry bands in U+2700..U+27BF

The dingbats block is split by kind, and a new drawing should join the band it
belongs to rather than pick its own:

* **ornaments** -- stars, crosses, florettes, snowflakes, arrows -- use the 7x7
  symbol box on **rows 4..10**, centred on the math axis at row 7.  That is the
  same box as `★` U+2605 and `◆` U+25C6.
* **pictographs and the tall crosses** use **rows 3..11**, starting at cap
  height, because they need the extra height to read at all.
* **bracket ornaments** sit on **rows 2..12**, the span the base font gives
  `( ) [ ] { }`.

## What is not drawn here

The four generated blocks -- braille U+2800, arrows U+2190, the circled digits
U+2776..U+2793 and Latin Extended-A U+0100..U+017F -- have no files in
`glyphs/7x14/`.  They are computed into `build/gen/7x14/` on every build by
`tools/gen-*.py`, which means those generators are still free to be improved.
Draw one of them here only to overrule the computation for that one codepoint.

The bold, italic and bold-italic faces have no drawings at all yet: bold comes
from upstream plus `tools/embolden.py`, and the two slanted faces from
`tools/slant-bdf.py` and `tools/slant-bold.py`.  Every one of those 3006 glyphs
can now be corrected by drawing it.
