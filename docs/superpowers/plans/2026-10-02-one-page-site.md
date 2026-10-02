# One Specimen Page for Every Cell Size: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the per-size specimen pages `build/site/7x14/` and `build/site/8x16/` with one page at `build/site/index.html` that shows any choice of sizes side by side.

**Architecture:** `tools/build-site.py` writes one page, a shared `data/site.json`, one `data/<size>.json` per size, one font family per size in `fonts.css`, and a `sizes.css` that scopes each size's cell geometry under `[data-size="<size>"]`. `site/smalti.js` keeps a per-size store, loads a size's data when its checkbox is checked, and renders every section for the checked sizes. `tools/check-site.py` checks the new layout once per size.

**Tech Stack:** Python 3 (venv from `requirements.txt`, fontTools), plain JavaScript (no build step, no npm), CSS custom properties, GNU make.

**Spec:** `docs/superpowers/specs/2026-10-02-one-page-site-design.md`

## Global Constraints

- Sizes are shown only at whole multiples of their own cell height: 7x14 at 14/28/42 px, 8x16 at 16/32/48 px.
- Chrome (nav, labels, buttons) is set in `Smalti8x16` at 16 px, from `:root` in `sizes.css`.
- Both checkboxes checked by default; the last checked box cannot be unchecked.
- URL `?sizes=7x14,8x16` wins over `localStorage` key `smalti.sizes`; every `localStorage` access goes through the existing `pref()`/`setPref()` wrappers.
- Editor route: `#/glyph/<size>/<face>/<hex>`. The old `#/glyph/<face>/<hex>` route is dropped.
- No redirect and no per-size directory under `build/site/`. `.nojekyll` stays at the root.
- The build stops when two sizes list different codepoints, different headers, different `state`, `textok` or `hint`.
- Every character of the chrome and of the specimen text must exist in every size.
- The bytes the editor puts on the clipboard stay byte-identical to the committed `.txt` files (`check-site` proves it).
- At most 4 cores: run `make -j4` at most. No `/tmp`; scratch goes under `/scratch/oetiker/claude-tmp/`.
- `CHANGES.md` under `## [Unreleased]`, `### Changed`; no em dashes in new prose (house style).

## Review Focus

- A URL with `?sizes=` naming an unknown size, or naming none: the page falls back to the default (both sizes), never to an empty page. Test in Task 3.
- `localStorage` blocked (private window): the page renders with both sizes and the checkboxes still work. Test in Task 3.
- An editor link for a size that is not checked (`#/glyph/8x16/regular/0041` with `?sizes=7x14`): the editor opens anyway, loading that size's data on demand. Test in Task 5.
- Unchecking a size while its editor is open: the editor stays open and usable (its data is not dropped). Test in Task 5.
- A control-code tile (`textok` 0) at two sizes: each half is an SVG of its own cell, not both at one size. Test in Task 4.

---

### Task 1: Build and check the one-page layout

**Files:**
- Modify: `tools/check-site.py` (whole `main()`; argument `--site` now points at `build/site`, new `--size`)
- Modify: `tools/build-site.py` (`build_data`, `build_one` split into `build_shared`/`build_size`, `write_root`, `main`, module docstring)
- Modify: `Makefile:415-426` (`site` and `check-site` recipes)

**Interfaces:**
- Produces (data contract every later task reads):
  - `data/site.json`: `{"sizes": ["7x14","8x16"], "faces": [...], "faceLabel": {...}, "cps": [...], "headers": [...], "state": "...", "textok": "...", "hint": "...", "blocks": [...], "specimen": [{"z": 3, "text": "..."}, ...], "repo": "...", "branch": "main"}`
  - `data/<size>.json`: `{"size": "7x14", "cell": {"w": 7, "h": 14}, "guides": {"baseline": 10, "cap": 3, "xheight": 5, "axis": 7}, "family": "Smalti7x14", "faceFile": {...}, "bits": {...}, "layers": {...}, "totals": [...], "cmap": 1201}`
  - `fonts.css`: `font-family: Smalti7x14` / `Smalti8x16`, four `@font-face` each.
  - `sizes.css`: `:root { 8x16 values }` then `[data-size="7x14"] { ... }` and `[data-size="8x16"] { ... }`, each declaring `--cell-cols`, `--cell-rows`, `--u`, `--u2`, `--u3`, `--u4`, `--u6`, `--u8`, `--pix`.
  - `index.html` with `{{WORDMARKS}}` replaced by one `<svg class="wordmark" data-size="<size>">` per size, and no other `{{`.

- [ ] **Step 1: Rewrite `check-site.py` for the new layout (red first)**

Change the argument parsing and the file reads at the top of `main()`:

```python
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default=os.path.join('build', 'site'))
    ap.add_argument('--size', required=True)
    a = ap.parse_args()
    size, site = a.size, a.site

    with open(os.path.join(site, 'data', 'site.json'), encoding='utf-8') as fh:
        shared = json.load(fh)
    path = os.path.join(site, 'data', f'{size}.json')
    if not os.path.exists(path):
        bad(f'{path} is missing, so the page cannot show {size} at all')
        return finish()
    with open(path, encoding='utf-8') as fh:
        mine = json.load(fh)
    if size not in shared['sizes']:
        bad(f'site.json lists sizes {shared["sizes"]}, not {size}')
    # Every existing check reads `d`.  One merged dict keeps them unchanged:
    # the shared keys and this size's keys never collide by construction.
    d = dict(shared)
    d.update(mine)
    d['size'] = size
```

(Use whatever the file's existing end-of-run function is in place of `finish()`; read the bottom of `main()` first and keep its exit behaviour.)

Replace the `size.css` leg with a `sizes.css` leg:

```python
    scss = os.path.join(site, 'sizes.css')
    css2 = open(scss, encoding='utf-8').read() if os.path.exists(scss) else ''
    if not css2:
        bad('sizes.css is missing, so the page has no cell geometry at all')
    else:
        block = re.search(r'\[data-size="' + re.escape(size) + r'"\]\s*\{([^}]*)\}', css2)
        if not block:
            bad(f'sizes.css has no [data-size="{size}"] block')
        else:
            body = block.group(1)
            for prop, want in (('--cell-cols', w), ('--cell-rows', h),
                               ('--u2', f'{h}px')):
                if not re.search(re.escape(prop) + r':\s*' + re.escape(str(want)) + r'(px)?;', body):
                    bad(f'sizes.css [data-size="{size}"] does not declare {prop}: {want}')
        root = re.search(r':root\s*\{([^}]*)\}', css2)
        if not root or not re.search(r'--u2:\s*16px;', root.group(1)):
            bad('sizes.css :root does not carry 8x16\'s --u2: 16px for the chrome')
```

Change the `fonts.css` leg so each `faceFile` must appear exactly once AND under `font-family: Smalti<size>`:

```python
    fam = f'Smalti{size}'
    if d.get('family') != fam:
        bad(f'{size}.json names family {d.get("family")!r}, expected {fam!r}')
    n_fam = len(re.findall(r'font-family:\s*' + re.escape(fam) + r';', css))
    if n_fam != len(gs.FACES):
        bad(f'fonts.css declares {n_fam} faces of {fam}, expected {len(gs.FACES)}')
```

Remove the specimen-class leg that compares `spec["px"]` (the shared specimen no longer carries `px`); keep the check that every `spec["z"]` has a `.s<z>` rule in `smalti.css`.

Add at the end of `main()`, before the exit:

```python
    for s in os.listdir(site):
        if re.fullmatch(r'\d+x\d+', s) and os.path.isdir(os.path.join(site, s)):
            bad(f'{site}/{s}/ exists: the per-size pages are gone, nothing may be built there')
```

Keep the existing `{{` placeholder check on `index.html` unchanged; it now reads `os.path.join(site, 'index.html')`, which is the root page.

- [ ] **Step 2: Point the Makefile at the root and run the checker against the old build**

In `Makefile`, `check-site:` recipe becomes:

```make
check-site: site
	$(PY) tools/check-site.py --site $(SITE) --size $(SIZE)
```

Run: `make check-site`
Expected: FAIL with `build/site/data/site.json` missing (FileNotFoundError or the checker's own message), because the builder still writes per-size pages.

- [ ] **Step 3: Split `build_data` into shared and per-size parts**

In `tools/build-site.py`, keep `build_data(size, repo, branch, hinted)` as it is (it already computes everything per size) and add, after it:

```python
SHARED_KEYS = ('faces', 'faceLabel', 'cps', 'headers', 'state', 'textok',
               'hint', 'blocks', 'repo', 'branch')


def split_sizes(per_size):
    """One shared dict and one dict per size, from build_data()'s output.

    The page shows the sizes side by side and draws ONE coverage strip per
    block, so every key it treats as shared must be identical across sizes.
    A future size that covers a different set is refused here rather than
    drawn with a strip that is true for one size only.
    """
    sizes = list(per_size)
    first = per_size[sizes[0]]
    for s in sizes[1:]:
        for key in SHARED_KEYS:
            if per_size[s][key] != first[key]:
                raise SystemExit(
                    f'{s} and {sizes[0]} differ in {key!r} -- the one-page site '
                    f'draws one coverage strip and one header per codepoint, so '
                    f'every size must list the same codepoints the same way')
    shared = {k: first[k] for k in SHARED_KEYS}
    shared['sizes'] = sizes
    shared['specimen'] = [{'z': z, 'text': t} for z, t in SPECIMEN]
    own = {}
    for s in sizes:
        d = per_size[s]
        own[s] = {'size': s, 'cell': d['cell'], 'family': f'Smalti{s}',
                  'faceFile': d['faceFile'], 'bits': d['bits'],
                  'layers': d['layers'], 'totals': d['totals']}
    return shared, own
```

- [ ] **Step 4: Replace `build_one` with a one-page writer**

Restructure `build_one` into a function that measures one size and returns its pieces (guides, cmap, wordmark, size css block, font css rules) without writing a page, and a `main()` that writes once. Concretely:

```python
def measure_size(size, repo, branch, plan):
    """Everything one size contributes to the page.  Writes nothing."""
    data, resolved, covered = build_data(
        size, repo, branch, {cp for _fn, cps in plan for cp in cps})
    w, h = data['cell']['w'], data['cell']['h']
    # (keep the existing TTFont cmap / upem / ascent block verbatim here,
    #  producing `cmap` and `ascent_px`)
    data['guides'] = {'baseline': ascent_px - 1, 'cap': GUIDE_CAP,
                      'xheight': GUIDE_XHEIGHT, 'axis': GUIDE_AXIS}
    data['cmap'] = cmap
    if h != 2 * w:
        raise SystemExit(...)   # keep the existing 1:2 message verbatim
    svg = wordmark_svg(resolved, w, h).replace(
        '<svg class="wordmark"', f'<svg class="wordmark" data-size="{size}"', 1)
    return data, svg


def size_vars(w, h):
    unit = [1, 2, 3, 4, 6, 8]
    return ([f'  --cell-cols: {w};', f'  --cell-rows: {h};'] +
            [f'  --u{"" if n == 1 else n}: {n * w}px;' for n in unit] +
            ['  --pix: var(--u4);'])


CHROME_SIZE = '8x16'   # spec 2.7: the chrome is set in 8x16 at 1x
```

In `main()`, after `plan = hint_plan()`:

```python
    if CHROME_SIZE not in sizes:
        raise SystemExit(f'the chrome is set in {CHROME_SIZE}, which this run '
                         f'does not build (sizes: {sizes})')
    root = a.out
    shutil.rmtree(root, ignore_errors=True)
    for sub in ('fonts', 'data', 'hint'):
        os.makedirs(os.path.join(root, sub), exist_ok=True)

    per_size, svgs = {}, {}
    for size in sizes:
        per_size[size], svgs[size] = measure_size(size, repo, a.branch, plan)
    shared, own = split_sizes(per_size)
    for size in sizes:
        own[size]['guides'] = per_size[size]['guides']
        own[size]['cmap'] = per_size[size]['cmap']

    dump = lambda obj, name: json.dump(
        obj, open(os.path.join(root, 'data', name), 'w', encoding='utf-8'),
        separators=(',', ':'), sort_keys=True)
    dump(shared, 'site.json')
    for size in sizes:
        dump(own[size], f'{size}.json')
```

Then, still in `main()`:
- copy every size's `.woff2` into `root/fonts/` (the existing loop, run per size);
- write `fonts.css` with one `@font-face` per size and face, `font-family: Smalti<size>;` (the existing rule body with the family changed);
- write `sizes.css`:

```python
    cw, ch = per_size[CHROME_SIZE]['cell']['w'], per_size[CHROME_SIZE]['cell']['h']
    css = ['/* generated by tools/build-site.py -- do not edit */', ':root {'] + \
          size_vars(cw, ch) + ['}']
    for size in sizes:
        w, h = per_size[size]['cell']['w'], per_size[size]['cell']['h']
        css += [f'[data-size="{size}"] {{'] + size_vars(w, h) + ['}']
    css += ['@media (max-width: 720px) {',
            '  :root, [data-size] { --pix: var(--u3); }', '}']
    open(os.path.join(root, 'sizes.css'), 'w', encoding='utf-8').write('\n'.join(css) + '\n')
```

- copy `ASSETS` and the hint fonts into `root` (existing code, run once);
- write `index.html`: `tmpl.replace('{{WORDMARKS}}', ''.join(svgs[s] for s in sizes)).replace('{{REPO}}', repo or '')`;
- write `.nojekyll`; delete `write_root()` (no redirect, spec 2.8);
- print one summary line: sizes, glyph count, codepoints listed.

`ui_chars()` and the specimen character checks already run inside `build_data()` per size, so every size is checked. Leave them there.

Replace the module docstring paragraph "ONE PAGE PER SIZE, ..." with:

```
ONE PAGE FOR EVERY SIZE.  Comparing 7x14 with 8x16 on two pages meant a jump
that lost the scroll position, the face, the filter and the search.  The page
shows the sizes side by side instead.  What the sizes share (codepoints,
headers, coverage) is written once to data/site.json and refused when two
sizes disagree; what differs (cell, drawings, provenance) goes to
data/<size>.json, which the page fetches only for the sizes it shows.
```

- [ ] **Step 5: Template placeholder for the wordmarks (minimal, so the build runs)**

In `site/index.html`, replace `<div class="hero-mark">{{WORDMARK}}</div>` with `<div class="hero-mark">{{WORDMARKS}}</div>`, and replace `href="fonts/Smalti{{SIZE}}-Regular.woff2"` in the preload with `href="fonts/Smalti8x16-Regular.woff2"`, and `<link rel="stylesheet" href="size.css">` with `<link rel="stylesheet" href="sizes.css">`. Every other `{{...}}` is removed in Task 2; for now replace each remaining per-size placeholder with the literal text `7x14` or `14` so the template check passes. (Task 2 rewrites these lines anyway.)

- [ ] **Step 6: Run the checker**

Run: `make -j4 check-site`
Expected: PASS for both sizes (`==> check-site [7x14]`, `==> check-site [8x16]`, no `bad:` lines). `ls build/site` shows `index.html data fonts hint fonts.css sizes.css smalti.css smalti.js hint.css .nojekyll` and no `7x14/` or `8x16/`.

- [ ] **Step 7: Prove the size mismatch is refused**

Run (one throwaway check, nothing committed): copy `tools/build-site.py` to the session scratch dir, and in a Python shell import its `split_sizes` with two dicts that differ only in `state`; expect `SystemExit` naming `'state'`.

- [ ] **Step 8: Commit**

```bash
git add tools/build-site.py tools/check-site.py Makefile site/index.html
git commit -m "Build the specimen site as one page with per-size data files"
```

---

### Task 2: Page template and stylesheet for several sizes

**Files:**
- Modify: `site/index.html` (masthead, hero, specimen prose, coverage prose, toolbar, editor help)
- Modify: `site/smalti.css` (root comment, `--pixel`, `.tile`, `.spec-line`, new `.sizes`, `.tile-half`)

**Interfaces:**
- Consumes: `sizes.css` and `fonts.css` from Task 1.
- Produces (DOM ids and classes Task 3-5 use): `#sizes` (fieldset with one `<input type="checkbox" name="size" value="<size>">` per size, filled by JS), `.facts` items `#fact-glyphs`, `#fact-faces`, `#fact-sizes`, `#fact-hand`; `#px-ladder` (span the JS fills with the pixel ladders); `[name=zoom]` radios with values `1`, `2`, `3` and labels `1x`, `2x`, `3x`; `.tile` containing one `.half[data-size]` per shown size.

- [ ] **Step 1: Masthead and hero**

In `site/index.html`:
- `<title>Smalti, a pixel font you can draw in your browser</title>`; the description meta drops `{{SIZE}}`, `{{GLYPHS}}`, `{{FACES}}` and reads "Specimen and glyph editor for Smalti, a bitmap terminal font in two cell sizes. Click any glyph to change its pixels and open a pull request."
- Mark: `<a class="mark px" href="#top">smalti</a>`.
- Replace `{{SIZENAV}}` with `<fieldset id="sizes" class="sizes px"><legend class="sr-only">Sizes shown</legend></fieldset>`.
- `<h1 class="sr-only">Smalti</h1>`.
- Lede: "This is a bitmap terminal font in two cell sizes, 7×14 and 8×16, forked from Tamzen, in which every glyph is an ASCII-art text file, drawn per size. <strong>The drawings are the font.</strong> The font files are what the build spits out afterwards." Check `×` is in both fonts' coverage (it is used in the existing template, so `ui_chars()` already proved it for both).
- Facts: `<li><b id="fact-glyphs"></b> glyphs per face</li><li><b id="fact-faces"></b> faces</li><li><b id="fact-sizes"></b> cell sizes</li><li><b id="fact-hand"></b> drawn here</li>`.

- [ ] **Step 2: Specimen, coverage and browser prose**

- Specimen prose: "Everything below is the real font, loaded as a web font and rendered as text by your browser. Each size is set at its cell height and whole multiples of it (<span id="px-ladder"></span>), because that is where the outlines land exactly on the pixel grid and reproduce the bitmap with no antialiasing at all. No size in between is offered."
- Fractional-scale note: "If these look soft, your display is running at a fractional scale factor, and no outline can be exact at a half pixel. It is crisp at 100%, 200% and 300%."
- Coverage paragraph: replace "a {{CELL_W}}&times;{{CELL_H}} bitmap" with "a single-cell bitmap".
- Counting note: replace "Each face holds {{GLYPHS}} glyphs but its <code>cmap</code> has {{CMAP}} entries" with "Each face's <code>cmap</code> has one entry fewer than it has glyphs".
- Browser prose: "Rendered as text, in the face, sizes and zoom you choose. Click either half of a tile to open that size's pixel grid and change the pixels."
- Zoom radios: values `1`, `2`, `3`, labels `1x`, `2x`, `3x`, `2` checked.

Run: `grep -n '{{' site/index.html`
Expected: only `{{WORDMARKS}}` and `{{REPO}}`.

- [ ] **Step 3: Stylesheet**

In `site/smalti.css`:
- Replace the root comment about `size.css` with: "--u .. --u8, --pix, --cell-cols and --cell-rows come from sizes.css: the chrome's values on :root (8x16), and each size's again under [data-size], so an element carrying data-size gets its own cell geometry."
- `--pixel: Smalti8x16, ui-monospace, ...` (chrome family).
- Add, after `.px`:

```css
/* An element that shows one size's glyphs carries data-size and that size's
 * family; sizes.css gives it that size's --u2..--u6 under the same selector,
 * so .s1/.s2/.s3 resolve to its own cell height and multiples. */
[data-size="7x14"] { font-family: Smalti7x14, var(--pixel); }
[data-size="8x16"] { font-family: Smalti8x16, var(--pixel); }

.sizes { display: flex; gap: var(--u2); border: 0; margin: 0; padding: 0; }
.sizes label { display: flex; align-items: center; gap: 4px; cursor: pointer;
               color: var(--ink-dim); }
.sizes input:checked + span { color: var(--gold); }
.masthead { position: sticky; top: 0; z-index: 5; }
```

  (Keep the size selectors in this file literal for the two sizes; if a size is added later, `check-site` fails on the missing family rule because `fonts.css` and the page disagree. Add to `check-site` Step 1 a check that `smalti.css` contains `[data-size="<size>"] { font-family: Smalti<size>` for the checked size.)
- Remove the `.masthead nav a.size` rules (no size links any more).
- Tiles: `.tile` drops `aspect-ratio: 1` and `place-items: center`, becomes `display: flex; align-items: flex-end; justify-content: center; gap: 6px; padding: 6px 4px;`. Add:

```css
/* One half per shown size, bottom-aligned so both sit on the tile's
 * baseline.  The font size is the size's own multiple, set inline by the
 * script as --tsize on each half. */
.tile .half { font-size: var(--tsize); line-height: 1; border: 0; padding: 0;
              background: none; color: inherit; cursor: pointer; position: relative; }
.tile .half.h { box-shadow: inset 0 -2px 0 var(--gold); }
.tile .half:hover { outline: 1px solid var(--gold); outline-offset: 1px; }
.spec-line .size { color: var(--ink-dim); display: inline-block; width: 6ch; }
```

- [ ] **Step 4: Build and check**

Run: `make -j4 check-site`
Expected: PASS for both sizes.

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/smalti.css tools/check-site.py
git commit -m "Write the page template and stylesheet for several sizes"
```

---

### Task 3: Size state, data loading and the size control

**Files:**
- Modify: `site/smalti.js` (top-level state, `boot`, the `fetch` at the bottom, new `sizeChoice`, `loadSize`, `buildSizeControl`, `setSizes`)

**Interfaces:**
- Consumes: `data/site.json`, `data/<size>.json`, `#sizes`.
- Produces: globals `S` (shared data), `Z` (map size to its data, filled by `loadSize`), `SIZES` (checked sizes, in `S.sizes` order), `COVI` (unchanged meaning); functions `loadSize(size) -> Promise<sizeData>`, `setSizes(list)` (saves, loads, re-renders), `rowsOf(size, face, k)`, `blankRows(size)`, `artSvg(size, rows, px)`, `renderAll()` (calls the section builders of Task 4).

- [ ] **Step 1: Replace the single-data globals**

```js
var S = null;              // data/site.json: what every size shares
var Z = {};                // size -> data/<size>.json, once loaded
var SIZES = [];            // the checked sizes, in S.sizes order
var PENDING = {};          // size -> Promise, so a size loads once
```

Remove `var D = null;`. Every later `D.` read becomes `S.` for shared keys (`faces`, `faceLabel`, `cps`, `headers`, `state`, `textok`, `hint`, `blocks`, `specimen`, `repo`, `branch`) and `Z[size].` for per-size keys (`cell`, `guides`, `family`, `faceFile`, `bits`, `layers`, `totals`). Search: `grep -n 'D\.' site/smalti.js` must print nothing at the end of Task 5.

- [ ] **Step 2: Size-aware glyph helpers**

```js
function rowsOf(size, face, k) {
  var z = Z[size], w = z.cell.w, h = z.cell.h, s = z.bits[face], off = k * h * 2, out = [];
  for (var y = 0; y < h; y++) {
    var v = parseInt(s.substr(off + y * 2, 2), 16), r = '';
    for (var x = 0; x < w; x++) r += (v >> (w - 1 - x)) & 1 ? '#' : '.';
    out.push(r);
  }
  return out;
}

function blankRows(size) {
  var c = Z[size].cell, r = [], i;
  for (i = 0; i < c.h; i++) r.push('.'.repeat(c.w));
  return r;
}

function artSvg(size, rows, px) {
  var w = Z[size].cell.w, h = Z[size].cell.h, r = '', y, x;
  for (y = 0; y < h; y++) {
    for (x = 0; x < w; x++) {
      if (rows[y][x] === '#') r += '<rect x="' + x + '" y="' + y + '" width="1" height="1"/>';
    }
  }
  return '<svg class="art" width="' + (w * px / h) + '" height="' + px +
         '" viewBox="0 0 ' + w + ' ' + h + '" shape-rendering="crispEdges" ' +
         'fill="currentColor" aria-hidden="true">' + r + '</svg>';
}
```

`fileText(i, rows)` stays as it is but reads `S.headers[i]`.

- [ ] **Step 3: Size choice from URL and storage**

```js
var PREF = { repo: 'smalti.repo', branch: 'smalti.branch', hint: 'smalti.hint',
             sizes: 'smalti.sizes' };

/* The sizes to show.  The URL wins, so a shared link shows the view it was
 * copied from; then the visitor's last choice; then every size.  Anything
 * that names no known size falls through to the next source rather than to
 * an empty page. */
function sizeChoice() {
  var known = function (list) {
    return S.sizes.filter(function (s) { return list.indexOf(s) >= 0; });
  };
  var q = new URLSearchParams(location.search).get('sizes');
  var fromUrl = q ? known(q.split(',')) : [];
  if (fromUrl.length) return fromUrl;
  var fromPref = known(pref(PREF.sizes, '').split(','));
  if (fromPref.length) return fromPref;
  return S.sizes.slice();
}
```

(Move the existing `PREF`, `pref`, `setPref` definitions above `sizeChoice`; delete the old `PREF` line.)

- [ ] **Step 4: Loading and switching**

```js
function loadSize(size) {
  if (Z[size]) return Promise.resolve(Z[size]);
  if (!PENDING[size]) {
    PENDING[size] = fetch('data/' + size + '.json').then(function (r) {
      if (!r.ok) throw new Error(size + ': HTTP ' + r.status);
      return r.json();
    }).then(function (z) { Z[size] = z; return z; });
  }
  return PENDING[size];
}

function setSizes(list) {
  SIZES = S.sizes.filter(function (s) { return list.indexOf(s) >= 0; });
  setPref(PREF.sizes, SIZES.join(','));
  var u = new URL(location.href);
  u.searchParams.set('sizes', SIZES.join(','));
  history.replaceState(null, '', u.pathname + u.search + u.hash);
  Array.prototype.forEach.call(document.querySelectorAll('[name=size]'), function (cb) {
    cb.checked = SIZES.indexOf(cb.value) >= 0;
    /* The last checked box cannot be unchecked: a page showing no size has
     * nothing to show. */
    cb.disabled = cb.checked && SIZES.length === 1;
  });
  return Promise.all(SIZES.map(loadSize)).then(renderAll);
}

function buildSizeControl() {
  var host = $('#sizes');
  S.sizes.forEach(function (s) {
    var lab = el('label');
    var cb = el('input');
    cb.type = 'checkbox';
    cb.name = 'size';
    cb.value = s;
    cb.addEventListener('change', function () {
      var next = SIZES.filter(function (x) { return x !== s; });
      if (cb.checked) next.push(s);
      setSizes(next);
    });
    lab.appendChild(cb);
    lab.appendChild(el('span', null, s));
    host.appendChild(lab);
  });
}
```

- [ ] **Step 5: Boot**

```js
function boot(shared) {
  S = shared;
  var i, k = 0;
  COVI = new Int32Array(S.cps.length);
  for (i = 0; i < S.cps.length; i++) COVI[i] = S.state[i] === '#' ? k++ : -1;
  for (i = 0; i < S.headers.length; i++) {
    var m = HEAD_RE.exec(S.headers[i]);
    SHOWN.push(m ? m[2].trim() : '');
    NAME.push(m ? m[3] : '');
  }
  buildSizeControl();
  buildBlocks();
  buildControls();
  window.addEventListener('hashchange', route);
  return setSizes(sizeChoice()).then(function () {
    route();
    animateWordmark();
  });
}
```

`renderAll()` (defined in Task 4) calls `buildHero()`, `buildSpecimens()`, `buildProvenance()`, `renderGrid()`. Until Task 4 lands, define it as `function renderAll() { renderGrid(); }` so the page runs.

The bottom `fetch('data/glyphs.json')` becomes `fetch('data/site.json')`; its error text stays.

- [ ] **Step 6: Check the fallbacks in a browser**

Run: `make -j4 check-site && make serve-site` (in the background, `timeout: 7200000`), then load in a browser:
- `http://localhost:8014/?sizes=9x18`: both boxes checked, page renders.
- `http://localhost:8014/?sizes=`: both boxes checked.
- `http://localhost:8014/?sizes=7x14`: only 7x14 checked, that box disabled; `data/8x16.json` is NOT in the network log.
- In a private window with storage blocked (Firefox: `dom.storage.enabled=false`): page renders, toggling works.
Expected: all four as stated; no console errors.

- [ ] **Step 7: Commit**

```bash
git add site/smalti.js
git commit -m "Load each size's data on demand behind a size control"
```

---

### Task 4: Hero, specimen, provenance and tiles for the checked sizes

**Files:**
- Modify: `site/smalti.js` (`renderAll`, new `buildHero`, `buildSpecimens`, `buildProvenance`, `matches`, `renderGrid`, `tileHtml`, the grid click listener, `faceClass` unchanged)

**Interfaces:**
- Consumes: `S`, `Z`, `SIZES`, `rowsOf`, `artSvg`, `openEditor(i, face, size)` from Task 5 (until Task 5, the click listener calls `openEditor(i, null, size)` and the old `openEditor` ignores the third argument).
- Produces: `renderAll()`.

- [ ] **Step 1: renderAll and the hero**

```js
function renderAll() {
  buildHero();
  buildSpecimens();
  buildProvenance();
  renderGrid();
}

function largest(list) {
  return list.reduce(function (a, b) { return Z[b].cell.h > Z[a].cell.h ? b : a; });
}

function buildHero() {
  var big = largest(SIZES);
  Array.prototype.forEach.call(document.querySelectorAll('.wordmark'), function (svg) {
    svg.hidden = svg.getAttribute('data-size') !== big;
  });
  $('#fact-glyphs').textContent = Z[big].totals[0].total;
  $('#fact-faces').textContent = S.faces.length * S.sizes.length;
  $('#fact-sizes').textContent = S.sizes.length;
  $('#fact-hand').textContent = SIZES.map(function (s) {
    return Z[s].totals[0].hand;
  }).join(' / ');
  $('#px-ladder').textContent = SIZES.map(function (s) {
    var h = Z[s].cell.h;
    return s + ' at ' + h + ', ' + 2 * h + ' and ' + 3 * h + ' px';
  }).join('; ');
}
```

`animateWordmark()` must query `.wordmark:not([hidden])` for `box` and `.wordmark rect` for all tiles (each SVG has its own viewBox; compute `cols` per tile from `tiles[i].ownerSVGElement.viewBox.baseVal.width`).

- [ ] **Step 2: Specimens**

```js
function buildSpecimens() {
  var host = $('#specimen-faces');
  host.innerHTML = '';
  S.faces.forEach(function (f) {
    var card = el('div', 'spec');
    card.appendChild(el('p', 'spec-name px', S.faceLabel[f]));
    S.specimen.forEach(function (s) {
      SIZES.forEach(function (size) {
        var line = el('p', 'spec-line px s' + s.z + ' ' + faceClass(f));
        line.setAttribute('data-size', size);
        line.innerHTML = '<span class="size">' + size + '</span>' + esc(s.text);
        card.appendChild(line);
      });
    });
    host.appendChild(card);
  });
}
```

SIZES is in `S.sizes` order, and the build lists `7x14` before `8x16`, so the smaller cell comes first (spec 2.3). The `.size` label inherits the line's font size; `.spec-line .size` in the stylesheet sets it dim. Check after building that the label reads at the line size; if it should stay small, give `.spec-line .size` `font-size: var(--u2); line-height: inherit;`.

- [ ] **Step 3: Provenance, one column group per size**

```js
function buildProvenance() {
  var host = $('#provenance');
  host.innerHTML = '';
  var wrap = el('div', 'prov');
  S.faces.forEach(function (f, fi) {
    SIZES.forEach(function (size) {
      var t = Z[size].totals[fi];
      var row = el('div', 'prov-row');
      row.appendChild(el('div', 'prov-name px', t.label + ' ' + size));
      var bar = el('div', 'prov-bar');
      [['h', t.hand], ['u', t.upstream], ['g', t.gen]].forEach(function (p) {
        if (!p[1]) return;
        var s = el('span', p[0]);
        s.style.flex = p[1];
        s.title = p[1] + ' ' + LAYER_SHORT[p[0]];
        bar.appendChild(s);
      });
      row.appendChild(bar);
      row.appendChild(el('div', 'prov-n px',
        t.hand + ' / ' + t.upstream + ' / ' + t.gen + '  = ' + t.total));
      wrap.appendChild(row);
    });
  });
  host.appendChild(wrap);
  // the existing prov-key list, unchanged
}
```

Widen `.prov-row`'s first column in `smalti.css` from `13ch` to `18ch` so "Bold Oblique 8x16" fits.

- [ ] **Step 4: Filter and tiles**

```js
function matches(i) {
  var st = S.state[i];
  if (FILT === 'hand') {
    if (st !== '#') return false;
    var any = SIZES.some(function (s) { return Z[s].layers[FACE][COVI[i]] === 'h'; });
    if (!any) return false;
  }
  if (FILT === 'gap' && st !== '.') return false;
  if (!QUERY) return true;
  if (NAME[i].toLowerCase().indexOf(QUERY) >= 0) return true;
  if (hex(S.cps[i]).toLowerCase().indexOf(QUERY) >= 0) return true;
  return SHOWN[i] !== '' && SHOWN[i] === QUERY;
}

function tileHtml(i) {
  var cp = S.cps[i], st = S.state[i];
  var label = 'U+' + hex(cp) + ' ' + NAME[i];
  if (st === 'w') {
    return '<span class="tile rule" title="' + esc(label) +
           ' — East Asian Wide, taken from the emoji font">&#183;</span>';
  }
  var halves = SIZES.map(function (size) {
    var px = ZOOM * Z[size].cell.h;
    var open = ' data-i="' + i + '" data-size="' + size + '" style="--tsize:' + px + 'px"';
    if (st === '.') {
      return '<button class="half miss"' + open + ' title="' + esc(label) + ' ' + size +
             ' — not drawn yet, click to draw it" aria-label="' + esc(label) + ', ' +
             size + ', not drawn yet">+</button>';
    }
    var layer = Z[size].layers[FACE][COVI[i]];
    var body = S.textok[i] === '1'
      ? esc(String.fromCodePoint(cp))
      : artSvg(size, rowsOf(size, FACE, COVI[i]), px);
    return '<button class="half ' + layer + ' ' + faceClass(FACE) + '"' + open +
           ' title="' + esc(label) + ' ' + size + ' — ' + LAYER_SHORT[layer] +
           '" aria-label="' + esc(label) + ', ' + size + '">' + body + '</button>';
  }).join('');
  return '<div class="tile' + (st === '.' ? ' miss' : '') + '">' + halves + '</div>';
}
```

`renderGrid()`: drop the `px` argument to `tileHtml`; set `--tile` from the widest tile, `host.style.setProperty('--tile', (SIZES.reduce(function (a, s) { return a + ZOOM * Z[s].cell.w; }, 0) + 6 * SIZES.length + 20) + 'px')`; the count line reads `shown + ' of ' + S.cps.length + ' codepoints · ' + S.faceLabel[FACE] + ' · ' + ZOOM + 'x'`.

The grid click listener:

```js
$('#grid').addEventListener('click', function (e) {
  var t = e.target.closest('.half[data-i]');
  if (t) openEditor(+t.dataset.i, null, t.dataset.size);
});
```

The coverage strip buttons in `blockRow` call `openEditor(+e.currentTarget.dataset.i, null, SIZES[0])`.

- [ ] **Step 5: Build and look**

Run: `make -j4 check-site`, serve, open `http://localhost:8014/#browse`.
Expected: every tile shows two glyphs on one baseline; at `1x` the 7x14 half is 14 px tall and the 8x16 half 16 px; control-code tiles in the first block (`textok` 0, for example U+0001) show two SVGs of different heights; unchecking 8x16 leaves one glyph per tile; "drawn here" with 8x16 only shows 334 codepoints in Regular, with 7x14 only 313.

- [ ] **Step 6: Commit**

```bash
git add site/smalti.js site/smalti.css
git commit -m "Show the checked sizes side by side in hero, specimen, provenance and tiles"
```

---

### Task 5: The editor works per size

**Files:**
- Modify: `site/smalti.js` (`route`, `openEditor`, `closeEditor` unchanged, `drawEditor`, `gridGeom`, `drawOverlay`, `paintGrid`, `onGridKey`, `sidePanel`, `refresh`, `ghostChar`, the guide globals)

**Interfaces:**
- Consumes: `loadSize`, `Z`, `S`.
- Produces: `openEditor(i, face, size)`; `ED.size`; route `#/glyph/<size>/<face>/<hex>`.

- [ ] **Step 1: Route and open**

```js
function route() {
  var m = /^#\/glyph\/(\d+x\d+)\/([a-z-]+)\/([0-9A-F]+)$/.exec(location.hash);
  if (!m) { if (ED) closeEditor(true); return; }
  var size = S.sizes.indexOf(m[1]) >= 0 ? m[1] : SIZES[0];
  var face = S.faces.indexOf(m[2]) >= 0 ? m[2] : 'regular';
  var i = S.cps.indexOf(parseInt(m[3], 16));
  if (i < 0) { closeEditor(true); return; }
  if (ED && ED.i === i && ED.face === face && ED.size === size) return;
  openEditor(i, face, size, true);
}

function openEditor(i, face, size, fromHash) {
  face = face || FACE;
  size = size || SIZES[0];
  if (!fromHash) LAST_FOCUS = document.activeElement;
  /* A link may name a size that is not checked.  Its data loads on demand;
   * the size stays unchecked, because opening one glyph is not a vote to
   * show the whole size. */
  loadSize(size).then(function () { showEditor(i, face, size); });
}
```

`showEditor(i, face, size)` holds the old body of `openEditor`, with:
- `var z = Z[size], k = COVI[i];`
- `ED = { i: i, face: face, size: size, rows: k >= 0 ? rowsOf(size, face, k) : blankRows(size), orig: k >= 0 ? rowsOf(size, face, k) : blankRows(size), exists: k >= 0 && z.layers[face][k] === 'h', ghost: pref(PREF.hint, '1') === '1' };`
- `var want = '#/glyph/' + size + '/' + face + '/' + hex(S.cps[i]);`
- `$('#editor').setAttribute('data-size', size);` before `drawEditor()`, so `sizes.css` gives `.paint` this size's `--cell-cols` and `--pix`.

- [ ] **Step 2: Every `D.cell`, `D.guides`, `D.layers` in the editor reads `Z[ED.size]`**

Remove the globals `BASE, CAP, XH, AXIS`; add at the top of each editor function that used them:

```js
var G = Z[ED.size].guides, C = Z[ED.size].cell;
```

and replace `BASE` with `G.baseline`, `CAP` with `G.cap`, `XH` with `G.xheight`, `AXIS` with `G.axis`, `D.cell` with `C`. Functions: `gridGeom`, `drawOverlay`, `paintGrid`, `onGridKey`, `sidePanel`, `refresh`, `drawEditor`.

In `drawEditor`, the subtitle gains the size: `'U+' + hex(cp) + '  ·  ' + ED.size + '  ·  ' + (layer ? ...)`, and the face `<select>` change handler calls `openEditor(ED.i, fs.value, ED.size)`.

The help text names this size's own rows instead of 7x14's literal ones:

```js
help.innerHTML = 'Click or drag to paint. Arrow keys move, space toggles. ' +
  'Rows and columns follow the grid the rest of the font uses: columns 0 ' +
  'and ' + (C.w - 1) + ' are the side bearings, row ' + G.baseline +
  ' is the last row on the baseline, capitals start at row ' + G.cap +
  ', x-height at row ' + G.xheight + ', and the maths axis is row ' + G.axis + '.';
```

In `refresh`, `var rel = 'glyphs/' + ED.size + '/' + ED.face + '/' + hex(S.cps[ED.i]) + '.txt';`.

- [ ] **Step 3: Check the editor in a browser**

Serve and check:
- Click the 7x14 half of `A`: title subtitle says `7x14`, grid is 7 columns by 14 rows, path reads `glyphs/7x14/regular/0041.txt`, help says "columns 0 and 6", "row 10".
- Click the 8x16 half: 8 by 16, `glyphs/8x16/regular/0041.txt`, "columns 0 and 7", "row 11"; the gold baseline runs under the feet of the letter.
- `http://localhost:8014/?sizes=7x14#/glyph/8x16/regular/0041`: the editor opens on 8x16; the 8x16 checkbox stays unchecked.
- With the editor open on 8x16, uncheck 8x16 (via keyboard focus behind the scrim is blocked by `inert`, so: open `?sizes=7x14,8x16#/glyph/8x16/regular/0041`, close, uncheck 8x16, then press browser Back to the editor hash): the editor opens and paints.
- Copy the file for a hand-drawn glyph and diff against the repository file: identical.

- [ ] **Step 4: Run the full checks**

Run: `make -j4 check && make -j4 check-site`
Expected: PASS. `grep -n 'D\.' site/smalti.js` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add site/smalti.js
git commit -m "Open the glyph editor for the size of the half that was clicked"
```

---

### Task 6: Documentation and the user's look

**Files:**
- Modify: `CHANGES.md` (`## [Unreleased]`, `### Changed`)
- Modify: `README.md:276-279` and `README.md:458-459`

- [ ] **Step 1: CHANGES entry**

Under `### Changed`:

```markdown
- **The specimen site is one page for both cell sizes.** Checkboxes in the page header choose which of 7x14 and 8x16 are shown, and every specimen line, provenance row and glyph tile shows the chosen sizes side by side; clicking either half of a tile opens the pixel editor for that size. The per-size pages `/7x14/` and `/8x16/` no longer exist, and a link to an editor now names the size, as in `#/glyph/8x16/regular/0041`.
```

- [ ] **Step 2: README**

- Line 278-279: "Each specimen page offers exactly its own three sizes and nothing in between, for this reason." becomes "The specimen page sets each size at exactly its own three sizes and nothing in between, for this reason."
- Line 458-459: "**It only ever sets type at 14, 28 and 42 px**" becomes "**It only ever sets type at the cell height and its multiples**, 14, 28 and 42 px for 7x14 and 16, 32 and 48 px for 8x16".

- [ ] **Step 3: Final verification**

Run: `make -j4 check && make -j4 check-site`
Expected: PASS for both sizes, with the per-size counts printed by `check-site` unchanged from before Task 1 (same glyph count, same committed-file count).

- [ ] **Step 4: Commit**

```bash
git add CHANGES.md README.md
git commit -m "Describe the one-page specimen site"
```

- [ ] **Step 5: Hand the page to the user**

Serve `build/site` with `python3 -m http.server 8014 --bind 127.0.0.1` from `build/site` (background, `timeout: 7200000`) and ask the user to judge it at 100% and 200% browser zoom: the size control, a side-by-side tile row, the specimen stack, and one editor per size.
