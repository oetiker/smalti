# Box Drawing and Block Elements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cover U+2500..U+257F and U+2580..U+259F at 7x14 and 8x16 by generating all 160 glyphs from the Unicode character name, and hand-draw the two single guillemets that were asked for alongside them.

**Architecture:** The pure logic — the name grammar, the per-size geometry table, and the renderers — lives in `tools/boxgeom.py`, which is importable (no hyphen). `tools/gen-box.py` is a thin CLI that imports it and writes `build/gen/<size>/regular/`, exactly as `gen-braille.py` does. `tools/test-box.py` imports `boxgeom` directly and fault-injects it, in the shape of `tools/test-weight.py`. Bold and italic need no work at all.

**Tech Stack:** Python 3 standard library only (`unicodedata`, `re`). No new dependency. The font build's dependency list stays `python3-venv` and nothing else.

**Spec:** `docs/superpowers/specs/2026-09-15-box-drawing-design.md`

## Global Constraints

- **Cell geometry, drawn per size, never scaled.** 7x14: axis column 3, axis row 7, heavy vertical columns 2,3, heavy horizontal rows 6,7, double vertical columns 2 and 4, double horizontal rows 6 and 8. 8x16: axis column 4, axis row 7, heavy vertical columns 3,4, heavy horizontal rows 7,8, double vertical columns 3 and 5, double horizontal rows 6 and 8.
- **Every glyph in both blocks spans the full cell**, columns `0..W-1` and rows `0..H-1`. A rule that stops one column short comes apart at every cell boundary. This is `glyphs/8x16/README.md` rule 3.
- **Work in a 2-D grid of 0/1, never in packed bit rows.** `gen-braille.py`'s docstring records the near-miss this avoids: a hand-kept bit convention that agreed with the truth at width 7 and disagreed silently at width 8. A grid has no bit order to get wrong. Convert to art strings only at the boundary.
- **The generator writes the `regular` face only.** `embolden.py`'s `KEEP` already contains `range(0x2500, 0x2900)` and `slant-bdf.py` leaves category `So` upright, so bold, italic and bold italic all come out right for free. Do not add a bold or italic path.
- **Nothing under `build/` is hand-edited**, including `build/gen/`.
- **Never let one leg of `make check` answer to the name `check`.** New tests hang off `check-sources`.
- **No file may be added to `glyphs/<size>/regular/` for a codepoint the generator covers.** A hand drawing outranks the generator silently; that is the escape hatch for a bad-looking glyph, not a way to fix a generator bug.
- Run the venv Python as `$(PY)` from the Makefile, or `.venv/bin/python` by hand. This worktree has no `.venv` until `make venv` has run once.
- Comments, names and documentation in English.

---

### Task 1: The two single guillemets

Independent of everything else, and first so that four hand drawings are not buried in a 160-glyph diff.

**Files:**
- Create: `glyphs/7x14/regular/2039.txt`, `glyphs/7x14/regular/203A.txt`
- Create: `glyphs/8x16/regular/2039.txt`, `glyphs/8x16/regular/203A.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing other tasks read. `docs/coverage.md` target set grows by 2.

The models are upstream's own `«` U+00AB and `»` U+00BB, which are two chevrons side by side. A single guillemet is one of those chevrons, recentred on the cell rather than pushed aside — `«`/`»` are deliberately offset so that `«wort»` hugs its text, and a single chevron has no partner to hug.

At 7x14 the ink window is columns 2..4, centred on column 3, which is the same axis the box-drawing vertical uses. At 8x16 the window grows on the right to columns 2..5, following rule 2 of `glyphs/8x16/README.md` — added width goes on the right and column 0 stays clear. Mirroring is inside the glyph's own ink window, not the whole cell.

- [ ] **Step 1: Write `glyphs/7x14/regular/2039.txt`**

```
# U+2039 '‹'  SINGLE LEFT-POINTING ANGLE QUOTATION MARK
.......
.......
.......
.......
.......
.......
....#..
...#...
..#....
...#...
....#..
.......
.......
.......
```

- [ ] **Step 2: Write `glyphs/7x14/regular/203A.txt`**

```
# U+203A '›'  SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
.......
.......
.......
.......
.......
.......
..#....
...#...
....#..
...#...
..#....
.......
.......
.......
```

- [ ] **Step 3: Write `glyphs/8x16/regular/2039.txt`**

```
# U+2039 '‹'  SINGLE LEFT-POINTING ANGLE QUOTATION MARK
........
........
........
........
........
.....#..
....#...
...#....
..#.....
...#....
....#...
.....#..
........
........
........
........
```

- [ ] **Step 4: Write `glyphs/8x16/regular/203A.txt`**

```
# U+203A '›'  SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
........
........
........
........
........
..#.....
...#....
....#...
.....#..
....#...
...#....
..#.....
........
........
........
........
```

- [ ] **Step 5: Prove the drawings are in normal form**

Run: `make headers && git diff --stat`
Expected: no change to the four files. `make headers` rewrites exactly the files `make check` would reject, so a non-empty diff here means one of them was malformed — take the rewritten version.

- [ ] **Step 6: Run the source gate at both sizes**

Run: `make check-sources`
Expected: exit 0, for 7x14 and 8x16.

- [ ] **Step 7: Look at them**

Run: `make preview`
Expected: `‹` and `›` read as single chevrons, the same weight as `«` and `»` beside them, and centred rather than pushed to one side. If either looks off-centre next to its double, fix the art and return to step 5.

- [ ] **Step 8: Commit**

```bash
git add glyphs/7x14/regular/2039.txt glyphs/7x14/regular/203A.txt \
        glyphs/8x16/regular/2039.txt glyphs/8x16/regular/203A.txt
git commit -m "Draw the single guillemets at both sizes"
```

---

### Task 2: `boxgeom.py` — the name grammar

The Unicode name is the drawing instruction. This task builds only the parser, and proves it on the real block.

**Files:**
- Create: `tools/boxgeom.py`
- Create: `tools/test-box.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `boxgeom.parse(name: str) -> dict | None` — returns `{'arms': {str: str}, 'dash': int, 'arc': bool, 'diag': str | None}`. `arms` keys are `'up' | 'down' | 'left' | 'right'`; values are `'light' | 'heavy' | 'double'`. `dash` is 0, 2, 3 or 4. `diag` is the tail of the name for U+2571..2573 and `None` otherwise. Returns `None` if the name does not fit the grammar.
  - `boxgeom.BOX = range(0x2500, 0x2580)` and `boxgeom.BLOCKS = range(0x2580, 0x25A0)`.

- [ ] **Step 1: Write the failing test**

Create `tools/test-box.py`:

```python
#!/usr/bin/env python3
"""Fault injection for tools/boxgeom.py: prove the generator can go wrong.

Nothing here is invented. Every case below is a bug the prototype for this
block actually had, or the check that caught one:

  * the 128 specs must be DISTINCT -- a parser that returned garbage
    uniformly would still "parse 128 of 128";
  * DOUBLE in "LIGHT DOUBLE DASH HORIZONTAL" is a dash count, not a weight;
  * a double corner's outer stroke turns at the OUTER perpendicular stroke,
    and getting that backwards renders the top-left corner as a bottom-right
    one;
  * a heavy corner is one thick line and must come out solid, not stepped;
  * a light stem that runs through a double must pass straight on, while one
    that only meets it must stop at the near line.
"""
import sys
import unicodedata
import boxgeom

FAIL = 0


def check(name, got, want):
    global FAIL
    if got != want:
        print(f'FAIL {name}:\n  got  {got!r}\n  want {want!r}')
        FAIL += 1
    else:
        print(f'ok   {name}')


def spec_key(sp):
    return (tuple(sorted(sp['arms'].items())), sp['dash'], sp['arc'], sp['diag'])


# ---- the grammar covers the real block, and tells its members apart -------
specs = {cp: boxgeom.parse(unicodedata.name(chr(cp))) for cp in boxgeom.BOX}
check('every box drawing name parses',
      sum(1 for s in specs.values() if s is None), 0)
check('the 128 specs are distinct',
      len({spec_key(s) for s in specs.values()}), 128)

# ---- the forms that are easy to get wrong --------------------------------
check('prefix weight reaches both arms',
      boxgeom.parse('BOX DRAWINGS LIGHT DOWN AND RIGHT')['arms'],
      {'down': 'light', 'right': 'light'})
check('per-arm weights stay apart',
      boxgeom.parse('BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY')['arms'],
      {'down': 'light', 'right': 'heavy'})
check('a group may carry several arms',
      boxgeom.parse('BOX DRAWINGS LEFT UP HEAVY AND RIGHT DOWN LIGHT')['arms'],
      {'left': 'heavy', 'up': 'heavy', 'right': 'light', 'down': 'light'})
check('weight may follow its arm or precede it',
      boxgeom.parse('BOX DRAWINGS LIGHT LEFT AND HEAVY RIGHT')['arms'],
      {'left': 'light', 'right': 'heavy'})
check('SINGLE is a spelling of LIGHT',
      boxgeom.parse('BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE')['arms'],
      {'down': 'light', 'right': 'double'})
check('VERTICAL and HORIZONTAL expand to two arms each',
      boxgeom.parse('BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL')['arms'],
      {'up': 'double', 'down': 'double', 'left': 'double', 'right': 'double'})

# ---- DOUBLE DASH is a dash count, never a weight -------------------------
dd = boxgeom.parse('BOX DRAWINGS LIGHT DOUBLE DASH HORIZONTAL')
check('DOUBLE DASH counts dashes', dd['dash'], 2)
check('DOUBLE DASH leaves the weight light', dd['arms'],
      {'left': 'light', 'right': 'light'})
check('TRIPLE DASH counts three',
      boxgeom.parse('BOX DRAWINGS HEAVY TRIPLE DASH VERTICAL')['dash'], 3)

# ---- the modifiers are recognised ----------------------------------------
check('ARC is a modifier, not an arm',
      boxgeom.parse('BOX DRAWINGS LIGHT ARC DOWN AND RIGHT')['arc'], True)
check('ARC keeps its arms',
      boxgeom.parse('BOX DRAWINGS LIGHT ARC DOWN AND RIGHT')['arms'],
      {'down': 'light', 'right': 'light'})
check('a diagonal is set aside',
      boxgeom.parse(
          'BOX DRAWINGS LIGHT DIAGONAL CROSS')['diag'] is not None, True)

# ---- a name outside the grammar is refused, not guessed at ---------------
check('nonsense is refused', boxgeom.parse('BOX DRAWINGS SIDEWAYS GRAPEFRUIT'),
      None)

sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `.venv/bin/python tools/test-box.py`
Expected: `ModuleNotFoundError: No module named 'boxgeom'`.

- [ ] **Step 3: Write the parser**

Create `tools/boxgeom.py`:

```python
#!/usr/bin/env python3
"""Geometry and grammar for U+2500..U+259F -- box drawing and block elements.

THE UNICODE NAME IS THE DRAWING INSTRUCTION
    `BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY` says: a light arm pointing
    down, a heavy arm pointing right. All 128 names in the block are of this
    form over a closed 20-word vocabulary, and they parse into 128 DISTINCT
    arm specifications -- which is the check that matters, because a parser
    returning garbage uniformly would also parse 128 of 128.

    So there is no hand-kept table of 160 rows here. The table is Unicode's.
    gen-braille.py's docstring records the bug that avoids: a hand-kept bit
    convention that agreed with the truth at width 7 and disagreed silently
    at width 8, which would have made all 256 glyphs wrong with no error.

THE GRAMMAR
    Strip a `(DOUBLE|TRIPLE|QUADRUPLE) DASH` modifier and an `ARC` modifier
    first -- DOUBLE there is a dash count and must never be read as a weight.
    Split the rest on ' AND '. Each group is a set of arm words plus at most
    one weight word, in either order. A GROUP WITH NO WEIGHT INHERITS THE
    NEAREST STATED ONE: that single rule is what makes `LIGHT DOWN AND RIGHT`
    and `DOWN LIGHT AND RIGHT HEAVY` fall out of the same code. SINGLE is a
    spelling of LIGHT, used only opposite DOUBLE.

    The three diagonals are named differently and are set aside for the
    renderer to handle on their own.

EVERYTHING IS A 2-D GRID OF 0/1, NEVER A PACKED BIT ROW
    A packed row has a bit order to get wrong, and getting it wrong is silent.
    A grid does not. Packing happens once, at the boundary, in art().
"""
import re
import unicodedata

BOX = range(0x2500, 0x2580)
BLOCKS = range(0x2580, 0x25A0)

ARMS = {'UP': ('up',), 'DOWN': ('down',), 'LEFT': ('left',), 'RIGHT': ('right',),
        'VERTICAL': ('up', 'down'), 'HORIZONTAL': ('left', 'right')}
WEIGHTS = {'LIGHT': 'light', 'HEAVY': 'heavy', 'DOUBLE': 'double',
           'SINGLE': 'light'}
PREFIX = 'BOX DRAWINGS '
DASH_COUNT = {'DOUBLE': 2, 'TRIPLE': 3, 'QUADRUPLE': 4}


def parse(name):
    """Unicode name -> {'arms', 'dash', 'arc', 'diag'}, or None if it does
    not fit the grammar. A name that does not fit is REFUSED, never guessed
    at: a silent guess here becomes a wrong glyph with no error anywhere."""
    if not name.startswith(PREFIX):
        return None
    s = name[len(PREFIX):]
    spec = {'arms': {}, 'dash': 0, 'arc': False, 'diag': None}

    if 'DIAGONAL' in s:
        spec['diag'] = s
        return spec

    m = re.search(r'\b(DOUBLE|TRIPLE|QUADRUPLE) DASH\b', s)
    if m:
        spec['dash'] = DASH_COUNT[m.group(1)]
        s = ' '.join((s[:m.start()] + s[m.end():]).split())
    if ' ARC ' in f' {s} ':
        spec['arc'] = True
        s = s.replace('ARC ', '')

    groups = []
    for group in s.split(' AND '):
        tokens = group.split()
        weights = [t for t in tokens if t in WEIGHTS]
        arms = [t for t in tokens if t in ARMS]
        if len(weights) > 1 or not arms or len(weights) + len(arms) != len(tokens):
            return None
        groups.append((weights[0] if weights else None, arms))

    stated = next((w for w, _ in groups if w), None)
    if stated is None:
        return None
    for weight, arms in groups:
        if weight:
            stated = weight
        for token in arms:
            for arm in ARMS[token]:
                spec['arms'][arm] = WEIGHTS[stated]
    return spec
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python tools/test-box.py`
Expected: every line `ok`, exit 0. In particular `the 128 specs are distinct` must report 128.

- [ ] **Step 5: Confirm each case can go red on its own**

For each of the three load-bearing cases below, break the named line in `boxgeom.py`, re-run, confirm **only** that case flips, then put it back. A case that stays green without its rule was never testing it.

| break this | expect only this to fail |
|---|---|
| delete the `DASH` strip block | `DOUBLE DASH counts dashes`, `DOUBLE DASH leaves the weight light`, `TRIPLE DASH counts three` |
| replace the inheritance (`stated = weight`) with `stated = None` | `prefix weight reaches both arms` |
| make the final `return None` a `return spec` | `nonsense is refused` |

- [ ] **Step 6: Commit**

```bash
git add tools/boxgeom.py tools/test-box.py
git commit -m "Read the box drawing arm specification out of the Unicode name"
```

---

### Task 3: The geometry table and the junction rule

The heart of it. All three rules below were arrived at by rendering strips and reading them, not by reasoning; the test cases are the bugs that were found that way.

**Files:**
- Modify: `tools/boxgeom.py`
- Modify: `tools/test-box.py`

**Interfaces:**
- Consumes: `boxgeom.parse` from Task 2.
- Produces:
  - `boxgeom.GEOMETRY: dict[str, dict]` — keyed `'7x14'`, `'8x16'`.
  - `boxgeom.render_box(spec: dict, size: str) -> list[list[int]]` — an `H`-by-`W` grid of 0/1.
  - `boxgeom.art(px: list[list[int]]) -> list[str]` — grid to `#`/`.` rows.

- [ ] **Step 1: Write the failing test**

Append to `tools/test-box.py`, above the final `sys.exit(...)` line:

```python
# ---- geometry: the axes are where upstream already puts - + and | --------
def draw(cp, size):
    return boxgeom.art(boxgeom.render_box(
        boxgeom.parse(unicodedata.name(chr(cp))), size))


check('7x14 light horizontal is row 7, full width',
      [i for i, r in enumerate(draw(0x2500, '7x14')) if '#' in r], [7])
check('7x14 light horizontal spans the whole cell',
      draw(0x2500, '7x14')[7], '#######')
check('8x16 light vertical is column 4',
      {r.index('#') for r in draw(0x2502, '8x16')}, {4})
check('7x14 light vertical is column 3',
      {r.index('#') for r in draw(0x2502, '7x14')}, {3})

# ---- a heavy corner is ONE thick line, so it comes out solid -------------
# Capping the two rows of a heavy line separately rendered a stepped corner.
check('7x14 heavy down-and-right has a solid corner',
      draw(0x250F, '7x14')[6:8], ['..#####', '..#####'])

# ---- a double corner: outer turns at outer, inner at inner ---------------
# Getting this backwards renders the TOP-LEFT corner as a bottom-right one.
check('7x14 double down-and-right turns at the top left',
      draw(0x2554, '7x14')[6:9], ['..#####', '..#....', '..#.###'])

# ---- a double running past a branch keeps its outer line whole ----------
check('7x14 double vertical and right keeps the outer line continuous',
      [r[2] for r in draw(0x2560, '7x14')], ['#'] * 14)
check('7x14 double vertical and right breaks the inner line',
      draw(0x2560, '7x14')[7], '..#....')

# ---- the double cross opens into four corner pieces ---------------------
check('7x14 double cross is open in the middle',
      draw(0x256C, '7x14')[7], '.......')

# ---- a light stem that runs through passes on; one that meets, stops -----
check('7x14 single vertical crosses a double horizontal',
      [r[3] for r in draw(0x256A, '7x14')], ['#'] * 14)
check('7x14 a stem that only meets the double does not bridge its gap',
      draw(0x2564, '7x14')[7], '.......')

# ---- nothing comes apart at a cell boundary -----------------------------
# An arm that stops one pixel short is not a compromise, it is a seam.
for size in ('7x14', '8x16'):
    short = []
    for cp in boxgeom.BOX:
        spec = boxgeom.parse(unicodedata.name(chr(cp)))
        if spec['diag'] or spec['dash'] or spec['arc']:
            continue
        rows = boxgeom.art(boxgeom.render_box(spec, size))
        edge = {'up': rows[0],
                'down': rows[-1],
                'left': ''.join(r[0] for r in rows),
                'right': ''.join(r[-1] for r in rows)}
        for arm in spec['arms']:
            if '#' not in edge[arm]:
                short.append((hex(cp), arm))
    check(f'{size}: every arm reaches its own cell edge', short, [])
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `.venv/bin/python tools/test-box.py`
Expected: `AttributeError: module 'boxgeom' has no attribute 'art'`.

- [ ] **Step 3: Write the geometry table and the renderer**

Append to `tools/boxgeom.py`:

```python
# ---------------------------------------------------------------------------
# GEOMETRY, DRAWN PER SIZE, NEVER SCALED -- gen-braille.py's rule.
#
# c0 / r0 are where upstream already puts `|` and `-` at each size, so a
# generated `+`-shaped junction lines up with the real `+`. c0 is also rule 1
# of glyphs/8x16/README.md, which names box-drawing verticals as the reason
# that rule exists.
#
# HEAVY takes its second pixel on the side that centres the pair in the cell;
# ties go up and left. Worked through, that one rule gives all four entries:
# at 7x14 the cell centre is row 6.5, so heavy grows UP from row 7; at 8x16 it
# is row 7.5, so heavy grows DOWN. At 8x16 the horizontal centre is column 3.5
# so heavy grows LEFT from column 4; at 7x14 column 3 is already the exact
# centre -- the tie -- so heavy grows left there too.
#
# DOUBLE is clean at both sizes: one blank line between two strokes,
# symmetric about the axis, no rounding anywhere.
# ---------------------------------------------------------------------------
GEOMETRY = {
    '7x14': dict(w=7, h=14, c0=3, r0=7,
                 vheavy=(2, 3), hheavy=(6, 7), vdouble=(2, 4), hdouble=(6, 8)),
    '8x16': dict(w=8, h=16, c0=4, r0=7,
                 vheavy=(3, 4), hheavy=(7, 8), vdouble=(3, 5), hdouble=(6, 8)),
}


def art(px):
    return [''.join('#' if v else '.' for v in row) for row in px]


def _vpos(g, weight):
    return {'light': (g['c0'],), 'heavy': g['vheavy'], 'double': g['vdouble']}[weight]


def _hpos(g, weight):
    return {'light': (g['r0'],), 'heavy': g['hheavy'], 'double': g['hdouble']}[weight]


def render_box(spec, size):
    """An arm is a rectangle from its cell edge to the junction. The only
    question is where each arm stops, and there are exactly three answers.

    1. A LIGHT OR HEAVY arm reaches the FAR edge of the perpendicular band.
       Heavy is one thick line, not two strokes, which is what makes heavy
       corners solid. Capping its two rows separately renders a stepped `┏`.

    2. Except that it stops at the NEAR edge when a double runs past it --
       perpendicular band double, both perpendicular arms present, and its own
       axis not running through. This keeps the inside of a double open, so
       `╤` hangs its stem below the lower line while `╪`, whose vertical does
       run through, passes straight on.

    3. A DOUBLE's two strokes cap individually: outer turns at outer, inner at
       inner, where a stroke is "outer" when the perpendicular arm on its side
       is absent. That is the whole of the double-corner behaviour. It gives
       `╔` a clean corner with no stub, `╠` a continuous outer line with the
       inner one broken across the junction, and it opens `╬` into four corner
       pieces with a hole in the middle -- which is what `╬` is.

    Getting rule 3's orientation backwards renders `╔` as a bottom-right
    corner. test-box.py pins it.
    """
    g = GEOMETRY[size]
    width, height = g['w'], g['h']
    px = [[0] * width for _ in range(height)]
    a = spec['arms']
    up, dn, lf, rt = a.get('up'), a.get('down'), a.get('left'), a.get('right')

    vcols = sorted(set(_vpos(g, up) if up else ())
                   | set(_vpos(g, dn) if dn else ())) or [g['c0']]
    hrows = sorted(set(_hpos(g, lf) if lf else ())
                   | set(_hpos(g, rt) if rt else ())) or [g['r0']]
    cL, cR = vcols[0], vcols[-1]
    rT, rB = hrows[0], hrows[-1]

    h_is_double = 'double' in (lf, rt)
    v_is_double = 'double' in (up, dn)
    h_runs = lf is not None and rt is not None
    v_runs = up is not None and dn is not None

    def vstroke(col, weight, arm):
        if weight != 'double':
            near = h_is_double and h_runs and not v_runs
            if arm == 'up':
                return range(0, (rT if near else rB) + 1)
            return range(rB if near else rT, height)
        outer = (lf is None) if col == cL else ((rt is None) if col == cR else False)
        if arm == 'up':
            return range(0, (rB if outer else rT) + 1)
        return range(rT if outer else rB, height)

    def hstroke(row, weight, arm):
        if weight != 'double':
            near = v_is_double and v_runs and not h_runs
            if arm == 'left':
                return range(0, (cL if near else cR) + 1)
            return range(cR if near else cL, width)
        outer = (up is None) if row == rT else ((dn is None) if row == rB else False)
        if arm == 'left':
            return range(0, (cR if outer else cL) + 1)
        return range(cL if outer else cR, width)

    for arm, weight in (('up', up), ('down', dn)):
        if weight:
            for col in _vpos(g, weight):
                for r in vstroke(col, weight, arm):
                    px[r][col] = 1
    for arm, weight in (('left', lf), ('right', rt)):
        if weight:
            for row in _hpos(g, weight):
                for c in hstroke(row, weight, arm):
                    px[row][c] = 1
    return px
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python tools/test-box.py`
Expected: every line `ok`, exit 0.

- [ ] **Step 5: Confirm each case can go red on its own**

| break this | expect only this to fail |
|---|---|
| in `vstroke`/`hstroke`, drop the `if weight != 'double'` branch so everything caps individually | `7x14 heavy down-and-right has a solid corner` |
| swap `rB if outer else rT` to `rT if outer else rB` in the double branch of `vstroke` | `7x14 double down-and-right turns at the top left`, `...keeps the outer line continuous` |
| set `near = False` always | `7x14 a stem that only meets the double does not bridge its gap` |
| set `near = h_is_double and h_runs` (drop `not v_runs`) | `7x14 single vertical crosses a double horizontal` |

- [ ] **Step 6: Look at the whole block as a strip**

Run:
```bash
.venv/bin/python -c "
import sys, unicodedata; sys.path.insert(0,'tools')
import boxgeom
for size in ('7x14','8x16'):
    for base in range(0x2500, 0x2580, 8):
        cps=[c for c in range(base,base+8) if not boxgeom.parse(unicodedata.name(chr(c)))['diag']]
        if not cps: continue
        grids=[boxgeom.art(boxgeom.render_box(boxgeom.parse(unicodedata.name(chr(c))),size)) for c in cps]
        print('  '.join(f'{chr(c)} U+{c:04X}'.ljust(len(grids[0][0])) for c in cps))
        for r in range(len(grids[0])): print('  '.join(g[r] for g in grids))
        print()
"
```
Expected: read every one against the character printed above it. The project's rule is to render a batch and judge it; a generator does not exempt it. Arcs, dashes and diagonals will be wrong here — they are Task 4.

- [ ] **Step 7: Commit**

```bash
git add tools/boxgeom.py tools/test-box.py
git commit -m "Render a box drawing junction from its arm specification"
```

---

### Task 4: Arcs, diagonals and dashes

**Files:**
- Modify: `tools/boxgeom.py`
- Modify: `tools/test-box.py`

**Interfaces:**
- Consumes: `render_box`, `GEOMETRY`, `art`.
- Produces: `boxgeom.glyph(cp: int, size: str) -> list[list[int]]` — the single entry point for any codepoint in `BOX`. Task 6's CLI calls only this.

- [ ] **Step 1: Write the failing test**

Append to `tools/test-box.py`, above the final `sys.exit(...)`:

```python
# ---- arcs: the corner turn is pulled back one pixel on each arm ----------
def g(cp, size):
    return boxgeom.art(boxgeom.glyph(cp, size))


check('7x14 arc down-and-right cuts the corner',
      g(0x256D, '7x14')[7:9], ['....###', '...#...'])
check('7x14 arc keeps its vertical to the bottom edge',
      g(0x256D, '7x14')[13], '...#...')
check('7x14 arc up-and-left cuts the opposite corner',
      g(0x256F, '7x14')[6:8], ['...#...', '###....'])

# ---- diagonals run corner to corner -------------------------------------
check('7x14 upper-left to lower-right starts top left',
      g(0x2572, '7x14')[0], '#......')
check('7x14 upper-left to lower-right ends bottom right',
      g(0x2572, '7x14')[13], '......#')
check('7x14 the cross is its own mirror',
      [r[::-1] for r in g(0x2573, '7x14')], g(0x2573, '7x14'))

# ---- dashes break the line and nothing else -----------------------------
for cp, n in ((0x254C, 2), (0x2504, 3), (0x2508, 4)):
    rows = g(cp, '7x14')
    runs = [x for x in rows[7].split('.') if x]
    check(f'U+{cp:04X} breaks into {n} dashes', len(runs), n)
    check(f'U+{cp:04X} inks no row but the axis',
          sum(1 for r in rows if '#' in r), 1)
check('a dashed vertical breaks into three',
      len([x for x in ''.join(r[3] for r in g(0x2506, '7x14')).split('.') if x]), 3)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `.venv/bin/python tools/test-box.py`
Expected: `AttributeError: module 'boxgeom' has no attribute 'glyph'`.

- [ ] **Step 3: Write the three families and the entry point**

Append to `tools/boxgeom.py`:

```python
def _apply_dash(px, spec, size):
    """Break a straight line by clearing interior gap lines.

    DASHES MERGE ACROSS THE CELL BOUNDARY. A cell cannot both begin and end
    with a gap and still look evenly dashed, so a repeated `┄` shows one
    longer run at each seam. That is true of bitmap fonts generally at this
    width; the gap positions are chosen by eye per size and the seam is
    documented in README.md rather than hidden.
    """
    g = GEOMETRY[size]
    n = spec['dash']
    horizontal = 'left' in spec['arms']
    span = g['w'] if horizontal else g['h']
    for i in range(n - 1):
        k = (i + 1) * span // n
        if horizontal:
            for r in range(g['h']):
                px[r][k] = 0
        else:
            for c in range(g['w']):
                px[k][c] = 0
    return px


def _apply_arc(px, spec, size):
    """Round a light corner by pulling the turn back one pixel on each arm.

    At this size a one-pixel chamfer IS the whole of the curve. The two runs
    then meet diagonally, which is already normal here -- `❯` is nothing but
    diagonal steps -- and trace-outline.py's corner-touch rule handles it.
    """
    g = GEOMETRY[size]
    r0, c0 = g['r0'], g['c0']
    dr = 1 if 'down' in spec['arms'] else -1
    dc = 1 if 'right' in spec['arms'] else -1
    px[r0][c0] = 0                 # drop the sharp turn itself
    px[r0][c0 + dc] = 1            # the horizontal starts one column out
    px[r0 + dr][c0] = 1            # the vertical starts one row out
    return px


def _render_diag(name, size):
    g = GEOMETRY[size]
    width, height = g['w'], g['h']
    px = [[0] * width for _ in range(height)]
    up_right = 'UPPER RIGHT TO LOWER LEFT' in name
    cross = 'CROSS' in name
    for r in range(height):
        c = round(r * (width - 1) / (height - 1))
        if cross or not up_right:
            px[r][c] = 1                      # upper left -> lower right
        if cross or up_right:
            px[r][width - 1 - c] = 1          # upper right -> lower left
    return px


def glyph(cp, size):
    """The single entry point for a codepoint in BOX."""
    name = unicodedata.name(chr(cp))
    spec = parse(name)
    if spec is None:
        raise ValueError(f'U+{cp:04X} {name}: outside the box drawing grammar')
    if spec['diag']:
        return _render_diag(name, size)
    px = render_box(spec, size)
    if spec['dash']:
        px = _apply_dash(px, spec, size)
    if spec['arc']:
        px = _apply_arc(px, spec, size)
    return px
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python tools/test-box.py`
Expected: every line `ok`, exit 0.

- [ ] **Step 5: Confirm the arc and dash cases can go red**

| break this | expect only this to fail |
|---|---|
| in `_apply_arc`, delete the `px[r0][c0] = 0` line | `7x14 arc down-and-right cuts the corner` |
| in `_apply_dash`, change `(i + 1) * span // n` to `(i + 1) * span // (n + 1)` | the dash-count cases |
| in `_render_diag`, drop the `width - 1 - c` line | `7x14 the cross is its own mirror` |

- [ ] **Step 6: Look at the four arcs, three diagonals and twelve dashes**

Run the strip command from Task 3 step 6 again, now covering U+2504..250B, U+254C..254F and U+256D..2573 at both sizes.
Expected: the arcs read as rounded corners at 7x14. **At 8x16 a one-pixel chamfer may look too small** — that is risk 1 in the spec. If it does, widen it there and nowhere else, by adding a `chamfer` entry to `GEOMETRY` and reading it in `_apply_arc`. Do not scale it; pick it by eye per size, which is what the table is for.

- [ ] **Step 7: Commit**

```bash
git add tools/boxgeom.py tools/test-box.py
git commit -m "Draw the arcs, diagonals and dashed lines"
```

---

### Task 5: Block elements, and the two compromises

**Files:**
- Modify: `tools/boxgeom.py`
- Modify: `tools/test-box.py`

**Interfaces:**
- Consumes: `GEOMETRY`, `art`.
- Produces: `boxgeom.block(cp: int, size: str) -> list[list[int]]`, plus `boxgeom.rows_for(n, size)` and `boxgeom.cols_for(n, size)` returning the ink extent of an `n`/8 fraction.

- [ ] **Step 1: Write the failing test**

Append to `tools/test-box.py`, above the final `sys.exit(...)`:

```python
# ---- the halves tile the cell exactly: no overlap, no hole ---------------
def b(cp, size):
    return boxgeom.art(boxgeom.block(cp, size))


for size in ('7x14', '8x16'):
    upper, lower = b(0x2580, size), b(0x2584, size)
    full = b(0x2588, size)
    merged = [''.join('#' if (x == '#' or y == '#') else '.' for x, y in zip(u, l))
              for u, l in zip(upper, lower)]
    check(f'{size}: upper and lower half tile the cell', merged, full)
    check(f'{size}: upper and lower half do not overlap',
          sum(1 for u, l in zip(upper, lower) for x, y in zip(u, l)
              if x == '#' and y == '#'), 0)

    left, right = b(0x258C, size), b(0x2590, size)
    merged = [''.join('#' if (x == '#' or y == '#') else '.' for x, y in zip(a_, b_))
              for a_, b_ in zip(left, right)]
    check(f'{size}: left and right half tile the cell', merged, full)
    check(f'{size}: left and right half do not overlap',
          sum(1 for a_, b_ in zip(left, right) for x, y in zip(a_, b_)
              if x == '#' and y == '#'), 0)

# ---- the eighth ladders, and the one collapse that is forced ------------
check('7x14 left-eighth ladder', [boxgeom.cols_for(n, '7x14') for n in range(1, 8)],
      [1, 2, 3, 3, 4, 5, 6])
check('7x14 collapses exactly one pair -- six widths for seven steps',
      len({boxgeom.cols_for(n, '7x14') for n in range(1, 8)}), 6)
check('8x16 left-eighth ladder is exact',
      [boxgeom.cols_for(n, '8x16') for n in range(1, 8)], [1, 2, 3, 4, 5, 6, 7])
check('8x16 collapses nothing',
      len({boxgeom.cols_for(n, '8x16') for n in range(1, 8)}), 7)
check('7x14 lower-eighth ladder is distinct',
      [boxgeom.rows_for(n, '7x14') for n in range(1, 8)], [2, 4, 5, 7, 9, 11, 12])
check('8x16 lower-eighth ladder is exact',
      [boxgeom.rows_for(n, '8x16') for n in range(1, 8)], [2, 4, 6, 8, 10, 12, 14])

# ---- the collapse is where the design says it is, and only there ---------
# NOT `b(0x258C, size) == b(0x258C, size)` at 8x16: a check that compares a
# thing to itself passes whatever the code does, which is the defect this
# project keeps finding in its own checks.
check('7x14: the collapsed pair is three-eighths and one-half',
      b(0x258D, '7x14'), b(0x258C, '7x14'))
check('8x16: three-eighths and one-half stay apart',
      b(0x258D, '8x16') != b(0x258C, '8x16'), True)
check('7x14: five-eighths is NOT part of the collapse',
      b(0x258B, '7x14') != b(0x258C, '7x14'), True)

# ---- quadrants tile too -------------------------------------------------
for size in ('7x14', '8x16'):
    quads = [b(cp, size) for cp in (0x2598, 0x259D, 0x2596, 0x2597)]
    merged = [''.join('#' if any(q[r][c] == '#' for q in quads) else '.'
                      for c in range(len(quads[0][0])))
              for r in range(len(quads[0]))]
    check(f'{size}: the four quadrants tile the cell', merged, b(0x2588, size))

# ---- every block element parses and fills something ---------------------
for size in ('7x14', '8x16'):
    empty = [cp for cp in boxgeom.BLOCKS
             if not any('#' in r for r in b(cp, size))]
    check(f'{size}: no block element is blank', empty, [])
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `.venv/bin/python tools/test-box.py`
Expected: `AttributeError: module 'boxgeom' has no attribute 'block'`.

- [ ] **Step 3: Write the block element renderer**

Append to `tools/boxgeom.py`:

```python
# ---------------------------------------------------------------------------
# BLOCK ELEMENTS, U+2580..U+259F
#
# TWO THINGS CANNOT BE EXACT AT 7x14, AND BOTH ARE RECORDED IN README.md.
#
# 1. The left eighth-blocks must collapse one pair. Seven steps need seven
#    distinct widths below "full" and a 7-column cell has six. That is
#    pigeonhole; no rounding rule escapes it. cols_for rounds half DOWN,
#    giving 1,2,3,3,4,5,6 -- so `▍` and `▌` are the same glyph. Rounding down
#    is what makes 4/8 agree with the half-block split, which puts the axis
#    column in the RIGHT half, matching the way the axis row falls in the
#    lower half. `▌`+`▐` therefore tile the cell exactly.
#
# 2. The shades cannot tile at width 7: their dither period is even and 7 is
#    odd, so the pattern phase-shifts at every cell boundary and a seam shows.
#    At 8x16 both are exact.
# ---------------------------------------------------------------------------
EIGHTHS = {'ONE EIGHTH': 1, 'ONE QUARTER': 2, 'THREE EIGHTHS': 3, 'HALF': 4,
           'FIVE EIGHTHS': 5, 'THREE QUARTERS': 6, 'SEVEN EIGHTHS': 7}


def rows_for(n, size):
    """Rows of ink for an n/8 vertical fraction. Round half UP: 14 rows give
    2,4,5,7,9,11,12 -- seven distinct steps -- and 16 rows are exact."""
    return (n * GEOMETRY[size]['h'] + 4) // 8


def cols_for(n, size):
    """Columns of ink for an n/8 horizontal fraction. Round half DOWN, so 4/8
    agrees with the half-block split. See the note above for the collapse."""
    return max(1, (n * GEOMETRY[size]['w'] + 3) // 8)


def _vsplit(size):
    """Rows in the upper half -- an exact half at both sizes."""
    return GEOMETRY[size]['h'] // 2


def _hsplit(size):
    """Columns in the left half. The axis column belongs to the RIGHT half,
    matching the way the axis row belongs to the lower half."""
    return GEOMETRY[size]['c0']


def block(cp, size):
    g = GEOMETRY[size]
    width, height = g['w'], g['h']
    px = [[0] * width for _ in range(height)]
    name = unicodedata.name(chr(cp))

    def fill(rr, cc):
        for r in rr:
            for c in cc:
                px[r][c] = 1

    if name == 'FULL BLOCK':
        fill(range(height), range(width))
    elif name.endswith('SHADE'):
        level = name.split()[0]
        for r in range(height):
            for c in range(width):
                if level == 'MEDIUM':
                    on = (r + c) % 2 == 0
                elif level == 'LIGHT':
                    on = (r % 2 == 0 and c % 4 == 0) or (r % 2 == 1 and c % 4 == 2)
                else:
                    on = not ((r % 2 == 0 and c % 4 == 2) or (r % 2 == 1 and c % 4 == 0))
                px[r][c] = 1 if on else 0
    elif name.startswith('QUADRANT'):
        vs, hs = _vsplit(size), _hsplit(size)
        corner = {'UPPER LEFT': (range(0, vs), range(0, hs)),
                  'UPPER RIGHT': (range(0, vs), range(hs, width)),
                  'LOWER LEFT': (range(vs, height), range(0, hs)),
                  'LOWER RIGHT': (range(vs, height), range(hs, width))}
        for part in name[len('QUADRANT '):].split(' AND '):
            fill(*corner[part])
    else:                                   # <EDGE> <FRACTION> BLOCK
        edge, frac = name[:-len(' BLOCK')].split(' ', 1)
        n = EIGHTHS[frac]
        if edge == 'LOWER':
            fill(range(height - rows_for(n, size), height), range(width))
        elif edge == 'UPPER':
            k = _vsplit(size) if frac == 'HALF' else rows_for(n, size)
            fill(range(0, k), range(width))
        elif edge == 'LEFT':
            k = _hsplit(size) if frac == 'HALF' else cols_for(n, size)
            fill(range(height), range(0, k))
        else:                               # RIGHT
            k = (width - _hsplit(size)) if frac == 'HALF' else cols_for(n, size)
            fill(range(height), range(width - k, width))
    return px
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python tools/test-box.py`
Expected: every line `ok`, exit 0.

- [ ] **Step 5: Confirm the tiling cases can go red**

| break this | expect only this to fail |
|---|---|
| make `_hsplit` return `GEOMETRY[size]['c0'] + 1` | `left and right half tile the cell` at 7x14 (they overlap) |
| make `cols_for` round half up (`+ 4` instead of `+ 3`) | `7x14 left-eighth ladder`, `the left half IS four eighths` |
| make `_vsplit` return `h // 2 + 1` | `upper and lower half do not overlap` |

- [ ] **Step 6: Look at all 32 at both sizes**

Run the strip command from Task 3 step 6, over `range(0x2580, 0x25A0)` and calling `boxgeom.block` instead of `render_box`.
Expected: the ladders step evenly; `▌`+`▐` and `▀`+`▄` clearly halve the cell. **The three shades are a judgement call at width 7** — that is risk 2 in the spec. Print `░▒▓` repeated four cells wide and check that each still reads as a distinct density; if `▓` reads as solid, thin it.

- [ ] **Step 7: Commit**

```bash
git add tools/boxgeom.py tools/test-box.py
git commit -m "Draw the block elements, and record the two 7x14 compromises"
```

---

### Task 6: The generator and the build wiring

The first task where the font actually grows.

**Files:**
- Create: `tools/gen-box.py`
- Modify: `Makefile` (the `GENTOOL` list at line 161, the `$(GEN)` recipe at line 205, and the `check-sources` recipe at line 258)

**Interfaces:**
- Consumes: `boxgeom.glyph`, `boxgeom.block`, `boxgeom.art`, `boxgeom.BOX`, `boxgeom.BLOCKS`.
- Produces: 160 files in `build/gen/<size>/regular/` per size.

- [ ] **Step 1: Write the generator**

Create `tools/gen-box.py`:

```python
#!/usr/bin/env python3
"""Generate U+2500..U+259F -- box drawing and block elements -- into build/gen/.

Usage: gen-box.py [SIZE]          (default 7x14)

All the judgement is in tools/boxgeom.py: the grammar that reads an arm
specification out of the Unicode name, the per-size geometry table, and the
junction rule. This file only walks the two blocks and writes the result.

REGULAR ONLY, DELIBERATELY. embolden.py's KEEP already covers
range(0x2500, 0x2900) -- its comment says box drawing "must keep their exact
pitch to line up with their neighbours" -- and slant-bdf.py leaves category
So upright. So bold, italic and bold italic all come out right with no work
here, and adding a bold path would be the thing that broke them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxgeom
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'
if SIZE not in boxgeom.GEOMETRY:
    sys.exit(f'gen-box.py: the geometry table covers '
             f'{", ".join(sorted(boxgeom.GEOMETRY))}, not {SIZE}')

out = gs.gen_dir(SIZE, 'regular')
written = 0
for cp in boxgeom.BOX:
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp,
                   boxgeom.art(boxgeom.glyph(cp, SIZE)))
    written += 1
for cp in boxgeom.BLOCKS:
    gs.write_glyph(os.path.join(out, gs.filename(cp)), cp,
                   boxgeom.art(boxgeom.block(cp, SIZE)))
    written += 1
print(f'{out}: {written} box drawing and block element glyphs')
```

- [ ] **Step 2: Run it once by hand and check the output shape**

Run: `.venv/bin/python tools/gen-box.py 7x14 && ls build/gen/7x14/regular/ | wc -l`
Expected: the script prints `160 box drawing and block element glyphs`, and the directory holds at least 160 files. Then `cat build/gen/7x14/regular/250C.txt` and confirm it is a well-formed 14-row, 7-column drawing with a header naming U+250C.

- [ ] **Step 3: Wire it into the Makefile**

In `GENTOOL` (line 161), add `tools/gen-box.py` and `tools/boxgeom.py` to the list. In the `$(GEN)` recipe (line 205), add after the `gen-circled-digits.py` line:

```make
	python3 tools/gen-box.py $(SIZE)
```

In the `check-sources` recipe (line 258), add after the `test-weight.py` line:

```make
	$(PY) tools/test-box.py
```

`boxgeom.py` must be in `GENTOOL` as well as `gen-box.py`: the derived layer is regenerated when any generator tool changes, and a geometry edit that did not trigger a rebuild would leave stale glyphs in `build/gen/` with nothing to say so.

- [ ] **Step 4: Build both sizes clean**

Run: `make clean && make all`
Expected: exit 0 for 7x14 and 8x16.

- [ ] **Step 5: Run the whole gate**

Run: `make check`
Expected: exit 0. `check-sources`, `check-outlines` and `check-version` all pass, at both sizes. `check-outlines` is the one that matters most here — it proves the traced outline reproduces every new bitmap.

- [ ] **Step 6: Confirm the coverage actually grew, and by the right amount**

Run: `make index && head -20 docs/coverage.md`
Expected: the target set reads **1168** codepoints, and every face reports **0 missing**.

The arithmetic is 1006 + 2 + 160: the baseline, the two guillemets from Task 1, and the 160 generated here. The spec says 1166 because it counts only its own 160 — it puts the guillemets explicitly out of scope. Re-derive rather than trusting either number: 1006 was measured at commit `6055907`, and a different total means either a codepoint collided with something already covered or a generator wrote fewer files than it claimed. Do not adjust the expected number to match the output; find out why it differs.

- [ ] **Step 7: Prove bold and italic came out right without being asked to**

Run:
```bash
.venv/bin/python -c "
import sys; sys.path.insert(0,'tools')
import glyphstore as gs
for size in ('7x14','8x16'):
    reg = gs.bitmaps(size,'regular'); bold = gs.bitmaps(size,'bold')
    ital = gs.bitmaps(size,'italic')
    box = [c for c in range(0x2500,0x25A0)]
    print(size, 'bold differs from regular in',
          sum(1 for c in box if reg[c] != bold[c]), 'of 160')
    print(size, 'italic differs from regular in',
          sum(1 for c in box if reg[c] != ital[c]), 'of 160')
"
```
Expected: **0 of 160 in both**. A non-zero count means either `embolden.KEEP` or `is_slanted` is not doing what the spec says it does, and the generator must not paper over it — fix the cause.

- [ ] **Step 8: Commit**

```bash
git add tools/gen-box.py Makefile docs/coverage.md
git commit -m "Generate box drawing and block elements at both sizes"
```

---

### Task 7: Read both blocks as a rendered strip and settle the judgement calls

The spec names three things that can only be settled by eye. This task is where they get settled, and it is deliberately separate so that a reviewer can reject the look without rejecting the machinery.

**Files:**
- Modify: `tools/boxgeom.py` (the `GEOMETRY` table and, if needed, `_apply_arc`, `_apply_dash`, the shade patterns)

**Interfaces:**
- Consumes: everything above.
- Produces: no new names. Only geometry values change.

- [ ] **Step 1: Render both blocks at both sizes**

Run: `make preview`
Expected: 320 glyphs to read.

- [ ] **Step 2: Draw a real box and look at it**

Run:
```bash
.venv/bin/python -c "
import sys; sys.path.insert(0,'tools')
import boxgeom
def show(cps, size):
    grids=[boxgeom.art(boxgeom.glyph(c,size)) for c in cps]
    for r in range(len(grids[0])): print(''.join(g[r] for g in grids))
for size in ('7x14','8x16'):
    print('---', size, 'light box')
    show([0x250C,0x2500,0x252C,0x2500,0x2510], size)
    show([0x2502,0x0020 if False else 0x2502,0x2502,0x2502,0x2502], size)
    show([0x2514,0x2500,0x2534,0x2500,0x2518], size)
    print('---', size, 'rounded box')
    show([0x256D,0x2500,0x2500,0x2500,0x256E], size)
    show([0x2570,0x2500,0x2500,0x2500,0x256F], size)
"
```
Expected: the corners meet the rules with no seam and no overhang; the rounded box's corners read as curves, not as notches.

- [ ] **Step 3: Settle the arc chamfer at 8x16**

If the one-pixel chamfer looks too small in the rounded box at 8x16, add a `chamfer` key to each `GEOMETRY` entry (`1` at 7x14, `2` at 8x16) and read it in `_apply_arc`, stepping back that many pixels on each arm. Pick it by eye per size; do not scale it.
Then run: `.venv/bin/python tools/test-box.py` and update the three arc assertions to the new art if it changed.

- [ ] **Step 4: Settle the shades**

Run:
```bash
.venv/bin/python -c "
import sys; sys.path.insert(0,'tools')
import boxgeom
for size in ('7x14','8x16'):
    print('---', size)
    for cp in (0x2591,0x2592,0x2593):
        g=boxgeom.art(boxgeom.block(cp,size))
        for r in range(len(g)): print(g[r]*4)
        print()
"
```
Expected: four cells side by side. Each of the three must read as a distinct density, and `▓` must not read as solid. The seam at every 7th column is expected and is documented, not fixed.

- [ ] **Step 5: Settle the dash gaps**

Run the same four-cell repetition for U+2504, U+2508, U+254C, U+2506, U+250A, U+254E at both sizes.
Expected: the dashes read as dashes. The longer run at each seam is expected. If a pattern reads as a solid line with a nick in it, move the gaps.

- [ ] **Step 6: Re-run the whole gate**

Run: `make check`
Expected: exit 0. Any geometry change regenerates `build/gen/` through `GENTOOL`, so `check-outlines` re-proves every changed glyph.

- [ ] **Step 7: Commit**

```bash
git add tools/boxgeom.py tools/test-box.py
git commit -m "Settle the arc, shade and dash geometry by eye at both sizes"
```

If nothing needed changing, say so and skip the commit rather than inventing one.

---

### Task 8: Documentation

**Files:**
- Modify: `README.md` (add a section; edit "Known gaps")
- Modify: `glyphs/7x14/README.md`, `glyphs/8x16/README.md`
- Modify: `CHANGES.md`
- Modify: `docs/coverage.md` (regenerated, not edited)

**Interfaces:**
- Consumes: the final geometry values from Task 7.
- Produces: nothing code reads.

**A true-sounding sentence near changed code is suspect.** The last branch of this project shipped five sentences that described something the code did not do, and every one of them was true when it was written. Check each claim below against the code as it now stands, not against this plan.

- [ ] **Step 1: Add the README section**

Add after "## Terminal UI symbols", a section `## Box drawing and block elements` covering:
- Both blocks are complete at both sizes, 160 codepoints each, all generated.
- The Unicode name is the drawing instruction; the grammar parses 128 names into 128 distinct specs, which is the check that a uniformly broken parser would fail.
- The axis positions, and that they are where upstream already puts `-` and `|`, so `┼` lines up with `+`.
- The heavy-centring rule and the double spacing, per size, copied from the final `GEOMETRY`.
- **The two compromises, in the shape the dingbats compromises are written:** `▍` and `▌` are the same glyph at 7x14 because seven steps cannot fit in six widths, and the shades show a seam at every cell boundary at 7x14 because their dither period is even and 7 is odd. Both exact at 8x16.
- That dashes merge across the cell seam.
- That bold and italic needed no work, and why.

- [ ] **Step 2: Correct "Known gaps"**

Remove the box drawing and block elements entries if any were added. Note that `## Miscellaneous Symbols U+2600..U+26FF has only ★ and ☆` is unrelated and stays.

- [ ] **Step 3: Record the geometry where a drawer will look**

In both `glyphs/<size>/README.md`, add the axis column, axis row, heavy positions and double positions for that size to the geometry table, and say that these codepoints are generated so a file here would override the generator. At 8x16 this is the rule 1 and rule 3 the file already states — cross-reference rather than restate, and correct rule 1 if the final geometry differs from what it predicts.

- [ ] **Step 4: Write the changelog entry**

Add under `## [Unreleased]`, in the existing `### New` (create the heading only if absent — the file uses `### New`, never `### Added`):

A single entry covering both blocks, the count, that they are generated from the Unicode name, and **both 7x14 compromises named explicitly**. The changelog is read by people deciding whether to upgrade; a compromise omitted there is the same defect as a compromise omitted from the README.

Mention the two single guillemets from Task 1 in the same `### New` as their own entry.

- [ ] **Step 5: Regenerate coverage**

Run: `make index`
Expected: `docs/coverage.md` shows the new target-set size and 0 missing in all eight faces. CI fails if this file is stale, so it must be committed.

- [ ] **Step 6: Run everything one last time**

Run: `make check && make check-site`
Expected: both exit 0. `make check-packages` is deliberately not part of `make check`; run it only if `rpm` is installed locally, and if it fails for a missing `rpm` that is the check working, not a broken setup.

- [ ] **Step 7: Commit**

```bash
git add README.md glyphs/7x14/README.md glyphs/8x16/README.md CHANGES.md docs/coverage.md
git commit -m "Document the box drawing blocks and their two 7x14 compromises"
```

---

## Done

At this point the branch has: 160 generated glyphs per size covering U+2500..U+259F, four hand-drawn guillemets, one new importable module, one new generator, one new fault-injection suite wired into `check-sources`, and the documentation. `make check` and `make check-site` are green at both sizes, and bold and italic were proven to have come out right without being touched.

The branch is then ready for `superpowers:requesting-code-review` and a pull request.
