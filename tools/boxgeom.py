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
