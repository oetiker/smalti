#!/usr/bin/env python3
"""Generate the circled-digit dingbats, U+2776..U+2793, into build/gen/.

Usage: gen-circled-digits.py [SIZE]        (default 7x14)

Three runs of ten live in that range and Unicode separates them by a
distinction -- serif versus sans-serif -- that seven pixels cannot carry, so
U+2776..U+277F and U+278A..U+2793 come out identical here.  Both are the
NEGATIVE runs: a white digit knocked out of a black disc.  U+2780..U+2789 is
the positive run: a black digit inside a white ring.

The three TEN glyphs need a wider interior than the ring can give.  Two
digits take five columns -- a 3-wide zero, a 1-wide one and a gap -- and a
full ring takes the outer two, so the one would merge into the left wall and
the zero into the right.  The negative tens are fine as they are, because a
solid disc has no thin wall to merge with.  U+2789 gets an OPEN ring instead:
the top and bottom arcs only, drawn so that no arc pixel sits in a digit
column.  It keeps the family's height and still reads as an enclosure.

This writes only into build/gen/, so it is freely re-runnable and cannot
overwrite anyone's work.  To change one glyph, draw it: a file in
glyphs/<size>/regular/ outranks anything here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphstore as gs

SIZE = sys.argv[1] if len(sys.argv) > 1 else '7x14'

# Every part of the ring family is drawn fresh per size, never scaled: where
# the ink sits is a design decision, not an arithmetic one.  See
# glyphs/8x16/README.md for the placement rules the 8x16 entry follows.
GEOMETRY = {
    '7x14': {
        # the ring spans rows 3..11 of the 14-row cell (9 rows: one cap row,
        # one edge row, five full-width rows, mirrored).
        'top': 3,
        'ring': ['..###..', '.#...#.', '#.....#', '#.....#', '#.....#',
                 '#.....#', '#.....#', '.#...#.', '..###..'],
        # Same nine rows, but open at the sides so the five columns of "10"
        # are free.  Row 1 and row 7 hold the widest ink, at the two columns
        # the digits skip.
        'arcs': ['.#####.', '#.....#', '.......', '.......', '.......',
                 '.......', '.......', '#.....#', '.#####.'],
        'disc': ['..###..', '.#####.', '#######', '#######', '#######',
                 '#######', '#######', '.#####.', '..###..'],
        # 3 wide, 5 tall -- the largest that leaves a clear column beside
        # the ring.  Column offset 2 puts it at cols 2..4 of the 7-wide
        # ring, leaving col 1 and col 5 clear beside the wall at col 0/6.
        'digit_col': 2,
        'digit': {
            '1': ['.#.', '##.', '.#.', '.#.', '###'],
            '2': ['###', '..#', '###', '#..', '###'],
            '3': ['###', '..#', '###', '..#', '###'],
            '4': ['#.#', '#.#', '###', '..#', '..#'],
            '5': ['###', '#..', '###', '..#', '###'],
            '6': ['###', '#..', '###', '#.#', '###'],
            '7': ['###', '..#', '..#', '..#', '..#'],
            '8': ['###', '#.#', '###', '#.#', '###'],
            '9': ['###', '#.#', '###', '..#', '###'],
        },
        # 5 wide -- only ever knocked out of a disc, never set inside a
        # ring.  Passed at column offset 0: the string already carries its
        # own margin (col 0 and col 6 blank, matching where the ring's wall
        # would sit) so the "1 10" pair reads at the same width the family
        # would use if a ring could hold it.
        'ten': ['.#.###.', '.#.#.#.', '.#.#.#.', '.#.#.#.', '.#.###.'],
    },
    '8x16': {
        # Upstream's own digits (checked with show-glyphs.py against
        # Tamzen8x16r.bdf) start at row 3 at both sizes and grew from 8 rows
        # tall (3..10, baseline row 10 of 14) to 9 rows tall (3..11,
        # baseline row 11 of 16) -- the top stayed put and the extra row
        # went to the bottom.  The 7x14 ring already extends one row below
        # its own digit's baseline row for the round bottom, so the 8x16
        # ring keeps top=3 and grows to 10 rows (3..12): one more row than
        # upstream's taller 8x16 digit, dipping one row into the 4-row
        # descent exactly as the 7x14 ring dips one row into its 3-row
        # descent.  That leaves rows 13..15 clear beneath it (3 rows, up
        # from 2 at 7x14) -- the cell's extra 2 rows of height split evenly
        # between "ring" and "margin below the ring", with the top margin
        # unchanged because upstream's own digits don't move it either.
        'top': 3,
        # 8 columns wide throughout its widest rows (cols 0 and 7), per
        # glyphs/8x16/README.md rule 3: a ring is the cell-spanning case,
        # not a letterform with a gutter, so it must not stop at column 6.
        # Two cap rows (as at 7x14) plus six full-width rows (one more than
        # 7x14's five, since the ring grew a row) plus two more cap rows.
        'ring': ['..####..', '.#....#.', '#......#', '#......#', '#......#',
                 '#......#', '#......#', '#......#', '.#....#.', '..####..'],
        # Same ten rows, open at the sides for "10".  The cap rows thicken
        # into a solid bar (matching the 7x14 arcs, which widen their cap
        # into '.#####.' rather than reusing the ring's own narrower curve)
        # and the row beside it becomes a full edge-to-edge pixel pair;
        # the six straight rows in between are left entirely blank so "10"
        # can use any column there without touching an arc.
        'arcs': ['.######.', '#......#', '........', '........', '........',
                 '........', '........', '........', '#......#', '.######.'],
        'disc': ['..####..', '.######.', '########', '########', '########',
                 '########', '########', '########', '.######.', '..####..'],
        # 4 wide, 6 tall.  The ring's interior at the six full-width rows
        # is cols 1..6 (width 6, wall at col 0/7); a 4-wide digit at offset
        # 2 sits at cols 2..5, leaving col 1 and col 6 clear -- one column
        # beside the ring on each side, exactly the 7x14 proportion (one
        # clear column each side), not a scale of the 7x14 glyphs.  Six
        # rows tall fills the six full-width interior rows exactly, the
        # same "digit height == straight-row count" relationship 7x14 uses.
        'digit_col': 2,
        'digit': {
            '1': ['.##.', '###.', '.##.', '.##.', '.##.', '####'],
            '2': ['####', '...#', '..#.', '.#..', '#...', '####'],
            '3': ['####', '...#', '.###', '...#', '...#', '####'],
            '4': ['#..#', '#..#', '#..#', '####', '...#', '...#'],
            '5': ['####', '#...', '####', '...#', '...#', '####'],
            '6': ['####', '#...', '####', '#..#', '#..#', '####'],
            '7': ['####', '...#', '..#.', '..#.', '.#..', '.#..'],
            '8': ['####', '#..#', '####', '#..#', '#..#', '####'],
            '9': ['####', '#..#', '####', '...#', '...#', '####'],
        },
        # Column offset 0, like 7x14 -- the string already carries its own
        # margin.  Interior is cols 1..6 (width 6, matching the ring's
        # interior above): col 1 the "1" stroke, col 2 a gap, cols 3..6 a
        # 4-wide "0", cols 0 and 7 blank at the positions the ring's wall
        # would occupy.  Six rows tall to match the taller digit band.
        'ten': ['.#.####.', '.#.#..#.', '.#.#..#.', '.#.#..#.', '.#.#..#.',
                '.#.####.'],
    },
}
if SIZE not in GEOMETRY:
    sys.exit(f'gen-circled-digits.py: the ring below covers '
             f'{", ".join(sorted(GEOMETRY))}, not {SIZE}')

CELL_W, CELL_H = gs.cell(SIZE)
G = GEOMETRY[SIZE]
TOP = G['top']
BLANK = '.' * CELL_W
RING, ARCS, DISC = G['ring'], G['arcs'], G['disc']
DIGIT, DIGIT_COL = G['digit'], G['digit_col']
TEN = G['ten']

NAMES = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
         'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN']


def compose(base, art, col, negative):
    """Draw art onto a copy of base at column col; negative knocks it out.

    The hardcoded 2 below is the row where the ring's straight, full-width
    section starts (past its cap and edge rows) -- it is part of the ring
    art's own internal shape, not the cell geometry, so it stays a literal
    here.  Both sizes in GEOMETRY are drawn with a two-row cap (one curve
    row, one edge row) before the straight section, so it is 2 for each of
    them; a future size that changes the cap's row count would need this
    to move too, and an IndexError here is the loud signal that it did.
    """
    rows = [list(r) for r in base]
    for i, line in enumerate(art):
        for j, ch in enumerate(line):
            if ch == '#':
                rows[2 + i][col + j] = '.' if negative else '#'
    return [''.join(r) for r in rows]


def cell(rows):
    art = [BLANK] * CELL_H
    for i, r in enumerate(rows):
        art[TOP + i] = r
    return art


outdir = gs.gen_dir(SIZE, 'regular')
n = 0
for base_cp, negative in [(0x2776, True), (0x2780, False), (0x278A, True)]:
    for i, word in enumerate(NAMES):
        cp = base_cp + i
        if word == 'TEN':
            base = DISC if negative else ARCS
            rows = compose(base, TEN, 0, negative)
        else:
            base = DISC if negative else RING
            rows = compose(base, DIGIT[str(i + 1)], DIGIT_COL, negative)
        gs.write_glyph(os.path.join(outdir, gs.filename(cp)), cp, cell(rows))
        n += 1
print(f'{outdir}: {n} circled digits')
