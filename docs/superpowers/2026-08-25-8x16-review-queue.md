# 8x16 — glyphs held back for a final look

Every drawing in `glyphs/8x16/regular/` has passed `make check` and been
committed.  This file lists the ones **someone is not happy with**, so they can
be judged together at the end of the branch instead of one batch at a time.

Being on this list does not block anything.  A glyph is here because the
implementer or the controller distrusted it, or because a decision was made
that has a visible cost and someone should confirm it with fresh eyes.

**Delete this file before the branch merges.**  Anything still unresolved at
that point is either accepted or becomes an issue — it must not ship as a
silent open question.

Compare each entry against its 7x14 original in `build/compare/index.html`
(`make compare` regenerates it).

---

## Decisions with a visible cost

These were ruled on, or follow directly from a ruling.  They are listed so the
cost can be re-examined once the whole set exists and can be judged together.

| glyph | what | why it is here |
|---|---|---|
| `U+271A` ✚ HEAVY GREEK CROSS | 75% ink, up from 67% at 7x14 | Ruling R21.  The 2+4+2 arms are the only symmetric option that still reads "heavy"; 3+2+3 is too light.  It reads closer to a blob than a cross.  **This is the precedent every other heavy symmetric glyph follows**, so if it is wrong, several are wrong. |
| `U+2738` HEAVY EIGHT POINTED RECTILINEAR BLACK STAR | 75% ink | The worst case of R21 in pass 2.  Reads as a fat plus rather than a star.  Same complaint `271A` drew. |
| `U+273F` BLACK FLORETTE | 75% ink | Already 75.5% at 7x14, so it did **not** grow — listed only because it sits at the ceiling and should be judged beside `271A` and `2738`. |
| `U+2746` HEAVY CHEVRON SNOWFLAKE | 75% ink | Third glyph at the ceiling, 67% → 75%. |
| `U+25B4` / `U+25BE` | kept 3 rows while the rest of their batch grew to 8 | Ruling R19.  At 6 columns wide, 2,4,6 is the only clean triangle.  Cost: their centre sits half a row above the small squares', where at 7x14 the two matched exactly. |

## Drawings the implementer distrusts

| glyph | what is wrong |
|---|---|
| `U+2711` ✑ WHITE NIB | Named the weakest drawing in pass 1 when it was handed over, and accepted as drawn.  A thin outline whose right edge steps out to column 6 and back. |
| `U+2740` WHITE FLORETTE | **The one most wanted for a second opinion.**  Not weight — rhythm.  At 7x14 the petal seams alternate cleanly; at 8x16 the middle seam doubles, so it is visibly twice as thick as the two either side.  An odd number of seam rows cannot stay odd at even height. |
| `U+2735` / `U+2743` | Each ends with a 3-column spoke where its neighbouring spokes are 2, because the source's 2-wide feature straddled column 3.  Slightly lumpy.  Rotational symmetry holds. |
| `U+2736` / `U+2737` | Identical ink counts (40/64) and near mirror-images of each other.  Inherited from 7x14 (27 vs 25 there), not introduced here, and they sit 12 px apart — well outside the tight band. |

## Distinctions the extra column did not lift

`docs/superpowers/specs/2026-08-25-8x16-design.md` §4.1 says a 7x14 compromise
should be lifted where the extra room permits.  Seven cramped pairs did open —
`273B`/`273C` went from **one** pixel of difference to four, and `2744`/`2745`,
`2726`/`2747`, `2733`/`273B` all went from two to four.  Two pairs did not:

| pair | at 7x14 | at 8x16 |
|---|---|---|
| `U+2605` BLACK STAR / `U+272E` HEAVY OUTLINED BLACK STAR | 2 px apart | still 2 px apart |
| `U+2606` WHITE STAR / `U+2729` STRESS OUTLINED WHITE STAR | 2 px apart | still 2 px apart |

In both, the whole difference lives in **one row** — the leg row, `.#....#.`
against `##....##`.  Rows 4–10 are identical.  Centre doubling cannot help,
because the difference is not in the centre.

**This is a decision, not a redraw.**  Lifting it means giving the two
"outlined" variants a genuinely different silhouette — the proposal on the
table is a three-row leg splay (rows 9–11) against the plain stars' two.  The
alternative is to accept that the distinction stays as thin at 8x16 as it was
at 7x14.

## Deviations from an instruction, kept on purpose

| glyph | what |
|---|---|
| `U+2722` FOUR TEARDROP-SPOKED ASTERISK | Drawn at rows 4–10, not the rows 5–10 the batch brief specified.  **The reason is decisive: the 7x14 drawing is byte-identical to upstream's own 7x14 `+`, and the 8x16 drawing is byte-identical to upstream's own 8x16 `+`** (both verified by comparison, not by eye).  Upstream answered this exact question for this exact shape.  The instructed band would have forced either a two-row bar — 38% *heavier*, the opposite of its intent — or a stem with two arms above and three below.  Recommended: accept. |
