# tobit — Tamzen 7x14 with extra glyphs

Upstream Tamzen 7x14 has **189 glyphs and nothing above U+00FF**: no `§`, no
`¶`, no dashes, no arrows, no triangles, no `…`.  This repo adds glyphs to it
and rebuilds the `.otb` that wezterm loads.

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

## Known gaps

* **Bold is not built yet.** `Tamzen7x14b.otb` is still the baseline, so bold
  text falls back to CommitMono for every added glyph.
* Only 7 glyphs so far — this is a probe, not a finished character set.
