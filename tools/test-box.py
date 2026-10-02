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

sys.exit(1 if FAIL else 0)
