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

---

# Pass 5 — the 30 unanchored Greek

The other 30 of the `03xx` block: the ones the anchored pass (`5014099`) could
not resolve because nothing in the tree or upstream is byte-identical to them.

**The wide comparison returned almost nothing, and that is the finding.**  All
49 Greek drawings were compared against every glyph of all four upstream BDFs
(`7x14{r,b}`, `8x16{r,b}`) and every in-tree drawing at both sizes.  Upstream
carries **no Greek at all** — all four files stop at U+00FF.  Among the 30, the
only byte-identities that exist are the two `5014099` already named: `0398`≡
`03B8` and `03BC`≡`00B5`.  So the batch is genuinely unanchored: 30 freehand
redraws against upstream's neighbouring **Latin**, not ports.  The classifier
also ran: **all 30 are letter-box**, none cell-spanning (none lights both
column 0 and column 6 at 7x14).

## The descender line: row 14, not row 13

**The batch's single biggest call.**  Every descending Greek at 7x14 bottoms on
row 12.  Baseline-tracking alone (+1 row) would put them on row 13 at 8x16.
They are on **row 14**.

The census that decides it, over all four upstream BDFs:

| size | letter descenders bottom at | who else is down there |
|---|---|---|
| 7x14 | **split**: `g j ý þ ÿ ¡ ¿` on 12, `p q y , ; ¸ ç` on 13 | `( ) [ ] _ { } $ Q` also on 12 |
| 8x16 | **unified**: `g j p q y , ; ¸ ç ¡ ¿ ý þ ÿ` — all 15 on **14** | row 13 holds only `( ) / @ [ \ ] _ | ¦` |

Upstream merged both 7x14 families onto one line at 8x16, and moved `g` **two**
rows to do it.  The 7x14 Greek had followed `g`'s shallower depth.  At 8x16
there is no letter-shaped thing on row 13 — a Greek descender there would be
the only one in the font at that depth.  All nine descenders in this batch
(`β γ ζ η μ ξ ρ ς φ χ ψ`) therefore bottom on 14, three rows below the baseline,
exactly like `p`.

**Confirm this with fresh eyes.**  If it is wrong, eleven glyphs are wrong
together, and batch 10g's `00B5` inherits it.

## Three bowls that floated above the baseline at 7x14 now sit on it

`ρ`, `ς` and `φ` all close their bowl on row 9 at 7x14 — **one row above the
baseline** — with the stem starting at row 10.  `o`, `c`, `p`, `b`, `d`, `q` all
close on row 10 there.  The likely cause is arithmetic: at 7x14 only two rows
exist below the baseline, so a three-row stem had to start on it.

At 8x16 there are three rows below the baseline, so the compromise is not
forced.  `ρ` and `ς` now close on row 11 with `o`/`c`, and `φ`'s bowl is
centred on its stem as before.  Cost: `ρ`'s and `ς`'s bowls gained **two** rows
where everything else in the batch gained one.  It is a design change, not a
port, and it is the direct consequence of the descender ruling above.

## Distinctions the extra column changed

| what | at 7x14 | at 8x16 | note |
|---|---|---|---|
| `U+03C7` χ vs upstream `x` | 6 px apart (χ has a 1-row waist and a doubled leg row; `x` has a 2-row waist) | **3 px apart** — χ's body is now byte-identical to upstream 8x16 `x`, differing only by the descender | 7x14's difference reads as a compromise (χ needed its leg at column 1 by row 11 to start the tail), not a deliberate distinction. `x` at 8x16 already has the 1-row waist χ wanted. **Separation went DOWN. Worth a second opinion.** |
| `U+03C9` ω vs upstream `w` | 2 px apart | **6 px apart** | ω's rows 5–9 are byte-identical to `w` at *both* sizes; only the closing differs. At 7x14 ω closes in one row with 1 px feet; at 8x16 the three stems sit 3 columns apart instead of 2, so a 1 px foot can no longer bridge them and the close takes two rows. A §4.1 lift, but it was forced by geometry, not chosen. |
| `U+03BE` ξ's two waves | upper wave 2 rows, lower wave **1** row — visibly lopsided | both waves 2 rows | A clean §4.1 lift: the extra row went exactly where 7x14 had run out. |
| `U+0398` Θ / `U+03B8` θ bar | row 6 of the 3–10 body: 2 side rows above, 3 below | row 7 of the 3–11 body: **3 above, 3 below** | 8x16's 7 interior rows have a true centre; 7x14's 6 did not. |

## Θ and θ are still byte-identical

The hard constraint from `5014099` is held: `0398` and `03B8` are the same
bytes, as at 7x14.  The extra column would now permit them to differ (a
lowercase θ could take a shorter bowl), but that would invent a distinction the
7x14 face does not draw, so it was not acted on.  **Recorded as an open
question, not a decision.**

## Drawing μ has fixed `U+00B5` — but 00B5 is not in this commit

`03BC` is byte-identical to in-tree `00B5` MICRO SIGN at 7x14.  `00B5` belongs
to batch **10g** and is still absent at 8x16.  Whoever draws 10g must copy
`glyphs/8x16/regular/03BC.txt` verbatim rather than redraw it, or the identity
breaks.  Upstream carries `00B5` at neither size, so there is no other anchor.

## Deviations from the batch brief, kept on purpose

| glyph | what | the measurement |
|---|---|---|
| `U+039B` Λ | 7x14 draws a **2-row 1 px apex**; 8x16 uses a **1-row 2 px apex** over a 3-row taper | At 8 columns the apex must be 2 px wide (there is no centre column — in-tree `0394` Δ and upstream `A` both use `...##...`). Holding 7x14's 2-row apex would make a 2×2 block, which reads blunt, not pointed. The taper was lengthened to 3 rows instead, so Λ stays pointier than Δ exactly as it is at 7x14 — the distinction moved rather than being dropped. |
| `U+03A6` Φ, `U+03A8` Ψ, `U+03C6` φ, `U+03C8` ψ | drawn in columns **1–7**, not the 1–6 letter box | Each has a centred vertical stem, which README rule 1 puts on column 4. A 1–6 box gives that stem counters of 2 and 1 — visibly lopsided inside one glyph. 1–7 gives 2 and 2. This is what upstream does for its own centre-stem forms (`m`, `w`, `x` are 1–7), and what the committed `03A4` Τ, `03A5` Υ, `03A7` Χ already do. |
| `U+03C4` τ | bar on columns 1–6, stem on column **4** — 3 columns left of it, 2 right | Not centred, deliberately. 7x14 τ puts its foot's right end exactly under the bar's right end; stem 4 + foot 5–6 + bar 1–6 preserves that, stem 3 + foot 4–5 does not. Upstream's own `t` leans the other way by the same one column (stem 3 in a 1–6 bar), so a lean is house style; only the direction differs. |

## Drawings the implementer distrusts — pass 5

| glyph | what is wrong |
|---|---|
| `U+03B3` γ | **The weakest drawing in the batch, and the one most wanted for a second opinion.** Its body is byte-identical to upstream 8x16 `v` (as it is to `v` at 7x14 — a measured anchor, and it keeps γ and the committed `03BD` ν differing only by the tail). But `v` ends **2 px wide** at 8x16 where it ended 1 px at 7x14, so γ's tail has to narrow from 2 px to 1 px right at the baseline, and it drops from the *right* half of the V's point. Every other descender in the font is 1 px the whole way. The alternative — rebuilding γ on `x`'s geometry (columns 1–7 converging to a 1 px point) — gives a clean tail but throws away the `v` anchor and makes γ wider than ν. The implementer would not defend this trade hard. |
| `U+03BA` κ | The lower arm's terminal is a 3 px blob (`.#..###.`) where 7x14's is 2 px. The upper arm now runs 4 rows against the lower arm's 2, where 7x14 is 3 against 2 — the arm had to start at column 6 to fill the wider box, and stepping one column per row to the junction takes four rows. It reads slightly top-heavy. |
| `U+03B9` ι | The stem stays on column 2 (7x14's left edge, per README rule 2) while the foot and its terminal curl widen right, so the gap between stem and terminal grew from 2 columns to 3. At 10 px of ink it is the lightest glyph in the batch and it now looks a little sprawled for its weight. |
| `U+03A6` Φ / `U+03C6` φ | 24.2% and 21.9% ink — the densest in the batch, and their two full-width `.#######` bars embolden to a solid `########`, an entirely filled row. Faithful to 7x14 (24.5% / 20.4%) and the gate is green at every face, but they are the two glyphs most likely to read as blobs at 1x. |
