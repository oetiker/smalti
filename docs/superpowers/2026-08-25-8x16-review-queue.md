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
`03B8` and `03BC`≡`00B5`.  The classifier also ran: **all 30 are letter-box**,
none cell-spanning (none lights both column 0 and column 6 at 7x14).

**Correction, added after the batch was first written.**  "Genuinely
unanchored" was the conclusion of a byte-identity sweep, and byte-identity is
the wrong test for a letterform.  Allowing a **vertical flip** finds two
distance-0 anchors the sweep could not see:

| glyph | anchor at 7x14 | Hamming |
|---|---|---:|
| `U+0393` Γ | `vflip(` upstream 7x14 `L)` | **0** |
| `U+039B` Λ | `vflip(` upstream 7x14 `V)` | **0** |

and a third at distance 2, closer than anything the sweep reported:

| `U+0398` Θ | upstream 7x14 `8` (its waist opened to a full bar) | **2** |

So three of the seven capitals were determined, not designed.  Γ and Θ were
drawn correctly anyway — Γ came out byte-identical to `vflip(` upstream 8x16
`L)` and Θ byte-identical to upstream 8x16 `8` with row 7 opened, both by
independent reasoning.  Λ did not; see the ruling below.

**The lesson for the remaining blocks: search flips and rotations, not only
byte-identity.**  A pixel letterform's nearest relative is often a reflected
one, and the sweep that reports "nothing" is only reporting nothing *of the
kind it looked for*.

## The descender line: row 14, not row 13

**The batch's single biggest call.**  Every descending Greek at 7x14 bottoms on
row 12.  Baseline-tracking alone (+1 row) would put them on row 13 at 8x16.
They are on **row 14**.

**Upstream splits its descenders by POPULATION, not by depth.**  At 8x16 every
letterform — `g j p q y , ; ¸ ç ¡ ¿ ý þ ÿ`, 15 glyphs — bottoms on **14**, and
row 13 holds only brackets and rules: `( ) / @ [ \ ] _ | ¦`.  At 7x14 the
letterforms were themselves split (`g j ý þ ÿ ¡ ¿` on 12, `p q y , ; ¸ ç` on
13) and upstream merged them at 8x16, moving `g` **two** rows to do it.  Greek
are letterforms, so they join the letterform line.

Two facts that must be recorded rather than discovered later:

* **These are the first ink on row 14 anywhere in the 8x16 hand tree.**  Before
  this batch the floor was row 13, and all sixteen glyphs there (`2758`–`275A`,
  `2763`, `2768`–`276D`, `2770`–`2775`) are ornamental brackets and a heart —
  upstream's *13-population*, so they are not counter-evidence.  Twelve glyphs
  now sit on 14: the eleven Greek descenders plus `00B5`.
* **12 → 14 is a +2 move, and README rule 4 does not describe it.**  Rule 4's
  baseline-tracking is about the ascent band.  Below the baseline the rule has
  to be "match upstream's 8x16 letterform descender line", which is a different
  statement.  Worth adding to the README if this survives review.

## Bowls that close ABOVE the baseline: ρ, ς and φ keep their own construction

`ρ`, `ς` and `φ` all close their bowl on row 9 at 7x14 — **one row above the
baseline** — where `o c p b d q` close on it.  A first draft of this batch read
that as forced arithmetic and moved all three onto the baseline.  **That was
wrong and it has been reverted.**  ρ against upstream `p` is Hamming **11** at
7x14: it is a different construction (a bowl that closes early, then a separate
leg on column 1), not a compromised `p`.  Flattening it onto the baseline
narrowed ρ-to-`p` from 11 to 5 — inventing a resemblance the face does not
draw.

All three now grow by exactly one row in each part, which is the conservative
port: bowl rows 5–10, leg or tail rows 11–14.  Only the *descender depth* comes
from `p`.

## Derived distances, before and after

Ten of the 30 are near-determined: they are some upstream or committed glyph
plus one feature.  Those distances are the thing to preserve, and all of them
now are — every `+1` below is a descender that gained a row, which is the
arithmetic minimum:

| pair | 7x14 | 8x16 | |
|---|---:|---:|---|
| υ / committed `222A` | 2 | 2 | υ = 222A minus its top row |
| σ / committed `03BF` ο | 2 | 2 | ο with the top bar run out to column 7 |
| Θ / upstream `8` | 2 | 2 | `8`'s outline, waist opened to a full bar |
| ε / upstream `c` | 2 | 3 | `c` + one bar |
| γ / committed `03BD` ν | 2 | 3 | ν + tail |
| η / upstream `n` | 2 | 3 | `n` + right stem |
| β / committed `0392` Β | 3 | 4 | Β, top-left opened, + tail |
| Λ / committed `2227` ∧ | 1 | 2 | see the Λ ruling below |
| ρ / upstream `p` | 11 | 10 | **not** a derivation — only the descender depth is shared |
| ω / upstream `w` | 2 | **6** | the one that could not be held — see below |

## Distinctions the extra column changed

| what | at 7x14 | at 8x16 | note |
|---|---|---|---|
| `U+03C9` ω vs upstream `w` | 2 px | **6 px** | **The one distance that could not be preserved, and the reason is geometric.** ω's rows 5–9 are byte-identical to `w` at both sizes; only the closing differs. At 7x14 `w`'s three stems sit 2 columns apart, so a single 1 px foot bridges each pair diagonally and ω closes in one row. At 8x16 upstream's own `w` puts its stems 3 columns apart (1, 4, 7) and **a 1 px foot can no longer touch both sides** — holding d=2 leaves the outer strokes dangling. The close therefore takes two rows. Forced, not chosen. |
| `U+03C7` χ vs upstream `x` | 9 px | **3 px** | χ's body is now byte-identical to upstream 8x16 `x`, differing only by the descender. 7x14's gap reads as a compromise (χ needed its leg on column 1 by row 11 to start the tail) and 8x16 `x` already has the tight waist χ wanted — but **the separation went DOWN and that deserves a second opinion.** |
| `U+03BE` ξ's two waves | upper 2 rows, lower **1** — visibly lopsided | both 2 rows | A clean §4.1 lift: the extra row went exactly where 7x14 had run out. |

## Vertical parity: the bands gained a centre the columns lost

The cap band 3–11 is **9 rows — odd, true centre row 7**.  The x-height band
5–11 is **7 rows — odd, true centre row 8**.  Both gain a centre that 7x14's
even bands lacked, at the same time as the columns lose theirs (7 → 8).  The
committed batch already proves the cap case: **Β and Ε both moved their middle
bar from row 6 to row 7.**

Placed on row 7 accordingly: Θ/θ's crossbar, Ξ's middle bar, Φ's bowl centre,
β's waist, and **Ψ's arm junction** — the last also independently confirmed by
upstream `Y`, which between sizes held its arms at 2 rows and grew its *stem*
from 4 to 5.

**ε and ψ are on row 8, not 7, because they live in the x-height band.**  That
is the choice this section exists to flag: do not apply one centre number to
both bands.  ε's bar on row 8 also matches upstream's own 8x16 `e`.

**`U+039E` Ξ's middle bar is the parity casualty.**  At 7x14 it is 3 px wide
centred on the true centre column 3.  At 8 columns nothing odd-width centres on
3.5, so it is drawn 4 px (columns 2–5).  2 px would be 33% of the letter box
against 7x14's 60%; 4 px is 67%.  Same class of problem as `2740` above.

## Θ and θ are still byte-identical

The hard constraint is held: `0398` and `03B8` are the same bytes, as at 7x14.
The extra column would now permit them to differ; that would invent a
distinction the 7x14 face does not draw, so it was not acted on.  **Recorded as
an open question, not a decision.**

## Deviations from the batch brief, kept on purpose

| glyph | what | the measurement |
|---|---|---|
| `U+03A6` Φ, `U+03A8` Ψ, `U+03C6` φ, `U+03C8` ψ | drawn in columns **1–7**, not the 1–6 letter box | Each has a centred vertical stem, which README rule 1 puts on column 4. A 1–6 box gives that stem counters of 2 and 1 — lopsided inside one glyph; 1–7 gives 2 and 2. Upstream does this for its own centre-stem forms (`m w x` are 1–7) and the committed `03A4` Τ, `03A5` Υ, `03A7` Χ already do. |
| `U+03C4` τ | bar on columns **1–6**, not 1–7, with the stem on column 4 | **The brief asked for 1–7, on the grounds that a 1–6 τ bar under the committed 1–7 Τ bar breaks the pair. Upstream draws exactly that pair itself:** its `T` bar is 1–7 and its `t` bar is 1–6. A lowercase bar narrower than its capital's is the house pattern, not a break. Stem on 4 (not upstream `t`'s 3) because at 7x14 τ's stem sits one column right of `t`'s, and because only stem 4 + foot 5–6 puts the foot's right end under the bar's right end, which is what 7x14 draws. |
| `U+03B4` δ | bowl top on row **6**, where its `8` anchor would put it on row 7 | δ is `8` with its top-left opened (Hamming 5 at 7x14), and 8x16 `8` moved its waist from row 6 to row 7. But `8`'s waist moved because *two* bowls must share 9 rows; δ has one bowl and a flag, so it is not under that constraint. README rule 4 says the top holds and the bottom follows the baseline, which keeps δ's bowl at rows 6–11 — one row shorter than `o`, exactly as at 7x14. |
## RULED: `U+039B` Λ was re-cut to its anchor — the owner may want to overrule

Λ was first drawn freehand with a **1-row 2 px apex over a 3-row taper**, on
the reasoning that 7x14's 2-row apex becomes a 2×2 block at 8 columns and
"reads blunt, not pointed", with the pointier-than-Δ distinction moved into a
longer taper instead.  That is a coherent argument and it was made without
knowing an anchor existed.

It has been replaced by `vflip(` upstream 8x16 `V)` placed on rows 3–11, which
is what the 7x14 Hamming-0 relationship to `V` requires, and which is how the
other 22 anchored glyphs in this block were decided.  Measured consequences:

| | freehand version | anchored version | at 7x14 |
|---|---:|---:|---:|
| vs `vflip(`8x16 `V)` | 4 | **0** | 0 |
| vs committed `2227` ∧ | 6 | **2** | 1 |

The freehand Λ broke a 1-pixel relationship with a drawing already committed
at 8x16.  Upstream itself accepted the 2 px apex held for two rows in its own
8x16 `V`, and Λ *is* `V` flipped in this typeface — so the "reads blunt"
objection is one upstream already answered for the letterform Λ is made from.

**The open question is whether upstream was right.**  If the owner prefers the
pointier freehand cut, it is one edit, and Λ then stops matching `V` and
`2227`.  Nothing else in the batch depends on it.

## `U+00B5` MICRO SIGN was drawn in this batch, outside the `03xx` block

Deliberate, and a scope call worth knowing about.  `00B5` is byte-identical to
`03BC` μ at 7x14, upstream carries it at **neither** size, and nothing derives
it — the filesystem is the index, so it is created by hand or not at all.
Leaving it for batch **10g** meant a later drawer could redraw it and silently
break an identity that holds at 7x14.  It is therefore a byte-for-byte copy of
`glyphs/8x16/regular/03BC.txt`, committed here.  **Batch 10g is one glyph
shorter and must not draw it again.**

## Drawings the implementer distrusts — pass 5

| glyph | what is wrong |
|---|---|
| `U+03B3` γ | **Second pass done — no change, and the reason is a rule rather than a preference.** The worry was that γ's tail narrows 2 px → 1 px at the baseline and drops from the *right* half of `v`'s point, where every other descender in the font is 1 px throughout. Three tails were built and measured: down column 4 then kick to 3 (as drawn); down column 3 then kick to 2; and a stepped diagonal. **All three carry identical ink (17) and identical distance to ν (3)** — so the only question is which column the tail takes, and that is settled: at 7x14 the tail sits *on* the centre column (3) and kicks one left (2); at 8x16 the centre is 3.5, which is precisely the case README **rule 1** answers — a centred vertical stem goes on **column 4**. The committed `03C6` φ and `03C8` ψ both descend on column 4. The 2 px → 1 px step is forced, not chosen: ν's point is 2 px because the cell has no centre column, and every descender tail is 1 px. Rebuilding γ on `x`'s geometry was reconsidered and rejected — `x` spans columns 1–7 against ν's 1–6, so γ would stop differing from ν by only its tail, which is the anchor the whole drawing rests on. **Also checked and disproved: upstream `y` is NOT γ's anchor.** `y` looks like "`v` with a tail" but is Hamming 15 from `v` over their shared rows — upstream draws `y` with straight sides converging low, not from `v` at all. |
| `U+03BA` κ | The lower arm's terminal is a 3 px blob (`.#..###.`) where 7x14's is 2 px. The upper arm now runs 4 rows against the lower arm's 2, where 7x14 is 3 against 2 — the arm had to start at column 6 to fill the wider box, and stepping one column per row to the junction takes four rows. It reads slightly top-heavy. |
| `U+03B9` ι | The stem stays on column 2 (7x14's left edge, per README rule 2) while the foot and its terminal curl widen right, so the gap between stem and terminal grew from 2 columns to 3. At 10 px of ink it is the lightest glyph in the batch and it now looks a little sprawled for its weight. |
| `U+03A6` Φ / `U+03C6` φ | 24.2% and 21.9% ink — the densest in the batch, and their two full-width `.#######` bars embolden to a solid `########`, an entirely filled row. Faithful to 7x14 (24.5% / 20.4%) and the gate is green at every face, but they are the two glyphs most likely to read as blobs at 1x. |
