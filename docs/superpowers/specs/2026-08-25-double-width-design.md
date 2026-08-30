# Smalti double-width glyphs — design

Status: draft for review
Date: 2026-08-25
Target release: 0.3.0 (NOT 0.2.0 — see §12)

## 1. What ships

Sixty-two glyphs that occupy **two terminal cells** instead of one, drawn at
**both cell sizes** — 14x14 at 7x14 and 16x16 at 8x16, each a perfect square.
They are the emoji-width symbols Smalti has been deliberately stepping over
since it started.

That is **124 hand drawings**.  The set is 62 codepoints; every one is drawn
twice, because a pixel drawing does not scale between cell sizes — the same
reason the 8x16 release redraws rather than derives.

## 2. Why this is possible at all, and what it cannot do

**A terminal allocates cells from Unicode, not from the font.**  This project
already knows that — `tools/build-site.py:113` says so:

> `east_asian_width 'W'` means the terminal gives the character two cells

That single fact defines the whole feature:

* For a character Unicode calls **Wide (W)** or **Fullwidth (F)**, the terminal
  has ALREADY reserved two cells.  A one-cell glyph there is wrong, which is
  why Smalti refuses to draw them today.  A two-cell glyph is **correct**.
* For every other character, a two-cell drawing would **overlap its
  neighbour**.  The terminal handed out one cell and will not be argued with.

So "arbitrary double-width glyphs" is not a feature that exists.  What exists
is *drawing correctly the characters that were already double-width*.

**The doubled cell is square at both sizes** — 14x14 at 7x14, 16x16 at 8x16 —
because both cells are exactly 1:2.  That is a consequence of the aspect ratio,
not a coincidence, and 16x16 is the classic CJK cell.

## 3. The candidate set: 62 glyphs, enumerated not estimated

Every East Asian Wide or Fullwidth codepoint inside the blocks Smalti already
draws from:

| block | count | examples |
|---|---:|---|
| `26xx` Miscellaneous Symbols | 31 | `U+2614 U+2615 U+2648` |
| `27xx` Dingbats | 15 | `U+2705 U+270A U+2728` |
| `23xx` Miscellaneous Technical | 10 | `U+231A U+231B U+23E9` |
| `2Bxx` Arrows and shapes | 4 | `U+2B1B U+2B50 U+2B55` |
| `25xx` Geometric | 2 | `U+25FD U+25FE` |
| **total** | **62** | |

Zero of Smalti's existing hand drawings are W or F — verified.  The project has
obeyed its own rule strictly, so this set is exactly the gap that rule created.

## 4. The store: width comes from Unicode, not from a flag

**A double-width drawing is a file of 16 rows of 16 characters, in the same
directory as every other glyph.**  No new directory, no marker in the header, no
per-glyph configuration.

The expected width is *derived*:

```python
def glyph_width(cp, cell_w):
    return cell_w * 2 if unicodedata.east_asian_width(chr(cp)) in ('W', 'F') else cell_w
```

This is the design's one real idea, and it earns three properties for free:

1. **It cannot be set wrong.**  There is no flag to disagree with reality.  The
   file's width is a fact about the codepoint, and Unicode is the single source.
2. **It self-validates.**  A 16-wide file for a narrow codepoint is an error,
   and so is an 8-wide file for a wide one.  `read_glyph()` already raises
   `GlyphError` on a row of the wrong length; it simply needs to be told the
   right length.
3. **It matches how the project already thinks.**  `east_asian_width` is
   already the authority for what may be drawn; this makes it the authority for
   how wide, which is the same question answered once.

## 5. What has to change

| file | change |
|---|---|
| `tools/glyphstore.py` | `read_glyph()`/`read_dir()` take the per-glyph width from §4 rather than the cell width; `resolve()` carries it |
| `tools/build-face.py:124` | `DWIDTH {w} 0` becomes the per-glyph width.  **This is the single blocking line today** |
| `tools/check-glyphs.py` | validate against the per-glyph width |
| `tools/build-site.py` | render a wide glyph in a two-cell tile |
| `tools/build-compare.py` | same, so the chart stays honest |

**`tools/trace-outline.py` needs nothing.**  It already reads per-glyph `DWIDTH`
(line 135) rather than assuming one advance, so the outline path is ready.  That
is a genuine piece of luck and should be confirmed early rather than assumed.

The generators need nothing: none of them emits a wide codepoint.

## 6. The emboldening and shear rules

`tools/weight.py` derives its mask from a width that is now per-glyph rather
than per-face — `set_width()` must be called per glyph, not once per run.  This
is exactly the trap the 8x16 work hit twice (`weight.py`'s frozen `0xFE`, and
`slant-bdf.py`'s import-time `PAD_MASK`): **a correct formula evaluated before
the value it depends on is known is still a hardcoded constant.**

The oblique is the open question of §11.

## 7. Checks

* `check-glyphs` must reject a drawing whose width disagrees with its
  codepoint's East Asian width, in both directions.
* `check-outlines` must confirm a wide glyph's advance is exactly `2 * cell_w *
  64` units, and that it rasterises to the drawn pixels at the same ppem set as
  everything else.
* The fault-injection suite gains cases for both width errors.  Each must be
  confirmed to trip its own rule — remove the rule, confirm only that case
  flips.
* `docs/coverage.md` gains a wide column, so a partially-drawn wide set cannot
  read as complete.

## 8. Risks

1. **A monospace font with mixed advances may confuse consumers.**  Some
   terminals, and some of fontconfig's own heuristics, assume a monospace face
   has ONE advance and derive the cell from it.  A face carrying both 8 and 16
   could be mis-measured, or the wide glyphs silently squashed into one cell.
   **This is the risk that could kill the feature, and it must be settled by
   experiment before any drawing happens** — see §10.
2. **`east_asian_width` changes between Unicode versions.**  A codepoint that
   is Wide today may not be tomorrow, which would silently change a glyph's
   expected file width and break the build.  Pin the behaviour to the running
   Python's `unicodedata` and record the Unicode version in the build, so a
   change is loud.
3. **Ambiguous (`A`) characters are NOT included** and must not be.  They are
   narrow in a Western terminal and wide in an East Asian one, so no single
   drawing is correct.  `U+26F6` is one such, and it is being drawn
   single-width for exactly this reason.

## 9. Non-goals

* **No CJK.**  This is 62 symbols, not an ideograph set.  The blocks Smalti
  covers, and nothing else.
* **No Ambiguous-width characters.**  §8 risk 3.
* **No change to how narrow glyphs work.**  Every existing drawing keeps its
  meaning and its file, byte for byte.

## 10. Prove it works before drawing anything

The first task of implementation is a **spike, not a drawing**: hand-build a
face containing ONE wide glyph, install it, and look at it in wezterm and one
other terminal.  **Do this at 7x14 FIRST**, then 8x16 — the narrower cell is
the more likely to be mis-measured, so a failure shows up there soonest.

If a mixed-advance monospace face is mis-measured (§8 risk 1), the feature is
dead and 124 drawings would have been wasted.  That is well over a week of the
owner's judgement; the spike is an hour.  **Do not invert that order.**

## 11. Open decisions

1. **Which cell sizes — DECIDED 2026-08-25: BOTH.**  The owner ruled against
   the provisional 8x16-only scope.  So 0.3.0 is 124 drawings, not 62.

   The consequence to plan around: the spike of §10 must clear BOTH sizes
   before drawing starts, not just 8x16.  A mixed-advance face is a risk per
   size, and 7x14's narrower cell is the more likely of the two to be
   mis-measured, so it is the one to test first.
2. **Whether wide glyphs lean in the oblique faces.**  A 16-wide glyph has
   twice the horizontal room, so the same 2-pixel lean reads as half the slope.
   Options: same absolute lean, same visual slope (4 px), or no lean at all —
   emoji-like symbols arguably should not lean. Bring as a rendered comparison.
3. **Whether the bold face widens them.**  A filled 16x16 symbol has no stems
   to widen, and `weight.py` already leaves shapes, braille and dingbats
   identical for exactly that reason.  Extending that list is likely right.

## 12. Why this is 0.3.0 and not 0.2.0

0.2.0 already has 331 hand drawings ahead of it.  Adding a second axis of change
mid-flight is how a branch stops converging.  The 8x16 work has reached the
point where everything mechanical is done and only drawing remains — that is the
worst possible moment to widen scope.

This spec exists now so the idea does not evaporate, not so it can start now.
