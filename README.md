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

## The character set

67 glyphs, grouped by why they are here.

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

## Deliberately not drawn

Each of these was attempted and abandoned for a reason, not forgotten.  They
keep falling back to CommitMono, which is the right outcome.

| | why |
|---|---|
| `®` | the `©` ring spans 6 columns and leaves a 2-column interior.  A `C` fits there; an `R` does not. |
| `‰` | `%` already spans 6 of the 7 columns.  There is no room for a third zero. |
| `™` | two letterforms in one 7-pixel cell. |
| `¼` `½` `¾` | a digit, a solidus and a second digit in 7 columns. |
| `☆` | a hollow star at this size is mush; `★` is kept. |

`–` (en dash) is drawn **identical to the `-` hyphen**.  Tamzen's hyphen is
already 5 pixels and `—` takes all 7, so there is no third length available.
It is included anyway: without it the character would fall back to CommitMono
and render at a visibly different weight.

## Known gaps

* **Bold is not built yet.** `Tamzen7x14b.otb` is still the baseline, so bold
  text falls back to CommitMono for every added glyph.
* Only 7 glyphs so far — this is a probe, not a finished character set.
