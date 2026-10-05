# One specimen page for every cell size: design

Date: 2026-10-02
Status: design approved in conversation; not yet implemented
Scope: `site/`, `tools/build-site.py`, `tools/check-site.py`, the `site` and
`check-site` Makefile targets

## 1. The problem

Since 0.2.0 the specimen site is one page per cell size, `build/site/7x14/` and
`build/site/8x16/`, with a redirect at the root and a size link in the masthead.
Comparing the two sizes means jumping between two pages, and the jump loses the
scroll position, the face, the filter and the search. The two sizes are one
family and belong on one page, with a control that chooses which sizes are
shown.

The two sizes cover the same codepoints: both data files list 2631 codepoints
with the same coverage state. Only provenance differs (313 glyphs drawn here at
7x14, 334 at 8x16, regular face).

## 2. The page

### 2.1 Size control

- Checkboxes `7x14` and `8x16` in the masthead, which stays visible while the
  page scrolls.
- Both are checked by default. The last checked box cannot be unchecked.
- The choice is kept in the URL as `?sizes=7x14,8x16` and in `localStorage`.
  The URL wins over `localStorage`, so a shared link shows the view it was
  copied from. Every `localStorage` access is wrapped so the page works when
  storage is blocked.

### 2.2 Hero

- The lede describes the family: a bitmap terminal font in two cell sizes,
  7x14 and 8x16.
- The facts line gives glyphs per face, faces, sizes, and "drawn here" per size.
- The mosaic wordmark is built for every size and the page shows the one of the
  largest checked size.

### 2.3 Specimen

- Every sample line is shown once per checked size, the smaller cell first,
  with the size name as a label in the margin.
- Each line is set at a whole multiple of its own cell height (7x14 at 14, 28
  or 42 px; 8x16 at 16, 32 or 48 px). The specimen prose names both ladders.

### 2.4 Coverage

- The provenance table has one column group per checked size.
- Each covered block shows one strip per checked size, the smaller cell first,
  each labelled with its size. A cell is coloured by the layer that size's
  glyph comes from (drawn here, upstream, generated) in the face chosen in the
  glyph browser; not drawn yet and left undrawn by rule keep their look. A
  click opens the editor for that strip's size.
- The user chose this on 2026-10-03: the build refuses sizes whose codepoint
  lists differ (section 3.2), so coverage-only strips are identical across sizes.

### 2.5 Every glyph

- The zoom control offers `1x`, `2x` and `3x`, a multiple of the cell height.
- A tile shows the checked sizes side by side on a shared baseline, the smaller
  cell on the left. Each half is its own click target and opens the editor for
  its size. With one size checked, a tile holds one glyph, as today.
- Face menu, filter and search work as today. The "drawn here" filter matches a
  codepoint drawn here in any checked size, and the tile marks the half that is
  drawn here.

### 2.6 Editor

- Opens for the size of the half that was clicked; its title names the size.
- Route: `#/glyph/<size>/<face>/<hex>`. The old `#/glyph/<face>/<hex>` route is
  dropped, since the old pages are gone.
- Grid, guides and baseline come from that size's data, as today.

### 2.7 Page chrome

Nav, labels and buttons are set in Smalti at one fixed size, 8x16 at 1x
(16 px), so they do not change when the size control changes.

### 2.8 URLs

The page is `build/site/index.html`. `/7x14/` and `/8x16/` go away with no
redirect.

## 3. Build

### 3.1 One page

`tools/build-site.py` writes one `build/site/index.html` and its assets. No
per-size directory is written. `.github/workflows/pages.yml` keeps uploading
`build/site` unchanged.

### 3.2 Data files

| File | Holds |
|---|---|
| `data/site.json` | the size list, faces, face labels, codepoint list, headers, block table, coverage state, `textok`, `hint`, the specimen text, repo and branch |
| `data/<size>.json` | cell, guides, font file names, `bits`, `layers`, provenance totals, specimen pixel sizes |

The page fetches `site.json` and then only the checked sizes' files, and
fetches a size's file when its box is checked. Each size file is about 300 KB.

The build stops with an error when two sizes list different codepoints, in the
same way it stops today when two faces do.

### 3.3 Fonts

`fonts.css` declares one family per size, `Smalti7x14` and `Smalti8x16`, four
faces each. Tile halves, specimen lines and the editor use their size's family.
The chrome uses `Smalti8x16`.

### 3.4 Size CSS

`size.css` becomes `sizes.css`:

- the 8x16 values of `--cell-cols`, `--cell-rows`, `--u` ... `--u8` and `--pix`
  on `:root`, for the chrome;
- every size's values again under `[data-size="<size>"]`, so an element with
  that attribute gets its own cell geometry.

The 1:2 cell check stays, run once per size.

### 3.5 Template

- `site/index.html` drops `{{SIZE}}`, `{{CELL_W}}`, `{{CELL_H}}`, `{{PX1}}`,
  `{{PX2}}`, `{{PX3}}`, `{{PX_BLUR}}`, `{{PX_DEV}}`, `{{SIZENAV}}` and the other
  per-size placeholders. Text that names a size or a pixel size is written by
  `smalti.js` from the data.
- `ui_chars()` checks that every character of the chrome is in every size.
- The specimen text is checked against every size.

## 4. Checks

`make check-site` still runs once per size and checks `build/site` with
`--size <size>`:

- every glyph in every face of that size equals the store, including the exact
  bytes the editor emits (as today, reading `data/site.json` and
  `data/<size>.json`);
- `sizes.css` declares that size's geometry under `[data-size="<size>"]`, and
  `:root` carries 8x16's;
- `fonts.css` declares the four faces of that size's family;
- `index.html` holds no `{{` left over;
- no `build/site/<size>/` directory exists.

The look is judged by the user in a browser at 100% and 200% zoom, served from
`build/site` with `make serve-site`.

## 5. Out of scope

- Further cell sizes.
- The editor's drawing logic.
- The hint fonts, which stay shared as today.
- A marking for codepoints only some sizes cover; the build refuses that case
  instead.

## 6. Documentation

- `CHANGES.md`: one entry under `### Changed` for the single page with the size
  control, naming that `/7x14/` and `/8x16/` no longer exist.
- `README.md`: the paragraph on the specimen site, if it names the per-size
  pages.
- The `build-site.py` module docstring: replace the "ONE PAGE PER SIZE"
  rationale with the reason for one page.
