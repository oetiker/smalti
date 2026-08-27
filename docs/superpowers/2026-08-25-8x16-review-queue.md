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

## The quote ornaments' height — measured evidence against them

`U+275B` `U+275C` `U+275D` `U+275E` (high) and `U+275F` `U+2760` (low) were
grown from 4 rows to 5, following the project's default: top fixed, bottom
grown one row **to the new baseline**.

**Upstream answers this question differently for the same kind of mark, from
the same starting band.**  Measured from both upstream BDFs:

| glyph | 7x14 band | 8x16 band | rows |
|---|---|---|---|
| upstream `'` | rows 2–5 | rows 1–4 | 4 → **4** |
| upstream `"` | rows 2–5 | rows 1–4 | 4 → **4** |
| upstream `,` | rows 9–13 | rows 10–14 | 5 → **5** |
| our `275B`–`275E` | rows 2–5 | rows 2–6 | 4 → **5** |
| our `275F`/`2760` | rows 8–11 | rows 8–12 | 4 → **5** |

Upstream's `'` and `"` start at *exactly* the same band as ours and keep their
row count, moving **up** instead of growing down.  Its `,` likewise keeps five
rows and shifts.  A floating mark never touches the baseline, so "grown to the
new baseline" arguably does not apply to it at all.

The implementer named this as their weakest call and asked for it to be looked
at.  The result is a fat 5-row wedge where upstream would have drawn a 4-row
mark one row higher.  **Six glyphs turn on this.**

Not a strict rule violation: none of the six is byte-identical to an upstream
glyph, so the anchor rule does not formally reach them.  It is the *kind*
evidence that is strong.

## Drawings the implementer distrusts — pass 3

| glyph | what is wrong |
|---|---|
| `U+2762` HEAVY EXCLAMATION MARK ORNAMENT | Given a 4-column stem at columns 2–5 so it matches `2763`, whose heart is cell-spanning and centres on 3.5 — a column-4 stem overhung the heart's tip and read as broken.  But `2762` **alone** has no reason to leave the column-4 stem axis, and it is now a 4×6 block: +4.2 density points, the largest jump in the batch.  This also leaves two centring rules unreconciled inside one batch — bars on column 4, exclamations on 3.5 — the same situation `271A` versus `271B`/`271D` produced in pass 1. |
| `U+2761` CURVED STEM PARAGRAPH SIGN ORNAMENT | Freehand: upstream carries no `¶` at either size, so there is no anchor of any kind.  The bowl interior was widened from 1 column to 2, and the two descenders at columns 4 and 6 with a single-column gap read mechanically rather than drawn. |
| `U+2767` ROTATED FLORAL HEART BULLET | Now has exactly the same ink count as `U+2766` (22), where at 7x14 they were 18 against 17.  `2765` **is** a true 90° rotation of `2764` and that was preserved; `2767` is **not** a rotation of `2766`, and that asymmetry is inherited from 7x14 rather than introduced.  Second opinion, not a redraw. |

## The bars now stand taller than the brackets

`U+2758`/`U+2759`/`U+275A` sit at rows 1–13; the twelve bracket ornaments sit
at rows 2–13.  At 7x14 the bars were **shorter** than the brackets, so the
relationship is inverted.

This is not a mistake and not a free choice: `2758` is byte-identical to
upstream's 7x14 `|`, so it is drawn as upstream's 8x16 `|`, and upstream grew
`|` from 10 rows to 13 while growing `(` from 11 to 12.  **The inversion is
upstream's own.**  Listed only so it is confirmed deliberately rather than
discovered later.

## The arrows sit one row above everything drawn before them

All 39 dingbat arrows hold their 7x14 rows.  Passes 1–3 — the crosses, stars
and ornaments — were baseline-tracked and grew a row.  So this batch sits one
row **above** them.

**This is the documented rule, not a choice made in the batch.**
`glyphs/8x16/README.md`, "The row-7 maths axis", names arrows outright: any
new glyph that joins a formula — comparison operators, *further arrows*,
anything meant to line up with `+`/`-` — belongs on that axis, not on a
baseline-relative row.  The 92 generated arrows already obey it at 8x16.

It is listed here anyway because it is the largest single judgement in the
batch and it is visible: two neighbouring families now sit on different rows.
Upstream is split the same way (`-` `*` `+` `<` `>` axis-locked; `=` `A` `U`
baseline-tracked), so the split is real rather than an artefact — but it
should be confirmed with fresh eyes rather than inherited silently.

Holding the axis is also what kept the batch light.  A grown band would have
had no centre row, so ruling R21 would have doubled every horizontal shaft
from one row to two and collapsed five light/heavy pairs into each other
(`279D`/`279E`, `279F`/`27A0`, `27B5`/`27B8`, `27BA`/`27BB`, `27BC`/`27BD`).

## Drawings the implementer distrusts — pass 4

| glyph | what is wrong |
|---|---|
| `U+27A2` / `U+27A3` 3-D lighted arrowheads | **The one most wanted for a second opinion.**  To separate them the implementer removed a pixel from the head's **silhouette**, where 7x14 removed only an **interior** pixel.  The head now reads slightly chipped rather than lit, and leaves a near-isolated pixel.  The faithful alternative puts them back 2 px from each other and 1 px from plain `27A4`.  Separation was chosen over silhouette; the implementer says they would not defend that trade hard. |
| `U+2799` HEAVY RIGHTWARDS ARROW | Correct by the classifier and faithful to 7x14, and it still **looks like a bug**: a *heavy* rightwards arrow that stops one column short of the cell edge, sitting beside `27A1` which does not.  A run of `2799` therefore has a one-column seam.  Inherited from 7x14, where the same shortfall exists.  Fixing it at **both** sizes would be equally defensible and is not the implementer's call.  `279C`, `279D` and `279F` share the shortfall. |
| `U+27B4` / `U+27B6` feathered arrows | The extra column bought a fourth feather pixel, landing right where the arrowhead begins.  It reads as a clean parallel feather — but it is the one place in the batch where a feature was **added** rather than ported, and at this density a fourth stroke could read as clutter. |
| `U+27B2` CIRCLED HEAVY WHITE RIGHTWARDS ARROW | The batch's only horizontal-parity glyph.  A 1-column gap is kept between the interior head and the ring, which leaves the interior arrow centred on column 3 while the ring centres on 3.5.  Faithful to 7x14 and deliberate, but it is an asymmetry inside a single glyph. |

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

**Pass 3 produced the same shape of problem.**  `U+274F`/`U+2751` and
`U+2750`/`U+2752` are 2 px apart at *both* sizes.  Those two pixels are the
whole drop-shadowed / shadowed distinction — whether the shadow is detached at
the corners or attached.  Separating them further would invent a difference
Unicode does not draw.  Same decision as the star pairs above.

**Pass 4 has nine such pairs, and six are one family.**  `27A9` `27AA` `27AB`
`27AC` `27AD` `27AE` `27BE` are seven outlined arrows whose only difference is
which edge carries a shadow.  The outline alone costs 18 px of the cell,
leaving 3–4 px to distinguish "right-shaded" from "lower-right-shadowed" from
"open-outlined".  A fatter drop shadow on `27AD` was tried: it separated
`27AD`/`27BE` and collided with `27A9` instead, and was reverted.  The
remaining three are `279D`/`279F` (solid shaft against dashed shaft over a
4-column shaft — the arithmetic minimum), `27A0`/`27A4` and `27A2`/`27A4`.

Set against that, the extra column **did** lift five pairs in this batch,
including `279E`/`27A0` from 2 px to 14 and `27A2`/`27A3` from 2 px to 4.

## Deviations from an instruction, kept on purpose

| glyph | what |
|---|---|
| `U+2722` FOUR TEARDROP-SPOKED ASTERISK | Drawn at rows 4–10, not the rows 5–10 the batch brief specified.  **The reason is decisive: the 7x14 drawing is byte-identical to upstream's own 7x14 `+`, and the 8x16 drawing is byte-identical to upstream's own 8x16 `+`** (both verified by comparison, not by eye).  Upstream answered this exact question for this exact shape.  The instructed band would have forced either a two-row bar — 38% *heavier*, the opposite of its intent — or a stem with two arms above and three below.  Recommended: accept. |
