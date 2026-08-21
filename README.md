# tobit — Tamzen 7x14 with extra glyphs

Upstream Tamzen 7x14 has **189 glyphs and nothing above U+00FF**: no `§`, no
`¶`, no dashes, no arrows, no triangles, no `…`.  This repo adds glyphs to it
and rebuilds the `.otb` that wezterm loads.  Each face now carries **1002
glyphs**.

## License

Tamsyn (Scott Fial, 2010) and Tamzen (Suraj N. Kurapati, 2011) both say:

> "…font is free.  You are hereby granted permission to use, copy, modify,
> and distribute it as you see fit."

Modification is explicitly permitted.  See `LICENSE.tamzen`.  Keep the
`(c) 2015 Scott Fial` notice that is already in the font's name table.

## Build

Needs `fonttosfnt` (Debian/Ubuntu: `xfonts-utils`).

    make            # build build/Tamzen7x14r.otb
    make preview    # show the added glyphs as ASCII art
    make install    # copy it over ~/.local/share/fonts/tamzen-patched/
    make watch      # rebuild, install and reload on every save
    make restore    # put the untouched baseline back

After `make install`, reload wezterm with `Ctrl+Shift+R`.

## `make watch` — the editing loop

Run it in a spare pane, then just edit `glyphs/extra.txt` and save:

    make watch

Every save rebuilds, installs, and `touch`es `~/.config/wezterm/wezterm.lua`,
which triggers wezterm's own automatic config reload — the same thing
`Ctrl+Shift+R` does.  New pixels appear in about a second, in every wezterm
window.

If a glyph is malformed the build stops, prints the offending line, and
**leaves the installed font untouched**, so a half-typed glyph never blanks
your terminal.  The watcher keeps running; fix the file and save again.

It watches the `glyphs/` and `tools/` directories rather than individual
files, because editors replace a file instead of writing into it and a file
watch would end up pointing at the old inode.

## How it works

    glyphs/extra.txt  ──merge-glyphs.py──►  build/…bdf
                      ──fonttosfnt───────►  build/…otb
                      ──repair-tamzen.py─►  usable in wezterm

`upstream/` holds pristine upstream BDF sources and is never edited.
`baseline/` holds the exact `.otb` files that were live before this repo
existed, so `make restore` is always a working escape hatch.

`repair-tamzen.py` is required on every build, not just on upstream files:
`fonttosfnt` itself emits the four broken metric fields (wrong EBLC
`indexTablesSize`, wrong `hmtx` advance, wrong `OS/2` `xAvgCharWidth`, phantom
`hhea` leading).  Without the repair the font renders **blank** in wezterm,
because it is bitmap-only and has no outline to fall back to.

## Drawing a glyph

Add a block to `glyphs/extra.txt`:

    CHAR U+2192 RIGHTWARDS ARROW
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

Exactly 14 rows of exactly 7 characters.  `#` is ink, `.` is background.
The builder refuses anything else, so a miscounted row is a build error,
not a silently wrong glyph.

Geometry, read off the existing glyphs (`tools/show-glyphs.py` shows any of
them):

| what        | where                                                |
|-------------|------------------------------------------------------|
| cell        | 7 wide, 14 tall                                      |
| body        | columns 1..5 for most glyphs; 0 and 6 are the side bearings |
| wider       | 0 and 6 are allowed — 20 upstream glyphs use them; see below |
| baseline    | row 10 is the last row *on* the baseline             |
| cap height  | rows 3..10 (see `A`)                                 |
| x-height    | rows 5..10 (see `x`)                                 |
| math axis   | row 7 (see `-`, `+`; `=` uses rows 5 and 8)          |
| descender   | rows 11..12 (see `g`); `$` spans rows 2..12          |

### When to use columns 0 and 6

Staying inside columns 1..5 keeps one pixel of air against the neighbouring
cell, which is why most glyphs do it.  Upstream breaks out for three reasons,
and so may you:

* **Must join across cells.**  `_` uses all 7 columns so that underscores form
  one unbroken line.  Same for the VT100 line-drawing set that upstream keeps
  in the control-code slots (U+0002, U+000B..U+0018) -- though wezterm draws
  those itself via `custom_block_glyphs`, so they need no work here.
* **Needs the width.**  `%` `&` `©` `Ð` `Æ` `æ` are dense; five columns is not
  enough detail.
* **Deliberate asymmetry.**  `«` sits in columns 3..6 and `»` in columns 1..4,
  so each is pushed toward the text it quotes and `«wort»` hugs.

  tools/show-glyphs.py upstream/Tamzen7x14r.bdf U+005F U+00AB U+0026

## The character set

247 glyphs.  The tables below cover the symbol set; Latin
Extended-A (125) and Greek (49) are listed in `glyphs/latin-ext-a.txt`
and `glyphs/greek.txt`.

**Latin-1 characters upstream never drew** (11)

| | | |
|---|---|---|
| `§` | U+00A7 | Section Sign |
| `¨` | U+00A8 | Diaeresis |
| `¬` | U+00AC | Not Sign |
| `¯` | U+00AF | Macron |
| `±` | U+00B1 | Plus-Minus Sign |
| `²` | U+00B2 | Superscript Two |
| `³` | U+00B3 | Superscript Three |
| `µ` | U+00B5 | Micro Sign |
| `¶` | U+00B6 | Pilcrow Sign |
| `·` | U+00B7 | Middle Dot |
| `¹` | U+00B9 | Superscript One |

**Typography** (15)

| | | |
|---|---|---|
| `–` | U+2013 | En Dash |
| `—` | U+2014 | Em Dash |
| `‘` | U+2018 | Left Single Quotation Mark |
| `’` | U+2019 | Right Single Quotation Mark |
| `‚` | U+201A | Single Low-9 Quotation Mark |
| `“` | U+201C | Left Double Quotation Mark |
| `”` | U+201D | Right Double Quotation Mark |
| `„` | U+201E | Double Low-9 Quotation Mark |
| `†` | U+2020 | Dagger |
| `‡` | U+2021 | Double Dagger |
| `•` | U+2022 | Bullet |
| `…` | U+2026 | Horizontal Ellipsis |
| `′` | U+2032 | Prime |
| `″` | U+2033 | Double Prime |
| `€` | U+20AC | Euro Sign |

**Arrows** (10)

| | | |
|---|---|---|
| `←` | U+2190 | Leftwards Arrow |
| `↑` | U+2191 | Upwards Arrow |
| `→` | U+2192 | Rightwards Arrow |
| `↓` | U+2193 | Downwards Arrow |
| `↔` | U+2194 | Left Right Arrow |
| `↕` | U+2195 | Up Down Arrow |
| `↵` | U+21B5 | Downwards Arrow With Corner Leftwards |
| `⇐` | U+21D0 | Leftwards Double Arrow |
| `⇒` | U+21D2 | Rightwards Double Arrow |
| `⇔` | U+21D4 | Left Right Double Arrow |

**Mathematics** (17)

| | | |
|---|---|---|
| `Δ` | U+0394 | Greek Capital Letter Delta |
| `∆` | U+2206 | Increment |
| `∈` | U+2208 | Element Of |
| `∏` | U+220F | N-Ary Product |
| `∑` | U+2211 | N-Ary Summation |
| `−` | U+2212 | Minus Sign |
| `√` | U+221A | Square Root |
| `∞` | U+221E | Infinity |
| `∧` | U+2227 | Logical And |
| `∨` | U+2228 | Logical Or |
| `∩` | U+2229 | Intersection |
| `∪` | U+222A | Union |
| `≈` | U+2248 | Almost Equal To |
| `≠` | U+2260 | Not Equal To |
| `≡` | U+2261 | Identical To |
| `≤` | U+2264 | Less-Than Or Equal To |
| `≥` | U+2265 | Greater-Than Or Equal To |

**Shapes and marks** (14)

| | | |
|---|---|---|
| `■` | U+25A0 | Black Square |
| `□` | U+25A1 | White Square |
| `▲` | U+25B2 | Black Up-Pointing Triangle |
| `▴` | U+25B4 | Black Up-Pointing Small Triangle |
| `▶` | U+25B6 | Black Right-Pointing Triangle |
| `▼` | U+25BC | Black Down-Pointing Triangle |
| `▾` | U+25BE | Black Down-Pointing Small Triangle |
| `◀` | U+25C0 | Black Left-Pointing Triangle |
| `◆` | U+25C6 | Black Diamond |
| `○` | U+25CB | White Circle |
| `●` | U+25CF | Black Circle |
| `★` | U+2605 | Black Star |
| `✓` | U+2713 | Check Mark |
| `✗` | U+2717 | Ballot X |

## Nothing is refused any more

Every glyph that was once too hard is drawn.  Each needed the same move: stop
trying to draw it correctly and draw it *legibly*, because a cramped glyph in
the right weight beats a correct one borrowed from another font.

| | what it took |
|---|---|
| `®` | the ring spans all 7 columns.  At 6, like `©`, the interior is 2 columns and only a `C` fits; at 7 it is 3, which is what an `R` needs. |
| `‰` | the three rings become solid 2x2 blobs.  A hollow ring needs 3 columns and three of them plus a solidus need 11. |
| `™` | two 3-column letterforms with one column of air between them. |
| `¼` `½` `¾` | 3x4 numerals, numerator top-left, denominator bottom-right, solidus on Tamzen's own `/` slope. |
| `☆` | the outline of `★`, with the waist opened up. |
| `Ĳ` `ĳ` `ŉ` | both halves reduced to plain stems; there is no room for serifs. |
| `※` | dense by nature, and left identical in bold for the same reason as `®`. |

## The three dash lengths

`-` is 5 pixels (columns 1..5, Tamzen's own), `–` is 6 (columns 1..6), `—` is
all 7.  Only `—` joins into an unbroken rule when repeated.

## Latin Extended-A and Greek

`glyphs/latin-ext-a.txt` is **generated once** by `tools/gen-latin-ext-a.py`
and then owned by hand -- re-running the generator overwrites it.

It works by subtraction, not invention.  Tamzen already draws grave, acute,
circumflex, tilde, diaeresis, ring and cedilla on `a`, `A`, `c` and `C`;
subtracting the plain letter from the accented one recovers each mark exactly
as Tamzen drew it.  Only macron, breve, dot above, double acute, caron and
ogonek had to be added by hand.

Two traps worth recording:

* **Do not subtract from capitals.**  Tamzen *squashes* the capital under its
  own accents -- `Á` is a shorter `A` -- so `Á AND NOT A` leaves fragments of
  the squashed letter behind.  The generator always takes the lowercase mark
  and raises it over a full-height capital instead.
* **A mark above `i` or `j` replaces the dot** (`ī`, not an i with both).  That
  is the typographic rule and also the only way it fits.

Where a letter is too tall for a mark above it -- `ĺ` `ľ` `ť` `ģ` -- the
generator falls back to a raised comma beside the letter, which is what real
typography does anyway.  It prints every such case when it runs.

Greek in `glyphs/greek.txt` is hand-drawn, except the capitals whose letterform
is identical to Latin (`Α` `Β` `Ε` `Ζ` `Η` `Ι` `Κ` `Μ` `Ν` `Ο` `Ρ` `Τ` `Υ` `Χ`)
which are copies of Tamzen's own bitmaps, so the two cannot drift apart.
`μ` and `µ` share one shape.

## Bold

Both faces carry all 718 glyphs.  `glyphs/` is hand-written and is the source
of truth; `glyphs-bold/` is derived from it by `make sources`, three different
ways depending on what gives the better result:

| group | how the bold version is made |
|---|---|
| Latin Extended-A | composed again, against the **bold** base font -- Tamzen's bold letters and bold accents already exist, so nothing is invented |
| Greek capitals sharing a Latin form | copied straight from Tamzen's bold `A`, `B`, `E` ... so bold Alpha stays exactly bold A |
| shapes, braille, dingbats, and six maximum-density glyphs | **left identical**.  Widening a filled circle does not make it bold, it makes it lopsided; braille and box drawing must keep their pitch to line up with neighbours; and `®` `™` `‰` `¼` `½` `¾` already fill 6 or 7 columns with 1-pixel detail, so any widening merges the interior |
| everything else | each stroke widened by one pixel, the way Tamzen does it |

**The widening rule is not the obvious one.**  Plain `row | (row << 1)`
reproduces 108 of the 189 upstream bold glyphs -- but it merges every
1-pixel gap, which turned `¶`, `®` and `π` into solid blobs.  Widening whole
*runs*, and falling back to widening rightward when the left is blocked,
reproduces 93 of 189 and never fills a counter.  Fewer exact matches, better
glyphs; `tools/embolden.py` records the trade-off.

After editing anything in `glyphs/`, run `make sources` before `make install`.
`make watch` already does both.

## The arrows block

`glyphs/arrows.txt` is the **whole** U+2190..U+21FF block, generated by
`tools/gen-arrows.py`.  112 arrows drawn one at a time would drift apart, so a
handful of parts -- shaft, head, tail, overlay -- are drawn once facing right
or up and mirrored for the other three directions.

Mirroring is done **inside the glyph's own ink window**, so an arrow keeps its
vertical position instead of sliding down the cell.

Two mistakes worth not repeating: a gap cannot be made by overlaying more ink
(the first `↻` came out as a solid arc, so the ring is now drawn already
broken), and a mirrored half must be re-centred on its own shaft, not on the
cell (`⇅`'s left head sat one column off).

Honest limit: at 7x14 some distinctions Unicode draws are finer than the cell.
A wave arrow and a squiggle arrow differ by one pixel of amplitude, and a
triple arrow is three lines because four would touch.  Every arrow is drawn
distinct where distinct is possible, and directionally correct always.

## The fork, and the private use area

The git-branch mark in a shell prompt is written two different ways, so both
are drawn: `⑂` U+2442 OCR FORK (real Unicode, which is why prompts favour it)
and `` Powerline BRANCH (private use area).  The rest of the small OCR
block came along with the first, and the core Powerline set with the second.

`glyphs/powerline.txt` is the **only** private-use range drawn here, and
deliberately so.  Nerd Font puts about 3,600 more icons in the PUA; those are
designed for a double-width cell and the CommitMono Nerd Font fallback already
renders them properly, so drawing them at 7x14 would make them worse.  The
separators fill the cell edge to edge on purpose — they must butt against
their neighbours with no seam — which also means they must never be
emboldened, and `tools/embolden.py` keeps U+E0B0..E0BF as-is.

## Terminal UI symbols

`glyphs/ui.txt` covers what Claude Code and similar TUIs draw: the `❯` prompt
chevron, the spinner's dot-into-a-star progression (`✢ ∗ ✳ ✻ ✽ ✶ ✷ ✸ ✹ ✺`),
the part-filled circles `◐ ◑ ◒ ◓ ◔ ◕`, the `⏺` tool marker and the `⎿`
result connector.

`glyphs/braille.txt` is the **whole** U+2800 block, all 256 patterns,
generated by `tools/gen-braille.py`.  Partial coverage is worse than none for
a braille spinner: the frames the font lacks jump to the fallback and the
spinner visibly jitters.  The block is perfectly regular -- the codepoint's low
byte is the dot bitmask -- so there is no judgement involved, and it should be
regenerated rather than hand-edited.

## The dingbats block

`glyphs/dingbats.txt` and `glyphs/circled-digits.txt` cover **177 of the 192**
codepoints in U+2700..U+27BF.  Fifteen are left out.

They are left out **by rule**: they have `Emoji_Presentation=Yes`, which
makes them East Asian Wide.  A terminal gives such a character two cells and
takes it from the emoji font, so a 7x14 bitmap for it would be both unused and
the wrong width.  Those fifteen are `✅ ✊ ✋ ✨ ❌ ❎ ❓ ❔ ❕ ❗ ➕ ➖ ➗ ➰ ➿`.

One glyph that is drawn needed a trick to get there: `➉` U+2789 CIRCLED
SANS-SERIF NUMBER TEN.  Two digits take five columns -- a 3-wide zero, a 1-wide one and a gap
-- and a full ring takes the outer two, so there is no separation at all: the
one merges into the left wall and the zero into the right.  So `➉` gets an
**open ring**, the top and bottom arcs only, positioned so that no arc pixel
sits in a digit column.  It keeps the family's height and still reads as an
enclosure.  Its two *negative* siblings `❿` and `➓` need none of this: a solid
disc has no thin wall to merge with, so the digits are simply knocked out of
it.

Three compromises are deliberate and should not be "fixed":

* **Zapf's weight pairs collapse.**  Many of these characters differ only by
  stroke weight or by a shading effect that needs more than seven columns.
  Where two names land on one achievable shape, they are held apart by *which*
  edge carries the extra weight -- upper against lower, left against right.
  This is the same compromise `glyphs/ui.txt` already makes for the asterisks.
* **Serif and sans-serif are invisible at 7x14.**  U+2776..U+277F and
  U+278A..U+2793 are both negative circled runs and come out identical.
* **The geometry is split by kind.**  The ornaments -- stars, crosses,
  florettes, snowflakes, arrows -- use the 7x7 symbol box on rows 4..10, the
  same box as `★` and `◆`.  The pictographs and the tall crosses use rows
  3..11, starting at cap height, because they need the height to read at all.
  The bracket ornaments sit on rows 2..12, the span the base font gives
  `( ) [ ] { }`.

The circled digits are generated by `tools/gen-circled-digits.py`; everything
else in the block is hand-drawn.  Both files fall inside `embolden.py`'s
keep-as-is range, so bold and regular are identical here -- widening a
dingbat makes it lopsided, not bold.

## Known gaps

* **Cyrillic** U+0400..U+04FF is not drawn.
* **Miscellaneous Symbols** U+2600..U+26FF has only `★` and `☆`.
* **Miscellaneous Technical** U+2300..U+23FF has only what `glyphs/ui.txt`
  needed.
* Only the **7x14** size is patched.  Every Tamzen size shares the family name
  "Tamzen", so keep exactly one of them in
  `~/.local/share/fonts/tamzen-patched/`.
