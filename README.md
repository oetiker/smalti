# Smalti — a pixel font with wide Unicode coverage

*Smalti* are the small glass tiles a mosaic is made from.  A pixel is one.

Upstream Tamzen 7x14 has **189 glyphs and nothing above U+00FF**: no `§`, no
`¶`, no dashes, no arrows, no triangles, no `…`.  Smalti adds 815 more and
draws two faces upstream never had, so each of its **four faces carries 1004
glyphs**:

| face | how it is made |
|---|---|
| Regular | upstream, plus the drawings in `glyphs/7x14/regular/` |
| Bold | upstream's own bold, plus emboldened drawings |
| Oblique | the regular face sheared one column each way |
| Bold oblique | sheared first, emboldened second |

Every glyph is an ASCII-art text file of its own, named for its codepoint.  A
`#` is ink and a `.` is not; the drawings are the font and the `.ttf` files
are build artefacts.

    make install     # builds all four faces and installs them

It is a **pixel font delivered as outlines**.  Every glyph is a set of
axis-aligned rectangles on a grid where one pixel is exactly 64 font units,
so at its drawn size — and at every whole multiple of it — a rasteriser
reproduces the drawing exactly, with no grey and nothing to hint.  Between
those sizes it does not.  **See [Making it look right](#making-it-look-right)
before configuring a terminal**; two settings decide whether you get the
pixels or a blur.

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

Each face is drawn as a bitmap strike (`.bdf`) and traced into an outline
(`.ttf`).  The `.ttf` is the only delivered format.

Needs `python3-venv`, and nothing else — no system font tooling.

`make packages` additionally needs `envsubst` (Debian/Ubuntu: `gettext-base`)
to expand environment variables in the package configuration before passing
it to nfpm. `make check-packages` additionally needs `dpkg-deb`, `rpm` and
`cpio` (Debian/Ubuntu: `dpkg`, `rpm`, `cpio`) to open the built packages with
the package managers' own tools. Neither is needed to build or check the
fonts themselves.

    make               # build all four faces, .bdf and .ttf, into build/
    make venv          # just the Python dependencies, into ./.venv
    make outlines      # just the four .ttf files
    make woff2         # .woff2 for the web
    make check         # all three: the glyph store and the built faces, the
                       #   proof that each .ttf matches its strike, and the
                       #   version in every artefact
    make check-sources    # the glyph store and the built faces only
    make check-outlines   # the .ttf-against-.bdf proof only
    make check-version    # the version, read back out of every built face
    make packages       # build the .deb and .rpm into build/
    make check-packages # open both with dpkg-deb and rpm, and prove they
                        #   carry the same fonts make check just validated
    make headers       # rewrite every drawing into its normal form
    make index         # regenerate docs/coverage.md
    make site          # build the specimen site into build/site/
    make serve-site    # …and serve it on http://localhost:8014/
    make check-site    # prove the site ships this repository's drawings
    make preview       # show the added glyphs as ASCII art
    make install       # copy the .ttf files to ~/.local/share/fonts/smalti-ttf/
    make watch         # rebuild, install and reload on every save
    make restore       # put upstream Tamzen back, if Smalti misbehaves

From a clean clone, `make` is enough: it creates `.venv` itself.

After `make install`, reload wezterm with `Ctrl+Shift+R`.  If it then says it
cannot load the font, that is a stale font cache and not a failed install —
see [The font is installed and the terminal cannot see
it](#the-font-is-installed-and-the-terminal-cannot-see-it).

### Why there is no `.otb`

Smalti used to ship a second, bitmap-only format built by `fonttosfnt`.  It
is gone.  A bitmap-only font has `outline=false`, which
`/etc/fonts/conf.d/70-no-bitmaps-except-emoji.conf` rejects outright, and no
browser renders an embedded strike — so it reached nothing except a wezterm
patched to read strikes, while needing an apt package the rest of the build
did not.  The `.ttf` renders the same pixels everywhere, and `make check`
proves it glyph by glyph.  Dropping the format removed the last dependency
outside pip.

## Releases

    VERSION       0.0.0 — the one place the version is written down
    CHANGES.md    what is in each release, and what is not out yet

A release is two clicks: dispatch **Create release PR** from the Actions tab,
review the pull request it opens, and merge it.  Merging tags the version,
builds and checks the fonts and the `.deb`/`.rpm` packages, and attaches all
of them to the release.

**See [`RELEASING.md`](RELEASING.md)** for the whole procedure, including the
two things that look wrong and are not, and how to recover a run that failed
halfway.

### From a package

Every release attaches a `.deb` and an `.rpm`.

    sudo apt install ./fonts-smalti_0.1.0-1_all.deb    # Debian, Ubuntu
    sudo rpm -i smalti-fonts-0.1.0-1.noarch.rpm        # Fedora, RHEL, openSUSE

Both install the four faces where fontconfig finds them and carry no
maintainer scripts: the distributions' own `fontconfig` triggers rebuild the
cache.  There is no apt or yum repository to add — that would need a signing
key this project does not have.

The version reaches every artefact — `build-face.py` writes it into the BDF as
`FONT_VERSION`, `trace-outline.py` copies it into the `.ttf` name table and
`head.fontRevision` — and `make check-version` reads it back out to prove it.
A release flow that bumps a number nothing reads is worthless.

## Making it look right

Smalti is drawn at 7x14 pixels.  A rasteriser reproduces those pixels exactly
only if you tell it the right size and the right kind of antialiasing.  Get
either wrong and you get a font that is technically correct and visually
mush.  There are two rules, and a third thing that is not a rule at all.

### 1. Use an exact size, or a whole multiple of it

The em is a whole number of pixels — `upem = cell height * 64`, so 7x14 gets
`upem = 896` and one pixel is exactly 64 units.  At **14 px** every pixel
edge lands on a device pixel boundary, so coverage is 0 or 255 everywhere.
The mapping is linear, so **28 px** and **42 px** are exact too.

Anything in between is not.  At 20 px a one-pixel stem is 1.43 device pixels,
and the 0.43 has to go somewhere: it becomes grey.

Sizes are usually configured in **points**, and points become pixels through
the display's dpi:

    pixels = points * dpi / 72

So at the usual 96 dpi, **`font_size = 10.5`** is 14 px.  At 192 dpi the same
14 px is `font_size = 5.25`, and `10.5` would give you 28 px — also exact.
If your terminal takes a pixel size directly, use 14, 28 or 42 and skip the
arithmetic.

| device pixels | points at 96 dpi | result |
|---|---|---|
| 14 | 10.5 | exact — the drawing |
| 28 | 21 | exact, doubled |
| 42 | 31.5 | exact, tripled |
| anything else | — | antialiased |

### 2. Grayscale antialiasing, never LCD subpixel

This is the one that surprises people, because subpixel rendering normally
makes text *better*.

LCD subpixel rendering triples the horizontal sampling rate and then runs a
filter across the result, to trade colour accuracy for apparent sharpness.
On a font whose stems are already exactly one pixel wide, there is no
sharpness left to buy and the filter has nothing to do but smear.  Measured
on Smalti 7x14 Regular at 14 px, a one-pixel stem comes out as:

| render target | the stem |
|---|---|
| grayscale | `255` |
| LCD subpixel | `83  171  255  171  83` |

A solid black column becomes a five-subpixel coloured smudge.  Across the
regular face at 14 px, **1000 of the 1003 rendered glyphs differ from the
drawing under LCD, and none differ under grayscale**.  The three that survive
are `U+0020`, `U+00A0` and `U+2800` — the three with no ink in them.  It is
not the LCD filter setting either: `FT_LCD_FILTER_NONE` spreads it
identically.

So: grayscale.  In wezterm that is `freetype_load_target = 'Light'` and
`freetype_render_target = 'Light'`.  In fontconfig it is `rgba=none`.

### 3. Hinting does not matter

Hinting exists to drag outlines onto the pixel grid.  These outlines are
already on it, so there is nothing to drag.  Measured over every glyph at
14 px and 28 px, with hinting off, on, `TARGET_LIGHT` and forced autohint:
**identical to the drawing in all four, zero grey pixels.**  Leave the
setting wherever it is.

### The cell

A terminal sizes its cell from the font's metrics, and Smalti's are exact
rather than tuned:

| field | value | meaning |
|---|---|---|
| `unitsPerEm` | 896 | 14 rows x 64 units |
| `hhea.ascent` | 704 | 11 rows above the baseline |
| `hhea.descent` | -192 | 3 rows below |
| `hhea.lineGap` | 0 | leading is the terminal's business |
| `OS/2.xAvgCharWidth` | 448 | exactly the 7 px advance |

So in wezterm `cell_width = 1.0` gives `ceil(7.0) = 7` columns, and
`line_height = 1.14` gives `ceil(14 * 1.14) = 16` rows — the glyph plus two
rows of leading, split evenly above and below the baseline.  `line_height =
1.0` packs the rows with no leading at all.

`make check-sources` verifies every one of those fields on every built face.
Each has been wrong in a shipped build of this font at least once, and each
time the symptom was the font looking wrong rather than the build failing.

### wezterm, all together

```lua
config.font_dirs = { os.getenv 'HOME' .. '/.local/share/fonts/smalti-ttf' }
config.font = wezterm.font_with_fallback {
  {
    family = 'Smalti 7x14',
    freetype_load_target = 'Light',   -- grayscale, NOT 'HorizontalLcd'
  },
  {
    family = 'JetBrains Mono',        -- or whatever you fall back to
    freetype_load_target = 'Light',   -- the fallback needs it too, see below
  },
}
config.freetype_render_target = 'Light'
config.font_size = 10.5      -- 14 px at 96 dpi
config.cell_width = 1.0      -- 7 px
config.line_height = 1.14    -- 16 rows
```

**The fallback font needs the load target too.**  `freetype_load_target` is a
per-font attribute and only reaches the rasteriser from the entry that
actually supplies the glyph.  A fallback resolved implicitly carries no
attributes and rasterises grayscale while the base font is LCD, or the other
way round — invisible behind a font with full coverage, glaring behind one
that falls back for anything it lacks.

### Other terminals

The two rules are the same everywhere; only the spelling changes.

* **kitty** — `font_size 10.5`, and `text_composition_strategy legacy` if
  the default thickening looks heavy.  kitty has no subpixel mode, so rule 2
  is already satisfied.
* **Alacritty** — `font.size = 10.5`.  Set `rgba=none` for the family in
  fontconfig; Alacritty takes its antialiasing from there.
* **foot** — `font=Smalti 7x14:size=10.5`, and `dpi-aware=no` if you want
  points read against 96 dpi rather than the real display dpi.
* **A browser or an editor** — set the size in **`px`**, not `pt`, `em` or a
  percentage, and use 14, 28 or 42.  The specimen site offers exactly those
  three sizes and nothing in between, for this reason.

### The font is installed and the terminal cannot see it

    Unable to load a font specified by your font=wezterm.font('Smalti 7x14', …)
    configuration. Fallback(s) are being used instead

If `fc-list | grep -i smalti` lists all four faces and a *freshly started*
program finds the font, then it is installed and the message is about a
**cache, not the install**.

fontconfig builds its list of fonts once per process.  A terminal that was
already running when you installed the font has never seen those files, and
never will: reloading the configuration re-reads the config file, not the
system font database.  Restarting the program fixes it — and so does
`font_dirs`, which wezterm scans itself, on every reload, without asking
fontconfig.  That is why the snippet above sets it even though fontconfig
serves these files perfectly well.

**Keep that directory holding `.ttf` only.**  wezterm scans `font_dirs`
directly, including formats fontconfig would refuse, so a leftover file from
an older build sitting beside them offers a second candidate for every face.

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

`make check` is the proof, over all 4,016 glyphs of all four faces:

| check | result |
|---|---|
| signed filled area vs. lit pixel count | 0 discrepancies |
| segments that are not axis-aligned | 0 |
| coordinates off the 64-unit grid | 0 |
| off-curve points | 0 |
| points per glyph | 22.5 mean, 132 worst |

Nothing in this path runs `fonttosfnt`, so nothing inherits its broken name
table: nameID 6 is written, nameID 5 carries the real version, and nameID 10
is a whole sentence.  `head.macStyle` and `OS/2 fsSelection` are set from one
table in the tracer, so they cannot disagree — and `make check-sources`
verifies that they still agree in the file that comes out.

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
accident.

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
    build/gen/7x14/…     ┘                     │
                           ┌─trace-outline.py──┘
                           ├─►  build/…ttf     usable everywhere
                           └─►  build/…woff2   for the specimen site

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
`make restore` is always a working escape hatch.  Those are upstream Tamzen's
own files and have nothing to do with Smalti's build, which produces no
`.otb` at all.

`docs/coverage.md`, regenerated by `make index`, says what each size and face
actually carries.  A size with zero drawings still builds; it comes out as
plain upstream Tamzen.  Ragged coverage is a first-class state.

`repair-tamzen.py` is no longer part of the build.  It repaired the four
metric fields `fonttosfnt` emitted wrongly on every bitmap build (wrong EBLC
`indexTablesSize`, wrong `hmtx` advance, wrong `OS/2` `xAvgCharWidth`,
phantom `hhea` leading); with the `.otb` gone there is nothing to repair.  It
is kept for the one job that still needs it: repairing upstream Tamzen's own
files after `make restore`.  The same four fields are now *checked* rather
than repaired — see [The cell](#the-cell).

## The specimen site

    make site         # build it into build/site/
    make serve-site   # …and look at it on http://localhost:8014/
    make check-site   # prove it ships this repository's own drawings

`https://oetiker.github.io/smalti/` shows every glyph in every face as real
rendered text, says honestly what is and is not covered, and lets a visitor
**click any glyph, change its pixels and open the pull request from the
browser** — no clone, no Python, no toolchain.  For a codepoint nobody has
drawn yet the link arrives at GitHub with the path and the drawing already
filled in; for one that already has a file it opens that file in GitHub's
editor.  That is the property the one-file-per-glyph layout was for.

Three things about it are not obvious:

* **It loads the `.woff2` files**, which are the `.ttf` outlines compressed.
  No browser draws an embedded bitmap strike, so the outline path is the only
  one that could ever have reached a web page.
* **It only ever sets type at 14, 28 and 42 px**, because those are the sizes
  at which the outline reproduces the strike exactly.  A pixel font at 17px
  looks broken, so no size in between is offered.
* **Nothing under `build/site/` is committed.**  The page is generated from
  the drawings by `tools/build-site.py`, and `tools/check-site.py` compares
  every glyph it ships — and the exact bytes its editor would put on a
  contributor's clipboard — back against the store.  `site/` holds the HTML,
  CSS and JS it is generated from; there is no npm and no build step.

`.github/workflows/pages.yml` runs `make check-site` and publishes the result.

### The editor's ghost, and where its edits go

Two things in the editor exist for the case where you sit down to draw a
whole block rather than one character.

**A ghost of the character behind the grid.**  Drawing a codepoint nobody has
drawn yet means knowing what it is supposed to look like, and the reference
has to be the same for everybody — a hint that came from whichever fonts the
visitor happened to have installed would have two contributors tracing two
different shapes.  So the reference fonts are vendored, in `site/hint/`:

| file | codepoints |
|---|---:|
| `NotoSansMono-Regular.woff2` | letters, digits, punctuation, Greek, Cyrillic |
| `NotoSansSymbols2-Regular.woff2` | arrows, box drawing, blocks, braille, shapes |
| `NotoSansSymbols-Regular.woff2` | dingbats and the rest of the symbol blocks |
| `NotoSansMath-Regular.woff2` | mathematical operators |
| `SymbolsNerdFont-Regular.woff2` | the private-use icons, Powerline included |

**None of them is subsetted**, deliberately.  Cutting them down to what
Smalti covers today would delete the hint for exactly the glyphs that are not
drawn yet, which is the only case the ghost is for.  About 1.7 MB sits in the
repository; a visitor downloads **one** of those files, because
`tools/build-site.py` reads their cmaps and gives each file a `unicode-range`
covering exactly the codepoints it owns, with no overlaps.  (Do not try to
chunk the Nerd Font to make that download smaller.  Measured: splitting it by
range produced 2.2 MB of parts against 1.0 MB whole, because woff2 compresses
the whole glyph set better than its pieces.)

Where a codepoint is in none of them, the editor **says so** instead of
drawing the empty box a missing glyph produces — which a contributor would
reasonably read as a design decision.  `make check-site` proves both halves of
that claim: every codepoint offered a ghost really is in a shipped font, and
every codepoint refused really is in none of them.

`tools/make-hint-fonts.py` is what vendors them.  It is **not** part of
`make`: it needs the network, and putting a third party's release schedule
inside a byte-reproducible build would be a moving part in the one place this
project cannot afford one.  Every source is pinned to a commit or a release
tag, `site/hint/SOURCES.json` records the SHA-256 of what went in and what
came out, and `--check` re-derives the lot and compares without writing:

    .venv/bin/python tools/make-hint-fonts.py --check

Noto is under the SIL Open Font License, the Nerd Fonts symbols under MIT;
both licence files are vendored beside the fonts and served with them.

**A repository and branch of your own.**  The editor's links normally point at
this repository and its default branch.  Under *where edits go* you can point
them somewhere else, and the choice is remembered as you move from glyph to
glyph, so twenty edits land on one branch instead of scattering.  **The site
cannot create that branch** — a GitHub URL opens an editor on a ref, it does
not make one.  Make the first edit the ordinary way, then paste the branch
GitHub made for it into the box.  While a branch other than the default is in
force the editor offers both doors, create-the-file and edit-the-file, because
what the build knows about which glyphs exist is only true of the default
branch.

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

**Latin-1 characters upstream never drew** (13)

With `ª` and `º` this block is complete: 96 of 96.  Both are drawn as a
superscript letter in rows 2..6 over an underline in row 8, so the pair reads
as a pair -- and `°` U+00B0 stays the shorter four-row ring it always was,
because a degree sign is a symbol and an ordinal is a letter.

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
| `ª` | U+00AA | Feminine Ordinal Indicator |
| `º` | U+00BA | Masculine Ordinal Indicator |

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

All four faces carry all 1004 glyphs.  The bold face is upstream's own bold
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
* **Nothing proves a `.woff2` decompresses to the same outlines as the `.ttf`
  it came from.**  Every other artefact is checked against the drawings; this
  one is taken on trust from `fontTools`.  The build workflow emits a standing
  warning naming the gap rather than hiding it.  Closing it means
  decompressing the `.woff2` and running `check-outlines.py` on the result.
