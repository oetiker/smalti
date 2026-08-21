# Design: the glyph store

Status: proposed
Date: 2026-08-21 (revised 2026-08-22: §3 deep links, §11 rewritten, §12 naming)
Scope: sub-project **A** of five. B (outlines), C (CI + releases),
D (contributor surface) and E (more sizes populated) are out of scope; where
this design constrains them it says so.

## 1. Why

Three problems, one cause.

**A hand judgement about a derived face has to be written as Python.**
`tools/embolden.py` carries roughly 1040 codepoints in `KEEP` and 15 in
`TWIN`. Every one is a design decision -- "a filled circle has no strokes to
thicken" -- encoded as a set literal instead of as a drawing. For the oblique
and bold-oblique faces it is worse: **0 of 1002 glyphs can be hand-corrected
at all**. The nine letters the shear leaves upright are stuck upright.

**Three generators can never be run again.** `glyphs/arrows.txt`,
`glyphs/circled-digits.txt` and `glyphs/latin-ext-a.txt` each say
"re-running the generator overwrites your changes". They write into a path a
human owns, so the first hand edit retires the generator permanently.

**The format fights collaboration.** Block files mean two people drawing two
unrelated glyphs edit the same file and conflict. Worse, a codepoint defined
in two files silently shadows whichever sorts later -- a trap serious enough
that it is written down as a build-time check that must be remembered.

All three follow from the same thing: **there is no precedence.** Generated
output and hand-drawn output share a namespace, so one must destroy the other.

## 2. The rule

> A drawing always beats a computation. A computation always beats nothing.

Everything below is machinery for that sentence.

## 3. Layout

```
glyphs/<size>/<face>/<CP>.txt          committed, hand-owned, always wins
upstream/<size>/Tamzen<size><f>.bdf    committed, hand-drawn by upstream
build/gen/<size>/<face>/<CP>.txt       generated, never committed
```

* `<size>` is upstream's own spelling: `7x14`, `5x9`, `10x20`.
* `<face>` is one of `regular`, `bold`, `italic`, `bold-italic`.
* `<CP>` is the codepoint in **uppercase hex, at least four digits**:
  `0041.txt`, `00E9.txt`, `2500.txt`, `1F643.txt`.

### Why the filename is a codepoint and not the character

The character would be far nicer to read, and it cannot survive contributors.
Measured against the 1001 codepoints this font already covers:

* **142 case-insensitive collisions.** macOS APFS and Windows treat `A` and
  `a` as one path. A clone loses half the alphabet or fails. It is not only
  Latin -- Greek and Latin Extended collide too.
* **168 characters normalise to NFD on macOS.** `é` lands on disk as `e` plus
  a combining acute. `core.precomposeunicode` hides it, but it is a standing
  source of phantom "modified file" churn in pull requests.
* **17 codepoints cannot be a bare filename at all**: fourteen control
  characters, space, `.` and `/`.

Hex is pure ASCII, sorts naturally, collides with nothing and normalises to
itself. The readability comes back inside the file (§4) and in the generated
index (§9).

### Why one file per glyph

* A pull request touches **one file**. Two people drawing different glyphs
  can never conflict.
* The diff **is** the drawing: a reviewer watches `.` become `#`.
* Duplicate codepoints become **impossible**, because the filesystem enforces
  uniqueness. The existing hazard disappears rather than being checked for.
* An override is "create a file". That is the whole precedence mechanism --
  no markers, no in-file merging, no generator that has to parse and preserve
  its own previous output.
* **Every glyph gets a URL.** `github.com/<owner>/<repo>/edit/main/glyphs/7x14/regular/0041.txt`
  opens GitHub's web editor on that glyph's art. The specimen site (D) can
  therefore link each rendered character straight to its own edit box: see the
  glyph, click it, change a `.` to a `#`, open a pull request -- no clone, no
  toolchain, no Python. With block files a link could only ever point at a
  132-glyph file, so this property exists **only** because of this layout.

Cost: about 1000 files in one directory per populated size-and-face. Flat, not
grouped by Unicode block, because a block-grouped path would require a lookup
to know where a glyph lives.

## 4. File format

```
# U+0041 A  LATIN CAPITAL LETTER A
.......
.#####.
.#...#.
...
```

Line 1 is a header naming the codepoint, the character and its Unicode name.
Its only job is to make a diff legible, because `0041.txt` on its own tells a
reviewer nothing.

It is **normalised by `make headers` and checked by CI**, so a contributor may
leave it off entirely and have it filled in. Two cases have no obvious form
and are fixed here rather than left to whoever writes the tool:

* **The character is shown only when `str.isprintable()`**, quoted, so that
  `' '` for U+0020 is visible. Otherwise the field is empty.
* **15 codepoints in this font have no Unicode name** -- U+0000 and fourteen
  control characters that upstream draws anyway. They take `<control>` when
  their category is `Cc`, and `<unnamed>` otherwise.

```
# U+0041 'A'  LATIN CAPITAL LETTER A
# U+0020 ' '  SPACE
# U+000D      <control>
```

After it come exactly *H* rows of exactly *W* characters drawn from `.` and
`#`, where *W* and *H* come from the `<size>` in the path. The parser knows
the dimensions before it opens the file, so validation is exact.

**A pixel row is recognised before a comment.** `#` is both the ink pixel and
the comment marker, and the em dash row `#######` would otherwise be eaten as
a comment. This rule is inherited unchanged from `merge-glyphs.py`, where it
is already load-bearing.

## 5. Precedence

For each `(size, face, codepoint)` the build takes the first that exists:

| | Source | Owner |
|---|---|---|
| 1 | `glyphs/<size>/<face>/<CP>.txt` | this project's contributors |
| 2 | `upstream/<size>/…<face>.bdf` | Scott Fial / Suraj N. Kurapati |
| 3 | `build/gen/<size>/<face>/<CP>.txt` | a generator |

**Upstream sits above the generators, not below them, because it is also
hand-drawn.** Upstream ships a real bold face, and `tools/weight.py` records
that computed emboldening reproduces only 93 of its 189 glyphs. A hand-drawn
bold beats a computed one; the rule in §2 already says so.

This reproduces today's behaviour exactly: the 189 base glyphs come from
upstream, the 813 added ones from generators fed by `glyphs/`, and a hand file
overrides either.

Faces with no upstream equivalent -- `italic`, `bold-italic` -- simply have no
layer 2.

## 6. Generators

A generator **writes only into `build/gen/`** and never into a path a human
owns. That single constraint retires the whole "re-running this overwrites
your changes" class of problem: `gen-arrows.py`, `gen-circled-digits.py` and
`gen-latin-ext-a.py` become freely re-runnable, and a contributor who improves
one is not destroying anyone's work.

| Generator | Produces | From |
|---|---|---|
| `gen-braille.py` | regular | the codepoint's low byte, which *is* the dot mask |
| `gen-latin-ext-a.py` | regular, bold | base letter + accent lifted from the base font |
| `gen-circled-digits.py` | regular | a ring plus digits |
| `gen-arrows.py` | regular | hand-drawn parts, mirrored |
| `embolden.py` | bold | the **resolved** regular face |
| `slant-bdf.py` | italic | the **resolved** regular face |
| `slant-bold.py` | bold-italic | the resolved italic and bold faces |

**Derived faces consume the resolved regular face, not the raw one.** So
hand-drawing a regular glyph automatically improves its bold, italic and
bold-italic without anyone touching those faces. That is the main reason the
stack is worth building.

### Rules stay in code; shapes do not

`KEEP` and `TWIN` in `embolden.py`, and `PUNCT`, `LETTERS` and the
no-room-to-lean fallback in `slant-bdf.py`, are **policies about how to
derive**, not shapes. They stay in Python.

This still satisfies "changing a glyph shape needs no code change", because
the way to change a shape is to draw it, and a drawing outranks every rule.
Turning the rules themselves into data files is deliberately **not** done:
the override mechanism already covers the need, and a data file would be a
second way to express the same thing. Revisit only if it becomes real
friction.

## 7. Ragged coverage is a first-class state

A size with **zero** drawings still builds -- it comes out as plain upstream
Tamzen. A size with forty builds with forty extra glyphs. Nothing is ever
blocked on nobody having drawn `✦` at 5x9.

This is not a concession, it is the point. Full coverage of all seven sizes is
**1842 remaining hand drawings**; 506 of the 813 added glyphs per size are
generator output and cost code, not decisions. Ragged coverage turns that wall
into a queue, and the coverage table (§9) turns the queue into a recruiting
poster: someone who cares about 6x12 can see `6x12: 12 of 307` and go fill it.

**The layout is multi-size from day one and populated with 7x14 only.** The
size dimension costs nothing to add now and is a brutal retrofit once other
people have forks and open pull requests.

## 8. Build

`make` resolves the stack per `(size, face)`, emits a BDF, then an OTB through
the unchanged `fonttosfnt` + `repair-tamzen.py` path.

**The derived layer must be generated, never discovered.** Today the Makefile
finds bold sources with `$(wildcard glyphs-bold/*.txt)`; if that directory
were empty the bold face would silently build with upstream's 190 glyphs
instead of failing. Under this design `build/gen/**` is a make prerequisite,
so it cannot be silently absent.

`make watch` keeps watching directories rather than files, for the reason
already recorded: editors replace a file rather than writing into it, which
leaves a file watch pointing at the old inode.

## 9. Validation and index

CI checks, and `make check` runs locally:

* filename is uppercase hex, at least four digits, and parses to a codepoint
* the header line matches what `make headers` would write for that codepoint,
  including the two special cases in §4
* exactly *H* rows of exactly *W* characters from `.#`
* every built face passes `repair-tamzen.py` with no remaining defect
* glyph counts per face are equal across faces of a size

`make index` regenerates a coverage table per size and face -- total, hand,
generated, upstream, and what is missing. It is the contributor-facing view
and C will publish it.

## 10. Migration

One-time, and it must happen **before the repo goes public**.

1. Explode `glyphs/*.txt` into `glyphs/7x14/regular/<CP>.txt` (813 files).
2. Delete `glyphs-bold/` (9 files, 813 glyphs). All of it is reproducible;
   it becomes `build/gen/7x14/bold/`.
3. Move `upstream/Tamzen7x14?.bdf` to `upstream/7x14/`.
4. Rewrite the generators to emit per-glyph files into `build/gen/`.
5. Rewrite the merge step to resolve the stack.

**The block headers must survive.** `glyphs/extra.txt` carries the 7x14 grid
reference (baseline row 10, cap height rows 3..10, x-height rows 5..10, math
axis row 7) and `glyphs/dingbats.txt` carries the three geometry bands used in
that block. Per-size grid references move to `glyphs/<size>/README.md`, which
is the first thing anyone drawing at a new size needs. Block-specific
compromises are already documented in the top-level `README.md` and stay
there.

Expected diff: roughly 813 files added, 18 removed. Large, mechanical, and
verifiable.

**Acceptance test: whatever the build emits must be byte-identical before and
after, with exactly one permitted difference.** At migration time that is the
four `.otb` files; if B has already landed it is the `.ttf` files instead. The
glyph store must not change a single pixel.

That difference is `U+00A8 DIAERESIS` in the bold face -- the only codepoint
in the whole font where a generator's output overlaps a glyph upstream also
draws. `gen-latin-ext-a.py` emits it as a by-product of composing accents, and
it does not match: upstream puts the dots in columns 0-1 and 3-4, the
generated one in columns 1-2 and 4-5. Under §5 upstream wins and that glyph
reverts to Scott Fial's own drawing.

This is the rule in §2 working, not a regression, and it needs no exception in
the code. If the generated form is preferred after all, the answer is to draw
it: `glyphs/7x14/bold/00A8.txt` outranks both. That the fix for a disliked
precedence outcome is *a drawing* is the design working as intended.

## 11. What this settles for B

Recorded here so it is not rediscovered. B is out of scope, but the shape of
its output was decided while designing this, and it changed.

**The output is outline-only, one font file per strike.** Not the multi-strike
bitmap font with an outline fallback that was originally sketched.

### Why outlines, not strikes

* **Browsers do not render embedded bitmap strikes.** A specimen site loading
  a bitmap-only `.otb` shows nothing, so the site in D *requires* outlines.
* **fontconfig will not serve a bitmap-only font.**
  `/etc/fonts/conf.d/70-no-bitmaps-except-emoji.conf` rejects anything with
  `outline=false`, which is why `wezterm.lua` has to reach these fonts through
  `font_dirs`. An outline font works in every application.
* **The shared-metrics problem disappears.** A file holding several strikes
  has one set of scalable metrics, and the seven sizes do not share an advance
  ratio -- only 6x12, 7x14, 8x16 and 10x20 are exactly 1:2, against 0.5556 for
  5x9, 0.5385 for 7x13 and 0.5333 for 8x15. One file per strike makes the
  question moot.

Outlines could never have varied with size anyway. The only mechanism that
would -- a variable font's `opsz` axis -- needs interpolation-compatible
masters, and the same glyph at 5x9 and 10x20 is a different number of
rectangles in different places. Terminals do not apply `opsz` regardless.

### The em must be a whole number of pixels

This is what makes an outline *equivalent* to the bitmap rather than merely
similar. Set

    upem = cell_height x 64          one pixel = exactly 64 units

so every pixel edge is an integer coordinate:

| size | upem | advance |
|---|---|---|
| 5x9 | 576 | 320 |
| 6x12 | 768 | 384 |
| 7x13 | 832 | 448 |
| 7x14 | 896 | 448 |
| 8x15 | 960 | 512 |
| 8x16 | 1024 | 512 |
| 10x20 | 1280 | 640 |

At ppem equal to the cell height, a pixel edge at unit `k*64` maps to device
pixel `k` exactly -- no rounding, no antialiasing, indistinguishable from the
strike. The mapping is linear, so **every integer multiple is exact too**:
14px, 28px and 42px all land on the grid. Only sizes between multiples blur.
D should expose 1x, 2x and 3x for that reason.

Vertical metrics follow: ascent and descent are the cell's own rows times 64,
and they sum to upem by construction.

### The tracer, and the one hard case

Verified against all four faces, 4008 glyphs, before writing this: the filled
outline area equals the lit pixel count in **every** glyph, every segment is
axis-aligned, and the whole face costs about **22 points per glyph** (worst
case 132). These are very small fonts.

Each lit pixel contributes the edges that border an unlit pixel, directed so
the interior stays on one side; the edges are then walked into closed loops.

**The hard case is two pixels touching only at a corner.** That vertex has two
outgoing edges, so a naive point-keyed lookup loses one and the walk dies.
Resolve it by taking the sharpest right turn, which splits the boundary into
rectangles whose *union* is the same shape -- `o` comes out as four rectangles
rather than one pinched ring and fills identically under non-zero winding.
Do not try to make the contours minimal; correctness of the fill is what
matters, and the signed-area test above is what proves it.

### Format

Ship `.ttf` with `glyf` outlines -- pixel squares are all straight lines, so
TrueType is the natural fit and `fontTools`' pen API writes it directly. Add
`.woff2` for the site. Build with `fontTools` (a pip dependency) rather than
scripting `fontforge`, which is much harder to make reproducible in CI.

`repair-tamzen.py` becomes unnecessary for these files: its five fixes all
concern a strike disagreeing with the scalable metrics, and there is no longer
a strike. It stays in the tree for the `.otb` path if that is kept.

What is lost: crispness at *non*-multiple sizes, where a strike used to be
exact and an outline will antialias. Nothing real is given up, because wezterm
already only works at an exact ppem.

## 12. Naming

The font is renamed **Smalti**. Smalti are the small glass tiles a mosaic is
made from; a pixel is one.

### Why rename at all

The licence does not require it -- Tamsyn and Tamzen both grant "permission to
use, copy, modify, and distribute as you see fit", with no trademark clause.
Three other reasons do.

* **Precedent.** Tamzen is itself a rename: Suraj Kurapati forked Tamsyn and
  changed the name rather than shipping a different font under someone else's.
* **The family name is a collision.** This project already carries the warning
  "keep exactly ONE Tamzen size in the font directory, every size shares the
  family name". Anyone who installs upstream Tamzen alongside this one gets two
  families with the same name and wildly different coverage, resolved
  arbitrarily. A distinct name retires that permanently.
* **It is no longer Tamzen.** 1002 glyphs across four faces, including an
  oblique upstream never had.

### The size belongs in the family name

**Family name is `Smalti 7x14`, not `Smalti`.** This is the fix for the
collision above, applied to ourselves rather than only to upstream.

Each strike is its own file with its own metrics and its own design. If all
seven shared the family name `Smalti`, a font matcher would see twenty-eight
faces claiming four styles, and would pick among seven different designs
arbitrarily -- exactly upstream's bug, reproduced. Putting the size in the
family name gives each size a clean four-face family, and all seven can be
installed at once.

| name ID | value |
|---|---|
| 1 family | `Smalti 7x14` |
| 2 subfamily | `Regular` / `Bold` / `Italic` / `Bold Italic` |
| 6 PostScript | `Smalti7x14-Regular` |
| 16 typographic family | `Smalti` |
| 17 typographic subfamily | `7x14 Regular` |

IDs 16 and 17 let an application that understands them group all sizes under
one name, while IDs 1 and 2 stay unambiguous for the terminals that do not.
`wezterm.font('Smalti 7x14')`.

Files: `Smalti7x14-Regular.ttf`, `-Bold`, `-Italic`, `-BoldItalic`, plus
`.woff2` alongside for the site.

### What keeps the old name

`upstream/` keeps Tamzen's own filenames -- those files *are* Tamzen and must
stay recognisable as pristine upstream. `LICENSE.tamzen` stays. The name
table keeps the `(c) 2015 Scott Fial` notice and adds a copyright for this
work. The README states the chain plainly: **Tamsyn -> Tamzen -> Smalti**.

### Sequencing

**The rename is its own commit and must not be mixed with the migration in
§10.** That migration's acceptance test is byte-identical output; a rename
changes the name table, so the two would mask each other. Rename before or
after, never during.

## 13. Risks

* **A big mechanical diff.** Mitigated by the byte-identical acceptance test
  and by doing it while there is exactly one contributor.
* **1000 files per directory.** Fine for git and every modern filesystem;
  `ls` of a populated face is long. Accepted.
* **Losing the knowledge in the block headers.** Explicitly handled in §10;
  it is the part of the migration most likely to be done carelessly.
* **The repo has no remote.** Everything about contributors is blocked on
  that, and a disk failure currently costs the whole project.
