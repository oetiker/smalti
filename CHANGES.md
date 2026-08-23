# Changelog

All notable changes to Smalti will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### New

- **The glyph store**: one file per glyph, at `glyphs/<size>/<face>/<CP>.txt`, resolved through a three-layer stack — a drawing here always wins, upstream Tamzen's own hand-drawn bitmap comes next, and a generator fills what is left. A generator writes only into `build/gen/`, so all seven are re-runnable and none can overwrite anyone's work; overriding one is not a flag, it is drawing the glyph. Duplicate codepoints are impossible rather than checked for, because the filesystem enforces uniqueness. The layout carries a size dimension from day one, populated with 7x14.
- **Outline faces**: every strike is traced into a `.ttf`, and compressed to `.woff2` for the web. The em is a whole number of pixels (upem = cell height x 64), so the outline reproduces the bitmap exactly at 14, 28 and 42 px. `make outlines`, `make woff2`, `make install`.
- **A specimen site**: every glyph in every face rendered as real text, an honest account of what is and is not covered, and a click on any tile — including an empty one — that opens that glyph's grid, editable, with the pull request one link away. `make site`, `make serve-site`, published to GitHub Pages.
- **`make check`**, three proofs that can each go red on their own: the glyph store and the render contract every built face must carry, the traced outlines against the bitmaps at 1x, 2x and 3x, and the version in every artefact. `make check-site` proves the site ships this repository's own drawings.
- **`make index`** regenerates `docs/coverage.md`, and **`make headers`** rewrites any drawing that has drifted out of normal form.
- **`make venv`** installs the build's Python dependencies into a project-local `.venv`. That is now the whole dependency list.
- **GitHub Actions**: `validate` on every push and pull request, `build` from a clean checkout, `pages` for the specimen site, and a two-step release — `Create release PR` from the Actions UI, then merging that pull request publishes.
- **A `VERSION` file**, the one place this project's version is written down. It reaches the BDF, the `.ttf` and the `.woff2`, and `make check-version` reads it back out of all of them.
- **A guide to configuring the font so it renders as drawn** — exact sizes, grayscale rather than LCD subpixel antialiasing, the cell metrics, and why a running terminal can fail to see a font that is correctly installed. See "Making it look right" in `README.md`.
- `ª` U+00AA and `º` U+00BA, the two ordinal indicators, which completes Latin-1 Supplement at 96 of 96.

- **The specimen site's editor shows the character behind the grid.** Drawing a codepoint nobody has drawn yet means knowing what it is meant to look like. Five reference fonts are vendored, unsubsetted, in `site/hint/` — Noto Sans Mono, Symbols, Symbols 2 and Math, plus the Nerd Fonts symbols for the private-use icons — so every contributor traces the same shape rather than whatever their own machine happens to have installed. A visitor downloads one of those files, never all of them: `tools/build-site.py` reads their cmaps and writes a `unicode-range` per file with no overlaps. Where no reference exists the editor says so instead of drawing the empty box a missing glyph produces, and `make check-site` proves that claim in both directions. `tools/make-hint-fonts.py` vendors them from pinned commits and release tags, outside `make`, with a `--check` that re-derives the lot byte for byte.
- **The editor can send its pull requests to a repository and branch of your choosing.** Remembered as you move from glyph to glyph, so drawing a whole block lands on one branch instead of scattering across twenty. The site cannot create the branch — a GitHub URL opens an editor on a ref, it does not make one — so the panel says that, and while a non-default branch is in force both the create-the-file and edit-the-file links are offered, because what the build knows about which glyphs exist is only true of the default branch.

### Changed

- **The bitmap `.otb` format is no longer built or shipped.** A bitmap-only font has `outline=false`, which fontconfig's `70-no-bitmaps-except-emoji.conf` rejects outright, and no browser renders an embedded strike — so it reached nothing except a wezterm patched to read strikes, while requiring an apt package (`xfonts-utils`, for `fonttosfnt`) that nothing else in the build needed. The `.ttf` renders the same pixels everywhere, proven glyph by glyph. `make install` now installs the `.ttf` files, `make install-outlines` is gone, and the build's only dependency is `python3-venv`.
- `tools/repair-tamzen.py` is no longer part of the build. The four metric fields it repaired were emitted wrongly by `fonttosfnt`; with that tool gone there is nothing to repair. The same four fields are now *checked* on every built face instead, by `make check-sources`. The script is kept for `make restore`, which repairs upstream Tamzen's own files.
- `glyphs-bold/` is gone. All 813 of it was reproducible and is now generated into `build/gen/7x14/bold/`, so `make sources` is gone with it — there is nothing left to regenerate by hand.
- Derived faces are built from the *resolved* regular face, so hand-drawing one regular glyph improves its bold, italic and bold-italic without anyone touching those faces.
- `U+00A8 DIAERESIS` in the bold and bold-italic faces is upstream's drawing again. It is the only codepoint where a generator's output overlaps a glyph upstream also draws, and a hand-drawn bitmap outranks a computed one. Dropping a drawing at `glyphs/7x14/bold/00A8.txt` reverses that.

### Fixed

- **The editor's baseline was drawn one pixel too low and was never once visible.** It was a pseudo-element at `bottom: -2px` on the cells of row 10, which put it inside row 11, where that row's own background painted over it. Nudging the offset does not fix a z-order problem, so all four guide lines moved onto a single canvas over the grid, positioned from the cells' real rectangles. Cap height and x-height, which had been the same blue at the same opacity and so could not be told apart, are now dashed and dotted, and the legend draws each swatch the way its line is drawn.
- **The font no longer claims to be Tamzen 1.11.** `FONT_VERSION` was inherited from upstream and never rewritten, so the `.ttf` name table carried upstream's version. Every artefact now carries this project's own version, and `make check-version` reads it back out to prove it.
- **The first real release would have crashed the build.** `head.fontRevision` was computed with `float()` on the version string, which raises `ValueError` on a three-part semantic version; it worked only because it was inheriting Tamzen's two-part `1.11`. The encoding is now `MAJOR.MMPP`, which orders correctly inside a 16.16 fixed-point field.
- **The outline build is byte-reproducible.** fontTools defaults `head.created` and `head.modified` to the wall clock, so two clean builds of the same tree produced four different `.ttf`. They now come from `SOURCE_DATE_EPOCH`, or from a committed constant when it is unset. Without this the acceptance test for any glyph-store change — build before, build after, compare — could never be run again.
- **Two checks that verified less than their names claimed.** A drawing could drift out of normal form unnoticed, because only its header line was compared rather than the whole file; and a run with nothing built announced that it was skipping a check and then exited 0. Both now fail. `tools/test-check-glyphs.py` breaks the tree twelve ways and insists the checker notices each one, so a green check means the checker could have gone red.
