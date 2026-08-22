# Smalti — a pixel font with wide Unicode coverage

*Smalti* are the small glass tiles a mosaic is made from.  A pixel is one.

Upstream Tamzen 7x14 has **189 glyphs and nothing above U+00FF**: no `§`, no
`¶`, no dashes, no arrows, no triangles, no `…`.  Smalti adds 813 more and
draws two faces upstream never had, so each of its **four faces carries 1002
glyphs**:

| face | how it is made |
|---|---|
| Regular | upstream, plus the drawings in `glyphs/7x14/regular/` |
| Bold | upstream's own bold, plus emboldened drawings |
| Oblique | the regular face sheared one column each way |
| Bold oblique | sheared first, emboldened second |

Every glyph is an ASCII-art text file of its own, named for its codepoint.  A
`#` is ink and a `.` is not; the drawings are the font, and the `.otb` and the
`.ttf` are build artefacts.

    make install     # builds all four faces and installs them

## Lineage and licence

**Tamsyn → Tamzen → Smalti.**  Scott Fial drew Tamsyn in 2010.  Suraj N.
Kurapati forked it as Tamzen in 2011.  This is a fork of Tamzen, renamed for
the same reason Tamzen was: it is a different font now, and shipping it under
someone else's name would make both harder to install.

Both upstream licences say:

> "…font is free.  You are hereby granted permission to use, copy, modify,
> and distribute it as you see fit."

Modification is explicitly permitted.  See `LICENSE.tamzen`.  The
`(c) 2015 Scott Fial` notice stays in the font's name table, alongside ours.

**The size is part of the family name** — `Smalti 7x14`, not `Smalti`.  Each
cell size is a separate design with its own metrics, so if they all claimed
the family name `Smalti` a font matcher would pick between them arbitrarily.
That is the bug upstream has, and the reason Tamzen's own notes say to keep
only one size installed.  With the size in the name, every size can be
installed at once.

## Build

Every face is built twice: as a bitmap `.otb`, and as an outline `.ttf`
traced from the same bitmap.

Needs `fonttosfnt` (Debian/Ubuntu: `xfonts-utils`) for the `.otb` files and
`python3-venv` for the `.ttf` files.

    make               # build all four faces, bitmap and outline, into build/
    make venv          # just the Python dependencies, into ./.venv
    make outlines      # just the four .ttf files
    make woff2         # .woff2 for the web
    make check         # everything: the glyph store, the built faces, and
                       #   the proof that each .ttf matches its strike
    make check-sources    # the glyph store and the built faces only
    make check-outlines   # the .ttf-against-.bdf proof only
    make headers       # rewrite every drawing into its normal form
    make index         # regenerate docs/coverage.md
    make preview       # show the added glyphs as ASCII art
    make install       # copy the .otb files to ~/.local/share/fonts/smalti/
    make install-outlines   # copy the .ttf files to …/smalti-ttf/
    make watch         # rebuild, install and reload on every save
    make restore       # put upstream Tamzen back, if Smalti misbehaves

From a clean clone, `make` is enough: it creates `.venv` itself.

After `make install`, reload wezterm with `Ctrl+Shift+R`.

### Which file to use

The `.otb` files are **bitmap-only**, so fontconfig will not serve them —
`/etc/fonts/conf.d/70-no-bitmaps-except-emoji.conf` rejects anything with
`outline=false`, and no browser renders an embedded bitmap strike either.
wezterm reaches them through `config.font_dirs`:

    font_dirs = { os.getenv('HOME') .. '/.local/share/fonts/smalti' },
    font = wezterm.font_with_fallback { { family = 'Smalti 7x14' } },
    font_size = 10.5,   -- 14 ppem at 96 dpi

The `.ttf` files have real outlines, so `fc-match "Smalti 7x14"` finds them
and every other application does too.  `make install-outlines` puts them in
a *separate* directory on purpose: both formats carry the family name
`Smalti 7x14`, so keeping them apart is what stops wezterm's `font_dirs`
from seeing two candidates for every face.

## Outlines

`tools/trace-outline.py` turns one BDF strike into one `.ttf`.  Not a curve
fit — `potrace` and friends smooth pixel edges, which is exactly wrong here.
The outline is the **exact union of the lit pixels**, at integer coordinates.

**The em is a whole number of pixels.**  `upem = cell_height * 64`, so one
pixel is exactly 64 units and 7x14 gets `upem = 896`, advance 448, ascent
704, descent 192.  At 14 ppem a pixel edge at unit *k*·64 lands on device
pixel *k* with no rounding; the mapping is linear, so 28 px and 42 px are
exact too.  `make check` rasterises all four faces at 14, 28 and 42 ppem and
finds **no** pixel different from the bitmap and **no** antialiased pixel.
Sizes between multiples do blur — that is the one thing an outline gives up,
and wezterm only ever asks for an exact ppem anyway.

**One file per strike**, because outlines cannot vary with cell size: a
variable font's `opsz` axis would need interpolation-compatible masters, and
the same glyph at 5x9 and 10x20 is a different number of rectangles in
different places.

The one hard case is **two pixels touching only at a corner**.  That vertex
has two incoming and two outgoing edges, so a point-keyed lookup loses one
and the contour walk dies; there are 6,223 such vertices across the four
faces.  Each arrival is paired with the sharpest *right* turn.  Either
pairing is correct — the winding number of a point is a sum over the edges
and does not depend on how they are grouped into loops — so the choice only
decides whether `o` comes out as one pinched ring or as four rectangles
whose union is the same shape.  Contour count is not the goal; the area
check is.

`make check` is the proof, over all 4,008 glyphs of all four faces:

| check | result |
|---|---|
| signed filled area vs. lit pixel count | 0 discrepancies |
| segments that are not axis-aligned | 0 |
| coordinates off the 64-unit grid | 0 |
| off-curve points | 0 |
| points per glyph | 22.4 mean, 132 worst |

This path never runs `fonttosfnt`, so it does not inherit its broken name
table either: nameID 6 is written, nameID 5 carries the real version, and
nameID 10 is a whole sentence.  `head.macStyle` and `OS/2 fsSelection` are
set from one table in the tracer, so they cannot disagree.

### The build is byte-reproducible

Two clean builds of the same tree produce byte-identical `.ttf` and
`.woff2`.  This is not tidiness: **the acceptance test for any change to the
glyph store is that these files do not change**, which is how a
thousand-file restructuring is proved to have moved no pixel.  A wall-clock
stamp anywhere in the output would silently destroy that test, and it is
`fontTools`' default for `head.created` / `head.modified`, so the tracer
sets them explicitly.

    make                          # 2026-01-01, the committed fallback
    SOURCE_DATE_EPOCH=… make      # whatever CI or a release tag pins

`SOURCE_DATE_EPOCH` is the only thing that moves the bytes; nothing else in
the tracer is clock- or environment-derived, and glyph order, edge order and
the contour walk are all order-stable by construction rather than by
accident.  The `.otb` files are unaffected either way — `fonttosfnt` already
writes a fixed stamp.

## `make watch` — the editing loop

Run it in a spare pane, then just edit a glyph file and save:

    make watch

Every save rebuilds, installs, and `touch`es `~/.config/wezterm/wezterm.lua`,
which triggers wezterm's own automatic config reload — the same thing
`Ctrl+Shift+R` does.  New pixels appear in about a second, in every wezterm
window.

If a glyph is malformed the build stops, prints the offending line, and
**leaves the installed font untouched**, so a half-typed glyph never blanks
your terminal.  The watcher keeps running; fix the file and save again.

It watches the `glyphs/` and `tools/` trees rather than individual files,
because editors replace a file instead of writing into it and a file watch
would end up pointing at the old inode.

## How it works

    glyphs/7x14/<face>/  ┐
    upstream/7x14/       ├─build-face.py──►  build/…bdf
    build/gen/7x14/…     ┘ ──fonttosfnt───►  build/…otb
                           ──repair-tamzen.py─►  usable in wezterm
                           ──trace-outline.py─►  build/…ttf, usable everywhere

Three layers, and for each codepoint the build takes the first that exists:

| | source | owner |
|---|---|---|
| 1 | `glyphs/<size>/<face>/<CP>.txt` | this project's contributors |
| 2 | `upstream/<size>/…<face>.bdf` | Scott Fial / Suraj N. Kurapati |
| 3 | `build/gen/<size>/<face>/<CP>.txt` | a generator |

**A drawing always beats a computation.  A computation always beats nothing.**
Upstream sits above the generators, not below, because it is also hand-drawn:
`tools/weight.py` reproduces only 93 of upstream's 189 bold glyphs, and a
hand-drawn bold beats a computed one.  The faces upstream never drew — italic
and bold-italic — simply have no layer 2.

Everything a generator writes goes into `build/gen/` and nothing else, so
every generator stays re-runnable for ever and no contributor's work can be
overwritten by one.  Overriding a generator is not a flag or a marker, it is
just drawing the glyph: create the file and it wins.

One file per glyph, named for the codepoint in uppercase hex, so a pull
request touches exactly one file, the diff *is* the drawing, and a duplicate
codepoint is impossible rather than merely checked for.  Hex rather than the
character itself because the character does not survive contributors: 142 of
this font's codepoints collide case-insensitively on APFS and NTFS, 168
normalise to NFD on macOS, and 17 cannot be a bare filename at all.

`upstream/` holds pristine upstream BDF sources and is never edited — it keeps
Tamzen's own filenames, because those files *are* Tamzen.  `baseline/` holds
the exact `.otb` files that were live before this repo existed, so
`make restore` is always a working escape hatch.

`docs/coverage.md`, regenerated by `make index`, says what each size and face
actually carries.  A size with zero drawings still builds; it comes out as
plain upstream Tamzen.  Ragged coverage is a first-class state.

`repair-tamzen.py` is required on every `.otb` build, not just on upstream files:
`fonttosfnt` itself emits the four broken metric fields (wrong EBLC
`indexTablesSize`, wrong `hmtx` advance, wrong `OS/2` `xAvgCharWidth`, phantom
`hhea` leading).  Without the repair the font renders **blank** in wezterm,
because it is bitmap-only and has no outline to fall back to.

## Drawing a glyph

Create `glyphs/7x14/regular/2192.txt`:

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

Exactly 14 rows of exactly 7 characters.  `#` is ink, `.` is background.
The builder refuses anything else, so a miscounted row is a build error,
not a silently wrong glyph.  The header line is filled in by `make headers`,
so leave it off if you like — that command rewrites the whole file into its
normal form, which is what `make check` insists on, byte for byte.

The same file under `glyphs/7x14/bold/`, `…/italic/` or `…/bold-italic/`
overrules the derived face for that one codepoint — which is how the nine
letters the shear leaves upright, and every judgement `embolden.py` makes,
can now be corrected by hand.

`glyphs/7x14/README.md` is the per-size grid reference and is the first thing
to read before drawing at a new size.  Geometry, read off the existing glyphs
(`tools/show-glyphs.py` shows any of them):

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

  tools/show-glyphs.py build/Smalti7x14-Regular.bdf U+005F U+00AB U+0026

## The character set

The tables below cover the symbol set.  Latin Extended-A (128, generated) and
Greek (49, hand-drawn) are not listed here; `docs/coverage.md` counts every
face, and `make show` prints the lot in the terminal's own font.

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

Latin Extended-A is **generated on every build** by `tools/gen-latin-ext-a.py`,
into `build/gen/7x14/regular/` and `build/gen/7x14/bold/`.  It is the one
generator that produces the bold face as well, and for bold that beats
emboldening.

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

Greek, U+0370..U+03FF, is hand-drawn, except the capitals whose letterform
is identical to Latin (`Α` `Β` `Ε` `Ζ` `Η` `Ι` `Κ` `Μ` `Ν` `Ο` `Ρ` `Τ` `Υ` `Χ`)
which are copies of Tamzen's own bitmaps, so the two cannot drift apart.
`μ` and `µ` share one shape.

## Bold

All four faces carry all 1002 glyphs.  The bold face is upstream's own bold
wherever upstream drew one — 190 glyphs, hand-tuned, and nothing computed
beats that.  The other 812 are derived from the **resolved** regular face on
every build, so hand-drawing a regular glyph improves its bold without anyone
touching the bold face.  Three different ways, depending on what gives the
better result:

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

`KEEP` and `TWIN` in `tools/embolden.py` are policies about how to *derive*,
not shapes, so they stay in Python.  Changing a shape still needs no code
change, because the way to change a shape is to draw it — and a drawing in
`glyphs/7x14/bold/` outranks every rule in there.

There is nothing to regenerate by hand any more: `make` resolves the whole
stack, and `make watch` rebuilds on every save.

## Upstream's diaeresis

`U+00A8` is the one codepoint where a hand-drawn upstream bold and a derived
one both exist.  Upstream puts the dots in columns 0–1 and 3–4; emboldening
the regular drawing puts them in 1–2 and 4–5.  Upstream wins, because it is
hand-drawn.  If the other form is wanted after all, the answer is to draw it:
`glyphs/7x14/bold/00A8.txt` outranks both.

## The arrows block

The **whole** U+2190..U+21FF block is generated by
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

U+E0A0..U+E0BF is the **only** private-use range drawn here, and
deliberately so.  Nerd Font puts about 3,600 more icons in the PUA; those are
designed for a double-width cell and the CommitMono Nerd Font fallback already
renders them properly, so drawing them at 7x14 would make them worse.  The
separators fill the cell edge to edge on purpose — they must butt against
their neighbours with no seam — which also means they must never be
emboldened, and `tools/embolden.py` keeps U+E0B0..E0BF as-is.

## Terminal UI symbols

What Claude Code and similar TUIs draw is covered: the `❯` prompt chevron, the
spinner's dot-into-a-star progression (`✢ ∗ ✳ ✻ ✽ ✶ ✷ ✸ ✹ ✺`), the part-filled
circles `◐ ◑ ◒ ◓ ◔ ◕`, the `⏺` tool marker and the `⎿` result connector.

The **whole** U+2800 block, all 256 patterns, is generated by
`tools/gen-braille.py`.  Partial coverage is worse than none for
a braille spinner: the frames the font lacks jump to the fallback and the
spinner visibly jitters.  The block is perfectly regular -- the codepoint's low
byte is the dot bitmask -- so there is no judgement involved anywhere in it.

## The dingbats block

**177 of the 192** codepoints in U+2700..U+27BF are covered — 147 hand-drawn,
30 circled digits generated.  Fifteen are left out.

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
  This is the same compromise the terminal-UI asterisks already make.
* **Serif and sans-serif are invisible at 7x14.**  U+2776..U+277F and
  U+278A..U+2793 are both negative circled runs and come out identical.
* **The geometry is split by kind.**  The ornaments -- stars, crosses,
  florettes, snowflakes, arrows -- use the 7x7 symbol box on rows 4..10, the
  same box as `★` and `◆`.  The pictographs and the tall crosses use rows
  3..11, starting at cap height, because they need the height to read at all.
  The bracket ornaments sit on rows 2..12, the span the base font gives
  `( ) [ ] { }`.

The circled digits are generated by `tools/gen-circled-digits.py`; everything
else in the block is hand-drawn.  The whole block falls inside `embolden.py`'s
keep-as-is range, so bold and regular are identical here -- widening a
dingbat makes it lopsided, not bold.

The three geometry bands are also recorded in `glyphs/7x14/README.md`, where
someone drawing a new dingbat will actually look.

## Known gaps

* **Latin-1 Supplement is 94 of 96**, not finished: `ª` U+00AA FEMININE
  ORDINAL INDICATOR and `º` U+00BA MASCULINE ORDINAL INDICATOR are the two
  holes, in every face.  Nothing else in U+00A0..U+00FF is missing.
* **Cyrillic** U+0400..U+04FF is not drawn.
* **Miscellaneous Symbols** U+2600..U+26FF has only `★` and `☆`.
* **Miscellaneous Technical** U+2300..U+23FF has only what the terminal-UI
  glyphs needed.
* Only the **7x14** size is drawn.  Upstream ships 5x9, 6x12, 7x13, 8x15,
  8x16 and 10x20 as well.  The layout is multi-size from day one and populated
  with 7x14 only: adding `glyphs/6x12/regular/` costs nothing now and would be
  a brutal retrofit once other people have forks and open pull requests.
  Unlike Tamzen, several Smalti sizes *can* be installed side by side once
  they exist, because the size is part of the family name.
* **`fonttosfnt` writes an incomplete name table.**  nameID 6, the PostScript
  name, is missing although OpenType requires it; nameID 5 says
  "Version 0.0"; nameID 10 is truncated mid-word.  None of it stops the font
  working, and none of it is inherited by the `.ttf` files, which are written
  by `fontTools` and never see `fonttosfnt`.  Only the `.otb` path is
  affected, and `repair-tamzen.py` leaves the name table alone.
