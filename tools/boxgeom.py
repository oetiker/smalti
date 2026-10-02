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
