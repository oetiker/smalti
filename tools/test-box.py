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


def field(name, key):
    """One field of parse(name), or None when the name is refused -- so a
    refusal fails its own case instead of crashing every case after it."""
    sp = boxgeom.parse(name)
    return sp[key] if sp else None


# ---- the grammar covers the real block, and tells its members apart -------
specs = {cp: boxgeom.parse(unicodedata.name(chr(cp))) for cp in boxgeom.BOX}
check('every box drawing name parses',
      sum(1 for s in specs.values() if s is None), 0)
check('the 128 specs are distinct',
      len({spec_key(s) for s in specs.values() if s}), 128)

# ---- the forms that are easy to get wrong --------------------------------
check('prefix weight reaches both arms',
      field('BOX DRAWINGS LIGHT DOWN AND RIGHT', 'arms'),
      {'down': 'light', 'right': 'light'})
check('per-arm weights stay apart',
      field('BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY', 'arms'),
      {'down': 'light', 'right': 'heavy'})
check('a group may carry several arms',
      field('BOX DRAWINGS LEFT UP HEAVY AND RIGHT DOWN LIGHT', 'arms'),
      {'left': 'heavy', 'up': 'heavy', 'right': 'light', 'down': 'light'})
check('weight may follow its arm or precede it',
      field('BOX DRAWINGS LIGHT LEFT AND HEAVY RIGHT', 'arms'),
      {'left': 'light', 'right': 'heavy'})
check('SINGLE is a spelling of LIGHT',
      field('BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE', 'arms'),
      {'down': 'light', 'right': 'double'})
check('VERTICAL and HORIZONTAL expand to two arms each',
      field('BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL', 'arms'),
      {'up': 'double', 'down': 'double', 'left': 'double', 'right': 'double'})

# ---- DOUBLE DASH is a dash count, never a weight -------------------------
dd = 'BOX DRAWINGS LIGHT DOUBLE DASH HORIZONTAL'
check('DOUBLE DASH counts dashes', field(dd, 'dash'), 2)
check('DOUBLE DASH leaves the weight light', field(dd, 'arms'),
      {'left': 'light', 'right': 'light'})
check('TRIPLE DASH counts three',
      field('BOX DRAWINGS HEAVY TRIPLE DASH VERTICAL', 'dash'), 3)

# ---- the modifiers are recognised ----------------------------------------
check('ARC is a modifier, not an arm',
      field('BOX DRAWINGS LIGHT ARC DOWN AND RIGHT', 'arc'), True)
check('ARC keeps its arms',
      field('BOX DRAWINGS LIGHT ARC DOWN AND RIGHT', 'arms'),
      {'down': 'light', 'right': 'light'})
check('a diagonal is set aside',
      field('BOX DRAWINGS LIGHT DIAGONAL CROSS', 'diag') is not None, True)

# ---- a name outside the grammar is refused, not guessed at ---------------
check('nonsense is refused', boxgeom.parse('BOX DRAWINGS SIDEWAYS GRAPEFRUIT'),
      None)

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

# ---- arcs: the corner turn is pulled back one pixel on each arm ----------
def g(cp, size):
    return boxgeom.art(boxgeom.glyph(cp, size))


check('7x14 arc down-and-right cuts the corner',
      g(0x256D, '7x14')[7:9], ['....###', '...#...'])
check('7x14 arc keeps its vertical to the bottom edge',
      g(0x256D, '7x14')[13], '...#...')
check('7x14 arc up-and-left cuts the opposite corner',
      g(0x256F, '7x14')[6:8], ['...#...', '###....'])
# 8x16 cuts two pixels, picked by eye: the runs meet through one diagonal
# pixel. 7x14 stays at one.
check('8x16 arc down-and-right cuts two pixels',
      g(0x256D, '8x16')[7:10], ['......##', '.....#..', '....#...'])
check('8x16 arc up-and-left cuts two pixels',
      g(0x256F, '8x16')[5:8], ['....#...', '...#....', '###.....'])

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

# ---- a dash cell starts with ink and ends with a gap, so a run repeats
# evenly. Gaps only inside the cell made every seam one double-length dash.
# The one exception is forced: four dashes and four gaps need 8 columns, and
# 7x14 has 7, so its quadruple dashes keep the gaps inside.
uneven = []
for size in ('7x14', '8x16'):
    geo = boxgeom.GEOMETRY[size]
    for cp in boxgeom.BOX:
        spec = boxgeom.parse(unicodedata.name(chr(cp)))
        if not spec['dash']:
            continue
        rows = g(cp, size)
        if 'left' in spec['arms']:
            line = rows[geo['r0']]
            span = geo['w']
        else:
            line = ''.join(r[geo['c0']] for r in rows)
            span = geo['h']
        if 2 * spec['dash'] > span:
            continue
        if not (line[0] == '#' and line[-1] == '.'):
            uneven.append((size, hex(cp), line))
check('a dash cell starts with ink and ends with a gap', uneven, [])
check('7x14 double dash repeats evenly', g(0x254C, '7x14')[7], '###.##.')
check('8x16 quadruple dash repeats evenly', g(0x2508, '8x16')[7], '#.#.#.#.')
check('7x14 quadruple dash keeps its gaps inside', g(0x2508, '7x14')[7], '#.#.#.#')

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

sys.exit(1 if FAIL else 0)
