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

sys.exit(1 if FAIL else 0)
